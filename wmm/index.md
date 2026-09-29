---
title: "Magnetic declination"
description: "Test data for magnetic declination from the World Magnetic Model 2025."
layout: "algorithm"
slug: "wmm"
diagram: {"file": "declination.svg", "alt": "True north straight up, magnetic north 15 degrees to its right, the angle between them labelled declination 15° E"}
points: ["**East is positive.** Declination is east when the needle points east of true north, as it does across most of western North America.", "**To turn a compass bearing into a true bearing, add the declination.** With 15° E, a compass reading of 100° is 115° true.", "**It changes with place and over time.** The field drifts, so the model is replaced every five years. WMM2025 is good from 2025 to the end of 2029.", "**Near the magnetic poles a compass is unreliable.** The field's horizontal part is too weak to steer a needle. The model flags these areas."]
agents: "Implement WMM2025 from `WMM.COF` (in [sources](/wmm/sources/WMM.COF)) as the spherical harmonic expansion to degree 12 in the report's notation. Advance the coefficients linearly from 2025.0 with their secular variation. Convert geodetic latitude and height to geocentric before the expansion, and rotate the result back after. At a geographic pole, where the usual formulas divide by zero, use the report's special case. The report's Table 3 gives every intermediate value for one point, which finds most bugs. Take `decimalYear` as the year plus (day of year − 1) over the days in that year. `gridVariationInDegrees` is declination minus longitude from 55° N and plus longitude from 55° S, wrapped to −180 to 180, and `null` between. `blackout` comes from the horizontal intensity. Pass every case in `vectors.json` within its tolerance; never loosen a tolerance to pass."
---

A compass doesn't point to true north. **True north** is fixed: along a meridian to the North Pole, the north on a map. **Magnetic north** is where a compass needle points, lined up with the Earth's magnetic field. Almost everywhere the two differ, and the angle between them is **magnetic declination**.
