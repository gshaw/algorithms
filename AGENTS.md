# Agent Notes

Background for AI agents working in this repo.

## What this is

Test data for pure calculations (sun and moon, magnetic declination, grid references,
bearings) and a Jekyll site at [algorithms.gshaw.ca](https://algorithms.gshaw.ca) that
publishes it and links to implementations that pass it. The design is
[docs/plan.md](docs/plan.md); read it before a structural change.

**The repo and the site are both public.** Anything committed here is published.

**It stands alone.** Don't link to, load from or mention Gerry's other projects' sites or
services, except gshaw.ca in the footer and the apps by name where the plan explains why
an algorithm exists. The site has its own copy of everything it serves.

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
mise run deploy    # check, then wrangler deploy
mise run verify    # curl the live site after a deploy
```

**Read the counts, not just the exit code.** html-proofer prints `Ran on N files` and
cspell prints `Files checked: N`. A green run over zero files checked nothing.

## Deploys

A Worker named `algorithms` serves `_site` as static files, with no script
(`wrangler.jsonc`). `mise run deploy` builds and deploys from a Mac; nothing deploys on
push yet. GitHub Actions runs `mise run -c check` on pushes and PRs.

`Gemfile` and `Gemfile.lock` are identical to Gerry's other Jekyll sites; change them
together.

## Layout

- `_config.yml` holds the site name, description, icon, repo URL and author; the layout
  reads them. Its `exclude` keeps the repo's docs off the site.
- `_layouts/page.html` and `_includes/head.html` are the only layout.
- `_data/algorithms.yml` lists the algorithms in build order, with their slug, status and issue. Each has a page at `/{slug}/index.md`.
- `assets/diagrams/` holds the pages' diagrams: hand-written SVGs with their own light and dark colours. Add one only where it explains something words don't.
- `assets/css/pico.min.css` is Pico 2.1.1, copied in. `assets/css/site.css` holds the site's own rules; `table.ref` stacks a table below 64rem.
- `icon.svg` is the source of `favicon.192x192.png` and `apple-touch-icon.png`.

## Writing

Verdict first, plain words, sentence case, no em dashes. Date anything that can go
stale.

## Branches, issues and PRs

- Branch names are flat and short: `<issue>-<slug>`.
- Issue and PR bodies aren't hard-wrapped.
- Squash-merge only.
