---
title: "Sun"
description: "Test data for sunrise, sunset, twilight and the sun’s position."
layout: "algorithm"
slug: "sun"
diagram: {"file": "twilight.svg", "alt": "Bands below the horizon: civil twilight to 6 degrees, nautical to 12, astronomical to 18, then night"}
points: ["**Some days have no sunrise.** Inside the polar circles the sun can stay up or down all day, and the answer must say so rather than invent a time.", "**Events are asked for in a window of time**, 24 hours from a UTC start, so no time zone is needed.", "**It builds on [astronomical time](/astronomical-time/)**: the Julian day and the conversion to azimuth and altitude."]
edge_cases: [["Alert, Nunavut, in June", "`riseUtc` and `setUtc` null, `isAlwaysUp` true"], ["McMurdo Station in June", "`riseUtc` and `setUtc` null, `isAlwaysDown` true"], ["Twilight that never ends", "In high-latitude summer, `nauticalDuskUtc` and `nauticalDawnUtc` can be null"], ["A window crossing midnight UTC", "Events on both sides"]]
agents: "Follow Meeus, *Astronomical Algorithms*, chapters 25 and 15. Find events in the window from `startUtc` for `windowInHours`, never in a local calendar day. Use −0.833° for rise and set, and −6°, −12° and −18° for twilight. When the sun doesn't cross an altitude in the window, return null for that time, and set `isAlwaysUp` or `isAlwaysDown`. Pass every case in `vectors.json` within its tolerance."
---

**Sunrise and sunset** are when the top of the sun touches the horizon. The air bends its light, so the sun's centre is then 0.833° below it. **Twilight** is the light after sunset and before sunrise, in three steps by how far the sun is below the horizon. Soldiers and sailors plan around them: nautical twilight is when the horizon is still visible.
