---
title: "Moon"
description: "Test data for moonrise, moonset, where the moon is in the sky, its illumination and phase, and the dates of its phases."
layout: "algorithm"
slug: "moon"
diagram: {"file": "moon-phases.svg", "alt": "Eight moons from new to waning crescent, each with its name and how much of it is lit, over a 29.5-day timeline"}
points: ["**It rises about 50 minutes later each day**, so about once a month a day has no moonrise, and another has no moonset.", "**Waxing is growing, waning is shrinking.** The lit side is on the right while it waxes, seen from the northern hemisphere.", "**It builds on [astronomical time](/astronomical-time/)**, like the [sun](/sun/)."]
agents: "Follow Meeus, *Astronomical Algorithms*: chapter 47 for the moon's position, 48 for illumination and 49 for the phase dates, or search elongation for them. For rise and set, correct for the moon's parallax and semi-diameter: its altitude at rise changes with its distance. Search the window from `startUtc`, never a calendar day, and return the first of each event. Return the elongation, the moon's apparent ecliptic longitude minus the sun's, and name the phase from it in 45° bands centred on each phase. For `position`, give azimuth and altitude seen from the place, not the Earth's centre: correct for parallax, up to about 1°, and don't add refraction. Pass every case in `vectors.json` within its tolerance.\n\nTo check by hand against the book, 2nd edition (1998): example 47.a (p. 342) for position, 48.a (p. 347) for illumination, and 49.a and 49.b (p. 353) for phase dates. All four work in dynamical time, so subtract ΔT before comparing with a UTC case. The 1st edition (1991) numbers these chapters 45 to 47 and prints different values for the moon."
---

The moon goes around the Earth about every 29.5 days, lit by the sun from a different angle each night. **Illumination** is the fraction of its face that's lit, and the **phase** names where it is in the cycle. It's close enough that where you stand shifts where you see it, so its rise and set need a correction the sun doesn't.
