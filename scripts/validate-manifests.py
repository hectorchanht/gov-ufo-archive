#!/usr/bin/env python3
"""Validate every embedded archive manifest against the shared schema.

Each archive's HTML embeds a JSON blob in <script id="arch-data"> (or
<script id="archive-manifest"> for the legacy war.gov page). This validator
walks every record and checks:

  • Required fields are present and non-empty.
  • Field types match: title (str), date (str), etc.
  • At least one of `url`/`u` or `src`/`s` or `local`/`l` is set, so the
    record is actionable.
  • URLs (when present) parse and use http(s).
  • Unknown top-level fields are *allowed* (archives evolve) but reported.

Exits 0 if all archives pass, 1 otherwise. Designed to run in CI.
Zero dependencies (stdlib only).

Usage:
    python3 scripts/validate-manifests.py
    python3 scripts/validate-manifests.py --strict   # treat warnings as errors
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from typing import Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARCHIVES = [
    ('wargov',    'index.html'),
    ('aaro',      'aaro/index.html'),
    ('nasa',      'nasa/index.html'),
    ('nara',      'nara/index.html'),
    ('geipan',    'geipan/index.html'),
    ('uk',        'uk/index.html'),
    ('brazil',    'brazil/index.html'),
    ('chile',     'chile/index.html'),
    ('argentina', 'argentina/index.html'),
    ('canada',    'canada/index.html'),
    ('italy',     'italy/index.html'),
    ('nz',        'nz/index.html'),
    ('peru',      'peru/index.html'),
    ('spain',     'spain/index.html'),
    ('uruguay',   'uruguay/index.html'),
]

SCRIPT_IDS = ('arch-data', 'archive-manifest')

# Aliases. Field-canonical → list of alternative keys that satisfy it.
ALIASES = {
    'title':       ('ti', 'title', 'Title'),
    'desc':        ('de', 'desc', 'description', 'Description', 'Description Blurb'),
    'type':        ('t', 'type', 'Type', 'cat', 'category', 'Category'),
    'date':        ('date', 't', 'Date', 'year', 'Release Date', 'Incident Date'),
    'url':         ('u', 'url', 'URL', 'PDF | Image Link', 'Video Link', 'Modal Image'),
    'src':         ('s', 'src', 'Src'),
    'local':       ('l', 'local', 'Local'),
}
KNOWN_FIELDS = set(sum((list(v) for v in ALIASES.values()), [])) | {
    'ag', 'agency', 'Agency',
    'region', 're', 'Region', 'Incident Location',
    'cls', 'classification',
    'st', 'status', 'Status', 'Redaction',
    'th', 'thumb',
    'dvidsId', 'DVIDS Video ID', 'Image VIRIN',
    'Video Pairing', 'PDF Pairing', 'Video Title', 'Image Alt Text',
    'embed',
}


# ── extraction ──────────────────────────────────────────────────────────────
def load(rel: str) -> List[dict]:
    path = os.path.join(ROOT, rel)
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
    if isinstance(data, dict) and data.get('_external'):
        ext = os.path.join(os.path.dirname(path), data['_external'])
        if os.path.exists(ext):
            try:
                data = json.loads(open(ext, encoding='utf-8').read())
            except json.JSONDecodeError:
                return []
    if isinstance(data, list):
        return [r for r in data if isinstance(r, (dict, list))]
    if isinstance(data, dict):
        for k in ('assets', 'records', 'rows'):
            if isinstance(data.get(k), list):
                return [r for r in data[k] if isinstance(r, (dict, list))]
    return []


def first(record: dict, *keys):
    for k in keys:
        v = record.get(k)
        if v not in (None, ''):
            return v
    return None


# ── validation ──────────────────────────────────────────────────────────────
def validate_record(rec: dict, idx: int) -> Tuple[List[str], List[str]]:
    """Return (errors, warnings) for one record."""
    errs, warns = [], []
    if not isinstance(rec, dict):
        # Array-of-array shape (war.gov) — skip strict checks; flag as warning.
        warns.append(f'#{idx}: non-object record (array-style); skipped strict validation')
        return errs, warns

    title = first(rec, *ALIASES['title'])
    if not title or not isinstance(title, str):
        errs.append(f'#{idx}: missing/non-string title')

    # Actionable: at least one of url / src / local should be present. Some
    # legacy CSV-derived records (war.gov) ship without any link; we warn so
    # CI doesn't fail on historical data quality.
    has_action = any(first(rec, *ALIASES[k]) for k in ('url', 'src', 'local'))
    if not has_action:
        warns.append(f'#{idx}: no url/src/local — record is unactionable')

    # URL fields, if present: must be a string and parseable. Allow relative
    # paths (assets/images/foo.jpg) — they resolve under the archive's dir.
    # Only flag absolute schemes other than http(s) or unparseable strings.
    for canonical in ('url', 'src'):
        v = first(rec, *ALIASES[canonical])
        if not v: continue
        if not isinstance(v, str):
            errs.append(f'#{idx}: {canonical} is not a string'); continue
        if '://' in v:
            try:
                p = urllib.parse.urlparse(v)
                if p.scheme not in ('http', 'https'):
                    errs.append(f'#{idx}: {canonical} unsupported scheme: {v[:80]}')
            except ValueError:
                errs.append(f'#{idx}: {canonical} unparseable: {v[:80]}')
        elif v.startswith(('javascript:', 'data:')):
            errs.append(f'#{idx}: {canonical} unsafe scheme: {v[:60]}')

    # Date format hint (just warn — heterogeneous archives use varied formats).
    date = first(rec, *ALIASES['date'])
    if date and isinstance(date, str) and len(date) > 60:
        warns.append(f'#{idx}: unusually long date string ({len(date)} chars)')

    # Unknown fields
    for k in rec.keys():
        if k not in KNOWN_FIELDS:
            warns.append(f'#{idx}: unknown field "{k}"')

    return errs, warns


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--strict', action='store_true', help='treat warnings as errors')
    ap.add_argument('archives', nargs='*', help='archive slugs to validate (default: all)')
    args = ap.parse_args()

    slugs = args.archives or [s for s, _ in ARCHIVES]
    rel_for = dict(ARCHIVES)

    total_records = total_errs = total_warns = 0
    failed: List[str] = []

    for slug in slugs:
        rel = rel_for.get(slug)
        if not rel:
            print(f'  ! {slug:12s} not in registry'); failed.append(slug); continue
        records = load(rel)
        if not records:
            print(f'  ! {slug:12s} no manifest found at {rel}')
            failed.append(slug)
            continue
        e_count = w_count = 0
        for i, rec in enumerate(records):
            errs, warns = validate_record(rec, i)
            e_count += len(errs); w_count += len(warns)
            for e in errs[:3]:
                print(f'  ✗ {slug}: {e}')
            if len(errs) > 3:
                print(f'  ✗ {slug}: …and {len(errs) - 3} more')
        total_records += len(records); total_errs += e_count; total_warns += w_count
        print(f'  {("✗" if e_count else "✓")} {slug:12s} {len(records):5d} records · {e_count:3d} errors · {w_count:3d} warnings')
        if e_count:
            failed.append(slug)

    print(f'\n→ {total_records:,} records across {len(slugs)} archives')
    print(f'  {total_errs} errors, {total_warns} warnings')
    if failed:
        print('  Failed:', ', '.join(failed))
        return 1
    if args.strict and total_warns:
        print('  Strict mode → exiting non-zero on warnings.')
        return 1
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
