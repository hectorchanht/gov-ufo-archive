#!/usr/bin/env python3
"""Crawl archives.gov and related NARA pages for all UAP/UFO records.

Writes: nara/.cache/scraped-index.json
Each record: { title, url, src, type, date, desc, agency }

Read-only — no files are downloaded.
"""
from __future__ import annotations
import json, os, re, time, html, urllib.request, urllib.error, urllib.parse

REPO  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, 'nara', '.cache')
os.makedirs(CACHE, exist_ok=True)
PAGES_DIR = os.path.join(CACHE, 'scrape-pages')
os.makedirs(PAGES_DIR, exist_ok=True)

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

# UAP-relevant entry points on archives.gov
SEED_URLS = [
    'https://www.archives.gov/research/pentagon-papers',
    'https://www.archives.gov/research/military/uap',
    'https://catalog.archives.gov/search?q=%22UAP%22&availableOnline=true',
    'https://catalog.archives.gov/search?q=%22unidentified+aerial+phenomena%22&availableOnline=true',
    'https://catalog.archives.gov/search?q=%22UFO%22+%22classified%22&availableOnline=true&levelOfDescription=item',
    'https://www.archives.gov/declassification/iscap/uap',
]

KNOWN_RECORDS = [
    ('CATALOG', 'Project Blue Book (NARA RG 341)',
     'https://catalog.archives.gov/id/182466',
     'US Air Force Project Blue Book records — the primary historical UAP file (1947–1969).', '1947-1969'),
    ('CATALOG', 'CIA Robertson Panel Report (1953)',
     'https://www.cia.gov/readingroom/docs/DOC_0000015458.pdf',
     'Declassified CIA Scientific Advisory Panel on Unidentified Flying Objects report.', 'Jan 1953'),
    ('CATALOG', 'NSA FOIA Reading Room — UFO/UAP Documents',
     'https://www.nsa.gov/Portals/75/documents/news-features/declassified-documents/ufo/',
     'NSA declassified UFO/UAP documents collection — over 1,500 pages.', ''),
    ('PDF', 'UAP Disclosure Act — NARA Implementation Guidance',
     'https://www.archives.gov/about/laws/uap-disclosure-act.html',
     'NARA guidance on implementation of the UAP Disclosure Act of 2023.', '2024'),
    ('CATALOG', 'NARA ARC — Aerial Phenomena Records',
     'https://catalog.archives.gov/search?q=%22unidentified+aerial%22&resultTypes=item',
     'NARA Archival Research Catalog search for aerial phenomena records.', ''),
    ('PDF', 'Twining Memo — 1947 (AFB Roswell)',
     'https://www.archives.gov/files/research/military/air-force/twining-memo-1947.pdf',
     'Lt. Gen. Nathan Twining memo on "Flying Discs" — first official USAF documentation.', 'Sep 1947'),
    ('CATALOG', 'RG 255 — NASA Historical Records',
     'https://catalog.archives.gov/id/566916',
     'NASA historical records at NARA including early aerospace observations.', ''),
    ('CATALOG', 'RG 330 — Office of Secretary of Defense UAP files',
     'https://catalog.archives.gov/search?q=%22UAP%22&recordGroupNumber=330',
     'OSD records including UAP-related correspondence and analysis.', ''),
    ('PDF', 'ISCAP Appeal Decision — UAP Classification Challenges',
     'https://www.archives.gov/declassification/iscap/decisions.html',
     'ISCAP decisions on UAP-related declassification challenges.', ''),
    ('CATALOG', 'NARA FOIA Reading Room — UAP',
     'https://www.archives.gov/research/request-records/foia/reading-room',
     'NARA FOIA Electronic Reading Room with UAP-relevant records.', ''),
]


def fetch(url: str, cache_path: str) -> str:
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 200:
        return open(cache_path, encoding='utf-8').read()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode('utf-8', errors='replace')
        open(cache_path, 'w', encoding='utf-8').write(data)
        time.sleep(0.5)
        return data
    except Exception as e:
        print(f'  [ERR] {url}: {e}')
        return ''


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r'<[^>]+>', ' ', s or '')).strip()


def normalise(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def extract_docs(html_src: str, page_url: str) -> list[dict]:
    records = []
    seen = set()

    # PDF links
    for m in re.finditer(r'href="([^"]*\.pdf[^"]*)"', html_src, re.I):
        href = m.group(1)
        if not href.startswith('http'):
            href = urllib.parse.urljoin(page_url, href)
        fn = href.rsplit('/', 1)[-1].split('?')[0]
        if fn in seen:
            continue
        seen.add(fn)
        ctx = html_src[max(0, m.start()-400):m.end()+400]
        title = ''
        for pat in [r'<a[^>]*href="[^"]*\.pdf[^"]*"[^>]*>([^<]{5,120})</a>',
                    r'<h\d[^>]*>([^<]{5,120})</h\d>']:
            tm = re.search(pat, ctx, re.I)
            if tm:
                title = normalise(strip_tags(tm.group(1)))
                break
        if not title:
            title = normalise(urllib.parse.unquote(fn.replace('_', ' ').replace('-', ' ')).rsplit('.', 1)[0])
        records.append({
            'type': 'PDF', 'title': title or fn, 'url': href,
            'src': page_url, 'agency': 'NARA', 'date': '', 'desc': '',
        })

    return records


def crawl() -> list[dict]:
    all_records: list[dict] = []
    seen_urls: set[str] = set()

    # Add curated records first
    for typ, title, url, desc, date in KNOWN_RECORDS:
        if url not in seen_urls:
            seen_urls.add(url)
            all_records.append({'type': typ, 'title': title, 'url': url,
                                 'src': 'https://www.archives.gov/',
                                 'agency': 'NARA', 'date': date, 'desc': desc})

    # Crawl seed pages
    for seed in SEED_URLS:
        print(f'→ {seed}')
        slug = re.sub(r'[^a-z0-9]+', '_', seed.lower().split('//', 1)[-1])[:80]
        cache_path = os.path.join(PAGES_DIR, f'{slug}.html')
        src = fetch(seed, cache_path)
        if not src:
            continue
        for rec in extract_docs(src, seed):
            if rec['url'] not in seen_urls:
                seen_urls.add(rec['url'])
                all_records.append(rec)

    out = os.path.join(CACHE, 'scraped-index.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    print(f'\nWrote {out}  ({len(all_records)} records)')
    return all_records


if __name__ == '__main__':
    crawl()
