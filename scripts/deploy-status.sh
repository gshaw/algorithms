#!/usr/bin/env bash
# Says whether main has commits that aren't live, from the commit that
# `mise run deploy` tags each Worker version with. The lookup is almanac's
# scripts/deploy.sh. See Workshop's Tooling/deploy.md.
set -euo pipefail

git fetch --quiet origin main
version=$(wrangler deployments status --json | node -e '
  const d = JSON.parse(require("fs").readFileSync(0, "utf8"));
  console.log(d.versions.sort((a, b) => b.percentage - a.percentage)[0].version_id);
')
live=$(wrangler versions view "$version" --json | node -e '
  const v = JSON.parse(require("fs").readFileSync(0, "utf8"));
  console.log(v.annotations["workers/tag"] ?? "");
')
main=$(git rev-parse origin/main | cut -c1-12)

if [[ -z $live ]]; then
  echo "The live version has no commit tag, so what's live is unknown. Deploy once to fix that."
elif [[ $live == "$main" ]]; then
  echo "origin/main ($main) is live."
else
  echo "main has $(git rev-list --count "$live..origin/main") commits that aren't live. $live is live."
fi
