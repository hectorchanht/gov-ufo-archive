// Playwright config — Phase 2 INF-04. Chromium-only per D-15. 0.1% pixel
// threshold per D-16. baseURL is the CF Pages preview URL — CI passes
// PREVIEW_URL env var per D-31; local default is the production-branch URL.
//
// Baselines live at tests/visual-baselines/{archive}-{viewport}.png; the
// snapshotPathTemplate override below makes Playwright resolve to that path
// directly (instead of the default *.spec.ts-snapshots/ subfolder).
//
// See:
//  - .planning/phases/02-infrastructure-ci-scaffolding/02-CONTEXT.md
//    decisions D-12 (capture against live realufo.org), D-13 (60 PNGs raw),
//    D-14 (viewport list), D-15 (chromium-only), D-16 (0.1% threshold),
//    D-17 (operator-only regen).
//  - tests/visual-baselines/README.md for the D-17 operator runbook.

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.ts',
  fullyParallel: true,
  workers: 4,
  reporter: 'list',
  use: {
    baseURL: process.env.PREVIEW_URL || 'https://realufo.pages.dev',
    trace: 'off',
    screenshot: 'off',
    video: 'off',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.001,
      threshold: 0.1,
      animations: 'disabled',
    },
  },
  snapshotPathTemplate: 'tests/visual-baselines/{arg}{ext}',
});
