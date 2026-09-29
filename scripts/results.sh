#!/usr/bin/env bash
# Copies each listed implementation's conformance.json into _data/conformance/, where
# the pages read it. Commit what changes; the site has no fetch at build time.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p _data/conformance
ruby -r yaml -e 'YAML.load_file("_data/implementations.yml").each { |i| puts i["repo"] unless i["planned"] }' |
  while read -r repo; do
    file="_data/conformance/${repo//\//-}.json"
    if curl -fsSL "https://raw.githubusercontent.com/$repo/main/conformance.json" -o "$file.tmp"; then
      mv "$file.tmp" "$file"
      echo "$repo: $(ruby -r json -e 'puts JSON.parse(File.read(ARGV[0]))["results"].map { |k, v| "#{k} #{v["status"]}" }.join(", ")' "$file")"
    else
      rm -f "$file.tmp"
      echo "$repo: no conformance.json yet"
    fi
  done
