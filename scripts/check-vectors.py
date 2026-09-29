"""Checks that every test file lives beside its page, that _data/vectors links to it for
the page to read, and that the site publishes it byte for byte. Run after the build."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
bad = 0
links = sorted((ROOT / "_data" / "vectors").glob("*.json"))
for link in links:
    source = ROOT / link.stem / "vectors.json"
    published = ROOT / "_site" / link.stem / "vectors.json"
    if not link.is_symlink() or link.resolve() != source.resolve():
        print(f"{link.relative_to(ROOT)} should be a symlink to {source.relative_to(ROOT)}")
        bad += 1
    elif published.read_bytes() != source.read_bytes():
        print(f"{published.relative_to(ROOT)} isn't {source.relative_to(ROOT)} byte for byte")
        bad += 1
print(f"Checked {len(links)} test files: {'all published verbatim' if not bad else f'{bad} wrong'}")
sys.exit(1 if bad else 0)
