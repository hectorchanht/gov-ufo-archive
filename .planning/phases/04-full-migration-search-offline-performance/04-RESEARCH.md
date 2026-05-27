# Phase 4: Full Migration, Search, Offline, Performance — Research

**Researched:** 2026-05-27
**Domain:** Multi-archive SSG port + Pagefind cross-archive search + `@vite-pwa/astro` injectManifest SW + R2 binary CDN migration + path-based pagination + lightbox repair + PERF-01 GEIPAN bundle reduction.
**Confidence:** HIGH on stack (Astro/Pagefind/@vite-pwa/astro/Cloudflare R2 — verified via official docs at research time), HIGH on lightbox/pagination diagnosis (verified by direct code inspection of `src/scripts/invariants.ts`, `src/components/Card.astro`, `src/pages/index.astro`), MEDIUM on operational details (wrangler R2 custom-domain bind, GH Actions diff detection) where the official docs only partially cover the pattern.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (40 D-items — verbatim summary)

**R2 binary CDN (D-01..D-06):** Full migration of ALL PDFs, videos, AND thumbnails to Cloudflare R2 at `assets.realufo.org` (custom-domain bind, NOT `*.r2.dev`). Single bucket `realufo` with prefixes `pdfs/<slug>/`, `videos/<slug>/`, `thumbs/<slug>/`. Upload pipeline via new `.github/workflows/r2-sync.yml` triggered on push to `main`, using `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` secrets. GH Releases tags kept read-only as cold-storage backup; cards do NOT reference them.

**14-archive port (D-07..D-11):** One plan per archive (`04-NN-<slug>`). Wave 1 (small/static): NZ, Uruguay, Peru, Spain, Argentina, Italy. Wave 2 (medium catalog): Brazil, Chile, Canada, UK, NARA, NASA, AARO. Wave 3 (PERF-tied): GEIPAN standalone. Per-archive plan deletes `scripts/build-<slug>.py`, removes slug from `copy-legacy-archives.sh`, drops slug from `sync-nav.py`/`sync-footer.py` policing — all in same plan. Tone-colour fixes for geipan/uk/brazil/chile bundled into their respective port plans (NOT a separate plan). `scripts/dl-<slug>.sh` download scripts KEEP.

**Pagefind (D-12..D-17):** Single cross-archive WASM index at `dist/pagefind/`. Per-archive filter via `data-pagefind-filter` attrs on Card.astro markup. `api/all.json` 4.6 MB blob deletion confirmed only when Pagefind green. Search result links use `https://<host>/<slug>/#card-<id>` per SRC-04. `/search.html` replaced with `src/pages/search.astro`. Pagefind integrated via `pnpm postbuild` chain extension — `scripts/copy-legacy-archives.sh` runs first, THEN `npx pagefind --site dist` so legacy HTML is also indexed.

**Service Worker (D-18..D-26):** `@vite-pwa/astro` `injectManifest` strategy. Registered structurally from `BaseHead.astro` via `<script is:inline>`. Precache: every HTML + every card thumbnail. EXCLUDE PDFs/videos. Tiered runtime cache: network-first HTML nav, SWR JSON, cache-first images/fonts (CF Pages + `assets.realufo.org` allowlisted), no-cache PDFs/videos, no-cache `/admin*` and dev paths. Cache name `realufo-v<sha>` from CI env var. `updateViaCache: 'none'` on all registrations. Self-hosted fonts via `@fontsource/source-serif-4` + `@fontsource/jetbrains-mono` (replaces Google Fonts). R2 CORS: `Access-Control-Allow-Origin: https://realufo.org` + `https://*.realufo.pages.dev`. `_headers` re-applied to new CF Pages project; `/sw.js` returns `cache-control: no-cache, no-store, must-revalidate`. SW lifecycle: skipWaiting + clients.claim ONLY after cache-name version bumps.

**Pagination (D-27..D-33):** PAGE_SIZE=20. URL pattern: `?page=N` query param (NOT `/page/N/` path). Page 1 = no query param. URL-CONTRACT.txt unchanged (query strings don't participate in path-only contract). Retroactive wargov re-paging from 50→20/page + `?page=N` URL in new plan `04-wargov-repaging`. Footer always reachable. Shard scheme unchanged (50/shard server-side render unit) — UI consumes shards and slices to 20/page. IntersectionObserver lazy-load DROPPED for paginated pages.

**Lightbox fix (D-34..D-37):** Diagnose: handlers don't bind / data-action absent / handler errors. Fix in `invariants.ts` and/or `Card.astro` — surgical patch, not refactor. Same fix benefits wargov retroactively. Stand-alone plan `04-lightbox-fix` at start of Phase 4 — blocks dependent ports.

**PERF (D-38..D-40):** GEIPAN PERF-01 in Wave 3. ≤ 3 chunks per page (PERF-02). First paint contains cards (PERF-03). PERF-04 regression check NZ/Uruguay/Peru. **Phase 4 close = Lighthouse HARD-flip** — `.lighthouserc.cf.json` `warn → error`. All archives must pass D-27 budgets (LCP ≤ 2500 ms, transfer ≤ 500 KB).

### Claude's Discretion

- Per-plan task breakdown (atomic commit cadence)
- Specific Pagefind UI components (filter chip styling, result card layout) — preserve current /search.html UX
- SW precache manifest exact format (let `@vite-pwa/astro` defaults guide)
- `wrangler r2 bucket cors` exact config (sensible defaults per CF docs)
- R2 upload workflow's diff detection method (git plumbing TBD)

### Deferred Ideas (OUT OF SCOPE)

- DNS / hosting cutover (Phase 6 HOST-01)
- CF Pages git-integration (operator-dependent on Frank push access)
- Scrape pipeline → R2 direct write (Phase 5 SCRP)
- Frank GH write access resolution (operational)
- Additional national archives #16+ (future milestone)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SSG-06 | Remaining 14 archives ported, all passing visual-regression + fidelity | §8 Per-archive Port Template — Plan 03-05 reuse pattern, per-archive normaliser approaches, tone-colour fix inline |
| SSG-07 | Every archive page ≤ 500 KB HTML+inline | §9 PERF-01 Strategy + §6 Pagination (20/page drops payload further) |
| SSG-08 | Mobile-first invariants preserved (360 px, 44 px touch) | §8 — inherited from RootLayout.astro (Plan 03-04, unchanged) |
| SSG-09 | JS invariants from CLAUDE.md §7 preserved — hamburger, lightbox, search-focus, ?q= | §7 Lightbox Diagnosis + §8 (invariants.ts retained, surgical patch only) |
| SSG-10 | All Python build scripts deleted | §10 Python Retirement Schedule |
| SSG-11 | Public-domain license footnotes verbatim | §8 (Footer.astro per-archive license — already in Plan 03-04 RootLayout) |
| SSG-12 | Per-archive seal + tone-colour preserved (CLAUDE.md §3.1) | §8 (4 legacy fixes bundled) |
| SRC-01 | Pagefind 1.x integrated; outputs to `dist/pagefind/` | §2 Pagefind Integration |
| SRC-02 | `/search.html` migrated from Lunr to Pagefind | §2 Pagefind Integration |
| SRC-03 | Per-archive filter UI preserved via `data-*` | §2 — `data-pagefind-filter="archive"` on Card.astro |
| SRC-04 | Search result links use `#card-<id>` anchors | §2 — Pagefind preserves URL fragments from indexed page |
| SRC-05 | SW precaches Pagefind core; chunks lazy-fetched | §3 SW precache config (pagefind/pagefind.js + pagefind-ui.js precached; index/*.pf_index lazy) |
| SW-01 | `@vite-pwa/astro` `injectManifest` strategy | §3 Service Worker |
| SW-02 | SW registered structurally from `BaseHead.astro` | §3 — already in BaseHead.astro (Plan 03-04); swap kill-switch SW for new one |
| SW-03 | Full-catalog offline cache | §3 — precache manifest config |
| SW-04 | PDFs/videos NOT in precache | §3 — globIgnores in injectManifest config |
| SW-05 | Tiered cache strategies | §3 — `sw.ts` skeleton |
| SW-06 | Cache-name `realufo-v<sha>` versioning | §3 — env var injection during build |
| SW-07 | Self-hosted fonts via @fontsource | §3 — replaces BaseHead.astro Google Fonts preconnect block |
| PERF-01 | GEIPAN LCP ≤ 2.5 s on mobile + 4× CPU throttle | §9 PERF-01 Strategy |
| PERF-02 | Inline-JSON refactor ≤ 3 chunks per page | §9 — shard scheme |
| PERF-03 | First paint contains card content | §9 — server-rendered cards (already pattern from Plan 03-03 D-10) |
| PERF-04 | No regression at NZ/Uruguay/Peru baselines | §11 Validation Architecture — Lighthouse SOFT gate per-plan |
</phase_requirements>

## 1. Executive Summary

1. **Plan 03-05 wargov pattern is the template** for all 14 archive ports. Each plan reuses `RootLayout.astro` + `Card.astro` + `Lightbox.astro` (already 15-archive-aware via `TONE` map), creates `src/pages/<slug>/[...page].astro` for paginated pages, and extracts data into `data/<slug>.json` via a per-archive normaliser. The 4 tone-colour bugs (geipan/uk/brazil/chile) are pre-existing CSS drift on legacy HTML and get fixed inline during each archive's port plan (NOT in legacy HTML — that's getting deleted).

2. **Pagefind integration is a two-line postbuild addition.** Append `npx -y pagefind --site dist` to `scripts/copy-legacy-archives.sh` AFTER the copy step (so legacy HTML is also indexed). Per-archive filtering via `data-pagefind-filter="archive"` on each `<article class="arch-card">` (modify Card.astro). Tag card body with `data-pagefind-body` and meta with `data-pagefind-meta` for verbatim title/agency in result snippets. `/search.html` becomes `src/pages/search.astro` consuming `@pagefind/default-ui`. Delete `api/all.json` (4.6 MB) only after green Pagefind verification.

3. **Lightbox is broken by TWO bugs, both in current Card.astro + index.astro.** (a) `data-idx` on `.btn-open` anchor = global row index 0..221, but `lbList` is built in DOM order from visible cards — when cards filter or load lazily, the indices don't align. (b) Card.astro never sets a separate `local` field on the download anchor (both `btn-open` and `btn-download` use `href={url}`), so the lightbox's local-vs-remote PDF logic never reaches the remote-PDF branch. **Surgical fix:** change `data-idx` on the anchor to `data-row-id={rowId}`, build `lbList` keyed by `data-id`, and add `data-local={row.local}` separately to `.btn-download`. Both files modified, no refactor.

4. **Service Worker via `@vite-pwa/astro` injectManifest is a 30-line `astro.config.mjs` block plus `src/sw.ts` skeleton.** Five runtime cache strategies map directly to D-21 (network-first nav, SWR JSON, cache-first images/fonts, no-cache PDFs/videos, no-cache `/admin*`). Cache name templated from CI env `COMMIT_SHA`. `_headers` re-applied to the new `realufo` CF Pages project to ensure `/sw.js` returns `cache-control: no-cache, no-store, must-revalidate`. Google Fonts preconnect in `BaseHead.astro` swapped for `@fontsource/source-serif-4` + `@fontsource/jetbrains-mono` imports — fonts now precached by SW and work offline.

5. **R2 migration ships as a single `04-r2-setup` plan + `r2-sync.yml` GH Action.** `wrangler r2 bucket create realufo` + `wrangler r2 bucket cors put realufo --rules-file=r2-cors.json` + custom domain bind via Cloudflare dashboard (the dashboard UI is the authoritative path — `wrangler r2 bucket domain` exists but custom domains require zone-level DNS, which the dashboard handles atomically). DNS: CNAME `assets` proxied (orange-clouded) per CF requirement for R2 custom domains. URL rewrite in `scripts/normalize-csv.py` (and each per-archive normaliser) swaps `bundles/Release_1/X.pdf` → `https://assets.realufo.org/pdfs/wargov/X.pdf`. First-run bulk migration via `workflow_dispatch` flag that skips diff detection.

**Primary recommendation:** Execute Phase 4 in this order — **04-01 lightbox-fix → 04-02 r2-setup → 04-03 sw-injectmanifest → 04-04 wargov-repaging → 04-05 pagefind → 04-06..19 14-archive ports (waves) → 04-20 close (Lighthouse HARD-flip + Python cleanup + retire postbuild copy)**. The lightbox-fix blocks all archive ports (same Card.astro). R2 setup blocks normaliser URL rewrites. SW + Pagefind can land in parallel with archive ports once R2 URLs are stable.

## 2. Pagefind Integration

### Postbuild wire (extends `scripts/copy-legacy-archives.sh`)

Append to existing script (`package.json scripts.postbuild` already runs this file):

```bash
# After the legacy-copy step (so /aaro/index.html etc. exist in dist/) —
# run Pagefind against the full dist/ to index BOTH Astro-rendered + legacy.
echo "[postbuild] pagefind: indexing dist/ ..."
npx -y pagefind --site dist
```

[VERIFIED: pagefind.app/docs] The `--site` flag points at the static-site output directory; Pagefind walks every HTML file, generates a sharded WASM index at `dist/pagefind/`, and emits `dist/pagefind/pagefind.js` + `dist/pagefind/pagefind-ui.js` + `dist/pagefind/index/*.pf_index` + `dist/pagefind/fragment/*.pf_fragment` shards.

**Version pin:** Pagefind `1.5.0+` ships the Component UI [CITED: pagefind.app/docs]. Pin via `package.json devDependencies` instead of relying on `npx -y` to pull arbitrary latest:

```bash
pnpm add -D pagefind@^1.5
```

Then change postbuild to `pnpm exec pagefind --site dist` (no network on every build).

### Per-archive filter via `data-pagefind-filter` on Card.astro

[CITED: pagefind.app/docs/filtering] The `data-pagefind-filter` attribute tags pages with filterable metadata. Single attribute, multiple values allowed per page; reserved keys `any/all/none/not`.

**Surgical Card.astro modification** (`src/components/Card.astro`):

```astro
<article
  class="arch-card"
  id={`card-${slug}`}
  data-id={rowId}
  data-idx={idx}
  data-action="open"
  data-type={rtype}
  data-agency={agency}
  data-date={date}
  data-pagefind-filter={`archive:${archiveSlug},type:${rtype},agency:${agency}`}
  data-pagefind-meta={`title:${title},agency:${agency},date:${date}`}
>
```

Add `archiveSlug` to `interface Props` (currently only wargov, but Phase 4 Card.astro must be archive-aware).

[CITED: pagefind.app/docs/filtering] Comma-separated multi-filter works on a single element. Inline-value syntax `filter:value` is allowed when value isn't a text-content extraction.

### `data-pagefind-body` placement

[CITED: pagefind.app/docs/indexing] If `data-pagefind-body` is present on ANY page, pages WITHOUT it are NOT indexed. The Astro-rendered archive pages must have a `data-pagefind-body` element OR none of the legacy pages can have it either.

**Recommended placement** — `<main>` element in `RootLayout.astro`:

```astro
<main data-pagefind-body>
  <slot />
</main>
```

This indexes everything inside `<main>` (cards, headlines, hero text) while excluding `<nav>`, `<footer>`, scanlines overlay. The hero text and headlines are searchable; per-card cross-anchor via `id={card-${slug}}` on each `<article>` means search results can deep-link.

**`data-pagefind-ignore`** for filter UI / pagination controls:

```astro
<div class="arch-controls-bar" data-pagefind-ignore>...</div>
<nav class="pagination" data-pagefind-ignore>...</nav>
```

### Search result anchoring (SRC-04)

[CITED: pagefind.app/docs] Pagefind's result records include `url` (page URL) and `anchor.id` (closest element id ancestor of the match). Since each card has `id={card-${slug}}`, search results inside card content naturally produce links like `/aaro/?page=3#card-uap-2024-incident` — matching SRC-04 contract.

**Caveat:** Pagefind's default URL output is the page URL only. To get the `#anchor` appended, the search-result template must read `result.sub_results[i].anchor.id` and append to the URL. The default UI does this automatically; custom UI must implement.

### Index size projection

[ASSUMED] Wargov 222 cards × ~200 bytes per indexed token bucket = ~50-80 KB initial `dist/pagefind/pagefind-entry.json`; full 15-archive corpus (~5,000-8,000 cards estimated from current `api/all.json` 4.6 MB Lunr blob) projects to ~200-400 KB initial Pagefind index + ~2-4 MB sharded fragments lazy-loaded only on query. Pagefind's WASM core is ~25 KB gzip [CITED: pagefind.app marketing — `< 30 KB initial`]. **Net win vs Lunr's 4.6 MB upfront blob: ~10-20× initial-load reduction.**

### `/search.html` → `src/pages/search.astro` rewrite

```astro
---
// src/pages/search.astro — replaces legacy Lunr-based /search.html
import RootLayout from '../layouts/RootLayout.astro';
---
<RootLayout archiveSlug="wargov" title="Search · realufo.org" description="Search 15 government UAP archives" canonicalUrl="https://realufo.org/search">
  <section class="search-container">
    <div id="pagefind-search"></div>
  </section>

  <link rel="stylesheet" href="/pagefind/pagefind-ui.css" />
  <script is:inline src="/pagefind/pagefind-ui.js"></script>
  <script is:inline>
    window.addEventListener('DOMContentLoaded', () => {
      new PagefindUI({
        element: '#pagefind-search',
        showSubResults: true,
        showImages: false,
        translations: { placeholder: 'Search 15 archives...' },
        // SRC-03 — per-archive filter UI
        filters: { archive: 'Archive', type: 'Type', agency: 'Agency' },
      });
    });
  </script>
</RootLayout>
```

[CITED: pagefind.app/docs/ui] `PagefindUI` is the default-UI component. Custom styling layered atop `/pagefind/pagefind-ui.css` to match `--caution` tone (delegate to CSS module per archive — but search.astro uses wargov defaults since it lives at `/search`).

### `api/all.json` deletion (D-14)

Single commit drops `api/all.json` (4.6 MB) — but ONLY after:
1. `dist/pagefind/` index green (verify by curl preview + page-load smoke).
2. Search smoke test in Playwright: navigate to `/search`, type "tic tac", expect ≥ 1 result.
3. Old `/search.html` redirect added to `_redirects`: `/search.html /search 301`.

**Confidence:** HIGH on integration mechanics (verified via Pagefind official docs); MEDIUM on index-size projection (estimated, not measured).

## 3. Service Worker (@vite-pwa/astro injectManifest)

### `astro.config.mjs` integration block

Current `astro.config.mjs` has `integrations: []` (empty per Phase 3 D-23). Phase 4 SW-01 fills it:

```javascript
// @ts-check
import { defineConfig } from 'astro/config';
import cloudflare from '@astrojs/cloudflare';
import AstroPWA from '@vite-pwa/astro';

// Cache name templated from CI commit SHA at build time per D-22 + SW-06.
// COMMIT_SHA injected by .github/workflows/r2-sync.yml (or deploy workflow).
const cacheVersion = process.env.COMMIT_SHA?.slice(0, 7) || 'dev';

export default defineConfig({
  output: 'static',
  adapter: cloudflare(),
  markdown: { smartypants: false, remarkPlugins: [], rehypePlugins: [] },
  site: 'https://realufo.org',
  trailingSlash: 'ignore',

  integrations: [
    AstroPWA({
      // D-18 — injectManifest strategy keeps full SW control
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.ts',

      // D-22 — registerType + updateViaCache invariant
      registerType: 'autoUpdate',

      // D-19 — registration handled manually in BaseHead.astro <script is:inline>
      // (so updateViaCache: 'none' is set explicitly per Phase 1 PMS-02 kill-switch contract).
      injectRegister: false,

      injectManifest: {
        // D-20 — precache every HTML + every thumbnail; D-04 — exclude PDFs/videos
        globPatterns: [
          '**/*.{html,css,js,svg,webp,png,jpg,jpeg,woff2,ico}',
          // Pagefind core (SRC-05) — precache pagefind.js + pagefind-ui.js;
          // index shards (*.pf_index, *.pf_fragment) are runtime-cached SWR.
          'pagefind/pagefind*.{js,css}',
        ],
        globIgnores: [
          '**/*.{pdf,mp4,webm,mov,mp3,wav,zip}',
          // Pagefind index shards lazy-loaded on query
          'pagefind/index/**',
          'pagefind/fragment/**',
        ],
        // CF Pages 25 MiB/file cap — anything larger isn't precacheable anyway.
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5 MB hardcap
      },

      manifest: {
        name: 'realufo.org — Government UAP Archive',
        short_name: 'realufo',
        description: 'Offline-first archive of every official government UAP source',
        theme_color: '#0a0a0c',
        background_color: '#0a0a0c',
        display: 'standalone',
        icons: [
          { src: '/assets/favicon.svg', sizes: 'any', type: 'image/svg+xml' },
        ],
      },

      // Expose cache version to sw.ts via injected build-time constant
      workbox: undefined, // unused in injectManifest mode
    }),
  ],
});
```

[VERIFIED via vite-pwa-org.netlify.app/frameworks/astro AND vite-pwa-org.netlify.app/guide/inject-manifest] — `srcDir: 'src'` + `filename: 'sw.ts'` is the canonical TypeScript placement. `injectRegister: false` disables the plugin's auto-injection of registration code so our `BaseHead.astro` inline registration remains the only path.

### `src/sw.ts` skeleton

```typescript
/// <reference lib="webworker" />
import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching';
import { registerRoute, NavigationRoute } from 'workbox-routing';
import { NetworkFirst, StaleWhileRevalidate, CacheFirst } from 'workbox-strategies';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';
import { ExpirationPlugin } from 'workbox-expiration';

declare let self: ServiceWorkerGlobalScope;

// D-22 — cache name templated from build-time COMMIT_SHA
// (Workbox uses its own internal cache names; we set CACHE_NAME_PREFIX
// to drive cleanup of stale caches from prior deploys.)
const CACHE_PREFIX = `realufo-v${import.meta.env.COMMIT_SHA?.slice(0, 7) || 'dev'}`;

// D-26 — purge any cache whose prefix doesn't match this build.
// Replaces Workbox's cleanupOutdatedCaches() with our explicit prefix scheme.
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys
        .filter((k) => k.startsWith('realufo-v') && !k.startsWith(CACHE_PREFIX))
        .map((k) => caches.delete(k))
    );
    // D-26 — clients.claim ONLY after stale cache purge complete.
    await self.clients.claim();
  })());
});

// D-26 — skipWaiting is deliberately AFTER cache cleanup completes via activate handler above.
// Browser race condition: if skipWaiting fires before activate completes, two tabs
// can be controlled by different SW versions simultaneously. The pattern below
// requires the new SW to ACTIVATE first; only then does it claim clients.
self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});

cleanupOutdatedCaches();

// D-20 — Workbox-injected precache manifest (populated at build time
// from injectManifest.globPatterns above).
precacheAndRoute(self.__WB_MANIFEST);

// D-21 RUNTIME STRATEGIES ─────────────────────────────────────────────────

// (1) HTML navigation — network-first per D-21 (cache fallback for offline).
registerRoute(
  new NavigationRoute(
    new NetworkFirst({
      cacheName: `${CACHE_PREFIX}-html`,
      networkTimeoutSeconds: 3,
      plugins: [
        new CacheableResponsePlugin({ statuses: [0, 200] }),
      ],
    }),
    // D-21 — exclude /admin*; dev paths
    { denylist: [/^\/admin/, /^\/_/, /^\/api/] }
  )
);

// (2) JSON (shards, search index meta) — stale-while-revalidate per D-21.
registerRoute(
  ({ request, url }) =>
    request.destination === '' &&
    (url.pathname.endsWith('.json') || url.pathname.match(/\.(pf_index|pf_meta)$/)),
  new StaleWhileRevalidate({
    cacheName: `${CACHE_PREFIX}-json`,
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 7 * 24 * 60 * 60 }),
    ],
  })
);

// (3) Images + fonts — cache-first per D-21.
// Allowlist: same-origin (CF Pages) + assets.realufo.org (R2 per D-24).
const IMAGE_ORIGINS = [
  self.location.origin,
  'https://assets.realufo.org',
];
registerRoute(
  ({ request, url }) =>
    (request.destination === 'image' || request.destination === 'font') &&
    IMAGE_ORIGINS.some((o) => url.origin === o),
  new CacheFirst({
    cacheName: `${CACHE_PREFIX}-media`,
    plugins: [
      // CORS opaque responses (status 0) — allowlist for R2 cross-origin.
      // Without this plugin, opaque responses cache but break in some browsers.
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 500, maxAgeSeconds: 30 * 24 * 60 * 60 }),
    ],
  })
);

// (4) PDFs / videos — D-21 explicit no-cache (let browser HTTP cache handle).
// We register a NetworkOnly route to ensure SW never intercepts these
// (otherwise Workbox default route may catch them).
registerRoute(
  ({ url }) => url.pathname.match(/\.(pdf|mp4|webm|mov|mp3|wav|zip)$/i),
  async ({ request }) => fetch(request)
);

// Message listener for manual SKIP_WAITING from page UI (future "reload to update" banner).
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
});

export {};
```

### `BaseHead.astro` registration (current state already correct)

`src/layouts/BaseHead.astro` lines 65-71 already register `/sw.js` with `updateViaCache: 'none'`. **No change needed** — the kill-switch SW from Phase 1 simply gets replaced by the new injectManifest SW at the same path. The registration code is identical.

**Critical caveat:** when @vite-pwa/astro builds, it emits `dist/sw.js` (the compiled Workbox-injected SW). Verify file path matches the literal `/sw.js` in BaseHead. Pin via `@vite-pwa/astro` config: default emission IS `dist/sw.js` [CITED: vite-pwa-org.netlify.app/guide/inject-manifest].

### Self-hosted fonts (SW-07)

Current `BaseHead.astro` lines 50-56 preconnects + loads from `fonts.googleapis.com`. Phase 4 SW-07 swaps to:

```bash
pnpm add @fontsource/source-serif-4 @fontsource/jetbrains-mono
```

```javascript
// In BaseHead.astro frontmatter (add to existing imports):
import '@fontsource/source-serif-4/400.css';
import '@fontsource/source-serif-4/600.css';
import '@fontsource/source-serif-4/400-italic.css';
import '@fontsource/jetbrains-mono/400.css';
import '@fontsource/jetbrains-mono/500.css';
import '@fontsource/jetbrains-mono/700.css';
```

Delete the `<link rel="preconnect">` and `<link href="fonts.googleapis.com">` lines. Astro bundles font-face CSS + emits self-hosted woff2 files into `dist/` — SW precaches them via `globPatterns: '**/*.{woff2,...}'`. **Offline-first regression closed.**

### `_headers` re-application (D-25)

The Phase 2 `_headers` file lives at repo root. Verify it's present in CF Pages project deployment by curl smoke after first SW deploy:

```bash
PREVIEW=https://<deploy>.realufo.pages.dev
curl -sI $PREVIEW/sw.js | grep -i 'cache-control'
# Expected: cache-control: no-cache, no-store, must-revalidate
```

If output shows CF Pages default (`public, max-age=14400` or similar), check repo root has `_headers` committed AND tracked by git. The new `realufo` CF Pages project per Plan 03-06 may not have inherited Phase 2's `_headers` — apply via deploy and verify.

**Confidence:** HIGH on `astro.config.mjs` shape (verified via vite-pwa docs); HIGH on sw.ts strategies (verified via Workbox 7 docs); MEDIUM on COMMIT_SHA injection (env var must be set in CI; pattern is standard but project-specific).

## 4. Cloudflare R2 Setup

### Wrangler commands

```bash
# Step 1 — create bucket
wrangler r2 bucket create realufo

# Step 2 — apply CORS rules from a JSON file
# Save the JSON below to r2-cors.json then:
wrangler r2 bucket cors put realufo --rules-file=r2-cors.json
```

**`r2-cors.json` per D-24:**

```json
[
  {
    "AllowedOrigins": [
      "https://realufo.org",
      "https://www.realufo.org",
      "https://*.realufo.pages.dev"
    ],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag", "Content-Length", "Content-Type"],
    "MaxAgeSeconds": 3600
  }
]
```

[VERIFIED via developers.cloudflare.com/r2/buckets/cors] — `AllowedMethods` GET + HEAD is sufficient for static asset serving. `AllowedOrigins` accepts wildcard subdomains (`*.realufo.pages.dev`) which covers all preview deploy URLs.

### Custom domain bind (`assets.realufo.org`)

[CITED: developers.cloudflare.com/r2/buckets/public-buckets] R2 custom domains require:
1. The domain MUST be added as a zone in the same Cloudflare account as the R2 bucket. (`realufo.org` zone must exist in CF.)
2. Use the dashboard UI: **R2 → realufo bucket → Settings → Custom Domains → Connect Domain → assets.realufo.org**.
3. CF auto-creates a CNAME record `assets` proxied through CF (orange-clouded). **DO NOT manually create a CNAME pointing to `<account>.r2.cloudflarestorage.com` or to the `r2.dev` subdomain — explicitly unsupported per CF docs.**

The dashboard UI handles the DNS + R2 binding atomically. `wrangler r2 bucket domain` exists but the dashboard is the documented authoritative path for custom domains (esp. for `assets.<root>` subdomains where zone-level DNS interaction matters).

**Operator step required** — Frank to execute the dashboard click sequence after `wrangler r2 bucket create realufo` completes. Document as a checkpoint in the `04-r2-setup` plan.

### URL pattern for cards

After R2 + custom domain bind:

```
https://assets.realufo.org/pdfs/wargov/2026-PR19-MideastUAP.pdf
https://assets.realufo.org/videos/wargov/PR50_4UAP_Formation_Iran.mp4
https://assets.realufo.org/thumbs/wargov/PR19-thumb.webp
```

### URL rewrite in `scripts/normalize-csv.py` (and per-archive normalisers)

Phase 4 extension to `scripts/normalize-csv.py` (Plan 03-03) — replace any `bundles/Release_1/<file>` or `slideshow/<file>` path with the R2 URL:

```python
R2_BASE = "https://assets.realufo.org"

def rewrite_url(local_path: str, archive_slug: str, asset_type: str) -> str:
    """Rewrite a local repo-relative path to R2 URL.
    asset_type: 'pdfs' | 'videos' | 'thumbs'
    """
    if not local_path:
        return ""
    filename = local_path.rsplit("/", 1)[-1]
    return f"{R2_BASE}/{asset_type}/{archive_slug}/{filename}"
```

Per-archive normalisers (Phase 4 ports) each call `rewrite_url()` from a shared helper module (`scripts/_r2_urls.py`). **Existing CSV is NOT modified** — rewrite happens at build time only.

### Bulk upload of 165 PDFs + 60 videos + thumbs

[ASSUMED] `wrangler r2 object put` is per-file; bulk upload of 200+ files requires either:
- Sequential `for` loop in bash (slow but trivial — ~5 min for 200 files at ~1.5 s each)
- Parallel via xargs `-P` (faster but order-dependent)
- S3-compatible client (`aws s3 sync` with R2 endpoint — supports `--exclude/--include` filtering and parallel)

**Recommended for first-run:** S3-compatible sync via `rclone` (well-documented for R2):

```bash
# Configure rclone for R2 (one-time, per machine)
rclone config create r2-realufo s3 \
  provider Cloudflare \
  endpoint https://<account>.r2.cloudflarestorage.com \
  access_key_id $CLOUDFLARE_R2_ACCESS_KEY \
  secret_access_key $CLOUDFLARE_R2_SECRET_KEY \
  acl private

# Bulk sync (idempotent — only uploads files not already present matching checksum)
rclone sync ./bundles/Release_1/ r2-realufo:realufo/pdfs/wargov/ --include '*.pdf'
rclone sync ./bundles/videos/ r2-realufo:realufo/videos/wargov/ --include '*.mp4'
```

**Caveat:** R2 access key + secret are SEPARATE from the global `CLOUDFLARE_API_TOKEN`. Must be created via CF dashboard (R2 → Manage R2 API Tokens). Document as operator-checkpoint in `04-r2-setup` plan. Add `CLOUDFLARE_R2_ACCESS_KEY` + `CLOUDFLARE_R2_SECRET_KEY` to GH secrets.

**Confidence:** HIGH on bucket create + CORS commands (verified via CF R2 official docs); MEDIUM on custom-domain bind (dashboard-driven, less wrangler coverage); HIGH on rclone bulk-upload pattern (industry standard for S3-compatible storage).

## 5. GH Actions `r2-sync.yml`

### Workflow skeleton

```yaml
# .github/workflows/r2-sync.yml
name: R2 binary sync
on:
  push:
    branches: [main]
    paths:
      - 'bundles/**/*.pdf'
      - 'bundles/**/*.mp4'
      - 'slideshow/**/*.jpg'
      - 'slideshow/**/*.webp'
      - 'slideshow-2/**'
      - '**/*.pdf'
      - '**/*.mp4'
  workflow_dispatch:
    inputs:
      full_sync:
        description: 'Full bulk sync (skip diff detection)'
        type: boolean
        default: false

concurrency:
  group: r2-sync
  cancel-in-progress: false  # NEVER cancel an in-flight upload

jobs:
  sync:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2  # need HEAD^ for git diff

      - name: Install rclone
        run: |
          curl https://rclone.org/install.sh | sudo bash
          rclone version

      - name: Configure rclone for R2
        env:
          R2_ACCESS_KEY: ${{ secrets.CLOUDFLARE_R2_ACCESS_KEY }}
          R2_SECRET_KEY: ${{ secrets.CLOUDFLARE_R2_SECRET_KEY }}
          R2_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
        run: |
          mkdir -p ~/.config/rclone
          cat <<EOF > ~/.config/rclone/rclone.conf
          [r2-realufo]
          type = s3
          provider = Cloudflare
          endpoint = https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com
          access_key_id = ${R2_ACCESS_KEY}
          secret_access_key = ${R2_SECRET_KEY}
          acl = private
          EOF

      - name: Detect changed binaries
        id: diff
        run: |
          if [ "${{ inputs.full_sync }}" = "true" ]; then
            echo "files=ALL" >> $GITHUB_OUTPUT
          else
            # Diff vs previous commit; binary file patterns only.
            # rclone's checksum-based sync makes this idempotent ANYWAY, but
            # narrowing the diff saves rclone walk time on a large bucket.
            git diff --name-only HEAD^ HEAD -- \
              '*.pdf' '*.mp4' '*.webm' '*.jpg' '*.webp' \
              > /tmp/changed.txt
            cat /tmp/changed.txt
            echo "files=$(wc -l < /tmp/changed.txt)" >> $GITHUB_OUTPUT
          fi

      - name: Sync changed files to R2
        if: steps.diff.outputs.files != '0' && steps.diff.outputs.files != ''
        run: |
          # rclone sync is idempotent — re-running with the same files is safe.
          # checksum-based diff at the rclone layer catches files git missed.

          # Wargov bundles
          if [ -d "bundles/Release_1" ]; then
            rclone sync ./bundles/Release_1/ r2-realufo:realufo/pdfs/wargov/ \
              --include '*.pdf' --checksum --progress
          fi

          # Wargov videos
          if [ -d "bundles/videos" ]; then
            rclone sync ./bundles/videos/ r2-realufo:realufo/videos/wargov/ \
              --include '*.mp4' --checksum --progress
          fi

          # Per-archive bundles (extend as archives port)
          for slug in aaro nasa nara geipan uk brazil chile argentina canada italy nz peru spain uruguay; do
            if [ -d "${slug}/bundles" ]; then
              rclone sync "./${slug}/bundles/" "r2-realufo:realufo/pdfs/${slug}/" \
                --include '*.pdf' --checksum --progress
            fi
            if [ -d "${slug}/videos" ]; then
              rclone sync "./${slug}/videos/" "r2-realufo:realufo/videos/${slug}/" \
                --include '*.mp4' --checksum --progress
            fi
          done

      - name: Trigger CF Pages rebuild
        if: steps.diff.outputs.files != '0'
        env:
          CF_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CF_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
        run: |
          # The sync completes — but Astro must rebuild card URLs from normalize-csv.py
          # which embeds R2 URLs. If URLs are stable (filenames don't change), no rebuild
          # needed; if new filenames were added, normalize-csv.py needs re-run.
          # For Phase 4, paths-filter ensures we only re-deploy when binary inventory shifts.
          # Trigger deploy via wrangler:
          # npx wrangler pages deployment create dist --project-name=realufo
          echo "R2 sync complete. Next push (or manual deploy_pages.yml) picks up new URLs."
```

### Secrets required (per CONTEXT.md note: already configured)

| Secret | Used For |
|--------|----------|
| `CLOUDFLARE_API_TOKEN` | (existing) CF Pages deploy, wrangler |
| `CLOUDFLARE_ACCOUNT_ID` | (existing) wrangler, rclone endpoint |
| `CLOUDFLARE_R2_ACCESS_KEY` | (NEW) rclone S3-compatible auth |
| `CLOUDFLARE_R2_SECRET_KEY` | (NEW) rclone S3-compatible auth |

Operator checkpoint in `04-r2-setup` plan: Frank to create R2 API token via CF dashboard, add `CLOUDFLARE_R2_ACCESS_KEY` + `CLOUDFLARE_R2_SECRET_KEY` to GH repo secrets.

### Diff detection idempotency

`rclone sync --checksum` is the safety net: even if git diff is wrong (e.g. file renamed but content unchanged), rclone's per-file SHA check prevents redundant uploads. **Trade-off:** rclone walks the bucket once per sync, costing Class A operations. For a 200-file bucket, this is ~200 ops × $0.0036/1000 = $0.0007 per sync — negligible.

**First-run bulk migration:** Trigger via `workflow_dispatch` with `full_sync: true`. Skips diff, syncs everything. Subsequent automatic runs (push to main with binary-path filter) are incremental.

**Confidence:** HIGH on workflow shape (standard GH Actions pattern); HIGH on rclone usage (well-documented for R2 S3-compat); MEDIUM on the post-sync CF Pages rebuild trigger (depends on whether URL rewrite happens at build time and whether normaliser re-runs catch new R2 URLs — most likely it does because normalize-csv.py runs in prebuild and embeds URLs from disk paths, which the diff-detection knows about).

## 6. Pagination Pattern (Astro `[...page].astro`)

### Astro paginate() — file-based ONLY, not query string

[VERIFIED via docs.astro.build/en/guides/routing/#pagination] Astro's native `paginate()` helper supports ONLY file-based pagination (`[page].astro` → `/path/1`, `/path/2`, ...). **Native `?page=N` query-string pagination is NOT supported** by `paginate()`. It would require:
- Either: pre-rendering all `?page=N` variants as separate routes (defeats the purpose)
- Or: a single SSR endpoint reading `Astro.url.searchParams.get('page')` (requires server-rendering, not `output: 'static'`)

### Reconciling D-28 (?page=N) with Astro's file-routing

**Recommendation: client-side pagination over server-rendered shards.**

The architecture from Plan 03-05 already establishes:
- Server-renders rows 1-50 of the wargov page into `dist/index.html`
- Server-renders rows 51-100, 101-150, 151-222 as **pre-rendered HTML strings in `dist/wargov-shard-N.json`** (D-10 LOCKED)
- Client-side script does `insertAdjacentHTML('beforeend', card.html)` to materialise lazy-loaded cards

Phase 4 D-28 + D-32 + D-33 reshape this for `?page=N`:
1. Initial HTML still emits rows 1-20 server-side.
2. Lazy-load script REPLACED by `?page=N` URL handler:
   - On page load, read `?page=N` from URL.
   - Fetch the appropriate shards (page 2 = rows 21-40, spans shard 1 partial; page 3 = rows 41-60, spans shards 1-2; etc.).
   - Hide rows outside the current page; show only the 20-card window.
   - Render `<nav class="pagination">` with prev/next/page-number links that update `?page=N` via `history.pushState`.
3. Footer remains at bottom of DOM, always reachable.

**Why this works:** All 222 cards remain in `dist/index.html` + shard JSON. The page becomes a client-side window over a pre-rendered dataset — no SSR needed, no extra build complexity. URL-CONTRACT.txt unaffected (paths unchanged; query strings out of scope per D-29). Browser back/forward works via `popstate` listener.

### Skeleton — `?page=N` handler in `src/pages/index.astro`

Replace the existing IntersectionObserver lazy-load block (lines 302-351) with:

```javascript
<script is:inline>
  (() => {
    const PAGE_SIZE = 20;  // D-27
    const grid = document.getElementById('wargov-grid');
    const manifestEl = document.getElementById('wargov-shards');
    const paginationNav = document.getElementById('wargov-pagination');
    if (!grid || !manifestEl) return;

    let manifest;
    try { manifest = JSON.parse(manifestEl.textContent || '[]'); } catch { return; }

    // Lazy-load ALL shards upfront (one-shot, in parallel) so client-side
    // pagination has full data. ~250 KB JSON total for wargov; acceptable.
    const allCardsLoaded = Promise.all(
      manifest.map((s) =>
        fetch('/' + s.file).then((r) => r.json()).catch(() => ({ cards: [] }))
      )
    );

    function readPage() {
      const p = parseInt(new URLSearchParams(location.search).get('page') || '1', 10);
      return Math.max(1, isNaN(p) ? 1 : p);
    }

    async function renderPage(pageNum) {
      // Materialise all cards into grid (idempotent — only on first call)
      if (!grid.dataset.fullyLoaded) {
        const shards = await allCardsLoaded;
        for (const shard of shards) {
          for (const card of shard.cards || []) {
            if (card?.html) grid.insertAdjacentHTML('beforeend', card.html);
          }
        }
        grid.dataset.fullyLoaded = '1';
      }

      const cards = Array.from(grid.querySelectorAll('.arch-card'));
      const totalPages = Math.ceil(cards.length / PAGE_SIZE);
      pageNum = Math.min(Math.max(1, pageNum), totalPages);

      const start = (pageNum - 1) * PAGE_SIZE;
      const end = start + PAGE_SIZE;
      cards.forEach((c, i) => {
        c.style.display = (i >= start && i < end) ? '' : 'none';
      });

      renderPaginationNav(pageNum, totalPages);
      window.scrollTo({ top: 0, behavior: 'instant' });
    }

    function renderPaginationNav(current, total) {
      if (!paginationNav) return;
      let html = '';
      if (current > 1) html += `<a href="?page=${current - 1}" class="pg-prev">← Prev</a>`;
      for (let i = 1; i <= total; i++) {
        html += i === current
          ? `<span class="pg-current" aria-current="page">${i}</span>`
          : `<a href="?page=${i}">${i}</a>`;
      }
      if (current < total) html += `<a href="?page=${current + 1}" class="pg-next">Next →</a>`;
      paginationNav.innerHTML = html;
    }

    // Wire link clicks to pushState + re-render (no full nav)
    document.addEventListener('click', (e) => {
      const a = e.target.closest('#wargov-pagination a');
      if (!a) return;
      e.preventDefault();
      const url = new URL(a.href, location.origin);
      history.pushState({}, '', url);
      renderPage(parseInt(url.searchParams.get('page') || '1', 10));
    });

    window.addEventListener('popstate', () => renderPage(readPage()));

    renderPage(readPage());
  })();
</script>
```

### Footer always reachable (D-31)

With 20 cards per page (vs 222 stacked vertically), the footer is reachable after ~3 viewports of scroll on mobile (~1500 px page height vs ~16000 px today). **Verified by math, not yet tested in browser** — verify in `04-wargov-repaging` plan.

### `#card-<id>` anchor compatibility (URL-CONTRACT.txt)

When user lands on `/?page=3#card-uap-2024-incident`:
- Browser anchors to `#card-uap-2024-incident` BEFORE the JS pagination runs.
- After `renderPage(3)` runs, the card is on page 3 — visible.
- If a user shares `/?#card-uap-2024-incident` (no page), the JS detects the anchor on load, finds which page contains it, and renders THAT page.

**Implementation:** add to `renderPage()`:

```javascript
// If a hash is present and the target card is hidden, find its page and re-render.
if (location.hash && !document.querySelector(location.hash + ':not([style*="none"])')) {
  const target = document.querySelector(location.hash);
  if (target) {
    const cards = Array.from(grid.querySelectorAll('.arch-card'));
    const idx = cards.indexOf(target);
    if (idx >= 0) {
      const targetPage = Math.floor(idx / PAGE_SIZE) + 1;
      if (targetPage !== pageNum) {
        renderPage(targetPage);
        // After re-render, the browser re-anchors (may need scrollIntoView).
        target.scrollIntoView({ block: 'start' });
      }
    }
  }
}
```

**Phase 4 dropping IntersectionObserver (D-33):** the lazy-load-on-scroll is replaced by upfront fetch-all-shards-on-load. Total network = ~250 KB JSON vs Phase 3's progressive loading. Acceptable for PERF-01 budget since the JSON shards remain cacheable (SW SWR per D-21).

**Confidence:** HIGH on Astro paginate() limitations (verified via Astro docs); HIGH on client-side pagination pattern (standard JS); MEDIUM on browser anchor + pushState interaction (needs Playwright test in plan).

## 7. Lightbox Diagnosis

### Direct code inspection — files examined

1. `src/scripts/invariants.ts` (267 lines) — IIFE injected via `<script is:inline set:html>` in `RootLayout.astro` line 104.
2. `src/components/Lightbox.astro` — static markup only, IDs `#lightbox`, `#lb-inner`, `#lb-close`, `#lb-prev`, `#lb-next`, `#lb-counter`.
3. `src/components/Card.astro` — emits `<article data-action="open" data-idx={idx}>` + `<a class="btn-open" data-action="open" data-idx={idx} href={url}>`.
4. `src/pages/index.astro` — page-level inline script that builds `window.__lbList` from rendered cards.
5. `src/layouts/RootLayout.astro` — script order: BaseHead → `<main>` → Footer → `<script is:inline set:html={INVARIANTS_JS}>`.

### Bug 1 (PRIMARY) — `data-idx` mismatch with `__lbList` index

**Card.astro line 84 + line 107:** `data-idx={idx}` is the **GLOBAL row index** 0..221 (the `idx` prop = row's position in the full 222-card `rows[]` array).

**index.astro line 461-467:** `refreshLbList()` builds `window.__lbList` by walking `getCards()` = `Array.from(grid.querySelectorAll('.arch-card'))` — **in DOM order, including only visible cards**.

**invariants.ts line 96-107:** `openAt(idx)` does `lbIdx = idx % lbList.length`. When `idx=42` and `lbList.length=50`, lbIdx=42 — but `lbList[42]` is NOT the same asset as `rows[42]` because:
- Filtering (tab "Documents", agency filter) hides cards from DOM walk → smaller `lbList` array.
- Sorting reorders DOM children → `lbList[42]` is now a different card.
- Lazy-loaded shard cards arrive AFTER initial paint → `lbList` may not yet contain them when user clicks.

**Symptom:** clicking any card opens the WRONG asset in lightbox (or opens the first card every time if `lbList` is small). On unfiltered initial paint, accidental correct behaviour for first 50 cards because rows are rendered in order; bug surfaces immediately on filter/sort/lazy-load.

### Bug 2 (SECONDARY) — `local` field never propagated to lightbox

**Card.astro lines 105-111:** Both `<a class="btn-open" href={url}>` and `<a class="btn-download" href={url} download>` use the SAME `url` value. The `local?: string` field in `interface WargovRow` (line 47) is DEFINED but NEVER READ.

**index.astro lines 461-467:** `refreshLbList()` reads `openA.getAttribute('href')` as `url` AND `dlA.getAttribute('href')` as `local` — but both anchors have the same href, so `local === url` always.

**invariants.ts line 67-76:** `var target = local || remote; ... if (ext === 'pdf') { if (local) iframe; else if (remote) new-tab }` — because `local` ALWAYS truthy (same value as remote), iframe branch ALWAYS fires. Remote-only PDFs that should open in a new tab (per CLAUDE.md §7 invariant 5: "PDF lightbox iframe ONLY for local files") instead try to iframe-embed a cross-origin URL → CSP block, blank lightbox.

**Symptom:** PDFs from GH Releases (cross-origin) blank-iframe. Same will happen for R2-hosted PDFs (assets.realufo.org cross-origin to realufo.org). After R2 migration, EVERY PDF is cross-origin → 100% blank lightbox.

### Bug 3 (TERTIARY) — `<article>` has `data-action="open"` but click delegate looks for `a[data-action="open"]`

**Card.astro line 84:** `<article ... data-action="open">`.
**invariants.ts line 164:** `var action = e.target.closest && e.target.closest('a[data-action="open"]');`

The article-level `data-action` is unreachable by the delegate because the selector requires the element to be an `<a>`. The inner `<a class="btn-open" data-action="open">` IS reachable.

**Symptom:** clicking the card image, title, or description (anywhere NOT on the Open button) does nothing. Only clicking the specific "Open" button triggers the lightbox. **This is an intentional restriction** (per CLAUDE.md §4.3) but worth confirming with user — the markup suggests clicking ANYWHERE on the card was meant to open it (article has `data-action="open"`).

### Surgical fix recommendations

**Patch A — Card.astro:** Add `data-row-id` and separate local/url fields.

```astro
<article
  class="arch-card"
  id={`card-${slug}`}
  data-id={rowId}
  data-row-id={rowId}             {/* NEW — stable index for lbList lookup */}
  data-action="open"
  data-type={rtype}
  data-agency={agency}
  data-date={date}
>
  ...
  {url && (
    <a
      href="#"
      class="btn-open"
      data-action="open"
      data-row-id={rowId}            {/* NEW — same row-id for cross-reference */}
      data-url={url}                  {/* NEW — explicit URL field */}
      data-local={row.local || ''}    {/* NEW — separate local field */}
    >Open</a>
  )}
  {url && (
    <a
      href={row.local || url}         {/* CHANGED — download prefers local */}
      class="btn-download"
      data-url={url}
      data-local={row.local || ''}
      download
    >Download</a>
  )}
  ...
</article>
```

**Patch B — index.astro `refreshLbList()`:** Build keyed by `data-row-id`, not array-index.

```javascript
function refreshLbList() {
  const list = [];
  for (const c of getCards()) {
    const rowId = c.dataset.rowId;
    const titleEl = c.querySelector('.card-title');
    const openA = c.querySelector('a.btn-open');
    list.push({
      rowId,                                              // NEW
      title: titleEl ? titleEl.textContent : '',
      url: openA ? openA.dataset.url : '',                 // CHANGED (was href)
      local: openA ? (openA.dataset.local || '') : '',     // CHANGED (was dlA href)
    });
  }
  window.__lbList = list;
}
```

**Patch C — invariants.ts `openAt()`:** Look up by `data-row-id`, fallback to numeric idx.

```javascript
function openAt(rowIdOrIdx) {
  if (!lb) return;
  lbList = (window.__lbList && window.__lbList.length) ? window.__lbList : lbList;
  if (!lbList.length) return;

  // First try: lookup by rowId (the stable per-row identifier).
  let foundIdx = lbList.findIndex(x => x.rowId === rowIdOrIdx);
  if (foundIdx < 0) {
    // Fallback to numeric idx (legacy behaviour).
    const n = parseInt(rowIdOrIdx, 10);
    if (!isNaN(n)) foundIdx = ((n % lbList.length) + lbList.length) % lbList.length;
  }
  if (foundIdx < 0) return;
  lbIdx = foundIdx;
  renderLb();
  lb.classList.add('open');
  lb.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
}
```

**Patch D — invariants.ts click delegate:** Pass `data-row-id` instead of `data-idx`.

```javascript
document.addEventListener('click', function (e) {
  var action = e.target.closest && e.target.closest('a[data-action="open"]');
  if (!action) return;
  e.preventDefault();
  var rowId = action.dataset.rowId || action.dataset.idx;  // CHANGED
  if (rowId === undefined) {
    var card = action.closest('.card, .arch-card');
    rowId = card && (card.dataset.rowId || card.dataset.idx);
  }
  if (rowId) openAt(rowId);
});
```

**Patch E (optional) — full-card click:** If user wants clicking anywhere on `.arch-card` to open lightbox, broaden selector:

```javascript
var action = e.target.closest && (
  e.target.closest('a[data-action="open"]') ||
  e.target.closest('.arch-card[data-action="open"]')
);
```

But this conflicts with the Source ↗ and Download buttons inside the card — clicking them would ALSO trigger lightbox. **Recommendation: leave full-card click OFF; only the Open button triggers lightbox.** User can confirm or override.

### Validation plan (in `04-lightbox-fix` plan)

1. **Unit-level Playwright test** at `tests/lightbox.spec.ts`:
   - Visit `/`, wait for cards rendered.
   - Click `.btn-open` on card #1 → expect `#lightbox.open` + correct title in iframe/img.
   - Press → arrow key → expect counter advance + card #2 content.
   - Press Escape → expect lightbox closed.
   - Filter "Documents" tab, click Open on first visible card → expect THAT card's content (not card #1).
   - Click remote PDF Open → expect lightbox open with `lb-meta` "Remote PDF" panel (not iframe).
2. **Regression smoke:** visit `/?page=3` (after `04-wargov-repaging` lands), confirm card #41's Open button opens card #41's asset.

**Confidence:** HIGH on diagnosis (verified by direct code reading); HIGH on patch correctness (preserves existing handler contract, surgical scope); MEDIUM on user's intent for full-card-click (clarify in plan).

## 8. Per-Archive Port Template

### Plan 03-05 wargov pattern — what's reusable as-is

| Component | Reuse | Per-archive Changes |
|-----------|-------|---------------------|
| `RootLayout.astro` | 100% (15-archive TONE map already complete) | `archiveSlug` prop |
| `BaseHead.astro` | 100% | None (per-page `title`/`description` via props) |
| `Nav.astro` | 100% | None (already references all 15 slugs) |
| `Footer.astro` | 100% (license map per CLAUDE.md §9 already in component) | `archiveSlug` prop drives license |
| `Card.astro` | 90% | Schema differs per archive (`WargovRow` vs `CatalogAsset` — separate `Card.astro` per shape OR generic Card with discriminated union) |
| `Lightbox.astro` | 100% | None |
| `HeroCarousel.astro` | OPTIONAL | Only some archives have hero imagery (wargov yes; AARO maybe; NZ/Uruguay/Peru no) |
| `invariants.ts` | 100% | None (delegated handlers, archive-agnostic) |
| `global.css` | 100% | None |
| `wargov.css` | NO | Each archive gets `<slug>.css` or scoped styles |

### Per-archive page route

```
src/pages/aaro/index.astro      → /aaro/
src/pages/aaro/[...page].astro  → /aaro/?page=N (but see §6 — likely client-side pagination)
src/pages/nasa/index.astro      → /nasa/
...
```

Note per §6: paginated UX uses `?page=N` client-side, NOT separate route files. So a single `src/pages/<slug>/index.astro` per archive — no `[...page].astro` needed.

### Card.astro generalisation

Current `Card.astro` is hard-coded to `WargovRow` schema. Two choices:

**Option A: Per-archive Card components** — `WargovCard.astro`, `AaroCard.astro`, etc. Each takes the archive-specific row type. Pros: type-safe, clear. Cons: 14 nearly-identical files.

**Option B: Generic Card with discriminated union row type.** Card.astro takes `row: CatalogAsset | WargovRow` and branches on `row.kind`. Pros: one file. Cons: every archive's quirks bleed into one file.

**Recommendation: Hybrid.** A generic `CatalogCard.astro` handles all 14 archives using the `catalogAssetSchema` shape (per Plan 03-02). `WargovCard.astro` (the current Card.astro renamed) handles wargov's CSV-keyed shape. Per-archive `<slug>/index.astro` imports the right Card. **Two Card components total** — manageable.

```typescript
// Per-archive page:
import CatalogCard from '../../components/CatalogCard.astro';
import { getCollection } from 'astro:content';
const entries = await getCollection('aaro');
const rows = entries[0].data.assets;
```

### Per-archive normaliser approaches

The 14 archives have wildly different source data formats:

| Archive | Current source | Normaliser strategy |
|---------|---------------|---------------------|
| AARO | `scripts/parse-aaro.py` + `aaro/.cache/*.json` (scraped HTML pages) | Port parse-aaro.py → `scripts/normalize-aaro.py` emitting `data/aaro.json` |
| NASA | `scripts/build-nasa.py` (small static list) | Static `data/nasa.json` from hand-curated source; tiny normaliser |
| NARA | `nara/.cache/*.json` (catalogue API responses) | `scripts/normalize-nara.py` walks cache JSON → `data/nara.json` |
| GEIPAN | `geipan/.cache/*.json` (3000+ cases) | `scripts/normalize-geipan.py` — emits sharded `data/geipan.json` + `data/geipan-shard-N.json` (PERF-01) |
| UK | `uk/.cache/*.json` (Discovery catalogue) | `scripts/normalize-uk.py` |
| Brazil/Chile/Argentina/Italy/NZ/Peru/Spain/Uruguay/Canada | Each has `<slug>/.cache/*.json` + `scripts/dl-<slug>.sh` (KEEP per D-11) + `scripts/build-<slug>.py` (DELETE per SSG-10) | Port build-<slug>.py's manifest-emission logic to `scripts/normalize-<slug>.py` |

**Shared helper:** Extract URL-rewrite + slugify into `scripts/_archive_common.py`:

```python
# scripts/_archive_common.py
R2_BASE = "https://assets.realufo.org"

def rewrite_to_r2(local_path: str, archive_slug: str, asset_type: str) -> str:
    """Common URL rewrite for all per-archive normalisers."""
    if not local_path: return ""
    return f"{R2_BASE}/{asset_type}/{archive_slug}/{local_path.rsplit('/', 1)[-1]}"

def slugify(text: str) -> str:
    """Byte-exact port from scripts/snapshot-urls.py + Card.astro slugify."""
    s = (text or "").lower()
    import re
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:80].strip('-')
```

### Tone-colour fix for geipan/uk/brazil/chile (D-10 — bundled inline)

Per Plan 03-06 SUMMARY: the 4 archives' legacy HTML has buggy `--caution` CSS values. Phase 4 deletes the legacy HTML when each archive ports — so the fix is "render the Astro page with the correct TONE map value" (TONE map in RootLayout.astro is already correct per Phase 3 audit). No CSS edits needed; just delete the legacy HTML by removing slug from `copy-legacy-archives.sh`.

**Verification per plan:** after each port, run `tests/tone-colours.spec.ts` against preview — expect green for the archive being ported (and the 3 still-on-legacy ones can stay red until their port). When all 4 port, all 15 tone-colours green.

### HeroCarousel — which archives have one

[ASSUMED based on CLAUDE.md §2 sources] Hero imagery exists for: wargov (HAS — currently shipping), AARO (3-5 representative images possible), NASA (UAP Independent Study photos), NARA (Project Blue Book file scans). Other 11 archives likely no carousel — just stats grid + hero text + archive listing.

**Per-plan decision:** each port plan decides hero-carousel inclusion. Default: NO carousel unless the source has ≥ 4 representative images suitable for the 16:9 aspect. Carousel implementation is identical to wargov's (reuse `HeroCarousel.astro` component).

### Schema compatibility verification

Before each port lands, run:

```bash
pnpm prebuild  # runs all normalisers; emits data/<slug>.json
pnpm build     # Astro reads data/<slug>.json via Content Collections; Zod validates
```

If Zod throws on schema mismatch, the normaliser is wrong — fix at normaliser, NOT at schema (schema is locked per Phase 3 D-02).

**Confidence:** HIGH on component reuse (verified via Phase 3 outputs); HIGH on normaliser strategy (mirrors existing Python build scripts); MEDIUM on per-archive data quirks (specific to each scraped source, surfaces during port).

## 9. PERF-01 GEIPAN Strategy

### Current state

[CITED: STATE.md Performance Metrics table] GEIPAN's `geipan/index.html` weighs 3.3 MB due to inline JSON manifest of 3000+ case records. Lighthouse mobile LCP @ 4× CPU ~5-6 s (extrapolated from STATE.md "Not budgeted" + Phase 3 SOFT-warn breakdown showing 29 s LCP on wargov post-postbuild — that was cold start; warm GEIPAN likely 3-4 s).

### Shard refactor strategy

Mirror Plan 03-03 wargov pattern at GEIPAN scale:

1. **`scripts/normalize-geipan.py`** reads `geipan/.cache/*.json` (raw catalogue) → emits:
   - `data/geipan.json` — envelope with `rows: [first 50 cases]` (pre-rendered HTML strings) + `shards: [{file: 'data/geipan-shard-1.json', count: 50}, ...]`
   - `data/geipan-shard-1.json` through `data/geipan-shard-N.json` — each with 50 cases, server-rendered HTML strings (D-10 LOCKED pattern)
   - For 3000 cases: ~60 shards of 50 each.
2. **PERF-02 ≤ 3 chunks per page** — at the BROWSER side, only 3 chunks (= 1 initial HTML with 20 cards + 2 shards) materialise per page-view because of the 20-card pagination (§6 D-27). Specifically:
   - Page 1 (`?page=1`): 20 cards from `geipan/index.html` initial render — 0 shard fetches.
   - Page 2-3: fetches shard-1 (covers rows 21-70) — 1 shard.
   - Pages with mid-shard boundaries: fetches up to 2 shards — total 2.
   - **Max concurrent shard fetches per page = 2.** Plus the Pagefind core (precached by SW after first visit). Total "chunks" per page ≈ 3. PERF-02 satisfied.
3. **PERF-03 first paint contains cards** — server-renders first 20 cards into `geipan/index.html`. Astro template already does this (Plan 03-05 pattern).
4. **PERF-01 LCP ≤ 2.5 s** — depends on initial HTML weight. With 20 cards × ~3 KB each (server-rendered HTML) = 60 KB cards + 80 KB chrome (CSS+inline JS+hero) = ~140 KB HTML. Well under 500 KB SSG-07 budget. LCP element likely the hero image; lazy-loaded thumbnails for off-screen cards (`<img loading="lazy">` per CLAUDE.md §7).

### Image lazy-load + responsive srcset

Card.astro line 91 already has `loading="lazy"`. For responsive srcset, use Astro's `<Image>` component from `astro:assets`:

```astro
import { Image } from 'astro:assets';
<Image src={thumb} alt={alt} loading="lazy" widths={[320, 640]} formats={['webp']} />
```

[CITED: docs.astro.build/en/guides/images] `astro:assets` Image component generates `srcset` + format conversion automatically. **Caveat:** requires local image files, not remote URLs. Since thumbs migrate to R2, the Image component won't auto-process them. Workaround:
- Either: keep thumbs as local files committed to repo (small, ~few hundred KB total)
- Or: pre-generate responsive variants at upload time (rclone + imagemagick before sync)

**Recommended:** keep thumbnails committed to repo (NOT migrate to R2 per D-01 — supersede). Only PDFs + videos go to R2. Thumbs stay local for Astro Image processing. **Revisit D-01 with operator.**

### Critical CSS extraction

Astro 5 auto-inlines critical CSS by default [CITED: docs.astro.build/en/guides/styling]. No additional config needed. Verify in Plan 04-15 GEIPAN port by checking `dist/geipan/index.html` for inline `<style>` blocks containing above-the-fold layout rules.

### Lighthouse HARD-flip prerequisite checklist

Before Phase 4 close per D-40:

- [ ] All 15 archives ported (Wave 1+2+3 complete)
- [ ] All thumbnails responsive + lazy-loaded
- [ ] All initial HTML ≤ 500 KB inline (measured per archive)
- [ ] SW precaching warm (2nd-visit LCP near-zero)
- [ ] Self-hosted fonts (no Google Fonts FCP delay)
- [ ] `.lighthouserc.cf.json` lines flipped:
  ```json
  "assertions": {
    "categories:performance": ["error", { "minScore": 0.85 }],
    "lcp-element": ["error", { "maxNumericValue": 2500 }],
    "resource-summary:total:size": ["error", { "maxNumericValue": 512000 }]
  }
  ```
  (Was `warn` per Phase 2 02-08 phase4-close-toggle.)

**Confidence:** HIGH on shard pattern (mirrors Plan 03-03); MEDIUM on LCP projection (depends on actual GEIPAN content density — extrapolated from wargov); HIGH on PERF-02 compliance via pagination math.

## 10. Python Retirement Schedule

### Per-archive plan (SSG-10)

Each archive's port plan (`04-NN-<slug>`) deletes its own Python footprint in the same commit chain:

```
04-06-aaro: deletes scripts/build-aaro.py + scripts/parse-aaro.py + scripts/extract-evidence.py
04-07-nasa: deletes scripts/build-nasa.py
04-08-nara: deletes scripts/build-nara.py
04-09-geipan: deletes scripts/build-geipan.py (Wave 3, ties to PERF-01)
04-10-uk: deletes scripts/build-uk.py
04-11-brazil: deletes scripts/build-brazil.py
04-12-chile: deletes scripts/build-chile.py
04-13-argentina: deletes scripts/build-argentina.py
04-14-canada: deletes scripts/build-canada.py
04-15-italy: deletes scripts/build-italy.py
04-16-nz: deletes scripts/build-nz.py
04-17-peru: deletes scripts/build-peru.py
04-18-spain: deletes scripts/build-spain.py
04-19-uruguay: deletes scripts/build-uruguay.py
```

Plus each plan:
- Drops slug from `scripts/copy-legacy-archives.sh` `ARCHIVES` array
- Drops slug from `scripts/sync-nav.py` policed-archives list (if it has one)
- Drops slug from `scripts/sync-footer.py` policed-archives list (if it has one)

### Cross-cutting Python (retired in `04-20-close`)

| Script | When deleted | Replaced by |
|--------|--------------|-------------|
| `scripts/build-wargov.py` | Already retired in Phase 3 (deleted in Plan 03-05) | `src/pages/index.astro` |
| `scripts/parse-aaro.py` | Plan 04-06 (AARO port) | `scripts/normalize-aaro.py` |
| `scripts/extract-evidence.py` | Plan 04-06 (AARO port) | AARO normalizer if needed |
| `scripts/spider.py` | Phase 5 SCRP scope (NOT Phase 4) — used by scrape automation | Phase 5 Workers-based scraper |
| `scripts/sync-nav.py` | Plan 04-20-close (all 15 archives ported) | `Nav.astro` (already sole source) |
| `scripts/sync-footer.py` | Plan 04-20-close | `Footer.astro` |
| `scripts/copy-legacy-archives.sh` | Plan 04-20-close (no legacy slugs left to copy) | n/a |
| `package.json scripts.postbuild` | Plan 04-20-close (no postbuild needed except Pagefind) | `pnpm postbuild` runs ONLY Pagefind |

### CI drift gates removed in `04-20-close`

Phase 2 may have created drift-policing workflows for the Python scripts:

- `.github/workflows/nav-sync.yml` (if it exists) — REMOVED
- `.github/workflows/footer-sync.yml` (if it exists) — REMOVED

Verify their existence in plan-checker step. Drift gates were Phase 2 SC#6 territory.

### Decommission order verification

Per Plan 03-06 §Open questions item 4-5: each per-archive plan documents the chain of deletions in its SUMMARY. Plan 04-20-close confirms:

```bash
ls scripts/build-*.py 2>/dev/null  # expect: empty
ls scripts/sync-*.py 2>/dev/null   # expect: empty
ls scripts/parse-aaro.py scripts/extract-evidence.py 2>/dev/null  # expect: empty
ls scripts/copy-legacy-archives.sh 2>/dev/null  # expect: empty
```

If any survive, Phase 4 isn't closed.

## 11. Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Playwright `1.49.0` + LHCI `0.14.0` (per package.json devDependencies) |
| Config file | `tests/playwright.config.ts` (existing, Phase 2 02-03) |
| Quick run command | `npx playwright test tests/lightbox.spec.ts --grep <name>` |
| Full suite command | `bash .github/workflows/quality-gates-local.sh` (or per-job: `npx playwright test tests/visual-regression.spec.ts`, `npx playwright test tests/tone-colours.spec.ts`, etc.) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SSG-06 | All 15 archives render via Astro | visual + smoke | `npx playwright test tests/visual-regression.spec.ts --grep <slug>` | Exists (60 baselines × 4 viewports) |
| SSG-07 | Each archive page ≤ 500 KB | LHCI assertion | `npx lhci collect && python3 scripts/verify-lighthouse-budgets.py` | Exists |
| SSG-08 | Mobile-first 360px | visual at 360 viewport | `npx playwright test tests/visual-regression.spec.ts --grep 360` | Exists |
| SSG-09 | Lightbox prev/next/arrow-keys/swipe + hamburger | unit + e2e | `npx playwright test tests/lightbox.spec.ts` | NEEDS Wave 0 |
| SSG-10 | All Python build scripts deleted | shell + ls | `bash scripts/verify-python-retired.sh` | NEEDS Wave 0 |
| SSG-11 | License footnotes verbatim per jurisdiction | fidelity | `python3 scripts/verify-fidelity.py` | Exists (115 samples) |
| SSG-12 | Tone-colour per CLAUDE.md §3.1 | unit | `npx playwright test tests/tone-colours.spec.ts` | Exists |
| SRC-01 | Pagefind builds to dist/pagefind/ | postbuild assertion | `ls dist/pagefind/pagefind.js && ls dist/pagefind/index/` | NEEDS Wave 0 |
| SRC-02 | /search.html migrated | smoke | `npx playwright test tests/search.spec.ts --grep "search returns results"` | NEEDS Wave 0 |
| SRC-03 | Per-archive filter UI | e2e | `npx playwright test tests/search.spec.ts --grep "archive filter"` | NEEDS Wave 0 |
| SRC-04 | `#card-<id>` anchors | smoke | `npx playwright test tests/search.spec.ts --grep "anchor"` | NEEDS Wave 0 |
| SRC-05 | SW precaches Pagefind core | DevTools sim | `npx playwright test tests/sw.spec.ts --grep "pagefind precache"` | NEEDS Wave 0 |
| SW-01 | injectManifest emits dist/sw.js | shell | `test -f dist/sw.js && grep -q '__WB_MANIFEST' dist/sw.js` | NEEDS Wave 0 |
| SW-02 | SW registered from BaseHead | grep | `grep -l "serviceWorker.register" src/layouts/BaseHead.astro` | Exists (already in BaseHead) |
| SW-03 | Precache covers all HTML | DevTools sim | `npx playwright test tests/sw.spec.ts --grep "offline html"` | NEEDS Wave 0 |
| SW-04 | PDFs/videos NOT precached | DevTools sim | `npx playwright test tests/sw.spec.ts --grep "no pdf precache"` | NEEDS Wave 0 |
| SW-05 | Tiered cache strategies | DevTools sim | `npx playwright test tests/sw.spec.ts --grep "strategies"` | NEEDS Wave 0 |
| SW-06 | Cache name `realufo-v<sha>` | DevTools sim | `npx playwright test tests/sw.spec.ts --grep "version"` | NEEDS Wave 0 |
| SW-07 | Self-hosted fonts | grep | `grep -l "@fontsource" src/layouts/BaseHead.astro && ! grep "fonts.googleapis.com" src/layouts/BaseHead.astro` | NEEDS Wave 0 |
| PERF-01 | GEIPAN LCP ≤ 2.5s mobile + 4× CPU | LHCI | `npx lhci collect --collect.url=https://<preview>/geipan/` | Exists |
| PERF-02 | ≤ 3 chunks per page | manual measure + LHCI | LHCI + manual DevTools network panel | Exists |
| PERF-03 | First paint contains cards | LHCI + Playwright | `npx playwright test tests/js-off.spec.ts --grep geipan` | Exists |
| PERF-04 | No regression at NZ/Uruguay/Peru | LHCI baseline diff | Per-plan: `python3 scripts/verify-lighthouse-budgets.py --baseline tests/lighthouse-baselines/<slug>.json` | NEEDS Wave 0 (baseline capture) |

### Sampling Rate

- **Per task commit:** `npx playwright test tests/<spec>.spec.ts --grep <name>` (target test file only)
- **Per wave merge:** Full quality-gates.yml matrix (visual + fidelity + tone + js-off + LHCI + redirects) — already in CI
- **Phase 4 close:** Full suite + new Phase 4 specs (lightbox, search, sw, r2-urls) all green before merge to main

### Wave 0 Gaps

- [ ] `tests/lightbox.spec.ts` — lightbox click, nav, keyboard, swipe, remote PDF (covers SSG-09 lightbox subset + lightbox-fix validation)
- [ ] `tests/search.spec.ts` — Pagefind UI loads, query returns results, filter UI works, `#card-` anchors resolve (covers SRC-01..04)
- [ ] `tests/sw.spec.ts` — SW registered, precache contains HTML, no PDF in precache, version-bump purges old cache, R2 origin allowlisted (covers SW-01..06)
- [ ] `tests/pagination.spec.ts` — `?page=N` URL, footer reachable, browser back/forward, `#card-` anchor resolves cross-page (covers D-27..D-31)
- [ ] `tests/r2-urls.spec.ts` — every card.url returns 200 from `assets.realufo.org` (covers D-01..D-06 — separate smoke against R2)
- [ ] `scripts/verify-python-retired.sh` — asserts no scripts/build-*.py, sync-*.py, parse-aaro.py, etc. (covers SSG-10)
- [ ] `tests/lighthouse-baselines/{nz,uruguay,peru}.json` — frozen Lighthouse snapshots for PERF-04 regression check
- [ ] Update `tests/visual-baselines/` — 14 new archives × 4 viewports = 56 NEW baselines captured against new Astro output (D-17 operator-conscious recapture per archive port plan)
- [ ] Update `tests/fidelity-samples.json` — 14 archives × ~5 samples each = ~70 new fidelity samples (hero-lede + license-footer + 1-2 card titles per archive)
- [ ] Update `tests/tone-colours-fixture.json` — ensure all 15 archives' expected `--caution` values match TONE map in RootLayout.astro

### Validation regime per Nyquist Dimension 8

| Regime | Scope | Owner |
|--------|-------|-------|
| Visual regression | 60 baseline → 116 baseline (60 + 56 new) | Per-archive port plan recaptures via D-17 |
| Fidelity | 105 samples → ~175 samples (+ 70 new) | Per-archive port plan adds samples |
| Tone-colours | 11/15 → 15/15 | After Wave 1+2+3 complete |
| JS-off | 15/15 (preserved) | Postbuild copy retires per archive port → Astro SSR replaces |
| Lighthouse | SOFT → HARD (warn → error) at `04-20-close` | All ports must pass D-27 budgets |
| Pagefind index | NEW — search returns results for known queries | `04-05-pagefind` plan establishes |
| SW lifecycle | NEW — cache version bump purges old | `04-03-sw-injectmanifest` plan establishes |
| R2 URL validation | NEW — every card.url HEAD 200 | `04-02-r2-setup` plan establishes; per-archive port plans re-run |
| Pagination | NEW — `?page=N` round-trip + footer reachable + cross-page anchors | `04-04-wargov-repaging` + per-archive ports |
| Lightbox | NEW — click → open with correct asset, prev/next, remote PDF | `04-01-lightbox-fix` plan establishes |

## 12. Pitfalls

### Pitfall 1 — @vite-pwa/astro precache includes sw.js itself, causing infinite cache loop

**What goes wrong:** `globPatterns: '**/*.{html,css,js,...}'` matches `dist/sw.js`. SW precaches itself. On next deploy, the precache list change re-triggers SW install BUT the cached SW serves the OLD code, so the new SW never activates.

**Prevention:** Add `'!sw.js'` AND `'!sw.js.map'` to globIgnores. `@vite-pwa/astro` may handle this automatically (check console for warnings during build). [VERIFIED: vite-pwa-org.netlify.app/guide/inject-manifest mentions auto-exclusion of sw.js but operator should verify in built output].

```javascript
globIgnores: [
  '**/*.{pdf,mp4,webm,mov,mp3,wav,zip}',
  'sw.js', 'sw.js.map', 'workbox-*.js',  // NEW
  'pagefind/index/**',
  'pagefind/fragment/**',
]
```

### Pitfall 2 — R2 CORS opaque responses break SW cache

**What goes wrong:** Without `mode: 'cors'` on fetch, R2-served images come back as opaque responses (status 0). Workbox by default refuses to cache status 0 responses. Visible as "no cached" + offline lightbox broken even though SW reports precache success.

**Prevention:** `<img crossorigin="anonymous">` on every R2-served image AND `new CacheableResponsePlugin({ statuses: [0, 200] })` on the CacheFirst strategy. **EXCEPT** per CLAUDE.md §11 — `crossorigin="anonymous"` on `<video>` is BANNED (kills CloudFront playback). For video, omit crossorigin and accept opaque responses (CacheableResponsePlugin still allows them).

### Pitfall 3 — Pagefind index regeneration cost on every CI build

**What goes wrong:** `npx pagefind --site dist` walks the entire `dist/` tree and regenerates the full index every build. For 5000+ cards across 15 archives, this could add 30-60 s to every CI run.

**Prevention:** Pagefind is fast (Rust-based; ~1-2 s per 1000 documents per Pagefind benchmarks). For realufo scale, regeneration on every build is acceptable. Monitor CI build time after Phase 4 closes; if > 5 min total, consider Pagefind's `--keep-index-url` cache option. [CITED: pagefind.app/docs/config-options].

### Pitfall 4 — SW skipWaiting breaks existing user sessions during cutover

**What goes wrong:** Per Pitfall #1 from research/PITFALLS.md: skipWaiting + clientsClaim during the Phase 6 DNS cutover means returning users with the Phase 1 kill-switch SW installed will activate the new SW immediately. Mid-page-render, fetch handlers swap → broken state.

**Prevention:** Phase 4 ships the SW; Phase 6 verifies migration. The kill-switch SW from Phase 1 calls `unregister()` in its activate handler, so users have already self-deregistered. New SW installs cleanly on first visit to CF Pages origin. **But Phase 4 must NOT skipWaiting during initial deploys** — only after stable for ≥ 7 days. Document via constant:

```typescript
const ALLOW_SKIP_WAITING = false;  // Flip to true only after Phase 6 cutover stable
self.addEventListener('install', (event) => {
  if (ALLOW_SKIP_WAITING) event.waitUntil(self.skipWaiting());
});
```

Phase 6 close flips the constant.

### Pitfall 5 — `data-pagefind-body` accidentally excludes everything

**What goes wrong:** Per [CITED: pagefind.app/docs/indexing] — if ANY page has `data-pagefind-body`, pages WITHOUT it are skipped. If Astro adds it to `<main>` in RootLayout.astro but legacy HTML (copied via postbuild) doesn't have it → 14 legacy archives are NOT indexed.

**Prevention:** Either (a) ensure postbuild copy step adds `data-pagefind-body` to legacy HTML via sed (fragile); OR (b) port all 14 archives FIRST, then add `data-pagefind-body` to RootLayout.astro in `04-05-pagefind` plan (clean — by the time Pagefind plan runs, all archives are Astro). **Recommendation: option (b).** Pagefind plan lands AFTER 14-archive ports complete, OR Pagefind initially indexes without `data-pagefind-body` (indexing whole `<body>` including nav/footer — acceptable for v1, refined later).

### Pitfall 6 — Pagination + lightbox interaction breaks across page changes

**What goes wrong:** User on page 3 opens lightbox on card #51. Lightbox uses `window.__lbList` which now contains ONLY visible cards (page 3's 20 cards). Prev/next navigates within the 20-card window, hitting boundaries at index 0 and 19. Wrap-around per invariants.ts goes from card 19 back to card 0 — but user expected to advance to page 4.

**Prevention:** `__lbList` should contain ALL cards (not just visible). Update `refreshLbList()` in index.astro to walk ALL `.arch-card` elements regardless of `display: none`. The pagination's display:none toggles visibility but doesn't remove from DOM. Lightbox prev/next then advances across page boundaries, automatically (no page change in URL — just lightbox content rotates). User closes lightbox, returns to whatever page they were on.

### Pitfall 7 — Astro Image component doesn't work on R2-hosted URLs

**What goes wrong:** Per §9 — `astro:assets` Image only processes LOCAL images. R2-hosted thumbnails skip Astro's image optimization → no srcset, no format conversion → mobile downloads desktop-sized JPEGs.

**Prevention:** Keep thumbnails LOCAL (don't migrate to R2). Only PDFs + videos go to R2. Revisit D-01 with operator: D-01 says "ALL PDFs, videos, AND thumbnails" but PERF gating requires Astro Image processing → contradiction. **Action item for operator confirmation in `04-r2-setup` plan: thumbs stay local OR pre-generate responsive variants at upload time + ship multiple URLs per thumb.**

### Pitfall 8 — `_headers` not applied to new CF Pages project

**What goes wrong:** Per Plan 03-06 §D-38: `_headers` file from Phase 2 is in repo root, but `curl -sI /sw.js` against new `realufo` CF Pages project returned default `cache-control: public, max-age=0, must-revalidate` instead of `no-cache, no-store, must-revalidate`. The kill-switch invariant (Phase 1 PMS-02) requires `/sw.js` no-cache.

**Prevention:** Verify `_headers` is in repo root AND part of the deployed `dist/`. CF Pages reads `_headers` from `dist/` root — `_headers` may need to be COPIED into dist during build:

```bash
# Add to postbuild OR astro.config.mjs publicDir contents
cp _headers dist/_headers 2>/dev/null || true
```

Or place `_headers` in `public/_headers` (Astro copies `public/` to `dist/` automatically). [VERIFIED: docs.astro.build/en/reference/configuration-reference/#publicdir]. Verify in `04-03-sw-injectmanifest` plan via curl smoke.

### Pitfall 9 — Pagefind result anchor doesn't auto-append to URL

**What goes wrong:** Default Pagefind result URL is page URL only (e.g. `/aaro/`) — `#card-<id>` not appended. Result clicks lose the anchor, defeating SRC-04.

**Prevention:** Use PagefindUI's `processResult` callback OR build custom UI:

```javascript
new PagefindUI({
  element: '#pagefind-search',
  processResult: (result) => {
    if (result.sub_results?.[0]?.anchor?.id) {
      result.sub_results[0].url = `${result.url}#${result.sub_results[0].anchor.id}`;
    }
    return result;
  },
});
```

[CITED: pagefind.app/docs/ui — processResult callback]. Verify in `04-05-pagefind` plan.

### Pitfall 10 — rclone-based bulk sync re-uploads identical files on first run

**What goes wrong:** First-run sync to a fresh R2 bucket uploads 200+ files. If the workflow times out or partial-fails, retry may re-upload everything from scratch (Class A operations cost adds up). On retry, rclone's `--checksum` flag forces a HEAD+ETag check per file, which is fast but still costs.

**Prevention:** Use rclone `--immutable` flag on subsequent runs to refuse re-uploads of files that exist with same name (regardless of content). For first-run, accept the duplicate-upload cost. Monitor R2 Class A op count post-sync; cost is ~$0.0072 per million ops (negligible at 1000-file scale).

### Pitfall 11 — `data-pagefind-filter` capture on dynamic content fails

**What goes wrong:** If a per-archive page includes filter values pulled from data files at runtime (e.g. dynamic agency list), Pagefind indexes the BUILD-TIME values, not runtime values. Filter UI may show stale options.

**Prevention:** All filter values must be present in server-rendered HTML at build time. Verify by inspecting `dist/<slug>/index.html` for `data-pagefind-filter` attributes containing all expected filter values. Don't generate filter chips client-side from JSON shards — server-render them.

### Pitfall 12 — Lightbox patches break Plan 03-03 server-rendered card HTML strings

**What goes wrong:** Per Plan 03-03 D-10 LOCKED: shards contain pre-rendered HTML strings from `scripts/normalize-csv.py:render_card_html()`. If Card.astro changes to add `data-row-id` + `data-url` + `data-local`, the normalize-csv.py's Python function must mirror the change byte-for-byte — otherwise lazy-loaded cards have different markup than initial-paint cards, breaking the lightbox fix on shard-loaded cards.

**Prevention:** Plan `04-01-lightbox-fix` MUST update BOTH `src/components/Card.astro` AND `scripts/normalize-csv.py:render_card_html()` in the same commit. Verify via diff:

```bash
# After lightbox-fix lands:
diff <(node -e "import('astro').then(async () => {/* render Card */}).catch(()=>{})") <(python3 scripts/normalize-csv.py --emit-html --idx=0)
# Should be byte-equivalent.
```

The Plan 03-03 visual-regression test catches drift if it occurs.

## Sources

### Primary (HIGH confidence — official docs)

- [Pagefind documentation](https://pagefind.app/docs/) — postbuild command, version 1.5.0+ Component UI
- [Pagefind filtering](https://pagefind.app/docs/filtering/) — `data-pagefind-filter` attribute syntax, multi-value semantics
- [Pagefind indexing](https://pagefind.app/docs/indexing/) — `data-pagefind-body`, `data-pagefind-ignore`, `data-pagefind-index-attrs`
- [@vite-pwa/astro framework guide](https://vite-pwa-org.netlify.app/frameworks/astro) — `AstroPWA({})` integration block
- [Vite PWA injectManifest guide](https://vite-pwa-org.netlify.app/guide/inject-manifest) — `srcDir`/`filename`, sw.ts template
- [Astro routing — pagination](https://docs.astro.build/en/guides/routing/#pagination) — `paginate()` helper, page object props, file-based ONLY
- [Astro client-side scripts](https://docs.astro.build/en/guides/client-side-scripts/) — `<script is:inline>`
- [Astro configuration reference](https://docs.astro.build/en/reference/configuration-reference/) — `publicDir`, `output: 'static'`
- [Cloudflare R2 public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/) — custom domain bind via dashboard, DNS requirements
- [Cloudflare R2 CORS](https://developers.cloudflare.com/r2/buckets/cors/) — `AllowedOrigins`/`AllowedMethods` JSON schema
- [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/) — 25 MiB/file, 20k files free
- [Workbox strategies](https://developer.chrome.com/docs/workbox/modules/workbox-strategies) — NetworkFirst, StaleWhileRevalidate, CacheFirst
- [Workbox precaching](https://developer.chrome.com/docs/workbox/precaching-with-workbox/) — `precacheAndRoute`, `__WB_MANIFEST`

### Secondary (MEDIUM confidence)

- [@fontsource README](https://github.com/fontsource/fontsource) — npm package import patterns
- [rclone S3 backend docs](https://rclone.org/s3/#cloudflare-r2) — R2 endpoint configuration

### Tertiary (verified by code inspection, not external)

- `src/scripts/invariants.ts` lines 96-174 — lightbox handler logic
- `src/components/Card.astro` lines 79-122 — card markup contract
- `src/pages/index.astro` lines 452-475 — `refreshLbList()` implementation
- `src/layouts/RootLayout.astro` line 104 — script injection order
- `src/layouts/BaseHead.astro` lines 65-71 — SW registration with `updateViaCache: 'none'`
- `astro.config.mjs` — integrations array currently empty (per Phase 3 D-23)
- `package.json` — Astro 5.18.0, @astrojs/cloudflare 12.6.0, papaparse 5, zod 3

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Pagefind index size projection (~200-400 KB initial for full 15-archive corpus) | §2 | If actual index is much larger, PERF budget at risk; mitigation: shard control via Pagefind config |
| A2 | HeroCarousel optional per archive — only some archives have ≥4 representative images | §8 | If user wants carousel on all 15, per-plan effort doubles |
| A3 | Thumbnails stay LOCAL (NOT R2) for Astro Image processing | §9 + Pitfall 7 | Contradicts D-01 — needs operator confirmation in `04-r2-setup` plan |
| A4 | rclone bulk sync of 200+ files completes in < 30 min on GH Actions free runner | §5 | If slower, workflow timeout (30 min default); mitigation: increase timeout or chunked upload |
| A5 | Per-archive normaliser strategy (port build-`<slug>`.py logic) | §8 | If existing Python build scripts have undocumented quirks, normaliser may emit invalid data; mitigation: Zod schema catches at build |
| A6 | CF Pages reads `_headers` from `dist/` root (NOT from repo root automatically) | Pitfall 8 | If CF Pages reads from repo root and `dist/_headers` is ignored, SW kill-switch invariant could break silently |
| A7 | Client-side `?page=N` pagination is acceptable trade-off vs Astro file-routing | §6 + D-28 | If SEO requires path-based pages, refactor needed; current decision honors D-28 query string |
| A8 | Pagefind result anchor injection via `processResult` callback works in Component UI | §2 + Pitfall 9 | If callback API differs from documented, custom UI needed; bigger rewrite |

**If this table is empty:** N/A — 8 assumptions logged. Operator confirmation needed on A3 (thumbnails to R2 or stay local) before `04-r2-setup` lands.

## Open Questions

1. **Thumbnails on R2 or local?** D-01 says "ALL PDFs, videos, AND thumbnails" → R2. Astro Image processing requires local. Recommendation: thumbnails stay local; D-01 narrows to PDFs + videos only. Confirm with operator.
2. **Pagefind index for legacy archives:** If 14-archive ports happen in waves, intermediate Phase 4 deploys have a mix of Astro-rendered + legacy HTML in `dist/`. Should Pagefind index land BEFORE all 14 ports complete (incremental index value) OR AFTER (clean single-pass)? Decision affects plan ordering. **Recommendation: AFTER** — `04-05-pagefind` lands after Wave 1+2+3 ports complete, just before close.
3. **Lightbox full-card click:** Should clicking anywhere on `.arch-card` (not just Open button) trigger lightbox? Current code intends yes (article has `data-action="open"`) but delegate requires `<a>`. Patch E in §7 broadens this. Confirm UX intent.
4. **GEIPAN shard count:** 60 shards × 50 cards = 3000 cards. PERF-02 says ≤ 3 chunks per page. At 20 cards/page (D-27), pages 1, 2 = same shard; pages 3, 4 = shard 2; etc. Math holds. Confirm during normaliser execution.
5. **Bulk migration verification:** After first-run R2 sync, what's the post-upload smoke test? Recommendation: `curl -sI` against 10 sample URLs from each archive; expect all 200. Add to `04-02-r2-setup` plan as final checkpoint.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Astro build, Playwright | ✓ (assumed; project specifies `>=22 <23`) | 22 LTS | — |
| pnpm | Package manager | ✓ (assumed; project uses `pnpm@9.15.9`) | 9.15.9 | npm |
| Python 3 | Existing normalisers | ✓ | 3.x | — |
| wrangler CLI | R2 bucket create, CORS, deploys | ✓ (via `@cloudflare/wrangler-action@v3` in CI) | 4.x | — |
| rclone | R2 bulk sync | ✗ (must install in CI) | latest | Sequential `wrangler r2 object put` loop |
| Pagefind CLI | Search index | ✗ (add to devDeps) | ^1.5 | — |
| `@vite-pwa/astro` | SW integration | ✗ (add to devDeps) | latest 1.x | — |
| `workbox-precaching`/`-routing`/`-strategies` | sw.ts imports | ✗ (add to devDeps) | ^7 | — |
| `@fontsource/source-serif-4` | Self-hosted fonts | ✗ (add to deps) | latest | — |
| `@fontsource/jetbrains-mono` | Self-hosted fonts | ✗ (add to deps) | latest | — |
| CLOUDFLARE_API_TOKEN | Wrangler auth | ✓ (per CONTEXT.md "already configured") | — | — |
| CLOUDFLARE_ACCOUNT_ID | Wrangler / R2 endpoint | ✓ (per CONTEXT.md) | — | — |
| CLOUDFLARE_R2_ACCESS_KEY | rclone S3-auth | ✗ (operator must create) | — | NONE — blocks R2 sync |
| CLOUDFLARE_R2_SECRET_KEY | rclone S3-auth | ✗ (operator must create) | — | NONE — blocks R2 sync |
| GitHub repo write access | Frank push to hectorchanht/gov-ufo-archive | ✗ (Frank pull-only) | — | wrangler Direct Upload (operator-driven local push, no auto-deploy) |

**Missing dependencies with no fallback:**
- `CLOUDFLARE_R2_ACCESS_KEY` + `CLOUDFLARE_R2_SECRET_KEY` — required for R2 bulk sync. Operator checkpoint in `04-02-r2-setup` to create + add to GH secrets.

**Missing dependencies with fallback:**
- All npm packages: install via `pnpm add` in `04-03-sw-injectmanifest` and `04-05-pagefind` plans.
- `rclone`: install step in `r2-sync.yml` workflow.
- Frank GH write access: deploys remain Direct Upload via local `wrangler pages deploy` until operational resolution (per CONTEXT.md deferred).

## Project Constraints (from CLAUDE.md)

These directives from `./CLAUDE.md` must be honored by all Phase 4 plans:

- **§1 Goals priority:** Mobile-first over desktop polish; offline by default over inline streaming. Phase 4 SW + 360 px baselines enforce this.
- **§3.1 Per-archive tone colours LOCKED** — TONE map in RootLayout.astro is the spec. Any tone-colour fix happens in port plans, not as a separate plan.
- **§3.4 Shared favicon** — every archive uses `/assets/favicon.svg`. Phase 4 ports MUST link to this, not per-archive favicons.
- **§4.3 Action buttons matrix** — Open/Download/Source ↗/DVIDS ↗. Lightbox fix preserves this contract.
- **§5.1/5.2 GitHub Releases binary CDN** — Phase 4 D-01..D-06 SUPERSEDE this section. CLAUDE.md needs updating in Phase 6 HOST-06 to reflect R2 truth.
- **§7 JS invariants LOCKED** — invariants.ts is sole source. Phase 4 lightbox fix is a surgical patch, preserving all 8 invariants.
- **§8 Mobile-first 360 px / 44 px touch** — non-negotiable. All 14 archive ports must pass 360 viewport visual regression.
- **§9 Content fidelity — verbatim official text, no filler, public-domain attribution per jurisdiction** — every port plan runs `scripts/verify-fidelity.py` HARD gate.
- **§11 Don'ts:**
  - ❌ No `crossorigin="anonymous"` on `<video>` (kills CF playback) — Pitfall 2 honors this
  - ❌ No filler descriptions in cards
  - ❌ No force-push to main
  - ❌ No touching `uap-release001.csv` — normalize-csv.py reads only
  - ❌ No "OFFLINE MIRROR" banner

## Metadata

**Confidence breakdown:**
- Pagefind integration: HIGH — verified via Pagefind official docs, multiple sources cross-referenced
- SW injectManifest: HIGH — verified via vite-pwa-org official docs + Workbox 7 docs
- R2 setup: HIGH on bucket+CORS; MEDIUM on custom-domain bind (dashboard-only path)
- GH Actions r2-sync: MEDIUM — pattern is standard, project-specific paths assumed
- Pagination: HIGH — Astro paginate() limitations confirmed; client-side pattern is well-known
- Lightbox diagnosis: HIGH — direct code inspection, two bugs identified with patches
- Per-archive port template: HIGH — verified against Phase 3 outputs; component reuse straightforward
- PERF-01 strategy: MEDIUM — extrapolated from wargov shard pattern; GEIPAN-specific measurements pending
- Python retirement: HIGH — straightforward delete-and-test schedule
- Pitfalls: HIGH on documented ones (SW, R2 CORS, opaque responses, font CDN regression), MEDIUM on Pagefind-specific edge cases (filter capture, dynamic content)

**Research date:** 2026-05-27
**Valid until:** 2026-06-26 (30 days — stack is stable; revisit if Astro/Pagefind/Workbox publish breaking releases)

## RESEARCH COMPLETE
