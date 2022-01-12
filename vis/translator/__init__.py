from deep_translator.exceptions import LanguageNotSupportedException
from deep_translator import GoogleTranslator

from .langauges import *


def translate(text: str, from_lang: str, to_lang: str):
    try:
        return GoogleTranslator(source=from_lang, target=to_lang).translate(text)
    except LanguageNotSupportedException:
        return "Language not supported!"
