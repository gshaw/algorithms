"""Writes a test file so Jekyll publishes it unchanged.

Jekyll reads _data/*.json with its YAML parser, and YAML 1.1 reads a number like 1e-07,
with no decimal point, as a string. Writing 1.0e-07 keeps it a number.
"""

import json
import re

EXPONENT = re.compile(r'(?<=[\s\[:,])(-?\d+)e([-+]?\d+)(?=[\s,\]}])')


def dumps(data):
    return EXPONENT.sub(r"\1.0e\2", json.dumps(data, indent=2, ensure_ascii=False)) + "\n"
