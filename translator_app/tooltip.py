# ===================== GRAMMAR TOOLTIP =====================
# Shows a single hover tooltip describing the grammar issue under the cursor.

import tkinter as tk
from .config import FONT_FAMILY, TOOLTIP_TIMEOUT_MS
from .theme import get_bg_color, get_text_color, get_border_color


class GrammarTooltip:
    def __init__(self, root):
        self.root = root
        self._window = None
        self._after_id = None
        self._message = None  # what the visible tooltip currently says

    def clear(self):
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self._window is not None:
            self._window.destroy()
            self._window = None
        self._message = None

    def show(self, x_root, y_root, message):
        # mouse motion repeats, so do not rebuild a tooltip that already says this
        if self._window is not None and message == self._message:
            return
        self.clear()
        window = tk.Toplevel(self.root)
        window.wm_overrideredirect(True)
        window.wm_geometry(f"+{int(x_root) + 15}+{int(y_root) + 15}")

        label = tk.Label(
            window,
            text=message,
            background=get_bg_color(),
            foreground=get_text_color(),
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=8,
            font=(FONT_FAMILY, 10),
            wraplength=300,
            highlightbackground=get_border_color(),
            highlightthickness=1,
            justify="left",
        )
        label.pack()
        label.bind("<Leave>", lambda e: self.clear())
        self._window = window
        self._message = message
        self._after_id = self.root.after(TOOLTIP_TIMEOUT_MS, self.clear)
