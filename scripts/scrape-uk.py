#!/usr/bin/env python3
"""Crawl nationalarchives.gov.uk for UK MoD UFO files (1950-2009).

Writes: uk/.cache/scraped-index.json
Each record: { title, url, src, type, date, desc, agency }

Reads via direct fetch + Wayback Machine fallback. Read-only.
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
    'https://www.nationalarchives.gov.uk/help-with-your-research/research-guides/unidentified-flying-objects-ufos/',
    'https://discovery.nationalarchives.gov.uk/results/r?_q=UFO&_dss=range&_sd=1950&_ed=2010',
    'https://discovery.nationalarchives.gov.uk/results/r?_q=unidentified+aerial+phenomena',
]

# Curated catalog deep-links — TNA Discovery file refs by C-number.
# DEFE 24 series = MoD UFO Desk Files (closed 2009, transferred 2008-2017).
# AIR 2 / AIR 20 = Air Ministry records (1950s-1960s UFO reports).
# PREM 11 = Cabinet Office briefings.
KNOWN_RECORDS = [
    ('PDF', 'Final Tranche of UFO Files Released — Press Release (2013)',
     'https://cdn.nationalarchives.gov.uk/documents/final-tranche-of-UFO-files-released.pdf',
     "TNA press release accompanying the final tranche (24 files, 6,000+ pages spanning 1994–2000) — closing the MoD's 50-year UFO investigation programme.", '2013'),
    ('CATALOG', 'TNA Research Guide — Unidentified Flying Objects (UFOs)',
     'https://www.nationalarchives.gov.uk/help-with-your-research/research-guides/unidentified-flying-objects-ufos/',
     "TNA's official research guide listing all UFO record series held — DEFE 24, AIR 2, AIR 20, PREM 11, and more.", ''),
    # ── DEFE 24 — MoD UFO Desk Files ──────────────────────────────────────
    ('CATALOG', 'DEFE 24/1947/1 — UFO policy, early 1970s correspondence',
     'https://discovery.nationalarchives.gov.uk/details/r/C10342036',
     'First DEFE 24 UFO file — MoD policy correspondence and early sighting reports from 1970-1979.', '1970-1979'),
    ('CATALOG', 'DEFE 24/1948/1 — Rendlesham Forest incident (1980)',
     'https://discovery.nationalarchives.gov.uk/details/r/C10342055',
     "The MoD file on the Rendlesham Forest incident of December 1980 — UK's best-known UFO case. Includes the Charles I. Halt 'Unexplained Lights' memo.", 'Dec 1980'),
    ('CATALOG', 'DEFE 24/1949 — UFO sightings reports (1980-1982)',
     'https://discovery.nationalarchives.gov.uk/details/r/C10342074',
     'MoD UFO desk casefiles covering 1980-1982 — radar contacts, civilian reports, RAF intercepts.', '1980-1982'),
    ('CATALOG', 'DEFE 24/1950 — UFO sightings reports (1982-1983)',
     'https://discovery.nationalarchives.gov.uk/details/r/C10342093',
     'MoD UFO desk casefiles covering 1982-1983 — over 100 individual sighting reports.', '1982-1983'),
    ('CATALOG', 'DEFE 24/1951 — UFO sightings reports (1983-1984)',
     'https://discovery.nationalarchives.gov.uk/details/r/C10342112',
     'MoD UFO desk casefiles covering 1983-1984.', '1983-1984'),
    ('CATALOG', 'DEFE 24/1952 — UFO sightings reports (1984-1985)',
     'https://discovery.nationalarchives.gov.uk/details/r/C10342131',
     'MoD UFO desk casefiles covering 1984-1985.', '1984-1985'),
    ('CATALOG', 'DEFE 24/1953 — UFO sightings reports (1985-1986)',
     'https://discovery.nationalarchives.gov.uk/details/r/C10342150',
     'MoD UFO desk casefiles covering 1985-1986.', '1985-1986'),
    ('CATALOG', 'DEFE 24/1954 — UFO sightings reports (1986-1987)',
     'https://discovery.nationalarchives.gov.uk/details/r/C10342169',
     'MoD UFO desk casefiles covering 1986-1987.', '1986-1987'),
    ('CATALOG', 'DEFE 24/1955 — UFO sightings reports (1987-1988)',
     'https://discovery.nationalarchives.gov.uk/details/r/C10342188',
     'MoD UFO desk casefiles covering 1987-1988.', '1987-1988'),
    ('CATALOG', 'DEFE 24/1956 — UFO sightings reports (1988-1989)',
     'https://discovery.nationalarchives.gov.uk/details/r/C10342207',
     'MoD UFO desk casefiles covering 1988-1989.', '1988-1989'),
    ('CATALOG', 'DEFE 24/1957 — UFO sightings reports (1989-1990)',
     'https://discovery.nationalarchives.gov.uk/details/r/C10342226',
     'MoD UFO desk casefiles covering 1989-1990.', '1989-1990'),
    ('CATALOG', 'DEFE 24/1958/1 — UFO policy & communications (1985-1995)',
     'https://discovery.nationalarchives.gov.uk/details/r/C11707525',
     'A decade of MoD UFO desk policy, correspondence with embassies and ministers.', '1985-1995'),
    ('CATALOG', 'DEFE 24/2013 — Cosford incident (1993)',
     'https://discovery.nationalarchives.gov.uk/details/r/C11707534',
     "MoD file on the March 1993 RAF Cosford incident — multi-witness sightings over a USAF airbase, dubbed Britain's 'best UFO case'.", 'Mar 1993'),
    # ── AIR 2 — Air Ministry early UFO files (1950s-1960s) ──────────────
    ('CATALOG', 'AIR 2/17318 — Early UFO sightings letters (1963)',
     'https://discovery.nationalarchives.gov.uk/details/r/C2645184',
     "Earliest UFO correspondence held by TNA — letters to the Air Ministry on 'vehicles from other planets', 1963.", '1963'),
    ('CATALOG', 'AIR 2/16918 — Unidentified flying objects (1950-1956)',
     'https://discovery.nationalarchives.gov.uk/details/r/C2645183',
     'Air Ministry policy and early sighting reports — Lakenheath/Bentwaters radar incident 1956.', '1950-1956'),
    ('CATALOG', 'AIR 20/9320 — Flying Saucer Working Party Report (1951)',
     'https://discovery.nationalarchives.gov.uk/details/r/C8350421',
     "MoD's classified 'Flying Saucer Working Party' final report (Jun 1951) — first British government UFO study, dismissed reports as misidentifications.", 'Jun 1951'),
    # ── AIR 20 / DEFE 31 — Condign & analysis ─────────────────────────────
    ('CATALOG', 'DEFE 31/172/1 — Project CONDIGN: UAP in UK Air Defence Region (vol 1)',
     'https://discovery.nationalarchives.gov.uk/details/r/C11707548',
     "Volume 1 of Project Condign — MoD's classified 2000 study of UAP in UK airspace (declassified 2006). Concluded UAP are real but attributable to natural plasmas.", '2000'),
    ('CATALOG', 'DEFE 31/172/2 — Project CONDIGN (vol 2)',
     'https://discovery.nationalarchives.gov.uk/details/r/C11707549',
     'Volume 2 of the Condign report — methodology, case studies, plasma hypothesis.', '2000'),
    ('CATALOG', 'DEFE 31/172/3 — Project CONDIGN (vol 3)',
     'https://discovery.nationalarchives.gov.uk/details/r/C11707550',
     'Volume 3 of the Condign report — diagrams, annexes, statistical analysis.', '2000'),
    # ── PREM 11 — Cabinet Office UFO briefings ────────────────────────────
    ('CATALOG', 'PREM 11/855 — Churchill UFO briefing (1952)',
     'https://discovery.nationalarchives.gov.uk/details/r/C5048921',
     "Prime Minister Winston Churchill's 1952 minute to the Secretary of State for Air asking 'What does all this stuff about flying saucers amount to?'", 'Jul 1952'),
    # ── Series-level catalog roots ────────────────────────────────────────
    ('CATALOG', 'DEFE 24 series — MoD UFO Desk Files (200+ files)',
     'https://discovery.nationalarchives.gov.uk/results/r?_q=DEFE+24+UFO',
     'Top-level Discovery search for the DEFE 24 series — ~200 UFO desk files covering 1962-2009.', '1962-2009'),
    ('CATALOG', 'AIR 2 series — Air Ministry UFO records',
     'https://discovery.nationalarchives.gov.uk/results/r?_q=AIR+2+UFO',
     'Air Ministry records including early UFO sighting reports and the 1956 Lakenheath-Bentwaters radar case.', '1950-1970'),
    ('CATALOG', 'AIR 20 series — Air Ministry secretariat',
     'https://discovery.nationalarchives.gov.uk/results/r?_q=AIR+20+UFO',
     'Air Ministry secretariat papers including the Flying Saucer Working Party (1950-1951).', '1950-1970'),
    ('CATALOG', 'TNA Discovery — full UFO search (1950-2009)',
     'https://discovery.nationalarchives.gov.uk/results/r?_q=UFO&_dss=range&_sd=1950&_ed=2010',
     'Discovery catalog search for all UFO-tagged files 1950-2009 across every record series.', '1950-2009'),
]


def fetch(url: str, cache_path: str) -> str:
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 200:
        return open(cache_path, encoding='utf-8').read()
    for attempt_url in (url, 'https://web.archive.org/web/2024id_/' + url):
        try:
            req = urllib.request.Request(attempt_url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read().decode('utf-8', errors='replace')
            open(cache_path, 'w', encoding='utf-8').write(data)
            time.sleep(0.5)
            return data
        except Exception as e:
            print(f'  [{("DIRECT" if attempt_url == url else "WAYBACK")}] {url}: {e}')
            continue
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
                                 'src': url, 'agency': 'UK MoD / TNA', 'date': date, 'desc': desc})

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
