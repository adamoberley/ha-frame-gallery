"""Recently-shown history, so pieces don't repeat until the pool is exhausted.

Persists the last N artwork keys (source:id) in /data; the picker skips anything
still in the window. This is the fix for the old art-changer's constant repeats.
"""
from __future__ import annotations

import json
import logging
import os

log = logging.getLogger("frame-gallery.state")

STATE_PATH = "/data/gallery-state.json"


class History:
    def __init__(self, cap: int) -> None:
        self.cap = max(0, cap)
        self.recent = self._load()

    def _load(self) -> list:
        if os.path.exists(STATE_PATH):
            try:
                with open(STATE_PATH, encoding="utf-8") as fh:
                    return list(json.load(fh).get("recent", []))
            except (OSError, ValueError):
                pass
        return []

    def seen(self, key: str) -> bool:
        return self.cap > 0 and key in self.recent

    def add(self, key: str) -> None:
        if self.cap <= 0:
            return
        if key in self.recent:
            self.recent.remove(key)
        self.recent.append(key)
        if len(self.recent) > self.cap:
            self.recent = self.recent[-self.cap:]
        tmp = STATE_PATH + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump({"recent": self.recent}, fh)
            os.replace(tmp, STATE_PATH)
        except OSError as exc:
            log.warning("could not persist history: %s", exc)
