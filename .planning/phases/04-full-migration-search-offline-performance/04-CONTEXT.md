# Phase 4: Full Migration, Search, Offline, Performance — Context

**Gathered:** 2026-05-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Port the remaining 14 archives to Astro (matching Plan 03-05 wargov pattern), swap Lunr → Pagefind 1.x for cross-archive search, ship the `@vite-pwa/astro` injectManifest Service Worker registered structurally from `BaseHead.astro`, hit ≤ 500 KB-per-page weight target (GEIPAN currently 3.3 MB), migrate the binary CDN from GitHub Releases to Cloudflare R2 at `assets.realufo.org`, fix the lightbox + add explicit `?page=N` pagination (20 cards/page) flagged broken on Phase 3 preview, and delete all legacy Python build scripts replaced by SSG.

**Within scope:**
- 22 requirements (SSG-06..10, SRC-01..05, SW-01..07, PERF-01..04)
- R2 binary-CDN migration (expands roadmap's "R2 for >2 GB overflow" → "R2 for everything")
- Lightbox + pagination fixes (carry over from Phase 3 wargov preview observations)
- Retroactively re-page wargov (50 → 20/page + URL pagination) so all 15 archives use the same UI

**Out of scope (deferred to other phases):**
- Hosting cutover (DNS swap GH Pages → CF Pages) — Phase 6 HOST-01
- Scrape automation R2-write path — Phase 5 SCRP
- Additional national archives (#16+) — future milestone
- Account-access resolution (Frank push access to hectorchanht repo) — operational, not Phase 4 scope
</domain>

<decisions>
## Implementation Decisions

### R2 Binary CDN Migration (NEW user requirement)

- **D-01:** **R2 migration for PDFs + videos only** — thumbnails STAY LOCAL (tracked in git, served from dist/ via Astro Image). Astro Image component only processes local files for responsive srcset + format conversion + lazy-load hints; pushing thumbs to R2 loses PERF-04 image perf path. GitHub Releases tags (`pdfs-v1`, `videos-v1`, etc.) archived as cold-storage backup; site fetches PDFs/videos from R2 at `assets.realufo.org`; card `url` fields rewritten at build time. Refined per 04-RESEARCH.md §5 + A3 assumption. (Expands PROJECT.md §STACK which said "GH Releases stays, R2 for >2 GB overflow only" — Phase 4 supersedes for PDFs/videos.)
- **D-02:** **R2 URL serving via custom domain `assets.realufo.org`** — bind R2 bucket to subdomain via CF dashboard custom-domain feature + DNS CNAME `assets` → R2 public URL. Stable URLs (survive bucket regeneration via DNS swap), easy SW allowlist, no opaque `*.r2.dev` URLs hardcoded into cards.
- **D-03:** **GH Actions upload pipeline** — new `.github/workflows/r2-sync.yml` runs on push to `main`. Detects new/changed binaries via `git diff` vs last successful run, `wrangler r2 object put` each. Uses `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` repo secrets (already configured per 03-06 user note). Idempotent.
- **D-04:** **First-run batch migration** — initial workflow run uploads existing 165 PDFs + 60 videos. One-time bulk; subsequent runs incremental. Document the bulk-migration in 04-CONTEXT.md follow-ups so operator can sanity-check object count post-upload.
- **D-05:** **Bucket layout** — single bucket `realufo` with path prefixes mirroring repo structure (`pdfs/<slug>/<file>`, `videos/<slug>/<file>`, `thumbs/<slug>/<file>`). Avoids per-type CORS / lifecycle policy fragmentation.
- **D-06:** **GH Releases status** — keep existing tags read-only as cold-storage backup. Cards do NOT reference them. Future tag creation paused (Phase 5 scrape automation may revisit).

### 14-Archive Port (SSG-06..10)

- **D-07:** **One plan per archive** — 14 dedicated plans `04-NN-<slug>` (e.g. `04-01-aaro`, `04-02-nasa`, etc.). Each plan template mirrors Plan 03-05 structure (`src/pages/<slug>/index.astro` + `Card.astro` reuse + page-specific CSS + per-archive shard manifest from `data/<slug>.json`). Wargov-specific bits (HeroCarousel) optional per archive.
- **D-08:** **Wave grouping by complexity tier:**
  - **Wave 1 (small/static):** NZ, Uruguay, Peru, Spain, Argentina, Italy — ~5-6 plans parallel
  - **Wave 2 (medium catalog):** Brazil, Chile, Canada, UK, NARA, NASA, AARO — parallel batches of 2-3
  - **Wave 3 (PERF-tied):** GEIPAN standalone — drives PERF-01 inline-JSON refactor + ≤ 3 chunks per page (PERF-02). Must hit LCP ≤ 2.5s mobile + 4× CPU throttle
- **D-09:** **Per-archive Python retirement (SSG-10) inside each plan's commit chain:**
  - Delete `scripts/build-<slug>.py`
  - Drop slug from `scripts/copy-legacy-archives.sh` archive list
  - Drop slug from `scripts/sync-nav.py` + `scripts/sync-footer.py` drift policing
  - All in the same plan that ports the archive — Phase 4 close = postbuild hook removed, all Python build scripts gone, drift gates retired
- **D-10:** **Tone-colour fixes for geipan/uk/brazil/chile bundled** — these 4 archives have preexisting `--caution` CSS bugs (per 03-06 SUMMARY). Their respective per-archive port plans include the tone-colour fix as a sub-task; not a separate plan.
- **D-11:** **`scripts/dl-<slug>.sh` download scripts KEEP** — Phase 4 doesn't touch download/scrape (Phase 5 SCRP territory).

### Pagefind Search (SRC-01..05)

- **D-12:** **Single cross-archive WASM index** at `dist/pagefind/`. Matches current Lunr cross-archive UX. Sharded automatically by Pagefind default.
- **D-13:** **Per-archive filter via `data-pagefind-filter` attrs** on Card.astro markup — preserves SRC-03 per-archive filter UI; operates on already-rendered DOM, no re-fetch.
- **D-14:** **`api/all.json` (4.6 MB) deletion** — confirmed when Pagefind index green per success criteria. Single commit drops it; doesn't gradual deprecate.
- **D-15:** **Search result link format** `https://<host>/<slug>/#card-<id>` per SRC-04 (stable anchors preserved from URL-CONTRACT.txt + Plan 03-05 slugify).
- **D-16:** **`/search.html` rewrite** — replaced with `src/pages/search.astro` consuming Pagefind UI. Drops Lunr code path entirely.
- **D-17:** **Pagefind integration point** — `pnpm postbuild` hook chain extends `scripts/copy-legacy-archives.sh` to also run `pnpm exec pagefind --site dist`. Builds after copy step so legacy `<slug>/` HTML is indexed too.
- **D-17b:** **Pagefind plan lands AFTER all 14 archive ports complete** (Wave order: ports → Pagefind, not parallel). Reason: `data-pagefind-body` on RootLayout.astro would silently exclude legacy postbuild-copied HTML during transition window. Per 04-RESEARCH.md §2 Pitfall #5.

### Service Worker (SW-01..07)

- **D-18:** **`@vite-pwa/astro` injectManifest strategy** — full control over precache list + runtime cache strategies. No Workbox generateSW.
- **D-19:** **Registered structurally from `BaseHead.astro`** via inline `<script is:inline>` — every Astro page inherits registration. Eliminates the 12-of-32-pages gap from CONCERNS.md. Resolves SW-02.
- **D-20:** **Precache list:** every HTML page + every card thumbnail. Excludes PDFs/videos per SW-04 (size-prohibitive; on-demand from R2).
- **D-21:** **Runtime cache strategies (tiered, per SW-05):**
  - Network-first for HTML navigation
  - Stale-while-revalidate for JSON (shards, search index meta)
  - Cache-first for images/fonts (CF Pages + `assets.realufo.org` R2 origins both allowlisted)
  - No-cache for PDFs/videos (let browser HTTP cache handle; SW skips)
  - No-cache for `/admin*` and dev-only paths
- **D-22:** **Cache name `realufo-v<sha>`** where `<sha>` = short commit SHA at build time (CI-injected via env var). Old caches purged on new SW activation. `updateViaCache: 'none'` on all registrations (per SW-06 + Phase 1 PMS-04 invariant).
- **D-23:** **Self-hosted fonts (SW-07):** `@fontsource/source-serif-4` + `@fontsource/jetbrains-mono` replace current Google Fonts setup. Breaks the offline-first regression Google CDN causes.
- **D-24:** **R2 CORS configuration** — `Access-Control-Allow-Origin: https://realufo.org` (production) + `https://*.realufo.pages.dev` (preview). Configured via `wrangler r2 bucket cors` in same workflow that creates the bucket (Plan 04-R2 setup).
- **D-25:** **`_headers` application to new CF Pages project** — Phase 2 `_headers` file (Cache-Control + HSTS + SW kill-switch headers) NOT auto-applied to the new `realufo` CF Pages project. SW-01 plan re-applies + verifies via `curl -sI /sw.js` returns `cache-control: no-cache, no-store, must-revalidate` per D-38 (03-06 SUMMARY carryover).
- **D-26:** **SW lifecycle migration** — production cutover (Phase 6 HOST-01) will face users with existing GH-Pages-era SW. New SW uses `skipWaiting` + `clients.claim` only after cache name version bumps. Phase 4 ships the SW; Phase 6 verifies migration during cutover window.

### Pagination (NEW user requirement, ties to SSG-09)

- **D-27:** **PAGE_SIZE = 20 cards per page** (Phase 3 wargov shipped 50/page; Phase 4 reduces). Reason: footer reachable from each page without scrolling through all cards.
- **D-28:** **Explicit `?page=N` query parameter in URL** — bookmarkable, browser-history-friendly. Page 1 = no query param OR `?page=1` (both resolve identically). Page N = `?page=N`. Implementation is CLIENT-SIDE windowing (see D-33), not Astro file-based paginate() (Astro `paginate()` only generates path-based routes per 04-RESEARCH.md §6 — query strings unsupported).
- **D-29:** **URL contract compatibility** — `?page=N` is a query string; URL-CONTRACT.txt + redirects gate operate on paths only. No URL-CONTRACT.txt modification needed. `verify-redirects.sh` unchanged.
- **D-30:** **Retroactive wargov re-paging** — Plan 03-05's wargov page reflows from 50/page-lazy-load → 20/page + `?page=N` URL. NEW Phase 4 plan `04-wargov-repaging` does this so all 15 archives share the same UI.
- **D-31:** **Footer always reachable** below the 20 cards rendered. No infinite-scroll trap.
- **D-32:** **Shard scheme unchanged (D-08..D-10 Plan 03-03)** — `data/<slug>-shard-N.json` shards stay at 50 cards/shard (server-side render unit). All shards fetched upfront on initial load (~250 KB JSON for wargov, SW SWR-cached), client JS windows to 20 cards/page based on `URL.searchParams.get('page')`. Server-side rendering doesn't change; client pagination reshapes display.
- **D-33:** **IntersectionObserver lazy-load REMOVED; client-side windowing replaces it** — `URL.searchParams.get('page')` reads page number, JS calls `insertAdjacentHTML('beforeend', ...)` for the 20 cards in that page's window (cards still come from pre-rendered shard HTML strings per D-10 LOCKED — zero client templating). Browser back/forward + `#card-` anchors continue to work. Per 04-RESEARCH.md §6 recommendation.

### Lightbox Fix (NEW user requirement, ties to SSG-09)

- **D-34:** **Diagnose root cause** — current preview `https://1c266693.realufo.pages.dev` (pre-postbuild) and `https://e0196623.realufo.pages.dev` (post-postbuild) report broken lightbox. Plan 03-05 shipped Lightbox.astro + Plan 03-04 shipped invariants.ts handlers. Diagnose whether: (a) handlers don't bind on page load, (b) `data-action="open"` markers absent from cards, (c) handler exists but errors on missing references, (d) all of above.
- **D-35:** **Fix in invariants.ts and/or Card.astro markup** — D-21..D-23 progressive-enhancement contract preserved (no framework). Fix is surgical patch, not refactor.
- **D-36:** **Same fix benefits wargov retroactively** — both wargov and 14 new ports use same Lightbox.astro + invariants.ts. One fix lands across all 15 archives.
- **D-37:** **Lightbox plan** stands alone (`04-lightbox-fix`) at start of Phase 4 — blocks dependent ports if not fixed first.

### PERF (PERF-01..04)

- **D-38:** **GEIPAN PERF-01** — driven by GEIPAN port plan (Wave 3). 3.3 MB inline JSON refactored to ≤ 3 chunks per page. PERF-02 = chunk count cap. PERF-03 = first-paint contains cards (pre-rendered, not hydrated).
- **D-39:** **PERF-04 regression check** — NZ/Uruguay/Peru baselines preserved. Per-archive port plans must run Lighthouse SOFT gate; LCP regression flagged.
- **D-40:** **Phase 4 close = Lighthouse HARD-flip** — per 02-08 phase4-close-toggle, `.lighthouserc.cf.json` assertion levels flip `warn → error`. All archives must pass D-27 budgets (LCP ≤ 2500 ms, transfer ≤ 500 KB) before Phase 4 closes per ROADMAP §Phase 4 SC#2.

### Shared-File Serialization (Plan-Checker Iter 1 fix — race condition addressed)

- **D-41:** **`scripts/copy-legacy-archives.sh` shared-file write serialization** — all 14 archive port plans (04-05..04-18) modify this file to drop their slug from the archive list. Execute-phase workflow §execute_waves Step 1 ("Intra-wave files_modified overlap check") automatically detects this and overrides `parallelization=false` for any wave where ≥2 plans claim this file. Plans within a wave that share `scripts/copy-legacy-archives.sh` in `files_modified` will SERIALIZE rather than parallel-worktree, eliminating the merge-conflict risk plan-checker flagged. Same applies to `scripts/sync-nav.py` + `scripts/sync-footer.py` + `package.json` if multiple plans touch them in the same wave. No per-plan changes needed — execute-phase handles it.
- **D-42:** **04-20 close plan retires `scripts/copy-legacy-archives.sh` entirely** — by Phase 4 close, every port has dropped its slug; the script is a no-op. 04-20 deletes it + removes `postbuild` hook from package.json.

### Claude's Discretion

- Per-plan task breakdown (how many tasks per archive plan, atomic commit cadence)
- Specific Pagefind UI components (filter chip styling, result card layout) — preserve current /search.html UX
- SW precache manifest exact format (let `@vite-pwa/astro` defaults guide)
- `wrangler r2 bucket cors` exact config (sensible defaults per CF docs)
- R2 upload workflow's diff detection method (git plumbing TBD by researcher)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 4 ROADMAP entry
- `.planning/ROADMAP.md` §Phase 4 — 22 requirements list + 5 success criteria
- `.planning/REQUIREMENTS.md` lines 37-90 — SSG-06..10 + SRC-01..05 + SW-01..07 + PERF-01..04 detail

### Project-wide rules
- `./CLAUDE.md` — master spec; §3.1 tone colours LOCKED, §3.4 favicon shared, §4 page architecture skeleton, §5.1/5.2 GH Releases binary CDN policy (Phase 4 supersedes for R2), §7 JS invariants (lightbox = invariant #2), §8 mobile-first (360 px baseline), §9 content fidelity (verbatim official text, no filler), §11 don'ts (no force push, no CSV touching)
- `.planning/PROJECT.md` §Active — SSG/OFFLINE/PERF/HOST requirements; §Context Deployment
- `.planning/research/STACK.md` — Astro 5.x + Cloudflare Pages + Pagefind + injectManifest decisions

### Phase 3 outputs (consumed by Phase 4 ports)
- `src/content.config.ts` — Plan 03-02 schema (wargovEnvelopeSchema + catalogEnvelopeSchema for 14 archives)
- `src/layouts/RootLayout.astro` + `src/layouts/BaseHead.astro` — Plan 03-04 shared chrome
- `src/components/Nav.astro` + `src/components/Footer.astro` — Plan 03-04 shared components (all 15 slugs registered)
- `src/components/Card.astro` + `src/components/Lightbox.astro` — Plan 03-05 wargov implementations, reusable per-archive
- `src/styles/global.css` — Plan 03-04 (412 lines, 15 archive tone-colour map + palette + typography)
- `src/scripts/invariants.ts` — Plan 03-04 (267 lines, 8 inline JS invariants — lightbox handler is invariant #2)
- `scripts/normalize-csv.py` — Plan 03-03 (CSV → wargov.json + shards). Phase 4 may extend or fork for other archives' CSVs
- `scripts/copy-legacy-archives.sh` — Plan 03-06 postbuild hook (Phase 4 drops per archive port)

### Phase 3 sign-off + carryover
- `.planning/phases/03-ssg-foundation/03-06-SUMMARY.md` — D-17 operator-conscious recapture record, 14-archive js-off pass via postbuild copy, R2/_headers/SW carryover items in §Open questions
- `.planning/phases/03-ssg-foundation/03-CONTEXT.md` — D-01..D-40 Phase 3 LOCKED decisions (D-10 server-side shards, D-17 archiveSlug prop, D-23 no hydration, D-25 js-off HARD-FAIL, D-26..D-28 fidelity, D-37..D-40 invariants)

### Phase 2 CI gates (Phase 4 must keep green)
- `.github/workflows/quality-gates.yml` — 7-job matrix (preflight + visual-regression + fidelity + tone-colours + js-off + lighthouse + redirects)
- `scripts/verify-redirects.sh` — URL contract harness (Phase 4 unchanged)
- `scripts/verify-fidelity.py` — fidelity drift gate (per-archive samples in `tests/fidelity-samples.json`)
- `scripts/verify-lighthouse-budgets.py` — soft now, HARD-flip at Phase 4 close per D-28 + 02-08 phase4-close-toggle
- `tests/visual-baselines/` — 60 frozen PNGs (operator-only recapture per D-17)
- `tests/playwright.config.ts` — `PREVIEW_URL` env var contract
- `.lighthouserc.cf.json` — Phase 4 close: flip both assertion levels `warn → error`

### Phase 2 hosting decisions
- `.planning/decisions/cf-pages-project.md` — CF Pages project setup. Phase 4 R2 binding added.
- `.planning/decisions/akamai-spike.md` — Phase 5 scrape ingestion strategy (for context)

### Cloudflare docs (researcher to expand)
- R2 custom domain binding: https://developers.cloudflare.com/r2/buckets/public-buckets/
- R2 CORS: https://developers.cloudflare.com/r2/buckets/cors/
- R2 25 MiB CF Pages per-file limit: https://developers.cloudflare.com/pages/platform/limits/
- @vite-pwa/astro injectManifest: https://vite-pwa-org.netlify.app/frameworks/astro
- Pagefind 1.x: https://pagefind.app/docs/

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets (from Phase 3 outputs)

- **`src/components/Card.astro`** (122 lines) — server-renders single card from `wargovEnvelopeSchema.rows[]`. Per-archive ports reuse with archive-specific row type from `catalogEnvelopeSchema`. Markup contract: matches `scripts/normalize-csv.py:render_card_html()` byte-for-byte.
- **`src/components/Lightbox.astro`** (107 lines) — markup-only shell. Handlers in `invariants.ts` invariant #2. Single component serves all 15 archives.
- **`src/components/HeroCarousel.astro`** (301 lines) — 4-slide 16:9 carousel, autoplay, swipe. Optional per archive (wargov uses; others may skip if archive has no carousel content).
- **`src/components/Nav.astro` + `Footer.astro`** (151 + 171 lines) — already registers all 15 slugs. No edits needed for Phase 4 ports.
- **`src/styles/global.css`** (412 lines) — shared palette + 15-archive tone-colour map + mobile-first base. Per-archive `.css` extends only for archive-specific layout.
- **`src/scripts/invariants.ts`** (267 lines) — 8 JS invariants inline. Phase 4 lightbox-fix patches here.
- **`data/<slug>.json` × 14 skeleton envelopes** (Plan 03-02) — schema-valid empty; 14 per-archive normalisers fill them in their respective port plans.

### Established Patterns

- **D-10 LOCKED:** lazy-loaded shards contain pre-rendered HTML strings; runtime ONLY calls `insertAdjacentHTML`. PHASE 4 NEW: pagination via `?page=N` ROUTES (Astro `[...page].astro`) supersedes lazy-load for paginated pages, but D-10 still applies if any plan uses lazy-load fallback.
- **Per-archive normaliser pattern:** wargov has `scripts/normalize-csv.py` (Phase 3). Other 14 archives currently use `scripts/build-<slug>.py` (Python build, retired per SSG-10). Replacement: per-archive port plan extracts data into `data/<slug>.json` directly OR writes a per-archive normaliser if data source is complex.
- **Postbuild copy pattern (D-08 Phase 4):** `scripts/copy-legacy-archives.sh` shrinks per archive port until Phase 4 close drops it entirely.
- **Schema-strict envelopes:** `catalogAssetSchema.strict()` — unknown fields in `assets[]` fail build (D-02 Phase 3 schema; Phase 4 honors).
- **CSV untouchability (CLAUDE.md §11):** wargov reads `uap-release001.csv`. Other archives have their own data sources; Phase 4 ports MUST NOT write to source CSVs/JSONs.
- **Slugify byte-for-byte equivalence:** Card.astro + normalize-csv.py + snapshot-urls.py share slug algorithm. Phase 4 ports inherit; URL-CONTRACT.txt `#card-<id>` anchors stable across changes.

### Integration Points

- **Astro `[...page].astro` dynamic route** for pagination — Astro built-in `paginate()` helper from `getStaticPaths` generates `?page=N` (or `/page/N/`) static routes. D-28 decides query-param vs path-param; query-param chosen.
- **`@vite-pwa/astro` integration** added to `astro.config.mjs` `integrations[]` array (Phase 3 D-23 had it empty — Phase 4 SW-01 adds it).
- **Pagefind binary** invoked via `npx pagefind --site dist` in postbuild chain (D-17 Phase 4).
- **R2 binding** for build-time URL rewrite: card `url` fields swap `bundles/Release_1/X.pdf` → `https://assets.realufo.org/pdfs/wargov/X.pdf`. Done in `scripts/normalize-csv.py` (Phase 4 extension) + per-archive normalisers.
- **GH Actions `r2-sync.yml`** triggered on push to `main`, runs from `frankchanflow` account (or hectorchanht — depends on push-access resolution; deferred from Phase 4).
- **CF Pages `_headers`** file (Phase 2 02-01) — Phase 4 SW-01 plan re-applies to new realufo CF Pages project; verifies via curl smoke.

</code_context>

<specifics>
## Specific Ideas

- User feedback on preview `https://1c266693.realufo.pages.dev` and `https://e0196623.realufo.pages.dev`:
  - "non of the assets can be view on click on the website like video or pdf" — Lightbox click handler broken. Fix is invariants.ts (Plan 03-04) + Card.astro `data-action="open"` wiring (Plan 03-05).
  - "lacks the pagination" — clarified: lazy-load IS firing but loads all 222 wargov cards into a single page, forcing user to scroll past everything to reach footer. Solution: 20 cards/page + `?page=N` URL.
- "upload all of the assets to cf storage R2 and wired up" — strict requirement. Drives D-01..D-06.
- `assets.realufo.org` preferred custom domain (D-02). Operator owns DNS — sets CNAME during R2 plan.
- `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` already in GH secrets per user statement at start of session (verified accessible to workflows even though Frank can't list them as pull-only on hectorchanht repo).
- Use `frankchanflow.pub` / `frankchanflow` SSH key for ALL git operations (operator instruction Phase 3) — applies to any Phase 4 push.

</specifics>

<deferred>
## Deferred Ideas

- **DNS / hosting cutover** — Phase 6 HOST-01 swaps `realufo.org` DNS off GH Pages onto CF Pages. Phase 4 ships infrastructure but does NOT touch DNS (D-37 invariant from Phase 3).
- **CF Pages git-integration** — operator UI step (connect GitHub App) deferred to whenever Frank has push access on a frank-owned fork. Phase 4 keeps Direct Upload via wrangler (operator-driven; LHCI workflow can fire on workflow_dispatch).
- **Scrape pipeline → R2 direct write** — Phase 5 SCRP rewrites scrape automation to write new binaries directly to R2 via Workers cron. Phase 4 only provides the R2 bucket + URL contract; no scrape changes.
- **Phase 4 close lighthouse HARD-flip** is IN scope, but the operator-conscious recapture path for any post-port visual regression (per D-17) is per-plan: each port plan documents whether new baselines were recaptured or template was patched to match.
- **Stale `.planning/HANDOFF.json`** cleanup — trivial; first Phase 4 plan can `rm` it as a side-effect commit.
- **Frank GH write access** — operational; not Phase 4 scope. May surface during Phase 4 if `r2-sync.yml` PR cannot be opened from Frank's account.
- **Additional national archives (#16+)** — future milestone after Phase 6 close.

</deferred>

---

*Phase: 04-full-migration-search-offline-performance*
*Context gathered: 2026-05-27*
