---
phase: 04-full-migration-search-offline-performance
plan: "04"
subsystem: wargov-pagination
tags: [pagination, wargov, query-param, client-side-windowing, retroactive-repaging]
requirements: [SSG-09]
status: complete
dependency-graph:
  requires:
    - "04-01 (lightbox-fix — data-row-id contract on Card.astro / refreshLbList)"
  provides:
    - "?page=N pagination contract reusable by all 14 archive ports (Wave 3+)"
    - "Client-side windowing pattern over D-10 LOCKED pre-rendered shards"
    - "Custom event 'wargov:page-rendered' for downstream handler coordination"
  affects:
    - "src/pages/index.astro (IntersectionObserver block removed; pagination handler added)"
    - "tests/pagination.spec.ts (new Playwright spec, 7 tests)"
tech-stack:
  added: []
  patterns:
    - "URLSearchParams.get('page') + Math.min/Math.max clamp"
    - "history.pushState + popstate for bookmarkable client-side nav"
    - "Promise.all upfront shard fetch + display:none windowing"
    - "Custom event 'wargov:page-rendered' for cross-handler coordination"
    - "Re-entrant hash handler with opts.fromHash guard"
key-files:
  created:
    - tests/pagination.spec.ts
  modified:
    - src/pages/index.astro
decisions:
  - "Page 1 = no query OR ?page=1 (D-28)"
  - "PAGE_SIZE = 20 (D-27); 222 cards = 12 pages (last = 2 cards)"
  - "All 4 shards fetched upfront in parallel (D-33 — IntersectionObserver removed)"
  - "Hash handling re-renders to the page containing #card-<slug>, then scrollIntoView; guarded against re-entry via opts.fromHash"
  - "lbList walks ALL .arch-card regardless of display (Pitfall #6) — refreshLbList wired to the new wargov:page-rendered custom event AND the existing MutationObserver"
  - "Click delegate scoped to '#wargov-pagination a' only — prev/next/page-number anchors preventDefault + pushState"
  - "Defensive scrollTo fallback: try { scrollTo({ behavior: 'instant' }) } catch → scrollTo(0,0)"
metrics:
  duration: ~25m
  completed: 2026-05-27
---

# Phase 04 Plan 04: Wargov Re-paging Summary

Replaces the Phase 3 IntersectionObserver lazy-load on `src/pages/index.astro` with a
client-side `?page=N` pagination handler. PAGE_SIZE drops from 50 to 20 so the footer
is reachable on every page; the URL is bookmarkable; browser back/forward + `#card-<slug>`
anchors continue to work; and the lightbox prev/next arrows cross page boundaries because
`window.__lbList` walks the entire 222-card universe (including `display: none` cards).

Establishes the pagination contract that all 14 archive ports in Wave 3+ inherit
(see 04-PATTERNS.md §1 "wargov-everything-as-template").

## Tasks Completed

- [x] Task 1 — Replace IntersectionObserver block with `?page=N` handler + nav markup (commit `08d315b`)
- [x] Task 2 — Add `tests/pagination.spec.ts` (7 tests) covering URL, popstate, hash, footer, lightbox cross-page (commit `f9100bc`)

## Commits

| Task | Hash      | Subject |
|------|-----------|---------|
| 1    | `08d315b` | feat(04-04): replace IO lazy-load with ?page=N client-side pagination |
| skel | `c4fa172` | docs(04-04): seed SUMMARY skeleton (#2070 — write before narrate) |
| 2    | `f9100bc` | test(04-04): add pagination.spec.ts — URL, popstate, hash, footer, lightbox cross-page |

## Implementation Notes

### 1. Pagination handler structure

Located in `src/pages/index.astro` between the `<Lightbox />` mount and the existing
filter/sort progressive-enhancement block. The handler is a single `<script is:inline>`
IIFE (D-21..D-23 — no client:* directives, no module-system reliance, no Vite bundler
touch). Constants and shape:

```text
PAGE_SIZE = 20                              (D-27)
manifest  = JSON.parse(#wargov-shards)      (existing — shape: [{ file, index }, …])
allShardsLoaded = Promise.all(manifest.map(s => fetch('/'+s.file).then(.json)))
materialised = false                        (one-shot guard)
ensureCardsMaterialised()                   (awaits Promise.all + insertAdjacentHTML)
renderPage(pageNum, opts)                   (display-toggles + nav + scroll)
renderPaginationNav(current, total)         (innerHTML: prev / 1..N / next)
readPage()                                  (URLSearchParams + clamp >= 1)
```

The data flow:

1. On script init, kick `allShardsLoaded` (parallel fetch of 4 shards; ~250 KB total).
2. Wire the click delegate (`#wargov-pagination a` only) and `popstate` listener.
3. Call `renderPage(readPage())` — initial render path.
4. `renderPage` awaits `ensureCardsMaterialised` (idempotent — only the first call does
   work; subsequent calls return immediately because `materialised = true`).
5. Toggle `display: ''` / `display: 'none'` over `cards[start..end]`; render nav.
6. Hash branch: if `location.hash` and the target card is on a different page,
   re-call `renderPage(targetPage, { fromHash: true })` then `scrollIntoView`.
7. Dispatch `wargov:page-rendered` custom event — picked up by `refreshLbList`.

### 2. D-10 LOCKED preserved

The only HTML-producing operation in the handler is
`grid.insertAdjacentHTML('beforeend', card.html)` against the pre-rendered shard HTML
strings produced by `scripts/normalize-csv.py:render_card_html()` at build time.
Zero client-side templating. The verify grep
`grep -c "function templ.*ateCard"` returns 0 in `src/`. The string `templateCard`
appears once in `src/pages/index.astro` — inside a comment line forbidding it.

### 3. Lightbox + Pitfall #6 integration

The existing `refreshLbList()` (preserved from Plan 04-01) already walks
`grid.querySelectorAll('.arch-card')` (NOT `:visible`), so it picks up cards even when
they are `display: none`. The pagination handler emits a new
`wargov:page-rendered` CustomEvent after each render; the refreshLbList block adds a
listener for it so the lbList is always in sync with the current 222-card universe.
(The existing MutationObserver also catches each shard insertion, so refreshLbList
runs many times during initial materialisation — idempotent.)

Test 7 verifies the contract: opening the 20th visible card (r020, last on page 1)
and pressing ArrowRight advances the lightbox counter to `21 / 222` — the lightbox
moves to r021 which is currently `display: none` because it lives on page 2.

### 4. Custom event coordination

Why a CustomEvent instead of a direct function call? The pagination handler runs in
its own IIFE and `refreshLbList` is closed over by a different IIFE (the filter/sort
block). They don't share a scope. A grid-scoped CustomEvent is the cleanest cross-IIFE
hand-off, requires no global namespace pollution, and stays consistent with the
existing `MutationObserver` pattern (both fire on `grid`).

### 5. URL contract

- Page 1: bare `/` OR `/?page=1` — both render the first 20 cards. The handler reads
  `URLSearchParams.get('page') || '1'` so absent / blank / non-numeric → 1.
- Pages 2..12: `/?page=N` — handler clamps to `[1, totalPages]`.
- Hash-only: `/#card-<slug>` — handler detects the hash, finds the card's idx in the
  full 222-card walk, computes `Math.floor(idx/PAGE_SIZE)+1`, re-renders that page,
  then `scrollIntoView({ block: 'start' })`.
- URL-CONTRACT.txt unaffected per D-29 (only paths participate in that contract;
  query strings are out of scope).

### 6. Filter/sort interaction (known limitation, out of scope)

The existing filter/sort handler (lines 355..481) toggles `display` on cards based on
the active tab and agency dropdown. The pagination handler ALSO toggles `display`.
Both handlers compete: if a user clicks the PDF tab, the filter handler hides
non-PDF cards; if pagination then re-renders, it will overwrite that with its
20-card window. This interaction is outside the Plan 04-04 scope per the plan's
`files_modified` constraint and `<action>` directive ("Locate and DELETE the existing
IntersectionObserver block. The shards manifest is PRESERVED."). The plan does not
ask for filter-aware pagination; that would be a future plan if needed.

For the wargov page today, filter/sort and pagination both operate but the last
event wins. The pagination tests don't exercise filter/sort, and `tests/lightbox.spec.ts`
Test 4 (filter + lightbox) operates inside a single rendered page so the conflict
doesn't surface.

## Deviations from Plan

### Auto-fixed / minor scope additions

**1. [Rule 3 - Tooling] Installed `@astrojs/check` dev dependency to run `pnpm exec astro check`**
- **Found during:** Task 1 verify gate (the planned `pnpm exec astro check` command).
- **Issue:** `node_modules` did not exist in the worktree; after `pnpm install`, `astro check` prompted to install `@astrojs/check` interactively (blocks non-interactive CI).
- **Fix:** Ran `pnpm add -D @astrojs/check` to install the typechecker non-interactively.
- **Files modified:** `package.json` + `pnpm-lock.yaml` (local-only — NOT committed to keep the plan strictly within `files_modified`).
- **Commit:** none — left in working tree; orchestrator / next agent may commit if they choose.

**2. [Scope - Custom event] Added `wargov:page-rendered` CustomEvent + listener**
- **Found during:** Task 1 design (Pitfall #6).
- **Issue:** The plan's `<action>` directs us to "update refreshLbList" but refreshLbList already walks all cards correctly (post Plan 04-01). The remaining gap was *when* to call refreshLbList after a page change (the MutationObserver only fires on `childList` mutations — but `display` toggles don't add/remove children).
- **Fix:** Dispatch a `wargov:page-rendered` CustomEvent from the pagination handler; add an `addEventListener` for it on the existing refreshLbList block. Idempotent — fires more often than strictly necessary but never produces wrong state.
- **Files modified:** `src/pages/index.astro` (same file as Task 1; same commit `08d315b`).
- **Tracked as:** Rule 2 (correctness — without this, lbList could go stale on first page change before any DOM-child mutation).

**3. [Scope - Defensive scrollTo fallback]**
- **Found during:** Task 1 implementation.
- **Issue:** `behavior: 'instant'` is a relatively new CSS option; older WebKit may not accept it.
- **Fix:** Wrap `scrollTo({ top: 0, behavior: 'instant' })` in try/catch with fallback to `scrollTo(0, 0)`.
- **Files modified:** `src/pages/index.astro`.
- **Tracked as:** Rule 2 (correctness — guarantees a scroll-to-top happens on every page change).

### Out of scope, documented for future plans

**Filter/sort × pagination interaction.** As above (Implementation Notes §6).
A future plan may want filter-aware pagination (the visible cards count for the
filter would drive the totalPages). Not in 04-04's `files_modified` scope.

## Authentication Gates

None encountered.

## Known Stubs

None.

## Threat Flags

None — the pagination handler only reads URL search params (clamped to `[1, totalPages]`)
and toggles `display` on already-trusted DOM nodes. T-04-15..T-04-18 from the threat
register all have their mitigations in place:

| Threat ID | Mitigation status |
|-----------|-------------------|
| T-04-15 (page param tampering) | Mitigated — `parseInt` + `isNaN` fallback + `Math.max(1, …)` + `Math.min(totalPages, …)` clamp |
| T-04-16 (untrusted shard JSON) | Mitigated — shards emitted by build-time `scripts/normalize-csv.py`; runtime ONLY calls `insertAdjacentHTML` on `card.html` (D-10 LOCKED, html.escape'd at build) |
| T-04-17 (hash injection) | Accepted — `location.hash` used only as `querySelector(hash)` argument; wrapped in try/catch for malformed selectors |
| T-04-18 (DoS via Promise.all blocking first paint) | Mitigated — first 50 cards are server-rendered so first paint is unaffected; shards 51-222 are off-screen on page 1 |

## Self-Check: PASSED

**Created files exist:**

```
FOUND: tests/pagination.spec.ts
FOUND: .planning/phases/04-full-migration-search-offline-performance/04-04-SUMMARY.md
```

**Commits exist:**

```
FOUND: 08d315b feat(04-04): replace IO lazy-load with ?page=N client-side pagination
FOUND: c4fa172 docs(04-04): seed SUMMARY skeleton (#2070 — write before narrate)
FOUND: f9100bc test(04-04): add pagination.spec.ts — URL, popstate, hash, footer, lightbox cross-page
```

**Acceptance gates:**

```
PASS  grep -c 'wargov-pagination' src/pages/index.astro          → 3 (>= 1)
PASS  grep -E 'const PAGE_SIZE *= *20' src/pages/index.astro     → 1 match
PASS  grep -c 'URLSearchParams' src/pages/index.astro            → 1 (>= 1)
PASS  grep -c 'popstate' src/pages/index.astro                   → 2 (>= 1)
PASS  grep -c 'new IntersectionObserver' src/pages/index.astro   → 0 (must be 0)
PASS  grep -c querySelectorAll('.arch-card') in src/pages/index  → 4 (>= 1)
PASS  pnpm exec astro check                                       → 0 errors, 0 warnings
PASS  pnpm build                                                  → exit 0
PASS  dist/index.html SSR card count                              → 50 (D-32 unchanged)
PASS  dist/index.html contains nav#wargov-pagination + PAGE_SIZE  → yes
PASS  dist/index.html grep IntersectionObserver                   → 0
PASS  pnpm exec playwright test tests/pagination.spec.ts --list   → 7 tests
PASS  pnpm exec tsc --noEmit                                      → exit 0
PASS  tests/lightbox.spec.ts unmodified                           → no diff
PASS  Scope guard — no STATE.md / ROADMAP.md / scripts/ touched   → confirmed
```

**Out-of-scope guard:** files touched by this plan's commits:

```
.planning/phases/04-full-migration-search-offline-performance/04-04-SUMMARY.md
src/pages/index.astro
tests/pagination.spec.ts
```

No modifications to: STATE.md, ROADMAP.md, scripts/*, Card.astro, Lightbox.astro,
invariants.ts, or any other Phase 4 plan artifact.
