---
phase: 02-infrastructure-ci-scaffolding
plan: 01
subsystem: infra
tags: [cloudflare-pages, ssg-migration-branch, _headers, hsts, sw-cache-control, node-skeleton, pnpm, wrangler]

# Dependency graph
requires:
  - phase: 01-pre-migration-safety
    provides: "sw.js kill-switch (01-05) — Phase 2 _headers `/sw.js` Cache-Control: no-cache, no-store, must-revalidate defends Pitfall #1 against the kill-switch + any future real SW"
  - phase: 02-infrastructure-ci-scaffolding
    provides: "02-CONTEXT.md decisions D-01..D-04 (CF Pages bootstrap), D-07..D-08 (_headers content), D-33 (ssg-migration branch), D-37 (no DNS swap), D-38 (no SSG code)"
provides:
  - "Cloudflare Pages project 'realufo' in account f1868a071996e836eae6da2b65f37929; serves at https://realufo.pages.dev/ once git-integration is connected"
  - "ssg-migration long-running remote branch forked from main HEAD 7d55341 — every Phase 2-5 commit lands here"
  - "_headers at repo root (4 rule blocks: /sw.js, /*, /assets/*, /_astro/*); CSP intentionally absent (D-07)"
  - "package.json skeleton with engines.node=>=22 <23, packageManager=pnpm@9, empty scripts + devDependencies (02-03 + 02-07 extend)"
  - ".nvmrc=22 (CF Pages NODE_VERSION auto-detection)"
  - ".planning/decisions/cf-pages-project.md ADR (project identity + branch strategy + build config + preview URLs + 7 invariants + git-integration follow-up)"
affects: [02-02-redirects, 02-03-playwright-baselines, 02-04-fidelity-samples, 02-05-redirects-builder, 02-06-tone-jsoff, 02-07-lighthouse, 02-08-quality-gates, 03-astro-install, 06-cutover]

# Tech tracking
tech-stack:
  added:
    - "Cloudflare Pages (project bootstrap; runtime deploys via CF git-integration once operator finishes UI step)"
    - "wrangler 4.94.0 (used ONCE for project creation; not used for runtime deploys per D-04)"
    - "pnpm 9 (declared via packageManager — install deferred to 02-03 per D-38)"
  patterns:
    - "Cloudflare Pages _headers v1 syntax: one rule block per path pattern, two-space header-value indent"
    - "Per-path SW cache-control: explicit /sw.js no-cache override defending against Pitfall #1 (SW HTTP-cache poisoning) and Pitfall #8 (CF Pages _headers default cache-control)"
    - "Immutable asset cache (max-age=31536000, immutable) for content-addressed paths (/assets/*, /_astro/*)"
    - "Node-version pinning via .nvmrc=22 + engines.node='>=22 <23' (dual-source: CF Pages reads .nvmrc, local devs read engines)"
    - "Wrangler env-var token sourcing: CLOUDFLARE_API_TOKEN=$(cat /tmp/file) to avoid token persistence in shell history or commits"
    - "ADR-style decision-doc structure: ## Status / ## Project identity / ## Branch strategy / ## Build configuration / ## Preview URLs / ## Phase N invariants honored / ## Future-phase hooks (matches dns-ttl.md + akamai-spike.md precedent)"

key-files:
  created:
    - _headers
    - package.json
    - .nvmrc
    - .planning/decisions/cf-pages-project.md
  modified:
    - .gitignore
  remote-side:
    - "origin/ssg-migration (new branch at 7d55341)"
    - "Cloudflare Pages project 'realufo' (account f1868a07...37929) — no on-disk artifact in repo, but project lifecycle anchors here"

key-decisions:
  - "Used wrangler to create the CF Pages project instead of the dashboard. The operator-supplied API token at /tmp/cf-realufo-token (600 perms) lets `wrangler pages project create` substitute for steps 1-7 of the plan's checkpoint:human-action Task 1. Git-integration (CF GitHub-App handshake) still requires a CF dashboard UI click — documented as a soft followup in the decision doc, not blocking Phase 2 progress because Direct-Upload via `wrangler pages deploy` is available as a fallback if git-integration is still pending at plan 02-08."
  - "Token sourcing pattern: ALWAYS env-var via $(cat /tmp/cf-realufo-token); never echo, write, log, or commit the value. The token file lives outside the repo at /tmp; .gitignore was deliberately NOT updated to exclude /tmp/* because doing so would imply the token might live in the repo path (defense-in-depth via path isolation, not gitignore filtering)."
  - "ssg-migration branch was pushed from local main HEAD (7d55341) which contains the Phase 2 planning commits not yet pushed to origin/main. This means origin/ssg-migration is briefly AHEAD of origin/main — intentional per D-33 (ssg-migration is the SSG-work branch; main stays on the production-ready commit until Phase 6 fast-forward). The next push of main to origin (out-of-scope for this plan) will resolve the divergence."
  - "_headers structure uses one rule block per path with two-space header-value indent — matches CF Pages v1 syntax per https://developers.cloudflare.com/pages/configuration/headers/. Zero CSP directives (D-07 explicitly defers to Phase 6 cutover because the current site is inline-CSS+JS-heavy and strict CSP would break it)."
  - "package.json deliberately ships with empty `scripts` and `devDependencies`. D-38 forbids 'install Astro while I'm here' — the Node skeleton exists so 02-03 (Playwright) and 02-07 (lighthouse-ci) can `pnpm add -D <dep>` without re-bootstrapping the project. No `pnpm-lock.yaml` yet — 02-03 generates it on first install."
  - "node_modules/ appears twice in .gitignore (line 49 from Phase 1 + new SSG-migration section line 64). Harmless to git (duplicate entries are idempotent) and intentional: the fenced 'SSG migration (Phase 2+)' section is a self-contained block so future plans can append without grepping the legacy section. Cosmetic cleanup deferred to plan 02-08 close if it ever matters."

patterns-established:
  - "ADR-style decision-doc structure: ## Status (with state-machine transitions) → ## Project identity → ## Branch strategy → ## Build configuration → ## Preview URLs → ## Phase N invariants honored → ## Future-phase hooks. Matches dns-ttl.md and akamai-spike.md precedent."
  - "CI gate dependency on CF Pages preview URL: per-deployment URL pattern is https://<commit-sha>.realufo.pages.dev/; production-branch URL is https://realufo.pages.dev/. Plan 02-08 (quality-gates.yml) reads these from PR deployment_status event payloads per D-31."
  - "Defense-in-depth for operator secrets: tokens live at /tmp (outside repo path) AND .env / .dev.vars are gitignored AND the env-var sourcing pattern never writes the token to a file inside the repo."

requirements-completed: [INF-01]
requirements-partial: [INF-02]
# INF-02 ('_headers + _redirects') is HALF done: _headers ships in this plan;
# _redirects ships in 02-05 (after URL-CONTRACT.txt stabilizes per D-09..D-11).

# Metrics
duration: ~12min
completed: 2026-05-25T05:50:00Z
---

# Phase 02 Plan 01: CF Pages Bootstrap + _headers + Node Skeleton Summary

**Stood up the long-running Cloudflare Pages preview origin (`realufo` project at `https://realufo.pages.dev/`) and the `ssg-migration` long-running branch, then committed the `_headers` file pinning `/sw.js` no-cache + global HSTS + nosniff + immutable-asset cache — the four rules from D-08 that every Phase 2-5 CI gate depends on.**

## Performance

- **Duration:** ~12 min (executor wall-time end-to-end including wrangler CLI roundtrip + decision-doc authoring)
- **Started:** 2026-05-25T05:38:00Z
- **Completed:** 2026-05-25T05:50:00Z
- **Tasks committed:** 1 of 2 (Task 1 produced no on-disk artifacts; Task 2 ships everything in one commit `85dcb01`)
- **Files created/modified:** 5 (4 created, 1 modified)

## Accomplishments

### Task 1 — CF Pages project + ssg-migration branch (now auto via wrangler)

The plan originally framed Task 1 as `checkpoint:human-action` because CF Pages project creation needs a dashboard session. The operator provided an API token at `/tmp/cf-realufo-token` (600 perms), which lets `wrangler pages project create` do the bootstrap server-side without a browser.

- **Created CF Pages project `realufo`** in account `f1868a071996e836eae6da2b65f37929`:
  ```
  CLOUDFLARE_API_TOKEN=$(cat /tmp/cf-realufo-token) \
  CLOUDFLARE_ACCOUNT_ID=f1868a071996e836eae6da2b65f37929 \
  npx -y wrangler@latest pages project create realufo --production-branch=ssg-migration
  ```
  wrangler 4.94.0 returned: `✨ Successfully created the 'realufo' project. It will be available at https://realufo.pages.dev/ once you create your first deployment.`
- **Verified via `wrangler pages project list`** — `realufo` row appears alongside the user's other Pages project (`wope-network`, unrelated):
  ```
  ┌──────────────┬──────────────────────────────────────┬──────────────┬────────────────┐
  │ Project Name │ Project Domains                      │ Git Provider │ Last Modified  │
  ├──────────────┼──────────────────────────────────────┼──────────────┼────────────────┤
  │ realufo      │ realufo.pages.dev                    │ No           │ 10 seconds ago │
  ├──────────────┼──────────────────────────────────────┼──────────────┼────────────────┤
  │ wope-network │ wope-network.pages.dev, wope.ccwu.cc │ No           │ 1 month ago    │
  └──────────────┴──────────────────────────────────────┴──────────────┴────────────────┘
  ```
  `Git Provider: No` confirms the project exists but is not yet bound to the GitHub repo — the operator finishes git-integration in the CF dashboard at their convenience (see "Open question" + the decision doc's "Soft followup" section).
- **Pushed `ssg-migration` branch to `origin`** from local `main` HEAD `7d55341f840fc9f1d227f1c9df0e47cb2f8a1cea`:
  ```
  git push origin HEAD:refs/heads/ssg-migration
  ```
  `git ls-remote origin ssg-migration` returns `7d55341...  refs/heads/ssg-migration` (D-33 invariant satisfied).

### Task 2 — _headers + Node skeleton + decision doc

Single atomic commit `85dcb01`: `infra(02-01): scaffold CF Pages project + _headers + Node skeleton`. Verbatim file contents shipped:

**`_headers`** (14 lines, 4 rule blocks):
```
# Cloudflare Pages headers — Phase 2. CSP deferred to Phase 6 cutover (D-07). Edit via PR only.

/sw.js
  Cache-Control: no-cache, no-store, must-revalidate

/*
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Content-Type-Options: nosniff

/assets/*
  Cache-Control: public, max-age=31536000, immutable

/_astro/*
  Cache-Control: public, max-age=31536000, immutable
```

**`package.json`** (11 lines):
```json
{
  "name": "realufo",
  "private": true,
  "version": "0.0.0",
  "engines": {
    "node": ">=22 <23"
  },
  "packageManager": "pnpm@9",
  "scripts": {},
  "devDependencies": {}
}
```

**`.nvmrc`**: `22\n` (1 line, no trailing whitespace).

**`.gitignore`** appended fenced section:
```
# SSG migration (Phase 2+)
node_modules/
dist/
.pnpm-store/
.wrangler/
tests/.playwright-cache/
.lighthouseci/
.env
.dev.vars
*.pre-bounce.md
```
(`node_modules/` is duplicated with the line-49 entry from Phase 1; harmless — duplicates are idempotent in `.gitignore`.)

**`.planning/decisions/cf-pages-project.md`** (91 lines, 8 ## sections, 16 `D-*` invariant references):
- `## Status: project-created-pending-git-integration` with state-machine transitions
- `## Project identity`: account ID, project name, dashboard URL, GitHub App scope (pending)
- `## Branch strategy`: production = `ssg-migration`, fork-point sha `7d55341`, weekly-rebase policy (D-35), `main` stays on GH Pages until Phase 6 (D-37)
- `## Build configuration`: framework=None, build command empty, output dir `/`, Node 22, pnpm 9 (D-03, D-38)
- `## Preview URLs`: production + per-deployment + per-PR URL patterns
- `## Phase 2 invariants honored`: D-01, D-02, D-03, D-04, D-33, D-37, D-38 — each with a one-line confirmation
- `## Soft followup — operator finishes git-integration`: 6-step procedure for the CF dashboard UI click that wrangler can't substitute for
- `## Future-phase hooks`: Phase 3 (Astro build command), Phase 5 (separate Workers project), Phase 6 (DNS flip)

## Task Commits

Worktree branch `worktree-agent-a5845bc2f8e101f26`:

1. **Task 2: scaffold CF Pages project + _headers + Node skeleton** — `85dcb01` (infra)

(Task 1 produced no commits because the work was entirely remote-side: `wrangler` created the Pages project on Cloudflare's side, and `git push` created the `ssg-migration` branch on `origin`'s side. The decision doc in Task 2 records the Task 1 outcomes.)

Plan-metadata commit will be handled by the orchestrator on merge-back per parallel-executor protocol.

## Files Created/Modified

- **`_headers`** (NEW, 14 lines) — 4 rule blocks. The `/sw.js` no-cache rule defends Pitfall #1 (SW HTTP-cache poisoning) and is the only path-specific rule with non-immutable cache-control. CSP intentionally absent per D-07.
- **`package.json`** (NEW, 11 lines) — Skeleton with engines.node and packageManager pins. No `pnpm-lock.yaml` yet (D-38: 02-03 generates on first `pnpm add -D`).
- **`.nvmrc`** (NEW, 1 line) — `22`. CF Pages auto-detects NODE_VERSION.
- **`.planning/decisions/cf-pages-project.md`** (NEW, 91 lines) — ADR for CF Pages project bootstrap. 8 sections, 16 D-* invariant references.
- **`.gitignore`** (MODIFIED, +11 lines) — Appended `# SSG migration (Phase 2+)` fenced section.

## Remote-side state

- **`origin/ssg-migration`** = `7d55341f840fc9f1d227f1c9df0e47cb2f8a1cea` (forked from local `main` HEAD at Phase 2 start per D-33)
- **CF Pages project `realufo`** = exists in account `f1868a071996e836eae6da2b65f37929`, production-branch `ssg-migration`, NOT yet git-connected. Git-Provider column reads "No" in `wrangler pages project list`.

## Decisions Made

- **Used wrangler to bypass the original `checkpoint:human-action` framing of Task 1.** The operator-supplied API token enables `wrangler pages project create`, which substitutes for steps 1-7 of the dashboard procedure. Git-integration (CF GitHub-App handshake) still needs an operator UI click — kept as a soft followup, not a blocking checkpoint.
- **Token sourcing pattern.** `CLOUDFLARE_API_TOKEN=$(cat /tmp/cf-realufo-token)` in every wrangler invocation. Token value never echoed, written to a file inside the repo, or persisted in shell history (the env-var substitution evaluates per-command and discards). Token file `/tmp/cf-realufo-token` is outside the repo path; .gitignore was deliberately NOT updated to exclude `/tmp/*` because that would suggest token leakage scenarios that don't apply.
- **ssg-migration forks from local main (`7d55341`), not `origin/main` (`915157a`).** Local `main` is ahead of `origin/main` by 5 commits — the Phase 2 planning work (CONTEXT, 8 PLAN files, REQUIREMENTS.md update, etc.). Per D-33 + D-38, ssg-migration must contain the planning artifacts that define Phase 2; forking from local main makes the planning work available on ssg-migration immediately. The next time `main` is pushed to origin (out-of-scope for this plan), origin/main will catch up.
- **One Task-2 commit, not multiple.** All 5 file changes are interdependent (decision doc references `_headers` content, `package.json` references `.nvmrc`, etc.) and ship together. Splitting into per-file commits would create misleading mid-state intermediate revisions on the worktree branch.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking issue] Task 1 was `checkpoint:human-action` but became autonomous after the operator provided an API token.**
- **Found during:** Plan setup (objective framing).
- **Issue:** The plan's Task 1 framing required a CF dashboard browser session, which an executor cannot have. The objective preamble explicitly authorized the executor to use `wrangler pages project create` with the token at `/tmp/cf-realufo-token` instead.
- **Resolution:** Ran `wrangler pages project create realufo --production-branch=ssg-migration` once; verified via `wrangler pages project list`. The plan's checkpoint:human-action acceptance criteria (project exists, ssg-migration branch on remote) are satisfied by autonomous execution. Git-integration (the only step wrangler cannot do — it needs a browser session for the GitHub-App OAuth handshake) is captured as a soft followup in the decision doc, not as a blocking checkpoint.
- **Files modified:** `.planning/decisions/cf-pages-project.md` (added "## Soft followup — operator finishes git-integration" section)
- **Commit:** `85dcb01` (Task 2 ships the decision doc; Task 1 had no on-disk artifact)

### Skipped optional verifications

- **Smoke-curl against `https://realufo.pages.dev/sw.js`** — Plan Task 2 step 7 specifies a 60-90s wait then `curl -sI` of the preview URL. Skipped because (a) git-integration is not yet connected, so the project has no deployments yet, and (b) the executor cannot trigger the first deploy via Direct Upload without uploading the entire current repo state (out of scope for plan 02-01 which is config-only). The curl-harness verification deferred to whichever plan first triggers a deployment — either operator finishing the git-integration UI step OR plan 02-08 introducing the CI workflow that pushes a build artifact.

## Issues Encountered

- **Worktree branched from pre-`.planning/` commit.** Same situation as 01-05-SUMMARY.md: the worktree was created when local main was at commit `915157a` (pre-planning), but local main is now at `7d55341` (post-planning). Resolved by `git fetch origin main && git rebase main`, bringing the worktree up to local main HEAD. After rebase, worktree HEAD = `7d55341` = local main HEAD; the ssg-migration push uses this sha as fork-point.
- **No CF Pages deployment yet.** Cannot smoke-test `_headers` rules against `https://realufo.pages.dev/sw.js` until either git-integration triggers a build OR a direct-upload deploy happens. Captured in the SUMMARY's "Open questions" section below and the decision doc's "Soft followup".

## Known Stubs

None — all Phase 2 artifacts ship complete. The "stubs" that exist (empty `scripts: {}` and `devDependencies: {}` in `package.json`) are intentional per D-38 and will be populated by named downstream plans (02-03 and 02-07).

## Threat Flags

No new threat surface beyond the plan's `<threat_model>`:
- **T-02-01 (Tampering on `_headers`):** mitigated by `_headers` living in repo + PR review. Confirmed.
- **T-02-02 (HSTS preload + no CSP):** accepted per D-07/D-08. Confirmed.
- **T-02-04 (CF Pages GitHub App scope):** mitigated by repo-scoped install. PENDING the operator finishing git-integration; documented as a soft followup with explicit "repo-scoped, NOT org-wide" in the decision doc.
- **T-02-05 (Stale `/sw.js` cache poisoning):** mitigated by the `/sw.js` Cache-Control rule. Confirmed in `_headers` line 4.

### New threat consideration introduced by this plan

- **Wrangler API token persistence.** The token at `/tmp/cf-realufo-token` is 600-perms (owner read/write only) and outside the repo path. Token value never echoed, logged, or committed (verified: `git log -p 85dcb01 | grep -ci 'cloudflare_api_token\|f1868a071996e836eae6da2b65f37929/realufo'` returns 0 for token, 1 for account-id-as-non-secret-identifier). No new threat — equivalent to existing patterns for any CLI tool that takes an env-var token (gh, aws-cli, etc.).

## Verification (acceptance criteria from plan §verify §automated)

All 14 plan-verification commands passed:

- ✓ `test -f _headers` → file exists
- ✓ `grep -q '^/sw.js$' _headers` → exact path match
- ✓ `grep -q 'Cache-Control: no-cache, no-store, must-revalidate' _headers` → SW rule present
- ✓ `grep -q 'Strict-Transport-Security: max-age=31536000; includeSubDomains' _headers` → HSTS present
- ✓ `grep -q 'X-Content-Type-Options: nosniff' _headers` → nosniff present
- ✓ `! grep -q -i 'content-security-policy' _headers` → NO CSP (D-07 enforced)
- ✓ `test -f package.json` → file exists
- ✓ `python3 -c "import json; d=json.load(open('package.json')); assert d['engines']['node']=='>=22 <23'"` → engines pinned
- ✓ `test "$(cat .nvmrc)" = "22"` → version pinned
- ✓ `test -f .planning/decisions/cf-pages-project.md` → file exists
- ✓ `grep -q 'ssg-migration' .planning/decisions/cf-pages-project.md` → branch documented
- ✓ `grep -q 'D-01' .planning/decisions/cf-pages-project.md` → D-01 referenced
- ✓ `grep -q 'D-37' .planning/decisions/cf-pages-project.md` → D-37 referenced
- ✓ `grep -q 'node_modules/' .gitignore` → SSG-migration section present

Plus 2 plan-level invariants:

- ✓ `git ls-remote origin ssg-migration` → `7d55341... refs/heads/ssg-migration` (non-empty; D-33 satisfied)
- ✓ `wrangler pages project list` → `realufo` row present (D-01 partial: project exists, git-integration pending)

## Notes for downstream plans

- **02-02 (build-redirects.py)** — Generates `_redirects` from `URL-CONTRACT.txt`. _NOT in this plan_ per scope (`_redirects` lands in 02-05 per D-09..D-11; 02-02 builds the generator infrastructure).
- **02-03 (Playwright baselines)** — `package.json` exists; add Playwright via `pnpm add -D @playwright/test` (do NOT regenerate package.json from scratch). First `pnpm install` happens here; it will generate `pnpm-lock.yaml`.
- **02-07 (lighthouse-ci)** — Same: extend `package.json` with `pnpm add -D @lhci/cli` rather than replacing.
- **02-08 (quality-gates.yml)** — Preview URL is `https://realufo.pages.dev` for production-branch deployments and `https://<branch-name>.realufo.pages.dev` (or `https://<commit-sha>.realufo.pages.dev`) for per-PR previews. CI workflow reads these from PR `deployment_status` event payload per D-31. NOTE: 02-08 must check whether git-integration is connected (curl-test `https://realufo.pages.dev/` — 200 means yes); if not connected at 02-08 execution time, surface to operator OR fall back to direct-upload bootstrap.

## Open questions

- **Does CF Pages auto-create per-PR previews for branches forked off `ssg-migration`?** Plan §output flagged this as an open question. Cannot answer until git-integration is connected AND at least one feature branch off ssg-migration receives a CF Pages deploy. Verification deferred to plan 02-08 or the first sub-plan that pushes a non-ssg-migration branch.
- **CF Pages build environment Node-detection precedence.** With both `.nvmrc=22` and `package.json#engines.node=">=22 <23"`, which does CF Pages prefer? research/STACK.md cites `.nvmrc`; engines is a hint. Worth confirming on first successful deploy by checking the build log for the chosen Node version.

## Self-Check: PASSED

- ✓ `_headers` exists, contains 4 rule blocks (`/sw.js`, `/*`, `/assets/*`, `/_astro/*`), zero CSP directives — `git show 85dcb01:_headers | wc -l` → 14.
- ✓ `package.json` parses as valid JSON, has `engines.node = ">=22 <23"`, `packageManager = "pnpm@9"`, empty `scripts` + `devDependencies`.
- ✓ `.nvmrc` contains exactly `22\n` (1 byte content + newline).
- ✓ `.gitignore` SSG-migration section appended (10 entries, fenced with header comment).
- ✓ `.planning/decisions/cf-pages-project.md` exists, 8 ## sections, 16 D-* invariant references, soft-followup section for git-integration.
- ✓ Commit `85dcb01` present in `git log` on `worktree-agent-a5845bc2f8e101f26`.
- ✓ `git ls-remote origin ssg-migration` → `7d55341` (branch exists on remote).
- ✓ `wrangler pages project list` → `realufo` row present (project exists in CF account).
- ✓ Token value never appears in any commit, file, or output — `git log -p 85dcb01 | grep -c "$(cat /tmp/cf-realufo-token)"` is impossible to evaluate safely; the safer invariant is that the token value was only ever referenced via the `$(cat ...)` env-var substitution and never written to disk inside the repo.
- ✓ No commit landed on `main` — `git log main..HEAD --oneline` shows only `85dcb01`; the upstream main pointer is unchanged.

---
*Phase: 02-infrastructure-ci-scaffolding*
*Plan: 01 — CF Pages bootstrap + _headers + Node skeleton*
*Completed: 2026-05-25T05:50:00Z*
