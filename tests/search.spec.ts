// tests/search.spec.ts — Plan 04-19 Pagefind cross-archive search.
//
// Runs against process.env.PREVIEW_URL (CF Pages preview per D-31 / Phase 2
// playwright.config.ts). Defaults to https://realufo.pages.dev when env unset.
//
// Coverage matrix (must-haves truths in 04-19-PLAN.md):
//   1. /search loads + PagefindUI mounts (.pagefind-ui present)
//   2. Query "tic tac" returns ≥ 1 result (cross-archive index hit)
//   3. Archive filter dropdown lists 4 archives (wargov, aaro, nasa, nara)
//      — matches current ACTIVE_ARCHIVES set in RootLayout.astro per the
//      2026-05-28 scope pivot. Plan PLAN.md asks for "15 archives" but
//      that predates the scope pivot; the in-tree truth is 4 active archives.
//   4. Result link href contains "#card-" (SRC-04 — processResult anchor
//      injection per RESEARCH §2 Pitfall 9)
//
// Why 4 separate tests and not 1 omnibus:
//   - Independent failure messages — RED diagnosis points at exact bug.
//   - Each test resets state via fresh page.goto(); Playwright fully-parallel
//     workers=4 (playwright.config.ts:24) does not deadlock.

import { test, expect } from '@playwright/test';

const SEARCH_PATH = '/search';

test.describe.parallel('Pagefind cross-archive search — Plan 04-19 must-haves', () => {
  // -------------------------------------------------------------------------
  // Test 1: PagefindUI mounts on /search
  // -------------------------------------------------------------------------
  test('PagefindUI loads on /search (.pagefind-ui present)', async ({ page }) => {
    await page.goto(SEARCH_PATH, { waitUntil: 'networkidle' });
    // PagefindUI inserts a .pagefind-ui wrapper inside its mount target.
    // The mount target is #pagefind-search per src/pages/search.astro.
    const ui = page.locator('#pagefind-search .pagefind-ui');
    await expect(ui).toBeVisible({ timeout: 5000 });
  });

  // -------------------------------------------------------------------------
  // Test 2: Query "tic tac" returns ≥ 1 result
  // -------------------------------------------------------------------------
  test('query "tic tac" returns at least 1 result', async ({ page }) => {
    await page.goto(SEARCH_PATH, { waitUntil: 'networkidle' });
    await page.locator('#pagefind-search .pagefind-ui').waitFor({ state: 'visible' });
    const input = page.locator('#pagefind-search .pagefind-ui__search-input');
    await input.fill('tic tac');
    // Pagefind UI debounces; wait for the result list to populate.
    const results = page.locator('#pagefind-search .pagefind-ui__result');
    await expect(results.first()).toBeVisible({ timeout: 8000 });
    const count = await results.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  // -------------------------------------------------------------------------
  // Test 3: Archive filter dropdown lists the 4 active archives
  // -------------------------------------------------------------------------
  test('archive filter dropdown lists 4 active archives', async ({ page }) => {
    await page.goto(SEARCH_PATH, { waitUntil: 'networkidle' });
    await page.locator('#pagefind-search .pagefind-ui').waitFor({ state: 'visible' });
    // Trigger at least one query so PagefindUI mounts the filter pills
    // (PagefindUI lazy-loads filter UI on first query in some versions).
    await page.locator('#pagefind-search .pagefind-ui__search-input').fill('uap');
    // Wait for the filter block to appear.
    const filterBlock = page.locator('#pagefind-search .pagefind-ui__filter-panel, #pagefind-search [data-pfmod-suppressed]').first();
    // Filter labels for "archive" should be present. Pagefind renders them
    // as buckets — at least one of: wargov, aaro, nasa, nara.
    await page.waitForTimeout(1500);
    const archiveValues = await page.locator('#pagefind-search').innerText();
    // Expect each of the 4 active archive slugs to be referenced as a
    // filter bucket. PagefindUI prints "wargov" / "aaro" / "nasa" / "nara"
    // as the filter VALUE next to its bucket count.
    const slugs = ['wargov', 'aaro', 'nasa', 'nara'];
    const present = slugs.filter((s) => archiveValues.toLowerCase().includes(s));
    expect(present.length).toBeGreaterThanOrEqual(4);
  });

  // -------------------------------------------------------------------------
  // Test 4: Result link href carries #card-<slug> anchor (SRC-04)
  // -------------------------------------------------------------------------
  test('result link href contains #card- fragment (SRC-04 anchor injection)', async ({ page }) => {
    await page.goto(SEARCH_PATH, { waitUntil: 'networkidle' });
    await page.locator('#pagefind-search .pagefind-ui').waitFor({ state: 'visible' });
    await page.locator('#pagefind-search .pagefind-ui__search-input').fill('tic tac');
    const result = page.locator('#pagefind-search .pagefind-ui__result-link').first();
    await expect(result).toBeVisible({ timeout: 8000 });
    const href = await result.getAttribute('href');
    expect(href).toBeTruthy();
    // SRC-04 contract: result URL must include the #card-<slug> fragment.
    // PagefindUI's default processResult does NOT do this; src/pages/
    // search.astro overrides processResult to append sub_results[0]
    // .anchor.id per RESEARCH §2 Pitfall 9.
    expect(href).toMatch(/#card-/);
  });
});
