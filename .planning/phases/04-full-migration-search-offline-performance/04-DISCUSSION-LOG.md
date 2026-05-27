# Phase 4: Full Migration, Search, Offline, Performance — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in 04-CONTEXT.md — this log preserves the conversation.

**Date:** 2026-05-27
**Phase:** 04-full-migration-search-offline-performance
**Mode:** discuss (default)

## Pre-Discussion State

**User-supplied locked decisions (from `/gsd:discuss-phase 4` args):**
1. R2 storage for ALL assets (PDFs + videos + thumbnails) — REQUIRED
2. Lightbox broken on preview `https://1c266693.realufo.pages.dev` — MUST fix
3. Pagination missing — MUST add

**Carried forward from prior phases:**
- Phase 1 PMS-01 URL-CONTRACT.txt locked
- Phase 2 D-17 operator-only baseline invariant
- Phase 3 D-10 LOCKED server-side card HTML shards
- Phase 3 03-04 shared layouts + JS invariants + tone-colour map
- Phase 3 03-05 Card + Lightbox + HeroCarousel components reusable
- Phase 3 03-06 SUMMARY §Open questions 1-10 (4 legacy tone-colour fixes, `_headers`, /sw.js 200, SW lifecycle, postbuild hook retirement)

**Scope expansion flag:**
- R2 for ALL assets exceeds PROJECT.md §STACK target ("R2 for >2 GB overflow only"). User confirmed Phase 4 supersedes — see D-01.

## Round 1 — 4 gray areas presented

### Q1: R2 binary CDN strategy
- Options: Full migration / Hybrid 25 MiB threshold / Mixed (R2 for videos+PDFs, dist for thumbs)
- **User chose:** Full migration: R2 primary, GH Releases archived
- Locked as D-01

### Q2: 14-archive port (SSG-06)
- Options: 14 plans by complexity tier / 4-5 grouped plans / Big bang single plan
- **User chose:** One plan per archive (14 plans, parallel by complexity tier)
- Locked as D-07, D-08

### Q3: Pagefind search architecture
- Options: Single cross-archive index / Per-archive indexes + meta / Defer to Phase 5
- **User chose:** Single cross-archive index
- Locked as D-12

### Q4: Service Worker rollout
- Options: vite-pwa injectManifest + R2 allowlist / vite-pwa generateSW (workbox) / Defer to Phase 4.5
- **User chose:** vite-pwa injectManifest + R2 origin allowlist
- Locked as D-18

## Round 2 — 4 sharp follow-ups

### Q5: R2 URL serving
- Options: Custom domain `assets.realufo.org` / `pub-<hash>.r2.dev` default / Worker proxy `/assets/*`
- **User chose:** Custom domain `assets.realufo.org`
- Locked as D-02

### Q6: R2 upload pipeline
- Options: GH Actions on push to main / Operator-manual sync-r2.sh / Workers cron (Phase 5)
- **User chose:** GH Actions workflow on push to main
- Locked as D-03, D-04

### Q7: Python script retirement (SSG-10)
- Options: Inside each per-archive port plan / Batch in Plan 04-99-cleanup
- **User chose:** Inside each per-archive port plan
- Locked as D-09

### Q8: Pagination model
- Options: Lazy-load + 'Load more' fallback / Explicit page-num URL replacing lazy-load / Both hybrid
- **User chose (correcting orchestrator framing):** "lazy load is fired but it should show 20 each page so user can scroll to the bottom footer easier without going through all the assets first . explicit page num on url"
- Locked as D-27..D-33:
  - PAGE_SIZE = 20 cards/page (Phase 3 wargov shipped 50)
  - `?page=N` query parameter (bookmarkable)
  - Footer reachable from every page (no infinite-scroll trap)
  - Lazy-load dropped for paginated routes; Astro `[...page].astro` SSR each page
  - Wargov retroactively re-paged via separate Plan 04-wargov-repaging

## Claude's Discretion (no follow-up needed)

- Per-plan task breakdown (executor decides)
- Pagefind UI component styling (preserve current /search.html UX)
- SW precache manifest exact format (vite-pwa defaults)
- `wrangler r2 bucket cors` exact config (sensible defaults per CF docs)
- R2 upload workflow diff detection method (researcher TBD)

## Deferred Ideas (out of Phase 4 scope)

| Idea | Reason | Phase |
|------|--------|-------|
| DNS swap GH Pages → CF Pages | D-37 invariant; Phase 6 HOST-01 | 6 |
| CF Pages git-integration | Operational, push-access dependent | n/a |
| Scrape pipeline → R2 direct write | Phase 5 SCRP scope | 5 |
| Additional national archives (#16+) | Future milestone | post-v1 |
| Frank GH write access on hectorchanht repo | Operational | n/a |

## Source Material

- ROADMAP.md §Phase 4 (22 requirements)
- REQUIREMENTS.md lines 37-90 (SSG/SRC/SW/PERF detail)
- PROJECT.md §Active + §Out of Scope (milestone boundary)
- 03-06-SUMMARY §Open questions 1-10 (carryover items)
- 03-CONTEXT.md D-01..D-40 (Phase 3 LOCKED decisions)
- CLAUDE.md §3, §4, §5, §7, §8, §9, §11 (locked invariants)
- User feedback on preview `https://1c266693.realufo.pages.dev` and `https://e0196623.realufo.pages.dev`
