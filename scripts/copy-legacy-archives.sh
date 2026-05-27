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
# Plan 04-05 (D-09): the New Zealand archive index page is now served by
# src/pages/[archive]/index.astro. As subsequent Wave 3+ ports complete
# (04-06..04-18), drop each slug from this list. When the list is empty,
# this script can be deleted entirely.
for slug in aaro nasa nara geipan uk brazil chile argentina canada italy peru spain uruguay; do
  if [ -d "$slug" ]; then
    while IFS= read -r f; do
      copy_one "$f"
    done < <(git ls-files "$slug/")
  fi
done

# --- partial-port archives ---
# Plan 04-05 (D-09): the [archive]/ index page was ported to Astro but
# legacy story sub-pages remain (story.html, case-specific narratives).
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
