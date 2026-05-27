---
phase: 04-full-migration-search-offline-performance
plan: "04"
subsystem: wargov-pagination
tags: [pagination, wargov, query-param, client-side-windowing, retroactive-repaging]
requirements: [SSG-09]
status: in-progress
dependency-graph:
  requires:
    - 04-01 (lightbox-fix — data-row-id contract on Card.astro / refreshLbList)
  provides:
    - "?page=N pagination contract for all 14 archive ports (Wave 3+)"
    - "client-side windowing pattern over D-10 LOCKED pre-rendered shards"
  affects:
    - src/pages/index.astro (IntersectionObserver removed)
    - tests/pagination.spec.ts (new Playwright spec)
tech-stack:
  added: []
  patterns:
    - "URLSearchParams.get('page') + Math.min/Math.max clamp"
    - "history.pushState + popstate for bookmarkable client-side nav"
    - "Promise.all upfront shard fetch + display:none windowing"
    - "Custom event 'wargov:page-rendered' for cross-handler coordination"
key-files:
  created:
    - tests/pagination.spec.ts
  modified:
    - src/pages/index.astro
decisions:
  - "Page 1 = no query OR ?page=1 (D-28)"
  - "PAGE_SIZE = 20 (D-27); 222 cards = 12 pages (last = 2)"
  - "All shards fetched upfront in parallel (D-33 — IntersectionObserver removed)"
  - "Hash handling re-renders to the page containing #card-<slug> + scrollIntoView"
  - "lbList walks ALL .arch-card regardless of display (Pitfall #6)"
metrics:
  duration: TBD
  completed: TBD
---

# Phase 04 Plan 04: Wargov Re-paging Summary

PAGE_SIZE drops from 50 to 20; URL-driven `?page=N` pagination handler replaces the
Phase 3 IntersectionObserver lazy-load on `src/pages/index.astro` so the footer is
reachable on every page, the URL is bookmarkable, browser back/forward works, and
`#card-<slug>` anchors resolve cross-page.

## Tasks Completed

- [x] Task 1 — Replace IntersectionObserver block with `?page=N` handler + nav markup (commit 08d315b)
- [ ] Task 2 — Add `tests/pagination.spec.ts` (≥7 tests) (pending)

## Commits

| Task | Hash | Subject |
|------|------|---------|
| 1 | 08d315b | feat(04-04): replace IO lazy-load with ?page=N client-side pagination |
| 2 | TBD | test(04-04): add tests/pagination.spec.ts covering URL, popstate, hash, footer, lightbox-cross-page |

## Implementation Notes

(populated after Task 2 completes)

## Deviations from Plan

(populated after Task 2 completes)

## Self-Check

(populated after Task 2 completes)
