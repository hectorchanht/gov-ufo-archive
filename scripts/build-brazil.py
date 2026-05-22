#!/usr/bin/env python3
"""Build brazil/index.html — Brazil FAB / Arquivo Nacional OVNI mirror.

The ~4,500 declassified Brazilian UFO documents released 2008-2016 live in
two catalog systems (Arquivo Nacional / Dibrarq + FAB CENDOC); both are
session-based and CAPTCHA-gated, so this mirror surfaces deep-links.
Tone: Brazilian green (#009c3b).
"""
import json, os, sys, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, 'brazil')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _mirror_shared import SHARED_CSS, SHARED_JS
from _release_manifest import apply_manifest
from _site_template import make_nav, LIGHTBOX_HTML

def git_tracked(rel_dir):
    try:
        out = subprocess.run(['git','-C',REPO,'ls-files',f'brazil/{rel_dir}/'],
            capture_output=True, text=True, check=True).stdout
        prefix = f'brazil/{rel_dir}/'
        return {ln[len(prefix):] for ln in out.splitlines() if ln.startswith(prefix)}
    except Exception:
        p = os.path.join(ROOT, rel_dir)
        return set(os.listdir(p)) if os.path.isdir(p) else set()

tracked_pdfs = git_tracked('pdfs')
def Lp(f): return f'pdfs/{f}' if f in tracked_pdfs else ''

ASSETS = [
    {
        't': 'CATALOG',
        'ti': 'Arquivo Nacional — Dibrarq · OVNI collection',
        'de': "The Arquivo Nacional's Dibrarq catalog entry for declassified Brazilian UFO records — ~4,500 documents from FAB (1952–2016) transferred to the National Archive in five tranches.",
        'ag': 'Arquivo Nacional',
        'cat': 'Catalog',
        'date': '1952–2016',
        'l': '',
        'u': 'https://dibrarq.arquivonacional.gov.br/index.php/objeto-voador-nao-identificado-ovni',
        's': 'https://dibrarq.arquivonacional.gov.br/index.php/objeto-voador-nao-identificado-ovni',
    },
    {
        't': 'CATALOG',
        'ti': 'FAB CENDOC — Documentos Especiais (Special Documents)',
        'de': "The Air Force's Documentation and History Centre (CENDOC) special-documents catalog. Houses the FAB-originated OVNI files before transfer to Arquivo Nacional.",
        'ag': 'FAB CENDOC',
        'cat': 'Catalog',
        'l': '',
        'u': 'https://www2.fab.mil.br/cendoc/index.php/doc-especiais',
        's': 'https://www2.fab.mil.br/cendoc/index.php/doc-especiais',
    },
    {
        't': 'CATALOG',
        'ti': 'Arquivo Nacional — Comando da Aeronáutica fonds',
        'de': "The Comando da Aeronáutica record group in the National Archive — Brazilian Air Force records including the OVNI files.",
        'ag': 'Arquivo Nacional',
        'cat': 'Catalog',
        'l': '',
        'u': 'https://dibrarq.arquivonacional.gov.br/index.php/ministerio-da-defesa-brasil-comando-da-aeronautica',
        's': 'https://dibrarq.arquivonacional.gov.br/index.php/ministerio-da-defesa-brasil-comando-da-aeronautica',
    },
    {
        't': 'CATALOG',
        'ti': 'FAB Notimp 250 (08/09/2013) — OVNI policy ordinance',
        'de': "The 2013 FAB instruction (COMAER) that formalised the procedure for registering, handling, and forwarding UFO reports to the Arquivo Nacional.",
        'ag': 'Força Aérea Brasileira',
        'cat': 'Policy',
        'date': '8 Sep 2013',
        'l': '',
        'u': 'https://www.fab.mil.br/notimp/mostra/08-09-2013',
        's': 'https://www.fab.mil.br/notimp/mostra/08-09-2013',
    },
    {
        't': 'CATALOG',
        'ti': 'FAB Notimp 173 (21/06/2015) — UFO reporting update',
        'de': "A 2015 FAB update reaffirming the role of COMDABRA (Brazilian Aerospace Defense Command) in receiving and cataloging UFO reports.",
        'ag': 'Força Aérea Brasileira',
        'cat': 'Policy',
        'date': '21 Jun 2015',
        'l': '',
        'u': 'https://www.fab.mil.br/notimp/mostra/21-06-2015',
        's': 'https://www.fab.mil.br/notimp/mostra/21-06-2015',
    },
    {
        't': 'CATALOG',
        'ti': 'CENDOC — Arquivo Geral do Comando da Aeronáutica',
        'de': "Overview of CENDOC's general archive of the Brazilian Air Force Command — context and scope of the records that include OVNI files.",
        'ag': 'FAB CENDOC',
        'cat': 'Reference',
        'l': '',
        'u': 'https://www2.fab.mil.br/cendoc/index.php/sobre-arquivologia',
        's': 'https://www2.fab.mil.br/cendoc/index.php/sobre-arquivologia',
    },
]

_scraped_cache = os.path.join(ROOT, '.cache', 'scraped-index.json')
if os.path.exists(_scraped_cache):
    _seen = {a.get('u', '') or a.get('url', '') for a in ASSETS}
    for _r in json.load(open(_scraped_cache)):
        _url = _r.get('url', '')
        if _url and _url not in _seen:
            _seen.add(_url)
            ASSETS.append({'t': _r.get('type', 'PDF'), 'ti': _r.get('title', ''), 'de': _r.get('desc', ''),
                           'ag': _r.get('agency', 'FAB / COMDABRA'), 'cat': _r.get('type', 'PDF').capitalize(),
                           'date': _r.get('date', ''), 'l': '', 'u': _url, 's': _r.get('src', ''),})

apply_manifest(ASSETS)
stats = {
    'total': len(ASSETS),
    'local_total': sum(1 for a in ASSETS if a.get('l')),
    'pdf_total': sum(1 for a in ASSETS if a['t'] == 'PDF'),
    'catalog_total': sum(1 for a in ASSETS if a['t'] == 'CATALOG'),
}
data_json = json.dumps({'assets': ASSETS, 'stats': stats}, ensure_ascii=False).replace('</script', '<\\/script')

PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Brazil FAB / Arquivo Nacional — OVNI Records (Offline Mirror)</title>
<meta name="description" content="Offline mirror of Brazil's declassified UFO (OVNI) records: ~4,500 documents from the Força Aérea Brasileira held at Arquivo Nacional.">
<link rel="canonical" href="https://realufo.org/brazil/">
<meta property="og:title" content="Brazil OVNI Records — FAB & Arquivo Nacional | realufo.org">
<meta property="og:description" content="Brazil's declassified UFO files. ~4,500 documents from the Força Aérea Brasileira (1952-2016) held at Arquivo Nacional. Released under Lei nº 12.527/2011.">
<meta property="og:image" content="https://realufo.org/slideshow/NASA-UAP-VM6-Apollo-17-1972.jpg">
<meta property="og:url" content="https://realufo.org/brazil/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="realufo.org">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Brazil OVNI Records — FAB & Arquivo Nacional | realufo.org">
<meta name="twitter:description" content="Brazil's declassified UFO files. ~4,500 documents from the Força Aérea Brasileira (1952-2016) held at Arquivo Nacional. Released under Lei nº 12.527/2011.">
<meta name="twitter:image" content="https://realufo.org/slideshow/NASA-UAP-VM6-Apollo-17-1972.jpg">
<link rel="icon" type="image/svg+xml" href="./assets/favicon.svg">
<link rel="apple-touch-icon" href="./assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet">
<style>
__SHARED_CSS__
:root { --caution: #4ade80; }
.seal { background: radial-gradient(circle at 50% 50%, #ffdc00, #009c3b 55%, #002776); color: #0a0a0c; }
body { background-image:
  radial-gradient(ellipse at 20% 0%, rgba(0,156,59,0.08) 0%, transparent 50%),
  radial-gradient(ellipse at 80% 100%, rgba(255,220,0,0.04) 0%, transparent 50%); background-attachment: fixed; }
</style>
</head>
<body>
<div class="scanlines"></div>

<div class="header-wrap">
<header>
  <div class="container">
    <a href="#top" class="brand">
      <div class="seal">BR</div>
      <div class="brand-text">
        <span class="super">Arquivo Nacional · FAB</span>
        <span class="name">OVNI Records · Brazil</span>
      </div>
    </a>
    <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
    __NAV__
  </div>
</header>
</div>

<div class="hero" id="top">
  <div class="container">
    <div class="coords">15°47′S, 47°53′W · ARQUIVO NACIONAL · BRASÍLIA / RIO DE JANEIRO</div>
    <h1 class="hero-title">Brazil's <em>OVNI</em> files — declassified in five tranches.</h1>
    <p class="hero-sub">
      Between <strong>2008 and 2016</strong>, the Força Aérea Brasileira (FAB) declassified
      approximately <strong>4,500 documents</strong> spanning 1952-2016 and transferred them to
      the <a href="https://dibrarq.arquivonacional.gov.br/index.php/objeto-voador-nao-identificado-ovni" target="_blank" rel="noopener">Arquivo Nacional</a>.
      A 2013 COMAER ordinance formalised the procedure for registering UFO reports. Releases are
      reusable under <a href="https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12527.htm" target="_blank" rel="noopener">Lei nº 12.527/2011 (LAI)</a> — Brazil's Freedom of Information Act.
    </p>
  </div>
</div>

<section id="headlines" class="headlines">
  <div class="container">
    <div class="section-label">§ Headlines · Brazilian UFO records, distilled</div>
    <div class="head-grid">
      <div class="head-card"><div class="h-label">Releases</div><span class="h-num">5</span><div class="h-text">Successive tranches 2008-2016.</div></div>
      <div class="head-card"><div class="h-label">Documents</div><span class="h-num">~4 500</span><div class="h-text">Spanning 1952-2016.</div></div>
      <div class="head-card"><div class="h-label">Custodian</div><div class="h-text">Arquivo Nacional (Brasília / Rio) — transferred from FAB CENDOC.</div></div>
      <div class="head-card"><div class="h-label">Authority</div><div class="h-text">2013 COMAER ordinance + Lei nº 12.527/2011 (LAI).</div></div>
      <div class="head-card"><div class="h-label">Current intake</div><div class="h-text">COMDABRA — Comando de Defesa Aeroespacial Brasileiro.</div></div>
      <div class="head-card"><div class="h-label">Reusable under</div><div class="h-text">Lei nº 12.527/2011 — Acesso à Informação.</div></div>
    </div>
  </div>
</section>

<section id="archive">
  <div class="container">
    <div class="section-label">§ Records · Catalog gateways</div>
    <h2>Both catalogs that hold Brazil's declassified UFO record.</h2>
    <p class="lede">
      Each card deep-links into either Arquivo Nacional's <a href="https://dibrarq.arquivonacional.gov.br/" target="_blank" rel="noopener">Dibrarq</a>
      catalog or FAB CENDOC. Direct PDF download isn't available without a session, but the
      catalog pages list every available record and request channel.
    </p>

    <div class="stats-grid" id="arch-stats"></div>

    <div class="arch-controls-bar">
      <div class="tabs" id="arch-tabs"></div>
      <div class="search-wrap">
        <input id="arch-search" type="search" placeholder="Search title, agency, date…" autocomplete="off">
      </div>
    </div>

    <div class="arch-grid" id="arch-grid"></div>
    <div class="empty" id="arch-empty" hidden>No records match.</div>
  </div>
</section>

<footer>
  <div class="container">
    <div>
      <h4>Brazil Mirror</h4>
      <p style="color: var(--ink-dim); font-family: var(--serif); margin-bottom: 14px;">
        Offline gateway to Brazil's official OVNI record. Federal Brazilian works are reusable
        under Lei nº 12.527/2011 (LAI).
      </p>
      <p style="color: var(--ink-faint); font-size: 10px; letter-spacing: 0.1em;">Source: arquivonacional.gov.br · fab.mil.br · captured 2026.</p>
    </div>
    <div>
      <h4>Related Mirrors</h4>
      <ul>
        <li><a href="../index.html">war.gov / UFO Release 01</a></li>
        <li><a href="../aaro/index.html">AARO — DoW</a></li>
        <li><a href="../nasa/index.html">NASA UAP Study</a></li>
        <li><a href="../nara/index.html">NARA UAP Records</a></li>
        <li><a href="../geipan/index.html">France GEIPAN</a></li>
        <li><a href="../uk/index.html">UK MoD UFO Files</a></li>
      </ul>
    </div>
    <div>
      <h4>Source</h4>
      <ul>
        <li><a href="https://dibrarq.arquivonacional.gov.br/index.php/objeto-voador-nao-identificado-ovni" target="_blank" rel="noopener">Arquivo Nacional OVNI ↗</a></li>
        <li><a href="https://www2.fab.mil.br/cendoc/" target="_blank" rel="noopener">FAB CENDOC ↗</a></li>
        <li><a href="https://www.fab.mil.br/" target="_blank" rel="noopener">fab.mil.br ↗</a></li>
      </ul>
    </div>
    <div class="colophon">
      <span>Offline mirror · For research and reference</span>
      <span>Lei nº 12.527/2011 (LAI)</span>
    </div>
  </div>
</footer>

__LIGHTBOX__

<script id="arch-data" type="application/json">__DATA__</script>
<script>__SHARED_JS__</script>
</body>
</html>
'''
_nav = make_nav('brazil', depth=1, internal_links=[
    ('Intro','#top','intro'), ('Headlines','#headlines','headlines'), ('Records','#archive','archive'),
])
PAGE = (PAGE
    .replace('__SHARED_CSS__', SHARED_CSS)
    .replace('__SHARED_JS__', SHARED_JS)
    .replace('__DATA__', data_json)
    .replace('__NAV__', _nav)
    .replace('__LIGHTBOX__', LIGHTBOX_HTML)
)
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(PAGE)
print(f'wrote {ROOT}/index.html ({len(PAGE):,} bytes) · {stats["local_total"]}/{stats["total"]} local')
