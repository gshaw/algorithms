---
title: "Astronomical time"
description: "Test data for Julian day, ΔT, sidereal time, and turning a sky position into azimuth and altitude."
layout: "algorithm"
slug: "astronomical-time"
diagram: {"file": "azimuth-altitude.svg", "alt": "An observer at the centre of the horizon, with azimuth measured clockwise from north along the horizon and altitude measured up from it"}
points: ["**Test these first.** When a sunrise is wrong, these cases say whether the fault is underneath.", "**ΔT is measured, not computed**, so its values expire and the file says when.", "**A sidereal day is 23 h 56 min 4 s**, about 4 minutes shorter than a solar day."]
operations: [["Julian day", "A UTC instant to a Julian day, and back to a date"], ["ΔT", "The seconds between uniform time and the Earth's rotation, for a date"], ["Sidereal time", "Greenwich and local mean sidereal time for an instant"], ["Horizontal position", "Right ascension and declination to azimuth and altitude for a place and instant"]]
edge_cases: [["2000-01-01 12:00 TT", "Julian day 2451545.0, the standard epoch"], ["1582-10-04 to 1582-10-15", "The Gregorian calendar starts; the ten days between never happened"], ["Dates before year 1", "Astronomical years: 1 BC is year 0"], ["A position below the horizon", "A negative altitude, not an error"]]
agents: "Follow Meeus, *Astronomical Algorithms*: chapter 7 for the Julian day, 12 for sidereal time and 13 for coordinate transforms. Use the Gregorian calendar from 1582-10-15 and the Julian before it, with astronomical year numbering. Take ΔT from the file's table and interpolate between its entries. Pass every case in `vectors.json` within its tolerance."
---

The [sun](/sun/) and [moon](/moon/) both stand on these. A calendar date is awkward to do arithmetic with, so astronomy counts days instead: the **Julian day** is the number of days since noon on 1 January 4713 BC. Clocks keep uniform time, but the Earth's spin wobbles and slows, and **ΔT** is the gap between the two, about 69 seconds now and not predictable far ahead. **Sidereal time** is the Earth's turn measured against the stars, which says which part of the sky is overhead. With it, any position in the sky becomes two angles for a place on the ground.
