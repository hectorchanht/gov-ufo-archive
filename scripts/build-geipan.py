#!/usr/bin/env python3
"""Build geipan/index.html — France GEIPAN (CNES) mirror.

Renders the full 3,351-case GEIPAN database scraped via
scripts/scrape-geipan.py (cached at .cache/cases.json) alongside the
official PDFs / case videos / imagery. Tone: French blue (#0055a4).
"""
import json, os, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, 'geipan')
CACHE = os.path.join(ROOT, '.cache')

def git_tracked(rel_dir):
    try:
        out = subprocess.run(['git','-C',REPO,'ls-files',f'geipan/{rel_dir}/'],
            capture_output=True, text=True, check=True).stdout
        prefix = f'geipan/{rel_dir}/'
        return {ln[len(prefix):] for ln in out.splitlines() if ln.startswith(prefix)}
    except Exception:
        p = os.path.join(ROOT, rel_dir)
        return set(os.listdir(p)) if os.path.isdir(p) else set()

tracked_pdfs = git_tracked('pdfs')
tracked_vids = git_tracked('videos')
tracked_imgs = git_tracked('assets/images')
def Lp(f): return f'pdfs/{f}' if f in tracked_pdfs else ''
def Lv(f): return f'videos/{f}' if f in tracked_vids else ''
def Li(f): return f'assets/images/{f}' if f in tracked_imgs else ''


CURATED = [
    {
        't': 'PDF',
        'ti': 'GEIPAN — FAQ (English)',
        'de': "Official press FAQ — history, methodology, classification scheme.",
        'ag': 'GEIPAN / CNES', 'cat': 'FAQ', 'date': '2021',
        'l': Lp('GEIPAN-FAQ-English.pdf'),
        'u': Lp('GEIPAN-FAQ-English.pdf') or 'https://www.cnes-geipan.fr/sites/default/files/2021-08/FAQ%20-%20Press%20-%20English.pdf',
        's': 'https://www.cnes-geipan.fr/sites/default/files/2021-08/FAQ%20-%20Press%20-%20English.pdf',
    },
    {
        't': 'PDF',
        'ti': 'GEIPAN — FAQ (Français)',
        'de': "Dossier de presse officiel — historique, méthodologie, classification PAN A/B/C/D.",
        'ag': 'GEIPAN / CNES', 'cat': 'FAQ', 'date': '2021',
        'l': Lp('GEIPAN-FAQ-Francais.pdf'),
        'u': Lp('GEIPAN-FAQ-Francais.pdf') or 'https://www.cnes-geipan.fr/sites/default/files/2021-08/FAQ%20-%20Dossier%20presse.pdf',
        's': 'https://www.cnes-geipan.fr/sites/default/files/2021-08/FAQ%20-%20Dossier%20presse.pdf',
    },
    {
        't': 'PDF',
        'ti': 'GEIPAN — Mission, History, Methodology (English)',
        'de': "Mission, 1977-present history, scientific methodology, PAN A/B/C/D taxonomy.",
        'ag': 'GEIPAN / CNES', 'cat': 'Mission', 'date': '2021',
        'l': Lp('GEIPAN-Mission-Method-English.pdf'),
        'u': Lp('GEIPAN-Mission-Method-English.pdf') or 'https://www.cnes-geipan.fr/sites/default/files/2021-08/GEIPAN-informationenglish.pdf',
        's': 'https://www.cnes-geipan.fr/sites/default/files/2021-08/GEIPAN-informationenglish.pdf',
    },
    {
        't': 'PDF',
        'ti': 'GEIPAN — Mission, Historique, Méthodologie (Français)',
        'de': "Document officiel — mission, historique, méthodologie, classification PAN A/B/C/D.",
        'ag': 'GEIPAN / CNES', 'cat': 'Mission', 'date': '2021',
        'l': Lp('GEIPAN-Mission-Methode-Francais.pdf'),
        'u': Lp('GEIPAN-Mission-Methode-Francais.pdf') or 'https://www.cnes-geipan.fr/sites/default/files/2021-08/GEIPAN-informations.pdf',
        's': 'https://www.cnes-geipan.fr/sites/default/files/2021-08/GEIPAN-informations.pdf',
    },
    {
        't': 'VID', 'ti': 'Saint-Germain-en-Laye (78) — 30 May 2020',
        'de': "Witness video of an unidentified luminous object.",
        'ag': 'GEIPAN', 'cat': 'Case Video', 'date': '30 May 2020', 'region': 'Île-de-France',
        'l': Lv('Saint-Germain-en-Laye-2020-05-30.mp4'),
        'u': Lv('Saint-Germain-en-Laye-2020-05-30.mp4') or 'https://www.cnes-geipan.fr/sites/default/files/2021-08/SAINT-GERMAIN-EN-LAYE%20%2878%29%2030.05.2020.mp4',
        's': 'https://www.cnes-geipan.fr/fr/recherche/cas',
    },
    {
        't': 'VID', 'ti': 'Lyon (69) — 19 December 2019',
        'de': "Witness video of an unidentified phenomenon.",
        'ag': 'GEIPAN', 'cat': 'Case Video', 'date': '19 Dec 2019', 'region': 'Auvergne-Rhône-Alpes',
        'l': Lv('Lyon-2019-12-19.mp4'),
        'u': Lv('Lyon-2019-12-19.mp4') or 'https://www.cnes-geipan.fr/sites/default/files/2021-08/LYON%20%2869%29%2019.12.2019.mp4',
        's': 'https://www.cnes-geipan.fr/fr/recherche/cas',
    },
    {
        't': 'IMG', 'ti': 'Cases by Phenomenon Type (2024)',
        'de': "GEIPAN's 2024 breakdown of identified phenomena.",
        'ag': 'GEIPAN', 'cat': 'Statistics', 'date': '2024',
        'l': Li('GEIPAN-Cases-By-Phenomenon-2024.png'),
        'u': Li('GEIPAN-Cases-By-Phenomenon-2024.png') or '',
        's': 'https://www.cnes-geipan.fr/fr/stats',
    },
    {
        't': 'IMG', 'ti': 'IPACO® team (2025)',
        'de': "GEIPAN's IPACO® image/video authentication software team.",
        'ag': 'GEIPAN / CNES', 'cat': 'Imagery', 'date': '2025',
        'l': Li('IPACO-team-2025.jpg'),
        'u': Li('IPACO-team-2025.jpg') or '',
        's': 'https://www.cnes-geipan.fr/',
    },
    {
        't': 'IMG', 'ti': 'Starlink satellite flare note',
        'de': "GEIPAN's 2024 information note on Starlink-related misidentifications.",
        'ag': 'GEIPAN', 'cat': 'Imagery', 'date': '2024',
        'l': Li('Starlink-flare-note-2024.jpg'),
        'u': Li('Starlink-flare-note-2024.jpg') or '',
        's': 'https://www.cnes-geipan.fr/',
    },
]

cases = []
cases_path = os.path.join(CACHE, 'cases.json')
if os.path.exists(cases_path):
    raw = json.load(open(cases_path, encoding='utf-8'))
    for c in raw:
        title = f"{c['location']} ({c['dept_code']}) — {c['observation_date']}" if c.get('observation_date') else c.get('location','?')
        cat = {
            'A':'PAN A — Identified',
            'B':'PAN B — Probably identified',
            'C':'PAN C — Insufficient data',
            'D':'PAN D — Unexplained',
            'D1':'PAN D1 — Unexplained (mod.)',
            'D2':'PAN D2 — Unexplained (strong)',
        }.get(c.get('classification',''), 'PAN ?')
        cases.append({
            't': 'CASE',
            'ti': title,
            'ag': 'GEIPAN',
            'cat': cat,
            'region': c.get('department',''),
            'date': c.get('observation_date',''),
            'cls': c.get('classification',''),
            'l': '',
            'u': c['url'],
            's': c['url'],
        })

ASSETS = CURATED + cases

cls_count = {}
for c in cases:
    cls_count[c['cls']] = cls_count.get(c['cls'], 0) + 1

stats = {
    'total': len(ASSETS),
    'local_total': sum(1 for a in ASSETS if a.get('l')),
    'cases_total': len(cases),
    'pdf_total': sum(1 for a in ASSETS if a['t'] == 'PDF'),
    'vid_total': sum(1 for a in ASSETS if a['t'] == 'VID'),
    'img_total': sum(1 for a in ASSETS if a['t'] == 'IMG'),
}

data_json = json.dumps({'assets': ASSETS, 'stats': stats}, ensure_ascii=False).replace('</script', '<\\/script')


def pct(k):
    if not cases: return '?'
    n = cls_count.get(k, 0)
    return f'{n / len(cases) * 100:.2f}%'

import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _mirror_shared import SHARED_CSS, SHARED_JS
from _site_template import make_nav, LIGHTBOX_HTML, _I18N_JSON

TOTAL = f'{stats["cases_total"]:,}'
NOW_STAMP = datetime.datetime.utcnow().strftime('%b %Y')
PCT_A = pct('A'); PCT_B = pct('B'); PCT_C = pct('C')
PCT_D = f'{(cls_count.get("D",0)+cls_count.get("D1",0)+cls_count.get("D2",0)) / max(1,len(cases)) * 100:.2f}%'

PAGE = (
'<!DOCTYPE html><html lang="en"><head>'
'<meta charset="UTF-8">'
'<meta name="viewport" content="width=device-width, initial-scale=1.0">'
f'<title>GEIPAN — France\'s civilian UAP archive ({TOTAL} cases) | realufo.org</title>'
f'<meta name="description" content="Offline mirror of France\'s GEIPAN — every one of {TOTAL} classified UAP cases (1977–present), plus official FAQ/methodology PDFs and sample case videos.">'
'<link rel="canonical" href="https://realufo.org/geipan/">'
f'<meta property="og:title" content="GEIPAN — {TOTAL} cases | realufo.org">'
f'<meta property="og:description" content="GEIPAN at CNES — the world\'s longest-running civilian UAP programme. {TOTAL} classified cases. Full database mirrored.">'
'<meta property="og:image" content="https://realufo.org/geipan/assets/images/IPACO-team-2025.jpg">'
'<meta property="og:url" content="https://realufo.org/geipan/">'
'<meta property="og:type" content="website"><meta property="og:site_name" content="realufo.org">'
'<meta name="twitter:card" content="summary_large_image">'
f'<meta name="twitter:title" content="GEIPAN — {TOTAL} cases | realufo.org">'
f'<meta name="twitter:description" content="GEIPAN at CNES — {TOTAL} classified UAP cases mirrored.">'
'<meta name="twitter:image" content="https://realufo.org/geipan/assets/images/IPACO-team-2025.jpg">'
'<link rel="icon" type="image/svg+xml" href="./assets/favicon.svg">'
'<link rel="apple-touch-icon" href="./assets/favicon.svg">'
'<link rel="preconnect" href="https://fonts.googleapis.com">'
'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
'<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet">'
'<style>'
+ SHARED_CSS +
':root { --caution: #5b9bd5; }\n'
'.seal { background: radial-gradient(circle at 50% 50%, #0055a4, #003278 60%, #001f4d); }\n'
'body { background-image: radial-gradient(ellipse at 20% 0%, rgba(0,85,164,0.08) 0%, transparent 50%); background-attachment: fixed; }\n'
'.badge.cls-A, .badge.cls-B { color: #6fbf52; }\n'
'.badge.cls-C { color: #d4a017; }\n'
'.badge.cls-D, .badge.cls-D1, .badge.cls-D2 { color: #c9362c; }\n'
'.glyph-case { background: linear-gradient(135deg, rgba(91,155,213,0.12), rgba(0,0,0,0)); }\n'
'.glyph-case .ico { color: var(--caution); border-color: var(--caution); font-size: 14px; padding: 3px 8px; }\n'
'.video-glyph { background: linear-gradient(135deg, rgba(0,85,164,0.14), rgba(239,65,53,0.05)); }\n'
'.filter-bar { display: flex; flex-direction: column; gap: 10px; padding: 14px 0; border-bottom: 1px dashed var(--rule); }\n'
'@media (min-width: 720px) { .filter-bar { flex-direction: row; align-items: center; gap: 20px; flex-wrap: wrap; } }\n'
'.filter-bar label { font-family: var(--mono); font-size: 10px; color: var(--ink-faint); letter-spacing: 0.08em; text-transform: uppercase; display: flex; align-items: center; gap: 8px; }\n'
'.filter-bar select { background: var(--panel); color: var(--ink); border: 1px solid var(--rule-strong); padding: 6px 10px; font-family: var(--mono); font-size: 11px; max-width: 100%; }\n'
'.pagination { display: flex; gap: 6px; justify-content: center; align-items: center; flex-wrap: wrap; margin: 24px 0 0; padding: 20px 0; border-top: 1px solid var(--rule); }\n'
'.pagination button { font-family: var(--mono); font-size: 11px; padding: 8px 12px; min-width: 36px; border: 1px solid var(--rule-strong); background: var(--panel); color: var(--ink-dim); cursor: pointer; }\n'
'.pagination button:hover:not(:disabled) { color: var(--ink); border-color: var(--caution); }\n'
'.pagination button.active { background: var(--caution); color: var(--bg); border-color: var(--caution); font-weight: 700; }\n'
'.pagination button:disabled { opacity: 0.3; cursor: not-allowed; }\n'
'.pagination .ellipsis { color: var(--ink-faint); padding: 0 6px; font-family: var(--mono); }\n'
'.pagination .info { color: var(--ink-faint); font-family: var(--mono); font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; flex-basis: 100%; text-align: center; margin-top: 8px; }\n'
'@media (min-width: 720px) { .pagination .info { flex-basis: auto; margin: 0 0 0 12px; text-align: left; } }\n'
'.result-count { font-family: var(--mono); font-size: 11px; color: var(--ink-faint); letter-spacing: 0.12em; text-transform: uppercase; padding: 18px 0 8px; }\n'
'.result-count b { color: var(--caution); }\n'
'</style></head>\n'
'<body><div class="scanlines"></div>\n'
'<div class="header-wrap"><header><div class="container">'
'<a href="#top" class="brand">'
'<div class="seal">GEIPAN</div>'
'<div class="brand-text"><span class="super">Groupe d\'Études · Phénomènes Aérospatiaux</span>'
'<span class="name">GEIPAN · CNES</span></div></a>'
'<button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>'
+ make_nav('geipan', depth=1, internal_links=[
    ('Intro', '#top', 'intro'),
    ('Headlines', '#headlines', 'headlines'),
    ('Cases', '#archive', 'archive'),
]) +
'</div></header></div>\n'
'<div class="hero" id="top"><div class="container">'
'<div class="coords">43°33′N, 1°28′E · CENTRE NATIONAL D\'ÉTUDES SPATIALES · TOULOUSE</div>'
'<h1 class="hero-title">France\'s <em>civilian</em> UAP office — every case since 1977.</h1>'
'<p class="hero-sub">'
'<strong>GEIPAN</strong> at <a href="https://cnes.fr/" target="_blank" rel="noopener">CNES</a> '
'is the world\'s longest-running official civilian UAP programme. '
f'<strong>{TOTAL} cases</strong> classified and published in the '
'<a href="https://www.cnes-geipan.fr/fr/recherche/cas" target="_blank" rel="noopener">public database</a>'
' — every one of them browsable below. Tone: French blue.'
'</p></div></div>\n'
'<section id="headlines" class="headlines"><div class="container">'
'<div class="section-label">§ Headlines · GEIPAN, distilled</div>'
'<div class="head-grid">'
'<div class="head-card"><div class="h-label">Founded</div><span class="h-num">1977</span><div class="h-text">As GEPAN; renamed SEPRA (1988), GEIPAN (2005).</div></div>'
f'<div class="head-card"><div class="h-label">Total cases</div><span class="h-num">{TOTAL}</span><div class="h-text">Classified &amp; published (scraped {NOW_STAMP}).</div></div>'
f'<div class="head-card"><div class="h-label">PAN A</div><div class="h-text"><strong>{PCT_A}</strong> — phenomenon perfectly identified.</div></div>'
f'<div class="head-card"><div class="h-label">PAN B</div><div class="h-text"><strong>{PCT_B}</strong> — phenomenon probably identified.</div></div>'
f'<div class="head-card"><div class="h-label">PAN C</div><div class="h-text"><strong>{PCT_C}</strong> — unidentified (insufficient data).</div></div>'
f'<div class="head-card"><div class="h-label">PAN D</div><div class="h-text"><strong>{PCT_D}</strong> — unidentified after full investigation.</div></div>'
'</div></div></section>\n'
'<section id="archive"><div class="container">'
'<div class="section-label">§ Cases · Full database (search · filter · paginate)</div>'
'<h2>Every classified case GEIPAN has published.</h2>'
f'<p class="lede">All <strong>{TOTAL}</strong> cases from the GEIPAN public database, plus the official methodology PDFs and sample case videos. Filter by PAN class (A/B/C/D), department, or observation year. Click any case → full investigative file on cnes-geipan.fr.</p>'
'<div class="stats-grid" id="arch-stats"></div>'
'<div class="arch-controls-bar">'
'<div class="tabs" id="arch-tabs"></div>'
'<div class="search-wrap"><input id="arch-search" type="search" placeholder="Search location, department, date…" autocomplete="off"></div>'
'</div>'
'<div class="filter-bar">'
'<label>Class:<select id="filter-cls"><option value="">All</option><option value="A">PAN A — identified</option><option value="B">PAN B — probably identified</option><option value="C">PAN C — insufficient data</option><option value="D">PAN D — unexplained</option><option value="D1">PAN D1</option><option value="D2">PAN D2</option></select></label>'
'<label>Region:<select id="filter-region"><option value="">All</option></select></label>'
'<label>Year:<select id="filter-year"><option value="">All</option></select></label>'
'<label>Per page:<select id="filter-perpage"><option>24</option><option selected>48</option><option>96</option><option>192</option></select></label>'
'</div>'
'<div class="result-count" id="arch-count"></div>'
'<div class="arch-grid" id="arch-grid"></div>'
'<div class="empty" id="arch-empty" hidden>No records match.</div>'
'<nav class="pagination" id="pagination"></nav>'
'</div></section>\n'
'<footer><div class="container">'
'<div><h4>GEIPAN Mirror</h4>'
'<p style="color: var(--ink-dim); font-family: var(--serif); margin-bottom: 14px;">'
'Offline archival mirror of GEIPAN at CNES — the entire public case database scraped &amp; cached. Reusable under Loi n° 78-753.'
'</p>'
'<p style="color: var(--ink-faint); font-size: 10px; letter-spacing: 0.1em;">Source: cnes-geipan.fr · scraped 2026.</p>'
'</div>'
'<div><h4>Related Mirrors</h4><ul>'
'<li><a href="../index.html">war.gov / UFO Release 01</a></li>'
'<li><a href="../aaro/index.html">AARO — DoW</a></li>'
'<li><a href="../nasa/index.html">NASA UAP Study</a></li>'
'<li><a href="../nara/index.html">NARA UAP Records</a></li>'
'<li><a href="../uk/index.html">UK MoD UFO Files</a></li>'
'</ul></div>'
'<div><h4>Source</h4><ul>'
'<li><a href="https://www.cnes-geipan.fr/" target="_blank" rel="noopener">cnes-geipan.fr ↗</a></li>'
'<li><a href="https://www.cnes-geipan.fr/fr/recherche/cas" target="_blank" rel="noopener">Case search ↗</a></li>'
'<li><a href="https://www.cnes-geipan.fr/fr/stats" target="_blank" rel="noopener">Statistics ↗</a></li>'
'</ul></div>'
'<div class="colophon"><span>Offline mirror · For research and reference</span><span>realufo.org</span></div>'
'</div></footer>'
f'<script id="arch-data" type="application/json">{data_json}</script>'
f'<script>{SHARED_JS}</script>'
'<script>\n'
'(() => {\n'
'  const D = JSON.parse(document.getElementById("arch-data").textContent);\n'
'  const items = D.assets;\n'
'  const STATS = D.stats;\n'
'  function esc(s){return (s||"").replace(/[&<>"\']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","\'":"&#39;"}[c]));}\n'
'  document.getElementById("arch-stats").innerHTML = [\n'
'    ["Total", STATS.total], ["Cases", STATS.cases_total],\n'
'    ["Documents", STATS.pdf_total], ["Videos", STATS.vid_total],\n'
'    ["Images", STATS.img_total],\n'
'    ["PAN D", items.filter(a => a.cls && a.cls.startsWith("D")).length],\n'
'  ].map(([k,v]) => `<div class="stat"><b>${v}</b><small>${k}</small></div>`).join("");\n'
'  const regions = Array.from(new Set(items.map(a => a.region).filter(Boolean))).sort();\n'
'  const regionSel = document.getElementById("filter-region");\n'
'  regions.forEach(r => { const o = document.createElement("option"); o.value=r; o.textContent=r; regionSel.appendChild(o); });\n'
'  const years = Array.from(new Set(items.map(a => (a.date||"").split("/").pop()).filter(y => y && /^\\d{4}$/.test(y)))).sort().reverse();\n'
'  const yearSel = document.getElementById("filter-year");\n'
'  years.forEach(y => { const o = document.createElement("option"); o.value=y; o.textContent=y; yearSel.appendChild(o); });\n'
'  const TABS = [{key:"ALL",label:"All"},{key:"CASE",label:"Cases"},{key:"PDF",label:"Docs"},{key:"VID",label:"Videos"},{key:"IMG",label:"Images"}];\n'
'  const state = { tab:"ALL", q:"", cls:"", region:"", year:"", perPage:48, page:1 };\n'
'  const tabsEl = document.getElementById("arch-tabs");\n'
'  function tabCount(k){ return k === "ALL" ? items.length : items.filter(a => a.t === k).length; }\n'
'  tabsEl.innerHTML = TABS.map(t => `<button class="tab${t.key===state.tab?" active":""}" data-key="${t.key}">${t.label}<span class="count">${tabCount(t.key)}</span></button>`).join("");\n'
'  tabsEl.addEventListener("click", e => { const t = e.target.closest(".tab"); if (!t) return; state.tab = t.dataset.key; state.page=1; tabsEl.querySelectorAll(".tab").forEach(x => x.classList.toggle("active", x.dataset.key === state.tab)); render(); });\n'
'  document.getElementById("arch-search").addEventListener("input", e => { state.q = e.target.value.trim().toLowerCase(); state.page=1; render(); });\n'
'  document.getElementById("filter-cls").addEventListener("change", e => { state.cls = e.target.value; state.page=1; render(); });\n'
'  document.getElementById("filter-region").addEventListener("change", e => { state.region = e.target.value; state.page=1; render(); });\n'
'  document.getElementById("filter-year").addEventListener("change", e => { state.year = e.target.value; state.page=1; render(); });\n'
'  document.getElementById("filter-perpage").addEventListener("change", e => { state.perPage = parseInt(e.target.value,10); state.page=1; render(); });\n'
'  function glyphFor(a){\n'
'    if (a.t === "IMG" && a.l) { const fb = a.s ? `onerror="this.onerror=null;this.src=\'${esc(a.s)}\';"` : ""; return `<img loading="lazy" src="./${a.l}" alt="${esc(a.ti)}" ${fb}>`; }\n'
'    if (a.t === "VID") return `<div class="pdf-glyph video-glyph"><span class="ico">▶</span><span>${esc(a.region||a.cat||"Case")}</span></div>`;\n'
'    if (a.t === "CASE") return `<div class="pdf-glyph glyph-case"><span class="ico">${esc(a.cls||"PAN")}</span><span>${esc(a.region||"GEIPAN")}</span></div>`;\n'
'    return `<div class="pdf-glyph"><span class="ico">PDF</span><span>${esc(a.ag||"Document")}</span></div>`;\n'
'  }\n'
'  function metaFor(a){\n'
'    const rows = [];\n'
'    if (a.cat) rows.push(["Cat", a.cat]);\n'
'    if (a.region) rows.push(["Region", a.region]);\n'
'    if (a.date) rows.push(["Date", a.date]);\n'
'    return `<dl class="card-meta">${rows.map(r => `<dt>${r[0]}</dt><dd>${esc(r[1])}</dd>`).join("")}</dl>`;\n'
'  }\n'
'  function actionsFor(a){\n'
'    const out = [];\n'
'    if (a.l) { out.push(`<a href="./${esc(a.l)}" target="_blank">${a.t==="PDF"?"Open PDF":"View"}</a>`); out.push(`<a href="./${esc(a.l)}" download>Download</a>`); }\n'
'    else if (a.t === "CASE") { out.push(`<a href="${esc(a.u)}" target="_blank" rel="noopener">Case file ↗</a>`); }\n'
'    else if (a.u && a.t === "PDF") { out.push(`<a href="${esc(a.u)}" target="_blank" rel="noopener">Open PDF</a>`); }\n'
'    else if (a.u) { out.push(`<a href="${esc(a.u)}" target="_blank" rel="noopener">Open ↗</a>`); }\n'
'    return `<div class="card-actions">${out.join("")}</div>`;\n'
'  }\n'
'  function cardHtml(a, gidx){\n'
'    const clsBadge = a.cls ? `<span class="badge cls-${a.cls}">${esc(a.cls)}</span>` : `<span class="badge">${esc(a.t)}</span>`;\n'
'    return `<article class="card" data-idx="${gidx}"><div class="card-media">${glyphFor(a)}${clsBadge}</div><div class="card-body"><div class="card-title">${esc(a.ti)}</div>${metaFor(a)}${actionsFor(a)}</div></article>`;\n'
'  }\n'
'  function filtered(){\n'
'    return items.filter(a => {\n'
'      if (state.tab !== "ALL" && a.t !== state.tab) return false;\n'
'      if (state.cls) { if (!(a.cls === state.cls || (state.cls === "D" && (a.cls === "D" || a.cls === "D1" || a.cls === "D2")))) return false; }\n'
'      if (state.region && a.region !== state.region) return false;\n'
'      if (state.year && !((a.date||"").endsWith("/" + state.year))) return false;\n'
'      if (state.q) { const hay = [a.ti, a.region, a.cat, a.date, a.ag].join(" ").toLowerCase(); if (!hay.includes(state.q)) return false; }\n'
'      return true;\n'
'    });\n'
'  }\n'
'  const grid = document.getElementById("arch-grid");\n'
'  const emptyEl = document.getElementById("arch-empty");\n'
'  const countEl = document.getElementById("arch-count");\n'
'  const pagEl = document.getElementById("pagination");\n'
'  function paginate(list){\n'
'    const total = list.length;\n'
'    const pages = Math.max(1, Math.ceil(total / state.perPage));\n'
'    if (state.page > pages) state.page = pages;\n'
'    const start = (state.page - 1) * state.perPage;\n'
'    return { slice: list.slice(start, start+state.perPage), pages, total, start };\n'
'  }\n'
'  function renderPagination(pages, total, start){\n'
'    if (pages <= 1) { pagEl.innerHTML = `<span class="info">${total} ${total===1?"item":"items"}</span>`; return; }\n'
'    const p = state.page;\n'
'    const set = new Set([1,2,pages-1,pages,p-1,p,p+1]);\n'
'    const sorted = Array.from(set).filter(n => n>=1 && n<=pages).sort((a,b)=>a-b);\n'
'    const out = [`<button data-go="prev"${p===1?" disabled":""}>‹</button>`];\n'
'    let prev = 0;\n'
'    for (const n of sorted) { if (prev && n - prev > 1) out.push(`<span class="ellipsis">…</span>`); out.push(`<button data-go="${n}"${n===p?" class=\\"active\\"":""}>${n}</button>`); prev = n; }\n'
'    out.push(`<button data-go="next"${p===pages?" disabled":""}>›</button>`);\n'
'    out.push(`<span class="info">Page ${p} of ${pages} · ${start+1}–${Math.min(start+state.perPage, total)} of ${total}</span>`);\n'
'    pagEl.innerHTML = out.join("");\n'
'  }\n'
'  pagEl.addEventListener("click", e => { const b = e.target.closest("button[data-go]"); if (!b) return; const g = b.dataset.go; if (g === "prev") state.page = Math.max(1, state.page-1); else if (g === "next") state.page += 1; else state.page = parseInt(g,10); render(true); });\n'
'  function render(scroll){\n'
'    const list = filtered();\n'
'    const { slice, pages, total, start } = paginate(list);\n'
'    countEl.innerHTML = `Showing <b>${slice.length}</b> of ${total} items${state.q?` matching "${esc(state.q)}"`:""}`;\n'
'    grid.innerHTML = slice.map((a, i) => cardHtml(a, start + i)).join("");\n'
'    emptyEl.hidden = total > 0;\n'
'    renderPagination(pages, total, start);\n'
'    if (scroll) document.getElementById("archive").scrollIntoView({ behavior:"smooth", block:"start" });\n'
'  }\n'
'  render();\n'
'})();\n'
'</script></body></html>'
)

open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(PAGE)
print(f'wrote {ROOT}/index.html ({len(PAGE):,} B) · {stats["cases_total"]} cases + {len(CURATED)} curated')
