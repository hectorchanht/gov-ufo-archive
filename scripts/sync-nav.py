#!/usr/bin/env python3
"""Single source of truth for the navigation bar.

Reads `scripts/_site_template.make_nav()` and injects its output into
every hand-written HTML page in the repo. Static-built mirror pages
(aaro/index.html, nasa/index.html, etc.) already call make_nav() at
build time, so this script targets the rest:

  - Root:          index.html (War.gov landing)
  - Utility pages: search.html, timeline.html, map.html, about.html,
                    donate.html, glossary.html, stats.html, 404.html
  - Story pages:   22 case narratives under aaro/, uk/, brazil/, and the
                    11 per-mirror story.html files
  - Detail pages:  aaro/details.html (auto-rebuilt by build-details.py)

Each target file must contain exactly one
  <nav class="primary" id="primary-nav" ...>...</nav>
or
  <nav class="primary-nav" id="primary-nav" ...>...</nav>
block. The script replaces that block with the canonical output of
make_nav(current_slug, depth, internal_links=None).

current_slug + depth are inferred from the file path. Add an override
in PAGE_OVERRIDES below to flag a story page or rename slugs.

Run:
    python3 scripts/sync-nav.py
    python3 scripts/sync-nav.py --check    # CI mode: exit non-zero on drift
"""
from __future__ import annotations
import os, re, sys, glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _site_template import make_nav, STORIES, SITE_PAGES, MORE


def page_meta(path: str) -> tuple[str, int]:
    """Return (current_slug, depth) for a given HTML file path."""
    rel = os.path.relpath(path, REPO).replace(os.sep, '/')
    # Root-level utility pages
    root_pages = {
        'index.html':    ('wargov',   0),
        'search.html':   ('search',   0),
        'timeline.html': ('timeline', 0),
        'map.html':      ('map',      0),
        'about.html':    ('about',    0),
        'donate.html':   ('support',  0),
        'glossary.html': ('glossary', 0),
        'stats.html':    ('stats',    0),
        '404.html':      ('404',      0),
    }
    if rel in root_pages:
        return root_pages[rel]
    # Story pages — slug is the full mirror/file.html path so Story dropdown highlights correctly
    for _, story_path in STORIES:
        if rel == story_path:
            return (story_path, 1)
    # Mirror index pages
    parts = rel.split('/')
    if len(parts) == 2 and parts[1] == 'index.html':
        return (parts[0], 1)
    # Mirror sub-page (e.g. aaro/details.html)
    if len(parts) == 2 and parts[1].endswith('.html'):
        return (parts[0], 1)
    # Default
    return ('', 1)


# Match the existing <nav> block. Two markup variants — primary and primary-nav.
NAV_RE = re.compile(
    r'<nav class="primary(?:-nav)?"[^>]*id="primary-nav"[^>]*>[\s\S]*?</nav>',
    re.M,
)

# Pages to skip entirely
SKIP = {'README.md', 'CLAUDE.md'}
SKIP_DIRS = {'.git', '.cache', 'node_modules', 'bundles', 'slideshow',
             'assets', 'api', '_site', 'scripts'}


def collect_html_files() -> list[str]:
    out = []
    for root, dirs, files in os.walk(REPO):
        # Skip noise dirs
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
        for f in files:
            if not f.endswith('.html'): continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, REPO).replace(os.sep, '/')
            if rel in SKIP: continue
            out.append(path)
    return sorted(out)


def sync(check: bool = False) -> int:
    drift = []
    updated = []
    skipped = []
    for path in collect_html_files():
        with open(path, encoding='utf-8') as f:
            src = f.read()
        if not NAV_RE.search(src):
            skipped.append(path)
            continue
        slug, depth = page_meta(path)
        new_nav = make_nav(slug, depth).rstrip()
        # Compare against existing
        existing = NAV_RE.search(src).group(0)
        if existing.strip() == new_nav.strip():
            continue   # no drift
        if check:
            drift.append(path)
            continue
        new_src = NAV_RE.sub(new_nav, src, count=1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_src)
        updated.append(path)

    if check:
        if drift:
            print(f'NAV DRIFT in {len(drift)} files:')
            for p in drift:
                print(f'  {os.path.relpath(p, REPO)}')
            return 1
        print(f'No nav drift across {len(collect_html_files())} files.')
        return 0

    print(f'Updated {len(updated)} files; skipped {len(skipped)} without nav.')
    for p in updated[:25]:
        print(f'  ✓ {os.path.relpath(p, REPO)}')
    if len(updated) > 25:
        print(f'  … and {len(updated) - 25} more')
    return 0


if __name__ == '__main__':
    sys.exit(sync(check='--check' in sys.argv))
