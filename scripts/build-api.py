#!/usr/bin/env python3
"""Bake the cross-archive static API dump.

Reads every archive's embedded JSON manifest, normalises records to a flat
schema, and writes:

    api/all.json          — every record across every archive (flat)
    api/by-archive.json   — { archiveSlug: [records...] }
    api/stats.json        — totals per archive + grand total
    api/README.md         — consumer docs

GitHub Pages serves static JSON with `Content-Type: application/json` and a
permissive `Access-Control-Allow-Origin: *` header by default, so the dump
is consumable from any origin.

Usage:
    python3 scripts/build-api.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT, 'api')

ARCHIVES = [
    ('wargov',    'War.gov / PURSUE',          'index.html',                'index.html'),
    ('aaro',      'AARO',                      'aaro/index.html',           'aaro/'),
    ('nasa',      'NASA UAP',                  'nasa/index.html',           'nasa/'),
    ('nara',      'NARA',                      'nara/index.html',           'nara/'),
    ('geipan',    'France · GEIPAN',           'geipan/index.html',         'geipan/'),
    ('uk',        'UK · National Archives',    'uk/index.html',             'uk/'),
    ('brazil',    'Brazil · FAB',              'brazil/index.html',         'brazil/'),
    ('chile',     'Chile · SEFAA',             'chile/index.html',          'chile/'),
    ('argentina', 'Argentina · CEFAe',         'argentina/index.html',      'argentina/'),
    ('canada',    'Canada · LAC / Magnet',     'canada/index.html',         'canada/'),
    ('italy',     'Italy · Aeronautica',       'italy/index.html',          'italy/'),
    ('nz',        'NZ · NZDF',                 'nz/index.html',             'nz/'),
    ('peru',      'Peru · OIFAA',              'peru/index.html',           'peru/'),
    ('spain',     'Spain · Ejército del Aire', 'spain/index.html',          'spain/'),
    ('uruguay',   'Uruguay · CRIDOVNI',        'uruguay/index.html',        'uruguay/'),
]

SCRIPT_IDS = ('arch-data', 'archive-manifest')


def load_archive(rel_html: str) -> List[dict]:
    """Return the raw records list for one archive's HTML page."""
    path = os.path.join(ROOT, rel_html)
    if not os.path.exists(path):
        return []
    src = open(path, encoding='utf-8').read()
    m = None
    for sid in SCRIPT_IDS:
        m = re.search(
            r'<script[^>]+id=["\']' + sid + r'["\'][^>]*>([\s\S]*?)</script>',
            src, re.I,
        )
        if m:
            break
    if not m:
        return []
    raw = m.group(1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    # External-pointer (e.g. GEIPAN cases.json split).
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


def normalise(raw: dict, arc_id: str, arc_label: str, arc_dir: str) -> dict:
    """Coerce heterogeneous record shapes into one schema."""
    def g(*keys):
        for k in keys:
            v = raw.get(k)
            if v:
                return v
        return ''
    return {
        'archive':      arc_id,
        'archiveLabel': arc_label,
        'archiveDir':   arc_dir,
        'title':        g('ti', 'title', 'Title'),
        'description':  g('de', 'desc', 'description', 'Description'),
        'agency':       g('ag', 'agency', 'Agency'),
        'category':     g('cat', 'type', 'category', 'Category'),
        'classification': g('cls', 'classification', 'st', 'status', 'Status'),
        'date':         g('date', 't', 'Date', 'year'),
        'region':       g('region', 're', 'Region'),
        'url':          g('u', 'url', 'URL'),
        'src':          g('s', 'src', 'Src'),
        'local':        g('l', 'local', 'Local'),
        'thumb':        g('th', 'thumb'),
        'type':         g('t', 'type', 'Type'),
    }


def main() -> int:
    os.makedirs(API_DIR, exist_ok=True)

    all_records: List[dict] = []
    by_archive: Dict[str, List[dict]] = {}
    counts: Dict[str, int] = {}
    locals_by_arc: Dict[str, int] = {}

    for arc_id, arc_label, rel_html, arc_dir in ARCHIVES:
        raw = load_archive(rel_html)
        recs = [normalise(r, arc_id, arc_label, arc_dir) for r in raw]
        by_archive[arc_id] = recs
        counts[arc_id] = len(recs)
        locals_by_arc[arc_id] = sum(1 for r in recs if r.get('local'))
        all_records.extend(recs)
        local_pct = 0 if not recs else round(locals_by_arc[arc_id] * 100 / len(recs), 1)
        print(f'  {arc_id:12s} {len(recs):5d} records ({locals_by_arc[arc_id]:4d} local · {local_pct:5.1f}%)')

    grand_total = len(all_records)
    meta = {
        'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'totalRecords': grand_total,
        'totalArchives': len(ARCHIVES),
        'license': 'See per-archive source jurisdictions on https://realufo.org/',
        'docs': 'https://realufo.org/api/',
    }
    stats = {
        '_meta': meta,
        'perArchive': [
            {
                'id': a,
                'label': lab,
                'count': counts[a],
                'local': locals_by_arc[a],
                'localPct': round(locals_by_arc[a] * 100 / counts[a], 1) if counts[a] else 0.0,
                'sourceOnly': counts[a] - locals_by_arc[a],
                'release': f'{a}-v1' if a not in ('wargov',) else 'pdfs-v1',
            }
            for a, lab, _, _ in ARCHIVES
        ],
        'totals': {
            'records': sum(counts.values()),
            'local':   sum(locals_by_arc.values()),
            'archives': len(ARCHIVES),
        },
    }

    # Persist
    with open(os.path.join(API_DIR, 'all.json'), 'w', encoding='utf-8') as f:
        json.dump({'_meta': meta, 'records': all_records}, f,
                  ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(API_DIR, 'by-archive.json'), 'w', encoding='utf-8') as f:
        json.dump({'_meta': meta, 'archives': by_archive}, f,
                  ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(API_DIR, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # README
    readme = (
        '# realufo.org static API\n\n'
        f'Generated: {meta["generatedAt"]}  \n'
        f'Total records: **{grand_total:,}**  \n'
        f'Total archives: **{len(ARCHIVES)}**\n\n'
        '## Endpoints\n\n'
        '| File | Shape | Use case |\n'
        '| --- | --- | --- |\n'
        '| [`all.json`](all.json) | `{_meta, records: [...]}` | Every record across every archive. |\n'
        '| [`by-archive.json`](by-archive.json) | `{_meta, archives: {slug: [...]}}` | Group by archive. |\n'
        '| [`stats.json`](stats.json) | `{_meta, perArchive: [...]}` | Counts only, low bandwidth. |\n\n'
        '## Record schema\n\n'
        '```json\n'
        '{\n'
        '  "archive": "aaro",\n'
        '  "archiveLabel": "AARO",\n'
        '  "archiveDir": "aaro/",\n'
        '  "title": "...",\n'
        '  "description": "...",\n'
        '  "agency": "...",\n'
        '  "category": "...",\n'
        '  "classification": "...",\n'
        '  "date": "...",\n'
        '  "region": "...",\n'
        '  "url": "https://...",\n'
        '  "src": "https://...",\n'
        '  "local": "pdfs/whatever.pdf",\n'
        '  "thumb": "https://...",\n'
        '  "type": "PDF"\n'
        '}\n'
        '```\n\n'
        '## Licensing\n\n'
        'Each record inherits the licence of its source jurisdiction\n'
        '(US 17 U.S.C. §105, UK OGL v3, France Loi 78-753, Brazil LAI 12.527,\n'
        'Chile 20.285, etc.). See the matching archive page for the canonical\n'
        'source URL of any record.\n\n'
        '## CORS\n\n'
        'GitHub Pages serves these files with `Access-Control-Allow-Origin: *`.\n'
    )
    with open(os.path.join(API_DIR, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(readme)

    print(f'\n→ wrote api/all.json ({grand_total:,} records)')
    print('→ wrote api/by-archive.json')
    print('→ wrote api/stats.json')
    print('→ wrote api/README.md')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
