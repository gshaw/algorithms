---
title: Design
description: The colours, statuses and diagram rules every page on this site follows.
layout: page
permalink: /design/
---

One palette for every page and diagram here. It changes rarely, so it lives on a page rather than in each file.

## Levels

For a status that goes from good to bad. Always a dot and a word, never colour alone.

<div class="fields">
  <table>
    <thead><tr><th>Level</th><th>Hex</th><th>Used for</th></tr></thead>
    <tbody>
      <tr><td><span class="swatch" style="background: #1baf7a"></span>OK</td><td><code>#1baf7a</code></td><td>Test data published; an implementation passes</td></tr>
      <tr><td><span class="swatch" style="background: #e0a526"></span>Caution</td><td><code>#e0a526</code></td><td>An implementation is incomplete; test data expires within 90 days</td></tr>
      <tr><td><span class="swatch" style="background: #d64545"></span>Avoid</td><td><code>#d64545</code></td><td>An implementation fails; test data has expired</td></tr>
      <tr><td><span class="swatch" style="background: #9aa5b1"></span>Unknown</td><td><code>#9aa5b1</code></td><td>Planned: no test data yet</td></tr>
    </tbody>
  </table>
</div>

## Series

One colour per item, in this order, for lines and marks that are told apart rather than ranked. Chosen to stay apart for colour-blind readers.

<p>
  <span class="swatch" style="background: #2a78d6"></span><code>#2a78d6</code>&nbsp;
  <span class="swatch" style="background: #eb6834"></span><code>#eb6834</code>&nbsp;
  <span class="swatch" style="background: #1baf7a"></span><code>#1baf7a</code>&nbsp;
  <span class="swatch" style="background: #eda100"></span><code>#eda100</code>&nbsp;
  <span class="swatch" style="background: #e87ba4"></span><code>#e87ba4</code>&nbsp;
  <span class="swatch" style="background: #8a63d2"></span><code>#8a63d2</code>
</p>

## Diagrams

A diagram goes on a page only where it explains something words don't. Every diagram is a hand-written SVG in `assets/diagrams/`, with the same parts and colours, and its own light and dark versions through `prefers-color-scheme`. A page embeds one with `<object>`, not `<img>`: Safari ignores the dark version inside an `<img>`.

<figure class="diagram"><object type="image/svg+xml" data="/assets/diagrams/style-guide.svg" role="img" aria-label="A sample diagram: a muted reference arrow, an ink subject arrow, the angle between them as a pale blue wedge with an accent arc, a sun in the light colour, a dashed guide, and a key of each colour role and line weight">A sample diagram: a muted reference arrow, an ink subject arrow, the angle between them as a pale blue wedge with an accent arc, a sun in the light colour, a dashed guide, and a key of each colour role and line weight</object></figure>

The sample above shows each role in use; the table gives its colours.

<div class="fields">
  <table>
    <thead><tr><th>Role</th><th>Light · dark</th><th>Used for</th></tr></thead>
    <tbody>
      <tr><td>Card</td><td><code>#f6f8fa</code> · <code>#161b22</code></td><td>The background: a card with 12 px corners, so a diagram reads as one on a light page and a dark one</td></tr>
      <tr><td>Ink</td><td><code>#1f2937</code> · <code>#e5e7eb</code></td><td>Labels, and the lines the diagram is about</td></tr>
      <tr><td>Muted</td><td><code>#6b7280</code> · <code>#9aa5b1</code></td><td>References like true north, guides, scales and the caption</td></tr>
      <tr><td>Hairline</td><td><code>#d0d7de</code> · <code>#3a414b</code></td><td>Grids, leader lines, the ground and the moon's dark side</td></tr>
      <tr><td>Accent</td><td><code>#2a78d6</code> · <code>#6aa7ee</code></td><td>The one quantity the diagram explains, and its label</td></tr>
      <tr><td>Accent wash</td><td>Accent at 14% · 20%</td><td>The area of that quantity: an angle's wedge, a square</td></tr>
      <tr><td>Light</td><td><code>#eda100</code></td><td>The sun, and the lit part of the moon</td></tr>
    </tbody>
  </table>
</div>

- **Type:** the system font. Labels at 15 px, notes and the caption at 13 px.
- **Size:** 560 wide, so type comes out the same size on every page.
- **Lines:** 2.5 px for the subject, 1.5 px for arcs that mark an angle, 1 px dashed (3 on, 3 off) for guides. Round ends and joins.
- **Angles** are a wash wedge with an accent arc along its edge, not a bare arc.
- **Labels** sit beside what they name, leading-aligned where they stack. A label that must cross a line gets a halo in the card colour.
- **Caption:** one sentence in muted type along the bottom, saying how to read it or what's exaggerated.
- **Examples say so.** A made-up angle or value is labelled an example, and drawn to scale where it can be.
- **Alt text** says what the diagram shows in a sentence, for readers who can't see it.

## Ink

`#0b0b0b` rings every dot and swatch, so a colour holds on a light page and a dark one. The site's icon has no tile: accent blue rings around an OK green dot, which hold on light and dark tabs. `apple-touch-icon.png` puts it on white, because iOS fills transparency with black.
