# ===================== APPLICATION =====================
# The TranslatorApp window ties the UI to the translation, detection,
# grammar, TTS, and history modules. All widget updates happen on the main
# thread; slow work runs on a thread pool and reports back through a
# thread-safe queue that the main thread drains.

import queue
import tkinter as tk
import customtkinter as ctk
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from . import translation, detection
from .config import (
    FONT, FONT_SIZE, FONT_FAMILY, BUTTON_FONT, HEADER_FONT, TITLE_FONT,
    SUBTITLE_FONT, LABEL_FONT, SMALL_FONT, DEBOUNCE_MS, DANGER_HOVER,
    NEUTRAL_COLOR, MAX_TEXT_LENGTH, MAX_TRANSLATION_LENGTH,
)
from .languages import load_language_maps, AUTO_DETECT, AUTO
from .grammar import GrammarChecker
from .tts import TextToSpeech
from .history import HistoryStore
from .tooltip import GrammarTooltip
from .history_window import HistoryWindow
from .theme import (
    get_actual_theme, get_bg_color, get_text_color, get_border_color,
    get_button_primary, get_button_secondary, get_button_danger,
    get_hover_color, get_scroll_thumb_color, get_secondary_text_color,
    get_confidence_color,
)


class TranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Language Translator")
        self.geometry("950x600")
        self.minsize(950, 600)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # enforce a real network timeout since deep-translator ignores its own
        translation.apply_network_timeout()

        # services
        self.history = HistoryStore()
        self.history.load()
        self.grammar = GrammarChecker()
        self.tts = TextToSpeech()
        self.tooltip = GrammarTooltip(self)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # language maps
        self.code_to_name, self.name_to_code, self.name_list = load_language_maps()
        self.valid_codes = set(self.code_to_name)

        # runtime state
        self._request_id = 0  # only the newest translation request may update the UI
        self._has_result = False  # True only while the output box holds a translation
        self._closing = False
        self._detect_job = None
        self._grammar_job = None
        self._copy_job = None
        self._poll_job = None
        self._matches = {}  # text widget -> grammar matches valid for its current text

        # worker threads push UI updates here; the main thread drains them safely
        self._ui_queue = queue.Queue()

        self._build_ui()
        self._bind_events()
        self._apply_theme()
        self.input_box.focus_set()
        self._poll_job = self.after(50, self._poll_ui_queue)

    def _post(self, fn):
        # schedule a callable to run on the main thread from any worker thread
        self._ui_queue.put(fn)

    def _post_current(self, request_id, fn):
        # queue a UI update that is dropped if a newer request has replaced this one
        def run():
            if request_id == self._request_id:
                fn()
        self._post(run)

    def _poll_ui_queue(self):
        if self._closing:
            return
        try:
            while True:
                fn = self._ui_queue.get_nowait()
                try:
                    fn()
                except Exception as e:
                    print(f"UI update error: {e}")
        except queue.Empty:
            pass
        self._poll_job = self.after(50, self._poll_ui_queue)

    # --------------------- UI construction ---------------------
    def _build_ui(self):
        self._build_header()
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self._build_language_selection()
        self._build_text_areas()
        self._build_action_buttons()
        self._build_status_bar()

    def _build_header(self):
        self.header = ctk.CTkFrame(self, corner_radius=0, fg_color=get_bg_color(), height=80)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(self.header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w", padx=25)

        self.title_label = ctk.CTkLabel(
            title_box, text="Language Translator", font=TITLE_FONT,
            text_color=get_text_color(),
        )
        self.title_label.grid(row=0, column=0, sticky="w", pady=(10, 0))

        self.subtitle_label = ctk.CTkLabel(
            title_box, text="Advanced Translation with Noun Optimization",
            font=SUBTITLE_FONT, text_color=get_secondary_text_color(),
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(0, 10))

        controls = ctk.CTkFrame(self.header, fg_color="transparent")
        controls.grid(row=0, column=1, sticky="e", padx=25)

        theme_is_dark = get_actual_theme() == "Dark"
        self.appearance_switch = ctk.CTkButton(
            controls, text="🔆 Light" if theme_is_dark else "🌙 Dark",
            command=self.toggle_theme, width=100, height=32,
            fg_color=get_button_secondary(), hover_color=get_hover_color(),
            text_color=get_text_color(), font=BUTTON_FONT, corner_radius=6,
        )
        self.appearance_switch.grid(row=0, column=0, padx=(0, 10))

        self.clear_btn = ctk.CTkButton(
            controls, text="🗑️ Clear", command=self.clear_all, width=100, height=32,
            fg_color=get_button_danger(), hover_color=DANGER_HOVER,
            text_color="#FFFFFF", font=BUTTON_FONT, corner_radius=6,
        )
        self.clear_btn.grid(row=0, column=1)

    def _build_language_selection(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=50)
        frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(0, 10))
        frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="lang_cols")

        self.source_label = ctk.CTkLabel(
            frame, text="From:", font=LABEL_FONT, anchor="e", text_color=get_text_color(),
        )
        self.source_label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="e")

        self.source_combo = ctk.CTkComboBox(
            frame, values=self.name_list, width=170, height=36, font=SMALL_FONT,
            dropdown_font=SMALL_FONT, button_color=get_button_primary(),
            border_color=get_border_color(), dropdown_hover_color=get_hover_color(),
            corner_radius=6,
        )
        self.source_combo.set(AUTO_DETECT)
        self.source_combo.grid(row=0, column=1, sticky="w")

        self.swap_btn = ctk.CTkButton(
            frame, text="⇄", width=50, height=36, command=self.swap_languages,
            fg_color="transparent", hover_color=get_hover_color(), border_width=1,
            border_color=get_border_color(), font=(FONT_FAMILY, 16, "bold"),
            text_color=get_text_color(),
        )
        self.swap_btn.grid(row=0, column=2, padx=10)

        self.target_label = ctk.CTkLabel(
            frame, text="To:", font=LABEL_FONT, anchor="e", text_color=get_text_color(),
        )
        self.target_label.grid(row=0, column=3, padx=(10, 5), pady=5, sticky="e")

        # the target must be a real language, so Auto Detect is not offered here
        target_values = [name for name in self.name_list if name != AUTO_DETECT]
        self.target_combo = ctk.CTkComboBox(
            frame, values=target_values, width=170, height=36, font=SMALL_FONT,
            dropdown_font=SMALL_FONT, button_color=get_button_primary(),
            border_color=get_border_color(), dropdown_hover_color=get_hover_color(),
            corner_radius=6,
        )
        self.target_combo.set("English")
        self.target_combo.grid(row=0, column=4, sticky="w")

        noun_box = ctk.CTkFrame(frame, fg_color="transparent")
        noun_box.grid(row=0, column=5, padx=(10, 0), sticky="e")

        self.noun_var = ctk.IntVar(value=0)
        self.noun_toggle = ctk.CTkSwitch(
            noun_box, text="Noun Mode", variable=self.noun_var, button_color="#FFFFFF",
            progress_color=get_button_secondary(), font=SMALL_FONT, border_width=1,
            border_color=get_border_color(), text_color=get_text_color(),
        )
        self.noun_toggle.pack(side="right")

    def _build_text_areas(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.grid(row=1, column=0, sticky="nsew", padx=20)
        frame.grid_columnconfigure((0, 1), weight=1, uniform="text_cols")
        frame.grid_rowconfigure(0, weight=1)

        self.input_box, self.input_scrollbar, self.input_container, \
            self.input_label, self.char_count_label, self.detect_btn = \
            self._build_input_panel(frame)

        self.output_box, self.output_scrollbar, self.output_container, \
            self.output_label, self.copy_btn = self._build_output_panel(frame)

    def _build_input_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=8)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(panel, fg_color="transparent", height=40)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        input_label = ctk.CTkLabel(
            header, text="Input Text", font=HEADER_FONT, anchor="w",
            text_color=get_text_color(),
        )
        input_label.grid(row=0, column=0, padx=(15, 5), sticky="w")

        char_count_label = ctk.CTkLabel(
            header, text="Chars: 0", font=(FONT_FAMILY, 13),
            text_color=get_secondary_text_color(), anchor="e",
        )
        char_count_label.grid(row=0, column=1, padx=(0, 10), sticky="e")

        detect_btn = ctk.CTkButton(
            header, text="Detect", command=self.detect_language, width=80, height=32,
            font=BUTTON_FONT, fg_color="transparent", hover_color=get_hover_color(),
            border_width=1, border_color=get_border_color(), text_color=get_text_color(),
            corner_radius=6,
        )
        detect_btn.grid(row=0, column=2, padx=(0, 15), sticky="e")

        container = ctk.CTkFrame(panel, fg_color=get_bg_color(), corner_radius=6)
        container.grid(row=1, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        box = tk.Text(
            container, font=FONT, wrap="word", padx=18, pady=18, bg=get_bg_color(),
            fg=get_text_color(), insertbackground=get_text_color(), relief="flat",
            highlightthickness=0,
        )
        box.grid(row=0, column=0, sticky="nsew")

        scrollbar = ctk.CTkScrollbar(
            container, command=box.yview, fg_color="transparent",
            button_color=get_scroll_thumb_color(), button_hover_color=get_button_primary(),
            width=16,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        box.configure(yscrollcommand=scrollbar.set)

        return box, scrollbar, container, input_label, char_count_label, detect_btn

    def _build_output_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=8)
        panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(panel, fg_color="transparent", height=40)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        output_label = ctk.CTkLabel(
            header, text="Translated Text", font=HEADER_FONT, anchor="w",
            text_color=get_text_color(),
        )
        output_label.grid(row=0, column=0, padx=(15, 5), sticky="w")

        copy_btn = ctk.CTkButton(
            header, text="📋 Copy", command=self.copy_output, width=80, height=32,
            font=BUTTON_FONT, fg_color="transparent", hover_color=get_hover_color(),
            border_width=1, border_color=get_border_color(), text_color=get_text_color(),
            corner_radius=6,
        )
        copy_btn.grid(row=0, column=1, padx=(0, 15), sticky="e")

        container = ctk.CTkFrame(panel, fg_color=get_bg_color(), corner_radius=6)
        container.grid(row=1, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        box = tk.Text(
            container, font=FONT, wrap="word", padx=18, pady=18, state="disabled",
            bg=get_bg_color(), fg=get_text_color(), relief="flat", highlightthickness=0,
        )
        box.grid(row=0, column=0, sticky="nsew")

        scrollbar = ctk.CTkScrollbar(
            container, command=box.yview, fg_color="transparent",
            button_color=get_scroll_thumb_color(), button_hover_color=get_button_primary(),
            width=16,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        box.configure(yscrollcommand=scrollbar.set)

        return box, scrollbar, container, output_label, copy_btn

    def _build_action_buttons(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=60)
        frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 0))
        frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="action_cols")

        self.translate_btn = ctk.CTkButton(
            frame, text="Translate", command=self.translate, width=120, height=42,
            fg_color=get_button_primary(), hover_color=get_hover_color(),
            font=(FONT_FAMILY, FONT_SIZE, "bold"), corner_radius=8,
        )
        self.translate_btn.grid(row=0, column=0, padx=(0, 10))

        self.tts_input_btn = ctk.CTkButton(
            frame, text="🎙 Input Audio", command=self._speak_input, width=120, height=38,
            font=BUTTON_FONT, fg_color="transparent", hover_color=get_hover_color(),
            border_width=1, border_color=get_border_color(), text_color=get_text_color(),
            corner_radius=8,
        )
        self.tts_input_btn.grid(row=0, column=1, padx=5)

        self.tts_output_btn = ctk.CTkButton(
            frame, text="🔊 Output Audio", command=self._speak_output, width=120, height=38,
            font=BUTTON_FONT, fg_color="transparent", hover_color=get_hover_color(),
            border_width=1, border_color=get_border_color(), text_color=get_text_color(),
            corner_radius=8,
        )
        self.tts_output_btn.grid(row=0, column=2, padx=5)

        self.history_btn = ctk.CTkButton(
            frame, text="🕒 History", command=self.open_history, width=100, height=38,
            font=BUTTON_FONT, fg_color="transparent", hover_color=get_hover_color(),
            border_width=1, border_color=get_border_color(), text_color=get_text_color(),
            corner_radius=8,
        )
        self.history_btn.grid(row=0, column=3, padx=5)

        self.cancel_btn = ctk.CTkButton(
            frame, text="✖ Cancel", command=self.cancel_translation, width=100, height=38,
            font=BUTTON_FONT, fg_color="transparent", hover_color=DANGER_HOVER,
            border_width=1, border_color=get_border_color(), text_color=get_text_color(),
            corner_radius=8, state="disabled",
        )
        self.cancel_btn.grid(row=0, column=4, padx=(5, 0))

    def _build_status_bar(self):
        self.status_frame = ctk.CTkFrame(
            self, height=50, corner_radius=0, fg_color=get_bg_color(),
            border_color=get_border_color(), border_width=1,
        )
        self.status_frame.grid(row=3, column=0, sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=25)

        self.confidence_label = ctk.CTkLabel(
            left, text="", font=LABEL_FONT, anchor="w", text_color=get_text_color(),
        )
        self.confidence_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.confidence_bar = ctk.CTkProgressBar(left, width=180, height=10, corner_radius=4)
        self.confidence_bar.set(0)
        self.confidence_bar.grid(row=0, column=1, sticky="w")

        right = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e", padx=25)

        self.detected_lang_label = ctk.CTkLabel(
            right, text="", font=LABEL_FONT, anchor="e", text_color=get_text_color(),
        )
        self.detected_lang_label.grid(row=0, column=0, padx=(0, 15), sticky="e")

        self.progress_bar = ctk.CTkProgressBar(
            right, mode="indeterminate", width=180, height=10, corner_radius=4,
            progress_color=get_button_primary(),
        )
        self.progress_bar.grid(row=0, column=1, sticky="e")
        self.progress_bar.set(0)

    # --------------------- events ---------------------
    def _bind_events(self):
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Control-t>", lambda e: self.translate())
        self.bind("<Control-s>", lambda e: self.swap_languages())
        self.bind("<Control-l>", lambda e: self.toggle_theme())
        self.bind("<Control-h>", lambda e: self.open_history())
        self.bind("<Control-n>", lambda e: self.noun_var.set(0 if self.noun_var.get() else 1))
        self.input_box.bind("<KeyRelease>", self._on_key_release)
        self.input_box.bind("<Motion>", self._on_grammar_motion)
        self.output_box.bind("<Motion>", self._on_grammar_motion)

    def _on_key_release(self, event=None):
        # update the count immediately, debounce the expensive detect + grammar work
        count = len(self.input_box.get("1.0", "end-1c").strip())
        self.char_count_label.configure(text=f"Chars: {count}")
        self._clear_grammar(self.input_box)

        if self._detect_job:
            self.after_cancel(self._detect_job)
        if self._grammar_job:
            self.after_cancel(self._grammar_job)
        self._detect_job = self.after(DEBOUNCE_MS, self._auto_detect)
        self._grammar_job = self.after(DEBOUNCE_MS, self._auto_grammar)

    def _auto_detect(self):
        self._detect_job = None
        if self.input_box.get("1.0", "end-1c").strip():
            self.detect_language()

    def _auto_grammar(self):
        self._grammar_job = None
        text = self.input_box.get("1.0", "end-1c").strip()
        source = self.source_combo.get()
        if not text or len(text) > MAX_TEXT_LENGTH:
            return
        if not (detection.is_latin_text(text) and any(ch.isalpha() for ch in text)):
            return
        # grammar is English-only, so avoid flagging non-English input as mistakes
        if source == "English":
            self._schedule_grammar(self.input_box, text, "en")
        elif source == AUTO_DETECT and detection.detect(text, self.code_to_name).code == "en":
            self._schedule_grammar(self.input_box, text, "en")

    # --------------------- detection ---------------------
    def detect_language(self):
        text = self.input_box.get("1.0", "end-1c").strip()
        result = detection.detect(text, self.code_to_name)
        self.detected_lang_label.configure(text=result.message)
        return result.code

    # --------------------- translation ---------------------
    def translate(self):
        text = " ".join(self.input_box.get("1.0", "end-1c").split())
        count = len(text)

        if not text:
            return
        if not any(ch.isalpha() for ch in text):
            self._show_error("No translatable text found (only numbers/symbols)")
            return
        if count >= MAX_TRANSLATION_LENGTH:
            self._show_error(f"Text too long (max {MAX_TRANSLATION_LENGTH - 1} chars)")
            return

        source_name = self.source_combo.get()
        target_name = self.target_combo.get()

        if not target_name or target_name == AUTO_DETECT:
            self._set_output("Please select a target language")
            return
        if target_name not in self.name_to_code:
            return

        if source_name == AUTO_DETECT:
            source_code = self.detect_language()
        else:
            source_code = self.name_to_code.get(source_name, AUTO)
        target_code = self.name_to_code[target_name]

        # this request supersedes any translation still running
        self._request_id += 1
        request_id = self._request_id

        self._start_busy(count)
        noun_mode = self.noun_var.get() == 1
        self.executor.submit(
            self._translation_worker,
            text, source_name, source_code, target_name, target_code, noun_mode, request_id,
        )

    def _translation_worker(self, text, source_name, source_code,
                            target_name, target_code, noun_mode, request_id):
        try:
            translated, source_used, target_used = translation.translate(
                text, source_code, target_code, self.valid_codes, noun_mode,
            )
            # a newer request or a cancel makes this result obsolete
            if request_id != self._request_id:
                return
            if not translated or not translated.strip():
                self._post_current(request_id, lambda: self._show_error("Empty translation result"))
                return

            untranslated = translation.looks_untranslated(text, translated)

            # confidence needs a known source language to translate back into
            score = None
            note = None
            if source_used == AUTO:
                note = "Not available (unknown source language)"
            else:
                try:
                    back = translation.back_translate(translated, target_used, source_used)
                    if request_id != self._request_id:
                        return
                    if back and back.strip():
                        score = translation.confidence(text, back)
                    else:
                        note = "Back-translation failed"
                except Exception as e:
                    note = "Back-translation failed"
                    print(f"Back translation error: {e}")

            # only record a result the user is actually going to see
            if request_id != self._request_id:
                return

            self.history.add({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": f"{source_name} ({source_used})",
                "target": f"{target_name} ({target_used})",
                "original": text,
                "translated": translated,
                "confidence": score if score is not None else -1,
                "noun_mode": noun_mode,
            })

            self._post_current(request_id, lambda: self._show_result(
                translated, score, note, target_used, untranslated,
            ))
        except Exception as e:
            self._post_current(request_id, lambda err=e: self._show_error(self._friendly_error(err)))
        finally:
            self._post_current(request_id, self._end_busy)

    @staticmethod
    def _friendly_error(error):
        message = str(error).lower()
        if "no support for the provided language" in message:
            return "Error: This language pair is not supported"
        if "timed out" in message or "timeout" in message:
            return "Error: Translation timed out. Try shorter text."
        if "connection" in message or "network" in message:
            return "Error: Network error. Check your internet connection."
        if "too many requests" in message:
            return "Error: Service limit reached. Please wait and try again."
        return f"Error: Translation failed: {error}"

    def _show_result(self, translated, score, note, target_code, untranslated):
        self._set_output(translated)
        self._has_result = True
        self._update_confidence(score, note)

        if untranslated:
            self.detected_lang_label.configure(text="Result matches the source text")

        if self.grammar.supports(target_code) and len(translated) <= MAX_TEXT_LENGTH:
            self._schedule_grammar(self.output_box, translated, target_code)

    def _update_confidence(self, score, note):
        # score is an int 0-100, or None with a reason in note
        if score is None:
            self.confidence_label.configure(text=f"Confidence: {note}")
            self.confidence_bar.set(0)
            self.confidence_bar.configure(progress_color=NEUTRAL_COLOR)
        else:
            self.confidence_label.configure(text=f"Confidence: {score}%")
            self.confidence_bar.set(score / 100)
            self.confidence_bar.configure(progress_color=get_confidence_color(score))

    def _start_busy(self, count):
        self.progress_bar.start()
        self.translate_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.char_count_label.configure(text=f"Chars: {count}")
        self._set_output("Translating...")

    def _end_busy(self):
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.translate_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")

    def cancel_translation(self):
        # supersede the running request so its result is dropped when it arrives
        self._request_id += 1
        self._show_error("Translation cancelled")

    # --------------------- grammar ---------------------
    def _schedule_grammar(self, widget, text, lang_code):
        # run the check off the main thread, then apply the tags on it
        self.executor.submit(self._grammar_worker, widget, text, lang_code)

    def _grammar_worker(self, widget, text, lang_code):
        matches = self.grammar.check(text, lang_code)
        self._post(lambda: self._apply_grammar(widget, text, matches))

    def _apply_grammar(self, widget, text, matches):
        # skip if the widget's text changed while the check was running
        if widget.get("1.0", "end-1c") != text:
            return
        widget.tag_remove("mistake", "1.0", "end")
        for match in matches:
            start = f"1.0 + {match.offset} chars"
            end = f"1.0 + {match.offset + match.length} chars"
            widget.tag_add("mistake", start, end)
        widget.tag_config("mistake", underline=True, underlinefg="red")
        self._matches[widget] = matches

    def _clear_grammar(self, widget):
        # drop results whose offsets no longer line up with the widget's text
        if self._matches.pop(widget, None) is not None:
            widget.tag_remove("mistake", "1.0", "end")
        self.tooltip.clear()

    def _on_grammar_motion(self, event):
        widget = event.widget
        matches = self._matches.get(widget)
        if not matches:
            return
        index = widget.index(f"@{event.x},{event.y}")
        for match in matches:
            start = f"1.0 + {match.offset} chars"
            end = f"1.0 + {match.offset + match.length} chars"
            if widget.compare(index, ">=", start) and widget.compare(index, "<", end):
                message = match.message
                if match.replacements:
                    message = f"{message}\nSuggested: {match.replacements[0]}"
                self.tooltip.show(event.x_root, event.y_root, message)
                return

    # --------------------- text to speech ---------------------
    def _speak_input(self):
        text = self.input_box.get("1.0", "end-1c").strip()
        source = self.source_combo.get()
        # Auto Detect has no code, so detect the language before speaking
        if source == AUTO_DETECT:
            code = self.detect_language()
        else:
            code = self.name_to_code.get(source, "en")
        self.tts.speak(text, code, on_error=self._async_error)

    def _speak_output(self):
        # never read a status or error message aloud as if it were a translation
        if not self._has_result:
            return
        text = self.output_box.get("1.0", "end-1c").strip()
        code = self.name_to_code.get(self.target_combo.get(), "en")
        self.tts.speak(text, code, on_error=self._async_error)

    def _async_error(self, message):
        self._post(lambda: self._show_error(message))

    # --------------------- history ---------------------
    def open_history(self):
        if not self.history.is_empty():
            HistoryWindow(self, self.history, self._use_history_entry)

    def _use_history_entry(self, entry):
        self._set_input(entry["original"])
        # names can contain "(...)", so split off only the trailing "(code)"
        self.source_combo.set(entry["source"].rsplit(" (", 1)[0])
        self.target_combo.set(entry["target"].rsplit(" (", 1)[0])
        self.noun_var.set(1 if entry.get("noun_mode") else 0)
        self.detect_language()

    # --------------------- clipboard ---------------------
    def copy_output(self):
        # only a real translation is worth putting on the clipboard
        if not self._has_result:
            return
        text = self.output_box.get("1.0", "end-1c").strip()
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.copy_btn.configure(text="✓ Copied!")
        if self._copy_job:
            self.after_cancel(self._copy_job)
        self._copy_job = self.after(1500, lambda: self.copy_btn.configure(text="📋 Copy"))

    # --------------------- misc actions ---------------------
    def swap_languages(self):
        source = self.source_combo.get()
        target = self.target_combo.get()
        if AUTO_DETECT in (source, target):
            return

        self.source_combo.set(target)
        self.target_combo.set(source)

        # without a translation there is nothing to exchange, so keep the typed text
        if not self._has_result:
            return

        input_text = self.input_box.get("1.0", "end-1c").strip()
        output_text = self.output_box.get("1.0", "end-1c").strip()
        self._set_input(output_text)
        self._set_output(input_text)
        # both boxes still hold real text, now matching the swapped languages
        self._has_result = True
        self.detect_language()

    def clear_all(self):
        # supersede any running translation so a late result cannot repopulate the UI
        self._request_id += 1
        self.tts.stop()
        self._set_input("")
        self._set_output("")
        self.detected_lang_label.configure(text="")
        self.confidence_label.configure(text="")
        self.char_count_label.configure(text="Chars: 0")
        self.confidence_bar.set(0)
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.tooltip.clear()
        self._matches.clear()
        self.source_combo.set(AUTO_DETECT)
        self.target_combo.set("English")
        self.noun_var.set(0)
        self.input_box.focus_set()

    def _show_error(self, message):
        print(f"ERROR: {message}")
        self._set_output(message)
        self._end_busy()

    # --------------------- widget helpers ---------------------
    def _set_input(self, text):
        self.input_box.delete("1.0", "end")
        if text:
            self.input_box.insert("1.0", text)
        self._clear_grammar(self.input_box)

    def _set_output(self, text):
        # status and error messages go through here, so they never count as results
        self._has_result = False
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        if text:
            self.output_box.insert("1.0", text)
        self._clear_grammar(self.output_box)
        self.output_box.configure(state="disabled")

    # --------------------- theme ---------------------
    def toggle_theme(self):
        if get_actual_theme() == "Dark":
            ctk.set_appearance_mode("Light")
            self.appearance_switch.configure(text="🌙 Dark")
        else:
            ctk.set_appearance_mode("Dark")
            self.appearance_switch.configure(text="🔆 Light")
        self._apply_theme()

    def _apply_theme(self):
        bg = get_bg_color()
        fg = get_text_color()
        border = get_border_color()
        hover = get_hover_color()
        secondary = get_secondary_text_color()

        # header
        self.header.configure(fg_color=bg)
        self.title_label.configure(text_color=fg)
        self.subtitle_label.configure(text_color=secondary)

        # language selection
        self.source_label.configure(text_color=fg)
        self.target_label.configure(text_color=fg)
        for combo in (self.source_combo, self.target_combo):
            combo.configure(border_color=border, button_color=get_button_primary())
        self.noun_toggle.configure(
            text_color=fg, border_color=border, progress_color=get_button_secondary(),
        )
        self.swap_btn.configure(border_color=border, text_color=fg, hover_color=hover)

        # text widgets
        self.input_box.configure(bg=bg, fg=fg, insertbackground=fg)
        self.output_box.configure(bg=bg, fg=fg)
        self.input_container.configure(fg_color=bg)
        self.output_container.configure(fg_color=bg)
        self.input_label.configure(text_color=fg)
        self.output_label.configure(text_color=fg)
        self.char_count_label.configure(text_color=secondary)
        self.input_scrollbar.configure(button_color=get_scroll_thumb_color())
        self.output_scrollbar.configure(button_color=get_scroll_thumb_color())

        # header buttons
        self.appearance_switch.configure(
            fg_color=get_button_secondary(), text_color=fg, hover_color=hover,
        )
        self.clear_btn.configure(
            fg_color=get_button_danger(), hover_color=DANGER_HOVER, text_color="#FFFFFF",
        )

        # outlined buttons
        for button in (self.detect_btn, self.copy_btn, self.tts_input_btn,
                       self.tts_output_btn, self.history_btn):
            button.configure(text_color=fg, border_color=border, hover_color=hover)
        self.cancel_btn.configure(text_color=fg, border_color=border, hover_color=DANGER_HOVER)
        self.translate_btn.configure(fg_color=get_button_primary(), hover_color=hover)

        # status bar
        self.status_frame.configure(fg_color=bg, border_color=border)
        self.confidence_label.configure(text_color=fg)
        self.detected_lang_label.configure(text_color=fg)
        self.progress_bar.configure(progress_color=get_button_primary())

    # --------------------- shutdown ---------------------
    def on_close(self):
        self._closing = True
        self._request_id += 1  # drop any result still on its way back
        # cancel every pending timer so none fires on a destroyed widget
        for job in (self._poll_job, self._detect_job, self._grammar_job, self._copy_job):
            if job:
                self.after_cancel(job)
        self.tts.stop()
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.grammar.close()
        self.quit()     # stop the event loop before tearing down widgets
        self.destroy()


def main():
    app = TranslatorApp()
    app.mainloop()
