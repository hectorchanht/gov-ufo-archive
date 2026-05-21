#!/usr/bin/env bash
# ============================================================
# AARO offline downloader.
#
# Two phases (call separately or together):
#   pages   – snapshot the 12 main aaro.mil pages via Wayback
#   assets  – download every UAP video, PDF, image discovered
#             while crawling those pages
#
# Idempotent: skips files already on disk.
#
# Usage:
#   ./scripts/dl-aaro.sh pages
#   ./scripts/dl-aaro.sh assets [--no-videos]
#   ./scripts/dl-aaro.sh all
# ============================================================
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AARO="$ROOT/aaro-mirror"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

mkdir -p "$AARO/pages" "$AARO/pdfs" "$AARO/videos" "$AARO/assets/images"

NO_VIDEOS=0
MODE="${1:-all}"
for arg in "${@:2}"; do
  [ "$arg" = "--no-videos" ] && NO_VIDEOS=1
done

# ---------- helpers ----------
snapshot_for() {
  # Best Wayback snapshot timestamp for a URL (or empty).
  local url="$1"
  curl -s --max-time 10 "http://archive.org/wayback/available?url=$url" \
    | python3 -c 'import sys,json
try:
    d=json.load(sys.stdin); s=d.get("archived_snapshots",{}).get("closest")
    print(s.get("timestamp") if s and s.get("status")=="200" else "")
except: pass' 2>/dev/null
}

cdx_latest() {
  # CDX fallback for an older 200 snapshot
  curl -s --max-time 10 "https://web.archive.org/cdx/search/cdx?url=$1&output=json&limit=-3&filter=statuscode:200" \
    | python3 -c 'import sys,json
try:
    d=json.load(sys.stdin)
    if len(d)>1: print(d[-1][1])
except: pass' 2>/dev/null
}

fetch_url() {
  # fetch_url URL DEST MODE
  # MODE: direct (try direct first), wayback (only Wayback)
  local url="$1" dest="$2" mode="${3:-wayback}"
  [ -s "$dest" ] && return 0
  mkdir -p "$(dirname "$dest")"

  if [ "$mode" = "direct" ]; then
    curl -fsSL --max-time 240 --connect-timeout 15 -A "$UA" -o "$dest" "$url" 2>/dev/null && return 0
  fi

  local ts; ts=$(snapshot_for "$url")
  if [ -n "$ts" ]; then
    local flag="if_"
    case "$url" in *.jpg|*.jpeg|*.png|*.gif|*.svg|*.webp) flag="im_";; esac
    case "$url" in *.mp4|*.mov|*.webm) flag="if_";; esac
    curl -fsSL --max-time 120 --connect-timeout 15 -A "$UA" \
      -o "$dest" "https://web.archive.org/web/${ts}${flag}/${url}" 2>/dev/null && return 0
  fi

  local cdx_ts; cdx_ts=$(cdx_latest "$url")
  if [ -n "$cdx_ts" ] && [ "$cdx_ts" != "$ts" ]; then
    curl -fsSL --max-time 120 --connect-timeout 15 -A "$UA" \
      -o "$dest" "https://web.archive.org/web/${cdx_ts}id_/${url}" 2>/dev/null && return 0
  fi

  rm -f "$dest"
  return 1
}
export -f fetch_url snapshot_for cdx_latest
export UA

# ---------- PAGES ----------
do_pages() {
  echo "» AARO page snapshots → aaro-mirror/pages/"
  local PAGES=(
    "home|https://www.aaro.mil/"
    "mission-vision|https://www.aaro.mil/About/Mission-Vision/"
    "leaders|https://www.aaro.mil/About/Leaders/"
    "official-uap-imagery|https://www.aaro.mil/UAP-Cases/Official-UAP-Imagery/"
    "uap-case-resolution-reports|https://www.aaro.mil/UAP-Cases/UAP-Case-Resolution-Reports/"
    "uap-reporting-trends|https://www.aaro.mil/UAP-Cases/UAP-Reporting-Trends/"
    "uap-records|https://www.aaro.mil/UAP-Records/"
    "congressional-press-products|https://www.aaro.mil/Congressional-Press-Products/"
    "resources|https://www.aaro.mil/Resources/"
    "efoia-reading-room|https://www.aaro.mil/EFOIA-Reading-Room/"
    "submit-a-report|https://www.aaro.mil/Submit-A-Report/"
    "faq|https://www.aaro.mil/FAQ/"
  )
  for entry in "${PAGES[@]}"; do
    local slug="${entry%%|*}" url="${entry##*|}"
    local dest="$AARO/pages/${slug}.html"
    if [ -s "$dest" ]; then echo "  [cache] $slug"; continue; fi
    if fetch_url "$url" "$dest" wayback; then
      echo "  [ok]    $slug ($(wc -c <"$dest" | tr -d ' ') bytes)"
    else
      echo "  [FAIL]  $slug — no Wayback snapshot"
    fi
  done
}

# ---------- ASSETS ----------
do_assets() {
  echo "» AARO assets — videos, PDFs, images"
  # Need the evidence map. Build it if missing or stale.
  if [ ! -f "$AARO/.cache/evidence.json" ] || [ "$AARO/pages" -nt "$AARO/.cache/evidence.json" ]; then
    echo "  (building evidence map…)"
    mkdir -p "$AARO/.cache"
    python3 "$ROOT/scripts/parse-aaro.py" > /dev/null
    python3 "$ROOT/scripts/extract-evidence.py" > /dev/null
  fi

  # === Videos (cloudfront direct) ===
  if [ "$NO_VIDEOS" -eq 0 ]; then
    echo "» Videos (cloudfront, parallel x3)"
    python3 -c "
import json, os
ev = json.load(open('$AARO/.cache/evidence.json'))
have = set(os.listdir('$AARO/videos')) if os.path.isdir('$AARO/videos') else set()
for v in ev['videos']:
    if v['filename'] not in have:
        print(v['url'] + '|' + v['filename'])
" > "$AARO/.cache/vid-todo.txt"
    local n; n=$(wc -l <"$AARO/.cache/vid-todo.txt" | tr -d ' ')
    echo "  $n video(s) to fetch"
    local batch=0
    while IFS='|' read -r url fname; do
      [ -z "$url" ] && continue
      (
        if fetch_url "$url" "$AARO/videos/$fname" direct; then
          echo "  [ok] $fname $(wc -c <"$AARO/videos/$fname" | tr -d ' ')"
        else
          echo "  [FAIL] $fname"
        fi
      ) &
      batch=$((batch+1))
      if [ $((batch % 3)) -eq 0 ]; then wait; fi
    done < "$AARO/.cache/vid-todo.txt"
    wait
  else
    echo "» Videos (skipped: --no-videos)"
  fi

  # === PDFs (Wayback) ===
  echo "» PDFs (Wayback, parallel x4)"
  python3 -c "
import json, os, urllib.parse
ev = json.load(open('$AARO/.cache/evidence.json'))
have = set(os.listdir('$AARO/pdfs')) if os.path.isdir('$AARO/pdfs') else set()
for p in ev['pdfs']:
    bn = urllib.parse.unquote(p['url'].rsplit('/',1)[-1].split('?')[0])
    if bn not in have:
        print(p['url'] + '|' + bn)
" > "$AARO/.cache/pdf-todo.txt"
  local np; np=$(wc -l <"$AARO/.cache/pdf-todo.txt" | tr -d ' ')
  echo "  $np PDF(s) to fetch"
  local batch=0
  while IFS='|' read -r url fname; do
    [ -z "$url" ] && continue
    (
      if fetch_url "$url" "$AARO/pdfs/$fname" wayback; then
        echo "  [ok] $fname"
      else
        echo "  [FAIL] $fname (not archived)"
      fi
    ) &
    batch=$((batch+1))
    if [ $((batch % 4)) -eq 0 ]; then wait; fi
  done < "$AARO/.cache/pdf-todo.txt"
  wait

  # === Images (Wayback) ===
  echo "» Images (Wayback, parallel x4)"
  python3 -c "
import json, os, urllib.parse
ev = json.load(open('$AARO/.cache/evidence.json'))
have = set(os.listdir('$AARO/assets/images')) if os.path.isdir('$AARO/assets/images') else set()
for i in ev['images']:
    bn = urllib.parse.unquote(i['url'].rsplit('/',1)[-1].split('?')[0])
    if bn not in have:
        print(i['url'] + '|' + bn)
" > "$AARO/.cache/img-todo.txt"
  local ni; ni=$(wc -l <"$AARO/.cache/img-todo.txt" | tr -d ' ')
  echo "  $ni image(s) to fetch"
  local batch=0
  while IFS='|' read -r url fname; do
    [ -z "$url" ] && continue
    (
      if fetch_url "$url" "$AARO/assets/images/$fname" wayback; then
        echo "  [ok] $fname"
      else
        echo "  [FAIL] $fname (not archived)"
      fi
    ) &
    batch=$((batch+1))
    if [ $((batch % 4)) -eq 0 ]; then wait; fi
  done < "$AARO/.cache/img-todo.txt"
  wait
}

case "$MODE" in
  pages)  do_pages ;;
  assets) do_assets ;;
  all)    do_pages; do_assets ;;
  *) echo "usage: $0 pages|assets|all [--no-videos]" >&2; exit 2 ;;
esac
