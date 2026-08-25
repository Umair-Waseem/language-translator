# ===================== GRAMMAR CHECKING =====================
# Lazily starts LanguageTool so a missing Java runtime never crashes startup.

from collections import namedtuple
import threading
import language_tool_python
from .config import GRAMMAR_LANGUAGES

# a simple, library-agnostic view of one grammar issue
Issue = namedtuple("Issue", "offset length message replacements")


def _to_issue(match):
    # language-tool-python renamed errorLength -> error_length; support both
    length = getattr(match, "error_length", None)
    if length is None:
        length = getattr(match, "errorLength", 0)
    return Issue(match.offset, length, match.message, list(match.replacements))


class GrammarChecker:
    def __init__(self):
        self._tools = {}           # base language -> LanguageTool instance
        self._unavailable = set()  # languages we already failed to load
        self._closed = False       # set on shutdown so no new tool is started
        self._lock = threading.Lock()  # checks run on worker threads

    def _tool_for(self, lang_code):
        base = lang_code.split("-")[0].lower()
        if base not in GRAMMAR_LANGUAGES:
            return None
        # serialize creation so concurrent checks never start two Java servers
        with self._lock:
            if self._closed or base in self._unavailable:
                return None
            if base not in self._tools:
                try:
                    self._tools[base] = language_tool_python.LanguageTool(GRAMMAR_LANGUAGES[base])
                except Exception as e:
                    # Java missing or download failed; disable this language and move on
                    print(f"Grammar checking unavailable for '{base}': {e}")
                    self._unavailable.add(base)
                    return None
            return self._tools[base]

    def check(self, text, lang_code):
        # returns a list of Issue objects, or [] when unavailable
        tool = self._tool_for(lang_code)
        if not tool:
            return []
        try:
            return [_to_issue(match) for match in tool.check(text)]
        except Exception as e:
            print(f"Grammar check error: {e}")
            return []

    def supports(self, lang_code):
        return lang_code.split("-")[0].lower() in GRAMMAR_LANGUAGES

    def close(self):
        # take the tools under the lock so a running check cannot mutate the dict
        with self._lock:
            self._closed = True
            tools = list(self._tools.values())
            self._tools.clear()
        for tool in tools:
            try:
                tool.close()
            except Exception:
                pass
