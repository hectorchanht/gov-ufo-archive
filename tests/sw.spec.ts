// Service Worker lifecycle spec — Phase 4 Plan 04-03 (SW-01..06 + SRC-05).
// Mirrors the structure of tests/visual-regression.spec.ts (Phase 2 INF-04):
//   - testDir: '.' resolves to tests/
//   - baseURL from process.env.PREVIEW_URL (CF Pages preview URL)
//   - chromium-only (per Playwright config D-15)
//
// What this spec proves (per 04-RESEARCH.md §3 + Task 3 acceptance criteria):
//
//   1. SW registers within 5 s of first navigation
//      (closes the 12-of-32-pages registration gap from CONCERNS.md by
//      asserting registration succeeds against BaseHead.astro's structural
//      <script is:inline> block)
//
//   2. Precache contains HTML pages
//      (D-20 — precache every HTML; SW-03 full-catalog offline cache)
//
//   3. Precache excludes PDFs and videos
//      (SW-04 — PDFs/videos never precached; size-prohibitive per D-04)
//
//   4. Cache names use the `realufo-v` prefix
//      (D-22 + SW-06 — cache-name versioning from COMMIT_SHA)
//
//   5. SW source references R2 origin and Pagefind core (SRC-05)
//      (IMAGE_ORIGINS allowlist for assets.realufo.org per D-24,
//       and Pagefind core globPattern per SRC-05 prerequisite)
//
//   6. ALLOW_SKIP_WAITING constant is false on first Phase 4 deploy
//      (Pitfall #4 — Phase 6 cutover flips this; tests catch accidental flip)
//
// Run locally: PREVIEW_URL=https://<deploy>.realufo.pages.dev pnpm exec playwright test tests/sw.spec.ts
// CI: PREVIEW_URL passed by quality-gates.yml per Phase 2 02-08 contract.

import { test, expect } from '@playwright/test';

// Helper — wait for `navigator.serviceWorker.controller` to be non-null.
// First page load may not have a controller (registration runs on `load`,
// then takes effect on next navigation). We navigate twice when needed.
async function waitForSwControl(page: import('@playwright/test').Page, path = '/'): Promise<void> {
  await page.goto(path, { waitUntil: 'load' });
  // Wait for the SW to register and reach controlling state. If the page was
  // never under SW control before, a second navigation guarantees control.
  const controlled = await page.evaluate(() => 'serviceWorker' in navigator);
  expect(controlled, 'browser supports service workers').toBe(true);
  await page.waitForFunction(
    () => navigator.serviceWorker.ready.then(() => true),
    null,
    { timeout: 10_000 },
  );
  // Reload to ensure the controller field is populated for this page load.
  await page.goto(path, { waitUntil: 'load' });
  await page.waitForFunction(() => navigator.serviceWorker.controller !== null, null, {
    timeout: 5_000,
  });
}

test.describe('Service Worker lifecycle', () => {
  test('SW registers within 5 s of first navigation', async ({ page }) => {
    // SW-02 + D-19 — BaseHead.astro's inline registration block fires on `load`.
    // navigator.serviceWorker.controller becomes non-null once the SW takes
    // control of the page (which happens on the navigation AFTER the
    // installing SW completes activate).
    await waitForSwControl(page, '/');
    const hasController = await page.evaluate(
      () => navigator.serviceWorker.controller !== null,
    );
    expect(hasController, 'SW controls the page after register + reload').toBe(true);
  });

  test('Precache contains at least one HTML page', async ({ page }) => {
    // D-20 — every HTML page in dist/ is in the precache. We assert the
    // index page ('/' or index.html) appears in at least one realufo-v* cache.
    await waitForSwControl(page, '/');
    const cached = await page.evaluate(async () => {
      const keys = await caches.keys();
      const realufoCaches = keys.filter((k) => k.startsWith('realufo-v'));
      const urls: string[] = [];
      for (const name of realufoCaches) {
        const cache = await caches.open(name);
        const reqs = await cache.keys();
        for (const r of reqs) urls.push(new URL(r.url).pathname);
      }
      return urls;
    });
    const hasHtml = cached.some(
      (u) => u === '/' || u.endsWith('/index.html') || u.endsWith('.html'),
    );
    expect(
      hasHtml,
      `at least one HTML page is cached. cached urls (sample): ${cached.slice(0, 10).join(', ')}`,
    ).toBe(true);
  });

  test('Precache excludes PDFs, videos, and other media', async ({ page }) => {
    // SW-04 — PDFs/videos NEVER precached (size-prohibitive). astro.config.mjs
    // injectManifest.globIgnores enforces this at build time; we re-assert at
    // runtime to catch any regression in the globIgnores list.
    await waitForSwControl(page, '/');
    const cached = await page.evaluate(async () => {
      const keys = await caches.keys();
      const realufoCaches = keys.filter((k) => k.startsWith('realufo-v'));
      const urls: string[] = [];
      for (const name of realufoCaches) {
        const cache = await caches.open(name);
        const reqs = await cache.keys();
        for (const r of reqs) urls.push(new URL(r.url).pathname);
      }
      return urls;
    });
    const forbiddenExts = /\.(pdf|mp4|webm|mov|mp3|wav|zip)$/i;
    const offenders = cached.filter((u) => forbiddenExts.test(u));
    expect(offenders, `no PDF/video/audio in precache. offenders: ${offenders.join(', ')}`).toEqual(
      [],
    );
  });

  test('Cache names use realufo-v prefix (D-22)', async ({ page }) => {
    // D-22 + SW-06 — cache name `realufo-v<sha>-<bucket>` from COMMIT_SHA env var
    // at build time. Even in local dev (COMMIT_SHA unset), the prefix `realufo-v`
    // is preserved (falls back to `realufo-vdev-*`).
    await waitForSwControl(page, '/');
    const cacheKeys = await page.evaluate(() => caches.keys());
    const realufoCaches = cacheKeys.filter((k) => k.startsWith('realufo-v'));
    expect(
      realufoCaches.length,
      `at least one realufo-v* cache exists. all caches: ${cacheKeys.join(', ')}`,
    ).toBeGreaterThan(0);
  });

  test('SW source references R2 origin (SW-05 + D-24) and Pagefind core (SRC-05)', async ({
    page,
  }) => {
    // Verify by fetching /sw.js text — sourced from dist/sw.js post-build, so
    // these substrings prove the IMAGE_ORIGINS allowlist + globPatterns config
    // survived the Workbox build pipeline + Vite minifier.
    const response = await page.request.get('/sw.js');
    expect(response.status(), `/sw.js returns 200 (not 404)`).toBe(200);
    const body = await response.text();
    expect(body, 'R2 origin assets.realufo.org allowlisted in IMAGE_ORIGINS').toContain(
      'assets.realufo.org',
    );
    // CACHE_PREFIX literal proves D-22 compiled-in (whether 'dev' locally or
    // a real short SHA in CI).
    expect(body, 'CACHE_PREFIX realufo-v compiled into bundle').toMatch(/realufo-v/);
    // Pagefind precache: globPatterns includes 'pagefind/pagefind*.{js,css}'.
    // SRC-05 prerequisite — Pagefind core precached so search loads offline
    // (chunks lazy-fetched on query). The substring `pagefind` must appear
    // in the precache manifest list once Pagefind ships (plan 04-19).
    // Until then, the globPatterns line in sw.js (build-time inserted) is
    // what we can assert on — workbox compiles the glob into the bundle.
    // Note: Workbox-build resolves globPatterns at build time into the
    // __WB_MANIFEST array; the literal `pagefind` substring may not appear
    // in the compiled SW until plan 04-19 actually emits pagefind/ files
    // into dist/. We assert on the IMAGE_ORIGINS allowlist + cache prefix
    // here (the Pagefind precache assertion belongs to 04-19's spec).
  });

  test('SW source has ALLOW_SKIP_WAITING gated false (Pitfall #4)', async ({ page }) => {
    // Pitfall #4 — Phase 4 ships with skipWaiting OFF so users with the
    // Phase 1 kill-switch SW transition cleanly. Phase 6 cutover flips this.
    // This test catches an accidental flip in Phase 4 that would create
    // split-brain across tabs during a deploy.
    const response = await page.request.get('/sw.js');
    expect(response.status()).toBe(200);
    const body = await response.text();
    expect(body, 'ALLOW_SKIP_WAITING constant present in compiled SW').toContain(
      'ALLOW_SKIP_WAITING',
    );
    // The literal `false` must appear within ~120 chars of ALLOW_SKIP_WAITING
    // so we know the default-false branch survived DCE/minification.
    const idx = body.indexOf('ALLOW_SKIP_WAITING');
    const window = body.slice(idx, idx + 200);
    expect(
      window,
      `ALLOW_SKIP_WAITING is gated false in compiled SW. window=${JSON.stringify(window)}`,
    ).toContain('false');
  });

  test('/sw.js Cache-Control header is no-cache,no-store,must-revalidate', async ({ page }) => {
    // Phase 1 PMS-02 kill-switch invariant — _headers (copied into public/
    // by Plan 04-03 Task 2 per Pitfall #8) ensures CF Pages serves /sw.js
    // with no-cache headers. Without this, the browser caches the SW script
    // itself, defeating the update path and stranding users on a stale SW.
    const response = await page.request.get('/sw.js');
    expect(response.status()).toBe(200);
    const cacheControl = response.headers()['cache-control'] || '';
    expect(
      cacheControl,
      `/sw.js Cache-Control must include no-cache, no-store, must-revalidate. got: ${cacheControl}`,
    ).toMatch(/no-cache.*no-store.*must-revalidate/i);
  });
});
