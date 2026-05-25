---
phase: 02-infrastructure-ci-scaffolding
plan: 03
subsystem: visual-regression
tags: [playwright, visual-regression, baselines, chromium, mobile-first, ssg-migration-branch]

# Dependency graph
requires:
  - phase: 02-infrastructure-ci-scaffolding
    provides: "02-01 — package.json + .nvmrc skeleton (extended in place with pnpm-managed Playwright dev deps; no regeneration per 02-01-SUMMARY follow-up note)"
  - phase: 02-infrastructure-ci-scaffolding
    provides: "02-CONTEXT.md decisions D-12 (capture live realufo.org), D-13 (60 raw PNGs), D-14 (4 viewports), D-15 (chromium-only), D-16 (0.1% threshold), D-17 (operator-only regen), D-38 (no SSG code)"
provides:
  - "tests/playwright.config.ts — chromium-only Playwright config; 0.001 maxDiffPixelRatio (D-16); PREVIEW_URL env override (D-31); snapshotPathTemplate resolves to tests/visual-baselines/"
  - "scripts/capture-baselines.py — operator-only capture script; argparse CLI (--archive / --viewport / --check / --base-url / --full-page); exit codes 0/1/2 mirror snapshot-urls.py; lazy `playwright` import so --help and --check work without venv"
  - "60 baseline PNGs at tests/visual-baselines/{slug}-{w}.png (15 archives × 4 viewports per D-13/D-14), captured 2026-05-25 from live https://realufo.org GitHub Pages production origin"
  - "tests/visual-regression.spec.ts — 60 toHaveScreenshot tests against process.env.PREVIEW_URL with 0.1% threshold (consumed by Plan 02-08 quality-gates.yml)"
  - "tests/visual-baselines/README.md — D-17 operator-only-regen invariant + explicit recapture procedure + venv setup (Python 3.11 venv required because greenlet wheel-build fails on Python 3.14)"
  - "Verified 60 / 60 visual-regression tests pass against live realufo.org locally in 37 s (sanity check; CI gate wires this in Plan 02-08)"
affects: [02-06-tone-jsoff, 02-08-quality-gates, 03-astro-install, 04-content-migration, 06-cutover]

# Tech tracking
tech-stack:
  added:
    - "@playwright/test 1.49.0 (exact pin per CONVENTIONS.md anti-drift; no caret/tilde)"
    - "playwright 1.49.0 (browser-driver runtime; same exact pin)"
    - "Playwright chromium browser binary (revision 1148, cached at ~/Library/Caches/ms-playwright/chromium-1148)"
  patterns:
    - "Exact-pin dev deps (`pnpm add -D --save-exact`) — matches Astro `~5.x.y` posture from research/STACK.md; mitigates T-02-10 supply-chain tampering"
    - "Operator-only capture script with lazy third-party import — argparse + stdlib for --check and --help; playwright module imported only inside run_capture() so the script is usable without venv setup for verification"
    - "Filename convention `{slug}-{w}.png` byte-identical between Python capture script and TypeScript spec — drift between the two silently breaks the gate; SOURCE-OF-TRUTH lists live in both files and must change together"
    - "Playwright config snapshotPathTemplate override resolves to repo-root tests/visual-baselines/ (path relative to testDir = config file's directory)"
    - "Playwright test-results/ + playwright-report/ gitignored; only tests/visual-baselines/ is tracked (clean separation between operator-frozen baselines and ephemeral test runner output)"

key-files:
  created:
    - tests/playwright.config.ts
    - tests/visual-regression.spec.ts
    - tests/visual-baselines/.gitkeep
    - tests/visual-baselines/README.md
    - scripts/capture-baselines.py
    - pnpm-lock.yaml
    - "60 × tests/visual-baselines/{slug}-{w}.png"
  modified:
    - package.json
    - .gitignore
  remote-side:
    - "tests/visual-baselines/ committed in this worktree branch — fast-forwards to ssg-migration on orchestrator merge-back (parallel-executor protocol; no direct push from worktree)"

key-decisions:
  - "Operator runs capture-baselines.py from a Python 3.11 venv, not via project pnpm. Rationale: the Python `playwright` bindings depend on greenlet, whose wheel-build fails on Python 3.14 (current Homebrew default). Documented in tests/visual-baselines/README.md `## Runtime setup`. The TypeScript Playwright dev-dep (pnpm) is unaffected; only the capture-script Python path needs the venv. This isolates the venv requirement to operator workflows (the CI gate never runs capture-baselines.py per D-17)."
  - "Bumped packageManager pin pnpm@9 → pnpm@9.15.9 (full semver) as a Rule 3 blocking fix. Corepack 0.34 (shipping with Node 22.22.0) rejects the floating `pnpm@9` declaration with `Invalid package manager specification ... expected a semver version`. Pinned to the latest 9.x at execution time (9.15.9). Maintains 02-01's intent of pinning pnpm 9.x — just at the granularity Corepack demands."
  - "Two Playwright config fixes shipped in Task 2 commit (not Task 1) because they were discovered by running the spec, not by static analysis: (a) testDir '.' (was './tests' — resolved to tests/tests/); (b) snapshotPathTemplate 'visual-baselines/{arg}{ext}' (was 'tests/visual-baselines/...' — resolved to tests/tests/visual-baselines/). Both are Rule 1 bugs the plan-author couldn't have caught without execution; the fixed config is what 02-06 + 02-08 will inherit."
  - "PNG total is 14 MB, not the 6 MB the plan estimated. Cause: device.scaleFactor=2 from Playwright's `devices['Desktop Chrome']` (Retina capture); raw above-the-fold densities. No PNG exceeds 1 MB (verified by `find -size +1M`). Acceptable: well within git tracking budget; matches D-13 'raw PNG, not LFS, ~50-200 KB each' band on the low end (NARA, Canada, NZ) but exceeds on dense pages (wargov-1440 = 804 KB; NASA-1440 = 711 KB; AARO-1440 = 558 KB) — these are the archives with hero-carousel imagery + headlines strip above the fold."
  - "Added test-results/ and playwright-report/ to .gitignore (Rule 2 — Playwright generates these on every run). The fenced 'SSG migration (Phase 2+)' section in .gitignore gets two new entries with an explanatory comment distinguishing them from tests/visual-baselines/ (which IS tracked)."

requirements-completed: [INF-04]

# Metrics
duration: ~14min
completed: 2026-05-25T16:14:23+08:00
---

# Phase 02 Plan 03: Playwright + 60-PNG Baseline Capture Summary

**Stood up the visual-regression gate that locks the current production
pixels (15 archives × 4 viewports = 60 PNGs from live
`https://realufo.org`) as the regression target every Phase 3-5 CF Pages
preview must match within 0.1 %. INF-04 fully satisfied. D-17 invariant
codified.**

## Performance

- **Duration:** ~14 min (Task 1 ~5 min including venv-setup detour; Task 2 ~9 min including 60-PNG capture + 60-test sanity-run)
- **Started:** 2026-05-25T16:00:00Z (worktree spawn)
- **Completed:** 2026-05-25T16:14:23+08:00 (Task 2 commit `3533b5c`)
- **Tasks committed:** 2 of 2

## Accomplishments

### Task 1 — Playwright install + config + capture script + README (commit `d161ac4`)

- **Pinned `@playwright/test@1.49.0` + `playwright@1.49.0`** as exact dev deps via `pnpm add -D --save-exact`. Generated `pnpm-lock.yaml` (sha256: `cb47774...`). package.json shows literal `"1.49.0"` strings — no caret/tilde drift, satisfying T-02-10 supply-chain mitigation.
- **Chromium browser binary already present in `~/Library/Caches/ms-playwright/chromium-1148`** from prior Playwright work; `pnpm exec playwright install chromium` was a no-op cache hit.
- **`tests/playwright.config.ts`** (50 lines):
  - `testDir: '.'` (config-relative; resolves to repo `tests/`)
  - `testMatch: '**/*.spec.ts'`
  - `fullyParallel: true; workers: 4; reporter: 'list'`
  - `use.baseURL: process.env.PREVIEW_URL || 'https://realufo.pages.dev'` (D-31)
  - `projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }]` (D-15 chromium-only)
  - `expect.toHaveScreenshot: { maxDiffPixelRatio: 0.001, threshold: 0.1, animations: 'disabled' }` (D-16 0.1%)
  - `snapshotPathTemplate: 'visual-baselines/{arg}{ext}'` (testDir-relative)
- **`scripts/capture-baselines.py`** (165 lines, executable):
  - Module docstring documents D-12 / D-13 / D-17 invariants
  - Stdlib (`argparse`, `os`, `sys`, `pathlib`); `playwright.sync_api` imported lazily inside `run_capture()` so `--check` and `--help` work without venv
  - `ARCHIVES`: 15 (slug, path) tuples — canonical CLAUDE.md §2 list
  - `VIEWPORTS`: `[(360, 800), (768, 1024), (1024, 768), (1440, 900)]` — 360 first per CLAUDE.md §8 mobile-first
  - CLI: `--archive`, `--viewport`, `--check`, `--base-url` (default `https://realufo.org`), `--full-page` (default false)
  - Exit codes: 0 success, 1 gap/failure, 2 missing dep — mirrors `scripts/snapshot-urls.py`
- **`tests/visual-baselines/README.md`** (~120 lines):
  - `## D-17 invariant — NEVER auto-regen` section with the 5-step explicit recapture procedure
  - `## Capture source` cites D-12 verbatim
  - `## Runtime setup` documents the Python 3.11 venv requirement (greenlet wheel issue on 3.14)
  - Verification commands at the bottom

### Task 2 — 60 PNG capture + spec + path-resolution fixes (commit `3533b5c`)

- **Captured 60 PNGs from live https://realufo.org** via Playwright headless chromium driven from `scripts/capture-baselines.py` running in `/tmp/pw-venv` (Python 3.11 venv with `playwright==1.49.0`). Capture timestamp: 2026-05-25 16:08-16:12 UTC.
- **Per-archive byte sizes (above-the-fold, JS-enabled, device scaleFactor=2):**
  | Archive | 360 | 768 | 1024 | 1440 |
  | --- | --- | --- | --- | --- |
  | wargov | 237 KB | 590 KB | 514 KB | 804 KB |
  | aaro | 225 KB | 376 KB | 371 KB | 558 KB |
  | nasa | 163 KB | 544 KB | 447 KB | 711 KB |
  | nara | 116 KB | 221 KB | 196 KB | 243 KB |
  | geipan | 97 KB | 160 KB | 163 KB | 184 KB |
  | uk | 135 KB | 217 KB | 198 KB | 266 KB |
  | brazil | 123 KB | 209 KB | 199 KB | 251 KB |
  | chile | 135 KB | 224 KB | 205 KB | 276 KB |
  | argentina | 127 KB | 214 KB | 204 KB | 265 KB |
  | canada | 113 KB | 183 KB | 165 KB | 208 KB |
  | italy | 124 KB | 208 KB | 193 KB | 257 KB |
  | nz | 108 KB | 179 KB | 167 KB | 209 KB |
  | peru | 115 KB | 189 KB | 183 KB | 236 KB |
  | spain | 126 KB | 209 KB | 196 KB | 269 KB |
  | uruguay | 135 KB | 231 KB | 220 KB | 283 KB |
  Total: **14 MB across 60 PNGs**. No PNG > 1 MB (verified by `find -size +1M`).
- **`tests/visual-regression.spec.ts`** (59 lines):
  - `test.describe.parallel('visual regression — 15 archives × 4 viewports')` block
  - Iterates ARCHIVES × VIEWPORTS → 60 tests
  - Each: `setViewportSize → goto(path, {waitUntil: 'networkidle'}) → waitForTimeout(500) → toHaveScreenshot(${slug}-${w}.png)`
  - The 500 ms settle matches the capture script's `wait_for_timeout(500)` (CLAUDE.md §3 carousel autoplay 6500 ms; 500 ms keeps slide 1 stable)
- **Sanity-test run against live realufo.org** (same source the baselines were captured from): **60 / 60 passed in 37 s** with the production-pinned baseURL `https://realufo.org`. This proves the gate evaluates correctly end-to-end before Plan 02-08 wires it into CI.

## Task Commits

Worktree branch `worktree-agent-acf902b67862ba0d5` (forked from `main` at `76c933f`):

1. **Task 1 — install Playwright + capture-baselines.py + visual-baselines/ scaffold** — `d161ac4` (infra)
2. **Task 2 — capture 60 baselines from live realufo.org + visual-regression spec** — `3533b5c` (infra)

Plan-metadata commit handled by orchestrator on merge-back per parallel-executor protocol.

## Files Created/Modified

- **`package.json`** (MODIFIED, +3 lines) — Added `@playwright/test`: `1.49.0` and `playwright`: `1.49.0` to `devDependencies`; bumped `packageManager` to `pnpm@9.15.9` (Rule 3 fix for Corepack 0.34 strict semver requirement).
- **`pnpm-lock.yaml`** (NEW, lockfile-v9, sha256 `cb47774...`) — Reproducible install for the 2 dev deps + 2 transitives (4 packages total).
- **`tests/playwright.config.ts`** (NEW, 50 lines) — Chromium-only config; 0.001 maxDiffPixelRatio; PREVIEW_URL env override; `testDir: '.'` (config-relative); `snapshotPathTemplate: 'visual-baselines/{arg}{ext}'`.
- **`tests/visual-regression.spec.ts`** (NEW, 59 lines) — 60 toHaveScreenshot tests. SOURCE-OF-TRUTH ARCHIVES + VIEWPORTS lists byte-identical to scripts/capture-baselines.py.
- **`tests/visual-baselines/.gitkeep`** (NEW, 0 bytes) — Tracked-directory placeholder; technically redundant after the 60 PNGs land but preserved for symbolic consistency.
- **`tests/visual-baselines/README.md`** (NEW, ~120 lines) — D-17 operator-only-regen runbook.
- **`tests/visual-baselines/*.png`** (NEW × 60) — 15 archives × 4 viewports = 60 PNGs. 14 MB total. Captured from `https://realufo.org` on 2026-05-25.
- **`scripts/capture-baselines.py`** (NEW, 165 lines, executable) — Operator capture script.
- **`.gitignore`** (MODIFIED, +4 lines) — Added `test-results/` and `playwright-report/` with explanatory comment distinguishing them from the tracked `tests/visual-baselines/` directory.

## Decisions Made

- **Python 3.11 venv for capture-script runtime** — Documented at `tests/visual-baselines/README.md` `## Runtime setup`. The script's `--check` and `--help` paths use stdlib only so they work without the venv; only the actual capture (`run_capture`) requires playwright + greenlet. Setting up the venv is the operator's one-time cost; future recaptures reuse it.
- **packageManager pin to full semver `pnpm@9.15.9`** — Forced by Corepack 0.34. The 02-01 plan committed `pnpm@9` floating; Corepack rejected it at the very first `pnpm` invocation. Pinned to latest 9.x (9.15.9) at execution time; maintains 02-01's intent of "pnpm 9.x" at the granularity Corepack requires.
- **testDir = `'.'` not `'./tests'`** — In Playwright, `testDir` is resolved relative to the config file's directory. Since the config lives at `tests/playwright.config.ts`, `'./tests'` resolved to `tests/tests/` (zero specs found). Inline comment documents this for the next reader.
- **snapshotPathTemplate = `'visual-baselines/{arg}{ext}'` not `'tests/visual-baselines/...'`** — Same reason: testDir-relative resolution. Inline comment documents.
- **Above-the-fold capture only (no `--full-page`)** — D-13 size budget (50-200 KB target per PNG). With `--full-page` enabled, wargov-1440 would exceed 3 MB (3334-record geipan inline list). Above-the-fold gives 14 MB total — well within git tracking comfort.
- **Two atomic commits, not one** — Task 1 ships the infrastructure (config + script + README + lockfile); Task 2 ships the artifacts (60 PNGs + spec) PLUS the two config bug-fixes (Rule 1) discovered during the test run. Splitting clarifies what's pre-capture infra vs. capture-output. Each commit independently verifiable.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking issue] Corepack 0.34 rejects floating `pnpm@9` packageManager spec.**
- **Found during:** First `pnpm --version` invocation (before any Playwright work).
- **Issue:** `Invalid package manager specification in package.json (pnpm@9); expected a semver version`. Corepack 0.34 (Node 22.22.0 default) enforces strict full-semver pins.
- **Resolution:** Updated `package.json` `packageManager` to `pnpm@9.15.9` (latest 9.x at execution time per `npm view pnpm@9 version`).
- **Files modified:** `package.json` (line 8)
- **Commit:** `d161ac4` (Task 1)

**2. [Rule 1 — Bug] `testDir: './tests'` finds zero specs.**
- **Found during:** First `playwright test --list` run.
- **Issue:** `testDir` is resolved relative to the config file's directory. The config lives at `tests/playwright.config.ts`, so `'./tests'` becomes `tests/tests/` — wrong target.
- **Resolution:** Changed to `testDir: '.'` with an inline comment documenting the resolution rule.
- **Files modified:** `tests/playwright.config.ts`
- **Commit:** `3533b5c` (Task 2 — discovered after Task 1 commit by running the spec)

**3. [Rule 1 — Bug] `snapshotPathTemplate: 'tests/visual-baselines/{arg}{ext}'` double-prefixes the path.**
- **Found during:** First passing-test run failed with `A snapshot doesn't exist at .../tests/tests/visual-baselines/argentina-360.png`.
- **Issue:** Same root cause as bug #2 — snapshotPathTemplate is testDir-relative. The path `'tests/visual-baselines/...'` was being interpreted as `tests/` (testDir) + `tests/visual-baselines/...` = `tests/tests/visual-baselines/`.
- **Resolution:** Changed to `'visual-baselines/{arg}{ext}'` (testDir-relative). Confirmed by passing local sanity-test (60 / 60).
- **Files modified:** `tests/playwright.config.ts`
- **Commit:** `3533b5c` (Task 2)

**4. [Rule 2 — Missing critical functionality] `test-results/` and `playwright-report/` not gitignored.**
- **Found during:** `git status` after sanity-test run produced an untracked `test-results/` directory with diff PNGs.
- **Issue:** Playwright always writes test runner output (traces, diff PNGs, video on failure) to these dirs. Without gitignore, a developer accidentally `git add .` would commit the diff PNGs and pollute the repo.
- **Resolution:** Added both to the SSG-migration section of `.gitignore` with an inline comment distinguishing them from `tests/visual-baselines/` (tracked).
- **Files modified:** `.gitignore`
- **Commit:** `3533b5c` (Task 2)

### Skipped optional verifications

- **Pushed-to-remote step.** Plan Task 1 step 5 + Task 2 step 5 specify `git push origin ssg-migration`. Skipped because parallel-executor protocol: worktree branches are merged back to `ssg-migration` by the orchestrator, not pushed directly from the worktree. The orchestrator handles the fast-forward + remote push after all parallel plans in this wave finish.

## Issues Encountered

- **Worktree branched from stale base (`915157a`) instead of current `main` (`76c933f`).** Re-dispatch instruction from orchestrator confirmed this. Resolved with `git reset --hard main` at worktree-startup (no executor commits unique to the stale branch). After reset, worktree HEAD = `76c933f` = current main HEAD; all subsequent work forks from there.
- **Python 3.14 greenlet wheel-build failure.** First venv attempt with `/usr/bin/python3 -m venv` (Python 3.14.5) failed at `pip install playwright` with `command '/usr/bin/clang++' failed with exit code 1` during greenlet compile. Worked around by creating venv with `python3.11` (Homebrew). Documented in tests/visual-baselines/README.md as the operator setup path.
- **Initial test run wrote a stray `tests/tests/visual-baselines/argentina-360.png`** before the snapshotPathTemplate fix landed. Cleaned with `rm -rf tests/tests` before committing Task 2.

## Known Stubs

None. All 60 baselines are real captures from live realufo.org. The spec compares against them with 0.1% threshold. The capture script's `--check` mode confirms 60 / 60 are present and non-empty.

## Threat Flags

No new threat surface beyond the plan's `<threat_model>`:
- **T-02-09 (Auto-regen of baselines).** mitigated — D-17 documented in tests/visual-baselines/README.md; `grep -r capture-baselines .github/workflows/` returns empty (verified).
- **T-02-10 (Playwright supply chain).** mitigated — exact pin `1.49.0` (no caret), `pnpm-lock.yaml` committed for reproducible installs. Playwright is a Microsoft-owned legitimate npm package (HIGH-confidence per research/STACK.md).
- **T-02-11 (Baseline PNGs leak authenticated content).** accepted — capture script visits public anonymous archive pages only; no auth/session. Public-domain archive content (CLAUDE.md §9).
- **T-02-SC (Playwright + chromium binary).** mitigated — legitimate Microsoft package, no package-legitimacy checkpoint needed.

## Verification (acceptance criteria from plan §verification)

All 6 plan-verification commands passed:

1. ✓ `pnpm list @playwright/test` shows version `1.49.0` (exact pin)
2. ✓ `find tests/visual-baselines -name '*.png' | wc -l` returns 60
3. ✓ `python3 scripts/capture-baselines.py --check` exits 0 with `60 / 60 baselines present`
4. ✓ `PREVIEW_URL=https://realufo.org pnpm exec playwright test --config=tests/playwright.config.ts` reports 60 passed (37.1 s, parallel)
5. ✓ `git log --oneline -- tests/visual-baselines/` shows `3533b5c` + `d161ac4` (executor-authored, not CI)
6. ✓ `grep -r "tests/visual-baselines\|capture-baselines" .github/workflows/` returns empty (no workflow invokes the script — D-17 honored)

Plus Task 1 + Task 2 automated-verify blocks: 15 / 15 checks passed.

## Notes for downstream plans

- **02-06 (tone-colour + JS-off specs).** Playwright config, chromium binary, and pnpm-lock.yaml already in place. Just `import { test, expect } from '@playwright/test'`; reuse `tests/playwright.config.ts` (no new config needed). Add `tests/tone-colours.spec.ts` and `tests/js-off.spec.ts` alongside `tests/visual-regression.spec.ts`.
- **02-08 (quality-gates.yml).** The `visual-regression` job runs `pnpm exec playwright test tests/visual-regression.spec.ts --config=tests/playwright.config.ts` with `PREVIEW_URL` populated from the PR's `deployment_status` event payload (CF Pages preview URL). The 0.1% threshold + D-17 freeze mean any PR that drifts >0.1% from the captured 2026-05-25 baseline hard-fails until the operator explicitly regen's. CRITICAL: 02-08 MUST NOT invoke `scripts/capture-baselines.py` — only `playwright test` against the existing PNGs.
- **03-astro-install** + **04-content-migration**: every Astro template change will be evaluated against these baselines. Any intentional visual change requires the explicit-recapture procedure documented in `tests/visual-baselines/README.md`.

## Open questions

- **Will the 14 MB tests/visual-baselines/ inflate git clone times noticeably?** 14 MB is below the threshold where LFS becomes worthwhile (typically >100 MB). At Phase 2 the cost is one-time (60 PNG initial commit). The recapture cadence is driven by intentional visual changes, not regular development churn.
- **Should we run cross-browser (Firefox + WebKit) in a follow-up phase?** D-15 defers to Phase 4 if Chromium-only proves insufficient. Open. Will revisit if Phase 3 SSG output produces engine-specific rendering bugs.

## Self-Check: PASSED

- ✓ `tests/playwright.config.ts` exists; contains `maxDiffPixelRatio: 0.001`, `chromium`, `process.env.PREVIEW_URL`, `testDir: '.'`, `snapshotPathTemplate: 'visual-baselines/{arg}{ext}'`
- ✓ `scripts/capture-baselines.py` exists, executable (mode 755), contains `DEFAULT_BASE.*realufo.org`, `ARCHIVES`, `(360, 800)`, `(1440, 900)`
- ✓ `tests/visual-baselines/README.md` exists; contains `D-17`, `NEVER auto-regen`
- ✓ `tests/visual-regression.spec.ts` exists; contains `toHaveScreenshot`, `VIEWPORTS`, 15 archive tuples
- ✓ `tests/visual-baselines/` contains exactly 60 PNG files; none zero-byte; none > 1 MB
- ✓ `package.json` `devDependencies['@playwright/test'] === '1.49.0'` (string-equal, no caret)
- ✓ `pnpm-lock.yaml` exists (lockfile-v9, sha256 `cb47774...`)
- ✓ Commits `d161ac4` + `3533b5c` present in `git log` on `worktree-agent-acf902b67862ba0d5`
- ✓ `git log --oneline -- tests/visual-baselines/` returns the 2 executor commits (not CI-generated)
- ✓ `grep -r capture-baselines .github/workflows/` empty (D-17 enforced)

---
*Phase: 02-infrastructure-ci-scaffolding*
*Plan: 03 — Playwright install + 60-PNG baseline capture*
*Completed: 2026-05-25T16:14:23+08:00*
