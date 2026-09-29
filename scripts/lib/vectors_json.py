"""Writes a test file the way the site publishes it, byte for byte: indented two spaces,
with its keys in a fixed order, so it reads well in a browser or an editor.

Jekyll also reads the file, through the symlink in _data/vectors, with its YAML parser,
where a number like 1e-07 with no decimal point is a string. Writing 1.0e-07 keeps it a
number there too.
"""

import json
import re

EXPONENT = re.compile(r'(?<=[\s\[:,])(-?\d+)e([-+]?\d+)(?=[\s,\]}])')
FILE_ORDER = ["algorithm", "placeholder", "publishedDate", "expiresDate", "earthModel", "sources",
              "operations", "fields", "tolerances", "cases"]
CASE_ORDER = ["id", "operation", "tags", "note", "input", "expected"]


def ordered(item, order):
    assert set(item) <= set(order), set(item) - set(order)
    return {key: item[key] for key in order if key in item}


def add_notes(cases, notes):
    """Attaches each note to its case by id. A note for a case that isn't there is an error."""
    by_id = {case["id"]: case for case in cases}
    for case_id, note in notes.items():
        assert case_id in by_id, f"a note for a case that doesn't exist: {case_id}"
        by_id[case_id]["note"] = note


def dumps(data):
    data = ordered(data, FILE_ORDER)
    data["cases"] = [ordered(case, CASE_ORDER) for case in data.get("cases", [])]
    return EXPONENT.sub(r"\1.0e\2", json.dumps(data, indent=2, ensure_ascii=False)) + "\n"
