# ===================== SHARED STATE & ONE-TIME INITIALIZATION =====================
import os
import re
import difflib
import customtkinter as ctk
import threading
import pygame
import concurrent.futures
from langdetect import detect_langs, LangDetectException
from deep_translator import GoogleTranslator
from datetime import datetime
import tkinter as tk
import language_tool_python

from .theme import get_bg_color, get_text_color, get_border_color
import json
from .config import (
    # fonts & sizes used in UI
    FONT_FAMILY, FONT_SIZE, FONT, BUTTON_FONT, HEADER_FONT,
    # limits/timeouts
    MAX_TEXT_LENGTH, MAX_TRANSLATION_LENGTH, TRANSLATION_TIMEOUT,
    # language helpers
    SIMILAR_LANGUAGE_GROUPS, NOUN_CONTEXT_PHRASES,
    # history file constants (if used here)
    HISTORY_FILE, MAX_HISTORY_SIZE
)

from .theme import (
    get_bg_color, get_text_color, get_border_color,
    get_button_primary, get_button_secondary, get_button_danger,
    get_hover_color, get_secondary_text_color
)

import time
from gtts import gTTS
from .config import DEBOUNCE_TIME
from .theme import (
    get_bg_color, get_text_color, get_border_color,
    get_button_primary, get_button_secondary, get_button_danger,
    get_hover_color, get_scroll_thumb_color, get_secondary_text_color,
    get_actual_theme

)
from .language_support import initialize_language_support


# --------------------- Global flags & locks (unchanged names) ---------------------
cancelled = False
translation_lock = threading.Lock()
translation_history = []
debounce_timer = None
grammar_timer = None
active_tooltip = None

# --------------------- Initialize pygame (same place in lifecycle) ----------------
pygame.init()

# --------------------- Thread pool (unchanged settings) --------------------------
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# --------------------- Main application (same properties as original) ------------
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.title("Language Translator")
app.geometry("950x600")
app.minsize(950, 600)
app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(1, weight=1)

# --------------------- Global UI references (preserve names; assigned later) -----
header = None
title_label = None
subtitle_label = None
appearance_switch = None
clear_btn = None
input_label = None
output_label = None
lang_frame = None
source_combo = None
target_combo = None
noun_mode = None
input_box = None
output_box = None
char_count_label = None
detect_btn = None
copy_btn = None
input_scrollbar = None
output_scrollbar = None
translate_btn = None
cancel_btn = None
tts_input_btn = None
tts_output_btn = None
history_btn = None
status_frame = None
detected_lang_label = None
confidence_label = None
progress_bar = None
confidence_bar = None
input_text_container = None
output_text_container = None
source_label = None
target_label = None
noun_toggle = None
swap_btn = None

# Language support maps are created later during initialization; define placeholders
code_to_name = None
name_to_code = None
name_list = None

# Main content frame placeholder
main_frame = None

def cleanup_resources():
    global cancelled
    cancelled = True
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    thread_pool.shutdown(wait=False, cancel_futures=True)
    for filename in os.listdir():
        if filename.startswith("tts_") and filename.endswith(".mp3"):
            try:
                os.remove(filename)
            except:
                pass

def is_identical_translation(original, translated):
    norm_original = re.sub(r'\s+', ' ', original).strip().lower()
    norm_translated = re.sub(r'\s+', ' ', translated).strip().lower()
    norm_original = re.sub(r'[^\w\s]', '', norm_original)
    norm_translated = re.sub(r'[^\w\s]', '', norm_translated)
    matcher = difflib.SequenceMatcher(None, norm_original, norm_translated)
    return matcher.ratio() > 0.95

def calculate_confidence(original, back_translated):
    def normalize(text):
        text = re.sub(r'\s+', ' ', text).strip().lower()
        return re.sub(r'[^\w\s]', '', text)
    
    norm_original = normalize(original)
    norm_back = normalize(back_translated)
    matcher = difflib.SequenceMatcher(None, norm_original, norm_back)
    ratio = matcher.ratio()
    length_factor = min(1.0, len(norm_original) / 50)
    confidence = (ratio * 0.8 + length_factor * 0.2) * 100
    return min(100, max(0, int(confidence)))

def detect_language():
    input_text = input_box.get("1.0", "end-1c").strip()
    
    if not input_text:
        detected_lang_label.configure(text="")
        return 'auto'
    
    # Improved detection for short text
    if len(input_text) < 3:
        try:
            # Special handling for CJK characters
            if any('\u4e00' <= char <= '\u9fff' for char in input_text):  # Chinese
                detected_lang_label.configure(text="Detected: Chinese")
                return 'zh'
            if any('\u3040' <= char <= '\u309f' for char in input_text):  # Hiragana
                detected_lang_label.configure(text="Detected: Japanese")
                return 'ja'
            if any('\u30a0' <= char <= '\u30ff' for char in input_text):  # Katakana
                detected_lang_label.configure(text="Detected: Japanese")
                return 'ja'
            if any('\uac00' <= char <= '\ud7a3' for char in input_text):  # Hangul
                detected_lang_label.configure(text="Detected: Korean")
                return 'ko'
            if any('\u0600' <= char <= '\u06ff' for char in input_text):  # Arabic
                detected_lang_label.configure(text="Detected: Arabic")
                return 'ar'
        except:
            pass
        detected_lang_label.configure(text="Text too short for detection")
        return 'auto'
    
    # Skip detection for numeric/symbol-only content
    if not any(char.isalpha() for char in input_text):
        detected_lang_label.configure(text="Text contains only numbers/symbols")
        return 'auto'
    
    try:
        # Use GoogleTranslator for better accuracy on short text
        if len(input_text) < 10:
            lang_code = GoogleTranslator().detect(input_text)
            lang_name = code_to_name.get(lang_code, "Unknown")
            detected_lang_label.configure(text=f"Detected: {lang_name}")
            return lang_code
        
        # Use langdetect for longer text
        detections = detect_langs(input_text)
        if not detections:
            detected_lang_label.configure(text="Detection Failed")
            return 'auto'
        
        best_detection = detections[0]
        lang_code = best_detection.lang
        confidence = best_detection.prob
        
        # Handle similar language groups
        for base_lang, variants in SIMILAR_LANGUAGE_GROUPS.items():
            if lang_code in variants:
                lang_code = base_lang
                break
        
        # Special case for Chinese
        if lang_code in ['zh-cn', 'zh-tw']:
            lang_code = 'zh'
            lang_name = "Chinese"
        else:
            lang_name = code_to_name.get(lang_code, "Unknown")
            
        conf_text = f"{confidence*100:.1f}%"
        
        if confidence < 0.5:
            detected_lang_label.configure(text=f"Detected: {lang_name} (Low confidence: {conf_text})")
        else:
            detected_lang_label.configure(text=f"Detected: {lang_name} ({conf_text})")
            
        return lang_code
        
    except LangDetectException:
        detected_lang_label.configure(text="Detection Error")
        return 'auto'
    except Exception as e:
        print(f"Detection error: {e}")
        detected_lang_label.configure(text="Detection Failed")
        return 'auto'

def translate_text():
    global cancelled
    cancelled = False
    
    input_text = input_box.get("1.0", "end-1c").strip()
    
    # Add input sanitization
    input_text = re.sub(r'\s+', ' ', input_text).strip()
    char_count = len(input_text)
    
    # Skip translation for non-text content
    if not input_text:
        return
    elif not any(char.isalpha() for char in input_text):
        show_error("No translatable text found (only numbers/symbols)")
        return
    elif char_count > MAX_TRANSLATION_LENGTH:
        show_error(f"Text too long (max {MAX_TRANSLATION_LENGTH} chars)")
        return
        
    target_lang = target_combo.get()
    source_lang = source_combo.get()
    
    if source_lang == "Auto Detect":
        source_lang_code = detect_language()
        if source_lang_code == 'auto' or not source_lang_code:
            source_lang_code = 'auto'
    else:
        source_lang_code = name_to_code.get(source_lang, 'auto')
    
    if not target_lang or target_lang == "Auto Detect":
        output_box.configure(state="normal")
        output_box.delete("1.0", "end")
        output_box.insert("1.0", "Please select a target language")
        output_box.configure(state="disabled")
        return
    
    target_code = name_to_code.get(target_lang)
    if not target_code:
        return

    progress_bar.start()
    translate_btn.configure(state="disabled")
    cancel_btn.configure(state="normal")
    char_count_label.configure(text=f"Chars: {char_count}")
    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    output_box.insert("1.0", "Translating...")
    app.update_idletasks()
    
    def translation_worker():
        global cancelled
        try:
            # Enhanced noun translation using context phrases
            if noun_mode.get() == 1 and char_count < 50:
                # Handle Chinese variants
                if source_lang_code in ['zh-cn', 'zh-tw']:
                    source_lang_code_used = 'zh'
                else:
                    source_lang_code_used = source_lang_code
                    
                if target_code in ['zh-cn', 'zh-tw']:
                    target_code_used = 'zh'
                else:
                    target_code_used = target_code
                
                context_phrase = NOUN_CONTEXT_PHRASES.get(source_lang_code_used, NOUN_CONTEXT_PHRASES["en"])
                context_text = context_phrase.format(text=input_text)
                
                # Translate context phrase
                translated = GoogleTranslator(
                    source=source_lang_code_used, 
                    target=target_code_used
                ).translate(context_text, timeout=TRANSLATION_TIMEOUT)
                
                if cancelled:
                    app.after(0, lambda: show_error("Translation cancelled"))
                    return
                
                # Extract the translated noun by removing the context phrase
                context_target = NOUN_CONTEXT_PHRASES.get(target_code_used, NOUN_CONTEXT_PHRASES["en"])
                if context_target in translated:
                    translated = translated.replace(context_target, "").strip()
                else:
                    # Fallback to standard translation if context removal fails
                    translated = GoogleTranslator(
                        source=source_lang_code_used, 
                        target=target_code_used
                    ).translate(input_text, timeout=TRANSLATION_TIMEOUT)
            else:
                # Standard translation
                if source_lang_code in ['zh-cn', 'zh-tw']:
                    source_lang_code_used = 'zh'
                else:
                    source_lang_code_used = source_lang_code
                    
                if target_code in ['zh-cn', 'zh-tw']:
                    target_code_used = 'zh'
                else:
                    target_code_used = target_code
                
                translated = GoogleTranslator(
                    source=source_lang_code_used, 
                    target=target_code_used
                ).translate(input_text, timeout=TRANSLATION_TIMEOUT)
            
            if cancelled:
                app.after(0, lambda: show_error("Translation cancelled"))
                return
                
            if not translated or translated.strip() == "":
                app.after(0, lambda: show_error("Empty translation result"))
                return
                
            if is_identical_translation(input_text, translated):
                app.after(0, lambda: show_error("Translation identical to input"))
                return
            
            confidence = -1
            back_translation_failed = False
            
            if char_count <= MAX_TEXT_LENGTH and char_count > 0:
                try:
                    back_translated = GoogleTranslator(
                        source=target_code_used, 
                        target=source_lang_code_used
                    ).translate(translated, timeout=TRANSLATION_TIMEOUT)
                    
                    if cancelled:
                        app.after(0, lambda: show_error("Translation cancelled"))
                        return
                    
                    if not back_translated or back_translated.strip() == "":
                        back_translation_failed = True
                    else:
                        confidence = calculate_confidence(input_text, back_translated)
                except Exception as e:
                    back_translation_failed = True
                    print(f"Back translation error: {e}")
            else:
                confidence = -1
                
            history_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": f"{source_lang} ({source_lang_code})",
                "target": f"{target_lang} ({target_code})",
                "original": input_text,
                "translated": translated,
                "confidence": confidence,
                "noun_mode": noun_mode.get() == 1
            }
            save_to_history(history_entry)
            
            app.after(0, lambda: update_translation_result(
                translated, 
                confidence, 
                back_translation_failed,
                target_code_used
            ))
            
        except Exception as e:
            error_msg = str(e)
            if "timed out" in error_msg.lower():
                error_msg = "Translation timed out. Try shorter text."
            elif "connection" in error_msg.lower():
                error_msg = "Network error. Check your internet connection."
            elif "too many requests" in error_msg.lower():
                error_msg = "API limit exceeded. Please wait before trying again."
            else:
                error_msg = f"Translation failed: {e}"
            app.after(0, lambda: show_error(f"Error: {error_msg}"))
        finally:
            app.after(0, lambda: [progress_bar.stop(), 
                                  progress_bar.set(0),
                                  translate_btn.configure(state="normal"),
                                  cancel_btn.configure(state="disabled")])
    
    with translation_lock:
        thread_pool.submit(translation_worker)

def update_translation_result(translated, confidence, back_translation_failed, target_code):
    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    output_box.insert("1.0", translated)
    output_box.configure(state="disabled")
    
    if confidence == -1:
        confidence_label.configure(text="Confidence: Not calculated for long texts")
        confidence_bar.set(0)
        confidence_bar.configure(progress_color="#95A5A6")
    elif back_translation_failed:
        confidence_label.configure(text="Confidence: Back-translation failed")
        confidence_bar.set(0)
        confidence_bar.configure(progress_color="#95A5A6")
    else:
        confidence_label.configure(text=f"Confidence: {confidence}%")
        color = (
            "#27AE60" if confidence >= 80 else
            "#F39C12" if confidence >= 50 else
            "#E74C3C"
        )
        confidence_bar.set(confidence / 100)
        confidence_bar.configure(progress_color=color)
    
    if len(translated) <= MAX_TEXT_LENGTH:
        grammar_tool = get_grammar_tool(target_code)
        if grammar_tool:
            underline_mistakes(output_box, translated, target_code)

def show_error(message):
    print(f"ERROR: {message}")
    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    output_box.insert("1.0", message)
    output_box.configure(state="disabled")
    translate_btn.configure(state="normal")
    cancel_btn.configure(state="disabled")
    progress_bar.stop()
    progress_bar.set(0)

# ===================== GRAMMAR CHECKING =====================
grammar_tools = {
    'en': language_tool_python.LanguageTool('en-US'),
}

def get_grammar_tool(lang_code):
    base_lang = lang_code.split('-')[0].lower()
    return grammar_tools.get(base_lang)

def clear_tooltip():
    global active_tooltip
    if active_tooltip:
        active_tooltip.destroy()
        active_tooltip = None

def underline_mistakes(text_widget, text, lang_code):
    if not text.strip() or len(text) > MAX_TEXT_LENGTH:
        return
        
    # Skip grammar check for non-text content
    if not any(char.isalpha() for char in text):
        return
        
    # Skip grammar check for non-Latin scripts
    if any('\u4e00' <= char <= '\u9fff' for char in text):  # Chinese
        return
    if any('\u3040' <= char <= '\u30ff' for char in text):  # Japanese
        return
    if any('\uac00' <= char <= '\ud7a3' for char in text):  # Korean
        return
    if any('\u0600' <= char <= '\u06ff' for char in text):  # Arabic
        return
        
    try:
        tool = get_grammar_tool(lang_code)
        if not tool:
            return
            
        text_widget.tag_remove("mistake", "1.0", "end")
        
        matches = tool.check(text)
        for match in matches:
            start = f"1.0 + {match.offset} chars"
            end = f"1.0 + {match.offset + match.errorLength} chars"
            text_widget.tag_add("mistake", start, end)

        text_widget.tag_config("mistake", underline=True, underlinefg="red")
        
        def show_tooltip(event):
            clear_tooltip()
            index = text_widget.index(f"@{event.x},{event.y}")
            
            for match in matches:
                start_idx = f"1.0 + {match.offset} chars"
                end_idx = f"1.0 + {match.offset + match.errorLength} chars"
                
                if text_widget.compare(index, ">=", start_idx) and text_widget.compare(index, "<=", end_idx):
                    global active_tooltip
                    active_tooltip = tk.Toplevel(app)
                    active_tooltip.wm_overrideredirect(True)
                    x = event.x_root + 15
                    y = event.y_root + 15
                    active_tooltip.wm_geometry(f"+{int(x)}+{int(y)}")
                    
                    bg_color = get_bg_color()
                    fg_color = get_text_color()
                    border_color = get_border_color()
                    
                    suggestion = match.replacements[0] if match.replacements else ""
                    message = match.message
                    if suggestion:
                        message = f"{message}\nSuggested: {suggestion}"
                    
                    label = tk.Label(
                        active_tooltip, 
                        text=message, 
                        background=bg_color, 
                        foreground=fg_color,
                        relief="solid", 
                        borderwidth=1,
                        padx=12,
                        pady=8,
                        font=(FONT_FAMILY, 10),
                        wraplength=300,
                        bd=0,
                        highlightbackground=border_color,
                        highlightthickness=1,
                        justify="left"
                    )
                    label.pack()
                    
                    def on_leave(e):
                        clear_tooltip()
                    
                    label.bind("<Leave>", on_leave)
                    active_tooltip.after(5000, clear_tooltip)
                    break
                    
        text_widget.bind("<Motion>", show_tooltip)
        
    except Exception as e:
        print(f"Grammar check error: {e}")

# ===================== HISTORY MANAGEMENT =====================
def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading history: {e}")
    return []

def save_to_history(entry):
    translation_history.append(entry)
    if len(translation_history) > MAX_HISTORY_SIZE:
        translation_history.pop(0)
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(translation_history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")

def create_history_card(scroll_frame, entry, idx):
    card = ctk.CTkFrame(
        scroll_frame, 
        border_width=1,
        border_color=get_border_color(),
        corner_radius=8,
        fg_color=get_bg_color()  # Match current theme
    )
    card.grid(row=idx, column=0, sticky="ew", padx=5, pady=8)  # Increased padding
    card.grid_columnconfigure(0, weight=1)
    card.grid_rowconfigure(0, weight=1)
    
    # Main content frame
    content_frame = ctk.CTkFrame(card, fg_color="transparent")
    content_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)  # Increased padding
    content_frame.grid_columnconfigure(0, weight=1)
    
    # Header with timestamp and language info
    header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    
    time_label = ctk.CTkLabel(
        header_frame, 
        text=entry["timestamp"],
        font=(FONT_FAMILY, 11, "italic"),
        anchor="w",
        text_color=get_secondary_text_color()
    )
    time_label.pack(side="left", fill="x", expand=True)
    
    lang_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    lang_frame.pack(side="right", padx=(10, 0))
    
    ctk.CTkLabel(
        lang_frame, 
        text=f"{entry['source'].split(' (')[0]} → {entry['target'].split(' (')[0]}",
        font=(FONT_FAMILY, 12, "bold"),
        anchor="e",
        text_color=get_text_color()
    ).pack(side="right")
    
    if entry.get("noun_mode", False):
        noun_tag = ctk.CTkLabel(
            lang_frame,
            text="(Noun Mode)",
            font=(FONT_FAMILY, 10, "italic"),
            text_color=get_button_secondary(),
            anchor="e"
        )
        noun_tag.pack(side="right", padx=(0, 5))
    
    # Text content
    text_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    text_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
    
    # Original text
    orig_frame = ctk.CTkFrame(text_frame, fg_color="transparent")
    orig_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    
    ctk.CTkLabel(
        orig_frame, 
        text="Original:",
        font=(FONT_FAMILY, 11, "bold"),
        anchor="w"
    ).grid(row=0, column=0, sticky="w")
    
    original_text = ctk.CTkTextbox(
        orig_frame, 
        height=90,  
        width = 675, # Increased height
        font=(FONT_FAMILY, 11),
        wrap="word",
        border_width=1,
        border_color=get_border_color(),
        corner_radius=4,
        fg_color=get_bg_color(),
        text_color=get_text_color()
    )
    original_text.insert("1.0", entry["original"])
    original_text.configure(state="disabled")
    original_text.grid(row=1, column=0, sticky="ew", pady=(5, 0))
    
    # Translated text
    trans_frame = ctk.CTkFrame(text_frame, fg_color="transparent")
    trans_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
    
    ctk.CTkLabel(
        trans_frame, 
        text="Translated:",
        font=(FONT_FAMILY, 11, "bold"),
        anchor="w"
    ).grid(row=0, column=0, sticky="w")
    
    translated_text = ctk.CTkTextbox(
        trans_frame, 
        height=90,  
        width = 675,
        font=(FONT_FAMILY, 11),
        wrap="word",
        border_width=1,
        border_color=get_border_color(),
        corner_radius=4,
        fg_color=get_bg_color(),
        text_color=get_text_color()
    )
    translated_text.insert("1.0", entry["translated"])
    translated_text.configure(state="disabled")
    translated_text.grid(row=1, column=0, sticky="ew", pady=(5, 0))
    
    # Confidence and actions
    footer_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    footer_frame.grid(row=2, column=0, sticky="ew")
    footer_frame.grid_columnconfigure(0, weight=1)
    footer_frame.grid_columnconfigure(1, weight=0)
    
    # Confidence indicator
    conf_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
    conf_frame.grid(row=0, column=0, sticky="w")
    
    ctk.CTkLabel(
        conf_frame, 
        text="Confidence:",
        font=(FONT_FAMILY, 11, "bold"),
        anchor="w"
    ).pack(side="left", padx=(0, 5))
    
    if entry["confidence"] == -1:
        conf_text = "Not calculated"
        conf_color = "#95A5A6"
    elif entry["confidence"] == 0:
        conf_text = "Failed"
        conf_color = "#95A5A6"
    else:
        conf_text = f"{entry['confidence']}%"
        conf_color = (
            "#27AE60" if entry["confidence"] >= 80 else
            "#F39C12" if entry["confidence"] >= 50 else
            "#E74C3C"
        )
    
    conf_label = ctk.CTkLabel(
        conf_frame, 
        text=conf_text,
        font=(FONT_FAMILY, 11),
        text_color=conf_color,
        anchor="w"
    )
    conf_label.pack(side="left")
    
    # Action buttons - increased size and consistent styling
    action_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
    action_frame.grid(row=0, column=1, sticky="e")
    
    use_btn = ctk.CTkButton(
        action_frame,
        text="Use Translation",
        command=lambda e=entry: use_history_entry(e),
        width=140,  # Increased width
        height=30,   # Increased height
        font=BUTTON_FONT,
        fg_color=get_button_primary(),
        hover_color=get_hover_color(),
        corner_radius=8
    )
    use_btn.grid(row=0, column=0, padx=(0, 10))
    
    delete_btn = ctk.CTkButton(
        action_frame,
        text="Delete",
        command=lambda idx=len(translation_history)-1-idx: delete_history_entry(idx, scroll_frame),
        width=100,   # Increased width
        height=30,   # Increased height
        font=BUTTON_FONT,
        fg_color=get_button_danger(),
        hover_color="#c0392b",
        corner_radius=8
    )
    delete_btn.grid(row=0, column=1)
    
    return card

def show_history():
    if not translation_history:
        return
        
    history_window = ctk.CTkToplevel(app)
    history_window.title("Translation History")
    history_window.geometry("800x548")
    history_window.transient(app)
    history_window.grab_set()
    
    history_window.grid_columnconfigure(0, weight=1)
    history_window.grid_rowconfigure(0, weight=1)
    
    # Main container with consistent styling
    main_frame = ctk.CTkFrame(
        history_window, 
        fg_color=get_bg_color(),  # Match current theme
        corner_radius=8
    )
    main_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=1)
    
    # Header with title and controls
    header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
    header_frame.grid_columnconfigure(0, weight=1)
    
    ctk.CTkLabel(
        header_frame,
        text="🕒 Translation History",
        font=(FONT_FAMILY, 18, "bold"),
        text_color=get_text_color(),
        anchor="w"
    ).grid(row=0, column=0, sticky="w")
    
    # Buttons with increased size and consistent styling
    controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    controls_frame.grid(row=0, column=1, sticky="e")
    
    clear_btn = ctk.CTkButton(
        controls_frame,
        text="🗑 Clear History",
        command=lambda: clear_history(history_window),
        width=140,  # Increased width
        height=30,  # Increased height
        font=BUTTON_FONT,
        fg_color=get_button_danger(),
        hover_color="#c0392b"
    )
    clear_btn.grid(row=0, column=0, padx=(0, 10))
    
    close_btn = ctk.CTkButton(
        controls_frame,
        text="✖ Close",
        command=history_window.destroy,
        width=100,  # Increased width
        height=30,  # Increased height
        font=BUTTON_FONT,
        fg_color=get_button_secondary(),
        hover_color=get_hover_color()
    )
    close_btn.grid(row=0, column=1)
    
    # Scrollable history area
    scroll_frame = ctk.CTkScrollableFrame(
        main_frame,
        fg_color="transparent"
    )
    scroll_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
    scroll_frame.grid_columnconfigure(0, weight=1)
    
    # Add history entries
    for idx, entry in enumerate(reversed(translation_history)):
        create_history_card(scroll_frame, entry, idx)
    
    # Status footer
    status_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    status_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
    
    ctk.CTkLabel(
        status_frame,
        text=f"Entries: {len(translation_history)} ",
        font=(FONT_FAMILY, 12),
        text_color=get_secondary_text_color()
    ).pack(side="left")
    
    return history_window

def clear_history(history_window):
    global translation_history
    translation_history = []
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
    except Exception as e:
        print(f"Error clearing history: {e}")
    history_window.destroy()
    show_error("History cleared")

def delete_history_entry(index, scroll_frame):
    global translation_history
    if 0 <= index < len(translation_history):
        del translation_history[index]
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(translation_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")
        
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        
        for idx, entry in enumerate(reversed(translation_history)):
            create_history_card(scroll_frame, entry, idx)

def use_history_entry(entry):
    input_box.delete("1.0", "end")
    input_box.insert("1.0", entry["original"])
    
    # Extract language name from the stored string
    source_name = entry["source"].split(' (')[0]
    target_name = entry["target"].split(' (')[0]
    
    source_combo.set(source_name)
    target_combo.set(target_name)
    
    noun_mode.set(1 if entry.get("noun_mode", False) else 0)
    detect_language()

def text_to_speech(text, lang_code):
    if not text or not lang_code or lang_code == 'auto':
        show_error("Language not supported for TTS")
        return
        
    def tts_worker():
        filename = None
        try:
            filename = f"tts_{time.time()}.mp3"
            tts = gTTS(text=text, lang=lang_code)
            tts.save(filename)
            
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            start_time = time.time()
            while pygame.mixer.music.get_busy():
                if time.time() - start_time > 60:
                    break
                time.sleep(0.1)
                
        except Exception as e:
            error_msg = str(e)
            if "language not supported" in error_msg.lower():
                error_msg = "TTS not supported for this language"
            app.after(0, lambda: show_error(f"TTS Error: {error_msg}"))
        finally:
            if filename and os.path.exists(filename):
                try:
                    # Retry mechanism for file deletion
                    for i in range(5):
                        try:
                            os.remove(filename)
                            break
                        except:
                            time.sleep(0.1)
                except:
                    pass
    
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
        
    thread_pool.submit(tts_worker)

def auto_detect_typing(event=None):
    global debounce_timer
    if debounce_timer:
        debounce_timer.cancel()
    debounce_timer = threading.Timer(DEBOUNCE_TIME, safe_detect_typing)
    debounce_timer.start()

def safe_detect_typing():
    input_text = input_box.get("1.0", "end-1c").strip()
    char_count = len(input_text)
    char_count_label.configure(text=f"Chars: {char_count}")
    
    if input_text:
        lang_code = detect_language()
        if char_count <= MAX_TEXT_LENGTH:
            source_lang = source_combo.get()
            if source_lang == "English" or source_lang == "Auto Detect":
                auto_check_grammar()

def auto_check_grammar():
    global grammar_timer
    if grammar_timer:
        grammar_timer.cancel()
    grammar_timer = threading.Timer(DEBOUNCE_TIME, safe_check_grammar)
    grammar_timer.start()

def safe_check_grammar():
    input_text = input_box.get("1.0", "end-1c").strip()
    if input_text and len(input_text) <= MAX_TEXT_LENGTH:
        source_lang = source_combo.get()
        if source_lang == "English" or source_lang == "Auto Detect":
            if any(char.isalpha() for char in input_text):
                underline_mistakes(input_box, input_text, 'en')

def update_header_colors():
    """Update header colors based on current theme"""
    bg_color = get_bg_color()
    text_color = get_text_color()
    subtitle_color = get_secondary_text_color()
    
    header.configure(fg_color=bg_color)
    title_label.configure(text_color=text_color)
    subtitle_label.configure(text_color=subtitle_color)

def update_language_selection_colors():
    """Update language selection area colors"""
    text_color = get_text_color()
    border_color = get_border_color()
    
    source_label.configure(text_color=text_color)
    target_label.configure(text_color=text_color)
    source_combo.configure(border_color=border_color, button_color=get_button_primary())
    target_combo.configure(border_color=border_color, button_color=get_button_primary())
    noun_toggle.configure(text_color=text_color, border_color=border_color, progress_color=get_button_secondary())
    swap_btn.configure(border_color=border_color, text_color=text_color, hover_color=get_hover_color())

def update_text_widget_colors():
    """Update text widget colors"""
    bg = get_bg_color()
    fg = get_text_color()
    border_color = get_border_color()
    
    input_box.configure(bg=bg, fg=fg, insertbackground=fg)
    output_box.configure(bg=bg, fg=fg)
    
    # Update text container frames
    input_text_container.configure(fg_color=bg)
    output_text_container.configure(fg_color=bg)
    
    # Update header labels
    input_label.configure(text_color=fg)
    output_label.configure(text_color=fg)
    char_count_label.configure(text_color=get_secondary_text_color())
    
    # Update scrollbars
    input_scrollbar.configure(button_color=get_scroll_thumb_color())
    output_scrollbar.configure(button_color=get_scroll_thumb_color())

def update_buttons_colors():
    """Update all buttons to match current theme"""
    text_color = get_text_color()
    border_color = get_border_color()
    hover_color = get_hover_color()
    
    # Header buttons
    appearance_switch.configure(
        fg_color=get_button_secondary(),
        text_color=text_color,
        hover_color=hover_color
    )
    clear_btn.configure(
        fg_color=get_button_danger(),
        hover_color="#c0392b",
        text_color="#FFFFFF"
    )
    
    # Language detection button
    detect_btn.configure(
        text_color=text_color,
        border_color=border_color,
        hover_color=hover_color
    )
    
    # Text area buttons
    copy_btn.configure(
        text_color=text_color,
        border_color=border_color,
        hover_color=hover_color
    )
    
    # Action buttons
    tts_input_btn.configure(
        text_color=text_color,
        border_color=border_color,
        hover_color=hover_color
    )
    
    tts_output_btn.configure(
        text_color=text_color,
        border_color=border_color,
        hover_color=hover_color
    )
    
    history_btn.configure(
        text_color=text_color,
        border_color=border_color,
        hover_color=hover_color
    )
    
    cancel_btn.configure(
        text_color=text_color,
        border_color=border_color,
        hover_color="#c0392b"
    )
    
    # Primary action button
    translate_btn.configure(
        fg_color=get_button_primary(),
        hover_color=hover_color
    )

def update_status_bar_colors():
    """Update status bar colors"""
    bg_color = get_bg_color()
    text_color = get_text_color()
    border_color = get_border_color()
    
    status_frame.configure(fg_color=bg_color, border_color=border_color)
    confidence_label.configure(text_color=text_color)
    detected_lang_label.configure(text_color=text_color)
    
    # Update progress bar color
    progress_bar.configure(progress_color=get_button_primary())

def update_ui_colors():
    """Update all UI colors based on current theme"""
    # Update header
    update_header_colors()
    
    # Update language selection
    update_language_selection_colors()
    
    # Update text widgets
    update_text_widget_colors()
    
    # Update buttons
    update_buttons_colors()
    
    # Update status bar
    update_status_bar_colors()

def clear_all():
    global cancelled
    cancelled = True
    if pygame.mixer.get_init():
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            # Also stop any potential queued playback
            pygame.mixer.stop()
        except:
            pass
    input_box.delete("1.0", "end")
    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    output_box.configure(state="disabled")
    detected_lang_label.configure(text="")
    confidence_label.configure(text="")
    char_count_label.configure(text="Chars: 0")
    confidence_bar.set(0)
    clear_tooltip()
    input_box.focus_set()
    
    # Reset to initial state
    source_combo.set("Auto Detect")
    target_combo.set("English")
    noun_mode.set(0)
    progress_bar.set(0)  # Explicitly reset progress bar
    progress_bar.stop()  # Ensure it stops animating
    confidence_bar.set(0)
    
    cancelled = False

def copy_output():
    output_text = output_box.get("1.0", "end-1c").strip()
    if output_text:
        app.clipboard_clear()
        app.clipboard_append(output_text)
        copy_btn.configure(text="✓ Copied!")
        app.after(1500, lambda: copy_btn.configure(text="📋 Copy"))

def toggle_mode():
    # Determine current theme and switch to the opposite
    current_theme = get_actual_theme()
    if current_theme == "Dark":
        ctk.set_appearance_mode("Light")
        appearance_switch.configure(text="🌙 Dark") 
    else:
        ctk.set_appearance_mode("Dark")
        appearance_switch.configure(text="🔆 Light")
    
    # Update all UI colors
    update_ui_colors()

def swap_languages():
    current_source = source_combo.get()
    current_target = target_combo.get()
    
    if current_source == "Auto Detect" or current_target == "Auto Detect":
        return
        
    source_combo.set(current_target)
    target_combo.set(current_source)
    
    input_text = input_box.get("1.0", "end-1c").strip()
    output_text = output_box.get("1.0", "end-1c").strip()
    
    input_box.delete("1.0", "end")
    input_box.insert("1.0", output_text)
    
    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    output_box.insert("1.0", input_text)
    output_box.configure(state="disabled")
    
    if input_text:
        detect_language()

def setup_header():
    global header, title_label, subtitle_label, appearance_switch, clear_btn
    header = ctk.CTkFrame(app, corner_radius=0, fg_color=get_bg_color(), height=80)
    header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
    header.grid_columnconfigure(0, weight=1)
    header.grid_columnconfigure(1, weight=0)
    
    # Left side - Title
    title_frame = ctk.CTkFrame(header, fg_color="transparent")
    title_frame.grid(row=0, column=0, sticky="w", padx=25, pady=0)
    
    title_label = ctk.CTkLabel(
        title_frame, 
        text="Language Translator", 
        font=("Segoe UI", 24, "bold"),
        text_color=get_text_color()
    )
    title_label.grid(row=0, column=0, sticky="w", pady=(10, 0))
    
    subtitle_label = ctk.CTkLabel(
        title_frame, 
        text="Advanced Translation with Noun Optimization", 
        font=("Segoe UI", 11),
        text_color=get_secondary_text_color()
    )
    subtitle_label.grid(row=1, column=0, sticky="w", pady=(0, 10))
    
    # Right side - Controls
    controls_frame = ctk.CTkFrame(header, fg_color="transparent")
    controls_frame.grid(row=0, column=1, sticky="e", padx=25, pady=0)
    
    # Appearance switch - Set initial state based on current theme
    initial_theme = get_actual_theme()
    button_text = "🔆 Light" if initial_theme == "Dark" else "🌙 Dark"
    button_fg = get_button_secondary()
    button_hover = get_hover_color()
    text_color = get_text_color()
    
    appearance_switch = ctk.CTkButton(
        controls_frame, 
        text=button_text,
        command=toggle_mode,
        width=100,  # Increased width
        height=32,  # Increased height
        fg_color=button_fg,
        hover_color=button_hover,
        text_color=text_color,
        font=BUTTON_FONT,
        corner_radius=6
    )
    appearance_switch.grid(row=0, column=0, padx=(0, 10), pady=0)
    
    # Clear button
    clear_btn = ctk.CTkButton(
        controls_frame, 
        text="🗑️Clear", 
        command=clear_all,
        width=100,  # Increased width
        height=32,  # Increased height
        fg_color=get_button_danger(),
        hover_color="#c0392b",
        text_color="#FFFFFF",
        font=BUTTON_FONT,
        corner_radius=6
    )
    clear_btn.grid(row=0, column=1, padx=0, pady=0)
    
    return header

def setup_language_selection():
    global lang_frame, source_combo, target_combo, noun_mode, source_label, target_label, noun_toggle, swap_btn
    lang_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=50)
    lang_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=(0, 10))
    lang_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="lang_cols")
    
    # Source language
    source_label = ctk.CTkLabel(
        lang_frame, 
        text="From:", 
        font=("Segoe UI", 12, "bold"),
        anchor="e",
        text_color=get_text_color()
    )
    source_label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="e")
    
    source_combo = ctk.CTkComboBox(
        lang_frame, 
        values=name_list, 
        width=170,
        height=36,  # Increased height
        font=("Segoe UI", 11),
        dropdown_font=("Segoe UI", 11),
        button_color=get_button_primary(),
        border_color=get_border_color(),
        dropdown_hover_color=get_hover_color(),
        corner_radius=6
    )
    source_combo.set("Auto Detect")
    source_combo.grid(row=0, column=1, padx=0, pady=0, sticky="w")
    
    # Swap button
    swap_btn = ctk.CTkButton(
        lang_frame, 
        text="⇄", 
        width=50,
        height=36,  # Increased height
        command=swap_languages,
        fg_color="transparent",
        hover_color=get_hover_color(),
        border_width=1,
        border_color=get_border_color(),
        font=("Segoe UI", 16, "bold"),
        text_color=get_text_color()
    )
    swap_btn.grid(row=0, column=2, padx=10, pady=0)
    
    # Target language
    target_label = ctk.CTkLabel(
        lang_frame, 
        text="To:", 
        font=("Segoe UI", 12, "bold"),
        anchor="e",
        text_color=get_text_color()
    )
    target_label.grid(row=0, column=3, padx=(10, 5), pady=5, sticky="e")
    
    target_combo = ctk.CTkComboBox(
        lang_frame, 
        values=name_list, 
        width=170,
        height=36,  # Increased height
        font=("Segoe UI", 11),
        dropdown_font=("Segoe UI", 11),
        button_color=get_button_primary(),
        border_color=get_border_color(),
        dropdown_hover_color=get_hover_color(),
        corner_radius=6
    )
    target_combo.set("English")
    target_combo.grid(row=0, column=4, padx=0, pady=0, sticky="w")
    
    # Noun mode
    noun_frame = ctk.CTkFrame(lang_frame, fg_color="transparent")
    noun_frame.grid(row=0, column=5, padx=(10, 0), pady=0, sticky="e")
    
    noun_mode = ctk.IntVar(value=0)
    noun_toggle = ctk.CTkSwitch(
        noun_frame,
        text="Noun Mode",
        variable=noun_mode,
        button_color="#ffffff",
        progress_color=get_button_secondary(),
        font=("Segoe UI", 11),
        border_width=1,
        border_color=get_border_color(),
        text_color=get_text_color()
    )
    noun_toggle.pack(side="right", padx=0)
    
    return lang_frame

def setup_text_areas():
    global input_box, output_box, char_count_label, detect_btn, copy_btn, input_scrollbar, output_scrollbar, input_text_container, output_text_container, input_label, output_label
    text_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    text_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=0)
    text_frame.grid_columnconfigure((0, 1), weight=1, uniform="text_cols")
    text_frame.grid_rowconfigure(0, weight=1)

    # Input text area
    input_frame = ctk.CTkFrame(text_frame, fg_color="transparent", corner_radius=8)
    input_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
    input_frame.grid_rowconfigure(1, weight=1)
    input_frame.grid_columnconfigure(0, weight=1)

    # Input header
    input_header = ctk.CTkFrame(input_frame, fg_color="transparent", height=40)
    input_header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
    input_header.grid_columnconfigure(0, weight=1)
    input_header.grid_columnconfigure(1, weight=0)

    input_label = ctk.CTkLabel(
        input_header, 
        text="Input Text", 
        font=HEADER_FONT,  # Use header font
        anchor="w",
        text_color=get_text_color()
    )
    input_label.grid(row=0, column=0, padx=(15, 5), pady=0, sticky="w")

    char_count_label = ctk.CTkLabel(
        input_header,
        text="Chars: 0",
        font=("Segoe UI", 13),
        text_color=get_secondary_text_color(),
        anchor="e"
    )
    char_count_label.grid(row=0, column=1, padx=(0, 10), pady=0, sticky="e")

    detect_btn = ctk.CTkButton(
        input_header, 
        text="Detect", 
        command=detect_language,
        width=80,
        height=32,  # Increased height
        font=BUTTON_FONT,
        fg_color="transparent",
        hover_color=get_hover_color(),
        border_width=1,
        border_color=get_border_color(),
        text_color=get_text_color(),
        corner_radius=6
    )
    detect_btn.grid(row=0, column=2, padx=(0, 15), pady=0, sticky="e")

    # Input text box
    input_text_container = ctk.CTkFrame(input_frame, fg_color=get_bg_color(), corner_radius=6)
    input_text_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 0))
    input_text_container.grid_rowconfigure(0, weight=1)
    input_text_container.grid_columnconfigure(0, weight=1)

    input_box = tk.Text(
        input_text_container, 
        font=FONT,  # Use increased font size
        wrap="word", 
        padx=18, 
        pady=18,
        bg=get_bg_color(),
        fg=get_text_color(),
        insertbackground=get_text_color(),
        relief="flat",
        highlightthickness=0
    )
    input_box.grid(row=0, column=0, sticky="nsew")

    # Scrollbar with improved visibility
    input_scrollbar = ctk.CTkScrollbar(
        input_text_container, 
        command=input_box.yview,
        fg_color="transparent",
        button_color=get_scroll_thumb_color(),
        button_hover_color=get_button_primary(),
        width=16
    )
    input_scrollbar.grid(row=0, column=1, sticky="ns")
    input_box.configure(yscrollcommand=input_scrollbar.set)

    # Output text area
    output_frame = ctk.CTkFrame(text_frame, fg_color="transparent", corner_radius=8)
    output_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)
    output_frame.grid_rowconfigure(1, weight=1)
    output_frame.grid_columnconfigure(0, weight=1)

    # Output header
    output_header = ctk.CTkFrame(output_frame, fg_color="transparent", height=40)
    output_header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
    output_header.grid_columnconfigure(0, weight=1)
    output_header.grid_columnconfigure(1, weight=0)

    output_label = ctk.CTkLabel(
        output_header, 
        text="Translated Text", 
        font=HEADER_FONT,  # Use header font
        anchor="w",
        text_color=get_text_color()
    )
    output_label.grid(row=0, column=0, padx=(15, 5), pady=0, sticky="w")

    copy_btn = ctk.CTkButton(
        output_header, 
        text="📋 Copy", 
        command=copy_output,
        width=80,
        height=32,  # Increased height
        font=BUTTON_FONT,
        fg_color="transparent",
        hover_color=get_hover_color(),
        border_width=1,
        border_color=get_border_color(),
        text_color=get_text_color(),
        corner_radius=6
    )
    copy_btn.grid(row=0, column=1, padx=(0, 15), pady=0, sticky="e")

    # Output text box
    output_text_container = ctk.CTkFrame(output_frame, fg_color=get_bg_color(), corner_radius=6)
    output_text_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 0))
    output_text_container.grid_rowconfigure(0, weight=1)
    output_text_container.grid_columnconfigure(0, weight=1)

    output_box = tk.Text(
        output_text_container, 
        font=FONT,  # Use increased font size
        wrap="word", 
        padx=18, 
        pady=18,
        state="disabled",
        bg=get_bg_color(),
        fg=get_text_color(),
        relief="flat",
        highlightthickness=0
    )
    output_box.grid(row=0, column=0, sticky="nsew")
    for event in ["<Button-1>", "<Button-2>", "<Button-3>", 
              "<Key>", "<Enter>", "<Leave>", "<Motion>"]:
              output_box.bind(event, lambda e: "break")

    # Scrollbar with improved visibility
    output_scrollbar = ctk.CTkScrollbar(
        output_text_container, 
        command=output_box.yview,
        fg_color="transparent",
        button_color=get_scroll_thumb_color(),
        button_hover_color=get_button_primary(),
        width=16
    )
    output_scrollbar.grid(row=0, column=1, sticky="ns")
    output_box.configure(yscrollcommand=output_scrollbar.set)
    
    return input_box, output_box

def setup_action_buttons():
    global translate_btn, cancel_btn, tts_input_btn, tts_output_btn, history_btn
    action_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=60)
    action_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 0))
    action_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="action_cols")
    
    # Translate button
    translate_btn = ctk.CTkButton(
        action_frame, 
        text="Translate", 
        command=translate_text,
        width=120,
        height=42,  # Increased height
        fg_color=get_button_primary(),
        hover_color=get_hover_color(),
        font=("Segoe UI", FONT_SIZE, "bold"),  # Larger font
        corner_radius=8
    )
    translate_btn.grid(row=0, column=0, padx=(0, 10), pady=0)
    
    # TTS buttons
    tts_input_btn = ctk.CTkButton(
        action_frame, 
        text="🎙 Input Audio", 
        command=lambda: text_to_speech(
            input_box.get("1.0", "end-1c").strip(), 
            name_to_code.get(source_combo.get(), 'en')
        ),
        width=120,
        height=38,  # Increased height
        font=BUTTON_FONT,
        fg_color="transparent",
        hover_color=get_hover_color(),
        border_width=1,
        border_color=get_border_color(),
        text_color=get_text_color(),
        corner_radius=8
    )
    tts_input_btn.grid(row=0, column=1, padx=5, pady=0)
    
    tts_output_btn = ctk.CTkButton(
        action_frame, 
        text="🔊 Output Audio", 
        command=lambda: text_to_speech(
            output_box.get("1.0", "end-1c").strip(), 
            name_to_code.get(target_combo.get(), 'en')
        ),
        width=120,
        height=38,  # Increased height
        font=BUTTON_FONT,
        fg_color="transparent",
        hover_color=get_hover_color(),
        border_width=1,
        border_color=get_border_color(),
        text_color=get_text_color(),
        corner_radius=8
    )
    tts_output_btn.grid(row=0, column=3, padx=5, pady=0)
    
    # History button
    history_btn = ctk.CTkButton(
        action_frame, 
        text="🕒 History", 
        command=show_history,
        width=100,
        height=38,  # Increased height
        font=BUTTON_FONT,
        fg_color="transparent",
        hover_color=get_hover_color(),
        border_width=1,
        border_color=get_border_color(),
        text_color=get_text_color(),
        corner_radius=8
    )
    history_btn.grid(row=0, column=4, padx=(5, 10), pady=0)
    
    # Cancel button
    cancel_btn = ctk.CTkButton(
        action_frame, 
        text="✖ Cancel",
        command=lambda: globals().update({'cancelled': True}),
        width=100,
        height=38,  # Increased height
        font=BUTTON_FONT,
        fg_color="transparent",
        hover_color="#c0392b",
        border_width=1,
        border_color=get_border_color(),
        text_color=get_text_color(),
        corner_radius=8,
        state="disabled"
    )
    cancel_btn.grid(row=0, column=5, padx=0, pady=0)
    
    return translate_btn, cancel_btn

def setup_status_bar():
    global status_frame, detected_lang_label, confidence_label, progress_bar, confidence_bar
    status_frame = ctk.CTkFrame(app, height=50, corner_radius=0, 
                               fg_color=get_bg_color(),
                               border_color=get_border_color(),
                               border_width=1)
    status_frame.grid(row=3, column=0, sticky="ew", padx=0, pady=(0, 0))
    status_frame.grid_columnconfigure(0, weight=1)
    status_frame.grid_columnconfigure(1, weight=0)
    
    # Left side - Confidence
    confidence_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
    confidence_frame.grid(row=0, column=0, sticky="w", padx=25, pady=0)
    
    # Confidence label with increased size and boldness
    confidence_label = ctk.CTkLabel(
        confidence_frame, 
        text="", 
        font=("Segoe UI", 12, "bold"),
        anchor="w",
        text_color=get_text_color()
    )
    confidence_label.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="w")
    
    confidence_bar = ctk.CTkProgressBar(
        confidence_frame, 
        width=180,
        height=10,
        corner_radius=4
    )
    confidence_bar.set(0)
    confidence_bar.grid(row=0, column=1, padx=0, pady=0, sticky="w")
    
    # Right side - Progress and detection
    progress_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
    progress_frame.grid(row=0, column=1, sticky="e", padx=25, pady=0)
    
    # Detected lang with increased size and boldness
    detected_lang_label = ctk.CTkLabel(
        progress_frame, 
        text="", 
        font=("Segoe UI", 12, "bold"),
        anchor="e",
        text_color=get_text_color()
    )
    detected_lang_label.grid(row=0, column=0, padx=(0, 15), pady=0, sticky="e")
    
    progress_bar = ctk.CTkProgressBar(
        progress_frame, 
        mode="indeterminate",
        width=180,
        height=10,
        corner_radius=4,
        progress_color=get_button_primary()
    )
    progress_bar.grid(row=0, column=1, padx=0, pady=0, sticky="e")
    progress_bar.set(0)
    
    return status_frame

def create_main_ui():
    global main_frame
    # Create main containers
    main_frame = ctk.CTkFrame(app, fg_color="transparent")
    main_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(0, weight=0)  # Language row
    main_frame.grid_rowconfigure(1, weight=1)  # Text areas row
    main_frame.grid_rowconfigure(2, weight=0)  # Action buttons row
    
    # Build UI sections
    setup_header()
    setup_language_selection()
    setup_text_areas()
    setup_action_buttons()
    setup_status_bar()

# ===================== EVENT BINDINGS & INITIALIZATION =====================
def setup_event_bindings():
    app.protocol("WM_DELETE_WINDOW", lambda: [cleanup_resources(), app.destroy()])
    
    # Keyboard shortcuts
    app.bind("<Control-t>", lambda e: translate_text())
    app.bind("<Control-s>", lambda e: swap_languages())
    app.bind("<Control-l>", lambda e: toggle_mode())
    app.bind("<Control-h>", lambda e: show_history())
    app.bind("<Control-n>", lambda e: noun_mode.set(1 if noun_mode.get() == 0 else 0))
    app.focus_force() 
    # Text box events
    input_box.bind("<KeyRelease>", 
        lambda e: [auto_detect_typing(), auto_check_grammar()]
    )

def initialize_application():
    # Load translation history
    global translation_history
    translation_history = load_history()
    
    # Initialize language support
    global code_to_name, name_to_code, name_list
    code_to_name, name_to_code, name_list = initialize_language_support()
    
    # Create UI
    create_main_ui()
    
    # Set up event bindings
    setup_event_bindings()
    
    # Final initialization
    update_ui_colors()
    input_box.focus_set()

