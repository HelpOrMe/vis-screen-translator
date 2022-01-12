import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class TesseractMissingWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.resize(250, 100)
        self.setWindowTitle("Tesseract is missing!")
        self.label = QLabel(self)
        self.label.setText("Tesseract is missing!\n Please provide its installation path.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 11pt")

        geometry = self.geometry()
        geometry.setHeight(int(self.height() / 2))
        self.label.setGeometry(geometry)

        self.button = QPushButton("Select path", self)
        self.button.move(75, 50)
        self.button.clicked.connect(self.select_file)

        self.show()

    def select_file(self):
        path, ext = QFileDialog.getOpenFileName(self, "Select Tesseract", "C:/Program Files/", "*.exe")
        print(path)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = TesseractMissingWindow()
    app.exec()

