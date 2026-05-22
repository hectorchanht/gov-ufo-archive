#!/usr/bin/env python3
"""Extract plain-text from every locally-mirrored PDF.

Uses `pdftotext` (poppler-utils) — available on every Linux runner via
`apt install poppler-utils` and on macOS via `brew install poppler`. For
each `<archive>/pdfs/*.pdf` we emit `<archive>/.pdftext/<basename>.txt`
containing the extracted UTF-8 text.

The output is consumed by scripts/build-pages-index.py (a later step) to
fold body text into the Lunr search index — turning the cross-archive
search into a true full-text search.

Skips files that already have a fresher text companion (mtime-based) so
CI re-runs are cheap.

Usage:
    python3 scripts/extract-pdf-text.py                    # all archives
    python3 scripts/extract-pdf-text.py aaro nara          # specific archives
    python3 scripts/extract-pdf-text.py --force            # ignore mtime cache
"""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
import time
from typing import List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARCHIVES = [
    'wargov', 'aaro', 'nasa', 'nara',
    'geipan', 'uk', 'brazil', 'chile',
    'argentina', 'canada', 'italy', 'nz',
    'peru', 'spain', 'uruguay',
]


def archive_pdf_dir(slug: str) -> str:
    if slug == 'wargov':
        return os.path.join(ROOT, 'bundles', 'Release_1')
    return os.path.join(ROOT, slug, 'pdfs')


def archive_text_dir(slug: str) -> str:
    if slug == 'wargov':
        return os.path.join(ROOT, 'bundles', '.pdftext')
    return os.path.join(ROOT, slug, '.pdftext')


def needs_refresh(pdf: str, txt: str) -> bool:
    if not os.path.exists(txt):
        return True
    try:
        return os.path.getmtime(pdf) > os.path.getmtime(txt)
    except OSError:
        return True


def extract_one(pdf: str, txt: str, timeout: int = 90) -> tuple[bool, str]:
    """Run pdftotext on a single file. Returns (ok, message)."""
    os.makedirs(os.path.dirname(txt), exist_ok=True)
    cmd = ['pdftotext', '-layout', '-enc', 'UTF-8', '-nopgbrk', pdf, txt]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except FileNotFoundError:
        return False, 'pdftotext not installed'
    except subprocess.TimeoutExpired:
        return False, f'timeout after {timeout}s'
    if proc.returncode != 0:
        return False, (proc.stderr or b'').decode('utf-8', 'replace').strip()[:100]
    # Empty output is a soft failure (image-only scan); leave the empty file
    # in place so we don't keep retrying.
    return True, ''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('archives', nargs='*', help='archive slugs (default: all)')
    ap.add_argument('--force', action='store_true', help='ignore mtime cache')
    ap.add_argument('--timeout', type=int, default=90, help='per-file seconds')
    args = ap.parse_args()

    if not shutil.which('pdftotext'):
        print('FATAL: pdftotext not on PATH. Install via:')
        print('  apt install -y poppler-utils      # Debian/Ubuntu')
        print('  brew install poppler              # macOS')
        return 2

    slugs = args.archives or ARCHIVES
    total = ok_count = skipped = failed = 0
    start = time.monotonic()

    for slug in slugs:
        pdf_dir = archive_pdf_dir(slug)
        txt_dir = archive_text_dir(slug)
        if not os.path.isdir(pdf_dir):
            print(f'  · {slug:10s} no PDFs dir at {os.path.relpath(pdf_dir)}')
            continue
        pdfs = sorted(glob.glob(os.path.join(pdf_dir, '*.pdf')))
        if not pdfs:
            print(f'  · {slug:10s} empty PDF dir')
            continue
        s_ok = s_skip = s_fail = 0
        for pdf in pdfs:
            base = os.path.basename(pdf)[:-4] + '.txt'
            txt = os.path.join(txt_dir, base)
            total += 1
            if not args.force and not needs_refresh(pdf, txt):
                s_skip += 1; skipped += 1
                continue
            ok, msg = extract_one(pdf, txt, timeout=args.timeout)
            if ok:
                s_ok += 1; ok_count += 1
            else:
                s_fail += 1; failed += 1
                print(f'    ! {os.path.basename(pdf)} — {msg}')
        print(f'  {slug:10s} {s_ok:4d} extracted · {s_skip:4d} cached · {s_fail:3d} failed  ({len(pdfs)} pdfs)')

    elapsed = time.monotonic() - start
    print(f'\n→ total {total} PDFs · {ok_count} extracted · {skipped} cached · {failed} failed in {elapsed:.1f}s')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
