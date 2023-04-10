import os
import sys
from typing import List

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
    QMainWindow,
    QPushButton,
    QRadioButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from image import ImageComponent, ImageData


class ImageWindow(QMainWindow):
    def __init__(self, image: Image, title):
        super().__init__()
        self.setWindowTitle(title)

        self.image = image.convert("RGB")

        widget = QWidget()
        widget_layout = QVBoxLayout()
        image_field = QLabel()
        save_button = QPushButton("Save")

        imageqt = ImageQt(self.image)
        pixmap = QPixmap.fromImage(imageqt).copy()
        image_field.setPixmap(pixmap)

        save_button.clicked.connect(self.save_file)

        widget_layout.addWidget(image_field)
        widget_layout.addWidget(save_button)

        widget.setLayout(widget_layout)
        self.setCentralWidget(widget)

    def save_file(self):
        name = QFileDialog.getSaveFileName(
            self,
            "Save File",
            filter="Images (*.ico *.jp2 *.jpg *.jpm *.jpx *.png *.tiff *.webp *.xpm)",
        )
        self.image.save(name[0])


class MainWindow(QMainWindow):
    original_image_path: str = ""
    new_image: Image = None
    watermark_path: str = ""
    selected_component = 0
    selected_depth = 0
    image_windows: List[Image.Image] = []

    def __init__(self):
        super().__init__()
        self.setWindowTitle("WatermarkApp")

        self.widget = QWidget()
        self.applayout = QVBoxLayout()
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
        self.encode_image_label = QLabel()
        self.watermark_button = QPushButton("Select Watermark")
        self.watermark_label = QLabel()
        self.encode_button = QPushButton("Encode")
        self.decode_image_button = QPushButton("Select Image")
        self.decode_image_label = QLabel()
        self.decode_button = QPushButton("Decode")

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
        self.encode_image_button.clicked.connect(self.open_file)
        self.decode_image_button.clicked.connect(self.open_file)
        self.watermark_button.clicked.connect(self.open_file)
        self.encode_radio.toggled.connect(self.on_radio_selected)
        self.decode_radio.toggled.connect(self.on_radio_selected)
        self.encode_button.clicked.connect(self.encode)
        self.decode_button.clicked.connect(self.decode)

        self.toplayout.addWidget(self.rgb_label, 0, 0)
        self.toplayout.addWidget(self.rgb_combobox, 1, 0)
        self.toplayout.addWidget(self.depth_label, 0, 1)
        self.toplayout.addWidget(self.depth_slider, 1, 1)
        self.toplayout.addWidget(self.encode_radio, 2, 0)
        self.toplayout.addWidget(self.decode_radio, 2, 1)

        self.encodelayout.addWidget(self.encode_image_button, 0, 0)
        self.encodelayout.addWidget(self.watermark_button, 0, 1)
        self.encodelayout.addWidget(self.encode_image_label, 1, 0)
        self.encodelayout.addWidget(self.watermark_label, 1, 1)
        self.encodelayout.addWidget(self.encode_button, 2, 0, 1, 2)

        self.decodelayout.addWidget(self.decode_image_button, 0, 0)
        self.decodelayout.addWidget(self.decode_image_label, 0, 1)
        self.decodelayout.addWidget(self.decode_button, 1, 0, 1, 2)

        self.pagelayout.addWidget(self.topframe)
        self.pagelayout.addWidget(self.encodeframe)
        self.pagelayout.addWidget(self.decodeframe)

        self.applayout.addLayout(self.pagelayout)

        self.widget.setLayout(self.applayout)
        self.setCentralWidget(self.widget)

    def on_radio_selected(self):
        radio_button = self.sender()

        if radio_button.isChecked():
            match radio_button.text():
                case "Encode":
                    self.decodeframe.hide()
                    self.encodeframe.show()
                case "Decode":
                    self.encodeframe.hide()
                    self.decodeframe.show()
                case _:
                    raise ValueError("Invalid RadioButton text")

    def on_combobox_activated(self, index):
        self.selected_component = index

    def on_slider_changed(self, index):
        self.selected_depth = index
        self.depth_label.setText(f"Watermark depth: {index}")

    def open_file(self):
        push_button = self.sender()
        result = QFileDialog.getOpenFileName(
            self,
            "Select File",
            filter="Images (*.ico *.jp2 *.jpg *.jpm *.jpx *.png *.tiff *.webp *.xpm)",
        )
        file_path = result[0]

        match push_button.text():
            case "Select Image":
                self.encode_image_label.setText(os.path.basename(file_path))
                self.decode_image_label.setText(os.path.basename(file_path))
                self.original_image_path = file_path
            case "Select Watermark":
                self.watermark_label.setText(os.path.basename(file_path))
                self.watermark_path = file_path
            case _:
                raise ValueError("Invalid PushButton text")

    def encode(self):
        if self.original_image_path is not None and self.watermark_path is not None:
            self.original_image = Image.open(self.original_image_path)
            self.watermark = Image.open(self.watermark_path)

            image_data = ImageData(self.original_image)
            image_data.lsb_encode(
                ImageComponent(self.selected_component),
                self.watermark,
                self.selected_depth,
            )

            w1 = ImageWindow(image_data.original_image, title="Original")
            self.image_windows.append(w1)
            w1.show()
            w2 = ImageWindow(image_data.rgb2image(), title="Watermarked")
            self.image_windows.append(w2)
            w2.show()

    def decode(self):
        if self.original_image_path is not None:
            self.original_image = Image.open(self.original_image_path)
            image_data = ImageData(self.original_image)
            extracted = image_data.lsb_decode(
                ImageComponent(self.selected_component),
                self.selected_depth,
            )

            w1 = ImageWindow(self.original_image, title="Original")
            w2 = ImageWindow(extracted, title="Extracted")
            self.image_windows.append(w1)
            self.image_windows.append(w2)
            w1.show()
            w2.show()


app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec()
