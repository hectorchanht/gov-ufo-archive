#!/usr/bin/env bash
# ============================================================
# NASA UAP downloader.
#
# Fetches the 4 official PDFs + 2 cover images from
# science.nasa.gov/uap/ — small, fast, no Akamai block.
# YouTube videos play via iframe embed; no local copy.
#
# Idempotent.
# ============================================================
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NASA="$ROOT/nasa"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
mkdir -p "$NASA/pdfs" "$NASA/assets/images"

fetch() {
  local url="$1" dest="$2"
  [ -s "$dest" ] && { echo "  [cache] $(basename "$dest")"; return 0; }
  if curl -fsSL --max-time 120 --connect-timeout 15 -A "$UA" -o "$dest" "$url"; then
    echo "  [ok]    $(basename "$dest") $(wc -c <"$dest" | tr -d ' ') bytes"
  else
    rm -f "$dest"
    echo "  [FAIL]  $(basename "$dest")"
    return 1
  fi
}

echo "» NASA PDFs"
fetch "https://science.nasa.gov/wp-content/uploads/2023/09/uap-independent-study-team-final-report.pdf" \
      "$NASA/pdfs/uap-independent-study-team-final-report.pdf"
fetch "https://science.nasa.gov/wp-content/uploads/2024/01/public-meeting-agenda-tagged.pdf" \
      "$NASA/pdfs/public-meeting-agenda-tagged.pdf"
fetch "https://science.nasa.gov/wp-content/uploads/2024/01/frn-uapist-public-meeting-tagged.pdf" \
      "$NASA/pdfs/frn-uapist-public-meeting-tagged.pdf"
fetch "https://science.nasa.gov/wp-content/uploads/2023/04/UAPISTTermsofReference_Signed.pdf" \
      "$NASA/pdfs/UAPISTTermsofReference_Signed.pdf"

echo "» NASA images"
fetch "https://science.nasa.gov/wp-content/uploads/2022/06/uap-meeting-2023-e1692299097471.jpeg" \
      "$NASA/assets/images/uap-meeting-2023.jpeg"
fetch "https://science.nasa.gov/wp-content/uploads/2023/09/uap-report-cover-9-2023.png" \
      "$NASA/assets/images/uap-report-cover.png"

echo "» NASA done"
ls "$NASA/pdfs" "$NASA/assets/images"
