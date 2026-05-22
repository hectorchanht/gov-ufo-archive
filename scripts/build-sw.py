#!/usr/bin/env python3
"""Stamp the service-worker version with the current commit / timestamp.

Reads sw.js, replaces the literal `__SW_VERSION__` placeholder with a
short version stamp (git commit short SHA when available, otherwise an
ISO date), and writes the file back in place.

Run before deploying so users on previous caches get invalidated on
their next page load. Idempotent.

    python3 scripts/build-sw.py
"""
from __future__ import annotations
import os, re, subprocess, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SW   = os.path.join(REPO, 'sw.js')


def short_sha() -> str | None:
    try:
        out = subprocess.run(
            ['git', '-C', REPO, 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, check=True, timeout=3,
        ).stdout.strip()
        return out or None
    except Exception:
        return None


def main() -> int:
    if not os.path.exists(SW):
        print(f'sw.js not found at {SW}'); return 1
    src = open(SW, encoding='utf-8').read()

    # Build the version stamp: prefer git short SHA, fall back to UTC date.
    sha = short_sha()
    date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')
    new_version = (sha + '-' + date) if sha else date

    # Replace either the placeholder OR a previously-stamped const.
    # Pattern matches: const VERSION    = '<anything>';
    patched, n = re.subn(
        r"const VERSION(\s*)= '([^']*)';",
        lambda m: f"const VERSION{m.group(1)}= '{new_version}';",
        src, count=1,
    )
    if n != 1:
        print('warn: VERSION line not found in sw.js'); return 1

    if patched == src:
        print(f'sw.js already at {new_version}')
        return 0

    open(SW, 'w', encoding='utf-8').write(patched)
    print(f'sw.js stamped → {new_version}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
