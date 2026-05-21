#!/usr/bin/env python3
"""
PURSUE — war.gov/UFO offline mirror downloader (TLS-impersonating version).

Why this exists:
  www.war.gov is behind Akamai bot protection that fingerprints the TLS
  handshake (JA3/JA4). curl, wget, and python-requests all have detectable
  fingerprints and get 403'd no matter what headers you send.

  curl_cffi wraps curl-impersonate, which replicates a real Chrome TLS
  handshake byte-for-byte, so Akamai lets the request through.

Setup:
  pip install curl_cffi

Run:
  python3 download.py
"""

from __future__ import annotations
import os, sys, time
from pathlib import Path

try:
    from curl_cffi import requests
except ImportError:
    sys.exit(
        "\nMissing dependency. Install with:\n"
        "    pip install curl_cffi\n"
        "or, if you use pipx / a venv, install it there.\n"
    )

ROOT = Path(__file__).resolve().parent
SLIDES_DIR  = ROOT / "slideshow"
BUNDLES_DIR = ROOT / "bundles"
ASSETS_DIR  = ROOT / "assets"
for d in (SLIDES_DIR, BUNDLES_DIR, ASSETS_DIR):
    d.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "Referer": "https://www.war.gov/UFO/",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

# Try a few Chrome versions if one gets blocked
IMPERSONATE_PROFILES = ["chrome124", "chrome120", "chrome116", "chrome110"]


def fetch(url: str, out: Path) -> bool:
    """Download url -> out. Returns True on success."""
    label = out.name
    if out.exists() and out.stat().st_size > 0:
        print(f"  → {label:<70} [skip — already {out.stat().st_size:,} B]")
        return True

    last_code = "?"
    for profile in IMPERSONATE_PROFILES:
        try:
            r = requests.get(
                url,
                headers=HEADERS,
                impersonate=profile,
                timeout=1800,
                allow_redirects=True,
            )
            last_code = r.status_code
            if r.status_code == 200 and r.content:
                out.write_bytes(r.content)
                size = len(r.content)
                size_h = (
                    f"{size/1_000_000_000:.2f} GB" if size > 1_000_000_000 else
                    f"{size/1_000_000:.1f} MB"    if size > 1_000_000 else
                    f"{size/1_000:.1f} KB"        if size > 1_000 else
                    f"{size} B"
                )
                print(f"  → {label:<70} [ok  {size_h}  via {profile}]")
                return True
        except Exception as e:
            last_code = type(e).__name__
            time.sleep(1)
            continue

    print(f"  → {label:<70} [FAIL http={last_code}]")
    return False


SLIDESHOW_BASE = "https://www.war.gov/portals/1/Interactive/2026/UFO/Slideshow/"
SLIDES = [
    "FBI-Photo-1.jpg",
    "FBI-Photo-A5.jpg",
    "FBI-Photo-B2.jpg",
    "FBI-Photo-B7-.jpg",
    "FBI-Photo-B18.jpg",
    "FBI-Photo-B20.jpg",
    "2024-04-30-Composite-Sketch.jpg",
    "NASA-UAP-VM6-Apollo-17-1972.jpg",
    "DOW-UAP-PR19-Unresolved-UAP-Report-Middle-East-May-2022.jpg",
    "DOW-UAP-PR26-Unresolved-UAP-Report-United-Arab-Emirates-October-2023.jpg",
    "DOW-UAP-PR34-Unresolved-UAP-Report-Greece-October-2023.jpg",
    "DOW-UAP-PR35-Unresolved-UAP-Report-Greece-October-2023.jpg",
    "DOW-UAP-PR38-Unresolved-UAP-Report-Middle-East-2013.jpg",
    "DOW-UAP-PR43-Unresolved-UAP-Report-Africa-2025.jpg",
    "DOW-UAP-PR45-Unresolved-UAP-Report-Middle-East-2020.jpg",
    "DOW-UAP-PR46-Unresolved-UAP-Report-INDOPACOM-2024.jpg",
    "DOW-UAP-PR49-Unresolved-UAP-Report-Department-of-the-Army-2026.jpg",
]

LOGOS = [
    ("https://www.war.gov/Portals/1/Images/DOD-Icon-Header.png", "DOD-Icon-Header.png"),
    ("https://www.war.gov/Portals/1/Images/DOW-Icon-Header.png", "DOW-Icon-Header.png"),
]

MANIFEST = ("https://www.war.gov/Portals/1/Interactive/2026/UFO/uap-release001.csv",
            "uap-release001.csv")

BUNDLES = [
    ("https://www.war.gov/medialink/ufo/bundle/Release_1.zip", "Release_1.zip"),
    ("https://cdn.dvidshub.net/press/uapvideos.zip",           "uapvideos.zip"),
]


def main():
    print("\n=== Slideshow images (17) ===")
    ok = sum(fetch(SLIDESHOW_BASE + f, SLIDES_DIR / f) for f in SLIDES)
    print(f"  ({ok}/{len(SLIDES)} ok)")

    print("\n=== Site chrome (logos) ===")
    for url, name in LOGOS:
        fetch(url, ASSETS_DIR / name)

    print("\n=== File manifest CSV ===")
    fetch(MANIFEST[0], ROOT / MANIFEST[1])

    print("\n=== Bundles ===")
    print("  (Release_1.zip ≈ docs+imgs; uapvideos.zip ≈ 1.3 GB — be patient)")
    for url, name in BUNDLES:
        fetch(url, BUNDLES_DIR / name)

    print("\n=== Done. Tree: ===")
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and p.name != "download.py":
            rel = p.relative_to(ROOT)
            print(f"  {str(rel):<60} {p.stat().st_size:>14,} B")
    print("\nOpen index.html in a browser to view the offline page.\n")


if __name__ == "__main__":
    main()
