#!/usr/bin/env bash
# ============================================================
# CF Pages _redirects verification harness — Phase 2 INF-02
#
# Iterates every canonical route in URL-CONTRACT.txt and asserts
# the CF Pages preview origin returns the status code that
# build-redirects.py promised (200 for canonical paths; 301 for
# unslashed-form redirects to canonical, opt-in via --strict).
#
# Catches research/PITFALLS.md §Pitfall #8 (CF Pages silently
# drops _redirects rules when it disagrees with the parser).
# build-redirects.py's drift gate catches structural changes
# against URL-CONTRACT.txt; this harness catches CF Pages
# disagreeing with the file we shipped.
#
# Usage:
#   scripts/verify-redirects.sh https://<sha>.realufo.pages.dev
#   scripts/verify-redirects.sh https://realufo.pages.dev --strict
#
# Exit codes:
#   0 — every probed route returned the expected status
#   1 — at least one route returned an unexpected status
#   2 — usage error (missing preview URL)
#
# Output style follows codebase/CONVENTIONS.md §"Shell Conventions":
#   [ok]    https://… → 200
#   [FAIL]  https://… → got 404, expected 200
# ============================================================
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
URL_CONTRACT="$ROOT/URL-CONTRACT.txt"
UA="realufo-redirects-gate/1.0"

# CI early-bail. If CF Pages dropped a whole archive (Pitfall #8)
# we don't need to print 100s of [FAIL] lines — first 10 + summary
# is enough for the operator to start diagnosing.
MAX_FAILS=10

usage() {
  cat >&2 <<EOF
usage: $0 <preview-url> [--strict]

  preview-url   Required. The CF Pages preview origin, e.g.
                https://abc1234.realufo.pages.dev or
                https://realufo.pages.dev (production-branch URL).

  --strict      Additionally probe trailing-slash 301 leg for every
                directory route (e.g. /aaro should 301 -> /aaro/).
                Default (lenient) only asserts 200 on canonical routes;
                Phase 2/3 may keep 301 leg unverified because CF Pages
                parser drops are easiest to spot on the 200 leg first.

Environment:
  Honors no env vars. Pass the preview URL as a positional arg so the
  invocation is identical in shell and CI (.github/workflows/quality-gates.yml).
EOF
  exit 2
}

# ---------- args ----------
[ "$#" -ge 1 ] || usage
PREVIEW_URL="$1"
STRICT=0
for arg in "${@:2}"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    -h|--help) usage ;;
    *) echo "unknown arg: $arg" >&2; usage ;;
  esac
done

# Strip trailing slash on preview URL — we always concatenate routes that
# start with '/', so a `https://x.pages.dev/` + `/aaro/` would produce a
# double-slash URL that CF Pages does NOT normalize (it 404s).
PREVIEW_URL="${PREVIEW_URL%/}"

[ -f "$URL_CONTRACT" ] || { echo "FATAL: $URL_CONTRACT not found" >&2; exit 2; }

# ---------- helpers ----------
# check_url URL EXPECTED_STATUS
# Returns 0 on match, 1 on mismatch. Prints one line either way.
check_url() {
  local url="$1" expected="$2"
  local actual
  actual=$(curl -sI -o /dev/null \
    -w '%{http_code}' \
    --max-time 15 \
    --connect-timeout 10 \
    -A "$UA" \
    "$url" 2>/dev/null)
  if [ "$actual" = "$expected" ]; then
    echo "  [ok]    $url → $actual"
    return 0
  fi
  echo "  [FAIL]  $url → got $actual, expected $expected"
  return 1
}

# ---------- collect canonical routes ----------
# URL-CONTRACT.txt format (per 02-05 SUMMARY):
#   - lines starting with '#' are comments (header)
#   - blank lines are skipped
#   - every other line is a route starting with '/'
#   - some lines carry a '#fragment' anchor (e.g. /#card-...); strip + dedupe
#
# 4937 lines in URL-CONTRACT.txt collapse to 95 canonical routes once
# fragments are stripped and duplicates removed.
#
# Use `while read` instead of `mapfile` — `mapfile` is a bash 4+ builtin,
# absent on macOS' system bash (3.2). CI Ubuntu has bash 5+ either way.
ROUTES=()
while IFS= read -r route; do
  [ -z "$route" ] && continue
  ROUTES+=("$route")
done < <(
  grep -vE '^#|^$' "$URL_CONTRACT" \
    | sed -E 's/#.*$//' \
    | grep -E '^/' \
    | sort -u
)

TOTAL="${#ROUTES[@]}"
[ "$TOTAL" -ge 1 ] || { echo "FATAL: parsed zero routes from $URL_CONTRACT" >&2; exit 2; }

echo "» CF Pages _redirects curl harness"
echo "  preview:  $PREVIEW_URL"
echo "  routes:   $TOTAL canonical (from URL-CONTRACT.txt)"
echo "  strict:   $([ "$STRICT" -eq 1 ] && echo "yes (probes /foo → /foo/ 301 leg)" || echo "no (200 leg only)")"
echo "  UA:       $UA"
echo

# ---------- probe ----------
pass=0
fail=0
for route in "${ROUTES[@]}"; do
  if check_url "${PREVIEW_URL}${route}" 200; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    if [ "$fail" -ge "$MAX_FAILS" ]; then
      echo
      echo "  …stopping at $MAX_FAILS failures (use --strict for full sweep or inspect CF Pages build log)"
      break
    fi
  fi

  # Optional 301 leg for directory routes (e.g. /aaro -> /aaro/).
  # Only probe routes that END with '/' AND are not the root '/'.
  if [ "$STRICT" -eq 1 ] && [ "${route: -1}" = "/" ] && [ "$route" != "/" ]; then
    unslashed="${route%/}"
    if check_url "${PREVIEW_URL}${unslashed}" 301; then
      pass=$((pass + 1))
    else
      fail=$((fail + 1))
      if [ "$fail" -ge "$MAX_FAILS" ]; then
        echo
        echo "  …stopping at $MAX_FAILS failures (use --strict for full sweep or inspect CF Pages build log)"
        break 2
      fi
    fi
  fi
done

echo
echo "» Summary"
echo "  passed:  $pass"
echo "  failed:  $fail"
echo "  total:   $((pass + fail))"

if [ "$fail" -gt 0 ]; then
  echo
  echo "  Any [FAIL] line above signals CF Pages disagrees with the rule"
  echo "  build-redirects.py emitted. Inspect the CF Pages build log for"
  echo "  'Parsed N redirects' (Pitfall #8): N below 109 means rules were"
  echo "  silently dropped at parse time."
  exit 1
fi

echo "  All canonical routes match expected status."
exit 0
