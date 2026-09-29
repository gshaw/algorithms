# Algorithms

Test data for the calculations an app does on the device, checked against each
authority's own published values. Live at [algorithms.gshaw.ca](https://algorithms.gshaw.ca).

There's no implementation code here. Implementations live in their own repos and are
linked from the site. The design and what's next are in [docs/plan.md](docs/plan.md).

## Develop

```sh
mise install       # Ruby, Node, cspell, markdownlint, html-proofer, wrangler
mise run install   # bundle install
mise run dev       # http://localhost:4007 with livereload
mise run check     # build, spell check, markdown lint, internal links
mise run deploy    # check, then deploy the Worker
mise run verify    # check the live site
```

## Licence

The test data is [CC0](LICENSE-DATA). The site and tools are [MIT](LICENSE).

## Powered by

- DNS and hosting: [Cloudflare](https://www.cloudflare.com), a Worker serving static files
- Build system: [Jekyll](https://jekyllrb.com)
- CSS: [Pico.css](https://picocss.com)
