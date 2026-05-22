#!/usr/bin/env python3
"""Emit per-archive story.html pages.

Reads content from scripts/_stories.json. Each entry produces a long-form
story page at /<slug>/story.html mirroring the source agency's mission +
history + scope, verbatim where quoted.

Usage:
    python3 scripts/build-stories.py
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'scripts', '_stories.json')

TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' https://cloud.umami.is; script-src-attr 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://cloud.umami.is; object-src 'none'; base-uri 'self'; form-action 'self'; manifest-src 'self'; worker-src 'self'; upgrade-insecure-requests">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name_short} — story · realufo.org</title>
<meta name="description" content="The mission, history, and public record of {name_short_attr}, as published by the source agency. Verbatim official-source text mirrored from {official_host}.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://realufo.org/{slug}/story.html">
<meta property="og:title" content="{name_short_attr} — story · realufo.org">
<meta property="og:description" content="Mission and history of {name_short_attr}, mirrored verbatim from the source agency.">
<meta property="og:url" content="https://realufo.org/{slug}/story.html">
<meta property="og:type" content="article">
<meta property="og:image" content="https://realufo.org/{slug}/assets/og.svg">
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
:root{{--bg:#0a0a0c;--bg-2:#111114;--panel:#15151a;--ink:#e8e3d8;--ink-dim:#a8a298;--ink-faint:#6b665d;--rule:rgba(232,227,216,0.12);--rule-strong:rgba(232,227,216,0.28);--accent:{accent};--warm:#d4a017;--stamp:#b91c1c;--serif:"Source Serif 4",Georgia,serif;--mono:"JetBrains Mono",monospace}}
html{{scroll-behavior:smooth;scroll-padding-top:80px}}
body{{background:var(--bg);color:var(--ink);font-family:var(--serif);font-size:16px;line-height:1.7;overflow-x:hidden}}
.scanlines{{position:fixed;inset:0;pointer-events:none;z-index:9999;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.03) 2px,rgba(0,0,0,0.03) 4px)}}
@media (prefers-reduced-motion: reduce){{.scanlines{{display:none}}*,*::before,*::after{{animation-duration:0.001ms!important;transition-duration:0.001ms!important;scroll-behavior:auto!important}}}}
.container{{max-width:780px;margin:0 auto;padding:0 16px}}
.header-wrap{{position:sticky;top:0;z-index:900;background:rgba(21,21,26,0.92);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--rule);height:64px}}
.header{{max-width:1400px;margin:0 auto;padding:0 16px;height:100%;display:flex;align-items:center;gap:16px}}
.brand{{display:flex;align-items:center;gap:10px;text-decoration:none;flex-shrink:0;color:var(--ink)}}
.brand-seal{{width:36px;height:36px;border-radius:50%;background:radial-gradient(circle,{g1},{g2},{g3});display:flex;align-items:center;justify-content:center;font-family:var(--mono);font-size:9px;color:{seal_color};letter-spacing:0.06em;flex-shrink:0;font-weight:700}}
.brand-name{{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--ink);letter-spacing:0.12em;text-transform:uppercase}}
nav.primary{{display:flex;align-items:center;gap:4px;margin-left:auto;list-style:none}}
nav.primary a{{font-family:var(--mono);font-size:11px;color:var(--ink-dim);text-decoration:none;letter-spacing:0.1em;text-transform:uppercase;padding:10px;border-radius:4px}}
nav.primary a:hover{{color:var(--ink);background:rgba(232,227,216,0.06)}}
nav.primary a.active{{color:var(--accent)}}
.nav-toggle{{display:none;background:none;border:none;color:var(--ink);font-size:22px;cursor:pointer;padding:10px 8px;line-height:1;margin-left:auto}}
@media(max-width:719px){{.nav-toggle{{display:flex;align-items:center;justify-content:center}}nav.primary{{display:none;position:fixed;top:64px;left:0;right:0;background:var(--panel);border-bottom:1px solid var(--rule-strong);flex-direction:column;align-items:stretch;padding:8px 0 16px;margin-left:0;gap:0;max-height:calc(100vh - 64px);overflow-y:auto}}nav.primary.open{{display:flex}}nav.primary a{{padding:12px 20px}}}}

.hero{{padding:48px 0 24px;border-bottom:1px solid var(--rule)}}
.hero .coords{{font-family:var(--mono);font-size:12px;color:var(--accent);letter-spacing:0.14em;margin-bottom:14px;text-transform:uppercase}}
h1{{font-family:var(--serif);font-size:clamp(28px,5vw,40px);font-weight:700;line-height:1.15;letter-spacing:-0.02em}}
h1 em{{font-style:italic;color:var(--accent)}}
.hero p.lede{{max-width:65ch;color:var(--ink-dim);margin-top:18px;font-size:17px;line-height:1.55}}
.hero p.lede strong{{color:var(--ink)}}
.hero p.lede em{{color:var(--ink);font-style:italic}}
.hero p.lede a{{color:var(--ink);text-decoration:underline;text-decoration-color:rgba(212,160,23,0.4)}}
.attr-strip{{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:22px;font-family:var(--mono);font-size:11px;color:var(--ink-faint);letter-spacing:0.08em;text-transform:uppercase}}
.attr-strip strong{{color:var(--ink-dim);font-weight:500;margin-right:6px}}
.attr-strip a{{color:var(--ink-dim);text-decoration:none;border-bottom:1px dashed var(--rule-strong)}}
.attr-strip a:hover{{color:var(--accent);border-color:var(--accent)}}

section.s{{padding:34px 0;border-bottom:1px solid var(--rule)}}
h2{{font-family:var(--serif);font-size:clamp(20px,3vw,26px);font-weight:600;margin-bottom:16px;letter-spacing:-0.01em}}
p{{color:var(--ink-dim);margin-bottom:14px;max-width:68ch}}
p strong{{color:var(--ink);font-weight:600}}
p em{{font-style:italic;color:var(--ink)}}
a{{color:var(--accent);text-decoration:none}}
a:hover{{text-decoration:underline}}
.cross-refs{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}
.cross-refs a{{font-family:var(--mono);font-size:10px;letter-spacing:0.08em;text-transform:uppercase;padding:6px 11px;border-radius:3px;border:1px solid var(--rule);color:var(--ink-dim)}}
.cross-refs a:hover{{color:var(--accent);border-color:var(--accent);text-decoration:none}}
.back-link{{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;color:var(--ink-faint);text-decoration:none;letter-spacing:0.1em;margin-top:32px;padding:8px 0}}
.back-link:hover{{color:var(--accent)}}

footer{{border-top:1px solid var(--rule);margin-top:40px;padding:28px 16px;text-align:center}}
footer p{{font-family:var(--mono);font-size:10px;color:var(--ink-faint);letter-spacing:0.08em;line-height:1.8}}
footer a{{color:var(--ink-dim);text-decoration:none}}
@media print{{.scanlines,.header-wrap,footer,.back-link{{display:none}}body{{background:#fff;color:#000;font-size:11pt}}a{{color:#000;text-decoration:underline}}section.s{{break-inside:avoid;border:0}}h1,h2,h3{{color:#000}}}}
</style>
</head>
<body>
<div class="scanlines" aria-hidden="true"></div>

<div class="header-wrap">
  <div class="header">
    <a href="../" class="brand" aria-label="realufo.org home">
      <div class="brand-seal">{seal_text}</div>
      <span class="brand-name">{archive_display_name}</span>
    </a>
    <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false" aria-controls="primary-nav">&#9776;</button>
    <nav class="primary" id="primary-nav" aria-label="Main navigation">
      <a href="./">Archive</a>
      <a href="./story.html" class="active">Story</a>
      <a href="../search.html">Search</a>
      <a href="../timeline.html">Timeline</a>
      <a href="../">War.gov</a>
    </nav>
  </div>
</div>

<main class="container">

  <section class="hero">
    <div class="coords">{hero_coord}</div>
    <h1>{name_h1}</h1>
    <p class="lede">{lede}</p>
    <div class="attr-strip">
      <div><strong>Source:</strong> <a href="{official_url}" target="_blank" rel="noopener">{official_host}</a></div>
      <div><strong>Licence:</strong> {licence}</div>
    </div>
  </section>

{sections_html}

  <section class="s">
    <h2>Cross-references</h2>
    <div class="cross-refs">
{cross_refs_html}
    </div>
    <a class="back-link" href="./">&larr; Back to archive</a>
  </section>

</main>

<footer>
  <p>
    <a href="../">realufo.org</a> · {name_short} story · Mirrored from
    <a href="{official_url}" target="_blank" rel="noopener">{official_host}</a> ·
    {licence}
  </p>
</footer>

<script>
(function(){{
  var t=document.getElementById('nav-toggle'),n=document.getElementById('primary-nav');
  if(t&&n){{t.addEventListener('click',function(){{var o=n.classList.toggle('open');t.setAttribute('aria-expanded',o?'true':'false');}});}}
}})();
</script>
</body>
</html>
'''


def host_of(url: str) -> str:
    return urllib.parse.urlparse(url).netloc or url


def strip_html(s: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()


def section_html(title: str, body: str) -> str:
    return (
        '  <section class="s">\n'
        f'    <h2>{html.escape(title)}</h2>\n'
        f'    <p>{body}</p>\n'
        '  </section>\n'
    )


def cross_ref_html(label: str, href: str) -> str:
    return f'      <a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>\n'


def name_h1(name: str) -> str:
    base = name.split(' · ')[0] if ' · ' in name else name
    if ' — ' in base:
        a, b = base.split(' — ', 1)
        return f'{html.escape(a)} <em>—</em> {html.escape(b)}'
    if ' ' in base:
        first, rest = base.split(' ', 1)
        return f'<em>{html.escape(first)}</em> {html.escape(rest)}'
    return html.escape(base)


def render(arc: dict) -> str:
    sections = ''.join(section_html(t, b) for t, b in arc['sections'])
    crefs = ''.join(cross_ref_html(l, h) for l, h in arc['cross_refs'])
    name = arc['name']
    display_name = (name[:36] + '…') if len(name) > 36 else name

    jsonld = json.dumps({
        '@context': 'https://schema.org',
        '@type': 'AboutPage',
        'name': f'{name} — story',
        'description': strip_html(arc['lede'])[:300],
        'url': f'https://realufo.org/{arc["slug"]}/story.html',
        'publisher': {'@type': 'Organization', 'name': 'realufo.org', 'url': 'https://realufo.org/'},
        'sourceOrganization': {'@type': 'GovernmentOrganization', 'name': name, 'url': arc['official_url']},
        'license': arc['licence'],
        'isAccessibleForFree': True,
        'inLanguage': 'en',
    }, ensure_ascii=False, indent=2)

    return TEMPLATE.format(
        slug=arc['slug'],
        name_short=name,
        name_short_attr=html.escape(name, quote=True),
        name_h1=name_h1(name),
        archive_display_name=html.escape(display_name),
        seal_text=html.escape(arc['sealText']),
        seal_color=arc['sealColor'],
        accent=arc['accent'],
        g1=arc['gradient'][0], g2=arc['gradient'][1], g3=arc['gradient'][2],
        official_url=arc['official_url'],
        official_host=host_of(arc['official_url']),
        licence=arc['licence'],
        hero_coord=arc['hero_coord'],
        lede=arc['lede'],
        jsonld=jsonld,
        sections_html=sections,
        cross_refs_html=crefs,
    )


def main() -> int:
    archives = json.load(open(DATA, encoding='utf-8'))
    written = 0
    for arc in archives:
        out_dir = os.path.join(ROOT, arc['slug'])
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, 'story.html')
        body = render(arc)
        open(out, 'w', encoding='utf-8').write(body)
        size = os.path.getsize(out)
        print(f'  + {arc["slug"]:12s} → {os.path.relpath(out)} ({size:,} bytes)')
        written += 1
    print(f'\n→ {written} story pages emitted')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
