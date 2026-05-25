# Workers Paid activation — Phase 2 INF-03

Fourth ADR-style decision document under `.planning/decisions/` (after
`akamai-spike.md` from plan 01-03, `dns-ttl.md` from plan 01-04, and
`cf-pages-project.md` from plan 02-01). Records the Cloudflare Workers
Paid plan ($5/mo) activation performed in Phase 2 plan 02-02 — the
billing precondition that unlocks Phase 5's scrape Worker scope
(15-minute CPU on cron triggers, 10k subrequests/invocation).

## Status

`paid-plan-active` — Cloudflare Workers Paid plan is active on account
`f1868a071996e836eae6da2b65f37929` as of 2026-05-25 (user-reported
activation via CF dashboard billing flow). Programmatic verification
confirms `default_usage_model: "standard"` on the account Workers
settings — the canonical post-2024 marker for Workers Standard pricing
(Paid tier).

Transitions: `paid-plan-active` → `paid-plan-billing-confirmed` (operator
attaches the first monthly invoice showing the $5/mo Workers Paid line
item — soft followup, see §Open followups) → `paid-plan-in-production`
(Phase 5 lands the first cron Worker that exercises the CPU budget).

## Activation

| Field | Value |
| --- | --- |
| CF account ID | `f1868a071996e836eae6da2b65f37929` |
| Account email | `f147259@gmail.com` |
| Plan name | `Workers Paid` |
| Plan price | `$5/month USD` (flat; metered overage stays opt-in per research/PITFALLS.md Pitfall #10) |
| Activation date (UTC) | `2026-05-25` (user-reported via execute-plan resume-signal; exact dashboard timestamp not captured — see §Open followups) |
| Next billing date | TBD — first invoice cycle; operator confirms on receipt |
| Verification method | Cloudflare API `GET /accounts/<id>/workers/account-settings` returns `default_usage_model: "standard"` (Workers Standard pricing model = Paid plan). Verified 2026-05-25 from this plan's execute step. |
| Verification token | `a4d176a9121d869e55e12053dd260543` (token ID; the secret itself is stored at `/tmp/cf-realufo-token` with 600 perms and is never committed) |

## Why now (D-05, D-06)

Per `.planning/phases/02-infrastructure-ci-scaffolding/02-CONTEXT.md`
decisions D-05 and D-06, and per
`.planning/research/STACK.md` §"Critical: Don't try this on the Free
plan":

1. **Free plan is unusable for the Phase 5 scrape pipeline.** Free
   Workers cap CPU at 10 ms per invocation. HTML parsing of the 15
   government source pages — even the small ones — exceeds this. Free
   is a hard reject for SCRAPE-03.
2. **Paid plan unlocks the budget Phase 5 was designed against.** Paid
   gives 15 minutes of CPU on cron-triggered invocations (≥1 hr
   interval), 10,000 subrequests/invocation, 128 MB memory, and 10 MB
   compressed Worker script size. The Akamai spike (`01-03-SUMMARY.md`)
   confirmed the hybrid Worker-cron + GH-Actions-build architecture
   requires this budget.
3. **Activate at Phase 2, not at Phase 5 start.** Activating now lets
   the ssg-migration branch verify the Paid CPU/subrequest limits are
   live in the same window as the rest of the CI scaffolding. Without
   it, Phase 5 architecture commits would be planning against unverified
   billing state.
4. **Billing requires UI interaction.** Cloudflare's public API does not
   expose a "subscribe to a paid Workers plan" endpoint — billing
   actions require a logged-in dashboard session against the operator's
   account. There is no API workaround. This is why D-06 surfaces
   activation as `checkpoint:human-action`; without it, Phase 5 cannot
   start (D-36).

## Confirmed Paid-plan limits

Verbatim from `.planning/research/STACK.md` §"Limits to design within
(Paid plan, $5/mo)":

| Limit | Value | Phase 5 headroom |
| --- | --- | --- |
| CPU time per cron invocation | **15 min** | Plenty — HTML parse + diff is sub-second per source |
| Wall clock | **15 min** | Plenty |
| Subrequests per invocation | **10,000** (configurable to 10M) | 15 sources × ~50 fetches = 750. Comfortable |
| Memory | **128 MB** | Plenty — stream binaries, don't buffer |
| Worker size (compressed) | **10 MB** gzip | Octokit + papaparse ~1 MB. Comfortable |
| Cron triggers per account | **250 paid** | More than needed |

Phase 5 plans cite this table by reference. If Cloudflare changes any
Paid-plan limit, this doc is the canonical update site.

## Cost ceiling

- **Projected steady-state:** **$5/month USD flat.** No metered overage
  projected for Phase 5 scope (per research/STACK.md §"Limits to design
  within" — every limit has comfortable headroom for the 15-source,
  daily-cron design).
- **Budget alert threshold:** operator commits to a **$20/month** CF
  billing alert (per research/PITFALLS.md Pitfall #10 §"Budget
  guardrails"). At $20/mo the alert fires, the operator investigates,
  and either a runaway cron is fixed or KV cron-lock is added to
  serialise overlapping invocations.
- **Annual ceiling:** ~$60/year under steady state, ~$240/year at the
  budget-alert threshold. Both well within the project's "free or
  near-free" CLAUDE.md §1 goal.

## Phase 2 invariants honored

- **D-05:** Operator activated ASAP (2026-05-25, in Phase 2 plan 02-02);
  not deferred to Phase 5. The Paid CPU/subrequest limits are now
  verifiable before Phase 5 architecture commits land.
- **D-06:** Surfaced as `checkpoint:human-action` (this plan, Task 1).
  The execute-plan run blocked on operator confirmation; Task 2 (this
  ADR) ran only after the operator resumed with activation confirmed.
- **D-04:** No wrangler-based GH-Actions deploy step lands in this plan
  — Wrangler is reserved for Workers cron in Phase 5 (and project
  bootstrap in 02-01). The Workers Paid plan activation is a billing
  state change only.
- **D-36:** Workers Paid plan activation was the ONLY operator action
  gating Phase 2 completion (alongside 02-01's CF Pages git-integration
  click). Both are now either complete or queued as soft followups.
- **D-37:** No DNS or domain config touched. `realufo.org` continues to
  resolve to GitHub Pages (`185.199.108-111.153`).
- **D-38:** No SSG code committed. No Workers code committed. No
  wrangler.toml committed.

## Future-phase hooks

- **Phase 5 (scrape automation)** scaffolds the first cron Worker. Its
  plan(s) MUST cite this doc and include a preflight check:
  ```sh
  grep -q "paid-plan-active\|Plan: Workers Paid\|plan-active\|Paid plan" \
    .planning/decisions/workers-paid.md \
    || { echo "ABORT: Workers Paid plan not active — see .planning/decisions/workers-paid.md"; exit 1; }
  ```
  This prevents a Phase 5 plan from accidentally trying to ship cron
  triggers against a downgraded account.
- **Phase 1 PMS-02 SW kill-switch** runs in parallel; its ≥14-day
  kill-switch counter starts from the SW deploy date
  (`01-05-SUMMARY.md`), not from this activation. The two timelines are
  independent.
- **Phase 6 (cutover)** — at DNS swap time, this doc gets a `## Cutover
  Log` section if any billing change is needed (e.g., raising the
  subrequest cap from 10k to 10M for higher-volume scraping). Default
  expectation: no change at cutover.

## Open followups

1. **Operator confirms exact activation timestamp + next-billing date.**
   The execute-plan resume signal was a user message ("activation
   already done") rather than the explicit timestamped paste-block in
   02-02-PLAN.md §Task 1's `<resume-signal>`. Operator should append the
   real UTC timestamp + next-billing date to this doc on the first
   monthly invoice (or sooner if they grab it from the CF dashboard
   Subscriptions tab).
2. **Operator sets the $20/mo billing alert.** Cloudflare's billing
   alerts live under
   `https://dash.cloudflare.com/f1868a071996e836eae6da2b65f37929/billing/alerts`.
   Set threshold = `$20.00 USD`, notification = account email. Soft
   followup — not blocking Phase 2 close.
3. **Verify the four Paid-plan limits visible in dashboard match the
   table above.** The API verification confirms the usage model is
   `standard` (Paid). The dashboard's per-Worker Settings → Usage panel
   is the user-facing source of truth and should match the §Confirmed
   Paid-plan limits table verbatim. Operator confirms on next dashboard
   visit.

## Out of scope for this plan

- **Workers code.** No `*.js` or `*.ts` Worker files commit in this
  plan. Phase 5 plans (`05-NN-PLAN.md`) own the first Worker.
- **`wrangler.toml`.** No `wrangler.toml` lands here. Phase 5 owns the
  first one.
- **KV namespaces.** No KV namespaces are created. Phase 5 creates the
  cron-lock KV namespace if/when needed (per research/PITFALLS.md
  Pitfall #10).
- **R2 buckets.** No R2 buckets are created. Phase 5 may create an R2
  staging bucket for >2 GB binary overflow (per research/STACK.md
  §"Hybrid split: who runs what").
- **Cron triggers.** No cron triggers are registered. Phase 5 registers
  the first one via `wrangler.toml` `[triggers]` and validates with
  `wrangler triggers deploy`.
- **Queues / Durable Objects.** Out of scope for Phase 5 baseline; only
  considered if a Worker exceeds the 15-min wall-clock budget (per
  research/STACK.md §"If the scrape Worker exceeds 15 min wall clock").
- **DNS / domain config.** Out of scope per D-37. Apex stays on GitHub
  Pages anycast until Phase 6 cutover (`.planning/decisions/dns-ttl.md`).
