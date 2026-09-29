# Plan

**2026-09-29. The lander is live; no test data yet.** The first four algorithms are issues
[#1](https://github.com/gshaw/algorithms/issues/1) to
[#4](https://github.com/gshaw/algorithms/issues/4), in that order.

**This site publishes test data for pure calculations, and links to implementations that
pass it.** It has no implementation code of its own. An app copies an implementation into
its own source, often one an agent wrote from the algorithm's page, and knows it's right
because it passes the file.

## Why

Gerry's apps each carry the same physical-world maths behind a different dependency, and
one copy has already gone stale: LandNav ships the WMM-2020 magnetic model, which expired
at the end of 2024. The same maths shows up across the apps:

| Dependency | In | Replaced by |
| --- | --- | --- |
| Geographic (vendored GeographicLib C++) | LandNav | UTM and MGRS, #2 |
| SunCalc | LandNav, Tides, MarNav | Sun and moon, #4 |
| A hand-copied WMM-2020 | LandNav, LandNav 2 | Magnetic declination, #1 |
| SwiftTimeZoneLookup | Tides, MarNav | A time zone data file, later |
| Polyline, Geoflash | MarNav | Encoded polyline and geohash, later |

Turf stays in the apps that use Mapbox, which brings it anyway. It is never the reference
for a number.

## Rules

- **Expected values never come from a language model.** Each comes from an authority's
  published values or a reference program run on a Mac: NOAA's WMM test values,
  GeographicLib's `GeoConvert`, the USNO API. The raw output is kept in the repo beside
  the file it produced, so anyone can audit it or regenerate without the reference.
- **Tolerances, not bit-for-bit matching.** Each output says how close is right: 1 mm for
  an easting, 1 min for a sunrise. Any correct method passes.
- **One earth model per number.** Each file says whether it measures on the WGS84
  ellipsoid or on a sphere, and which radius.
- **Every edge case is a named case**, not a paragraph: polar night, the Svalbard zones,
  359.6° written as `000°`.
- **Data that expires says so.** A file built on a model with an end date carries
  `expiresAt`, and the site shows it.
- **Licences travel with the data.** Test data is CC0. Sources are mostly public domain
  (NOAA, USNO) or MIT (GeographicLib). Anything derived from OpenStreetMap is ODbL, so
  decide what that means before any boundary data.

## An algorithm's page

At `algorithms.gshaw.ca/{name}/`, with its test data at `/{name}/vectors.json`. Jekyll
builds the page from the file, so the two can't drift.

1. **Breadcrumb**: back to the home page.
2. **Title**: what it computes, in plain words.
3. **Subtitle**: the standard, whose it is, its licence.
4. **Headline**: the number of cases, and the expiry date if there is one.
5. **What it is**: the problem in plain words, for someone who hasn't met it, with a
   diagram where one explains it better than words. LandNav's declination help sheet is
   the model. Diagrams are SVGs in `assets/diagrams/`, drawn for light and dark.
6. **Inputs** and **Outputs**: a unit in every name, and the range each takes.
7. **Accuracy**: each output's tolerance and why.
8. **Edge cases**: the named cases and what's right for each.
9. **For agents**: a short brief to paste into an agent, naming the method and the
   traps. A paragraph, not code.
10. **Implementations**: one row per repo, with its language and whether it passes, fails
    or is incomplete on the current data.
11. **History**: each version of the file and what changed.
12. **Source**: each source by role (standard, test values, reference program), with its
    credit verbatim.

Each planned algorithm has a placeholder page now, with the parts that are known.

## The test file

```json
{
  "algorithm": "wmm",
  "version": 1,
  "publishedAt": "2026-10-01",
  "expiresAt": "2029-12-31",
  "earthModel": "WGS84",
  "sources": [
    { "role": "test values", "name": "WMM2025 test values", "url": "…", "licence": "Public domain" }
  ],
  "tolerances": { "declinationInDegrees": 0.01 },
  "cases": [
    {
      "id": "noaa-1",
      "tags": ["published"],
      "input": { "latitudeInDegrees": 80, "longitudeInDegrees": 0, "heightInKilometers": 0, "decimalYear": 2025.0 },
      "expected": { "declinationInDegrees": 0.0 }
    }
  ]
}
```

The values above are placeholders; #1 fills in real ones. `tags` says where a case came
from (`published`, `reference`, `hand`) and what it tests (`edge`, `polar`). A new version
may add cases, change a tolerance or rename a field. There are no compatibility rules:
implementations are checked against the current file only.

## Implementations

**Each implementation is a public repo that follows one contract, so an automated check
works the same way in every language.** A repo is an implementation; several in one
language are fine.

- `mise install` sets up the language's tools and the checker.
- `mise run evaluate` reads cases as JSON Lines on standard input and writes one result
  per line. The implementation never sees an expected value:

  ```text
  in:  {"algorithm":"wmm","id":"noaa-1","input":{…}}
  out: {"id":"noaa-1","output":{"declinationInDegrees":…}}
  out: {"id":"bad-latitude","error":"outOfRange"}
  out: {"id":"utm-1","error":"notImplemented"}
  ```

- `mise run test` runs the checker against the current test data and prints each case's
  result and error against its tolerance.
- A scheduled CI run, weekly and on every push, publishes the checker's `conformance.json`
  as a release asset.

**The checker does all the judging, and it's the one piece of code this repo owns.** It
feeds the cases, applies the tolerances and writes the results, so no implementation
writes its own comparison or loosens it. It ships as a single binary on this repo's
releases, installed by mise.

**The status per algorithm is Passes, Fails (with a count) or Incomplete**, always
against the current data. New cases can turn an implementation red, and that's the
prompt to fix it.

**Listing an implementation is a pull request here** adding its repo to
`_data/implementations.yml`. The site reads each listed repo's latest `conformance.json`.
The results are self-reported, which is enough while the list is short. Running every
implementation centrally, in containers, waits until someone games it.

Three repos make it work:

| Repo | What |
| --- | --- |
| `gshaw/algorithms` | This one: test data, generators, the site, the checker |
| `gshaw/algorithms-template` | A GitHub template: `.mise.toml`, the CI workflow and the contract. No language in it. |
| `gshaw/algorithms-swift` | Gerry's Swift implementation, made from the template, and the worked example |

The checker, the template and the Swift repo are built with #1, the first algorithm with
real data to build them against.

## Later

In the order the apps will ask. Each waits for an app that needs it.

- Rhumb lines, cross-track error, ETA and velocity made good: MarNav routes and LandNav's
  navigation.
- Resection and intersection, and hiking time (Naismith, Tobler): LandNav.
- Search patterns from the IAMSAR manual.
- Anchor drag against GPS noise: AnchorAlert.
- Encoded polyline and geohash: MarNav.
- Wind chill, humidex, heat index, dew point, and the Beaufort, Douglas sea state, UV
  index and pressure tendency scales.
- Time zones and country borders, as data. No authority publishes either as lines: tzdb
  has the rules, and the lines come from OpenStreetMap under ODbL.
- GPX parsing, as real files with their expected result.

## Open

- **Distance on a sphere or the ellipsoid.** #3 recommends the sphere, matching Turf, so a
  map and its numbers agree.
- **Zone padding in MGRS display**: `04Q` or `4Q`. #2.
- **ODbL**, before any time zone or border data.
