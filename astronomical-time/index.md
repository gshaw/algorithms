---
title: "Astronomical time"
description: "Test data for Julian day, ΔT, sidereal time, and turning a sky position into azimuth and altitude."
layout: "algorithm"
slug: "astronomical-time"
diagram: {"file": "azimuth-altitude.svg", "alt": "An observer at the centre of the horizon, with azimuth measured clockwise from north along the horizon and altitude measured up from it"}
points: ["**Test these first.** When a sunrise is wrong, these cases say whether the fault is underneath.", "**ΔT is measured, not computed**, so its values expire and the file says when.", "**A sidereal day is 23 h 56 min 4 s**, about 4 minutes shorter than a solar day."]
edge_cases: [["2000-01-01T12:00:00Z", "`julianDay` 2451545.0, the J2000 epoch"], ["1582-10-04 to 1582-10-15", "The Gregorian calendar starts; the ten days between never happened"], ["Dates before year 1", "Astronomical years: 1 BC is year 0"], ["A position below the horizon", "A negative `altitudeInDegrees`, not an error"]]
agents: "Follow Meeus, *Astronomical Algorithms*: chapter 7 for the Julian day, 12 for sidereal time and 13 for coordinate transforms. Use the Gregorian calendar from 1582-10-15 and the Julian before it, with astronomical year numbering. Interpolate `deltaTInSeconds` from the IERS values the file is built from. Pass every case in `vectors.json` within its tolerance."
---

The [sun](/sun/) and [moon](/moon/) both stand on these. A calendar date is awkward to do arithmetic with, so astronomy counts days instead: the **Julian day** is the number of days since noon on 1 January 4713 BC. Clocks keep uniform time, but the Earth's spin wobbles and slows, and **ΔT** is the gap between the two, about 69 seconds now and not predictable far ahead. **Sidereal time** is the Earth's turn measured against the stars, which says which part of the sky is overhead. With it, any position in the sky becomes two angles for a place on the ground.
