"""Builds _data/vectors/utm-mgrs.json from GeographicLib's GeoConvert.

  generate.py            run GeoConvert, log every call to utm-mgrs/sources/geoconvert.txt,
                         and rebuild the cases
  generate.py --offline  rebuild the cases from the committed log, without GeoConvert

Needs `brew install geographiclib` for the first. The words (sources, operations,
fields, tolerances) are edited in the JSON by hand; this replaces `cases` and
`publishedDate`. Every expected value is GeoConvert's output, verbatim.
"""

import datetime
import json
import math
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "utm-mgrs" / "sources" / "geoconvert.txt"
VECTORS = ROOT / "_data" / "vectors" / "utm-mgrs.json"
RANDOM_POINTS = 400

OFFLINE = "--offline" in sys.argv
logged = {}  # (args, input) -> output, from the committed log when offline
log_lines = []


def read_log():
    args = None
    pending = None
    for line in LOG.read_text().splitlines():
        if line.startswith("$ GeoConvert"):
            args = line[len("$ GeoConvert"):].strip()
        elif line.startswith("< "):
            pending = line[2:]
        elif line.startswith("> "):
            logged[(args, pending)] = line[2:]


def geoconvert(args, lines):
    """GeoConvert's output for each input line, one for one."""
    if OFFLINE:
        return [logged[(args, line)] for line in lines]
    result = subprocess.run(["GeoConvert", *args.split()], input="\n".join(lines) + "\n",
                            capture_output=True, text=True)
    out = result.stdout.splitlines()
    assert len(out) == len(lines), (args, len(out), len(lines))
    log_lines.append(f"$ GeoConvert {args}")
    for i, o in zip(lines, out):
        log_lines.append(f"< {i}")
        log_lines.append(f"> {o}")
    return out


def utm(line):
    """'32n 276979.926401 6658157.202407' or 'n 2000000 2000000' for UPS."""
    zone, easting, northing = line.split()
    return {
        "zone": int(zone[:-1]) if zone[:-1] else 0,
        "hemisphere": "north" if zone[-1] == "n" else "south",
        "eastingInMeters": float(easting),
        "northingInMeters": float(northing),
    }


def utm_text(expected):
    zone = f"{expected['zone']:02d}" if expected["zone"] else ""
    return f"{zone}{expected['hemisphere'][0]} {expected['eastingInMeters']:.3f} {expected['northingInMeters']:.3f}"


def latlon(line):
    lat, lon = line.split()
    return {"latitudeInDegrees": float(lat), "longitudeInDegrees": float(lon)}


def near_grid_line(expected, digits, lat):
    """Within 1 mm of a line where a truncated MGRS digit flips, or a latitude band edge."""
    size = 10 ** (5 - digits)
    for value in (expected["eastingInMeters"], expected["northingInMeters"]):
        r = value % size
        if r < 0.001 or size - r < 0.001:
            return True
    return -80 <= lat <= 84 and abs(lat / 8 - round(lat / 8)) * 8 < 1e-6


def to_utm_cases(points, ids, tags):
    inputs = [f"{lat} {lon}" for lat, lon in points]
    out = geoconvert("-u -p 6", inputs)
    conv = geoconvert("-c -p 9", inputs)
    cases = []
    for (lat, lon), case_id, u, c in zip(points, ids, out, conv):
        expected = utm(u)
        gamma, k = c.split()
        expected["convergenceInDegrees"] = float(gamma)
        expected["pointScale"] = float(k)
        cases.append({"id": case_id, "operation": "toUtm", "tags": tags(lat),
                      "input": {"latitudeInDegrees": float(lat), "longitudeInDegrees": float(lon)},
                      "expected": expected})
    return cases


def from_utm_cases(grids, ids, tags):
    out = geoconvert("-g -p 9", [utm_text(g) for g in grids])
    return [{"id": case_id, "operation": "fromUtm", "tags": tags,
             "input": {**g, "eastingInMeters": round(g["eastingInMeters"], 3),
                       "northingInMeters": round(g["northingInMeters"], 3)},
             "expected": latlon(o)}
            for g, case_id, o in zip(grids, ids, out)]


def to_mgrs(points_digits):
    return [geoconvert(f"-m -p {digits - 5}", [f"{lat} {lon}"])[0] for lat, lon, digits in points_digits]


def polar(lat):
    return ["polar"] if abs(float(lat)) >= 80 else []


def random_cases():
    rng = random.Random(2026)
    points = []
    for _ in range(RANDOM_POINTS):
        lat = math.degrees(math.asin(2 * rng.random() - 1))
        lon = rng.uniform(-180, 180)
        points.append((f"{lat:.7f}", f"{lon:.7f}"))
    to_utm = to_utm_cases(points, [f"geoconvert-to-utm-{i}" for i in range(1, len(points) + 1)],
                          lambda lat: ["reference", *polar(lat)])
    grids = [{k: c["expected"][k] for k in ("zone", "hemisphere", "eastingInMeters", "northingInMeters")} for c in to_utm]
    from_utm = from_utm_cases(grids, [f"geoconvert-from-utm-{i}" for i in range(1, len(points) + 1)], ["reference"])
    for case, (lat, _) in zip(from_utm, points):
        case["tags"] = ["reference", *polar(lat)]

    # MGRS at every precision in turn, leaving out points that sit on a flip.
    chosen = []
    for i, ((lat, lon), grid) in enumerate(zip(points, grids)):
        digits = i % 6
        if not near_grid_line(grid, digits, float(lat)):
            chosen.append((i + 1, lat, lon, digits))
    refs = to_mgrs([(lat, lon, digits) for _, lat, lon, digits in chosen])
    to_mgrs_cases, from_mgrs_inputs = [], []
    for (n, lat, lon, digits), ref in zip(chosen, refs):
        to_mgrs_cases.append({"id": f"geoconvert-to-mgrs-{n}", "operation": "toMgrs", "tags": ["reference", *polar(lat)],
                              "input": {"latitudeInDegrees": float(lat), "longitudeInDegrees": float(lon),
                                        "precisionInDigits": digits},
                              "expected": {"mgrs": ref}})
        from_mgrs_inputs.append((n, lat, ref))
    centres = geoconvert("-g -p 9", [ref for _, _, ref in from_mgrs_inputs])
    from_mgrs_cases = [{"id": f"geoconvert-from-mgrs-{n}", "operation": "fromMgrs", "tags": ["reference", *polar(lat)],
                        "input": {"mgrs": ref}, "expected": latlon(c)}
                       for (n, lat, ref), c in zip(from_mgrs_inputs, centres)]
    return to_utm + from_utm + to_mgrs_cases + from_mgrs_cases


EDGE_POINTS = [
    ("norway-32v", "60", "5"),
    ("norway-32v-west-edge", "60", "3.0000001"),
    ("norway-31v-west-of-edge", "60", "2.9999999"),
    ("norway-32v-south-edge", "56", "3.5"),
    ("norway-31u-south-of-edge", "55.9999999", "3.5"),
    ("norway-32v-north", "63.9999999", "3.5"),
    ("norway-31w-north-of-band", "64", "3.5"),
    ("svalbard-31x", "78", "8.9999999"),
    ("svalbard-33x-west", "78", "9"),
    ("svalbard-33x-east", "78", "20.9999999"),
    ("svalbard-35x-west", "78", "21"),
    ("svalbard-35x-east", "78", "32.9999999"),
    ("svalbard-37x", "78", "33"),
    ("svalbard-32w-below-band", "71.9999999", "8.9999999"),
    ("utm-last-north", "83.9999999", "10"),
    ("ups-first-north", "84", "10"),
    ("utm-last-south", "-80", "10"),
    ("ups-first-south", "-80.0000001", "10"),
    ("antimeridian-east", "10", "180"),
    ("antimeridian-west", "10", "-180"),
    ("zone-60", "10", "179.9999999"),
    ("equator", "0", "10"),
    ("just-south-of-equator", "-0.0000001", "10"),
    ("north-pole", "90", "0"),
    ("south-pole", "-90", "0"),
    ("central-meridian", "49", "-123"),
]


def edge_cases():
    points = [(lat, lon) for _, lat, lon in EDGE_POINTS]
    cases = to_utm_cases(points, [f"edge-to-utm-{name}" for name, _, _ in EDGE_POINTS],
                         lambda lat: ["reference", "edge", *polar(lat)])
    refs = to_mgrs([(lat, lon, 5) for lat, lon in points])
    # Band edges and exact lines are the point here, so no grid-line filter: each lands
    # exactly on a line (a pole, the equator, a central meridian) or clear of one.
    for (name, lat, lon), ref in zip(EDGE_POINTS, refs):
        cases.append({"id": f"edge-to-mgrs-{name}", "operation": "toMgrs", "tags": ["reference", "edge", *polar(lat)],
                      "input": {"latitudeInDegrees": float(lat), "longitudeInDegrees": float(lon), "precisionInDigits": 5},
                      "expected": {"mgrs": ref}})

    # The truncation diagram: easting 485234.9 and northing 5371665.8 in 10n.
    grid = {"zone": 10, "hemisphere": "north", "eastingInMeters": 485234.9, "northingInMeters": 5371665.8}
    point = from_utm_cases([grid], ["edge-from-utm-truncation"], ["reference", "edge"])
    cases += point
    lat = f"{point[0]['expected']['latitudeInDegrees']:.9f}"
    lon = f"{point[0]['expected']['longitudeInDegrees']:.9f}"
    for digits in (5, 4, 3):
        ref = to_mgrs([(lat, lon, digits)])[0]
        cases.append({"id": f"edge-to-mgrs-truncation-{digits}", "operation": "toMgrs", "tags": ["reference", "edge"],
                      "input": {"latitudeInDegrees": float(lat), "longitudeInDegrees": float(lon), "precisionInDigits": digits},
                      "expected": {"mgrs": ref}})

    refs = [("padded-zone", "04QFJ1234567890"), ("unpadded-zone", "4QFJ1234567890"),
            ("lower-case", "10udv9122158889"), ("ups-north", "ZAE3856181304"),
            ("100-km-square", "10UDV"), ("svalbard", "33XVG6371765261")]
    centres = geoconvert("-g -p 9", [r for _, r in refs])
    cases += [{"id": f"edge-from-mgrs-{name}", "operation": "fromMgrs", "tags": ["reference", "edge"],
               "input": {"mgrs": ref}, "expected": latlon(c)} for (name, ref), c in zip(refs, centres)]
    return cases


PARSE = [
    ("decimal", "49.2827 -123.1207"),
    ("hemisphere-letters", "49.2827N 123.1207W"),
    ("letters-first", "N49.2827 W123.1207"),
    ("longitude-first", "123.1207W 49.2827N"),
    ("degrees-minutes", "49°16.962'N 123°07.242'W"),
    ("degrees-minutes-seconds", "49°16'57.72\"N 123°07'14.52\"W"),
    ("colons", "49:16:57.72N 123:07:14.52W"),
    ("southern-eastern", "33°52'04\"S 151°12'36\"E"),
    ("utm", "10n 491221.771 5458889.980"),
    ("mgrs", "10UDV9122158889"),
    ("mgrs-unpadded", "4QFJ1234567890"),
]

KEBAB = {"toUtm": "to-utm", "fromUtm": "from-utm", "toMgrs": "to-mgrs", "fromMgrs": "from-mgrs", "parse": "parse"}

INVALID = [
    ("toUtm", "latitude-91", {"latitudeInDegrees": 91, "longitudeInDegrees": 0}, "outOfRange", "91 0", "-u"),
    ("fromUtm", "easting-1500-km", {"zone": 10, "hemisphere": "north", "eastingInMeters": 1500000, "northingInMeters": 5000000},
     "outOfRange", "10n 1500000 5000000", "-g"),
    ("fromUtm", "zone-61", {"zone": 61, "hemisphere": "north", "eastingInMeters": 500000, "northingInMeters": 5000000},
     "outOfRange", "61n 500000 5000000", "-g"),
    ("fromMgrs", "odd-digits", {"mgrs": "10UDV912345876"}, "invalidInput", "10UDV912345876", "-g"),
    ("fromMgrs", "band-z", {"mgrs": "10ZDV9123458765"}, "invalidInput", "10ZDV9123458765", "-g"),
    ("parse", "words", {"text": "hello"}, "invalidInput", "hello", "-g"),
    ("parse", "latitude-91", {"text": "91 0"}, "outOfRange", "91 0", "-g"),
    ("parse", "two-latitudes", {"text": "49.2827N 49.2827N"}, "invalidInput", "49.2827N 49.2827N", "-g"),
]


def parse_and_invalid_cases():
    out = geoconvert("-g -p 9", [text for _, text in PARSE])
    cases = [{"id": f"parse-{name}", "operation": "parse", "tags": ["reference", "edge"],
              "input": {"text": text}, "expected": latlon(o)} for (name, text), o in zip(PARSE, out)]
    for operation, name, case_input, error, text, mode in INVALID:
        assert geoconvert(mode, [text])[0].startswith("ERROR"), (name, text)
        cases.append({"id": f"invalid-{KEBAB[operation]}-{name}", "operation": operation, "tags": ["reference", "invalid"],
                      "input": case_input, "expected": {"error": error}})
    # Past the range this file defines; GeoConvert would give 6 digits.
    cases.append({"id": "invalid-to-mgrs-precision-6", "operation": "toMgrs", "tags": ["invalid"],
                  "input": {"latitudeInDegrees": 49.2827, "longitudeInDegrees": -123.1207, "precisionInDigits": 6},
                  "expected": {"error": "outOfRange"}})
    return cases


def main():
    if OFFLINE:
        read_log()
    else:
        version = subprocess.run(["GeoConvert", "--version"], capture_output=True, text=True).stdout.strip()
        log_lines.append(f"# {version}. Generated by scripts/utm-mgrs/generate.py; < is input, > is GeoConvert's output.")
    cases = edge_cases() + parse_and_invalid_cases() + random_cases()
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), "duplicate case id"
    for c in cases:
        assert not any(str(v).startswith("ERROR") for v in c["expected"].values()), c
    if not OFFLINE:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.write_text("\n".join(log_lines) + "\n")

    data = json.loads(VECTORS.read_text())
    data.pop("placeholder", None)
    if data.get("cases") != cases:
        data["publishedDate"] = datetime.date.today().isoformat()
    data["cases"] = cases
    VECTORS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(cases)} cases to {VECTORS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
