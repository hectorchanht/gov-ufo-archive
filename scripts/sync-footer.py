#!/usr/bin/env python3
"""Single source of truth for the page footer.

Mirrors sync-nav.py's pattern. Each page has a footer-config table entry
that specifies (variant, depth, meta). The script calls
_site_template.make_footer() and rewrites the existing <footer>...</footer>
block in-place.

Variants:
  minimal — 1-line attribution (utility pages, story pages)
  mirror  — 3-col grid (mirror index pages)
  root    — special; index.html keeps its hand-written multi-section
            footer (war.gov branding is too specific to template). The
            script SKIPS root index.html and prints a notice.

Run:
    python3 scripts/sync-footer.py
    python3 scripts/sync-footer.py --check     # CI mode
"""
from __future__ import annotations
import os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _site_template import make_footer

# Per-page footer config. Path is repo-relative.
# (variant, depth, meta_dict)
PAGES: dict[str, tuple[str, int, dict]] = {
    # Root utility pages (depth 0)
    'search.html':   ('minimal', 0, {'archive_label': 'Search every archive'}),
    'timeline.html': ('minimal', 0, {'archive_label': 'Timeline view'}),
    'map.html':      ('minimal', 0, {'archive_label': 'Map view'}),
    'about.html':    ('minimal', 0, {'archive_label': 'About this project',
                                      'jurisdiction_text': 'MIT code · public-domain content per jurisdiction'}),
    'donate.html':   ('minimal', 0, {'archive_label': 'Support'}),
    'glossary.html': ('minimal', 0, {'archive_label': 'Glossary'}),
    'stats.html':    ('minimal', 0, {'archive_label': 'Project statistics'}),
    'foia.html':     ('minimal', 0, {'archive_label': 'FOIA quick-start'}),
    'compare.html':  ('minimal', 0, {'archive_label': 'Cross-archive comparison'}),
    '404.html':      ('minimal', 0, {'archive_label': 'Page not found'}),
}

# Story pages → minimal footer with per-page metadata
STORY_META: dict[str, dict] = {
    'aaro/tic-tac.html':        {'archive_label': 'AARO · USS Nimitz · 2004',  'source_url': 'https://www.aaro.mil/'},
    'aaro/gimbal.html':         {'archive_label': 'AARO · USS Roosevelt · 2015','source_url': 'https://www.aaro.mil/'},
    'aaro/phoenix-lights.html': {'archive_label': 'AARO · Phoenix · 1997',     'source_url': 'https://www.aaro.mil/'},
    'aaro/belgian-wave.html':   {'archive_label': 'AARO · Belgian Wave · 1989-90','source_url': 'https://www.aaro.mil/'},
    'aaro/cash-landrum.html':   {'archive_label': 'AARO · Cash–Landrum · 1980','source_url': 'https://www.aaro.mil/'},
    'aaro/coyne.html':          {'archive_label': 'AARO · Coyne · 1973',       'source_url': 'https://www.aaro.mil/'},
    'aaro/jal-1628.html':       {'archive_label': 'AARO · JAL 1628 · 1986',    'source_url': 'https://www.aaro.mil/'},
    'aaro/tehran.html':         {'archive_label': 'AARO · Tehran F-4 · 1976',  'source_url': 'https://www.aaro.mil/'},
    'aaro/travis-walton.html':  {'archive_label': 'AARO · Travis Walton · 1975','source_url': 'https://www.aaro.mil/'},
    'aaro/cash-landrum.html':   {'archive_label': 'AARO · Cash–Landrum · 1980','source_url': 'https://www.aaro.mil/'},
    'aaro/coyne.html':          {'archive_label': 'AARO · Coyne helicopter · 1973','source_url': 'https://www.aaro.mil/'},
    'aaro/jal-1628.html':       {'archive_label': 'AARO · JAL Flight 1628 · 1986','source_url': 'https://www.aaro.mil/'},
    'aaro/tehran.html':         {'archive_label': 'AARO · Tehran F-4 · 1976','source_url': 'https://www.aaro.mil/'},
    'aaro/ohare-2006.html':     {'archive_label': 'AARO · O’Hare · 2006','source_url': 'https://www.aaro.mil/'},
    'aaro/stephenville.html':   {'archive_label': 'AARO · Stephenville · 2008','source_url': 'https://www.aaro.mil/'},
    'aaro/story.html':          {'archive_label': 'AARO — full story',         'source_url': 'https://www.aaro.mil/'},
    'uk/cosford.html':          {'archive_label': 'UK MoD · Cosford/Shawbury · 1993', 'source_url': 'https://discovery.nationalarchives.gov.uk/',
                                  'jurisdiction_text': 'Open Government Licence v3'},
    'nara/mantell.html':        {'archive_label': 'NARA · Mantell · 1948',     'source_url': 'https://catalog.archives.gov/'},
    'nara/chiles-whitted.html': {'archive_label': 'NARA · Chiles-Whitted · 1948','source_url': 'https://catalog.archives.gov/'},
    'nara/mcminnville.html':    {'archive_label': 'NARA · McMinnville · 1950','source_url': 'https://catalog.archives.gov/'},
    'nara/lubbock-lights.html': {'archive_label': 'NARA · Lubbock Lights · 1951','source_url': 'https://catalog.archives.gov/'},
    'nara/levelland.html':      {'archive_label': 'NARA · Levelland · 1957',  'source_url': 'https://catalog.archives.gov/'},
    'canada/shag-harbour.html': {'archive_label': 'Canada · Shag Harbour · 1967','source_url': 'https://www.bac-lac.gc.ca/'},
    'canada/falcon-lake.html':  {'archive_label': 'Canada · Falcon Lake · 1967','source_url': 'https://www.bac-lac.gc.ca/'},
    'uk/rendlesham.html':       {'archive_label': 'UK MoD · Rendlesham · 1980','source_url': 'https://discovery.nationalarchives.gov.uk/',
                                  'jurisdiction_text': 'Open Government Licence v3'},
    'uk/story.html':            {'archive_label': 'UK MoD — full story',        'source_url': 'https://discovery.nationalarchives.gov.uk/',
                                  'jurisdiction_text': 'Open Government Licence v3'},
    'brazil/operacao-prato.html':{'archive_label':'Brazil FAB · Colares · 1977','source_url':'https://dibrarq.arquivonacional.gov.br/',
                                  'jurisdiction_text': 'Lei nº 12.527/2011 (LAI)'},
    'brazil/varginha.html':     {'archive_label': 'Brazil · Varginha · 1996',   'source_url': 'https://dibrarq.arquivonacional.gov.br/',
                                  'jurisdiction_text': 'Lei nº 12.527/2011 (LAI)'},
    'brazil/trindade.html':     {'archive_label': 'Brazil Navy · Trindade · 1958','source_url': 'https://dibrarq.arquivonacional.gov.br/',
                                  'jurisdiction_text': 'Lei nº 12.527/2011 (LAI)'},
    'brazil/story.html':        {'archive_label': 'Brazil OVNI — full story',   'source_url': 'https://dibrarq.arquivonacional.gov.br/',
                                  'jurisdiction_text': 'Lei nº 12.527/2011 (LAI)'},
    'nasa/story.html':          {'archive_label': 'NASA UAP — full story',      'source_url': 'https://science.nasa.gov/uap/'},
    'nara/story.html':          {'archive_label': 'NARA — full story',          'source_url': 'https://www.archives.gov/research/topics/uaps'},
    'nara/roswell.html':        {'archive_label': 'NARA · Roswell · 1947',      'source_url': 'https://catalog.archives.gov/'},
    'nara/socorro.html':        {'archive_label': 'NARA · Socorro · 1964',      'source_url': 'https://catalog.archives.gov/'},
    'nara/robertson-panel.html':{'archive_label':'NARA · Robertson Panel · 1953','source_url': 'https://catalog.archives.gov/'},
    'nara/condon-committee.html':{'archive_label':'NARA · Condon · 1966-69',    'source_url': 'https://catalog.archives.gov/'},
    'geipan/story.html':        {'archive_label': 'GEIPAN — full story',        'source_url': 'https://www.cnes-geipan.fr/',
                                  'jurisdiction_text': 'Loi nº 78-753 (Information Publique)'},
    'geipan/trans-en-provence.html':{'archive_label':'GEIPAN · Trans-en-Provence · 1981','source_url':'https://www.cnes-geipan.fr/',
                                      'jurisdiction_text': 'Loi nº 78-753 (Information Publique)'},
    'geipan/valensole.html':    {'archive_label': 'GEIPAN · Valensole · 1965',  'source_url': 'https://www.cnes-geipan.fr/',
                                  'jurisdiction_text': 'Loi nº 78-753 (Information Publique)'},
    'chile/story.html':         {'archive_label': 'Chile SEFAA — full story',   'source_url': 'https://sefaa.dgac.gob.cl/',
                                  'jurisdiction_text': 'Ley nº 20.285'},
    'chile/el-bosque.html':     {'archive_label': 'Chile · El Bosque · 2010',   'source_url': 'https://sefaa.dgac.gob.cl/',
                                  'jurisdiction_text': 'Ley nº 20.285'},
    'argentina/story.html':     {'archive_label': 'Argentina CEFAe — full story','source_url': 'https://www.argentina.gob.ar/fuerzaaerea/cefae',
                                  'jurisdiction_text': 'Ley nº 27.275'},
    'canada/story.html':        {'archive_label': 'Canada LAC — full story',    'source_url': 'https://www.bac-lac.gc.ca/'},
    'italy/story.html':         {'archive_label': 'Italy AM — full story',      'source_url': 'https://www.aeronautica.difesa.it/',
                                  'jurisdiction_text': 'D.lgs. 33/2013 (FOIA)'},
    'nz/story.html':            {'archive_label': 'NZ NZDF — full story',       'source_url': 'https://www.nzdf.mil.nz/'},
    'nz/kaikoura.html':         {'archive_label': 'NZ · Kaikoura · 1978',       'source_url': 'https://www.nzdf.mil.nz/'},
    'peru/story.html':          {'archive_label': 'Peru OIFAA — full story',    'source_url': 'https://www.gob.pe/fap'},
    'spain/story.html':         {'archive_label': 'Spain Ejército — full story','source_url': 'https://ejercitodelaire.defensa.gob.es/',
                                  'jurisdiction_text': 'Ley 19/2013 (Transparencia)'},
    'spain/manises.html':       {'archive_label': 'Spain · Manises · 1979',     'source_url': 'https://ejercitodelaire.defensa.gob.es/',
                                  'jurisdiction_text': 'Ley 19/2013 (Transparencia)'},
    'uruguay/story.html':       {'archive_label': 'Uruguay CRIDOVNI — full story','source_url': 'https://www.fau.mil.uy/',
                                  'jurisdiction_text': 'Ley nº 18.381'},
}
for path, m in STORY_META.items():
    PAGES[path] = ('minimal', 1, m)

# Pages to leave alone (rich, hand-tuned footers)
SKIP_PATHS = {
    'index.html',                # War.gov landing — keeps its multi-section branded footer
    # aaro/index.html removed (Plan 04-17): Astro owns the route now; the
    # legacy aaro/index.html is deleted in this plan. sync-footer.py
    # never sees the file.
    # nasa/index.html removed (Plan 04-16): Astro owns the route now; the
    # legacy nasa/index.html is deleted in this plan. sync-footer.py
    # never sees the file.
    # nara/index.html removed (Plan 04-15): Astro owns the route now; the
    # legacy nara/index.html is deleted in this plan. sync-footer.py
    # never sees the file.
    'geipan/index.html',
    'uk/index.html',
    'brazil/index.html',
    'chile/index.html',
    'canada/index.html', 'argentina/index.html',
    'peru/index.html', 'spain/index.html', 'italy/index.html',
    'aaro/details.html',         # rebuilt by build-details.py
}

FOOTER_RE = re.compile(r'<footer\b[^>]*>[\s\S]*?</footer>', re.M)


def main(check: bool = False) -> int:
    drift, updated, missing = [], [], []
    for rel_path, (variant, depth, meta) in PAGES.items():
        full = os.path.join(REPO, rel_path)
        if rel_path in SKIP_PATHS or not os.path.isfile(full):
            missing.append(rel_path); continue
        src = open(full, encoding='utf-8').read()
        m = FOOTER_RE.search(src)
        if not m:
            missing.append(rel_path); continue
        new_footer = make_footer(variant, depth, meta).rstrip()
        if m.group(0).strip() == new_footer.strip():
            continue
        if check:
            drift.append(rel_path); continue
        new_src = FOOTER_RE.sub(new_footer, src, count=1)
        with open(full, 'w', encoding='utf-8') as f:
            f.write(new_src)
        updated.append(rel_path)

    if check:
        if drift:
            print(f'FOOTER DRIFT in {len(drift)} files:')
            for p in drift: print(f'  {p}')
            return 1
        print(f'No footer drift across {len(PAGES)} configured pages.')
        return 0

    print(f'Updated {len(updated)} files; {len(missing)} skipped (missing file or in SKIP_PATHS).')
    for p in updated[:20]: print(f'  ✓ {p}')
    if len(updated) > 20: print(f'  … and {len(updated) - 20} more')
    return 0


if __name__ == '__main__':
    sys.exit(main(check='--check' in sys.argv))
