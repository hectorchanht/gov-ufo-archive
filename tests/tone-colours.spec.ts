// Tone-colour smoke test — Phase 2 INF-06. Asserts :root --caution per archive
// matches CLAUDE.md §3.1 (via tests/tone-colours-fixture.json) per D-22. Hard-fail
// per D-23. Runs against process.env.PREVIEW_URL (Plan 02-08 wires this from PR
// deployment_status per D-31).
//
// Why this gate exists: research/PITFALLS.md §Pitfall #7 (cross-archive drift) —
// one --caution typo on archive 14 of 15 produces a 95%-right page (e.g. Spain
// blue instead of gold) that visual-regression alone may miss. This smoke test
// catches it in <100 ms per archive.
//
// Iteration is driven by the hard-coded ARCHIVES list below, NOT by
// Object.keys(fixture) — that keeps the fixture's `_metadata` key separate from
// archive slugs without needing runtime filtering.
//
// TS typing (W3 revision): the fixture object has a `_metadata` key plus 15
// archive slug keys. TS infers a narrow object-literal type from the JSON
// import, so `fixture[slug]` with `slug: string` would fail strict type-check.
// We cast at access site to `Record<string, string>` — see expected lookup
// below. The `_metadata` key is never indexed because iteration is driven by
// ARCHIVES.

import { test, expect } from '@playwright/test';
import fixture from './tone-colours-fixture.json';

// 15 archives — order matches CLAUDE.md §2 + visual-regression.spec.ts ARCHIVES.
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

test.describe('tone-colour smoke — 15 archives vs CLAUDE.md §3.1 (D-22 / D-23)', () => {
  for (const [slug, path] of ARCHIVES) {
    test(`tone colour for ${slug}`, async ({ page }) => {
      await page.goto(path);
      const actual = (
        await page.evaluate(() =>
          getComputedStyle(document.documentElement).getPropertyValue('--caution')
        )
      )
        .trim()
        .toLowerCase();

      // W3 cast pattern: narrow the JSON-import type at the access site so the
      // `_metadata` key + 15 archive keys coexist without TS narrowing failure.
      const expected = ((fixture as unknown) as Record<string, string>)[slug].toLowerCase();

      expect(
        actual,
        `Archive ${slug} (${path}) — expected --caution=${expected}, got ${actual}. ` +
          `Check CLAUDE.md §3.1 vs the archive's :root CSS.`
      ).toBe(expected);
    });
  }
});
