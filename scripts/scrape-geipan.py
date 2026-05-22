#!/usr/bin/env python3
"""Crawl GEIPAN's public case search and cache every case as JSON.

Source: https://www.cnes-geipan.fr/fr/recherche/cas?page=,N
Output: geipan/.cache/cases.json

Politely throttled (0.4 s between requests). Idempotent — re-running
skips pages whose snapshot is already cached.
"""
from __future__ import annotations
import json, os, re, sys, time, html
import urllib.request, urllib.error

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, 'geipan', '.cache')
os.makedirs(CACHE, exist_ok=True)
PAGES_DIR = os.path.join(CACHE, 'pages')
os.makedirs(PAGES_DIR, exist_ok=True)

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
BASE = 'https://www.cnes-geipan.fr'

def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return open(dest, encoding='utf-8').read()
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read().decode('utf-8', errors='replace')
    open(dest, 'w', encoding='utf-8').write(data)
    return data


def parse_listing(htmlsrc):
    """Each case row: title (PAPEETE (987) 12.01.2026), classification, dept, dates, detail-link."""
    cases = []
    # Each case is wrapped in a <tr> or <li>; the detail link is /fr/cas/YYYY-MM-NNNNN
    for m in re.finditer(r'<a[^>]*href="(/fr/cas/[^"]+)"[^>]*>(.*?)</a>(.*?)(?=<a[^>]*href="/fr/cas/|$)', htmlsrc, re.S):
        link, title_inner, rest = m.group(1), m.group(2), m.group(3)
        title = re.sub(r'<[^>]+>', ' ', title_inner)
        title = html.unescape(re.sub(r'\s+', ' ', title)).strip()
        if not title:
            continue
        # Extract classification, dept, update from rest until next case anchor
        block = title + ' ' + re.sub(r'<[^>]+>', ' ', rest)
        block = html.unescape(re.sub(r'\s+', ' ', block)).strip()
        clas = ''
        m_clas = re.search(r'Classification\s*:\s*(D2|D1|A|B|C|D)\b', block)
        if m_clas: clas = m_clas.group(1)
        dept = ''
        m_dept = re.search(r'Département\s*:\s*([^·]+?)\s+Date de mise', block)
        if m_dept: dept = m_dept.group(1).strip()
        upd = ''
        m_upd = re.search(r'Date de mise à jour\s*:\s*(\d{2}/\d{2}/\d{4})', block)
        if m_upd: upd = m_upd.group(1)
        # Title looks like "PAPEETE (987) 12.01.2026"
        m_t = re.match(r'^(.*?)\s*\((\d{1,5})\)\s+(\d{2}\.\d{2}\.\d{4})', title)
        loc = title; dept_code = ''; obs_date = ''
        if m_t:
            loc = m_t.group(1).strip()
            dept_code = m_t.group(2)
            obs_date = m_t.group(3).replace('.', '/')
        case_id = link.rsplit('/', 1)[-1]
        cases.append({
            'id': case_id,
            'url': BASE + link,
            'location': loc,
            'dept_code': dept_code,
            'department': dept,
            'classification': clas,
            'observation_date': obs_date,
            'update_date': upd,
        })
    return cases


def crawl():
    all_cases = []
    seen = set()
    # Each page has 6 cases; total ~3,351 → 559 pages. Probe until we hit empty page.
    last_count = None
    consecutive_empty = 0
    page = 0
    while True:
        url = f'{BASE}/fr/recherche/cas?page=,{page}'
        dest = os.path.join(PAGES_DIR, f'page-{page:04d}.html')
        try:
            htmlsrc = fetch(url, dest)
        except urllib.error.HTTPError as e:
            print(f'  [HTTP {e.code}] page {page}')
            if e.code in (404, 410):
                break
            consecutive_empty += 1
            if consecutive_empty >= 3:
                break
            time.sleep(2); page += 1; continue
        except Exception as e:
            print(f'  [ERR] page {page}: {e}')
            time.sleep(2); consecutive_empty += 1
            if consecutive_empty >= 3: break
            page += 1; continue

        cases = parse_listing(htmlsrc)
        new = [c for c in cases if c['id'] not in seen]
        for c in new:
            seen.add(c['id'])
            all_cases.append(c)

        if not new:
            consecutive_empty += 1
        else:
            consecutive_empty = 0

        if (page % 25) == 0:
            print(f'  page {page:4d}  +{len(new):2d}  total {len(all_cases):5d}')

        if consecutive_empty >= 5:
            print(f'  end at page {page} (5 consecutive empty pages)')
            break

        page += 1
        # Polite throttle — skip for cached pages
        if not (os.path.exists(dest) and os.path.getsize(dest) > 1000 and last_count == len(all_cases)):
            time.sleep(0.4)
        last_count = len(all_cases)

    out_path = os.path.join(CACHE, 'cases.json')
    open(out_path, 'w', encoding='utf-8').write(json.dumps(all_cases, ensure_ascii=False, indent=2))
    print(f'\nwrote {out_path}  ({len(all_cases)} cases)')
    return all_cases


if __name__ == '__main__':
    crawl()
