#!/usr/bin/env python3
"""Idempotent patcher: ensure every HTML SW registration carries
``updateViaCache: 'none'``.

Walks every tracked ``*.html`` (per ``git ls-files '*.html'``) and rewrites
``navigator.serviceWorker.register("/sw.js")`` → ``navigator.serviceWorker.register("/sw.js", { updateViaCache: 'none' })``.

Why this exists
---------------
Per ``.planning/research/PITFALLS.md`` Pitfall #1 mitigation #2 (and
``ROADMAP.md`` Phase 6 success criterion 2), without ``updateViaCache:
'none'`` the browser HTTP-caches ``sw.js`` for up to 24 h regardless of
the SW's own cache-control semantics — returning users keep getting
the OLD versioned-shell SW for hours-to-days after a kill-switch deploy,
defeating the 14-day Phase 6 countdown the kill-switch is supposed to
bound (``.planning/phases/01-pre-migration-safety/01-CONTEXT.md`` D-08).

Idempotency
-----------
The substitution checks for the literal pre-patch shape; a file already
carrying the option is skipped untouched. Re-running prints ``patched=0``.

Constraints
-----------
* Stdlib only (``subprocess``, ``pathlib``, ``sys``).
* Never touches anything outside ``git ls-files '*.html'`` (no
  node_modules/, no .git/, no untracked HTML files).
* Never touches ``sw.js``, ``manifest.webmanifest``, or
  ``scripts/build-sw.py`` — those are Task 1's surface.

Usage::

    python3 scripts/patch-sw-registration.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BEFORE = 'navigator.serviceWorker.register("/sw.js")'
AFTER = "navigator.serviceWorker.register(\"/sw.js\", { updateViaCache: 'none' })"
GUARD = "updateViaCache"  # presence of this substring → already patched


def tracked_html_files() -> list[Path]:
    """Enumerate tracked HTML files via git (CLAUDE.md §6.2 convention)."""
    result = subprocess.run(
        ["git", "ls-files", "*.html"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [Path(p) for p in result.stdout.split() if p]


def main() -> int:
    files = tracked_html_files()

    patched = 0
    already_ok = 0
    no_register = 0

    for path in files:
        text = path.read_text(encoding="utf-8")

        if BEFORE not in text:
            # File either has no SW registration OR already carries the option.
            if GUARD in text and AFTER in text:
                already_ok += 1
            else:
                no_register += 1
            continue

        new_text = text.replace(BEFORE, AFTER)
        if new_text == text:
            # Paranoia guard: substitution somehow no-op'd despite BEFORE being
            # found. Treat as nothing-to-do and move on (don't mis-report).
            no_register += 1
            continue

        path.write_text(new_text, encoding="utf-8")
        patched += 1

    total = len(files)
    print(
        f"patched={patched} already_ok={already_ok} "
        f"no_register={no_register} total={total}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
