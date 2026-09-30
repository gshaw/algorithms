# Algorithms

Test data for the calculations an app does on the device, checked against each
authority's own published values. Live at [algorithms.gshaw.ca](https://algorithms.gshaw.ca).

There's no implementation code here. Implementations live in their own repos and are
linked from the site. The list of algorithms, published, planned and ideas, is
[#26](https://github.com/gshaw/algorithms/issues/26).

## How it fits together

The design is on the site: [how it works](https://algorithms.gshaw.ca/), the
[test data format](https://algorithms.gshaw.ca/format/) and the
[styles](https://algorithms.gshaw.ca/styles/). Three repos make it work:

| Repo | What |
| --- | --- |
| `gshaw/algorithms` | This one: test data, generators, the site, the checker |
| [`gshaw/algorithms-template`](https://github.com/gshaw/algorithms-template) | A GitHub template: `.mise.toml`, the CI workflow and the contract. No language in it. |
| [`gshaw/algorithms-swift`](https://github.com/gshaw/algorithms-swift) | The Swift implementation, made from the template, and the worked example |

A new algorithm gets its own issue and starts as a preview page built from a test file
with a `placeholder` property, so the layout can be reviewed before the data lands. The
real file replaces it when the issue lands.

## Develop

```sh
mise install       # Ruby, Node, cspell, markdownlint, html-proofer, wrangler
mise run install   # bundle install
mise run dev       # http://localhost:4007 with livereload
mise run check     # build, spell check, markdown lint, internal links
mise run deploy    # guard, check, deploy the Worker, verify
mise run verify    # check the live site
mise run deploy-status  # is main live?
```

Deploy with `mise run deploy`. It refuses unless you're on a clean `main` that matches GitHub's, then checks, deploys and runs `mise run verify`. Nothing else ships to production. The rule is in [Workshop's deploy note](https://github.com/gshaw/Workshop/blob/main/Tooling/deploy.md).

## Licence

The test data is [CC0](LICENSE-DATA). The site and tools are [MIT](LICENSE).

## Powered by

- DNS and hosting: [Cloudflare](https://www.cloudflare.com), a Worker serving static files
- Build system: [Jekyll](https://jekyllrb.com)
- CSS: [Pico.css](https://picocss.com)
