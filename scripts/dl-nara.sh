#!/usr/bin/env bash
# ============================================================
# NARA UAP topic downloader.
#
# Snapshots the topic gateway pages from archives.gov.
# The actual records (millions of pages) live in the NARA
# Catalog at catalog.archives.gov and aren't bulk-downloadable
# here; this mirror surfaces the official guide pages and the
# Bulk Catalog Download manifest URL.
# ============================================================
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NARA="$ROOT/nara-mirror"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
mkdir -p "$NARA/pages" "$NARA/pdfs"

PAGES=(
  "topic|https://www.archives.gov/research/topics/uaps"
  "rg-615|https://www.archives.gov/research/topics/uaps/rg-615"
  "photographs|https://www.archives.gov/research/topics/uaps/photographs"
  "moving-images-and-sound|https://www.archives.gov/research/topics/uaps/moving-images-and-sound"
  "textual-and-microfilm|https://www.archives.gov/research/topics/uaps/textual-and-microfilm"
  "presidential-libraries|https://www.archives.gov/research/topics/uaps/presidential-libraries"
  "federal-agency|https://www.archives.gov/research/topics/uaps/federal-agency"
  "blogs-and-articles|https://www.archives.gov/research/topics/uaps/blogs-and-articles"
  "faqs|https://www.archives.gov/research/topics/uaps/faqs"
)

fetch() {
  local url="$1" dest="$2"
  [ -s "$dest" ] && { echo "  [cache] $(basename "$dest")"; return 0; }
  if curl -fsSL --max-time 60 --connect-timeout 15 -A "$UA" -o "$dest" "$url"; then
    echo "  [ok]    $(basename "$dest") $(wc -c <"$dest" | tr -d ' ') bytes"
  else
    rm -f "$dest"
    echo "  [FAIL]  $(basename "$dest") (archives.gov may rate-limit; retry later)"
    return 1
  fi
}

echo "» NARA topic pages"
for entry in "${PAGES[@]}"; do
  slug="${entry%%|*}"
  url="${entry##*|}"
  fetch "$url" "$NARA/pages/${slug}.html"
done

# 2024 NDAA reference (Public Law 118-31) — the legal basis for RG 615.
fetch "https://www.congress.gov/118/bills/hr2670/BILLS-118hr2670enr.pdf" \
      "$NARA/pdfs/2024-NDAA-Public-Law-118-31.pdf"

echo "» NARA done"
ls "$NARA/pages" 2>/dev/null
