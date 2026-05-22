#!/usr/bin/env python3
"""Generate per-archive Open Graph SVG images (1200x630).

Each archive gets a card with:
  • full-bleed radial seal-gradient background
  • centered classic-disk UFO silhouette + archive name + tagline
  • realufo.org wordmark

Output:
  <slug>/assets/og.svg

The script also rewrites the og:image / twitter:image meta tags on each
archive's index.html to point at the new file. PNG rasterisation is a
follow-up; modern scrapers (Slack, Discord, Telegram, X/Twitter, LinkedIn
preview cards) handle SVG. Facebook still wants a PNG; CI can run
`rsvg-convert` to produce a `og.png` sibling.

Usage:
    python3 scripts/build-og.py
"""
from __future__ import annotations

import os
import re
import sys
from textwrap import dedent

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tone colour table mirrors CLAUDE.md § 3.1.
ARCHIVES = [
    # (slug, name, tagline, accent,    grad_stops)
    ('wargov',    'War.gov / PURSUE',           'Department of War · Releases 01 + 02',  '#d4a017', ('#b91c1c','#6b1010','#2a0606')),
    ('aaro',      'AARO',                        'All-domain Anomaly Resolution',   '#4a9eff', ('#1e3a8a','#102560','#061238')),
    ('nasa',      'NASA UAP',                    'Independent Study Team',          '#fc3d21', ('#fc3d21','#a01818','#400606')),
    ('nara',      'NARA',                        'Project Blue Book · JFK · UAP',   '#cbd5e1', ('#9ca3af','#4b5563','#1f2937')),
    ('geipan',    'GEIPAN',                      'CNES · France',                   '#0055a4', ('#0055a4','#003278','#001f4d')),
    ('uk',        'UK · National Archives',      'MoD UAP files',                   '#012169', ('#012169','#001440','#000820')),
    ('brazil',    'Brazil · FAB',                'Força Aérea Brasileira',          '#009c3b', ('#ffdc00','#009c3b','#002776')),
    ('chile',     'Chile · SEFAA',               'DGAC · Comité de Estudios',       '#d52b1e', ('#d52b1e','#8b1413','#3d0908')),
    ('argentina', 'Argentina · CEFAe',           'Fuerza Aérea Argentina',          '#74acdf', ('#74acdf','#3d6a9c','#1e3a5e')),
    ('canada',    'Canada · LAC',                'Project Magnet',                  '#ff6b6b', ('#ff0000','#990000','#330000')),
    ('italy',     'Italy · Aeronautica',         'Aeronautica Militare',            '#5cb85c', ('#009246','#005a2b','#002612')),
    ('nz',        'NZ · NZDF',                   'NZ Defence Force',                '#5b8def', ('#000000','#333333','#000000')),
    ('peru',      'Peru · OIFAA',                'Fuerza Aérea del Perú',           '#ff6b6b', ('#d91023','#7d0b14','#3a0508')),
    ('spain',     'Spain · Ejército del Aire',   'Ministerio de Defensa',           '#f4c542', ('#aa151b','#700c10','#350608')),
    ('uruguay',   'Uruguay · CRIDOVNI',          'Fuerza Aérea Uruguaya',           '#3ba0d8', ('#3ba0d8','#1e5d80','#0d2c3e')),
]

# 1200x630 Open Graph canvas.
W, H = 1200, 630

OG_TEMPLATE = '''\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <radialGradient id="g" cx="32%" cy="38%" r="80%">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="55%" stop-color="{c2}"/>
      <stop offset="100%" stop-color="{c3}"/>
    </radialGradient>
    <linearGradient id="vignette" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="rgba(10,10,12,0)"/>
      <stop offset="100%" stop-color="rgba(10,10,12,0.55)"/>
    </linearGradient>
  </defs>

  <!-- background -->
  <rect width="{W}" height="{H}" fill="#0a0a0c"/>
  <rect width="{W}" height="{H}" fill="url(#g)" opacity="0.92"/>
  <rect width="{W}" height="{H}" fill="url(#vignette)"/>

  <!-- scanlines -->
  <g opacity="0.07">
    <rect x="0" y="0" width="{W}" height="{H}" fill="url(#scanlines)"/>
  </g>

  <!-- classic disk UFO silhouette, upper-right -->
  <g transform="translate(880,180)" opacity="0.94">
    <ellipse cx="0" cy="40" rx="190" ry="38" fill="#e8e3d8"/>
    <path d="M -80 40 A 80 80 0 0 1 80 40 Z" fill="#e8e3d8"/>
    <ellipse cx="0" cy="60" rx="140" ry="14" fill="#0a0a0c" opacity="0.45"/>
    <rect x="-22" y="14" width="16" height="22" rx="2" fill="#0a0a0c"/>
    <rect x="6"   y="14" width="16" height="22" rx="2" fill="#0a0a0c"/>
    <circle cx="0" cy="68" r="10" fill="{accent}"/>
  </g>

  <!-- wordmark -->
  <text x="80" y="130" fill="{accent}" font-family="JetBrains Mono, ui-monospace, monospace" font-size="20" font-weight="700" letter-spacing="6">REALUFO.ORG</text>

  <!-- name + tagline -->
  <text x="80" y="350" fill="#e8e3d8" font-family="Source Serif 4, Georgia, serif" font-size="84" font-weight="700" letter-spacing="-1">{name_xml}</text>
  <text x="80" y="410" fill="#e8e3d8" font-family="Source Serif 4, Georgia, serif" font-size="34" font-weight="400" opacity="0.78" font-style="italic">{tagline_xml}</text>

  <!-- bottom strip -->
  <line x1="80" y1="540" x2="1120" y2="540" stroke="#e8e3d8" stroke-opacity="0.18"/>
  <text x="80" y="582" fill="#e8e3d8" font-family="JetBrains Mono, ui-monospace, monospace" font-size="18" font-weight="500" letter-spacing="3" opacity="0.86">◉ OFFICIAL GOVERNMENT UAP ARCHIVE</text>
  <text x="1120" y="582" fill="{accent}" font-family="JetBrains Mono, ui-monospace, monospace" font-size="18" font-weight="700" letter-spacing="3" text-anchor="end">{slug_caps}</text>
</svg>
'''


def xml_escape(s: str) -> str:
    return (s.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;').replace('"', '&quot;'))


def write_svg(slug, name, tagline, accent, grad):
    out_dir = os.path.join(ROOT, slug, 'assets')
    if slug == 'wargov':
        out_dir = os.path.join(ROOT, 'assets')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'og.svg')
    body = OG_TEMPLATE.format(
        W=W, H=H,
        c1=grad[0], c2=grad[1], c3=grad[2],
        accent=accent,
        name_xml=xml_escape(name),
        tagline_xml=xml_escape(tagline),
        slug_caps=slug.upper(),
    )
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(body)
    return os.path.relpath(out_path, ROOT)


def rewrite_meta(index_path: str, og_url_abs: str) -> bool:
    if not os.path.exists(index_path):
        return False
    src = open(index_path, encoding='utf-8').read()
    new = re.sub(
        r'(<meta\s+property="og:image"\s+content=")[^"]+(")',
        r'\g<1>' + og_url_abs + r'\g<2>', src, count=1,
    )
    new = re.sub(
        r'(<meta\s+name="twitter:image"\s+content=")[^"]+(")',
        r'\g<1>' + og_url_abs + r'\g<2>', new, count=1,
    )
    if new == src:
        return False
    open(index_path, 'w', encoding='utf-8').write(new)
    return True


def main() -> int:
    for slug, name, tagline, accent, grad in ARCHIVES:
        rel = write_svg(slug, name, tagline, accent, grad)
        # Rewrite the matching index.html's og:image / twitter:image
        if slug == 'wargov':
            idx = os.path.join(ROOT, 'index.html')
            og_abs = 'https://realufo.org/assets/og.svg'
        else:
            idx = os.path.join(ROOT, slug, 'index.html')
            og_abs = f'https://realufo.org/{slug}/assets/og.svg'
        changed = rewrite_meta(idx, og_abs)
        flag = '✓' if changed else '·'
        print(f'  {slug:12s} wrote {rel:30s}  meta {flag}')
    print(f'\n→ {len(ARCHIVES)} Open Graph SVGs written and meta tags updated')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
