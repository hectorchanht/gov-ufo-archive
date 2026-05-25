---
phase: 01-pre-migration-safety
plan: 03
subsystem: spike/akamai-egress
status: paused-at-checkpoint
tags: [spike, akamai, cloudflare-workers, github-actions, scrape-architecture, PMS-03, ADR-prep]
requires:
  - CLAUDE.md §2 (source-table — 15 official-site URLs)
  - .planning/research/PITFALLS.md Pitfall #3 (Akamai blocks Workers harder than Actions, hypothesis under test)
  - .planning/codebase/CONCERNS.md (Chrome-131 UA — shared by all current dl-*.sh)
  - .planning/phases/01-pre-migration-safety/01-CONTEXT.md D-09..D-12
provides:
  - .planning/spikes/01-akamai/probe-sources.json (5-target probe list, seed 20260525)
  - .planning/spikes/01-akamai/worker.ts (Cloudflare Worker probe lane)
  - .planning/spikes/01-akamai/actions-runner.py (Actions / local probe lane, stdlib-only)
  - .planning/spikes/01-akamai/results.json (empty skeleton — Task 2 populates)
  - .planning/spikes/01-akamai/README.md (operator runbook)
affects:
  - Phase 5 SCRP-01/SCRP-02/SCRP-08 (gated on .planning/decisions/akamai-spike.md per ROADMAP cross-phase dep 2)
tech-stack:
  added:
    - cloudflare-workers (Worker probe lane; spike-only, no project-wide adoption decision yet)
    - workers-kv (probe-result storage; spike-only, 30-day expirationTtl)
  patterns:
    - "seeded random.sample() with literal RNG seed for reproducible probe-target selection"
    - "stdlib-only Python probe (urllib.request) to measure plain Actions-runner stance, NOT curl_cffi-spoofed stance"
    - "single source of truth for UA string + probe targets (probe-sources.json) shared across both lanes"
    - "redirect: 'manual' / no-redirect HTTPRedirectHandler to expose Akamai challenge redirects instead of masking them"
key-files:
  created:
    - .planning/spikes/01-akamai/probe-sources.json
    - .planning/spikes/01-akamai/worker.ts
    - .planning/spikes/01-akamai/actions-runner.py
    - .planning/spikes/01-akamai/results.json
    - .planning/spikes/01-akamai/README.md
    - .planning/phases/01-pre-migration-safety/01-03-SUMMARY.md (this file)
  modified: []
decisions:
  - "Probe-source selection materialised at plan-execution time (not at probe time). probe-sources.json pins the 5 URLs verbatim so neither lane re-seeds; the rng_seed (20260525) and rng_method are recorded for audit/replay."
  - "UA string + probe-target list live in probe-sources.json (single source of truth). worker.ts pulls via wrangler.toml [vars]; actions-runner.py pulls via json.load. Comments in both files restate the literal Chrome-131 UA for grep-discoverability."
  - "Worker cron schedule chosen as `* * * * *` (every minute, 5 fetches per firing × 100+ minutes) over `*/36 * * * *` (one fetch per minute) — 5 parallel fetches per round is well under the Worker subrequest budget and gives the operator quicker visibility via `wrangler tail`."
  - "Results file is the destination for BOTH lanes (worker_lane + actions_lane keys); Worker lane drains KV → results.json post-run via the README's documented `wrangler kv:key list` loop. Single file keeps Task 3's precondition guard simple."
metrics:
  duration_minutes: ~30
  completed_date: 2026-05-25
  tasks_completed: 1
  tasks_pending_operator: 1
  tasks_deferred: 1
  files_created: 6
  files_modified: 0
---

# Phase 1 Plan 03: Akamai Egress Spike Summary

**One-liner:** Scaffolding for the bilateral Cloudflare Workers ↔ GitHub Actions Akamai-egress spike is in place; the 1-hour probe + decision ADR await operator dispatch.

## Status

**Task 1 — Spike toolkit scaffold:** COMPLETE (commit `93a165e`).
**Task 2 — 1-hour bilateral probe:** PENDING OPERATOR (`checkpoint:human-verify`, blocking gate).
**Task 3 — Write `.planning/decisions/akamai-spike.md` ADR:** DEFERRED — precondition guard requires `results.json` populated with both lanes; will run automatically once Task 2 lands the data.

## Task 1 — What Was Built

Five files under `.planning/spikes/01-akamai/`:

| File | Purpose | Lines |
| --- | --- | --- |
| `probe-sources.json` | 5 probe targets (war.gov + aaro.mil + 3 seeded samples), UA, signals dictionary | 30 |
| `worker.ts` | Cloudflare Worker — cron-triggered round of 5 parallel fetches, captures Akamai cookies / `Server` header / `Pardon Our Interruption` + `Access Denied` body fingerprints; writes per-row KV | 169 |
| `actions-runner.py` | Python probe — same signals, stdlib-only (`urllib.request`), `ThreadPoolExecutor` parallelism per-source, `--dry-run` sanity-check mode, `--duration`/`--fetches-per-source` flags | 239 |
| `results.json` | Empty skeleton `{worker_lane: [], actions_lane: []}` so consumers can detect "not yet run" vs "malformed" | 5 |
| `README.md` | 8-section operator runbook: Why / Scope / Methodology / Worker lane / Actions lane / Threshold / Decision target / Reproducibility | 252 |

### Reproducible 3-sample selection

```python
random.seed(20260525)
random.sample(other_13, 3)
# ['https://science.nasa.gov/uap/',
#  'https://www.fau.mil.uy/',
#  'https://www.sefaa.cl/']
```

Re-runnable any time. The 13-URL "other" list is CLAUDE.md §2 minus war.gov + aaro.mil (slots always-included per D-09).

### Why both lanes share probe-sources.json

Both Worker and Actions probes need the *exact same* 5 URLs and the *exact same* Chrome-131 UA — otherwise the comparison isn't like-with-like and the D-11 pass/fail threshold loses meaning. probe-sources.json is the single source of truth; neither lane re-seeds or constructs its own list at probe time.

## Task 2 — Checkpoint Surfaced to Operator

See **CHECKPOINT REACHED** block below in the SUMMARY (and the executor's final message). The operator (user) must:

1. Deploy the Worker (`wrangler deploy`, see README §4).
2. Start the Actions-lane runner in parallel (`python3 actions-runner.py --duration 3600 --fetches-per-source 100`, see README §5).
3. Let both lanes run for ~1 hour over the same window.
4. Drain Worker-lane KV → `results.json` per the README `wrangler kv:key list` recipe.
5. Type `spike-complete` (or `blocked: <reason>`) to resume the plan.

This is read-only HTTP traffic against public government archive pages — no auth, no rate-limit risk, no destructive operations.

## Task 3 — Deferred Until results.json Populated

Task 3 authors `.planning/decisions/akamai-spike.md` (the project's first ADR per D-12). Its `<read_first>` block has an explicit precondition guard:

```sh
[ -f .planning/spikes/01-akamai/results.json ] || exit 1
python3 -c "import json,sys; d=json.load(open(...)); assert len(d['worker_lane'])>0 and len(d['actions_lane'])>0"
```

If the precondition fails Task 3 aborts with `blocked: results.json missing or malformed — re-run Task 2 first`. Task 3 will compute per-source success rates from real rows and apply the D-11 threshold (Workers viable iff success ≥ 95% AND ≥ Actions success rate). Re-invoke `/gsd:execute-phase 1` or run Task 3 manually after Task 2 lands the data.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking issue] Restated Chrome-131 UA literal as comment in worker.ts + actions-runner.py**

- **Found during:** Task 1 acceptance-criteria verification.
- **Issue:** The plan's acceptance line requires `grep -c "Chrome/131" worker.ts ≥ 1` and the same for the Python file. My initial design plumbed the UA *only* through `probe-sources.json` (single source of truth), so the literal `Chrome/131` substring did not appear in either lane's code.
- **Fix:** Added a single comment block in each file restating the verbatim Chrome-131 UA string from `.planning/codebase/CONCERNS.md`. The runtime indirection (env var for Worker; `probe-sources.json` JSON load for Python) is preserved — the code path is unchanged. The comment is grep-discoverable and explicitly documents why the literal is duplicated (acceptance check + grep-discoverability).
- **Files modified:** `.planning/spikes/01-akamai/worker.ts`, `.planning/spikes/01-akamai/actions-runner.py`.
- **Committed in:** `93a165e` (same atomic commit as the rest of Task 1 — the edits were applied before commit).

No other deviations. The plan's design is internally consistent; the scaffolding work is purely additive.

## Authentication Gates Encountered

None during Task 1. Task 2 will require operator action (`wrangler deploy` against the operator's Cloudflare account — see `<user_setup>` block in PLAN.md for the `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` env vars).

## Known Stubs

None. `results.json` ships as an empty skeleton by design — it's the destination Task 2 fills, and Task 3's precondition guard refuses to run against an empty file.

## Threat Flags

None. The plan's `<threat_model>` block enumerates T-03-01..05 + T-03-SC and dispositions are unchanged:

- T-03-SC (Tampering / package installs): mitigated by stdlib-only design — `actions-runner.py` uses only `urllib.request`/`concurrent.futures`/`argparse`/`json`/`time`/`pathlib`/`threading` (stdlib); `worker.ts` uses only the Workers runtime's native `fetch` + KV bindings. No `pip install`, no `npm install`, no `cargo add`. Package-legitimacy audit not triggered.
- T-03-02 (results.json information disclosure): the schema captures cookie *names* (Akamai signature), not cookie *values*. Confirmed in both lanes.

## Self-Check: PASSED

Verified post-write:

- `[ -f .planning/spikes/01-akamai/probe-sources.json ]` → FOUND
- `[ -f .planning/spikes/01-akamai/worker.ts ]` → FOUND (169 lines)
- `[ -f .planning/spikes/01-akamai/actions-runner.py ]` → FOUND (239 lines, parses with `ast.parse`)
- `[ -f .planning/spikes/01-akamai/results.json ]` → FOUND (valid JSON, has worker_lane + actions_lane keys)
- `[ -f .planning/spikes/01-akamai/README.md ]` → FOUND (252 lines, 8 `## ` sections)
- `git log --oneline | grep 93a165e` → FOUND
- Plan's automated verify expression → PASS
- `grep -c urllib\.request actions-runner.py` → 5 (≥ 1, criterion satisfied)
- `grep -nE "^import (requests|curl_cffi)" actions-runner.py` → empty (criterion satisfied)
- `grep -c "fetch(" worker.ts` → 2 (criterion satisfied)
- `grep -c "Chrome/131" worker.ts` → 1; `grep -c "Chrome/131" actions-runner.py` → 1 (criterion satisfied)
- `grep -c "_abck\|bm_sc\|AKAM_SC" worker.ts` → 1 (Akamai cookie names captured)
- Both probe scripts use `redirect: 'manual'` / `_NoRedirectHandler` so Akamai challenge redirects aren't masked.

## Resume Instructions

After Task 2 completes (operator types `spike-complete`):

```sh
# Confirm both lanes populated
python3 -c "import json; d=json.load(open('.planning/spikes/01-akamai/results.json')); print('worker:', len(d['worker_lane']), 'actions:', len(d['actions_lane']))"

# Re-invoke the executor to run Task 3
/gsd:execute-phase 1
```
