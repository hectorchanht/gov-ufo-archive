---
phase: 05-scrape-automation
plan: "02"
subsystem: scrape-automation
status: blocked-on-operator
tags: [scrape, workers, akamai, spike, kv, blocked-on-operator]
requires:
  - workers-paid plan active (`.planning/decisions/workers-paid.md`)
  - operator has `wrangler` CLI installed locally + can log in to realufo CF account `f1868a071996e836eae6da2b65f37929`
provides:
  - `workers/akamai-spike/` scaffold (4 files; Task 1 complete)
  - operator gate for spike deploy + invoke + result capture (Task 2 pending)
  - `.planning/decisions/akamai-spike.md` ADR (Task 3 — blocked on Task 2 data)
affects:
  - Plan 05-03 (Workers cron skeleton — depends on this plan; BLOCKED until Tasks 2+3 complete)
  - Plan 05-04 (per-archive scrape lanes — imports `AKAMAI_BLOCKED_SOURCES` constant from Task 3's ADR)
  - Plan 05-05 (GH Actions `curl_cffi` runner — consumes same constant)
tech-stack:
  added:
    - "@cloudflare/workers-types ^4.20260528.1"
    - "wrangler ^4.95.0"
    - "typescript ~5"
  patterns:
    - "Throwaway spike Worker isolated under `workers/akamai-spike/` with its own package.json (distinct from root realufo package)"
    - "Parallel fetch of 4 sources inside a single Worker invocation (latency data for Plan 05-04)"
    - "60s edge `Cache-Control` on Worker response + 24h KV TTL — absorbs operator re-polls without re-charging upstream fetches (T-05-02-03 mitigation)"
key-files:
  created:
    - workers/akamai-spike/wrangler.toml
    - workers/akamai-spike/src/index.ts
    - workers/akamai-spike/package.json
    - workers/akamai-spike/.gitignore
  modified: []
decisions:
  - "Spike Worker name `realufo-akamai-spike` (throwaway; deleted after ADR locks)"
  - "Realistic Chrome 124 UA used so probe measures the same blocking surface a production cron Worker would see"
  - "4 fetches run in parallel via `Promise.all` (settled with try/catch per source so one failure does not poison the others)"
  - "KV binding `AKAMAI_SPIKE` with placeholder id; operator pastes real id post-`wrangler kv namespace create`"
metrics:
  duration_partial: "~10 min (Task 1 only)"
  completed_partial: "2026-05-28"
  tasks_complete: 1
  tasks_total: 3
  tasks_blocked: 2
---

# Phase 5 Plan 05-02: Akamai Spike Worker Summary (PARTIAL — BLOCKED ON OPERATOR)

**Status:** `blocked-on-operator` — Task 1 (scaffold) complete; Task 2 (operator deploy + invoke) and Task 3 (ADR transcription) require operator action against the realufo Cloudflare account.

One-liner: Scaffolded a throwaway one-shot Worker at `workers/akamai-spike/` that probes the 4 active source origins (war.gov / aaro.mil / science.nasa.gov / catalog.archives.gov) in parallel and persists status + headers to KV; deploy + invoke are operator-only steps pending Wrangler login.

## Wave status

**Wave 1 (this plan):** PARTIAL — 1/3 tasks done.
**Wave 2 (Plan 05-03 — Workers cron skeleton):** BLOCKED. 05-03 `depends_on` 05-02; the cron skeleton cannot proceed until `.planning/decisions/akamai-spike.md` locks the `AKAMAI_BLOCKED_SOURCES` constant.

## Task 1 — `workers/akamai-spike/` scaffold (DONE)

Status: **complete**. Commit `90f1418`.

| File | Lines | Notes |
| --- | --- | --- |
| `workers/akamai-spike/wrangler.toml` | 22 | `name = "realufo-akamai-spike"`; `compatibility_date = "2026-05-28"`; `[[kv_namespaces]] binding = "AKAMAI_SPIKE"` with placeholder id pending operator. |
| `workers/akamai-spike/src/index.ts` | 108 | Default `fetch` handler. Declares the 4-source `SOURCES` constant, realistic Chrome 124 `UA` constant, typed `Env`/`ProbeResult` interfaces. Runs `Promise.all(SOURCES.map(probe))` (parallel); each probe captures `status`, `server`, `x-akamai-transformed`, `cf-ray`, `latencyMs` (and `errorMsg` if `fetch` throws). Writes the run payload JSON to `AKAMAI_SPIKE.put('last-spike-result', ..., { expirationTtl: 86400 })`. Returns same JSON with `Cache-Control: public, max-age=60`. |
| `workers/akamai-spike/package.json` | 16 | `wrangler ^4.95.0`, `@cloudflare/workers-types ^4.20260528.1`, `typescript ~5`. Scripts: `dev`/`deploy`/`tail`. |
| `workers/akamai-spike/.gitignore` | 3 | `node_modules/`, `.wrangler/`, `dist/`. |

Acceptance criteria (Task 1) — all pass:
- name in wrangler.toml: 1 hit (`realufo-akamai-spike`)
- AKAMAI_SPIKE binding in wrangler.toml: 2 hits (binding line + comment guidance)
- Each of `www.war.gov`, `aaro.mil`, `science.nasa.gov`, `catalog.archives.gov`: 1 hit each in `src/index.ts`
- AKAMAI_SPIKE referenced in `src/index.ts`: 3 hits (Env type + put call + comment)
- `src/index.ts` line count: 108 (≤120 ceiling)
- `wrangler` + `@cloudflare/workers-types` declared in package.json
- `.gitignore` lists all 3 required entries

## Task 2 — Operator deploys + invokes spike Worker (BLOCKED — REQUIRES OPERATOR)

Status: **blocked-on-operator**. Cannot be executed by the agent — requires interactive Wrangler login against the realufo CF account `f1868a071996e836eae6da2b65f37929`.

### Exact operator commands (run from `workers/akamai-spike/`):

```bash
cd workers/akamai-spike

# 1. Install local devDeps (pulls wrangler + @cloudflare/workers-types + typescript)
pnpm install

# 2. Log in to Wrangler if not already authenticated against realufo CF account
#    f1868a071996e836eae6da2b65f37929
pnpm exec wrangler login

# 3. Create the throwaway KV namespace
pnpm exec wrangler kv namespace create AKAMAI_SPIKE
#    Returns a block including `id = "<hex>"`. Paste this id into
#    workers/akamai-spike/wrangler.toml, replacing the `<populated-during-deploy>`
#    placeholder under [[kv_namespaces]], then `git add` + `git commit -m "chore(05-02): paste AKAMAI_SPIKE KV id from wrangler"`

# 4. Deploy the spike Worker
pnpm exec wrangler deploy
#    On success, record the Worker URL (e.g. https://realufo-akamai-spike.<account>.workers.dev)

# 5. Invoke the Worker once via curl — this triggers the 4 fetches + KV write
curl -s https://realufo-akamai-spike.<account>.workers.dev | jq .
#    Capture the entire JSON output verbatim. This is the primary spike result
#    that Task 3 transcribes into `.planning/decisions/akamai-spike.md`.

# 6. (Optional but recommended) Re-invoke 2–3 times spread across an hour
#    to confirm results are stable under Akamai's burst-vs-steady heuristics:
sleep 1800  # ~30 min
curl -s https://realufo-akamai-spike.<account>.workers.dev | jq .

# 7. Cost-guard capture (for D-20 + akamai-spike.md `## Workers cost-guard headroom`):
#    Open CF dashboard → Workers & Pages → realufo-akamai-spike → Metrics.
#    Record per-invocation CPU (target: < 1000 ms; wall clock < 5s for 4 fetches).
```

### What to report back

Resume signal: type `approved` plus paste:
1. The full JSON output from the `curl` invocation (all 4 source rows).
2. The CF dashboard per-invocation CPU metric in ms.
3. The deployed Worker URL.

Cost / billing note: Workers Paid plan already active (`.planning/decisions/workers-paid.md`). The spike runs ≤4 invocations total; per-invocation CPU expected < 1s. Spike cost is rounding error against the $5/mo flat fee.

### Acceptance criteria (Task 2)

- `wrangler.toml` has a real KV namespace id (no `<populated-during-deploy>` placeholder left).
- `wrangler deploy` returns 200 with a `.workers.dev` URL.
- At least one `curl` invocation returns 200 JSON listing all 4 sources with `status` + `latencyMs`.
- Per-invocation CPU metric captured from CF dashboard.

## Task 3 — Write `.planning/decisions/akamai-spike.md` ADR (BLOCKED — WAITING ON TASK 2 DATA)

Status: **waiting-on-task-2**. Cannot start: the ADR's `## Results` table and `## Blocked sources` TypeScript constant must be transcribed verbatim from Task 2's JSON output. Without that data, the ADR would be an empty shell.

Required ADR sections (per PLAN.md Task 3 `<action>`):
1. `## Status` — `complete` when Task 2 done.
2. `## Context` — why the spike was needed (PMS-03 deferred from Phase 1; Plan 05-04 dependency).
3. `## Method` — Worker name, CF account id, 4 source URLs, Chrome UA, KV namespace id, invocation count.
4. `## Results` — Markdown table, one row per source with HTTP status / server header / Akamai header / latency / verdict.
5. `## Blocked sources` — fenced TypeScript block: `export const AKAMAI_BLOCKED_SOURCES: ReadonlyArray<string> = [...] as const;`
6. `## Workers cost-guard headroom` — per-invocation CPU × ~52 weekly runs/year; confirm well under Workers Paid flat $5/mo per D-20.
7. `## Plan 05-04 instruction` — paragraph stating Plan 05-04 imports `AKAMAI_BLOCKED_SOURCES` verbatim.
8. `## Locked-by` — phase 5 plan-phase + Plan 05-02 — execute-phase pass at `<YYYY-MM-DD>`.

## Wave 2 unblock signal

Plan 05-03 (Workers cron skeleton) and Plan 05-04 (per-archive scrape lanes) may proceed **only after Task 3 lands `.planning/decisions/akamai-spike.md` with the `AKAMAI_BLOCKED_SOURCES` constant populated**. Until then, Wave 2 is BLOCKED.

## Throwaway KV namespace cleanup (deferred follow-up)

After Phase 5 closes (or sooner if convenient), operator should delete the spike namespace:
```bash
pnpm exec wrangler kv namespace delete --binding AKAMAI_SPIKE --namespace-id <hex-from-task-2>
```
This frees the KV slot on the realufo CF account; Plan 05-03 creates a separate `SCRAPE_STATE` namespace (D-04) for production cron-lock and fingerprint state — the two namespaces never collide by design.

## Deviations from Plan

None — Task 1 executed exactly as written. No bugs, no missing functionality, no architectural changes. Tasks 2 and 3 are pre-marked operator-gated in PLAN.md (`checkpoint:human-action` + dependency on Task 2 data); blocking-on-operator is the expected control flow, not a deviation.

## Threat surface scan

No new threat surface beyond what PLAN.md's `<threat_model>` already enumerates (T-05-02-01..04 + T-05-02-SC). All five threats are mitigated or accepted as documented:
- T-05-02-01 (UA spoofing) — accepted; realistic Chrome UA is the intended measurement surface.
- T-05-02-02 (KV data exposure) — accepted; headers are public, 24h TTL.
- T-05-02-03 (operator DoS via re-poll) — mitigated; `Cache-Control: public, max-age=60` on response.
- T-05-02-04 (KV cross-binding contamination) — accepted; throwaway namespace deleted post-phase.
- T-05-02-SC (supply chain) — mitigated; only first-party Cloudflare + Microsoft packages pinned at major version.

## Self-Check

- [x] `workers/akamai-spike/wrangler.toml` exists
- [x] `workers/akamai-spike/src/index.ts` exists (108 lines ≤ 120)
- [x] `workers/akamai-spike/package.json` exists
- [x] `workers/akamai-spike/.gitignore` exists
- [x] Commit `90f1418` exists in `git log`
- [x] All 4 source URLs grep-present in `src/index.ts`
- [x] `AKAMAI_SPIKE` KV binding referenced in both wrangler.toml and src/index.ts
- [x] No modifications to STATE.md or ROADMAP.md (worktree mode)

## Self-Check: PASSED
