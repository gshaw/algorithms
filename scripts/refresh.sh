#!/usr/bin/env bash
# Puts every implementation's latest results on the site: copies their conformance.json,
# commits straight to main if any changed, and deploys if main isn't live. Safe to run
# again: with nothing new it changes nothing. Implementations re-test themselves on every
# push and daily; this only carries the results here.
set -euo pipefail
cd "$(dirname "$0")/.."

git pull --ff-only --quiet origin main
scripts/deploy-guard.sh
scripts/results.sh
if [[ -n $(git status --porcelain _data/conformance) ]]; then
  git add _data/conformance
  git commit --quiet -m "Implementations' results, from their conformance.json"
  git push --quiet origin main
fi
if scripts/deploy-status.sh | grep -q "is live\.$"; then
  echo "✅ Every implementation's results are already live."
else
  mise run deploy
fi
