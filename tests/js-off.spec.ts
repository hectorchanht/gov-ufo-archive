// JS-off rendering test — Phase 2 INF-07. Asserts each archive renders cards +
// headings + no 'loading' placeholder with JavaScript disabled (D-24). Hard-fail
// per D-25 (UNCONDITIONAL — Plan 02-08 wires this WITHOUT continue-on-error).
// Phase 3 SSG MUST pre-render cards not hydrate from JSON (PROJECT.md core
// constraint; research/PITFALLS.md §Pitfall #9). Runs against
// process.env.PREVIEW_URL (Plan 02-08 wires from PR deployment_status per D-31).
//
// During the Phase 2/3 wargov-only window, this gate WILL fail for archives
// that still hydrate client-side — that failure is the SIGNAL that Phase 3
// work for the archive is pending, NOT a reason to soften the gate. Plan 02-08
// ships the js-off job with no continue-on-error.

import { test, expect } from '@playwright/test';

// 15 archives — order matches CLAUDE.md §2 + visual-regression.spec.ts +
// tone-colours.spec.ts ARCHIVES.
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

test.describe('JS-off rendering — 15 archives (D-24 / D-25)', () => {
  for (const [slug, path] of ARCHIVES) {
    test(`${slug} renders meaningfully without JS`, async ({ browser }) => {
      const context = await browser.newContext({ javaScriptEnabled: false });
      const page = await context.newPage();
      try {
        // domcontentloaded (NOT networkidle) — with JS off, networkidle never
        // fires reliably because some pages keep long-poll connections open or
        // fail to resolve fetch() side effects.
        await page.goto(path, { waitUntil: 'domcontentloaded' });

        // D-24 first assertion: at least one card visible. Selector union covers
        // the archive's current and Phase-3+ Astro markup variants:
        //   <article>          — semantic card wrapper
        //   .arch-grid > *     — direct children of the evidence grid
        //   .card / .head-card — utility class variants in current HTML
        const cards = await page.locator('article, .arch-grid > *, .card, .head-card').count();
        expect(
          cards,
          `${slug}: expected >=1 card visible with JS off (D-24); got ${cards}. ` +
            `Page must pre-render cards per PROJECT.md "Pre-rendered cards, no hydration".`
        ).toBeGreaterThan(0);

        // D-24 second assertion: at least one heading visible.
        const headings = await page.locator('h1, h2').count();
        expect(
          headings,
          `${slug}: expected >=1 heading visible with JS off (D-24); got ${headings}`
        ).toBeGreaterThan(0);

        // D-24 third assertion: body has meaningful content (not just a loader).
        const bodyText = ((await page.textContent('body')) || '').trim();
        expect(
          bodyText.length,
          `${slug}: empty body with JS off — page failed to render any text`
        ).toBeGreaterThan(50);

        // D-24 fourth assertion: no JS-off placeholder dominates the viewport.
        // Inspect first 100 chars of body text; if a placeholder is the
        // visible content, the page is hydration-blocking and Phase 3 hasn't
        // ported this archive yet.
        const firstChars = bodyText.slice(0, 100).toLowerCase();
        expect(
          firstChars,
          `${slug}: first 100 chars of body match a JS-off placeholder — ` +
            `page is hydration-blocking. First 100 chars: "${firstChars}"`
        ).not.toMatch(/^(enable javascript|loading|please wait|loading\.\.\.|please enable)/i);
      } finally {
        await context.close();
      }
    });
  }
});
