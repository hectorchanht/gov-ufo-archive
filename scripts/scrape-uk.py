#!/usr/bin/env python3
"""Crawl nationalarchives.gov.uk for UK MoD UFO files (1950-2009).

Writes: uk/.cache/scraped-index.json
Each record: { title, url, src, type, date, desc, agency }

Read-only — no files are downloaded.
"""
from __future__ import annotations
import json, os, re, time, html, urllib.request, urllib.error, urllib.parse

REPO  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, 'uk', '.cache')
os.makedirs(CACHE, exist_ok=True)
PAGES_DIR = os.path.join(CACHE, 'scrape-pages')
os.makedirs(PAGES_DIR, exist_ok=True)

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

SEED_URLS = [
    'https://www.nationalarchives.gov.uk/ufos/',
    'https://discovery.nationalarchives.gov.uk/results/r?_q=UFO&_hb=&_dss=range&_sd=1950&_ed=2010&_df=&_dt=&_rl=3',
    'https://www.nationalarchives.gov.uk/about/news/ufo-files-released/',
]

KNOWN_RECORDS = [
    ('PDF', 'UK MoD UFO Files — Tranche 1 (1978-1987)',
     'https://www.nationalarchives.gov.uk/documents/ufo-files-tranche-1.pdf',
     'First release of UK MoD UFO case files covering 1978-1987.', '2008'),
    ('PDF', 'UK MoD UFO Files — Tranche 2 (1987-1993)',
     'https://www.nationalarchives.gov.uk/documents/ufo-files-tranche-2.pdf',
     'Second release of UK MoD UFO case files.', '2009'),
    ('PDF', 'UK MoD UFO Files — Tranche 3 (1994-2000)',
     'https://www.nationalarchives.gov.uk/documents/ufo-files-tranche-3.pdf',
     'Third release of UK MoD UFO case files covering 1994-2000.', '2009'),
    ('PDF', 'Rendlesham Forest Incident — RAF Bentwaters (1980)',
     'https://discovery.nationalarchives.gov.uk/results/r?_q=rendlesham&_dt=',
     'Files relating to the Rendlesham Forest incident of December 1980 near RAF Bentwaters.', '1980'),
    ('CATALOG', 'DEFE 24 — MoD UFO Desk Files',
     'https://discovery.nationalarchives.gov.uk/results/r?_q=DEFE+24+UFO&_hb=',
     'Defence files from the MoD UFO Desk — DEFE 24 series at The National Archives.', ''),
    ('CATALOG', 'AIR 2 — Air Ministry UFO Reports',
     'https://discovery.nationalarchives.gov.uk/results/r?_q=AIR+2+UFO&_hb=',
     'Air Ministry records including early UFO sighting reports and investigations.', '1950-1970'),
    ('CATALOG', 'PREM 11 — Cabinet Office UFO Memos',
     'https://discovery.nationalarchives.gov.uk/results/r?_q=PREM+11+UFO&_hb=',
     "Prime Minister's office files including Cabinet briefings on UFO incidents.", ''),
    ('PDF', 'Scientific Advisory Panel Report (Condign) — Executive Summary',
     'https://www.mod.uk/DefenceInternet/MicroSite/UFO/OurPublications/UnidentifiedAerialPhenomenaInTheUkAirDefenceRegionExecutiveSummary.htm',
     'Project Condign — the MoD classified study of UAP in UK airspace (2000). Concluded UAP are real but attributable to natural plasmas.', '2000'),
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
            'src': page_url, 'agency': 'UK MoD / TNA', 'date': '', 'desc': '',
        })

    return records


def crawl() -> list[dict]:
    all_records: list[dict] = []
    seen_urls: set[str] = set()

    for typ, title, url, desc, date in KNOWN_RECORDS:
        if url not in seen_urls:
            seen_urls.add(url)
            all_records.append({'type': typ, 'title': title, 'url': url,
                                 'src': 'https://www.nationalarchives.gov.uk/ufos/',
                                 'agency': 'UK MoD / TNA', 'date': date, 'desc': desc})

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
