---
phase: 04-full-migration-search-offline-performance
plan: "03"
subsystem: service-worker
tags: [service-worker, vite-pwa, workbox, fonts, offline-first, headers]
status: in-progress
requires:
  - "Plan 03-01 astro.config.mjs baseline"
  - "Plan 03-04 BaseHead.astro SW registration"
  - "Plan 02-01 _headers /sw.js no-cache rule"
provides:
  - "dist/sw.js — Workbox-based SW with 5 runtime cache strategies"
  - "Self-hosted fonts via @fontsource (offline-first)"
  - "public/_headers — copied so dist/_headers ships with /sw.js no-cache"
  - "tests/sw.spec.ts — Playwright SW lifecycle coverage"
affects:
  - "All Astro pages register /sw.js via BaseHead.astro (D-19)"
  - "Closes 12-of-32-pages SW registration gap from CONCERNS.md"
tech-stack:
  added:
    - "@vite-pwa/astro@1.2.0"
    - "workbox-precaching@7.4.1"
    - "workbox-routing@7.4.1"
    - "workbox-strategies@7.4.1"
    - "workbox-cacheable-response@7.4.1"
    - "workbox-expiration@7.4.1"
    - "@fontsource/source-serif-4 (pending Task 2)"
    - "@fontsource/jetbrains-mono (pending Task 2)"
  patterns:
    - "Workbox 7 injectManifest with custom sw.ts"
    - "Inline Astro integration for build:done hook (CF adapter workaround)"
decisions:
  - "D-18..D-26 SW config implemented"
  - "Pitfall #4 — ALLOW_SKIP_WAITING=false on first deploy"
key-files:
  created:
    - "src/sw.ts"
    - "public/_headers (pending Task 2)"
    - "tests/sw.spec.ts (pending Task 3)"
  modified:
    - "astro.config.mjs"
    - "src/layouts/BaseHead.astro (pending Task 2)"
    - "package.json"
    - "pnpm-lock.yaml"
metrics:
  completed: "in-progress"
---

# Phase 4 Plan 03: Service Worker via @vite-pwa/astro injectManifest Summary

Wire `@vite-pwa/astro` injectManifest SW so every Astro page registers `/sw.js` from BaseHead.astro (closes the 12-of-32-pages registration gap from CONCERNS.md), implement five tiered cache strategies per D-21 (NetworkFirst HTML, SWR JSON, CacheFirst images/fonts, NetworkOnly PDFs/videos, NetworkOnly admin/dev), swap Google Fonts for self-hosted `@fontsource`, and copy `_headers` into `public/` so `dist/_headers` ships with the Phase 1 PMS-02 `/sw.js` no-cache invariant.

## Status

**In progress.** This skeleton SUMMARY exists per execute-plan #2070 hedge — full content lands after Task 3 completes.

## Tasks

- [x] **Task 1** — Install deps + patch astro.config.mjs + ship src/sw.ts skeleton (commit `6d550fa`)
- [ ] **Task 2** — Swap Google Fonts for @fontsource + copy _headers into public/
- [ ] **Task 3** — Add tests/sw.spec.ts covering SW lifecycle

## Deviations from Plan

To be filled in after Task 3.
