"""Canonical footer builder + source-link helper.

Public surface:
    make_footer(variant, depth, meta)            — 1-line / mirror / root variants
    make_footer_sources(source_links, ...)       — multi-column source-list footer

scripts/sync-footer.py walks every hand-written HTML page (root + utility
+ story) and rewrites its <footer> block to make_footer() output. Mirror
build scripts can call make_footer_sources() for their per-archive
sources block. CI gate: .github/workflows/sync-footer.yml.
"""
from __future__ import annotations

# nav._href is used by make_footer_sources for cross-site relative URLs.
from .nav import _href


def make_footer(variant: str = 'minimal', depth: int = 1, meta: dict | None = None) -> str:
    """Three variants share the same wrapper.

      variant="minimal" → 1-line attribution (utility + story pages)
      variant="mirror"  → 3-col grid (archive, related, jurisdiction)
      variant="root"    → multi-section war.gov branding (root index.html only)

    Caller supplies `meta` dict with optional keys:
      archive_label, source_url, source_label, jurisdiction_text,
      related (list[(label, href)]), coords, agency_blurb.
    """
    meta = meta or {}
    up = '../' * depth
    root = up or './'

    if variant == 'minimal':
        archive = meta.get('archive_label', '')
        src_url = meta.get('source_url', '')
        src_lbl = meta.get('source_label', src_url.replace('https://', '').rstrip('/'))
        jur     = meta.get('jurisdiction_text', '17 U.S.C. § 105')
        bits    = [f'<a href="{root}">realufo.org</a>']
        if archive: bits.append(archive)
        bits.append(jur)
        if src_url:
            bits.append(f'Mirrored from <a href="{src_url}" target="_blank" rel="noopener">{src_lbl}</a>')
        return f'<footer>\n  <p>{" · ".join(bits)}</p>\n</footer>'

    if variant == 'mirror':
        archive = meta.get('archive_label', 'Archive')
        src_url = meta.get('source_url', '')
        src_lbl = meta.get('source_label', src_url.replace('https://', '').rstrip('/'))
        jur     = meta.get('jurisdiction_text', '17 U.S.C. § 105 — public domain')
        related = meta.get('related', [])
        rel_html = ''.join(f'<li><a href="{href}">{label}</a></li>' for label, href in related)
        rel_block = f'<div><h4>Related</h4><ul>{rel_html}</ul></div>' if rel_html else ''
        src_block = (
            f'<div><h4>Original source</h4>'
            f'<p><a href="{src_url}" target="_blank" rel="noopener">{src_lbl}</a></p>'
            f'<p style="color:var(--ink-faint);font-size:10px;margin-top:6px">{jur}</p></div>'
        ) if src_url else ''
        return (
            '<footer>\n  <div class="container">\n'
            f'    <div><h4>{archive}</h4><p>Offline archival mirror — <a href="{root}">realufo.org</a></p></div>\n'
            f'    {rel_block}\n'
            f'    {src_block}\n'
            '  </div>\n</footer>'
        )

    if variant == 'root':
        # Caller is expected to override with rich branded markup; this is a
        # minimal scaffold that the canonical index.html replaces wholesale.
        coords = meta.get('coords', '')
        blurb  = meta.get('agency_blurb', 'realufo.org — every official government UAP archive in one place.')
        return (
            '<footer>\n  <div class="container">\n'
            f'    <div><h4>realufo.org</h4><p>{blurb}</p>'
            f'<p style="color:var(--ink-faint);font-size:10px">{coords}</p></div>\n'
            '  </div>\n</footer>'
        )

    raise ValueError(f'unknown footer variant: {variant}')


def make_footer_sources(source_links, license_text: str = '', colophon: str = ''):
    """Return multi-column source-list footer for mirror pages.

    source_links — list of (label, url) for official sources.
    """
    links_html = '\n'.join(
        f'<li><a href="{url}" target="_blank" rel="noopener">{label}</a></li>'
        for label, url in source_links
    )
    sites_html = ''.join(
        f'<li><a href="{_href(slug, 1)}">{name}</a></li>'
        for name, slug in [
            ('War.gov / UFO', None), ('AARO', 'aaro'), ('NASA', 'nasa'),
            ('NARA', 'nara'), ('GEIPAN', 'geipan'), ('UK Archives', 'uk'),
            ('Brazil FAB', 'brazil'), ('Chile CEFAA', 'chile'),
        ]
    )
    return f'''\
<footer>
  <div class="container">
    <div>
      <h4>Official Sources</h4>
      <ul>{links_html}</ul>
    </div>
    <div>
      <h4>All Sites</h4>
      <ul>{sites_html}</ul>
    </div>
    <div>
      <h4>Project</h4>
      <ul>
        <li><a href="https://realufo.org/">realufo.org</a></li>
        <li><a href="https://github.com/hectorchanht/war-gov-ufo-release">GitHub</a></li>
      </ul>
      {f'<p style="margin-top:14px;font-size:10px;color:var(--ink-faint);line-height:1.6;">{license_text}</p>' if license_text else ''}
    </div>
    <div class="colophon">{colophon if colophon else 'All content is sourced from official government archives and is in the public domain.'}</div>
  </div>
</footer>'''
