---
title: "Bearings"
description: "Test data for distance and bearing, degrees and mils, compass points, and true, magnetic and grid north."
layout: "algorithm"
slug: "bearings"
diagram: {"file": "three-norths.svg", "alt": "True north, grid north 5 degrees east of it, and magnetic north 20 degrees east of true, with grid convergence, the G-M angle and declination marked between them"}
points: ["**Grid convergence** is true to grid. It's zero on a UTM zone's centre line and grows toward the zone's edges and the poles.", "**Declination** is true to magnetic. It comes from the [magnetic model](/wmm/).", "**The G-M angle** is grid to magnetic: declination minus convergence. Military maps print it in the margin."]
edge_cases: [["359.6°", "`bearingText` is `000°`, never `360°`. Round, then wrap. The same for mils: 359.98° is `0000`."], ["A turn across north", "350° to 10° is 20° right, not 340° left"], ["A turn of exactly 180°", "right, by this file's rule"], ["Half-way between compass points", "Goes clockwise: 11.25° with 16 points is NNE"], ["Every sign of declination and convergence", "Each combination has a `convertNorth` case, and FM 3-25.26's six worked examples are cases"], ["The antimeridian", "A path from 179.5° to −179.5° is 110 km east, not most of the way round"], ["The same point, antipodes, a pole", "`inverse` gives the distance; the bearing isn't compared"]]
agents: "Measure on a sphere of radius 6,371,008.8 m, not the ellipsoid, so distances match Turf and the map: use the haversine or spherical law of cosines for distance, and the standard spherical formulas for initial bearing and destination. Normalize longitudes to −180 to 180 and bearings to 0 to 360. In `convertNorth`, true = magnetic + declination and true = grid + convergence, both east positive. In `formatBearing`, round half up first and wrap after, so 359.6° writes as `000°`. For `compassPoint`, use Bowditch's abbreviations, with ties going clockwise. Pass every case in `vectors.json`; text must match exactly."
---

A bearing is only meaningful with its north. A map has three: **true north** along the meridian, **grid north** along the map's grid lines, and **magnetic north** where the compass points. Converting between them means adding or subtracting the angles between them, and the sign of each angle is where code goes wrong.
