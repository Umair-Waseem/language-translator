# Unit tests for the pure-logic modules: no network, no GUI, no Java.

import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translator_app import detection, translation, languages
from translator_app.history import HistoryStore
from translator_app.grammar import GrammarChecker, _to_issue

# a representative slice of Google's code->name map for detection labels
CODE_TO_NAME = {
    "en": "English", "fr": "French", "de": "German", "es": "Spanish",
    "zh-CN": "Chinese (Simplified)", "ja": "Japanese", "ko": "Korean",
    "ar": "Arabic", "iw": "Hebrew",
}
VALID_CODES = set(CODE_TO_NAME)


class DetectionTests(unittest.TestCase):
    def test_empty_text_returns_auto(self):
        self.assertEqual(detection.detect("", CODE_TO_NAME), ("auto", ""))

    def test_chinese_script_maps_to_google_code(self):
        self.assertEqual(detection.detect("你好世界", CODE_TO_NAME).code, "zh-CN")

    def test_japanese_with_kanji_is_japanese_not_chinese(self):
        # kana presence must win over shared CJK ideographs
        self.assertEqual(detection.detect("私は日本語を話します", CODE_TO_NAME).code, "ja")

    def test_pure_kanji_falls_back_to_chinese(self):
        self.assertEqual(detection.detect("日本語", CODE_TO_NAME).code, "zh-CN")

    def test_korean_script(self):
        self.assertEqual(detection.detect("안녕하세요", CODE_TO_NAME).code, "ko")

    def test_arabic_script(self):
        self.assertEqual(detection.detect("مرحبا بالعالم", CODE_TO_NAME).code, "ar")

    def test_numbers_only(self):
        result = detection.detect("12345", CODE_TO_NAME)
        self.assertEqual(result.code, "auto")
        self.assertIn("numbers", result.message.lower())

    def test_too_short(self):
        self.assertEqual(detection.detect("hi", CODE_TO_NAME).code, "auto")

    def test_english_sentence(self):
        result = detection.detect("This is a clearly English sentence.", CODE_TO_NAME)
        self.assertEqual(result.code, "en")
        self.assertIn("English", result.message)

    def test_french_sentence(self):
        result = detection.detect("Bonjour tout le monde comment allez vous", CODE_TO_NAME)
        self.assertEqual(result.code, "fr")

    def test_is_latin_text(self):
        self.assertTrue(detection.is_latin_text("hello world"))
        self.assertFalse(detection.is_latin_text("你好世界"))


class LanguageCodeTests(unittest.TestCase):
    def test_generic_chinese_alias(self):
        self.assertEqual(languages.to_google_code("zh", VALID_CODES), "zh-CN")

    def test_simplified_chinese_alias(self):
        self.assertEqual(languages.to_google_code("zh-cn", VALID_CODES), "zh-CN")

    def test_hebrew_alias(self):
        self.assertEqual(languages.to_google_code("he", VALID_CODES), "iw")

    def test_valid_code_unchanged(self):
        self.assertEqual(languages.to_google_code("en", VALID_CODES), "en")

    def test_unknown_code_falls_back_to_auto(self):
        self.assertEqual(languages.to_google_code("xx-unknown", VALID_CODES), "auto")

    def test_empty_code_falls_back_to_auto(self):
        self.assertEqual(languages.to_google_code("", VALID_CODES), "auto")


class ConfidenceTests(unittest.TestCase):
    def test_identical_long_text_scores_full(self):
        text = "this is a much longer identical sentence used to verify the score"
        self.assertEqual(translation.confidence(text, text), 100)

    def test_identical_short_text_is_length_penalized(self):
        # short text cannot reach 100 by design (length factor)
        self.assertLess(translation.confidence("hello world", "hello world"), 100)

    def test_score_within_bounds(self):
        self.assertTrue(0 <= translation.confidence("abc", "xyz") <= 100)

    def test_looks_untranslated(self):
        self.assertTrue(translation.looks_untranslated("Hotel", "Hotel"))
        self.assertFalse(translation.looks_untranslated("cat", "un chat tres different"))

    def test_base_lang(self):
        self.assertEqual(translation._base_lang("zh-CN"), "zh")


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.path = tempfile.mktemp(suffix=".json")
        self.store = HistoryStore(path=self.path, max_size=3)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_load_empty_when_missing(self):
        self.assertEqual(self.store.load(), [])
        self.assertTrue(self.store.is_empty())

    def test_add_and_trim_to_max_size(self):
        for i in range(4):
            self.store.add({"id": i})
        self.assertEqual([e["id"] for e in self.store.snapshot()], [1, 2, 3])

    def test_persist_and_reload(self):
        self.store.add({"id": "a"})
        reloaded = HistoryStore(path=self.path, max_size=3)
        reloaded.load()
        self.assertEqual([e["id"] for e in reloaded.snapshot()], ["a"])

    def test_delete_entry_by_value(self):
        a, b = {"id": "a"}, {"id": "b"}
        self.store.add(a)
        self.store.add(b)
        self.store.delete_entry(a)
        self.assertEqual([e["id"] for e in self.store.snapshot()], ["b"])

    def test_delete_missing_entry_is_noop(self):
        self.store.add({"id": "a"})
        self.store.delete_entry({"id": "does-not-exist"})
        self.assertEqual(len(self.store.snapshot()), 1)

    def test_clear_removes_file(self):
        self.store.add({"id": "a"})
        self.store.clear()
        self.assertTrue(self.store.is_empty())
        self.assertFalse(os.path.exists(self.path))

    def test_snapshot_is_a_copy(self):
        self.store.add({"id": "a"})
        snap = self.store.snapshot()
        snap.append({"id": "b"})
        self.assertEqual(len(self.store.snapshot()), 1)

    def test_corrupt_file_is_tolerated(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{ not valid json")
        self.store.load()
        self.assertEqual(self.store.snapshot(), [])

    def test_load_enforces_max_size(self):
        # an oversized file must be trimmed to the newest entries on load
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([{"id": i} for i in range(10)], f)
        self.store.load()
        self.assertEqual([e["id"] for e in self.store.snapshot()], [7, 8, 9])


class _FakeMatch:
    # mimics a language-tool-python Match; snake toggles the attribute name
    def __init__(self, offset, length, message, replacements, snake=True):
        self.offset = offset
        self.message = message
        self.replacements = replacements
        if snake:
            self.error_length = length
        else:
            self.errorLength = length


class _FakeTool:
    def __init__(self, matches):
        self._matches = matches

    def check(self, text):
        return self._matches


class GrammarTests(unittest.TestCase):
    def test_issue_mapping_snake_case(self):
        issue = _to_issue(_FakeMatch(4, 2, "bad", ["good"], snake=True))
        self.assertEqual((issue.offset, issue.length, issue.message), (4, 2, "bad"))
        self.assertEqual(issue.replacements, ["good"])

    def test_issue_mapping_camel_case_fallback(self):
        issue = _to_issue(_FakeMatch(1, 5, "x", [], snake=False))
        self.assertEqual(issue.length, 5)

    def test_check_maps_raw_matches_to_issues(self):
        checker = GrammarChecker()
        checker._tool_for = lambda code: _FakeTool([_FakeMatch(0, 3, "m", ["r"])])
        issues = checker.check("some text", "en")
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].length, 3)

    def test_unsupported_language_returns_empty(self):
        checker = GrammarChecker()
        self.assertEqual(checker.check("bonjour", "fr"), [])
        self.assertFalse(checker.supports("fr"))
        self.assertTrue(checker.supports("en"))

    def test_close_prevents_new_tools(self):
        # after shutdown no tool is created, so checks return empty without Java
        checker = GrammarChecker()
        checker.close()
        self.assertIsNone(checker._tool_for("en"))
        self.assertEqual(checker.check("hello world test", "en"), [])

    def test_failed_init_degrades_gracefully(self):
        import translator_app.grammar as grammar_module

        class _Boom:
            def __init__(self, *a, **k):
                raise RuntimeError("no java")

        original = grammar_module.language_tool_python.LanguageTool
        grammar_module.language_tool_python.LanguageTool = _Boom
        try:
            checker = GrammarChecker()
            self.assertEqual(checker.check("test one two", "en"), [])
            self.assertEqual(checker.check("test again", "en"), [])  # cached, no retry
        finally:
            grammar_module.language_tool_python.LanguageTool = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
