#!/usr/bin/env python3
"""Full crawl of aaro.mil to discover every public PDF, video, and document.

Writes: aaro/.cache/scraped-index.json
Each record: { title, url, src, type, date, desc, agency }

Run before build-aaro.py to expand the asset list beyond the hand-curated set.
This is READ-ONLY — no files are downloaded. Use dl-aaro.sh to download.

Polite: 0.5 s between requests, realistic Chrome UA, Wayback fallback.
"""
from __future__ import annotations
import json, os, re, time, html, sys, urllib.request, urllib.error, urllib.parse

REPO  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, 'aaro', '.cache')
os.makedirs(CACHE, exist_ok=True)
PAGES_DIR = os.path.join(CACHE, 'scrape-pages')
os.makedirs(PAGES_DIR, exist_ok=True)

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
BASE = 'https://www.aaro.mil'

SEED_URLS = [
    'https://www.aaro.mil/UAP-Cases/Official-UAP-Imagery/',
    'https://www.aaro.mil/Reports-Testimonies/Reports/',
    'https://www.aaro.mil/Reports-Testimonies/Testimonies/',
    'https://www.aaro.mil/About-AARO/',
    'https://www.aaro.mil/FOIA/',
    'https://www.aaro.mil/Media-Room/',
]


def fetch(url: str, cache_path: str, throttle: float = 0.5) -> str:
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 500:
        return open(cache_path, encoding='utf-8').read()
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read().decode('utf-8', errors='replace')
            open(cache_path, 'w', encoding='utf-8').write(data)
            time.sleep(throttle)
            return data
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return ''
            print(f'  [HTTP {e.code}] {url}  attempt {attempt+1}')
            time.sleep(2 ** attempt)
        except Exception as e:
            print(f'  [ERR] {url}: {e}  attempt {attempt+1}')
            time.sleep(2 ** attempt)
    # Wayback fallback
    wb = f'https://web.archive.org/web/2025id_/{url}'
    try:
        req = urllib.request.Request(wb, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=45) as r:
            data = r.read().decode('utf-8', errors='replace')
        open(cache_path, 'w', encoding='utf-8').write(data)
        return data
    except Exception as e:
        print(f'  [WAYBACK FAIL] {url}: {e}')
        return ''


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r'<[^>]+>', ' ', s or '')).strip()


def normalise_ws(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def extract_links(html_src: str, page_url: str) -> list[dict]:
    """Extract all links to PDFs, videos, and pages from an HTML source."""
    records = []
    seen = set()

    # PDF direct links
    for m in re.finditer(r'href="([^"]*\.pdf[^"]*)"', html_src, re.I):
        href = m.group(1)
        if href.startswith('//'):
            href = 'https:' + href
        elif href.startswith('/'):
            href = BASE + href
        elif not href.startswith('http'):
            href = urllib.parse.urljoin(page_url, href)
        fn = href.rsplit('/', 1)[-1].split('?')[0]
        if fn in seen:
            continue
        seen.add(fn)
        # Try to find surrounding title
        context = html_src[max(0, m.start()-300):m.end()+300]
        title = ''
        for pat in [
            r'<a[^>]*href="[^"]*\.pdf[^"]*"[^>]*>([^<]+)</a>',
            r'alt="([^"]+)"',
            r'title="([^"]+)"',
        ]:
            tm = re.search(pat, context, re.I)
            if tm:
                title = normalise_ws(strip_tags(tm.group(1)))
                break
        if not title:
            title = normalise_ws(urllib.parse.unquote(fn.replace('_', ' ').replace('-', ' ')).rsplit('.', 1)[0])
        records.append({
            'type': 'PDF',
            'title': title or fn,
            'url': href,
            'src': page_url,
            'agency': 'AARO',
            'date': '',
            'desc': '',
        })

    # Internal aaro.mil page links (for recursive crawl)
    for m in re.finditer(r'href="(/[^"#?]+)"', html_src):
        path = m.group(1)
        if any(path.lower().endswith(ext) for ext in ('.pdf', '.jpg', '.png', '.mp4', '.docx', '.xlsx')):
            continue
        url = BASE + path
        if url not in seen:
            seen.add(url)

    return records


def crawl_page(url: str, depth: int = 0, max_depth: int = 2) -> list[dict]:
    """Recursively crawl an AARO page for assets."""
    slug = re.sub(r'[^a-z0-9]+', '_', url.lower().split('//', 1)[-1])[:80]
    cache_path = os.path.join(PAGES_DIR, f'{slug}.html')
    src = fetch(url, cache_path)
    if not src:
        return []
    records = extract_links(src, url)

    if depth < max_depth:
        # Find internal sub-pages to crawl
        sub_pages = set()
        for m in re.finditer(r'href="(/(?:Reports-Testimonies|UAP-Cases|FOIA|About-AARO|Media-Room)[^"#?]*)"', src):
            sub_pages.add(BASE + m.group(1))
        for sp in sub_pages:
            if sp == url:
                continue
            slug2 = re.sub(r'[^a-z0-9]+', '_', sp.lower().split('//', 1)[-1])[:80]
            if not os.path.exists(os.path.join(PAGES_DIR, f'{slug2}.html')):
                records.extend(crawl_page(sp, depth + 1, max_depth))

    return records


def crawl() -> list[dict]:
    all_records: list[dict] = []
    seen_urls: set[str] = set()

    for seed in SEED_URLS:
        print(f'→ {seed}')
        recs = crawl_page(seed, depth=0, max_depth=2)
        for r in recs:
            if r['url'] not in seen_urls:
                seen_urls.add(r['url'])
                all_records.append(r)

    # Add known-good curated items not always linked from HTML
    KNOWN = [
        ('PDF', 'AARO Historical Record Report Vol. 1 (2024)',
         'https://media.defense.gov/2024/Mar/08/2003409233/-1/-1/0/AARO_HISTORICAL_RECORD_REPORT_2024.PDF',
         'AARO Historical Record Report'),
        ('PDF', 'AARO Mission Brief (2025)',
         'https://www.aaro.mil/Portals/136/PDFs/AARO_Mission_Brief_2025.pdf',
         'AARO mission briefing material'),
        ('PDF', 'Dr Jon Kosloski — SASC Open Hearing Statement (Nov 2024)',
         'https://www.aaro.mil/Portals/136/PDFs/Dr_Jon_Kosloski_Statement_for_the_Record_SASC_Open_Hearing_Nov2024.pdf',
         'Senate Armed Services Committee testimony'),
    ]
    for typ, title, url, desc in KNOWN:
        if url not in seen_urls:
            seen_urls.add(url)
            all_records.append({'type': typ, 'title': title, 'url': url,
                                 'src': 'https://www.aaro.mil/', 'agency': 'AARO',
                                 'date': '', 'desc': desc})

    out = os.path.join(CACHE, 'scraped-index.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    print(f'\nWrote {out}  ({len(all_records)} records)')
    return all_records


if __name__ == '__main__':
    crawl()
