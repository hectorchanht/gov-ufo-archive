# Architecture Research

**Domain:** Offline-first, multi-collection static site generator with CI-driven scrape pipeline, Cloudflare Pages hosting, GitHub Releases binary CDN
**Researched:** 2026-05-25
**Confidence:** HIGH for SSG / SW / search choices; MEDIUM for scrape-pipeline seam placement (depends on operator preference); HIGH for binary-CDN sizing constraints

---

## 1. Target Architecture — System Overview

```
                                  ┌─────────────────────────────────────────────────────────┐
                                  │  OFFICIAL GOVERNMENT SOURCES  (15 archives, external)    │
                                  │  war.gov · aaro.mil · nasa.gov · archives.gov ·          │
                                  │  cnes-geipan.fr · nationalarchives.gov.uk · fab.mil.br · │
                                  │  sefaa.cl · cefae.ar · italy.mil · nzdf.mil.nz · …       │
                                  └────────────┬────────────────────────────────────────────┘
                                               │   HTTP + Wayback fallback
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                  CLOUDFLARE WORKERS — SCRAPE PIPELINE (cron / on-demand)                    │
│                                                                                              │
│  ┌─────────────────┐    ┌──────────────────┐    ┌────────────────────────────────────┐      │
│  │ poll-sources    │───▶│ diff-and-fetch    │──▶│ stage-to-R2 (incoming/<run-id>/…)  │      │
│  │ (cron daily)    │    │ (per-archive       │    │ + write manifest delta JSON       │      │
│  │                 │    │  scraper)          │    │                                   │      │
│  └─────────────────┘    └──────────────────┘    └──────────────────┬─────────────────┘      │
│                                                                     │                        │
│  ┌──────────────────────────────────────────────────────────────────▼─────────────┐         │
│  │ dispatch-to-github (Worker writes to GitHub API /dispatches with run-id payload)│         │
│  └──────────────────────────────────────────────────────────────────┬─────────────┘         │
└─────────────────────────────────────────────────────────────────────┼───────────────────────┘
                                                                      │ repository_dispatch
                                                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                       GITHUB ACTIONS — INGEST + RELEASE + DEPLOY                            │
│                                                                                              │
│  ┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────────────────────┐       │
│  │ pull-from-R2     │─▶│ gh release upload    │─▶│ write release-manifest deltas    │       │
│  │ (run-id payload) │  │ <tag> <files>        │  │ + commit normalized data/*.json  │       │
│  └──────────────────┘  └──────────────────────┘  └────────────────┬─────────────────┘       │
│                                                                    │ (git push origin main)  │
└────────────────────────────────────────────────────────────────────┼────────────────────────┘
                                                                     │
                                                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                      ASTRO SSG BUILD  (Cloudflare Pages build env)                          │
│                                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────────────┐         │
│  │  src/content/  ←─ content collections (Content Layer API, glob + file loaders)│         │
│  │     wargov/    aaro/    nasa/    nara/    geipan/    uk/    brazil/  …  (15) │         │
│  │     (each loaded from data/<slug>.json + data/cases/*.json)                  │         │
│  └─────────────────────────────────────┬───────────────────────────────────────┘            │
│                                        │  collection.getEntries() + getStaticPaths()        │
│                                        ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐            │
│  │  src/pages/                                                                  │            │
│  │    [slug]/index.astro       ← list page per archive, ALL cards SSR'd        │            │
│  │    [slug]/[case].astro      ← case detail pages                              │            │
│  │    search.astro             ← Pagefind-powered                               │            │
│  │  src/components/   shared Card, Lightbox, Nav, Footer, HeroCarousel          │            │
│  │  src/layouts/      ArchiveLayout, RootLayout, StoryLayout                    │            │
│  └─────────────────────────────────────┬───────────────────────────────────────┘            │
│                                        │  vite + astro build + pagefind --site dist          │
│                                        ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐            │
│  │  vite-plugin-pwa (injectManifest) generates /sw.js with __WB_MANIFEST       │            │
│  │  populated from build output (HTML + thumbs + Pagefind index chunks)        │            │
│  └─────────────────────────────────────┬───────────────────────────────────────┘            │
└────────────────────────────────────────┼─────────────────────────────────────────────────────┘
                                         │  dist/ → Cloudflare Pages
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              CLOUDFLARE PAGES (CDN + DNS)                                   │
│                                                                                              │
│  realufo.org              ← production (auto-deployed from main)                            │
│  preview.realufo.org      ← optional custom-domain preview alias                            │
│  <hash>.realufo.pages.dev ← per-PR / per-branch preview deployments                         │
│                                                                                              │
│  Rewrites/Functions:  /binaries/* → GitHub Releases OR R2 (basename routing)                │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                CLIENT (mobile / desktop browser)                            │
│                                                                                              │
│  HTML  ─ Astro-rendered, cards already in DOM (no hydrate-from-JSON)                        │
│  /sw.js ─ Workbox: precache shell + thumbs · stale-while-revalidate per-archive JSON ·      │
│           cache-first images/fonts · network-first navigations · NEVER cache non-2xx        │
│  Pagefind ─ lazy-loaded WASM + sharded index; first chunk ~30 KB                            │
│  Lightbox ─ progressive enhancement, opens by data-* attrs on already-rendered cards        │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

           ┌──────────────────────────────────────────────────────────────────┐
           │                    STATE LOCATIONS                                │
           ├──────────────────────────────────────────────────────────────────┤
           │ Git (main)            normalized data/*.json + release-manifest │
           │ GitHub Releases       binary assets (PDFs, mp4) ≤ 2 GB / file   │
           │ Cloudflare R2         binary overflow (> 2 GB) + scrape staging │
           │ Cloudflare Workers KV scrape-state cursors, last-run fingerprint│
           │ Cloudflare Pages      built dist/ (HTML, JSON shards, sw.js)   │
           │ Client cache          SW caches (SHELL, DATA, IMG) — versioned │
           └──────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Responsibilities

| Component | Responsibility | Implementation | Confidence |
|-----------|---------------|----------------|------------|
| **Cloudflare Workers — scrape** | Poll sources on cron, diff against last fingerprint, fetch new binaries, stage to R2, dispatch GitHub Action | TypeScript Workers + cron triggers + R2 binding + KV binding | HIGH |
| **GitHub Actions — ingest/release** | Pull staged R2 objects, run `gh release upload <tag> --clobber`, commit normalized JSON + release-manifest delta | Existing `.github/workflows/scrape.yml` rewritten | HIGH |
| **Normalized data layer** | `data/<slug>.json` (catalog rows) + `data/cases/*.json` (long-form), git-tracked, source of truth post-scrape | Plain JSON files committed to repo | HIGH |
| **Astro Content Layer** | Load `data/*.json` via `file()` + `glob()` loaders, expose typed collections, drive `getStaticPaths()` | `src/content.config.ts` with Zod schemas | HIGH |
| **Page routes** | One list page per archive + case detail pages + utility pages | `src/pages/[slug]/index.astro` + `[slug]/[case].astro` | HIGH |
| **Shared components** | Nav, Footer, Card, Lightbox, HeroCarousel, FilterBar — written **once**, imported everywhere | `src/components/*.astro` (+ minimal vanilla TS for interactivity) | HIGH |
| **Pagefind** | Build-time scan of `dist/`, emits sharded WASM-powered search index alongside HTML | `pagefind --site dist` runs after `astro build` | HIGH |
| **vite-plugin-pwa (injectManifest)** | Inject precache manifest into custom Workbox SW; covers all HTML routes + thumbs + Pagefind chunks | `@vite-pwa/astro` integration with `strategies: 'injectManifest'` | HIGH |
| **Service worker** | Root-scope SW (`/sw.js`) controlling all 15 archives; tiered cache strategies per asset type | Workbox `precaching` + `routing` + `strategies` modules | HIGH |
| **Binary CDN routing** | `/binaries/<basename>` rewrite to GH Releases URL by default, R2 for files > 2 GB | Cloudflare Pages `_redirects` file + small Pages Function | HIGH |
| **R2 overflow** | Stores binaries > 2 GB (GH Releases per-file limit) + scrape staging | Cloudflare R2 bucket with public access for served files | HIGH |
| **KV state** | `scrape:last-run`, `scrape:source-fingerprints/<slug>`, `dispatch:in-flight` | Cloudflare Workers KV | MEDIUM |
| **Cloudflare Pages** | Build + deploy + preview URLs + production custom-domain serving | `wrangler.toml` / Pages dashboard config | HIGH |

---

## 3. Question-by-Question Decisions

### 3.1 SSG content model — collections, not file-based per-card

**Decision:** Use Astro's **Content Layer API** with one `defineCollection()` per archive. Drive routes via dynamic `[slug]/index.astro` + `[slug]/[case].astro` and `getStaticPaths()`.

**Why:**
- 15 archives × up to ~3,300 records each (GEIPAN) = file-based routing would mean tens of thousands of `.astro` files — unworkable.
- Astro Content Collections are designed for "large number of pages, tens of thousands" and the Content Layer API (default since Astro 5, current 2026 release Astro 6.0.2) is "25–50% lower memory usage" than legacy collections. ([Astro Content Layer blog](https://astro.build/blog/content-layer-deep-dive/), [Astro 6 Migration Guide](https://www.oscargallegoruiz.com/en/blog/astro-5-migration-guide/))
- Content lives in `data/<slug>.json` (one per archive, normalized output of the scrape pipeline) — **not** committed inline into HTML. This is the architectural fix for the 3.3 MB GEIPAN bundle. The current inline-JSON manifest *becomes* the input to a Content Collection loader.
- CSV (`uap-data.csv`) stays untouched per CLAUDE.md §11 — wrapped by a custom loader function (Content Layer supports parser callbacks for `.csv`). ([Astro Content Loader API](https://docs.astro.build/en/reference/content-loader-reference/))

**Manifest JSON location:**
- Pre-build: `data/<slug>.json` — committed JSON, source of truth for the SSG
- Build-time: consumed by content collections; never inlined into HTML
- Post-build: a *shard* `dist/data/<slug>.json` emitted for client-side use (filters, search hydration) — served as a separate file, cached independently by SW (stale-while-revalidate). Each shard ≤ 500 KB target (CLAUDE.md PERF-01).

**Memory note:** `getStaticPaths()` returns only IDs + minimal props; the page component itself reads its full record via `await getEntry()` to avoid the "all data loaded in `getStaticPaths`" out-of-memory trap documented in the community. ([dev.to: Astro pagination for large data](https://dev.to/lovestaco/implementing-astro-pagination-for-large-data-2jmk))

### 3.2 Build-time vs runtime split — pre-render cards, no hydration

**Decision:** Cards are **fully rendered to HTML at build time**. Runtime JS is a thin progressive-enhancement layer for filter/sort/lightbox — operating on the already-painted DOM, not re-rendering from JSON.

**Why:**
- Eliminates the 3.3 MB GEIPAN initial-paint penalty entirely (the JSON never reaches the client during the first paint).
- Matches PROJECT.md constraint "SPAs that require JS to render content are rejected (breaks offline-first + JS-disabled archival)."
- Lightbox open / search / filter still need data — they fetch `/data/<slug>.json` (small, sharded, SW-cached) lazily on first interaction. This is the same pattern `search.html` already moved to in commit 7294b29.

**Trade-off acknowledged:** Each per-archive HTML page becomes larger (full card HTML inline) but loads progressively as the browser parses (vs blocking on a JSON parse + JS render cycle). For GEIPAN's 3,300 rows, pre-rendered HTML is ~700 KB-1.2 MB gzipped — still under the inline-JSON page weight today and offering instant FCP.

**Hybrid for very large archives:** Archives over ~2,000 records should use Astro **paginate()** to emit `[slug]/page/[…page].astro` files (50–100 cards per page). Mirrors the existing GEIPAN paginator bail-out but as a first-class SSG pattern.

### 3.3 Service-worker architecture — single root scope, Workbox via vite-plugin-pwa

**Decision:** **One** service worker at `/sw.js`, root scope `/`, registered from a shared `<BaseHead>` Astro component so every page registers it. Generated by `@vite-pwa/astro` using **`injectManifest`** strategy with a hand-written custom SW source.

**Why root scope:**
- "Recommended approach is to load a service worker from the root directory so its scope is as broad as possible." ([MDN Using Service Workers](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers))
- Solves the current critical gap (CONCERNS.md §"Service Worker Registered on Only 12 of ~32 Pages") — Astro's `<BaseHead>` slot lands the registration `<script>` on every page automatically; no `sync-sw-registration.py` drift gate needed.
- Per-archive scoping would require 15 separate registrations + cross-talk between cache namespaces. Worth nothing here — the archives all sit under the same origin and never conflict.

**Why `injectManifest` over `generateSW`:**
- The current `sw.js` has bespoke logic (2xx-only caching after `dcbc0d7`, version-stamping per deploy, per-asset-type strategies). `generateSW` only supports declarative config; `injectManifest` lets us ship the existing strategies verbatim with Workbox doing the precache-list injection. ([vite-pwa injectManifest docs](https://vite-pwa-org.netlify.app/guide/inject-manifest), [vite-pwa Astro integration](https://vite-pwa-org.netlify.app/frameworks/astro))
- `self.__WB_MANIFEST` placeholder is replaced at build time with the full file list — eliminates the manual `SHELL` array maintenance that currently misses every archive root.

**Cache strategies per asset type:**

| Asset type | Strategy | Cache name | Notes |
|------------|----------|------------|-------|
| HTML navigations (precached) | precache (CacheFirst with revision) | `realufo-shell-v<sha>` | All 15 `/<slug>/` roots + utility pages |
| HTML navigations (uncached, e.g. case detail) | NetworkFirst, 3s timeout, fall back to cache then `/404.html` | `realufo-pages-v<sha>` | Only cache `res.ok` (preserve `dcbc0d7` fix) |
| Data JSON (`/data/*.json`) | StaleWhileRevalidate | `realufo-data-v<sha>` | Per-archive shards; ETag-aware |
| Pagefind chunks (`/pagefind/*`) | CacheFirst, 30-day expiration | `realufo-search-v<sha>` | Immutable hashed chunks |
| Images (thumbnails, slideshow) | CacheFirst, 50 MB cap (LRU) | `realufo-img-v<sha>` | All thumbs precached up to budget |
| Fonts | CacheFirst, 1-year expiration | `realufo-fonts-v<sha>` | Already self-hosted |
| PDFs | NetworkOnly (no cache) | — | Files lifetime is too long to pin |
| Videos | NetworkOnly (no cache) | — | Too large to cache opportunistically |

Each cache name carries a version stamp (commit SHA from `vite-plugin-pwa`'s injected manifest revision) — a deploy invalidates client caches automatically, replacing the current `build-sw.py` version stamper.

### 3.4 Scrape pipeline — Cloudflare Worker → R2 → GitHub Action → commit + release

**Decision (seam map):**

```
SEAM 1: Source HTML / binary           SEAM 2: Normalized JSON
        ▲ Worker fetches, parses               ▲ Worker writes structured diff
        │                                      │
SEAM 3: Staged binaries in R2          SEAM 4: GitHub Action picks up
        ▲ Worker uploads with run-id           ▲ via repository_dispatch
        │                                      │
SEAM 5: GH Releases binary             SEAM 6: Git commit
        ▲ Action runs `gh release upload`      ▲ Action commits data/*.json deltas
        │                                      │
SEAM 7: Cloudflare Pages auto-deploys           SEAM 8: Client sees update
        ▲ on push to main                      ▲ via SW cache version bump
```

**State that lives where:**

| State | Location | Why |
|-------|----------|-----|
| Source-page fingerprints (HEAD ETag / content hash) | Cloudflare Workers KV | Worker needs cheap fast reads on every cron tick |
| Last-run cursor per archive | Workers KV | Worker-only state |
| Pending scrape run (in-flight payload) | R2 staging prefix `incoming/<run-id>/` | Binaries are large; KV is for ≤ 25 MiB values |
| Normalized catalog rows | Git (`data/<slug>.json`) | Versioned, diffable, source of truth |
| Release-manifest (basename → URL) | Git (`release-manifest.json`) | Same as today; consumed at build time |
| Binary assets ≤ 2 GB | GitHub Releases | Preserves existing URL pattern; durable mirror |
| Binary assets > 2 GB | R2 public bucket | GH Releases hard limit per-file |
| Built site | Cloudflare Pages | CDN serves |
| Client cache | SW caches | User-side |

**Why this seam structure:**
1. **Cloudflare Workers cron** (vs GitHub Actions cron) — different egress IPs, mitigates Akamai/gov-IP blocks that currently force `curl_cffi`. ([Cloudflare Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/))
2. **R2 staging** decouples scrape success from CI availability — Worker can keep fetching even if GitHub is having an incident.
3. **`repository_dispatch`** is the documented pattern for Worker → GH Action handoff. Worker POSTs to `/repos/<owner>/<repo>/dispatches` with `{event_type: 'scrape-complete', client_payload: {runId}}`. ([GitHub Actions Cloudflare integration](https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/))
4. **CI commits** normalized JSON — keeps git as the source of truth for data, so the SSG build is deterministic and reproducible from a clean clone (with the bundled `data/` directory).
5. **Release upload + commit in same workflow run** — atomicity. If the upload fails, the commit doesn't happen; the next run retries cleanly.

**Idempotency contract:** Every step keys off `run-id`. R2 staging prefix is `incoming/<run-id>/`. Failed runs can be replayed by dispatching `event_type: 'replay'` with the same `runId`.

### 3.5 Binary CDN — GH Releases primary, R2 overflow, transparent URL layer

**Decision:** `/binaries/<basename>` becomes the canonical URL. A Cloudflare Pages Function (or `_redirects`) routes by basename lookup in `release-manifest.json`:
- Files in GitHub Releases → 302 to `https://github.com/<repo>/releases/download/<tag>/<basename>`
- Files in R2 → 302 to `https://<r2-public>.r2.dev/<basename>` or proxied through the Pages domain

**Why:**
- GitHub Releases stay primary (the existing URL pattern, durable public mirror — matches PROJECT.md "Distribution — binaries: GitHub Releases stays the binary CDN").
- R2 absorbs the > 2 GiB tail. GitHub's per-file limit is 2 GB; R2's is ~4.995 TiB. ([R2 limits](https://developers.cloudflare.com/r2/platform/limits/))
- A **single canonical URL** in HTML means the SSG output is stable regardless of where the file physically lives — a file can be promoted from Release to R2 without rebuilding pages.
- Cloudflare Pages itself has a 25 MiB per-static-asset limit ([Pages limits](https://developers.cloudflare.com/pages/platform/limits/)), so binaries cannot live in `dist/`. The URL-rewrite layer enforces this separation.

**Tag-naming convention:** Per-archive tags (`wargov-r02-v1`, `geipan-v1`, `uk-v1`, `pdfs-v1` for cross-archive overflow) — already started, formalized here. Each release tag ≤ 1,000 assets (GH Releases soft limit).

### 3.6 Search architecture — Pagefind, build-time index, SW-precached

**Decision:** **Pagefind** built into the SSG output. Replace runtime Lunr (currently 4.6 MB `api/all.json` fetched on `/search.html`).

**Why:**
- Pagefind "shards its index and loads chunks lazily as the user types — initial load is under 30 KB (WASM + manifest), individual chunks fetched on demand." ([dev.to: Pagefind over Algolia and Lunr](https://dev.to/morinaga/static-site-search-for-astro-in-2026-why-i-picked-pagefind-over-algolia-and-lunr-pg1))
- For 15 archives × ~4,000 records ≈ 60,000 docs (current scale), Lunr would emit a ~10 MB single-file index. Pagefind's sharded approach: client downloads ~30 KB + only the chunks relevant to active search terms.
- Adopted as the default by Astro Starlight — "By default, Starlight sites include full-text search powered by Pagefind." ([Starlight Site Search](https://starlight.astro.build/guides/site-search/))
- Build-time output is HTML-only by scanning `dist/` — exactly compatible with Astro's static export.
- The SW precaches **only** the Pagefind core (~30 KB WASM + manifest), letting the index chunks load on demand and be cached opportunistically (CacheFirst). No bloating of the precache budget.

**Index structure:**
- Run `npx pagefind --site dist` after `astro build` as a post-build step
- Pagefind emits `dist/pagefind/` with `pagefind.js`, `pagefind.wasm`, `pagefind-entry.json`, and sharded `index/*` and `fragment/*` directories
- Single search page at `src/pages/search.astro` mounts the Pagefind UI component
- Per-archive scoped search via Pagefind's `filter` API (each card tagged with its archive slug at build time)

**What this replaces:**
- `api/all.json` (4.6 MB) — no longer needed for search
- `api/pages-index.json` — no longer needed
- `assets/vendor/lunr/lunr.min.js` — no longer needed
- `scripts/build-pages-index.py` — deleted
- `scripts/extract-pdf-text.py` — Pagefind can index PDF text if we feed it as HTML (case prose pages); the separate `.pdftext/` cache can be retired or fed into the SSG as collections

### 3.7 Cross-archive nav consistency — components, not drift gates

**Decision:** Nav and footer become **Astro components** imported by every layout. No build-time drift possible.

**Why this eliminates `sync-nav.py` / `sync-footer.py`:**
- Today: HTML strings spliced into 30+ `.html` files by Python regex, then a CI gate (`sync-nav.yml`) verifies all files match.
- SSG: A single `<Nav.astro>` is imported by `ArchiveLayout.astro`, which is rendered by every page. There's nothing to drift — the component IS the canonical source, and there are no copies of it on disk.
- Removes: `scripts/sync-nav.py`, `scripts/sync-footer.py`, `.github/workflows/sync-nav.yml`, `.github/workflows/sync-footer.yml`, `scripts/templates/nav.py`, `scripts/templates/footer.py` (replaced by `.astro` files)
- Adding archive #16 becomes: add an entry to `src/content/config.ts` `archives` collection. Nav auto-renders from the collection iteration.

### 3.8 Deployment & cutover — branch + preview + DNS swap

**Decision:** Build the SSG on a long-running `ssg-migration` branch with Cloudflare Pages preview deploys. Cut over by promoting the branch to the production custom domain.

**Cutover plan:**
1. **Phase A (parallel):** New `ssg-migration` branch. Cloudflare Pages project created, building from this branch. Preview URL `<hash>.realufo.pages.dev` accessible. Current GitHub Pages site at `realufo.org` untouched.
2. **Phase B (preview alias):** Add `preview.realufo.org` as a Cloudflare Pages custom domain pointing at the preview branch deployment ([Pages preview deployments](https://developers.cloudflare.com/pages/configuration/preview-deployments/)). Run for 1–2 weeks for testing.
3. **Phase C (cutover):** Change DNS — `realufo.org` CNAME / A records move from GitHub Pages → Cloudflare Pages. Promote `ssg-migration` to `main`. Old `CNAME` file removed from repo.
4. **Phase D (rollback path):** Any production deployment that succeeded is a valid Cloudflare Pages rollback target ([Cloudflare Pages Rollbacks](https://developers.cloudflare.com/pages/configuration/rollbacks/)) — instant revert via the dashboard. Worst case: re-point DNS back to GitHub Pages (TTL ≤ 300s during cutover window).

**Per-PR previews:** Every PR gets a unique `<hash>.realufo.pages.dev` URL automatically. Replaces "manual visual review" with shareable preview links — major win for solo-maintainer review cycles.

**Custom-domain constraint to honour:** "only commits to your main production branch will update your custom domains attached to the project." ([Pages config](https://developers.cloudflare.com/pages/configuration/branch-build-controls/)) — so the alias domain pattern (preview.realufo.org → branch alias) needs careful setup; the standard pattern is preview-branch deployments visible via Pages' own subdomain, and `realufo.org` only flips after the merge to main.

### 3.9 Local dev — Astro dev server + Workbox dev mode + Worker miniflare

**Current model:** `python3 -m http.server` serves the built site. Builders run separately.

**Target model:**

| Concern | Local-dev tool | Notes |
|---------|---------------|-------|
| SSG dev | `npm run dev` (Astro dev server) | Hot reload, content-collection re-load on JSON change |
| Service worker dev | `vite-plugin-pwa` `devOptions.enabled: true` | SW runs in dev with a separate cache namespace |
| Scrape pipeline dev | `wrangler dev` (Miniflare) | Local Worker with simulated R2 + KV |
| GitHub Action dev | `act` (nektos/act) | Run workflows locally against the dev Worker's R2 output |
| Pagefind dev | `pagefind --site dist` after a one-time `astro build` | Search dev only against a built snapshot — acceptable cost |
| Binary CDN dev | `_redirects` works locally via `wrangler pages dev dist` | Maps `/binaries/*` to actual GH Release URLs in dev too |

**One command:** `npm run dev` starts Astro + a stub SW. `npm run scrape:dev` starts `wrangler dev` against local fixtures. Solo-maintainer mental model: SSG dev is decoupled from scrape dev; both can be exercised independently.

### 3.10 Build-order / data-flow — single canonical diagram

```
                       SCRAPE                          BUILD                              DEPLOY
                       ──────                          ─────                              ──────
                                                                                                       
[Sources]──fetch──▶[Worker]──stage──▶[R2 incoming]                                                    
                       │                                                                              
                       └─dispatch─▶[GH Action]                                                        
                                       │                                                              
                                       ├─pull─▶[R2 incoming]                                          
                                       │                                                              
                                       ├─release─▶[GH Releases <tag>]                                 
                                       │                                                              
                                       └─commit─▶[git main: data/*.json + release-manifest.json]      
                                                              │                                       
                                                              └─trigger──▶[CF Pages build]            
                                                                              │                       
                                                                              ├─npm ci                
                                                                              ├─astro build           
                                                                              │   ├─Content Layer     
                                                                              │   │   loads data/*    
                                                                              │   ├─renders cards     
                                                                              │   └─writes dist/      
                                                                              ├─pagefind --site dist  
                                                                              │   └─writes pagefind/  
                                                                              ├─vite-plugin-pwa       
                                                                              │   └─injects __WB_MANIFEST
                                                                              └─dist/ → CF Pages CDN  
                                                                                       │              
                                                                                       └─SW activates─▶[client cache rebuild]
```

**Dependencies (what blocks what):**
- Worker scrape → R2 staging → GH Action ingest → git commit → Pages build
- Content Layer loaders depend on `data/*.json` being committed before build starts
- Pagefind depends on Astro build completing (scans `dist/`)
- SW manifest depends on Pagefind completing (precaches chunks)
- SW activation depends on Pages deployment completing

**Build order is strictly linear** at the deploy level (no parallelization across the listed stages without losing determinism). Within `astro build`, Astro parallelizes per-route rendering automatically.

---

## 4. Recommended Project Structure

```
realufo/
├── astro.config.mjs              # Astro + vite-plugin-pwa + integrations
├── content.config.ts             # Content Collections schema (15 archive collections)
├── wrangler.toml                 # Cloudflare Pages + Worker bindings (R2, KV)
├── package.json                  # npm deps (Astro, vite-plugin-pwa, pagefind, wrangler)
├── tsconfig.json
│
├── src/
│   ├── pages/
│   │   ├── index.astro                  # War.gov landing (hand-tuned, splice-equivalent)
│   │   ├── search.astro                 # Pagefind UI
│   │   ├── [slug]/
│   │   │   ├── index.astro              # Archive list page (DYNAMIC over 15 slugs)
│   │   │   ├── page/
│   │   │   │   └── [...page].astro      # Paginated overflow for large archives
│   │   │   └── [case].astro             # Case-detail pages (e.g. rendlesham)
│   │   ├── timeline.astro
│   │   ├── map.astro
│   │   └── 404.astro
│   │
│   ├── content/
│   │   └── config.ts                    # defineCollection() for each archive
│   │
│   ├── layouts/
│   │   ├── RootLayout.astro             # <html>, <head>, SW registration, scanlines
│   │   ├── ArchiveLayout.astro          # extends Root + hero + headlines + archive grid
│   │   └── StoryLayout.astro
│   │
│   ├── components/
│   │   ├── Nav.astro                    # Single canonical nav (no sync-nav.py)
│   │   ├── Footer.astro
│   │   ├── HeroCarousel.astro
│   │   ├── Card.astro                   # Card rendering — once, used everywhere
│   │   ├── FilterBar.astro
│   │   ├── Lightbox.astro
│   │   ├── Stats.astro
│   │   └── SearchUi.astro
│   │
│   ├── lib/
│   │   ├── tone.ts                      # Per-archive tone colours (CLAUDE.md §3.1)
│   │   ├── manifest.ts                  # release-manifest.json → URL resolver
│   │   ├── url.ts                       # escUrl() allowlist (CONCERNS.md fix)
│   │   └── i18n.ts                      # Future-friendly i18n stub (inactive)
│   │
│   └── sw/
│       └── sw.ts                        # Custom Workbox SW (injectManifest target)
│
├── data/                                # ← Source of truth for the SSG
│   ├── wargov.json
│   ├── aaro.json
│   ├── nasa.json
│   ├── nara.json
│   ├── geipan.json
│   ├── uk.json
│   ├── brazil.json
│   ├── chile.json
│   ├── argentina.json
│   ├── canada.json
│   ├── italy.json
│   ├── nz.json
│   ├── peru.json
│   ├── spain.json
│   ├── uruguay.json
│   ├── cases/                           # Long-form case prose
│   │   ├── rendlesham.md
│   │   ├── tic-tac.md
│   │   └── …
│   └── release-manifest.json            # Basename → URL (CDN routing)
│
├── public/                              # Pass-through static assets
│   ├── favicon.svg
│   ├── manifest.webmanifest
│   ├── _redirects                       # /binaries/* → GH Release URLs
│   ├── robots.txt
│   ├── sitemap.xml
│   └── slideshow/                       # Tracked imagery
│
├── workers/
│   ├── scrape/
│   │   ├── src/index.ts                 # Cron + dispatch
│   │   ├── src/scrapers/<slug>.ts       # Per-archive scrapers (one file each)
│   │   ├── src/_http.ts                 # Shared UA + curl-cffi-equivalent
│   │   └── wrangler.toml
│   └── routing/
│       └── src/index.ts                 # Optional: /binaries/* Pages Function
│
├── .github/workflows/
│   ├── ingest-and-release.yml           # Triggered by repository_dispatch from Worker
│   ├── html-validate.yml                # Adapted to dist/ output
│   ├── lighthouse.yml
│   └── links.yml                        # lychee
│
└── .planning/                           # GSD docs (unchanged)
```

**Structure rationale:**
- **`src/content/` + `data/`:** Astro convention — schema in `src/content/config.ts`, data files in `data/`. Single source of truth, no inline JSON in HTML.
- **`src/components/`:** Replaces `scripts/templates/*.py`. Components are imported by layouts; impossible to drift.
- **`src/lib/`:** Pure-TS helpers (manifest URL rewriter, URL escaper, tone palette).
- **`src/sw/`:** Custom service-worker source. `vite-plugin-pwa` consumes this in `injectManifest` mode.
- **`workers/`:** Cloudflare Workers code, kept separate from the SSG to make local dev independent (`wrangler dev`).
- **`data/`:** Git-tracked, edited only by the CI workflow (or manual one-off seed). Solo-maintainer-friendly: diffs are reviewable JSON, not 1,300-line Python.
- **`public/`:** Pass-through assets. `_redirects` is a single file declaring `/binaries/*` → GH Release URL.

---

## 5. Architectural Patterns

### Pattern 1: Content Collections with custom loaders

**What:** Define one collection per archive; load via Astro's Content Layer API with built-in or custom loaders.

**When to use:** Whenever the data lives outside `src/pages/` and needs schema validation + typing.

**Example:**
```typescript
// src/content/config.ts
import { defineCollection, z } from 'astro:content';
import { file } from 'astro/loaders';

const cardSchema = z.object({
  t: z.string(),        // type: PDF | VID | IMG | CATALOG
  ti: z.string(),       // title
  de: z.string().optional(),
  ag: z.string(),
  cat: z.string(),
  date: z.string(),
  region: z.string().optional(),
  l: z.string().optional(),   // local path (deprecated; resolved at build)
  u: z.string().optional(),   // primary URL
  s: z.string().optional(),   // source URL
  th: z.string().optional(),  // thumb
});

const archives = ['wargov','aaro','nasa','nara','geipan','uk','brazil','chile',
                  'argentina','canada','italy','nz','peru','spain','uruguay'] as const;

const collections = Object.fromEntries(
  archives.map(slug => [slug, defineCollection({
    loader: file(`data/${slug}.json`),
    schema: cardSchema,
  })])
);

export { collections };
```

**Trade-offs:** Adds a typed boundary (good — catches malformed CSV/JSON at build); requires the data to be in JSON (the CSV stays as scrape input, gets normalized into JSON by the CI ingest step).

### Pattern 2: Component-driven shared UI

**What:** Nav, Footer, Card, Lightbox are `.astro` components imported by every layout. No template strings, no regex splicing.

**When to use:** Anywhere a shared HTML/CSS block appears in more than one page.

**Example:**
```astro
---
// src/components/Nav.astro
import { getCollection } from 'astro:content';
const archives = await Promise.all([
  'wargov','aaro','nasa','nara','geipan','uk',  // …
].map(async slug => ({
  slug,
  count: (await getCollection(slug)).length,
})));
const { current } = Astro.props;
---
<nav class="primary" aria-label="Archives">
  {archives.map(a => (
    <a href={`/${a.slug}/`} class:list={[{ active: current === a.slug }]}>
      {a.slug.toUpperCase()} <span class="count">{a.count}</span>
    </a>
  ))}
</nav>
```

**Trade-offs:** Components are runtime-free at the browser (zero JS). The cost is learning Astro's island model — minimal for a project this size.

### Pattern 3: Service worker with custom Workbox source + auto-injected manifest

**What:** Hand-written `src/sw/sw.ts` referencing `self.__WB_MANIFEST`, compiled by `vite-plugin-pwa` with the manifest injected at build.

**When to use:** When `generateSW`-style declarative SW config isn't expressive enough (our case: 2xx-only caching, per-asset-type strategies).

**Example:**
```typescript
// src/sw/sw.ts
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';

declare const self: ServiceWorkerGlobalScope;
precacheAndRoute(self.__WB_MANIFEST);  // ← Injected by vite-plugin-pwa

// JSON data: SWR, version on deploy invalidates
registerRoute(
  ({url}) => url.pathname.startsWith('/data/'),
  new StaleWhileRevalidate({ cacheName: 'realufo-data' })
);

// Navigations: NetworkFirst, 2xx-only (preserves dcbc0d7 fix)
registerRoute(
  ({request}) => request.mode === 'navigate',
  new NetworkFirst({
    cacheName: 'realufo-pages',
    plugins: [{
      cacheWillUpdate: async ({response}) =>
        response && response.status >= 200 && response.status < 300 ? response : null,
    }],
  })
);

// Images: CacheFirst with LRU
registerRoute(
  ({request}) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'realufo-img',
    plugins: [new ExpirationPlugin({ maxEntries: 200, maxAgeSeconds: 30*24*60*60 })],
  })
);
```

**Trade-offs:** Slightly more code than `generateSW`, but full control over cache semantics — necessary for the offline-first contract.

### Pattern 4: URL-rewrite layer for binary CDN

**What:** A single `_redirects` file at `public/_redirects` makes `/binaries/<basename>` the canonical asset URL. The SSG writes only `/binaries/<basename>` into HTML; physical location (GH Release tag, R2 bucket) is resolved at request time.

**Example:**
```
# public/_redirects
/binaries/uap-disclosure-2024.pdf  https://github.com/<repo>/releases/download/pdfs-v2/uap-disclosure-2024.pdf  302
/binaries/operation-prato-vol1.pdf https://github.com/<repo>/releases/download/brazil-v1/operation-prato-vol1.pdf  302
/binaries/jellyfish-uap-2024.mp4   https://github.com/<repo>/releases/download/videos-v1/jellyfish-uap-2024.mp4  302
# Overflow > 2 GB
/binaries/full-corpus-archive.zip  https://<bucket>.r2.dev/full-corpus-archive.zip  302
```

The redirects file is **generated at build time** from `release-manifest.json` so a basename → URL change is one git commit. Alternatively, a tiny Pages Function does the lookup dynamically against R2 + git data.

**Trade-offs:** One additional HTTP hop (302) on first request — but the browser caches the redirect (and the SW can be taught to cache redirect targets directly).

### Pattern 5: Lazy hydration via attribute-driven JS

**What:** Components render fully to HTML. Interactivity (lightbox open, filter change) attaches via vanilla JS that operates on `data-*` attributes already in the DOM.

**Example:**
```astro
---
// src/components/Card.astro
const { card, idx } = Astro.props;
---
<article class="card" data-idx={idx} data-archive={card.slug}
         data-binary={card.u} data-source={card.s}>
  <h3>{card.ti}</h3>
  <p>{card.de}</p>
  <button data-action="open">Open</button>
</article>
```

```typescript
// src/scripts/lightbox.ts (loaded once per layout)
document.addEventListener('click', e => {
  const btn = (e.target as Element).closest('[data-action="open"]');
  if (!btn) return;
  const card = btn.closest('.card');
  // Open lightbox using card.dataset.binary / card.dataset.source
});
```

**Trade-offs:** Slightly more JS than full Astro Island hydration, but stays simpler than React/Vue islands and matches CLAUDE.md §7 invariants verbatim. Zero JS framework dependency.

---

## 6. Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **Current (15 archives, ~60k records)** | Astro Content Collections, Pagefind, single SW, GH Releases. Build time on Pages: ~3–6 min. |
| **Mid (20–30 archives, ~200k records)** | Switch large collections (>5k entries) to Astro paginate() with stricter page size. Pagefind handles 200k docs in ~80–200 MB index — start sharding by archive. Build time: ~10–15 min. |
| **Large (50+ archives, 1M+ records, e.g. UK TNA full catalog)** | Consider Astro `server` islands for case-detail pages or move to on-demand-rendered routes via Cloudflare Pages Functions for the long-tail. Pagefind index would exceed reasonable client-side scale; introduce a backend search (Pages Function + indexed JSON in R2 with prefix-search). Build time: needs incremental builds (out of scope until needed). |

### Scaling Priorities

1. **First bottleneck:** Build time on Cloudflare Pages — `getStaticPaths()` memory pressure on archives with >5k records. *Fix:* paginate() + lazy entry loading in components.
2. **Second bottleneck:** Pagefind index size if a single archive grows past ~50k records. *Fix:* per-archive Pagefind indices, search UI scopes to active archive by default.
3. **Third bottleneck:** GitHub Releases per-tag asset count (~1k). *Fix:* per-archive + per-version tags (`<slug>-v1`, `<slug>-v2`, …).
4. **Fourth bottleneck:** Service-worker precache budget (target: ≤ 15 MB precached, otherwise mobile cache eviction). *Fix:* precache HTML + thumbs only; defer PDFs/videos to runtime.

---

## 7. Anti-Patterns

### Anti-Pattern 1: Hydrating cards from inline JSON at runtime

**What people do:** Server-render an empty shell, ship a JSON blob, hydrate cards client-side via JS.
**Why it's wrong:** Reproduces the exact 3.3 MB GEIPAN problem in a new framework. Breaks offline-first (JS must run before content appears). Defeats the SSG's value.
**Do this instead:** Pre-render every card to HTML at build time. Use JS only for interactivity (filter, sort, lightbox) operating on already-painted DOM.

### Anti-Pattern 2: Single Pagefind index for everything

**What people do:** Build one giant Pagefind index over `dist/` with no scoping. Search results mix all 15 archives indiscriminately.
**Why it's wrong:** With 15 archives, users almost always want to scope to one archive at a time. A single 80 MB index loads chunks the user never needs.
**Do this instead:** Use Pagefind's `data-pagefind-filter` attribute to tag every card with its archive slug. UI defaults to "current archive only" with an "all archives" toggle.

### Anti-Pattern 3: Per-archive service worker scope

**What people do:** Register a separate SW at `/<slug>/sw.js` for each archive, reasoning that "each archive is isolated."
**Why it's wrong:** 15 separate cache namespaces; first visit to `/aaro/` doesn't precache `/nasa/`; SW upgrades become 15 separate flips. The current bug is exactly this (CONCERNS.md §"SW registered on only 12 of ~32 pages").
**Do this instead:** Single root-scope SW. Registered from a shared `RootLayout.astro` — there is no way to "forget" to register it on a new page.

### Anti-Pattern 4: Treating R2 as the primary binary CDN

**What people do:** Migrate all PDFs/videos to R2 because it has no per-file limit, dropping GH Releases.
**Why it's wrong:** Loses the durable public mirror (GH Releases) — the project's archival mission depends on the public-domain content being visible at a well-known GitHub URL. If Cloudflare ever drops a free tier, GH Releases is the fallback.
**Do this instead:** GH Releases primary, R2 only for overflow (> 2 GB per file, or archives with > 1k assets per tag). URL-rewrite layer abstracts the physical location so swap is invisible to consumers.

### Anti-Pattern 5: Importing all collections in a single nav build

**What people do:** `await Promise.all(15 collections)` to compute nav counts, called from every page → 15 collection loads per page render.
**Why it's wrong:** Astro caches collection loads per-build, so it's actually fine — BUT if a future contributor introduces a runtime API route, the same pattern explodes.
**Do this instead:** Compute archive counts once into a static `src/lib/archive-meta.ts` constant at config time, or via a build-time `astro:build:setup` hook.

### Anti-Pattern 6: Letting the SW cache HTML 404s

**What people do:** Cache every navigation response indiscriminately.
**Why it's wrong:** Caused the stale-404 bug fixed in commit `dcbc0d7`. A transient 404 (file not yet deployed) gets pinned in client cache; the page stays broken even after the file lands.
**Do this instead:** `cacheWillUpdate` plugin that returns `null` for non-2xx. Test in `npm run test:sw` against a fixture that serves 404 → 200 sequence.

---

## 8. Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **GitHub API (releases)** | `gh release upload <tag> <files> --clobber` from CI; `repository_dispatch` from Worker | Token: `secrets.GITHUB_TOKEN` (already present); `permissions: contents: write` |
| **Cloudflare R2** | Worker R2 binding for staging writes; public-bucket URL for overflow reads | Bucket: `realufo-overflow` (public) + `realufo-staging` (private) |
| **Cloudflare Pages** | Git-integration: auto-deploys on push to `main` | Build cmd: `npm run build && npx pagefind --site dist`. Output dir: `dist`. |
| **Cloudflare Workers (cron)** | `wrangler.toml` cron triggers; KV binding for fingerprints | Cron: daily at 06:00 UTC (matches current scrape schedule) |
| **Wayback Machine CDX API** | Fallback in scraper for blocked sources | Promoted from `dl-aaro.sh:45` pattern to shared `_http.ts` |
| **DVIDS / DOD** | Direct fetch, no auth | Same as today; per-release ID mapping in `data/dvids-map.json` |
| **Umami analytics** | Script tag in `RootLayout.astro` | CSP: `script-src` allows `umami.is` (unchanged from today) |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Worker ↔ R2** | Native binding, async I/O | No HTTP overhead inside Cloudflare network |
| **Worker → GitHub** | HTTPS POST to `/repos/<owner>/<repo>/dispatches` with PAT secret | Worker secret: `GITHUB_DISPATCH_TOKEN` |
| **GitHub Action ↔ R2** | `aws s3` CLI with R2 S3-compatible endpoint OR `wrangler r2 object get` | Choose based on which has fewer install steps |
| **GitHub Action → git** | `git commit + git push` from `actions/checkout` token | Standard; `permissions: contents: write` |
| **Astro build ↔ Content Layer** | Filesystem read of `data/*.json` at build time | Synchronous within Vite |
| **Pages build ↔ Pages CDN** | Wrangler internal | Atomic deploy, instant rollback |
| **Client ↔ SW** | `navigator.serviceWorker.register('/sw.js')` from `RootLayout.astro` | Single root registration |
| **SW ↔ Pages CDN** | Fetch through SW → respects CDN caching, but SW takes precedence | Cache busting via versioned cache names |

---

## 9. Cutover Risk Map

| Risk | Severity | Mitigation |
|------|----------|------------|
| Build time on CF Pages exceeds limit (currently 20 min) | MEDIUM | Profile early with GEIPAN (largest collection); use `astro build --logLevel info`; introduce pagination before final cutover |
| SW registration regression (first-visit users miss SW) | LOW | Single registration point in `RootLayout.astro` — impossible to "forget" on a page |
| Pagefind index too large for slow connections | LOW | Pagefind shards on demand; initial load < 30 KB |
| GH Action cannot read R2 without exposing public bucket | LOW | R2 S3-compatible API with access keys (Worker-only); staging bucket is private |
| Cloudflare Workers cron fails silently | MEDIUM | Worker writes a heartbeat to KV; GH Action checks freshness; alerts on staleness > 36h |
| DNS cutover causes downtime | LOW | DNS TTL ≤ 300s during cutover; Pages preview alias tested for 2 weeks first |
| Inline-JSON readers (external API consumers) break | MEDIUM | Keep `api/all.json` emitted as a build-time artifact from data/ — preserves the existing `/api/*.json` URL contract |

---

## 10. Sources

- [Astro Content Collections (docs.astro.build)](https://docs.astro.build/en/guides/content-collections/) — HIGH confidence
- [Astro Content Loader API reference](https://docs.astro.build/en/reference/content-loader-reference/) — HIGH confidence
- [Astro Content Layer: A Deep Dive](https://astro.build/blog/content-layer-deep-dive/) — HIGH confidence (performance numbers)
- [Astro 6 Migration Guide (2026)](https://www.oscargallegoruiz.com/en/blog/astro-5-migration-guide/) — MEDIUM confidence (third-party)
- [Astro getStaticPaths reference](https://docs.astro.build/en/reference/routing-reference/) — HIGH confidence
- [Implementing Astro Pagination for Large Data](https://dev.to/lovestaco/implementing-astro-pagination-for-large-data-2jmk) — MEDIUM confidence (community pattern)
- [vite-plugin-pwa Astro framework integration](https://vite-pwa-org.netlify.app/frameworks/astro) — HIGH confidence
- [vite-plugin-pwa injectManifest guide](https://vite-pwa-org.netlify.app/guide/inject-manifest) — HIGH confidence
- [@vite-pwa/astro GitHub](https://github.com/vite-pwa/astro) — HIGH confidence
- [Pagefind static site search](https://pagefind.app/) (via Starlight ref) — HIGH confidence
- [Astro Starlight Site Search](https://starlight.astro.build/guides/site-search/) — HIGH confidence
- [Static site search in 2026: Pagefind over Algolia and Lunr](https://dev.to/morinaga/static-site-search-for-astro-in-2026-why-i-picked-pagefind-over-algolia-and-lunr-pg1) — MEDIUM confidence (community comparison)
- [Cloudflare Pages Preview Deployments](https://developers.cloudflare.com/pages/configuration/preview-deployments/) — HIGH confidence
- [Cloudflare Pages Rollbacks](https://developers.cloudflare.com/pages/configuration/rollbacks/) — HIGH confidence
- [Cloudflare Pages Branch deployment controls](https://developers.cloudflare.com/pages/configuration/branch-build-controls/) — HIGH confidence
- [Cloudflare Pages limits (25 MiB / asset)](https://developers.cloudflare.com/pages/platform/limits/) — HIGH confidence
- [Cloudflare R2 limits (~5 TiB / object)](https://developers.cloudflare.com/r2/platform/limits/) — HIGH confidence
- [Cloudflare Workers Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/) — HIGH confidence
- [Cloudflare Workers ↔ GitHub Actions integration](https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/) — HIGH confidence
- [MDN Using Service Workers (scope)](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers) — HIGH confidence
- [Workbox Service Worker lifecycle](https://developer.chrome.com/docs/workbox/service-worker-lifecycle) — HIGH confidence
- [Use R2 as static asset storage for Pages](https://developers.cloudflare.com/pages/tutorials/use-r2-as-static-asset-storage-for-pages/) — HIGH confidence

---
*Architecture research for: offline-first multi-archive SSG with CI-driven scrape pipeline + Cloudflare hosting*
*Researched: 2026-05-25*
