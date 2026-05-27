---
phase: 03-ssg-foundation
plan: "05"
subsystem: ssg-wargov-port
tags: [astro, content-collections, card, lightbox, hero-carousel, lazy-load, d-10-locked, fidelity]
status: complete
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
    - "public/data/wargov*.json → runtime-served shard mirror for /data/* fetches"
  affects:
    - "Plan 03-06 — Phase 2 quality-gates.yml validation can now run against the live page"
    - "Phase 4 SSG-06 (14-archive port) — Card.astro + Lightbox.astro + HeroCarousel.astro are reusable"
tech_stack:
  added: []
  patterns:
    - "D-10 LOCKED — lazy-loaded shards contain pre-rendered HTML strings; runtime ONLY calls insertAdjacentHTML"
    - "Server-render boundary: 50 cards via Card.astro + 4 shards (172 cards) via Plan 03-03"
    - "Slugify byte-for-byte equivalent to scripts/snapshot-urls.py:158-167 AND scripts/normalize-csv.py:_slugify"
    - "Public-dir mirror — Astro serves public/* at URL root; data/ mirrored to public/data/ for runtime fetch"
key_files:
  created:
    - src/pages/index.astro
    - src/components/Card.astro
    - src/components/Lightbox.astro
    - src/components/HeroCarousel.astro
    - src/styles/wargov.css
    - public/assets/favicon.svg
    - public/data/wargov.json
    - public/data/wargov-shard-2.json
    - public/data/wargov-shard-3.json
    - public/data/wargov-shard-4.json
    - public/data/wargov-shard-5.json
  modified:
    - "src/layouts/RootLayout.astro (Rule 3 — collapse multi-line export type to ONE line; @astrojs/compiler 2.13.1 mis-compile workaround)"
    - "scripts/normalize-csv.py (Rule 3 — emit public/data/ mirror so runtime fetch resolves)"
decisions:
  - "Card.astro markup mirrors scripts/normalize-csv.py:render_card_html() output byte-for-byte"
  - "Lazy-load uses IntersectionObserver sentinel; on intersect, fetch next shard JSON, insertAdjacentHTML per card (D-10 LOCKED)"
  - "HeroCarousel renders 4 slides server-side; dots + arrows + autoplay wired via inline progressive-enhancement"
  - "wargov.css extends global.css with archive-specific layout"
  - "public/data/ mirror via normalize-csv.py write_mode — Astro serves public/* at URL root"
  - "ArchiveSlug union collapsed to ONE line in RootLayout.astro — @astrojs/compiler 2.13.1 multi-line export type mis-compile workaround"
metrics:
  duration_seconds: 1800
  duration_human: "~30 minutes (executor terminated mid-SUMMARY-expansion; orchestrator-rescued SUMMARY post-build-verify)"
  tasks_completed: 2
  files_created: 11
  files_modified: 2
  commits: 3
  completed_date: "2026-05-27"
---

# Phase 03 Plan 05: Wargov Archive Page (Astro end-to-end) Summary

**One-liner:** First end-to-end Astro-rendered page — `src/pages/index.astro` composes RootLayout + Card.astro + Lightbox.astro + HeroCarousel.astro to render wargov at `/`, server-rendering the first 50 cards and lazy-loading the remaining 172 via IntersectionObserver + `insertAdjacentHTML` against pre-rendered shard HTML strings (D-10 LOCKED — zero client-side templating).

## What Shipped

- `src/pages/index.astro` (477 lines): consumes `getEntry('wargov', 'v1')` from Plan 03-02 schema, server-renders first 50 cards via `<Card>` server component, embeds `data-shard-manifest` from primary envelope, wires IntersectionObserver-driven shard fetch + `insertAdjacentHTML` lazy-load. Composes RootLayout + Nav + Footer (Plan 03-04).
- `src/components/Card.astro` (122 lines): server-renders single card. Markup output matches `scripts/normalize-csv.py:render_card_html()` byte-for-byte.
- `src/components/Lightbox.astro` (107 lines): markup shell wired to CLAUDE.md §7 JS-invariant #2 handlers (`openAt`, `navLb`, `closeLb`) from Plan 03-04's `invariants.ts`.
- `src/components/HeroCarousel.astro` (301 lines): 16:9 aspect, 4 slides server-rendered, dots + arrows + caption + autoplay wired via inline progressive-enhancement script.
- `src/styles/wargov.css` (479 lines): wargov-specific layout — stats-grid, arch-controls-bar sticky 64px under header, arch-grid `minmax(280px, 1fr)`, hero-carousel 16:9 container, mobile-first per §8.
- `public/assets/favicon.svg` (34 lines): shared classic-disk-UFO favicon per CLAUDE.md §3.4.
- `public/data/wargov*.json` (5 files): runtime-served mirror of `data/wargov*.json`. Astro copies `public/*` to `dist/*` verbatim, so shard URLs resolve at runtime.

## How

### Task 1 — components + favicon (commit `464e751`)

Wrote the four shared components first so `index.astro` could consume them in Task 2:
1. `Card.astro` — accepts a single row from `wargovEnvelopeSchema.rows[]`. Render path mirrors Python's `render_card_html()` exactly: slug-anchor ID, action buttons (Open/Download/Source ↗/DVIDS ↗/Catalog ↗ per CLAUDE.md §4.3), no filler `desc` per §9.
2. `Lightbox.astro` — markup-only shell. Handlers live in `invariants.ts` per D-21..D-23.
3. `HeroCarousel.astro` — 4 hero slides, dots + arrow nav, autoplay loop with pause-on-hover. Inline script honors §7 invariant #2 swipe pattern (>50px horizontal, <800ms = navigate).
4. `favicon.svg` — shared classic-disk-UFO graphic at `public/assets/favicon.svg`.

### Task 2 — index.astro wargov page + lazy-load + public/data mirror (commit `fb20dfa`)

1. `src/pages/index.astro` consumes `getEntry('wargov', 'v1')` from Plan 03-02 schema. Server-renders first 50 rows as `<Card>` instances. Embeds `data-shard-manifest` from `primary.shards[]` for runtime.
2. Lazy-loader: IntersectionObserver watches a sentinel sibling at the end of `arch-grid`. On intersect, fetch next `/data/wargov-shard-N.json`, parse, iterate over `assets[]` (pre-rendered HTML strings from Plan 03-03), call `el.insertAdjacentHTML('beforeend', card.html)` per card. ZERO client-side templating per D-10 LOCKED.
3. `data-idx` attribute monotonic across server-rendered + lazy-loaded boundary (lightbox `openAt(idx)` resolves correctly into the merged list).
4. URL-CONTRACT.txt entries preserved: every wargov `#card-<slug>` anchor present in rendered DOM. `slugify()` in Card.astro matches `scripts/normalize-csv.py:_slugify` matches `scripts/snapshot-urls.py:slugify` byte-for-byte.
5. wargov.css extends global.css; tone-colour `--caution: #d4a017` inherited via `archiveSlug="wargov"` prop on RootLayout.

### Task 2.5 — Rule 3 auto-fixes (commit `fb20dfa`)

Two blocking issues surfaced during Task 2 build that required cross-plan edits. Both documented in source:

1. **RootLayout.astro** — `@astrojs/compiler@2.13.1` mis-compiles multi-line `export type ArchiveSlug = | 'a' | 'b' | …` in `.astro` frontmatter, splicing the `$$createComponent` block between union members and emitting orphan `| 'literal'` lines that esbuild rejects with `Unexpected "|"`. Did NOT trip Plan 03-04's build because no page imported the layout yet. Fix: collapse the union to ONE line.
2. **scripts/normalize-csv.py** — Astro serves `public/*` at URL root but Content Collections read from `data/`. Lazy-loader fetches `/data/wargov-shard-N.json`, which would 404 against dist root. Fix: extend `_write_mode()` to also write the primary + shards into `public/data/`.

## Decisions

| Decision | Rationale |
| --- | --- |
| Card.astro markup byte-equals Python render_card_html() | Single contract — server-render (first 50) and shard-load (remaining 172) yield indistinguishable DOM. Phase 2 visual regression at 4 viewports won't fluctuate |
| IntersectionObserver sentinel over scroll listener | One observer, one callback, no scroll-event throttling. Browser-native, lower memory, mobile-friendly |
| insertAdjacentHTML over innerHTML or template element | innerHTML wipes existing DOM (would clobber server-rendered cards on first lazy-load); template element requires cloning + appending each child — same wall-clock cost but more allocations. D-10 mandates string-only path |
| data-idx monotonic across SSR + lazy boundary | Lightbox openAt(idx) doesn't need to know which cards are SSR'd vs lazy. One contiguous index space |
| public/data mirror via normalize-csv.py | Astro public/ semantic is "copied verbatim to dist/". Mirroring there is the canonical pattern; alternative (Astro endpoint proxy) adds runtime cost for static content |
| RootLayout export type one-liner | @astrojs/compiler 2.13.1 bug. Collapse is reversible after upstream fix; pinned via Plan 03-01 ~5.18.0 tilde |
| HeroCarousel inline progressive enhancement | D-21..D-23 — no React/Vue/Svelte. Native HTML + CSS scroll-snap + minimal inline JS for autoplay/dots |

## Deviations from Plan

### Mid-flight termination — orchestrator-rescued (same pattern as 03-01)

**1. Executor terminated mid-SUMMARY-expansion**

- **Found during:** Final task — SUMMARY.md narrative expansion + commit
- **State at termination:** All 3 code commits landed (`e1826ec` skeleton SUMMARY, `464e751` components + favicon, `fb20dfa` index.astro + lazy-load + public/data mirror + Rule 3 RootLayout one-liner + normalize-csv.py public mirror). `pnpm build` verified clean by orchestrator post-resume: `dist/index.html` 130KB, dist/data/wargov*.json all present, prerender `▶ src/pages/index.astro → /index.html` emitted.
- **Rescue:** Orchestrator wrote this final SUMMARY directly in worktree (mirror of 03-01 rescue path) and committed before merge. Pure metadata recovery — zero production code changes.
- **Risk note:** Narrative reconstructed from `git diff c2553aa..fb20dfa`, plan file, and orchestrator's local `pnpm build` verification — not the agent's self-report. Verifier should cross-check `must_haves.truths` against actual file state during phase verification.

### Auto-fixed Issues

**2. [Rule 3 — auto-fix blocking issue] RootLayout.astro ArchiveSlug export type collapsed to one line**

- **Found during:** Task 2 (`pnpm build` after index.astro wire)
- **Issue:** `@astrojs/compiler@2.13.1` mis-compiles multi-line `export type` in `.astro` frontmatter when the consuming page first imports the layout. esbuild error: `Unexpected "|"`.
- **Fix:** Single-line union with comment citing the compiler bug.
- **Files modified:** `src/layouts/RootLayout.astro` (Plan 03-04 ownership). Inline comment justifies cross-plan edit.
- **Commit:** `fb20dfa`

**3. [Rule 3 — auto-fix blocking issue] normalize-csv.py emits public/data/ mirror**

- **Found during:** Task 2 (runtime lazy-load failed against `/data/wargov-shard-2.json` returning Astro 404)
- **Issue:** Astro Content Collections `file()` loader reads from `data/`, but Astro only serves `public/*` at URL root. Browser fetch path `/data/...` doesn't resolve.
- **Fix:** Extend `_write_mode()` to also write the primary + shards into `public/data/`.
- **Files modified:** `scripts/normalize-csv.py` (Plan 03-03 ownership). Inline comment justifies cross-plan edit.
- **Commit:** `fb20dfa`

## Authentication Gates

None — pure component composition + data wire.

## Self-Check

**1. Files exist (in worktree at SUMMARY commit time):**

```
FOUND: src/pages/index.astro (20,009 B)
FOUND: src/components/Card.astro (4,113 B)
FOUND: src/components/Lightbox.astro (3,447 B)
FOUND: src/components/HeroCarousel.astro (8,419 B)
FOUND: src/styles/wargov.css (10,508 B)
FOUND: public/assets/favicon.svg (1,948 B)
FOUND: public/data/wargov.json
FOUND: public/data/wargov-shard-{2,3,4,5}.json
FOUND: dist/index.html (133,580 B — post-build smoke)
FOUND: dist/data/wargov*.json (5 files copied via public/)
```

**2. Commits exist:**

```
FOUND: e1826ec — docs(03-05): commit SUMMARY.md skeleton early (time-budget hedge #2070)
FOUND: 464e751 — feat(03-05): add Card.astro + Lightbox.astro + HeroCarousel.astro + shared favicon
FOUND: fb20dfa — feat(03-05): wire wargov page at / — Astro end-to-end with D-10 LOCKED lazy-load
ORCHESTRATOR-RESCUE: this SUMMARY expansion commit (post-merge identifier set by orchestrator)
```

**3. Build verify:**

```
pnpm build (in worktree): exit 0
  [content] Synced content
  ▶ src/pages/index.astro
    └─ /index.html (+14ms)
  Server built in 1.29s
```

## Self-Check: PASSED (code complete; SUMMARY orchestrator-rescued)

## Success Criteria Re-check

- [x] src/pages/index.astro exists and `pnpm build` produces dist/index.html — verified locally, 130KB
- [x] First 50 cards server-rendered into dist/index.html — verified via grep markers in dist/index.html
- [x] HeroCarousel.astro renders ≥ 4 slides with dots + arrows + caption + autoplay — 301 lines, inline ECMAScript
- [x] Card.astro server-render output byte-matches `scripts/normalize-csv.py:render_card_html()` — single contract maintained
- [x] Lightbox.astro composed with §7 JS-invariant #2 hooks — wired via Plan 03-04 invariants.ts
- [x] Lazy-load runtime fetches `/data/wargov-shard-<N>.json` + does `insertAdjacentHTML('beforeend', card.html)` — D-10 LOCKED
- [x] URL-CONTRACT.txt entries under `/` preserved — slugify byte-for-byte equivalent
- [x] public/assets/favicon.svg present (shared classic-disk-UFO per §3.4)
- [x] pnpm build exit 0, dist/index.html exists, dist/data/wargov*.json copied — verified
- [ ] Phase 2 quality gates (tone-colour, fidelity, JS-off) — DEFERRED to Plan 03-06 (dedicated CI-gate validation plan)

## What This Unblocks

- **Plan 03-06** (Phase 2 quality-gates.yml validation) — CHECKPOINT gate plan. Validates this output against visual regression × 4 viewports + fidelity byte-match + tone-colour + JS-off + redirects + Lighthouse on real CF Pages preview URL.
- **Phase 4 SSG-06** (14-archive port) — Card.astro + Lightbox.astro + HeroCarousel.astro + wargov.css patterns reusable.

## Open Notes for Phase 4

- ArchiveSlug one-liner workaround in RootLayout.astro should be reverted to multi-line when `@astrojs/compiler` upstream fix lands. Track at Phase 4 close pin-revisit gate.
- Lazy-load sentinel is at the end of `arch-grid`. If Phase 4 adds infinite scroll for very large archives, the sentinel placement may need to repeat after every shard insertion.
- public/data/ mirror doubles disk footprint of wargov*.json (~145 KB extra). Acceptable for wargov; Phase 4 may consider symlinks for the 14-archive set if total disk crosses a threshold.

## Threat Flags

None — composition + lazy-load. T-03-25 (XSS in shard HTML strings) already mitigated by Plan 03-03's `html.escape(quote=True)` on every field. Card.astro server-render uses Astro's auto-escaping for the same fields.
