#!/usr/bin/env bash
# Chile — SEFAA (formerly CEFAA) / DGAC downloader.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CL="$ROOT/chile-mirror"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
mkdir -p "$CL/pdfs" "$CL/assets/images"

fetch() {
  local url="$1" dest="$2"
  [ -s "$dest" ] && { echo "  [cache] $(basename "$dest")"; return 0; }
  if curl -fsSL --max-time 120 --connect-timeout 15 -A "$UA" -o "$dest" "$url"; then
    echo "  [ok]    $(basename "$dest") $(wc -c <"$dest" | tr -d ' ') bytes"
  else
    rm -f "$dest"; echo "  [FAIL]  $(basename "$dest")"; return 1
  fi
}

echo "» Chile DGAC CEFAA publication"
fetch "https://www.dgac.gob.cl/wp-content/uploads/2019/09/PUBLICACI%C3%93N-WEB-DGAC-CEFAA-CORREGIDA-11-SEPT-2019-1.pdf" \
      "$CL/pdfs/DGAC-CEFAA-Publicacion-Web-2019.pdf"

echo "» Chile done"
ls "$CL/pdfs" 2>/dev/null
