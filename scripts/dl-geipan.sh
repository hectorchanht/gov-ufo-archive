#!/usr/bin/env bash
# ============================================================
# France GEIPAN downloader.
#
# Fetches the 4 official PDFs (FAQ + Info, FR + EN) + 2 example
# case videos + IPACO image from cnes-geipan.fr.
# ============================================================
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GEIPAN="$ROOT/geipan"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
mkdir -p "$GEIPAN/pdfs" "$GEIPAN/videos" "$GEIPAN/assets/images"

fetch() {
  local url="$1" dest="$2"
  [ -s "$dest" ] && { echo "  [cache] $(basename "$dest")"; return 0; }
  if curl -fsSL --max-time 180 --connect-timeout 15 -A "$UA" -o "$dest" "$url"; then
    echo "  [ok]    $(basename "$dest") $(wc -c <"$dest" | tr -d ' ') bytes"
  else
    rm -f "$dest"; echo "  [FAIL]  $(basename "$dest")"; return 1
  fi
}

echo "» GEIPAN PDFs"
fetch "https://www.cnes-geipan.fr/sites/default/files/2021-08/FAQ%20-%20Press%20-%20English.pdf"      "$GEIPAN/pdfs/GEIPAN-FAQ-English.pdf"
fetch "https://www.cnes-geipan.fr/sites/default/files/2021-08/FAQ%20-%20Dossier%20presse.pdf"          "$GEIPAN/pdfs/GEIPAN-FAQ-Francais.pdf"
fetch "https://www.cnes-geipan.fr/sites/default/files/2021-08/GEIPAN-informationenglish.pdf"           "$GEIPAN/pdfs/GEIPAN-Mission-Method-English.pdf"
fetch "https://www.cnes-geipan.fr/sites/default/files/2021-08/GEIPAN-informations.pdf"                 "$GEIPAN/pdfs/GEIPAN-Mission-Methode-Francais.pdf"

echo "» GEIPAN case videos"
fetch "https://www.cnes-geipan.fr/sites/default/files/2021-08/SAINT-GERMAIN-EN-LAYE%20%2878%29%2030.05.2020.mp4" \
      "$GEIPAN/videos/Saint-Germain-en-Laye-2020-05-30.mp4"
fetch "https://www.cnes-geipan.fr/sites/default/files/2021-08/LYON%20%2869%29%2019.12.2019.mp4" \
      "$GEIPAN/videos/Lyon-2019-12-19.mp4"

echo "» GEIPAN images"
fetch "https://www.cnes-geipan.fr/sites/default/files/styles/vignette_a_la_une/public/2025-05/ipaco.jpg" \
      "$GEIPAN/assets/images/IPACO-team-2025.jpg"
fetch "https://www.cnes-geipan.fr/sites/default/files/styles/vignette/public/2024-07/starlink_note.jpg" \
      "$GEIPAN/assets/images/Starlink-flare-note-2024.jpg"
fetch "https://www.cnes-geipan.fr/sites/default/files/styles/large/public/2024-12/2024-509%20Diagramme%20Geipan.png" \
      "$GEIPAN/assets/images/GEIPAN-Cases-By-Phenomenon-2024.png"

echo "» GEIPAN done"
ls "$GEIPAN/pdfs" "$GEIPAN/videos" "$GEIPAN/assets/images"
