"""Builds _data/vectors/tides.json.

  generate.py            query NOAA and run XTide, log both under tides/sources/,
                         and rebuild the cases
  generate.py --offline  rebuild from the committed logs alone

Where the values come from:
- constituents: NOAA CO-OPS's harmonic constants for each station (Metadata API,
  harcon.json, metric), in NOAA's order, leaving out those with zero amplitude.
- height: NOAA's 6-minute predictions on mean sea level, in GMT, to the millimetre.
- nextExtremes: NOAA's high and low predictions (interval=hilo), to the minute.
Every request and response is logged in noaa.jsonl.

XTide checks each value and is logged in xtide.txt; no expected value comes from it. It runs
on a TCD built from the same NOAA constants, so it shows what a correct SP 98
implementation gets from the published constants. The first run needs, in $XTIDE_DIR
(default /tmp/xtide), from https://flaterco.com/xtide/files.html: libtcd 2.2.7 installed
under inst/, xtide-2.16 with `tide` built, tcd-utils-20240222 with `build_tide_db` and
`restore_tide_db` built, and harmonics-dwf-20251228-free.tcd, whose constituent tables
(congen's) the TCD reuses.
"""

import datetime
import json
import os
import random
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import vectors_json  # noqa: E402
from logged import OFFLINE, Program  # noqa: E402
from logged import USNO as Logged  # noqa: E402  any JSON API's responses, logged the same way

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "tides" / "sources"
VECTORS = ROOT / "tides" / "vectors.json"
noaa = Logged(SOURCES / "noaa.jsonl")
API = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
QUERY = "product=predictions&datum=MSL&units=metric&time_zone=gmt&format=json"

STATIONS = [("9447130", "seattle"), ("9414290", "san-francisco"), ("8443970", "boston"),
            ("8729840", "pensacola"), ("1612340", "honolulu"), ("9455760", "nikiski"),
            ("8410140", "eastport"), ("8454000", "providence"), ("8771450", "galveston")]
FIRST = datetime.datetime(2026, 1, 1)
LAST = datetime.datetime(2051, 1, 1)
HEIGHTS_PER_STATION = 10
EXTREMES_PER_STATION = 5
# How far XTide may be from NOAA, inside the file's tolerances (0.005 m and 120 s).
CHECK_METERS = 0.004
CHECK_SECONDS = 60
dropped = []


def iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp(moment):
    return moment.strftime("%Y%m%d %H:%M").replace(" ", "%20")


def near_new_year(moment, hours=1):
    """XTide blends one year into the next over the hour either side of 1 January."""
    edges = [datetime.datetime(moment.year, 1, 1), datetime.datetime(moment.year + 1, 1, 1)]
    return any(abs((moment - edge).total_seconds()) < hours * 3600 for edge in edges)


def constants(station):
    data = noaa.get(f"https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/{station}/harcon.json?units=metric")
    assert data["units"] == "meters"
    return [{"name": c["name"], "amplitudeInMeters": c["amplitude"], "phaseInDegrees": c["phase_GMT"]}
            for c in sorted(data["HarmonicConstituents"], key=lambda c: c["number"]) if c["amplitude"] > 0]


def noaa_height(station, moment):
    end = moment + datetime.timedelta(minutes=6)
    data = noaa.get(f"{API}?{QUERY}&station={station}&begin_date={stamp(moment)}&end_date={stamp(end)}&interval=6")
    first = data["predictions"][0]
    assert first["t"] == moment.strftime("%Y-%m-%d %H:%M"), (station, moment, first)
    return float(first["v"])


def noaa_extremes(station, start):
    end = start + datetime.timedelta(days=2)
    data = noaa.get(f"{API}?{QUERY}&station={station}&begin_date={start:%Y%m%d}&end_date={end:%Y%m%d}&interval=hilo")
    return [(datetime.datetime.strptime(p["t"], "%Y-%m-%d %H:%M"), float(p["v"]), p["type"]) for p in data["predictions"]]


class XTide:
    """XTide 2.16 on a TCD of NOAA's constants, one station per NOAA id, on mean sea level."""

    def __init__(self):
        self.log = Program(SOURCES / "xtide.txt", "")
        self.ready = False
        if not OFFLINE:
            self.dir = Path(os.environ.get("XTIDE_DIR", "/tmp/xtide"))
            self.log.header = ("XTide 2.16 (David Flater) on a TCD built from NOAA's metric harmonic constants for each "
                               "station, with congen's equilibrium arguments and node factors from "
                               "harmonics-dwf-20251228, datum 0 (mean sea level). 'height' lines: station instant => "
                               "metres. 'extremes' lines: station start => the highs (H) and lows (L) in the next 36 h, "
                               "to the minute and centimetre.")

    def _prepare(self):
        if self.ready:
            return
        work = self.dir / "algorithms"
        work.mkdir(exist_ok=True)
        env = dict(os.environ, DYLD_LIBRARY_PATH=str(self.dir / "inst" / "lib"), LD_LIBRARY_PATH=str(self.dir / "inst" / "lib"))
        subprocess.run([self.dir / "tcd-utils-20240222" / "restore_tide_db",
                        self.dir / "harmonics-dwf-20251228" / "harmonics-dwf-20251228-free.tcd", work / "dwf"],
                       env=env, check=True, capture_output=True)
        lines = (work / "dwf.txt").read_text(encoding="latin-1").splitlines()
        # Speeds, equilibrium arguments and node factors by year, and the comments after them:
        # build_tide_db wants its input laid out as it was, comments included.
        first = lines.index("# BEGIN HOT COMMENTS")
        header = lines[:max(n for n in range(first) if lines[n] == "#") + 1]
        count = int(header[header.index("# Number of constituents") + 1])
        names = [line.split()[0] for line in header[header.index("# Number of constituents") + 2:]
                 if line and not line.startswith("#")][:count]
        # NOAA's names for two of congen's.
        aliases = {"LDA2": "LAM2", "RHO1": "RHO"}
        records = header
        for station, _ in STATIONS:
            known = {c["name"]: c for c in constants(station)}
            assert set(known) <= {aliases.get(n, n) for n in names}, set(known) - set(names)
            records += ["# BEGIN HOT COMMENTS", "# station_id_context: NOS", f"# station_id: {station}",
                        "# datum: Mean Sea Level", "# !units: meters", "# !longitude: 0.0000", "# !latitude: 0.0000",
                        f"NOAA {station}", "+00:00 :UTC", "0.0000 meters"]
            for name in names:
                c = known.get(aliases.get(name, name))
                records.append(f"{name} {c['amplitudeInMeters']:.4f} {c['phaseInDegrees']:.2f}" if c else "x 0 0")
        (work / "noaa.txt").write_text("\n".join(records) + "\n", encoding="latin-1")
        (work / "noaa.xml").write_text('<?xml version="1.0" encoding="ISO-8859-1"?>\n<document>\n</document>\n')
        (work / "noaa.tcd").unlink(missing_ok=True)
        subprocess.run([self.dir / "tcd-utils-20240222" / "build_tide_db", work / "noaa.tcd", work / "noaa.txt",
                        work / "noaa.xml"], env=env, check=True, capture_output=True)
        (work / ".disableXTidedisclaimer").touch()
        self.env = dict(env, HOME=str(work), HFILE_PATH=str(work / "noaa.tcd"))
        self.ready = True

    def _tide(self, station, mode, begin, end, *more):
        self._prepare()
        out = subprocess.run([self.dir / "xtide-2.16" / "tide", "-l", f"NOAA {station}", "-m", mode, "-z", "-u", "m",
                              "-b", begin.strftime("%Y-%m-%d %H:%M"), "-e", end.strftime("%Y-%m-%d %H:%M"), *more],
                             env=self.env, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def height(self, station, moment):
        def compute():
            lines = self._tide(station, "r", moment, moment + datetime.timedelta(minutes=6), "-s", "00:06")
            when, value = lines[0].split()
            assert int(when) == int(moment.replace(tzinfo=datetime.timezone.utc).timestamp())
            return f"{float(value):.4f}"
        return float(self.log.call(f"height {station} {iso(moment)}", compute))

    def extremes(self, station, start):
        def compute():
            found = []
            for line in self._tide(station, "p", start, start + datetime.timedelta(hours=36), "-f", "c", "-em", "pSsMm")[1:]:
                _, date, clock, value, kind = line.rsplit(",", 4)
                if "Tide" in kind:
                    moment = datetime.datetime.strptime(f"{date} {clock.replace(' UTC', '')}", "%Y-%m-%d %I:%M %p")
                    found.append(f"{'H' if 'High' in kind else 'L'}@{iso(moment)}@{float(value.split()[0]):.2f}")
            return " ".join(found)
        return [(datetime.datetime.strptime(when, "%Y-%m-%dT%H:%M:%SZ"), float(value), kind)
                for kind, when, value in (part.split("@") for part in self.log.call(f"extremes {station} {iso(start)}", compute).split())]


def height_case(xtide, case_id, station, moment, tags):
    value = noaa_height(station, moment)
    if not near_new_year(moment):
        check = xtide.height(station, moment)
        assert abs(check - value) <= CHECK_METERS, (case_id, value, check)
    return {"id": case_id, "operation": "height", "tags": tags,
            "input": {"constituents": constants(station), "instantUtc": iso(moment)},
            "expected": {"heightInMeters": value}}


def height_cases(xtide):
    rng = random.Random(17)
    cases = []
    for station, name in STATIONS:
        for _ in range(HEIGHTS_PER_STATION):
            while True:
                moment = FIRST + datetime.timedelta(minutes=6 * rng.randrange(0, int((LAST - FIRST).total_seconds() // 360)))
                if not near_new_year(moment):
                    break
            cases.append(height_case(xtide, f"noaa-height-{name}-{moment:%Y-%m-%d-%H%M}", station, moment, ["published"]))
    for station, name in (("9447130", "seattle"), ("9455760", "nikiski")):
        for moment in (datetime.datetime(2026, 12, 31, 23, 54), datetime.datetime(2027, 1, 1)):
            cases.append(height_case(xtide, f"noaa-height-{name}-{moment:%Y-%m-%d-%H%M}", station, moment,
                                     ["published", "edge"]))
    return cases


def first_after(events, start):
    """The first high and the first low after the start."""
    high = next((e for e in events if e[2] == "H" and e[0] > start), None)
    low = next((e for e in events if e[2] == "L" and e[0] > start), None)
    return high, low


def extremes_case(xtide, case_id, station, start, tags):
    """None when the case isn't clear-cut: an extreme within 15 minutes of the start, or
    NOAA and XTide disagreeing on which extremes come first, as where NOAA leaves out a high
    and a low less than about 2 hours apart."""
    events = noaa_extremes(station, start)
    high, low = first_after(events, start)
    assert high and low and max(high[0], low[0]) < events[-1][0], (case_id, events)
    if min(high[0], low[0]) - start < datetime.timedelta(minutes=15):
        dropped.append((case_id, "an extreme within 15 minutes of the start"))
        return None
    check_high, check_low = first_after(xtide.extremes(station, start), start)
    for ours, theirs in ((high, check_high), (low, check_low)):
        if theirs is None or abs((ours[0] - theirs[0]).total_seconds()) > 3600:
            dropped.append((case_id, f"XTide's first {ours[2]} is {theirs}, NOAA's {ours}"))
            return None
        assert abs((ours[0] - theirs[0]).total_seconds()) <= CHECK_SECONDS, (case_id, ours, theirs)
        if not near_new_year(ours[0]):
            assert abs(xtide.height(station, ours[0]) - ours[1]) <= CHECK_METERS, (case_id, ours)
    return {"id": case_id, "operation": "nextExtremes", "tags": tags,
            "input": {"constituents": constants(station), "startUtc": iso(start)},
            "expected": {"highUtc": iso(high[0]), "highHeightInMeters": high[1],
                         "lowUtc": iso(low[0]), "lowHeightInMeters": low[1]}}


def extremes_cases(xtide):
    rng = random.Random(18)
    cases = []
    for station, name in STATIONS:
        found = 0
        while found < EXTREMES_PER_STATION:
            start = FIRST + datetime.timedelta(hours=rng.randrange(0, int((LAST - FIRST).total_seconds() // 3600)))
            if near_new_year(start, 48):
                continue
            case = extremes_case(xtide, f"noaa-next-extremes-{name}-{start:%Y-%m-%d-%H%M}", station, start, ["published"])
            if case:
                cases.append(case)
                found += 1
    case = extremes_case(xtide, "noaa-next-extremes-seattle-2026-12-31-2000", "9447130",
                         datetime.datetime(2026, 12, 31, 20), ["published", "edge"])
    assert case
    return cases + [case]


def invalid_cases():
    m2 = {"name": "M2", "amplitudeInMeters": 1.0, "phaseInDegrees": 10.0}
    return [
        {"id": "invalid-height-unknown-constituent", "operation": "height", "tags": ["invalid"],
         "input": {"constituents": [m2, {"name": "XYZ2", "amplitudeInMeters": 0.1, "phaseInDegrees": 0.0}],
                   "instantUtc": "2026-01-01T00:00:00Z"},
         "expected": {"error": "invalidInput"}},
        {"id": "invalid-height-not-an-instant", "operation": "height", "tags": ["invalid"],
         "input": {"constituents": [m2], "instantUtc": "high tide"}, "expected": {"error": "invalidInput"}},
        {"id": "invalid-height-negative-amplitude", "operation": "height", "tags": ["invalid"],
         "input": {"constituents": [{"name": "M2", "amplitudeInMeters": -1.0, "phaseInDegrees": 10.0}],
                   "instantUtc": "2026-01-01T00:00:00Z"},
         "expected": {"error": "outOfRange"}},
        {"id": "invalid-next-extremes-unknown-constituent", "operation": "nextExtremes", "tags": ["invalid"],
         "input": {"constituents": [m2, {"name": "XYZ2", "amplitudeInMeters": 0.1, "phaseInDegrees": 0.0}],
                   "startUtc": "2026-01-01T00:00:00Z"},
         "expected": {"error": "invalidInput"}},
    ]


# Why a case exists, for the reader of the file and the page's list of edge cases.
NOTES = {
    "noaa-height-seattle-2026-12-31-2354": "The last 2026 prediction: still under 2026's V0+u and node factors.",
    "noaa-height-seattle-2027-01-01-0000": "The first 2027 prediction: NOAA switches to 2027's V0+u and node factors at 00:00 UTC, and Seattle's curve jumps about 8 cm.",
    "noaa-height-nikiski-2026-12-31-2354": "A large tide in Cook Inlet, the last 2026 prediction.",
    "noaa-height-nikiski-2027-01-01-0000": "The first 2027 prediction at Nikiski: the curve steps about 6 cm here.",
    "noaa-next-extremes-seattle-2026-12-31-2000": "Starts in 2026; the low and the high come in 2027, under 2027's values.",
    "invalid-height-unknown-constituent": "A name NOAA doesn't use.",
    "invalid-next-extremes-unknown-constituent": "A name NOAA doesn't use.",
}


def main():
    xtide = XTide()
    try:
        cases = height_cases(xtide) + extremes_cases(xtide) + invalid_cases()
    finally:
        noaa.save()
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids))
    xtide.log.save()
    data = json.loads(VECTORS.read_text())
    data.pop("placeholder", None)
    if data.get("cases") != cases:
        data["publishedDate"] = datetime.date.today().isoformat()
    data["cases"] = cases
    vectors_json.add_notes(data["cases"], NOTES)
    VECTORS.write_text(vectors_json.dumps(data))
    print(f"Wrote {len(cases)} cases to {VECTORS.relative_to(ROOT)}; left out: {dropped}")


if __name__ == "__main__":
    main()
