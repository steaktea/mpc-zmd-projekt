from enum import Enum
from typing import Union
from PIL import Image
import numpy as np


class ImageComponent(Enum):
    RED = 0
    GREEN = 1
    BLUE = 2


class ImageData:
    end_string = "$t3g0"

    def __init__(self, image: Image):
        """ImageData class

        Args:
            image_file (PIL Image): The imported image file

        Attributes:
            original_array (np.NDArray): The original image numpy array
            rgb_array (np.NDArray): Numpy 3D array containing the image RGB components
            ycbcr_array (np.NDArray) Numpy 3D array containing the image YCbCr components
        """
        self.original_array = np.asarray(image)
        self.rgb_array = np.asarray(image).copy()
        self.ycbcr_array = self.rgb2ycbcr()

    @property
    def original_image(self) -> Image:
        return Image.fromarray(self.original_array, mode="RGB")

    def rgb2image(self) -> Image:
        """Converts the RGB data to PIL Image

        Returns:
            Image: Resulting image
        """
        return Image.fromarray(self.rgb_array, mode="RGB")

    def ycbcr2image(self) -> Image:
        """Converts the YCbCr data to a PIL Image

        Returns:
            Image: Resulting image
        """
        return Image.fromarray(self.ycbcr_array, mode="YCbCr")

    def rgb2ycbcr(self):
        """Takes the RGB components and computes the components in YCbCr

        Returns:
            np.NDArray: Numpy 3D array containing the image YCbCr components
        """
        xform = np.array(
            [[0.299, 0.587, 0.114], [-0.1687, -0.3313, 0.5], [0.5, -0.4187, -0.0813]]
        )
        ycbcr = self.rgb_array.dot(xform.T)
        ycbcr[:, :, [1, 2]] += 128
        return np.uint8(ycbcr)

    def ycbcr2rgb(self):
        """Takes the YCbCr components and computes the components in RGB

        Returns:
            np.NDArray: Numpy 3D array containing the image RGB components
        """
        xform = np.array([[1, 0, 1.402], [1, -0.34414, -0.71414], [1, 1.772, 0]])
        rgb = self.ycbcr_array.astype(np.float)
        rgb[:, :, [1, 2]] -= 128
        rgb = rgb.dot(xform.T)
        np.putmask(rgb, rgb > 255, 255)
        np.putmask(rgb, rgb < 0, 0)
        return np.uint8(rgb)

    def lsb_encode(
        self,
        selected_component: ImageComponent,
        watermark: Image,
        depth: int,
    ):
        """Least Significant Bit watermark encoding

        Args:
            selected_component (ImageComponent): The image component to encode watermark in (Red/Green/Blue)
            watermark (str): Watermark string
            depth (int): The bit depth

        Raises:
            ValueError: In case of invalid ImageComponent input
        """
        match selected_component:
            case ImageComponent.RED:
                self.rgb_array[:, :, 0] = self.encode_lsb_image(
                    self.rgb_array[:, :, 0], watermark, depth
                )

            case ImageComponent.GREEN:
                self.rgb_array[:, :, 1] = self.encode_lsb_image(
                    self.rgb_array[:, :, 1], watermark, depth
                )
            case ImageComponent.BLUE:
                self.rgb_array[:, :, 2] = self.encode_lsb_image(
                    self.rgb_array[:, :, 2], watermark, depth
                )
            case _:
                raise ValueError("Invalid ImageComponent input")

    def encode_lsb_text(
        self, component: np.ndarray, watermark_str: str, depth: int
    ) -> np.ndarray:
        """Single component LSB string encoding

        Args:
            component (np.ndarray): The selected component array
            watermark_str (str): Watermark string
            depth (int): The bit depth

        Raises:
            ValueError: In case the picture is too small to encode the message

        Returns:
            np.ndarray: New image component with encoded data.
        """
        watermark = watermark_str + self.end_string
        binary_watermark = "".join([f"{i:08b}" for i in watermark.encode()])
        data_length = len(binary_watermark)
        if data_length > component.size:
            raise ValueError("Picture is too small to encode the message.")

        # převod pole intů na pole bitů
        binary_component = np.unpackbits(component, axis=1)

        # vytvoří 1D array o stejné velikosti jako složka doplněný nulami na konci
        binary_watermark_array = np.array(list(binary_watermark), dtype=np.uint8)
        data_bits = np.pad(
            binary_watermark_array,
            (0, component.size - len(binary_watermark_array)),
            "constant",
            constant_values=(0),
        )

        # přemění 1D array na 2D array o stejných rozměrech jako má složka
        data_array = data_bits.reshape(component.shape)

        # nahradí bitovou hladinu složku prvky z `data_array`
        binary_component[:, depth::8] = data_array

        # převod pole bitů zpět na pole intů
        new_component = np.packbits(binary_component, axis=1)

        return new_component

    def encode_lsb_image(
        self, component: np.ndarray, watermark: Image, depth: int
    ) -> np.ndarray:
        """Single component LSB image encoding

        Args:
            component (np.ndarray): The selected component array
            watermark_img (str): Watermark string
            depth (int): The bit depth

        Raises:
            ValueError: In case the picture is too small to encode the message

        Returns:
            np.ndarray: New image component with encoded data.
        """
        watermark.convert("1")
        watermark_array = np.asarray(watermark, dtype=np.uint8)

        tiled_watermark = np.tile(
            watermark_array,
            np.array(component.shape) // np.array(np.shape(watermark_array)) + 1,
        )[tuple(map(slice, component.shape))]

        # převod pole intů na pole bitů
        binary_component = np.unpackbits(component, axis=1)
        # vložím svůj pattern do definované hloubky
        binary_component[:, depth::8] = tiled_watermark

        return np.packbits(binary_component, axis=1)

    def lsb_decode(self, selected_component: ImageComponent, depth: int) -> Image:
        """Least Significant Bit watermark decoding

        print(i)
            selected_component (ImageComponent): The image component to encode watermark in (Red/Green/Blue)
            depth (int): The bit depth

        Raises:
            ValueError: In case of invalid ImageComponent input

        Returns:
            str: The decoded string
        """
        match selected_component:
            case ImageComponent.RED:
                data = self.decode_lsb_image(self.rgb_array[:, :, 0], depth)

            case ImageComponent.GREEN:
                data = self.decode_lsb_image(self.rgb_array[:, :, 1], depth)
            case ImageComponent.BLUE:
                data = self.decode_lsb_image(self.rgb_array[:, :, 2], depth)
            case _:
                raise ValueError("Invalid ImageComponent input")

        return data

    def decode_lsb_text(self, component: np.ndarray, depth: int) -> str:
        """Single component LSB decoding

        Args:
            component (np.ndarray): The selected component array
            depth (int): The bit depth

        Returns:
            str: The decoded string
        """
        binary_end = "".join([f"{i:08b}" for i in self.end_string.encode()])
        binary_component = np.unpackbits(component, axis=1)
        # extrakce bitové hladiny
        data_array = binary_component[:, depth::8]

        # převod bitové hladiny do listu byte stringů
        bit_list = data_array.flatten().tolist()
        full_bit_str = "".join(str(int) for int in bit_list)
        bit_data = full_bit_str.split(binary_end, 1)[0]
        byte_data = [bit_data[i * 8 : i * 8 + 8] for i in range(len(bit_data) // 8)]

        # převod zpět do UTF-8
        data_str = bytes([int(x, 2) for x in byte_data]).decode("utf-8")

        return data_str

    def decode_lsb_image(self, component: np.ndarray, depth: int) -> Image:
        """Single component LSB decoding

        Args:
            component (np.ndarray): The selected component array
            depth (int): The bit depth

        Returns:
            str: The decoded string
        """
        binary_component = np.unpackbits(component, axis=1)
        # extrakce bitové hladiny
        data_array = binary_component[:, depth::8]

        # převod bitové hladiny do listu byte stringů
        image = Image.frombytes(
            mode="1", size=data_array.shape[::-1], data=np.packbits(data_array, axis=1)
        )

        return image
