from pytesseract import get_languages, TesseractNotFoundError

TESSERACT_PATH_FILE = "../tesseract_path.txt"


def verify_tesseract_installed():
    try:
        get_languages()
    except TesseractNotFoundError:
        print("Tesseract not installed!")
        exit()
