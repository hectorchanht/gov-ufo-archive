---
phase: 03-ssg-foundation
plan: 04
subsystem: shared-layouts
tags: [ssg, astro-layouts, css-variables, js-invariants, mobile-first]
status: in-progress
requirements: [SSG-03, SSG-04]
key-files:
  created:
    - src/styles/global.css
    - src/scripts/invariants.ts
    - src/layouts/BaseHead.astro
    - src/layouts/RootLayout.astro
    - src/components/Nav.astro
    - src/components/Footer.astro
  modified: []
---

# Phase 3 Plan 04: Shared Layout Components Summary

One-liner: Four Astro layout/component files + global stylesheet + JS-invariants reference module form the SSG single-source-of-truth that retires sync-nav.py + sync-footer.py.

Skeleton placeholder — expanded in follow-up commit per worktree time-budget protocol.
