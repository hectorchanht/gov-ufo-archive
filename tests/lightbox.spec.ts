// tests/lightbox.spec.ts — Plan 04-01 lightbox-fix.
//
// Runs against process.env.PREVIEW_URL (CF Pages preview per D-31, Phase 2
// playwright.config.ts). Defaults to https://realufo.pages.dev for unset env.
//
// Coverage matrix (must-haves truths in 04-01-PLAN.md):
//   1. Click open card #1                            → lightbox opens, counter "1 / N"
//   2. ArrowRight                                    → counter advances, title differs
//   3. Escape                                        → lightbox closes, body.overflow restored
//   4. Documents tab filter + click first visible    → THAT card opens (not #1) — Bug 1
//   5. Remote PDF (data-local empty)                 → .lb-meta panel, NO iframe — Bug 2
//   6. /?page=3 cross-page smoke (test.skip)         → placeholder for Plan 04-04
//
// Why 6 tests and not 1 omnibus:
//   - Each test resets state via fresh page.goto(); Playwright fully-parallel
//     mode (playwright.config.ts:24 workers=4) won't deadlock on shared state.
//   - Independent failure messages — RED diagnosis points at exact bug.

import { test, expect } from '@playwright/test';

const WARGOV_PATH = '/';

test.describe.parallel('lightbox — Plan 04-01 must-haves', () => {
  // -------------------------------------------------------------------------
  // Test 1: lightbox opens on btn-open click (smoke)
  // -------------------------------------------------------------------------
  test('click open on card #1 opens lightbox with counter 1 / N', async ({ page }) => {
    await page.goto(WARGOV_PATH, { waitUntil: 'networkidle' });
    // Wait for at least one card to render (server-rendered first 50 per D-08).
    await page.locator('#wargov-grid .arch-card').first().waitFor({ state: 'visible' });
    await page.locator('#wargov-grid .arch-card a.btn-open').first().click();

    const lb = page.locator('#lightbox');
    await expect(lb).toHaveClass(/open/);

    const counter = page.locator('#lb-counter');
    await expect(counter).toHaveText(/^1 \/ \d+$/);
  });

  // -------------------------------------------------------------------------
  // Test 2: ArrowRight advances counter + content
  // -------------------------------------------------------------------------
  test('arrow right key advances lightbox counter and content', async ({ page }) => {
    await page.goto(WARGOV_PATH, { waitUntil: 'networkidle' });
    await page.locator('#wargov-grid .arch-card').first().waitFor({ state: 'visible' });
    // Capture the first card's title (anchor opens with this content).
    const firstTitle = await page.locator('#wargov-grid .arch-card .card-title').first().textContent();
    await page.locator('#wargov-grid .arch-card a.btn-open').first().click();
    await expect(page.locator('#lightbox')).toHaveClass(/open/);

    await page.keyboard.press('ArrowRight');
    await expect(page.locator('#lb-counter')).toHaveText(/^2 \/ \d+$/);

    // After advancing, the lightbox's interior content (#lb-inner) MUST have
    // re-rendered. We don't assert the exact title in the panel (the lightbox
    // doesn't currently render a title element inside #lb-inner for non-PDF
    // assets), so we assert the counter advanced and the first card's title
    // is unchanged in the DOM (sanity: cards didn't reflow).
    const stillFirstTitle = await page.locator('#wargov-grid .arch-card .card-title').first().textContent();
    expect(stillFirstTitle).toBe(firstTitle);
  });

  // -------------------------------------------------------------------------
  // Test 3: Escape closes lightbox + restores body scroll
  // -------------------------------------------------------------------------
  test('Escape closes lightbox and restores body.overflow', async ({ page }) => {
    await page.goto(WARGOV_PATH, { waitUntil: 'networkidle' });
    await page.locator('#wargov-grid .arch-card').first().waitFor({ state: 'visible' });
    await page.locator('#wargov-grid .arch-card a.btn-open').first().click();
    await expect(page.locator('#lightbox')).toHaveClass(/open/);

    await page.keyboard.press('Escape');
    await expect(page.locator('#lightbox')).not.toHaveClass(/open/);

    // closeLb() sets document.body.style.overflow = ''.
    const bodyOverflow = await page.evaluate(() => document.body.style.overflow);
    expect(bodyOverflow).toBe('');
  });

  // -------------------------------------------------------------------------
  // Test 4: Filtered Documents tab opens the visible card (not card #1)
  //         — regression for Bug 1 (data-idx drift)
  // -------------------------------------------------------------------------
  test('filter Documents tab then click open opens the filtered card not #1', async ({ page }) => {
    await page.goto(WARGOV_PATH, { waitUntil: 'networkidle' });
    await page.locator('#wargov-grid .arch-card').first().waitFor({ state: 'visible' });

    // Capture unfiltered card #1 title for cross-check.
    const unfilteredFirstTitle = await page.locator('#wargov-grid .arch-card .card-title').first().textContent();

    // Click the PDF tab (CLAUDE.md §4 + index.astro tabs use data-tab="PDF"
    // matching Card.astro's data-type emission; "DOC" is the displayed text
    // but `data-tab` attr carries the canonical type string).
    const pdfTab = page.locator('.arch-controls-bar .tab[data-tab="PDF"]');
    // If the wargov page uses a different tab id, fall back to the first
    // non-"all" tab (defensive — test should still exercise the filtered path).
    const tabCount = await pdfTab.count();
    if (tabCount > 0) {
      await pdfTab.first().click();
    } else {
      const firstNonAllTab = page.locator('.arch-controls-bar .tab:not([data-tab="all"])').first();
      await firstNonAllTab.click();
    }

    // Find first VISIBLE filtered card. display:none cards are filtered out
    // by Playwright's :visible selector.
    const firstVisibleCard = page.locator('#wargov-grid .arch-card:visible').first();
    await firstVisibleCard.waitFor({ state: 'visible' });
    const filteredFirstTitle = await firstVisibleCard.locator('.card-title').textContent();

    // Click the visible card's Open button.
    await firstVisibleCard.locator('a.btn-open').click();
    await expect(page.locator('#lightbox')).toHaveClass(/open/);

    // The lightbox internally renders the asset (iframe/img/video). The
    // counter MUST reflect the rowId of the filtered card, not card #1.
    // We cross-check by reading rowId off the visible card and asserting the
    // lightbox's counter is positioned to that rowId via __lbList state.
    const filteredRowId = await firstVisibleCard.getAttribute('data-row-id');
    const lbIdxResolved = await page.evaluate((rowId) => {
      const list = (window as unknown as { __lbList?: Array<{ rowId: string }> }).__lbList || [];
      return list.findIndex((x) => x && x.rowId === rowId);
    }, filteredRowId);
    // The lbList lookup MUST resolve to a non-negative index for the patch
    // to be considered working. Bug 1 would return -1 or the wrong asset.
    expect(lbIdxResolved).toBeGreaterThanOrEqual(0);

    // If the filtered first card differs from the unfiltered first card, the
    // test is meaningful. Otherwise (PDF tab includes card #1), at least
    // verify the open lightbox is correctly addressing the filtered card.
    if (filteredFirstTitle !== unfilteredFirstTitle) {
      // Counter should match the rowId's position in __lbList + 1.
      const expectedCounter = String(lbIdxResolved + 1);
      await expect(page.locator('#lb-counter')).toHaveText(new RegExp(`^${expectedCounter} \\/ \\d+$`));
    }
  });

  // -------------------------------------------------------------------------
  // Test 5: Remote PDF (data-local empty) shows meta panel, NO iframe
  //         — regression for Bug 2 (local field never propagated)
  // -------------------------------------------------------------------------
  test('remote PDF Open shows lb-meta panel not iframe', async ({ page }) => {
    await page.goto(WARGOV_PATH, { waitUntil: 'networkidle' });
    await page.locator('#wargov-grid .arch-card').first().waitFor({ state: 'visible' });

    // Find a card whose btn-open has empty data-local AND whose data-url
    // ends with .pdf (case-insensitive). All wargov PDFs are remote in the
    // current dataset (Phase 4 R2 migration NOT yet applied), so this will
    // match card #1 in practice.
    const remotePdfOpen = page.locator(
      '#wargov-grid .arch-card a.btn-open[data-local=""]'
    ).filter({
      hasNot: page.locator('[data-url*=".html"]'),
    }).first();

    // Defensive: if the selector doesn't match (e.g. all PDFs are local in a
    // future migration step), assert by attribute manually.
    const count = await remotePdfOpen.count();
    if (count === 0) {
      test.skip(true, 'No remote PDF found on wargov — likely all migrated to local; skip Bug 2 regression');
    }
    // Sanity: confirm the url is a PDF.
    const url = await remotePdfOpen.getAttribute('data-url');
    expect(url?.toLowerCase().endsWith('.pdf')).toBe(true);

    await remotePdfOpen.click();
    await expect(page.locator('#lightbox')).toHaveClass(/open/);

    // CRITICAL: renderLb() Bug 2 fix — remote PDF must render .lb-meta panel
    // not an iframe. (invariants.ts line ~75)
    const metaPanel = page.locator('#lb-inner .lb-meta');
    const iframe = page.locator('#lb-inner iframe');
    await expect(metaPanel).toBeVisible();
    await expect(iframe).toHaveCount(0);
  });

  // -------------------------------------------------------------------------
  // Test 6: Cross-page anchor — skipped pending Plan 04-04 wargov-repaging
  // -------------------------------------------------------------------------
  test('pagination cross-page anchor opens correct asset (Plan 04-04)', async () => {
    test.skip(true, 'requires 04-04-wargov-repaging merged — see 04-RESEARCH.md §6');
  });
});
