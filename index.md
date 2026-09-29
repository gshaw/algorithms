---
title: Algorithms
subtitle: Test data for the calculations an app does on the device, checked against each authority's own published values.
layout: page
---

Sunrise, magnetic declination, grid references and bearings are pure functions: the same input always gives the same answer. So the best way to know an implementation is right is a thorough set of test cases from an authority. This site publishes those cases, and the rules for reading them. It has no code. It links to implementations and says whether each passes.

## Test data

<table class="ref">
  <thead>
    <tr>
      <th>Algorithm</th>
      <th>Gives</th>
      <th>Standard</th>
      <th>Checked against</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    {% for algorithm in site.data.algorithms %}
    <tr>
      <td><a href="/{{ algorithm.slug }}/">{{ algorithm.name }}</a></td>
      <td>{{ algorithm.gives }}</td>
      <td data-label="Standard">{{ algorithm.standard }}</td>
      <td data-label="Checked against">{{ algorithm.checked_against }}</td>
      <td data-label="Status" class="status">{% include status.html status=algorithm.status %}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>

## How it works

- **Every expected value comes from outside.** An authority's published values, such as NOAA's for the magnetic model, or a trusted reference program run for the purpose, such as GeographicLib. Never a guess by a person or a language model.
- **Each algorithm has one file of test cases**, with a tolerance for each output and every edge case named: polar night, the Svalbard grid zones, a bearing of 359.6° written as 000°.
- **An implementation is right when it passes the file.** How it was written doesn't matter. Many will be written by agents from the page.
- **Every file follows one [format](/format/)**: the same shape, the same naming rules and the same way of comparing. [algorithms.json](/algorithms.json) lists every file.

## Implementations

Each is a public repo anyone can fork. `mise install` sets up its tools and `mise run test` checks it against the current test data, the same way in every language; the [format](/format/#implementations) has the contract. Each listed implementation shows, for every algorithm, whether it passes, fails or is incomplete. New test cases can turn an implementation red; that's the prompt to fix it.

<div class="fields compact">
  <table>
    <thead><tr><th>Repo</th><th>Status</th></tr></thead>
    <tbody>
      {%- for implementation in site.data.implementations %}
      {%- assign passing = 0 %}
      {%- assign failing = 0 %}
      {%- for algorithm in site.data.algorithms %}{% include result.html implementation=implementation slug=algorithm.slug %}{% if result_status == "passes" %}{% assign passing = passing | plus: 1 %}{% elsif result_status == "fails" %}{% assign failing = failing | plus: 1 %}{% endif %}{% endfor %}
      {%- if failing > 0 %}{% assign overall = "fails" %}{% elsif passing == site.data.algorithms.size %}{% assign overall = "passes" %}{% else %}{% assign overall = "incomplete" %}{% endif %}
      <tr><td>{% if implementation.planned %}{{ implementation.repo }}{% else %}<a href="https://github.com/{{ implementation.repo }}">{{ implementation.repo }}</a>{% endif %}<small>{{ implementation.language }}</small></td><td class="status">{% include status.html status=overall %} · {{ passing }} of {{ site.data.algorithms.size }} pass</td></tr>
      {%- endfor %}
    </tbody>
  </table>
</div>

## Licence

The test data is [CC0](https://creativecommons.org/publicdomain/zero/1.0/): copy it into any project with no strings. The site and its tools are MIT. Each source's own terms are listed with its data.
