# Integration tests for the TranslatorApp window.
# The network, audio, and grammar are mocked; tests skip when no display exists.
# Note: customtkinter may print harmless "invalid command name ... (after script)"
# messages on stderr as windows are torn down; they are not test failures.

import os
import sys
import time
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk

from translator_app.grammar import Issue

# small deterministic language map used in place of the network fetch;
# includes a parenthesized name to guard the history round-trip parsing
FAKE_MAPS = (
    {"en": "English", "es": "Spanish", "fr": "French", "zh-CN": "Chinese (Simplified)"},
    {"English": "en", "Spanish": "es", "French": "fr", "Chinese (Simplified)": "zh-CN"},
    ["Chinese (Simplified)", "English", "French", "Spanish", "Auto Detect"],
)


class _FakeTTS:
    # records requests instead of opening an audio device
    def __init__(self):
        self.spoken = []

    def speak(self, text, lang_code, on_error=None):
        self.spoken.append((text, lang_code))

    def stop(self):
        pass


class _FakeGrammar:
    # never touches Java; reports no issues
    def __init__(self):
        pass

    def check(self, text, lang_code):
        return []

    def supports(self, lang_code):
        return lang_code.split("-")[0].lower() == "en"

    def close(self):
        pass


def _fake_translate(text, source_code, target_code, valid_codes, noun_mode=False):
    # uppercases the text; resolves codes exactly like the real function
    from translator_app.languages import to_google_code, AUTO
    source = to_google_code(source_code, valid_codes) if source_code != AUTO else AUTO
    target = to_google_code(target_code, valid_codes)
    return f"<{text.upper()}>", source, target


def _fake_back_translate(text, source, target):
    return text.strip("<>").lower()


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.mkdtemp()
        os.chdir(self._tmp)  # isolate the history file from the repo

        patchers = [
            mock.patch("translator_app.app.load_language_maps", return_value=FAKE_MAPS),
            mock.patch("translator_app.app.TextToSpeech", _FakeTTS),
            mock.patch("translator_app.app.GrammarChecker", _FakeGrammar),
            mock.patch("translator_app.translation.apply_network_timeout", lambda: None),
            mock.patch("translator_app.translation.translate", _fake_translate),
            mock.patch("translator_app.translation.back_translate", _fake_back_translate),
        ]
        for p in patchers:
            p.start()
            self.addCleanup(p.stop)

        from translator_app.app import TranslatorApp
        try:
            self.app = TranslatorApp()
        except tk.TclError as e:
            self.skipTest(f"no display available: {e}")
        self.addCleanup(self._destroy_app)
        self.app.update()

    def _destroy_app(self):
        try:
            self.app.on_close()
        except Exception:
            pass
        os.chdir(self._cwd)

    def _pump_until(self, predicate, timeout=5.0):
        # drive the event loop until predicate() is true or time runs out
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.app.update()
            if predicate():
                return True
            time.sleep(0.02)
        return False

    def test_starts_with_expected_defaults(self):
        self.assertEqual(self.app.source_combo.get(), "Auto Detect")
        self.assertEqual(self.app.target_combo.get(), "English")

    def test_detects_language(self):
        self.app._set_input("This is an English sentence for detection.")
        self.assertEqual(self.app.detect_language(), "en")
        self.assertIn("English", self.app.detected_lang_label.cget("text"))

    def test_translation_updates_output_and_history(self):
        self.app._set_input("hello there")
        self.app.source_combo.set("English")
        self.app.target_combo.set("Spanish")
        self.app.translate()
        self.assertTrue(self._pump_until(
            lambda: self.app.output_box.get("1.0", "end-1c") == "<HELLO THERE>"))
        self.assertEqual(self.app.translate_btn.cget("state"), "normal")
        self.assertEqual(str(self.app.cancel_btn.cget("state")), "disabled")
        entries = self.app.history.snapshot()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["original"], "hello there")
        self.assertEqual(entries[0]["translated"], "<HELLO THERE>")
        self.assertGreaterEqual(entries[0]["confidence"], 0)

    def test_confidence_note_when_source_unknown(self):
        # detection of very short text yields 'auto', so no back-translation is possible
        self.app._set_input("ok")
        self.app.source_combo.set("Auto Detect")
        self.app.target_combo.set("Spanish")
        self.app.translate()
        self.assertTrue(self._pump_until(
            lambda: "unknown source" in self.app.confidence_label.cget("text").lower()))
        self.assertEqual(self.app.history.snapshot()[0]["confidence"], -1)

    def test_rejects_text_that_is_too_long(self):
        self.app._set_input("a" * 6000)
        self.app.translate()
        self.app.update()
        self.assertIn("too long", self.app.output_box.get("1.0", "end-1c").lower())

    def test_rejects_symbols_only(self):
        self.app._set_input("123 !!!")
        self.app.translate()
        self.app.update()
        self.assertIn("numbers", self.app.output_box.get("1.0", "end-1c").lower())

    def test_swap_exchanges_text_after_a_translation(self):
        self.app.source_combo.set("English")
        self.app.target_combo.set("Spanish")
        self.app._set_input("hello")
        self.app.translate()
        self.assertTrue(self._pump_until(
            lambda: self.app.output_box.get("1.0", "end-1c") == "<HELLO>"))
        self.app.swap_languages()
        self.app.update()
        self.assertEqual(self.app.source_combo.get(), "Spanish")
        self.assertEqual(self.app.target_combo.get(), "English")
        self.assertEqual(self.app.input_box.get("1.0", "end-1c"), "<HELLO>")
        self.assertEqual(self.app.output_box.get("1.0", "end-1c"), "hello")

    def test_swap_keeps_typed_text_when_no_translation_exists(self):
        # swapping before translating must not move the typed text out of reach
        self.app.source_combo.set("English")
        self.app.target_combo.set("Spanish")
        self.app._set_input("my typed sentence")
        self.app.swap_languages()
        self.app.update()
        self.assertEqual(self.app.input_box.get("1.0", "end-1c"), "my typed sentence")
        self.assertEqual(self.app.source_combo.get(), "Spanish")
        self.assertEqual(self.app.target_combo.get(), "English")

    def test_swap_does_not_move_an_error_message_into_the_input(self):
        self.app.source_combo.set("English")
        self.app.target_combo.set("Spanish")
        self.app._set_input("hello")
        self.app._show_error("Error: Network error.")
        self.app.swap_languages()
        self.app.update()
        self.assertEqual(self.app.input_box.get("1.0", "end-1c"), "hello")

    def test_audio_and_copy_ignore_error_messages(self):
        self.app._show_error("Error: Network error.")
        self.app._speak_output()
        self.assertEqual(self.app.tts.spoken, [])
        self.app.copy_btn.configure(text="Copy")
        self.app.copy_output()
        self.assertEqual(self.app.copy_btn.cget("text"), "Copy")

    def test_clear_resets_state(self):
        self.app._set_input("something")
        self.app.clear_all()
        self.app.update()
        self.assertEqual(self.app.input_box.get("1.0", "end-1c"), "")
        self.assertEqual(self.app.source_combo.get(), "Auto Detect")
        self.assertEqual(self.app.target_combo.get(), "English")
        self.assertEqual(self.app.char_count_label.cget("text"), "Chars: 0")

    def test_theme_toggle_changes_button_label(self):
        before = self.app.appearance_switch.cget("text")
        self.app.toggle_theme()
        self.app.update()
        self.assertNotEqual(before, self.app.appearance_switch.cget("text"))

    def test_history_window_opens_and_closes(self):
        self.app.history.add({
            "timestamp": "2026-01-01 00:00:00", "source": "English (en)",
            "target": "Spanish (es)", "original": "hi", "translated": "<HI>",
            "confidence": 90, "noun_mode": False,
        })
        self.app.open_history()
        self.app.update()
        tops = [w for w in self.app.winfo_children() if isinstance(w, tk.Toplevel)]
        self.assertGreaterEqual(len(tops), 1)
        for w in tops:
            w.destroy()
        self.app.update()

    def test_speak_input_with_auto_detect_uses_detected_code(self):
        self.app._set_input("This is an English sentence for detection.")
        self.app.source_combo.set("Auto Detect")
        self.app._speak_input()
        self.assertEqual(self.app.tts.spoken[-1][1], "en")

    def test_history_restore_handles_parenthesized_names(self):
        # "Chinese (Simplified)" must survive the round-trip through "Name (code)"
        self.app.history.add({
            "timestamp": "2026-01-01 00:00:00", "source": "English (en)",
            "target": "Chinese (Simplified) (zh-CN)", "original": "hello",
            "translated": "<HELLO>", "confidence": 90, "noun_mode": False,
        })
        self.app._use_history_entry(self.app.history.snapshot()[0])
        self.app.update()
        self.assertEqual(self.app.source_combo.get(), "English")
        self.assertEqual(self.app.target_combo.get(), "Chinese (Simplified)")

    def test_auto_detect_not_offered_as_target(self):
        self.assertNotIn("Auto Detect", self.app.target_combo.cget("values"))
        self.assertIn("Auto Detect", self.app.source_combo.cget("values"))

    def test_input_grammar_runs_for_english(self):
        calls = []
        self.app._schedule_grammar = lambda widget, text, code: calls.append(code)
        self.app.source_combo.set("English")
        self.app._set_input("This is an english sentence that should be checked.")
        self.app._auto_grammar()
        self.assertEqual(calls, ["en"])

    def test_input_grammar_skips_non_english_under_auto_detect(self):
        calls = []
        self.app._schedule_grammar = lambda widget, text, code: calls.append(code)
        self.app.source_combo.set("Auto Detect")
        self.app._set_input("Bonjour tout le monde comment allez vous aujourd hui")
        self.app._auto_grammar()
        self.assertEqual(calls, [])

    def test_grammar_results_are_dropped_when_input_changes(self):
        # stale offsets would otherwise describe the wrong words on hover
        text = "She go home"
        self.app._set_input(text)
        self.app._apply_grammar(self.app.input_box, text, [Issue(4, 2, "Verb error", ["goes"])])
        self.assertIn(self.app.input_box, self.app._matches)
        self.app.input_box.insert("1.0", "Yesterday ")
        self.app._on_key_release()
        self.assertNotIn(self.app.input_box, self.app._matches)
        self.assertEqual(self.app.input_box.tag_ranges("mistake"), ())

    def test_grammar_results_are_dropped_when_output_changes(self):
        text = "He go home"
        self.app._set_output(text)
        self.app._apply_grammar(self.app.output_box, text, [Issue(3, 2, "Verb error", ["goes"])])
        self.assertIn(self.app.output_box, self.app._matches)
        self.app._set_output("a completely different result")
        self.assertNotIn(self.app.output_box, self.app._matches)

    def test_newer_translation_supersedes_a_slower_older_one(self):
        # a slow earlier request must never overwrite the newer result
        def staged(text, source_code, target_code, valid_codes, noun_mode=False):
            if text == "slow":
                time.sleep(1.0)
                return "<SLOW>", "en", "es"
            return "<FAST>", "en", "es"

        with mock.patch("translator_app.translation.translate", staged):
            self.app.source_combo.set("English")
            self.app.target_combo.set("Spanish")
            self.app._set_input("slow")
            self.app.translate()
            time.sleep(0.1)
            self.app._set_input("fast")
            self.app.translate()
            self.assertTrue(self._pump_until(
                lambda: self.app.output_box.get("1.0", "end-1c") == "<FAST>"))
            # the slow result arrives later and must be discarded
            self.assertFalse(self._pump_until(
                lambda: self.app.output_box.get("1.0", "end-1c") == "<SLOW>", timeout=2.0))
        self.assertEqual([e["translated"] for e in self.app.history.snapshot()], ["<FAST>"])

    def test_cancel_restores_ui_and_discards_the_late_result(self):
        def slow(text, source_code, target_code, valid_codes, noun_mode=False):
            time.sleep(1.0)
            return "<LATE>", "en", "es"

        with mock.patch("translator_app.translation.translate", slow):
            self.app.source_combo.set("English")
            self.app.target_combo.set("Spanish")
            self.app._set_input("hello")
            self.app.translate()
            self.app.update()
            self.app.cancel_translation()
            self.app.update()
            # the UI recovers at once instead of waiting for the network call
            self.assertIn("cancelled", self.app.output_box.get("1.0", "end-1c").lower())
            self.assertEqual(self.app.translate_btn.cget("state"), "normal")
            self.assertFalse(self._pump_until(
                lambda: "<LATE>" in self.app.output_box.get("1.0", "end-1c"), timeout=2.0))
        self.assertTrue(self.app.history.is_empty())


if __name__ == "__main__":
    unittest.main(verbosity=2)
