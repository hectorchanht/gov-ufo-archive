---
phase: 04-full-migration-search-offline-performance
plan: "17"
subsystem: aaro-archive-port
tags: [archive-port, aaro, all-domain-anomaly-resolution-office, large-catalog, d-09-retirement, parse-aaro-retirement, wave-5]
requirements: [SSG-06, SSG-08, SSG-09, SSG-10, SSG-11, SSG-12, PERF-04]
status: in-progress
dependency-graph:
  requires:
    - "04-01 (lightbox-fix — data-row-id contract inherited by CatalogCard.astro)"
    - "04-02 (_archive_common.rewrite_to_r2 — normalize-aaro.py imports this helper)"
    - "04-04 (?page=N pagination handler — adapted for /aaro/ as aaro:page-rendered)"
    - "04-05 (CatalogCard.astro template + normalize-<slug>.py pattern + partial-port postbuild block)"
    - "04-06 (Uruguay port — stub-envelope detection inherited verbatim)"
    - "04-15 (NARA port — large-catalog precedent + partial-port block largest pattern)"
    - "04-16 (NASA port — immediate predecessor + title-cleanup precedent + extra-keys filter pattern)"
    - "04-scope-pivot 7bd91ac (Lightbox.astro extended meta panel + dual-action buttons; CatalogCard emits data-desc/agency/date/region/category/src)"
  provides:
    - "Fifth per-archive port reference — final ACTIVE archive port in scope. Confirms CatalogCard.astro is reusable WITHOUT modification across all 4 ACTIVE archives + closes the 4-active set (wargov + aaro + nasa + nara)."
    - "scripts/normalize-aaro.py — sixth example of the dual-source idempotency pattern; first large-catalog example (112 rows mixed PDF/VID/IMG)"
    - "Empirical confirmation: a 112-row archive (32 VID + 59 PDF + 21 IMG) flows cleanly through rewrite_to_r2 (PDF/VID → R2 custom-domain; IMG verbatim for Astro Image)"
    - "TRIPLE Python retirement precedent: parse-aaro.py + extract-evidence.py + build-aaro.py all deleted in a single plan (D-09 absorption pattern)"
    - "DVIDS deep-link contract empirically verified: VID asset.s carries dvidshub.net page URL; CatalogCard's Source ↗ button renders the DVIDS deep-link verbatim"
  affects:
    - "scripts/copy-legacy-archives.sh (aaro dropped from main for-loop; partial-port block preserves all 14 aaro/<case>.html + aaro/pages/* + aaro/assets/*)"
    - "scripts/sync-footer.py (aaro/index.html removed from SKIP_PATHS — Astro owns the route now; all 14 aaro/<case>.html STORY_META entries preserved)"
    - "tests/fidelity-samples.json (8 legacy AARO entries replaced with 5 fresh Astro-targeted entries)"
tech-stack:
  added: []
  patterns:
    - "Pattern reuse: CatalogCard.astro (Plan 04-05) used verbatim — no modifications needed for AARO (5th archive confirmed reusable; closes 4-active set)"
    - "Pattern reuse: normalize-nara.py structural clone with slug + source-path swap + sentinel-shard emission + VID/PDF/IMG type handling"
    - "Pattern reuse: @import url('./wargov.css') from aaro.css — share archive-agnostic layout via tone-colour variable"
    - "Pattern reuse: partial-port postbuild block (copy 14+ aaro/<case>.html sub-pages + pages/ + assets/, skip index.html owned by Astro)"
    - "Pattern reuse: stub-envelope detection from Plan 04-06 (_read_from_existing_envelope returns None when assets=[])"
    - "Pattern reuse: Title-cleanup precedent — DROPS legacy '(Offline Mirror)' suffix per CLAUDE.md §11 + NARA + NASA precedent"
    - "Pattern reuse: extra-key filter via _CATALOG_KEYS strict tuple — drops legacy k/re/st/di/dd keys from VID/PDF rows (extends NASA precedent for legacy 'embed' key)"
    - "AARO-specific: VID rows carry both R2 download URL (asset.u) AND DVIDS page URL (asset.s) — CatalogCard renders Source ↗ as DVIDS ↗ per CLAUDE.md §4.3"
    - "AARO-specific: sentinel data/aaro-shard-1.json emitted matching NARA precedent (1-to-1 copy; future operator can drop real shard-2/3 splits without page-template changes)"
key-files:
  created:
    - src/pages/aaro/index.astro
    - src/styles/aaro.css
    - scripts/normalize-aaro.py
    - public/data/aaro.json
    - data/aaro-shard-1.json
  modified:
    - data/aaro.json
    - scripts/copy-legacy-archives.sh
    - scripts/sync-footer.py
    - tests/fidelity-samples.json
  deleted:
    - aaro/index.html
    - scripts/build-aaro.py
    - scripts/parse-aaro.py
    - scripts/extract-evidence.py
decisions: []
metrics:
  duration: TBD
  completed: TBD
---

# Phase 04 Plan 17: AARO Archive Port (All-domain Anomaly Resolution Office) Summary

(SKELETON — populated by the executor after Task 2 completes.)

## Tasks Completed

(populated after each task commit)

## Commits

(populated after each task commit)

## Implementation Notes

(populated after Task 2)

## Deviations from Plan

(populated after Task 2)

## Deferred Items

(populated after Task 2)

## Known Stubs

(populated after Task 2)

## Self-Check

(populated after Task 2)
