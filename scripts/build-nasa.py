#!/usr/bin/env python3
"""Build nasa/index.html — NASA UAP Independent Study mirror.

Smaller than war.gov/AARO: a single curated asset list (4 PDFs +
3 YouTube videos + 2 images). Tone color = NASA red (#fc3d21).
"""
import json, os, subprocess, sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from _release_manifest import apply_manifest
from _site_template import make_nav, LIGHTBOX_HTML, LIGHTBOX_CSS, LIGHTBOX_JS, _I18N_JSON

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, 'nasa')


def git_tracked(rel_dir):
    try:
        out = subprocess.run(
            ['git', '-C', REPO, 'ls-files', f'nasa/{rel_dir}/'],
            capture_output=True, text=True, check=True,
        ).stdout
        prefix = f'nasa/{rel_dir}/'
        return {ln[len(prefix):] for ln in out.splitlines() if ln.startswith(prefix)}
    except (subprocess.CalledProcessError, FileNotFoundError):
        p = os.path.join(ROOT, rel_dir)
        return set(os.listdir(p)) if os.path.isdir(p) else set()


tracked_pdfs = git_tracked('pdfs')
tracked_imgs = git_tracked('assets/images')

def L(rel_dir, fname):
    """Local path if file is in git, else empty string."""
    base = rel_dir.split('/')[-1] if rel_dir.startswith('assets') else rel_dir
    pool = tracked_imgs if rel_dir == 'assets/images' else tracked_pdfs
    return f'{rel_dir}/{fname}' if fname in pool else ''

import urllib.parse as _up
PDF_RELEASE_BASE = 'https://github.com/hectorchanht/war-gov-ufo-release/releases/download/pdfs-v1/'
def R(fname): return PDF_RELEASE_BASE + _up.quote(fname)


ASSETS = [
    # ----- PDFs -----
    {
        't': 'PDF',
        'ti': 'NASA UAP Independent Study Team — Final Report',
        'de': 'The 36-page final report of the NASA UAP Independent Study Team (Sep 2023). Recommends a unified data-collection strategy, expanded use of NASA Earth-observing assets, and AI/ML for anomaly detection. Led by astrophysicist David Spergel.',
        'ag': 'NASA',
        'cat': 'Study Report',
        'date': 'Sep 2023',
        'l': L('pdfs', 'uap-independent-study-team-final-report.pdf'),
        'u': R('uap-independent-study-team-final-report.pdf'),
        's': 'https://science.nasa.gov/wp-content/uploads/2023/09/uap-independent-study-team-final-report.pdf',
    },
    {
        't': 'PDF',
        'ti': 'UAP Independent Study Team — Terms of Reference',
        'de': 'Signed charter establishing the UAP Independent Study Team. Defines scope, deliverables, and the 9-month study period (June 2022 → Mar 2023).',
        'ag': 'NASA',
        'cat': 'Charter',
        'date': 'Apr 2023',
        'l': L('pdfs', 'UAPISTTermsofReference_Signed.pdf'),
        'u': R('UAPISTTermsofReference_Signed.pdf'),
        's': 'https://science.nasa.gov/wp-content/uploads/2023/04/UAPISTTermsofReference_Signed.pdf',
    },
    {
        't': 'PDF',
        'ti': 'Public Meeting Agenda — May 31, 2023',
        'de': 'Agenda for the NASA UAP Independent Study Team public meeting held May 31 2023. Lists every team member presentation and topic.',
        'ag': 'NASA',
        'cat': 'Public Meeting',
        'date': 'May 2023',
        'l': L('pdfs', 'public-meeting-agenda-tagged.pdf'),
        'u': R('public-meeting-agenda-tagged.pdf'),
        's': 'https://science.nasa.gov/wp-content/uploads/2024/01/public-meeting-agenda-tagged.pdf',
    },
    {
        't': 'PDF',
        'ti': 'Federal Register Notice — UAP Public Meeting',
        'de': 'Official Federal Register notice announcing the NASA UAP Independent Study Team public meeting and inviting public participation.',
        'ag': 'NASA',
        'cat': 'Public Meeting',
        'date': 'May 2023',
        'l': L('pdfs', 'frn-uapist-public-meeting-tagged.pdf'),
        'u': R('frn-uapist-public-meeting-tagged.pdf'),
        's': 'https://science.nasa.gov/wp-content/uploads/2024/01/frn-uapist-public-meeting-tagged.pdf',
    },
    # ----- YouTube videos (iframe embed only — YouTube doesn't expose mp4) -----
    {
        't': 'VID',
        'ti': 'Media Briefing: UAP Independent Study Report (Sep 14, 2023)',
        'de': 'NASA holds a media briefing to discuss the findings of the UAP Independent Study Team Report. Administrator Bill Nelson opens; study lead David Spergel presents findings.',
        'ag': 'NASA',
        'cat': 'Public Briefing',
        'date': 'Sep 14, 2023',
        'embed': 'https://www.youtube.com/embed/eoY2sGo7ZiY',
        'u': 'https://youtu.be/eoY2sGo7ZiY',
    },
    {
        't': 'VID',
        'ti': 'NASA UAP Telecon — Pre-meeting Briefing',
        'de': 'Pre-meeting press telecon held ahead of the May 31 2023 UAP Independent Study Team public meeting.',
        'ag': 'NASA',
        'cat': 'Public Briefing',
        'date': '2023',
        'embed': 'https://www.youtube.com/embed/C3uXUfgSadU',
        'u': 'https://www.youtube.com/watch?v=C3uXUfgSadU',
    },
    {
        't': 'VID',
        'ti': 'UAP Independent Study Team Public Meeting (May 31, 2023)',
        'de': 'Full 4-hour public meeting of the NASA UAP Independent Study Team. Each panellist presents their analysis tasking; Q&A from press and public.',
        'ag': 'NASA',
        'cat': 'Public Meeting',
        'date': 'May 31, 2023',
        'embed': 'https://www.youtube.com/embed/bQo08JRY0iM',
        'u': 'https://www.youtube.com/watch?v=bQo08JRY0iM',
    },
    # ----- Images -----
    {
        't': 'IMG',
        'ti': 'UAP Study Team — Public Meeting Group Photo',
        'de': 'Group photo of the NASA UAP Independent Study Team at the May 31 2023 public meeting at NASA HQ.',
        'ag': 'NASA',
        'cat': 'Imagery',
        'date': 'May 31, 2023',
        'l': L('assets/images', 'uap-meeting-2023.jpeg'),
        'u': 'https://science.nasa.gov/wp-content/uploads/2022/06/uap-meeting-2023-e1692299097471.jpeg',
    },
    {
        't': 'IMG',
        'ti': 'UAP Final Report — Cover',
        'de': 'Cover image of the UAP Independent Study Team final report (Sep 2023). Northern hemisphere of earth, deep black background.',
        'ag': 'NASA',
        'cat': 'Imagery',
        'date': 'Sep 2023',
        'l': L('assets/images', 'uap-report-cover.png'),
        'u': 'https://science.nasa.gov/wp-content/uploads/2023/09/uap-report-cover-9-2023.png',
    },
]

# Merge any additional records discovered by scrape-nasa.py
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
                'ag': _r.get('agency', 'NASA'),
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
    'pdf_total': sum(1 for a in ASSETS if a['t'] == 'PDF'),
    'vid_total': sum(1 for a in ASSETS if a['t'] == 'VID'),
    'img_total': sum(1 for a in ASSETS if a['t'] == 'IMG'),
}

# Carousel: prefer images first
carousel = []
for a in ASSETS:
    if a['t'] == 'IMG' and a.get('l'):
        carousel.append({
            'local': a['l'],
            'url': a.get('u', ''),
            'title': a['ti'],
            'kind': 'image',
        })
        if len(carousel) >= 4:
            break

data_json = json.dumps({'assets': ASSETS, 'carousel': carousel, 'stats': stats}, ensure_ascii=False).replace('</script', '<\\/script')

PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NASA UAP Independent Study — Offline Mirror</title>
<meta name="description" content="Offline mirror of NASA's UAP Independent Study Team final report, briefings, and public meeting record.">
<link rel="canonical" href="https://realufo.org/nasa/">
<meta property="og:title" content="NASA UAP Independent Study | realufo.org">
<meta property="og:description" content="NASA's UAP Independent Study Team final report (Sep 2023). 4 PDFs + 3 YouTube briefings + study-team imagery. Led by Dr David Spergel.">
<meta property="og:image" content="https://realufo.org/nasa/assets/images/uap-report-cover.png">
<meta property="og:url" content="https://realufo.org/nasa/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="realufo.org">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="NASA UAP Independent Study | realufo.org">
<meta name="twitter:description" content="NASA's UAP Independent Study Team final report (Sep 2023). 4 PDFs + 3 YouTube briefings + study-team imagery. Led by Dr David Spergel.">
<meta name="twitter:image" content="https://realufo.org/nasa/assets/images/uap-report-cover.png">
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
  --stamp:#b91c1c; --caution:#fc3d21; --warm:#d4a017; --classified:#c9362c;
  --serif:"Source Serif 4","Iowan Old Style",Georgia,serif;
  --mono:"JetBrains Mono","SF Mono",Consolas,monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; scroll-padding-top: 70px; }
body {
  background: var(--bg); color: var(--ink);
  font-family: var(--serif); font-size: 16px; line-height: 1.65;
  background-image:
    radial-gradient(ellipse at 20% 0%, rgba(252,61,33,0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(212,160,23,0.03) 0%, transparent 50%);
  background-attachment: fixed;
}
.scanlines { position: fixed; inset: 0; background: repeating-linear-gradient(to bottom, transparent 0, transparent 2px, rgba(255,255,255,0.012) 3px, transparent 4px); pointer-events: none; z-index: 50; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 32px; position: relative; z-index: 2; }

.gov-banner {
  background: #1a1a1f; border-bottom: 1px solid var(--rule);
  font-family: var(--mono); font-size: 11px; color: var(--ink-dim); letter-spacing: 0.04em;
}
.gov-banner .container { display: flex; align-items: center; gap: 16px; padding: 10px 32px; flex-wrap: wrap; }
.gov-banner a { color: var(--caution); text-decoration: none; }
.gov-banner a:hover { text-decoration: underline; }
.gov-banner .nav-mirrors { margin-left: auto; display: flex; gap: 14px; flex-wrap: wrap; }
.flag-dot { width: 10px; height: 10px; border-radius: 50%;
  background: linear-gradient(45deg,#b91c1c 0,#b91c1c 50%,#1e3a8a 50%,#1e3a8a 100%); flex-shrink: 0; }

.header-wrap {
  position: sticky; top: 0; z-index: 40;
  background: rgba(10,10,12,0.95);
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--rule);
}
header { padding: 16px 0; }
header .container { display: flex; align-items: center; gap: 24px; flex-wrap: wrap; }
.brand { display: flex; align-items: center; gap: 14px; text-decoration: none; color: var(--ink); flex-shrink: 0; }
.seal {
  width: 44px; height: 44px;
  background: radial-gradient(circle at 50% 50%, #fc3d21, #a01818 60%, #400606);
  border-radius: 50%; display: grid; place-items: center;
  box-shadow: 0 0 0 2px var(--ink), 0 0 0 4px var(--bg), 0 0 0 5px var(--ink-faint);
  font-family: var(--mono); font-weight: 700; font-size: 11px; color: var(--ink);
}
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

.hero { padding: 56px 0 40px; border-bottom: 1px solid var(--rule); position: relative; }
.coords {
  font-family: var(--mono); font-size: 12px; color: var(--caution);
  letter-spacing: 0.12em; margin-bottom: 18px; display: flex; align-items: center; gap: 12px;
}
.coords::before { content: "◉"; color: var(--stamp); }
.coords::after { content: ""; flex: 1; height: 1px; background: linear-gradient(to right, var(--caution), transparent); margin-left: 12px; max-width: 200px; }
h1.hero-title {
  font-family: var(--serif); font-weight: 700;
  font-size: clamp(28px,4.5vw,52px); line-height: 1.05;
  letter-spacing: -0.02em; max-width: 24ch; margin-bottom: 22px;
}
h1.hero-title em { color: var(--caution); font-style: italic; }
.hero-sub { max-width: 65ch; color: var(--ink-dim); font-size: 17px; line-height: 1.65; margin-bottom: 28px; }
.hero-sub a { color: var(--caution); }

/* CAROUSEL */
.hero-carousel {
  position: relative; border: 1px solid var(--rule-strong); background: var(--bg-2);
  aspect-ratio: 16/9; overflow: hidden; max-width: 960px; margin-top: 12px;
}
.carousel-slide { position: absolute; inset: 0; opacity: 0; transition: opacity .8s ease; pointer-events: none; }
.carousel-slide.active { opacity: 1; pointer-events: auto; }
.carousel-slide img, .carousel-slide video { width: 100%; height: 100%; object-fit: cover; display: block; filter: contrast(1.04) saturate(0.9); }
.carousel-slide::after { content: ""; position: absolute; inset: 0; background: linear-gradient(to top, rgba(0,0,0,0.78), transparent 50%); pointer-events: none; }
.carousel-btn {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 46px; height: 46px; background: rgba(0,0,0,0.6); border: 1px solid var(--rule-strong); color: var(--ink);
  font-family: var(--serif); font-size: 28px; cursor: pointer; z-index: 3;
}
.carousel-btn:hover { background: rgba(0,0,0,0.9); border-color: var(--caution); color: var(--caution); }
.carousel-btn.prev { left: 14px; } .carousel-btn.next { right: 14px; }
.carousel-dots { position: absolute; bottom: 56px; left: 50%; transform: translateX(-50%); display: flex; gap: 6px; z-index: 3; }
.carousel-dots button { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.4); border: 0; cursor: pointer; padding: 0; transition: transform .15s, background .15s; }
.carousel-dots button.active { background: var(--caution); transform: scale(1.4); }
.carousel-caption {
  position: absolute; bottom: 16px; left: 0; right: 0; text-align: center;
  font-family: var(--mono); font-size: 11px; color: var(--ink); letter-spacing: 0.06em;
  padding: 0 70px; z-index: 2; text-shadow: 0 1px 4px rgba(0,0,0,0.9);
}
.carousel-caption .badge { color: var(--caution); margin-right: 8px; font-weight: 700; }

/* HEADLINES */
.headlines { padding: 40px 0; border-bottom: 1px solid var(--rule); }
.head-grid { display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
.head-card {
  padding: 20px 22px; background: var(--panel);
  border: 1px solid var(--rule); border-left: 3px solid var(--caution);
}
.head-card .h-label { font-family: var(--mono); font-size: 10px; color: var(--caution); letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 10px; }
.head-card .h-text { font-size: 17px; line-height: 1.4; color: var(--ink); }
.head-card .h-num { font-family: var(--mono); font-size: 28px; color: var(--ink); font-weight: 600; display: block; margin-bottom: 4px; }

section { padding: 56px 0; border-bottom: 1px solid var(--rule); position: relative; }
.section-label {
  font-family: var(--mono); font-size: 11px; letter-spacing: 0.24em;
  text-transform: uppercase; color: var(--ink-faint);
  display: flex; align-items: center; gap: 16px; margin-bottom: 18px;
}
.section-label::before { content: ""; width: 28px; height: 1px; background: var(--ink-faint); }
h2 { font-family: var(--serif); font-size: clamp(24px,3vw,36px); font-weight: 700; letter-spacing: -0.015em; margin-bottom: 20px; max-width: 28ch; }
.lede { max-width: 70ch; color: var(--ink); font-size: 17px; }
.lede a { color: var(--caution); }

/* ARCHIVE */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1px; background: var(--rule); border: 1px solid var(--rule); margin: 22px 0 28px; }
.stat { background: var(--panel); padding: 16px 20px; font-family: var(--mono); }
.stat b { display: block; font-size: 26px; color: var(--ink); font-weight: 500; }
.stat small { display: block; font-size: 10px; color: var(--ink-faint); letter-spacing: 0.16em; text-transform: uppercase; margin-top: 6px; }

.arch-controls-bar {
  position: sticky; top: 64px; z-index: 30;
  background: rgba(10,10,12,0.95); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule);
  margin: 24px -32px 0; padding: 14px 32px;
  display: flex; gap: 14px; align-items: center; flex-wrap: wrap;
}
.tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.tab { font-family: var(--mono); font-size: 11px; padding: 8px 14px; border: 1px solid var(--rule-strong); background: var(--panel); color: var(--ink-dim); cursor: pointer; letter-spacing: 0.08em; text-transform: uppercase; }
.tab:hover { color: var(--ink); border-color: var(--ink-faint); }
.tab.active { background: var(--caution); color: var(--bg); border-color: var(--caution); font-weight: 700; }
.tab .count { opacity: 0.6; margin-left: 6px; font-size: 10px; }
.search-wrap {
  margin-left: auto; display: flex; align-items: center; gap: 8px;
  background: var(--panel); border: 1px solid var(--rule-strong); padding: 6px 12px; min-width: 220px;
}
.search-wrap::before { content: "⌕"; color: var(--ink-faint); font-family: var(--mono); }
.search-wrap input { background: transparent; border: 0; outline: 0; color: var(--ink); font-family: var(--mono); font-size: 12px; flex: 1; }
.search-wrap input::placeholder { color: var(--ink-faint); }

.arch-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 18px; padding: 18px 0 24px; }
.card { background: var(--panel); border: 1px solid var(--rule); display: flex; flex-direction: column; overflow: hidden; transition: border-color .2s, transform .2s; }
.card:hover { border-color: var(--caution); transform: translateY(-2px); }
.card-media { aspect-ratio: 16/9; background: var(--bg-2); position: relative; overflow: hidden; display: grid; place-items: center; border-bottom: 1px solid var(--rule); cursor: pointer; }
.card-media img, .card-media iframe { width: 100%; height: 100%; object-fit: cover; display: block; border: 0; }
.pdf-glyph { font-family: var(--mono); font-size: 13px; color: var(--ink-faint); background: repeating-linear-gradient(45deg,#1a1a1f,#1a1a1f 8px,#15151a 8px,#15151a 16px); width: 100%; height: 100%; display: grid; place-items: center; text-align: center; padding: 16px; }
.pdf-glyph .ico { font-size: 26px; color: var(--caution); margin-bottom: 6px; border: 2px solid var(--caution); padding: 4px 10px; font-weight: 700; letter-spacing: 0.04em; display: inline-block; }
.video-glyph { background: linear-gradient(135deg, rgba(252,61,33,0.12), rgba(212,160,23,0.04)); }
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

/* LIGHTBOX — injected from _site_template.LIGHTBOX_CSS at build time */
__LIGHTBOX_CSS__

/* FOOTER */
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
      <div class="seal">NASA</div>
      <div class="brand-text">
        <span class="super">National Aeronautics and Space Administration</span>
        <span class="name">UAP Independent Study</span>
      </div>
    </a>
    <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
    __SITE_NAV__
  </div>
</header>
</div>

<div class="hero" id="top">
  <div class="container">
    <div class="coords">38°53′00″N, 77°00′59″W · NASA HQ · MARY W. JACKSON BUILDING, WASHINGTON, D.C.</div>
    <h1 class="hero-title">NASA UAP <em>Independent</em> Study</h1>
    <p class="hero-sub">
      In June 2022 NASA commissioned a 16-member independent study team led by astrophysicist
      Dr. David Spergel to examine unidentified anomalous phenomena from a strictly scientific
      perspective. The team delivered its <a href="./pdfs/uap-independent-study-team-final-report.pdf">final report</a>
      on September 14, 2023 — recommending a unified data pipeline, expanded use of NASA Earth
      observation assets, and the application of AI/ML to anomaly detection. Source: <a href="https://science.nasa.gov/uap/" target="_blank" rel="noopener">science.nasa.gov/uap</a>.
    </p>

    <div class="hero-carousel" id="hero-carousel" aria-label="Featured NASA UAP imagery">
      <div id="carousel-track"></div>
      <button class="carousel-btn prev" id="carousel-prev" aria-label="Previous">‹</button>
      <button class="carousel-btn next" id="carousel-next" aria-label="Next">›</button>
      <div class="carousel-dots" id="carousel-dots"></div>
      <div class="carousel-caption" id="carousel-caption"></div>
    </div>
  </div>
</div>

<section id="headlines" class="headlines">
  <div class="container">
    <div class="section-label">§ Headlines · The study, distilled</div>
    <div class="head-grid">
      <div class="head-card"><div class="h-label">Commissioned</div><span class="h-num">2022</span><div class="h-text">Study team announced June 9, 2022.</div></div>
      <div class="head-card"><div class="h-label">Members</div><span class="h-num">16</span><div class="h-text">Scientists, astronauts, intelligence and data experts.</div></div>
      <div class="head-card"><div class="h-label">Lead</div><div class="h-text">Dr. David Spergel — President, Simons Foundation. Princeton astrophysicist.</div></div>
      <div class="head-card"><div class="h-label">Final report</div><div class="h-text">36 pages · published Sep 14, 2023 · publicly downloadable.</div></div>
      <div class="head-card"><div class="h-label">Public meeting</div><div class="h-text">May 31, 2023 — full 4-hour deliberation streamed live.</div></div>
      <div class="head-card"><div class="h-label">Stance</div><div class="h-text"><em>No conclusive evidence</em> of extraterrestrial origin; data is the path forward.</div></div>
    </div>
  </div>
</section>

<section id="archive">
  <div class="container">
    <div class="section-label">§ Evidence · Reports, briefings, public meeting</div>
    <h2>Every report and presentation the Independent Study Team produced.</h2>
    <p class="lede">
      Four PDFs (final report, charter, public meeting agenda, federal register notice) and three
      public video sessions — all served from this mirror where possible, otherwise embedded
      directly from YouTube.
    </p>

    <div class="stats-grid" id="arch-stats"></div>

    <div class="arch-controls-bar">
      <div class="tabs" id="arch-tabs"></div>
      <div class="search-wrap">
        <input id="arch-search" type="search" placeholder="Search title, category, description…" autocomplete="off">
      </div>
    </div>

    <div class="arch-grid" id="arch-grid"></div>
    <div class="empty" id="arch-empty" hidden>No items match.</div>
  </div>
</section>

<footer>
  <div class="container">
    <div>
      <h4>NASA Mirror</h4>
      <p style="color: var(--ink-dim); font-family: var(--serif); margin-bottom: 14px;">
        Offline archival mirror of the NASA UAP Independent Study materials. Federal U.S.
        government works are public domain (17 U.S.C. § 105).
      </p>
      <p style="color: var(--ink-faint); font-size: 10px; letter-spacing: 0.1em;">Source: science.nasa.gov/uap · YouTube · Sep 2023.</p>
    </div>
    <div>
      <h4>Related Mirrors</h4>
      <ul>
        <li><a href="../index.html">war.gov / UFO Release 01</a></li>
        <li><a href="../aaro/index.html">AARO — DoW</a></li>
        <li><a href="../nara/index.html">NARA — US Archives</a></li>
      </ul>
    </div>
    <div>
      <h4>Source</h4>
      <ul>
        <li><a href="https://science.nasa.gov/uap/" target="_blank" rel="noopener">science.nasa.gov/uap ↗</a></li>
        <li><a href="https://science.nasa.gov/uap/faqs/" target="_blank" rel="noopener">UAP FAQs ↗</a></li>
      </ul>
    </div>
    <div class="colophon">
      <span>Offline mirror · For research and reference</span>
      <span>Built from public-domain NASA source</span>
    </div>
  </div>
</footer>

<div class="lightbox" id="lightbox" aria-hidden="true">
  <button class="lb-rotate" id="lb-rotate" aria-label="Rotate view" title="Rotate">⟳</button>
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
  const CAR = D.carousel;
  const STATS = D.stats;
  function esc(s){return (s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

  // Stats
  const statsEl = document.getElementById('arch-stats');
  statsEl.innerHTML = [
    ['Total', STATS.total],
    ['Local', STATS.local_total],
    ['Documents', STATS.pdf_total],
    ['Videos', STATS.vid_total],
    ['Images', STATS.img_total],
  ].map(([k,v]) => `<div class="stat"><b>${v}</b><small>${k}</small></div>`).join('');

  // Carousel
  const cTrack = document.getElementById('carousel-track');
  const cDots = document.getElementById('carousel-dots');
  const cCap = document.getElementById('carousel-caption');
  if (CAR.length) {
    CAR.forEach((s, i) => {
      const slide = document.createElement('div');
      slide.className = 'carousel-slide' + (i === 0 ? ' active' : '');
      const fb = s.url ? `onerror="this.onerror=null;this.src='${esc(s.url)}';"` : '';
      slide.innerHTML = `<img src="./${s.local}" alt="${esc(s.title)}" ${fb}>`;
      cTrack.appendChild(slide);
      const dot = document.createElement('button');
      dot.type = 'button';
      if (i === 0) dot.classList.add('active');
      dot.addEventListener('click', () => goTo(i));
      cDots.appendChild(dot);
    });
    cCap.innerHTML = `<span class="badge">NASA</span>${esc(CAR[0].title)}`;
    let cIdx = 0, timer;
    function goTo(i){
      const slides = cTrack.children, dots = cDots.children;
      slides[cIdx].classList.remove('active'); dots[cIdx].classList.remove('active');
      cIdx = (i + slides.length) % slides.length;
      slides[cIdx].classList.add('active'); dots[cIdx].classList.add('active');
      cCap.innerHTML = `<span class="badge">NASA</span>${esc(CAR[cIdx].title)}`;
    }
    document.getElementById('carousel-prev').addEventListener('click', () => { goTo(cIdx-1); restart(); });
    document.getElementById('carousel-next').addEventListener('click', () => { goTo(cIdx+1); restart(); });
    function start(){ timer = setInterval(() => goTo(cIdx+1), 6500); }
    function restart(){ clearInterval(timer); start(); }
    start();
    const heroEl = document.getElementById('hero-carousel');
    heroEl.addEventListener('mouseenter', () => clearInterval(timer));
    heroEl.addEventListener('mouseleave', restart);
  } else {
    document.getElementById('hero-carousel').style.display = 'none';
  }

  // Tabs
  const TABS = [
    {key:'ALL', label:'All'},
    {key:'PDF', label:'Documents'},
    {key:'VID', label:'Videos'},
    {key:'IMG', label:'Images'},
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

  function mediaFor(a) {
    if (a.t === 'IMG' && a.l) {
      const fb = a.u ? `onerror="this.onerror=null;this.src='${esc(a.u)}';"` : '';
      return `<img loading="lazy" src="./${a.l}" alt="${esc(a.ti)}" ${fb}>`;
    }
    if (a.t === 'VID' && a.embed) {
      // Use a poster glyph in the card; iframe loads only when opened.
      return `<div class="pdf-glyph video-glyph"><span class="ico">▶</span><span>YouTube · ${esc(a.cat||'')}</span></div>`;
    }
    return `<div class="pdf-glyph"><span class="ico">PDF</span><span>${esc(a.ag||'')}</span></div>`;
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
    const verb = a.t==='PDF'?'Open PDF': a.embed?'▶ Play': a.t==='IMG'?'View':'Open';
    if (a.l || a.u || a.embed) {
      out.push(`<a href="#" data-action="open" data-title="${esc(a.ti)}">${verb}</a>`);
      const dl = a.l ? './' + a.l : a.u;
      if (dl && !a.embed) out.push(`<a href="${esc(dl)}" ${a.l?'download':'target="_blank" rel="noopener"'}>Download</a>`);
    }
    const src = a.s || a.u;
    if (src) out.push(`<a class="warn" href="${esc(src)}" target="_blank" rel="noopener">Source ↗</a>`);
    return `<div class="card-actions">${out.join('')}</div>`;
  }
  function cardHtml(a, gidx) {
    const localBadge = a.l ? '<span class="badge local">LOCAL</span>' : '<span class="badge source">SOURCE</span>';
    return `<article class="card" data-idx="${gidx}">
      <div class="card-media">
        ${mediaFor(a)}
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

  /* Lightbox lifecycle delegated to LIGHTBOX_JS (window._lb). It already
     handles IMG/VID/PDF/iframe + arrow keys + swipe + ESC + rotate. We
     just feed it the filtered list on every render and trigger open. */
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
    const list = filtered();
    if (window._lb) window._lb.setList(list);
    grid.innerHTML = list.map((a, i) => cardHtml(a, i)).join('');
    emptyEl.hidden = list.length > 0;
  }
  render();

  grid.addEventListener('click', e => {
    const action = e.target.closest('a[data-action]');
    const card = e.target.closest('.card');
    if (action) e.preventDefault();
    if (card && card.dataset.idx !== undefined && (action || e.target.closest('.card-media'))) {
      if (window._lb) window._lb.open(parseInt(card.dataset.idx, 10));
    }
  });
})();
</script>
</body>
</html>
'''
_site_nav = make_nav('nasa', depth=1, internal_links=[('Intro', '#top', 'intro'), ('Headlines', '#headlines', 'headlines'), ('Archive', '#archive', 'archive')])
_nav_js = '''<script>
(function(){var I18N=__I18N__;var lang=localStorage.getItem('realufo_lang')||'en';if(!I18N[lang])lang='en';function applyLang(c){lang=c;localStorage.setItem('realufo_lang',c);var t=I18N[c];document.querySelectorAll('[data-i18n]').forEach(function(el){var k=el.getAttribute('data-i18n');if(t[k]!==undefined)el.textContent=t[k];});var lb=document.getElementById('lang-btn');if(lb)lb.textContent=t.code||c.toUpperCase();};var lp=document.getElementById('lang-picker'),lbtn=document.getElementById('lang-btn'),lm=document.getElementById('lang-menu');if(lbtn&&lp){lbtn.addEventListener('click',function(e){e.stopPropagation();lp.classList.toggle('open');});if(lm)lm.addEventListener('click',function(e){var b=e.target.closest('button[data-lang]');if(!b)return;applyLang(b.dataset.lang);lp.classList.remove('open');});}var nd=Array.from(document.querySelectorAll('.has-dropdown > details'));nd.forEach(function(d){d.addEventListener('toggle',function(){if(!d.open)return;nd.forEach(function(o){if(o!==d)o.open=false;});});});document.addEventListener('click',function(e){if(lp)lp.classList.remove('open');if(!e.target.closest('.has-dropdown')){nd.forEach(function(d){d.open=false;});}});document.addEventListener('keydown',function(e){if(e.key==='Escape')nd.forEach(function(d){d.open=false;});});var bar=document.querySelector('.arch-controls-bar');if(bar){var lY=window.scrollY;window.addEventListener('scroll',function(){if(window.innerWidth>=720){bar.classList.remove('bar-hidden');return;}var y=window.scrollY;if(y<80)bar.classList.remove('bar-hidden');else if(y>lY+4)bar.classList.add('bar-hidden');else if(y<lY-4)bar.classList.remove('bar-hidden');lY=y;},{passive:true});}applyLang(lang);})();
</script>'''.replace('__I18N__', _I18N_JSON)
PAGE = PAGE.replace('__LIGHTBOX_CSS__', LIGHTBOX_CSS.strip())
PAGE = PAGE.replace('__DATA__', data_json)
PAGE = PAGE.replace('__SITE_NAV__', _site_nav)
PAGE = PAGE.replace('__SITE_NAV_JS__', _nav_js)
# Inject LIGHTBOX_JS just before </body> so window._lb exists by click time.
PAGE = PAGE.replace('</body>', f'<script>{LIGHTBOX_JS.strip()}</script>\n</body>', 1)
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(PAGE)
print(f'wrote {ROOT}/index.html ({len(PAGE):,} bytes)')
print(f'  total assets: {stats["total"]}, local: {stats["local_total"]}')
