---
title: "Moon"
description: "Test data for moonrise, moonset, the moon’s illumination and phase, and the dates of its phases."
layout: "algorithm"
slug: "moon"
diagram: {"file": "moon-phases.svg", "alt": "Eight moons from new to waning crescent, each with its name and how much of it is lit"}
points: ["**It rises about 50 minutes later each day**, so about once a month a day has no moonrise, and another has no moonset.", "**Waxing is growing, waning is shrinking.** The lit side is on the right while it waxes, seen from the northern hemisphere.", "**It builds on [astronomical time](/astronomical-time/)**, like the [sun](/sun/)."]
edge_cases: [["A day with no moonrise", "`riseUtc` null, not the next day's"], ["Above the Arctic Circle", "Days when the moon never crosses the horizon: `isAlwaysUp` or `isAlwaysDown`"], ["Exactly at a phase", "`phaseName` is that phase, not its neighbour"]]
agents: "Follow Meeus, *Astronomical Algorithms*: chapter 47 for position, 48 for illumination and 49 for the phase dates. Correct for the moon's parallax and semi-diameter when finding rise and set; its altitude at rise changes with its distance. Find events in the window from `startUtc`. Pass every case in `vectors.json` within its tolerance."
---

The moon goes around the Earth about every 29.5 days, lit by the sun from a different angle each night. **Illumination** is the fraction of its face that's lit, and the **phase** names where it is in the cycle. It's close enough that where you stand shifts where you see it, so its rise and set need a correction the sun doesn't.
