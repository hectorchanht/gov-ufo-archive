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
DO_NASA=1
DO_NARA=1
DO_GEIPAN=1
DO_UK=1
DO_BRAZIL=1
DO_CHILE=1
DO_NZ=1
DO_CANADA=1
DO_ARGENTINA=1
DO_URUGUAY=1
DO_PERU=1
DO_SPAIN=1
DO_ITALY=1
DO_BUILD=1
DO_VIDEOS=1
INTERACTIVE=1

# Helper: set all DO_* to 0
reset_all() { DO_WARGOV=0; DO_AARO=0; DO_NASA=0; DO_NARA=0; DO_GEIPAN=0; DO_UK=0; DO_BRAZIL=0; DO_CHILE=0; DO_NZ=0; DO_CANADA=0; DO_ARGENTINA=0; DO_URUGUAY=0; DO_PERU=0; DO_SPAIN=0; DO_ITALY=0; }

for arg in "$@"; do
  case "$arg" in
    --all)          INTERACTIVE=0 ;;
    --wargov-only)    reset_all; DO_WARGOV=1; INTERACTIVE=0 ;;
    --aaro-only)      reset_all; DO_AARO=1;   INTERACTIVE=0 ;;
    --nasa-only)      reset_all; DO_NASA=1;   INTERACTIVE=0 ;;
    --nara-only)      reset_all; DO_NARA=1;   INTERACTIVE=0 ;;
    --geipan-only)    reset_all; DO_GEIPAN=1; INTERACTIVE=0 ;;
    --uk-only)        reset_all; DO_UK=1;     INTERACTIVE=0 ;;
    --brazil-only)    reset_all; DO_BRAZIL=1; INTERACTIVE=0 ;;
    --chile-only)     reset_all; DO_CHILE=1;  INTERACTIVE=0 ;;
    --nz-only)        reset_all; DO_NZ=1;        INTERACTIVE=0 ;;
    --canada-only)    reset_all; DO_CANADA=1;    INTERACTIVE=0 ;;
    --argentina-only) reset_all; DO_ARGENTINA=1; INTERACTIVE=0 ;;
    --uruguay-only)   reset_all; DO_URUGUAY=1;   INTERACTIVE=0 ;;
    --peru-only)      reset_all; DO_PERU=1;      INTERACTIVE=0 ;;
    --spain-only)     reset_all; DO_SPAIN=1;     INTERACTIVE=0 ;;
    --italy-only)     reset_all; DO_ITALY=1;     INTERACTIVE=0 ;;
    --no-build)     DO_BUILD=0 ;;
    --no-videos)    DO_VIDEOS=0 ;;
    -h|--help)
      sed -n '2,20p' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

# Interactive picker — only on TTY, no explicit flag.
if [ "$INTERACTIVE" -eq 1 ] && [ -t 0 ]; then
  echo ""
  echo "Which sites? (comma-separated, e.g. 1,3,5)"
  echo "  [1]  war.gov / UFO Release 01"
  echo "  [2]  AARO (U.S.)"
  echo "  [3]  NASA UAP Independent Study"
  echo "  [4]  NARA UAP records gateway"
  echo "  [5]  France GEIPAN (CNES)"
  echo "  [6]  UK MoD UFO Files"
  echo "  [7]  Brazil FAB / Arquivo Nacional"
  echo "  [8]  Chile SEFAA / DGAC"
  echo "  [9]  New Zealand NZDF"
  echo "  [10] Canada Operation Magnet (LAC)"
  echo "  [11] Argentina CEFAe"
  echo "  [12] Uruguay CRIDOVNI"
  echo "  [13] Peru OIFAA"
  echo "  [14] Spain Ejército del Aire"
  echo "  [15] Italy Aeronautica Militare"
  echo "  [a]  ALL (default)"
  echo "  [q]  quit"
  printf "Select: "
  read -r CHOICE
  CHOICE="${CHOICE:-a}"
  if [ "$CHOICE" = "q" ] || [ "$CHOICE" = "Q" ]; then
    echo "aborted."; exit 0
  fi
  if [ "$CHOICE" != "a" ] && [ "$CHOICE" != "A" ]; then
    reset_all
    IFS=',' read -ra PICKS <<< "$CHOICE"
    for p in "${PICKS[@]}"; do
      case "$(echo "$p" | tr -d ' ')" in
        1)  DO_WARGOV=1 ;;
        2)  DO_AARO=1 ;;
        3)  DO_NASA=1 ;;
        4)  DO_NARA=1 ;;
        5)  DO_GEIPAN=1 ;;
        6)  DO_UK=1 ;;
        7)  DO_BRAZIL=1 ;;
        8)  DO_CHILE=1 ;;
        9)  DO_NZ=1 ;;
        10) DO_CANADA=1 ;;
        11) DO_ARGENTINA=1 ;;
        12) DO_URUGUAY=1 ;;
        13) DO_PERU=1 ;;
        14) DO_SPAIN=1 ;;
        15) DO_ITALY=1 ;;
        *)  echo "  ignored: $p" ;;
      esac
    done
  fi
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
    python3 "$ROOT/scripts/download-war.gov.py"
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

# ---------- NASA ----------
if [ "$DO_NASA" -eq 1 ]; then
  echo ""
  echo "──── NASA UAP downloader ────"
  bash "$ROOT/scripts/dl-nasa.sh"
fi

# ---------- NARA ----------
if [ "$DO_NARA" -eq 1 ]; then
  echo ""
  echo "──── NARA topic-page downloader ────"
  bash "$ROOT/scripts/dl-nara.sh"
fi

# ---------- France GEIPAN ----------
if [ "$DO_GEIPAN" -eq 1 ]; then
  echo ""
  echo "──── France GEIPAN downloader ────"
  bash "$ROOT/scripts/dl-geipan.sh"
fi

# ---------- UK National Archives ----------
if [ "$DO_UK" -eq 1 ]; then
  echo ""
  echo "──── UK National Archives downloader ────"
  bash "$ROOT/scripts/dl-uk.sh"
fi

# ---------- Brazil ----------
if [ "$DO_BRAZIL" -eq 1 ]; then
  echo ""
  echo "──── Brazil FAB / Arquivo Nacional downloader ────"
  bash "$ROOT/scripts/dl-brazil.sh"
fi

# ---------- Chile ----------
if [ "$DO_CHILE" -eq 1 ]; then
  echo ""
  echo "──── Chile SEFAA / DGAC downloader ────"
  bash "$ROOT/scripts/dl-chile.sh"
fi

# ---------- Rebuild HTML ----------
if [ "$DO_BUILD" -eq 1 ]; then
  echo ""
  echo "──── Rebuild mirror pages ────"
  python3 "$ROOT/scripts/build-wargov.py"
  python3 "$ROOT/scripts/parse-aaro.py"
  python3 "$ROOT/scripts/extract-evidence.py"
  python3 "$ROOT/scripts/build-aaro.py"
  python3 "$ROOT/scripts/build-details.py"
  python3 "$ROOT/scripts/build-nasa.py"
  python3 "$ROOT/scripts/build-nara.py"
  python3 "$ROOT/scripts/build-geipan.py"
  python3 "$ROOT/scripts/build-uk.py"
  python3 "$ROOT/scripts/build-brazil.py"
  python3 "$ROOT/scripts/build-chile.py"
  # Catalog-only mirrors (NZ, Canada, Argentina, Uruguay, Peru, Spain, Italy)
  python3 "$ROOT/scripts/build_batch3.py"
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
  "$(ls -1 "$ROOT/aaro/pages" 2>/dev/null | wc -l | tr -d ' ')" \
  "$(du -sh "$ROOT/aaro/pages" 2>/dev/null | cut -f1)"
printf "  AARO PDFs         %4d files (%s)\n" \
  "$(ls -1 "$ROOT/aaro/pdfs" 2>/dev/null | wc -l | tr -d ' ')" \
  "$(du -sh "$ROOT/aaro/pdfs" 2>/dev/null | cut -f1)"
printf "  AARO videos       %4d files (%s)\n" \
  "$(ls -1 "$ROOT/aaro/videos" 2>/dev/null | wc -l | tr -d ' ')" \
  "$(du -sh "$ROOT/aaro/videos" 2>/dev/null | cut -f1)"
printf "  AARO images       %4d files (%s)\n" \
  "$(ls -1 "$ROOT/aaro/assets/images" 2>/dev/null | wc -l | tr -d ' ')" \
  "$(du -sh "$ROOT/aaro/assets/images" 2>/dev/null | cut -f1)"

echo ""
echo "Done. Open index.html or aaro/index.html in a browser."
