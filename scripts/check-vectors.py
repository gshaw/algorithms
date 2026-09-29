"""Checks that every test file the site publishes equals its source in _data/vectors.

Run after the build. Catches Jekyll's YAML reading turning a number into a string.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
bad = 0
files = sorted((ROOT / "_data" / "vectors").glob("*.json"))
for source in files:
    published = ROOT / "_site" / source.stem / "vectors.json"
    if json.loads(source.read_text()) != json.loads(published.read_text()):
        print(f"{published.relative_to(ROOT)} differs from {source.relative_to(ROOT)}")
        bad += 1
print(f"Compared {len(files)} published test files with their sources: {'all match' if not bad else f'{bad} differ'}")
sys.exit(1 if bad else 0)
