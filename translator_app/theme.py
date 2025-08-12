import customtkinter as ctk
from .config import (
    DARK_BG, LIGHT_BG,
    DARK_TEXT, LIGHT_TEXT,
    DARK_BORDER, LIGHT_BORDER,
    DARK_BUTTON_PRIMARY, LIGHT_BUTTON_PRIMARY,
    DARK_BUTTON_SECONDARY, LIGHT_BUTTON_SECONDARY,
    DARK_BUTTON_DANGER, LIGHT_BUTTON_DANGER,
    DARK_HOVER, LIGHT_HOVER,
    DARK_SCROLL_THUMB, LIGHT_SCROLL_THUMB
)

def get_actual_theme():
    theme = ctk.get_appearance_mode()
    return theme if theme in ["Light", "Dark"] else "Dark"

def get_current_theme():
    return get_actual_theme()

def get_bg_color():
    return DARK_BG if get_actual_theme() == "Dark" else LIGHT_BG

def get_text_color():
    return DARK_TEXT if get_actual_theme() == "Dark" else LIGHT_TEXT

def get_border_color():
    return DARK_BORDER if get_actual_theme() == "Dark" else LIGHT_BORDER

def get_button_primary():
    return DARK_BUTTON_PRIMARY if get_actual_theme() == "Dark" else LIGHT_BUTTON_PRIMARY

def get_button_secondary():
    return DARK_BUTTON_SECONDARY if get_actual_theme() == "Dark" else LIGHT_BUTTON_SECONDARY

def get_button_danger():
    return DARK_BUTTON_DANGER if get_actual_theme() == "Dark" else LIGHT_BUTTON_DANGER

def get_hover_color():
    return DARK_HOVER if get_actual_theme() == "Dark" else LIGHT_HOVER

def get_scroll_thumb_color():
    return DARK_SCROLL_THUMB if get_actual_theme() == "Dark" else LIGHT_SCROLL_THUMB

def get_secondary_text_color():
    return "#A1A1AA" if get_actual_theme() == "Dark" else "#0C0D0D"
