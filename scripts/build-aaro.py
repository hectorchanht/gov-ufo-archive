#!/usr/bin/env python3
"""Build aaro/index.html — evidence-first archive page.

Reads:  aaro/.cache/parsed.json + .cache/evidence.json
Writes: aaro/index.html

Output reflects whatever's actually on disk: videos, PDFs, and images that
exist locally are marked LOCAL; the rest fall back to the original source URL.
"""
import json, os, re, html, urllib.parse, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _site_template import make_nav, LIGHTBOX_HTML, _I18N_JSON

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, 'aaro')
CACHE = os.path.join(ROOT, '.cache')
parsed = json.load(open(os.path.join(CACHE, 'parsed.json')))
evidence = json.load(open(os.path.join(CACHE, 'evidence.json')))

# Local inventories — git-tracking-aware so the manifest matches what will
# actually be served from GitHub Pages (or any deployed clone).
#
# A file is marked `local` ONLY if it is committed to the repo. Files that
# exist on disk but are gitignored stay routed through their source URL,
# so Download buttons can't return a 404 HTML page on Pages.
#
# Local users who want to browse their full sync'd disk can still get to
# the files via the OS file manager — buttons on the page reflect what
# the public site will serve.
import subprocess
def git_tracked(rel_dir):
    """Set of filenames committed under <repo>/aaro/<rel_dir>/."""
    try:
        out = subprocess.run(
            ['git', '-C', REPO, 'ls-files', f'aaro/{rel_dir}/'],
            capture_output=True, text=True, check=True,
        ).stdout
        prefix = f'aaro/{rel_dir}/'
        return {ln[len(prefix):] for ln in out.splitlines() if ln.startswith(prefix)}
    except (subprocess.CalledProcessError, FileNotFoundError):
        # No git or no checkout — fall back to disk, so this script still works
        # before the first commit.
        p = os.path.join(ROOT, rel_dir)
        return set(os.listdir(p)) if os.path.isdir(p) else set()
local_pdfs = git_tracked('pdfs')
local_imgs = git_tracked('assets/images')
local_vids = git_tracked('videos')

def basename(url):
    return urllib.parse.unquote(url.rsplit('/',1)[-1].split('?')[0])

# === Build asset table ===
assets = []

# Videos
for v in evidence['videos']:
    bn = v['filename']
    local = 'videos/' + bn if bn in local_vids else ''
    # Parse title for tags
    title = v.get('title') or v['dod_id']
    # Detect status
    status = 'Unresolved' if 'Unresolved' in title else \
             'Resolved' if 'Resolv' in title else \
             'Undergoing Analysis' if 'Undergoing' in title else \
             'Closed' if 'Closed' in title else \
             'Other'
    # Detect region
    region = ''
    for r in ['Europe','Africa','Middle East','Asia','Atlantic','Pacific','Western U.S.','Western US','Puerto Rico','Etna','Al Taqaddum','Navy','South Asian']:
        if r in title: region = r; break
    assets.append({
        'type': 'VID',
        'kind_label': 'Video',
        'title': title,
        'desc': '',  # add below
        'agency': 'AARO / DVIDS',
        'date': '',
        'region': region,
        'status': status,
        'dod_id': v['dod_id'],
        'dvids_id': v.get('dvids_id'),
        'url': v['url'],
        'src': f"https://www.dvidshub.net/video/{v['dvids_id']}" if v.get('dvids_id') else 'https://www.aaro.mil/UAP-Cases/Official-UAP-Imagery/',
        'local': local,
    })

# Pop in case-resolution PDFs as documents (priority list)
PRIORITY_PDFS = [
    ('AARO_Al_Taqaddam_Case_Resolution_Final.pdf', 'Al Taqaddum Case Resolution', 'AARO case-resolution report for Al Taqaddum object.', 'Case Resolution'),
    ('AARO_GoFast_Case_Resolution_Card_Methodology_Final.pdf', '"GO FAST" Case Resolution Methodology', 'AARO case-resolution methodology for the famous Navy "GO FAST" video.', 'Case Resolution'),
    ('AARO_Puerto_Rico_UAP_Case_Resolution.pdf', 'Puerto Rico UAP Case Resolution', 'AARO case-resolution report on Puerto Rico UAP object.', 'Case Resolution'),
    ('Case_Resolution_of _Western_United_States_Uap_508-02262024.pdf', 'Western U.S. UAP Case Resolution', 'AARO case-resolution covering Western U.S. UAP observations.', 'Case Resolution'),
    ('Case_Resolution_of_Atmospheric_Wakes_508-02262024.pdf', 'Atmospheric Wakes Case Resolution', 'AARO case-resolution report explaining atmospheric wakes — South Asian object.', 'Case Resolution'),
    ('Mt-Etna-Object.pdf', 'Mt. Etna Object Analysis', 'AARO analysis of the Mt. Etna object incident.', 'Case Resolution'),
    ('AARO_Historical_Record_Report_Vol_1_2024.pdf', 'Historical Record Report Vol. 1 (2024)', 'AARO Historical Record Report, Volume 1 — exhaustive review of U.S. government UAP records.', 'Historical Record'),
    ('AARO_Mission_Brief_2025.pdf', 'AARO Mission Brief (2025)', 'Official mission brief covering AARO scope, methodology, and progress.', 'Mission Brief'),
    ('AARO_PIA_Section_1.pdf', 'Privacy Impact Assessment', 'Privacy Impact Assessment for AARO data collection and reporting systems.', 'Mission Brief'),
    ('AARO_SAPCO_CAPCO_Memos_on_AARO_Authorities.pdf', 'SAPCO/CAPCO Authority Memos', 'Special Access Program Central Office memos on AARO classification handling authorities.', 'Authority'),
    ('AARO_Brief_to_SASC-DoD_UAP_Mission-April_19_2023_508.pdf', 'Senate Armed Services Committee Brief (April 2023)', 'AARO briefing to the Senate Armed Services Committee on the DoD UAP mission.', 'Congressional'),
    ('AARO_Brief_at_Annual_Transportation_Research_Board-January_11_2023_508.pdf', 'Transportation Research Board Brief (Jan 2023)', 'AARO brief delivered at the Annual Transportation Research Board.', 'Congressional'),
    ('Dr_Jon_Kosloski_Statement_for_the_Record_SASC_Open_Hearing_Nov2024.pdf', 'Director Kosloski — SASC Open Hearing Statement (Nov 2024)', 'Statement for the record by AARO Director Dr. Jon T. Kosloski before the Senate Armed Services Committee.', 'Congressional'),
]
priority_set = {p[0] for p in PRIORITY_PDFS}
PDF_RELEASE_BASE = 'https://github.com/hectorchanht/war-gov-ufo-release/releases/download/pdfs-v1/'
import urllib.parse as _up
def release_url(fname):
    return PDF_RELEASE_BASE + _up.quote(fname)

# Add priority PDFs first
for fname, title, desc, category in PRIORITY_PDFS:
    local = 'pdfs/' + fname if fname in local_pdfs else ''
    src_url = next((p['url'] for p in evidence['pdfs'] if basename(p['url']) == fname), '')
    if not src_url:
        for p in evidence['pdfs']:
            if basename(p['url']).lower() == fname.lower():
                src_url = p['url']; break
    assets.append({
        'type': 'PDF',
        'kind_label': 'Document',
        'title': title,
        'desc': desc,
        'agency': 'AARO',
        'category': category,
        'url': release_url(fname),
        'src': src_url,
        'local': local,
    })

# Remaining PDFs
for p in evidence['pdfs']:
    bn = basename(p['url'])
    if bn in priority_set: continue
    local = 'pdfs/' + bn if bn in local_pdfs else ''
    url_low = p['url'].lower()
    category = 'FOIA' if 'foia' in url_low else \
               'Case Resolution' if 'case_resolution' in url_low else \
               'Document'
    title = bn.rsplit('.',1)[0].replace('_',' ').replace('-',' ').strip()
    agency = 'FBI' if 'fbi' in bn.lower() else \
             'NARA' if 'nara' in bn.lower() else \
             'AARO'
    assets.append({
        'type': 'PDF',
        'kind_label': 'Document',
        'title': title,
        'desc': '',
        'agency': agency,
        'category': category,
        'url': release_url(bn),
        'src': p['url'],
        'local': local,
    })

# Images
for i in evidence['images']:
    bn = basename(i['url'])
    local = 'assets/images/' + bn if bn in local_imgs else ''
    # Skip tiny UI chrome
    if any(x in bn.lower() for x in ('seal_100','icon','sprite','header_')):
        continue
    assets.append({
        'type': 'IMG',
        'kind_label': 'Image',
        'title': bn.rsplit('.',1)[0].replace('_',' ').replace('-',' '),
        'desc': '',
        'agency': 'AARO',
        'url': local or i['url'],
        'src': i['url'],
        'local': local,
    })

# Merge scraped records not already in the assets list
_scraped_cache = os.path.join(CACHE, 'scraped-index.json')
if os.path.exists(_scraped_cache):
    _seen_src = {a.get('src', '') for a in assets}
    _seen_bn  = {basename(a.get('src', '') or a.get('url', '')) for a in assets}
    for _r in json.load(open(_scraped_cache)):
        _url = _r.get('url', '')
        if not _url: continue
        if _url in _seen_src or basename(_url) in _seen_bn: continue
        _seen_src.add(_url); _seen_bn.add(basename(_url))
        assets.append({
            'type': 'PDF',
            'kind_label': 'Document',
            'title': _r.get('title', ''),
            'desc': _r.get('desc', ''),
            'agency': 'AARO',
            'category': 'Document',
            'date': '',
            'region': '',
            'status': 'Other',
            'url': _url,
            'src': _r.get('src', _url),
            'local': '',
        })

# Stats
stats = {
    'videos_local': sum(1 for a in assets if a['type']=='VID' and a['local']),
    'videos_total': sum(1 for a in assets if a['type']=='VID'),
    'pdfs_local':   sum(1 for a in assets if a['type']=='PDF' and a['local']),
    'pdfs_total':   sum(1 for a in assets if a['type']=='PDF'),
    'imgs_local':   sum(1 for a in assets if a['type']=='IMG' and a['local']),
    'imgs_total':   sum(1 for a in assets if a['type']=='IMG'),
    'total':        len(assets),
    'local_total':  sum(1 for a in assets if a['local']),
}

# Carousel slides: pick up to 8 highest-priority videos (with local files);
# fall back to local case-resolution images. Dedupe by local path.
# Each slide carries BOTH local + remote URL so the carousel still works
# on GitHub Pages where gitignored videos are absent — the <video> element
# uses two <source> children, browser picks first that loads.
carousel = []
seen = set()
for a in assets:
    if a['type']=='VID' and a['local'] and a['local'] not in seen:
        carousel.append({
            'local': a['local'],
            'url':   a.get('url') or '',
            'title': a['title'],
            'dod_id': a.get('dod_id'),
            'kind': 'video',
        })
        seen.add(a['local'])
        if len(carousel) >= 8: break
# If we didn't get 8 videos locally, fill with VID assets where we only
# have a remote URL — they will still play in the carousel via cloudfront.
if len(carousel) < 8:
    for a in assets:
        if a['type']=='VID' and not a['local'] and a.get('url') and a['url'] not in seen:
            carousel.append({
                'local': '',
                'url': a['url'],
                'title': a['title'],
                'dod_id': a.get('dod_id'),
                'kind': 'video',
            })
            seen.add(a['url'])
            if len(carousel) >= 8: break
if len(carousel) < 8:
    for a in assets:
        if a['type']=='IMG' and a['local'] and a['local'] not in seen:
            carousel.append({
                'local': a['local'],
                'url':   a.get('url') or '',
                'title': a['title'],
                'kind': 'image',
            })
            seen.add(a['local'])
            if len(carousel) >= 8: break

# Asset data for JS (compact)
asset_data = []
for a in assets:
    asset_data.append({
        't': a['type'],
        'k': a.get('kind_label',''),
        'ti': a['title'],
        'de': a.get('desc',''),
        'ag': a.get('agency',''),
        'cat': a.get('category',''),
        're': a.get('region',''),
        'st': a.get('status',''),
        'di': a.get('dvids_id') or '',
        'dd': a.get('dod_id') or '',
        'u': a.get('url','') or '',
        's': a.get('src','') or '',
        'l': a.get('local','') or '',
    })

asset_json = json.dumps({'assets': asset_data, 'carousel': carousel, 'stats': stats}, ensure_ascii=False).replace('</script', '<\\/script')
PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AARO — All-domain Anomaly Resolution Office (Offline Mirror)</title>
<meta name="description" content="Offline archival mirror of aaro.mil — official UAP imagery, case resolution reports, and historical records.">
<link rel="canonical" href="https://realufo.org/aaro/">
<meta property="og:title" content="AARO — All-domain Anomaly Resolution Office | realufo.org">
<meta property="og:description" content="Offline mirror of aaro.mil. 32 official UAP videos, 44 case-resolution and FOIA PDFs, full mission text and FAQ — the U.S. government's live UAP investigation programme.">
<meta property="og:image" content="https://realufo.org/aaro/assets/images/Go_Fast_UAP.jpg">
<meta property="og:url" content="https://realufo.org/aaro/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="realufo.org">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="AARO — All-domain Anomaly Resolution Office | realufo.org">
<meta name="twitter:description" content="Offline mirror of aaro.mil. 32 official UAP videos, 44 case-resolution and FOIA PDFs, full mission text and FAQ — the U.S. government's live UAP investigation programme.">
<meta name="twitter:image" content="https://realufo.org/aaro/assets/images/Go_Fast_UAP.jpg">
<link rel="icon" type="image/svg+xml" href="./assets/favicon.svg">
<link rel="apple-touch-icon" href="./assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap" rel="stylesheet">
<style>
:root {
  --bg:#0a0a0c; --bg-2:#111114; --panel:#15151a; --panel-2:#1a1a20;
  --ink:#e8e3d8; --ink-dim:#a8a298; --ink-faint:#6b665d;
  --rule:rgba(232,227,216,0.12); --rule-strong:rgba(232,227,216,0.28);
  --stamp:#b91c1c; --caution:#4a9eff; --warm:#d4a017; --classified:#c9362c;
  --resolved:#6fbf52; --unresolved:#c9362c; --analysis:#d4a017;
  --serif:"Source Serif 4","Iowan Old Style",Georgia,serif;
  --mono:"JetBrains Mono","SF Mono",Consolas,monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; scroll-padding-top: 64px; }
body {
  background: var(--bg); color: var(--ink);
  font-family: var(--serif); font-size: 17px; line-height: 1.65;
  background-image:
    radial-gradient(ellipse at 20% 0%, rgba(74,158,255,0.05) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(212,160,23,0.04) 0%, transparent 50%);
  background-attachment: fixed;
  overflow-x: hidden;
}
body::before {
  content:""; position: fixed; inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.06 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  opacity: 0.4; pointer-events: none; z-index: 1; mix-blend-mode: overlay;
}
.scanlines {
  position: fixed; inset: 0;
  background: repeating-linear-gradient(to bottom, transparent 0, transparent 2px, rgba(255,255,255,0.012) 3px, transparent 4px);
  pointer-events: none; z-index: 50;
}
.container { max-width: 1280px; margin: 0 auto; padding: 0 32px; position: relative; z-index: 2; }

.gov-banner {
  background: #1a1a1f; border-bottom: 1px solid var(--rule);
  font-family: var(--mono); font-size: 11px; color: var(--ink-dim);
  letter-spacing: 0.04em;
}
.gov-banner .container { display: flex; align-items: center; gap: 16px; padding: 10px 32px; }
.gov-banner strong { color: var(--ink); font-weight: 500; }
.gov-banner a { color: var(--caution); text-decoration: none; margin-left: auto; }
.gov-banner a:hover { text-decoration: underline; }
.flag-dot { width: 10px; height: 10px; border-radius: 50%;
  background: linear-gradient(45deg,#b91c1c 0,#b91c1c 50%,#1e3a8a 50%,#1e3a8a 100%); flex-shrink: 0; }

/* Header sticky */
.header-wrap {
  position: sticky; top: 0; z-index: 40;
  background: rgba(10,10,12,0.95);
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--rule);
}
header { padding: 16px 0; }
header .container { display: flex; align-items: center; gap: 12px; flex-wrap: nowrap; }
.brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--ink); flex-shrink: 1; min-width: 0; }
.seal {
  width: 48px; height: 48px;
  background: radial-gradient(circle at 50% 50%, #1e3a8a 0%, #102560 60%, #061238 100%);
  border-radius: 50%; display: grid; place-items: center;
  box-shadow: 0 0 0 2px var(--ink), 0 0 0 4px var(--bg), 0 0 0 5px var(--ink-faint);
  font-family: var(--mono); font-weight: 700; font-size: 11px; color: var(--ink);
  letter-spacing: 0.04em; position: relative;
}
.seal::after { content: ""; position: absolute; inset: 4px; border: 1px dashed rgba(232, 227, 216, 0.4); border-radius: 50%; }
.brand-text { display: flex; flex-direction: column; line-height: 1.1; min-width: 0; }
.brand-text .super { font-family: var(--mono); font-size: 9px; letter-spacing: 0.2em; color: var(--ink-dim); text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 210px; }
.brand-text .name { font-family: var(--serif); font-size: 18px; font-weight: 600; margin-top: 2px; }
nav.primary { font-family: var(--mono); font-size: 12px; letter-spacing: 0.08em; flex: 1; }
.nav-toggle { display: none; background: transparent; border: 1px solid var(--rule-strong); width: 38px; height: 38px; cursor: pointer; padding: 0; flex-direction: column; justify-content: center; align-items: center; gap: 4px; flex-shrink: 0; margin-left: auto; }
.nav-toggle span { display: block; width: 18px; height: 2px; background: var(--ink); transition: transform .2s, opacity .2s; }
.nav-toggle[aria-expanded="true"] span:nth-child(1) { transform: translateY(6px) rotate(45deg); }
.nav-toggle[aria-expanded="true"] span:nth-child(2) { opacity: 0; }
.nav-toggle[aria-expanded="true"] span:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }
@media (max-width: 720px) {
  .nav-toggle { display: flex; }
  nav.primary { display: none; flex-basis: 100%; }
  nav.primary.open { display: block; }
  nav.primary ul { flex-direction: column; gap: 0; padding-top: 12px; margin-top: 12px; border-top: 1px solid var(--rule); justify-content: flex-start; }
  nav.primary ul li { width: 100%; }
  nav.primary ul a { display: block; padding: 12px 0; border-bottom: 1px solid var(--rule); }
  .arch-controls-bar { flex-direction: column; align-items: stretch; gap: 10px; }
  .tabs { gap: 6px; flex-wrap: wrap; width: 100%; }
  .tab { padding: 6px 10px; font-size: 10px; }
  .sort-wrap, .search-wrap { margin: 0; width: 100%; }
  .filter-bar { gap: 12px; }
  .filter-bar label { font-size: 10px; }
  .arch-grid { grid-template-columns: 1fr; gap: 12px; }
  body { font-size: 15px; }
}
nav.primary ul { display: flex; gap: 4px 22px; list-style: none; flex-wrap: wrap; justify-content: flex-end; }
nav.primary a { color: var(--ink-dim); text-decoration: none; transition: color .15s; text-transform: uppercase; }
nav.primary a:hover { color: var(--caution); }
nav.primary a.active { color: var(--caution); }
nav.primary a.active::before { content: "▸ "; }

/* HERO */
.hero { padding: 64px 0 48px; border-bottom: 1px solid var(--rule); position: relative; }
.coords {
  font-family: var(--mono); font-size: 12px;
  color: var(--caution); letter-spacing: 0.12em;
  margin-bottom: 20px; display: flex; align-items: center; gap: 12px;
}
.coords::before { content: "◉"; color: var(--stamp); }
.coords::after { content: ""; flex: 1; height: 1px; background: linear-gradient(to right, var(--caution), transparent); margin-left: 12px; max-width: 200px; }
h1.hero-title {
  font-family: var(--serif); font-weight: 700;
  font-size: clamp(30px,4.8vw,56px); line-height: 1.05;
  letter-spacing: -0.02em; max-width: 22ch; margin-bottom: 22px;
}
h1.hero-title em { color: var(--caution); font-style: italic; }
.hero-sub {
  max-width: 65ch; color: var(--ink-dim); font-size: 17px; line-height: 1.65;
  margin-bottom: 32px;
}
.hero-sub a { color: var(--caution); }

.classified-stamp {
  position: absolute; top: 56px; right: 32px;
  transform: rotate(-10deg);
  border: 3px solid var(--classified); color: var(--classified);
  padding: 8px 16px;
  font-family: var(--mono); font-weight: 700; font-size: 12px;
  letter-spacing: 0.18em; opacity: 0.7;
}
.classified-stamp small { display: block; font-size: 9px; opacity: 0.7; margin-top: 2px; letter-spacing: 0.1em; }
@media (max-width: 800px) { .classified-stamp { display: none; } }

/* HERO CAROUSEL */
.hero-carousel {
  position: relative;
  border: 1px solid var(--rule-strong);
  background: var(--bg-2);
  aspect-ratio: 16/9;
  overflow: hidden;
  max-width: 1080px;
  margin-top: 12px;
}
.carousel-slide {
  position: absolute; inset: 0;
  opacity: 0; transition: opacity .8s ease;
  pointer-events: none;
}
.carousel-slide.active { opacity: 1; pointer-events: auto; }
.carousel-slide img, .carousel-slide video {
  width: 100%; height: 100%; object-fit: cover;
  filter: contrast(1.04) saturate(0.9);
  display: block;
}
.carousel-slide::after {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.78) 0%, rgba(0,0,0,0.0) 50%);
  pointer-events: none;
}
.carousel-btn {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 46px; height: 46px;
  background: rgba(0,0,0,0.6); border: 1px solid var(--rule-strong); color: var(--ink);
  font-family: var(--serif); font-size: 28px; cursor: pointer; z-index: 3;
  transition: background .15s, border-color .15s, color .15s;
}
.carousel-btn:hover { background: rgba(0,0,0,0.9); border-color: var(--caution); color: var(--caution); }
.carousel-btn.prev { left: 14px; }
.carousel-btn.next { right: 14px; }
.carousel-dots {
  position: absolute; bottom: 64px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 6px; z-index: 3;
}
.carousel-dots button {
  width: 8px; height: 8px; border-radius: 50%;
  background: rgba(255,255,255,0.4); border: 0; cursor: pointer; padding: 0;
  transition: background .15s, transform .15s;
}
.carousel-dots button.active { background: var(--caution); transform: scale(1.4); }
.carousel-caption {
  position: absolute; bottom: 18px; left: 0; right: 0; text-align: center;
  font-family: var(--mono); font-size: 12px; color: var(--ink); letter-spacing: 0.06em;
  padding: 0 70px; z-index: 2; text-shadow: 0 1px 4px rgba(0,0,0,0.9);
}
.carousel-caption .badge { color: var(--caution); margin-right: 8px; font-weight: 700; }

/* HEADLINES */
.headlines {
  padding: 48px 0; border-bottom: 1px solid var(--rule);
}
.head-grid {
  display: grid; gap: 20px;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}
.head-card {
  padding: 22px 24px; background: var(--panel);
  border: 1px solid var(--rule); border-left: 3px solid var(--caution);
  font-family: var(--serif);
}
.head-card .h-label {
  font-family: var(--mono); font-size: 10px; color: var(--caution);
  letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 10px;
}
.head-card .h-text { font-size: 18px; line-height: 1.4; color: var(--ink); }
.head-card .h-text em { color: var(--warm); font-style: italic; }
.head-card .h-num {
  font-family: var(--mono); font-size: 32px; color: var(--ink); font-weight: 600;
  display: block; margin-bottom: 4px;
}

/* SECTION */
section { padding: 64px 0; border-bottom: 1px solid var(--rule); position: relative; }
.section-label {
  font-family: var(--mono); font-size: 11px; letter-spacing: 0.24em;
  text-transform: uppercase; color: var(--ink-faint);
  display: flex; align-items: center; gap: 16px; margin-bottom: 20px;
}
.section-label::before { content: ""; width: 28px; height: 1px; background: var(--ink-faint); }
h2 {
  font-family: var(--serif); font-size: clamp(26px,3.2vw,40px);
  font-weight: 700; letter-spacing: -0.015em; line-height: 1.1;
  margin-bottom: 22px; max-width: 26ch;
}
.lede { max-width: 70ch; color: var(--ink); font-size: 18px; line-height: 1.65; }
.lede + .lede { margin-top: 14px; color: var(--ink-dim); }
.lede a { color: var(--caution); }

/* ARCHIVE */
.stats-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1px; background: var(--rule); border: 1px solid var(--rule);
  margin: 24px 0 28px;
}
.stat { background: var(--panel); padding: 18px 22px; font-family: var(--mono); }
.stat b { display: block; font-size: 28px; color: var(--ink); font-weight: 500; letter-spacing: -0.02em; }
.stat small { display: block; font-size: 10px; color: var(--ink-faint); letter-spacing: 0.16em; text-transform: uppercase; margin-top: 6px; }

.arch-controls-bar {
  position: sticky; top: 64px; z-index: 30;
  background: rgba(10,10,12,0.95);
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule);
  margin: 28px -32px 0; padding: 14px 32px;
  display: flex; gap: 14px; align-items: center; flex-wrap: wrap;
}
.tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.tab {
  font-family: var(--mono); font-size: 11px;
  padding: 8px 14px; border: 1px solid var(--rule-strong);
  background: var(--panel); color: var(--ink-dim);
  cursor: pointer; letter-spacing: 0.08em; text-transform: uppercase;
  transition: all .15s;
}
.tab:hover { color: var(--ink); border-color: var(--ink-faint); }
.tab.active { background: var(--caution); color: var(--bg); border-color: var(--caution); font-weight: 700; }
.tab .count { opacity: 0.6; margin-left: 6px; font-size: 10px; }
.tab.active .count { opacity: 0.9; }
.sort-wrap, .filter-bar label {
  display: flex; align-items: center; gap: 8px;
  font-family: var(--mono); font-size: 11px; color: var(--ink-faint);
  letter-spacing: 0.08em; text-transform: uppercase;
}
.sort-wrap select, .filter-bar select {
  background: var(--panel); color: var(--ink);
  border: 1px solid var(--rule-strong); padding: 6px 10px;
  font-family: var(--mono); font-size: 11px; cursor: pointer;
}
.search-wrap {
  margin-left: auto;
  display: flex; align-items: center; gap: 8px;
  background: var(--panel); border: 1px solid var(--rule-strong);
  padding: 6px 12px; min-width: 240px;
}
.search-wrap::before { content: "⌕"; color: var(--ink-faint); font-family: var(--mono); }
.search-wrap input { background: transparent; border: 0; outline: 0; color: var(--ink); font-family: var(--mono); font-size: 12px; flex: 1; }
.search-wrap input::placeholder { color: var(--ink-faint); }
.filter-bar {
  display: flex; align-items: center; gap: 24px; flex-wrap: wrap;
  margin: 18px 0 4px; padding: 14px 0;
  border-bottom: 1px dashed var(--rule);
}
.filter-bar label.localonly { color: var(--ink-dim); }
.filter-bar input[type=checkbox] { width: 14px; height: 14px; accent-color: var(--caution); }

.result-count {
  font-family: var(--mono); font-size: 11px; color: var(--ink-faint);
  letter-spacing: 0.12em; text-transform: uppercase;
  padding: 20px 0 8px;
}
.result-count b { color: var(--caution); }

.arch-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px; padding: 8px 0 24px;
}
.card {
  background: var(--panel); border: 1px solid var(--rule);
  display: flex; flex-direction: column; overflow: hidden;
  transition: border-color .2s, transform .2s; position: relative;
}
.card:hover { border-color: var(--caution); transform: translateY(-2px); }
.card-media {
  aspect-ratio: 16/9; background: var(--bg-2);
  position: relative; overflow: hidden;
  display: grid; place-items: center;
  border-bottom: 1px solid var(--rule); cursor: pointer;
}
.card-media img, .card-media video {
  width: 100%; height: 100%; object-fit: cover; display: block;
}
.pdf-glyph {
  font-family: var(--mono); font-size: 13px; color: var(--ink-faint);
  background: repeating-linear-gradient(45deg,#1a1a1f,#1a1a1f 8px,#15151a 8px,#15151a 16px);
  width: 100%; height: 100%; display: grid; place-items: center;
  text-align: center; padding: 16px;
}
.pdf-glyph .ico {
  font-size: 26px; color: var(--caution); margin-bottom: 6px;
  border: 2px solid var(--caution); padding: 4px 10px;
  font-weight: 700; letter-spacing: 0.04em;
  display: inline-block;
}
.video-glyph { background: linear-gradient(135deg, rgba(74,158,255,0.08), rgba(212,160,23,0.04)); }
.video-glyph .ico { color: var(--warm); border-color: var(--warm); }
.badge {
  position: absolute; top: 8px; left: 8px;
  background: rgba(0,0,0,0.78); color: var(--caution);
  font-family: var(--mono); font-size: 9px;
  padding: 3px 8px; letter-spacing: 0.14em;
  text-transform: uppercase;
}
.badge.status {
  top: 8px; right: 8px; left: auto;
}
.badge.status.unresolved { background: rgba(201,54,44,0.85); color: var(--ink); }
.badge.status.resolved { background: rgba(111,191,82,0.85); color: var(--bg); }
.badge.status.analysis { background: rgba(212,160,23,0.85); color: var(--bg); }
.badge.status.closed { background: rgba(168,162,152,0.6); color: var(--ink); }
.badge.local { bottom: 8px; left: 8px; top: auto;
  background: rgba(0,0,0,0.78); color: var(--warm);
}
.badge.source { bottom: 8px; left: 8px; top: auto;
  background: rgba(0,0,0,0.78); color: var(--ink-faint);
}
.card-body {
  padding: 14px 16px; flex: 1;
  display: flex; flex-direction: column; gap: 6px;
}
.card-title {
  font-family: var(--serif); font-size: 14px; line-height: 1.35;
  font-weight: 600; color: var(--ink); overflow-wrap: anywhere;
}
.card-desc {
  font-family: var(--serif); font-size: 12.5px;
  color: var(--ink-dim); line-height: 1.5; margin-top: 4px;
}
.card-meta {
  display: grid; grid-template-columns: 80px 1fr;
  gap: 4px 12px; margin-top: 8px; padding: 10px 0;
  border-top: 1px solid var(--rule);
}
.card-meta dt {
  font-family: var(--mono); font-size: 9px; color: var(--ink-faint);
  letter-spacing: 0.14em; text-transform: uppercase;
}
.card-meta dd {
  font-family: var(--serif); color: var(--ink); font-size: 12px; line-height: 1.4;
  overflow-wrap: anywhere;
}
.card-meta dd.mono { font-family: var(--mono); font-size: 10px; color: var(--caution); }
.card-actions {
  display: flex; gap: 8px; margin-top: 8px;
  padding-top: 8px; border-top: 1px dashed var(--rule);
  flex-wrap: wrap;
}
.card-actions a {
  font-family: var(--mono); font-size: 10px;
  color: var(--caution); text-decoration: none;
  letter-spacing: 0.12em; text-transform: uppercase;
  padding: 4px 8px; border: 1px solid var(--rule-strong);
  transition: all .15s;
}
.card-actions a:hover { background: var(--caution); color: var(--bg); border-color: var(--caution); }
.card-actions a.warn { color: var(--ink-faint); }
.card-actions a.warn:hover { background: var(--ink-faint); color: var(--bg); }

.empty {
  padding: 60px 0; text-align: center; color: var(--ink-faint);
  font-family: var(--mono); font-size: 13px; letter-spacing: 0.08em;
}

/* PAGINATION */
.pagination {
  display: flex; gap: 6px; justify-content: center; align-items: center;
  flex-wrap: wrap; margin: 32px 0 0;
  padding: 24px 0; border-top: 1px solid var(--rule);
}
.pagination button {
  font-family: var(--mono); font-size: 11px;
  padding: 8px 12px; min-width: 36px;
  border: 1px solid var(--rule-strong);
  background: var(--panel); color: var(--ink-dim); cursor: pointer;
  letter-spacing: 0.06em;
  transition: all .15s;
}
.pagination button:hover:not(:disabled) { color: var(--ink); border-color: var(--caution); }
.pagination button.active { background: var(--caution); color: var(--bg); border-color: var(--caution); font-weight: 700; }
.pagination button:disabled { opacity: 0.3; cursor: not-allowed; }
.pagination .ellipsis { color: var(--ink-faint); padding: 0 6px; font-family: var(--mono); }
.pagination .info {
  margin-left: 12px; color: var(--ink-faint);
  font-family: var(--mono); font-size: 10px;
  letter-spacing: 0.08em; text-transform: uppercase;
}

/* LIGHTBOX */
.lightbox {
  position: fixed; inset: 0; background: rgba(0,0,0,0.94);
  display: none; place-items: center; z-index: 200; padding: 32px;
}
.lightbox.open { display: grid; }
.lb-inner { max-width: 92vw; max-height: 92vh; display: flex; flex-direction: column; gap: 10px; align-items: center; }
.lb-inner img, .lb-inner video { max-width: 90vw; max-height: 82vh; border: 1px solid var(--rule-strong); background: #000; }
.lb-inner iframe { width: 90vw; height: 86vh; border: 1px solid var(--rule-strong); background: #fff; }
.lb-meta { font-family: var(--mono); font-size: 11px; color: var(--ink); background: var(--bg-2);
           border: 1px solid var(--rule-strong); padding: 8px 14px; max-width: 80vw; text-align: center; }
.lb-meta a { color: var(--caution); }
.lb-close {
  position: absolute; top: 16px; right: 24px;
  width: 40px; height: 40px;
  background: var(--bg-2); border: 1px solid var(--rule-strong); color: var(--ink);
  display: grid; place-items: center; cursor: pointer;
  font-family: var(--mono); font-size: 22px; z-index: 2;
}
.lb-nav {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 52px; height: 52px;
  background: rgba(20,20,24,0.6);
  border: 1px solid var(--rule-strong);
  color: var(--ink);
  display: grid; place-items: center; cursor: pointer;
  font-family: var(--serif); font-size: 32px; line-height: 1;
  z-index: 2;
  transition: background .15s, color .15s, border-color .15s;
}
.lb-nav:hover { background: rgba(0,0,0,0.85); color: var(--caution); border-color: var(--caution); }
.lb-nav.prev { left: 16px; }
.lb-nav.next { right: 16px; }
.lb-counter {
  position: absolute; top: 24px; left: 50%; transform: translateX(-50%);
  font-family: var(--mono); font-size: 11px; letter-spacing: 0.16em;
  color: var(--ink-dim); background: var(--bg-2);
  border: 1px solid var(--rule); padding: 4px 12px; z-index: 2;
}
@media (max-width: 720px) {
  .lb-nav { width: 40px; height: 40px; font-size: 24px; }
  .lb-nav.prev { left: 8px; }
  .lb-nav.next { right: 8px; }
}

/* CALL TO READ */
.learn { text-align: center; padding: 64px 0; }
.learn h2 { margin: 0 auto 18px; }
.learn p { color: var(--ink-dim); margin-bottom: 22px; max-width: 60ch; margin-left:auto; margin-right:auto; }
.learn a.external {
  display: inline-block;
  font-family: var(--mono); font-size: 13px; letter-spacing: 0.14em;
  color: var(--caution); text-decoration: none;
  padding: 14px 28px; border: 1px solid var(--caution);
  transition: all .2s;
}
.learn a.external:hover { background: var(--caution); color: var(--bg); }
.learn a.external::after { content: " ↗"; }

/* FOOTER */
footer {
  background: #060608; padding: 48px 0 28px;
  color: var(--ink-dim); font-family: var(--mono); font-size: 12px;
}
footer .container { display: grid; grid-template-columns: 1.4fr 1fr 1fr 1fr; gap: 40px; }
footer h4 {
  font-family: var(--mono); font-size: 11px; letter-spacing: 0.18em;
  text-transform: uppercase; color: var(--ink); margin-bottom: 14px;
}
footer ul { list-style: none; display: flex; flex-direction: column; gap: 8px; }
footer a { color: var(--ink-dim); text-decoration: none; }
footer a:hover { color: var(--caution); }
footer .colophon {
  grid-column: 1 / -1;
  border-top: 1px solid var(--rule); padding-top: 20px; margin-top: 20px;
  display: flex; justify-content: space-between; flex-wrap: wrap; gap: 16px;
  font-size: 10px; color: var(--ink-faint); letter-spacing: 0.1em;
}
@media (max-width: 760px) { footer .container { grid-template-columns: 1fr 1fr; } }
@media (max-width: 720px) {
  .container { padding: 0 16px; }
  .gov-banner .container { padding: 10px 16px; }
  .arch-controls-bar { margin: 24px -16px 0; padding: 12px 16px; }
  .hero-carousel { aspect-ratio: 16/10; }
  .carousel-caption { font-size: 10px; padding: 0 56px; bottom: 12px; }
  .carousel-dots { bottom: 36px; }
  .arch-grid { grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); }
  .card-meta { grid-template-columns: 72px 1fr; }
}
/* ── "More" dropdown + lang picker + scroll-hide (shared template) ── */
.nav-sep { display: none; }
@media (min-width: 720px) { .nav-sep { display: block; width: 1px; height: 16px; background: var(--rule-strong); } }
.has-dropdown { position: relative; }
.nav-more-btn { background: none; border: none; color: var(--ink-dim); cursor: pointer; font-family: var(--mono); font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; padding: 12px 0; display: block; width: 100%; text-align: left; border-bottom: 1px solid var(--rule); }
.nav-more-btn:hover { color: var(--caution); }
.nav-dropdown { display: none; list-style: none; background: var(--panel); border: 1px solid var(--rule-strong); padding: 6px 0; z-index: 200; }
.nav-dropdown li a { border: 0 !important; padding: 9px 16px !important; font-size: 10.5px; white-space: nowrap; }
.lang-picker { position: relative; }
.lang-btn { background: transparent; border: 1px solid var(--rule-strong); color: var(--ink-dim); cursor: pointer; font-family: var(--mono); font-size: 9.5px; letter-spacing: 0.12em; padding: 4px 8px; text-transform: uppercase; display: block; width: 100%; text-align: left; margin: 8px 0; }
.lang-btn:hover { color: var(--caution); border-color: var(--caution); }
.lang-menu { display: none; list-style: none; background: var(--panel); border: 1px solid var(--rule-strong); padding: 6px 0; z-index: 300; }
.lang-menu button { background: none; border: none; color: var(--ink-dim); cursor: pointer; font-family: var(--mono); font-size: 10.5px; padding: 8px 16px; width: 100%; text-align: left; }
.lang-menu button:hover { color: var(--caution); }
.lang-picker.open .lang-menu { display: block; }
.has-dropdown.open .nav-dropdown { display: block; }
.arch-controls-bar { transition: top 0.28s ease; }
.arch-controls-bar.bar-hidden { top: -160px; }
@media (max-width: 719px) {
  .nav-more-btn { padding: 11px 0; font-size: 11px; }
  .has-dropdown.open .nav-dropdown { margin-left: 12px; border: 0; background: transparent; }
  .lang-btn { border: 0; margin: 0; padding: 11px 0; font-size: 11px; border-bottom: 1px solid var(--rule); }
  .lang-picker.open .lang-menu { margin-left: 12px; border: 0; background: transparent; }
}
@media (min-width: 720px) {
  .nav-more-btn { padding: 0; border: 0; font-size: 10.5px; }
  .nav-dropdown { position: absolute; right: 0; top: calc(100% + 10px); min-width: 180px; }
  .has-dropdown:hover .nav-dropdown, .has-dropdown:focus-within .nav-dropdown { display: block; }
  .lang-btn { width: auto; margin: 0; padding: 3px 8px; }
  .lang-menu { position: absolute; right: 0; top: calc(100% + 10px); min-width: 130px; }
}
</style>
</head>
<body>

<div class="scanlines"></div>

<div class="header-wrap">
<header>
  <div class="container">
    <a href="#top" class="brand">
      <div class="seal">AARO</div>
      <div class="brand-text">
        <span class="super">All-domain Anomaly Resolution Office</span>
        <span class="name">AARO</span>
      </div>
    </a>
    <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
    __AARO_NAV__
  </div>
</header>
</div>

<!-- HERO -->
<div class="hero" id="top">
  <div class="container">
    <div class="coords">38°52′15″N, 77°03′18″W · OFFICE OF THE UNDER SECRETARY OF DEFENSE FOR INTELLIGENCE &amp; SECURITY</div>
    <h1 class="hero-title">All-domain Anomaly <em>Resolution</em> Office</h1>
    <p class="hero-sub">
      AARO leads the U.S. government's effort to detect, identify, attribute, and mitigate
      Unidentified Anomalous Phenomena using a rigorous scientific framework and a data-driven
      approach. This is an offline archival mirror of <a href="https://www.aaro.mil/" target="_blank" rel="noopener">aaro.mil</a> — every video, image, and report you see below
      is served from this local archive.
    </p>

    <div class="classified-stamp">
      DECLASSIFIED
      <small>OFFICIAL UAP IMAGERY</small>
    </div>

    <!-- Carousel -->
    <div class="hero-carousel" id="hero-carousel" aria-label="Featured AARO evidence">
      <div id="carousel-track"></div>
      <button class="carousel-btn prev" id="carousel-prev" aria-label="Previous">‹</button>
      <button class="carousel-btn next" id="carousel-next" aria-label="Next">›</button>
      <div class="carousel-dots" id="carousel-dots"></div>
      <div class="carousel-caption" id="carousel-caption"></div>
    </div>
  </div>
</div>

<!-- HEADLINES -->
<section id="headlines" class="headlines">
  <div class="container">
    <div class="section-label">§ Headlines · The mission, distilled</div>
    <div class="head-grid">
      <div class="head-card">
        <div class="h-label">Mandate</div>
        <div class="h-text">Detect, track, attribute, and <em>resolve</em> UAP near national-security areas.</div>
      </div>
      <div class="head-card">
        <div class="h-label">Established</div>
        <div class="h-num">2022</div>
        <div class="h-text">Stood up under the Office of the Under Secretary of Defense for Intelligence &amp; Security.</div>
      </div>
      <div class="head-card">
        <div class="h-label">Director</div>
        <div class="h-text">Dr. Jon T. Kosloski — formerly NSA Research Directorate; Ph.D., Electrical Engineering (Johns Hopkins).</div>
      </div>
      <div class="head-card">
        <div class="h-label">Methodology</div>
        <div class="h-text">Rigorous scientific framework. Reports treated like intelligence: collected, analyzed, attributed.</div>
      </div>
      <div class="head-card">
        <div class="h-label">Outputs</div>
        <div class="h-text">Case Resolution Reports · Historical Record Reports · Periodic Trend Reports · Public imagery.</div>
      </div>
      <div class="head-card">
        <div class="h-label">Transparency</div>
        <div class="h-text">Every release archived here. <em>Files are local</em> — no live aaro.mil calls required.</div>
      </div>
    </div>
  </div>
</section>

<!-- ARCHIVE — primary content -->
<section id="archive">
  <div class="container">
    <div class="section-label">§ Evidence · Official AARO Releases</div>
    <h2>Videos, case-resolution reports, congressional briefs, and FOIA releases.</h2>
    <p class="lede">
      Every UAP video AARO has officially released, alongside every case-resolution methodology, historical record,
      and congressional brief. Sourced from <a href="https://www.aaro.mil/UAP-Cases/Official-UAP-Imagery/" target="_blank" rel="noopener">aaro.mil/UAP-Cases/Official-UAP-Imagery</a> and the AARO documents portal.
    </p>

    <div class="stats-grid" id="arch-stats"></div>

    <div class="arch-controls-bar">
      <div class="tabs" id="arch-tabs"></div>
      <div class="sort-wrap">
        <label for="arch-sort">Sort:</label>
        <select id="arch-sort">
          <option value="status">Status</option>
          <option value="title">Title (A→Z)</option>
          <option value="title-desc">Title (Z→A)</option>
          <option value="local">Local first</option>
          <option value="type">Type</option>
        </select>
      </div>
      <div class="search-wrap">
        <input id="arch-search" type="search" placeholder="Search title, region, status, DVIDS…" autocomplete="off">
      </div>
    </div>

    <div class="filter-bar">
      <label>Status:
        <select id="filter-status">
          <option value="">All</option>
          <option value="Unresolved">Unresolved</option>
          <option value="Resolved">Resolved</option>
          <option value="Undergoing Analysis">Undergoing Analysis</option>
          <option value="Closed">Closed / Not Anomalous</option>
        </select>
      </label>
      <label>Region:
        <select id="filter-region"><option value="">All</option></select>
      </label>
      <label>Per page:
        <select id="filter-perpage">
          <option value="12">12</option>
          <option value="24" selected>24</option>
          <option value="48">48</option>
          <option value="96">96</option>
        </select>
      </label>
      <label class="localonly">
        <input type="checkbox" id="filter-local">
        <span>Local only</span>
      </label>
    </div>

    <div class="result-count" id="arch-count"></div>
    <div class="arch-grid" id="arch-grid"></div>
    <div class="empty" id="arch-empty" hidden>No evidence matches the current filter.</div>
    <nav class="pagination" id="pagination" aria-label="Evidence pagination"></nav>
  </div>
</section>

<!-- LEARN MORE -->
<section id="learn" class="learn">
  <div class="container">
    <div class="section-label" style="justify-content:center;">§ Background / FAQ / Mission</div>
    <h2>For the longer story.</h2>
    <p>
      Background on the office, the director's bio, frequently asked questions, the EFOIA reading room
      catalog, and the full text of every mirrored page — moved off this main page for focus.
    </p>
    <a class="external" href="./details.html">Open the details page</a>
  </div>
</section>

<footer>
  <div class="container">
    <div>
      <h4>AARO Mirror</h4>
      <p style="color: var(--ink-dim); font-family: var(--serif); margin-bottom: 14px;">
        Offline archival replica of aaro.mil. Federal U.S. government works are public domain (17 U.S.C. § 105).
      </p>
      <p style="color: var(--ink-faint); font-size: 10px; letter-spacing: 0.1em;">Source: aaro.mil + cloudfront CDN, captured 2025–2026.</p>
    </div>
    <div>
      <h4>Sections</h4>
      <ul>
        <li><a href="#top">Intro</a></li>
        <li><a href="#headlines">Headlines</a></li>
        <li><a href="#archive">Evidence</a></li>
        <li><a href="./details.html">Details ↗</a></li>
      </ul>
    </div>
    <div>
      <h4>Related</h4>
      <ul>
        <li><a href="../index.html">war.gov/UFO mirror</a></li>
        <li><a href="https://www.aaro.mil/" target="_blank" rel="noopener">Live aaro.mil ↗</a></li>
        <li><a href="https://www.archives.gov/research/topics/uaps" target="_blank" rel="noopener">NARA · UAP records ↗</a></li>
      </ul>
    </div>
    <div>
      <h4>Stats</h4>
      <ul>
        <li>Videos: __VID_L__ / __VID_T__ local</li>
        <li>Documents: __PDF_L__ / __PDF_T__ local</li>
        <li>Images: __IMG_L__ / __IMG_T__ local</li>
      </ul>
    </div>
    <div class="colophon">
      <span>Offline mirror · For research and reference</span>
      <span>Built from public source — aaro.mil</span>
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
__AARO_NAV_JS__
<script>
(() => {
  // Hamburger toggle
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
  const CAR = D.carousel;
  const STATS = D.stats;

  function esc(s){return (s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

  // ===== Stats =====
  const statsEl = document.getElementById('arch-stats');
  const STAT_DEFS = [
    ['Total', STATS.total],
    ['Local', STATS.local_total],
    ['Videos', STATS.videos_local + ' / ' + STATS.videos_total],
    ['Documents', STATS.pdfs_local + ' / ' + STATS.pdfs_total],
    ['Images', STATS.imgs_local + ' / ' + STATS.imgs_total],
  ];
  statsEl.innerHTML = STAT_DEFS.map(([k,v]) => `<div class="stat"><b>${v}</b><small>${k}</small></div>`).join('');

  // ===== Hero carousel =====
  const cTrack = document.getElementById('carousel-track');
  const cDots = document.getElementById('carousel-dots');
  const cCap = document.getElementById('carousel-caption');
  if (CAR.length) {
    CAR.forEach((s, i) => {
      const slide = document.createElement('div');
      slide.className = 'carousel-slide' + (i === 0 ? ' active' : '');
      if (s.kind === 'video') {
        // Two <source> children: local first, source URL second.
        // Browser walks the list and uses first that loads — so the
        // carousel works whether or not the local file was committed.
        const srcs = [];
        if (s.local) srcs.push(`<source src="./${s.local}#t=0.5" type="video/mp4">`);
        if (s.url)   srcs.push(`<source src="${esc(s.url)}#t=0.5" type="video/mp4">`);
        slide.innerHTML = `<video muted playsinline preload="metadata">${srcs.join('')}</video>`;
      } else {
        const fb = s.url ? `onerror="this.onerror=null;this.src='${esc(s.url)}';"` : '';
        slide.innerHTML = `<img src="./${s.local || s.url}" alt="${esc(s.title)}" loading="${i===0?'eager':'lazy'}" ${fb}>`;
      }
      cTrack.appendChild(slide);
      const dot = document.createElement('button');
      dot.type = 'button';
      if (i === 0) dot.classList.add('active');
      dot.setAttribute('aria-label', `Slide ${i+1}`);
      dot.addEventListener('click', () => goTo(i));
      cDots.appendChild(dot);
    });
    cCap.innerHTML = `<span class="badge">${CAR[0].dod_id || 'AARO'}</span>${esc(CAR[0].title)}`;
    let cIdx = 0, timer;
    function goTo(i){
      const slides = cTrack.children;
      const dots = cDots.children;
      slides[cIdx].classList.remove('active');
      dots[cIdx].classList.remove('active');
      // pause video before switching
      const oldVid = slides[cIdx].querySelector('video');
      if (oldVid) oldVid.pause();
      cIdx = (i + slides.length) % slides.length;
      slides[cIdx].classList.add('active');
      dots[cIdx].classList.add('active');
      const slide = CAR[cIdx];
      cCap.innerHTML = `<span class="badge">${slide.dod_id || 'AARO'}</span>${esc(slide.title)}`;
    }
    document.getElementById('carousel-prev').addEventListener('click', () => { goTo(cIdx-1); restart(); });
    document.getElementById('carousel-next').addEventListener('click', () => { goTo(cIdx+1); restart(); });
    function start(){ timer = setInterval(() => goTo(cIdx+1), 6500); }
    function restart(){ clearInterval(timer); start(); }
    start();
    const heroEl = document.getElementById('hero-carousel');
    heroEl.addEventListener('mouseenter', () => clearInterval(timer));
    heroEl.addEventListener('mouseleave', restart);
    cTrack.addEventListener('click', () => {
      openMedia(CAR[cIdx].local, CAR[cIdx].title, CAR[cIdx].url);
    });
  } else {
    document.getElementById('hero-carousel').style.display = 'none';
  }

  // ===== Region filter populate =====
  const regions = Array.from(new Set(items.map(a => a.re).filter(Boolean))).sort();
  const rSel = document.getElementById('filter-region');
  regions.forEach(r => { const o = document.createElement('option'); o.value = r; o.textContent = r; rSel.appendChild(o); });

  // ===== Tabs =====
  const COUNTS = { ALL: items.length };
  for (const a of items) COUNTS[a.t] = (COUNTS[a.t]||0)+1;
  const TABS = [
    {key:'ALL',label:'All Evidence'},
    {key:'VID',label:'Videos'},
    {key:'PDF',label:'Documents'},
    {key:'IMG',label:'Images'},
  ];
  const state = { tab:'ALL', q:'', sort:'status', status:'', region:'', perPage:24, page:1, local:false };
  const tabsEl = document.getElementById('arch-tabs');
  tabsEl.innerHTML = TABS.map(t => `<button class="tab${t.key===state.tab?' active':''}" data-key="${t.key}">${t.label}<span class="count">${COUNTS[t.key]||COUNTS.ALL}</span></button>`).join('');
  tabsEl.addEventListener('click', e => {
    const t = e.target.closest('.tab'); if (!t) return;
    state.tab = t.dataset.key; state.page = 1;
    tabsEl.querySelectorAll('.tab').forEach(x => x.classList.toggle('active', x.dataset.key===state.tab));
    render();
  });
  document.getElementById('arch-search').addEventListener('input', e => { state.q = e.target.value.trim().toLowerCase(); state.page = 1; render(); });
  document.getElementById('arch-sort').addEventListener('change', e => { state.sort = e.target.value; render(); });
  document.getElementById('filter-status').addEventListener('change', e => { state.status = e.target.value; state.page = 1; render(); });
  document.getElementById('filter-region').addEventListener('change', e => { state.region = e.target.value; state.page = 1; render(); });
  document.getElementById('filter-perpage').addEventListener('change', e => { state.perPage = parseInt(e.target.value,10); state.page = 1; render(); });
  document.getElementById('filter-local').addEventListener('change', e => { state.local = e.target.checked; state.page = 1; render(); });

  function statusBadge(st) {
    if (!st || st === 'Other') return '';
    const cls = st === 'Unresolved' ? 'unresolved' :
                st === 'Resolved' ? 'resolved' :
                st === 'Undergoing Analysis' ? 'analysis' :
                st === 'Closed' ? 'closed' : '';
    return `<span class="badge status ${cls}">${esc(st)}</span>`;
  }
  function mediaFor(a) {
    // For images: try local first, fall back to source URL on error.
    // Browser-native — works on both fully-synced local checkouts and on
    // GitHub Pages where gitignored files are absent.
    if (a.t === 'IMG' && a.l) {
      const fb = a.u ? `onerror="this.onerror=null;this.src='${esc(a.u)}';"` : '';
      return `<img loading="lazy" src="./${a.l}" alt="${esc(a.ti)}" ${fb}>`;
    }
    if (a.t === 'IMG' && a.u) return `<img loading="lazy" src="${esc(a.u)}" alt="${esc(a.ti)}" onerror="this.style.display='none';this.parentElement.classList.add('pdf-glyph');this.parentElement.innerHTML='<span class=&quot;ico&quot;>IMG</span><span>not archived</span>';">`;
    if (a.t === 'VID') {
      // Card preview uses a static glyph (no <video preload>) — rendering
      // 24 simultaneous cloudfront preloads chokes the page on mobile.
      // The lightbox creates a single <video> on click and streams directly.
      const label = esc(a.dd || a.ti.slice(0, 30));
      return `<div class="pdf-glyph video-glyph"><span class="ico">▶</span><span>${label}</span></div>`;
    }
    return `<div class="pdf-glyph"><span class="ico">PDF</span><span>${esc(a.ag||'')}</span></div>`;
  }
  function metaFor(a) {
    const rows = [];
    if (a.ag) rows.push(['Agency', a.ag]);
    if (a.cat) rows.push(['Category', a.cat]);
    if (a.re) rows.push(['Region', a.re]);
    if (a.st && a.st !== 'Other') rows.push(['Status', a.st]);
    if (a.dd) rows.push(['DOD ID', a.dd, 'mono']);
    if (a.di) rows.push(['DVIDS ID', a.di, 'mono']);
    return `<dl class="card-meta">` + rows.map(r => `<dt>${r[0]}</dt><dd${r[2]?' class="'+r[2]+'"':''}>${esc(r[1])}</dd>`).join('') + `</dl>`;
  }
  function actionsFor(a) {
    // Source = official site (a.s). Download = local file or release URL (a.u).
    const out = [];
    const verb = a.t === 'PDF' ? 'Open PDF' : (a.t === 'VID' ? '▶ Play' : 'View');
    const dl = a.l ? './' + a.l : a.u;
    if (a.l || a.u) {
      out.push(`<a href="#" data-action="open" data-title="${esc(a.ti)}">${verb}</a>`);
      out.push(`<a href="${esc(dl)}" ${a.l?'download':'target="_blank" rel="noopener"'}>Download</a>`);
    }
    if (a.s) out.push(`<a class="warn" href="${esc(a.s)}" target="_blank" rel="noopener">Source ↗</a>`);
    return `<div class="card-actions">${out.join('')}</div>`;
  }
  function cardHtml(a) {
    const localBadge = a.l ? `<span class="badge local">LOCAL</span>` : `<span class="badge source">SOURCE</span>`;
    return `<article class="card">
      <div class="card-media" data-local="${esc(a.l)}" data-remote="${esc(a.u||'')}" data-title="${esc(a.ti)}" data-action="${a.l?'open':'source'}">
        ${mediaFor(a)}
        <span class="badge">${esc(a.k||a.t)}</span>
        ${statusBadge(a.st)}
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

  function compare(a,b) {
    switch (state.sort) {
      case 'title': return (a.ti||'').localeCompare(b.ti||'');
      case 'title-desc': return (b.ti||'').localeCompare(a.ti||'');
      case 'local': return (b.l?1:0) - (a.l?1:0) || (a.ti||'').localeCompare(b.ti||'');
      case 'type':
        const ord = {'VID':0,'PDF':1,'IMG':2};
        return (ord[a.t]??9)-(ord[b.t]??9) || (a.ti||'').localeCompare(b.ti||'');
      case 'status':
      default:
        const sord = {'Unresolved':0,'Undergoing Analysis':1,'Resolved':2,'Closed':3,'Other':4,'':5};
        return (sord[a.st]??9)-(sord[b.st]??9) || (a.ti||'').localeCompare(b.ti||'');
    }
  }
  function filtered() {
    let list = items.filter(a => {
      if (state.tab !== 'ALL' && a.t !== state.tab) return false;
      if (state.local && !a.l) return false;
      if (state.status && a.st !== state.status) return false;
      if (state.region && a.re !== state.region) return false;
      if (state.q) {
        const hay = [a.ti,a.de,a.ag,a.cat,a.re,a.st,a.di,a.dd,a.l].join(' ').toLowerCase();
        if (!hay.includes(state.q)) return false;
      }
      return true;
    });
    list.sort(compare);
    return list;
  }
  const grid = document.getElementById('arch-grid');
  const countEl = document.getElementById('arch-count');
  const emptyEl = document.getElementById('arch-empty');
  const pagEl = document.getElementById('pagination');
  function paginate(list){
    const total = list.length;
    const pages = Math.max(1, Math.ceil(total/state.perPage));
    if (state.page > pages) state.page = pages;
    const start = (state.page-1)*state.perPage;
    return { slice: list.slice(start, start+state.perPage), pages, total, start };
  }
  function renderPagination(pages, total, start){
    if (pages <= 1) { pagEl.innerHTML = `<span class="info">${total} ${total===1?'asset':'assets'}</span>`; return; }
    const p = state.page;
    const set = new Set([1,2,pages-1,pages,p-1,p,p+1]);
    const sorted = Array.from(set).filter(n => n >=1 && n <= pages).sort((a,b)=>a-b);
    const out = [];
    out.push(`<button data-go="prev"${p===1?' disabled':''}>‹ Prev</button>`);
    let prev = 0;
    for (const n of sorted) {
      if (prev && n - prev > 1) out.push(`<span class="ellipsis">…</span>`);
      out.push(`<button data-go="${n}"${n===p?' class="active"':''}>${n}</button>`);
      prev = n;
    }
    out.push(`<button data-go="next"${p===pages?' disabled':''}>Next ›</button>`);
    out.push(`<span class="info">Page ${p} of ${pages} · ${start+1}–${Math.min(start+state.perPage, total)} of ${total}</span>`);
    pagEl.innerHTML = out.join('');
  }
  pagEl.addEventListener('click', e => {
    const b = e.target.closest('button[data-go]'); if (!b) return;
    const g = b.dataset.go;
    if (g === 'prev') state.page = Math.max(1, state.page-1);
    else if (g === 'next') state.page += 1;
    else state.page = parseInt(g,10);
    render(true);
  });
  // Latest filtered+sorted asset list (used by lightbox navigation).
  let lbList = [];
  let lbIdx = 0;
  function render(scroll=false){
    const list = filtered();
    lbList = list;
    const { slice, pages, total, start } = paginate(list);
    countEl.innerHTML = `Showing <b>${slice.length}</b> of ${total} assets${state.q?` matching "${esc(state.q)}"`:''}`;
    grid.innerHTML = slice.map((a, i) => cardHtml(a).replace('<article class="card"', `<article class="card" data-idx="${start+i}"`)).join('');
    emptyEl.hidden = total > 0;
    renderPagination(pages, total, start);
    if (scroll) document.getElementById('archive').scrollIntoView({ behavior:'smooth', block:'start' });
  }
  render();

  // === Lightbox with navigation (arrow keys, swipe, prev/next buttons) ===
  const lb = document.getElementById('lightbox');
  const lbI = document.getElementById('lb-inner');
  const lbC = document.getElementById('lb-close');
  const lbPrev = document.getElementById('lb-prev');
  const lbNext = document.getElementById('lb-next');
  const lbCounter = document.getElementById('lb-counter');

  function renderLightbox() {
    const a = lbList[lbIdx];
    if (!a) return;
    const local = a.l || '';
    const remote = a.u || '';
    const title = a.ti || '';
    const target = local || remote;
    if (!target) { lbI.innerHTML = `<div class="lb-meta">${esc(title)} — file not available; run <code>./scripts/sync.sh</code> or visit the source.</div>`; return; }
    const ext = target.split('?')[0].split('#')[0].split('.').pop().toLowerCase();
    const localHref = local ? './' + local : '';
    const meta = `<div class="lb-meta">${esc(title)}</div>`;
    let html;
    if (['jpg','jpeg','png','gif','webp','svg'].includes(ext)) {
      const fb = remote ? `onerror="this.onerror=null;this.src='${esc(remote)}';"` : '';
      html = `<img src="${esc(localHref || remote)}" alt="${esc(title)}" ${fb}>${meta}`;
    } else if (['mp4','webm','mov'].includes(ext)) {
      const srcs = [];
      if (localHref) srcs.push(`<source src="${esc(localHref)}" type="video/mp4">`);
      if (remote)    srcs.push(`<source src="${esc(remote)}" type="video/mp4">`);
      html = `<video controls autoplay playsinline>${srcs.join('')}</video>${meta}`;
    } else if (['mp3','wav','ogg','m4a'].includes(ext)) {
      html = `<audio controls autoplay src="${esc(localHref || remote)}"></audio>${meta}`;
    } else if (ext === 'pdf') {
      const src = localHref || remote;
      html = `<iframe src="${esc(src)}#view=FitH"></iframe><div class="lb-meta">${esc(title)} — <a href="${esc(src)}" target="_blank">open in new tab ↗</a></div>`;
    } else {
      window.open(localHref || remote, '_blank'); closeLb(); return;
    }
    lbI.innerHTML = html;
    if (lbCounter) lbCounter.textContent = (lbIdx + 1) + ' / ' + lbList.length;
    if (lbPrev) lbPrev.style.visibility = lbList.length > 1 ? 'visible' : 'hidden';
    if (lbNext) lbNext.style.visibility = lbList.length > 1 ? 'visible' : 'hidden';
  }
  function openAt(idx) {
    if (!lbList.length) return;
    lbIdx = (idx + lbList.length) % lbList.length;
    renderLightbox();
    lb.classList.add('open');
    lb.setAttribute('aria-hidden', 'false');
  }
  function navLb(delta) {
    if (!lbList.length) return;
    lbIdx = (lbIdx + delta + lbList.length) % lbList.length;
    renderLightbox();
  }
  function closeLb() {
    lb.classList.remove('open');
    lb.setAttribute('aria-hidden', 'true');
    lbI.innerHTML = '';
  }
  lbC.addEventListener('click', closeLb);
  if (lbPrev) lbPrev.addEventListener('click', e => { e.stopPropagation(); navLb(-1); });
  if (lbNext) lbNext.addEventListener('click', e => { e.stopPropagation(); navLb( 1); });
  lb.addEventListener('click', e => { if (e.target === lb) closeLb(); });
  document.addEventListener('keydown', e => {
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') closeLb();
    else if (e.key === 'ArrowRight') navLb(1);
    else if (e.key === 'ArrowLeft')  navLb(-1);
  });
  // Touch swipe
  let touchX = 0, touchY = 0, touchT = 0;
  lb.addEventListener('touchstart', e => {
    if (!e.touches.length) return;
    touchX = e.touches[0].clientX; touchY = e.touches[0].clientY; touchT = Date.now();
  }, { passive: true });
  lb.addEventListener('touchend', e => {
    if (!e.changedTouches.length) return;
    const dx = e.changedTouches[0].clientX - touchX;
    const dy = e.changedTouches[0].clientY - touchY;
    const dt = Date.now() - touchT;
    if (dt < 800 && Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
      navLb(dx < 0 ? 1 : -1);
    }
  }, { passive: true });

  grid.addEventListener('click', e => {
    const a = e.target.closest('a[data-action]');
    const card = e.target.closest('.card');
    if (a) {
      e.preventDefault();
      if (card && card.dataset.idx !== undefined) openAt(parseInt(card.dataset.idx, 10));
      return;
    }
    const m = e.target.closest('.card-media');
    if (m && card && card.dataset.idx !== undefined) {
      openAt(parseInt(card.dataset.idx, 10));
    }
  });
})();
</script>
</body>
</html>'''

_aaro_nav = make_nav('aaro', depth=1, internal_links=[
    ('Intro',    '#top',       'intro'),
    ('Headlines','#headlines', 'headlines'),
    ('Evidence', '#archive',   'archive'),
    ('About / FAQ', './details.html', 'faq'),
])
PAGE = PAGE.replace('__DATA__', asset_json)
PAGE = PAGE.replace('__VID_L__', str(stats['videos_local'])).replace('__VID_T__', str(stats['videos_total']))
PAGE = PAGE.replace('__PDF_L__', str(stats['pdfs_local'])).replace('__PDF_T__', str(stats['pdfs_total']))
PAGE = PAGE.replace('__IMG_L__', str(stats['imgs_local'])).replace('__IMG_T__', str(stats['imgs_total']))
PAGE = PAGE.replace('__AARO_NAV__', _aaro_nav)

# i18n + nav dropdown + lang picker + scroll-hide — injected before main <script>
_aaro_nav_js = f'''<script>
(function(){{
  var I18N={_I18N_JSON};
  var lang=localStorage.getItem('realufo_lang')||'en';
  if(!I18N[lang])lang='en';
  function applyLang(code){{lang=code;localStorage.setItem('realufo_lang',code);var t=I18N[code];document.querySelectorAll('[data-i18n]').forEach(function(el){{var k=el.getAttribute('data-i18n');if(t[k]!==undefined)el.textContent=t[k];}});var lb=document.getElementById('lang-btn');if(lb)lb.textContent=t.code||code.toUpperCase();}}
  var lp=document.getElementById('lang-picker'),lbtn=document.getElementById('lang-btn'),lm=document.getElementById('lang-menu');
  if(lbtn&&lp){{lbtn.addEventListener('click',function(e){{e.stopPropagation();lp.classList.toggle('open');lbtn.setAttribute('aria-expanded',lp.classList.contains('open')?'true':'false');}});if(lm)lm.addEventListener('click',function(e){{var b=e.target.closest('button[data-lang]');if(!b)return;applyLang(b.dataset.lang);lp.classList.remove('open');lbtn.setAttribute('aria-expanded','false');}});}}
  var mw=document.getElementById('nav-more-wrap'),mb=document.getElementById('nav-more-btn');
  if(mw&&mb){{mb.addEventListener('click',function(e){{e.stopPropagation();mw.classList.toggle('open');mb.setAttribute('aria-expanded',mw.classList.contains('open')?'true':'false');}});}}
  document.addEventListener('click',function(){{if(lp){{lp.classList.remove('open');if(lbtn)lbtn.setAttribute('aria-expanded','false');}}if(mw){{mw.classList.remove('open');if(mb)mb.setAttribute('aria-expanded','false');}}}});
  var bar=document.querySelector('.arch-controls-bar');
  if(bar){{var lastY=window.scrollY;window.addEventListener('scroll',function(){{if(window.innerWidth>=720){{bar.classList.remove('bar-hidden');return;}}var y=window.scrollY;if(y<80)bar.classList.remove('bar-hidden');else if(y>lastY+4)bar.classList.add('bar-hidden');else if(y<lastY-4)bar.classList.remove('bar-hidden');lastY=y;}},{{passive:true}});}}
  applyLang(lang);
}})();
</script>'''
PAGE = PAGE.replace('__AARO_NAV_JS__', _aaro_nav_js)

open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(PAGE)
print(f'wrote index.html ({len(PAGE):,} bytes)')
print(f'  videos local: {stats["videos_local"]}/{stats["videos_total"]}')
print(f'  pdfs local: {stats["pdfs_local"]}/{stats["pdfs_total"]}')
print(f'  imgs local: {stats["imgs_local"]}/{stats["imgs_total"]}')
