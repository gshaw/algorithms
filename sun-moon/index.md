---
title: Sun and moon
description: Test data for sunrise, sunset, twilight, the sun's and moon's positions, and the moon's phase.
layout: page
---

{% include planned.html slug="sun-moon" %}

## What it is

**Sunrise and sunset** are when the top of the sun touches the horizon. The air bends its light, so the sun's centre is then 0.833° below it. **Twilight** is the light after sunset and before sunrise, in three steps by how far the sun is below the horizon. Soldiers and sailors plan around them: nautical twilight is when the horizon is still visible.

<figure class="diagram"><img src="/assets/diagrams/twilight.svg" alt="Bands below the horizon: civil twilight to 6 degrees, nautical to 12, astronomical to 18, then night"></figure>

- **Some days have no sunrise.** Inside the polar circles the sun can stay up or down all day, and the answer must say so rather than invent a time.
- **The moon has its own rise and set**, about 50 minutes later each day, so about once a month a day has none.
- **Events are asked for in a window of time**, 24 hours from a UTC start, so no time zone is needed.

## Outputs

<div class="fields" markdown="1">

| Output | Meaning |
| --- | --- |
| Sun | Rise, set and transit; the start and end of civil, nautical and astronomical twilight; azimuth and altitude |
| Moon | Rise, set and transit; illumination; phase angle and name; the next new, first quarter, full and last quarter |
| Julian day | Both ways, the base for everything above |

</div>

## Edge cases

<div class="fields" markdown="1">

| Case | What's right |
| --- | --- |
| Alert, Nunavut, in June | No sunset |
| McMurdo Station in June | No sunrise |
| A day with no moonrise | None, not the next day's |
| A window crossing midnight UTC | Events on both sides |

</div>

{% include implementations.html %}

## Source

<div class="fields" markdown="1">

| Role | Source |
| --- | --- |
| Method | Meeus, *Astronomical Algorithms*, 2nd edition, 1998 |
| Reference | The US Naval Observatory's Astronomical Applications API. Public domain. |

</div>
