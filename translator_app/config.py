# ===================== CONSTANTS & CONFIGURATION =====================

# Timing
DEBOUNCE_MS = 800                 # delay before auto-detect / grammar runs while typing
TRANSLATION_TIMEOUT = 30          # seconds; enforced via a global socket timeout
TOOLTIP_TIMEOUT_MS = 5000         # auto-hide grammar tooltip after this long
TTS_MAX_WAIT_SECONDS = 60         # stop waiting on audio playback after this long

# Text limits (Google's free endpoint rejects input of 5000+ characters)
MAX_TRANSLATION_LENGTH = 5000     # reject input at or above this length
MAX_TEXT_LENGTH = 5000            # run grammar checking only below this length
NOUN_MODE_MAX_CHARS = 50          # noun mode only applies to short input
SHORT_TEXT_MIN = 3                # below this length detection is unreliable

# History
HISTORY_FILE = "translation_history.json"
MAX_HISTORY_SIZE = 100

# Fonts
FONT_SIZE = 16
FONT_FAMILY = "Segoe UI"          # Windows-native font; falls back automatically elsewhere
FONT = (FONT_FAMILY, FONT_SIZE)
BUTTON_FONT = (FONT_FAMILY, FONT_SIZE - 1)
HEADER_FONT = (FONT_FAMILY, FONT_SIZE + 2, "bold")
TITLE_FONT = (FONT_FAMILY, 24, "bold")
SUBTITLE_FONT = (FONT_FAMILY, 11)
LABEL_FONT = (FONT_FAMILY, 12, "bold")
SMALL_FONT = (FONT_FAMILY, 11)

# Color scheme - dark mode
DARK_BG = "#1E1F29"
DARK_TEXT = "#FFFFFF"
DARK_BORDER = "#3A3D4D"
DARK_SCROLL_THUMB = "#8BE9FD"
DARK_BUTTON_PRIMARY = "#2ACE53"
DARK_BUTTON_SECONDARY = "#26B3D2"
DARK_BUTTON_DANGER = "#FF6E6E"
DARK_HOVER = "#BD93F9"
DARK_SECONDARY_TEXT = "#A1A1AA"

# Color scheme - light mode
LIGHT_BG = "#F8FAFC"
LIGHT_TEXT = "#000000"
LIGHT_BORDER = "#CBD5E0"
LIGHT_SCROLL_THUMB = "#4C6EF5"
LIGHT_BUTTON_PRIMARY = "#4C6EF5"
LIGHT_BUTTON_SECONDARY = "#3B82F6"
LIGHT_BUTTON_DANGER = "#E53E3E"
LIGHT_HOVER = "#5C7CFA"
LIGHT_SECONDARY_TEXT = "#0C0D0D"

# Shared status colors
DANGER_HOVER = "#C0392B"
NEUTRAL_COLOR = "#95A5A6"
CONFIDENCE_HIGH = "#27AE60"       # >= 80%
CONFIDENCE_MEDIUM = "#F39C12"     # >= 50%
CONFIDENCE_LOW = "#E74C3C"        # < 50%

# Languages that grammar checking supports, mapped to their LanguageTool locale
GRAMMAR_LANGUAGES = {"en": "en-US"}

# langdetect emits a few codes Google Translate does not accept; map them
LANGUAGE_CODE_ALIASES = {
    "zh": "zh-CN",      # generic Chinese -> Simplified (Google has no plain 'zh')
    "zh-cn": "zh-CN",   # langdetect Simplified Chinese -> Google casing
    "zh-tw": "zh-TW",   # langdetect Traditional Chinese -> Google casing
    "he": "iw",         # langdetect Hebrew -> Google's 'iw'
}

# Context phrases used by noun mode to bias short-word translations
NOUN_CONTEXT_PHRASES = {
    "en": "Translate this noun: {text}",
    "es": "Traduce este sustantivo: {text}",
    "fr": "Traduisez ce nom: {text}",
    "de": "Übersetzen Sie dieses Substantiv: {text}",
    "it": "Traduci questo sostantivo: {text}",
    "ru": "Переведите это существительное: {text}",
    "ja": "この名詞を翻訳してください: {text}",
    "zh": "翻译这个名词: {text}",
    "ar": "ترجم هذا الاسم: {text}",
}
