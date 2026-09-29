# Plan

**2026-09-29. Magnetic declination has real test data; the other five are previews.** The first six algorithms are issues
[#1](https://github.com/gshaw/algorithms/issues/1) to
[#6](https://github.com/gshaw/algorithms/issues/6), in that order. Sun and moon were one
algorithm; they split into astronomical time (the foundation both use), sun and moon, so a
failing sunrise says whether the fault is underneath.

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
| SunCalc | LandNav, Tides, MarNav | Astronomical time, sun and moon, #4 to #6 |
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

At `algorithms.gshaw.ca/{name}/`, with its test data at `/{name}/vectors.json`. **Every
algorithm page is the same template**, `_layouts/algorithm.html`, with the same parts in the
same order. A page supplies only its words: the explanation as its body, and its diagram,
points, inputs and outputs (or operations), edge cases and agent brief as front matter. The
test data, implementations, history and sources come from the test file, so the two can't
drift. Colours and diagram rules are on the site's [Styles](https://algorithms.gshaw.ca/styles/) page.

1. **Breadcrumb**: back to the home page.
2. **Title**: what it computes, in plain words.
3. **Subtitle**: the standard, and what the values are checked against.
4. **Headline**: the status, the number of cases, and the expiry date if there is one.
   A page whose test data is a placeholder opens with a warning, drawn like a GitHub alert.
5. **What it is**: the problem in plain words, for someone who hasn't met it, with a
   diagram where one explains it better than words. LandNav's declination help sheet is
   the model. Diagrams follow the [Styles](https://algorithms.gshaw.ca/styles/) page.
6. **Operations** and **Fields**: from the test file, with each operation's id and the
   names of its inputs and outputs, and what each field means.
7. **Edge cases**: the named cases and what's right for each.
8. **For agents**: a short brief to paste into an agent, naming the method and the
   traps. A paragraph, not code.
9. **Test data**: a link to the file, the tolerances, and the cases.
10. **Implementations**: one row per repo, with its language and whether it passes, fails
    or is incomplete on the current data.
11. **Source**: each source by role, with its credit verbatim.

Each planned algorithm has a preview page now, built from a placeholder test file in
`_data/vectors/` that says it's a placeholder, so the finished layout can be reviewed. Each
file is replaced by the real one when its issue lands.

## The test file

**The site's [Test data format](https://algorithms.gshaw.ca/format/) page is the standard**:
the file's shape, how fields are named, how results are compared, and the implementation
contract. `format.md` in this repo is its source; change the standard there, then every
file to match. [algorithms.json](https://algorithms.gshaw.ca/algorithms.json) lists every
file for a program to find.

Each file carries its own `operations` and `fields`, so a page and its file can't disagree,
and a checker can reject a case that uses a field its operation doesn't have.

## Implementations

**Each implementation is a public repo that follows one contract, so an automated check
works the same way in every language.** A repo is an implementation; several in one
language are fine.

The contract (`mise install`, `mise run evaluate` over JSON Lines, `mise run test`, and a
weekly `conformance.json`) is on the [format page](https://algorithms.gshaw.ca/format/#implementations).

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
