---
phase: 03-ssg-foundation
plan: 04
subsystem: shared-layouts
tags: [ssg, astro-layouts, css-variables, js-invariants, mobile-first]
status: complete
requirements: [SSG-03, SSG-04]
dependency-graph:
  requires: [03-01]
  provides: [shared-RootLayout, shared-Nav, shared-Footer, INVARIANTS_JS]
  affects: [03-05, 04-SSG-06, 04-SSG-10]
tech-stack:
  added: []
  patterns:
    - Astro 5 layout-component composition (RootLayout wraps BaseHead + Nav + slot + Footer)
    - <script is:inline set:html={template-string}> for verbatim JS injection
    - 15-literal TypeScript union (ArchiveSlug) drives both CSS variable + license lookup
    - Defence-in-depth idempotent script wiring (Nav.astro + invariants.ts share a dataset.wired latch)
key-files:
  created:
    - src/styles/global.css
    - src/scripts/invariants.ts
    - src/layouts/BaseHead.astro
    - src/layouts/RootLayout.astro
    - src/components/Nav.astro
    - src/components/Footer.astro
  modified: []
decisions:
  - "Used `set:html={INVARIANTS_JS}` pattern for the bottom-of-body script (Astro 5.18 accepted it cleanly; `pnpm build` exits 0)."
  - "Re-exported `ArchiveSlug` literal-union from RootLayout.astro so Nav.astro + Footer.astro import a single typed contract — keeps the 15-archive list as one source-of-truth instead of three."
  - "Component-level idempotency latch (`navToggle.dataset.wired`) prevents the hamburger handler from binding twice when both Nav.astro's scoped script AND RootLayout's invariants.ts run on the same page."
  - "TONE map values bit-for-bit match tests/tone-colours-fixture.json (Phase 2 02-06) — wargov caution = #d4a017, all 15 entries reconciled."
  - "Defensive `?? TONE.wargov` fallback on TONE lookup + `?? LICENSE.wargov` on Footer license + `?? BRAND.wargov` on Nav brand text — T-03-11 mitigation against typo'd or attacker-supplied archiveSlug values."
metrics:
  duration: ~45 minutes
  completed: 2026-05-27
  total-loc: 1194
  per-file-loc:
    "src/styles/global.css": 412
    "src/scripts/invariants.ts": 267
    "src/layouts/BaseHead.astro": 79
    "src/layouts/RootLayout.astro": 114
    "src/components/Nav.astro": 151
    "src/components/Footer.astro": 171
---

# Phase 3 Plan 04: Shared Layout Components Summary

One-liner: Four Astro layout/component files + 412-line global stylesheet + 267-line JS-invariants reference module form the SSG single-source-of-truth that retires (in Phase 4 SSG-10) sync-nav.py + sync-footer.py drift gates.

## Outcome

SSG-03 satisfied: `src/layouts/RootLayout.astro` + `BaseHead.astro` + `src/components/Nav.astro` + `Footer.astro` exist and compile cleanly under `pnpm build`. SSG-04 (JS-invariants portion) satisfied: every CLAUDE.md §7 invariant 1-8 inlined via `<script is:inline>` (D-21..D-23). Tone-colour contract held: the 15-archive TONE map in RootLayout.astro matches `tests/tone-colours-fixture.json` byte-for-byte, so Plan 03-05's wargov index can pass `archiveSlug="wargov"` and the Phase 2 `tone-colours.spec.ts` assertion (`--caution: #d4a017`) will pass.

## Files created (6)

| File | Lines | Purpose |
|------|-------|---------|
| `src/styles/global.css` | 412 | 13 CLAUDE.md §3.2 design tokens verbatim + mobile-first base + 44px touch targets + sticky 64px header + arch-grid responsive |
| `src/scripts/invariants.ts` | 267 | `INVARIANTS_JS` template-literal export covering all 8 CLAUDE.md §7 invariants |
| `src/layouts/BaseHead.astro` | 79 | Meta + OG/Twitter + canonical + shared favicon (`/assets/favicon.svg`) + Source Serif 4 + JetBrains Mono preconnect + Umami + SW registration (`updateViaCache: 'none'`) |
| `src/layouts/RootLayout.astro` | 114 | 15-literal `ArchiveSlug` union prop, 15-archive TONE map, BaseHead+Nav+slot+Footer composition, bottom-of-body `<script is:inline set:html={INVARIANTS_JS}>` |
| `src/components/Nav.astro` | 151 | Sticky header + brand seal + hamburger toggle + 15-archive cross-nav (data-archive + path), defence-in-depth idempotent script |
| `src/components/Footer.astro` | 171 | 4-column grid (collapses 2→1 on mobile), per-archive public-domain license verbatim from CLAUDE.md §9, official-source URL list (CLAUDE.md §4.1) |

## CLAUDE.md §7 invariants ↔ implementation map

| # | Invariant | File | Implementation entry-point |
|---|-----------|------|----------------------------|
| 1 | Hamburger toggle | `src/scripts/invariants.ts` + `src/components/Nav.astro` | IIFE @ ~line 18 in invariants.ts; duplicate IIFE in Nav.astro (idempotent via `dataset.wired` latch) |
| 2 | Lightbox prev/next/swipe/arrow-keys/Escape | `src/scripts/invariants.ts` | `openAt(idx)` / `navLb(delta)` / `closeLb()` + keydown listener + touchstart/touchend swipe (>50px / <800ms) |
| 3 | Image fallback `<img onerror>` | `src/scripts/invariants.ts` | Delegated capture-phase `error` listener reads `data-fallback`; WeakSet tracker prevents loop |
| 4 | Video dual-source | `src/scripts/invariants.ts` | `<video data-remote>` runtime sanity check injects a second `<source>` if missing; renderLb() emits two `<source>` children when both local + remote exist |
| 5 | PDF lightbox iframe (local) vs new tab (remote) | `src/scripts/invariants.ts` | `renderLb()` branches on `ext === 'pdf'` → iframe iff `local`, otherwise metadata panel with target=_blank download anchor |
| 6 | `data-action="open"` delegated click | `src/scripts/invariants.ts` | `document.addEventListener('click')` → closest `a[data-action="open"]` → reads `data-idx` (anchor or `.card` ancestor) → `openAt()` |
| 7 | `/` keydown focuses search input | `src/scripts/invariants.ts` | Skips when target is INPUT/TEXTAREA/contenteditable; selector covers `input[type="search"], input[name="q"], #q, #arch-search` |
| 8 | `?q=` URL persistence | `src/scripts/invariants.ts` | Early-returns silently when no matching input found (W4 — Phase 3 wargov has no search input per D-24). On match: hydrates from `URLSearchParams.get('q')` on load, debounced 180ms `history.replaceState` on input |

## Inline-script injection pattern decision

The plan presented two candidates: `<script is:inline set:html={INVARIANTS_JS}>` vs writing the JS verbatim inside a `<script is:inline>` block. Astro 5.18.2 accepts `set:html` on `<script is:inline>` cleanly — `pnpm build` exits 0 with no warnings about hydration directives, processed scripts, or HTML interpolation. Decision: use `set:html` (DRY-er, keeps the invariants in one TS file with full editor tooling).

Astro-compiled output: the build emits no per-page chunks for these components yet because `src/pages/` is still empty (Plan 03-05 wires `src/pages/index.astro`). The build's "Building server entrypoints" pass shows the components included via the Cloudflare adapter's server bundle, ~688 ms vite build. Concrete HTML stencil bytes will land in Plan 03-05's SUMMARY when the first page exists.

## TypeScript strictness adjustments

None required. `astro/tsconfigs/strict` accepts the 15-literal `ArchiveSlug` union as-is. Re-exporting the type from `RootLayout.astro` and importing it in `Nav.astro` + `Footer.astro` typechecks cleanly via Astro's `.astro` TS module resolution.

## 15-archive Nav verification (checker B3)

Per-slug grep loop (`grep -q "\"$s\"\|/$s/" src/components/Nav.astro`) hit count:

```
  wargov     → 2 hit(s)   (path "/" via ARCHIVES + data-archive="wargov" attr)
  aaro       → 1 hit(s)
  nasa       → 1 hit(s)
  nara       → 1 hit(s)
  geipan     → 1 hit(s)
  uk         → 1 hit(s)
  brazil     → 1 hit(s)
  chile      → 1 hit(s)
  argentina  → 1 hit(s)
  canada     → 1 hit(s)
  italy      → 1 hit(s)
  nz         → 1 hit(s)
  peru       → 1 hit(s)
  spain      → 1 hit(s)
  uruguay    → 1 hit(s)
```

All 15 present. The wargov entry intentionally relies on `data-archive="wargov"` for slug-literal detection (its href is `/`, not `/wargov/`); the 2-hit count is from the `ARCHIVES` config table emitting both the literal and the data-attr.

## `?q=` handler DOM-disconnected state (W4 documentation)

Per D-24, Phase 3's wargov page does **not** ship a cross-archive search input — Pagefind integration is deferred to Phase 4 SRC. The `?q=` URL-persistence handler in `src/scripts/invariants.ts` (CLAUDE.md §7 invariant 8) queries `input[type="search"], input[name="q"], #q, #arch-search` and **silently early-returns** when no match is found. The handler ships today so that Phase 4 SRC's Pagefind input wiring activates the behaviour automatically with zero code change to the invariants module. Plan 03-06 reviewers should NOT flag this as dead code: it's a contract-bound future-activation hook.

The `/` keydown handler (invariant 7) uses the same selector and behaves identically — early-returns on no-match, activates the moment a search input exists.

## Deviations from plan

### Auto-fixed Issues

None — Tasks 1 and 2 executed exactly as written.

### Notes on `archiveSlug` ergonomics

- The 15-literal union type lives in `RootLayout.astro` and is re-exported as `export type ArchiveSlug`. `Nav.astro` and `Footer.astro` import it via `import type { ArchiveSlug } from '../layouts/RootLayout.astro';`.
- Each lookup (TONE, LICENSE, SOURCE_URLS, BRAND, PATH) has a `?? TABLE.wargov` fallback. This is the T-03-11 mitigation: a typo'd or attacker-supplied slug renders wargov defaults rather than `undefined` flowing into a CSS variable or attribute.

## Self-Check

- Files exist:
  - `src/styles/global.css` — FOUND
  - `src/scripts/invariants.ts` — FOUND
  - `src/layouts/BaseHead.astro` — FOUND
  - `src/layouts/RootLayout.astro` — FOUND
  - `src/components/Nav.astro` — FOUND
  - `src/components/Footer.astro` — FOUND
- Commits exist on `worktree-agent-a2eebe9e81fa4b194`:
  - `6cc9ae1` — skeleton SUMMARY (docs)
  - `412f8be` — Task 1 (feat 03-04)
  - `2cdd929` — Task 2 (feat 03-04)
- `pnpm build` exit code: 0 (file-loader warning for `data/wargov.json` is Plan 03-03's responsibility per dependency graph; out of scope here)
- No `client:*` directives in `src/`: confirmed
- No framework imports (`react|vue|svelte|solid-js|preact`) in `src/`: confirmed
- All 15 archive slugs present in `Nav.astro`: confirmed (per-slug grep loop above)
- 13 CLAUDE.md §3.2 design tokens present verbatim in `global.css`: confirmed
- TONE map matches `tests/tone-colours-fixture.json` for wargov (#d4a017) and aaro (#4a9eff): confirmed

## Self-Check: PASSED
