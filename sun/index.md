---
title: "Sun"
description: "Test data for sunrise, sunset, twilight and the sun’s position."
layout: "algorithm"
slug: "sun"
diagram: {"file": "twilight.svg", "alt": "Bands below the horizon: civil twilight to 6 degrees, nautical to 12, astronomical to 18, then night"}
points: ["**Some days have no sunrise.** Inside the polar circles the sun can stay up or down all day, and the answer must say so rather than invent a time.", "**Events are asked for in a window of time**, 24 hours from a UTC start, so no time zone is needed.", "**It builds on [astronomical time](/astronomical-time/)**: the Julian day and the conversion to azimuth and altitude."]
edge_cases: [["Alert, Nunavut, in June", "`riseUtc` and `setUtc` null, `isAlwaysUp` true, and a transit"], ["McMurdo Station in June", "`riseUtc` and `setUtc` null, `isAlwaysDown` true, but nautical and astronomical twilight still come and go"], ["Twilight that never ends", "In high-latitude summer, `nauticalDuskUtc` and `nauticalDawnUtc` are null"], ["A window crossing midnight UTC", "Vancouver's UTC day has a set before its rise"], ["A window from local midnight", "Starting 08:00Z for Vancouver, or across the date line for Suva and Tonga"], ["An event grazing a level, or a minute from the window's edge", "Left out: in or out depends on rounding"]]
agents: "Follow Meeus, *Astronomical Algorithms*: chapter 25 for the sun's apparent right ascension and declination, and 15 for rise, set and transit, or search the altitude through the window. Find events in the window from `startUtc` for `windowInHours`, never in a local calendar day, and return the first of each. Use −0.833° for rise and set and −6°, −12° and −18° for twilight, all geometric. When the sun doesn't cross a level in the window, return null for it, and set `isAlwaysUp` or `isAlwaysDown`. Pass every case in `vectors.json` within its tolerance."
---

**Sunrise and sunset** are when the top of the sun touches the horizon. The air bends its light, so the sun's centre is then 0.833° below it. **Twilight** is the light after sunset and before sunrise, in three steps by how far the sun is below the horizon. Soldiers and sailors plan around them: nautical twilight is when the horizon is still visible.
