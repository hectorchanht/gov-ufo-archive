#!/usr/bin/env bash
# Brazil — Arquivo Nacional / FAB OVNI downloader.
# The 4,500+ declassified Brazilian UFO docs live behind the Dibrarq catalog
# (CAPTCHA-gated) and the FAB CENDOC archive. We surface the catalog deep-links.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BR="$ROOT/brazil-mirror"
mkdir -p "$BR/pdfs" "$BR/assets/images"
echo "» Brazil mirror = curated catalog deep-links (no direct PDFs reachable)"
echo "  (Arquivo Nacional + FAB CENDOC sit behind CAPTCHA / session-based catalogs)"
