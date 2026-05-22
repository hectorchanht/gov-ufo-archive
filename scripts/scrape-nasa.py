#!/usr/bin/env python3
"""Crawl science.nasa.gov/uap and related NASA pages for all UAP documents.

Writes: nasa/.cache/scraped-index.json
Each record: { title, url, src, type, date, desc, agency }

Read-only — no files are downloaded.
"""
from __future__ import annotations
import json, os, re, time, html, urllib.request, urllib.error, urllib.parse

REPO  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, 'nasa', '.cache')
os.makedirs(CACHE, exist_ok=True)
PAGES_DIR = os.path.join(CACHE, 'scrape-pages')
os.makedirs(PAGES_DIR, exist_ok=True)

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

SEED_URLS = [
    'https://science.nasa.gov/uap/',
    'https://science.nasa.gov/uap/media/',
    'https://science.nasa.gov/uap/resources/',
    'https://science.nasa.gov/uap/team/',
    'https://www.nasa.gov/uap/',
]

# Known direct PDF/doc URLs
KNOWN_DOCS = [
    ('PDF', 'NASA UAP Independent Study Team — Final Report (Sep 2023)',
     'https://science.nasa.gov/wp-content/uploads/2023/09/uap-independent-study-team-final-report.pdf',
     'The 36-page final report of the NASA UAP Independent Study Team.', 'Sep 2023'),
    ('PDF', 'UAP Independent Study Team — Terms of Reference',
     'https://science.nasa.gov/wp-content/uploads/2023/04/UAPISTTermsofReference_Signed.pdf',
     'Signed charter establishing the UAP Independent Study Team.', 'Apr 2023'),
    ('PDF', 'Public Meeting Agenda — May 31, 2023',
     'https://science.nasa.gov/wp-content/uploads/2024/01/public-meeting-agenda-tagged.pdf',
     'Agenda for the NASA UAP Independent Study Team public meeting.', 'May 2023'),
    ('PDF', 'Federal Register Notice — UAP Public Meeting',
     'https://science.nasa.gov/wp-content/uploads/2023/05/FRN.pdf',
     'Official Federal Register notice announcing the NASA UAP public meeting.', 'May 2023'),
    ('PDF', 'NASA UAP Director Appointment — Press Release',
     'https://www.nasa.gov/news-release/nasa-appoints-new-director-of-uap-research/',
     'Press release announcing Dr. Mark McInerney as inaugural NASA UAP Research Director.', 'Nov 2023'),
    ('PDF', 'NASA UAP 2024 Annual Report',
     'https://smd-cms.nasa.gov/wp-content/uploads/2024/07/nasa-uap-annual-report-2024.pdf',
     'NASA annual report on UAP research activities and findings.', '2024'),
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
                    r'<h\d[^>]*>([^<]{5,120})</h\d>', r'alt="([^"]{5,120})"']:
            tm = re.search(pat, ctx, re.I)
            if tm:
                title = normalise(strip_tags(tm.group(1)))
                break
        if not title:
            title = normalise(urllib.parse.unquote(fn.replace('_', ' ').replace('-', ' ')).rsplit('.', 1)[0])
        records.append({
            'type': 'PDF', 'title': title or fn, 'url': href,
            'src': page_url, 'agency': 'NASA', 'date': '', 'desc': '',
        })

    # YouTube video embeds
    for m in re.finditer(r'(?:youtube\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})', html_src):
        vid_id = m.group(1)
        vid_url = f'https://www.youtube.com/watch?v={vid_id}'
        if vid_url in seen:
            continue
        seen.add(vid_url)
        ctx = html_src[max(0, m.start()-300):m.end()+300]
        title = ''
        tm = re.search(r'<(?:h\d|strong|b)[^>]*>([^<]{5,120})</', ctx, re.I)
        if tm:
            title = normalise(strip_tags(tm.group(1)))
        records.append({
            'type': 'VID', 'title': title or 'NASA UAP Video', 'url': vid_url,
            'src': page_url, 'agency': 'NASA', 'date': '', 'desc': '',
            'embed': f'https://www.youtube.com/embed/{vid_id}',
        })

    return records


def crawl() -> list[dict]:
    all_records: list[dict] = []
    seen_urls: set[str] = set()

    # Add known docs first
    for typ, title, url, desc, date in KNOWN_DOCS:
        if url not in seen_urls:
            seen_urls.add(url)
            all_records.append({'type': typ, 'title': title, 'url': url,
                                 'src': 'https://science.nasa.gov/uap/',
                                 'agency': 'NASA', 'date': date, 'desc': desc})

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
