# ===================== CONSTANTS & CONFIGURATION =====================
import os
from langdetect import DetectorFactory

DEBOUNCE_TIME = 0.8
GRAMMAR_LANGUAGES = ['en'] 
MAX_TEXT_LENGTH = 5000
MAX_TRANSLATION_LENGTH = 15000
TRANSLATION_TIMEOUT = 30

# Enhanced font sizes for better readability
FONT_SIZE = 16
FONT_FAMILY = "Segoe UI" if os.name == 'nt' else "Roboto"
FONT = (FONT_FAMILY, FONT_SIZE)
BUTTON_FONT = (FONT_FAMILY, FONT_SIZE - 1)  # Button text size
HEADER_FONT = (FONT_FAMILY, FONT_SIZE + 2, "bold")  # Larger for headers
HISTORY_FILE = "translation_history.json"
MAX_HISTORY_SIZE = 100

# Updated Color Scheme - Dark Mode (calm, professional)
DARK_BG = "#1E1F29"
DARK_TEXT = "#FFFFFF"
DARK_BORDER = "#3A3D4D"
DARK_SCROLL_THUMB = "#8BE9FD"
DARK_SCROLL_TRACK = "#282A36"
DARK_BUTTON_PRIMARY = "#2ACE53" 
DARK_BUTTON_SECONDARY = "#26B3D2"
DARK_BUTTON_DANGER = "#FF6E6E"
DARK_HOVER = "#BD93F9"

# Updated Color Scheme - Light Mode (pleasant, soothing)
LIGHT_BG = "#F8FAFC"
LIGHT_TEXT = "#000000"
LIGHT_BORDER = "#CBD5E0"
LIGHT_SCROLL_THUMB = "#4C6EF5"
LIGHT_SCROLL_TRACK = "#EDF2F7"
LIGHT_BUTTON_PRIMARY = "#4C6EF5"
LIGHT_BUTTON_SECONDARY = "#3B82F6"
LIGHT_BUTTON_DANGER = "#E53E3E"
LIGHT_HOVER = "#5C7CFA"

# Language Configuration
DetectorFactory.seed = 0

SIMILAR_LANGUAGE_GROUPS = {
    'zh': ['zh-cn', 'zh-tw', 'zh'],
    'no': ['nb', 'nn'],
    'pt': ['pt-br', 'pt-pt'],
    'sr': ['sr-Cyrl', 'sr-Latn']
}

NOUN_CONTEXT_PHRASES = {
    "en": "Translate this noun: {text}",
    "es": "Traduce este sustantivo: {text}",
    "fr": "Traduisez ce nom: {text}",
    "de": "Übersetzen Sie dieses Substantiv: {text}",
    "it": "Traduci questo sostantivo: {text}",
    "ru": "Переведите это существительное: {text}",
    "ja": "この名詞を翻訳してください: {text}",
    "zh": "翻译这个名词: {text}",
    "ar": "ترجم هذا الاسم: {text}"
}
