"""Builds _data/vectors/moon.json.

  generate.py            query USNO and run Skyfield, log both under moon/sources/,
                         and rebuild the cases
  generate.py --offline  rebuild from the committed logs alone

Needs skyfield and JPL's de421.bsp for the first. Where the values come from:
- rise, set, transit and isAlwaysUp/Down: USNO's one-day data (/api/rstt/oneday), to
  the minute, checked against Skyfield's find_risings and find_settings.
- nextPhases: USNO's primary phases (/api/moon/phases/date), to the minute.
- phase: Skyfield on DE421 for illumination, phase angle and elongation, checked against
  USNO's percentage lit; phaseName from the elongation by the rule in the file's fields.
  Elongation is left out within 0.5° of new moon, where it wraps from 360 to 0.
- position: Skyfield on DE421, seen from the place, checked against USNO's celestial
  navigation data (/api/celnav). USNO's Hc is from the Earth's centre, so the check is
  against Hc minus its parallax in altitude.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sun"))
from generate import DATES, PLACES, SHIFTED, iso  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "moon" / "sources"
VECTORS = ROOT / "moon" / "vectors.json"
usno = USNO(SOURCES / "usno.jsonl")
dropped = []
NAMES = ["new", "waxingCrescent", "firstQuarter", "waxingGibbous", "full", "waningGibbous", "lastQuarter", "waningCrescent"]


class Sky:
    def __init__(self):
        self.log = Program(SOURCES / "skyfield.txt", "")
        if not OFFLINE:
            from skyfield import __version__, almanac
            from skyfield.api import load, wgs84
            self.almanac, self.wgs84 = almanac, wgs84
            self.eph = load("/tmp/astro/de421.bsp")
            self.ts = load.timescale()
            self.log.header = (f"Skyfield {__version__} on JPL DE421. 'events' lines: latitude longitude start => risings "
                               "and settings in the next 24 h (find_risings, find_settings) and the moon's lowest and highest "
                               "altitude. 'phase' lines: instant => fraction illuminated, phase angle, elongation (degrees). "
                               "'position' lines: place and instant => azimuth and altitude seen from the place, no "
                               "refraction.")

    def t(self, moment):
        return self.ts.from_datetime(moment.replace(tzinfo=datetime.timezone.utc))

    def events(self, lat, lon, start):
        def compute():
            place = self.wgs84.latlon(lat, lon)
            observer = self.eph["earth"] + place
            t0, t1 = self.t(start), self.t(start + datetime.timedelta(hours=24))
            rises, rise_ok = self.almanac.find_risings(observer, self.eph["moon"], t0, t1)
            sets, set_ok = self.almanac.find_settings(observer, self.eph["moon"], t0, t1)
            alt = observer.at(self.ts.linspace(t0, t1, 289)).observe(self.eph["moon"]).apparent().altaz()[0].degrees
            parts = [f"rise:{t.utc_strftime('%Y-%m-%dT%H:%M:%SZ')}" for t, ok in zip(rises, rise_ok) if ok]
            parts += [f"set:{t.utc_strftime('%Y-%m-%dT%H:%M:%SZ')}" for t, ok in zip(sets, set_ok) if ok]
            return " ".join(parts + [f"min:{alt.min():.4f}", f"max:{alt.max():.4f}"])
        answer = self.log.call(f"events {lat} {lon} {iso(start)}", compute)
        found, info = {}, {}
        for part in answer.split():
            key, _, value = part.partition(":")
            if key in ("min", "max"):
                info[key] = float(value)
            else:
                found.setdefault(key, datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ"))
        return found, info

    def phase(self, moment):
        def compute():
            t = self.t(moment)
            earth, sun, moon = self.eph["earth"], self.eph["sun"], self.eph["moon"]
            fraction = self.almanac.fraction_illuminated(self.eph, "moon", t)
            m = earth.at(t).observe(moon).apparent()
            s = earth.at(t).observe(sun).apparent()
            angle = m.phase_angle(sun).degrees
            _, moon_lon, _ = m.frame_latlon(self._ecliptic())
            _, sun_lon, _ = s.frame_latlon(self._ecliptic())
            elongation = (moon_lon.degrees - sun_lon.degrees) % 360
            return f"{fraction:.6f} {angle:.6f} {elongation:.6f}"
        fraction, angle, elongation = (float(v) for v in self.log.call(f"phase {iso(moment)}", compute).split())
        return fraction, angle, elongation

    def position(self, lat, lon, moment):
        def compute():
            observer = self.eph["earth"] + self.wgs84.latlon(lat, lon)
            alt, az, _ = observer.at(self.t(moment)).observe(self.eph["moon"]).apparent().altaz()
            return f"{az.degrees:.6f} {alt.degrees:.6f}"
        return (float(v) for v in self.log.call(f"position {lat} {lon} {iso(moment)}", compute).split())

    def _ecliptic(self):
        from skyfield.framelib import ecliptic_frame
        return ecliptic_frame


def events_case(sky, case_id, lat, lon, date, tz, tags):
    start = datetime.datetime.combine(date, datetime.time()) - datetime.timedelta(hours=tz)
    end = start + datetime.timedelta(hours=24)
    data = usno.get(f"https://aa.usno.navy.mil/api/rstt/oneday?date={date.isoformat()}&coords={lat},{lon}&tz={tz}")
    phens = {e["phen"]: e["time"] for e in data["properties"]["data"]["moondata"]}
    expected = {}
    for phen, field in (("Rise", "riseUtc"), ("Set", "setUtc"), ("Upper Transit", "transitUtc")):
        if phens.get(phen):
            h, m = (int(v) for v in phens[phen].split(":"))
            expected[field] = datetime.datetime.combine(date, datetime.time(h, m)) - datetime.timedelta(hours=tz)
        else:
            expected[field] = None
    always_up = "Object continuously above the Horizon" in phens
    always_down = "Object continuously below the Horizon" in phens
    if expected["transitUtc"] is None:
        del expected["transitUtc"]

    found, info = sky.events(lat, lon, start)
    grazing = abs(info["max"]) < 1.2 or abs(info["min"]) < 1.2

    def near_edge(m):
        return m is not None and min(abs((m - start).total_seconds()), abs((m - end).total_seconds())) < 180

    for field, key in (("riseUtc", "rise"), ("setUtc", "set")):
        a, b = expected[field], found.get(key)
        if near_edge(a) or near_edge(b) or grazing:
            del expected[field]
            continue
        if (a is None) != (b is None) or (a and abs((a - b).total_seconds()) > 90):
            # Near a pole the moon can skim the horizon for hours; USNO and Skyfield may
            # then disagree, so the field is left out. Anywhere else they must agree.
            assert abs(lat) >= 60, (case_id, field, a, b, info)
            dropped.append((case_id, field))
            del expected[field]
    if "transitUtc" in expected and near_edge(expected["transitUtc"]):
        del expected["transitUtc"]
    out = {k: (iso(v) if v else None) for k, v in expected.items()}
    if not grazing:
        out["isAlwaysUp"] = always_up
        out["isAlwaysDown"] = always_down
    return {"id": case_id, "operation": "events", "tags": tags,
            "input": {"latitudeInDegrees": lat, "longitudeInDegrees": lon, "startUtc": iso(start), "windowInHours": 24},
            "expected": out}


def events_cases(sky):
    by_name = {name: (lat, lon) for name, lat, lon in PLACES}
    cases = [events_case(sky, f"usno-events-{name}", *by_name[place], date, tz, ["published", "edge"])
             for name, place, date, tz in SHIFTED]
    for name, lat, lon in PLACES:
        for date in DATES:
            tags = ["published"] + (["polar"] if abs(lat) >= 60 else [])
            cases.append(events_case(sky, f"usno-events-{name}-{date.isoformat()}", lat, lon, date, 0, tags))
    return cases


def primary_phases(date, count=4):
    data = usno.get(f"https://aa.usno.navy.mil/api/moon/phases/date?date={date.isoformat()}&nump={count}")
    phases = []
    for p in data["phasedata"]:
        h, m = (int(v) for v in p["time"].split(":"))
        phases.append((p["phase"], datetime.datetime(p["year"], p["month"], p["day"], h, m)))
    return phases


def next_phase_cases():
    fields = {"New Moon": "newMoonUtc", "First Quarter": "firstQuarterUtc", "Full Moon": "fullMoonUtc", "Last Quarter": "lastQuarterUtc"}
    cases = []
    for month in range(1, 13):
        for day in (1, 16):
            date = datetime.date(2026, month, day)
            start = datetime.datetime.combine(date, datetime.time())
            phases = primary_phases(date)
            expected = {fields[name]: iso(moment) for name, moment in phases}
            if any(abs((m - start).total_seconds()) < 180 for _, m in phases):
                continue
            order = ["newMoonUtc", "firstQuarterUtc", "fullMoonUtc", "lastQuarterUtc"]
            cases.append({"id": f"usno-next-phases-{date.isoformat()}", "operation": "nextPhases", "tags": ["published"],
                          "input": {"startUtc": iso(start)}, "expected": {k: expected[k] for k in order}})
    return cases


def name_for(elongation):
    return NAMES[int(((elongation + 22.5) % 360) // 45)]


def phase_cases(sky):
    rng = random.Random(10)
    moments = [(f"random-{n}", datetime.datetime(2026, 1, 1) + datetime.timedelta(seconds=rng.randrange(0, 365 * 86400)))
               for n in range(1, 61)]
    # Exactly at USNO's primary phases: the name must be that phase.
    for name, moment in primary_phases(datetime.date(2026, 3, 1), 8):
        moments.append((f"at-{name.lower().replace(' ', '-')}-{moment.date().isoformat()}", moment))
    cases = []
    for label, moment in moments:
        fraction, angle, elongation = sky.phase(moment)
        edge = min(abs(((elongation - 22.5) % 45) - 0), abs(((elongation - 22.5) % 45) - 45))
        if edge < 0.5:
            continue  # within 0.5° of a boundary between names
        # USNO gives the fraction lit as a whole percent for 12:00 UT on the date, whatever
        # time is asked: check Skyfield against it there.
        data = usno.get(f"https://aa.usno.navy.mil/api/rstt/oneday?date={moment.date().isoformat()}&coords=0,0&tz=0")
        percent = int(data["properties"]["data"]["fracillum"].rstrip("%"))
        noon_fraction, _, _ = sky.phase(datetime.datetime.combine(moment.date(), datetime.time(12)))
        assert abs(percent / 100 - noon_fraction) <= 0.006, (label, percent, noon_fraction)
        expected = {"illuminationFraction": round(fraction, 4), "phaseAngleInDegrees": round(angle, 3),
                    "elongationInDegrees": round(elongation, 4), "phaseName": name_for(elongation)}
        if min(elongation, 360 - elongation) < 0.5:
            del expected["elongationInDegrees"]  # 359.996 and 0.002 are the same answer
        cases.append({"id": f"skyfield-phase-{label}", "operation": "phase",
                      "tags": ["reference", "edge"] if label.startswith("at-") else ["reference"],
                      "input": {"instantUtc": iso(moment)}, "expected": expected})
    return cases


def position_cases(sky):
    rows = [("low", 49.2827, -123.1207, datetime.datetime(2026, 9, 30, 3, 0)),
            ("below-horizon", 49.2827, -123.1207, datetime.datetime(2026, 9, 29, 20, 0)),
            ("always-up", 82.5018, -62.3481, datetime.datetime(2026, 3, 21, 12, 0)),
            ("south-pole", -89.99, 0.0, datetime.datetime(2026, 6, 21, 0, 0))]
    rng = random.Random(11)
    for n in range(1, 41):
        moment = datetime.datetime(2026, 1, 1) + datetime.timedelta(seconds=rng.randrange(0, 365 * 86400))
        rows.append((f"random-{n}", round(math.degrees(math.asin(2 * rng.random() - 1)) * 0.95, 4),
                     round(rng.uniform(-180, 180), 4), moment))
    cases = []
    for name, lat, lon, moment in rows:
        az, alt = sky.position(lat, lon, moment)
        date, clock = iso(moment).rstrip("Z").split("T")
        data = usno.get(f"https://aa.usno.navy.mil/api/celnav?date={date}&time={clock}&coords={lat},{lon}")
        moon = [b for b in data["properties"]["data"] if b["object"] == "Moon"]
        if moon and moon[0]["altitude_corrections"]["isCorrected"]:
            # USNO lists the moon only when it's up, from the Earth's centre, with its
            # parallax in altitude (pa) beside it.
            usno_alt = moon[0]["almanac_data"]["hc"] - moon[0]["altitude_corrections"]["pa"]
            usno_az = moon[0]["almanac_data"]["zn"]
            assert abs(alt - usno_alt) < 0.005, (name, alt, usno_alt)
            assert abs((az - usno_az + 180) % 360 - 180) * math.cos(math.radians(alt)) < 0.01, (name, az, usno_az)
        expected = {"azimuthInDegrees": round(az, 4), "altitudeInDegrees": round(alt, 4)}
        if alt > 89.9:
            del expected["azimuthInDegrees"]
        cases.append({"id": f"skyfield-position-{name}", "operation": "position",
                      "tags": ["reference"] if name.startswith("random") else ["reference", "edge"],
                      "input": {"latitudeInDegrees": lat, "longitudeInDegrees": lon, "instantUtc": iso(moment)},
                      "expected": expected})
    return cases


def invalid_cases():
    return [
        {"id": "invalid-events-latitude-91", "operation": "events", "tags": ["invalid"],
         "input": {"latitudeInDegrees": 91, "longitudeInDegrees": 0, "startUtc": "2026-01-01T00:00:00Z", "windowInHours": 24},
         "expected": {"error": "outOfRange"}},
        {"id": "invalid-phase-not-an-instant", "operation": "phase", "tags": ["invalid"],
         "input": {"instantUtc": "tonight"}, "expected": {"error": "invalidInput"}},
        {"id": "invalid-position-latitude-91", "operation": "position", "tags": ["invalid"],
         "input": {"latitudeInDegrees": 91, "longitudeInDegrees": 0, "instantUtc": "2026-01-01T00:00:00Z"},
         "expected": {"error": "outOfRange"}},
    ]


# Why a case exists, for the reader of the file and the page's list of edge cases.
NOTES = {
    "usno-events-vancouver-2026-09-21": "No moonrise in this UTC day: riseUtc is null, not the next day's.",
    "usno-events-alert-2026-03-21": "The moon stays up all day.",
    "usno-events-alert-2026-08-21": "The moon stays down all day.",
    "usno-events-tonga-local-day": "A window from local midnight across the date line.",
    "skyfield-phase-at-first-quarter-2026-03-25": "Exactly at first quarter: firstQuarter, not a neighbour.",
    "skyfield-phase-at-full-moon-2026-03-03": "Exactly at full moon.",
    "skyfield-phase-at-new-moon-2026-03-19": "Exactly at new moon: almost nothing lit.",
    "skyfield-position-low": "Just risen: seen from the place, almost 1° lower than from the Earth's centre.",
    "skyfield-position-below-horizon": "Below the horizon: a negative altitude, not an error.",
    "skyfield-position-always-up": "Up all day at Alert, low in the sky.",
    "skyfield-position-south-pole": "A kilometre from the South Pole: azimuth is still clockwise from true north.",
    "usno-next-phases-2026-03-16": "The four phases come in order from the start, crossing into April.",
}

def main():
    sky = Sky()
    try:
        cases = events_cases(sky) + next_phase_cases() + phase_cases(sky) + position_cases(sky) + invalid_cases()
    finally:
        usno.save()
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids))
    sky.log.save()
    data = json.loads(VECTORS.read_text())
    data.pop("placeholder", None)
    data.pop("expiresDate", None)  # the moon's data doesn't run out
    if data.get("cases") != cases:
        data["publishedDate"] = datetime.date.today().isoformat()
    data["cases"] = cases
    vectors_json.add_notes(data["cases"], NOTES)
    VECTORS.write_text(vectors_json.dumps(data))
    print(f"Wrote {len(cases)} cases to {VECTORS.relative_to(ROOT)}; left out where USNO and Skyfield disagree: {dropped}")


if __name__ == "__main__":
    main()
