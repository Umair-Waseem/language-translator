# ===================== HISTORY STORE =====================
# Loads, trims, and persists translation history to a JSON file.

import os
import json
import threading
from .config import HISTORY_FILE, MAX_HISTORY_SIZE

# fields every usable record must provide as text
_REQUIRED_FIELDS = ("timestamp", "source", "target", "original", "translated")


def _clean_entry(entry):
    # returns a usable copy of a stored record, or None when it is damaged
    if not isinstance(entry, dict):
        return None
    if not all(isinstance(entry.get(field), str) for field in _REQUIRED_FIELDS):
        return None
    cleaned = dict(entry)
    score = cleaned.get("confidence")
    # a non-numeric score would break the history window, so treat it as unknown
    valid_score = isinstance(score, int) and not isinstance(score, bool)
    cleaned["confidence"] = score if valid_score else -1
    cleaned["noun_mode"] = bool(cleaned.get("noun_mode"))
    return cleaned


class HistoryStore:
    def __init__(self, path=HISTORY_FILE, max_size=MAX_HISTORY_SIZE):
        self.path = path
        self.max_size = max_size
        self.entries = []
        self._lock = threading.Lock()  # add() runs on worker threads

    def load(self):
        # read persisted history, tolerating a missing or corrupt file
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # drop damaged records so one bad entry cannot break the window
                        usable = [e for e in map(_clean_entry, data) if e is not None]
                        # an oversized file would otherwise stay oversized forever
                        self.entries = usable[-self.max_size:]
        except Exception as e:
            print(f"Error loading history: {e}")
            self.entries = []
        return self.entries

    def snapshot(self):
        # a copy safe to iterate on the UI thread while workers append
        with self._lock:
            return list(self.entries)

    def is_empty(self):
        with self._lock:
            return not self.entries

    def add(self, entry):
        # refuse a record that could not be reloaded or displayed later
        cleaned = _clean_entry(entry)
        if cleaned is None:
            print("Ignoring malformed history entry")
            return
        with self._lock:
            self.entries.append(cleaned)
            if len(self.entries) > self.max_size:
                self.entries.pop(0)
            self._save()

    def delete_entry(self, entry):
        # delete by value so it stays correct even if the list changed meanwhile
        with self._lock:
            try:
                self.entries.remove(entry)
                self._save()
            except ValueError:
                pass

    def clear(self):
        with self._lock:
            self.entries = []
            try:
                if os.path.exists(self.path):
                    os.remove(self.path)
            except OSError as e:
                print(f"Error clearing history: {e}")

    def _save(self):
        # called with the lock already held
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"Error saving history: {e}")
