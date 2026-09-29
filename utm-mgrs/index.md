---
title: "UTM and MGRS"
description: "Test data for UTM and MGRS grid references, grid convergence and coordinate parsing."
layout: "algorithm"
slug: "utm-mgrs"
diagram: {"file": "mgrs-truncation.svg", "alt": "A point at easting 85234.9 and northing 71665.8 has the reference 85234 71665, the corner of its square, not 85235 71666"}
edge_cases: [["Norway, zone 32V", "Widened west to 3° E, from 56° N to 64° N. `edge-to-utm-norway-32v-west-edge`"], ["Svalbard, 31X to 37X", "Zones 32X, 34X and 36X don't exist; 33X runs from 9° E to 21° E. `edge-to-utm-svalbard-33x-west`"], ["84° N and 80° S", "UPS, `zone` 0, from exactly 84° N, but only beyond 80° S: exactly 80° S is UTM"], ["180°", "The same meridian as −180°, in zone 1. Just west of it is zone 60."], ["The equator", "`hemisphere` north with northing 0; a hair south is northing 9,999,999.99 in the south"], ["A point 0.9 m past a digit", "`toMgrs` truncates: easting 85234.9 is `85234`. `edge-to-mgrs-truncation-5`"], ["fromMgrs", "The centre of the square, not its corner: half a metre in at 5 digits, 50 km at 0"], ["Typed text", "`parse` takes what GeoConvert reads: decimal, DDM, DMS, lettered hemispheres, UTM and MGRS. Two latitudes is `invalidInput`."]]
agents: "Implement the Transverse Mercator projection with the Krüger series to sixth order in n, as in Karney (2011), on WGS84, with a scale of 0.9996 on each zone's central meridian and false easting 500,000 m (and false northing 10,000,000 m in the south). Simpler textbook formulas drift near zone edges and fail the 1 mm tolerance. Beyond it, use Universal Polar Stereographic, `zone` 0, with scale 0.994 at the pole and false easting and northing 2,000,000 m. Apply the Norway and Svalbard zone exceptions. For MGRS, truncate the digits, never round, and read a reference back as the centre of its square. GeographicLib's GeoConvert is the reference: match its choices, including where UPS starts. Pass every case in `vectors.json` within its tolerance."
---

**UTM** splits the world into 60 zones, each 6° of longitude wide, and flattens each onto its own grid in metres: an easting and a northing. **MGRS** is the military form of the same grid. It names the zone, a latitude band and a 100 km square, then gives the easting and northing inside that square, with more digits for more precision.

<div class="fields" markdown="1">

| Part of `10U DU 85234 71665` | Means |
| --- | --- |
| `10` | Zone 10, 126° W to 120° W |
| `U` | Latitude band U, 48° N to 56° N |
| `DU` | The 100 km square |
| `85234 71665` | Easting and northing in that square: five digits each is 1 m |

</div>

**A reference names the south-west corner of the square the point is in.** So each digit is truncated, never rounded. This is the most common mistake in MGRS code.

The test data writes references as GeographicLib does, with no spaces and the zone padded to two digits: `10UDU8523471665`. How to space them for a person is the display's call.
