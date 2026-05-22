#!/usr/bin/env python3
"""Build uk/index.html — UK National Archives MoD UFO files mirror.

The MoD UFO desk closed in 2009; ~52,000 pages of files transferred to
The National Archives at Kew over 2008-2017, all digitized and free to
view via Discovery (the TNA catalog). We surface the curated topic page
+ flagship file deep-links + the press release PDF.
Tone: Royal Navy blue (#012169).
"""
import json, os, sys, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _mirror_shared import SHARED_CSS, SHARED_JS
from _release_manifest import apply_manifest
from _site_template import make_nav, LIGHTBOX_HTML
ROOT = os.path.join(REPO, 'uk')


def git_tracked(rel_dir):
    try:
        out = subprocess.run(['git','-C',REPO,'ls-files',f'uk/{rel_dir}/'],
            capture_output=True, text=True, check=True).stdout
        prefix = f'uk/{rel_dir}/'
        return {ln[len(prefix):] for ln in out.splitlines() if ln.startswith(prefix)}
    except (subprocess.CalledProcessError, FileNotFoundError):
        p = os.path.join(ROOT, rel_dir)
        return set(os.listdir(p)) if os.path.isdir(p) else set()


tracked_pdfs = git_tracked('pdfs')
def Lp(fname): return f'pdfs/{fname}' if fname in tracked_pdfs else ''

ASSETS = [
    {
        't': 'PDF',
        'ti': 'Final Tranche of UFO Files Released — Press Release',
        'de': "TNA's press release accompanying the final tranche (24 files, 6,000+ pages spanning 1994–2000) — closing the MoD's 50-year UFO investigation programme.",
        'ag': 'The National Archives',
        'cat': 'Press Release',
        'date': '2013',
        'l': Lp('Final-Tranche-UFO-Files-Press-Release.pdf'),
        'u': Lp('Final-Tranche-UFO-Files-Press-Release.pdf') or 'https://cdn.nationalarchives.gov.uk/documents/final-tranche-of-UFO-files-released.pdf',
        's': 'https://cdn.nationalarchives.gov.uk/documents/final-tranche-of-UFO-files-released.pdf',
    },
    {
        't': 'CATALOG',
        'ti': 'AIR 2/17318 — Early UFO sightings letters (1963)',
        'de': "Earliest UFO correspondence held by TNA — letters to the Air Ministry on 'vehicles from other planets', 1963. AIR series record.",
        'ag': 'Air Ministry · UK',
        'cat': 'Catalog',
        'date': '1963',
        'l': '',
        'u': 'https://discovery.nationalarchives.gov.uk/details/r/C2645184',
        's': 'https://discovery.nationalarchives.gov.uk/details/r/C2645184',
    },
    {
        't': 'CATALOG',
        'ti': 'DEFE 24/1948/1 — Rendlesham Forest incident',
        'de': "The MoD file on the Rendlesham Forest incident of December 1980 — UK's best-known UFO case. Includes the Charles I. Halt 'Unexplained Lights' memo.",
        'ag': 'Ministry of Defence',
        'cat': 'Catalog',
        'date': 'Dec 1980',
        'region': 'Suffolk, England',
        'l': '',
        'u': 'https://discovery.nationalarchives.gov.uk/details/r/C10342055',
        's': 'https://discovery.nationalarchives.gov.uk/details/r/C10342055',
    },
    {
        't': 'CATALOG',
        'ti': 'DEFE 24/1958/1 — UFO policy and communications (1985–1995)',
        'de': "A decade of MoD UFO desk policy, correspondence, and communications with overseas embassies and ministers.",
        'ag': 'Ministry of Defence',
        'cat': 'Catalog',
        'date': '1985–1995',
        'l': '',
        'u': 'https://discovery.nationalarchives.gov.uk/details/r/C11707525',
        's': 'https://discovery.nationalarchives.gov.uk/details/r/C11707525',
    },
    {
        't': 'CATALOG',
        'ti': 'DEFE 24/1943/1 — Reports of alien encounters (1985–1992)',
        'de': "Reports submitted by members of the public claiming alien abduction, contact, or close-encounter experiences. Includes annotated sketches.",
        'ag': 'Ministry of Defence',
        'cat': 'Catalog',
        'date': '1985–1992',
        'l': '',
        'u': 'https://discovery.nationalarchives.gov.uk/details/r/C10130127',
        's': 'https://discovery.nationalarchives.gov.uk/details/r/C10130127',
    },
    {
        't': 'CATALOG',
        'ti': 'DEFE 31/172/1 — UFO observation reports (1982)',
        'de': "Printed MoD UFO report form: date, time, duration of sighting, weather conditions, witness details — the standard intake form used through the 1980s.",
        'ag': 'Ministry of Defence',
        'cat': 'Catalog',
        'date': '21 Feb 1982',
        'l': '',
        'u': 'https://discovery.nationalarchives.gov.uk/details/r/C10023454',
        's': 'https://discovery.nationalarchives.gov.uk/details/r/C10023454',
    },
    {
        't': 'CATALOG',
        'ti': 'DEFE 24/1930 — UFO correspondence (digitised, redacted)',
        'de': "Digital copy of DEFE 24/1930 with redactions, hosted on Discovery — example of TNA's fully-online UFO file delivery.",
        'ag': 'Ministry of Defence',
        'cat': 'Catalog',
        'l': '',
        'u': 'https://discovery.nationalarchives.gov.uk/details/r/C10130118',
        's': 'https://discovery.nationalarchives.gov.uk/details/r/C10130118',
    },
    {
        't': 'CATALOG',
        'ti': 'TNA — UFO Reports topic gateway',
        'de': "The National Archives' curated entry-point for every UFO/UAP file it holds. Browse by record group (AIR, DEFE, PREM) or by case.",
        'ag': 'The National Archives',
        'cat': 'Catalog',
        'l': '',
        'u': 'https://www.nationalarchives.gov.uk/explore-the-collection/explore-by-time-period/postwar/ufo-reports/',
        's': 'https://www.nationalarchives.gov.uk/explore-the-collection/explore-by-time-period/postwar/ufo-reports/',
    },
    {
        't': 'CATALOG',
        'ti': 'Discovery — TNA full catalog search',
        'de': "Discovery is TNA's master catalog — search 28 million records across all series. Filter by date, record group, or place.",
        'ag': 'The National Archives',
        'cat': 'Catalog',
        'l': '',
        'u': 'https://discovery.nationalarchives.gov.uk/',
        's': 'https://discovery.nationalarchives.gov.uk/',
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
                           'ag': _r.get('agency', 'UK MoD / TNA'), 'cat': _r.get('type', 'PDF').capitalize(),
                           'date': _r.get('date', ''), 'l': '', 'u': _url, 's': _r.get('src', ''),})

# TNA Discovery API harvest — 900+ catalog records from DEFE 24, AIR, PREM series
_tna_cache = os.path.join(ROOT, '.cache', 'tna-index.json')
if os.path.exists(_tna_cache):
    _seen_u = {a.get('u', '') for a in ASSETS}
    for _r in json.load(open(_tna_cache)):
        _url = _r.get('url', '')
        if _url and _url not in _seen_u:
            _seen_u.add(_url)
            _dept = _r.get('department', '')
            ASSETS.append({
                't': 'CATALOG',
                'ti': _r.get('title', ''),
                'de': _r.get('desc', ''),
                'ag': f'UK MoD / TNA ({_dept})' if _dept else 'UK MoD / TNA',
                'cat': 'Catalog',
                'date': _r.get('date', ''),
                'l': '', 'u': _url, 's': _url,
            })

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
<title>UK MoD UFO Files — The National Archives (Offline Mirror)</title>
<meta name="description" content="Offline mirror of the UK's Ministry of Defence UFO files at The National Archives, Kew. 52,000+ pages transferred 2008–2017.">
<link rel="canonical" href="https://realufo.org/uk/">
<meta property="og:title" content="UK MoD UFO Files — National Archives at Kew | realufo.org">
<meta property="og:description" content="Britain's Ministry of Defence UFO desk (1950-2009). 52,000+ pages transferred to The National Archives at Kew. Deep-links into Discovery: Rendlesham Forest, DEFE 24, AIR 2.">
<meta property="og:image" content="https://realufo.org/slideshow/FBI-Photo-1.jpg">
<meta property="og:url" content="https://realufo.org/uk/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="realufo.org">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="UK MoD UFO Files — National Archives at Kew | realufo.org">
<meta name="twitter:description" content="Britain's Ministry of Defence UFO desk (1950-2009). 52,000+ pages transferred to The National Archives at Kew. Deep-links into Discovery: Rendlesham Forest, DEFE 24, AIR 2.">
<meta name="twitter:image" content="https://realufo.org/slideshow/FBI-Photo-1.jpg">
<link rel="icon" type="image/svg+xml" href="./assets/favicon.svg">
<link rel="apple-touch-icon" href="./assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet">
<style>
__SHARED_CSS__
:root { --caution: #5b8def; --seal-from: #012169; --seal-mid: #001440; --seal-to: #000820; }
.seal { background: radial-gradient(circle at 50% 50%, var(--seal-from), var(--seal-mid) 60%, var(--seal-to)); }
body { background-image:
  radial-gradient(ellipse at 20% 0%, rgba(1,33,105,0.10) 0%, transparent 50%),
  radial-gradient(ellipse at 80% 100%, rgba(207,20,43,0.04) 0%, transparent 50%); background-attachment: fixed; }

.featured-cases{padding:32px 0;border-bottom:1px solid var(--rule)}
.featured-cases .container{max-width:1200px;margin:0 auto;padding:0 16px}
.featured-cases h2{font-family:var(--mono);font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:var(--caution);margin-bottom:20px;display:flex;align-items:baseline;gap:12px}
.featured-cases h2 .sub{font-family:var(--serif);font-style:italic;font-size:14px;color:var(--ink-dim);text-transform:none;letter-spacing:0}
.case-grid{display:grid;gap:14px;grid-template-columns:1fr}
@media (min-width:540px){.case-grid{grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}}
.case-card{display:block;padding:18px 20px;background:var(--panel);border:1px solid var(--rule);border-left:3px solid var(--caution);text-decoration:none;transition:border-color .15s,transform .15s}
.case-card:hover{border-color:var(--rule-strong);transform:translateY(-2px)}
.case-card .c-when{font-family:var(--mono);font-size:10px;color:var(--caution);letter-spacing:0.14em;text-transform:uppercase;margin-bottom:8px}
.case-card .c-name{font-family:var(--serif);font-size:18px;font-weight:600;color:var(--ink);margin-bottom:6px}
.case-card .c-desc{font-family:var(--serif);font-size:13px;color:var(--ink-dim);line-height:1.5}
</style>
</head>
<body>
<div class="scanlines"></div>

<div class="header-wrap">
<header>
  <div class="container">
    <a href="#top" class="brand">
      <div class="seal">UK</div>
      <div class="brand-text">
        <span class="super">The National Archives · Kew</span>
        <span class="name">MoD UFO Files</span>
      </div>
    </a>
    <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
    __NAV__
  </div>
</header>
</div>

<div class="hero" id="top">
  <div class="container">
    <div class="coords">51°28′53″N, 0°16′52″W · THE NATIONAL ARCHIVES · KEW, LONDON</div>
    <h1 class="hero-title">UK's <em>MoD UFO</em> Desk — closed for good, files all here.</h1>
    <p class="hero-sub">
      The Ministry of Defence's UFO desk and its public hotline ran from 1950 to 2009. On closure the
      surviving files — <strong>52,000+ pages</strong> across the AIR, DEFE and PREM record groups —
      were transferred to <strong>The National Archives at Kew</strong> in successive tranches between
      2008 and 2017. All are digitised and free to view via <a href="https://discovery.nationalarchives.gov.uk/" target="_blank" rel="noopener">Discovery</a>.
      Reusable under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/" target="_blank" rel="noopener">Open Government Licence v3</a>.
      Source: <a href="https://www.nationalarchives.gov.uk/explore-the-collection/explore-by-time-period/postwar/ufo-reports/" target="_blank" rel="noopener">TNA UFO Reports</a>.
    </p>
  </div>
</div>

<section id="headlines" class="headlines">
  <div class="container">
    <div class="section-label">§ Headlines · UK MoD UFO Desk, distilled</div>
    <div class="head-grid">
      <div class="head-card"><div class="h-label">Active</div><div class="h-text"><strong>1950–2009</strong> — 59 years of MoD investigations and a public hotline.</div></div>
      <div class="head-card"><div class="h-label">Pages released</div><span class="h-num">52 000+</span><div class="h-text">All digitised, all free to download.</div></div>
      <div class="head-card"><div class="h-label">Closure</div><span class="h-num">2009</span><div class="h-text">UFO desk &amp; hotline shut down — files transferred to Kew.</div></div>
      <div class="head-card"><div class="h-label">Final tranche</div><div class="h-text"><strong>24 files · 6,000 pages</strong> covering 1994–2000.</div></div>
      <div class="head-card"><div class="h-label">Flagship case</div><div class="h-text">Rendlesham Forest (Dec 1980) — the 'British Roswell'.</div></div>
      <div class="head-card"><div class="h-label">License</div><div class="h-text">Open Government Licence v3 — reusable, attributable.</div></div>
    </div>
  </div>
</section>

<section class="featured-cases" id="cases">
  <div class="container">
    <h2>Featured cases <span class="sub">— deep-dive stories</span></h2>
    <div class="case-grid">
      <a class="case-card" href="./rendlesham.html"><div class="c-when">RAF Bentwaters · Dec 1980</div><div class="c-name">Rendlesham Forest</div><div class="c-desc">UK's best-known UFO case</div></a>
<a class="case-card" href="./story.html"><div class="c-when">DEFE 24 · 50 years</div><div class="c-name">UK MoD — full story</div><div class="c-desc">Programme history 1950-2009</div></a>

    </div>
  </div>
</section>

<section id="archive">
  <div class="container">
    <div class="section-label">§ Records · Key files + catalog deep-links</div>
    <h2>Every DEFE / AIR / PREM file with a UFO bearing.</h2>
    <p class="lede">
      Hand-picked highlights from TNA's UFO topic page plus deep-links into Discovery for the full
      collection. The press release PDF below is local; everything else loads on Discovery itself.
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
      <h4>UK Mirror</h4>
      <p style="color: var(--ink-dim); font-family: var(--serif); margin-bottom: 14px;">
        Offline archival mirror of The National Archives' MoD UFO collection at Kew. Crown-copyright material
        reused under the Open Government Licence v3.
      </p>
      <p style="color: var(--ink-faint); font-size: 10px; letter-spacing: 0.1em;">Source: nationalarchives.gov.uk · captured 2026.</p>
    </div>
    <div>
      <h4>Related Mirrors</h4>
      <ul>
        <li><a href="../index.html">war.gov / UFO Release 01</a></li>
        <li><a href="../aaro/index.html">AARO — DoW</a></li>
        <li><a href="../nasa/index.html">NASA UAP Study</a></li>
        <li><a href="../nara/index.html">NARA UAP Records</a></li>
        <li><a href="../geipan/index.html">France GEIPAN</a></li>
      </ul>
    </div>
    <div>
      <h4>Source</h4>
      <ul>
        <li><a href="https://www.nationalarchives.gov.uk/explore-the-collection/explore-by-time-period/postwar/ufo-reports/" target="_blank" rel="noopener">TNA UFO reports ↗</a></li>
        <li><a href="https://discovery.nationalarchives.gov.uk/" target="_blank" rel="noopener">Discovery (full catalog) ↗</a></li>
        <li><a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/" target="_blank" rel="noopener">OGL v3 ↗</a></li>
      </ul>
    </div>
    <div class="colophon">
      <span>Offline mirror · For research and reference</span>
      <span>OGL v3 / Crown copyright</span>
    </div>
  </div>
</footer>

__LIGHTBOX__

<script id="arch-data" type="application/json">__DATA__</script>
<script>__SHARED_JS__</script>
</body>
</html>
'''

_nav = make_nav('uk', depth=1, internal_links=[
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
