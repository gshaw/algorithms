---
title: "Magnetic declination"
description: "Test data for magnetic declination from the World Magnetic Model 2025."
layout: "algorithm"
slug: "wmm"
diagram: {"file": "declination.svg", "alt": "True north straight up, magnetic north 15 degrees to its right, the angle between them labelled declination 15° E"}
points: ["**East is positive.** Declination is east when the needle points east of true north, as it does across most of western North America.", "**To turn a compass bearing into a true bearing, add the declination.** With 15° E, a compass reading of 100° is 115° true.", "**It changes with place and over time.** The field drifts, so the model is replaced every five years. WMM2025 is good from 2025 to the end of 2029.", "**Near the magnetic poles a compass is unreliable.** The field's horizontal part is too weak to steer a needle. The model flags these areas."]
edge_cases: [["Near the north magnetic pole", "`blackout: unreliable`, with `magneticDeclinationInDegrees` still given"], ["The geographic poles", "Longitude is undefined; the answer must still be a number"], ["29 February 2028", "Its `decimalYear` counts the leap day"], ["After 2029-12-31", "Still computed; the page shows the file has expired"]]
agents: "Implement WMM2025 from its coefficient file, as the spherical harmonic expansion to degree 12 in the NOAA report's notation. Convert geodetic input to geocentric before the expansion, and back after. Return `magneticDeclinationInDegrees` east positive, `gridVariationInDegrees` only above 55° N and below 55° S (null elsewhere), and `blackout` from `horizontalIntensityInNanoteslas`. Pass every case in `vectors.json` within its tolerance; never loosen a tolerance to pass."
---

A compass doesn't point to true north. **True north** is fixed: along a meridian to the North Pole, the north on a map. **Magnetic north** is where a compass needle points, lined up with the Earth's magnetic field. Almost everywhere the two differ, and the angle between them is **magnetic declination**.
