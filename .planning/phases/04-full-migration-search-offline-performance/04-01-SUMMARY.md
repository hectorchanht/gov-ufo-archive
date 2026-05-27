---
phase: "04-full-migration-search-offline-performance"
plan: "01"
subsystem: "lightbox"
tags: [lightbox, invariants, wargov, blocking-port-foundation]
requires:
  - "Plan 03-04 invariants.ts lightbox handler (modified surgically)"
  - "Plan 03-05 Card.astro markup (modified surgically)"
  - "Plan 03-03 normalize-csv.py render_card_html (modified surgically — D-10 LOCKED pair)"
provides:
  - "data-row-id / data-url / data-local contract on Card.astro <article> + <a.btn-open> + <a.btn-download>"
  - "openAt(rowIdOrIdx) keyed-lookup with numeric idx fallback"
  - "tests/lightbox.spec.ts Playwright spec covering click / arrow / Escape / filter / remote-PDF / pagination-smoke"
  - "blocking-port-foundation contract for 14 archive ports (04-05..04-18)"
affects:
  - "src/components/Card.astro"
  - "src/scripts/invariants.ts"
  - "src/pages/index.astro (refreshLbList)"
  - "scripts/normalize-csv.py (render_card_html)"
  - "data/wargov-shard-{2..5}.json + public/data/wargov-shard-{2..5}.json (regenerated)"
tech-stack:
  added: []
  patterns:
    - "Stable row-id lightbox lookup (replaces fragile DOM-order index)"
    - "Explicit data-local separation for local-vs-remote PDF branching"
    - "D-10 LOCKED byte-equivalent shard HTML (Card.astro ↔ render_card_html)"
key-files:
  created:
    - "tests/lightbox.spec.ts"
  modified:
    - "src/components/Card.astro"
    - "src/scripts/invariants.ts"
    - "src/pages/index.astro"
    - "scripts/normalize-csv.py"
decisions:
  - "Preserve data-idx + data-id alongside new data-row-id (backwards-compat for any third-party reader; openAt falls back to numeric idx if rowId lookup misses)"
  - "btn-open href='#' instead of href={url} — preventDefault already in click delegate; semantically correct anchor"
  - "btn-download href={local || url} — download prefers local file when present (CLAUDE.md §4.3)"
  - "Astro emits boolean-style data-local when value is empty string; Python emits data-local=\"\"; runtime dataset.local === '' in both cases (verified)"
metrics:
  duration: "PLACEHOLDER"
  completed: "PLACEHOLDER"
---

# Phase 4 Plan 01: Lightbox Fix Summary

One-liner: Surgical patches A–D from 04-RESEARCH.md §7 fix data-idx drift (Bug 1) and remote-PDF blank-iframe (Bug 2); adds tests/lightbox.spec.ts Playwright spec; preserves all 8 CLAUDE.md §7 JS invariants.

## Status: IN PROGRESS (skeleton — expanded after final task)

## Tasks Completed (running tally)

| Task | Name                                                                              | Commit  |
| ---- | --------------------------------------------------------------------------------- | ------- |
| 1    | Card.astro + render_card_html patches (data-row-id, data-url, data-local)         | b2a17b6 |
| 2    | invariants.ts openAt() + click delegate + index.astro refreshLbList()             | PENDING |
| 3    | tests/lightbox.spec.ts Playwright spec                                            | PENDING |

## Self-Check: PENDING
