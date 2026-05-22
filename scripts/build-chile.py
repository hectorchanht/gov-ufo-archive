#!/usr/bin/env python3
"""Build chile/index.html — Chile DGAC SEFAA (formerly CEFAA) mirror.

SEFAA — Sección de Estudios de Fenómenos Aéreos Anómalos — is the only
civil-aviation UAP unit in the world. Monthly resolved-case dispatches
since 2020. Tone: Chilean red (#d52b1e).
"""
import json, os, sys, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, 'chile')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _mirror_shared import SHARED_CSS, SHARED_JS
from _release_manifest import apply_manifest
from _site_template import make_nav, LIGHTBOX_HTML

def git_tracked(rel_dir):
    try:
        out = subprocess.run(['git','-C',REPO,'ls-files',f'chile/{rel_dir}/'],
            capture_output=True, text=True, check=True).stdout
        prefix = f'chile/{rel_dir}/'
        return {ln[len(prefix):] for ln in out.splitlines() if ln.startswith(prefix)}
    except Exception:
        p = os.path.join(ROOT, rel_dir)
        return set(os.listdir(p)) if os.path.isdir(p) else set()

tracked_pdfs = git_tracked('pdfs')
def Lp(f): return f'pdfs/{f}' if f in tracked_pdfs else ''

ASSETS = [
    {
        't': 'PDF',
        'ti': 'DGAC — CEFAA: An Investigative Model for Anomalous Aerial Phenomena',
        'de': "DGAC's 2019 white paper laying out CEFAA's methodology and case work. Sets out the civilian-aviation framework that later became SEFAA.",
        'ag': 'DGAC · CEFAA',
        'cat': 'Methodology',
        'date': 'Sep 2019',
        'l': Lp('DGAC-CEFAA-Publicacion-Web-2019.pdf'),
        'u': Lp('DGAC-CEFAA-Publicacion-Web-2019.pdf') or 'https://www.dgac.gob.cl/wp-content/uploads/2019/09/PUBLICACI%C3%93N-WEB-DGAC-CEFAA-CORREGIDA-11-SEPT-2019-1.pdf',
        's': 'https://www.dgac.gob.cl/wp-content/uploads/2019/09/PUBLICACI%C3%93N-WEB-DGAC-CEFAA-CORREGIDA-11-SEPT-2019-1.pdf',
    },
    {
        't': 'CATALOG',
        'ti': 'SEFAA — resolved cases archive',
        'de': "Monthly dispatches of resolved anomalous aerial phenomena cases. Every report has the phenomenon description and SEFAA's conclusion. Continuous since 2020.",
        'ag': 'DGAC · SEFAA',
        'cat': 'Catalog',
        'l': '',
        'u': 'https://sefaa.dgac.gob.cl/category/casos-resueltos/',
        's': 'https://sefaa.dgac.gob.cl/category/casos-resueltos/',
    },
    {
        't': 'CATALOG',
        'ti': 'SEFAA — Quiénes somos (about the office)',
        'de': "SEFAA's mission and structure. The world's only UAP unit embedded inside a civilian aviation authority.",
        'ag': 'DGAC · SEFAA',
        'cat': 'Mission',
        'l': '',
        'u': 'https://sefaa.dgac.gob.cl/quienes-somos/',
        's': 'https://sefaa.dgac.gob.cl/quienes-somos/',
    },
    {
        't': 'CATALOG',
        'ti': 'DGAC — CEFAA: An Investigative Model (page)',
        'de': "DGAC's overview article describing CEFAA's investigative model, methodology, and partnerships with academic institutions in Chile.",
        'ag': 'DGAC',
        'cat': 'Reference',
        'l': '',
        'u': 'https://www.dgac.gob.cl/cefaa-un-modelo-investigativo-de-fenomenos-aereos-anomalos/',
        's': 'https://www.dgac.gob.cl/cefaa-un-modelo-investigativo-de-fenomenos-aereos-anomalos/',
    },
    {
        't': 'CATALOG',
        'ti': 'DGAC — CEFAA→SEFAA transition announcement',
        'de': "DGAC's announcement of the 2020 transition from CEFAA (Comité) to SEFAA (Sección) — formalising the unit's place inside the directorate.",
        'ag': 'DGAC',
        'cat': 'Policy',
        'date': '2020',
        'l': '',
        'u': 'https://www.dgac.gob.cl/con-nuevo-ano-nuevos-cambios-el-cefaa-pasa-a-ser-ahora-sefaa/',
        's': 'https://www.dgac.gob.cl/con-nuevo-ano-nuevos-cambios-el-cefaa-pasa-a-ser-ahora-sefaa/',
    },
    {
        't': 'CATALOG',
        'ti': 'SEFAA — landing page',
        'de': "Live SEFAA homepage with the latest dispatches and news updates.",
        'ag': 'DGAC · SEFAA',
        'cat': 'Catalog',
        'l': '',
        'u': 'https://sefaa.dgac.gob.cl/',
        's': 'https://sefaa.dgac.gob.cl/',
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
                           'ag': _r.get('agency', 'DGAC / SEFAA'), 'cat': _r.get('type', 'PDF').capitalize(),
                           'date': _r.get('date', ''), 'l': '', 'u': _url, 's': _r.get('src', ''),})

# Spider crawl results — each page becomes a CATALOG entry with text context.
_spider_cache = os.path.join(ROOT, '.cache', 'spider-index.json')
if os.path.exists(_spider_cache):
    _seen_u = {a.get('u', '') for a in ASSETS}
    for _r in json.load(open(_spider_cache)).get('records', []):
        _url = _r.get('url', '')
        _title = _r.get('title', '').replace(' – SEFAA', '').strip()
        _ctx = _r.get('context', '').strip()
        if not _url or _url in _seen_u or not _title:
            continue
        # Skip top-level / category index pages — only keep monthly dispatches.
        if _url.rstrip('/').endswith(('casos-resueltos', 'sefaa.dgac.gob.cl', 'quienes-somos')):
            continue
        _seen_u.add(_url)
        _file_count = len(_r.get('files', []))
        _desc = (_ctx[:300] + '…') if len(_ctx) > 300 else _ctx
        if _file_count:
            _desc = f'{_file_count} case files referenced. ' + _desc
        ASSETS.append({'t': 'CATALOG', 'ti': _title, 'de': _desc,
                       'ag': 'DGAC / SEFAA', 'cat': 'Monthly Dispatch',
                       'date': '', 'l': '', 'u': _url, 's': _url,
                       'th': _r.get('thumb', '')})

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
<title>SEFAA — Sección de Estudios de Fenómenos Aéreos Anómalos · Chile (Offline Mirror)</title>
<meta name="description" content="Offline mirror of Chile's SEFAA (formerly CEFAA) — the world's only civil-aviation UAP unit, at DGAC.">
<link rel="canonical" href="https://realufo.org/chile/">
<meta property="og:title" content="SEFAA / CEFAA — Chile's Civil-Aviation UAP Unit | realufo.org">
<meta property="og:description" content="Chile's SEFAA (formerly CEFAA) at DGAC — the world's only UAP unit embedded in a civil aviation authority. Monthly resolved-case dispatches since 2020.">
<meta property="og:image" content="https://realufo.org/slideshow/FBI-Photo-B18.jpg">
<meta property="og:url" content="https://realufo.org/chile/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="realufo.org">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="SEFAA / CEFAA — Chile's Civil-Aviation UAP Unit | realufo.org">
<meta name="twitter:description" content="Chile's SEFAA (formerly CEFAA) at DGAC — the world's only UAP unit embedded in a civil aviation authority. Monthly resolved-case dispatches since 2020.">
<meta name="twitter:image" content="https://realufo.org/slideshow/FBI-Photo-B18.jpg">
<link rel="icon" type="image/svg+xml" href="./assets/favicon.svg">
<link rel="apple-touch-icon" href="./assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet">
<style>
__SHARED_CSS__
:root { --caution: #f87171; }
.seal { background: radial-gradient(circle at 50% 50%, #d52b1e, #8b1413 60%, #3d0908); }
body { background-image:
  radial-gradient(ellipse at 20% 0%, rgba(213,43,30,0.08) 0%, transparent 50%),
  radial-gradient(ellipse at 80% 100%, rgba(0,82,165,0.04) 0%, transparent 50%); background-attachment: fixed; }
</style>
</head>
<body>
<div class="scanlines"></div>

<div class="header-wrap">
<header>
  <div class="container">
    <a href="#top" class="brand">
      <div class="seal">SEFAA</div>
      <div class="brand-text">
        <span class="super">Dirección General de Aeronáutica Civil · Chile</span>
        <span class="name">SEFAA · Chile</span>
      </div>
    </a>
    <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
    __NAV__
  </div>
</header>
</div>

<div class="hero" id="top">
  <div class="container">
    <div class="coords">33°27′S, 70°39′W · DIRECCIÓN GENERAL DE AERONÁUTICA CIVIL · SANTIAGO</div>
    <h1 class="hero-title">Chile's <em>civil-aviation</em> UAP office — the only one of its kind.</h1>
    <p class="hero-sub">
      <strong>SEFAA</strong> (Sección de Estudios de Fenómenos Aéreos Anómalos) — formerly CEFAA — is
      the world's only UAP unit embedded inside a civil aviation authority. Sitting within
      <a href="https://www.dgac.gob.cl/" target="_blank" rel="noopener">DGAC</a>, it investigates
      anomalies reported by pilots, air traffic controllers, and the public, and publishes
      <a href="https://sefaa.dgac.gob.cl/category/casos-resueltos/" target="_blank" rel="noopener">monthly resolved-case dispatches</a>.
      Records reusable under <a href="https://www.bcn.cl/leychile/navegar?idNorma=276363" target="_blank" rel="noopener">Ley nº 20.285</a> (Acceso a la Información Pública).
    </p>
  </div>
</div>

<section id="headlines" class="headlines">
  <div class="container">
    <div class="section-label">§ Headlines · SEFAA, distilled</div>
    <div class="head-grid">
      <div class="head-card"><div class="h-label">Founded</div><span class="h-num">1997</span><div class="h-text">As CEFAA. Restructured into SEFAA in 2020.</div></div>
      <div class="head-card"><div class="h-label">Status</div><div class="h-text">Section of <strong>DGAC</strong> — Chilean civil aviation authority.</div></div>
      <div class="head-card"><div class="h-label">Cadence</div><div class="h-text">Monthly resolved-case dispatches since 2020.</div></div>
      <div class="head-card"><div class="h-label">Speciality</div><div class="h-text">Pilot &amp; ATC reports; radar/IR/photographic cross-correlation.</div></div>
      <div class="head-card"><div class="h-label">Methodology</div><div class="h-text">Scientific framework backed by Chilean universities.</div></div>
      <div class="head-card"><div class="h-label">Authority</div><div class="h-text">Ley nº 20.285 sobre Acceso a la Información Pública.</div></div>
    </div>
  </div>
</section>

<section id="archive">
  <div class="container">
    <div class="section-label">§ Records · DGAC publication + live catalog</div>
    <h2>The 2019 publication + every live SEFAA portal.</h2>
    <p class="lede">
      The DGAC's 2019 publication on CEFAA's investigative model is the one substantive PDF; the
      rest are deep-links into the live SEFAA dispatches and DGAC's press archive.
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
      <h4>Chile Mirror</h4>
      <p style="color: var(--ink-dim); font-family: var(--serif); margin-bottom: 14px;">
        Offline gateway to Chile's SEFAA UAP unit at DGAC. Government records reusable under
        Ley nº 20.285 sobre Acceso a la Información Pública.
      </p>
      <p style="color: var(--ink-faint); font-size: 10px; letter-spacing: 0.1em;">Source: dgac.gob.cl · sefaa.dgac.gob.cl · captured 2026.</p>
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
        <li><a href="../brazil/index.html">Brazil OVNI</a></li>
      </ul>
    </div>
    <div>
      <h4>Source</h4>
      <ul>
        <li><a href="https://sefaa.dgac.gob.cl/" target="_blank" rel="noopener">sefaa.dgac.gob.cl ↗</a></li>
        <li><a href="https://www.dgac.gob.cl/" target="_blank" rel="noopener">dgac.gob.cl ↗</a></li>
      </ul>
    </div>
    <div class="colophon">
      <span>Offline mirror · For research and reference</span>
      <span>Ley nº 20.285 · Acceso a la Información Pública</span>
    </div>
  </div>
</footer>

__LIGHTBOX__

<script id="arch-data" type="application/json">__DATA__</script>
<script>__SHARED_JS__</script>
</body>
</html>
'''
_nav = make_nav('chile', depth=1, internal_links=[
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
