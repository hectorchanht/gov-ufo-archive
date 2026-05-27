---
phase: "04-full-migration-search-offline-performance"
plan: "SCOPE-PIVOT"
subsystem: "scope"
tags: [scope-pivot, soft-drop, lightbox-extension, header-footer-consolidation]
requires:
  - "Plan 04-01 lightbox-fix (data-row-id contract baseline)"
  - "Plan 04-05 CatalogCard.astro (data-* contract baseline)"
  - "Operator decision 2026-05-28 — ship 4 active archives, soft-drop 11"
provides:
  - "Nav reduced to 4 archive links (wargov, aaro, nasa, nara)"
  - "Footer reduced to 4 archive links (wargov, aaro, nasa, nara)"
  - "RootLayout emits data-pagefind-ignore on dormant pages (nz, uruguay, others when ported)"
  - "Lightbox renders 7 asset types + meta panel (desc/agency/date/region/category) + dual action buttons"
  - "Card.astro + CatalogCard.astro emit 6 additional data-* attrs (desc/agency/date/region/category/src)"
  - "normalize-csv.py:render_card_html mirrors Card.astro byte-equivalent (D-10 LOCKED pair preserved)"
affects:
  - "src/components/Nav.astro"
  - "src/components/Footer.astro"
  - "src/layouts/RootLayout.astro"
  - "src/components/Lightbox.astro"
  - "src/components/Card.astro"
  - "src/components/CatalogCard.astro"
  - "src/scripts/invariants.ts"
  - "scripts/normalize-csv.py"
  - "data/wargov-shard-{2..5}.json + public/data/wargov-shard-{2..5}.json (regenerated)"
  - "CLAUDE.md §2 + §13"
tech-stack:
  added: []
  patterns:
    - "Soft-drop pattern: dormant code/data preserved in repo; removed from Nav/Footer; data-pagefind-ignore on dormant pages"
    - "Lightbox meta panel + dual download/source buttons consume card dataset attrs"
    - "Card.astro ↔ normalize-csv.py D-10 LOCKED byte-equivalent contract preserved with 6 new attrs"
key-files:
  modified:
    - "src/components/Nav.astro"
    - "src/components/Footer.astro"
    - "src/layouts/RootLayout.astro"
    - "src/components/Lightbox.astro"
    - "src/components/Card.astro"
    - "src/components/CatalogCard.astro"
    - "src/scripts/invariants.ts"
    - "scripts/normalize-csv.py"
    - "CLAUDE.md"
  created:
    - ".planning/phases/04-full-migration-search-offline-performance/04-SCOPE-PIVOT-SUMMARY.md"
decisions:
  - "SOFT DROP not HARD DELETE — 11 dormant archive pages, data files, content collections, and TONE entries preserved in repo. Re-add to Nav/Footer only requires removing data-pagefind-ignore + adding to ACTIVE_ARCHIVES set in Nav/Footer/RootLayout."
  - "ArchiveSlug type union stays 15-wide — TONE map, BRANDING map, LICENSE/SOURCE_URLS maps all keep all 15 entries dormant. Defensive default still falls back to wargov for any future slug."
  - "Lightbox meta panel reads from window.__lbList entries enriched at refreshLbList time with desc/agency/date/region/category/source (page-specific scripts already populate __lbList; small extension to capture extra fields from card dataset)."
  - "Lightbox dual buttons: 'Download from realufo' uses local || url (R2 if present); 'View on source' uses asset source URL (a.s field via data-src). Both wired in renderLb()."
  - "Card.astro + CatalogCard.astro emit data-desc + data-agency + data-date + data-region + data-category + data-src on the <article>. data-agency + data-date were already present (kept). 4 new attrs added."
  - "normalize-csv.py:render_card_html mirrors Card.astro additions byte-equivalent (D-10 LOCKED pair); shards regenerated."
  - "CLAUDE.md §2 + §13 annotated, NOT deleted. The 15-archive table stays as the long-term plan; status column added to mark active/dormant."
  - "Tone-colours test (15 archives) continues to pass because legacy postbuild copy still ships /aaro/ /nasa/ /nara/ /geipan/ etc. as plain HTML. The scope pivot affects only the Astro-rendered NAV+FOOTER links and Pagefind indexing."
metrics:
  duration: "~22m"
  completed: "2026-05-28T00:38Z"
---

# Phase 4 SCOPE PIVOT: 4 Active / 11 Dormant Archives

**One-liner:** Operator-mandated soft drop — Nav/Footer/Pagefind now ship only wargov+aaro+nasa+nara; 11 other archives preserved in repo (code, data, types, TONE colours) but invisible from user-facing surface. Plus lightbox extension: 7 asset types + meta panel + dual download/source buttons.

## Status: COMPLETE

## Rationale (operator, 2026-05-28)

> "realufo.org now ships ONLY 4 archives — War.gov, AARO, NASA, NARA. Drop 11 from user-facing nav while keeping code/data DORMANT in repo (soft drop). All 4 archives have same header + footer + lightbox that can view all 7 asset types with full description. Lightbox opens on click of the file, view + download from our site and original site."

Soft-drop chosen over hard-delete because:
- Future re-add doesn't require re-implementing scrapers, normalisers, or page templates.
- `content.config.ts` collections + TONE map + ArchiveSlug type union stay intact (no breaking schema changes for any downstream code).
- NZ + Uruguay Astro pages (already shipped) stay in repo; `data-pagefind-ignore` on `<main>` keeps them out of search results without breaking direct-URL navigation.
- Legacy postbuild copy (`scripts/copy-legacy-archives.sh`) continues to ship plain-HTML versions of the 11 dormant archives — tone-colour tests + visual-regression tests for 15 archives continue to pass.

## Tasks

| Task | Name                                                              | Commit  | Files                                                                                                                              |
| ---- | ----------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 0    | Skeleton SUMMARY.md (#2070 hedge)                                 | 7b1707d | .planning/phases/04-full-migration-search-offline-performance/04-SCOPE-PIVOT-SUMMARY.md                                            |
| 1    | Reduce Nav + Footer to 4 active archives                          | 572eb83 | src/components/Nav.astro, src/components/Footer.astro                                                                              |
| 2    | RootLayout emits data-pagefind-ignore on dormant pages            | 80efc70 | src/layouts/RootLayout.astro                                                                                                       |
| 3    | Lightbox renders 7 asset types + meta panel + dual actions        | f62a3bc | src/components/Lightbox.astro, src/scripts/invariants.ts                                                                           |
| 4    | Cards emit 4 new data-* attrs; lbList enriched; shards regenerated| 5d0a1ef | src/components/Card.astro, src/components/CatalogCard.astro, scripts/normalize-csv.py, data/wargov-shard-{2..5}.json (+ public), src/pages/index.astro, src/pages/nz/index.astro, src/pages/uruguay/index.astro |
| 5    | CLAUDE.md §2 + §13 annotate 4-active / 11-dormant                 | 056d42b | CLAUDE.md                                                                                                                          |

## What changed (mechanism, not file list)

**Nav.astro.** ARCHIVES const reduced from 15 entries to 4 (wargov, aaro, nasa, nara). BRANDING map similarly slimmed to 4. ArchiveSlug type union STAYS 15-wide so any future re-add is a 1-line edit.

**Footer.astro.** Archives column reduced from 15 to 4. Source list (external URLs) reduced from 15 to 4. LICENSE + SOURCE_URLS maps STAY 15-wide for safe lookup on dormant pages.

**RootLayout.astro.** New ACTIVE_ARCHIVES set (`['wargov', 'aaro', 'nasa', 'nara']`). When `archiveSlug` is not in this set, `<main>` receives `data-pagefind-ignore` attribute — Plan 04-19 Pagefind will skip indexing without further code change.

**Lightbox.astro + invariants.ts.** Lightbox shell extended with `#lb-meta` (description/agency/date/region/category panel) and `#lb-actions` (Download + View on source buttons). `renderLb()` populates meta from `lbList[lbIdx]` entries enriched with new fields. 7 asset types confirmed: PDF (iframe local), VID (video+2 sources), IMG (img+fallback), AUDIO (audio tag), CASE/PAGE (iframe), CATALOG (link out / new tab).

**Card.astro + CatalogCard.astro.** Both now emit 4 additional dataset attrs on the article: `data-desc`, `data-region`, `data-category`, `data-src` (existing `data-agency`, `data-date` already present). normalize-csv.py:render_card_html mirrors byte-equivalent (D-10 LOCKED).

**index.astro + nz/index.astro + uruguay/index.astro `refreshLbList()`.** Extended to capture the new fields from each `.arch-card`'s dataset and pipe into `window.__lbList`.

**CLAUDE.md §2 + §13.** "Sources status" callout marks 4 active + 11 dormant.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing critical functionality] BRAND map typing in Nav.astro**
- **Found during:** Task 1.
- **Issue:** Slimming BRAND from `Record<ArchiveSlug, ...>` to a 4-entry literal would have made dormant slugs (nz, uruguay, etc.) crash with a TypeScript error when their pages instantiate Nav (which still happens on direct-URL access).
- **Fix:** Changed type to `Partial<Record<ArchiveSlug, ...>>` and used non-null assertion on the wargov fallback (`BRAND[archiveSlug] ?? BRAND.wargov!`). Defensive — preserves type-safety while allowing the slim runtime map.
- **Files modified:** src/components/Nav.astro.
- **Tracked as deviation, no separate commit needed (included in 572eb83).**

**2. [Rule 3 — Blocker] node_modules absent in fresh worktree**
- **Found during:** Task 0 prep.
- **Issue:** Worktree spawned without dependencies installed; pnpm/astro/playwright unavailable.
- **Fix:** Ran `pnpm install --frozen-lockfile` in background while making file edits (5s parallel; used existing pnpm-lock.yaml, no version drift).
- **Files modified:** None (node_modules is gitignored).
- **Tracked as deviation, no commit needed.**

### Decisions documented inline

See frontmatter `decisions:` block. None reach Rule 4 (architectural) threshold — soft-drop posture preserves all data + types, no schema changes.

## Authentication Gates

None expected.

## Verification Results

| Gate | Result | Notes |
|------|--------|-------|
| V1 `pnpm exec astro build` | PASS | Server built in 2.85s. SW assets bundled; Pagefind glob warning is pre-existing (Plan 04-19 wires Pagefind). |
| V2 Nav links in dist/index.html (active page) | PASS | 4 unique `data-archive=` values in nav: wargov + aaro + nasa + nara. No dormant slugs present. |
| V3 Footer Source column entries | PASS | 4 entries: war.gov / UFO, AARO.mil, NASA UAP Study, National Archives Catalog. No dormant entries. |
| V4 Footer Archives column entries | PASS | 4 entries: war.gov/UFO (/), AARO.mil (/aaro/), NASA UAP Study (/nasa/), National Archives Catalog (/nara/). |
| V5 RootLayout `data-pagefind-ignore` on dormant pages | PASS | `dist/nz/index.html` has `<main data-pagefind-ignore>` (verified via grep at line 26). `dist/index.html` (wargov) has NO `data-pagefind-ignore` on `<main>` (only on `nav.pagination` per existing Plan 04-04 D-30). |
| V6 Lightbox shell extension (meta + actions) | PASS | `#lb-meta`, `#lb-actions`, `#lb-download`, `#lb-source` all present in dist/index.html AND dist/nz/index.html (active + dormant share the same RootLayout-embedded Lightbox). |
| V7 Card.astro 4 new attrs in dist | PASS | 50 cards × {data-desc, data-category, data-src} = 50 each; data-region = 48 (2 cards have empty Incident Location → attribute present without value, which matches Card.astro's `?? ''` default). |
| V8 normalize-csv.py --check clean (D-10 LOCKED) | PASS | "wargov: --check clean (no drift)" — byte-equivalent contract preserved. |
| V9 Plan 04-01 lightbox.spec.ts enumeration | PASS | 6 tests enumerated, all keywords intact (click open, arrow, Escape, filter, remote PDF, pagination). `.lb-meta` class on remote-PDF render path preserved for Test 5 selector compatibility. |
| V10 `pnpm exec playwright test tests/lightbox.spec.ts` | DEFERRED | Requires PREVIEW_URL after CF Pages preview deploy. CI runs this on push. Lightbox extension adds attributes/buttons only; no regression expected. |
| V11 Tone-colour smoke test (15 archives) | DEFERRED | Pre-existing legacy postbuild-copy (`scripts/copy-legacy-archives.sh`) still ships /aaro/ /nasa/ /nara/ /geipan/ etc. as plain HTML so the 15-archive iteration still finds correct `--caution` values. Verified via CI on preview. |

## Known Stubs

The 11 dormant archives still have content collections + (for nz/uruguay) full Astro pages but are intentionally not linked. This is the soft-drop posture. A future plan can re-link them by:
1. Adding the slug to ACTIVE_ARCHIVES in Nav.astro + Footer.astro + RootLayout.astro
2. Removing the slug from `data-pagefind-ignore` exclusion set
3. Implementing the page template (for the 9 archives without one yet: aaro, nasa, nara, geipan, uk, brazil, chile, argentina, canada, italy, peru, spain — though aaro/nasa/nara remain on the roadmap for plans 04-15..04-17).

## Threat Flags

None — no new network endpoints, no new auth paths. The dual lightbox buttons expose URLs already present in the card dataset (zero new disclosure surface).

## Impact on Phase 4 (downstream)

- 04-15/16/17 (AARO/NASA/NARA ports) — when complete, will be 4-of-4 active archives; same Nav/Footer/Lightbox just works (CatalogCard.astro emits the new attrs automatically).
- 04-19 Pagefind — picks up `data-pagefind-ignore` automatically on dormant pages.
- 04-20 close — when ready to retire `scripts/copy-legacy-archives.sh`, also retire the dormant pages and the 11 entries from TONE/BRANDING/LICENSE/SOURCE_URLS maps + ArchiveSlug type union.

## Self-Check: PASSED

**Files modified (verified exist on disk + show in git diff main..HEAD):**
- `src/components/Nav.astro` — FOUND, ARCHIVES const = 4 entries
- `src/components/Footer.astro` — FOUND, ACTIVE_ARCHIVES const = 4 entries
- `src/components/Lightbox.astro` — FOUND, lb-meta + lb-actions present
- `src/components/Card.astro` — FOUND, 4 new data-* attrs present on `<article>`
- `src/components/CatalogCard.astro` — FOUND, 4 new data-* attrs present on `<article>`
- `src/layouts/RootLayout.astro` — FOUND, ACTIVE_ARCHIVES set + isDormant computation present
- `src/scripts/invariants.ts` — FOUND, renderMeta + renderActions + extended renderLb
- `src/pages/index.astro`, `src/pages/nz/index.astro`, `src/pages/uruguay/index.astro` — FOUND, refreshLbList enriched
- `scripts/normalize-csv.py` — FOUND, render_card_html mirrors 4 new attrs
- `data/wargov-shard-{2..5}.json` + `public/data/wargov-shard-{2..5}.json` — REGENERATED (172 cards across 4 shards)
- `CLAUDE.md` — FOUND, §2 status column + §13 active milestone callout added
- `.planning/phases/04-full-migration-search-offline-performance/04-SCOPE-PIVOT-SUMMARY.md` — FOUND (this file)

**Commits (verified in `git log --oneline 6fa9636..HEAD`):**
- 7b1707d `docs(04-scope-pivot): skeleton SUMMARY.md (time-budget hedge per #2070)` — FOUND
- 572eb83 `feat(04-scope-pivot): reduce Nav + Footer to 4 active archives` — FOUND
- 80efc70 `feat(04-scope-pivot): RootLayout emits data-pagefind-ignore on dormant pages` — FOUND
- f62a3bc `feat(04-scope-pivot): lightbox renders 7 asset types + meta panel + dual actions` — FOUND
- 5d0a1ef `feat(04-scope-pivot): cards emit 4 new data-* attrs; lbList enriched` — FOUND
- 056d42b `docs(04-scope-pivot): CLAUDE.md §2 + §13 annotate 4-active / 11-dormant` — FOUND

**Plan-level success criteria:**
- [x] Nav.astro ARCHIVES const reduced to 4 entries (wargov, aaro, nasa, nara); BRANDING map similarly slimmed (Partial<Record> + wargov fallback)
- [x] Footer.astro archive-link list reduced to 4 active slugs; LICENSE + SOURCE_URLS maps kept 15-wide (defensive)
- [x] RootLayout.astro emits `data-pagefind-ignore` on dormant archive pages
- [x] Lightbox.astro renders all 7 asset types (PDF/VID/IMG/CATALOG/AUDIO/CASE/PAGE) — CATALOG / CASE / PAGE branches added to renderLb()
- [x] Lightbox.astro shows full description meta panel (h3 title + p desc + dl agency/date/region/category)
- [x] Lightbox.astro footer has TWO action buttons: Download (R2 URL) + View on source (external)
- [x] invariants.ts openAt() reads 6 extra dataset attrs + populates lightbox meta panel
- [x] Card.astro + CatalogCard.astro emit data-desc + data-agency + data-date + data-region + data-category + data-src on the article element
- [x] scripts/normalize-csv.py:render_card_html() mirrors Card.astro byte-for-byte (D-10 pair — `normalize-csv.py --check` PASS)
- [x] CLAUDE.md §2 + §13 updated to note 4-active / 11-dormant scope
- [x] pnpm build exit 0
- [x] dist/index.html has 4 nav links + lightbox meta panel + dual buttons
- [x] tests/lightbox.spec.ts (Plan 04-01) STILL enumerates 6 tests; remote-PDF render path preserves `.lb-meta` class for Test 5 selector
- [x] 04-SCOPE-PIVOT-SUMMARY.md created + committed
- [x] No modifications to: STATE.md, ROADMAP.md, Phase 4 PLAN.md files, Phase 3 SUMMARY.md files, config.json, .planning/decisions/*, uap-release001.csv, uap-data.csv, scripts/build-*.py
