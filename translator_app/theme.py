# ===================== THEME COLORS =====================
# Thin accessors that return the right color for the active appearance mode.

import customtkinter as ctk
from .config import (
    DARK_BG, LIGHT_BG,
    DARK_TEXT, LIGHT_TEXT,
    DARK_BORDER, LIGHT_BORDER,
    DARK_BUTTON_PRIMARY, LIGHT_BUTTON_PRIMARY,
    DARK_BUTTON_SECONDARY, LIGHT_BUTTON_SECONDARY,
    DARK_BUTTON_DANGER, LIGHT_BUTTON_DANGER,
    DARK_HOVER, LIGHT_HOVER,
    DARK_SCROLL_THUMB, LIGHT_SCROLL_THUMB,
    DARK_SECONDARY_TEXT, LIGHT_SECONDARY_TEXT,
    CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CONFIDENCE_LOW,
)


def get_actual_theme():
    # customtkinter resolves "System" to "Light"/"Dark"; default to Dark otherwise
    theme = ctk.get_appearance_mode()
    return theme if theme in ["Light", "Dark"] else "Dark"


def _pick(dark_color, light_color):
    return dark_color if get_actual_theme() == "Dark" else light_color


def get_bg_color():
    return _pick(DARK_BG, LIGHT_BG)


def get_text_color():
    return _pick(DARK_TEXT, LIGHT_TEXT)


def get_border_color():
    return _pick(DARK_BORDER, LIGHT_BORDER)


def get_button_primary():
    return _pick(DARK_BUTTON_PRIMARY, LIGHT_BUTTON_PRIMARY)


def get_button_secondary():
    return _pick(DARK_BUTTON_SECONDARY, LIGHT_BUTTON_SECONDARY)


def get_button_danger():
    return _pick(DARK_BUTTON_DANGER, LIGHT_BUTTON_DANGER)


def get_hover_color():
    return _pick(DARK_HOVER, LIGHT_HOVER)


def get_scroll_thumb_color():
    return _pick(DARK_SCROLL_THUMB, LIGHT_SCROLL_THUMB)


def get_secondary_text_color():
    return _pick(DARK_SECONDARY_TEXT, LIGHT_SECONDARY_TEXT)


def get_confidence_color(confidence):
    # green / orange / red band for a 0-100 confidence score
    if confidence >= 80:
        return CONFIDENCE_HIGH
    if confidence >= 50:
        return CONFIDENCE_MEDIUM
    return CONFIDENCE_LOW
