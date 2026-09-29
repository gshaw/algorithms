---
title: "Moon"
description: "Test data for moonrise, moonset, the moon’s illumination and phase, and the dates of its phases."
layout: "algorithm"
slug: "moon"
diagram: {"file": "moon-phases.svg", "alt": "Eight moons from new to waning crescent, each with its name and how much of it is lit, over a 29.5-day timeline"}
points: ["**It rises about 50 minutes later each day**, so about once a month a day has no moonrise, and another has no moonset.", "**Waxing is growing, waning is shrinking.** The lit side is on the right while it waxes, seen from the northern hemisphere.", "**It builds on [astronomical time](/astronomical-time/)**, like the [sun](/sun/)."]
agents: "Follow Meeus, *Astronomical Algorithms*: chapter 47 for the moon's position, 48 for illumination and 49 for the phase dates, or search elongation for them. For rise and set, correct for the moon's parallax and semi-diameter: its altitude at rise changes with its distance. Search the window from `startUtc`, never a calendar day, and return the first of each event. Name the phase from the elongation in 45° bands centred on each phase. Pass every case in `vectors.json` within its tolerance."
---

The moon goes around the Earth about every 29.5 days, lit by the sun from a different angle each night. **Illumination** is the fraction of its face that's lit, and the **phase** names where it is in the cycle. It's close enough that where you stand shifts where you see it, so its rise and set need a correction the sun doesn't.
