#!/usr/bin/env python3
"""One-shot sweep that fixes the html-validate a11y errors flagged on
non-scraped pages.

Patterns covered:
  1. aria-label on plain <div> (hero-carousel, archive-pills, filter-group,
     chips, #map, #archive-chips) → add role="region" / role="group".
  2. <div class="lightbox" ... aria-hidden="true"> → drop aria-hidden
     (the lightbox is hidden via CSS display:none; the attribute lies when
     opened and traps focusable children when html-validate examines the
     static markup).
  3. <nav class="toc"> / <nav class="pagination"> → add aria-label.
  4. index.html <span> that wraps the brand + nav-toggle → change to <div>.
"""
from __future__ import annotations
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# (regex, replacement, flags) — regex must be idempotent.
SUBS = [
    # hero-carousel div → add role="region" if missing
    (
        r'(<div class="hero-carousel"(?![^>]*role=)[^>]*?)>',
        r'\1 role="region">',
    ),
    # archive-pills / filter-group / chips / archive-chips → role="group"
    (
        r'(<div class="archive-pills"(?![^>]*role=)[^>]*?)>',
        r'\1 role="group">',
    ),
    (
        r'(<div class="filter-group"(?![^>]*role=)[^>]*?)>',
        r'\1 role="group">',
    ),
    (
        r'(<div class="chips"(?![^>]*role=)[^>]*?aria-label="[^"]*"[^>]*?)>',
        r'\1 role="group">',
    ),
    # #map → role="region"
    (
        r'(<div id="map"(?![^>]*role=)[^>]*?aria-label="[^"]*"[^>]*?)>',
        r'\1 role="region">',
    ),
    # lightbox container static aria-hidden — strip the attribute
    (
        r'(<div class="lightbox"[^>]*?)\s+aria-hidden="true"',
        r'\1',
    ),
    # <nav class="toc"> add aria-label="Page sections"
    (
        r'(<nav class="toc"(?![^>]*aria-label=)[^>]*?)>',
        r'\1 aria-label="Page sections">',
    ),
    # <nav class="pagination"> add aria-label="Pagination"
    (
        r'(<nav class="pagination"(?![^>]*aria-label=)[^>]*?)>',
        r'\1 aria-label="Pagination">',
    ),
]

# index.html-specific: the <span> wrapping brand+nav-toggle should be <div>.
# Idempotent: only target the exact <span> that immediately follows
# <div class="container"> and contains <a class="brand"> + nav-toggle.
SPAN_PATCH = (
    re.compile(
        r'(<div class="container">\s*)<span>\s*'
        r'(<a href="#" class="brand">.*?</a>\s*'
        r'<button class="nav-toggle"[^>]*>.*?</button>\s*)</span>',
        re.DOTALL,
    ),
    r'\1<div class="brand-row">\n      \2</div>',
)

def fix(html: str) -> tuple[str, int]:
    n = 0
    for pat, rep in SUBS:
        new, count = re.subn(pat, rep, html)
        n += count
        html = new
    new, count = SPAN_PATCH[0].subn(SPAN_PATCH[1], html)
    n += count
    return new, n

def main() -> None:
    targets = [
        REPO / 'foia.html',
        REPO / 'glossary.html',
        REPO / 'index.html',
        REPO / 'map.html',
        REPO / 'search.html',
        REPO / 'whatsnew.html',
        REPO / 'aaro/index.html',
        REPO / 'geipan/index.html',
        REPO / 'nara/index.html',
        REPO / 'nasa/index.html',
    ]
    total = 0
    for p in targets:
        if not p.exists():
            continue
        src = p.read_text(encoding='utf-8')
        out, n = fix(src)
        if n:
            p.write_text(out, encoding='utf-8')
            total += n
            print(f"  {p.relative_to(REPO)}: {n} edit(s)")
    print(f"\napplied {total} edit(s)")

if __name__ == '__main__':
    main()
