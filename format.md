---
title: Test data format
description: The shape of every test data file, how its fields are named, how results are compared, and the contract an implementation follows.
layout: page
permalink: /format/
---

Every algorithm's test data is one JSON file in the same shape, with fields named by the same rules. Read this once and every file reads the same way. [algorithms.json](/algorithms.json) lists every file.

## The file

<div class="fields">
  <table>
    <thead><tr><th>Property</th><th>Holds</th></tr></thead>
    <tbody>
      <tr><td><code>algorithm</code></td><td>The algorithm's slug, as in its page's address: <code>wmm</code></td></tr>
      <tr><td><code>placeholder</code></td><td>Only while the values are made up, saying so. Never test against a file that has it.</td></tr>
      <tr><td><code>publishedDate</code></td><td>When this file was last changed</td></tr>
      <tr><td><code>expiresDate</code></td><td>Only when the data behind it runs out, like a magnetic model's last day</td></tr>
      <tr><td><code>earthModel</code></td><td>The earth the numbers are on: <code>WGS84</code>, or a sphere and its radius</td></tr>
      <tr><td><code>sources</code></td><td>Where the values come from: each with <code>role</code>, <code>name</code>, <code>by</code>, <code>url</code> and <code>licence</code></td></tr>
      <tr><td><code>operations</code></td><td>What can be computed: each with an <code>id</code>, what it <code>gives</code>, and the names of its <code>inputs</code> and <code>outputs</code></td></tr>
      <tr><td><code>fields</code></td><td>Every input and output name, with what it means and its range</td></tr>
      <tr><td><code>tolerances</code></td><td>How close each numeric output must be</td></tr>
      <tr><td><code>cases</code></td><td>The tests: each with an <code>id</code>, an <code>operation</code>, <code>tags</code>, an <code>input</code> and what's <code>expected</code></td></tr>
    </tbody>
  </table>
</div>

The file has no version. It changes in place, and an implementation is always checked against the current file.

## Naming

A field's name says what it is and, for a number, its unit. The same name means the same thing in every file.

<div class="fields">
  <table>
    <thead><tr><th>Kind</th><th>Rule</th><th>Like</th></tr></thead>
    <tbody>
      <tr><td>Every name</td><td>lowerCamelCase English words. No abbreviations but established ones.</td><td><code>eastingInMeters</code></td></tr>
      <tr><td>A number with a unit</td><td>Ends in <code>In</code> and the unit, spelled out</td><td><code>distanceInMeters</code>, <code>deltaTInSeconds</code>, <code>precisionInDigits</code></td></tr>
      <tr><td>A number without a unit</td><td>Named for what it is</td><td><code>julianDay</code>, <code>decimalYear</code>, <code>illuminationFraction</code>, <code>pointScale</code></td></tr>
      <tr><td>An instant</td><td>Ends in <code>Utc</code>. ISO 8601 in UTC with a <code>Z</code>, to the second.</td><td><code>riseUtc</code> <code>"2026-06-21T12:04:00Z"</code></td></tr>
      <tr><td>A calendar date</td><td>Is or ends in <code>date</code>. <code>YYYY-MM-DD</code>.</td><td><code>publishedDate</code>, <code>date</code></td></tr>
      <tr><td>Text for a person</td><td>Ends in <code>Text</code></td><td><code>bearingText</code> <code>"000°"</code></td></tr>
      <tr><td>A choice</td><td>A lowerCamelCase word from the list in the field's meaning</td><td><code>hemisphere</code> <code>"north"</code>, <code>phaseName</code> <code>"waxingCrescent"</code></td></tr>
      <tr><td>Yes or no</td><td>Starts with <code>is</code> or <code>has</code></td><td><code>isAlwaysUp</code></td></tr>
      <tr><td>A pair of places or bearings</td><td>Starts with <code>from</code> and <code>to</code></td><td><code>fromLatitudeInDegrees</code></td></tr>
      <tr><td>Angles</td><td>Degrees, except where a field says hours. East and north positive; bearings clockwise from north, 0 to 360.</td><td><code>rightAscensionInHours</code></td></tr>
      <tr><td>Operations</td><td>lowerCamelCase, a verb or the thing given</td><td><code>toMgrs</code>, <code>events</code></td></tr>
      <tr><td>Case ids</td><td>kebab-case, starting with where the case came from</td><td><code>noaa-3</code>, <code>edge-svalbard-33x</code></td></tr>
    </tbody>
  </table>
</div>

`null` means the thing doesn't exist, like a sunrise on a day without one. It never means unknown.

## Comparing

- **Only the fields in `expected` are compared.** An implementation may return more.
- **A number passes when it's within its tolerance**: absolute, in the field's own unit, written as a decimal string. An instant's tolerance is in seconds.
- **Everything else is compared exactly**: text, choices, whole numbers, `true`, `false` and `null`.
- **A tolerance is never loosened to make an implementation pass.** If one is wrong, the file changes.

## Cases

Each case's `tags` say where its values came from and what it tests.

<div class="fields compact">
  <table>
    <thead><tr><th>Tag</th><th>Means</th></tr></thead>
    <tbody>
      <tr><td><code>published</code></td><td>The authority's own published value</td></tr>
      <tr><td><code>reference</code></td><td>Output of the reference program, kept with the file</td></tr>
      <tr><td><code>hand</code></td><td>Worked out from a definition, like a compass point's name</td></tr>
      <tr><td><code>edge</code></td><td>A named edge case</td></tr>
      <tr><td><code>polar</code></td><td>Near a pole</td></tr>
      <tr><td><code>invalid</code></td><td>Input that must be refused</td></tr>
    </tbody>
  </table>
</div>

A case expecting refusal has `"expected": { "error": "outOfRange" }`. The errors are `outOfRange`, for input outside a field's range, and `invalidInput`, for input that can't be read.

## Implementations

An implementation is a public repo that follows one contract, so it can be checked the same way in any language. [algorithms-template](https://github.com/gshaw/algorithms-template) is a GitHub template with the contract already wired up; [algorithms-swift](https://github.com/gshaw/algorithms-swift) is a worked example.

- `mise install` sets up its tools, including the checker, `algorithms-check`, from [this repo's releases](https://github.com/gshaw/algorithms/releases):

  ```toml
  [tools]
  "github:gshaw/algorithms" = { version = "latest", exe = "algorithms-check" }
  ```

- `mise run evaluate` reads cases on standard input, one JSON object per line, and writes one result per line in any order. It never sees `expected`. It runs once per algorithm, and answers `notImplemented` for an algorithm it doesn't have.

  ```text
  in:  {"algorithm":"wmm","id":"noaa-table-1","operation":"field","input":{"latitudeInDegrees":80,…}}
  out: {"id":"noaa-table-1","output":{"magneticDeclinationInDegrees":1.28,…}}
  out: {"id":"invalid-after-2030","error":"outOfRange"}
  out: {"id":"utm-1","error":"notImplemented"}
  ```

- `mise run test` runs `algorithms-check`, which feeds every published file to `mise run evaluate`, prints each case's result and writes `conformance.json`. It skips placeholder files.
- Its CI runs the check weekly and on every push, and commits `conformance.json` to the root of `main`, where this site reads it.

  ```json
  {
    "checker": "0.1.0",
    "source": "https://algorithms.gshaw.ca/algorithms.json",
    "results": {
      "wmm": { "status": "passes", "publishedDate": "2026-09-29", "cases": 135, "passed": 135, "failed": 0, "notImplemented": 0 }
    }
  }
  ```

An algorithm with every case passing **passes**. One with a failing case **fails**. One with any `notImplemented` case is **incomplete**. A result against an older `publishedDate` counts as incomplete until the check runs again.

`algorithms-check -h` lists its options: `-only wmm` checks one algorithm, and `-source` takes a directory of test files for working offline.
