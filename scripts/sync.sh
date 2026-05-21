#!/usr/bin/env bash
# ============================================================
# PURSUE × AARO — Master sync.
#
# Downloads every asset (war.gov UFO + AARO) and rebuilds both
# mirror pages so they reflect what's actually on disk.
#
# Idempotent — safe to re-run on a schedule (cron, launchd, …).
#
# Usage:
#   ./scripts/sync.sh                # interactive site picker
#   ./scripts/sync.sh --all          # all sites, no prompt
#   ./scripts/sync.sh --aaro-only    # only AARO
#   ./scripts/sync.sh --wargov-only  # only war.gov
#   ./scripts/sync.sh --no-build     # skip HTML rebuild
#   ./scripts/sync.sh --no-videos    # skip big AARO videos
# ============================================================
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DO_WARGOV=1
DO_AARO=1
DO_BUILD=1
DO_VIDEOS=1
INTERACTIVE=1
for arg in "$@"; do
  case "$arg" in
    --all)          INTERACTIVE=0 ;;
    --aaro-only)    DO_WARGOV=0; INTERACTIVE=0 ;;
    --wargov-only)  DO_AARO=0;   INTERACTIVE=0 ;;
    --no-build)     DO_BUILD=0 ;;
    --no-videos)    DO_VIDEOS=0 ;;
    -h|--help)
      sed -n '2,18p' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

# Interactive site picker — only when stdin is a TTY and no explicit flag given.
if [ "$INTERACTIVE" -eq 1 ] && [ -t 0 ]; then
  echo ""
  echo "Which sites do you want to sync?"
  echo "  [1] war.gov / UFO Release 01  (slideshow + Release_1 + DVIDS bundle)"
  echo "  [2] AARO                       (pages + PDFs + cloudfront videos)"
  echo "  [3] Both  (default)"
  echo "  [q] quit"
  printf "Select: "
  read -r CHOICE
  case "${CHOICE:-3}" in
    1)   DO_AARO=0 ;;
    2)   DO_WARGOV=0 ;;
    3|"") : ;;  # both
    q|Q) echo "aborted."; exit 0 ;;
    *)   echo "unknown selection — defaulting to both" ;;
  esac
  if [ "$DO_AARO" -eq 1 ] && [ "$DO_VIDEOS" -eq 1 ]; then
    printf "Include AARO cloudfront videos (~2.7 GB)? [Y/n]: "
    read -r VR
    case "${VR:-Y}" in n|N) DO_VIDEOS=0 ;; esac
  fi
fi

echo "=========================================================="
echo "  PURSUE × AARO offline mirror sync"
echo "  $(date -u +%Y-%m-%dT%H:%M:%SZ)  →  $ROOT"
echo "=========================================================="

# ---------- war.gov UFO ----------
if [ "$DO_WARGOV" -eq 1 ]; then
  echo ""
  echo "──── 1/4  war.gov/UFO downloader (curl_cffi) ────"
  if ! python3 -c "import curl_cffi" 2>/dev/null; then
    echo "  ! Missing dependency: curl_cffi"
    echo "  ! Install with: pip install curl_cffi"
    echo "  ! Skipping war.gov side."
  else
    python3 "$ROOT/download.py"
  fi
fi

# ---------- AARO ----------
if [ "$DO_AARO" -eq 1 ]; then
  echo ""
  echo "──── 2/4  AARO page snapshots (Wayback Machine) ────"
  bash "$ROOT/scripts/dl-aaro.sh" pages

  echo ""
  echo "──── 3/4  AARO asset downloader (videos + PDFs + imgs) ────"
  if [ "$DO_VIDEOS" -eq 1 ]; then
    bash "$ROOT/scripts/dl-aaro.sh" assets
  else
    bash "$ROOT/scripts/dl-aaro.sh" assets --no-videos
  fi
fi

# ---------- Rebuild HTML ----------
if [ "$DO_BUILD" -eq 1 ]; then
  echo ""
  echo "──── 4/4  Rebuild both mirror pages ────"
  python3 "$ROOT/scripts/build-wargov.py"
  python3 "$ROOT/scripts/parse-aaro.py"
  python3 "$ROOT/scripts/extract-evidence.py"
  python3 "$ROOT/scripts/build-aaro.py"
  python3 "$ROOT/scripts/build-details.py"
  echo "  Mirror pages rebuilt."
fi

echo ""
echo "──── Local-asset summary ────"
printf "  slideshow images  %4d files (%s)\n" \
  "$(ls -1 "$ROOT/slideshow" 2>/dev/null | wc -l | tr -d ' ')" \
  "$(du -sh "$ROOT/slideshow" 2>/dev/null | cut -f1)"
printf "  Release_1 docs    %4d files (%s)\n" \
  "$(ls -1 "$ROOT/bundles/Release_1" 2>/dev/null | wc -l | tr -d ' ')" \
  "$(du -sh "$ROOT/bundles/Release_1" 2>/dev/null | cut -f1)"
printf "  DVIDS videos      %4d files (%s)\n" \
  "$(ls -1 "$ROOT/bundles/uapvideos" 2>/dev/null | wc -l | tr -d ' ')" \
  "$(du -sh "$ROOT/bundles/uapvideos" 2>/dev/null | cut -f1)"
printf "  AARO pages        %4d files (%s)\n" \
  "$(ls -1 "$ROOT/aaro-mirror/pages" 2>/dev/null | wc -l | tr -d ' ')" \
  "$(du -sh "$ROOT/aaro-mirror/pages" 2>/dev/null | cut -f1)"
printf "  AARO PDFs         %4d files (%s)\n" \
  "$(ls -1 "$ROOT/aaro-mirror/pdfs" 2>/dev/null | wc -l | tr -d ' ')" \
  "$(du -sh "$ROOT/aaro-mirror/pdfs" 2>/dev/null | cut -f1)"
printf "  AARO videos       %4d files (%s)\n" \
  "$(ls -1 "$ROOT/aaro-mirror/videos" 2>/dev/null | wc -l | tr -d ' ')" \
  "$(du -sh "$ROOT/aaro-mirror/videos" 2>/dev/null | cut -f1)"
printf "  AARO images       %4d files (%s)\n" \
  "$(ls -1 "$ROOT/aaro-mirror/assets/images" 2>/dev/null | wc -l | tr -d ' ')" \
  "$(du -sh "$ROOT/aaro-mirror/assets/images" 2>/dev/null | cut -f1)"

echo ""
echo "Done. Open index.html or aaro-mirror/index.html in a browser."
