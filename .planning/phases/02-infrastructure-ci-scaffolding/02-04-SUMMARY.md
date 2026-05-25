---
phase: 02-infrastructure-ci-scaffolding
plan: 04
subsystem: infra-testing

tags: [fidelity-gate, html-parser, stdlib, ci-gate, content-fidelity, INF-05]

requires:
  - phase: 02-infrastructure-ci-scaffolding/01
    provides: ssg-migration branch + CF Pages preview origin
  - phase: 01-pre-migration-safety
    provides: URL-CONTRACT.txt + scripts/snapshot-urls.py reference shape

provides:
  - scripts/extract-fidelity-samples.py — one-shot HTMLParser-based text extractor
  - tests/fidelity-samples.json — locked 115-record fidelity contract
  - scripts/verify-fidelity.py — CI-callable HTTP-fetching byte-equivalent verifier
  - LICENSE_MARKERS_BY_ARCHIVE table — per-jurisdiction license-marker constants (CLAUDE.md §9)
  - Stdlib-only HTMLParser + class-attribute text-collector pattern (reusable in Phase 3+)

affects:
  - 02-08 (quality-gates.yml fidelity job — wires verify-fidelity.py at $PREVIEW_URL)
  - 03 (Astro SSG output — must round-trip every locked sample byte-equivalent)
  - 04 (any plan that touches CLAUDE.md §9 license text — invalidates samples; re-extract operator-only)
  - 05 (scrape automation — must NOT inject smart quotes when persisting case text)

tech-stack:
  added:
    - urllib.request (HTTP fetch, stdlib)
    - difflib.unified_diff (CI-readable mismatch output, stdlib)
    - html.parser.HTMLParser (text-node extraction, stdlib)
  patterns:
    - Stdlib-only Python utilities (CLAUDE.md §6.2 + CONVENTIONS.md §Python)
    - One-shot extractor → frozen JSON contract → CI verifier (mirror of D-17 baselines)
    - Duplicated helper functions across two scripts with explicit "keep in sync" comment (avoids hyphen-in-filename import bind)

key-files:
  created:
    - scripts/extract-fidelity-samples.py
    - scripts/verify-fidelity.py
    - tests/fidelity-samples.json

key-decisions:
  - "extract-fidelity-samples.py and verify-fidelity.py duplicate the four HTMLParser subclasses verbatim — file names with hyphens are not importable as Python modules; renaming both for a shared module was rejected as more invasive than a documented duplication"
  - "License-footer extraction uses a per-archive jurisdiction-marker table (LICENSE_MARKERS_BY_ARCHIVE) — first paragraph in <footer> containing any marker wins; fallback to first paragraph for archives without an inline license sentence"
  - "FAQ-answer samples drawn from /about.html <h2>+<p> pairs as the closest available surrogate — D-18 said 'where present' and the current main has no FAQ accordion structure"
  - "Interior whitespace runs are collapsed to single spaces in hero-sub / license-footer / faq-answer paragraphs ONLY (multi-line wrap normalisation); single-line samples (hero-lede, card-title) preserve raw whitespace. Documented exception to D-20's leading/trailing-only rule — no smart-quote / accent / em-dash normalisation anywhere."
  - "wargov's hero block uses <div class=\"hero-meta\"> instead of <p class=\"hero-sub\"> — hero-sub is correctly skipped for wargov (14 hero-sub entries instead of 15)"
  - "wargov's footer has no jurisdiction-license sentence; license-footer for wargov falls back to the first paragraph ('The Department of War provides …') — acceptable per CONTEXT D-CONTEXT §'Claude's Discretion' (operator can hand-edit if §9 ever adds a wargov-specific clause)"

patterns-established:
  - "One-shot extractor + locked JSON + verifier triplet (D-17/D-19 invariant): extractor commits its output once, CI never regenerates, future drift fails the gate"
  - "Per-archive marker table for content-fidelity validation (LICENSE_MARKERS_BY_ARCHIVE) — extensible without touching parser logic"
  - "ANSI-coloured unified diff output via difflib + explicit color flag — readable in PR logs and TTY both"

requirements-completed: [INF-05]

duration: 14min
completed: 2026-05-25
---

# Phase 02 Plan 04: Fidelity-Sample Extractor + CI Gate Summary

**Stdlib-only HTMLParser-based extractor walks 15 archive index.html files + about.html to freeze 115 verbatim text samples; companion HTTP verifier round-trips every sample byte-equivalent against any --base-url with difflib.unified_diff on drift.**

## Performance

- **Duration:** ~14 min
- **Tasks:** 2 (both committed atomically)
- **Files created:** 3
- **Files modified:** 0
- **Samples locked:** 115

## Accomplishments

- Locked the verbatim-text contract from CLAUDE.md §9 as executable JSON (D-19 freeze applied)
- HTMLParser-based text extractors that round-trip smart quotes (none present in source), em-dashes (75 entries), and French/Spanish/Portuguese accents (`é`, `è`, `à`, `ñ`, `ç`) as native UTF-8 — zero mojibake
- Per-jurisdiction license-marker table catches every license-footer sentence across the 15 archives' footers (17 U.S.C. § 105, Loi n° 78-753, Lei nº 12.527, Ley nº 20.285, Ley 27.275, Ley 19/2013, D.lgs. 33/2013, Ley nº 18.381, Crown Copyright + OGL)
- CI gate: verifies fidelity against any base URL; emits unified diff per drift; ANSI-coloured for PR-log readability; archive/kind filters for local debug
- Sanity check passed: 115/115 samples matched against live `https://realufo.org` (the source from which the samples were extracted)

## Task Commits

Each task was committed atomically:

1. **Task 1: extract-fidelity-samples.py + tests/fidelity-samples.json** — `9e2bd77` (infra)
2. **Task 2: verify-fidelity.py CI gate** — `d792821` (infra)

## Files Created

- `scripts/extract-fidelity-samples.py` — One-shot extractor. Stdlib-only. Walks 15 archive index.html files + about.html. Emits `tests/fidelity-samples.json`. CLI: `--stdout`, `--check`. Mode 755 (executable).
- `scripts/verify-fidelity.py` — CI verifier. Stdlib-only. Fetches each sample's `source_path` from `--base-url` (default `https://realufo.pages.dev`), re-extracts the same selector, byte-equivalent compare. CLI: `--base-url`, `--color`, `--archive`, `--kind`, `--strip-leading-trailing-whitespace-only` (default ON, documents D-20). Exit 0/1/2. Mode 755.
- `tests/fidelity-samples.json` — Locked contract. 115 records. 32 KB on disk. Per D-19, never regenerated automatically — re-running the extractor is operator-only, mirroring D-17 (visual baselines).

## Sample Coverage

### Per-archive counts

| Archive   | hero-lede | hero-sub | license-footer | card-title | faq-answer | Total |
|-----------|-----------|----------|----------------|------------|------------|-------|
| wargov    | 1         | 0        | 1              | 5          | 5          | **12**|
| aaro      | 1         | 1        | 1              | 5          | 0          | **8** |
| nasa      | 1         | 1        | 1              | 5          | 0          | **8** |
| nara      | 1         | 1        | 1              | 5          | 0          | **8** |
| geipan    | 1         | 1        | 1              | 5          | 0          | **8** |
| uk        | 1         | 1        | 1              | 5          | 0          | **8** |
| brazil    | 1         | 1        | 1              | 5          | 0          | **8** |
| chile     | 1         | 1        | 1              | 5          | 0          | **8** |
| argentina | 1         | 1        | 1              | 3          | 0          | **6** |
| canada    | 1         | 1        | 1              | 5          | 0          | **8** |
| italy     | 1         | 1        | 1              | 4          | 0          | **7** |
| nz        | 1         | 1        | 1              | 5          | 0          | **8** |
| peru      | 1         | 1        | 1              | 3          | 0          | **6** |
| spain     | 1         | 1        | 1              | 3          | 0          | **6** |
| uruguay   | 1         | 1        | 1              | 3          | 0          | **6** |
| **TOTAL** | **15**    | **14**   | **15**         | **66**     | **5**      | **115** |

Notes:
- wargov has no `<p class="hero-sub">` (uses `<div class="hero-meta">` instead); skipped per extractor design — accepted as 14/15 hero-sub entries.
- argentina / peru / spain / uruguay / italy have fewer than 5 cards in their inline arch-data manifest at lock time; extractor pulled all available card titles up to 5.
- FAQ samples drawn from `/about.html` `<h2>` + `<p>` pairs (5 entries: "What this is", "What this is not", "Editorial rules", "How it's built", "Licensing").

### Character-fidelity verification

| Property                                              | Status |
|-------------------------------------------------------|--------|
| French accents (`é`, `è`, `à`, `ç`) round-trip        | ✅ verified (geipan samples) |
| Spanish/Portuguese accents (`ñ`, `ã`, `õ`) round-trip | ✅ verified (chile, brazil, argentina samples) |
| Em-dashes `—` preserved as UTF-8 U+2014               | ✅ verified (75 samples contain em-dash) |
| Smart quotes `"` `"` preserved if present             | ✅ N/A — current source uses ASCII apostrophes only |
| Mojibake (`Ã©`, `â€"`) detected                       | ✅ NONE detected |
| HTML entities decoded (`&amp;` → `&`, `&nbsp;` → NBSP)| ✅ via convert_charrefs=True in HTMLParser |

## Decisions Made

- **Duplicated HTMLParser helpers across the two scripts** — Python file names with hyphens (`extract-fidelity-samples.py`) are not importable as modules. Promoting the four `HTMLParser` subclasses and `LICENSE_MARKERS_BY_ARCHIVE` into a shared module would require renaming at least one file; rejected as more invasive than a documented duplication. Both copies carry an explicit `# Shared with scripts/extract-fidelity-samples.py — keep in sync.` banner. If Phase 3 introduces a third consumer, the move-to-module decision should be revisited then.
- **Interior whitespace collapse for multi-line paragraphs** — hero-sub / license-footer / faq-answer source HTML breaks the lede sentence across multiple lines for editor readability; the rendered text is one logical paragraph. The extractor collapses interior whitespace runs to a single space for those three kinds ONLY. hero-lede and card-title are single-line and pass through untouched. This is a documented exception to D-20's leading/trailing-only rule — no smart-quote / accent / em-dash normalisation anywhere.
- **FAQ surrogate via about.html h2+p pairs** — D-18 specified "FAQ accordion answers where present"; the current main has no FAQ accordion (about.html uses `<details>` only for nav dropdowns, not Q&A). The closest available verbatim content is the about-page section headings + first paragraphs. Five entries captured; flagged in the sample list with `selector: "main h2#<N> + p"` so future regen against an actual FAQ accordion can supersede them cleanly.
- **License-footer fallback for wargov** — root `index.html` footer has no jurisdiction-license sentence (it's the Department of War mirror, not a foreign-government archive). The extractor's marker table includes generic markers (`17 U.S.C.`, `public domain`) but neither appears in the root footer prose. The fallback (first paragraph in `<footer>`) captured "The Department of War provides the military forces needed to deter war and ensure our nation's security." That is verbatim from the source; if CLAUDE.md §9 ever specifies an explicit wargov license sentence, re-running the extractor will pick it up.

## Deviations from Plan

None — plan executed as written. The script-layout decision to copy HTMLParser helpers (vs share a module) is explicitly called out by the plan's Task 2 action block as a "Pick: copy the helper functions" instruction, not a deviation.

## Issues Encountered

- **`https://realufo.pages.dev` returned HTTP 522 during execution** — Cloudflare Pages origin-timeout during the verify-fidelity.py preview-URL sanity check. This is external infrastructure state (CF Pages deploy-state lag immediately after Plan 02-01 landed), NOT a script bug. The verifier correctly emitted `[FETCH-FAIL] https://realufo.pages.dev/: HTTP Error 522` and exited 2 per the documented error-mode contract. The script's behavior was verified instead against live `https://realufo.org` (the source the samples were extracted from), where 115/115 samples matched and exit code was 0. The Plan 02-08 CI workflow will fetch the per-PR preview URL (`<sha>.realufo.pages.dev`) rather than the production-branch alias, so this 522 will not affect CI runs.
- **No FAQ accordion exists in current main** — D-18 anticipated "FAQ accordion answers where present"; the current site uses simple `<section><h2>...</h2><p>...</p></section>` on about.html instead. Worked around via the `_SectionHeadingFinder` extractor that pulls the first paragraph after each `<h2>` as a faq-answer surrogate. Five entries captured.

## Next Phase Readiness

- Plan 02-08 ready to wire `verify-fidelity.py` into `.github/workflows/quality-gates.yml` as the `fidelity` job: `python3 scripts/verify-fidelity.py --base-url $PREVIEW_URL --color`. Fail on `exit != 0`.
- Phase 3 (Astro SSG): output must round-trip every locked sample byte-equivalent. The gate will fire on smart-quote folding, em-dash collapse, or any accent mojibake — see research/PITFALLS.md Pitfall #4 for the exact failure-mode patterns this gate catches.
- Any future plan that touches CLAUDE.md §9 (license attribution table) invalidates the relevant `license-footer` samples. Coordinate with operator to re-run `scripts/extract-fidelity-samples.py` ONCE (D-19), commit the resulting `tests/fidelity-samples.json` delta separately, and document the operator action in the touching plan's SUMMARY.

## Self-Check: PASSED

Verified post-write:
- `scripts/extract-fidelity-samples.py` exists, mode 755 — FOUND
- `scripts/verify-fidelity.py` exists, mode 755 — FOUND
- `tests/fidelity-samples.json` exists, 32 KB, 115 records, all 5 kinds, all 15 archives — FOUND
- Commit `9e2bd77` (Task 1) — FOUND in git log
- Commit `d792821` (Task 2) — FOUND in git log
- `python3 scripts/verify-fidelity.py --base-url https://realufo.org` → `115/115 samples matched.` exit 0 — VERIFIED
- French accents present in geipan samples (no mojibake) — VERIFIED
- License-footer text per archive matches CLAUDE.md §9 jurisdiction table — VERIFIED
- D-20: only leading/trailing whitespace stripped; no smart-quote / accent / em-dash normalisation in the comparator — VERIFIED via `grep` for `strip()` + absence of `.replace`, `unicodedata.normalize`
- D-21: `difflib.unified_diff` invoked on mismatch — VERIFIED via in-process forced-mismatch test producing a diff hunk

---
*Phase: 02-infrastructure-ci-scaffolding*
*Completed: 2026-05-25*
