#!/usr/bin/env bash
# ============================================================
# postbuild: copy git-tracked legacy archive files into dist/
#
# Phase 3 Plan 03-05/03-06 — option (a) per cf-pages-project.md
# §interfaces: until Phase 4 SSG-06 ports the 14 non-wargov
# archives to Astro, copy their legacy Python-built HTML into
# dist/<slug>/ so URL-CONTRACT.txt routes resolve to the correct
# content instead of being shadowed by the wargov SPA fallback.
#
# CRITICAL: uses `git ls-files` to enumerate sources so that
#   - PDFs (gitignored per CLAUDE.md §5.2) are NOT copied (binary
#     CDN via GitHub Releases per §5.1)
#   - Videos (gitignored) are NOT copied
#   - Only HTML/SVG/PNG/JPG/JSON/CSS/JS that are version-controlled
#     end up in dist/
#
# Skipped:
#   - wargov/ — does not exist; Astro owns / via src/pages/index.astro
#   - root index.html — Astro overwrites this with the new wargov page
# ============================================================
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
DIST="$REPO/dist"

if [ ! -d "$DIST" ]; then
  echo "postbuild: $DIST does not exist; skipping (was astro build run?)" >&2
  exit 0
fi

copied_count=0
skipped_count=0
# CF Pages hard limit per file (25 MiB) per https://developers.cloudflare.com/pages/platform/limits/
MAX_BYTES=$((25 * 1024 * 1024))

copy_one() {
  local f="$1"
  local size
  size=$(stat -f %z "$f" 2>/dev/null || stat -c %s "$f" 2>/dev/null || echo 0)
  if [ "${size:-0}" -gt "$MAX_BYTES" ]; then
    echo "postbuild: SKIP $f (${size} bytes > 25 MiB CF Pages limit; belongs in GitHub Releases per CLAUDE.md §5.1)" >&2
    skipped_count=$((skipped_count + 1))
    return
  fi
  mkdir -p "$DIST/$(dirname "$f")"
  cp "$f" "$DIST/$f"
  copied_count=$((copied_count + 1))
}

# --- non-wargov archive directories (excluding ones now ported to Astro) ---
# Plans 04-05/04-06 (D-09): the New Zealand + Uruguay archive index pages
# are now served by src/pages/[archive]/index.astro. As subsequent Wave 3+
# ports complete (04-07..04-18), drop each slug from this list. When the
# list is empty, this script can be deleted entirely.
for slug in geipan uk brazil chile argentina canada italy peru spain; do
  if [ -d "$slug" ]; then
    while IFS= read -r f; do
      copy_one "$f"
    done < <(git ls-files "$slug/")
  fi
done

# --- partial-port archives ---
# Plans 04-05/04-06 (D-09): the [archive]/ index page was ported to Astro
# but legacy story sub-pages remain (story.html, case-specific narratives).
# Copy ONLY the sub-pages, NEVER the legacy index.html — Astro now owns
# the index route and the legacy HTML would shadow it. Cross-archive
# links policed by scripts/sync-nav.py + sync-footer.py still target
# these sub-pages, so a 404 here would break the live site.
if [ -d "nz" ]; then
  while IFS= read -r f; do
    case "$f" in
      nz/index.html) continue ;;  # Astro now owns /nz/ — never copy
      *) copy_one "$f" ;;
    esac
  done < <(git ls-files "nz/")
fi
if [ -d "uruguay" ]; then
  while IFS= read -r f; do
    case "$f" in
      uruguay/index.html) continue ;;  # Astro now owns /uruguay/ — never copy
      *) copy_one "$f" ;;
    esac
  done < <(git ls-files "uruguay/")
fi
if [ -d "nasa" ]; then
  # Plan 04-16 partial-port: Astro owns /nasa/ (src/pages/nasa/index.astro)
  # but NASA has a legacy long-form sub-page (nasa/story.html — full
  # narrative of the UAP Independent Study Team's work) plus
  # nasa/assets/* (favicon.svg, og.svg, images/uap-meeting-2023.jpeg,
  # images/uap-report-cover.png). All are policed by
  # scripts/sync-footer.py STORY_META + URL-CONTRACT.txt; missing them
  # would 404 cross-archive nav links. Copy everything EXCEPT
  # nasa/index.html (which Astro owns).
  while IFS= read -r f; do
    case "$f" in
      nasa/index.html) continue ;;  # Astro now owns /nasa/ — never copy
      *) copy_one "$f" ;;
    esac
  done < <(git ls-files "nasa/")
fi
if [ -d "nara" ]; then
  # Plan 04-15 partial-port: Astro owns /nara/ (src/pages/nara/index.astro)
  # but NARA has many legacy sub-pages — case-specific narratives
  # (chiles-whitted, condon-committee, levelland, lubbock-lights,
  # mantell, mcminnville, robertson-panel, roswell, socorro, story) and
  # a nara/pages/* directory (blogs-and-articles, faqs, federal-agency,
  # moving-images-and-sound, photographs, presidential-libraries,
  # rg-615, textual-and-microfilm, topic). All are policed by
  # scripts/sync-footer.py STORY_META and URL-CONTRACT.txt; missing them
  # would 404 cross-archive nav links. Copy everything EXCEPT
  # nara/index.html (which Astro owns).
  while IFS= read -r f; do
    case "$f" in
      nara/index.html) continue ;;  # Astro now owns /nara/ — never copy
      *) copy_one "$f" ;;
    esac
  done < <(git ls-files "nara/")
fi
if [ -d "aaro" ]; then
  # Plan 04-17 partial-port: Astro owns /aaro/ (src/pages/aaro/index.astro)
  # but AARO has the LARGEST legacy sub-page set of any partial-port
  # archive — 14 case-specific narratives (belgian-wave, cash-landrum,
  # coyne, gimbal, jal-1628, ohare-2006, phoenix-lights, stephenville,
  # story, tehran, tic-tac, travis-walton + details.html master index)
  # plus the aaro/pages/* directory (congressional-press-products,
  # efoia-reading-room, faq, home, leaders, mission-vision,
  # official-uap-imagery, resources, submit-a-report,
  # uap-case-resolution-reports, uap-records, uap-reporting-trends)
  # plus aaro/assets/* (favicon.svg, og.svg, images/*). All are policed
  # by scripts/sync-footer.py STORY_META + URL-CONTRACT.txt; missing
  # them would 404 cross-archive nav links. Copy everything EXCEPT
  # aaro/index.html (which Astro owns).
  while IFS= read -r f; do
    case "$f" in
      aaro/index.html) continue ;;  # Astro now owns /aaro/ — never copy
      *) copy_one "$f" ;;
    esac
  done < <(git ls-files "aaro/")
fi

# --- top-level static pages (NOT root index.html — Astro owns wargov at /) ---
for f in search.html stats.html timeline.html whatsnew.html; do
  if [ -f "$f" ]; then
    copy_one "$f"
  fi
done

# --- shared root-level assets + slideshow ---
for dir in assets slideshow; do
  if [ -d "$dir" ]; then
    while IFS= read -r f; do
      copy_one "$f"
    done < <(git ls-files "$dir/")
  fi
done

echo "postbuild: copied $copied_count legacy files into dist/; skipped $skipped_count oversized files"
