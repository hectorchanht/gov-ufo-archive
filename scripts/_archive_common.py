"""Shared helpers for Phase 4 archive normalisers.

Two public exports:

  * ``R2_BASE`` — module constant ``"https://assets.realufo.org"``. The
    custom-domain front of the Cloudflare R2 bucket ``realufo`` per
    `.planning/phases/04-full-migration-search-offline-performance/04-CONTEXT.md`
    decisions D-01..D-06.
  * ``rewrite_to_r2(local_path, archive_slug, asset_type)`` — rewrite a
    repo-relative or remote URL into the R2 URL contract
    ``{R2_BASE}/{asset_type}/{archive_slug}/{basename}``. Image-extension
    inputs are returned as-is per D-01 refinement + Pitfall #7
    (thumbnails stay local so Astro Image can process them).
  * ``slugify(text)`` — byte-equivalent port of
    ``scripts/snapshot-urls.py:slugify`` (which mirrors
    ``scripts/normalize-csv.py:_slugify``). Single source of truth for
    Wave 3+ per-archive normalisers so card anchor IDs stay synced with
    ``URL-CONTRACT.txt``.

Why ``_archive_common.py`` and not ``_r2_urls.py`` (as 04-RESEARCH.md §4
sketched): Wave 3+ archive normalisers will accumulate other shared
helpers (per-archive ``Source`` URL maps, common CSV-row schema
normalisation, etc.). One module to import is friendlier than fifteen
slug-keyed modules.

Pure stdlib (``re`` only); zero I/O, zero global mutation; safe to call
from any normaliser without side-effects. Matches the
``stdlib-only except curl_cffi`` convention from CLAUDE.md §6.2.

### Threat mitigations

- **T-04-05** (R2 token leak): this helper does NOT touch credentials.
  Token-handling is GH Actions ``r2-sync.yml`` scope only.
- **T-04-08** (CORS misconfiguration): irrelevant here — the helper
  emits URLs against the bound custom-domain origin which the bucket's
  CORS rules (operator-applied via ``wrangler r2 bucket cors set``)
  already restrict to ``https://realufo.org`` + preview origins.

### Cross-references

- ``.planning/decisions/r2-setup.md`` — bucket name, custom domain,
  secrets, A3 thumbnail decision.
- ``.planning/phases/04-full-migration-search-offline-performance/04-RESEARCH.md``
  §4 — URL pattern + bulk-migration rclone recipe.
- ``scripts/snapshot-urls.py`` — slugify source-of-truth.
- ``scripts/normalize-csv.py`` — first consumer; Wave 3+ archive
  normalisers will follow the same import pattern.
"""
from __future__ import annotations

import re

# Custom-domain front for the Cloudflare R2 bucket `realufo`
# (.planning/decisions/r2-setup.md). Constant — NOT configurable per
# environment; preview and production both serve from this origin so
# preview-vs-prod URL drift is impossible.
R2_BASE: str = 'https://assets.realufo.org'

# Image extensions are preserved verbatim per D-01 refinement + Pitfall
# #7. Astro Image processes LOCAL files for responsive srcset + format
# conversion; pushing thumbnails to R2 loses that path. The CSV may
# still hand the normaliser a `.png`/`.jpg`/`.webp`/`.svg` URL — in
# that case the helper returns the input untouched so downstream code
# preserves the original URL (already a stable origin like
# `https://www.war.gov/medialink/...`).
_IMAGE_EXTS: frozenset[str] = frozenset({
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.avif', '.bmp',
})

# Byte-for-byte port of `scripts/snapshot-urls.py:158-167` and
# `scripts/normalize-csv.py:117-119` (`_SLUG_RE`).
_SLUG_RE = re.compile(r'[^a-z0-9]+')


def rewrite_to_r2(local_path: str, archive_slug: str, asset_type: str) -> str:
    """Rewrite a binary asset URL/path to the R2 custom-domain URL.

    Parameters
    ----------
    local_path : str
        Either a repo-relative path (``bundles/Release_1/foo.pdf``) or
        an absolute URL (``https://www.war.gov/medialink/.../foo.pdf``).
        The basename after the final ``/`` is extracted; everything
        else is discarded.
    archive_slug : str
        One of the 15 archive slugs (``wargov``, ``aaro``, ``nasa``,
        ``nara``, ``geipan``, ``uk``, ``brazil``, ``chile``,
        ``argentina``, ``canada``, ``italy``, ``nz``, ``peru``,
        ``spain``, ``uruguay``).
    asset_type : str
        ``'pdfs'`` or ``'videos'``. Maps to the R2 prefix path per
        D-05 (single bucket, prefix-based layout).

    Returns
    -------
    str
        Empty string if ``local_path`` is falsy. Original input if
        ``local_path`` ends with an image extension (per D-01
        refinement — thumbnails stay local for Astro Image). Otherwise
        ``f"{R2_BASE}/{asset_type}/{archive_slug}/{basename}"``.

    Notes
    -----
    The function does NOT verify the file actually exists in R2 — it
    is a pure URL transform. Existence is asserted by
    ``tests/r2-urls.spec.ts`` (post-migration HEAD-check sample).

    Examples
    --------
    >>> rewrite_to_r2('bundles/Release_1/foo.pdf', 'wargov', 'pdfs')
    'https://assets.realufo.org/pdfs/wargov/foo.pdf'
    >>> rewrite_to_r2(
    ...     'https://www.war.gov/medialink/ufo/release_1/dow-uap-d10.pdf',
    ...     'wargov', 'pdfs')
    'https://assets.realufo.org/pdfs/wargov/dow-uap-d10.pdf'
    >>> rewrite_to_r2('aaro/videos/y.mp4', 'aaro', 'videos')
    'https://assets.realufo.org/videos/aaro/y.mp4'
    >>> rewrite_to_r2('', 'wargov', 'pdfs')
    ''
    >>> rewrite_to_r2('thumbs/a.png', 'wargov', 'pdfs')
    'thumbs/a.png'
    """
    if not local_path:
        return ''
    # Image extensions stay local (D-01 refinement + Pitfall #7).
    # Lowercase ext check tolerates `.PNG`, `.Jpg`, etc.
    lower = local_path.lower()
    # Strip any query-string / fragment before extension check so that
    # `foo.png?cb=1` still triggers the image-preservation path.
    bare = lower.split('?', 1)[0].split('#', 1)[0]
    for ext in _IMAGE_EXTS:
        if bare.endswith(ext):
            return local_path
    filename = local_path.rsplit('/', 1)[-1]
    return f'{R2_BASE}/{asset_type}/{archive_slug}/{filename}'


def slugify(text: str) -> str:
    """Reduce free text to the stable ``#card-<slug>`` anchor form.

    Byte-equivalent port of ``scripts/snapshot-urls.py:158-167`` so the
    ``card-<slug>`` ids in shard HTML match the anchors recorded in
    ``URL-CONTRACT.txt`` (Phase 2 PMS-01 drift gate). Wave 3+ archive
    normalisers MUST import this function rather than re-implementing
    — drift between two ports of the same algorithm is the cheapest
    way to break ``URL-CONTRACT.txt`` for half the archives.

    Rules (verbatim from snapshot-urls.py):
      1. Lowercase the input.
      2. Replace runs of non-``[a-z0-9]`` with a single ``-``.
      3. Strip leading/trailing ``-``.
      4. Truncate to 80 chars.
      5. Strip again (truncation may leave a trailing ``-``).

    Examples
    --------
    >>> slugify('Hello World 2024!')
    'hello-world-2024'
    >>> slugify('  Multiple   spaces — em-dash  ')
    'multiple-spaces-em-dash'
    >>> slugify('')
    ''
    """
    if not text:
        return ''
    s = _SLUG_RE.sub('-', text.lower()).strip('-')
    return s[:80].strip('-')
