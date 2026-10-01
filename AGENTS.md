# Agent Notes

Background for AI agents working in this repo.

## What this is

Test data for pure calculations (sun and moon, magnetic declination, grid references,
bearings) and a Jekyll site at [algorithms.gshaw.ca](https://algorithms.gshaw.ca) that
publishes it and links to implementations that pass it. The design is on the site's home,
`format.md` and `styles.md`; read them before a structural change. Every algorithm,
published, planned or an idea, is listed with a stable ID in
[#26](https://github.com/gshaw/algorithms/issues/26).

**The repo and the site are both public.** Anything committed here is published.

**It stands alone.** Don't link to, load from or mention Gerry's other projects' sites or
services or apps, except gshaw.ca in the footer. The site has its own copy of everything
it serves.

## Rules

- **No implementation code in this repo.** Implementations are separate repos, linked
  from `_data/implementations.yml`. The checker is the one exception: it runs
  implementations, it isn't one.
- **An expected value never comes from a language model**, yours included. It comes from
  an authority's published values or a reference program's output, and the raw source
  is committed beside the test file. If you can't get a value from a source, leave the
  case out and say so.
- **Keep it minimal.** Don't add gems, plugins, pages or build steps unless asked.

## Commands

```sh
mise run install   # bundle install
mise run dev       # serve on :4007 with livereload
mise run check     # build + spell + markdownlint + internal links
mise run deploy    # guard, check, wrangler deploy, verify
mise run verify    # curl the live site
mise run deploy-status  # is main live?
```

**Read the counts, not just the exit code.** html-proofer prints `Ran on N files` and
cspell prints `Files checked: N`. A green run over zero files checked nothing.

## Deploys

A Worker named `algorithms` serves `_site` as static files, with no script
(`wrangler.jsonc`). Nothing deploys on push. **Deploy with `mise run deploy`**, never
`wrangler deploy` by hand: `scripts/deploy-guard.sh` refuses unless the branch is `main`,
the tree is clean and `main` equals `origin/main`. Then it runs `check` (which builds),
deploys tagged with the commit, and runs `verify`. The rule is in
[Workshop's deploy note](https://github.com/gshaw/Workshop/blob/main/Tooling/deploy.md). GitHub Actions runs `mise run -c check` on pushes and PRs.

`Gemfile` and `Gemfile.lock` are identical to Gerry's other Jekyll sites; change them
together.

## Layout

- `_config.yml` holds the site name, description, icon, repo URL and author; the layout
  reads them. Its `exclude` keeps the repo's docs off the site.
- `_layouts/page.html` and `_includes/head.html` are the only layout.
- `_data/algorithms.yml` lists the algorithms in build order, with their slug, status and issue. Each has a page at `/{slug}/index.md`.
- `format.md` is the test data standard: the file's shape, naming, comparing and the implementation contract. Every file in `_data/vectors/` follows it; change the standard there first.
- `/{slug}/vectors.json` is each algorithm's test file, beside its page, published byte for byte. `_data/vectors/{slug}.json` is a symlink to it so `_layouts/algorithm.html` can read it. `scripts/{slug}/` builds it from the raw sources in `/{slug}/sources/`, which the site publishes so anyone can audit a value; `scripts/lib/vectors_json.py` writes it, formatted and ordered. A case's `note` says why it exists, and the page lists the noted cases as its edge cases; edit notes in the generator's `NOTES`, never the JSON. `_data/implementations.yml` lists implementations; `planned: true` until the repo exists. `mise run results` copies each one's `conformance.json` into `_data/conformance/`; commit it, then deploy.
- `_layouts/algorithm.html` is every algorithm page's template. A page's `index.md` holds its explanation as the body, and its diagram, points and agent brief as front matter; operations, fields, edge cases, the test data summary and sources come from the test file; don't add sections in a page, change the template.
- `assets/diagrams/` holds the pages' diagrams: hand-written SVGs that follow the palette and rules on `styles.md`. Add one only where it explains something words don't.
- `assets/css/pico.min.css` is Pico 2.1.1, copied in. `assets/css/site.css` holds the site's own rules; `table.ref` stacks a table below 64rem.
- `checker/` is `algorithms-check`, in Go. `mise run checker` vets and tests it; pushing a `vX.Y.Z` tag releases binaries through `.github/workflows/checker.yml`, and implementations pin a version in mise.
- `icon.svg` is the source of `favicon.192x192.png` and `apple-touch-icon.png`. When it changes, re-render both and bump `?v=` in `_includes/head.html` and `_config.yml`: browsers keep favicons in their own cache.

## Writing

Verdict first, plain words, sentence case, no em dashes. Date anything that can go
stale.

## Branches, issues and PRs

- Branch names are flat and short: `<issue>-<slug>`.
- Issue and PR bodies aren't hard-wrapped.
- Squash-merge only.
