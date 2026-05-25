# Plan 02-07 — Lighthouse-CI Mobile Budgets (SOFT per D-28)

**Phase:** 02-infrastructure-ci-scaffolding
**Plan:** 02-07
**Requirements:** INF-08
**Status:** Complete
**Date:** 2026-05-25

---

## Tasks

| # | Task | Commit | Status |
|---|------|--------|--------|
| 1 | Install `@lhci/cli@0.14.0` exact + write `.lighthouserc.cf.json` (mobile + 4× CPU throttle + D-27 budgets at `warn` level) | `aaa2899` | Done |
| 2 | `scripts/verify-lighthouse-budgets.py` — stdlib-only parser, exits 0 always (soft per D-28) | `4880eb8` | Done |

## Artifacts

- `.lighthouserc.cf.json` — Lighthouse-CI config (mobile preset, `cpuSlowdownMultiplier: 4`, asserts LCP ≤ 2500 ms + total-byte-weight ≤ 512000 B at `warn` level)
- `scripts/verify-lighthouse-budgets.py` (297 lines, stdlib-only, exit 0 always for Phase 2/3 soft mode; `--hard-fail` flag reserved for Phase 4 close)
- `package.json` + `pnpm-lock.yaml` extended with `@lhci/cli@0.14.0` (Playwright entries from 02-03 preserved)

## D-* Compliance

- **D-26:** Mobile profile + 4× CPU throttle — `.lighthouserc.cf.json` `formFactor: 'mobile'` + `cpuSlowdownMultiplier: 4`
- **D-27:** LCP ≤ 2.5 s + transfer ≤ 500 KB — asserted as `largest-contentful-paint` and `total-byte-weight`
- **D-28:** SOFT for Phase 2/3 — assertions at `warn` level (not `error`), `verify-lighthouse-budgets.py` exits 0 unconditionally; CI job in 02-08 wires `continue-on-error: true`. Hard-fail switch deferred to Phase 4 close.

## Notes

- Plan 02-08 wires LHCI into `.github/workflows/quality-gates.yml` `lighthouse` job. The `__PREVIEW_URL__` placeholder in `.lighthouserc.cf.json` is sed-substituted at CI run-time.
- Smoke test against live realufo.org skipped (Task 2 was killed mid-run by previous session). LHCI behavior verified via config inspection + script unit logic. Baseline LCP/transfer-byte values per archive will be captured during first CI run on Phase 3 SSG preview.

## Deviations

- One: Previous executor session was killed mid-Task-2 before `scripts/verify-lighthouse-budgets.py` was committed. This SUMMARY commit completes the plan; orchestrator merges to main.

---

*Plan 02-07 closes INF-08. Wave 3 complete (02-06 + 02-07). Next: Wave 4 (02-08 wires all 5 quality gates into `quality-gates.yml`).*
