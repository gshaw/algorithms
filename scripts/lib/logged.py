"""Logged calls to USNO's API and to reference programs, so a test file can be rebuilt
from its committed logs without the network or the program (--offline)."""

import json
import sys
import time
import urllib.request
from pathlib import Path

OFFLINE = "--offline" in sys.argv


class USNO:
    """USNO's responses, kept in a JSON Lines log: one {"url", "response"} per line."""

    def __init__(self, path: Path):
        self.path = path
        self.cache = {}
        self.used = []
        if path.exists():
            for line in path.read_text().splitlines():
                entry = json.loads(line)
                self.cache[entry["url"]] = entry["response"]

    def get(self, url):
        if url not in self.cache:
            assert not OFFLINE, f"not in the log: {url}"
            for attempt in range(5):
                try:
                    with urllib.request.urlopen(url, timeout=60) as response:
                        self.cache[url] = json.load(response)
                    break
                except OSError:
                    if attempt == 4:
                        raise
                    time.sleep(5 * (attempt + 1))
            time.sleep(0.3)
        self.used.append(url)
        return self.cache[url]

    def save(self):
        if not OFFLINE:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("".join(json.dumps({"url": u, "response": self.cache[u]}, sort_keys=True) + "\n"
                                         for u in dict.fromkeys(self.used)))


class Program:
    """A reference program's answers, logged as `key => answer` lines under a header."""

    def __init__(self, path: Path, header: str):
        self.path = path
        self.header = header
        self.answers = {}
        self.lines = []
        if OFFLINE:
            for line in path.read_text().splitlines():
                if not line.startswith("#"):
                    key, answer = line.split(" => ", 1)
                    self.answers[key] = answer

    def call(self, key, compute):
        """compute() returns the answer as a string, when not offline."""
        answer = self.answers[key] if OFFLINE else compute()
        self.lines.append(f"{key} => {answer}")
        return answer

    def save(self):
        if not OFFLINE:
            self.path.write_text(f"# {self.header}\n" + "\n".join(self.lines) + "\n")
