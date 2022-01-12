import pytesseract

__all__ = ('SUPPORTED_OCR_LANGUAGES', 'SCRIPT_LANGUAGES', 'ALL_LANGUAGE')


def _supported_script_languages(script_dict: dict) -> dict:
    out_dict = {}

    for script, languages in script_dict.items():
        supported_languages = SUPPORTED_OCR_LANGUAGES.intersection(languages)
        if len(supported_languages) > 0:
            out_dict[script] = supported_languages

    return out_dict


SUPPORTED_OCR_LANGUAGES = set(pytesseract.get_languages())


SCRIPT_LANGUAGES = _supported_script_languages({
    'Cyrillic': ['rus', 'bel', 'srp', 'ukr', 'mkd', 'bul', 'aze_cyrl', 'uzb_cyrl'],
    'Latin': ['eng', 'cez']
})

ALL_LANGUAGE = '+'.join('+'.join(languages) for languages in SCRIPT_LANGUAGES.values())
