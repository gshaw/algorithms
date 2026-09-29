---
title: Algorithms
subtitle: Test data for the calculations an app does on the device, checked against each authority's own published values.
layout: page
---

Sunrise, magnetic declination, grid references and bearings are pure functions: the same input always gives the same answer. So the best way to know an implementation is right is a thorough set of test cases from an authority. This site publishes those cases. It has no code. It links to implementations that pass.

## Algorithms

<table>
  <thead>
    <tr>
      <th>Algorithm</th>
      <th>Gives</th>
      <th>Standard</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    {% for algorithm in site.data.algorithms %}
    <tr>
      <td>{{ algorithm.name }}</td>
      <td>{{ algorithm.gives }}</td>
      <td>{{ algorithm.standard }}<small>{{ algorithm.authority }}</small></td>
      <td>{% if algorithm.status == "planned" %}<a href="{{ site.repo }}/issues/{{ algorithm.issue }}">Planned</a>{% endif %}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>

## How it works

- **Every expected value comes from outside.** An authority's published values, such as NOAA's for the magnetic model, or a trusted reference program run for the purpose, such as GeographicLib. Never a guess by a person or a language model.
- **Each algorithm has one file of test cases**, with a tolerance for each output and every edge case named: polar night, the Svalbard grid zones, a bearing of 359.6° written as 000°.
- **An implementation is right when it passes the file.** How it was written doesn't matter. Many will be written by agents from the page.

## Implementations

None yet. Each will be a public repo anyone can fork. `mise install` sets up its tools and `mise run test` checks it against the current test data, the same way in every language. Each listed implementation shows, for every algorithm, whether it passes, fails or is incomplete. New test cases can turn an implementation red; that's the prompt to fix it.

The first is in Swift, with the magnetic declination data.

## Licence

The test data is [CC0](https://creativecommons.org/publicdomain/zero/1.0/): copy it into any project with no strings. The site and its tools are MIT. Each source's own terms are listed with its data.
