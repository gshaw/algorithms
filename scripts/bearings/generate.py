"""Builds _data/vectors/bearings.json.

  generate.py            run GeodSolve, log every call to bearings/sources/geodsolve.txt,
                         and rebuild the cases
  generate.py --offline  rebuild from the committed log, without GeodSolve

Where the values come from:
- inverse and destination: GeographicLib's GeodSolve on a sphere of radius 6,371,008.8 m
  (`-e 6371008.8 0`), logged verbatim.
- convertNorth: six worked conversions from FM 3-25.26 (2001), figures 6-10 to 6-15,
  transcribed in bearings/sources/fm-3-25-26-excerpts.txt, plus cases worked out from
  the rules this file's fields state.
- compassPoint: the names in Bowditch, Appendix B, parsed from
  bearings/sources/bowditch-appendix-b.txt.
- backAzimuth, turn and formatBearing: worked out from the rules in the file's fields,
  here in plain arithmetic, and tagged `hand`.
The words (sources, operations, fields, tolerances) are edited in the JSON by hand.
"""

import datetime
import json
import math
import random
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import vectors_json  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "bearings" / "sources"
LOG = SOURCES / "geodsolve.txt"
VECTORS = ROOT / "_data" / "vectors" / "bearings.json"
SPHERE = "-e 6371008.8 0 -p 6"

OFFLINE = "--offline" in sys.argv
logged = {}
log_lines = []


def read_log():
    args = pending = None
    for line in LOG.read_text().splitlines():
        if line.startswith("$ GeodSolve"):
            args = line[len("$ GeodSolve"):].strip()
        elif line.startswith("< "):
            pending = line[2:]
        elif line.startswith("> "):
            logged[(args, pending)] = line[2:]


def geodsolve(args, lines):
    if OFFLINE:
        return [logged[(args, line)] for line in lines]
    result = subprocess.run(["GeodSolve", *args.split()], input="\n".join(lines) + "\n", capture_output=True, text=True)
    out = result.stdout.splitlines()
    assert len(out) == len(lines), (args, len(out), len(lines))
    log_lines.append(f"$ GeodSolve {args}")
    for i, o in zip(lines, out):
        log_lines.extend([f"< {i}", f"> {o}"])
    return out


def bearing(azimuth):
    """GeodSolve's azimuth, −180 to 180, as a bearing, 0 to 360."""
    value = float(azimuth)
    return value + 360 if value < 0 else value + 0.0


def clear_of_north(value):
    return 1e-5 < value < 360 - 1e-5


# Geodesics

def inverse_cases():
    rng = random.Random(3)
    pairs = []
    for i in range(300):
        lat1, lon1 = math.degrees(math.asin(2 * rng.random() - 1)), rng.uniform(-180, 180)
        if i % 2:  # local: within about 50 km
            lat2, lon2 = lat1 + rng.uniform(-0.45, 0.45), lon1 + rng.uniform(-0.45, 0.45)
            lat2 = max(-89.9, min(89.9, lat2))
            lon2 = (lon2 + 180) % 360 - 180
        else:
            lat2, lon2 = math.degrees(math.asin(2 * rng.random() - 1)), rng.uniform(-180, 180)
        pairs.append(tuple(f"{v:.7f}" for v in (lat1, lon1, lat2, lon2)))
    out = geodsolve(f"-i {SPHERE}", [" ".join(p) for p in pairs])
    cases = []
    for n, (p, o) in enumerate(zip(pairs, out), 1):
        azi1, _, s12 = o.split()
        b = bearing(azi1)
        if not clear_of_north(b) or abs(float(p[0])) > 89.99:
            continue
        cases.append({"id": f"geodsolve-inverse-{n}", "operation": "inverse", "tags": ["reference"],
                      "input": dict(zip(["fromLatitudeInDegrees", "fromLongitudeInDegrees", "toLatitudeInDegrees", "toLongitudeInDegrees"],
                                        map(float, p))),
                      "expected": {"distanceInMeters": float(s12), "bearingInDegrees": b}})
    return cases


def destination_cases():
    rng = random.Random(4)
    starts = []
    for _ in range(300):
        lat, lon = math.degrees(math.asin(2 * rng.random() - 1)), rng.uniform(-180, 180)
        distance = rng.choice([rng.uniform(0, 5000), rng.uniform(0, 100000), rng.uniform(0, 20000000)])
        starts.append((f"{lat:.7f}", f"{lon:.7f}", f"{rng.uniform(0, 360):.6f}", f"{distance:.3f}"))
    out = geodsolve(SPHERE, [f"{lat} {lon} {azi} {s}" for lat, lon, azi, s in starts])
    cases = []
    for n, ((lat, lon, azi, s), o) in enumerate(zip(starts, out), 1):
        lat2, lon2, _ = o.split()
        if abs(float(lon2)) > 179.9999 or abs(float(lat)) > 89.99:
            continue
        cases.append({"id": f"geodsolve-destination-{n}", "operation": "destination", "tags": ["reference"],
                      "input": {"fromLatitudeInDegrees": float(lat), "fromLongitudeInDegrees": float(lon),
                                "distanceInMeters": float(s), "bearingInDegrees": float(azi)},
                      "expected": {"toLatitudeInDegrees": float(lat2), "toLongitudeInDegrees": float(lon2)}})
    return cases


def geodesic_edges():
    # (name, from lat, from lon, to lat, to lon, whether the bearing is defined)
    edges = [
        ("across-antimeridian", "10", "179.5", "10", "-179.5", True),
        ("due-north", "49", "-123", "50", "-123", False),  # bearing 0 or 360
        ("due-east-on-equator", "0", "10", "0", "11", True),
        ("due-south", "49", "-123", "48", "-123", True),
        ("due-west", "0", "10", "0", "9", True),
        ("same-point", "49.28", "-123.12", "49.28", "-123.12", False),
        ("antipodes", "0", "0", "0", "180", False),
        ("near-antipodes", "30", "0", "-29.5", "179.5", True),
        ("from-north-pole", "90", "0", "45", "30", False),
        ("one-metre", "49.28", "-123.12", "49.280009", "-123.12", False),
        ("quarter-circle", "0", "0", "0", "90", True),
    ]
    out = geodsolve(f"-i {SPHERE}", [" ".join(e[1:5]) for e in edges])
    cases = []
    for (name, *p, bearing_defined), o in zip(edges, out):
        azi1, _, s12 = o.split()
        expected = {"distanceInMeters": float(s12)}
        if bearing_defined:
            expected["bearingInDegrees"] = bearing(azi1)
        cases.append({"id": f"edge-inverse-{name}", "operation": "inverse", "tags": ["reference", "edge"],
                      "input": dict(zip(["fromLatitudeInDegrees", "fromLongitudeInDegrees", "toLatitudeInDegrees", "toLongitudeInDegrees"],
                                        map(float, p))),
                      "expected": expected})
    trips = [
        ("zero-distance", "49.28", "-123.12", "45", "0"),
        ("across-antimeridian", "10", "179.5", "90", "110000"),
        ("half-way-round", "0", "0", "90", "10007557.221"),
        ("over-the-pole", "80", "10", "0", "2000000"),
    ]
    out = geodsolve(SPHERE, [" ".join(t[1:]) for t in trips])
    for (name, lat, lon, azi, s), o in zip(trips, out):
        lat2, lon2, _ = o.split()
        cases.append({"id": f"edge-destination-{name}", "operation": "destination", "tags": ["reference", "edge"],
                      "input": {"fromLatitudeInDegrees": float(lat), "fromLongitudeInDegrees": float(lon),
                                "distanceInMeters": float(s), "bearingInDegrees": float(azi)},
                      "expected": {"toLatitudeInDegrees": float(lat2), "toLongitudeInDegrees": float(lon2)}})
    return cases


# Norths, from FM 3-25.26

FM_FIGURES = [
    # (figure, from, to, bearing, G-M angle east positive, expected)
    ("6-10", "magnetic", "grid", 210, 12, 222),
    ("6-11", "grid", "magnetic", 303, 10, 293),
    ("6-12", "grid", "magnetic", 2, 16, 346),
    ("6-13", "magnetic", "grid", 65, -8, 57),
    ("6-14", "grid", "magnetic", 93, -14, 107),
    ("6-15", "magnetic", "grid", 5, -12, 353),
]


def north_cases():
    text = (SOURCES / "fm-3-25-26-excerpts.txt").read_text()
    cases = []
    for figure, from_north, to_north, value, gm, expected in FM_FIGURES:
        assert f"{figure}  " in text
        # The figures give only the G-M angle: with grid north on true north, it's the declination.
        cases.append({"id": f"fm-3-25-26-figure-{figure}", "operation": "convertNorth", "tags": ["published"],
                      "input": {"bearingInDegrees": value, "fromNorth": from_north, "toNorth": to_north,
                                "magneticDeclinationInDegrees": gm, "convergenceInDegrees": 0},
                      "expected": {"convertedBearingInDegrees": expected}})

    def to_true(value, north, d, c):
        return value + {"true": 0, "magnetic": d, "grid": c}[north]

    def from_true(value, north, d, c):
        return (value - {"true": 0, "magnetic": d, "grid": c}[north]) % 360

    n = 0
    for d in (15.5, -15.5):
        for c in (1.25, -1.25):
            for from_north, to_north in [("magnetic", "true"), ("true", "magnetic"), ("grid", "true"),
                                         ("true", "grid"), ("magnetic", "grid"), ("grid", "magnetic")]:
                n += 1
                value = [100, 5, 355, 180, 0.5, 359.5][n % 6]
                result = from_true(to_true(Fraction(str(value)), from_north, Fraction(str(d)), Fraction(str(c))),
                                   to_north, Fraction(str(d)), Fraction(str(c)))
                cases.append({"id": f"hand-convert-north-{n}", "operation": "convertNorth", "tags": ["hand"],
                              "input": {"bearingInDegrees": value, "fromNorth": from_north, "toNorth": to_north,
                                        "magneticDeclinationInDegrees": d, "convergenceInDegrees": c},
                              "expected": {"convertedBearingInDegrees": float(result)}})
    cases.append({"id": "hand-convert-north-same", "operation": "convertNorth", "tags": ["hand", "edge"],
                  "input": {"bearingInDegrees": 42, "fromNorth": "grid", "toNorth": "grid",
                            "magneticDeclinationInDegrees": 15.5, "convergenceInDegrees": 1.25},
                  "expected": {"convertedBearingInDegrees": 42}})
    return cases


# Compass points, from Bowditch

def bowditch_points():
    """The 32 whole points, in order from north, as Bowditch writes them."""
    names = {}
    pattern = re.compile(r"([A-Z][A-Za-z ]*?)\s{2,}(\d+)\s+(\d+)° ?(\d\d)'? ?(\d\d)")
    for line in (SOURCES / "bowditch-appendix-b.txt").read_text().splitlines():
        for name, point, degrees, minutes, seconds in pattern.findall(line):
            point = int(point)
            if point < 32:
                assert (int(degrees) * 3600 + int(minutes) * 60 + int(seconds)) == point * 40500, line
                names[point] = {"North": "N", "East": "E", "South": "S", "West": "W"}.get(name.strip(), name.strip())
    assert sorted(names) == list(range(32)), sorted(names)
    return [names[i] for i in range(32)]


def compass_cases():
    points = bowditch_points()

    def nearest(value, count):
        step = Fraction(360, count)
        index = math.floor(Fraction(str(value)) / step + Fraction(1, 2)) % count
        return points[index * (32 // count)]

    cases = []
    for count in (4, 8, 16, 32):
        step = 360 / count
        values = [i * step for i in range(count)]
        # Just either side of each boundary, and the boundary itself, which goes clockwise.
        values += [i * step + step / 2 for i in range(count) if (i * step + step / 2) == float(Fraction(2 * i + 1, 2) * Fraction(360, count))]
        values += [359.9, 0.01]
        for value in values:
            text = nearest(value, count)
            cases.append({"id": f"bowditch-points-{count}-{str(value).replace('.', '-')}", "operation": "compassPoint",
                          "tags": ["hand", "edge"] if value in (359.9, 0.01) or (value / step) % 1 else ["hand"],
                          "input": {"bearingInDegrees": value, "pointCount": count},
                          "expected": {"compassPointText": text}})
    return cases


# Back azimuth, turns and formatting, from the definitions

def hand_cases():
    cases = []
    for value in (0, 45, 179.5, 180, 180.5, 270, 359.9):
        result = (Fraction(str(value)) + 180) % 360
        cases.append({"id": f"hand-back-azimuth-{str(value).replace('.', '-')}", "operation": "backAzimuth",
                      "tags": ["hand", "edge"] if value in (0, 180, 359.9) else ["hand"],
                      "input": {"bearingInDegrees": value}, "expected": {"backAzimuthInDegrees": float(result)}})

    for a, b in [(350, 10), (10, 350), (0, 180), (180, 0), (90, 90), (45, 225.5), (225.5, 45), (0.25, 359.75), (100, 279.9)]:
        diff = (Fraction(str(b)) - Fraction(str(a))) % 360
        if diff == 0:
            turn, direction = 0, "none"
        elif diff <= 180:
            turn, direction = diff, "right"
        else:
            turn, direction = 360 - diff, "left"
        cases.append({"id": f"hand-turn-{str(a).replace('.', '-')}-to-{str(b).replace('.', '-')}", "operation": "turn",
                      "tags": ["hand", "edge"] if diff in (0, 180) or abs(a - b) > 180 else ["hand"],
                      "input": {"fromBearingInDegrees": a, "toBearingInDegrees": b},
                      "expected": {"turnInDegrees": float(turn), "direction": direction}})

    def half_up(x):
        return math.floor(x + Fraction(1, 2))

    for value in (0, 0.4, 0.5, 9.5, 45, 99.49, 180, 359.4, 359.5, 359.6, 359.999):
        text = f"{half_up(Fraction(str(value))) % 360:03d}°"
        cases.append({"id": f"hand-format-degrees-{str(value).replace('.', '-')}", "operation": "formatBearing",
                      "tags": ["hand", "edge"] if value >= 359.5 or value == 0.5 else ["hand"],
                      "input": {"bearingInDegrees": value, "angleUnit": "degrees"}, "expected": {"bearingText": text}})
    # Mils: 6400 to the circle. An exact half mil can't be written in decimal degrees, so
    # no case sits on one.
    for value in (0, 0.02, 0.04, 45, 90, 180, 270, 359.97, 359.98):
        mils = Fraction(str(value)) * 6400 / 360
        text = f"{half_up(mils) % 6400:04d}"
        cases.append({"id": f"hand-format-mils-{str(value).replace('.', '-')}", "operation": "formatBearing",
                      "tags": ["hand", "edge"] if value >= 359.97 else ["hand"],
                      "input": {"bearingInDegrees": value, "angleUnit": "mils"}, "expected": {"bearingText": text}})
    return cases


def invalid_cases():
    return [
        {"id": "invalid-inverse-latitude-91", "operation": "inverse", "tags": ["invalid"],
         "input": {"fromLatitudeInDegrees": 91, "fromLongitudeInDegrees": 0, "toLatitudeInDegrees": 0, "toLongitudeInDegrees": 0},
         "expected": {"error": "outOfRange"}},
        {"id": "invalid-destination-negative-distance", "operation": "destination", "tags": ["invalid"],
         "input": {"fromLatitudeInDegrees": 0, "fromLongitudeInDegrees": 0, "distanceInMeters": -1, "bearingInDegrees": 0},
         "expected": {"error": "outOfRange"}},
        {"id": "invalid-format-bearing-unit", "operation": "formatBearing", "tags": ["invalid"],
         "input": {"bearingInDegrees": 10, "angleUnit": "grads"}, "expected": {"error": "invalidInput"}},
        {"id": "invalid-compass-point-count-12", "operation": "compassPoint", "tags": ["invalid"],
         "input": {"bearingInDegrees": 10, "pointCount": 12}, "expected": {"error": "invalidInput"}},
        {"id": "invalid-convert-north-name", "operation": "convertNorth", "tags": ["invalid"],
         "input": {"bearingInDegrees": 10, "fromNorth": "compass", "toNorth": "true",
                   "magneticDeclinationInDegrees": 0, "convergenceInDegrees": 0},
         "expected": {"error": "invalidInput"}},
    ]


def main():
    if OFFLINE:
        read_log()
    else:
        version = subprocess.run(["GeodSolve", "--version"], capture_output=True, text=True).stdout.strip()
        log_lines.append(f"# {version}, on a sphere of radius 6,371,008.8 m. Generated by scripts/bearings/generate.py; "
                         "< is input, > is GeodSolve's output.")
    cases = geodesic_edges() + north_cases() + compass_cases() + hand_cases() + invalid_cases() + inverse_cases() + destination_cases()
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1][:5]
    if not OFFLINE:
        LOG.write_text("\n".join(log_lines) + "\n")
    data = json.loads(VECTORS.read_text())
    data.pop("placeholder", None)
    if data.get("cases") != cases:
        data["publishedDate"] = datetime.date.today().isoformat()
    data["cases"] = cases
    VECTORS.write_text(vectors_json.dumps(data))
    print(f"Wrote {len(cases)} cases to {VECTORS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
