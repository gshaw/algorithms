---
title: "UTM and MGRS"
description: "Test data for UTM and MGRS grid references, grid convergence and coordinate parsing."
layout: "algorithm"
slug: "utm-mgrs"
diagram: {"file": "mgrs-truncation.svg", "alt": "A point at easting 85234.9 and northing 71665.8 has the reference 85234 71665, the corner of its square, not 85235 71666"}
operations: [["To UTM", "Zone, hemisphere, easting, northing, grid convergence and point scale from a latitude and longitude"], ["From UTM", "Latitude and longitude"], ["To MGRS", "A reference at 0 to 5 digits of precision"], ["From MGRS", "The latitude and longitude of the square's centre"], ["Parse", "A typed coordinate in any common form: DD, DDM, DMS, UTM or MGRS"]]
edge_cases: [["Norway, zone 32V", "Widened to 9°, from 3° E to 12° E"], ["Svalbard, 31X to 37X", "Zones 32X, 34X and 36X don't exist"], ["Beyond 84° N and 80° S", "UPS, the polar grid, not UTM"], ["180°", "Zone 60 on one side, zone 1 on the other"], ["1 mm from a grid line", "Left out of the random cases; floating point can put it either side"]]
agents: "Implement the Transverse Mercator projection with the Krüger series to sixth order, as in Karney (2011), on WGS84, with a scale of 0.9996 on each zone's central meridian. Simpler textbook formulas drift near zone edges and fail the tolerances. Apply the Norway and Svalbard zone exceptions, and use UPS beyond 84° N and 80° S. Truncate MGRS digits; never round. Pass every case in `vectors.json` within its tolerance."
---

**UTM** splits the world into 60 zones, each 6° of longitude wide, and flattens each onto its own grid in metres: an easting and a northing. **MGRS** is the military form of the same grid. It names the zone, a latitude band and a 100 km square, then gives the easting and northing inside that square, with more digits for more precision.

<div class="fields" markdown="1">

| Part of `10U DV 85234 71665` | Means |
| --- | --- |
| `10` | Zone 10, 126° W to 120° W |
| `U` | Latitude band U, 48° N to 56° N |
| `DV` | The 100 km square |
| `85234 71665` | Easting and northing in that square: five digits each is 1 m |

</div>

**A reference names the south-west corner of the square the point is in.** So each digit is truncated, never rounded. This is the most common mistake in MGRS code.
