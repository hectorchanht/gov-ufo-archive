# Akamai Egress Spike — Operator Runbook

> Bilateral 1-hour probe to decide whether the Phase 5 scrape lane goes
> through Cloudflare Workers or stays on GitHub Actions runners.

## 1. Why

The SSG-migration plan (`.planning/PROJECT.md` Active list, `SCRAPE-03`)
assumes that moving the gov-site scraper from GitHub Actions runners to a
Cloudflare Workers cron will *help* with Akamai bot-blocks on `war.gov` /
`aaro.mil`. The assumption may be wrong:
`.planning/research/PITFALLS.md` Pitfall #3 documents that Cloudflare's
edge IPs are flagged in Akamai's IP-reputation database, while
Azure-hosted Actions runners carry less stigma.

This spike measures the assumption objectively per source so
`.planning/decisions/akamai-spike.md` can split sources into a
Workers-friendly bucket and an Actions-only bucket per the
D-09..D-12 plan in `01-CONTEXT.md`.

## 2. Scope

The 5 probe targets are pinned in `probe-sources.json`. Per D-09:

| # | URL | Selection method |
| --- | --- | --- |
| 1 | `https://www.war.gov/UFO/` | Always included — Akamai-fronted (PITFALLS.md Pitfall #3) |
| 2 | `https://www.aaro.mil/` | Always included — Akamai-fronted |
| 3 | `https://science.nasa.gov/uap/` | Random sample (seed 20260525, slot 0) |
| 4 | `https://www.fau.mil.uy/` | Random sample (seed 20260525, slot 1) |
| 5 | `https://www.sefaa.cl/` | Random sample (seed 20260525, slot 2) |

The 3 random samples are reproducible: re-run
`random.seed(20260525); random.sample(other_13, 3)` over the 13-URL
"non-Akamai-known" list (CLAUDE.md §2 minus war.gov/aaro.mil) and you get
the same picks. The list is the source of truth — neither lane re-seeds at
probe time.

## 3. Methodology (per D-10)

**Bilateral, 100 fetches per source per lane, over the same 1-hour window.**

- Worker lane: 100 invocations of the Cloudflare Worker, each probing all
  5 targets in parallel. Cron schedule `* * * * *` (every minute) for
  ~100 minutes; trim to first 100 per source post-run. 500 rows total.
- Actions lane: `actions-runner.py` runs locally or on a `workflow_dispatch`
  GH Actions runner. Per source, 100 fetches spaced `3600 ÷ 100 = 36s`
  apart, 5 sources in parallel via `ThreadPoolExecutor`. 500 rows total.

Both lanes use the **same** Chrome-131 UA string from
`.planning/codebase/CONCERNS.md` (the same UA every existing `scripts/dl-*.sh`
sends today) so the comparison is like-with-like:

```
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36
```

Both lanes capture per fetch: HTTP status, response body length, `Server`
header, presence of any Akamai cookie (`_abck`, `bm_sc`, `AKAM_SC`), and
whether the first 2 KB of body contains `Pardon Our Interruption` or
`Access Denied` (PITFALLS.md Pitfall #5 fingerprints from the planner's
`<interfaces>` block).

Redirects are **NOT followed** (`redirect: 'manual'` /
`HTTPRedirectHandler.http_error_30X = passthrough`). Akamai often
redirects to a challenge URL that is itself `200 OK`; following the
redirect would mask the block.

## 4. How to run the Worker lane

### 4.1 One-time deploy

The Worker is at `worker.ts`. A minimal `wrangler.toml` to drop alongside
it:

```toml
name = "realufo-akamai-spike"
main = "worker.ts"
compatibility_date = "2026-05-25"
account_id = "<from CLOUDFLARE_ACCOUNT_ID env>"

[triggers]
crons = ["* * * * *"]

[vars]
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
PROBE_TARGETS_JSON = "[\"https://www.war.gov/UFO/\",\"https://www.aaro.mil/\",\"https://science.nasa.gov/uap/\",\"https://www.fau.mil.uy/\",\"https://www.sefaa.cl/\"]"

[[kv_namespaces]]
binding = "SPIKE_RESULTS"
id = "<create with: wrangler kv:namespace create SPIKE_RESULTS, paste id here>"
```

Then:

```sh
# One-time KV namespace creation
wrangler kv:namespace create SPIKE_RESULTS
# (paste the returned id into wrangler.toml above)

# Dry-run / compile-check the bundle
wrangler deploy --dry-run

# Real deploy — starts the cron the moment it's accepted by the API
wrangler deploy
```

The cron fires every minute and writes 5 KV rows per firing under keys
`worker:<iso-timestamp>:<host>`. Watch live with `wrangler tail`.

### 4.2 Run the bilateral window

Coordinate the Actions lane to start at the same minute (see §5). Let
both lanes run for ~100 minutes wall-clock; you'll naturally accumulate
100+ rows per source per lane.

To run a single round on demand (without waiting for cron):

```sh
curl -X POST https://realufo-akamai-spike.<account>.workers.dev/run-now
```

### 4.3 Stop the cron + drain KV → results.json

```sh
# Stop the cron
wrangler deploy --triggers ""   # or delete the `[triggers]` block and redeploy

# Drain KV — produces a JSON array of worker_lane rows, with the first 100
# per source by timestamp.
wrangler kv:key list --binding SPIKE_RESULTS \
  | jq -r '.[].name' \
  | while read k; do
      wrangler kv:key get "$k" --binding SPIKE_RESULTS
      echo
    done \
  | jq -s 'group_by(.target_url) | map(sort_by(.iso_timestamp)[:100]) | flatten' \
  > /tmp/worker_lane.json

# Merge into results.json's worker_lane key — preserves actions_lane that
# the Actions runner has already populated.
python3 -c "
import json, pathlib
results = json.loads(pathlib.Path('.planning/spikes/01-akamai/results.json').read_text())
worker = json.loads(pathlib.Path('/tmp/worker_lane.json').read_text())
results['worker_lane'] = worker
pathlib.Path('.planning/spikes/01-akamai/results.json').write_text(json.dumps(results, indent=2))
print(f'worker_lane rows: {len(worker)}')
"
```

## 5. How to run the Actions lane

### 5.1 Local laptop

```sh
# Sanity check — one fetch per target, no sleep. Confirms targets are reachable.
python3 .planning/spikes/01-akamai/actions-runner.py --dry-run

# Real 1-hour run — start within 60s of the Worker cron
python3 .planning/spikes/01-akamai/actions-runner.py \
  --duration 3600 --fetches-per-source 100
```

Results are appended row-by-row to
`.planning/spikes/01-akamai/results.json` under `actions_lane`.

### 5.2 GitHub Actions runner (optional)

Drop this into `.github/workflows/akamai-spike.yml` if you'd rather run the
Actions lane from a real Actions runner (more representative of the eventual
SCRAPE-02 environment):

```yaml
name: akamai-spike-actions-lane
on:
  workflow_dispatch:
    inputs:
      duration:
        description: "Total spike seconds"
        default: "3600"
      fetches_per_source:
        description: "Fetches per source"
        default: "100"

permissions:
  contents: write   # to commit results.json back at the end

jobs:
  spike:
    runs-on: ubuntu-latest
    timeout-minutes: 75
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: |
          python3 .planning/spikes/01-akamai/actions-runner.py \
            --duration ${{ inputs.duration }} \
            --fetches-per-source ${{ inputs.fetches_per_source }}
      - run: |
          git config user.name 'github-actions[bot]'
          git config user.email 'github-actions[bot]@users.noreply.github.com'
          git add .planning/spikes/01-akamai/results.json
          git commit -m "spike(01-akamai): actions-lane results from runner $GITHUB_RUN_ID"
          git push
```

`workflow_dispatch` from the GitHub UI, paste the same start-minute as
the Worker cron deploy, wait ~1 hour, the runner commits results.json
back to `main`.

## 6. Pass/fail threshold (D-11, quoted verbatim)

> "Workers is viable if its success rate is ≥ 95% AND ≥ Actions success
> rate. Otherwise, that source falls through to the hybrid
> Actions+`curl_cffi` lane in Phase 5. The decision is per-source (some
> sources may be Workers-friendly, others Actions-only)."

"Success" = `200 OK` AND no Akamai-cookie present AND no
`Pardon Our Interruption` / `Access Denied` fingerprint in the first 2 KB.
A `200` that's actually a 12 KB Akamai block page is **not** a success.

## 7. Where the decision lands

`.planning/decisions/akamai-spike.md` — the project's first ADR, established
by this spike per D-12. Phase 5 (SCRP-01, SCRP-02, SCRP-08) reads it before
architecting the scrape Workers.

Task 3 of this plan computes per-source success rates from
`results.json`, applies the D-11 threshold, and writes the per-source
verdict (workers-viable / actions-only). Task 3 will refuse to run until
`results.json` has BOTH `worker_lane` and `actions_lane` populated.

## 8. Reproducibility

- **RNG seed:** `20260525` (today's date as YYYYMMDD). Stored in
  `probe-sources.json::rng_seed`.
- **The 13-URL "other" list** is the Official-site column of CLAUDE.md §2
  with war.gov + aaro.mil removed (their slots are always-included).
- `random.seed(20260525); random.sample(other_13, 3)` yields:
  `['https://science.nasa.gov/uap/', 'https://www.fau.mil.uy/', 'https://www.sefaa.cl/']`.
  Verify any time with the Python one-liner in
  `probe-sources.json::rng_method`.
- `results.json` is the raw source of truth — any future audit can replay
  the Task-3 aggregation without re-running the 1-hour spike.

---

*Spike scaffold: PMS-03 Task 1. Execution: PMS-03 Task 2 (human checkpoint).
Decision write-up: PMS-03 Task 3.*
