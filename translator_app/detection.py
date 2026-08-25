# ===================== LANGUAGE DETECTION =====================
# Pure detection logic: no widgets are touched here, only text in -> result out.

from collections import namedtuple
from langdetect import detect_langs, LangDetectException, DetectorFactory
from .config import SHORT_TEXT_MIN, LANGUAGE_CODE_ALIASES
from .languages import AUTO

# deterministic langdetect results across runs
DetectorFactory.seed = 0

# code + the message shown next to the input box
Detection = namedtuple("Detection", "code message")

# script ranges checked first because they are reliable even for one character;
# Chinese is checked last so Japanese text with kanji is not mistaken for Chinese
_SCRIPT_RANGES = [
    ("ja", "Japanese", 0x3040, 0x30FF),     # Hiragana + Katakana (uniquely Japanese)
    ("ko", "Korean", 0xAC00, 0xD7A3),       # Hangul syllables (uniquely Korean)
    ("ar", "Arabic", 0x0600, 0x06FF),       # Arabic
    ("zh-CN", "Chinese", 0x4E00, 0x9FFF),   # CJK ideographs (shared, so checked last)
]


def _script_match(text):
    for code, name, low, high in _SCRIPT_RANGES:
        if any(low <= ord(ch) <= high for ch in text):
            return code, name
    return None


def _canonical(code):
    # map langdetect's code onto one Google Translate accepts
    return LANGUAGE_CODE_ALIASES.get(code.lower(), code)


def detect(text, code_to_name):
    text = text.strip()
    if not text:
        return Detection(AUTO, "")

    # scripts win over everything else and work at any length
    script = _script_match(text)
    if script:
        code, name = script
        return Detection(code, f"Detected: {name}")

    if not any(ch.isalpha() for ch in text):
        return Detection(AUTO, "Text contains only numbers/symbols")

    if len(text) < SHORT_TEXT_MIN:
        return Detection(AUTO, "Text too short for detection")

    try:
        results = detect_langs(text)
        if not results:
            return Detection(AUTO, "Detection failed")

        best = results[0]
        code = _canonical(best.lang)
        # the code is more useful than "Unknown" when the name list is the small fallback
        name = code_to_name.get(code, code)
        percent = f"{best.prob * 100:.1f}%"

        if best.prob < 0.5:
            return Detection(code, f"Detected: {name} (Low confidence: {percent})")
        return Detection(code, f"Detected: {name} ({percent})")
    except LangDetectException:
        return Detection(AUTO, "Detection error")
    except Exception as e:
        print(f"Detection error: {e}")
        return Detection(AUTO, "Detection failed")


def is_latin_text(text):
    # grammar checking only makes sense for Latin-script text
    return _script_match(text) is None
