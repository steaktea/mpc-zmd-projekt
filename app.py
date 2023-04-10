import os
import sys
from typing import List

from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt6.QtCore import QSize, Qt
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
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from image import ImageComponent, ImageData


class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle("Watermark Application")
        layout = QGridLayout()
        self.setLayout(layout)
        label1 = QLabel("Widget in Tab 1.")
        label2 = QLabel("Widget in Tab 2.")
        tabwidget = QTabWidget()
        tabwidget.addTab(LSBTab(), "LSB")
        tabwidget.addTab(DCTTab(), "DCT")
        tabwidget.addTab(AttackTab(), "ATTACKS")
        layout.addWidget(tabwidget, 0, 0)


class LSBTab(QWidget):
    pre_encode_image_path: str = ""
    pre_decode_image_path: str = ""
    new_image: Image = None
    watermark_path: str = ""
    selected_component = 0
    selected_depth = 0
    image_windows: List[Image.Image] = []

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
        self.pagelayout.addWidget(self.new_image_field, 0, 1, 2, 1)
        self.pagelayout.addWidget(self.new_image_button, 2, 1, 1, 1)
        self.new_image_field.hide()
        self.new_image_button.hide()

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
        name = QFileDialog.getSaveFileName(
            self,
            "Save File",
            filter="Images (*.ico *.jp2 *.jpg *.jpm *.jpx *.png *.tiff *.webp *.xpm)",
        )
        self.new_image.save(name[0])


class DCTTab(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.pagelayout = QGridLayout()

        self.set_properties()

    def set_properties(self):
        self.setLayout(self.pagelayout)


class AttackTab(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.pagelayout = QGridLayout()

        self.set_properties()

    def set_properties(self):
        self.setLayout(self.pagelayout)


app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec()
