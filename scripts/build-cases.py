#!/usr/bin/env python3
"""Generate case detail pages from scripts/_cases.json.

Same visual + structural template as the hand-written case pages
(aaro/tic-tac.html, brazil/varginha.html, etc.) — hero with coord line,
meta strip, sections, pullquote, timeline, evidence list, cross-references,
share, citation, reading-time. Designed so adding another major case is
a JSON edit.

Usage:
    python3 scripts/build-cases.py
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'scripts', '_cases.json')


def strip_html(s: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()


def word_count(case: dict) -> int:
    """Approximate body word count for reading-time hint."""
    pieces = [case['lede']]
    for sec in case['sections']:
        pieces.append(sec['body'])
    pieces.append(case['pullquote']['text'])
    for t, b in case['timeline']:
        pieces.append(b)
    for ev in case['evidence']:
        pieces.append(ev['body'])
    pieces.append(case['why_matters'])
    text = ' '.join(strip_html(p) for p in pieces)
    return len(text.split())


def build_jsonld(case: dict) -> str:
    j = case['json_ld']
    about = j.get('about', [])
    about_nodes = [{'@type': 'Place', 'name': p} for p in about]
    data = {
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': j['headline'],
        'description': j['description'],
        'datePublished': j['datePublished'],
        'url': f'https://realufo.org/{case["archive"]}/{case["slug"]}.html',
        'image': case.get('twitter_image', 'https://realufo.org/assets/og.svg'),
        'author': {'@type': 'Organization', 'name': 'realufo.org'},
        'publisher': {'@type': 'Organization', 'name': 'realufo.org', 'url': 'https://realufo.org/'},
        'sourceOrganization': {'@type': 'GovernmentOrganization', 'name': j['sourceOrganization']},
        'about': about_nodes[0] if len(about_nodes) == 1 else about_nodes,
        'keywords': j['keywords'],
        'inLanguage': 'en',
        'isAccessibleForFree': True,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def render_meta_strip(items):
    return ''.join(
        f'      <div><strong>{html.escape(label)}:</strong> {value}</div>\n'
        for label, value in items
    )


def render_sections(sections):
    out = []
    for sec in sections:
        out.append(
            '  <section>\n'
            f'    <h2>{html.escape(sec["h"])}</h2>\n'
            f'    <p>{sec["body"]}</p>\n'
            '  </section>\n'
        )
    return ''.join(out)


def render_pullquote(p):
    return (
        '    <div class="pullquote">\n'
        f'      {p["text"]}\n'
        f'      <cite>{html.escape(p["cite"])}</cite>\n'
        '    </div>\n'
    )


def render_timeline(items):
    out = ['  <section>\n    <h2>Timeline</h2>\n    <ul class="timeline">\n']
    for t, b in items:
        out.append(
            f'      <li><time>{html.escape(t)}</time><p>{b}</p></li>\n'
        )
    out.append('    </ul>\n  </section>\n')
    return ''.join(out)


def render_evidence(items):
    out = ['  <section>\n    <h2>Linked evidence in this archive</h2>\n    <ul class="evidence-list">\n']
    for ev in items:
        actions = ''
        for action in ev.get('actions', []):
            # Normalize: ['Label', 'href'] or ['Label', 'href', 'Primary']
            label = action[0]
            href = action[1]
            cls = 'btn-primary' if (len(action) > 2 and action[2].lower() == 'primary') else ''
            ext = ' target="_blank" rel="noopener"' if href.startswith('http') else ''
            actions += (
                f'          <a class="btn {cls}" href="{html.escape(href, quote=True)}"{ext}>'
                f'{html.escape(label)}</a>\n'
            )
        out.append(
            '      <li>\n'
            f'        <div class="ev-meta"><span class="ev-id">{html.escape(ev["ev_id"])}</span> · '
            f'{html.escape(ev["ev_archive"])} · {html.escape(ev["ev_kind"])}</div>\n'
            f'        <div class="ev-title">{html.escape(ev["title"])}</div>\n'
            f'        <p>{ev["body"]}</p>\n'
            f'        <div class="ev-actions">\n{actions}        </div>\n'
            '      </li>\n'
        )
    out.append('    </ul>\n  </section>\n')
    return ''.join(out)


def render_cross_refs(items):
    links = '\n'.join(
        f'      <a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>'
        for label, href in items
    )
    return f'    <div class="cross-refs">\n{links}\n    </div>\n'


TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' https://cloud.umami.is; script-src-attr 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://cloud.umami.is; object-src 'none'; base-uri 'self'; form-action 'self'; manifest-src 'self'; worker-src 'self'; upgrade-insecure-requests">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title_html} — case file · {archive_label} · realufo.org</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://realufo.org/{archive}/{slug}.html">
<meta property="og:title" content="{title_html} · {archive_label} case file">
<meta property="og:description" content="{desc_short}">
<meta property="og:url" content="https://realufo.org/{archive}/{slug}.html">
<meta property="og:type" content="article">
<meta property="og:image" content="{twitter_image}">
<meta property="og:site_name" content="realufo.org">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/svg+xml" href="./assets/favicon.svg">
<link rel="apple-touch-icon" href="./assets/favicon.svg">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#0a0a0c">
<script>if("serviceWorker" in navigator){{window.addEventListener("load",function(){{navigator.serviceWorker.register("/sw.js").catch(function(){{}});}});}}</script>
<script defer src="/assets/vendor/hotkeys.js"></script>
<script defer src="https://cloud.umami.is/script.js" data-website-id="9c4f36ef-30ad-4d76-947a-1724fe6acdba"></script>
<script type="application/ld+json">
{jsonld}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Source+Serif+4:ital,wght@0,400;0,600;1,400;1,600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0a0a0c;--bg-2:#111114;--panel:#15151a;--ink:#e8e3d8;--ink-dim:#a8a298;--ink-faint:#6b665d;--rule:rgba(232,227,216,0.12);--rule-strong:rgba(232,227,216,0.28);--caution:{accent};--accent:{accent};--warm:#d4a017;--stamp:#b91c1c;--serif:"Source Serif 4",Georgia,serif;--mono:"JetBrains Mono",monospace}}
html{{scroll-behavior:smooth;scroll-padding-top:80px}}
body{{background:var(--bg);color:var(--ink);font-family:var(--serif);font-size:16px;line-height:1.65;overflow-x:hidden}}
.scanlines{{position:fixed;inset:0;pointer-events:none;z-index:9999;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.03) 2px,rgba(0,0,0,0.03) 4px)}}
@media (prefers-reduced-motion: reduce){{.scanlines{{display:none}}*,*::before,*::after{{animation-duration:0.001ms!important;transition-duration:0.001ms!important;scroll-behavior:auto!important}}}}
.container{{max-width:880px;margin:0 auto;padding:0 16px}}
.header-wrap{{position:sticky;top:0;z-index:900;background:rgba(21,21,26,0.92);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--rule);height:64px}}
.header{{max-width:1400px;margin:0 auto;padding:0 16px;height:100%;display:flex;align-items:center;gap:16px}}
.brand{{display:flex;align-items:center;gap:10px;text-decoration:none;flex-shrink:0;color:var(--ink)}}
.brand-seal{{width:36px;height:36px;border-radius:50%;background:radial-gradient(circle,{g1},{g2},{g3});display:flex;align-items:center;justify-content:center;font-family:var(--mono);font-size:9px;color:{seal_color};letter-spacing:0.06em;flex-shrink:0;font-weight:700}}
.brand-name{{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--ink);letter-spacing:0.12em;text-transform:uppercase}}
nav.primary{{display:flex;align-items:center;gap:4px;margin-left:auto;list-style:none}}
nav.primary a{{font-family:var(--mono);font-size:11px;color:var(--ink-dim);text-decoration:none;letter-spacing:0.1em;text-transform:uppercase;padding:10px;border-radius:4px}}
nav.primary a:hover{{color:var(--ink);background:rgba(232,227,216,0.06)}}
.nav-toggle{{display:none;background:none;border:none;color:var(--ink);font-size:22px;cursor:pointer;padding:10px 8px;line-height:1;margin-left:auto}}
@media(max-width:719px){{.nav-toggle{{display:flex;align-items:center;justify-content:center}}nav.primary{{display:none;position:fixed;top:64px;left:0;right:0;background:var(--panel);border-bottom:1px solid var(--rule-strong);flex-direction:column;align-items:stretch;padding:8px 0 16px;margin-left:0;gap:0;max-height:calc(100vh - 64px);overflow-y:auto}}nav.primary.open{{display:flex}}nav.primary a{{padding:12px 20px}}}}
.hero{{padding:48px 0 28px;border-bottom:1px solid var(--rule)}}
.hero .coords{{font-family:var(--mono);font-size:12px;color:var(--accent);letter-spacing:0.14em;margin-bottom:14px;text-transform:uppercase}}
h1{{font-family:var(--serif);font-size:clamp(28px,5vw,44px);font-weight:700;line-height:1.1;letter-spacing:-0.02em}}
h1 em{{font-style:italic;color:var(--accent)}}
.hero p.lede{{max-width:65ch;color:var(--ink-dim);margin-top:18px;font-size:17px;line-height:1.55}}
.hero p.lede a{{color:var(--ink);text-decoration:underline;text-decoration-color:rgba(212,160,23,0.4)}}
.meta-strip{{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:22px;font-family:var(--mono);font-size:11px;color:var(--ink-faint);letter-spacing:0.08em;text-transform:uppercase}}
.meta-strip strong{{color:var(--ink-dim);font-weight:500;margin-right:6px}}
section{{padding:40px 0;border-bottom:1px solid var(--rule)}}
h2{{font-family:var(--serif);font-size:clamp(20px,3vw,28px);font-weight:600;margin-bottom:18px;letter-spacing:-0.01em}}
h3{{font-family:var(--mono);font-size:11px;text-transform:uppercase;letter-spacing:0.14em;color:var(--accent);margin:24px 0 10px;font-weight:700}}
p{{max-width:68ch;color:var(--ink-dim);margin-bottom:14px}}
p strong{{color:var(--ink);font-weight:600}}
p em{{font-style:italic;color:var(--ink)}}
a{{color:var(--accent);text-decoration:none}}
a:hover{{text-decoration:underline}}
.timeline{{list-style:none;padding-left:0;margin:0;border-left:2px solid var(--rule-strong);padding-left:22px}}
.timeline li{{position:relative;padding:0 0 18px}}
.timeline li::before{{content:"";position:absolute;left:-29px;top:8px;width:10px;height:10px;border-radius:50%;background:var(--accent);border:2px solid var(--bg)}}
.timeline time{{display:block;font-family:var(--mono);font-size:11px;color:var(--accent);letter-spacing:0.1em;margin-bottom:4px;text-transform:uppercase}}
.timeline p{{margin-bottom:0;color:var(--ink-dim)}}
.evidence-list{{list-style:none;padding:0;display:grid;gap:12px}}
.evidence-list li{{background:var(--bg-2);border:1px solid var(--rule);border-radius:6px;padding:14px 16px}}
.evidence-list .ev-title{{font-family:var(--serif);font-size:15px;color:var(--ink);font-weight:600;margin-bottom:4px}}
.evidence-list .ev-meta{{font-family:var(--mono);font-size:10px;color:var(--ink-faint);letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px}}
.evidence-list .ev-meta .ev-id{{color:var(--accent);font-weight:700}}
.evidence-list p{{font-size:14px;margin-bottom:6px}}
.evidence-list .ev-actions{{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}}
.evidence-list .btn{{font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;padding:7px 12px;border-radius:4px;text-decoration:none;border:1px solid var(--rule-strong);color:var(--ink-dim);transition:color 0.15s,border-color 0.15s,background 0.15s}}
.evidence-list .btn:hover{{color:var(--ink);border-color:var(--accent);background:rgba(212,160,23,0.08)}}
.evidence-list .btn-primary{{background:rgba(212,160,23,0.14);border-color:rgba(212,160,23,0.4);color:var(--accent)}}
.pullquote{{margin:28px 0;padding:18px 22px;border-left:3px solid var(--accent);background:rgba(212,160,23,0.05);font-family:var(--serif);font-style:italic;color:var(--ink);font-size:17px;line-height:1.55;max-width:62ch}}
.pullquote cite{{display:block;margin-top:10px;font-style:normal;font-family:var(--mono);font-size:10px;letter-spacing:0.1em;color:var(--ink-faint);text-transform:uppercase}}
.cross-refs{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}
.cross-refs a{{font-family:var(--mono);font-size:10px;letter-spacing:0.08em;text-transform:uppercase;padding:6px 11px;border-radius:3px;border:1px solid var(--rule);color:var(--ink-dim)}}
.cross-refs a:hover{{color:var(--accent);border-color:var(--accent);text-decoration:none}}
.back-link{{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;color:var(--ink-faint);text-decoration:none;letter-spacing:0.1em;margin-top:32px;padding:8px 0}}
.back-link:hover{{color:var(--accent)}}
footer{{border-top:1px solid var(--rule);margin-top:40px;padding:28px 16px;text-align:center}}
footer p{{font-family:var(--mono);font-size:10px;color:var(--ink-faint);letter-spacing:0.08em;line-height:1.8}}
footer a{{color:var(--ink-dim)}}
/* share button */
#share-mount{{margin:22px 0 6px}}
.share-btn{{font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;padding:9px 16px;border-radius:4px;background:var(--bg-2);border:1px solid var(--rule-strong);color:var(--ink-dim);cursor:pointer;display:inline-flex;align-items:center;gap:8px;transition:color 0.15s,border-color 0.15s,background 0.15s}}
.share-btn:hover{{color:var(--accent);border-color:var(--accent);background:rgba(212,160,23,0.08)}}
.share-btn.copied{{color:#4ade80;border-color:#4ade80;background:rgba(74,222,128,0.12)}}
/* citation panel */
.cite-box{{margin:24px 0;padding:18px 20px;background:var(--bg-2);border:1px solid var(--rule);border-radius:8px}}
.cite-box h3{{font-family:var(--mono);font-size:11px;text-transform:uppercase;letter-spacing:0.14em;color:var(--accent);margin:0 0 12px;font-weight:700}}
.cite-buttons{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}}
.cite-buttons button{{font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:6px 12px;border-radius:3px;background:var(--bg);border:1px solid var(--rule-strong);color:var(--ink-dim);cursor:pointer;transition:color 0.15s,border-color 0.15s,background 0.15s}}
.cite-buttons button:hover{{color:var(--ink);border-color:var(--accent)}}
.cite-buttons button.copied{{background:rgba(74,222,128,0.16);border-color:#4ade80;color:#4ade80}}
.cite-out{{font-family:var(--mono);font-size:11px;line-height:1.5;color:var(--ink);background:var(--bg);border:1px solid var(--rule);border-radius:4px;padding:12px 14px;white-space:pre-wrap;overflow-x:auto;margin:0 0 10px;max-height:240px}}
.cite-hint{{font-family:var(--mono);font-size:10px;letter-spacing:0.06em;color:var(--ink-faint);line-height:1.5}}
@media print{{.scanlines,.header-wrap,footer,.back-link,#share-mount,.cite-box{{display:none}}body{{background:#fff;color:#000;font-size:11pt}}a{{color:#000;text-decoration:underline}}a[href^="http"]::after{{content:" <" attr(href) ">";font-size:9pt;color:#444}}.pullquote{{border-color:#000;background:#f0f0f0;color:#000}}section{{break-inside:avoid;border:0}}h1,h2,h3{{color:#000}}}}
</style>
</head>
<body>
<div class="scanlines" aria-hidden="true"></div>

<div class="header-wrap">
  <div class="header">
    <a href="../" class="brand" aria-label="realufo.org home">
      <div class="brand-seal">{seal_text}</div>
      <span class="brand-name">{archive_label}</span>
    </a>
    <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false" aria-controls="primary-nav">&#9776;</button>
    <nav class="primary" id="primary-nav" aria-label="Main navigation">
      <a href="./">Archive</a>
      <a href="./story.html">Story</a>
      <a href="../search.html">Search</a>
      <a href="../">War.gov</a>
    </nav>
  </div>
</div>

<main class="container">

  <section class="hero">
    <div class="coords">{hero_coord}</div>
    <h1><em>{name_h1_em}</em> {name_h1_tail}</h1>
    <p class="lede">{lede}</p>
    <div class="meta-strip">
{meta_strip}      <div data-readtime><strong>Read time:</strong> {minutes} min · {words:,} words</div>
    </div>
  </section>

{sections_html}
  <section>
    <h2>The voice on the tape</h2>
{pullquote_html}  </section>
{timeline_html}{evidence_html}  <section>
    <h2>Why this case still matters</h2>
    <p>{why_matters}</p>
{cross_refs_html}
<div id="share-mount"></div>
    <div id="cite-mount"></div>
    <a class="back-link" href="./">&larr; Back to archive</a>
  </section>

</main>

<footer>
  <p>
    <a href="../">realufo.org</a> · {archive_label} · {licence} ·
    Mirrored from <a href="{official_url}" target="_blank" rel="noopener">{official_host}</a>
  </p>
</footer>

<script>
(function(){{
  var t=document.getElementById('nav-toggle'),n=document.getElementById('primary-nav');
  if(t&&n){{t.addEventListener('click',function(){{var o=n.classList.toggle('open');t.setAttribute('aria-expanded',o?'true':'false');}});}}
}})();
</script>
<script defer src="/assets/vendor/citation.js"></script>
<script defer src="/assets/vendor/share.js"></script>
</body>
</html>
'''


def host_of(url: str) -> str:
    return urllib.parse.urlparse(url).netloc or url


def render(case: dict) -> str:
    minutes = max(1, round(word_count(case) / 220))
    desc_short = strip_html(case['json_ld']['description'])[:155]
    desc_full = strip_html(case['json_ld']['description'])[:300]
    title_h = html.escape(case['name'])
    return TEMPLATE.format(
        title_html=title_h,
        archive=case['archive'],
        slug=case['slug'],
        archive_label=html.escape(case['archive_label']),
        desc=html.escape(desc_full, quote=True),
        desc_short=html.escape(desc_short, quote=True),
        twitter_image=case.get('twitter_image', 'https://realufo.org/assets/og.svg'),
        jsonld=build_jsonld(case),
        accent=case['accent'],
        g1=case['gradient'][0], g2=case['gradient'][1], g3=case['gradient'][2],
        seal_text=case['seal_text'],
        seal_color=case['seal_color'],
        name_h1_em=html.escape(case['name_h1_em']),
        name_h1_tail=html.escape(case['name_h1_tail']),
        hero_coord=case['hero_coord'],
        lede=case['lede'],
        meta_strip=render_meta_strip(case['meta_strip']),
        minutes=minutes,
        words=word_count(case),
        sections_html=render_sections(case['sections']),
        pullquote_html=render_pullquote(case['pullquote']),
        timeline_html=render_timeline(case['timeline']),
        evidence_html=render_evidence(case['evidence']),
        why_matters=case['why_matters'],
        cross_refs_html=render_cross_refs(case['cross_refs']),
        licence=case['licence'],
        official_url=case['official_url'],
        official_host=host_of(case['official_url']),
    )


def main() -> int:
    cases = json.load(open(DATA, encoding='utf-8'))
    written = 0
    for case in cases:
        out_dir = os.path.join(ROOT, case['archive'])
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, f'{case["slug"]}.html')
        body = render(case)
        open(out, 'w', encoding='utf-8').write(body)
        size = os.path.getsize(out)
        print(f'  + {case["archive"]:8s} / {case["slug"]:20s} → {os.path.relpath(out)} ({size:,} bytes)')
        written += 1
    print(f'\n→ {written} case pages emitted')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
