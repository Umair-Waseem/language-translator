# ===================== HISTORY WINDOW =====================
# A modal window listing past translations, each reusable or deletable.

import customtkinter as ctk
from .config import (
    FONT_FAMILY, BUTTON_FONT, DANGER_HOVER, NEUTRAL_COLOR,
)
from .theme import (
    get_bg_color, get_text_color, get_border_color,
    get_button_primary, get_button_secondary, get_button_danger,
    get_hover_color, get_secondary_text_color, get_confidence_color,
)


class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, master, history_store, on_use):
        super().__init__(master)
        self.history_store = history_store
        self.on_use = on_use

        self.title("Translation History")
        self.geometry("800x548")
        self.transient(master)
        self.grab_set()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build()

    def _build(self):
        container = ctk.CTkFrame(self, fg_color=get_bg_color(), corner_radius=8)
        container.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        # header with title and controls
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="🕒 Translation History",
            font=(FONT_FAMILY, 18, "bold"),
            text_color=get_text_color(), anchor="w",
        ).grid(row=0, column=0, sticky="w")

        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            controls, text="🗑 Clear History", command=self._clear,
            width=140, height=30, font=BUTTON_FONT,
            fg_color=get_button_danger(), hover_color=DANGER_HOVER,
        ).grid(row=0, column=0, padx=(0, 10))

        ctk.CTkButton(
            controls, text="✖ Close", command=self.destroy,
            width=100, height=30, font=BUTTON_FONT,
            fg_color=get_button_secondary(), hover_color=get_hover_color(),
        ).grid(row=0, column=1)

        # scrollable list of cards
        self.scroll_frame = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # entry count footer
        self.status_label = ctk.CTkLabel(
            container, text="", font=(FONT_FAMILY, 12),
            text_color=get_secondary_text_color(),
        )
        self.status_label.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 15))

        self._render_cards()

    def refresh(self):
        # re-read the store so the list and count stay accurate while open
        self._render_cards()

    def _render_cards(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        entries = self.history_store.snapshot()
        for display_idx, entry in enumerate(reversed(entries)):
            self._create_card(entry, display_idx)

        self.status_label.configure(text=f"Entries: {len(entries)}")

    def _create_card(self, entry, display_idx):
        card = ctk.CTkFrame(
            self.scroll_frame, border_width=1, border_color=get_border_color(),
            corner_radius=8, fg_color=get_bg_color(),
        )
        card.grid(row=display_idx, column=0, sticky="ew", padx=5, pady=8)
        card.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        content.grid_columnconfigure(0, weight=1)

        self._card_header(content, entry)
        self._card_body(content, entry)
        self._card_footer(content, entry)
        return card

    def _card_header(self, parent, entry):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(
            header, text=entry["timestamp"], font=(FONT_FAMILY, 11, "italic"),
            anchor="w", text_color=get_secondary_text_color(),
        ).pack(side="left", fill="x", expand=True)

        lang_box = ctk.CTkFrame(header, fg_color="transparent")
        lang_box.pack(side="right", padx=(10, 0))

        # names can contain "(...)", so split off only the trailing "(code)"
        source = entry["source"].rsplit(" (", 1)[0]
        target = entry["target"].rsplit(" (", 1)[0]
        ctk.CTkLabel(
            lang_box, text=f"{source} → {target}", font=(FONT_FAMILY, 12, "bold"),
            anchor="e", text_color=get_text_color(),
        ).pack(side="right")

        if entry.get("noun_mode"):
            ctk.CTkLabel(
                lang_box, text="(Noun Mode)", font=(FONT_FAMILY, 10, "italic"),
                text_color=get_button_secondary(), anchor="e",
            ).pack(side="right", padx=(0, 5))

    def _card_body(self, parent, entry):
        body = ctk.CTkFrame(parent, fg_color="transparent")
        body.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        body.grid_columnconfigure(0, weight=1)

        self._labeled_text(body, 0, "Original:", entry["original"])
        self._labeled_text(body, 1, "Translated:", entry["translated"])

    def _labeled_text(self, parent, row, label, value):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame, text=label, font=(FONT_FAMILY, 11, "bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w")

        box = ctk.CTkTextbox(
            frame, height=90, font=(FONT_FAMILY, 11), wrap="word",
            border_width=1, border_color=get_border_color(), corner_radius=4,
            fg_color=get_bg_color(), text_color=get_text_color(),
        )
        box.insert("1.0", value)
        box.configure(state="disabled")
        box.grid(row=1, column=0, sticky="ew", pady=(5, 0))

    def _card_footer(self, parent, entry):
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        conf_box = ctk.CTkFrame(footer, fg_color="transparent")
        conf_box.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            conf_box, text="Confidence:", font=(FONT_FAMILY, 11, "bold"), anchor="w",
        ).pack(side="left", padx=(0, 5))

        conf_text, conf_color = self._confidence_display(entry["confidence"])
        ctk.CTkLabel(
            conf_box, text=conf_text, font=(FONT_FAMILY, 11),
            text_color=conf_color, anchor="w",
        ).pack(side="left")

        actions = ctk.CTkFrame(footer, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            actions, text="Use Translation", command=lambda: self.on_use(entry),
            width=140, height=30, font=BUTTON_FONT,
            fg_color=get_button_primary(), hover_color=get_hover_color(), corner_radius=8,
        ).grid(row=0, column=0, padx=(0, 10))

        ctk.CTkButton(
            actions, text="Delete", command=lambda e=entry: self._delete(e),
            width=100, height=30, font=BUTTON_FONT,
            fg_color=get_button_danger(), hover_color=DANGER_HOVER, corner_radius=8,
        ).grid(row=0, column=1)

    @staticmethod
    def _confidence_display(value):
        if value == -1:
            return "Not calculated", NEUTRAL_COLOR
        if value == 0:
            return "Failed", NEUTRAL_COLOR
        return f"{value}%", get_confidence_color(value)

    def _delete(self, entry):
        self.history_store.delete_entry(entry)
        self._render_cards()

    def _clear(self):
        self.history_store.clear()
        self.destroy()
