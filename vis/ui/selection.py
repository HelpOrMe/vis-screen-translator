from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from typing import Optional
from PIL import Image
from mss import mss

CACHE_IMAGE_NAME = "temp/screen.png"


class SelectionWindow(QWidget):
    enter_translation = pyqtSignal(QPoint, Image.Image)

    def __init__(self):
        super().__init__(None)

        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setFocusPolicy(Qt.StrongFocus)

        self.screen_image: Optional[Image.Image] = None
        self.selection_origin: Optional[QPoint] = None
        self.selection: Optional[Selection] = None

        self.setWindowFlag(Qt.FramelessWindowHint)
        self._init_as_frozen_screen()
        self._init_shortcuts()

        QApplication.setOverrideCursor(Qt.CrossCursor)

    def _init_as_frozen_screen(self):
        target_screen_number = QApplication.desktop().screenNumber(QCursor.pos())
        target_screen_geometry = QApplication.desktop().screen(target_screen_number).geometry()

        self.setGeometry(target_screen_geometry)

        with mss() as sct:
            # Take a screenshot of target screen and set it as background of the window

            screenshot = sct.grab(sct.monitors[target_screen_number + 1])
            self.screen_image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            darken_image = self.screen_image.point(lambda p: p * 0.5)
            darken_image.save(CACHE_IMAGE_NAME)

        self.setStyleSheet(f'background-image: url("{CACHE_IMAGE_NAME}");')

    def _init_shortcuts(self):
        self.__qs = QShortcut(QKeySequence("Escape"), self)
        self.__qs.activated.connect(self.close)

    def paintEvent(self, event: QPaintEvent):
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)

        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)

    def mousePressEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.selection = Selection(QRubberBand.Rectangle, self)
            self.selection_origin = event.pos()

            self.selection.setGeometry(QRect(self.selection_origin, QSize()))
            self.selection.show()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.selection.setGeometry(QRect(self.selection_origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event: QMouseEvent):
        rect: QRect = self.selection.geometry()
        box = (rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())

        origin = self.geometry().topLeft() + rect.topLeft()
        image = self.screen_image.crop(box)

        self.enter_translation.emit(origin, image)

    def close(self):
        QApplication.restoreOverrideCursor()
        super().close()


class Selection(QRubberBand):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.setStyle(QStyleFactory.create('windowsvista'))

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen()
        pen.setWidth(4)
        pen.setColor(QColor(Qt.white))
        painter.setPen(pen)

        painter.setBrush(QBrush(QColor(255, 255, 255, 10)))
        painter.drawRect(event.rect())
