---
title: "UTM and MGRS"
description: "Test data for UTM and MGRS grid references, grid convergence and coordinate parsing."
layout: "algorithm"
slug: "utm-mgrs"
diagram: {"file": "mgrs-truncation.svg", "alt": "A point at easting 85234.9 and northing 71665.8 has the reference 85234 71665, the corner of its square, not 85235 71666"}
agents: "Implement the Transverse Mercator projection with the Krüger series to sixth order in n, as in Karney (2011), on WGS84, with a scale of 0.9996 on each zone's central meridian and false easting 500,000 m (and false northing 10,000,000 m in the south). Simpler textbook formulas drift near zone edges and fail the 1 mm tolerance. Beyond it, use Universal Polar Stereographic, `zone` 0, with scale 0.994 at the pole and false easting and northing 2,000,000 m. Apply the Norway and Svalbard zone exceptions. For MGRS, truncate the digits, never round, and read a reference back as the centre of its square. When parsing UTM, read the letter after the zone as GPS units write it, a latitude band, not only as GeoConvert does, a hemisphere: a band other than N must contain the point, give or take 0.01°, and S is band S when the point falls in 32° N to 40° N, otherwise the southern hemisphere. GeographicLib's GeoConvert is the reference: match its choices, including where UPS starts. Pass every case in `vectors.json` within its tolerance."
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

**A UTM letter can be a band or a hemisphere.** GPS units write `10S 585822 4132180`, meaning band S, 32° N to 40° N. GeoConvert reads the same text as the southern hemisphere, 52.95° S. The test data reads it as a band when the point falls in band S, and as south otherwise.
