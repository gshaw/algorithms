"""Builds the cases in _data/vectors/wmm.json from the raw files in wmm/sources.

The words (sources, operations, fields, tolerances) are edited in the JSON by hand;
this replaces only `cases` and `publishedDate`. Every expected value is copied from
NOAA's published tables or from NOAA's own library, run by generate.sh.

  build.py                    rebuild the cases
  build.py --published-inputs print NOAA's published inputs for the reference program
  build.py --verify           read the reference program's output for those inputs on
                              stdin and check it against NOAA's tables
"""

import datetime
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import vectors_json  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "wmm" / "sources"
VECTORS = ROOT / "wmm" / "vectors.json"


def number(text):
    """A number as the source wrote it: 89 stays whole, 80.0 stays a decimal."""
    return int(text) if re.fullmatch(r"-?\d+", text) else float(text)


def rows(path):
    return [line.split() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]


def blackout(h):
    # NOAA's thresholds, from the WMM military specification. A published H within
    # the tolerance of one would make the expected blackout depend on rounding.
    assert abs(h - 2000) > 1 and abs(h - 6000) > 1, h
    return "unreliable" if h < 2000 else "caution" if h < 6000 else "none"


def tags(first, latitude, extra=()):
    result = [first, *extra]
    if abs(latitude) >= 80:
        result.append("polar")
    return result


def table_cases():
    """WMM2025_TEST_VALUES.txt: the table in NOAA's test values PDF, 12 rows."""
    cases = []
    for i, r in enumerate(rows(SOURCES / "WMM2025_TEST_VALUES.txt"), 1):
        year, height, lat, lon, x, y, z, h, f, incl, decl, gv = r[:12]
        cases.append({
            "id": f"noaa-table-{i}",
            "operation": "field",
            "tags": tags("published", float(lat)),
            "input": {
                "latitudeInDegrees": number(lat),
                "longitudeInDegrees": number(lon),
                "heightInKilometers": number(height),
                "decimalYear": number(year),
            },
            "expected": {
                "magneticDeclinationInDegrees": number(decl),
                "inclinationInDegrees": number(incl),
                "northIntensityInNanoteslas": number(x),
                "eastIntensityInNanoteslas": number(y),
                "downIntensityInNanoteslas": number(z),
                "horizontalIntensityInNanoteslas": number(h),
                "totalIntensityInNanoteslas": number(f),
                "gridVariationInDegrees": None if gv == "NaN" else number(gv),
                "blackout": blackout(float(h)),
            },
        })
    return cases


def points_cases():
    """WMM2025_TestValues.txt: 100 points from 2025.0 to 2029.5, in NOAA's coefficient zip.
    It has no grid variation, so none is expected."""
    cases = []
    for i, r in enumerate(rows(SOURCES / "WMM2025_TestValues.txt"), 1):
        year, height, lat, lon, decl, incl, h, x, y, z, f = r[:11]
        level = blackout(float(h))
        cases.append({
            "id": f"noaa-points-{i}",
            "operation": "field",
            "tags": tags("published", float(lat), ["edge"] if level != "none" else []),
            "input": {
                "latitudeInDegrees": number(lat),
                "longitudeInDegrees": number(lon),
                "heightInKilometers": number(height),
                "decimalYear": float(year),
            },
            "expected": {
                "magneticDeclinationInDegrees": number(decl),
                "inclinationInDegrees": number(incl),
                "northIntensityInNanoteslas": number(x),
                "eastIntensityInNanoteslas": number(y),
                "downIntensityInNanoteslas": number(z),
                "horizontalIntensityInNanoteslas": number(h),
                "totalIntensityInNanoteslas": number(f),
                "blackout": level,
            },
        })
    return cases


def grid_variation(latitude, gv):
    """NOAA's grid variation, null between 55° S and 55° N, wrapped to (−180, 180]
    as NOAA's table gives it."""
    if -55 < latitude < 55:
        return None
    gv = math.fmod(gv, 360)
    if gv > 180:
        gv -= 360
    elif gv <= -180:
        gv += 360
    return round(gv, 6)


REFERENCE_NAMES = {
    (90.0, 2026.0): "north-pole-2026",
    (-90.0, 2026.0): "south-pole-2026",
    (90.0, 2029.5): "north-pole-2029-5",
    (-90.0, 2029.5): "south-pole-2029-5",
    (49.3, 2025.0): "first-instant",
    (49.3, 2030.0): "last-instant",
    (55.0, 2026.0): "grid-variation-55n",
    (-55.0, 2026.0): "grid-variation-55s",
}


def reference_cases():
    """reference-output.txt: NOAA's library run by generate.sh on reference-input.txt."""
    cases = []
    for r in rows(SOURCES / "reference-output.txt"):
        if r[0] == "field":
            lat, lon, height, year = (float(v) for v in r[1:5])
            v = dict(zip(r[5::2], (float(n) for n in r[6::2])))
            name = REFERENCE_NAMES[(lat, year)]
            cases.append({
                "id": f"reference-{name}",
                "operation": "field",
                "tags": tags("reference", lat, ["edge"]),
                "input": {
                    "latitudeInDegrees": lat,
                    "longitudeInDegrees": lon,
                    "heightInKilometers": height,
                    "decimalYear": year,
                },
                "expected": {
                    "magneticDeclinationInDegrees": v["D"],
                    "inclinationInDegrees": v["I"],
                    "northIntensityInNanoteslas": v["X"],
                    "eastIntensityInNanoteslas": v["Y"],
                    "downIntensityInNanoteslas": v["Z"],
                    "horizontalIntensityInNanoteslas": v["H"],
                    "totalIntensityInNanoteslas": v["F"],
                    "gridVariationInDegrees": grid_variation(lat, v["GV"]),
                    "blackout": blackout(v["H"]),
                },
            })
        elif r[0] == "date":
            date, value = r[1], r[2]
            if value == "invalid":
                cases.append({
                    "id": f"reference-date-{date}",
                    "operation": "decimalYear",
                    "tags": ["reference", "invalid"],
                    "input": {"date": date},
                    "expected": {"error": "invalidInput"},
                })
            else:
                cases.append({
                    "id": f"reference-date-{date}",
                    "operation": "decimalYear",
                    "tags": ["reference", "edge"],
                    "input": {"date": date},
                    "expected": {"decimalYear": round(float(value), 10)},
                })
    return cases


def invalid_cases():
    """Input outside the ranges in the file's fields, which must be refused."""
    base = {"latitudeInDegrees": 49.3, "longitudeInDegrees": -123.1, "heightInKilometers": 0, "decimalYear": 2026.0}
    return [
        {
            "id": f"invalid-{name}",
            "operation": "field",
            "tags": ["invalid"],
            "input": {**base, **change},
            "expected": {"error": "outOfRange"},
        }
        for name, change in [
            ("latitude-90-5", {"latitudeInDegrees": 90.5}),
            ("before-2025", {"decimalYear": 2024.99}),
            ("after-2030", {"decimalYear": 2030.01}),
        ]
    ]


def published_inputs():
    for case in table_cases() + points_cases():
        i = case["input"]
        print("field", i["latitudeInDegrees"], i["longitudeInDegrees"], i["heightInKilometers"], i["decimalYear"])


def verify():
    """NOAA's library against NOAA's tables, within the file's tolerances."""
    tolerances = {k: float(v) for k, v in json.loads(VECTORS.read_text())["tolerances"].items()}
    keys = {
        "D": "magneticDeclinationInDegrees", "I": "inclinationInDegrees",
        "X": "northIntensityInNanoteslas", "Y": "eastIntensityInNanoteslas",
        "Z": "downIntensityInNanoteslas", "H": "horizontalIntensityInNanoteslas",
        "F": "totalIntensityInNanoteslas", "GV": "gridVariationInDegrees",
    }
    lines = [line.split() for line in sys.stdin if line.startswith("field")]
    cases = table_cases() + points_cases()
    assert len(lines) == len(cases), (len(lines), len(cases))
    worst = {}
    for case, r in zip(cases, lines):
        lat = float(r[1])
        got = {keys[k]: float(v) for k, v in zip(r[5::2], r[6::2])}
        got["gridVariationInDegrees"] = grid_variation(lat, got["gridVariationInDegrees"])
        for field, want in case["expected"].items():
            if field == "blackout":
                assert blackout(got["horizontalIntensityInNanoteslas"]) == want, case["id"]
            elif want is None:
                assert got[field] is None, (case["id"], field)
            else:
                off = abs(got[field] - want)
                assert off <= tolerances[field], (case["id"], field, got[field], want)
                worst[field] = max(worst.get(field, 0), off)
    print(f"NOAA's library matches all {len(cases)} published cases. Largest differences:")
    for field, off in worst.items():
        print(f"  {field} {off:.6f} of ±{tolerances[field]:g}")


# Why a case exists, for the reader of the file and the page's list of edge cases.
NOTES = {
    "noaa-table-1": "NOAA's Table 6. Grid variation equals declination on the prime meridian.",
    "noaa-table-2": "At the equator grid variation is null: NOAA prints NaN.",
    "noaa-table-3": "Longitude 240 is −120: grid variation is declination plus longitude, wrapped to −180 to 180.",
    "noaa-points-1": "Near the north magnetic pole: horizontal intensity under 2000 nT, blackout unreliable, declination still given.",
    "noaa-points-2": "Horizontal intensity under 6000 nT: blackout caution.",
    "reference-north-pole-2026": "The geographic north pole: longitude is undefined, so NOAA takes the limit along longitude 0. Blackout unreliable.",
    "reference-south-pole-2026": "The geographic south pole, along longitude 0.",
    "reference-first-instant": "2025.0, the model's first instant.",
    "reference-last-instant": "2030.0, the model's last instant: still computed.",
    "reference-grid-variation-55n": "Exactly 55° N, where grid variation starts: declination minus longitude.",
    "reference-grid-variation-55s": "Exactly 55° S: declination plus longitude.",
    "reference-date-2025-01-01": "1 January is a whole year.",
    "reference-date-2028-02-29": "A leap day: 2028 + 59/366.",
    "reference-date-2028-12-31": "The last day of a leap year: 2028 + 365/366.",
    "reference-date-2100-03-01": "2100 isn't a leap year: 2100 + 59/365.",
    "reference-date-2000-03-01": "2000 was a leap year: 2000 + 60/366.",
    "reference-date-2027-02-29": "Doesn't exist: invalidInput.",
    "invalid-before-2025": "Before the model's first instant: outOfRange, as NOAA's software refuses it.",
    "invalid-after-2030": "After the model's last instant: outOfRange.",
}

def build():
    data = json.loads(VECTORS.read_text())
    cases = table_cases() + points_cases() + reference_cases() + invalid_cases()
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), "duplicate case id"
    if data.get("cases") != cases:
        data["publishedDate"] = datetime.date.today().isoformat()
    data["cases"] = cases
    vectors_json.add_notes(data["cases"], NOTES)
    VECTORS.write_text(vectors_json.dumps(data))
    print(f"Wrote {len(cases)} cases to {VECTORS.relative_to(ROOT)}")


if __name__ == "__main__":
    {"--published-inputs": published_inputs, "--verify": verify}.get(sys.argv[1] if len(sys.argv) > 1 else "", build)()
