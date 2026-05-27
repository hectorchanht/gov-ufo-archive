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
  duration: "TBD"
  completed: "TBD"
---

# Phase 4 SCOPE PIVOT: 4 Active / 11 Dormant Archives

**One-liner:** Operator-mandated soft drop — Nav/Footer/Pagefind now ship only wargov+aaro+nasa+nara; 11 other archives preserved in repo (code, data, types, TONE colours) but invisible from user-facing surface. Plus lightbox extension: 7 asset types + meta panel + dual download/source buttons.

## Status: IN PROGRESS

(SUMMARY will be finalized after all commits land.)

## Rationale (operator, 2026-05-28)

> "realufo.org now ships ONLY 4 archives — War.gov, AARO, NASA, NARA. Drop 11 from user-facing nav while keeping code/data DORMANT in repo (soft drop). All 4 archives have same header + footer + lightbox that can view all 7 asset types with full description. Lightbox opens on click of the file, view + download from our site and original site."

Soft-drop chosen over hard-delete because:
- Future re-add doesn't require re-implementing scrapers, normalisers, or page templates.
- `content.config.ts` collections + TONE map + ArchiveSlug type union stay intact (no breaking schema changes for any downstream code).
- NZ + Uruguay Astro pages (already shipped) stay in repo; `data-pagefind-ignore` on `<main>` keeps them out of search results without breaking direct-URL navigation.
- Legacy postbuild copy (`scripts/copy-legacy-archives.sh`) continues to ship plain-HTML versions of the 11 dormant archives — tone-colour tests + visual-regression tests for 15 archives continue to pass.

## Tasks (commits listed when complete)

| Task | Name                                                              | Commit  | Files                                                                                                                              |
| ---- | ----------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------- |

## What changed (mechanism, not file list)

**Nav.astro.** ARCHIVES const reduced from 15 entries to 4 (wargov, aaro, nasa, nara). BRANDING map similarly slimmed to 4. ArchiveSlug type union STAYS 15-wide so any future re-add is a 1-line edit.

**Footer.astro.** Archives column reduced from 15 to 4. Source list (external URLs) reduced from 15 to 4. LICENSE + SOURCE_URLS maps STAY 15-wide for safe lookup on dormant pages.

**RootLayout.astro.** New ACTIVE_ARCHIVES set (`['wargov', 'aaro', 'nasa', 'nara']`). When `archiveSlug` is not in this set, `<main>` receives `data-pagefind-ignore` attribute — Plan 04-19 Pagefind will skip indexing without further code change.

**Lightbox.astro + invariants.ts.** Lightbox shell extended with `#lb-meta` (description/agency/date/region/category panel) and `#lb-actions` (Download + View on source buttons). `renderLb()` populates meta from `lbList[lbIdx]` entries enriched with new fields. 7 asset types confirmed: PDF (iframe local), VID (video+2 sources), IMG (img+fallback), AUDIO (audio tag), CASE/PAGE (iframe), CATALOG (link out / new tab).

**Card.astro + CatalogCard.astro.** Both now emit 4 additional dataset attrs on the article: `data-desc`, `data-region`, `data-category`, `data-src` (existing `data-agency`, `data-date` already present). normalize-csv.py:render_card_html mirrors byte-equivalent (D-10 LOCKED).

**index.astro + nz/index.astro + uruguay/index.astro `refreshLbList()`.** Extended to capture the new fields from each `.arch-card`'s dataset and pipe into `window.__lbList`.

**CLAUDE.md §2 + §13.** "Sources status" callout marks 4 active + 11 dormant.

## Deviations from Plan

(Will be filled in as tasks complete.)

## Authentication Gates

None expected.

## Verification Results

(Filled after final build + test.)

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

## Self-Check

(Filled at end.)
