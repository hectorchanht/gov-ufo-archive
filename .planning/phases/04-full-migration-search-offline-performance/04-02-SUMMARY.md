---
phase: 04-full-migration-search-offline-performance
plan: "02"
subsystem: infrastructure
tags: [r2, binary-cdn, cloudflare, cors, rclone, gh-actions, infrastructure, blocking-port-urls]
status: complete
requires:
  - "Plan 02-01 cf-pages-project.md (CF account + CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID secrets)"
  - "Plan 03-03 normalize-csv.py + data/wargov.json + shard scheme (extended by Task 3)"
  - "Plan 04-01 Card.astro data-row-id + data-local emissions (preserved — not regressed)"
  - "scripts/snapshot-urls.py:slugify (byte-equivalent port lives in _archive_common.py)"
provides:
  - "scripts/_archive_common.py — rewrite_to_r2 + slugify helpers consumed by all Wave 3+ archive normalisers"
  - ".planning/decisions/r2-setup.md — 5th ADR locking R2 bucket name, custom domain, CORS scope, GH secrets, A3 thumbnail decision"
  - ".github/workflows/r2-sync.yml — rclone S3-compat sync of PDFs/videos to R2 on push + workflow_dispatch"
  - "tests/r2-urls.spec.ts — Playwright HEAD-check sample of card.url R2 URLs (gated by R2_MIGRATED env var)"
  - "data/wargov.json + shards regenerated with R2 URLs in PDF | Image Link field (PDFs + videos only; images preserved verbatim)"
  - "public/data/wargov.json + shards mirrored (Astro consumer + runtime lazy-loader path)"
affects:
  - "All Wave 3+ archive port plans (04-05..04-18) — must `from _archive_common import rewrite_to_r2` to emit R2 URLs"
  - "Plan 04-04 wargov repaging — consumes the R2-URL wargov.json + shards regenerated here"
  - "Operator follow-up: `gh workflow run r2-sync.yml -f full_sync=true` after merge triggers bulk migration of 165 PDFs + 60 videos"
  - "Card.astro (no source change; reads PDF | Image Link directly — propagates R2 URLs to data-url + href emissions)"
tech-stack:
  added:
    - "rclone (installed at workflow runtime via curl https://rclone.org/install.sh; not committed to repo)"
  patterns:
    - "Shared helper module scripts/_archive_common.py for cross-archive normaliser logic (eliminates 14× duplicated slugify + R2 URL routing)"
    - "Image-extension allowlist (.png/.jpg/.webp/.svg/.avif/.bmp/.gif) preserved as-is by rewrite_to_r2 — thumbs stay local per D-01 refinement + Pitfall #7"
    - "rclone S3-compat sync with --checksum for idempotent incremental uploads + concurrency.cancel-in-progress:false for upload safety"
    - "Mutation at the read boundary (_read_rows): rewrite_to_r2 runs once per row in normalize-csv.py, propagating R2 URLs to both Astro server-rendered first-50 (via Card.astro reading PDF | Image Link) AND shard HTML strings (via render_card_html reading the already-rewritten field)"
    - "Skippable Playwright spec via env-var gate (R2_MIGRATED) — lets CI ship a test before the prerequisite migration completes without going red"
key-files:
  created:
    - "scripts/_archive_common.py (167 lines — rewrite_to_r2 + slugify + R2_BASE)"
    - ".planning/decisions/r2-setup.md (373 lines — 5th ADR)"
    - ".github/workflows/r2-sync.yml (~190 lines — 7-step rclone sync workflow)"
    - "tests/r2-urls.spec.ts (193 lines — 2 tests: data-shape always-runs + HEAD-check gated)"
  modified:
    - "scripts/normalize-csv.py (+48 lines — import _archive_common, rewrite PDF | Image Link in _read_rows for PDF/VID rows)"
    - "data/wargov.json (47 first-page rows rewritten to R2 URLs in PDF | Image Link field)"
    - "data/wargov-shard-2.json (rewritten — many PDF/VID rows in this page range)"
    - "data/wargov-shard-4.json (rewritten — many PDF/VID rows in this page range)"
    - "data/wargov-shard-5.json (rewritten — sparser PDF/VID rows in this last page range)"
    - "public/data/* (mirror of all above for runtime lazy-loader path)"
  preserved:
    - "r2-cors.json (NOT modified — already committed at e9ff48c with wrangler 4.x lowercase-key schema that operator already applied + smoke-verified; regenerating to wrangler 3.x AllowedOrigins schema would break working CORS — Rule 3 deviation)"
    - "uap-release001.csv + uap-data.csv (untouched per CLAUDE.md §11 + T-03-07 guard)"
    - "Card.astro (unchanged — reads PDF | Image Link directly; R2 URLs propagate via the read-boundary rewrite)"
    - "data/wargov-shard-3.json (unchanged — all rows in that 50-card range are IMG/AUD/empty types; no R2 routing needed)"
decisions:
  - "D-01 (refined): PDFs + videos migrate to R2; thumbs stay local (Astro Image processes local files only per Pitfall #7)"
  - "D-02: assets.realufo.org custom domain via CF dashboard (proxied CNAME); never reference *.r2.dev"
  - "D-04: rclone S3-compat sync for bulk migration (checksum-based idempotency for free)"
  - "D-05: single bucket `realufo`, prefix layout pdfs/<slug>/ + videos/<slug>/"
  - "D-24: CORS scope explicit allowlist (realufo.org + *.realufo.pages.dev + localhost dev); GET+HEAD only; no wildcard origin"
  - "Two-token model: CLOUDFLARE_API_TOKEN (wrangler bearer) + CLOUDFLARE_R2_ACCESS_KEY/SECRET_KEY (rclone S3-compat) — both kept; different auth surfaces"
  - "Jurisdiction: Global (public-domain content, no FedRAMP/EU constraint)"
  - "r2-cors.json schema preserved as committed at e9ff48c (wrangler 4.x lowercase keys); operator already applied + verified — regenerating would break working CORS"
  - "PDF | Image Link rewrite at _read_rows boundary (not at render_card_html) so both Card.astro server-render path + shard HTML path see the same R2 URL"
  - "rewrite_to_r2 handles 'PDF ' (trailing space — CSV data quality issue) by .strip()-ing the Type before comparing"
  - "R2 URL contract test split into always-runs (data-shape) + R2_MIGRATED-gated (HEAD-checks) so the spec ships before bulk migration without flaking CI"
requirements: [SSG-06]
metrics:
  duration: "~40 min"
  tasks_completed: "2/2 (Tasks 2 + 3; Task 1 was pre-spawn operator action, Task 4 deferred to operator post-merge)"
  commits: 4
  files_created: 4
  files_modified: 9
  completed: "2026-05-27"
---

# Phase 4 Plan 02: Cloudflare R2 binary CDN setup Summary

**Stands up R2 as the canonical binary CDN at `assets.realufo.org`, wires the
`rewrite_to_r2()` URL helper that every Wave 3+ archive normaliser depends on,
extends `scripts/normalize-csv.py` so wargov card URLs route through R2 for
PDFs + videos while preserving thumbnails on their original origin per Pitfall
#7, ships the `r2-sync.yml` GH Actions workflow for incremental + bulk binary
sync, and lands a skippable Playwright spec that validates the R2 URL contract
end-to-end once the operator triggers the bulk migration.**

## Performance

- **Duration:** ~40 min
- **Started:** 2026-05-27T22:59Z
- **Completed:** 2026-05-27T23:12Z (Task 3 final commit)
- **Tasks committed:** 2 of 4 in plan scope (1 + 4 are operator-handled per the
  orchestrator's scope note)
- **Commits:** 4 (Task 2 + skeleton SUMMARY + Task 3 + final SUMMARY)
- **Files created:** 4
- **Files modified:** 9 (1 script + 8 regenerated JSON; CSV untouched)

## Accomplishments

- **R2 URL routing helper landed.** `scripts/_archive_common.py rewrite_to_r2()`
  is the single source of truth for converting `bundles/.../foo.pdf` or
  `https://www.war.gov/medialink/.../foo.pdf` to
  `https://assets.realufo.org/<pdfs|videos>/<slug>/foo.pdf`. Image extensions
  (.png/.jpg/.webp/.svg/.avif/.bmp/.gif/.jpeg) are preserved verbatim per D-01
  refinement so Astro Image can still process them locally for responsive
  srcset + format conversion.
- **`scripts/_archive_common.py:slugify`** is a byte-equivalent port of
  `scripts/snapshot-urls.py:slugify` (verified by cross-call assertion in the
  verify step). All 14 Wave 3+ archive normalisers will import this rather
  than re-implementing — one source of truth, one URL-CONTRACT regression
  surface to maintain.
- **wargov manifest now emits R2 URLs.** 122 PDF rows (`Type='PDF'` + `'PDF '`
  with trailing space) + 12 VID rows with non-empty `PDF | Image Link` route
  through `assets.realufo.org/pdfs/wargov/` and `assets.realufo.org/videos/wargov/`
  prefixes. 14 IMG rows kept on the war.gov origin. 8 AUD + 66 empty-link VID
  rows have empty card.url. Source CSV unchanged (CLAUDE.md §11 guard passes).
- **r2-sync.yml workflow shipped.** Triggers on push to main with binary
  paths-filter + manual workflow_dispatch with `full_sync` boolean. rclone
  S3-compat sync uses checksum-based idempotency; `concurrency.cancel-in-progress:
  false` per T-04-07; 30-minute timeout; per-archive loop scaffolds future
  Wave 3+ binaries. Cleanup step removes rclone.conf even on failure
  (defence-in-depth even though runner is ephemeral).
- **Playwright spec lands.** `tests/r2-urls.spec.ts` has two tests: a
  data-shape sanity check that always runs (asserts wargov.json + shards
  contain R2 URLs and each URL is under the expected `pdfs/wargov/` or
  `videos/wargov/` prefix), and a HEAD-check test gated by
  `R2_MIGRATED=1` that samples 10 deterministic URLs and asserts HTTP 200 +
  CORS echo for `https://realufo.org`. Skip-gating lets CI ship the spec
  before the bulk migration completes.
- **ADR locked.** `.planning/decisions/r2-setup.md` documents bucket name,
  custom domain, jurisdiction (Global — public-domain content, no FedRAMP
  constraint), CORS scope, two-token model
  (`CLOUDFLARE_API_TOKEN` vs `CLOUDFLARE_R2_ACCESS_KEY`/`SECRET_KEY`),
  the A3 thumbnail decision, and the first-run bulk migration runbook.

## Task Commits

Each task was committed atomically:

1. **Task 2: `_archive_common.rewrite_to_r2` + ADR** — `53110d1` (feat)
2. **Skeleton SUMMARY** — `f376c90` (docs) (#2070 — commit early)
3. **Task 3: normalize-csv emits R2 URLs + r2-sync workflow + spec** — `d2d6904` (feat)
4. **Final SUMMARY (this file)** — pending (docs)

Task 1 (operator: bucket create, CORS apply, custom domain bind, GH secrets) was
completed by the orchestrator before this agent was spawned. Task 4
(operator-triggered bulk migration via `gh workflow run r2-sync.yml -f full_sync=true`)
is deferred until this plan merges to main — surfaced to the operator by the
orchestrator post-merge.

## Files Created / Modified

- `scripts/_archive_common.py` — NEW. `rewrite_to_r2()` + `slugify()` + R2_BASE.
  Pure stdlib. Consumed by Wave 3+ archive normalisers.
- `.planning/decisions/r2-setup.md` — NEW. 5th ADR. Bucket layout, CORS, secrets,
  A3 thumbnail decision, two-token rationale, bulk-migration runbook.
- `.github/workflows/r2-sync.yml` — NEW. 7-step rclone sync workflow with push +
  workflow_dispatch triggers.
- `tests/r2-urls.spec.ts` — NEW. 2 tests (data-shape always-runs + R2_MIGRATED-
  gated HEAD-check).
- `scripts/normalize-csv.py` — MODIFIED. Imports `rewrite_to_r2`; rewrites
  `PDF | Image Link` field in `_read_rows` for PDF/VID type rows.
- `data/wargov.json` + `data/wargov-shard-{2,4,5}.json` — REGENERATED. R2 URLs
  in PDF | Image Link field for PDF/VID rows. Shard 3 unchanged (no PDF/VID
  rows in that page range).
- `public/data/*` — REGENERATED. Mirrors of the above for runtime lazy-loader
  (Plan 03-05 Rule 3 — Astro serves `public/data/*.json` at `/data/*.json`).
- `r2-cors.json` — PRESERVED (NOT modified). Already committed at `e9ff48c`
  with wrangler 4.x lowercase-key schema; operator applied + smoke-verified.
- `uap-release001.csv` + `uap-data.csv` — PRESERVED. CSVs untouched per
  CLAUDE.md §11; `_assert_csv_unchanged()` post-step guard passes.

## R2 URL emission counts (verified)

| Surface | Count | Source |
|---------|-------|--------|
| `data/wargov.json` first-50 raw rows with R2 URL | 47 | 47 PDF/VID rows in CSV positions 1-50 |
| Shard cards with R2 URL | 87 | 122-47 PDFs + 12 VIDs split across shards 2,4,5 |
| **Total cards with R2 URL** | **134** | 122 PDF + 12 VID across all 222 rows |
| IMG cards kept on war.gov origin | 14 | `Type='IMG'` rows — Pitfall #7 |
| Empty card.url (no Link or AUD type) | 74 | 8 AUD + 66 empty-link VID rows |
| **Total wargov cards** | **222** | CSV row count after Title-truthiness filter |

Built `dist/index.html` ships 47 first-page cards with R2 URLs in both
`btn-open` `data-url` and `btn-download` `data-url` + `href` attributes
(verified via Python regex; `grep` underreported due to multi-line article tags).

## Decisions Made

- **`PDF | Image Link` rewrite happens at the `_read_rows` boundary, not at
  `render_card_html`.** This propagates the R2 URL to BOTH paths Card.astro
  consumes: the first 50 rows that Astro server-renders via Card.astro reading
  `PDF | Image Link` directly, AND the shard HTML strings that `render_card_html`
  pre-renders for client-side lazy-load. Single rewrite, single source of truth,
  no double-rewrite risk (the helper is idempotent on already-R2 URLs anyway).
- **Trailing-space `'PDF '` Type values are handled by `.strip()`.** 6 rows in
  the source CSV have `Type='PDF '` instead of `'PDF'` (data-quality issue).
  Rather than touch the CSV (CLAUDE.md §11), the normaliser strips before
  comparing — those rows route correctly through R2 while their `data-type`
  attribute preserves the original whitespace verbatim.
- **`r2-cors.json` schema preserved.** The on-disk file at `e9ff48c` uses the
  wrangler 4.x lowercase-key schema (`rules[].allowed.{origins,methods,headers}`
  + `exposeHeaders` + `maxAgeSeconds`) and the operator already applied it via
  `wrangler r2 bucket cors set realufo --file ./r2-cors.json --force` with
  CORS verified working. The plan task body specified the legacy wrangler 3.x
  array-of-rules schema (`AllowedOrigins` etc.) — regenerating to that schema
  would break the working CORS config. Tracked as Rule 3 deviation
  (auto-fix blocking issue).
- **Playwright spec ships in skippable form.** `R2_MIGRATED` env-var gate keeps
  the HEAD-check test off CI until the operator triggers bulk migration. The
  data-shape sanity test always runs and catches regression-class failures
  (e.g., `normalize-csv.py` stops emitting R2 URLs) without needing a populated
  bucket.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Preserved committed r2-cors.json schema (wrangler 4.x)**

- **Found during:** Task 2 setup — reading the on-disk file vs the plan body.
- **Issue:** The plan task 2 `<action>` block specifies "Create `r2-cors.json`
  with the single-rule JSON array from 04-RESEARCH.md §4 (AllowedOrigins ...)"
  — i.e., the wrangler 3.x legacy schema with capitalised top-level keys.
  However, the file already exists at `git sha e9ff48c` with the wrangler 4.x
  lowercase-key schema (`rules[].allowed.{origins,methods,headers}` +
  `exposeHeaders` + `maxAgeSeconds`). The orchestrator's scope note confirmed
  the operator had already executed `wrangler r2 bucket cors set realufo
  --file ./r2-cors.json --force` against this exact file and that
  `curl -sI -H "Origin: https://realufo.org" https://assets.realufo.org/`
  returns `access-control-allow-origin: https://realufo.org` — proving the
  on-disk schema works.
- **Fix:** Left `r2-cors.json` unchanged. The `.planning/decisions/r2-setup.md`
  ADR documents the actual on-disk schema verbatim so future planners read
  ground-truth rather than the plan-time draft.
- **Files modified:** NONE for r2-cors.json. ADR updated to reflect reality.
- **Verification:** `git diff e9ff48c -- r2-cors.json` shows no change; operator-
  captured smoke output of HTTP/2 404 + access-control-allow-origin documented
  in r2-setup.md `## Smoke verification` section.
- **Committed in:** No commit needed (the file was already at e9ff48c pre-Task 2).
  The ADR that documents this is part of `53110d1` (Task 2 commit).
- **Why this is Rule 3 (blocking), not Rule 4 (architectural):** the on-disk file
  is a strict superset of the plan's required allowlist (covers realufo.org +
  *.realufo.pages.dev plus realufo.pages.dev + localhost dev origins) and the
  read-only methods (GET+HEAD). Schema choice is a packaging concern, not
  an architectural one — wrangler 4.x is the version actively used by the
  operator's local tooling. Regenerating to the older schema would have
  broken the verified-working CORS config.

**2. [Rule 1 — Bug] Trailing-space `'PDF '` Type values route correctly through R2**

- **Found during:** Task 3 verify step (Type-counts audit).
- **Issue:** 6 rows in `uap-data.csv` have `Type='PDF '` (trailing whitespace)
  instead of `'PDF'`. A naive `== 'PDF'` comparison would skip these — they'd
  route as `asset_type=None` and emit their original war.gov URL, contradicting
  the success criterion "regenerated card.url fields contain
  `https://assets.realufo.org/pdfs/wargov/`".
- **Fix:** `(cleaned.get('Type', '') or '').strip()` before comparing. The
  raw `Type` field is preserved verbatim in the rows dict (D-26..D-28 fidelity)
  — only the COMPARISON key is stripped. `data-type="PDF "` (with trailing
  space) ships verbatim in the rendered HTML; the URL routing is correct.
- **Files modified:** `scripts/normalize-csv.py` (one extra `.strip()` in the
  `if rtype == 'VID' ... elif rtype in ('PDF', 'DOC')` block, plus a documenting
  comment).
- **Verification:** Audit script counted 116 strict `PDF` + 6 `PDF ` = 122 total
  PDF rows routing through R2; no remaining PDF rows route through war.gov.
- **Committed in:** `d2d6904` (Task 3 commit).

---

**Total deviations:** 2 auto-fixed (1 Rule 3 blocking + 1 Rule 1 bug).
**Impact on plan:** Both are scoped to "make the existing system work as the
plan intended". No scope creep. No architectural changes.

## Issues Encountered

- **`pnpm exec astro` initially failed with `Command "astro" not found`.**
  Worktree had no `node_modules`. Resolved by running `pnpm install
  --frozen-lockfile` once (6.4 s with cache; restored 11 declared devDeps from
  `pnpm-lock.yaml`). Not a code issue — worktree setup expectation.
- **Pagefind glob warning during `pnpm build`.** The `@vite-pwa/astro` config
  in `astro.config.mjs` precaches `pagefind/pagefind*.{js,css}` but Pagefind
  hasn't been integrated yet (Plan 04-19 territory). The warning is pre-existing
  (predates this plan) and doesn't fail the build. Not in scope.

## User Setup Required

**One operator follow-up after merge:** trigger the first-run bulk migration via
`gh workflow run r2-sync.yml -f full_sync=true` to upload the 165 PDFs + 60
videos to R2. Detailed runbook in `.planning/decisions/r2-setup.md` §"First-run
bulk migration method". Once that completes:

1. Spot-check 3 URLs via `curl -sI` (see r2-setup.md for sample URLs).
2. Set `R2_MIGRATED=1` in the workflow that runs Playwright (or run locally
   `R2_MIGRATED=1 pnpm exec playwright test tests/r2-urls.spec.ts`).
3. Reply "approved" on Plan 04-02 Task 4 checkpoint so the phase advances.

## Next Phase Readiness

- **Plan 04-04 (wargov repaging)** can consume the regenerated R2-URL
  wargov.json + shards as-is.
- **Wave 3+ archive port plans (04-05..04-18)** can `from _archive_common
  import rewrite_to_r2` and reuse the byte-equivalent `slugify` immediately.
  The helper module is the single seam — once it lands in main, no further
  cross-plan coordination is needed for URL rewrite consistency.
- **Plan 04-03 (SW)** is unaffected; the SW's `IMAGE_ORIGINS` allowlist already
  includes `https://assets.realufo.org` per D-24.

## Self-Check: PASSED

Claims verified post-write:

- `scripts/_archive_common.py` exists (167 lines): **FOUND**
- `.planning/decisions/r2-setup.md` exists (373 lines): **FOUND**
- `.github/workflows/r2-sync.yml` exists (~190 lines): **FOUND**
- `tests/r2-urls.spec.ts` exists (193 lines): **FOUND**
- `scripts/normalize-csv.py` modified (+48 lines): **FOUND** (git log on file)
- `data/wargov.json` regenerated with 47 R2 URLs in first-page rows: **FOUND**
- `data/wargov-shard-{2,4,5}.json` regenerated; shard-3 unchanged: **FOUND**
- `public/data/*` mirrored: **FOUND** (cmp -s passed on all 5 files)
- `uap-release001.csv` + `uap-data.csv` byte-identical to pre-plan state:
  **FOUND** (`git diff --quiet` exits 0)
- `r2-cors.json` byte-identical to e9ff48c: **FOUND** (`git diff --quiet`)
- Task 2 commit `53110d1` exists: **FOUND** in `git log`
- Skeleton SUMMARY commit `f376c90` exists: **FOUND** in `git log`
- Task 3 commit `d2d6904` exists: **FOUND** in `git log`
- `pnpm build` exits 0: **VERIFIED** (last build at Task 3 commit)
- `python3 scripts/normalize-csv.py --check` exits 0: **VERIFIED** (no drift)
- Playwright spec listable: **VERIFIED** (`pnpm exec playwright test tests/r2-urls.spec.ts --list` shows 2 tests)
- Playwright non-skipped test passes: **VERIFIED** (1 passed in 507 ms)

---

*Phase: 04-full-migration-search-offline-performance*
*Completed: 2026-05-27*
