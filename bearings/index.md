---
title: "Bearings"
description: "Test data for distance and bearing, degrees and mils, compass points, and true, magnetic and grid north."
layout: "algorithm"
slug: "bearings"
diagram: {"file": "three-norths.svg", "alt": "True north, grid north 5 degrees east of it, and magnetic north 20 degrees east of true, with grid convergence, the G-M angle and declination marked between them"}
points: ["**Grid convergence** is true to grid. It's zero on a UTM zone's centre line and grows toward the zone's edges and the poles.", "**Declination** is true to magnetic. It comes from the [magnetic model](/wmm/).", "**The G-M angle** is grid to magnetic: declination minus convergence. Military maps print it in the margin."]
edge_cases: [["359.6°", "`bearingText` is `000°`, never `360°`. The same for mils."], ["A turn across north", "350° to 10° is 20° right, not 340° left"], ["Every sign of declination and convergence", "Each combination has a `convertNorth` case"]]
agents: "Measure on a sphere of radius 6,371,008.8 m, not the ellipsoid, so distances match Turf and the map; this is proposed in issue #3. Normalize every bearing into [0°, 360°) after rounding, not before, so 359.6° writes as `000°`. In `convertNorth`, take `magneticDeclinationInDegrees` and `convergenceInDegrees` east positive, with true = magnetic + declination and grid = true − convergence. Pass every case in `vectors.json`; text must match exactly."
---

A bearing is only meaningful with its north. A map has three: **true north** along the meridian, **grid north** along the map's grid lines, and **magnetic north** where the compass points. Converting between them means adding or subtracting the angles between them, and the sign of each angle is where code goes wrong.
