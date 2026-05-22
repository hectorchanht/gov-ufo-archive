#!/usr/bin/env python3
"""Insert a dated sync entry directly under the [Unreleased] header in
CHANGELOG.md. No-ops if the dated entry already exists.

Used by .github/workflows/scrape.yml after every weekly auto-rebuild.
"""
from __future__ import annotations
import datetime as _dt
from pathlib import Path

CHANGELOG = Path('CHANGELOG.md')
DATE = _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%d')
MARKER = f'## [sync-{DATE}]'

def main() -> None:
    if not CHANGELOG.exists():
        return
    src = CHANGELOG.read_text(encoding='utf-8')
    if MARKER in src:
        return
    stamp = (
        f'{MARKER}\n\n'
        '- Weekly automated sync: scrapers + spider + API + feeds rebuilt.\n\n'
    )
    src = src.replace(
        '## [Unreleased]',
        '## [Unreleased]\n\n' + stamp,
        1,
    )
    CHANGELOG.write_text(src, encoding='utf-8')

if __name__ == '__main__':
    main()
