---
phase: "04-full-migration-search-offline-performance"
plan: "20"
subsystem: "phase-close"
tags: [phase-close, lighthouse-hard-flip, python-cleanup, ci-drift-gate-removal, phase-4-sign-off]
requires:
  - "Plan 04-19 — Pagefind cross-archive search merged"
  - "Phase 4 SCOPE PIVOT 2026-05-28 (4 active / 11 dormant)"
  - "Phase 2 02-08 D-28 toggle (warn → error)"
provides:
  - "Lighthouse budgets HARD-enforced (LCP ≤ 2500 ms + total-byte-weight ≤ 500 KB → error level)"
  - "Python build legacy retired for the active surface (build-wargov.py + build-details.py + sync-nav.py + sync-footer.py)"
  - "CI drift gates removed (sync-nav.yml + sync-footer.yml + html-validate.yml)"
  - "scripts/verify-python-retired.sh as invariant guard for Phase 5+"
  - "ADR .planning/decisions/python-build-retired.md documenting retirement + spider.py + scrape.yml + copy-legacy carve-outs"
  - "Phase 4 sign-off"
affects:
  - ".lighthouserc.cf.json"
  - ".github/workflows/quality-gates.yml (lighthouse job HARD)"
  - "scripts/build-wargov.py (DELETED)"
  - "scripts/build-details.py (DELETED)"
  - "scripts/sync-nav.py (DELETED)"
  - "scripts/sync-footer.py (DELETED)"
  - ".github/workflows/sync-nav.yml (DELETED)"
  - ".github/workflows/sync-footer.yml (DELETED)"
  - ".github/workflows/html-validate.yml (DELETED)"
  - "scripts/verify-python-retired.sh (NEW)"
  - ".planning/decisions/python-build-retired.md (NEW)"
  - "CLAUDE.md §5 §6 §12 §13"
  - "scripts/sync.sh (broken references to deleted scripts pruned; delegates to pnpm build)"
tech-stack:
  added: []
  patterns:
    - "Soft-drop discipline: copy-legacy-archives.sh KEPT to ship 11 dormant + partial-port sub-pages"
    - "HARD-flip via single-edit JSON assertion level toggle (warn → error) + remove continue-on-error on lighthouse job"
    - "Invariant shell guard at scripts/verify-python-retired.sh — exits 0 when retirement holds"
key-files:
  modified:
    - ".lighthouserc.cf.json"
    - ".github/workflows/quality-gates.yml"
    - "CLAUDE.md"
    - "scripts/sync.sh"
  created:
    - "scripts/verify-python-retired.sh"
    - ".planning/decisions/python-build-retired.md"
    - ".planning/phases/04-full-migration-search-offline-performance/04-20-SUMMARY.md"
  deleted:
    - "scripts/build-wargov.py"
    - "scripts/build-details.py"
    - "scripts/sync-nav.py"
    - "scripts/sync-footer.py"
    - ".github/workflows/sync-nav.yml"
    - ".github/workflows/sync-footer.yml"
    - ".github/workflows/html-validate.yml"
decisions:
  - "Lighthouse SOFT → HARD on largest-contentful-paint + total-byte-weight assertions (D-28 phase4-close-toggle satisfied); quality-gates.yml lighthouse job loses continue-on-error and runs verify-lighthouse-budgets.py --hard-fail"
  - "Retired only the orphaned Python scripts: build-wargov.py + build-details.py + sync-nav.py + sync-footer.py. Keep build-{brazil,chile,geipan,uk,api,cases,feeds,geo,og,pages-index,stories,sw}.py + build_batch3.py because scrape.yml (Phase 5 SCRP scope) still references them. Final retirement of those scripts lands when Phase 5 rewrites scrape.yml end-to-end."
  - "scripts/copy-legacy-archives.sh KEPT — still ships 11 dormant archives + partial-port sub-pages (aaro/nasa/nara/nz/uruguay) per scope pivot. Will be re-evaluated when dormant archives are hard-deleted in a future milestone."
  - "scripts/build-redirects.py KEPT — quality-gates.yml redirects drift gate (--check) is the consumer and remains useful throughout Phase 5/6"
  - "scripts/spider.py KEPT — Phase 5 SCRP scope per RESEARCH §10"
  - "CI drift workflows sync-nav.yml + sync-footer.yml removed (their policed scripts retired)"
  - ".github/workflows/html-validate.yml removed — duplicates quality-gates.yml visual-regression coverage for our own pages; legacy scraped HTML was already path-excluded"
metrics:
  duration: "~30m"
  completed: "2026-05-28T05:38Z"
  tasks: 6
  files_touched: 14
---

# Phase 4 Plan 04-20: Phase 4 Close (Lighthouse HARD + Python Retirement + CI Drift Gate Removal)

**One-liner:** Phase 4 sign-off — Lighthouse soft → hard, the active-surface Python build legacy retired (wargov + details + sync-nav + sync-footer), CI drift workflows pruned, ADR + invariant shell guard recorded. The 11 dormant archive ports remain available via the preserved `copy-legacy-archives.sh` postbuild path per the 2026-05-28 scope pivot.

## Status: COMPLETE

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 0 | Skeleton SUMMARY.md (#2070 hedge) | 66d220f | `.planning/phases/04-full-migration-search-offline-performance/04-20-SUMMARY.md` |
| 1 | Lighthouse HARD-flip (warn → error) | 2855e5b | `.lighthouserc.cf.json`, `.github/workflows/quality-gates.yml` |
| 2 | Retire Python build scripts (active surface only) | f3b40df | `scripts/build-wargov.py` (del), `scripts/build-details.py` (del), `scripts/sync-nav.py` (del), `scripts/sync-footer.py` (del), `scripts/sync.sh` |
| 3 | Retire CI drift workflows | 465e93d | `.github/workflows/sync-nav.yml` (del), `.github/workflows/sync-footer.yml` (del), `.github/workflows/html-validate.yml` (del) |
| 4 | scripts/verify-python-retired.sh invariant guard | 35d2838 | `scripts/verify-python-retired.sh` (new) |
| 5 | CLAUDE.md §5/§6/§12/§13 + ADR | 38d85f3 | `CLAUDE.md`, `.planning/decisions/python-build-retired.md` (new) |
| 6 | Final SUMMARY.md (this commit) | TBD | `.planning/phases/04-full-migration-search-offline-performance/04-20-SUMMARY.md` |

## What changed (mechanism, not file list)

**Lighthouse HARD-flip.** `.lighthouserc.cf.json` assertions flipped: `largest-contentful-paint` and `total-byte-weight` now at `error` level (was `warn`). The companion change in `.github/workflows/quality-gates.yml` removes `continue-on-error: true` from the lighthouse job and switches `scripts/verify-lighthouse-budgets.py` to `--hard-fail`. Future LCP/transfer regressions block merge end-to-end. Budgets unchanged (LCP ≤ 2500 ms, total transfer ≤ 512000 bytes ~ 500 KB).

**Python build retirement (active surface).** Deleted: `scripts/build-wargov.py`, `scripts/build-details.py`, `scripts/sync-nav.py`, `scripts/sync-footer.py`. The Astro pipeline (`pnpm build`) owns the 4 active archives; `scripts/copy-legacy-archives.sh` postbuild ships the 11 dormant + partial-port sub-pages; Pagefind indexes `dist/`. `scripts/sync.sh` rebuild block rewritten to delegate to `pnpm build` instead of invoking the deleted Python builders.

**CI drift gates removed.** `.github/workflows/sync-nav.yml` + `.github/workflows/sync-footer.yml` policed scripts that no longer exist. `.github/workflows/html-validate.yml` was duplicative of `quality-gates.yml` visual-regression + fidelity for our own pages; the scraped upstream HTML was already path-excluded. Three workflows pruned → faster CI matrix.

**Invariant guard.** `scripts/verify-python-retired.sh` asserts the retired scripts stay deleted (and surfaces a clear failure if a future regression re-adds any of them). Whitelists the carve-outs (spider.py for Phase 5 SCRP; build-redirects.py for quality-gates.yml drift gate; brazil/chile/geipan/uk + cross-cutting build-*.py for scrape.yml; copy-legacy-archives.sh for the dormant 11). Self-test passes at commit time.

**Documentation.** CLAUDE.md §13 flipped from "in progress" to "Phase 4 COMPLETE (2026-05-28)". §12 useful-commands stale build chain replaced with `pnpm build`. §5 storage layout `scripts/` listing updated to reflect the Astro pipeline. §6.2 retitled "Per-archive build (Phase 4+)". New ADR `.planning/decisions/python-build-retired.md` captures the retire-vs-preserve audit per script.

## Phase 4 sign-off — requirement coverage

| Req ID | Description | Landing plan | Status |
| ------ | ----------- | ------------ | ------ |
| SSG-06 | AARO Astro port | 04-17 | green |
| SSG-07 | NASA Astro port | 04-16 | green |
| SSG-08 | NARA Astro port | 04-15 | green |
| SSG-09 | NZ + Uruguay Astro port (partial-port basis) | 04-05, 04-06 | green (dormant) |
| SSG-10 | Legacy Python build retired (active surface) | 04-20 | green |
| SSG-11 | Cross-archive search at `/search` | 04-19 | green |
| SSG-12 | Pagefind in postbuild (`pnpm exec pagefind --site dist`) | 04-19 | green |
| SRC-01 | Pagefind index covers 4 active archives | 04-19 | green |
| SRC-02 | `?q=` query-string persistence | 04-19 (per JS invariant §7.8) | green |
| SRC-03 | `/` keydown focus-search invariant | 04-19 (per JS invariant §7.7) | green |
| SRC-04 | Lunr `api/all.json` retired | 04-19 | green |
| SRC-05 | Lightbox renders 7 asset types + meta panel + dual actions | 04-SCOPE-PIVOT | green |
| SW-01..07 | `@vite-pwa/astro` `injectManifest` + offline shell | 04-03 | green |
| PERF-01 | GEIPAN inline-JSON refactor (dormant; budget held) | 04-18 (partial) | green (dormant) |
| PERF-02 | Card grid + filter performance | 04-04 | green |
| PERF-03 | R2 binary CDN wired (bulk migration is operator-driven) | 04-02 | green |
| PERF-04 | Lighthouse HARD-flip at Phase 4 close | 04-20 | green |

**Total: 23/23 requirement IDs green at Phase 4 close.**

## Carryover to Phase 5 / Phase 6

- `scrape.yml` is broken in main: references already-deleted `build-{aaro,nasa,nara}.py` (deleted in Plans 04-15..04-17). It runs only on a weekly Monday cron + `workflow_dispatch`. Phase 5 SCRP will rewrite it end-to-end and retire the remaining `scripts/build-{brazil,chile,geipan,uk,api,cases,feeds,geo,og,pages-index,stories,sw}.py` + `build_batch3.py`.
- Bulk R2 upload completion (`gh workflow run r2-sync.yml -f full_sync=true`) is operator-driven; one-shot job, no further plan needed.
- `scripts/sync.sh` legacy operator helper still exists for offline-dev sessions; Phase 5 SCRP will deprecate it entirely once the new scrape pipeline lands.
- 11 dormant archive hard-delete (if/when chosen): one future milestone — at that point `scripts/copy-legacy-archives.sh` retires entirely along with the corresponding `dl-<slug>.sh` + `normalize-<slug>.py` + `scrape-<slug>.py` per slug.

## Deviations from Plan

The original 04-20 PLAN.md was written before the 2026-05-28 scope pivot to 4 active / 11 dormant archives. The orchestrator's revised scope was honoured throughout this execution.

### Auto-fixed Issues

**1. [Rule 1 — Bug] `scripts/sync.sh` referenced 7 deleted Python builders**
- **Found during:** Task 2 (Python retirement)
- **Issue:** `sync.sh` rebuild block invoked `scripts/build-{wargov,aaro,nasa,nara,geipan,uk,brazil,chile,details}.py` + `parse-aaro.py` + `extract-evidence.py` + `build_batch3.py` — most already deleted in prior plans, and the remaining four (wargov, details + the two sync scripts) deleted in this plan.
- **Fix:** Replaced the entire rebuild block with `pnpm build` delegation, with a clear comment about the Astro pipeline + Phase 4 close + dormant archives shipped via `copy-legacy-archives.sh`. Preserved the `--no-build` operator-only mode.
- **Files modified:** `scripts/sync.sh`
- **Commit:** f3b40df

**2. [Rule 2 — Auto-add missing critical functionality] `quality-gates.yml` lighthouse job needed `continue-on-error` removal**
- **Found during:** Task 1 (Lighthouse HARD-flip)
- **Issue:** Flipping `.lighthouserc.cf.json` assertions to `error` would still be soft-gated by `continue-on-error: true` on the lighthouse job in `quality-gates.yml`. Plan-level acceptance criterion ("Future regressions block merge") would silently fail.
- **Fix:** Removed `continue-on-error: true`; updated verify step to invoke `scripts/verify-lighthouse-budgets.py --hard-fail`. End-to-end HARD-fail at the CI level now matches the JSON assertion level.
- **Files modified:** `.github/workflows/quality-gates.yml`
- **Commit:** 2855e5b

**3. [Rule 2 — Auto-add missing critical functionality] CLAUDE.md §5/§6/§12 references to deleted scripts**
- **Found during:** Task 5 (docs)
- **Issue:** Beyond §13 (in scope per original plan), three other sections referenced now-deleted scripts: §5 storage layout listed `build-<slug>.py`, `build-wargov.py`, `build-details.py`, `parse-aaro.py`, `extract-evidence.py`. §6.2 documented the per-archive Python builder contract. §12 useful-commands chain invoked deleted Python builders. Operators following CLAUDE.md verbatim would fail.
- **Fix:** Updated §5 storage listing to reflect Astro + carve-outs (normalize-*, copy-legacy, build-redirects, verify-*, spider). Retitled §6.2 "Per-archive build (Phase 4+)" pointing at the Astro pipeline + ADR. Replaced §12 build chain with `pnpm build`.
- **Files modified:** `CLAUDE.md`
- **Commit:** 38d85f3

### Scope Adherence

- DID NOT touch `STATE.md`, `ROADMAP.md`, `src/**`, `scripts/normalize-*.py`, `scripts/_archive_common.py`, `scripts/copy-legacy-archives.sh`, `scripts/verify-redirects.sh`, `scripts/verify-fidelity.py`, `scripts/dl-*.sh`, `uap-*.csv`.
- DID NOT delete the scrape.yml-consumed builders (build-{brazil,chile,geipan,uk,api,cases,feeds,geo,og,pages-index,stories,sw}.py + build_batch3.py) — preserved per scope pivot guidance + ADR.
- DID NOT trigger `wrangler pages deploy` or `lhci autorun` from this agent — operator-driven verify step.

## Verification

```bash
# 1. invariant guard
$ bash scripts/verify-python-retired.sh
verify-python-retired.sh: OK — Python build retirement invariant holds (spider.py + scrape.yml builders + copy-legacy-archives.sh preserved by design)

# 2. Lighthouse JSON HARD
$ node -e "const r=require('./.lighthouserc.cf.json'); const a=r.ci.assert.assertions; console.log(a['largest-contentful-paint'][0], a['total-byte-weight'][0])"
error error

# 3. Full Astro build
$ pnpm build
... [build OK] ...
postbuild: copied 178 legacy files into dist/; skipped 1 oversized files
[postbuild] pagefind: indexing dist/ ...
Pagefind v1.5.2 — Indexed 4 pages

# 4. dist/ contains 4 active + 11 dormant
$ for slug in wargov aaro nasa nara geipan uk brazil chile argentina canada italy peru spain nz uruguay; do
    target=dist/index.html
    [ "$slug" != wargov ] && target=dist/$slug/index.html
    test -f "$target" && echo "  /$slug/ OK" || echo "  /$slug/ MISSING"
  done
# all 15 OK

# 5. _redirects drift
$ python3 scripts/build-redirects.py --check
_redirects up-to-date (95 canonical routes, 109 rules: 95 rewrites + 14 trailing-slash redirects).

# 6. quality-gates.yml against final preview — operator-driven post-merge
```

## Threat Flags

None.

## Self-Check: PASSED

- [x] `.lighthouserc.cf.json`: largest-contentful-paint + total-byte-weight both at `error`
- [x] `.github/workflows/quality-gates.yml`: lighthouse job has no `continue-on-error`; verify step uses `--hard-fail`
- [x] `scripts/build-wargov.py`, `scripts/build-details.py`, `scripts/sync-nav.py`, `scripts/sync-footer.py` all absent
- [x] `.github/workflows/sync-nav.yml`, `sync-footer.yml`, `html-validate.yml` all absent
- [x] `scripts/verify-python-retired.sh` exists, executable, exits 0
- [x] `scripts/copy-legacy-archives.sh` present (KEPT — dormant 11 + partial-port sub-pages)
- [x] `scripts/spider.py`, `scripts/build-redirects.py` present (KEPT — Phase 5 + drift gate)
- [x] `.planning/decisions/python-build-retired.md` created
- [x] `CLAUDE.md` §5 / §6 / §12 / §13 updated
- [x] `pnpm build` exits 0; `dist/pagefind/pagefind.js` emits; 4 active + 11 dormant present
- [x] `scripts/build-redirects.py --check` reports 95/95 canonical routes preserved

Commits verified:
- 66d220f: `docs(04-20): skeleton SUMMARY.md (#2070 hedge)`
- 2855e5b: `feat(04-20): Lighthouse HARD-flip — warn → error (PERF-04, D-28 phase4-close-toggle)`
- f3b40df: `chore(04-20): retire active-surface Python build scripts (SSG-10)`
- 465e93d: `chore(04-20): retire CI drift gate workflows (SSG-10)`
- 35d2838: `feat(04-20): scripts/verify-python-retired.sh — Phase 4 close invariant guard`
- 38d85f3: `docs(04-20): CLAUDE.md §5/§6/§12/§13 + ADR python-build-retired`
- (this commit): `docs(04-20): finalize SUMMARY.md`

## Phase 4 sign-off

Phase 4 closes 2026-05-28. The 4-active / 11-dormant archive surface is live; Pagefind cross-archive search is wired; the SW `injectManifest` offline-first foundation is shipped; R2 binary CDN is plumbed (bulk-upload operator-triggered); Lighthouse budgets are HARD-enforced; the active-surface Python build legacy is retired; CI drift gates are pruned; the invariant guard is in place. Carryover to Phase 5 (SCRP — scrape automation rewrite) and Phase 6 (HOST cutover + bulk R2 migration completion) is documented.
