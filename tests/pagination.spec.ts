// tests/pagination.spec.ts — Plan 04-04 wargov-repaging.
//
// Runs against process.env.PREVIEW_URL (CF Pages preview per Phase 2 D-31,
// playwright.config.ts). Defaults to https://realufo.pages.dev for unset env.
//
// Coverage matrix (must-haves truths in 04-04-PLAN.md, success criteria
// "Page 1..12 ... bookmarkable ... popstate ... hash ... lightbox cross-page"):
//   1. `/` shows exactly 20 visible cards (D-27 PAGE_SIZE=20)
//   2. `/?page=2` shows cards 21..40 (first visible is r021)
//   3. Footer reachable on every page without scrolling thousands of px (D-31)
//   4. Click pagination link updates URL via pushState — no full reload
//   5. Browser back (popstate) restores prior page state
//   6. `/#card-<slug>` resolves to the page containing that anchor (D-29)
//   7. Lightbox arrow advances across page boundary — lbList includes hidden
//      cards regardless of display:none (Pitfall #6)
//
// Why each test resets via fresh page.goto():
//   - Playwright fully-parallel mode (workers=4 in playwright.config.ts:25)
//     would deadlock on shared state.
//   - Independent failure messages — RED diagnosis points at exact bug.
//
// Helper note: each test waits for grid.dataset.fullyLoaded === '1' which the
// Plan 04-04 pagination handler sets after Promise.all(shards) resolves and
// all 222 cards are materialised via insertAdjacentHTML (D-10 LOCKED).

import { test, expect, type Page } from '@playwright/test';

const WARGOV_PATH = '/';
const PAGE_SIZE = 20;
const TOTAL_CARDS = 222; // 50 SSR + 50 + 50 + 50 + 22 across 4 shards (D-32)
// Total pages = 12 (Math.ceil(222 / 20)); not asserted directly but the
// rendered nav must contain anchors for pages 2..12 + Next on page 1.

// Wait until the pagination handler has materialised all 222 cards into the
// grid AND laid out the first page. Returns the visible-card count for
// callers that want to assert on it.
async function waitForFullyLoaded(page: Page): Promise<number> {
  await page.locator('#wargov-grid').waitFor({ state: 'attached' });
  await page.waitForFunction(
    () => document.getElementById('wargov-grid')?.dataset?.fullyLoaded === '1',
    null,
    { timeout: 15000 },
  );
  // Pagination nav must also be populated (renderPaginationNav fires after
  // ensureCardsMaterialised in the same microtask).
  await page.locator('#wargov-pagination a, #wargov-pagination span').first().waitFor({
    state: 'attached',
    timeout: 5000,
  });
  return page.locator('#wargov-grid .arch-card:visible').count();
}

test.describe.parallel('Pagination — Plan 04-04 wargov-repaging', () => {
  // -------------------------------------------------------------------------
  // Test 1: page 1 shows exactly 20 visible cards (D-27)
  // -------------------------------------------------------------------------
  test('page 1 shows exactly 20 visible cards', async ({ page }) => {
    await page.goto(WARGOV_PATH, { waitUntil: 'networkidle' });
    const visible = await waitForFullyLoaded(page);
    expect(visible).toBe(PAGE_SIZE);

    // Total card universe is 222 (sanity — guards against shard fetch failure).
    const total = await page.locator('#wargov-grid .arch-card').count();
    expect(total).toBe(TOTAL_CARDS);
  });

  // -------------------------------------------------------------------------
  // Test 2: ?page=2 shows cards 21..40 — first visible has data-row-id="r021"
  // -------------------------------------------------------------------------
  test('?page=2 shows cards 21..40 with r021 first', async ({ page }) => {
    await page.goto(`${WARGOV_PATH}?page=2`, { waitUntil: 'networkidle' });
    const visible = await waitForFullyLoaded(page);
    expect(visible).toBe(PAGE_SIZE);

    const firstVisibleRowId = await page
      .locator('#wargov-grid .arch-card:visible')
      .first()
      .getAttribute('data-row-id');
    expect(firstVisibleRowId).toBe('r021');

    const lastVisibleRowId = await page
      .locator('#wargov-grid .arch-card:visible')
      .last()
      .getAttribute('data-row-id');
    expect(lastVisibleRowId).toBe('r040');

    // URL bar should still show ?page=2 (no rewrite by handler).
    expect(page.url()).toContain('page=2');
  });

  // -------------------------------------------------------------------------
  // Test 3: footer reachable without scrolling thousands of px (D-31)
  // -------------------------------------------------------------------------
  test('footer reachable without scrolling past 5000 px on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(WARGOV_PATH, { waitUntil: 'networkidle' });
    await waitForFullyLoaded(page);

    // getBoundingClientRect().top is relative to viewport; bottom of document
    // = top + viewport offset already accounted. We measure offsetTop instead
    // which is independent of current scroll position — i.e. the footer's
    // absolute Y in the page. 5000 px = ~7 viewports on 360x667; with PAGE_SIZE
    // = 20 cards (each ~600 px tall) we expect ~3000-4000 px doc height.
    const footerTop = await page.evaluate(() => {
      const f = document.querySelector('footer');
      if (!f) return Number.POSITIVE_INFINITY;
      // offsetTop is relative to the nearest positioned ancestor; sum the
      // chain to get absolute document Y.
      let el: HTMLElement | null = f as HTMLElement;
      let y = 0;
      while (el) {
        y += el.offsetTop;
        el = el.offsetParent as HTMLElement | null;
      }
      return y;
    });
    expect(footerTop).toBeLessThan(5000);
  });

  // -------------------------------------------------------------------------
  // Test 4: clicking pagination link uses pushState — no full reload
  // -------------------------------------------------------------------------
  test('pagination link click updates URL via pushState (no full reload)', async ({ page }) => {
    await page.goto(WARGOV_PATH, { waitUntil: 'networkidle' });
    await waitForFullyLoaded(page);

    // Plant a sentinel on window — a full page navigation would wipe it; a
    // pushState SPA-style nav preserves it.
    await page.evaluate(() => {
      (window as unknown as { __spaSentinel?: number }).__spaSentinel = 0xdead;
    });

    // Click the ?page=2 anchor in the pagination nav.
    await page.locator('#wargov-pagination a[href="?page=2"]').click();

    // URL bar reflects pushState immediately.
    await expect.poll(() => page.url(), { timeout: 3000 }).toContain('page=2');

    // First visible card is now r021 (page 2 starts at idx 20 = r021).
    const firstVisibleRowId = await page
      .locator('#wargov-grid .arch-card:visible')
      .first()
      .getAttribute('data-row-id');
    expect(firstVisibleRowId).toBe('r021');

    // Sentinel survives — proves no full document navigation occurred.
    const sentinelStillSet = await page.evaluate(
      () => (window as unknown as { __spaSentinel?: number }).__spaSentinel === 0xdead,
    );
    expect(sentinelStillSet).toBe(true);
  });

  // -------------------------------------------------------------------------
  // Test 5: browser back (popstate) restores prior page state
  // -------------------------------------------------------------------------
  test('popstate restores prior page after browser back', async ({ page }) => {
    await page.goto(WARGOV_PATH, { waitUntil: 'networkidle' });
    await waitForFullyLoaded(page);

    // Navigate to page 3 via pagination click → pushState push.
    await page.locator('#wargov-pagination a[href="?page=3"]').click();
    await expect.poll(() => page.url(), { timeout: 3000 }).toContain('page=3');
    const firstAfterClick = await page
      .locator('#wargov-grid .arch-card:visible')
      .first()
      .getAttribute('data-row-id');
    expect(firstAfterClick).toBe('r041');

    // Browser back — popstate listener replays URLSearchParams.get('page') = null
    // → readPage() returns 1 → first visible card is r001.
    await page.goBack();
    await expect.poll(() => page.url(), { timeout: 3000 }).not.toContain('page=3');

    // After popstate fires, the page-rendered event re-derives visibility.
    await page.waitForFunction(
      () =>
        document
          .querySelector('#wargov-grid .arch-card:not([style*="display: none"])')
          ?.getAttribute('data-row-id') === 'r001',
      null,
      { timeout: 3000 },
    );
    const firstAfterBack = await page
      .locator('#wargov-grid .arch-card:visible')
      .first()
      .getAttribute('data-row-id');
    expect(firstAfterBack).toBe('r001');
  });

  // -------------------------------------------------------------------------
  // Test 6: /#card-<slug> resolves to the page containing the anchor
  // -------------------------------------------------------------------------
  test('hash link resolves to the page containing the card', async ({ page }) => {
    // First load page 1 to harvest a card slug from page 3 (cards 41..60).
    // Server-renders the first 50 rows (D-08); card #41 (idx 40) lives in
    // the SSR'd grid and we can read its id.
    await page.goto(WARGOV_PATH, { waitUntil: 'networkidle' });
    await waitForFullyLoaded(page);

    // Pick the card at idx 40 (row #41, page 3 first card per PAGE_SIZE=20).
    const slug = await page.evaluate(() => {
      const cards = document.querySelectorAll('#wargov-grid .arch-card');
      const c = cards[40]; // 0-indexed → row 41
      if (!c) return null;
      const id = c.getAttribute('id') || ''; // 'card-<slug>'
      return id.startsWith('card-') ? id : null;
    });
    expect(slug, 'card #41 must have a `card-<slug>` id').not.toBeNull();

    // Now deep-link to /#card-<slug>.
    await page.goto(`${WARGOV_PATH}#${slug}`, { waitUntil: 'networkidle' });
    await waitForFullyLoaded(page);

    // The pagination handler's hash-handling branch should re-render to page 3
    // (idx 40 = page 3). Wait for the target card to become visible.
    await page.waitForFunction(
      (sel) => {
        const el = document.querySelector(sel) as HTMLElement | null;
        if (!el) return false;
        return el.style.display !== 'none' && el.offsetParent !== null;
      },
      `#${slug}`,
      { timeout: 5000 },
    );

    const targetVisible = await page.locator(`#${slug}`).isVisible();
    expect(targetVisible).toBe(true);

    // First visible card on page 3 is r041.
    const firstVisibleRowId = await page
      .locator('#wargov-grid .arch-card:visible')
      .first()
      .getAttribute('data-row-id');
    expect(firstVisibleRowId).toBe('r041');

    // Hash preserved in URL.
    expect(page.url()).toContain(`#${slug}`);
  });

  // -------------------------------------------------------------------------
  // Test 7: lightbox arrow advances across page boundary (Pitfall #6)
  // -------------------------------------------------------------------------
  test('lightbox arrow advances across page boundary (lbList includes hidden)', async ({
    page,
  }) => {
    await page.goto(WARGOV_PATH, { waitUntil: 'networkidle' });
    await waitForFullyLoaded(page);

    // Open the 20th card (last on page 1, data-row-id="r020").
    await page.locator('#wargov-grid .arch-card[data-row-id="r020"] a.btn-open').click();
    await expect(page.locator('#lightbox')).toHaveClass(/open/);
    // Counter "20 / 222" — confirms __lbList walked all 222 cards regardless
    // of display:none (Pitfall #6).
    await expect(page.locator('#lb-counter')).toHaveText(new RegExp(`^20 \\/ ${TOTAL_CARDS}$`));

    // ArrowRight → counter advances to 21 (the first card of page 2 which is
    // currently display:none — the lightbox MUST be able to surface it).
    await page.keyboard.press('ArrowRight');
    await expect(page.locator('#lb-counter')).toHaveText(new RegExp(`^21 \\/ ${TOTAL_CARDS}$`));

    // Cross-verify via __lbList — the lbList entry at idx 20 must have rowId
    // 'r021' (the card the lightbox now displays).
    const lbList20RowId = await page.evaluate(() => {
      const list = (window as unknown as { __lbList?: Array<{ rowId: string }> }).__lbList || [];
      return list[20]?.rowId ?? null;
    });
    expect(lbList20RowId).toBe('r021');

    await page.keyboard.press('Escape');
    await expect(page.locator('#lightbox')).not.toHaveClass(/open/);
  });
});

// Sanity: this file ships >= 7 test() blocks. Plan acceptance criterion:
//   grep -c "test('" tests/pagination.spec.ts returns >= 7
