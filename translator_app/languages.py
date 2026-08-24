# ===================== LANGUAGE SUPPORT =====================
# Builds the name<->code maps used by the UI and normalizes codes to
# ones Google Translate actually accepts.

from deep_translator import GoogleTranslator
from .config import LANGUAGE_CODE_ALIASES

AUTO_DETECT = "Auto Detect"
AUTO = "auto"

# Minimal offline set so the window still opens without a network connection
_FALLBACK_LANGUAGES = {
    "english": "en", "spanish": "es", "french": "fr", "german": "de",
    "italian": "it", "portuguese": "pt", "russian": "ru", "arabic": "ar",
    "chinese (simplified)": "zh-CN", "japanese": "ja", "korean": "ko",
    "hindi": "hi", "urdu": "ur",
}


def load_language_maps():
    # returns (code_to_name, name_to_code, name_list) with "Auto Detect" appended
    try:
        language_dict = GoogleTranslator().get_supported_languages(as_dict=True)
    except Exception as e:
        print(f"Could not fetch language list, using offline fallback: {e}")
        language_dict = dict(_FALLBACK_LANGUAGES)

    code_to_name = {code: name.title() for name, code in language_dict.items()}
    name_to_code = {name.title(): code for name, code in language_dict.items()}
    name_list = sorted(name_to_code) + [AUTO_DETECT]
    return code_to_name, name_to_code, name_list


def to_google_code(code, valid_codes):
    # map a detected/alias code onto a supported Google code, else auto-detect
    if not code:
        return AUTO
    canonical = LANGUAGE_CODE_ALIASES.get(code.lower(), code)
    return canonical if canonical in valid_codes else AUTO
