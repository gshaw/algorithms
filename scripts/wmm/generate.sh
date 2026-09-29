#!/usr/bin/env bash
# Rebuilds wmm/sources/reference-output.txt with NOAA's own WMM2025 C library,
# checks that library against NOAA's published tables, then rebuilds the test file.
# Needs curl, unzip and a C compiler. The NOAA files are pinned by checksum.
set -euo pipefail
cd "$(dirname "$0")/../.."

url=https://www.ngdc.noaa.gov/geomag/WMM/data/WMM2025/wmm2025_Linux.zip
sha=e3a0fb9c9275f72574200456da20c3e7408dd7fa54e48abf3c4a0681b1ed3c2b
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

curl -fsSL -o "$work/noaa.zip" "$url"
echo "$sha  $work/noaa.zip" | shasum -a 256 -c --quiet
unzip -q "$work/noaa.zip" -d "$work"
noaa="$work/wmm2025_Linux"
# The two NOAA copies differ only in the header line's spacing.
cmp -s <(tail -n +2 "$noaa/data/WMM.COF") <(tail -n +2 wmm/sources/WMM.COF) || { echo "NOAA's coefficients differ from wmm/sources/WMM.COF"; exit 1; }

cc -std=c99 -O2 -w -I"$noaa/src" "$noaa"/src/*.c scripts/wmm/reference.c -o "$work/reference" -lm
cd "$noaa/data"
"$work/reference" < "$OLDPWD/scripts/wmm/reference-input.txt" > "$OLDPWD/wmm/sources/reference-output.txt"
python3 "$OLDPWD/scripts/wmm/build.py" --published-inputs | "$work/reference" | python3 "$OLDPWD/scripts/wmm/build.py" --verify
cd "$OLDPWD"
python3 scripts/wmm/build.py
