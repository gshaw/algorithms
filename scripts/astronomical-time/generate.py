"""Builds _data/vectors/astronomical-time.json.

  generate.py            query USNO and run ERFA, log both under astronomical-time/sources/,
                         and rebuild the cases
  generate.py --offline  rebuild from the committed logs alone

Needs pyerfa for the first (pip install pyerfa). Where the values come from:
- julianDay and calendarDate: USNO's Julian Date Converter API, logged in usno.jsonl.
- siderealTime: USNO's Sidereal Time API, logged in usno.jsonl.
- deltaT: USNO's tables for the IERS Rapid Service, deltat.data (observed, monthly)
  and deltat.preds (predicted, quarterly), copied verbatim.
- horizontal: ERFA 2.0 (the open-source SOFA), eraGmst82 and eraHd2ae, logged in erfa.txt.
The words (sources, operations, fields, tolerances) are edited in the JSON by hand.
"""

import datetime
import json
import math
import random
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import vectors_json  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "astronomical-time" / "sources"
USNO_LOG = SOURCES / "usno.jsonl"
ERFA_LOG = SOURCES / "erfa.txt"
VECTORS = ROOT / "astronomical-time" / "vectors.json"
OFFLINE = "--offline" in sys.argv

usno_cache = {}
if USNO_LOG.exists():
    for line in USNO_LOG.read_text().splitlines():
        entry = json.loads(line)
        usno_cache[entry["url"]] = entry["response"]
usno_used = []


def usno(url):
    """USNO's response, from the log when it's there. Only new URLs are fetched."""
    if url not in usno_cache:
        assert not OFFLINE, f"not in the log: {url}"
        with urllib.request.urlopen(url, timeout=60) as response:
            usno_cache[url] = json.load(response)
        time.sleep(0.5)
    usno_used.append(url)
    return usno_cache[url]


def decimal_year(year, month, day):
    """This file's rule, as in the wmm file: the year plus the days before the date over
    the days in its year."""
    start = datetime.date(year, 1, 1)
    days = (datetime.date(year + 1, 1, 1) - start).days
    return year + (datetime.date(year, month, day) - start).days / days


def astronomical(year, era):
    return year if era in ("AD", "CE") else 1 - year


# Julian days

INSTANTS = [
    ("j2000", "2000-01-01T12:00:00Z", "edge"),
    ("unix-epoch", "1970-01-01T00:00:00Z", None),
    ("gregorian-first-day", "1582-10-15T00:00:00Z", "edge"),
    ("julian-last-day", "1582-10-04T23:59:59Z", "edge"),
    ("julian-calendar", "1066-10-14T09:00:00Z", None),
    ("year-1", "0001-01-01T00:00:00Z", "edge"),
    ("year-0-leap-day", "0000-02-29T12:00:00Z", "edge"),
    ("julian-day-zero", "-4712-01-01T12:00:00Z", "edge"),
    ("century-not-leap", "1900-03-01T00:00:00Z", "edge"),
    ("century-leap", "2000-02-29T18:00:00Z", "edge"),
    ("far-future", "9999-12-31T23:59:59Z", "edge"),
    ("leap-second-day", "2016-12-31T23:59:59Z", None),
]


def split_instant(instant):
    sign = -1 if instant.startswith("-") else 1
    date, clock = instant.lstrip("-").rstrip("Z").split("T")
    year, month, day = (int(v) for v in date.split("-"))
    return sign * year, month, day, clock


def usno_julian_day(instant):
    year, month, day, clock = split_instant(instant)
    era, shown = ("AD", year) if year >= 1 else ("BC", 1 - year)
    url = f"https://aa.usno.navy.mil/api/juliandate?date={shown}-{month}-{day}&time={clock}&era={era}"
    data = usno(url)["data"][0]
    return float(data["jd"])


def julian_day_cases():
    cases = []
    rng = random.Random(5)
    instants = list(INSTANTS)
    for n in range(1, 21):
        moment = datetime.datetime(1600, 1, 1) + datetime.timedelta(seconds=rng.randrange(0, 500 * 365 * 86400))
        instants.append((f"random-{n}", moment.strftime("%Y-%m-%dT%H:%M:%SZ"), None))
    for name, instant, edge in instants:
        cases.append({"id": f"usno-julian-day-{name}", "operation": "julianDay",
                      "tags": ["published", edge] if edge else ["published"],
                      "input": {"instantUtc": instant},
                      "expected": {"julianDay": usno_julian_day(instant)}})
    return cases


JULIAN_DAYS = [
    ("gregorian-first-day", 2299160.5), ("julian-last-day", 2299159.5), ("j2000", 2451545.0),
    ("zero", 0.0), ("year-0", 1721057.5), ("year-1", 1721423.5), ("just-before-midnight", 2460000.49),
    ("modified-epoch", 2400000.5), ("sputnik", 2436116.31), ("far-future", 5373484.0),
]


def calendar_date_cases():
    cases = []
    rng = random.Random(6)
    days = list(JULIAN_DAYS) + [(f"random-{n}", round(rng.uniform(1_000_000, 2_600_000), 4)) for n in range(1, 16)]
    for name, jd in days:
        data = usno(f"https://aa.usno.navy.mil/api/calendardate?jd={jd}")["data"][0]
        year = astronomical(int(data["year"]), data["era"])
        date = f"{'-' if year < 0 else ''}{abs(year):04d}-{int(data['month']):02d}-{int(data['day']):02d}"
        calendar = "gregorian" if (year, int(data["month"]), int(data["day"])) >= (1582, 10, 15) else "julian"
        cases.append({"id": f"usno-calendar-date-{name}", "operation": "calendarDate",
                      "tags": ["published", "edge"] if not name.startswith("random") else ["published"],
                      "input": {"julianDay": jd}, "expected": {"date": date, "calendar": calendar}})
    return cases


# Sidereal time

def hours(text):
    h, m, s = text.split(":")
    return int(h) + int(m) / 60 + float(s) / 3600


def sidereal_cases():
    rng = random.Random(7)
    points = [("greenwich-j2000", "2000-01-01T12:00:00Z", 0.0), ("date-line", "2026-06-21T00:00:00Z", 180.0),
              ("west", "2026-09-29T19:21:00Z", -123.12), ("east", "1987-04-10T19:21:00Z", 139.69)]
    for n in range(1, 21):
        moment = datetime.datetime(1950, 1, 1) + datetime.timedelta(seconds=rng.randrange(0, 100 * 365 * 86400))
        points.append((f"random-{n}", moment.strftime("%Y-%m-%dT%H:%M:%SZ"), round(rng.uniform(-180, 180), 4)))
    cases = []
    for name, instant, lon in points:
        date, clock = instant.rstrip("Z").split("T")
        url = (f"https://aa.usno.navy.mil/api/siderealtime?date={date}&time={clock}"
               f"&coords=0,{lon}&reps=1&intv_mag=1&intv_unit=hours")
        data = usno(url)["properties"]["data"][0]
        cases.append({"id": f"usno-sidereal-{name}", "operation": "siderealTime",
                      "tags": ["published"] if name.startswith("random") else ["published", "edge"],
                      "input": {"instantUtc": instant, "longitudeInDegrees": lon},
                      "expected": {"greenwichSiderealTimeInHours": round(hours(data["gmst"]), 9),
                                   "localSiderealTimeInHours": round(hours(data["lmst"]), 9)}})
    return cases


# ΔT

def delta_t_cases():
    cases = []
    observed = [line.split() for line in (SOURCES / "deltat.data").read_text().splitlines() if line.strip()]
    for year, month, day, value in observed:
        year, month, day = int(year), int(month), int(day)
        if month != 1 and (year, month) != tuple(int(v) for v in observed[-1][:2]):
            continue
        cases.append({"id": f"usno-delta-t-{year}-{month:02d}", "operation": "deltaT", "tags": ["published"],
                      "input": {"decimalYear": round(decimal_year(year, month, day), 6)},
                      "expected": {"deltaTInSeconds": float(value)}})
    last = datetime.date(*(int(v) for v in observed[-1][:3]))
    for line in (SOURCES / "deltat.preds").read_text().splitlines()[1:]:
        fields = line.split()
        mjd, value = float(fields[0]), float(fields[2])
        date = datetime.date(1858, 11, 17) + datetime.timedelta(days=mjd)
        if date <= last:
            continue
        cases.append({"id": f"usno-delta-t-predicted-{date.year}-{date.month:02d}", "operation": "deltaT",
                      "tags": ["published"], "input": {"decimalYear": round(decimal_year(date.year, date.month, date.day), 6)},
                      "expected": {"deltaTInSeconds": value}})
    return cases, date


# Horizontal, from ERFA

def horizontal_cases():
    rng = random.Random(8)
    rows = []
    for n in range(1, 41):
        moment = datetime.datetime(2000, 1, 1) + datetime.timedelta(seconds=rng.randrange(0, 50 * 365 * 86400))
        rows.append((f"random-{n}", round(rng.uniform(0, 24), 6), round(math.degrees(math.asin(2 * rng.random() - 1)), 6),
                     round(math.degrees(math.asin(2 * rng.random() - 1)), 6), round(rng.uniform(-180, 180), 6),
                     moment.strftime("%Y-%m-%dT%H:%M:%SZ")))
    rows += [
        ("equinox-morning", 6.0, 49.0, 49.0, 0.0, "2026-03-20T06:00:00Z"),
        ("pole-star-from-equator", 2.5303, 89.2641, 0.0, 0.0, "2026-01-01T00:00:00Z"),
        ("below-horizon", 12.0, -60.0, 49.28, -123.12, "2026-09-29T19:21:00Z"),
        ("south-pole-observer", 5.0, -30.0, -89.9999, 0.0, "2026-06-21T12:00:00Z"),
    ]
    if OFFLINE:
        logged = {}
        for line in ERFA_LOG.read_text().splitlines():
            if not line.startswith("#"):
                key, result = line.split(" => ")
                logged[key] = result
    else:
        import erfa
        log = [f"# ERFA {erfa.version.erfa_version} via pyerfa {erfa.__version__}. Each line: ra hours, dec, latitude, "
               "longitude, instant => gmst82 hours, azimuth, altitude (degrees). UT1 taken as the UTC given."]
    cases = []
    for name, ra, dec, lat, lon, instant in rows:
        key = f"{ra} {dec} {lat} {lon} {instant}"
        if OFFLINE:
            gmst, az, alt = (float(v) for v in logged[key].split())
        else:
            moment = datetime.datetime.strptime(instant, "%Y-%m-%dT%H:%M:%SZ")
            jd = 2440587.5 + (moment - datetime.datetime(1970, 1, 1)).total_seconds() / 86400
            gmst = erfa.gmst82(jd, 0.0)
            ha = gmst + math.radians(lon) - math.radians(ra * 15)
            az_r, alt_r = erfa.hd2ae(ha, math.radians(dec), math.radians(lat))
            gmst, az, alt = math.degrees(gmst) / 15, math.degrees(az_r) % 360, math.degrees(alt_r)
            log.append(f"{key} => {gmst:.12f} {az:.10f} {alt:.10f}")
        if alt > 89.99 or abs(lat) > 89.99:
            az_expected = None  # azimuth is undefined at the zenith and at a pole
        else:
            az_expected = round(az, 8)
        expected = {"altitudeInDegrees": round(alt, 8)}
        if az_expected is not None and 1e-3 < az_expected < 360 - 1e-3:
            expected = {"azimuthInDegrees": az_expected, **expected}
        cases.append({"id": f"erfa-horizontal-{name}", "operation": "horizontal",
                      "tags": ["reference"] if name.startswith("random") else ["reference", "edge"],
                      "input": {"rightAscensionInHours": ra, "declinationInDegrees": dec, "latitudeInDegrees": lat,
                                "longitudeInDegrees": lon, "instantUtc": instant},
                      "expected": expected})
    if not OFFLINE:
        ERFA_LOG.write_text("\n".join(log) + "\n")
    return cases


def invalid_cases():
    return [
        {"id": "invalid-julian-day-nonexistent-date", "operation": "julianDay", "tags": ["invalid"],
         "input": {"instantUtc": "1582-10-10T00:00:00Z"}, "expected": {"error": "invalidInput"}},
        {"id": "invalid-julian-day-not-an-instant", "operation": "julianDay", "tags": ["invalid"],
         "input": {"instantUtc": "yesterday"}, "expected": {"error": "invalidInput"}},
        {"id": "invalid-delta-t-before-1973", "operation": "deltaT", "tags": ["invalid"],
         "input": {"decimalYear": 1900.0}, "expected": {"error": "outOfRange"}},
        {"id": "invalid-horizontal-latitude-91", "operation": "horizontal", "tags": ["invalid"],
         "input": {"rightAscensionInHours": 1, "declinationInDegrees": 1, "latitudeInDegrees": 91,
                   "longitudeInDegrees": 0, "instantUtc": "2026-01-01T00:00:00Z"}, "expected": {"error": "outOfRange"}},
    ]


# Why a case exists, for the reader of the file and the page's list of edge cases.
NOTES = {
    "usno-julian-day-j2000": "The J2000 epoch: 2451545.0.",
    "usno-julian-day-julian-last-day": "1582-10-04 in the Julian calendar is followed by 1582-10-15 in the Gregorian.",
    "usno-julian-day-gregorian-first-day": "The Gregorian calendar's first day: 2299160.5.",
    "usno-julian-day-year-0-leap-day": "Year 0 is 1 BC, a Julian leap year.",
    "usno-julian-day-julian-day-zero": "Noon on 1 January 4713 BC, written -4712: Julian day 0.",
    "usno-julian-day-century-not-leap": "1900 isn't a Gregorian leap year.",
    "usno-julian-day-century-leap": "2000 is.",
    "usno-calendar-date-zero": "Julian day 0 is -4712-01-01 in the Julian calendar.",
    "usno-calendar-date-just-before-midnight": "A fraction just under .5 is still the day before.",
    "usno-sidereal-greenwich-j2000": "Greenwich mean sidereal time at the J2000 epoch.",
    "usno-sidereal-date-line": "At 180°, local is Greenwich plus 12 hours, wrapped.",
    "erfa-horizontal-below-horizon": "Below the horizon: a negative altitude, not an error.",
    "erfa-horizontal-south-pole-observer": "At a pole azimuth is undefined: only altitude is compared.",
    "invalid-julian-day-nonexistent-date": "1582-10-10 never happened: invalidInput.",
    "invalid-delta-t-before-1973": "Before USNO's observed table: outOfRange.",
}

def main():
    delta, last_prediction = delta_t_cases()
    cases = julian_day_cases() + calendar_date_cases() + sidereal_cases() + delta + horizontal_cases() + invalid_cases()
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1][:5]
    if not OFFLINE:
        USNO_LOG.write_text("".join(json.dumps({"url": u, "response": usno_cache[u]}, sort_keys=True) + "\n"
                                    for u in dict.fromkeys(usno_used)))
    data = json.loads(VECTORS.read_text())
    data.pop("placeholder", None)
    data["expiresDate"] = last_prediction.isoformat()
    if data.get("cases") != cases:
        data["publishedDate"] = datetime.date.today().isoformat()
    data["cases"] = cases
    vectors_json.add_notes(data["cases"], NOTES)
    VECTORS.write_text(vectors_json.dumps(data))
    print(f"Wrote {len(cases)} cases to {VECTORS.relative_to(ROOT)}; ΔT predictions end {last_prediction}")


if __name__ == "__main__":
    main()
