---
title: "Astronomical time"
description: "Test data for Julian day, ΔT, sidereal time, and turning a sky position into azimuth and altitude."
layout: "algorithm"
slug: "astronomical-time"
diagram: {"file": "azimuth-altitude.svg", "alt": "An observer at the centre of the horizon, with azimuth measured clockwise from north along the horizon and altitude measured up from it"}
points: ["**Test these first.** When a sunrise is wrong, these cases say whether the fault is underneath.", "**ΔT is measured, not computed**, so its values expire and the file says when.", "**A sidereal day is 23 h 56 min 4 s**, about 4 minutes shorter than a solar day."]
agents: "Follow Meeus, *Astronomical Algorithms*: chapter 7 for the Julian day and back, 12 for mean sidereal time and 13 for the horizontal transform. Use the Julian calendar before 1582-10-15 and the Gregorian from it, with astronomical year numbering, and refuse the ten days that never happened. For `deltaTInSeconds`, embed USNO's observed and predicted table from the file's sources and interpolate between its points. Take the hour angle from local mean sidereal time, treat the UTC given as UT1, and don't add refraction. Pass every case in `vectors.json` within its tolerance."
---

The [sun](/sun/) and [moon](/moon/) both stand on these. A calendar date is awkward to do arithmetic with, so astronomy counts days instead: the **Julian day** is the number of days since noon on 1 January 4713 BC. Clocks keep uniform time, but the Earth's spin wobbles and slows, and **ΔT** is the gap between the two, about 69 seconds now and not predictable far ahead. **Sidereal time** is the Earth's turn measured against the stars, which says which part of the sky is overhead. With it, any position in the sky becomes two angles for a place on the ground.
