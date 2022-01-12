import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from typing import Optional
from PIL import Image

from .selection import SelectionWindow
from .translation import TranslationWindow


_app: QApplication = QApplication(sys.argv)

font_db = QFontDatabase()
font_db.addApplicationFont("resources/font.ttf")


# Thanks to https://github.com/pytest-dev/pytest-qt/issues/25
class ExceptionHandler(QObject):
    errorSignal = pyqtSignal()

    def __init__(self):
        super(ExceptionHandler, self).__init__()

    def handler(self, exctype, value, traceback):
        self.errorSignal.emit()
        sys._excepthook(exctype, value, traceback)


# It fix exception propagation
exceptionHandler = ExceptionHandler()
sys._excepthook = sys.excepthook
sys.excepthook = exceptionHandler.handler


class WindowController(QObject):
    _enter_selection_window_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.selection_window: Optional[SelectionWindow] = None
        self.translation_window: Optional[TranslationWindow] = None

    def enter_selection_window(self):
        if self.translation_window is not None:
            self.translation_window.close()

        self.selection_window = SelectionWindow()
        self.selection_window.enter_translation.connect(self.open_translation_window)
        self.selection_window.show()

    def open_translation_window(self, origin: QPoint, image: Image.Image):
        shared_config = {}

        if self.translation_window is not None:
            shared_config = self.translation_window.shared_config

        self.translation_window = TranslationWindow(origin, image)
        self.translation_window.shared_config = shared_config

        self.selection_window.close()
        self.translation_window.show()

    def close_all(self):
        if self.selection_window is not None:
            self.selection_window.close()

        if self.translation_window is not None:
            self.translation_window.close()


class WindowControllerThreadSafe(WindowController):
    _enter_selection_window_signal = pyqtSignal()
    _open_translation_window_signal = pyqtSignal(QPoint, Image.Image)
    _close_all = pyqtSignal()

    def __init__(self):
        super().__init__()

        self._enter_selection_window_signal.connect(super().enter_selection_window)
        self._open_translation_window_signal.connect(super().open_translation_window)
        self._close_all.connect(super().close_all)

    def enter_selection_window(self):
        self._enter_selection_window_signal.emit()

    def open_translation_window(self, origin: QPoint, image: Image.Image):
        self._open_translation_window_signal.emit(origin, image)

    def close_all(self):
        self._close_all.emit()


def behave_as_daemon():
    _app.setQuitOnLastWindowClosed(False)


def run():
    _app.exec()


def quit():
    _app.quit()
