// R2 binary CDN URL smoke — Phase 4 Plan 04-02 Task 3.
//
// Asserts that the R2 custom-domain (`https://assets.realufo.org/...`) URLs
// emitted by `scripts/normalize-csv.py` into `data/wargov.json` resolve to
// real R2 objects with HTTP 200 + the expected CORS echo for the
// `https://realufo.org` origin.
//
// This spec is intentionally SKIPPABLE during the pre-migration window
// (after this plan merges to main but before the operator triggers
// `gh workflow run r2-sync.yml -f full_sync=true`). Set the env var
// `R2_MIGRATED=1` to enable the assertions; absent that, the spec is
// `test.skip(...)`ed so CI doesn't go red while the bulk migration is in
// flight. See `.planning/decisions/r2-setup.md` for the bulk-migration
// runbook.
//
// Mirrors the structure of `tests/sw.spec.ts` / `tests/lightbox.spec.ts`:
//   - testDir: '.' resolves to tests/ (playwright.config.ts:24)
//   - chromium-only per playwright.config.ts D-15
//   - APIRequestContext (not page.evaluate) for clean HEAD requests
//     without dragging the SW into the picture
//
// Run locally:
//   R2_MIGRATED=1 pnpm exec playwright test tests/r2-urls.spec.ts
//
// CI: the workflow that triggers this spec must export `R2_MIGRATED=1`
// only after the operator confirms the bulk migration is complete.
// (Plan 04-02 Task 4 — operator checkpoint.)

import { test, expect, request as apiRequest } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const R2_BASE = 'https://assets.realufo.org';
const ORIGIN = 'https://realufo.org';

// `R2_MIGRATED` env-gate. Default unset → skip the HEAD-checks.
// Set to `1` / `true` / `yes` once the bulk migration is done.
const R2_MIGRATED = (() => {
  const v = (process.env.R2_MIGRATED || '').toLowerCase().trim();
  return v === '1' || v === 'true' || v === 'yes';
})();

// Sample size — the wargov manifest has ~134 R2 URLs across PDFs + videos.
// HEAD-checking every URL would spend ~134 × ~200 ms = ~27 s on a serial
// run; we sample 10 to stay under the 10-minute job budget while still
// catching systematic-config bugs (a typo in the prefix, a missing CORS
// rule, a wrong custom-domain bind).
const SAMPLE_SIZE = 10;

interface WargovRow {
  Title?: string;
  Type?: string;
  'PDF | Image Link'?: string;
  [k: string]: unknown;
}

interface WargovShardCard {
  id: string;
  html: string;
}

interface WargovShard {
  schemaVersion: number;
  slug: string;
  shardIndex: number;
  cards: WargovShardCard[];
}

interface WargovEnvelope {
  v1: {
    schemaVersion: number;
    slug: string;
    rows: WargovRow[];
    shards: Array<{ index: number; file: string }>;
  };
}

/** Extract every `https://assets.realufo.org/...` URL from data/wargov.json
 * + sibling shards. Reads files synchronously from disk (Astro `file()`
 * loader inputs live at `data/<slug>.json`).
 *
 * @returns deduplicated, sorted list of R2 URLs found in card.url-equivalent
 *          slots (`PDF | Image Link` on raw rows, `data-url=` on shard HTML).
 */
function collectR2Urls(): string[] {
  const repoRoot = resolve(__dirname, '..');
  const dataDir = resolve(repoRoot, 'data');
  const urls = new Set<string>();

  // First-page raw rows — server-rendered by Card.astro.
  const primary: WargovEnvelope = JSON.parse(
    readFileSync(resolve(dataDir, 'wargov.json'), 'utf8'),
  );
  for (const row of primary.v1.rows) {
    const u = (row['PDF | Image Link'] || '').trim();
    if (u.startsWith(`${R2_BASE}/`)) urls.add(u);
  }

  // Shards — pre-rendered HTML strings. Card markup uses
  // `data-url="..."` on `<a class="btn-open">` per D-10.
  for (const shardManifest of primary.v1.shards) {
    const shardPath = resolve(repoRoot, shardManifest.file);
    const shard: WargovShard = JSON.parse(readFileSync(shardPath, 'utf8'));
    for (const card of shard.cards) {
      // Match the FIRST data-url attribute in each card (btn-open). The
      // regex tolerates whitespace + any other attribute between
      // `class="btn-open"` and `data-url`. We greedy-match assets URLs only.
      const re = /data-url="(https:\/\/assets\.realufo\.org\/[^"]+)"/g;
      let m: RegExpExecArray | null;
      while ((m = re.exec(card.html)) !== null) {
        urls.add(m[1]);
      }
    }
  }

  return [...urls].sort();
}

/** Deterministic sample of `SAMPLE_SIZE` URLs from the list. Uses a
 * stride-based picker (not Math.random) so test failures are
 * reproducible across runs. */
function sampleUrls(all: string[]): string[] {
  if (all.length <= SAMPLE_SIZE) return all.slice();
  const stride = Math.floor(all.length / SAMPLE_SIZE);
  const picks: string[] = [];
  for (let i = 0; i < SAMPLE_SIZE; i++) picks.push(all[i * stride]);
  return picks;
}

test.describe('R2 binary CDN URLs', () => {
  // Sanity check that runs even when R2_MIGRATED is unset — confirms the
  // manifest contains R2 URLs at all. Catches accidental regressions where
  // `normalize-csv.py` stops emitting R2 URLs entirely.
  test('data/wargov.json contains R2 custom-domain URLs', () => {
    const all = collectR2Urls();
    expect(
      all.length,
      'expected wargov.json + shards to contain at least 1 R2 URL — re-run scripts/normalize-csv.py',
    ).toBeGreaterThan(0);

    // Spot-check: every R2 URL should route through pdfs/ or videos/
    // prefixes per .planning/decisions/r2-setup.md D-05.
    for (const u of all) {
      expect(
        u.startsWith(`${R2_BASE}/pdfs/wargov/`) ||
          u.startsWith(`${R2_BASE}/videos/wargov/`),
        `R2 URL outside the expected pdfs/wargov/ or videos/wargov/ prefix: ${u}`,
      ).toBe(true);
    }
  });

  // HEAD-checks — gated by R2_MIGRATED env var so CI can ship the spec
  // before the bulk migration completes.
  test('sample R2 URLs return 200 with realufo.org CORS allow', async () => {
    test.skip(
      !R2_MIGRATED,
      'set R2_MIGRATED=1 once the operator triggers bulk migration (Plan 04-02 Task 4)',
    );

    const all = collectR2Urls();
    const sample = sampleUrls(all);
    expect(
      sample.length,
      'sample must be non-empty when R2_MIGRATED gate is open',
    ).toBeGreaterThan(0);

    const ctx = await apiRequest.newContext({
      extraHTTPHeaders: { Origin: ORIGIN },
    });
    try {
      for (const url of sample) {
        const resp = await ctx.fetch(url, { method: 'HEAD' });
        expect(
          resp.status(),
          `HEAD ${url} returned ${resp.status()} — expected 200 (object present + custom domain bound)`,
        ).toBe(200);

        // CORS echo — bucket's allowlist includes ORIGIN, so the response
        // must echo it (NOT `*` — see r2-cors.json + r2-setup.md §"Allowed
        // origins"). Header lookup is case-insensitive per APIRequestContext.
        const allow = resp.headers()['access-control-allow-origin'] || '';
        expect(
          allow === ORIGIN || allow === '*',
          `CORS allow-origin for ${url} = "${allow}" — expected ${ORIGIN} (or wildcard if bucket policy ever loosens)`,
        ).toBe(true);
      }
    } finally {
      await ctx.dispose();
    }
  });
});
