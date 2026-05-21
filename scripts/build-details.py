#!/usr/bin/env python3
"""Build aaro-mirror/details.html — long-form content for every mirrored page.

Reads:  aaro-mirror/.cache/parsed.json
Writes: aaro-mirror/details.html
"""
import os, re, json, html, urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, 'aaro-mirror')
CACHE = os.path.join(ROOT, '.cache')
parsed = json.load(open(os.path.join(CACHE, 'parsed.json')))

ORDER = ['mission-vision','leaders','official-uap-imagery','uap-case-resolution-reports',
         'uap-reporting-trends','uap-records','congressional-press-products','resources',
         'efoia-reading-room','submit-a-report','faq']
LABELS = {
    'mission-vision':'Mission / Vision',
    'leaders':'Leaders',
    'official-uap-imagery':'Official UAP Imagery',
    'uap-case-resolution-reports':'Case Resolution Reports',
    'uap-reporting-trends':'UAP Reporting Trends',
    'uap-records':'UAP Records',
    'congressional-press-products':'Congressional / Press',
    'resources':'Resources',
    'efoia-reading-room':'EFOIA Reading Room',
    'submit-a-report':'Submit A Report',
    'faq':'FAQ',
}

# Local inventories
local_pdfs = set(os.listdir(os.path.join(ROOT,'pdfs'))) if os.path.isdir(os.path.join(ROOT,'pdfs')) else set()
local_imgs = set(os.listdir(os.path.join(ROOT,'assets/images'))) if os.path.isdir(os.path.join(ROOT,'assets/images')) else set()
local_vids = set(os.listdir(os.path.join(ROOT,'videos'))) if os.path.isdir(os.path.join(ROOT,'videos')) else set()

def basename(url):
    return urllib.parse.unquote(url.rsplit('/',1)[-1].split('?')[0])
def local_for(url, kind):
    bn = basename(url)
    if kind == 'pdf' and bn in local_pdfs: return 'pdfs/' + bn
    if kind == 'img' and bn in local_imgs: return 'assets/images/' + bn
    return ''

def text_to_html(txt):
    if not txt: return ''
    BOILER_PREFIXES = (
        'Official websites use', 'A .mil website belongs', 'Secure .mil websites',
        'A lock (lock', 'Share sensitive', 'Toggle navigation', "Here's how you know",
        'Skip to main content', 'An official website',
    )
    BOILER_LINES = {'lock','Search','Quick Links','SHARE','PRINT','Download'}
    lines = [l.strip() for l in txt.split('\n')]
    parts = []
    for l in lines:
        if not l:
            if parts and parts[-1] != '': parts.append('')
            continue
        if any(l.startswith(p) for p in BOILER_PREFIXES): continue
        if l in BOILER_LINES: continue
        parts.append(l)
    out = []
    para = []
    for l in parts:
        if not l:
            if para:
                out.append('<p>' + html.escape(' '.join(para)) + '</p>')
                para = []
        else:
            para.append(l)
    if para: out.append('<p>' + html.escape(' '.join(para)) + '</p>')
    return '\n'.join(out)

def render_links(links, max_n=60):
    out = []
    seen = set()
    for L in links:
        href = L.get('href','')
        label = L.get('label','').strip()
        if not href or not label: continue
        if href in seen: continue
        seen.add(href)
        if not href.startswith('http'):
            href = urllib.parse.urljoin('https://www.aaro.mil/', href)
        if href.startswith('https://www.aaro.mil/') and href.lower().endswith('.pdf'):
            local = local_for(href,'pdf')
            if local:
                out.append(f'<li><a href="./{local}" target="_blank">{html.escape(label)} <span class="lk-meta">[PDF · local]</span></a></li>')
            else:
                out.append(f'<li><a href="{html.escape(href)}" target="_blank" rel="noopener">{html.escape(label)} <span class="lk-meta">[PDF · source]</span></a></li>')
        else:
            cls = '' if 'aaro.mil' in href else ' class="ext"'
            arrow = '' if 'aaro.mil' in href else ' ↗'
            out.append(f'<li><a href="{html.escape(href)}" target="_blank" rel="noopener"{cls}>{html.escape(label)}{arrow}</a></li>')
        if len(out) >= max_n: break
    return '<ul class="lk-list">\n' + '\n'.join(out) + '\n</ul>' if out else ''

def render_images(images):
    out = []
    for I in images:
        src = I['src']
        if not src: continue
        if any(x in src.lower() for x in ('seal_100','sprite','header_','icon')):
            continue
        local = local_for(src,'img') if 'aaro.mil' in src else ''
        url = './'+local if local else src
        alt = I.get('alt','') or ''
        ttl = I.get('title','') or alt or 'Image'
        out.append(f'<figure class="pg-img"><img loading="lazy" src="{html.escape(url)}" alt="{html.escape(alt)}"><figcaption>{html.escape(ttl)}</figcaption></figure>')
    return '<div class="pg-imgs">\n' + '\n'.join(out) + '\n</div>' if out else ''

def render_accordion(items):
    """Render accordion Q&A as native <details>/<summary> blocks."""
    if not items: return ''
    out = ['<div class="qa-list">']
    for it in items:
        q = html.escape(it.get('q','').strip())
        a = html.escape(it.get('a','').strip())
        if not q or not a: continue
        out.append(f'<details class="qa"><summary>{q}</summary><div class="qa-body">{a}</div></details>')
    out.append('</div>')
    return '\n'.join(out)

# Build sections
sections = []
for slug in ORDER:
    if slug not in parsed['pages']: continue
    p = parsed['pages'][slug]
    accordion = p.get('accordion') or []
    # On FAQ page, suppress the (now-redundant) flat text rendering of the same Q list
    if slug == 'faq' and accordion:
        body = ''
    else:
        body = text_to_html(p['text'])
    imgs = render_images([i for i in p['images'] if 'aaro.mil' in i['src']][:24])
    links = render_links(p['links'], max_n=80)
    qa = render_accordion(accordion)
    h1 = next((h['text'] for h in p['headings'] if h['level']=='h1'), LABELS.get(slug, slug))
    sections.append(f'''<section id="{slug}">
  <div class="container">
    <div class="section-label">§ {LABELS[slug]}</div>
    <h2>{html.escape(h1)}</h2>
    <div class="pg-content">{body}</div>
    {qa}
    {imgs}
    {('<h3 class="sub">Related Links</h3>'+links) if links else ''}
  </div>
</section>''')

nav_html = '\n        '.join(f'<li><a href="#{s}">{LABELS[s]}</a></li>' for s in ORDER)

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AARO — Details · About / FAQ / Reading Room (Offline Mirror)</title>
<meta name="description" content="Full text of all aaro.mil pages — mission, leadership, FAQ, EFOIA reading room — archived offline.">
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
  --stamp:#b91c1c; --caution:#4a9eff; --warm:#d4a017;
  --serif:"Source Serif 4","Iowan Old Style",Georgia,serif;
  --mono:"JetBrains Mono","SF Mono",Consolas,monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; scroll-padding-top: 80px; }
body {
  background: var(--bg); color: var(--ink);
  font-family: var(--serif); font-size: 16px; line-height: 1.65;
  background-image:
    radial-gradient(ellipse at 20% 0%, rgba(74,158,255,0.05) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(212,160,23,0.04) 0%, transparent 50%);
  background-attachment: fixed;
}
.container { max-width: 1100px; margin: 0 auto; padding: 0 32px; }

.gov-banner {
  background: #1a1a1f; border-bottom: 1px solid var(--rule);
  font-family: var(--mono); font-size: 11px; color: var(--ink-dim); letter-spacing: 0.04em;
}
.gov-banner .container { display: flex; align-items: center; gap: 16px; padding: 10px 32px; }
.gov-banner a { color: var(--caution); text-decoration: none; margin-left: auto; }
.flag-dot { width: 10px; height: 10px; border-radius: 50%;
  background: linear-gradient(45deg,#b91c1c 0,#b91c1c 50%,#1e3a8a 50%,#1e3a8a 100%); }

.header-wrap {
  position: sticky; top: 0; z-index: 40;
  background: rgba(10,10,12,0.95);
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--rule);
}
header { padding: 16px 0; }
header .container { display: flex; align-items: center; gap: 24px; flex-wrap: wrap; }
.brand { display: flex; align-items: center; gap: 14px; text-decoration: none; color: var(--ink); }
.seal {
  width: 44px; height: 44px;
  background: radial-gradient(circle at 50% 50%, #1e3a8a, #102560 60%, #061238);
  border-radius: 50%; display: grid; place-items: center;
  box-shadow: 0 0 0 2px var(--ink), 0 0 0 4px var(--bg), 0 0 0 5px var(--ink-faint);
  font-family: var(--mono); font-weight: 700; font-size: 11px; color: var(--ink);
}
.brand-text { display: flex; flex-direction: column; line-height: 1.1; }
.brand-text .super { font-family: var(--mono); font-size: 9px; letter-spacing: 0.18em; color: var(--ink-dim); text-transform: uppercase; }
.brand-text .name { font-family: var(--serif); font-size: 18px; font-weight: 600; margin-top: 2px; }
nav.primary { font-family: var(--mono); font-size: 11px; letter-spacing: 0.06em; flex: 1; }
nav.primary ul { display: flex; gap: 4px 14px; list-style: none; flex-wrap: wrap; justify-content: flex-end; }
nav.primary a { color: var(--ink-dim); text-decoration: none; text-transform: uppercase; }
nav.primary a:hover { color: var(--caution); }

/* Page hero */
.hero { padding: 56px 0 32px; border-bottom: 1px solid var(--rule); }
.hero .coords {
  font-family: var(--mono); font-size: 12px; color: var(--caution);
  letter-spacing: 0.12em; margin-bottom: 16px;
}
h1 { font-family: var(--serif); font-size: clamp(28px,4vw,42px); font-weight: 700; line-height: 1.1; letter-spacing: -0.02em; }
.hero p { max-width: 70ch; color: var(--ink-dim); margin-top: 16px; font-size: 16px; }

/* TOC */
.toc {
  margin: 28px 0 0; padding: 16px 20px;
  background: var(--panel); border: 1px solid var(--rule);
}
.toc h4 {
  font-family: var(--mono); font-size: 10px; letter-spacing: 0.18em;
  text-transform: uppercase; color: var(--ink-faint); margin-bottom: 8px;
}
.toc ul { list-style: none; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 6px 16px; }
.toc a { color: var(--ink-dim); text-decoration: none; font-family: var(--mono); font-size: 12px; letter-spacing: 0.04em; }
.toc a:hover { color: var(--caution); }

section { padding: 56px 0; border-bottom: 1px solid var(--rule); }
.section-label {
  font-family: var(--mono); font-size: 11px; letter-spacing: 0.24em;
  text-transform: uppercase; color: var(--ink-faint);
  display: flex; align-items: center; gap: 16px; margin-bottom: 18px;
}
.section-label::before { content: ""; width: 28px; height: 1px; background: var(--ink-faint); }
h2 { font-family: var(--serif); font-size: clamp(24px,3vw,34px); font-weight: 700; letter-spacing: -0.015em; margin-bottom: 20px; }
h3.sub {
  font-family: var(--mono); font-size: 12px;
  letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--ink-faint); margin: 28px 0 12px;
  padding-bottom: 8px; border-bottom: 1px dashed var(--rule);
}
.pg-content { max-width: 72ch; }
.pg-content p { margin-bottom: 12px; color: var(--ink); }

.pg-imgs {
  margin-top: 28px;
  display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}
.pg-img { background: var(--panel); border: 1px solid var(--rule); overflow: hidden; }
.pg-img img { width: 100%; aspect-ratio: 16/10; object-fit: cover; display: block; }
.pg-img figcaption {
  padding: 8px 10px; font-family: var(--mono); font-size: 10px;
  color: var(--ink-dim); letter-spacing: 0.04em; border-top: 1px solid var(--rule);
}

ul.lk-list {
  list-style: none; display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 4px 20px; max-width: 90ch;
}
ul.lk-list a {
  display: block; padding: 6px 0;
  color: var(--ink); text-decoration: none; font-size: 13px;
  border-bottom: 1px dashed var(--rule);
}
ul.lk-list a:hover { color: var(--caution); }
ul.lk-list .lk-meta {
  font-family: var(--mono); font-size: 9px; letter-spacing: 0.1em;
  color: var(--warm); text-transform: uppercase; margin-left: 6px;
}
ul.lk-list a.ext { color: var(--ink-dim); }

/* Accordion (Q&A) */
.qa-list { display: flex; flex-direction: column; gap: 8px; max-width: 80ch; margin-top: 12px; }
.qa {
  background: var(--panel); border: 1px solid var(--rule);
  transition: border-color .15s;
}
.qa[open] { border-color: var(--caution); }
.qa summary {
  cursor: pointer; padding: 14px 18px;
  font-family: var(--serif); font-size: 15px; font-weight: 600;
  color: var(--ink); list-style: none;
  display: flex; align-items: center; gap: 12px;
}
.qa summary::-webkit-details-marker { display: none; }
.qa summary::before {
  content: "+"; flex-shrink: 0;
  font-family: var(--mono); font-size: 18px; color: var(--caution);
  width: 18px; text-align: center;
}
.qa[open] summary::before { content: "−"; }
.qa summary:hover { color: var(--caution); }
.qa-body {
  padding: 0 18px 16px 48px;
  font-family: var(--serif); font-size: 14px; line-height: 1.6;
  color: var(--ink-dim);
}

footer {
  background: #060608; padding: 40px 0 24px;
  color: var(--ink-dim); font-family: var(--mono); font-size: 12px;
}
footer .container { display: flex; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
footer a { color: var(--ink-dim); text-decoration: none; }
footer a:hover { color: var(--caution); }
</style>
</head>
<body>

<div class="gov-banner">
  <div class="container">
    <span class="flag-dot"></span>
    <span>OFFLINE MIRROR · aaro.mil details</span>
    <a href="./index.html">← Evidence Browser</a>
  </div>
</div>

<div class="header-wrap">
<header>
  <div class="container">
    <a href="./index.html" class="brand">
      <div class="seal">AARO</div>
      <div class="brand-text">
        <span class="super">All-domain Anomaly Resolution Office</span>
        <span class="name">Details · About / FAQ</span>
      </div>
    </a>
    <nav class="primary">
      <ul>
        <li><a href="./index.html">← Evidence</a></li>
        <li><a href="#top">Top</a></li>
        <li><a href="../index.html">war.gov/UFO ↗</a></li>
      </ul>
    </nav>
  </div>
</header>
</div>

<div class="hero" id="top">
  <div class="container">
    <div class="coords">◉ AARO · Full Text Archive · For deep reading</div>
    <h1>AARO Pages — Full Mirror</h1>
    <p>
      The long-form content from every aaro.mil page mirrored here. Mission, leadership,
      the FAQ, reading room indexes, and the official background. For the actual UAP
      videos and case-resolution PDFs, go to the <a href="./index.html" style="color:var(--caution)">Evidence Browser</a>.
    </p>
    <div class="toc">
      <h4>Jump to a section</h4>
      <ul>
        __TOC__
      </ul>
    </div>
  </div>
</div>

__SECTIONS__

<footer>
  <div class="container">
    <span>Offline mirror · Source: aaro.mil · Captured via Wayback Machine</span>
    <span><a href="./index.html">Evidence Browser</a> · <a href="../index.html">war.gov/UFO mirror</a> · <a href="https://www.aaro.mil/" target="_blank" rel="noopener">Live aaro.mil ↗</a></span>
  </div>
</footer>

</body>
</html>'''

toc_html = '\n        '.join(f'<li><a href="#{s}">{LABELS[s]}</a></li>' for s in ORDER if s in parsed['pages'])
out_html = HTML_TEMPLATE.replace('__TOC__', toc_html).replace('__SECTIONS__', '\n'.join(sections))
open(os.path.join(ROOT, 'details.html'), 'w', encoding='utf-8').write(out_html)
print(f'wrote details.html ({len(out_html):,} bytes)')
