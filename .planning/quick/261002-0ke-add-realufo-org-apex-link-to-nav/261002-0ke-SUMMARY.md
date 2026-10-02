---
phase: quick-261002-0ke
plan: 01
status: complete
subsystem: nav
tags: [nav, astro, cross-site]
key-files:
  modified:
    - src/components/Nav.astro
decisions:
  - "Apex link label 'RealUFO' with aria-hidden ↗, same-tab, placed last in nav.primary ul"
metrics:
  completed: 2026-10-02
  tasks: 1
  files: 1
---

# Quick 261002-0ke: Add realufo.org apex link to nav Summary

One `<li><a href="https://realufo.org/" data-external="apex">RealUFO <span aria-hidden="true">↗</span></a></li>` appended after `<slot name="nav-extra" />` in the shared `Nav.astro`. It shows up in the desktop nav and the mobile drawer on every page that uses RootLayout. The header comment now records this one link as the exception to the "no ↗ in header" rule (§11).

## Commits

- a3aa27b: feat(nav): add RealUFO apex link to header nav

## Verification (observed)

- `pnpm build`: exit 0 (postbuild, Pagefind, sitemap 67 urls, watchdog.json all ran).
- `href="https://realufo.org/"` count = 1 in each of dist/index.html, dist/aaro/index.html, dist/nasa/index.html, dist/nara/index.html.
- `data-external="apex"` present in dist/index.html. In the rendered output it is the last `<li>` before `</ul></nav>`, and it has no `target="_blank"`.
- `git diff --stat HEAD~1`: only src/components/Nav.astro changed.
- Not verified: the manual 360 px drawer check (it was optional). The link reuses the existing `nav.primary a` styles, so it gets the same 44 px+ touch target and flex-wrap behaviour as the other nav links.

## Deviations from Plan

1. **Verify command quirk (macOS):** on macOS, `wc -l` pads its output with leading spaces, so the plan's `grep -qx 4` failed even though all 4 files matched. I re-ran it with `tr -d ' '` and got OK. The product code was not affected.
2. **No GSD id in the code comment:** the plan wanted the comment to say "added quick-261002-0ke". I left that out because executor rules ban process metadata in product code. The comment describes the behaviour only.
3. **Build-generated tracked files:** `pnpm build` rewrote the tracked files api/*.json, api/README.md and feeds/*.xml. I restored them with `git checkout -- api/ feeds/` and did not commit them. They are outside the scope of this task.

## Known Side-effects

- The header screenshots in `tests/visual-regression.spec.ts` will be off by one nav item. The baselines in `tests/visual-baselines/` may need `--update-snapshots` the next time that suite runs. I did not run or update them here.
- Dormant legacy HTML archives (copy-legacy-archives.sh, scripts/templates/nav.py) were left untouched, as the plan specified.

## Self-Check: PASSED

- src/components/Nav.astro contains `href="https://realufo.org/"`: FOUND
- Commit a3aa27b: FOUND
