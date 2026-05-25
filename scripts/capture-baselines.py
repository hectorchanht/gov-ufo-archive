#!/usr/bin/env python3
# Generated input for the Phase 2 visual-regression gate. See .planning/REQUIREMENTS.md INF-04.
"""Capture the 60 visual-regression baselines for realufo.org.

Walks the canonical 15-archive slug list (CLAUDE.md §2) × 4 viewports
(D-14: 360 / 768 / 1024 / 1440), drives headless chromium via Playwright,
and writes one PNG per (archive, viewport) under
`tests/visual-baselines/<slug>-<width>.png`.

Why: Per CONTEXT D-12, Phase 2 freezes the current production-rendered
pixels (https://realufo.org via GitHub Pages) as the regression target
that every Phase 3-5 CF Pages preview MUST match within 0.1 %
(D-16). The baselines are committed as raw PNGs (D-13). The Playwright
test runner (`tests/visual-regression.spec.ts`) compares the preview
deployment against these baselines on every PR.

D-17 invariant — NEVER auto-regen. This script overwrites existing
PNGs when re-run. CI workflows MUST NEVER invoke it; only an operator
intentionally acknowledging a visual change should regenerate baselines.
See `tests/visual-baselines/README.md` for the explicit recapture
procedure.

CLI:
    python3 scripts/capture-baselines.py                   # capture all 60
    python3 scripts/capture-baselines.py --archive aaro    # one archive × 4 viewports
    python3 scripts/capture-baselines.py --viewport 360    # all 15 archives at 360 px
    python3 scripts/capture-baselines.py --check           # exit 1 if any PNG missing
    python3 scripts/capture-baselines.py --base-url https://realufo.org  # override

`--check` walks `tests/visual-baselines/` and asserts every expected
`<slug>-<width>.png` exists with size > 0. Useful from CI when verifying
the operator-committed baselines are intact (does NOT recapture).

Exit codes:
    0 — captured successfully (or `--check` found all 60).
    1 — `--check` found gaps OR a capture failed mid-run.
    2 — dependency missing (no `playwright` module — run `pip install playwright==1.49.0`).

Stdlib only — `argparse`, `os`, `sys`, `pathlib`. Third-party `playwright`
loaded lazily so `--check` and `--help` work without it. Matches the
CONVENTIONS.md §"Python Conventions (Build Scripts)" pattern: stdlib +
targeted libs only; no BeautifulSoup, no lxml.

Runtime note: The Python `playwright` bindings are NOT a project dev-dep
(those are TypeScript via pnpm — see `package.json`). The capture script
is operator-run on demand; the operator installs `playwright==1.49.0` in
a venv before running. Python 3.11 venv recommended (newer Pythons may
have wheel-build issues with greenlet — see README).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO / 'tests' / 'visual-baselines'
DEFAULT_BASE = 'https://realufo.org'

# Canonical archive slug list. Source: CLAUDE.md §2 (15 archives). The wargov
# landing page lives at `/` (historical: it predates the others); every other
# archive lives at `/<slug>/`. Keep order stable so `--check` output is sortable.
ARCHIVES: list[tuple[str, str]] = [
    ('wargov', '/'),
    ('aaro', '/aaro/'),
    ('nasa', '/nasa/'),
    ('nara', '/nara/'),
    ('geipan', '/geipan/'),
    ('uk', '/uk/'),
    ('brazil', '/brazil/'),
    ('chile', '/chile/'),
    ('argentina', '/argentina/'),
    ('canada', '/canada/'),
    ('italy', '/italy/'),
    ('nz', '/nz/'),
    ('peru', '/peru/'),
    ('spain', '/spain/'),
    ('uruguay', '/uruguay/'),
]

# Viewport list per D-14. Order matters: 360 first because CLAUDE.md §8 mandates
# mobile-first — the 360 px viewport is the canonical baseline, not the last.
VIEWPORTS: list[tuple[int, int]] = [
    (360, 800),
    (768, 1024),
    (1024, 768),
    (1440, 900),
]


def expected_files() -> list[Path]:
    """Return the 60 expected baseline paths in stable order."""
    out = []
    for slug, _ in ARCHIVES:
        for w, _ in VIEWPORTS:
            out.append(OUTPUT_DIR / f'{slug}-{w}.png')
    return out


def run_check() -> int:
    """`--check` mode: verify every expected PNG exists and is non-empty."""
    missing: list[Path] = []
    empty: list[Path] = []
    for path in expected_files():
        if not path.exists():
            missing.append(path)
        elif path.stat().st_size == 0:
            empty.append(path)
    total = len(expected_files())
    present = total - len(missing) - len(empty)
    if missing or empty:
        for p in missing:
            print(f'  [missing]  {p.relative_to(REPO)}')
        for p in empty:
            print(f'  [empty]    {p.relative_to(REPO)}')
        print(f'{present} / {total} baselines present ({len(missing)} missing, {len(empty)} empty)')
        return 1
    print(f'{present} / {total} baselines present')
    return 0


def run_capture(archives_filter: str | None, viewport_filter: int | None,
                base_url: str, full_page: bool) -> int:
    """Drive Playwright + chromium to capture the requested matrix."""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        print('error: `playwright` module not installed.', file=sys.stderr)
        print('       run: pip install playwright==1.49.0 && playwright install chromium',
              file=sys.stderr)
        print('       (python 3.11 venv recommended — see tests/visual-baselines/README.md)',
              file=sys.stderr)
        return 2

    archives = [(s, p) for s, p in ARCHIVES if archives_filter is None or s == archives_filter]
    if archives_filter and not archives:
        print(f'error: unknown --archive {archives_filter!r}; valid: '
              f'{", ".join(s for s, _ in ARCHIVES)}', file=sys.stderr)
        return 1
    viewports = [(w, h) for w, h in VIEWPORTS if viewport_filter is None or w == viewport_filter]
    if viewport_filter and not viewports:
        print(f'error: unknown --viewport {viewport_filter!r}; valid: '
              f'{", ".join(str(w) for w, _ in VIEWPORTS)}', file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    captured = 0
    failed: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for slug, path in archives:
            for w, h in viewports:
                # `javaScriptEnabled=True` is the default; we capture the
                # fully-rendered hydrated page (D-12 — what real users see).
                # The JS-off variant lives in Plan 02-06 (tests/js-off.spec.ts).
                ctx = browser.new_context(
                    viewport={'width': w, 'height': h},
                    java_script_enabled=True,
                )
                page = ctx.new_page()
                url = base_url.rstrip('/') + path
                out = OUTPUT_DIR / f'{slug}-{w}.png'
                try:
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    page.wait_for_selector('body', state='visible', timeout=10000)
                    # 500 ms settle: CLAUDE.md §3 hero carousel sets a 6500 ms
                    # autoplay interval. 500 ms ensures slide 1 is stable but
                    # not yet rotated. Empirically deterministic at networkidle.
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(out), full_page=full_page)
                    size = out.stat().st_size
                    print(f'  [ok]    {slug}-{w}.png ({size} B)')
                    captured += 1
                except Exception as exc:
                    print(f'  [fail]  {slug}-{w}.png — {exc!r}', file=sys.stderr)
                    failed.append(f'{slug}-{w}')
                    # rm partial file so --check correctly reports gap
                    if out.exists() and out.stat().st_size == 0:
                        try:
                            out.unlink()
                        except OSError:
                            pass
                finally:
                    ctx.close()
        browser.close()

    print(f'wrote {captured} baselines')
    if failed:
        print(f'FAILED: {len(failed)} captures — {", ".join(failed)}', file=sys.stderr)
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description='Capture realufo.org visual-regression baselines. '
                    'D-17: NEVER invoke from CI — operator-only.')
    p.add_argument('--archive', type=str, default=None,
                   help='Capture only this archive slug (all 4 viewports).')
    p.add_argument('--viewport', type=int, default=None,
                   help='Capture only this viewport width (all 15 archives).')
    p.add_argument('--check', action='store_true',
                   help='Verify all 60 baselines exist and are non-empty. Exit 1 on gaps.')
    p.add_argument('--base-url', type=str, default=DEFAULT_BASE,
                   help=f'Capture source (default: {DEFAULT_BASE}). D-12 forbids preview/localhost.')
    p.add_argument('--full-page', action='store_true',
                   help='Capture full page instead of above-the-fold (default: above-the-fold only).')
    args = p.parse_args()

    if args.check:
        return run_check()
    return run_capture(args.archive, args.viewport, args.base_url, args.full_page)


if __name__ == '__main__':
    sys.exit(main())
