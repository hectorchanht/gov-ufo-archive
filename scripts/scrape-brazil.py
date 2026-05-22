#!/usr/bin/env python3
"""Crawl FAB (Força Aérea Brasileira) UFO/UAP disclosure pages.

Writes: brazil/.cache/scraped-index.json
Each record: { title, url, src, type, date, desc, agency }

Read-only — no files are downloaded.
"""
from __future__ import annotations
import json, os, re, time, html, urllib.request, urllib.error, urllib.parse

REPO  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, 'brazil', '.cache')
os.makedirs(CACHE, exist_ok=True)
PAGES_DIR = os.path.join(CACHE, 'scrape-pages')
os.makedirs(PAGES_DIR, exist_ok=True)

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

SEED_URLS = [
    'https://www.fab.mil.br/noticias/noticia/3553-fab-divulga-arquivos-sobre-ovnis',
    'https://www.fab.mil.br/noticias/noticia/3728',
    'https://www.fab.mil.br/noticias/noticia/2929',
]

KNOWN_RECORDS = [
    ('PDF', 'FAB OVNI Tranche 1 — Arquivo Nacional (2009)',
     'https://www.fab.mil.br/arquivo_ovni/tranche1/',
     'First release of FAB UFO files — investigations from 1952-1982.', '2009'),
    ('PDF', 'FAB OVNI Tranche 2 — CINDACTA incidents (2010)',
     'https://www.fab.mil.br/arquivo_ovni/tranche2/',
     'Second release covering CINDACTA air traffic control UFO encounters.', '2010'),
    ('PDF', 'FAB OVNI Tranche 3 — Operação Prato (2011)',
     'https://www.fab.mil.br/arquivo_ovni/tranche3/',
     'Third release including the famous Operação Prato (Operation Saucer) files from 1977.', '2011'),
    ('PDF', 'FAB OVNI Tranche 4 (2013)',
     'https://www.fab.mil.br/arquivo_ovni/tranche4/',
     'Fourth release of declassified Brazilian Air Force UFO investigation files.', '2013'),
    ('PDF', 'FAB OVNI Tranche 5 (2016)',
     'https://www.fab.mil.br/arquivo_ovni/tranche5/',
     'Fifth and most recent release of FAB UFO investigation documents.', '2016'),
    ('PDF', 'Operação Prato — Full Investigation File (1977)',
     'https://www.fab.mil.br/noticias/noticia/3553',
     'Operation Saucer: the Brazilian Air Force investigation of mass UFO sightings over Colares, Pará (1977). Considered the most thorough official UFO investigation ever conducted.', '1977'),
    ('CATALOG', 'Arquivo Nacional OVNI Portal',
     'https://www.arquivonacional.gov.br/br/servicos-ao-cidadao/ovni-portal.html',
     'Brazilian National Archive portal for OVNI (UFO) declassified documents.', ''),
    ('PDF', 'CINDACTA — Official Radar Contacts Report',
     'https://www.fab.mil.br/arquivo_ovni/cindacta/',
     'CINDACTA I/II/III radar data on unidentified aerial objects — released under Brazilian transparency law.', ''),
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
            'src': page_url, 'agency': 'FAB / COMDABRA', 'date': '', 'desc': '',
        })

    return records


def crawl() -> list[dict]:
    all_records: list[dict] = []
    seen_urls: set[str] = set()

    for typ, title, url, desc, date in KNOWN_RECORDS:
        if url not in seen_urls:
            seen_urls.add(url)
            all_records.append({'type': typ, 'title': title, 'url': url,
                                 'src': 'https://www.fab.mil.br/noticias/noticia/3553-fab-divulga-arquivos-sobre-ovnis',
                                 'agency': 'FAB / COMDABRA', 'date': date, 'desc': desc})

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
