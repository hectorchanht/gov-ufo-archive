"""Helper for build scripts to rewrite asset URLs through GH releases.

Reads release-manifest.json (basename → release-download URL) and provides:
  apply_manifest(assets, key_map) — mutates assets in-place, swapping the
  primary URL field to the release URL when basename matches.

Convention: the "primary URL" key is u (short form) or url (long form).
Original source URL stays in s/src.
"""
from __future__ import annotations
import json, os
from urllib.parse import urlparse, unquote

REPO     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, 'release-manifest.json')


def _basename(url: str) -> str:
    if not url: return ''
    return unquote(urlparse(url).path.rsplit('/', 1)[-1].split('?', 1)[0].split('#', 1)[0])


def load_manifest() -> dict:
    if not os.path.exists(MANIFEST):
        return {'pdfs': {}, 'videos': {}}
    return json.load(open(MANIFEST, encoding='utf-8'))


def apply_manifest(assets: list, *, url_key: str = 'u', src_key: str = 's', local_key: str = 'l') -> int:
    """Mutate assets so url_key points to the release URL when basename matches.
    Original URL preserved in src_key if it wasn't already set.
    Returns count of assets swapped.
    """
    man = load_manifest()
    lookup = {}
    lookup.update(man.get('pdfs', {}))
    lookup.update(man.get('videos', {}))
    swapped = 0
    for a in assets:
        u = a.get(url_key, '')
        if not u: continue
        bn = _basename(u)
        if bn and bn in lookup:
            rel_url = lookup[bn]
            if rel_url == u: continue   # already release URL
            # preserve original as src if src is empty or same as u
            if not a.get(src_key):
                a[src_key] = u
            a[url_key] = rel_url
            # local pointer = release URL so Download button uses release
            if not a.get(local_key):
                a[local_key] = rel_url
            swapped += 1
    return swapped
