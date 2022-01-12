import re
import pytesseract
import langdetect

from dataclasses import dataclass

from .verify_tesseract import verify_tesseract_installed

verify_tesseract_installed()

from .languages import *
from vis.languages import LONG_LANGUAGE_CODES

__all__ = ('TextDocument', 'retrieve_text_document_quality', 'retrieve_text_document',
           'retrieve_text_document_fast', 'retrieve_text_with_lang',
           *languages.__all__)


@dataclass
class TextDocument:
    """ Structure for retrieved text """
    text: str
    lang: str


def retrieve_text_document_quality(image, context_image=None) -> TextDocument:
    """
    This method automatically detects the script and from it the languages. This helps to more clearly
    identify the language in the image. After that it works the same way as `retrieve_text_document()`.

    Should only be used for large images or with a context image as osd source.
    """

    if context_image is None:
        context_image = image

    # Try to get osd from a context image
    try:
        # Can raise TesseractError with too few characters
        # TODO: Save context_image manually with resolution meta
        osd = pytesseract.image_to_osd(context_image)
    except pytesseract.TesseractError:
        # Fallback
        return retrieve_text_document(image)

    script = re.search("Script: ([a-zA-Z]+)\n", osd).group(1)

    # We need all the script languages so that tesseract knows which alphabets to use to define the text
    script_languages = '+'.join(SCRIPT_LANGUAGES.get(script, 'eng'))

    return retrieve_text_document(image, script_languages)


def retrieve_text_document(image, default_lang=ALL_LANGUAGE) -> TextDocument:
    """
    Retrieves text with all possible languages, detects the exact language and retrieves the
    text again, but with the correct language.

    Should only be used for medium or large images
    """

    text = pytesseract.image_to_string(image, lang=default_lang)

    if len(text) == 0:
        return TextDocument(text="There is no text in the image!", lang='en')

    short_lang = langdetect.detect(text)
    long_lang = LONG_LANGUAGE_CODES.get(short_lang, None)

    if long_lang not in SUPPORTED_OCR_LANGUAGES:
        long_lang = default_lang

    # Retrieve again with correct language
    text = pytesseract.image_to_string(image, lang=long_lang)

    return TextDocument(text=text, lang=short_lang)


def retrieve_text_document_fast(image, default_lang=ALL_LANGUAGE) -> TextDocument:
    """ Retrieves text with all possible languages. """
    text = pytesseract.image_to_string(image, lang=default_lang)

    if len(text) == 0:
        return TextDocument(text="There is no text in the image!", lang='en')

    lang = langdetect.detect(text)
    return TextDocument(text=text, lang=lang)


def retrieve_text_with_lang(image, lang) -> str:
    return pytesseract.image_to_string(image, lang=lang)
