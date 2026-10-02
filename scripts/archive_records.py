"""Shared record loader for build-api.py + build-feeds.py.

Post-Phase-4 the root `index.html` / `<slug>/index.html` manifests are gone.
Records now live in:
    wargov          uap-data.csv (CSV rows, mapped to short keys below)
    active archives data/<slug>.json → v1.assets
    dormant         legacy/<slug>/index.html embedded manifest
Returns raw dicts using the short-key schema (ti, de, ag, cat, date, u, s, l, …).
"""
from __future__ import annotations

import csv
import json
import os
import re
from typing import List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_IDS = ('arch-data', 'archive-manifest')


def _wargov() -> List[dict]:
    out = []
    with open(os.path.join(ROOT, 'uap-data.csv'), encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if not (r.get('Title') or '').strip():
                continue
            m, d, y = (r.get('Release Date') or '0/0/0').split('/')
            dvids = (r.get('DVIDS Video ID') or '').strip()
            link = (r.get('PDF | Image Link') or '').strip() or (
                f'https://www.dvidshub.net/video/{dvids}' if dvids else '')
            out.append({
                'ti': r['Title'].replace('\xa0', ' ').strip(),
                'de': (r.get('Description Blurb') or '').strip(),
                'ag': (r.get('Agency') or '').strip(),
                'cat': (r.get('Type') or '').strip(),
                'date': f'20{int(y):02d}-{int(m):02d}-{int(d):02d}' if y != '0' else '',
                'region': (r.get('Incident Location') or '').strip(),
                # ponytail: official source link only; R2 mirror URL lives in the Astro
                # build (dist/watchdog.json) — wire it in if API consumers need it.
                'u': link,
                's': link,
            })
    return out


def _data_json(slug: str) -> List[dict]:
    path = os.path.join(ROOT, 'data', f'{slug}.json')
    if not os.path.exists(path):
        return []
    v1 = json.load(open(path, encoding='utf-8')).get('v1') or {}
    return [r for r in v1.get('assets') or [] if isinstance(r, dict)]


def _legacy_html(slug: str) -> List[dict]:
    path = os.path.join(ROOT, 'legacy', slug, 'index.html')
    if not os.path.exists(path):
        return []
    src = open(path, encoding='utf-8').read()
    for sid in SCRIPT_IDS:
        m = re.search(r'<script[^>]+id=["\']' + sid + r'["\'][^>]*>([\s\S]*?)</script>', src, re.I)
        if m:
            break
    else:
        return []
    try:
        data = json.loads(m.group(1).strip())
        if isinstance(data, dict) and data.get('_external'):
            data = json.load(open(os.path.join(os.path.dirname(path), data['_external']), encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(data, dict):
        data = next((data[k] for k in ('assets', 'records', 'rows') if isinstance(data.get(k), list)), [])
    return [r for r in data if isinstance(r, dict)] if isinstance(data, list) else []


def load(slug: str) -> List[dict]:
    if slug == 'wargov':
        return _wargov()
    return _data_json(slug) or _legacy_html(slug)


if __name__ == '__main__':
    counts = {s: len(load(s)) for s in ('wargov', 'aaro', 'nasa', 'nara', 'geipan', 'uk', 'nz', 'uruguay')}
    print(counts)
    assert counts['wargov'] == 450 and counts['aaro'] == 110 and counts['nara'] == 73, counts
    assert all(counts.values()), counts
    assert load('wargov')[-1]['date'] == '2026-09-18'
