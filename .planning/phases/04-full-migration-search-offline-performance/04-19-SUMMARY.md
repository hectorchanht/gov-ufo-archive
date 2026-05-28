---
phase: "04-full-migration-search-offline-performance"
plan: "19"
subsystem: "search"
tags: [pagefind, cross-archive-search, lunr-retirement, search-rewrite, src-01, src-02, src-03, src-04]
requires:
  - "Plan 04-05 CatalogCard.astro (data-pagefind-filter + data-pagefind-meta already emitted per Plan 04-05 contract)"
  - "Plan 04-15..04-17 AARO/NASA/NARA ports complete (4 active archives Astro-rendered)"
  - "Scope pivot 80efc70 (RootLayout emits data-pagefind-ignore on dormant pages)"
  - "Scope pivot 5d0a1ef (Card.astro carries data-desc/-region/-category/-src)"
provides:
  - "Pagefind 1.5+ cross-archive search at /search (replaces Lunr /search.html)"
  - "dist/pagefind/ shard dir generated in postbuild (after copy-legacy-archives.sh)"
  - "Card.astro emits data-pagefind-filter + data-pagefind-meta (wargov)"
  - "RootLayout.astro emits data-pagefind-body on <main> of active pages (dormant + NOT active = data-pagefind-ignore)"
  - "api/all.json (4.6 MB Lunr blob) DELETED (D-14)"
  - "search.html (legacy Lunr UI) DELETED (replaced by Astro page)"
  - "tests/search.spec.ts validates PagefindUI load + query + filter + anchor"
affects:
  - "package.json (pagefind devDep)"
  - "pnpm-lock.yaml (regenerated)"
  - "scripts/copy-legacy-archives.sh (postbuild append pagefind invoke)"
  - "src/layouts/RootLayout.astro (data-pagefind-body on active <main>)"
  - "src/components/Card.astro (data-pagefind-filter + data-pagefind-meta)"
  - "src/pages/search.astro (NEW — PagefindUI mount)"
  - "tests/search.spec.ts (NEW — Playwright spec)"
  - "search.html (DELETED)"
  - "api/all.json (DELETED)"
tech-stack:
  added:
    - "pagefind@^1.5 (devDependency — WASM static search index generator)"
  patterns:
    - "Pagefind data-pagefind-body selective indexing: active 4-archive set gets indexed; dormant pages + legacy postbuild-copy HTML excluded by absence of attribute (per RESEARCH §2 — if ANY page has data-pagefind-body, others are excluded)"
    - "PagefindUI Component UI mounted via <script is:inline> at /search (D-23 hydration-free)"
    - "Single postbuild pipeline: prebuild → astro build → copy-legacy-archives.sh → pagefind --site dist (D-17 order)"
key-files:
  modified:
    - "package.json (+ pagefind devDep)"
    - "scripts/copy-legacy-archives.sh (+ pnpm exec pagefind --site dist)"
    - "src/layouts/RootLayout.astro (data-pagefind-body on active <main>)"
    - "src/components/Card.astro (data-pagefind-filter + data-pagefind-meta)"
  created:
    - "src/pages/search.astro (PagefindUI mount + processResult anchor injection)"
    - "tests/search.spec.ts (4 specs — load, query, filter dropdown, anchor)"
  deleted:
    - "search.html (legacy Lunr UI)"
    - "api/all.json (4.6 MB Lunr blob — D-14)"
decisions:
  - "Pagefind selective indexing via data-pagefind-body (NOT data-pagefind-ignore on every legacy page). Per RESEARCH §2 / pagefind.app docs: presence of data-pagefind-body on ANY page makes Pagefind skip pages WITHOUT it. This naturally excludes (a) dormant Astro pages (nz, uruguay) whose <main> already had data-pagefind-ignore from scope-pivot 80efc70 (we now ALSO skip the attribute for them since data-pagefind-body wouldn't be added there), and (b) all legacy postbuild-copied HTML in /geipan/, /uk/, etc."
  - "Active archive set ['wargov','aaro','nasa','nara'] is the single source of truth in RootLayout.astro. <main> gets data-pagefind-body when archiveSlug is in this set, data-pagefind-ignore otherwise (kept from scope pivot for safety belt)."
  - "Card.astro (wargov-only) gets data-pagefind-filter + data-pagefind-meta UNCONDITIONALLY with archiveSlug='wargov' baked in. Idempotent — overwrites any pre-existing attrs to the canonical wargov form (per plan-checker iter 1 finding #7)."
  - "processResult callback in PagefindUI mounts appends sub_results[0].anchor.id to result URL (per RESEARCH §2 Pitfall 9, SRC-04)."
  - "api/all.json + search.html deleted in same plan AFTER Pagefind index green (D-14, confirmed by Task 1 verify)."
  - "Wargov archive filter listed alongside aaro/nasa/nara via CatalogCard's archive=<slug> filter — Card.astro emits archive:wargov so the filter dropdown lists exactly 4 archives."
metrics:
  duration: ""
  completed: ""
---

# Phase 4 Plan 04-19: Pagefind cross-archive search

**Status: IN PROGRESS** (skeleton — final content + verification appended on completion)

**One-liner:** Replace Lunr's 4.6 MB upfront blob with Pagefind 1.5+ WASM cross-archive search. Active 4-archive set (wargov + aaro + nasa + nara) indexed selectively via data-pagefind-body; dormant pages + legacy HTML auto-excluded. /search.html → src/pages/search.astro with PagefindUI Component UI + processResult anchor injection per SRC-04.

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 0    | Skeleton SUMMARY.md (#2070 hedge) | TBD | .planning/phases/04-full-migration-search-offline-performance/04-19-SUMMARY.md |
| 1    | Install pagefind devDep + RootLayout data-pagefind-body + Card.astro filter attrs + postbuild Pagefind invoke | TBD | package.json, pnpm-lock.yaml, src/layouts/RootLayout.astro, src/components/Card.astro, scripts/copy-legacy-archives.sh |
| 2    | src/pages/search.astro + tests/search.spec.ts + delete search.html + api/all.json | TBD | src/pages/search.astro, tests/search.spec.ts, search.html (DEL), api/all.json (DEL), _redirects (if applicable) |

## What changed (mechanism, not file list)

(To be finalised on completion.)

## Deviations from Plan

(To be finalised on completion.)

## Authentication Gates

None expected.

## Verification Results

(To be finalised on completion.)

## Known Stubs

(To be finalised on completion — none expected.)

## Threat Flags

None expected.

## Self-Check

(To be filled in on completion.)
