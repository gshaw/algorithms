---
title: "Sun"
description: "Test data for sunrise, sunset, twilight and the sun’s position."
layout: "algorithm"
slug: "sun"
diagram: {"file": "twilight.svg", "alt": "Bands below the horizon: civil twilight to 6 degrees, nautical to 12, astronomical to 18, then night"}
points: ["**Some days have no sunrise.** Inside the polar circles the sun can stay up or down all day, and the answer must say so rather than invent a time.", "**Events are asked for in a window of time**, 24 hours from a UTC start, so no time zone is needed.", "**It builds on [astronomical time](/astronomical-time/)**: the Julian day and the conversion to azimuth and altitude."]
agents: "Follow Meeus, *Astronomical Algorithms*: chapter 25 for the sun's apparent right ascension and declination, and 15 for rise, set and transit, or search the altitude through the window. Find events in the window from `startUtc` for `windowInHours`, never in a local calendar day, and return the first of each. Use −0.833° for rise and set and −6°, −12° and −18° for twilight, all geometric. When the sun doesn't cross a level in the window, return null for it, and set `isAlwaysUp` or `isAlwaysDown`. Pass every case in `vectors.json` within its tolerance.\n\nTo check by hand against the book, 2nd edition (1998): example 25.a (p. 165) for the sun's position. It works in dynamical time and gives right ascension and declination with no observer, so it checks a step, not a case in this file. Example 15.a (p. 103) is Venus, at −0.5667°, not the sun: it checks the rise and set method only."
---

**Sunrise and sunset** are when the top of the sun touches the horizon. The air bends its light, so the sun's centre is then 0.833° below it. **Twilight** is the light after sunset and before sunrise, in three steps by how far the sun is below the horizon. Soldiers and sailors plan around them: nautical twilight is when the horizon is still visible.
