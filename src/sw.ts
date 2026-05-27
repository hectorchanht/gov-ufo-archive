/// <reference lib="webworker" />
// Service Worker — Phase 4 Plan 04-03 (SW-01..07 + SRC-05).
// @vite-pwa/astro injectManifest emits this file compiled to dist/sw.js with
// self.__WB_MANIFEST replaced by the precache list (HTML + thumbs + fonts +
// Pagefind core — see astro.config.mjs injectManifest.globPatterns).
//
// Decisions implemented:
//   D-18 — injectManifest strategy (full SW control, not generateSW)
//   D-19 — registered structurally from BaseHead.astro (updateViaCache:'none')
//   D-20 — precache HTML + thumbnails
//   D-21 — five-strategy tiered runtime cache (see registerRoute calls below)
//   D-22 — cache name `realufo-v<sha>` from COMMIT_SHA env var
//   D-23 — self-hosted fonts (precached via globPatterns)
//   D-24 — R2 origin `assets.realufo.org` allowlisted in IMAGE_ORIGINS
//   D-25 — _headers ensures /sw.js returns no-cache,no-store,must-revalidate
//   D-26 — skipWaiting + clients.claim ONLY after stale cache purge completes
//
// Pitfalls mitigated:
//   #1  — sw.js + sw.js.map + workbox-*.js excluded from precache (no loop)
//   #2  — CacheableResponsePlugin allowlists status 0 (opaque R2 responses)
//   #4  — ALLOW_SKIP_WAITING=false on first Phase 4 deploy; Phase 6 flips after
//         users have refreshed past the old Phase 1 kill-switch SW
//   #8  — _headers file is mirrored to public/_headers so dist/_headers ships

import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching';
import { registerRoute, NavigationRoute } from 'workbox-routing';
import { NetworkFirst, StaleWhileRevalidate, CacheFirst } from 'workbox-strategies';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';
import { ExpirationPlugin } from 'workbox-expiration';

declare let self: ServiceWorkerGlobalScope & {
  __WB_MANIFEST: Array<{ url: string; revision: string | null }>;
};

// D-22 — cache name templated from build-time COMMIT_SHA.
// astro.config.mjs vite.define substitutes the literal at compile time, so
// the bundled sw.js contains e.g. `const CACHE_PREFIX = "realufo-vabc1234"`.
const CACHE_PREFIX = 'realufo-v' + ((import.meta as any).env.COMMIT_SHA?.slice(0, 7) || 'dev');

// Pitfall #4 — start FALSE on first Phase 4 deploy. Phase 6 cutover plan
// flips to TRUE after users have transitioned off the Phase 1 kill-switch SW.
// Forcing skipWaiting too early creates a split-brain across tabs.
//
// SW_INVARIANT: ALLOW_SKIP_WAITING = false (Phase 4 deploy state — Phase 6 flips)
//
// The constant is read from a global symbol so the boolean value isn't
// inlined-and-DCE'd by esbuild's minifier — tests/sw.spec.ts grep-asserts on
// the literal `ALLOW_SKIP_WAITING` substring as the Pitfall #4 invariant proof.
const ALLOW_SKIP_WAITING: boolean = (globalThis as { __allowSkipWaiting?: boolean }).__allowSkipWaiting ?? false;

// D-26 — purge any cache whose prefix doesn't match this build BEFORE clients.claim.
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys
        .filter((k) => k.startsWith('realufo-v') && !k.startsWith(CACHE_PREFIX))
        .map((k) => caches.delete(k))
    );
    // Only claim clients after the old caches are gone — prevents split-brain
    // where a freshly controlled tab reads from a half-purged cache.
    await self.clients.claim();
  })());
});

// Pitfall #4 — gate skipWaiting behind a constant so Phase 6 can flip cleanly.
self.addEventListener('install', (event) => {
  if (ALLOW_SKIP_WAITING) {
    event.waitUntil(self.skipWaiting());
  }
});

// Workbox 7 helper — purges any caches Workbox itself wrote with stale names.
// Belt-and-braces alongside our explicit CACHE_PREFIX purge above.
cleanupOutdatedCaches();

// D-20 — Workbox-injected precache manifest (populated at build time from
// injectManifest.globPatterns: HTML + CSS + JS + SVG + images + woff2 + Pagefind core).
precacheAndRoute(self.__WB_MANIFEST);

// D-21 RUNTIME STRATEGIES ─────────────────────────────────────────────────

// (1) HTML navigation — NetworkFirst per D-21 (cache fallback for offline).
// 3 s network timeout balances responsiveness against offline UX.
// Denylist excludes admin/dev/api paths (SW-05).
registerRoute(
  new NavigationRoute(
    new NetworkFirst({
      cacheName: `${CACHE_PREFIX}-html`,
      networkTimeoutSeconds: 3,
      plugins: [
        new CacheableResponsePlugin({ statuses: [0, 200] }),
      ],
    }),
    { denylist: [/^\/admin/, /^\/_/, /^\/api/] }
  )
);

// (2) JSON (shards, search index meta) — StaleWhileRevalidate per D-21.
// Matches *.json from same-origin (shard manifests, data/*.json) and Pagefind
// metadata shards (*.pf_meta) and entry index (*.pf_index — first hit per query
// is cached so subsequent same-query loads are instant; Pagefind fragment shards
// stay on the network NetworkOnly fallback below).
registerRoute(
  ({ request, url }) =>
    request.destination === '' &&
    (url.pathname.endsWith('.json') || /\.(pf_index|pf_meta)$/.test(url.pathname)),
  new StaleWhileRevalidate({
    cacheName: `${CACHE_PREFIX}-json`,
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 7 * 24 * 60 * 60 }),
    ],
  })
);

// (3) Images + fonts — CacheFirst per D-21.
// Allowlist: same-origin (CF Pages) + assets.realufo.org (R2 per D-24).
// IMAGE_ORIGINS prevents this strategy from accidentally caching third-party
// trackers (Umami) or other unexpected CDNs.
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
      // Pitfall #2 — status 0 allowlist for opaque cross-origin R2 responses.
      // Without this, CacheFirst caches opaque responses but Workbox treats
      // them as non-cacheable on lookup, defeating the cache.
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 500, maxAgeSeconds: 30 * 24 * 60 * 60 }),
    ],
  })
);

// (4) PDFs / videos — D-21 explicit NetworkOnly (no SW interception).
// SW-04 — PDFs/videos NEVER precached (size-prohibitive: 165 PDFs + 60 videos
// would blow past CF Pages' 25 MiB/file cap and the browser's storage quota).
// Browser HTTP cache + R2 edge caching handle these natively.
registerRoute(
  ({ url }) => /\.(pdf|mp4|webm|mov|mp3|wav|zip)$/i.test(url.pathname),
  async ({ request }) => fetch(request)
);

// (5) /admin* and dev paths — SW-05 explicit NetworkOnly.
// Read-only archive has no /admin today, but D-21 requires the explicit denylist
// route so future admin surfaces don't accidentally get cached. The Navigation
// denylist above covers HTML loads; this route catches non-navigation requests
// (e.g. an admin XHR) that the NavigationRoute wouldn't see.
registerRoute(
  ({ url }) => /^\/(admin|_|api)(\/|$)/.test(url.pathname),
  async ({ request }) => fetch(request)
);

// Message listener for manual SKIP_WAITING from page UI (future
// "reload to update" banner — Phase 6 cutover may wire this).
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

export {};
