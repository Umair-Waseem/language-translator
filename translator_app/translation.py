# ===================== TRANSLATION =====================
# Wraps deep-translator and provides the confidence helpers. GUI-free.

import re
import socket
import difflib
from deep_translator import GoogleTranslator
from .config import NOUN_CONTEXT_PHRASES, NOUN_MODE_MAX_CHARS, TRANSLATION_TIMEOUT
from .languages import to_google_code, AUTO


def apply_network_timeout():
    # deep-translator ignores a timeout argument, so enforce one at the socket level
    socket.setdefaulttimeout(TRANSLATION_TIMEOUT)


def _base_lang(code):
    return code.split("-")[0].lower()


def _translate_once(text, source, target):
    return GoogleTranslator(source=source, target=target).translate(text)


def translate(text, source_code, target_code, valid_codes, noun_mode=False):
    # resolve both codes to something Google accepts (source may fall back to auto)
    source = to_google_code(source_code, valid_codes) if source_code != AUTO else AUTO
    target = to_google_code(target_code, valid_codes)

    if noun_mode and len(text) < NOUN_MODE_MAX_CHARS:
        result = _translate_noun(text, source, target)
    else:
        result = _translate_once(text, source, target)

    return result, source, target


def _translate_noun(text, source, target):
    # bias short-word translations by embedding the word in a context phrase
    source_phrase = NOUN_CONTEXT_PHRASES.get(_base_lang(source), NOUN_CONTEXT_PHRASES["en"])
    translated = _translate_once(source_phrase.format(text=text), source, target)

    target_phrase = NOUN_CONTEXT_PHRASES.get(_base_lang(target), NOUN_CONTEXT_PHRASES["en"])
    prefix = target_phrase.split("{text}")[0].strip()
    if prefix and prefix in translated:
        return translated.replace(prefix, "").strip()

    # context could not be stripped cleanly, fall back to a plain translation
    return _translate_once(text, source, target)


def back_translate(text, source, target):
    # translate the result back to the original language to gauge round-trip quality
    return _translate_once(text, source, target)


def _normalize(text):
    text = re.sub(r"\s+", " ", text).strip().lower()
    return re.sub(r"[^\w\s]", "", text)


def confidence(original, back_translated):
    norm_original = _normalize(original)
    norm_back = _normalize(back_translated)
    ratio = difflib.SequenceMatcher(None, norm_original, norm_back).ratio()
    length_factor = min(1.0, len(norm_original) / 50)
    score = (ratio * 0.8 + length_factor * 0.2) * 100
    return min(100, max(0, int(score)))


def looks_untranslated(original, translated):
    # near-identical output usually means the pair was unsupported or text was symbolic
    ratio = difflib.SequenceMatcher(None, _normalize(original), _normalize(translated)).ratio()
    return ratio > 0.95
