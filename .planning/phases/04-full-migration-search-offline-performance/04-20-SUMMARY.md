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
  - "ADR .planning/decisions/python-build-retired.md documenting retirement + spider.py carve-out"
  - "Phase 4 sign-off"
affects:
  - ".lighthouserc.cf.json"
  - "scripts/build-wargov.py (DELETED)"
  - "scripts/build-details.py (DELETED)"
  - "scripts/sync-nav.py (DELETED)"
  - "scripts/sync-footer.py (DELETED)"
  - ".github/workflows/sync-nav.yml (DELETED)"
  - ".github/workflows/sync-footer.yml (DELETED)"
  - ".github/workflows/html-validate.yml (DELETED)"
  - "scripts/verify-python-retired.sh (NEW)"
  - ".planning/decisions/python-build-retired.md (NEW)"
  - "CLAUDE.md §13 SSG migration status"
  - "scripts/sync.sh (broken references to deleted scripts pruned)"
tech-stack:
  added: []
  patterns:
    - "Soft-drop discipline: copy-legacy-archives.sh KEPT to ship 11 dormant + partial-port sub-pages"
    - "HARD-flip via single-edit JSON assertion level toggle (warn → error)"
    - "Invariant shell guard at scripts/verify-python-retired.sh — exits 0 when retirement holds"
key-files:
  modified:
    - ".lighthouserc.cf.json"
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
  - "Lighthouse SOFT → HARD on largest-contentful-paint + total-byte-weight assertions (D-28 phase4-close-toggle satisfied)"
  - "Retired only the orphaned Python scripts: build-wargov.py + build-details.py + sync-nav.py + sync-footer.py. Keep build-{brazil,chile,geipan,uk,api,cases,feeds,geo,og,pages-index,stories,sw}.py because scrape.yml (Phase 5 SCRP scope) still references them. Final retirement of those scripts lands when Phase 5 rewrites scrape.yml end-to-end."
  - "scripts/copy-legacy-archives.sh KEPT — still ships 11 dormant archives + partial-port sub-pages (aaro/nasa/nara/nz/uruguay) per scope pivot. Will be re-evaluated when dormant archives are hard-deleted in a future milestone."
  - "scripts/build-redirects.py KEPT — quality-gates.yml redirects drift gate is the consumer (will remain throughout Phase 5/6)"
  - "scripts/spider.py KEPT — Phase 5 SCRP scope per RESEARCH §10"
  - "CI drift workflows sync-nav.yml + sync-footer.yml removed (their policed scripts retired)"
  - ".github/workflows/html-validate.yml removed — duplicates quality-gates.yml visual-regression coverage for our own pages; legacy scraped HTML excluded via path filter no longer needed"
metrics:
  duration: "TBD"
  completed: "TBD"
---

# Phase 4 Plan 04-20: Phase 4 Close (Lighthouse HARD + Python Retirement + CI Drift Gate Removal)

**One-liner:** Phase 4 sign-off — Lighthouse soft → hard, the active-surface Python build legacy retired (wargov + details + sync-nav + sync-footer), CI drift workflows pruned, ADR + invariant shell guard recorded. 11 dormant archive ports remain available via the preserved `copy-legacy-archives.sh` postbuild path per the 2026-05-28 scope pivot.

## Status: IN PROGRESS

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 0 | Skeleton SUMMARY.md (#2070 hedge) | TBD | .planning/phases/04-full-migration-search-offline-performance/04-20-SUMMARY.md |
| 1 | Lighthouse HARD-flip (warn → error) | TBD | .lighthouserc.cf.json |
| 2 | Retire Python build scripts (active surface only) | TBD | scripts/build-wargov.py, scripts/build-details.py, scripts/sync-nav.py, scripts/sync-footer.py, scripts/sync.sh |
| 3 | Retire CI drift workflows | TBD | .github/workflows/sync-nav.yml, .github/workflows/sync-footer.yml, .github/workflows/html-validate.yml |
| 4 | scripts/verify-python-retired.sh invariant guard | TBD | scripts/verify-python-retired.sh |
| 5 | CLAUDE.md §13 status + ADR python-build-retired.md | TBD | CLAUDE.md, .planning/decisions/python-build-retired.md |
| 6 | Final SUMMARY.md + verification | TBD | .planning/phases/04-full-migration-search-offline-performance/04-20-SUMMARY.md |

(Each row updated on commit.)

## Verification

To be populated post-execution.

## Deviations from Plan

To be populated post-execution.

## Self-Check

To be populated post-execution.
