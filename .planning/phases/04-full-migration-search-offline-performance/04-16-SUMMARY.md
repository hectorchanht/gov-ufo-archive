---
phase: 04-full-migration-search-offline-performance
plan: "16"
subsystem: nasa-archive-port
tags: [archive-port, nasa, uap-independent-study, small-catalog, d-09-retirement, wave-5]
requirements: [SSG-06, SSG-08, SSG-09, SSG-10, SSG-11, SSG-12, PERF-04]
status: in-progress
dependency-graph:
  requires:
    - "04-01 (lightbox-fix — data-row-id contract inherited by CatalogCard.astro)"
    - "04-02 (_archive_common.rewrite_to_r2 — normalize-nasa.py imports this helper)"
    - "04-04 (?page=N pagination handler — adapted for /nasa/ as nasa:page-rendered)"
    - "04-05 (CatalogCard.astro template + normalize-<slug>.py pattern + partial-port postbuild block)"
    - "04-06 (Uruguay port — closest-analog template; stub-envelope detection inherited verbatim)"
    - "04-15 (NARA port — IMMEDIATE predecessor; PAGE+CATALOG handling pattern inherited; title-cleanup precedent)"
    - "04-scope-pivot 7bd91ac (Lightbox.astro extended meta panel + dual-action buttons; CatalogCard emits data-desc/agency/date/region/category/src)"
  provides:
    - "Fourth per-archive port reference — fourth confirmation CatalogCard.astro is reusable WITHOUT modification across the 4 ACTIVE archives"
    - "scripts/normalize-nasa.py — fifth example of the dual-source idempotency pattern (alongside normalize-csv.py + normalize-nz.py + normalize-uruguay.py + normalize-nara.py)"
    - "Empirical confirmation: an archive with 18 mixed PDF + VID + IMG rows flows cleanly through rewrite_to_r2 (PDF + VID → R2; IMG verbatim)"
    - "IMG-type stats grouping: catalogStatsSchema has no img_total → IMG rows count toward local_total when l set, otherwise no dedicated tier"
  affects:
    - "scripts/copy-legacy-archives.sh (nasa dropped from main loop; partial-port block keeps nasa/story.html + nasa/assets/* copying)"
    - "scripts/sync-footer.py (nasa/index.html removed from SKIP_PATHS — Astro owns the route now; nasa/story.html STORY_META entry preserved)"
    - "tests/fidelity-samples.json (8 legacy NASA entries replaced with 5+ fresh Astro-targeted entries)"
tech-stack:
  added: []
  patterns:
    - "Pattern reuse: CatalogCard.astro (Plan 04-05) used verbatim — fourth archive confirmed reusable"
    - "Pattern reuse: normalize-uruguay.py structural clone with slug + source-path swap + IMG-type handling"
    - "Pattern reuse: @import url('./wargov.css') from nasa.css — share archive-agnostic layout via tone-colour variable"
    - "Pattern reuse: partial-port postbuild block (copy story.html + assets/, skip index.html owned by Astro)"
    - "Pattern reuse: stub-envelope detection from Plan 04-06 (_read_from_existing_envelope returns None when assets=[])"
    - "Pattern reuse: Title-cleanup precedent — DROPS legacy '(Offline Mirror)' suffix per CLAUDE.md §11 + NARA 04-15 precedent"
    - "NASA-specific: VID rows preserved verbatim (no R2 rewrite — YouTube URLs); IMG rows preserved verbatim (Astro Image future)"
key-files:
  created:
    - src/pages/nasa/index.astro
    - src/styles/nasa.css
    - scripts/normalize-nasa.py
    - public/data/nasa.json
  modified:
    - data/nasa.json
    - scripts/copy-legacy-archives.sh
    - scripts/sync-footer.py
    - tests/fidelity-samples.json
  deleted:
    - nasa/index.html
    - scripts/build-nasa.py
decisions:
  - "[skeleton — will be filled in after Task 2]"
metrics:
  duration: in-progress
  completed: 2026-05-28
---

# Phase 04 Plan 16: NASA Archive Port (UAP Independent Study Team) Summary

(Skeleton — will be replaced with full content after both tasks complete.)

## Tasks Completed

- [ ] Task 1 — Add `scripts/normalize-nasa.py` + emit `data/nasa.json` + delete `scripts/build-nasa.py`
- [ ] Task 2 — Create `src/pages/nasa/index.astro` + `src/styles/nasa.css`, delete `nasa/index.html`, update postbuild + sync + fidelity tooling

## Commits

| Task | Hash      | Subject                                                                                  |
| ---- | --------- | ---------------------------------------------------------------------------------------- |
| —    | (pending) | docs(04-16): SUMMARY skeleton (#2070)                                                    |
| 1    | (pending) | feat(04-16): add normalize-nasa.py + emit data/nasa.json with 18 catalog rows            |
| 2    | (pending) | feat(04-16): port NASA archive to Astro (D-09 retirement)                                |
