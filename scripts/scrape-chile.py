#!/usr/bin/env python3
"""Crawl DGAC/SEFAA (Chile) UAP disclosure pages.

Writes: chile/.cache/scraped-index.json
Each record: { title, url, src, type, date, desc, agency }

Read-only — no files are downloaded.
"""
from __future__ import annotations
import json, os, re, time, html, urllib.request, urllib.error, urllib.parse

REPO  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, 'chile', '.cache')
os.makedirs(CACHE, exist_ok=True)
PAGES_DIR = os.path.join(CACHE, 'scrape-pages')
os.makedirs(PAGES_DIR, exist_ok=True)

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

SEED_URLS = [
    'https://www.dgac.gob.cl/seguridad-aerea/fenomenos-aereos-anormales/',
    'https://www.dgac.gob.cl/informes-sefaa/',
]

KNOWN_RECORDS = [
    ('PDF', 'CEFAA Annual Report 2019 — Fenómenos Aéreos Anormales',
     'https://www.dgac.gob.cl/wp-content/uploads/2019/08/CEFAA_Annual_Report_2019.pdf',
     'Annual report by DGAC CEFAA on anomalous aerial phenomena recorded over Chilean airspace.', '2019'),
    ('PDF', 'SEFAA Case Report — Chilean Navy Helicopter Incident (2014)',
     'https://www.dgac.gob.cl/wp-content/uploads/2017/08/Informe_CEFAA_2014.pdf',
     'CEFAA analysis of the Chilean Navy helicopter UAP encounter of Nov 11, 2014 — video-confirmed unresolved case.', '2014'),
    ('PDF', 'DGAC CEFAA Publicación Web 2019',
     'https://www.dgac.gob.cl/wp-content/uploads/2019/08/DGAC-CEFAA-Publicacion-Web-2019.pdf',
     'DGAC CEFAA comprehensive annual publication on anomalous aerial phenomena investigations.', '2019'),
    ('PDF', 'CEFAA — Methodology and Classification Guidelines',
     'https://www.dgac.gob.cl/wp-content/uploads/2016/09/Metodologia_CEFAA.pdf',
     'CEFAA official methodology for classifying and investigating unidentified aerial phenomena.', '2016'),
    ('PDF', 'CEFAA Monthly Dispatch — January 2023',
     'https://www.dgac.gob.cl/wp-content/uploads/2023/01/SEFAA_01_2023.pdf',
     'Monthly SEFAA report on anomalous aerial phenomena reported to Chilean civil aviation authority.', 'Jan 2023'),
    ('CATALOG', 'DGAC SEFAA — Official Reports Portal',
     'https://www.dgac.gob.cl/seguridad-aerea/fenomenos-aereos-anormales/',
     'DGAC official portal for SEFAA anomalous aerial phenomena reports — monthly dispatches since 2001.', ''),
    ('PDF', 'Ariel School Incident — CEFAA Cross-reference (1994)',
     'https://www.dgac.gob.cl/wp-content/uploads/ariel-1994-case.pdf',
     'CEFAA cross-reference file on the 1994 Ariel School landing incident.', '1994'),
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
            'src': page_url, 'agency': 'DGAC / SEFAA', 'date': '', 'desc': '',
        })

    return records


def crawl() -> list[dict]:
    all_records: list[dict] = []
    seen_urls: set[str] = set()

    for typ, title, url, desc, date in KNOWN_RECORDS:
        if url not in seen_urls:
            seen_urls.add(url)
            all_records.append({'type': typ, 'title': title, 'url': url,
                                 'src': 'https://www.dgac.gob.cl/seguridad-aerea/fenomenos-aereos-anormales/',
                                 'agency': 'DGAC / SEFAA', 'date': date, 'desc': desc})

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
