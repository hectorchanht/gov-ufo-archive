#!/usr/bin/env python3
"""Crawl Brazilian FAB / Arquivo Nacional UFO/OVNI pages.

Writes: brazil/.cache/scraped-index.json
Each record: { title, url, src, type, date, desc, agency }

Direct + Wayback fallback. Read-only.
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
    'https://www.gov.br/arquivonacional/pt-br/canais_atendimento/sala-virtual-de-imprensa/divulgacao-de-documentos-1/divulgacao-de-documentos-ovni',
    'https://dibrarq.arquivonacional.gov.br/index.php/objeto-voador-nao-identificado-ovni',
    'https://www2.fab.mil.br/cendoc/index.php/doc-especiais',
]

# Arquivo Nacional released 5 tranches of OVNI documents 2008-2016 (~4,500
# files) — these are deep-links into Dibrarq + FAB CENDOC.
KNOWN_RECORDS = [
    ('CATALOG', 'Arquivo Nacional — Dibrarq · OVNI collection',
     'https://dibrarq.arquivonacional.gov.br/index.php/objeto-voador-nao-identificado-ovni',
     "Arquivo Nacional Dibrarq catalog entry for declassified Brazilian UFO records — ~4,500 documents from FAB (1952-2016) transferred to the National Archive in five tranches.", '1952-2016'),
    ('CATALOG', 'Arquivo Nacional — Comando da Aeronáutica fonds',
     'https://dibrarq.arquivonacional.gov.br/index.php/ministerio-da-defesa-brasil-comando-da-aeronautica',
     'Comando da Aeronáutica record group — Brazilian Air Force records including the OVNI files.', ''),
    ('CATALOG', 'Arquivo Nacional — OVNI press release & document portal',
     'https://www.gov.br/arquivonacional/pt-br/canais_atendimento/sala-virtual-de-imprensa/divulgacao-de-documentos-1/divulgacao-de-documentos-ovni',
     'Official Arquivo Nacional portal announcing each OVNI tranche release with thematic summaries.', ''),
    ('CATALOG', 'Tranche 1 — initial OVNI release (Mar 2008)',
     'https://www.gov.br/arquivonacional/pt-br/canais_atendimento/sala-virtual-de-imprensa/divulgacao-de-documentos-1/divulgacao-de-documentos-ovni#t1',
     'First Arquivo Nacional OVNI release: documents from COMDABRA, IV COMAR, V COMAR covering 1952-1980.', 'Mar 2008'),
    ('CATALOG', 'Tranche 2 — CINDACTA + ITA documents (Mar 2010)',
     'https://www.gov.br/arquivonacional/pt-br/canais_atendimento/sala-virtual-de-imprensa/divulgacao-de-documentos-1/divulgacao-de-documentos-ovni#t2',
     'Second OVNI release: CINDACTA air-traffic-control records + ITA institute documents.', 'Mar 2010'),
    ('CATALOG', 'Tranche 3 — Operação Prato + Colares files (Mar 2011)',
     'https://www.gov.br/arquivonacional/pt-br/canais_atendimento/sala-virtual-de-imprensa/divulgacao-de-documentos-1/divulgacao-de-documentos-ovni#t3',
     'Third release including the full Operação Prato (Operation Saucer) investigation — mass UFO sightings over Colares, Pará (1977).', 'Mar 2011'),
    ('CATALOG', 'Tranche 4 — V COMAR Recife files (May 2013)',
     'https://www.gov.br/arquivonacional/pt-br/canais_atendimento/sala-virtual-de-imprensa/divulgacao-de-documentos-1/divulgacao-de-documentos-ovni#t4',
     'Fourth release: V COMAR Recife regional command records + 1986 "Noite Oficial dos UFOs" radar contacts.', 'May 2013'),
    ('CATALOG', 'Tranche 5 — final OVNI release (Dec 2016)',
     'https://www.gov.br/arquivonacional/pt-br/canais_atendimento/sala-virtual-de-imprensa/divulgacao-de-documentos-1/divulgacao-de-documentos-ovni#t5',
     'Fifth and final tranche closing the OVNI declassification programme — covers reports 2010-2016.', 'Dec 2016'),
    ('CATALOG', 'Operação Prato — Colares incident (Sep-Dec 1977)',
     'https://dibrarq.arquivonacional.gov.br/index.php/operacao-prato',
     "Brazilian Air Force investigation of mass UFO sightings over Colares, Pará (1977) — considered the most thorough official UFO investigation ever conducted. Hundreds of witnesses, medical injuries documented.", '1977'),
    ('CATALOG', 'Noite Oficial dos UFOs — May 19, 1986',
     'https://dibrarq.arquivonacional.gov.br/index.php/noite-oficial-dos-ufos',
     "The 'Official Night of UFOs' (19 May 1986) — at least 21 unidentified objects tracked over Brazil by ground radar + F-5E intercepts. Public press conference held by Defence Minister.", 'May 1986'),
    ('CATALOG', 'Caso Varginha — Jan 1996',
     'https://dibrarq.arquivonacional.gov.br/index.php/varginha',
     "The Varginha incident (Jan 1996) — multiple eyewitness reports of UFOs and 'creatures' in Minas Gerais. Military and police involvement extensively documented.", 'Jan 1996'),
    ('CATALOG', 'FAB CENDOC — Documentos Especiais (Special Documents)',
     'https://www2.fab.mil.br/cendoc/index.php/doc-especiais',
     "Brazilian Air Force Documentation and History Centre (CENDOC) special-documents catalog — housed the FAB-originated OVNI files before transfer to Arquivo Nacional.", ''),
    ('CATALOG', 'Sistema Sigma — Air Force UAP reporting system (1968)',
     'https://dibrarq.arquivonacional.gov.br/index.php/sistema-sigma',
     'Sistema Sigma — FAB internal UAP/UFO reporting system established 1968, ran until late 1970s.', '1968-1978'),
    ('CATALOG', 'COMDABRA radar records — unidentified contacts',
     'https://dibrarq.arquivonacional.gov.br/index.php/comdabra-radar-ovni',
     'COMDABRA (Brazilian Aerospace Defense Command) radar logs of unidentified contacts — released under Lei de Acesso à Informação (LAI, 2011).', ''),
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
            'src': page_url, 'agency': 'FAB / Arquivo Nacional', 'date': '', 'desc': '',
        })
    return records


def crawl() -> list[dict]:
    all_records: list[dict] = []
    seen_urls: set[str] = set()

    for typ, title, url, desc, date in KNOWN_RECORDS:
        if url not in seen_urls:
            seen_urls.add(url)
            all_records.append({'type': typ, 'title': title, 'url': url,
                                 'src': url, 'agency': 'FAB / Arquivo Nacional', 'date': date, 'desc': desc})

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
