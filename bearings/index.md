---
title: Bearings
description: Test data for distance and bearing, degrees and mils, compass points, and true, magnetic and grid north.
layout: algorithm
slug: bearings
---

## What it is

A bearing is only meaningful with its north. A map has three: **true north** along the meridian, **grid north** along the map's grid lines, and **magnetic north** where the compass points. Converting between them means adding or subtracting the angles between them, and the sign of each angle is where code goes wrong.

<figure class="diagram"><img src="/assets/diagrams/three-norths.svg" alt="True north, grid north 5 degrees east of it, and magnetic north 20 degrees east of true, with grid convergence, the G-M angle and declination marked between them"></figure>

- **Grid convergence** is true to grid. It's zero on a UTM zone's centre line and grows toward the zone's edges and the poles.
- **Declination** is true to magnetic. It comes from the [magnetic model](/wmm/).
- **The G-M angle** is grid to magnetic: declination minus convergence. Military maps print it in the margin.

## Operations

<div class="fields" markdown="1">

| Operation | Gives |
| --- | --- |
| Distance and bearing | Between two points, and the point at a distance and bearing from another |
| Back azimuth and turns | The reverse bearing, and the shortest turn between two headings with its direction |
| True, magnetic and grid | A bearing converted between the three norths |
| Writing a bearing | Degrees as `000°` to `359°`, and mils in NATO's 6400, the Warsaw Pact's 6000 and Sweden's 6300 |
| Compass points | 4, 8, 16 and 32 points, abbreviated (`NNE`, `NbE`) and in words ("north by east") |

</div>

## Edge cases

<div class="fields" markdown="1">

| Case | What's right |
| --- | --- |
| 359.6° | Written `000°`, never `360°`. The same for mils. |
| A turn across north | 350° to 10° is 20° right, not 340° left |
| Every sign of declination and convergence | Each combination has a case |

</div>

## For agents

Measure on a sphere of radius 6,371,008.8 m, not the ellipsoid, so distances match Turf and the map. Normalize every bearing into [0°, 360°) after rounding, not before, so 359.6° writes as `000°`. Take declination and convergence as signed inputs, east positive, and convert as true = magnetic + declination and grid = true − convergence. Pass every case in `vectors.json`; text must match exactly.
