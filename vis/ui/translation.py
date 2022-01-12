from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from typing import Optional
from PIL import Image

from vis.utils.colors import *
from vis.utils.tasks import *
from vis.ocr import *
from vis.translator import translate, SUPPORTED_TRANSLATOR_LANGUAGES
from vis.languages import SHORT_LANGUAGE_CODES, LONG_LANGUAGE_CODES

CACHE_IMAGE_NAME = 'temp/translation_image.png'


class TranslationWindowBase(QWidget):
    def __init__(self, origin: QPoint, image: Image.Image):
        super().__init__()

        image.save(CACHE_IMAGE_NAME)

        self.origin: QPoint = origin
        self.image: Image.Image = image

        self.dominant_colors: [tuple[int]] = get_dominant_colors(self.image)
        self.primal_color = self.dominant_colors[2]
        self.primal_color_str = ','.join(map(str, self.primal_color))
        self.text_color = (200, 200, 200) if is_dark_color(self.primal_color) else (35, 35, 35)
        self.text_color_str = ','.join(map(str, self.text_color))

        self.book_view: bool = image.width / image.height <= 2
        self.small: bool = min(self.image.width, self.image.height) < 100
        self.border_size = 2 if self.small else 4

        self.text_panel_size = self._calculate_text_panel_size()
        self.tools_panel_size = 20

        self.image_panel_rect: QRect = self._calculate_image_panel_rect()
        self.text_panel_rect: QRect = self._calculate_text_panel_rect()
        self.tools_panel_rect: QRect = self._calculate_tools_panel_rect()

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setGeometry(self._calculate_window_rect())
        self._init_style()
        self._init_shortcuts()

        self.image_panel: QLabel = self._init_image_panel()
        self.tools_panel: ToolsPanel = self._init_tools_panel()
        self.text_panel: TextPanel = self._init_text_panel()

        self.drag_prev_pos: Optional[QPoint] = None

    def _calculate_text_panel_size(self):
        w = self.image.width
        h = self.image.height

        return max(70, min(400, (w if self.book_view else h)))

    def _calculate_window_rect(self) -> QRect:
        w = self.image.width
        h = self.image.height

        if self.book_view:
            size = w + self.text_panel_size - self.border_size, h
        else:
            size = w, h + self.text_panel_size - self.border_size + self.tools_panel_size

        return QRect(self.origin, QSize(*size))

    def _calculate_image_panel_rect(self) -> QRect:
        return QRect(0, 0, *self.image.size)

    def _calculate_text_panel_rect(self) -> QRect:
        w = self.image_panel_rect.x() + self.image_panel_rect.width()
        h = self.image_panel_rect.y() + self.image_panel_rect.height()

        if self.book_view:
            return QRect(w - self.border_size, self.tools_panel_size,
                         self.text_panel_size, h - self.tools_panel_size)
        else:
            return QRect(0, h - self.border_size + self.tools_panel_size,
                         w, self.text_panel_size)

    def _calculate_tools_panel_rect(self) -> QRect:
        w = self.image_panel_rect.x() + self.image_panel_rect.width()
        h = self.image_panel_rect.y() + self.image_panel_rect.height()

        if self.book_view:
            return QRect(w - self.border_size, 0,
                         self.text_panel_size, self.tools_panel_size)
        else:
            return QRect(0, h - self.border_size,
                         w, self.tools_panel_size)

    def _init_style(self):
        self.setStyleSheet(f"""
            border: {self.border_size}px solid rgb({self.primal_color_str}); 
            background-color: rgb({self.primal_color_str});
            """)

    def _init_shortcuts(self):
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.close)

    def _init_image_panel(self) -> QLabel:
        background_image = QLabel(self)
        background_image.setGeometry(self.image_panel_rect)
        background_image.setPixmap(QPixmap("temp/translation_image.png"))

        return background_image

    def _init_tools_panel(self) -> 'ToolsPanel':
        panel = ToolsPanel(self, text_color_str=self.text_color_str)
        panel.setGeometry(self.tools_panel_rect)
        panel.setStyleSheet(f"background: rgb({self.primal_color_str});")

        return panel

    def _init_text_panel(self) -> 'TextPanel':
        scroll = QScrollArea(self)
        text_panel = TextPanel(self)

        scroll.setWidget(text_panel)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll.setStyleSheet("QScrollBar {height:0px; };")
        scroll.setStyleSheet("QLabel { border: 0; };")

        scroll.setGeometry(self.text_panel_rect)
        text_panel.setAlignment(Qt.AlignLeft)

        text_panel.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextEditorInteraction)
        text_panel.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        text_panel.setStyleSheet(f"color: rgb({self.text_color_str}); " +
                                 f"padding: {1 if self.small else 3}px; "
                                 f"font-size: {10 if self.small else 14}px; ")
        text_panel.setFont(QFont("Source Code Pro Medium"))

        return text_panel

    def paintEvent(self, event: QPaintEvent):
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)

        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)

    def mousePressEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.drag_prev_pos = event.globalPos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self.drag_prev_pos is not None:
            delta = event.globalPos() - self.drag_prev_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_prev_pos = event.globalPos()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_prev_pos = None


class TranslationWindow(TranslationWindowBase):
    _set_document_signal = pyqtSignal(TextDocument)

    def __init__(self, *args):
        super().__init__(*args)

        self._set_document_signal.connect(self._set_document)

        self._connect_panels()

        self.retrieved_text = ''
        self.retrieve_text_with_lang_detect()

    @property
    def shared_config(self) -> dict:
        return {"to_lang": self.tools_panel.to_lang}

    @shared_config.setter
    def shared_config(self, cfg):
        self.tools_panel.to_lang = cfg.get('to_lang', 'en')

    def _connect_panels(self):
        self.tools_panel.on_retrieving_mode_changed.connect(self._on_retrieving_mode_changed)
        self.tools_panel.on_from_lang_changed.connect(self._on_from_lang_changed)
        self.tools_panel.on_to_lang_changed.connect(self._on_to_lang_changed)

    def _on_retrieving_mode_changed(self, state):
        if state:
            self.text_panel.setText(self.retrieved_text)
        if not state:
            self.retrieved_text = self.text_panel.toPlainText()
            self.force_text_translation()

    def _on_from_lang_changed(self, lang):
        self.retrieved_text = retrieve_text_with_lang(self.image, LONG_LANGUAGE_CODES[lang])

        if self.tools_panel.text_retrieving_mode:
            self.text_panel.setText(self.retrieved_text)
        else:
            self.force_text_translation()

    def _on_to_lang_changed(self, _):
        if not self.tools_panel.text_retrieving_mode:
            self.force_text_translation()

    def force_text_translation(self):
        run_non_blocking(
            translate, (self.retrieved_text, self.tools_panel.from_lang, self.tools_panel.to_lang),
            self.text_panel.set_text_thread_safe)

    def retrieve_text_with_lang_detect(self):
        retrieve = (retrieve_text_document_fast if self.small else retrieve_text_document)
        run_non_blocking(retrieve, (self.image, ), self._set_document_signal.emit)

    def _set_document(self, document):
        self.retrieved_text = document.text
        self.text_panel.setText(document.text)
        self.tools_panel.from_lang = document.lang


class ToolsPanel(QWidget):
    on_retrieving_mode_changed = pyqtSignal(bool)
    on_from_lang_changed = pyqtSignal(str)
    on_to_lang_changed = pyqtSignal(str)

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args)

        self.text_color_str = kwargs.get("text_color_str", "255, 255, 255")

        self.from_lang_box: QComboBox = self._init_from_lang_box()
        self.to_lang_box: QComboBox = self._init_to_lang_box()
        self.retrieve_mode_button: QPushButton = self._init_retrieve_mode_button()

        self.text_retrieving_mode = True
        self.set_text_retrieving_mode(True)

    @property
    def from_lang(self) -> str:
        return self.from_lang_box.currentText()

    @from_lang.setter
    def from_lang(self, lang: str):
        index = self.from_lang_box.findText(lang)
        if index >= 0:
            self.from_lang_box.setCurrentIndex(index)

    @property
    def to_lang(self) -> str:
        return self.to_lang_box.currentText()

    @to_lang.setter
    def to_lang(self, lang: str):
        index = self.to_lang_box.findText(lang)
        if index >= 0:
            self.to_lang_box.setCurrentIndex(index)

    def _init_from_lang_box(self) -> QComboBox:
        from_lang_box = QComboBox(self)
        from_lang_box.setStyleSheet(
            "QComboBox::drop-down {border-width: 0px;} " + \
            "QComboBox::down-arrow {image: url(noimg); border-width: 0px;}" + \
            "QComboBox, QAbstractItemView{"+f"color: rgb({self.text_color_str})"+"};")

        from_lang_box.addItems([SHORT_LANGUAGE_CODES[lang] for lang in SUPPORTED_OCR_LANGUAGES])
        from_lang_box.view().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        from_lang_box.currentTextChanged.connect(self.on_from_lang_changed.emit)
        from_lang_box.move(4, 0)

        return from_lang_box

    def _init_to_lang_box(self) -> QComboBox:
        to_lang_box = QComboBox(self)
        to_lang_box.setStyleSheet(
            "QComboBox::drop-down {border-width: 0px;} " + \
            "QComboBox::down-arrow {image: url(noimg); border-width: 0px;}" + \
            "QComboBox, QAbstractItemView{ "+f"color: rgb({self.text_color_str})"+"};")

        to_lang_box.addItems(SUPPORTED_TRANSLATOR_LANGUAGES)
        to_lang_box.view().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        to_lang_box.currentTextChanged.connect(self.on_to_lang_changed.emit)
        to_lang_box.move(39, 0)

        return to_lang_box

    def _init_retrieve_mode_button(self) -> QPushButton:
        retrieve_mode_button = QPushButton(self)
        retrieve_mode_button.move(24, 2)
        retrieve_mode_button.setStyleSheet(f"color: rgb({self.text_color_str})")

        retrieve_mode_button.clicked.connect(self.switch_text_retrieving_mode)
        return retrieve_mode_button

    def switch_text_retrieving_mode(self):
        self.set_text_retrieving_mode(not self.text_retrieving_mode)

    def set_text_retrieving_mode(self, state):
        if state:
            self.retrieve_mode_button.setText("=")
            self.to_lang_box.hide()
        else:
            self.retrieve_mode_button.setText(">")
            self.to_lang_box.show()

        self.on_retrieving_mode_changed.emit(state)
        self.text_retrieving_mode = state


class TextPanel(QTextEdit):
    _set_text_signal = pyqtSignal(str)

    def __init__(self, *args):
        super().__init__(*args)

        self._set_text_signal.connect(self.setText)

    def set_text_thread_safe(self, text):
        self._set_text_signal.emit(text)
