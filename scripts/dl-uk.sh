#!/usr/bin/env bash
# ============================================================
# UK National Archives — MoD UFO files downloader.
#
# Press releases + the catalog entry pages. The actual scanned
# PDFs sit behind discovery.nationalarchives.gov.uk's C-record
# pages — they're not direct PDF URLs, so we surface the catalog
# deep-links and grab what we can.
# ============================================================
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UK="$ROOT/uk-mirror"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
mkdir -p "$UK/pdfs" "$UK/assets/images"

fetch() {
  local url="$1" dest="$2"
  [ -s "$dest" ] && { echo "  [cache] $(basename "$dest")"; return 0; }
  if curl -fsSL --max-time 120 --connect-timeout 15 -A "$UA" -o "$dest" "$url"; then
    echo "  [ok]    $(basename "$dest") $(wc -c <"$dest" | tr -d ' ') bytes"
  else
    rm -f "$dest"; echo "  [FAIL]  $(basename "$dest")"; return 1
  fi
}

echo "» UK press release"
fetch "https://cdn.nationalarchives.gov.uk/documents/final-tranche-of-UFO-files-released.pdf" \
      "$UK/pdfs/Final-Tranche-UFO-Files-Press-Release.pdf"

echo "» UK done"
ls "$UK/pdfs" 2>/dev/null
