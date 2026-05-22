#!/usr/bin/env python3
"""Dead-source health check.

Crawls every embedded manifest (script#arch-data) across all archive HTML
pages, extracts every distinct external URL (`s`, `u`, `src`, `url` fields),
HEAD-requests each one with a realistic Chrome UA, and records the result.

Emits two files in the repo root:

    dead-links.json   — full results: { url: {status, ms, host, reachedAt}, ... }
    dead-links.md     — human-readable summary, grouped by archive

Usage:
    python3 scripts/check-sources.py                # all archives
    python3 scripts/check-sources.py aaro uk        # only specified archives
    python3 scripts/check-sources.py --concurrency 16

Exit codes:
    0  every URL reachable
    1  one or more URLs are dead (non-2xx / non-3xx)
    2  fatal crawler error
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Set, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UA = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 '
    '(KHTML, like Gecko) Version/17.5 Safari/605.1.15'
)
TIMEOUT = 12

ARCHIVE_HTML: Dict[str, List[str]] = {
    'wargov':    ['index.html'],
    'aaro':      ['aaro/index.html', 'aaro/details.html',
                  'aaro/tic-tac.html', 'aaro/gimbal.html'],
    'nasa':      ['nasa/index.html'],
    'nara':      ['nara/index.html'],
    'geipan':    ['geipan/index.html'],
    'uk':        ['uk/index.html', 'uk/rendlesham.html'],
    'brazil':    ['brazil/index.html', 'brazil/operacao-prato.html',
                  'brazil/varginha.html'],
    'chile':     ['chile/index.html'],
    'argentina': ['argentina/index.html'],
    'canada':    ['canada/index.html'],
    'italy':     ['italy/index.html'],
    'nz':        ['nz/index.html'],
    'peru':      ['peru/index.html'],
    'spain':     ['spain/index.html'],
    'uruguay':   ['uruguay/index.html'],
}

URL_FIELDS = ('s', 'src', 'u', 'url')
SCRIPT_RE = re.compile(
    r'<script[^>]+id=["\']arch-data["\'][^>]*>([\s\S]*?)</script>', re.I
)


# ── manifest extraction ─────────────────────────────────────────────────────
def load_manifest(html_path: str) -> List[dict]:
    """Return the flat list of asset records embedded in this HTML page."""
    if not os.path.exists(html_path):
        return []
    src = open(html_path, encoding='utf-8').read()
    m = SCRIPT_RE.search(src)
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw or raw.startswith('{'):
        pass
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    # If the page uses _external pointer, follow it.
    if isinstance(data, dict) and data.get('_external'):
        ext = os.path.join(os.path.dirname(html_path), data['_external'])
        if os.path.exists(ext):
            try:
                data = json.loads(open(ext, encoding='utf-8').read())
            except json.JSONDecodeError:
                return []
    if isinstance(data, dict):
        records = data.get('assets') or data.get('records') or data.get('rows') or []
    elif isinstance(data, list):
        records = data
    else:
        records = []
    return [r for r in records if isinstance(r, dict)]


def extract_urls(records: List[dict]) -> Set[str]:
    out: Set[str] = set()
    for r in records:
        for f in URL_FIELDS:
            v = r.get(f) or ''
            if isinstance(v, str) and v.startswith(('http://', 'https://')):
                out.add(v.strip())
    return out


# ── HEAD-request worker ─────────────────────────────────────────────────────
def check_one(url: str) -> dict:
    t0 = time.monotonic()
    host = urllib.parse.urlparse(url).netloc or '?'
    req = urllib.request.Request(url, method='HEAD', headers={
        'User-Agent': UA,
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.8',
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.status
            reached = resp.url
        ok = 200 <= status < 400
    except urllib.error.HTTPError as e:
        status, ok, reached = e.code, False, url
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        status, ok, reached = 0, False, str(e)[:120]
    ms = int((time.monotonic() - t0) * 1000)
    return {'url': url, 'status': status, 'ok': ok, 'ms': ms,
            'host': host, 'reachedAt': reached}


# ── main ────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('archives', nargs='*', help='archive slugs to check (default: all)')
    ap.add_argument('--concurrency', type=int, default=12)
    ap.add_argument('--out-json', default='dead-links.json')
    ap.add_argument('--out-md', default='dead-links.md')
    args = ap.parse_args()

    slugs = args.archives or list(ARCHIVE_HTML)
    print(f'Checking {len(slugs)} archive(s) at concurrency={args.concurrency}')

    per_archive: Dict[str, Set[str]] = {}
    for slug in slugs:
        urls: Set[str] = set()
        for rel in ARCHIVE_HTML.get(slug, []):
            urls |= extract_urls(load_manifest(os.path.join(ROOT, rel)))
        per_archive[slug] = urls
        print(f'  {slug:12s} {len(urls):5d} urls')

    all_urls: Set[str] = set().union(*per_archive.values())
    print(f'\nTotal distinct URLs: {len(all_urls)}\n')

    results: Dict[str, dict] = {}
    bad: List[Tuple[str, dict]] = []
    t0 = time.monotonic()
    with cf.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {ex.submit(check_one, u): u for u in sorted(all_urls)}
        done = 0
        for fut in cf.as_completed(futures):
            res = fut.result()
            results[res['url']] = res
            done += 1
            if not res['ok']:
                bad.append((res['url'], res))
            if done % 25 == 0 or done == len(futures):
                print(f'  [{done}/{len(futures)}] dead={len(bad)}')
    elapsed = time.monotonic() - t0

    # Persist
    summary = {
        'checkedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'total': len(all_urls),
        'dead': len(bad),
        'durationSec': round(elapsed, 1),
        'results': results,
    }
    with open(os.path.join(ROOT, args.out_json), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    with open(os.path.join(ROOT, args.out_md), 'w', encoding='utf-8') as f:
        f.write(f'# Source health — {summary["checkedAt"]}\n\n')
        f.write(f'- **Total URLs checked:** {summary["total"]}\n')
        f.write(f'- **Dead:** {summary["dead"]}\n')
        f.write(f'- **Took:** {summary["durationSec"]} s\n\n')
        for slug in slugs:
            urls = per_archive[slug]
            arc_bad = [(u, results[u]) for u in urls if not results[u]['ok']]
            f.write(f'## {slug} — {len(arc_bad)}/{len(urls)} dead\n\n')
            if not arc_bad:
                f.write('All reachable.\n\n')
                continue
            for u, r in sorted(arc_bad):
                f.write(f'- `{r["status"]}` [{r["host"]}]({u}) — {r["reachedAt"]}\n')
            f.write('\n')

    print(f'\nWrote {args.out_json} + {args.out_md}')
    print(f'{summary["dead"]} dead of {summary["total"]} ({summary["dead"]/max(1,summary["total"])*100:.1f}%)')
    return 1 if bad else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f'fatal: {e}', file=sys.stderr)
        sys.exit(2)
