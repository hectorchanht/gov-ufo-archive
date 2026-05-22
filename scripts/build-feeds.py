#!/usr/bin/env python3
"""Build Atom feeds per archive.

Reads each archive's manifest and emits an Atom 1.0 feed of the N most-recent
records under `feeds/<slug>.xml`. Records are sorted by parsed date when
present (newest first); otherwise the source order is preserved.

Also emits `feeds/all.xml` — newest records across every archive (top 100).

Usage:
    python3 scripts/build-feeds.py
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import time
import urllib.parse
from typing import Iterable, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDS_DIR = os.path.join(ROOT, 'feeds')
SITE_URL = 'https://realufo.org'
NOW_ISO = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

ARCHIVES = [
    ('wargov',    'War.gov / PURSUE',          'index.html',           '/'),
    ('aaro',      'AARO',                      'aaro/index.html',      '/aaro/'),
    ('nasa',      'NASA UAP',                  'nasa/index.html',      '/nasa/'),
    ('nara',      'NARA',                      'nara/index.html',      '/nara/'),
    ('geipan',    'France · GEIPAN',           'geipan/index.html',    '/geipan/'),
    ('uk',        'UK · National Archives',    'uk/index.html',        '/uk/'),
    ('brazil',    'Brazil · FAB',              'brazil/index.html',    '/brazil/'),
    ('chile',     'Chile · SEFAA',             'chile/index.html',     '/chile/'),
    ('argentina', 'Argentina · CEFAe',         'argentina/index.html', '/argentina/'),
    ('canada',    'Canada · LAC / Magnet',     'canada/index.html',    '/canada/'),
    ('italy',     'Italy · Aeronautica',       'italy/index.html',     '/italy/'),
    ('nz',        'NZ · NZDF',                 'nz/index.html',        '/nz/'),
    ('peru',      'Peru · OIFAA',              'peru/index.html',      '/peru/'),
    ('spain',     'Spain · Ejército del Aire', 'spain/index.html',     '/spain/'),
    ('uruguay',   'Uruguay · CRIDOVNI',        'uruguay/index.html',   '/uruguay/'),
]

SCRIPT_IDS = ('arch-data', 'archive-manifest')


# ── helpers ─────────────────────────────────────────────────────────────────
def load_records(rel_html: str) -> List[dict]:
    path = os.path.join(ROOT, rel_html)
    if not os.path.exists(path):
        return []
    src = open(path, encoding='utf-8').read()
    m = None
    for sid in SCRIPT_IDS:
        m = re.search(
            r'<script[^>]+id=["\']' + sid + r'["\'][^>]*>([\s\S]*?)</script>',
            src, re.I)
        if m:
            break
    if not m:
        return []
    try:
        data = json.loads(m.group(1).strip())
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict) and data.get('_external'):
        ext = os.path.join(os.path.dirname(path), data['_external'])
        if os.path.exists(ext):
            try:
                data = json.loads(open(ext, encoding='utf-8').read())
            except json.JSONDecodeError:
                return []
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        for k in ('assets', 'records', 'rows'):
            if isinstance(data.get(k), list):
                return [r for r in data[k] if isinstance(r, dict)]
    return []


def field(r: dict, *keys) -> str:
    for k in keys:
        v = r.get(k)
        if v:
            return str(v)
    return ''


def parse_date(r: dict) -> Optional[str]:
    """Return ISO-8601 best-effort. None if nothing parses."""
    s = field(r, 'date', 't', 'Date', 'year')
    if not s:
        return None
    # YYYY-MM-DD
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})', s)
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}T00:00:00Z'
    # DD/MM/YYYY  or  D/M/YYYY
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})', s)
    if m: return f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}T00:00:00Z'
    # bare year
    m = re.match(r'^(1[89]\d{2}|20\d{2}|21\d{2})$', s.strip())
    if m: return f'{m.group(1)}-01-01T00:00:00Z'
    # year embedded
    m = re.search(r'\b(1[89]\d{2}|20\d{2}|21\d{2})\b', s)
    if m: return f'{m.group(1)}-01-01T00:00:00Z'
    return None


def absolute_url(maybe_url: str, base_dir: str) -> str:
    if not maybe_url: return ''
    if maybe_url.startswith(('http://', 'https://')): return maybe_url
    # local path → join with archive dir under site
    base = SITE_URL + base_dir if base_dir.startswith('/') else SITE_URL + '/' + base_dir
    return urllib.parse.urljoin(base, maybe_url)


# ── feed writer ─────────────────────────────────────────────────────────────
def write_feed(slug: str, title: str, records: List[dict], arc_dir: str,
               out_path: str, limit: int = 50) -> None:
    """Render an Atom 1.0 feed."""
    # Sort newest-first when dates available; preserve order otherwise.
    decorated = []
    for i, r in enumerate(records):
        decorated.append((parse_date(r) or '0000', -i, r))
    decorated.sort(reverse=True)
    keep = [r for _, _, r in decorated[:limit]]

    feed_url = f'{SITE_URL}/feeds/{slug}.xml'
    site_url = f'{SITE_URL}{arc_dir}' if arc_dir.startswith('/') else SITE_URL + '/' + arc_dir
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f'  <title>realufo.org — {html.escape(title)}</title>',
        f'  <subtitle>Latest declassified records mirrored from {html.escape(title)}.</subtitle>',
        f'  <id>{feed_url}</id>',
        f'  <link rel="self" type="application/atom+xml" href="{feed_url}"/>',
        f'  <link rel="alternate" type="text/html" href="{site_url}"/>',
        f'  <updated>{NOW_ISO}</updated>',
        '  <author><name>realufo.org</name><uri>https://realufo.org/</uri></author>',
        '  <rights>Per-source jurisdiction (US 17 U.S.C. §105, UK OGL v3, France Loi 78-753, Brazil LAI 12.527, Chile 20.285, etc.)</rights>',
        f'  <generator uri="{SITE_URL}/">realufo.org build-feeds.py</generator>',
    ]
    for r in keep:
        title_t = html.escape(field(r, 'ti', 'title', 'Title') or '(Untitled)')
        desc = field(r, 'de', 'desc', 'description', 'Description')
        cat = field(r, 'cat', 'type', 'category', 't', 'Type')
        date_iso = parse_date(r) or NOW_ISO
        local = field(r, 'l', 'local', 'Local')
        ext = field(r, 'u', 'url', 'URL')
        src = field(r, 's', 'src', 'Src')
        link = absolute_url(local, arc_dir) if local else (
            ext if ext.startswith('http') else (src if src.startswith('http') else site_url)
        )
        if not link:
            link = site_url
        # Deterministic id
        seed = f'{slug}|{title_t}|{date_iso}|{link}'
        eid = f'tag:realufo.org,2026:{slug}/{abs(hash(seed)) % (10**12):012d}'
        out.append('  <entry>')
        out.append(f'    <id>{eid}</id>')
        out.append(f'    <title>{title_t}</title>')
        out.append(f'    <link rel="alternate" type="text/html" href="{html.escape(link)}"/>')
        if src and src.startswith('http') and src != link:
            out.append(f'    <link rel="via" href="{html.escape(src)}"/>')
        out.append(f'    <updated>{date_iso}</updated>')
        out.append(f'    <published>{date_iso}</published>')
        if cat:
            out.append(f'    <category term="{html.escape(cat)}"/>')
        out.append(f'    <category term="{html.escape(title)}"/>')
        if desc:
            out.append('    <summary type="text">' + html.escape(desc[:600]) + '</summary>')
        out.append('  </entry>')
    out.append('</feed>')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))


def main() -> int:
    os.makedirs(FEEDS_DIR, exist_ok=True)

    all_records: List[tuple] = []     # (slug, dir, record)
    written = []
    for slug, label, rel_html, arc_dir in ARCHIVES:
        recs = load_records(rel_html)
        if not recs:
            print(f'  {slug:12s}    empty — skipping')
            continue
        out_path = os.path.join(FEEDS_DIR, f'{slug}.xml')
        write_feed(slug, label, recs, arc_dir, out_path, limit=50)
        sz = os.path.getsize(out_path)
        print(f'  {slug:12s} {len(recs):5d} records → {os.path.relpath(out_path)} ({sz:,} bytes)')
        written.append(slug)
        for r in recs:
            all_records.append((slug, arc_dir, r))

    # Combined firehose feed — top 100 across everything by date.
    decorated = []
    for i, (slug, arc_dir, r) in enumerate(all_records):
        decorated.append((parse_date(r) or '0000', -i, slug, arc_dir, r))
    decorated.sort(reverse=True)
    all_path = os.path.join(FEEDS_DIR, 'all.xml')
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        '  <title>realufo.org — every archive, latest records</title>',
        '  <subtitle>Cross-archive Atom feed of the 100 most recent declassified UAP records across 15 government sources.</subtitle>',
        f'  <id>{SITE_URL}/feeds/all.xml</id>',
        f'  <link rel="self" type="application/atom+xml" href="{SITE_URL}/feeds/all.xml"/>',
        f'  <link rel="alternate" type="text/html" href="{SITE_URL}/"/>',
        f'  <updated>{NOW_ISO}</updated>',
        '  <author><name>realufo.org</name><uri>https://realufo.org/</uri></author>',
    ]
    for _, _, slug, arc_dir, r in decorated[:100]:
        title_t = html.escape(field(r, 'ti', 'title') or '(Untitled)')
        date_iso = parse_date(r) or NOW_ISO
        local = field(r, 'l', 'local')
        ext = field(r, 'u', 'url'); src = field(r, 's', 'src')
        link = absolute_url(local, arc_dir) if local else (
            ext if ext.startswith('http') else (src if src.startswith('http') else SITE_URL + arc_dir)
        )
        eid = f'tag:realufo.org,2026:{slug}/{abs(hash(title_t+link)) % (10**12):012d}'
        out.append('  <entry>')
        out.append(f'    <id>{eid}</id>')
        out.append(f'    <title>{title_t}</title>')
        out.append(f'    <link rel="alternate" type="text/html" href="{html.escape(link)}"/>')
        out.append(f'    <updated>{date_iso}</updated>')
        out.append(f'    <published>{date_iso}</published>')
        out.append(f'    <category term="{slug}"/>')
        desc = field(r, 'de', 'desc', 'description')
        if desc:
            out.append('    <summary type="text">' + html.escape(desc[:400]) + '</summary>')
        out.append('  </entry>')
    out.append('</feed>')
    with open(all_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print(f'\n→ feeds/all.xml ({os.path.getsize(all_path):,} bytes)')
    print(f'→ {len(written)} per-archive feeds written')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
