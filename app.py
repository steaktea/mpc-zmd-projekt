import os
import sys

from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSlider,
    QTabWidget,
    QWidget,
)

from image import ImageComponent, ImageData, ImagePSNR


class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle("Watermark Application")
        layout = QGridLayout()
        self.setLayout(layout)
        tabwidget = QTabWidget()
        tabwidget.addTab(LSBTab(), "LSB")
        tabwidget.addTab(AttackTab(), "ATTACKS")
        layout.addWidget(tabwidget, 0, 0)


class LSBTab(QWidget):
    pre_encode_image_path: str = ""
    pre_decode_image_path: str = ""
    new_image: Image = None
    watermark_path: str = ""
    selected_component = 0
    selected_depth = 0

    def __init__(self):
        QWidget.__init__(self)

        self.pagelayout = QGridLayout()
        self.topframe = QFrame()
        self.encodeframe = QFrame()
        self.decodeframe = QFrame()
        self.toplayout = QGridLayout()
        self.encodelayout = QGridLayout()
        self.decodelayout = QGridLayout()

        self.rgb_label = QLabel("Image Component")
        self.rgb_combobox = QComboBox()
        self.depth_label = QLabel("Watermark depth: 0")
        self.depth_slider = QSlider(Qt.Orientation.Horizontal)
        self.encode_radio = QRadioButton("Encode")
        self.decode_radio = QRadioButton("Decode")
        self.encode_image_button = QPushButton("Select Image")
        self.pre_encode_image_field = QLabel()
        self.pre_encode_image_label = QLabel()
        self.watermark_button = QPushButton("Select Watermark")
        self.watermark_field = QLabel()
        self.watermark_label = QLabel()
        self.new_image_field = QLabel()
        self.new_image_button = QPushButton("Save")
        self.pre_decode_image_field = QLabel()
        self.pre_decode_image_label = QLabel()
        self.encode_button = QPushButton("Encode")
        self.decode_image_button = QPushButton("Select Image")
        self.decode_image_label = QLabel()
        self.decode_button = QPushButton("Decode")
        self.psnr_label = QLabel("Encoded Image PSNR: 100%")

        self.set_properties()

    def set_properties(self):
        self.topframe.setFrameShape(QFrame.Shape.StyledPanel)
        self.encodeframe.setFrameShape(QFrame.Shape.StyledPanel)
        self.decodeframe.setFrameShape(QFrame.Shape.StyledPanel)
        self.topframe.setLayout(self.toplayout)
        self.encodeframe.setLayout(self.encodelayout)
        self.decodeframe.setLayout(self.decodelayout)
        self.decodeframe.hide()

        self.rgb_combobox.addItems(["Red", "Green", "Blue"])
        self.depth_slider.setMinimum(0)
        self.depth_slider.setMaximum(7)
        self.encode_radio.setChecked(True)

        # Connect signals to the methods.
        self.rgb_combobox.activated.connect(self.on_combobox_activated)
        self.depth_slider.valueChanged.connect(self.on_slider_changed)
        self.encode_image_button.clicked.connect(self.open_file_encoding)
        self.decode_image_button.clicked.connect(self.open_file_decoding)
        self.watermark_button.clicked.connect(self.open_file_encoding)
        self.encode_radio.toggled.connect(self.on_radio_selected)
        self.decode_radio.toggled.connect(self.on_radio_selected)
        self.encode_button.clicked.connect(self.encode)
        self.decode_button.clicked.connect(self.decode)
        self.new_image_button.clicked.connect(self.save_image)

        self.toplayout.addWidget(self.rgb_label, 0, 0)
        self.toplayout.addWidget(self.rgb_combobox, 1, 0)
        self.toplayout.addWidget(self.depth_label, 0, 1)
        self.toplayout.addWidget(self.depth_slider, 1, 1)
        self.toplayout.addWidget(self.encode_radio, 2, 0)
        self.toplayout.addWidget(self.decode_radio, 2, 1)

        self.encodelayout.addWidget(self.encode_image_button, 0, 0)
        self.encodelayout.addWidget(self.watermark_button, 0, 1)
        self.encodelayout.addWidget(self.pre_encode_image_field, 1, 0)
        self.encodelayout.addWidget(
            self.pre_encode_image_label, 2, 0, Qt.AlignmentFlag.AlignCenter
        )
        self.encodelayout.addWidget(self.watermark_field, 1, 1)
        self.encodelayout.addWidget(
            self.watermark_label, 2, 1, Qt.AlignmentFlag.AlignCenter
        )
        self.encodelayout.addWidget(self.encode_button, 3, 0, 1, 2)

        self.decodelayout.addWidget(self.decode_image_button, 0, 0)
        self.decodelayout.addWidget(self.decode_image_label, 0, 1)
        self.decodelayout.addWidget(
            self.pre_decode_image_field, 1, 0, 1, 2, Qt.AlignmentFlag.AlignCenter
        )
        self.decodelayout.addWidget(
            self.pre_decode_image_label, 2, 0, 1, 2, Qt.AlignmentFlag.AlignCenter
        )
        self.decodelayout.addWidget(self.decode_button, 3, 0, 1, 2)

        self.pagelayout.addWidget(self.topframe, 0, 0)
        self.pagelayout.addWidget(self.encodeframe, 1, 0)
        self.pagelayout.addWidget(self.decodeframe, 1, 0)
        self.pagelayout.addWidget(self.psnr_label, 2, 0)
        self.pagelayout.addWidget(self.new_image_field, 0, 1, 2, 1)
        self.pagelayout.addWidget(self.new_image_button, 2, 1, 1, 1)
        self.new_image_field.hide()
        self.new_image_button.hide()
        self.psnr_label.hide()

        self.setLayout(self.pagelayout)

    def on_radio_selected(self):
        radio_button = self.sender()

        if radio_button.isChecked():
            match radio_button.text():
                case "Encode":
                    self.pre_decode_image_field.clear()
                    self.pre_decode_image_label.clear()
                    self.pre_decode_image_path = ""
                    self.new_image: Image = None
                    self.new_image_field.clear()
                    self.new_image_button.hide()
                    self.decodeframe.hide()
                    self.encodeframe.show()
                case "Decode":
                    self.pre_encode_image_field.clear()
                    self.pre_encode_image_label.clear()
                    self.pre_encode_image_path = ""
                    self.watermark_field.clear()
                    self.watermark_label.clear()
                    self.watermark_path = ""
                    self.new_image: Image = None
                    self.new_image_field.clear()
                    self.new_image_button.hide()
                    self.encodeframe.hide()
                    self.psnr_label.hide()
                    self.decodeframe.show()
                case _:
                    raise ValueError("Invalid RadioButton text")

    def on_combobox_activated(self, index):
        self.selected_component = index

    def on_slider_changed(self, index):
        self.selected_depth = index
        self.depth_label.setText(f"Watermark depth: {index}")

    def show_resized_image(
        self, component: QLabel, label: QLabel, pixmap: QPixmap, text: str, size: int
    ):
        component.clear()
        if pixmap.size().height() > size:
            pixmap = pixmap.scaledToHeight(size)
        if pixmap.size().width() > size:
            pixmap = pixmap.scaledToWidth(size)
        component.setFixedSize(size, size)
        component.setPixmap(pixmap)
        component.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setText(text)

    def open_file_encoding(self):
        push_button = self.sender()
        result = QFileDialog.getOpenFileName(
            self,
            "Select File",
            filter="Images (*.ico *.jp2 *.jpg *.jpm *.jpx *.png *.tiff *.webp *.xpm)",
        )
        file_path = result[0]

        match push_button.text():
            case "Select Image":
                self.pre_encode_image_path = file_path
                image_pixmap = QPixmap(self.pre_encode_image_path)
                self.show_resized_image(
                    self.pre_encode_image_field,
                    self.pre_encode_image_label,
                    image_pixmap,
                    os.path.basename(file_path),
                    128,
                )

            case "Select Watermark":
                self.watermark_path = file_path
                watermark_pixmap = QPixmap(self.watermark_path)
                self.show_resized_image(
                    self.watermark_field,
                    self.watermark_label,
                    watermark_pixmap,
                    os.path.basename(file_path),
                    128,
                )
            case _:
                raise ValueError("Invalid PushButton text")

    def open_file_decoding(self):
        result = QFileDialog.getOpenFileName(
            self,
            "Select File",
            filter="Images (*.ico *.jp2 *.jpg *.jpm *.jpx *.png *.tiff *.webp *.xpm)",
        )
        file_path = result[0]

        self.pre_decode_image_path = file_path
        image_pixmap = QPixmap(self.pre_decode_image_path)
        self.show_resized_image(
            self.pre_decode_image_field,
            self.pre_decode_image_label,
            image_pixmap,
            os.path.basename(file_path),
            256,
        )

    def encode(self):
        if self.pre_encode_image_path is not None and self.watermark_path is not None:
            self.original_image = Image.open(self.pre_encode_image_path)
            self.watermark = Image.open(self.watermark_path)

            image_data = ImageData(self.original_image)
            image_data.lsb_encode(
                ImageComponent(self.selected_component),
                self.watermark,
                self.selected_depth,
            )
            self.new_image = image_data.rgb2image()

            psnr = ImagePSNR.calculate_psnr(self.original_image, self.new_image)
            self.psnr_label.setText(f"Encoded Image PSNR: {psnr:.2f}%")
            self.psnr_label.show()

            imageqt = ImageQt(self.new_image)
            pixmap = QPixmap.fromImage(imageqt).copy()
            self.new_image_field.setFixedSize(pixmap.size())
            self.new_image_field.setPixmap(pixmap)
            self.new_image_field.show()
            self.new_image_button.show()

    def decode(self):
        if self.pre_decode_image_path is not None:
            self.original_image = Image.open(self.pre_decode_image_path)
            image_data = ImageData(self.original_image)
            self.new_image = image_data.lsb_decode(
                ImageComponent(self.selected_component),
                self.selected_depth,
            )

            imageqt = ImageQt(self.new_image)
            pixmap = QPixmap.fromImage(imageqt).copy()
            self.new_image_field.setFixedSize(pixmap.size())
            self.new_image_field.setPixmap(pixmap)
            self.new_image_field.show()
            self.new_image_button.show()

    def save_image(self):
        try:
            name = QFileDialog.getSaveFileName(
                self,
                "Save File",
                filter="Images (*.ico *.jp2 *.jpg *.jpm *.jpx *.png *.tiff *.webp *.xpm)",
            )
            self.new_image.save(name[0], subsampling=0, quality=100)
        except ValueError:
            pass


class AttackTab(QWidget):
    original_image_path: str = ""
    original_image: Image = None
    new_image: Image = None
    image_quality = 0
    rotate_angle = 0
    size_percentage = 0
    selected_flip = "horizontal"

    def __init__(self):
        QWidget.__init__(self)

        self.pagelayout = QGridLayout()
        self.imagelayout = QGridLayout()
        self.jpeglayout = QGridLayout()
        self.rotatelayout = QGridLayout()
        self.sizelayout = QGridLayout()
        self.fliplayout = QGridLayout()

        self.imageframe = QFrame()
        self.jpegframe = QFrame()
        self.rotateframe = QFrame()
        self.sizeframe = QFrame()
        self.flipframe = QFrame()

        self.original_image_field = QLabel()
        self.original_image_label = QLabel()
        self.select_image_button = QPushButton("Select Image")

        self.jpeg_label = QLabel("JPEG Compression")
        self.quality_label = QLabel("Quality: 0")
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_button = QPushButton("Set")

        self.rotate_label = QLabel("Rotate by 0 degrees")
        self.rotate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotate_button = QPushButton("Set")

        self.size_label = QLabel("Resize to 0%")
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_button = QPushButton("Set")

        self.flip_label = QLabel("Flip image")
        self.flip_combo = QComboBox()
        self.flip_button = QPushButton("Set")

        self.new_image_field = QLabel()
        self.new_image_button = QPushButton("Save")

        self.set_properties()

    def set_properties(self):
        self.imageframe.setFrameShape(QFrame.Shape.StyledPanel)
        self.jpegframe.setFrameShape(QFrame.Shape.StyledPanel)
        self.rotateframe.setFrameShape(QFrame.Shape.StyledPanel)
        self.sizeframe.setFrameShape(QFrame.Shape.StyledPanel)
        self.flipframe.setFrameShape(QFrame.Shape.StyledPanel)
        self.imageframe.setLayout(self.imagelayout)
        self.jpegframe.setLayout(self.jpeglayout)
        self.rotateframe.setLayout(self.rotatelayout)
        self.sizeframe.setLayout(self.sizelayout)
        self.flipframe.setLayout(self.fliplayout)

        self.select_image_button.clicked.connect(self.open_file)
        self.quality_slider.setMinimum(0)
        self.quality_slider.setMaximum(100)
        self.quality_slider.valueChanged.connect(self.on_quality_slider_changed)
        self.quality_button.clicked.connect(self.compress)
        self.rotate_slider.setMinimum(0)
        self.rotate_slider.setMaximum(90)
        self.rotate_slider.valueChanged.connect(self.on_angle_slider_changed)
        self.rotate_button.clicked.connect(self.rotate)
        self.size_slider.setMinimum(0)
        self.size_slider.setMaximum(100)
        self.size_slider.valueChanged.connect(self.on_size_slider_changed)
        self.size_button.clicked.connect(self.resize)
        self.flip_combo.addItems(["Horizontal", "Vertical"])
        self.flip_combo.activated.connect(self.on_combobox_activated)
        self.flip_button.clicked.connect(self.flip)
        self.new_image_button.clicked.connect(self.save_image)

        self.imagelayout.addWidget(self.select_image_button, 0, 0)
        self.imagelayout.addWidget(self.original_image_field, 1, 0)
        self.imagelayout.addWidget(
            self.original_image_label, 2, 0, Qt.AlignmentFlag.AlignCenter
        )
        self.jpeglayout.addWidget(self.jpeg_label, 0, 0)
        self.jpeglayout.addWidget(self.quality_label, 1, 0)
        self.jpeglayout.addWidget(self.quality_slider, 2, 0)
        self.jpeglayout.addWidget(self.quality_button, 3, 0)

        self.rotatelayout.addWidget(self.rotate_label, 0, 0)
        self.rotatelayout.addWidget(self.rotate_slider, 1, 0)
        self.rotatelayout.addWidget(self.rotate_button, 2, 0)

        self.sizelayout.addWidget(self.size_label, 0, 0)
        self.sizelayout.addWidget(self.size_slider, 1, 0)
        self.sizelayout.addWidget(self.size_button, 2, 0)

        self.fliplayout.addWidget(self.flip_label, 0, 0)
        self.fliplayout.addWidget(self.flip_combo, 1, 0)
        self.fliplayout.addWidget(self.flip_button, 2, 0)

        self.pagelayout.addWidget(self.imageframe, 0, 0)
        self.pagelayout.addWidget(self.jpegframe, 1, 0)
        self.pagelayout.addWidget(self.rotateframe, 2, 0)
        self.pagelayout.addWidget(self.sizeframe, 3, 0)
        self.pagelayout.addWidget(self.flipframe, 4, 0)
        self.pagelayout.addWidget(self.new_image_field, 0, 1, 2, 1)
        self.pagelayout.addWidget(self.new_image_button, 2, 1, 1, 1)
        self.new_image_field.hide()
        self.new_image_button.hide()

        self.setLayout(self.pagelayout)

    def on_quality_slider_changed(self, index):
        self.image_quality = index
        self.quality_label.setText(f"Quality: {index}")

    def on_angle_slider_changed(self, index):
        self.rotate_angle = index
        self.rotate_label.setText(f"Rotate by {index} degrees")

    def on_size_slider_changed(self, index):
        self.size_percentage = index
        self.size_label.setText(f"Resize to {index}%")

    def on_combobox_activated(self, index):
        self.selected_flip = self.flip_combo.currentText().lower()

    def show_resized_image(
        self, component: QLabel, label: QLabel, pixmap: QPixmap, text: str, size: int
    ):
        component.clear()
        if pixmap.size().height() > size:
            pixmap = pixmap.scaledToHeight(size)
        if pixmap.size().width() > size:
            pixmap = pixmap.scaledToWidth(size)
        component.setFixedSize(size, size)
        component.setPixmap(pixmap)
        component.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setText(text)

    def open_file(self):
        result = QFileDialog.getOpenFileName(
            self,
            "Select File",
            filter="Images (*.ico *.jp2 *.jpg *.jpm *.jpx *.png *.tiff *.webp *.xpm)",
        )
        file_path = result[0]

        self.original_image_path = file_path
        self.original_image = Image.open(self.original_image_path)
        image_pixmap = QPixmap(self.original_image_path)
        self.show_resized_image(
            self.original_image_field,
            self.original_image_label,
            image_pixmap,
            os.path.basename(file_path),
            256,
        )

    def compress(self):
        if self.original_image_path != "":
            image_data = ImageData(self.original_image)
            image_data.jpeg_compress(self.image_quality)
            self.new_image = image_data.rgb2image()

            imageqt = ImageQt(self.new_image)
            pixmap = QPixmap.fromImage(imageqt).copy()
            self.new_image_field.setFixedSize(pixmap.size())
            self.new_image_field.setPixmap(pixmap)
            self.new_image_field.show()
            self.new_image_button.show()

    def rotate(self):
        if self.original_image_path != "":
            image_data = ImageData(self.original_image)
            image_data.image_rotate(self.rotate_angle)
            self.new_image = image_data.rgb2image()

            imageqt = ImageQt(self.new_image)
            pixmap = QPixmap.fromImage(imageqt).copy()
            self.new_image_field.setFixedSize(pixmap.size())
            self.new_image_field.setPixmap(pixmap)
            self.new_image_field.show()
            self.new_image_button.show()

    def resize(self):
        if self.original_image_path != "":
            image_data = ImageData(self.original_image)
            image_data.image_resize(self.size_percentage)
            self.new_image = image_data.rgb2image()

            imageqt = ImageQt(self.new_image)
            pixmap = QPixmap.fromImage(imageqt).copy()
            self.new_image_field.setFixedSize(pixmap.size())
            self.new_image_field.setPixmap(pixmap)
            self.new_image_field.show()
            self.new_image_button.show()

    def flip(self):
        if self.original_image_path != "":
            image_data = ImageData(self.original_image)
            image_data.image_flip(self.selected_flip)
            self.new_image = image_data.rgb2image()

            imageqt = ImageQt(self.new_image)
            pixmap = QPixmap.fromImage(imageqt).copy()
            self.new_image_field.setFixedSize(pixmap.size())
            self.new_image_field.setPixmap(pixmap)
            self.new_image_field.show()
            self.new_image_button.show()

    def save_image(self):
        try:
            name = QFileDialog.getSaveFileName(
                self,
                "Save File",
                filter="Images (*.ico *.jp2 *.jpg *.jpm *.jpx *.png *.tiff *.webp *.xpm)",
            )
            self.new_image.save(name[0], subsampling=0, quality=100)
        except ValueError:
            pass


app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec()
