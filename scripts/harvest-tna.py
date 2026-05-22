#!/usr/bin/env python3
"""Harvest UK National Archives Discovery API for UFO/UAP catalog records.

API: https://discovery.nationalarchives.gov.uk/API/search/v1/records
Each record → CATALOG entry with deep-link to discovery.nationalarchives.gov.uk/details/r/{id}

Writes: uk/.cache/tna-index.json   (consumed by build-uk.py)
"""
from __future__ import annotations
import json, os, sys, time, urllib.request, urllib.parse

REPO  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, 'uk', '.cache')
os.makedirs(CACHE, exist_ok=True)

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

QUERIES = [
    ('UFO', 'general UFO records'),
    ('unidentified flying object', 'unidentified flying object full-text'),
    ('unidentified aerial phenomena', 'UAP terminology'),
    ('DEFE 24', 'MoD UFO Desk series'),
    ('AIR 20 flying saucer', 'Flying Saucer Working Party 1951'),
    ('Rendlesham', 'Rendlesham Forest 1980'),
    ('Project Condign', 'Project Condign report'),
    ('flying saucer', 'pre-UFO terminology'),
]

API = 'https://discovery.nationalarchives.gov.uk/API/search/v1/records'
PAGE_SIZE = 100


def search(q: str, page: int = 0) -> dict:
    params = {
        'sps.searchQuery': q,
        'sps.recordCollections': 'Records',
        'sps.resultsPageSize': str(PAGE_SIZE),
        'sps.page': str(page),
    }
    url = API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def harvest() -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []

    for q, label in QUERIES:
        print(f'→ "{q}" — {label}')
        page = 0
        total = None
        while True:
            try:
                d = search(q, page)
            except Exception as e:
                print(f'  [ERR p{page}] {e}'); break
            recs = d.get('records', [])
            if total is None:
                total = d.get('count', 0)
                print(f'  total available: {total}')
            if not recs:
                break
            for r in recs:
                rid = r.get('id', '')
                if not rid or rid in seen:
                    continue
                seen.add(rid)
                title = (r.get('title') or '').strip() or (r.get('description', '')[:120]).strip()
                if not title:
                    continue
                ref   = r.get('citableReference') or ''
                dates = r.get('coveringDates') or ''
                ctx   = (r.get('context') or '').strip()
                dept  = r.get('department') or ''
                heldBy = (r.get('heldBy') or [''])[0] if isinstance(r.get('heldBy'), list) else (r.get('heldBy') or '')
                desc_bits = []
                if ctx: desc_bits.append(ctx)
                if heldBy: desc_bits.append(f'Held by {heldBy}.')
                if ref: desc_bits.append(f'Reference {ref}.')
                desc = ' '.join(desc_bits).strip()[:500]
                out.append({
                    'id': rid,
                    'title': f'{ref} — {title}' if ref else title,
                    'url':   f'https://discovery.nationalarchives.gov.uk/details/r/{rid}',
                    'date':  dates,
                    'desc':  desc,
                    'department': dept,
                    'query': q,
                })
            page += 1
            if page * PAGE_SIZE >= (total or 0):
                break
            if page * PAGE_SIZE > 500:    # cap per query
                break
            time.sleep(0.5)

    out_path = os.path.join(CACHE, 'tna-index.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f'\nWrote {out_path}  ({len(out)} records)')
    return out


if __name__ == '__main__':
    harvest()
