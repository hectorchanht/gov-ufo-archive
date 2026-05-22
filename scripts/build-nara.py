#!/usr/bin/env python3
"""Build nara/index.html — curated NARA UAP records gateway.

NARA's UAP holdings span dozens of record groups and millions of pages;
this mirror surfaces the official topic pages + the legal basis (2024
NDAA) + direct deep-links into the NARA Catalog. Tone color: silver
charcoal (#9ca3af).
"""
import json, os, subprocess, sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from _release_manifest import apply_manifest
from _site_template import make_nav, LIGHTBOX_HTML, _I18N_JSON

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, 'nara')


def git_tracked(rel_dir):
    try:
        out = subprocess.run(
            ['git', '-C', REPO, 'ls-files', f'nara/{rel_dir}/'],
            capture_output=True, text=True, check=True,
        ).stdout
        prefix = f'nara/{rel_dir}/'
        return {ln[len(prefix):] for ln in out.splitlines() if ln.startswith(prefix)}
    except (subprocess.CalledProcessError, FileNotFoundError):
        p = os.path.join(ROOT, rel_dir)
        return set(os.listdir(p)) if os.path.isdir(p) else set()


tracked_pages = git_tracked('pages')
tracked_pdfs = git_tracked('pdfs')

def Lp(fname): return f'pages/{fname}' if fname in tracked_pages else ''
def Lf(fname): return f'pdfs/{fname}' if fname in tracked_pdfs else ''


ASSETS = [
    # Gateway / legal basis
    {
        't': 'PDF',
        'ti': '2024 National Defense Authorization Act — Public Law 118-31',
        'de': "The 2024 NDAA established Record Group 615 ('Unidentified Anomalous Phenomena Records Collection') at NARA, mandating that federal agencies transfer UAP records and authorising a 25-year sealing review.",
        'ag': 'U.S. Congress',
        'cat': 'Legal',
        'date': 'Dec 22, 2023',
        'l': Lf('2024-NDAA-Public-Law-118-31.pdf'),
        'u': 'https://github.com/hectorchanht/war-gov-ufo-release/releases/download/pdfs-v1/2024-NDAA-Public-Law-118-31.pdf',
        's': 'https://www.congress.gov/118/bills/hr2670/BILLS-118hr2670enr.pdf',
    },
    # NARA topic pages (one card per page)
    {
        't': 'PAGE',
        'ti': 'UAP Records — Topic Gateway',
        'de': 'NARA\'s top-level gateway to UAP-related records across every collection it holds.',
        'ag': 'NARA',
        'cat': 'Gateway',
        'l': Lp('topic.html'),
        'u': 'https://www.archives.gov/research/topics/uaps',
    },
    {
        't': 'PAGE',
        'ti': 'Record Group 615 — Unidentified Anomalous Phenomena Records Collection',
        'de': 'The dedicated RG established by the 2024 NDAA. Holdings transferred from DoD, ODNI, AARO, FBI, CIA, NASA, DOE, NSA, and others.',
        'ag': 'NARA',
        'cat': 'Record Group',
        'l': Lp('rg-615.html'),
        'u': 'https://www.archives.gov/research/topics/uaps/rg-615',
    },
    {
        't': 'PAGE',
        'ti': 'Photographs',
        'de': 'NARA\'s photographic UAP holdings — Air Force Project Blue Book stills, NICAP files, presidential library photos.',
        'ag': 'NARA',
        'cat': 'Imagery',
        'l': Lp('photographs.html'),
        'u': 'https://www.archives.gov/research/topics/uaps/photographs',
    },
    {
        't': 'PAGE',
        'ti': 'Moving Images and Sound Recordings',
        'de': 'Films and audio relating to UAP investigations across federal agencies.',
        'ag': 'NARA',
        'cat': 'A/V',
        'l': Lp('moving-images-and-sound.html'),
        'u': 'https://www.archives.gov/research/topics/uaps/moving-images-and-sound',
    },
    {
        't': 'PAGE',
        'ti': 'Textual and Microfilm',
        'de': 'Paper records and microfilm — including Project Blue Book\'s 12,618-case textual file, J. Allen Hynek collection, and FBI HQ files.',
        'ag': 'NARA',
        'cat': 'Textual',
        'l': Lp('textual-and-microfilm.html'),
        'u': 'https://www.archives.gov/research/topics/uaps/textual-and-microfilm',
    },
    {
        't': 'PAGE',
        'ti': 'Presidential Libraries',
        'de': 'UAP-related material held in the presidential libraries (Truman, Eisenhower, Kennedy, Johnson, Nixon, Carter, Reagan, Clinton).',
        'ag': 'NARA',
        'cat': 'Presidential',
        'l': Lp('presidential-libraries.html'),
        'u': 'https://www.archives.gov/research/topics/uaps/presidential-libraries',
    },
    {
        't': 'PAGE',
        'ti': 'Research by Record Group or Collection',
        'de': 'Cross-index of every NARA record group containing UAP material — RG 18 (Army Air Forces), RG 65 (FBI), RG 341 (Air Staff), and many more.',
        'ag': 'NARA',
        'cat': 'Index',
        'l': Lp('federal-agency.html'),
        'u': 'https://www.archives.gov/research/topics/uaps/federal-agency',
    },
    {
        't': 'PAGE',
        'ti': 'NARA Publications, Blogs & Articles',
        'de': 'NARA-authored publications, archivist blog posts, and Prologue magazine articles about UAP collections.',
        'ag': 'NARA',
        'cat': 'Reference',
        'l': Lp('blogs-and-articles.html'),
        'u': 'https://www.archives.gov/research/topics/uaps/blogs-and-articles',
    },
    {
        't': 'PAGE',
        'ti': 'Frequently Asked Questions',
        'de': 'Common research questions about the UAP collection and how to request materials.',
        'ag': 'NARA',
        'cat': 'FAQ',
        'l': Lp('faqs.html'),
        'u': 'https://www.archives.gov/research/topics/uaps/faqs',
    },
    # External catalog links — no local copy possible, NARA Catalog is millions of pages
    {
        't': 'CATALOG',
        'ti': 'NARA Catalog — Bulk UAP Download Manifest',
        'de': 'Curated bulk-download index of digitised UAP records in the NARA online catalog — Project Blue Book, FBI HQ files, etc.',
        'ag': 'NARA',
        'cat': 'Catalog',
        'l': '',
        'u': 'https://www.archives.gov/research/catalog/catalog-bulk-downloads/uap-bulk-download',
    },
    {
        't': 'CATALOG',
        'ti': 'NARA Catalog — Full Search',
        'de': 'Search the entire NARA Catalog for keywords across all 600 million digitised pages.',
        'ag': 'NARA',
        'cat': 'Catalog',
        'l': '',
        'u': 'https://catalog.archives.gov/',
    },
    {
        't': 'CATALOG',
        'ti': 'Project Blue Book — Online File',
        'de': 'Air Force\'s 1947-1969 UFO investigation files: 12,618 cases, 130,000+ pages, fully digitised.',
        'ag': 'NARA',
        'cat': 'Catalog',
        'l': '',
        'u': 'https://catalog.archives.gov/search?q=project+blue+book',
    },
    {
        't': 'CATALOG',
        'ti': 'FBI Vault — UFO files',
        'de': 'FBI\'s declassified UFO holdings hosted on the FBI Vault — Hottel memo, Roswell-era memos, internal investigations.',
        'ag': 'FBI',
        'cat': 'Catalog',
        'l': '',
        'u': 'https://vault.fbi.gov/UFO',
    },
]

# Merge additional records discovered by scrape-nara.py
_scraped_cache = os.path.join(ROOT, '.cache', 'scraped-index.json')
if os.path.exists(_scraped_cache):
    _seen = {a.get('u', '') or a.get('url', '') for a in ASSETS}
    for _r in json.load(open(_scraped_cache)):
        _url = _r.get('url', '')
        if _url and _url not in _seen:
            _seen.add(_url)
            ASSETS.append({
                't': _r.get('type', 'PDF'),
                'ti': _r.get('title', ''),
                'de': _r.get('desc', ''),
                'ag': _r.get('agency', 'NARA'),
                'cat': _r.get('type', 'PDF').capitalize(),
                'date': _r.get('date', ''),
                'l': '',
                'u': _url,
                's': _r.get('src', ''),
            })

apply_manifest(ASSETS)
stats = {
    'total': len(ASSETS),
    'local_total': sum(1 for a in ASSETS if a.get('l')),
    'pages_total': sum(1 for a in ASSETS if a['t'] == 'PAGE'),
    'pdf_total': sum(1 for a in ASSETS if a['t'] == 'PDF'),
    'catalog_total': sum(1 for a in ASSETS if a['t'] == 'CATALOG'),
}

data_json = json.dumps({'assets': ASSETS, 'stats': stats}, ensure_ascii=False).replace('</script', '<\\/script')

PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NARA UAP Records — Offline Mirror</title>
<meta name="description" content="Offline mirror of the National Archives' Unidentified Anomalous Phenomena records gateway.">
<link rel="canonical" href="https://realufo.org/nara/">
<meta property="og:title" content="NARA — National Archives UAP Records | realufo.org">
<meta property="og:description" content="U.S. National Archives gateway to UAP records. Record Group 615 + Project Blue Book + FBI Vault. 2024 NDAA Public Law 118-31.">
<meta property="og:image" content="https://realufo.org/slideshow/NASA-UAP-VM6-Apollo-17-1972.jpg">
<meta property="og:url" content="https://realufo.org/nara/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="realufo.org">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="NARA — National Archives UAP Records | realufo.org">
<meta name="twitter:description" content="U.S. National Archives gateway to UAP records. Record Group 615 + Project Blue Book + FBI Vault. 2024 NDAA Public Law 118-31.">
<meta name="twitter:image" content="https://realufo.org/slideshow/NASA-UAP-VM6-Apollo-17-1972.jpg">
<link rel="icon" type="image/svg+xml" href="./assets/favicon.svg">
<link rel="apple-touch-icon" href="./assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet">
<style>
:root {
  --bg:#0a0a0c; --bg-2:#111114; --panel:#15151a;
  --ink:#e8e3d8; --ink-dim:#a8a298; --ink-faint:#6b665d;
  --rule:rgba(232,227,216,0.12); --rule-strong:rgba(232,227,216,0.28);
  --stamp:#b91c1c; --caution:#cbd5e1; --warm:#d4a017; --classified:#c9362c;
  --serif:"Source Serif 4","Iowan Old Style",Georgia,serif;
  --mono:"JetBrains Mono","SF Mono",Consolas,monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; scroll-padding-top: 70px; }
body { background: var(--bg); color: var(--ink); font-family: var(--serif); font-size: 16px; line-height: 1.65;
  background-image: radial-gradient(ellipse at 20% 0%, rgba(156,163,175,0.05) 0%, transparent 50%); background-attachment: fixed; }
.scanlines { position: fixed; inset: 0; background: repeating-linear-gradient(to bottom, transparent 0, transparent 2px, rgba(255,255,255,0.012) 3px, transparent 4px); pointer-events: none; z-index: 50; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 32px; position: relative; z-index: 2; }
.gov-banner { background: #1a1a1f; border-bottom: 1px solid var(--rule); font-family: var(--mono); font-size: 11px; color: var(--ink-dim); letter-spacing: 0.04em; }
.gov-banner .container { display: flex; align-items: center; gap: 16px; padding: 10px 32px; flex-wrap: wrap; }
.gov-banner a { color: var(--caution); text-decoration: none; }
.gov-banner .nav-mirrors { margin-left: auto; display: flex; gap: 14px; flex-wrap: wrap; }
.flag-dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(45deg,#b91c1c 0,#b91c1c 50%,#1e3a8a 50%,#1e3a8a 100%); flex-shrink: 0; }
.header-wrap { position: sticky; top: 0; z-index: 40; background: rgba(10,10,12,0.95); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid var(--rule); }
header { padding: 16px 0; }
header .container { display: flex; align-items: center; gap: 24px; flex-wrap: wrap; }
.brand { display: flex; align-items: center; gap: 14px; text-decoration: none; color: var(--ink); flex-shrink: 0; }
.seal { width: 44px; height: 44px; background: radial-gradient(circle at 50% 50%, #9ca3af, #4b5563 60%, #1f2937); border-radius: 50%; display: grid; place-items: center; box-shadow: 0 0 0 2px var(--ink), 0 0 0 4px var(--bg), 0 0 0 5px var(--ink-faint); font-family: var(--mono); font-weight: 700; font-size: 11px; color: var(--ink); }
.brand-text { display: flex; flex-direction: column; line-height: 1.1; }
.brand-text .super { font-family: var(--mono); font-size: 9px; letter-spacing: 0.2em; color: var(--ink-dim); text-transform: uppercase; }
.brand-text .name { font-family: var(--serif); font-size: 18px; font-weight: 600; margin-top: 2px; }
nav.primary { font-family: var(--mono); font-size: 11px; letter-spacing: 0.08em; flex: 1; }
.nav-toggle { display: none; background: transparent; border: 1px solid var(--rule-strong); width: 40px; height: 40px; cursor: pointer; padding: 0; flex-direction: column; justify-content: center; align-items: center; gap: 4px; }
.nav-toggle span { display: block; width: 18px; height: 2px; background: var(--ink); transition: transform .2s, opacity .2s; }
.nav-toggle[aria-expanded="true"] span:nth-child(1) { transform: translateY(6px) rotate(45deg); }
.nav-toggle[aria-expanded="true"] span:nth-child(2) { opacity: 0; }
.nav-toggle[aria-expanded="true"] span:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }
@media (max-width: 720px) {
  .nav-toggle { display: flex; }
  nav.primary { display: none; }
  nav.primary.open { display: block; position: fixed; top: 64px; left: 0; right: 0; background: var(--panel); border-bottom: 1px solid var(--rule-strong); padding: 8px 16px 16px; max-height: calc(100vh - 64px); overflow-y: auto; -webkit-overflow-scrolling: touch; overscroll-behavior: contain; z-index: 800; }
  nav.primary ul { flex-direction: column; gap: 0; padding-top: 12px; margin-top: 12px; border-top: 1px solid var(--rule); justify-content: flex-start; }
  nav.primary ul li { width: 100%; }
  nav.primary ul a { display: block; padding: 12px 0; border-bottom: 1px solid var(--rule); }
  .arch-controls-bar { flex-direction: column; align-items: stretch; gap: 10px; }
  .tabs { gap: 6px; flex-wrap: wrap; width: 100%; }
  .tab { padding: 6px 10px; font-size: 10px; }
  .search-wrap { margin: 0; width: 100%; }
  .arch-grid { grid-template-columns: 1fr; gap: 12px; }
  body { font-size: 15px; }
}
nav.primary ul { display: flex; gap: 4px 22px; list-style: none; flex-wrap: wrap; justify-content: flex-end; }
nav.primary a { color: var(--ink-dim); text-decoration: none; text-transform: uppercase; }
nav.primary a:hover { color: var(--caution); }
nav.primary a.active { color: var(--caution); }

.hero { padding: 56px 0 40px; border-bottom: 1px solid var(--rule); }
.coords { font-family: var(--mono); font-size: 12px; color: var(--caution); letter-spacing: 0.12em; margin-bottom: 18px; display: flex; align-items: center; gap: 12px; }
.coords::before { content: "◉"; color: var(--stamp); }
.coords::after { content: ""; flex: 1; height: 1px; background: linear-gradient(to right, var(--caution), transparent); margin-left: 12px; max-width: 200px; }
h1.hero-title { font-family: var(--serif); font-weight: 700; font-size: clamp(28px,4.5vw,52px); line-height: 1.05; letter-spacing: -0.02em; max-width: 24ch; margin-bottom: 22px; }
h1.hero-title em { color: var(--caution); font-style: italic; }
.hero-sub { max-width: 65ch; color: var(--ink-dim); font-size: 17px; line-height: 1.65; }
.hero-sub a { color: var(--caution); }

.headlines { padding: 40px 0; border-bottom: 1px solid var(--rule); }
.head-grid { display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
.head-card { padding: 20px 22px; background: var(--panel); border: 1px solid var(--rule); border-left: 3px solid var(--caution); }
.head-card .h-label { font-family: var(--mono); font-size: 10px; color: var(--caution); letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 10px; }
.head-card .h-text { font-size: 17px; line-height: 1.4; color: var(--ink); }
.head-card .h-num { font-family: var(--mono); font-size: 28px; color: var(--ink); font-weight: 600; display: block; margin-bottom: 4px; }

section { padding: 56px 0; border-bottom: 1px solid var(--rule); position: relative; }
.section-label { font-family: var(--mono); font-size: 11px; letter-spacing: 0.24em; text-transform: uppercase; color: var(--ink-faint); display: flex; align-items: center; gap: 16px; margin-bottom: 18px; }
.section-label::before { content: ""; width: 28px; height: 1px; background: var(--ink-faint); }
h2 { font-family: var(--serif); font-size: clamp(24px,3vw,36px); font-weight: 700; letter-spacing: -0.015em; margin-bottom: 20px; max-width: 28ch; }
.lede { max-width: 70ch; color: var(--ink); font-size: 17px; }
.lede a { color: var(--caution); }

.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1px; background: var(--rule); border: 1px solid var(--rule); margin: 22px 0 28px; }
.stat { background: var(--panel); padding: 16px 20px; font-family: var(--mono); }
.stat b { display: block; font-size: 26px; color: var(--ink); font-weight: 500; }
.stat small { display: block; font-size: 10px; color: var(--ink-faint); letter-spacing: 0.16em; text-transform: uppercase; margin-top: 6px; }
.arch-controls-bar { position: sticky; top: 64px; z-index: 30; background: rgba(10,10,12,0.95); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule); margin: 24px -32px 0; padding: 14px 32px; display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }
.tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.tab { font-family: var(--mono); font-size: 11px; padding: 8px 14px; border: 1px solid var(--rule-strong); background: var(--panel); color: var(--ink-dim); cursor: pointer; letter-spacing: 0.08em; text-transform: uppercase; }
.tab:hover { color: var(--ink); border-color: var(--ink-faint); }
.tab.active { background: var(--caution); color: var(--bg); border-color: var(--caution); font-weight: 700; }
.tab .count { opacity: 0.6; margin-left: 6px; font-size: 10px; }
.search-wrap { margin-left: auto; display: flex; align-items: center; gap: 8px; background: var(--panel); border: 1px solid var(--rule-strong); padding: 6px 12px; min-width: 220px; }
.search-wrap::before { content: "⌕"; color: var(--ink-faint); font-family: var(--mono); }
.search-wrap input { background: transparent; border: 0; outline: 0; color: var(--ink); font-family: var(--mono); font-size: 12px; flex: 1; }
.search-wrap input::placeholder { color: var(--ink-faint); }

.arch-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 18px; padding: 18px 0 24px; }
.card { background: var(--panel); border: 1px solid var(--rule); display: flex; flex-direction: column; overflow: hidden; transition: border-color .2s, transform .2s; }
.card:hover { border-color: var(--caution); transform: translateY(-2px); }
.card-media { aspect-ratio: 16/9; background: var(--bg-2); position: relative; overflow: hidden; display: grid; place-items: center; border-bottom: 1px solid var(--rule); cursor: pointer; }
.pdf-glyph { font-family: var(--mono); font-size: 12px; color: var(--ink-faint); background: repeating-linear-gradient(45deg,#1a1a1f,#1a1a1f 8px,#15151a 8px,#15151a 16px); width: 100%; height: 100%; display: grid; place-items: center; text-align: center; padding: 16px; }
.pdf-glyph .ico { font-size: 22px; color: var(--caution); margin-bottom: 6px; border: 2px solid var(--caution); padding: 4px 10px; font-weight: 700; letter-spacing: 0.04em; display: inline-block; }
.glyph-page { background: linear-gradient(135deg, rgba(156,163,175,0.15), rgba(75,85,99,0.04)); }
.glyph-cat { background: linear-gradient(135deg, rgba(212,160,23,0.12), rgba(0,0,0,0)); }
.glyph-cat .ico { color: var(--warm); border-color: var(--warm); }
.badge { position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.78); color: var(--caution); font-family: var(--mono); font-size: 9px; padding: 3px 8px; letter-spacing: 0.14em; text-transform: uppercase; }
.badge.local { bottom: 8px; left: 8px; top: auto; color: var(--warm); }
.badge.source { bottom: 8px; left: 8px; top: auto; color: var(--ink-faint); }
.card-body { padding: 14px 16px; flex: 1; display: flex; flex-direction: column; gap: 6px; }
.card-title { font-family: var(--serif); font-size: 14px; font-weight: 600; line-height: 1.35; color: var(--ink); overflow-wrap: anywhere; }
.card-desc { font-family: var(--serif); font-size: 12.5px; color: var(--ink-dim); line-height: 1.5; margin-top: 4px; }
.card-meta { display: grid; grid-template-columns: 80px 1fr; gap: 4px 12px; margin-top: 8px; padding: 10px 0; border-top: 1px solid var(--rule); }
.card-meta dt { font-family: var(--mono); font-size: 9px; color: var(--ink-faint); letter-spacing: 0.14em; text-transform: uppercase; }
.card-meta dd { font-family: var(--serif); color: var(--ink); font-size: 12px; line-height: 1.4; }
.card-actions { display: flex; gap: 8px; margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--rule); flex-wrap: wrap; }
.card-actions a { font-family: var(--mono); font-size: 10px; color: var(--caution); text-decoration: none; letter-spacing: 0.12em; text-transform: uppercase; padding: 4px 8px; border: 1px solid var(--rule-strong); }
.card-actions a:hover { background: var(--caution); color: var(--bg); border-color: var(--caution); }
.card-actions a.warn { color: var(--ink-faint); }
.card-actions a.warn:hover { background: var(--ink-faint); color: var(--bg); }
.empty { padding: 60px 0; text-align: center; color: var(--ink-faint); font-family: var(--mono); font-size: 13px; }

.lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.94); display: none; place-items: center; z-index: 200; padding: 32px; }
.lightbox.open { display: grid; }
.lb-inner { max-width: 92vw; max-height: 92vh; display: flex; flex-direction: column; gap: 10px; align-items: center; }
.lb-inner iframe { width: 92vw; height: 86vh; border: 1px solid var(--rule-strong); background: #fff; }
.lb-meta { font-family: var(--mono); font-size: 11px; color: var(--ink); background: var(--bg-2); border: 1px solid var(--rule-strong); padding: 8px 14px; max-width: 80vw; text-align: center; }
.lb-meta a { color: var(--caution); }
.lb-close { position: absolute; top: 16px; right: 24px; width: 40px; height: 40px; background: var(--bg-2); border: 1px solid var(--rule-strong); color: var(--ink); display: grid; place-items: center; cursor: pointer; font-family: var(--mono); font-size: 22px; z-index: 2; }
.lb-nav { position: absolute; top: 50%; transform: translateY(-50%); width: 52px; height: 52px; background: rgba(20,20,24,0.6); border: 1px solid var(--rule-strong); color: var(--ink); display: grid; place-items: center; cursor: pointer; font-family: var(--serif); font-size: 32px; z-index: 2; }
.lb-nav:hover { background: rgba(0,0,0,0.85); color: var(--caution); border-color: var(--caution); }
.lb-nav.prev { left: 16px; } .lb-nav.next { right: 16px; }
.lb-counter { position: absolute; top: 24px; left: 50%; transform: translateX(-50%); font-family: var(--mono); font-size: 11px; letter-spacing: 0.16em; color: var(--ink-dim); background: var(--bg-2); border: 1px solid var(--rule); padding: 4px 12px; z-index: 2; }

footer { background: #060608; padding: 40px 0 24px; color: var(--ink-dim); font-family: var(--mono); font-size: 12px; }
footer .container { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 40px; }
footer h4 { font-family: var(--mono); font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--ink); margin-bottom: 14px; }
footer ul { list-style: none; display: flex; flex-direction: column; gap: 8px; }
footer a { color: var(--ink-dim); text-decoration: none; }
footer a:hover { color: var(--caution); }
footer .colophon { grid-column: 1 / -1; border-top: 1px solid var(--rule); padding-top: 20px; margin-top: 20px; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 16px; font-size: 10px; color: var(--ink-faint); letter-spacing: 0.1em; }

@media (max-width: 760px) { footer .container { grid-template-columns: 1fr 1fr; } }
@media (max-width: 720px) {
  .container { padding: 0 16px; }
  .gov-banner .container { padding: 10px 16px; }
  .arch-controls-bar { margin: 24px -16px 0; padding: 12px 16px; }
  .lb-nav { width: 40px; height: 40px; font-size: 24px; }
  .lb-nav.prev { left: 8px; } .lb-nav.next { right: 8px; }
}

/* ── More dropdown + lang picker + scroll-hide ── */
.nav-sep { display: none; }
@media (min-width: 720px) { .nav-sep { display: block; width: 1px; height: 16px; background: var(--rule-strong); } }
.has-dropdown { position: relative; }
.nav-more-btn { background: none; border: none; color: var(--ink-dim); cursor: pointer; font-family: var(--mono); font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; padding: 12px 0; display: block; width: 100%; text-align: left; border-bottom: 1px solid var(--rule); }
.nav-more-btn:hover { color: var(--caution); }
.nav-dropdown { display: none; list-style: none; background: var(--panel); border: 1px solid var(--rule-strong); padding: 6px 0; z-index: 200; }
.nav-dropdown li a { border: 0 !important; padding: 9px 16px !important; white-space: nowrap; }
.lang-picker { position: relative; }
.lang-btn { background: transparent; border: 1px solid var(--rule-strong); color: var(--ink-dim); cursor: pointer; font-family: var(--mono); font-size: 9.5px; letter-spacing: 0.12em; padding: 4px 8px; text-transform: uppercase; display: block; width: 100%; text-align: left; margin: 8px 0; }
.lang-btn:hover { color: var(--caution); border-color: var(--caution); }
.lang-menu { display: none; list-style: none; background: var(--panel); border: 1px solid var(--rule-strong); padding: 6px 0; z-index: 300; }
.lang-menu button { background: none; border: none; color: var(--ink-dim); cursor: pointer; font-family: var(--mono); font-size: 10.5px; padding: 8px 16px; width: 100%; text-align: left; }
.lang-menu button:hover { color: var(--caution); }
.lang-picker.open .lang-menu, .has-dropdown.open .nav-dropdown { display: block; }
.arch-controls-bar { transition: top 0.28s ease; }
.arch-controls-bar.bar-hidden { top: -160px; }
@media (max-width: 719px) { .nav-more-btn { padding: 11px 0; } .nav-dropdown { position: static; right: auto; top: auto; min-width: 0; width: 100%; } .has-dropdown.open .nav-dropdown { margin-left: 12px; border: 0; background: transparent; box-shadow: none; padding: 0; } .lang-btn { border: 0; margin: 0; padding: 11px 0; font-size: 11px; border-bottom: 1px solid var(--rule); } .lang-picker.open .lang-menu { margin-left: 12px; border: 0; background: transparent; } }
@media (min-width: 720px) { .nav-more-btn { padding: 0; border: 0; font-size: 10.5px; } .nav-dropdown { position: absolute; right: 0; top: calc(100% + 10px); min-width: 240px; max-height: 70vh; overflow-y: auto;; } .has-dropdown.open .nav-dropdown { display: block; } .lang-btn { width: auto; margin: 0; padding: 3px 8px; } .lang-menu { position: absolute; right: 0; top: calc(100% + 10px); min-width: 130px; } }
</style>
</head>
<body>
<div class="scanlines"></div>

<div class="header-wrap">
<header>
  <div class="container">
    <a href="#top" class="brand">
      <div class="seal">NARA</div>
      <div class="brand-text">
        <span class="super">National Archives &amp; Records Administration</span>
        <span class="name">UAP Records Gateway</span>
      </div>
    </a>
    <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
    __SITE_NAV__
  </div>
</header>
</div>

<div class="hero" id="top">
  <div class="container">
    <div class="coords">38°53′34″N, 77°01′23″W · NATIONAL ARCHIVES BUILDING, WASHINGTON, D.C.</div>
    <h1 class="hero-title">National Archives — <em>UAP</em> Records</h1>
    <p class="hero-sub">
      Under the 2024 NDAA (Public Law 118-31) Congress created <strong>Record Group 615</strong>
      at NARA — the legal sink for every federal agency's UAP files. RG 615 sits alongside dozens
      of pre-existing collections: Project Blue Book, the FBI Vault, presidential libraries, NICAP
      donations, J. Allen Hynek's papers, and more. NARA holds, by their own estimate, millions of
      pages of UAP-related material — most digitised, all searchable via the
      <a href="https://catalog.archives.gov/" target="_blank" rel="noopener">NARA Catalog</a>.
      This mirror gives you the official navigation gateway offline; the catalog itself stays live.
    </p>
  </div>
</div>

<section id="headlines" class="headlines">
  <div class="container">
    <div class="section-label">§ Headlines · NARA UAP, distilled</div>
    <div class="head-grid">
      <div class="head-card"><div class="h-label">Authority</div><div class="h-text">2024 NDAA · Public Law 118-31 · Sec. 1841–1843.</div></div>
      <div class="head-card"><div class="h-label">Record Group</div><span class="h-num">615</span><div class="h-text">UAP Records Collection.</div></div>
      <div class="head-card"><div class="h-label">Project Blue Book</div><span class="h-num">12 618</span><div class="h-text">USAF UFO cases, 1947–1969. 130k+ pages, fully digitised.</div></div>
      <div class="head-card"><div class="h-label">Catalog</div><span class="h-num">600M+</span><div class="h-text">Digitised pages searchable via catalog.archives.gov.</div></div>
      <div class="head-card"><div class="h-label">Format</div><div class="h-text">Textual · Microfilm · Photographs · Moving Images · Sound.</div></div>
      <div class="head-card"><div class="h-label">Review</div><div class="h-text">25-year automatic declassification review mandated by statute.</div></div>
    </div>
  </div>
</section>

<section id="archive">
  <div class="container">
    <div class="section-label">§ Records · Gateway, sub-collections, catalog</div>
    <h2>Every official NARA UAP entry-point, all in one place.</h2>
    <p class="lede">
      The cards below cover NARA's topic-pages plus deep-links into the live catalog. Snapshots
      of every gateway page are mirrored locally; the actual records remain on
      <a href="https://catalog.archives.gov/" target="_blank">catalog.archives.gov</a>
      (too large to bundle).
    </p>

    <div class="stats-grid" id="arch-stats"></div>

    <div class="arch-controls-bar">
      <div class="tabs" id="arch-tabs"></div>
      <div class="search-wrap">
        <input id="arch-search" type="search" placeholder="Search title, agency, category, description…" autocomplete="off">
      </div>
    </div>

    <div class="arch-grid" id="arch-grid"></div>
    <div class="empty" id="arch-empty" hidden>No records match.</div>
  </div>
</section>

<footer>
  <div class="container">
    <div>
      <h4>NARA Mirror</h4>
      <p style="color: var(--ink-dim); font-family: var(--serif); margin-bottom: 14px;">
        Offline archival mirror of the NARA UAP records gateway. Federal U.S. government
        works are public domain (17 U.S.C. § 105).
      </p>
      <p style="color: var(--ink-faint); font-size: 10px; letter-spacing: 0.1em;">Source: archives.gov/research/topics/uaps · 2024 NDAA · catalog.archives.gov.</p>
    </div>
    <div>
      <h4>Related Mirrors</h4>
      <ul>
        <li><a href="../index.html">war.gov / UFO Release 01</a></li>
        <li><a href="../aaro/index.html">AARO — DoW</a></li>
        <li><a href="../nasa/index.html">NASA UAP Study</a></li>
      </ul>
    </div>
    <div>
      <h4>Source</h4>
      <ul>
        <li><a href="https://www.archives.gov/research/topics/uaps" target="_blank" rel="noopener">archives.gov/research/topics/uaps ↗</a></li>
        <li><a href="https://catalog.archives.gov/" target="_blank" rel="noopener">NARA Catalog ↗</a></li>
        <li><a href="https://vault.fbi.gov/UFO" target="_blank" rel="noopener">FBI Vault — UFO ↗</a></li>
      </ul>
    </div>
    <div class="colophon">
      <span>Offline mirror · For research and reference</span>
      <span>Built from public-domain NARA source</span>
    </div>
  </div>
</footer>

<div class="lightbox" id="lightbox" aria-hidden="true">
  <div class="lb-close" id="lb-close">×</div>
  <button class="lb-nav prev" id="lb-prev" aria-label="Previous (←)">‹</button>
  <button class="lb-nav next" id="lb-next" aria-label="Next (→)">›</button>
  <div class="lb-counter" id="lb-counter"></div>
  <div class="lb-inner" id="lb-inner"></div>
</div>

<script id="arch-data" type="application/json">__DATA__</script>
__SITE_NAV_JS__
<script>
(() => {
  const navToggle = document.getElementById('nav-toggle');
  const primaryNav = document.getElementById('primary-nav');
  if (navToggle && primaryNav) {
    navToggle.addEventListener('click', () => {
      const open = primaryNav.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    primaryNav.addEventListener('click', e => {
      if (e.target.tagName === 'A') { primaryNav.classList.remove('open'); navToggle.setAttribute('aria-expanded', 'false'); }
    });
  }
  const D = JSON.parse(document.getElementById('arch-data').textContent);
  const items = D.assets;
  const STATS = D.stats;
  function esc(s){return (s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

  document.getElementById('arch-stats').innerHTML = [
    ['Total', STATS.total],
    ['Local', STATS.local_total],
    ['Topic pages', STATS.pages_total],
    ['Documents', STATS.pdf_total],
    ['Catalog', STATS.catalog_total],
  ].map(([k,v]) => `<div class="stat"><b>${v}</b><small>${k}</small></div>`).join('');

  const TABS = [
    {key:'ALL', label:'All'},
    {key:'PAGE', label:'Topic pages'},
    {key:'PDF', label:'Documents'},
    {key:'CATALOG', label:'Catalog links'},
  ];
  const state = { tab: 'ALL', q: '' };
  const tabsEl = document.getElementById('arch-tabs');
  function count(k){ return k === 'ALL' ? items.length : items.filter(a => a.t === k).length; }
  tabsEl.innerHTML = TABS.map(t => `<button class="tab${t.key===state.tab?' active':''}" data-key="${t.key}">${t.label}<span class="count">${count(t.key)}</span></button>`).join('');
  tabsEl.addEventListener('click', e => {
    const t = e.target.closest('.tab'); if (!t) return;
    state.tab = t.dataset.key;
    tabsEl.querySelectorAll('.tab').forEach(x => x.classList.toggle('active', x.dataset.key === state.tab));
    render();
  });
  document.getElementById('arch-search').addEventListener('input', e => { state.q = e.target.value.trim().toLowerCase(); render(); });

  function glyphFor(a) {
    if (a.t === 'PAGE') return `<div class="pdf-glyph glyph-page"><span class="ico">PG</span><span>${esc(a.cat||'NARA')}</span></div>`;
    if (a.t === 'CATALOG') return `<div class="pdf-glyph glyph-cat"><span class="ico">⌕</span><span>NARA Catalog</span></div>`;
    return `<div class="pdf-glyph"><span class="ico">PDF</span><span>${esc(a.ag||'Document')}</span></div>`;
  }
  function metaFor(a) {
    const rows = [];
    if (a.ag) rows.push(['Agency', a.ag]);
    if (a.cat) rows.push(['Category', a.cat]);
    if (a.date) rows.push(['Date', a.date]);
    return `<dl class="card-meta">${rows.map(r => `<dt>${r[0]}</dt><dd>${esc(r[1])}</dd>`).join('')}</dl>`;
  }
  function actionsFor(a) {
    const out = [];
    const verb = a.t === 'PDF' ? 'Open PDF' : a.t === 'PAGE' ? 'Open Snapshot' : 'Open';
    if (a.l || (a.u && a.t === 'PDF')) {
      out.push(`<a href="#" data-action="open" data-title="${esc(a.ti)}">${verb}</a>`);
      const dl = a.l ? './' + a.l : a.u;
      if (dl) out.push(`<a href="${esc(dl)}" ${a.l?'download':'target="_blank" rel="noopener"'}>Download</a>`);
    }
    const src = a.s || a.u;
    if (src) out.push(`<a class="warn" href="${esc(src)}" target="_blank" rel="noopener">${a.t==='CATALOG' ? 'Catalog ↗' : 'Source ↗'}</a>`);
    return `<div class="card-actions">${out.join('')}</div>`;
  }
  function cardHtml(a, gidx) {
    const localBadge = a.l ? '<span class="badge local">LOCAL</span>' : '<span class="badge source">LIVE</span>';
    return `<article class="card" data-idx="${gidx}">
      <div class="card-media">
        ${glyphFor(a)}
        <span class="badge">${esc(a.t)}</span>
        ${localBadge}
      </div>
      <div class="card-body">
        <div class="card-title">${esc(a.ti)}</div>
        ${a.de ? `<div class="card-desc">${esc(a.de)}</div>` : ''}
        ${metaFor(a)}
        ${actionsFor(a)}
      </div>
    </article>`;
  }

  let lbList = [], lbIdx = 0;
  function filtered() {
    return items.filter(a => {
      if (state.tab !== 'ALL' && a.t !== state.tab) return false;
      if (state.q) {
        const hay = [a.ti, a.de, a.ag, a.cat, a.date].join(' ').toLowerCase();
        if (!hay.includes(state.q)) return false;
      }
      return true;
    });
  }
  const grid = document.getElementById('arch-grid');
  const emptyEl = document.getElementById('arch-empty');
  function render() {
    const list = filtered(); lbList = list;
    grid.innerHTML = list.map((a, i) => cardHtml(a, i)).join('');
    emptyEl.hidden = list.length > 0;
  }
  render();

  const lb = document.getElementById('lightbox');
  const lbI = document.getElementById('lb-inner');
  const lbC = document.getElementById('lb-close');
  const lbPrev = document.getElementById('lb-prev');
  const lbNext = document.getElementById('lb-next');
  const lbCounter = document.getElementById('lb-counter');

  function renderLb() {
    const a = lbList[lbIdx]; if (!a) return;
    let html;
    if (a.l) {
      html = `<iframe src="./${esc(a.l)}#view=FitH" sandbox="allow-same-origin allow-popups"></iframe><div class="lb-meta">${esc(a.ti)} — <a href="./${esc(a.l)}" target="_blank">open in new tab ↗</a>${a.u?` · <a href="${esc(a.u)}" target="_blank">live ↗</a>`:''}</div>`;
    } else if (a.u) {
      // CATALOG cards: can't iframe NARA (CSP) — open new tab directly.
      window.open(a.u, '_blank'); closeLb(); return;
    } else {
      html = `<div class="lb-meta">${esc(a.ti)} — no local or live link.</div>`;
    }
    lbI.innerHTML = html;
    if (lbCounter) lbCounter.textContent = (lbIdx + 1) + ' / ' + lbList.length;
    if (lbPrev) lbPrev.style.visibility = lbList.length > 1 ? 'visible' : 'hidden';
    if (lbNext) lbNext.style.visibility = lbList.length > 1 ? 'visible' : 'hidden';
  }
  function openAt(idx) { if (!lbList.length) return; lbIdx = (idx + lbList.length) % lbList.length; renderLb(); if (lb.classList.contains('open') || lbI.innerHTML) lb.classList.add('open'); }
  function navLb(d) { if (!lbList.length) return; lbIdx = (lbIdx + d + lbList.length) % lbList.length; renderLb(); }
  function closeLb() { lb.classList.remove('open'); lbI.innerHTML = ''; }
  lbC.addEventListener('click', closeLb);
  if (lbPrev) lbPrev.addEventListener('click', e => { e.stopPropagation(); navLb(-1); });
  if (lbNext) lbNext.addEventListener('click', e => { e.stopPropagation(); navLb(1); });
  lb.addEventListener('click', e => { if (e.target === lb) closeLb(); });
  document.addEventListener('keydown', e => {
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') closeLb();
    else if (e.key === 'ArrowRight') navLb(1);
    else if (e.key === 'ArrowLeft')  navLb(-1);
  });
  let touchX=0, touchY=0, touchT=0;
  lb.addEventListener('touchstart', e => { if (!e.touches.length) return; touchX = e.touches[0].clientX; touchY = e.touches[0].clientY; touchT = Date.now(); }, { passive:true });
  lb.addEventListener('touchend', e => {
    if (!e.changedTouches.length) return;
    const dx = e.changedTouches[0].clientX - touchX, dy = e.changedTouches[0].clientY - touchY;
    if (Date.now() - touchT < 800 && Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) navLb(dx < 0 ? 1 : -1);
  }, { passive:true });

  grid.addEventListener('click', e => {
    const action = e.target.closest('a[data-action]');
    const card = e.target.closest('.card');
    const media = e.target.closest('.card-media');
    if (action) e.preventDefault();
    if (card && card.dataset.idx !== undefined && (action || media)) {
      const a = lbList[parseInt(card.dataset.idx, 10)];
      if (a && a.t === 'CATALOG' && a.u) { window.open(a.u, '_blank'); return; }
      openAt(parseInt(card.dataset.idx, 10));
      lb.classList.add('open');
    }
  });
})();
</script>
</body>
</html>
'''
_site_nav = make_nav('nara', depth=1, internal_links=[('Intro', '#top', 'intro'), ('Headlines', '#headlines', 'headlines'), ('Records', '#archive', 'archive')])
_nav_js = '''<script>
(function(){var I18N=__I18N__;var lang=localStorage.getItem('realufo_lang')||'en';if(!I18N[lang])lang='en';function applyLang(c){lang=c;localStorage.setItem('realufo_lang',c);var t=I18N[c];document.querySelectorAll('[data-i18n]').forEach(function(el){var k=el.getAttribute('data-i18n');if(t[k]!==undefined)el.textContent=t[k];});var lb=document.getElementById('lang-btn');if(lb)lb.textContent=t.code||c.toUpperCase();};var lp=document.getElementById('lang-picker'),lbtn=document.getElementById('lang-btn'),lm=document.getElementById('lang-menu');if(lbtn&&lp){lbtn.addEventListener('click',function(e){e.stopPropagation();lp.classList.toggle('open');});if(lm)lm.addEventListener('click',function(e){var b=e.target.closest('button[data-lang]');if(!b)return;applyLang(b.dataset.lang);lp.classList.remove('open');});}var nd=Array.from(document.querySelectorAll('.has-dropdown > details'));nd.forEach(function(d){d.addEventListener('toggle',function(){if(!d.open)return;nd.forEach(function(o){if(o!==d)o.open=false;});});});document.addEventListener('click',function(e){if(lp)lp.classList.remove('open');if(!e.target.closest('.has-dropdown')){nd.forEach(function(d){d.open=false;});}});document.addEventListener('keydown',function(e){if(e.key==='Escape')nd.forEach(function(d){d.open=false;});});var bar=document.querySelector('.arch-controls-bar');if(bar){var lY=window.scrollY;window.addEventListener('scroll',function(){if(window.innerWidth>=720){bar.classList.remove('bar-hidden');return;}var y=window.scrollY;if(y<80)bar.classList.remove('bar-hidden');else if(y>lY+4)bar.classList.add('bar-hidden');else if(y<lY-4)bar.classList.remove('bar-hidden');lY=y;},{passive:true});}applyLang(lang);})();
</script>'''.replace('__I18N__', _I18N_JSON)
PAGE = PAGE.replace('__DATA__', data_json)
PAGE = PAGE.replace('__SITE_NAV__', _site_nav)
PAGE = PAGE.replace('__SITE_NAV_JS__', _nav_js)
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(PAGE)
print(f'wrote {ROOT}/index.html ({len(PAGE):,} bytes)')
print(f'  total: {stats["total"]}, local: {stats["local_total"]}')
