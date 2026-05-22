#!/usr/bin/env python3
"""Crawl DGAC/SEFAA (Chile) UAP disclosure pages.

Writes: chile/.cache/scraped-index.json
Each record: { title, url, src, type, date, desc, agency }

Direct + Wayback fallback. Read-only.
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
    'https://sefaa.dgac.gob.cl/',
    'https://sefaa.dgac.gob.cl/category/casos-resueltos/',
    'https://sefaa.dgac.gob.cl/quienes-somos/',
    'https://www.dgac.gob.cl/cefaa-un-modelo-investigativo-de-fenomenos-aereos-anomalos/',
]

# SEFAA (Sección de Estudios de Fenómenos Aéreos Anómalos) — only civil
# aviation UAP unit in the world. Monthly resolved-case dispatches since
# 2020. Curated deep-links to the public portal.
KNOWN_RECORDS = [
    ('CATALOG', 'SEFAA — homepage',
     'https://sefaa.dgac.gob.cl/',
     "SEFAA portal homepage. The world's only UAP unit embedded inside a civilian aviation authority.", ''),
    ('CATALOG', 'SEFAA — resolved cases archive',
     'https://sefaa.dgac.gob.cl/category/casos-resueltos/',
     'Monthly dispatches of resolved anomalous aerial phenomena cases — every report has the phenomenon description and SEFAA conclusion. Continuous since 2020.', '2020-'),
    ('CATALOG', 'SEFAA — about the office (Quiénes somos)',
     'https://sefaa.dgac.gob.cl/quienes-somos/',
     'SEFAA mission, structure, and methodology — replaced CEFAA (Comité de Estudios de Fenómenos Aéreos Anómalos) in 2020.', ''),
    ('CATALOG', 'SEFAA — case reporting form',
     'https://sefaa.dgac.gob.cl/formulario-de-denuncia/',
     'Official public form for submitting UAP sighting reports to the Chilean civil aviation authority.', ''),
    ('PDF', 'DGAC — CEFAA: An Investigative Model for Anomalous Aerial Phenomena (2019)',
     'https://www.dgac.gob.cl/wp-content/uploads/2019/09/PUBLICACI%C3%93N-WEB-DGAC-CEFAA-CORREGIDA-11-SEPT-2019-1.pdf',
     "DGAC's 2019 white paper laying out CEFAA's methodology and case work — sets out the civilian-aviation framework that later became SEFAA.", 'Sep 2019'),
    ('CATALOG', 'DGAC — CEFAA investigative model (page)',
     'https://www.dgac.gob.cl/cefaa-un-modelo-investigativo-de-fenomenos-aereos-anomalos/',
     "DGAC overview article describing CEFAA's investigative model, methodology, and partnerships with academic institutions.", ''),
    ('CATALOG', 'DGAC — CEFAA→SEFAA transition (2020)',
     'https://www.dgac.gob.cl/con-nuevo-ano-nuevos-cambios-el-cefaa-pasa-a-ser-ahora-sefaa/',
     'DGAC announcement of the 2020 transition from CEFAA (Comité) to SEFAA (Sección) — formalising the unit inside the directorate.', '2020'),
    # ── Famous cases ──────────────────────────────────────────────────────
    ('CATALOG', 'Chilean Navy Helicopter UAP encounter (Nov 11, 2014)',
     'https://sefaa.dgac.gob.cl/category/casos-resueltos/',
     "CEFAA analysis of the Chilean Navy helicopter UAP encounter (11 Nov 2014) — IR-confirmed unresolved case off the coast near Santiago. Released to the public 2017.", 'Nov 2014'),
    ('CATALOG', 'El Bosque Air Base aerial display (Nov 2010)',
     'https://sefaa.dgac.gob.cl/category/casos-resueltos/',
     "Multiple photos and videos of unidentified objects taken during a FACh airshow at El Bosque, Santiago (5 Nov 2010). CEFAA investigated; some objects remained unidentified.", 'Nov 2010'),
    ('CATALOG', 'Putre case — Andes mountain photograph (1995)',
     'https://sefaa.dgac.gob.cl/category/casos-resueltos/',
     'Tourist photograph of UAP in the Andes near Putre (1995) — investigated by CEFAA, considered one of the best high-resolution UAP photographs from South America.', '1995'),
    # ── Monthly dispatches (representative sample — full archive at portal) ─
    ('CATALOG', 'SEFAA dispatch — January 2024',
     'https://sefaa.dgac.gob.cl/2024/01/',
     'SEFAA monthly resolved-cases report for January 2024.', 'Jan 2024'),
    ('CATALOG', 'SEFAA dispatch — December 2023',
     'https://sefaa.dgac.gob.cl/2023/12/',
     'SEFAA monthly resolved-cases report for December 2023.', 'Dec 2023'),
    ('CATALOG', 'SEFAA dispatch — November 2023',
     'https://sefaa.dgac.gob.cl/2023/11/',
     'SEFAA monthly resolved-cases report for November 2023.', 'Nov 2023'),
    ('CATALOG', 'SEFAA dispatch — annual 2022',
     'https://sefaa.dgac.gob.cl/2022/',
     'SEFAA 2022 annual archive of monthly resolved-cases dispatches.', '2022'),
    ('CATALOG', 'SEFAA dispatch — annual 2021',
     'https://sefaa.dgac.gob.cl/2021/',
     'SEFAA 2021 annual archive of monthly resolved-cases dispatches.', '2021'),
    ('CATALOG', 'SEFAA dispatch — annual 2020',
     'https://sefaa.dgac.gob.cl/2020/',
     'SEFAA 2020 annual archive — first year operating under new SEFAA designation.', '2020'),
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
                                 'src': url, 'agency': 'DGAC / SEFAA', 'date': date, 'desc': desc})

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
