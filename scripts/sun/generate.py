"""Builds _data/vectors/sun.json.

  generate.py            query USNO and run Skyfield, log both under sun/sources/,
                         and rebuild the cases
  generate.py --offline  rebuild from the committed logs alone

Needs skyfield and JPL's de421.bsp for the first. Where the values come from:
- rise, set, transit, civil twilight and isAlwaysUp/Down: USNO's one-day data
  (/api/rstt/oneday), to the minute, logged in usno.jsonl.
- nautical and astronomical twilight: Skyfield's dark_twilight_day on DE421, logged in
  skyfield.txt. USNO's API doesn't give them. Skyfield is checked against USNO's rise, set
  and civil twilight on every case.
- position: USNO's celestial navigation data (/api/celnav), Hc and Zn, logged.
"""

import datetime
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import vectors_json  # noqa: E402
from logged import OFFLINE, USNO, Program  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "sun" / "sources"
VECTORS = ROOT / "_data" / "vectors" / "sun.json"
usno = USNO(SOURCES / "usno.jsonl")

PLACES = [
    ("alert", 82.5018, -62.3481), ("longyearbyen", 78.2232, 15.6267), ("tromso", 69.6492, 18.9553),
    ("reykjavik", 64.1466, -21.9426), ("fairbanks", 64.8378, -147.7164), ("helsinki", 60.1699, 24.9384),
    ("whitehorse", 60.7212, -135.0568), ("edinburgh", 55.9533, -3.1883), ("london", 51.5072, -0.1276),
    ("vancouver", 49.2827, -123.1207), ("west-vancouver", 49.3975, -123.2035), ("paris", 48.8566, 2.3522),
    ("montreal", 45.5019, -73.5674), ("new-york", 40.7128, -74.006), ("madrid", 40.4168, -3.7038),
    ("beijing", 39.9042, 116.4074), ("tokyo", 35.6762, 139.6503), ("los-angeles", 34.0522, -118.2437),
    ("cairo", 30.0444, 31.2357), ("delhi", 28.6139, 77.209), ("honolulu", 21.3099, -157.8581),
    ("mexico-city", 19.4326, -99.1332), ("dakar", 14.7167, -17.4677), ("bangkok", 13.7563, 100.5018),
    ("singapore", 1.3521, 103.8198), ("quito", -0.1807, -78.4678), ("nairobi", -1.2921, 36.8219),
    ("kiribati-line-islands", 1.8721, -157.4278), ("jakarta", -6.2088, 106.8456), ("lima", -12.0464, -77.0428),
    ("suva", -18.1248, 178.4501), ("tonga", -21.1394, -175.2018), ("rio", -22.9068, -43.1729),
    ("johannesburg", -26.2041, 28.0473), ("perth", -31.9523, 115.8613), ("santiago", -33.4489, -70.6693),
    ("sydney", -33.8688, 151.2093), ("cape-town", -33.9249, 18.4241), ("auckland", -36.8485, 174.7633),
    ("hobart", -42.8821, 147.3272), ("ushuaia", -54.8019, -68.303), ("mcmurdo", -77.8419, 166.6863),
    ("amundsen-scott", -89.99, 0.0), ("chatham-islands", -43.95, -176.55), ("date-line-north", 52.0, 179.9),
    ("date-line-west", 52.0, -179.9), ("equator-greenwich", 0.0, 0.0), ("arctic-circle", 66.5634, 25.8),
]
DATES = [datetime.date(2026, m, 21) for m in range(1, 13)]
# (name, place, date, tz): a window starting at local midnight rather than UTC midnight.
SHIFTED = [("vancouver-local-day", "vancouver", datetime.date(2026, 9, 29), -8),
           ("suva-local-day", "suva", datetime.date(2026, 3, 20), 12),
           ("tonga-local-day", "tonga", datetime.date(2026, 12, 21), 13),
           ("tokyo-local-day", "tokyo", datetime.date(2026, 6, 21), 9)]

USNO_NAMES = {"Rise": "riseUtc", "Set": "setUtc", "Upper Transit": "transitUtc",
              "Begin Civil Twilight": "civilDawnUtc", "End Civil Twilight": "civilDuskUtc"}


def iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


class Sky:
    """Skyfield, loaded only when not offline."""

    def __init__(self):
        self.log = Program(SOURCES / "skyfield.txt", "")
        if not OFFLINE:
            from skyfield import __version__, almanac
            from skyfield.api import load, wgs84
            self.almanac, self.wgs84 = almanac, wgs84
            self.eph = load("/tmp/astro/de421.bsp")
            self.ts = load.timescale()
            self.log.header = (f"Skyfield {__version__} on JPL DE421. Each line: latitude longitude start => the "
                               "dark_twilight_day transitions in the next 24 h as instant:state (0 night, 1 astronomical, "
                               "2 nautical, 3 civil, 4 day), then the state at the start and the sun's lowest and highest "
                               "altitude in the window.")

    def window(self, lat, lon, start):
        def compute():
            place = self.wgs84.latlon(lat, lon)
            t0 = self.ts.from_datetime(start.replace(tzinfo=datetime.timezone.utc))
            t1 = self.ts.from_datetime((start + datetime.timedelta(hours=24)).replace(tzinfo=datetime.timezone.utc))
            f = self.almanac.dark_twilight_day(self.eph, place)
            times, states = self.almanac.find_discrete(t0, t1, f)
            first = int(f(t0))
            observer = self.eph["earth"] + place
            samples = self.ts.linspace(t0, t1, 289)
            alt = observer.at(samples).observe(self.eph["sun"]).apparent().altaz()[0].degrees
            parts = [f"{t.utc_strftime('%Y-%m-%dT%H:%M:%SZ')}:{int(s)}" for t, s in zip(times, states)]
            return " ".join(parts + [f"start:{first}", f"min:{alt.min():.4f}", f"max:{alt.max():.4f}"])
        answer = self.log.call(f"{lat} {lon} {iso(start)}", compute)
        transitions, info = [], {}
        for part in answer.split():
            key, _, value = part.rpartition(":")
            if key in ("start", "min", "max"):
                info[key] = float(value)
            else:
                transitions.append((datetime.datetime.strptime(key, "%Y-%m-%dT%H:%M:%SZ"), int(value)))
        return transitions, info


def _position(self, lat, lon, instant):
    def compute():
        t = self.ts.from_datetime(datetime.datetime.strptime(instant, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc))
        alt, az, _ = (self.eph["earth"] + self.wgs84.latlon(lat, lon)).at(t).observe(self.eph["sun"]).apparent().altaz()
        return f"{az.degrees:.6f} {alt.degrees:.6f}"
    return self.log.call(f"position {lat} {lon} {instant}Z", compute)


Sky.position = _position


def crossings(transitions, start_state):
    """The first dawn and dusk across each level, from dark_twilight_day's transitions."""
    found = {}
    previous = start_state
    for moment, state in transitions:
        for level, dawn, dusk in ((1, "astronomicalDawnUtc", "astronomicalDuskUtc"), (2, "nauticalDawnUtc", "nauticalDuskUtc"),
                                  (3, "civilDawnUtc", "civilDuskUtc"), (4, "riseUtc", "setUtc")):
            if previous < level <= state:
                found.setdefault(dawn, moment)
            elif state < level <= previous:
                found.setdefault(dusk, moment)
        previous = state
    return found


def events_case(sky, case_id, lat, lon, date, tz, tags):
    start = datetime.datetime.combine(date, datetime.time()) - datetime.timedelta(hours=tz)
    data = usno.get(f"https://aa.usno.navy.mil/api/rstt/oneday?date={date.isoformat()}&coords={lat},{lon}&tz={tz}")
    sundata = data["properties"]["data"]["sundata"]
    phens = {entry["phen"]: entry["time"] for entry in sundata}
    expected = {}
    for phen, field in USNO_NAMES.items():
        if phens.get(phen):
            h, m = (int(v) for v in phens[phen].split(":"))
            expected[field] = datetime.datetime.combine(date, datetime.time(h, m)) - datetime.timedelta(hours=tz)
        else:
            expected[field] = None
    always_up = "Object continuously above the Horizon" in phens
    always_down = "Object continuously below the Horizon" in phens
    if expected["transitUtc"] is None:
        del expected["transitUtc"]  # USNO leaves transit out when the sun stays down; it still happens
    elif min(abs((expected["transitUtc"] - start).total_seconds()), abs((expected["transitUtc"] - start).total_seconds() - 86400)) < 90:
        del expected["transitUtc"]  # at the window's edge: the first transit may be just before or just after

    end = start + datetime.timedelta(hours=24)
    transitions, info = sky.window(lat, lon, start)
    sky_events = crossings(transitions, int(info["start"]))
    # Skyfield must agree with USNO on what USNO gives.
    for field in ("riseUtc", "setUtc", "civilDawnUtc", "civilDuskUtc"):
        a, b = expected[field], sky_events.get(field)
        grazing = min(abs(info["max"] - level) for level in (-0.8333, -6)) < 0.15 or \
            min(abs(info["min"] - level) for level in (-0.8333, -6)) < 0.15
        at_edge = any(m and min(abs((m - start).total_seconds()), abs((m - end).total_seconds())) < 90 for m in (a, b))
        if (a is None) != (b is None) or (a and abs((a - b).total_seconds()) > 45):
            assert grazing or at_edge, (case_id, field, a, b, info)
            del expected[field]
    for field, level in (("nauticalDawnUtc", -12), ("nauticalDuskUtc", -12),
                         ("astronomicalDawnUtc", -18), ("astronomicalDuskUtc", -18)):
        if abs(info["max"] - level) < 0.15 or abs(info["min"] - level) < 0.15:
            continue  # grazing the level: whether it's crossed depends on rounding
        moment = sky_events.get(field)
        if moment and min(abs((moment - start).total_seconds()), abs((moment - end).total_seconds())) < 90:
            continue  # at the window's edge: in or out depends on rounding
        expected[field] = moment
    out = {k: (iso(v) if v else None) for k, v in expected.items()}
    out["isAlwaysUp"] = always_up
    out["isAlwaysDown"] = always_down
    order = ["riseUtc", "setUtc", "transitUtc", "civilDawnUtc", "civilDuskUtc", "nauticalDawnUtc", "nauticalDuskUtc",
             "astronomicalDawnUtc", "astronomicalDuskUtc", "isAlwaysUp", "isAlwaysDown"]
    return {"id": case_id, "operation": "events", "tags": tags,
            "input": {"latitudeInDegrees": lat, "longitudeInDegrees": lon, "startUtc": iso(start), "windowInHours": 24},
            "expected": {k: out[k] for k in order if k in out}}


def events_cases(sky):
    cases = []
    by_name = {name: (lat, lon) for name, lat, lon in PLACES}
    for name, place, date, tz in SHIFTED:
        lat, lon = by_name[place]
        cases.append(events_case(sky, f"usno-events-{name}", lat, lon, date, tz, ["published", "reference", "edge"]))
    for name, lat, lon in PLACES:
        for date in DATES:
            polar = abs(lat) >= 60
            tags = ["published", "reference"] + (["polar"] if polar else [])
            if name in ("alert", "mcmurdo", "amundsen-scott", "longyearbyen") and date.month in (6, 12):
                tags.append("edge")
            cases.append(events_case(sky, f"usno-events-{name}-{date.isoformat()}", lat, lon, date, 0, tags))
    return cases


def position_cases(sky):
    rng = random.Random(9)
    rows = [("below-horizon", 49.2827, -123.1207, "2026-09-29T08:00:00"), ("noon-equator", 0.0, 0.0, "2026-03-20T12:00:00"),
            ("midnight-sun", 78.2232, 15.6267, "2026-06-21T23:00:00"), ("polar-night", -77.8419, 166.6863, "2026-06-21T00:00:00")]
    for n in range(1, 41):
        moment = datetime.datetime(2026, 1, 1) + datetime.timedelta(seconds=rng.randrange(0, 365 * 86400))
        rows.append((f"random-{n}", round(math.degrees(math.asin(2 * rng.random() - 1)) * 0.95, 4),
                     round(rng.uniform(-180, 180), 4), moment.strftime("%Y-%m-%dT%H:%M:%S")))
    cases = []
    for name, lat, lon, instant in rows:
        date, clock = instant.split("T")
        data = usno.get(f"https://aa.usno.navy.mil/api/celnav?date={date}&time={clock}&coords={lat},{lon}")
        bodies = [b for b in data["properties"]["data"] if b["object"] == "Sun"]
        if bodies:
            source, sun = "usno", bodies[0]["almanac_data"]
            zn, hc = sun["zn"], sun["hc"]
        else:
            # USNO lists only bodies above the horizon; below it, Skyfield answers.
            source = "skyfield"
            zn, hc = (float(v) for v in sky.position(lat, lon, instant).split())
        expected = {"azimuthInDegrees": zn, "altitudeInDegrees": hc}
        if hc > 89.9 or not 1e-3 < zn < 360 - 1e-3:
            del expected["azimuthInDegrees"]
        kind = "published" if source == "usno" else "reference"
        cases.append({"id": f"{source}-position-{name}", "operation": "position",
                      "tags": [kind] if name.startswith("random") else [kind, "edge"],
                      "input": {"latitudeInDegrees": lat, "longitudeInDegrees": lon, "instantUtc": instant + "Z"},
                      "expected": expected})
    return cases


def invalid_cases():
    return [
        {"id": "invalid-events-latitude-91", "operation": "events", "tags": ["invalid"],
         "input": {"latitudeInDegrees": 91, "longitudeInDegrees": 0, "startUtc": "2026-01-01T00:00:00Z", "windowInHours": 24},
         "expected": {"error": "outOfRange"}},
        {"id": "invalid-events-window-0", "operation": "events", "tags": ["invalid"],
         "input": {"latitudeInDegrees": 0, "longitudeInDegrees": 0, "startUtc": "2026-01-01T00:00:00Z", "windowInHours": 0},
         "expected": {"error": "outOfRange"}},
        {"id": "invalid-position-not-an-instant", "operation": "position", "tags": ["invalid"],
         "input": {"latitudeInDegrees": 0, "longitudeInDegrees": 0, "instantUtc": "noon"},
         "expected": {"error": "invalidInput"}},
    ]


def main():
    sky = Sky()
    try:
        cases = events_cases(sky) + position_cases(sky) + invalid_cases()
    finally:
        usno.save()
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids))
    usno.save()
    sky.log.save()
    data = json.loads(VECTORS.read_text())
    data.pop("placeholder", None)
    data.pop("expiresDate", None)  # the sun's data doesn't run out
    if data.get("cases") != cases:
        data["publishedDate"] = datetime.date.today().isoformat()
    data["cases"] = cases
    VECTORS.write_text(vectors_json.dumps(data))
    print(f"Wrote {len(cases)} cases to {VECTORS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
