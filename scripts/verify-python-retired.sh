#!/usr/bin/env bash
# ============================================================
# verify-python-retired.sh — Phase 4 close invariant guard (Plan 04-20)
#
# Asserts that the active-surface Python build legacy is retired:
#   - scripts/build-wargov.py        — DELETED (Astro owns /)
#   - scripts/build-details.py       — DELETED (per-archive normalisers + Astro)
#   - scripts/sync-nav.py            — DELETED (Nav.astro is sole source)
#   - scripts/sync-footer.py         — DELETED (Footer.astro is sole source)
#   - scripts/parse-aaro.py          — DELETED (Plan 04-17)
#   - scripts/extract-evidence.py    — DELETED (Plan 04-17)
#   - scripts/build-aaro.py          — DELETED (Plan 04-17)
#   - scripts/build-nasa.py          — DELETED (Plan 04-16)
#   - scripts/build-nara.py          — DELETED (Plan 04-15)
#   - scripts/build-{nz,uruguay,argentina,italy,canada,peru,spain}.py — DELETED
#
# DELIBERATELY PRESERVED (whitelist):
#   - scripts/spider.py              — Phase 5 SCRP scope per RESEARCH §10
#   - scripts/build-redirects.py     — quality-gates.yml redirects drift gate
#   - scripts/build-brazil.py        — scrape.yml (Phase 5 SCRP) consumer
#   - scripts/build-chile.py         — scrape.yml (Phase 5 SCRP) consumer
#   - scripts/build-geipan.py        — scrape.yml (Phase 5 SCRP) consumer
#   - scripts/build-uk.py            — scrape.yml (Phase 5 SCRP) consumer
#   - scripts/build-{api,cases,feeds,geo,og,pages-index,stories,sw}.py — scrape.yml
#   - scripts/build_batch3.py        — scrape.yml (Phase 5 SCRP) consumer
#   - scripts/copy-legacy-archives.sh — ships 11 dormant + partial-port sub-pages
#
# Exit 0 if invariant holds; exit 1 if any retired script reappears.
# ============================================================
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

fail=0

# Files that MUST be absent
must_be_absent=(
  scripts/build-wargov.py
  scripts/build-details.py
  scripts/sync-nav.py
  scripts/sync-footer.py
  scripts/parse-aaro.py
  scripts/extract-evidence.py
  scripts/build-aaro.py
  scripts/build-nasa.py
  scripts/build-nara.py
  scripts/build-nz.py
  scripts/build-uruguay.py
  scripts/build-argentina.py
  scripts/build-italy.py
  scripts/build-canada.py
  scripts/build-peru.py
  scripts/build-spain.py
)

for f in "${must_be_absent[@]}"; do
  if [ -e "$f" ]; then
    echo "FAIL: $f reappeared (Plan 04-20 retired this script)" >&2
    fail=1
  fi
done

# sync-* must all be absent
shopt -s nullglob
sync_survivors=(scripts/sync-*.py)
if [ ${#sync_survivors[@]} -gt 0 ]; then
  echo "FAIL: scripts/sync-*.py present — Plan 04-20 retired all of these:" >&2
  printf '  %s\n' "${sync_survivors[@]}" >&2
  fail=1
fi

# parse-* and extract-* must all be absent
parse_survivors=(scripts/parse-*.py)
if [ ${#parse_survivors[@]} -gt 0 ]; then
  echo "FAIL: scripts/parse-*.py present — Plan 04-17 retired all of these:" >&2
  printf '  %s\n' "${parse_survivors[@]}" >&2
  fail=1
fi
extract_survivors=(scripts/extract-*.py)
# Allow extract-fidelity-samples.py + extract-pdf-text.py (utility, NOT extract-evidence)
for f in "${extract_survivors[@]}"; do
  case "$f" in
    scripts/extract-fidelity-samples.py|scripts/extract-pdf-text.py) ;;
    *) echo "FAIL: $f present — only extract-fidelity-samples.py + extract-pdf-text.py are whitelisted" >&2; fail=1 ;;
  esac
done
shopt -u nullglob

# Whitelist guard for spider.py — it MUST exist (Phase 5 SCRP carve-out)
if [ ! -f scripts/spider.py ]; then
  echo "FAIL: scripts/spider.py missing — Phase 5 SCRP scope expects this" >&2
  fail=1
fi

# copy-legacy-archives.sh KEPT — ships dormant + partial-port sub-pages
if [ ! -f scripts/copy-legacy-archives.sh ]; then
  echo "FAIL: scripts/copy-legacy-archives.sh missing — still required to ship 11 dormant archives + partial-port sub-pages" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "" >&2
  echo "verify-python-retired.sh: INVARIANT VIOLATED — see failures above" >&2
  exit 1
fi

echo "verify-python-retired.sh: OK — Python build retirement invariant holds (spider.py + scrape.yml builders + copy-legacy-archives.sh preserved by design)"
exit 0
