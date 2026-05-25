// Visual regression spec — Phase 2 INF-04. Runs against process.env.PREVIEW_URL
// (CF Pages preview per D-31). Compares against tests/visual-baselines/*.png
// frozen per D-17. 0.1% pixel-diff hard-fails per D-16. 60 tests (15 archives ×
// 4 viewports) per D-13.
//
// Filename convention: `${slug}-${width}.png` MUST match the capture script's
// output (scripts/capture-baselines.py) so playwright.config.ts's
// `snapshotPathTemplate: 'tests/visual-baselines/{arg}{ext}'` resolves to the
// same file the operator committed.
//
// Source-of-truth lists below MUST stay byte-equal to scripts/capture-baselines.py
// — if the archive slug list or viewport list ever changes, BOTH this file AND
// the Python script must change together; a drift between them silently breaks
// the visual-regression gate.

import { test, expect } from '@playwright/test';

// 15 archives — order matches scripts/capture-baselines.py ARCHIVES.
// Source: CLAUDE.md §2.
const ARCHIVES: Array<[string, string]> = [
  ['wargov', '/'],
  ['aaro', '/aaro/'],
  ['nasa', '/nasa/'],
  ['nara', '/nara/'],
  ['geipan', '/geipan/'],
  ['uk', '/uk/'],
  ['brazil', '/brazil/'],
  ['chile', '/chile/'],
  ['argentina', '/argentina/'],
  ['canada', '/canada/'],
  ['italy', '/italy/'],
  ['nz', '/nz/'],
  ['peru', '/peru/'],
  ['spain', '/spain/'],
  ['uruguay', '/uruguay/'],
];

// 4 viewports per D-14. 360 first per CLAUDE.md §8 mobile-first rule.
const VIEWPORTS: Array<[number, number]> = [
  [360, 800],
  [768, 1024],
  [1024, 768],
  [1440, 900],
];

test.describe.parallel('visual regression — 15 archives × 4 viewports', () => {
  for (const [slug, path] of ARCHIVES) {
    for (const [w, h] of VIEWPORTS) {
      test(`${slug} @ ${w}x${h}`, async ({ page }) => {
        await page.setViewportSize({ width: w, height: h });
        await page.goto(path, { waitUntil: 'networkidle' });
        // 500 ms settle matches the capture script's wait. CLAUDE.md §3 hero
        // carousel uses setInterval(6500); 500 ms guarantees slide 1 stable.
        await page.waitForTimeout(500);
        await expect(page).toHaveScreenshot(`${slug}-${w}.png`);
      });
    }
  }
});
