---
phase: 03-ssg-foundation
plan: "05"
subsystem: ssg-wargov-port
tags: [astro, content-collections, card, lightbox, hero-carousel, lazy-load, d-10-locked, fidelity]
status: in-progress
requirements: [SSG-04, SSG-05]
dependency_graph:
  requires:
    - "Plan 03-01 (Astro install)"
    - "Plan 03-02 (Content Collections schema — wargovEnvelopeSchema)"
    - "Plan 03-03 (data/wargov.json + 4 shards of pre-rendered HTML strings)"
    - "Plan 03-04 (RootLayout + Nav + Footer + invariants.ts)"
  provides:
    - "src/pages/index.astro → wargov archive at / (D-05)"
    - "src/components/Card.astro → markup contract Plan 03-03's render_card_html() mirrors"
    - "src/components/Lightbox.astro → markup shell wired to invariants.ts handlers"
    - "src/components/HeroCarousel.astro → 16:9 ≥4-slide carousel"
    - "src/styles/wargov.css → wargov-specific layout extending global.css"
    - "public/assets/favicon.svg → shared classic-disk-UFO favicon (CLAUDE.md §3.4)"
  affects:
    - "Plan 03-06 — Phase 2 quality-gates.yml validation can now run against the live page"
    - "Phase 4 SSG-06 (14-archive port) — Card.astro + Lightbox.astro + HeroCarousel.astro are reusable"
tech_stack:
  added: []
  patterns:
    - "D-10 LOCKED — lazy-loaded shards contain pre-rendered HTML strings; runtime ONLY calls insertAdjacentHTML"
    - "Server-render boundary: 50 cards via Card.astro + 4 shards via Plan 03-03"
    - "Slugify byte-for-byte equivalent to scripts/snapshot-urls.py:158-167 AND scripts/normalize-csv.py:_slugify"
key_files:
  created:
    - src/pages/index.astro
    - src/components/Card.astro
    - src/components/Lightbox.astro
    - src/components/HeroCarousel.astro
    - src/styles/wargov.css
    - public/assets/favicon.svg
  modified: []
decisions: []
metrics:
  completed_date: pending
---

# Phase 03 Plan 05: Wargov Archive Page (Astro end-to-end) Summary

**One-liner:** First end-to-end Astro-rendered page — `src/pages/index.astro` composes RootLayout + Card.astro + Lightbox.astro + HeroCarousel.astro to render wargov at `/`, server-rendering the first 50 cards and lazy-loading the remaining 172 via IntersectionObserver + `insertAdjacentHTML` against pre-rendered shard HTML strings (D-10 LOCKED — zero client-side templating).

## What Shipped

(populated post-execution)

## How

(populated post-execution)

## Decisions

(populated post-execution)

## Deviations from Plan

(populated post-execution)

## Self-Check

(populated post-execution)
