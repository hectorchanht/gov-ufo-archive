# Phase 5: Scrape Automation — Context

**Gathered:** 2026-05-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Move source ingestion off the existing weekly GitHub Actions cron onto Cloudflare Workers cron with a hybrid Akamai-fronted-source fallback to GH Actions. Replace the manual/local-only `gh release upload` path with a CI flow that survives partial failures. Bulk-seed R2 with the existing 4-archive corpus on first run (Phase 4 UAT carryover).

**Within scope:**
- SCRP-01..10 (10 requirements: Workers cron + KV state + Akamai hybrid + R2 staging + per-archive release tags + cron-lock + curl_cffi resilience fixes + R2 overflow)
- Workers cron skeleton + KV fingerprint store + `repository_dispatch` → GH Action pipeline
- 4-active scope: wargov + aaro + nasa + nara (matches Phase 4 D-41 scope pivot)
- First-run bulk migration of existing PDF/video corpus from local repo + GH Releases to R2
- Rewrite of Phase 4 carryover `.github/workflows/r2-sync.yml` (currently unpushed locally)
- Spike test for Akamai-blocked sources + ADR `akamai-spike.md` (referenced but never written)

**Out of scope (deferred to later milestones / phases):**
- Real-time RSS-based scrape triggers (workflow_dispatch + cron is sufficient for current cadence)
- Dormant 11-archive re-activation (kept in repo but no scrape cycles spent on them)
- DNS cutover GH Pages → CF Pages (Phase 6 HOST-01)
- Disaster-recovery restore-from-GH-Releases drill
- Phase 4 R2 bulk migration sweep (folded into Plan 05-01 entry task)
</domain>

<decisions>
## Implementation Decisions

### Scrape Architecture (SCRP-01, SCRP-02)

- **D-01:** **Workers cron + GH Actions hybrid.** Cloudflare Worker fires on cron schedule, iterates per-source scrape lanes. Sources blocked from Cloudflare IP (Akamai-fronted .gov/.mil) fall through to a GH Actions runner with `curl_cffi`. Sources reachable from Workers IP stay on Workers (cheaper + faster).
- **D-02:** **Cron frequency: Weekly Monday 06:00 UTC.** Matches existing `.github/workflows/scrape.yml` cadence; preserves operator's existing mental model. Source content (gov disclosure docs) changes slowly enough that weekly is sufficient — daily wastes Worker invocations + Akamai egress.
- **D-03:** **Akamai-blocked-source determination via spike Worker.** Before Phase 5 planner runs, deploy one-shot Worker that fetches the 4 active sources (www.war.gov, aaro.mil, science.nasa.gov, catalog.archives.gov) and records 200 vs 403/blocked status. Hard-code the resulting blocked list as a constant in Workers source. Produce `.planning/decisions/akamai-spike.md` ADR documenting findings — this ADR is referenced by ROADMAP.md but never written.
- **D-04:** **KV cron-lock (SCRP-07).** Workers cron acquires a KV lock at run start; overlapping cron invocations (rare but possible during Cloudflare KV propagation delays) see the lock + exit silently.

### Binary Storage Path (SCRP-03, SCRP-05, SCRP-06, SCRP-10)

- **D-05:** **Hybrid R2 + GH Releases — R2 serves; GH Releases is cold-backup durable layer.** Scrape writes new binaries to R2 staging; promotion job copies to canonical R2 location AND uploads to GH Releases per-archive-quarter tag. Card URLs continue pointing at `assets.realufo.org` (R2). GH Releases tags survive R2 outages + serve as offline replication target.
- **D-06:** **Single `realufo` R2 bucket; `staging/` prefix for in-flight binaries.** New binaries land at `staging/pdfs/<slug>/<file>` or `staging/videos/<slug>/<file>`. Promotion job R2-internally copies to `pdfs/<slug>/<file>` or `videos/<slug>/<file>` (the canonical serving path). Single bucket = single CORS policy (Plan 04-02), single GH secrets, single custom domain.
- **D-07:** **Per-archive-quarter GH Release tag scheme (SCRP-06).** Format: `<slug>-pdfs-<YYYY>q<N>` and `<slug>-videos-<YYYY>q<N>`. Examples: `wargov-pdfs-2026q2`, `aaro-videos-2026q3`. Replaces the legacy `pdfs-v1` + `videos-v1` shared tags (which hit GitHub's 1000-asset ceiling). Existing legacy tags preserved read-only as cold archive.
- **D-08:** **`scripts/release-upload.py` helper (SCRP-05).** SHA-256 idempotency check before upload (skip if local SHA matches remote release asset SHA). Delete-then-upload retry loop. Serialized invocation (no parallel `gh release upload --clobber` races).
- **D-09:** **R2 overflow for >2 GB single assets (SCRP-10).** GitHub Releases per-asset ceiling is 2 GB. Any single binary >2 GB skips the GH Release upload step entirely and stays R2-only (no cold backup for outliers). Currently relevant only for `geipan/videos/Lyon-2019-12-19.mp4` (40 MB, in scope only if dormant scope re-activates).

### Scrape Scope

- **D-10:** **4 active archives ONLY:** wargov, aaro, nasa, nara. Matches Phase 4 scope-pivot D-41. Workers cron iterates this list verbatim.
- **D-11:** **Dormant `dl-{geipan,uk,brazil,chile,argentina,canada,italy,nz,peru,spain,uruguay}.sh` scripts remain in repo + are NOT invoked by cron.** Re-activation path = adding a slug to the 4-active list in Workers source.
- **D-12:** **`scripts/spider.py` preserved + extended.** Phase 4 ADR `python-build-retired.md` carved spider.py out of SSG-10 retirement for this phase. Phase 5 may extend with Workers-side helpers OR keep spider.py as the Akamai-fallback runner's entry point.

### First-Run Bulk Migration (Phase 4 UAT R2 Carryover)

- **D-13:** **Plan 05-01 = R2 bulk seed.** First plan of Phase 5 seeds R2 with existing 4-archive corpus before the cron starts running. Without this, Workers cron would have to back-fill incrementally over many cycles + cards would 404 in the meantime.
- **D-14:** **Rewrite `.github/workflows/r2-sync.yml`** as part of Plan 05-01 (Phase 4 carryover — the version committed in Plan 04-02 is unpushed because Frank lacks write on hectorchanht repo). Rewrite shape: triggers via `repository_dispatch` (Worker→GH-App-token, future) + `workflow_dispatch` (manual seed). Adds idempotent SHA-based skip. Supersedes Phase 4 version.
- **D-15:** **Operator-triggered initial bulk via `workflow_dispatch`.** After Plan 05-01 lands the rewritten r2-sync.yml on remote, operator runs `gh workflow run r2-sync.yml -f full_sync=true --repo hectorchanht/gov-ufo-archive` once. Subsequent runs are Worker-triggered.

### Pipeline Mechanics (SCRP-04, SCRP-08, SCRP-09)

- **D-16:** **`repository_dispatch` Worker → GH Action.** Worker (post-fetch + post-fingerprint-diff) fires a `repository_dispatch` event with payload `{ archive, asset_keys[] }`. GH Action's pipeline listens for this event + handles staging→canonical promotion + GH Release upload.
- **D-17:** **GH Action job stages:** (1) pull new R2 staging objects (download for SHA check), (2) `release-upload.py` to GH Releases per-archive-quarter tag, (3) R2-internal copy `staging/<path>` → `<path>` (canonical), (4) commit any data manifest deltas (per-archive `data/<slug>.json` SHA may update).
- **D-18:** **SCRP-08: remove all `|| true` from curl_cffi install steps.** Phase 5 scrape.yml rewrite explicitly fails on dependency-install errors instead of silently swallowing.
- **D-19:** **SCRP-09: workflow_dispatch path preserved.** Manual `gh workflow run scrape.yml` (and the new r2-sync.yml + workers-trigger.yml) still works for ad-hoc / back-fill. Useful when Worker is paused for debugging.
- **D-20:** **Worker cost guard.** Free Workers tier = 100k req/day. Per-cron run = ~20 fetches + ~20 KV reads + ~20 KV writes + 4 repository_dispatch calls = well under daily ceiling. Document headroom in akamai-spike.md ADR.

### GH Repo Access Carryover (Phase 4 unblocked issue)

- **D-21:** **All Phase 4 commits are LOCAL ONLY** (Frank pull-only on hectorchanht/gov-ufo-archive). Before Phase 5 entry plan (05-01) can land r2-sync.yml on remote, operator (Hector) must either: (a) `git pull` Frank's branch + push, OR (b) grant Frank write access, OR (c) Frank PRs from a fork to hectorchanht. Plan 05-01 begins with this operator gate.
- **D-22:** **All Phase 4 milestone commits propagate to remote in this same operator action.** That includes 11 phase 4 plans + scope-pivot + UAT + 4 archive ports + Pagefind + close. After Hector pushes, gh workflow list reflects current state; r2-sync.yml + quality-gates.yml (updated by 04-20) are dispatchable.

### Claude's Discretion

- Worker source language (TypeScript via wrangler init recommended; bind R2 + KV bindings)
- KV namespace name (`SCRAPE_STATE` recommended; bind both `realufo` R2 + `SCRAPE_STATE` KV in wrangler.toml)
- ETag vs content-hash for fingerprint diff (D-01 says both — implementation picks one or layers)
- Exact retry/backoff semantics for release-upload.py
- Spike Worker hostname (use existing realufo CF account, throwaway worker)
- Whether the 4 archives' scrape lanes can run in parallel inside one Worker invocation (vs. serial fan-out) — measure during spike

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 5 ROADMAP entry
- `.planning/ROADMAP.md` §Phase 5 — depends on Phase 3, may begin parallel with Phase 4, must complete before Phase 6 cutover
- `.planning/REQUIREMENTS.md` lines 74-83 — SCRP-01..10 detail

### Phase 4 outputs (consumed by Phase 5)
- `.planning/phases/04-full-migration-search-offline-performance/04-CONTEXT.md` D-01..D-42 — R2 binary CDN locked decisions, esp D-01 (R2 PDFs+videos only), D-02 (assets.realufo.org), D-24 (R2 CORS)
- `.planning/phases/04-full-migration-search-offline-performance/04-02-SUMMARY.md` — R2 setup mechanics, `_archive_common.py:rewrite_to_r2()` API
- `.planning/phases/04-full-migration-search-offline-performance/04-20-SUMMARY.md` — Python retirement boundary; spider.py + dl-*.sh preserved for Phase 5
- `.planning/phases/04-full-migration-search-offline-performance/04-UAT.md` §1 — R2 bulk migration PATH A (push r2-sync.yml) + PATH B (wrangler direct) commands
- `scripts/_archive_common.py` — `rewrite_to_r2(local_path, slug)` helper
- `scripts/spider.py` — generic source-page crawler (Phase 5 may extend)
- `scripts/dl-{aaro,nasa,nara}.sh` — per-source download orchestrators (4-archive scope: wargov uses different mechanism via uap-release001.csv)
- `.planning/decisions/r2-setup.md` — bucket name, custom-domain bind, CORS scope, GH secrets, jurisdiction choice
- `.planning/decisions/python-build-retired.md` — spider.py + dl-*.sh carve-out rationale for Phase 5

### Project-wide rules
- `./CLAUDE.md` §5.1 GH Releases binary CDN policy (Phase 4 D-01 supersedes for R2-primary serving; Phase 5 D-05 layers GH Releases as cold backup) + §5.2 .gitignore policy + §11 don'ts (CSV untouchable; no force-push)
- `.planning/PROJECT.md` §Active SSG-01..02, SCRAPE-02, SCRAPE-03, HOST-01 — Phase 5 closes SCRAPE-02 + SCRAPE-03

### Phase 2 CI gates (Phase 5 must keep green)
- `.github/workflows/quality-gates.yml` — 7-job matrix (Phase 5 changes do NOT regress these; r2-sync.yml + workers-trigger.yml are siblings)
- `scripts/verify-redirects.sh` (URL contract harness)
- `scripts/verify-fidelity.py` (Phase 5 may add new fidelity samples if scrape pipeline rewrites data JSON)

### Cloudflare docs (researcher to expand)
- Workers cron triggers: https://developers.cloudflare.com/workers/runtime-apis/cron/
- Workers KV: https://developers.cloudflare.com/kv/
- Wrangler R2 binding from Workers: https://developers.cloudflare.com/r2/api/workers/workers-api-reference/
- `repository_dispatch` GitHub event: https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event
- curl_cffi (Akamai bypass): https://github.com/yifeikong/curl_cffi
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`scripts/spider.py`** (387 lines): generic source-page crawler. Phase 5 may extract its fetch logic into a Workers-compatible shim OR keep it as the Akamai-fallback GH Action runner's entry point.
- **`scripts/dl-aaro.sh`** + **`scripts/dl-nasa.sh`** + **`scripts/dl-nara.sh`**: per-archive download orchestrators. Phase 5 cron lanes wrap these (sources with stable URL schemes) OR rewrite as Workers JS where Cloudflare IP is not blocked.
- **`scripts/_archive_common.py:rewrite_to_r2()`** (Plan 04-02): existing helper that maps local paths to R2 URLs. Scrape pipeline's post-promotion data-manifest update reuses this.
- **`scripts/normalize-csv.py`** + per-archive `scripts/normalize-{aaro,nasa,nara}.py` (Phase 4): take raw scrape output → produce `data/<slug>.json`. Scrape pipeline's data-manifest update step invokes these.
- **`uap-release001.csv`** (CLAUDE.md §11 untouchable): wargov source-of-truth. Scrape pipeline for wargov is a no-op on CSV; only the binary corpus is in scope.

### Established Patterns
- **D-10 LOCKED from Phase 3:** server-side card HTML shards + runtime `insertAdjacentHTML` only. Phase 5 doesn't touch this — it only updates the data layer the shards are built from.
- **`pnpm prebuild`** runs `scripts/normalize-csv.py` (Phase 3 + 4). If scrape pipeline updates a per-archive data source, the next site build picks it up automatically. No SSG changes needed.
- **CI workflows have `concurrency:` groups** (Phase 2 pattern). Phase 5 cron jobs use the same to prevent overlapping cron + manual dispatch races.
- **R2 CORS already configured** (Plan 04-02) for `https://realufo.org` + `https://*.realufo.pages.dev` + localhost. Scrape pipeline doesn't need new CORS.

### Integration Points
- **`scrape.yml` cron line** (`0 6 * * 1`) — preserved verbatim per D-02; Phase 5 rewrites the job body to call Workers' health endpoint instead of running scripts directly.
- **`repository_dispatch` event** from Worker → GH Action. New event type `scrape-promote` (or similar).
- **`wrangler.toml`** in repo root — needs new bindings: `[[r2_buckets]] binding = "REALUFO" bucket_name = "realufo"` + `[[kv_namespaces]] binding = "SCRAPE_STATE" id = "<populated-during-plan-05-02>"`.
- **GH Releases tag namespace** — Phase 5 introduces per-archive-quarter tags alongside existing legacy global tags. No deletion of legacy; pure additive.
- **`data/<slug>.json` files** (Phase 4) — scrape pipeline's data-manifest update step writes here. Per-archive normaliser scripts already idempotent (Phase 4 D-04).

</code_context>

<specifics>
## Specific Ideas

- Operator preference (2026-05-28 memory file): all GitHub operations attribute to `hectorchanht` (not `frankchanflow`). Applies to push, `repository_dispatch` event source, gh CLI invocations. Plan 05-01 begins with operator gate (D-21).
- Existing `scrape.yml` Monday 06:00 UTC cron cadence preserved per D-02 — minimal operator-noticeable change.
- akamai-spike.md ADR is overdue (referenced in roadmap, never written). Phase 5 plan should explicitly create it as the first artifact alongside the spike Worker code.
- 4-active scope means `dl-{geipan,uk,brazil,chile,argentina,canada,italy,nz,peru,spain,uruguay}.sh` (11 scripts) remain in repo but Workers cron + GH Actions ingest pipeline skip them. Re-activation = adding a slug to the 4-active list in Workers source.
- Phase 4 unpushed-state warning: Plan 05-01's first task is the operator push gate. Without it, `gh workflow run` fails with "workflow not found".
</specifics>

<deferred>
## Deferred Ideas

- **Real-time RSS scrape triggers** — Phase 5 stays on weekly cron; RSS-based reactive ingestion is future-milestone.
- **Dormant 11-archive re-activation** — code preserved (dl-*.sh + scope-pivot 80efc70 keeps schema 15-wide); not in Phase 5 scope.
- **Disaster-recovery restore-from-GH-Releases drill** — out of Phase 5 scope; should be Phase 6 HOST + post-cutover task.
- **Per-asset content-hash diff layer** — D-01 says ETag-only is sufficient for fingerprint diff. Content-hash may layer in if ETag false-negatives observed during weekly runs.
- **Parallel scrape lanes inside one Worker invocation** — D-claude's-discretion; measure during akamai-spike before deciding serial vs parallel.
- **Lighthouse Quality-gates HARD-flip enforcement on r2-sync.yml** — Plan 04-20 already flipped Lighthouse to HARD per D-40; Phase 5 doesn't add new gate jobs.
- **Frank → hectorchanht permanent write access** — operational decision out of Phase 5 scope; D-21 routes through "operator pushes for Frank" workaround indefinitely if needed.

</deferred>

---

*Phase: 05-scrape-automation*
*Context gathered: 2026-05-28*
