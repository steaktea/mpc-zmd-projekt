from enum import Enum
from io import BytesIO

import numpy as np
from PIL import Image


class ImageComponent(Enum):
    RED = 0
    GREEN = 1
    BLUE = 2


class ImagePSNR:
    def calculate_psnr(img1: Image, img2: Image, max_value: int = 255) -> float:
        """Calculating peak signal-to-noise ratio (PSNR) between two images.

        Args:
            img1: The first Image
            img2: The second Image
            max_value (optional): Maximum possible value in the image. Defaults to 255.

        Returns:
            float: Calculated PSNR
        """
        img1_arr = np.asarray(img1, dtype=np.float32).copy()
        img2_arr = np.asarray(img2, dtype=np.float32).copy()
        mse = np.mean((img1_arr - img2_arr) ** 2)
        if mse == 0:
            return 100
        return float(20 * np.log10(max_value / (np.sqrt(mse))))


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

    def rgb2ycbcr(self) -> np.ndarray:
        """Takes the RGB components and computes the components in YCbCr

        Returns:
            np.ndarray: Numpy 3D array containing the image YCbCr components
        """
        xform = np.array(
            [[0.299, 0.587, 0.114], [-0.1687, -0.3313, 0.5], [0.5, -0.4187, -0.0813]]
        )
        ycbcr = self.rgb_array.dot(xform.T)
        ycbcr[:, :, [1, 2]] += 128
        print(type(np.uint8(ycbcr)))
        return np.uint8(ycbcr)

    def ycbcr2rgb(self) -> np.ndarray:
        """Takes the YCbCr components and computes the components in RGB

        Returns:
            np.ndarray: Numpy 3D array containing the image RGB components
        """
        xform = np.array([[1, 0, 1.402], [1, -0.34414, -0.71414], [1, 1.772, 0]])
        rgb = self.ycbcr_array.astype(np.float)
        rgb[:, :, [1, 2]] -= 128
        rgb = rgb.dot(xform.T)
        np.putmask(rgb, rgb > 255, 255)
        np.putmask(rgb, rgb < 0, 0)
        print(type(np.uint8(rgb)))
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

    def jpeg_compress(self, quality: int):
        """Compress the image by the JPEG compression algorithm

        Args:
            quality: Compression quality
        """
        buffer = BytesIO()
        jpg_buffer = BytesIO()
        self.rgb2image().save(jpg_buffer, "JPEG", subsampling=0, quality=100)
        jpg_image = Image.open(jpg_buffer, formats=["JPEG"])
        jpg_image.save(buffer, "JPEG", subsampling=0, quality=quality)

        new_image = Image.open(buffer, formats=["JPEG"])
        self.rgb_array = np.asarray(new_image).copy()
        self.ycbcr_array = self.rgb2ycbcr()

    def image_rotate(self, angle: int):
        """Rotates the image by a given angle and back. When rotating back,
        the image is cropped to the original size

        Args:
            angle: Angle of rotation
        """
        temp_image: Image = self.original_image
        temp_image = temp_image.rotate(angle, expand=True)
        temp_image.show()
        original_size = self.original_image.size
        original_center = (int(original_size[0] / 2), int(original_size[1] / 2))
        temp_size = temp_image.size
        center_point = (int(temp_size[0] / 2), int(temp_size[1] / 2))
        new_image: Image = temp_image.rotate(-angle)
        new_image = new_image.crop(
            (
                center_point[0] - original_center[0],
                center_point[1] - original_center[1],
                center_point[0] + original_center[0],
                center_point[1] + original_center[1],
            )
        )

        self.rgb_array = np.asarray(new_image).copy()
        self.ycbcr_array = self.rgb2ycbcr()

    def image_resize(self, percentage: int):
        """Resizes the image to the given percentage.

        Args:
            angle: Angle of rotation
        """
        temp_image: Image = self.original_image
        original_size = self.original_image.size
        new_size = (
            int(original_size[0] * (percentage / 100)),
            int(original_size[1] * (percentage / 100)),
        )
        new_image: Image = temp_image.resize(new_size)

        self.rgb_array = np.asarray(new_image).copy()
        self.ycbcr_array = self.rgb2ycbcr()

    def image_flip(self, method: str):
        """Flips the image

        Args:
            method: horizontal or vertical
        """
        if method == "horizontal":
            transpose_method = Image.Transpose.FLIP_LEFT_RIGHT
        elif method == "vertical":
            transpose_method = Image.Transpose.FLIP_TOP_BOTTOM
        temp_image: Image = self.original_image
        new_image: Image = temp_image.transpose(transpose_method)

        self.rgb_array = np.asarray(new_image).copy()
        self.ycbcr_array = self.rgb2ycbcr()
