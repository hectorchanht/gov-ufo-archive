"""Canonical nav builder + nav config tables.

Single source of truth for the sticky header navigation across every page.

Public surface:
    PINNED, SITE_PAGES, MORE, STORIES   — configuration tables
    _href(slug, depth)                  — depth-aware relative-URL helper
    make_nav(current_slug, depth, ...)  — returns <nav class="primary">…</nav>

scripts/sync-nav.py walks every hand-written HTML file and rewrites its
<nav> block to the make_nav() output. Build scripts call make_nav() at
build time. CI workflow .github/workflows/sync-nav.yml gates against
drift by running `sync-nav.py --check`.
"""
from __future__ import annotations


# ── Configuration tables ─────────────────────────────────────────────────────

PINNED = [
    ('War.gov', None,   'wargov'),    # root — landing page
    ('AARO',    'aaro', 'aaro'),
    ('NASA',    'nasa', 'nasa'),
    ('NARA',    'nara', 'nara'),
]
# "Site ▾" dropdown — pages about the site itself. (label, file, slug_key)
SITE_PAGES = [
    ('Search',   'search.html',   'search'),
    ('Timeline', 'timeline.html', 'timeline'),
    ('Map',      'map.html',      'map'),
    ('About',    'about.html',    'about'),
    ('Support',  'donate.html',   'support'),
]
# "Nations ▾" dropdown — 11 non-US national mirrors.
MORE = [
    ('GEIPAN (France)',    'geipan'),
    ('UK Archives',        'uk'),
    ('Brazil FAB',         'brazil'),
    ('Chile CEFAA',        'chile'),
    ('NZ NZDF',            'nz'),
    ('Canada LAC',         'canada'),
    ('Argentina CEFAe',    'argentina'),
    ('Uruguay CRIDOVNI',   'uruguay'),
    ('Peru OIFAA',         'peru'),
    ('Spain Ejército',     'spain'),
    ('Italy Aeronautica',  'italy'),
]
# "Story ▾" dropdown — every story page across every mirror. Root-relative.
# Grouped by archive for readability; rendered in declared order.
STORIES = [
    # AARO — US Navy / military cases
    ('Tic-Tac (Nimitz · 2004)',         'aaro/tic-tac.html'),
    ('GIMBAL (Roosevelt · 2015)',       'aaro/gimbal.html'),
    ('Phoenix Lights (1997)',           'aaro/phoenix-lights.html'),
    ('Belgian Wave (1989-90)',          'aaro/belgian-wave.html'),
    ('Cash–Landrum (1980)',             'aaro/cash-landrum.html'),
    ('Coyne helicopter (1973)',         'aaro/coyne.html'),
    ('JAL Flight 1628 (1986)',          'aaro/jal-1628.html'),
    ('Tehran F-4 (1976)',               'aaro/tehran.html'),
    ('Travis Walton (1975)',            'aaro/travis-walton.html'),
    ('O’Hare Airport (2006)',           'aaro/ohare-2006.html'),
    ('Stephenville (2008)',             'aaro/stephenville.html'),
    ('AARO story',                      'aaro/story.html'),
    # UK
    ('Rendlesham Forest (1980)',        'uk/rendlesham.html'),
    ('Cosford / Shawbury (1993)',       'uk/cosford.html'),
    ('UK MoD story',                    'uk/story.html'),
    # Brazil
    ('Operação Prato (1977)',           'brazil/operacao-prato.html'),
    ('Varginha (1996)',                 'brazil/varginha.html'),
    ('Trindade Island (1958)',          'brazil/trindade.html'),
    ('Brazil OVNI story',               'brazil/story.html'),
    # NASA / NARA / GEIPAN
    ('NASA UAP story',                  'nasa/story.html'),
    ('NARA — Roswell (1947)',           'nara/roswell.html'),
    ('NARA — Socorro (1964)',           'nara/socorro.html'),
    ('NARA — Mantell (1948)',           'nara/mantell.html'),
    ('NARA — Chiles-Whitted (1948)',    'nara/chiles-whitted.html'),
    ('NARA — McMinnville (1950)',       'nara/mcminnville.html'),
    ('NARA — Lubbock Lights (1951)',    'nara/lubbock-lights.html'),
    ('NARA — Levelland (1957)',         'nara/levelland.html'),
    ('NARA — Robertson Panel (1953)',   'nara/robertson-panel.html'),
    ('NARA — Condon Committee (1966-69)','nara/condon-committee.html'),
    ('NARA story',                      'nara/story.html'),
    ('GEIPAN — Trans-en-Provence (81)', 'geipan/trans-en-provence.html'),
    ('GEIPAN — Valensole (1965)',       'geipan/valensole.html'),
    ('GEIPAN story',                    'geipan/story.html'),
    # Pacific / LAC / LatAm
    ('Chile — El Bosque (2010)',        'chile/el-bosque.html'),
    ('Chile SEFAA story',               'chile/story.html'),
    ('NZ — Kaikoura (1978)',            'nz/kaikoura.html'),
    ('NZ NZDF story',                   'nz/story.html'),
    ('Spain — Manises (1979)',          'spain/manises.html'),
    ('Spain Ejército story',            'spain/story.html'),
    ('Argentina CEFAe story',           'argentina/story.html'),
    ('Canada — Shag Harbour (1967)',    'canada/shag-harbour.html'),
    ('Canada — Falcon Lake (1967)',     'canada/falcon-lake.html'),
    ('Canada LAC story',                'canada/story.html'),
    ('Italy AM story',                  'italy/story.html'),
    ('Peru OIFAA story',                'peru/story.html'),
    ('Uruguay CRIDOVNI story',          'uruguay/story.html'),
]


# ── Builder ──────────────────────────────────────────────────────────────────

def _href(slug, depth):
    """Relative href from a page at `depth` to the site root of `slug`."""
    up = '../' * depth
    if slug is None:
        return up or './'         # root → index.html
    return f'{up}{slug}/'


def make_nav(current_slug: str, depth: int = 1, internal_links=None) -> str:
    """Return <nav> HTML — canonical structure, identical everywhere.

    current_slug  — used only to highlight the active item.
    depth         — 0 = root, 1 = mirror or root utility, 2 = story page.
    internal_links — kept for API compatibility, IGNORED (no per-page deviation).
    """
    root = _href(None, depth)

    # Pinned US archives (4 — rich content stays at top level)
    pinned_html = ''
    for name, slug, key in PINNED:
        href = _href(slug, depth)
        active = ' class="active"' if key == current_slug else ''
        pinned_html += f'<li><a href="{href}"{active}>{name}</a></li>'

    # "Site ▾" — pages about the site itself.
    site_active = any(k == current_slug for _, _, k in SITE_PAGES)
    def _site_li(name, file, k):
        cls = ' class="active"' if k == current_slug else ''
        return f'<li><a href="{root}{file}"{cls}>{name}</a></li>'
    site_items = ''.join(_site_li(n, f, k) for n, f, k in SITE_PAGES)

    # "Story ▾" — every story page across every mirror.
    cur_story_path = current_slug if current_slug and ('/' in current_slug) else ''
    story_active = any(path == cur_story_path for _, path in STORIES)
    def _story_li(label, path):
        cls = ' class="active"' if path == cur_story_path else ''
        return f'<li><a href="{root}{path}"{cls}>{label}</a></li>'
    story_items = ''.join(_story_li(l, p) for l, p in STORIES)

    # "Nations ▾" — 11 national mirrors.
    nations_active = any(slug == current_slug for _, slug in MORE)
    def _nation_li(name, slug):
        cls = ' class="active"' if slug == current_slug else ''
        return f'<li><a href="{_href(slug, depth)}"{cls}>{name}</a></li>'
    more_items = ''.join(_nation_li(n, s) for n, s in MORE)

    # NOTE: dropdowns use native <details>/<summary>. The browser handles
    # open/close natively (toggle event, ESC key, focus management). A tiny
    # JS snippet closes peers when one opens. No more stuck-open bugs.
    return f'''\
    <nav class="primary" id="primary-nav">
      <ul>
        {pinned_html}
        <li class="has-dropdown" id="nav-site-wrap">
          <details>
            <summary class="nav-more-btn{' active' if site_active else ''}" id="nav-site-btn">Site ▾</summary>
            <ul class="nav-dropdown" id="nav-site-dropdown" role="menu">
              {site_items}
            </ul>
          </details>
        </li>
        <li class="has-dropdown" id="nav-story-wrap">
          <details>
            <summary class="nav-more-btn{' active' if story_active else ''}" id="nav-story-btn">Story ▾</summary>
            <ul class="nav-dropdown" id="nav-story-dropdown" role="menu">
              {story_items}
            </ul>
          </details>
        </li>
        <li class="has-dropdown" id="nav-more-wrap">
          <details>
            <summary class="nav-more-btn{' active' if nations_active else ''}" id="nav-more-btn">Nations ▾</summary>
            <ul class="nav-dropdown" id="nav-dropdown" role="menu">
              {more_items}
            </ul>
          </details>
        </li>
      </ul>
    </nav>'''
