---
status: testing
phase: 04-full-migration-search-offline-performance
source: [04-01..06, 04-15, 04-16, 04-17, 04-19, 04-20 SUMMARYs + 04-SCOPE-PIVOT-SUMMARY]
started: 2026-05-28T00:00:00Z
updated: 2026-05-28T00:00:00Z
---

## Current Test

number: 3
name: Lightbox asset view sized "as big as possible"
expected: |
  Click thumbnail (or btn-open) on any /aaro/, /nasa/, /nara/, or / (wargov) card.
  Lightbox opens. Asset (PDF iframe, video, image) renders at viewport-fill scale —
  up to 96vw wide × 82vh tall. Meta panel (desc + agency/date/region) compressed
  to ~12vh footer. Dual action buttons (Download + Source ↗) visible.
awaiting: orchestrator + operator verification

## Tests

### 1. R2 bulk migration — all GH Release assets on R2
expected: |
  All 165 PDFs (Phase 1 pdfs-v1) + 60 videos (videos-v1) + per-archive PDFs/videos
  for the 4 active sites uploaded to R2 bucket `realufo` under prefixes
  pdfs/<slug>/ and videos/<slug>/. Card.url fields in dist/ rewritten to
  https://assets.realufo.org/... (already done at build time by
  scripts/normalize-csv.py + per-archive normalisers via _archive_common.rewrite_to_r2).
  HTTP GET on any random card url returns 200 + correct file bytes.
result: blocked
blocked_by: server
reason: |
  GH Actions workflow .github/workflows/r2-sync.yml exists locally (commit
  at Plan 04-02) but never pushed to remote (Frank pull-only on
  hectorchanht/gov-ufo-archive). `gh workflow list --repo hectorchanht/...`
  doesn't show r2-sync.yml. Two unblock paths:

  PATH A (Hector pushes):
    Hector runs `git push` from local OR Frank pushes via a hectorchanht
    SSH key OR Hector adds Frank as repo collaborator. Then:
    gh workflow run r2-sync.yml -f full_sync=true \
      --repo hectorchanht/gov-ufo-archive

  PATH B (operator-direct bulk upload via wrangler/rclone):
    From local repo root, where wrangler is OAuth-logged-in to
    F147259@gmail.com (account f1868a07...):

    # Wargov PDFs (Phase 1 Release_1)
    for f in bundles/Release_1/*.pdf; do
      [ -f "$f" ] || continue
      npx wrangler r2 object put "realufo/pdfs/wargov/$(basename "$f")" \
        --file "$f" --content-type application/pdf
    done

    # AARO PDFs (largest — 2.7GB; expect ~30min)
    find aaro/pdfs -name "*.pdf" -print0 | while IFS= read -r -d '' f; do
      key="pdfs/aaro/${f#aaro/pdfs/}"
      npx wrangler r2 object put "realufo/$key" --file "$f" \
        --content-type application/pdf
    done

    # AARO videos
    find aaro/videos -name "*.mp4" -o -name "*.mov" -print0 | while IFS= read -r -d '' f; do
      key="videos/aaro/${f#aaro/videos/}"
      npx wrangler r2 object put "realufo/$key" --file "$f" \
        --content-type video/mp4
    done

    # NASA + NARA PDFs/videos: same pattern, swap slug

  Recommended: PATH B (no GH push dependency). After upload, spot-check
  3 random URLs return 200:
    curl -sI https://assets.realufo.org/pdfs/wargov/<random-file>.pdf | head -1
    curl -sI https://assets.realufo.org/pdfs/aaro/<random-file>.pdf | head -1
    curl -sI https://assets.realufo.org/videos/aaro/<random-file>.mp4 | head -1

### 2. Thumbnail click opens lightbox
expected: |
  Click on the thumbnail <img> inside any card (wargov + aaro + nasa + nara)
  opens the lightbox modal showing that asset. Previously only the explicit
  btn-open anchor triggered lightbox; thumbnail clicks did nothing.
  Card already displays desc under the thumbnail (CatalogCard.astro line 155).
result: pass
fix_applied: |
  src/scripts/invariants.ts (this UAT) — added separate click delegate for
  <img> elements inside article[data-action="open"] that calls openAt() with
  the article's data-row-id. Doesn't conflict with existing
  a[data-action="open"] btn-open delegate. Download / Source ↗ anchors
  (which live in .card-actions and are NOT inside an article-level open trigger
  resolution path) keep native behaviour.
  pnpm build exits 0; click flow verifiable in preview deploy.

### 3. Lightbox asset view "as big as possible"
expected: |
  When lightbox open, asset (img/video/pdf-iframe) fills near-viewport:
  ≥ 82vh tall × ≥ 96vw wide. Meta panel + action buttons compress to
  remaining ~14vh footer. Iframe/PDF gets equivalent treatment.
result: pass
fix_applied: |
  src/components/Lightbox.astro (this UAT) —
  - .lb-frame: removed 1280px max-width cap; now 96vw / 96vh.
  - .lightbox-inner: max-height 70vh → 82vh; flex: 1 1 auto.
  - img/video: max-width 100% → 96vw; max-height 82vh.
  - iframe: was capped at min(92vw, 1280px) → now 96vw × 82vh.
  - audio: bumped to min(96vw, 900px).
  - .lb-meta-panel: max-height 28vh → 12vh; font 14px → 13px;
    padding tightened so it doesn't steal viewport.
  pnpm build exits 0.

## Summary

total: 3
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 1

## Gaps

[Issue #1 R2 bulk migration is `blocked` not `failed` — operator-action gate,
not a code gap. No diagnosis needed; runbook documented above. Not added to
plan-phase --gaps consumption list.]
