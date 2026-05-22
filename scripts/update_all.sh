#!/usr/bin/env bash
# ============================================================
# update_all.sh — fully autonomous mirror refresh.
#
# Pipeline (each step idempotent):
#   1. sync.sh --all              download every source page + asset
#   2. upload to GitHub Releases  push any new mp4 / pdf files to videos-v1 / pdfs-v1
#   3. rebuild every HTML page    via the build-*.py scripts
#   4. regenerate sitemap.xml     so search engines see fresh lastmod
#   5. git add + commit + push    only commits if there's something to commit
#
# Designed for cron / GitHub Actions / launchd. No prompts — exit-code
# preserved so a wrapper can alert on failure.
#
# Usage:
#   ./scripts/update_all.sh            # full pipeline
#   ./scripts/update_all.sh --no-push  # skip step 5
#   ./scripts/update_all.sh --dry-run  # show what would happen, no writes
# ============================================================
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DRY=0
DO_PUSH=1
for arg in "$@"; do
  case "$arg" in
    --no-push)  DO_PUSH=0 ;;
    --dry-run)  DRY=1 ;;
    -h|--help)
      sed -n '2,18p' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

step() { echo ""; echo "============================================================"; echo "  $*"; echo "============================================================"; }
maybe() { [ "$DRY" -eq 1 ] && echo "  [dry] $*" || eval "$@"; }

step "1/5  sync.sh --all"
maybe "bash '$ROOT/scripts/sync.sh' --all"

step "2/5  GitHub Releases — upload new mp4 + pdf assets"
if ! command -v gh >/dev/null 2>&1; then
  echo "  ! gh CLI not installed; skipping upload step"
else
  # Videos
  if ls bundles/uapvideos/*.mp4 aaro/videos/*.mp4 geipan/videos/*.mp4 2>/dev/null | grep -q .; then
    echo "  → uploading mp4 files to videos-v1 (--clobber)"
    maybe "gh release upload videos-v1 bundles/uapvideos/*.mp4 aaro/videos/*.mp4 geipan/videos/*.mp4 --clobber 2>/dev/null || true"
  fi
  # PDFs
  PDF_FILES=(bundles/Release_1/*.pdf aaro/pdfs/*.pdf nasa/pdfs/*.pdf nara/pdfs/*.pdf geipan/pdfs/*.pdf uk/pdfs/*.pdf chile/pdfs/*.pdf)
  for d in nz-mirror canada-mirror argentina-mirror uruguay-mirror peru-mirror spain-mirror italy-mirror; do
    if ls "$d"/pdfs/*.pdf 2>/dev/null | grep -q .; then
      PDF_FILES+=("$d/pdfs/"*.pdf)
    fi
  done
  if [ "${#PDF_FILES[@]}" -gt 0 ]; then
    echo "  → uploading ${#PDF_FILES[@]} pdf candidates to pdfs-v1 (--clobber)"
    maybe "gh release upload pdfs-v1 ${PDF_FILES[*]} --clobber 2>/dev/null || true"
  fi
fi

step "3/5  Rebuild every HTML page"
maybe "python3 '$ROOT/scripts/build-wargov.py'"
maybe "python3 '$ROOT/scripts/parse-aaro.py'"
maybe "python3 '$ROOT/scripts/extract-evidence.py'"
maybe "python3 '$ROOT/scripts/build-aaro.py'"
maybe "python3 '$ROOT/scripts/build-details.py'"
maybe "python3 '$ROOT/scripts/build-nasa.py'"
maybe "python3 '$ROOT/scripts/build-nara.py'"
maybe "python3 '$ROOT/scripts/build-geipan.py'"
maybe "python3 '$ROOT/scripts/build-uk.py'"
maybe "python3 '$ROOT/scripts/build-brazil.py'"
maybe "python3 '$ROOT/scripts/build-chile.py'"
maybe "python3 '$ROOT/scripts/build_batch3.py'"

step "4/5  Regenerate sitemap.xml"
cat > /tmp/build_sitemap.py <<'PY'
import os, datetime
ROOT = os.environ['ROOT']
BASE = 'https://realufo.org'
today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
URLS = [
    ('/', 'weekly', '1.0'),
    ('/aaro/', 'weekly', '0.9'),
    ('/aaro/details.html', 'monthly', '0.7'),
    ('/nasa/', 'monthly', '0.8'),
    ('/nara/', 'monthly', '0.8'),
    ('/geipan/', 'monthly', '0.8'),
    ('/uk/', 'monthly', '0.7'),
    ('/brazil/', 'monthly', '0.7'),
    ('/chile/', 'monthly', '0.7'),
    ('/nz/', 'monthly', '0.7'),
    ('/canada/', 'monthly', '0.7'),
    ('/argentina/', 'monthly', '0.7'),
    ('/uruguay/', 'monthly', '0.7'),
    ('/peru/', 'monthly', '0.7'),
    ('/spain/', 'monthly', '0.7'),
    ('/italy/', 'monthly', '0.7'),
]
out = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for path, freq, prio in URLS:
    out.append(f'  <url><loc>{BASE}{path}</loc><lastmod>{today}</lastmod><changefreq>{freq}</changefreq><priority>{prio}</priority></url>')
out.append('</urlset>')
open(os.path.join(ROOT, 'sitemap.xml'), 'w').write('\n'.join(out))
print(f'  sitemap.xml ({len(URLS)} URLs · lastmod {today})')
PY
maybe "ROOT='$ROOT' python3 /tmp/build_sitemap.py"

step "5/5  Commit + push"
if [ "$DO_PUSH" -eq 0 ]; then
  echo "  --no-push → skipping"
else
  if git diff --quiet && git diff --quiet --staged; then
    echo "  nothing to commit (working tree clean)"
  else
    maybe "git add -A"
    STAMP="$(date -u +%Y-%m-%dT%H:%MZ)"
    maybe "git commit -m 'auto-sync: $STAMP'"
    maybe "git push"
  fi
fi

echo ""
echo "✓ update_all.sh complete."
