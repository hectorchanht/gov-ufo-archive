# CF Pages Project Decision — realufo

Third ADR-style decision document under `.planning/decisions/` (after
`akamai-spike.md` from plan 01-03 and `dns-ttl.md` from plan 01-04).
Records the Cloudflare Pages project bootstrap performed in Phase 2 plan
02-01 — the long-running SSG-migration preview origin against which every
Phase 2-5 CI gate runs.

## Status

`project-created-pending-git-integration` — CF Pages project `realufo`
exists in account `f1868a071996e836eae6da2b65f37929`, created via
`wrangler pages project create` at 2026-05-25 (this plan). The project
serves at `https://realufo.pages.dev/` but is not yet bound to the
`hectorchanht/gov-ufo-archive` GitHub repo — that step requires a
browser-session click in the CF dashboard (CF's GitHub-App flow has no
public CLI surface). Transitions: `project-created-pending-git-integration`
→ `git-connected` (operator completes UI step) → `first-build-success`
(CF Pages auto-builds the first push to `ssg-migration`).

## Project identity

- **CF account ID:** `f1868a071996e836eae6da2b65f37929` (user `f147259@gmail.com`)
- **CF Pages project name:** `realufo`
- **Production preview URL:** `https://realufo.pages.dev/`
- **Per-deployment URL pattern:** `https://<commit-sha>.realufo.pages.dev/`
- **Per-branch URL pattern:** `https://<branch-name>.realufo.pages.dev/`
- **CF dashboard URL:** `https://dash.cloudflare.com/f1868a071996e836eae6da2b65f37929/pages/view/realufo`
- **Creation method:** `wrangler pages project create realufo --production-branch=ssg-migration` (wrangler 4.94.0)
- **GitHub App install scope (pending):** operator-scoped to `hectorchanht/gov-ufo-archive` only — NOT org-wide (T-02-04 mitigation per 02-01-PLAN.md)

## Branch strategy

- **Production branch (CF Pages setting):** `ssg-migration` (NOT `main` — per D-02, D-33)
- **`ssg-migration` fork point at Phase 2 start:** `7d55341f840fc9f1d227f1c9df0e47cb2f8a1cea` (local `main` HEAD at 2026-05-25 — the tip of the phase-2-plans planning commits; `docs(02): create phase plan (8 plans, 4 waves) + REQUIREMENTS.md INF-02 CSP-deferral note`)
- **`ssg-migration` remote created:** 2026-05-25 via `git push origin HEAD:refs/heads/ssg-migration`
- **Weekly-rebase policy:** D-35 — rebase `ssg-migration` onto `main` weekly (or whenever a non-SSG `main` commit lands) to keep merge cost zero
- **`main` continues on GH Pages until Phase 6:** D-37 — no DNS swap in Phase 2; `realufo.org` stays pointed at `185.199.108-111.153` (GitHub Pages anycast block per `.planning/decisions/dns-ttl.md`)

## Build configuration

- **Framework preset:** `None` (Phase 2 has no SSG — D-03, D-38; Astro arrives in Phase 3)
- **Build command:** empty (no SSG to build; CF Pages serves repo root as static)
- **Build output directory:** `/` (repo root for Phase 2; switches to `dist/` in Phase 3 when Astro lands per D-03)
- **Root directory:** `/`
- **Node version:** `22` (pinned via `.nvmrc` and `package.json#engines.node = ">=22 <23"`; CF Pages auto-detects from `.nvmrc` per research/STACK.md §"Node.js 22 LTS")
- **Package manager:** `pnpm@9` (pinned via `package.json#packageManager`; no `pnpm install` runs until plan 02-03 adds Playwright per D-38)

## Preview URLs

- **Production (ssg-migration branch) URL:** `https://realufo.pages.dev/`
- **Per-deployment URL pattern:** `https://<commit-sha>.realufo.pages.dev/` (read by `quality-gates.yml` from PR `deployment_status` event payload per D-31)
- **Per-PR URL pattern:** `https://<branch-name>.realufo.pages.dev/` (active once git-integration is connected; open-question per 02-01-PLAN.md §output — confirm by pushing a feature branch off ssg-migration and observing)
- **Smoke verification status:** PENDING — first deploy requires either (a) operator completing CF dash → Connect to Git, or (b) a `wrangler pages deploy` direct-upload run. Phase 2 plan 02-08 (CI quality-gates workflow) reads from this URL; if git-integration is still pending at 02-08 execution time, fall back to direct-upload bootstrap.

## Phase 2 invariants honored

- **D-01:** Cloudflare git integration is the deploy path (no GH-Actions wrangler step). CF Pages project exists; the GitHub App install pending operator UI click is the only remaining step for full D-01 compliance. _(Soft followup.)_
- **D-02:** Production branch in CF Pages settings is `ssg-migration`, NOT `main`. Set at project-creation time via `wrangler pages project create realufo --production-branch=ssg-migration`. `main` stays on GH Pages until Phase 6.
- **D-03:** Build command empty, output dir `/`, framework preset `None`. Phase 3 (Astro install) will edit these fields.
- **D-04:** No wrangler-based GH-Actions deploy step. Wrangler used here ONLY for project creation; runtime deploys go via CF git-integration.
- **D-33:** `ssg-migration` long-running branch created from `main` HEAD `7d55341` at Phase 2 start. All Phase 2-5 commits land here. Phase 6 fast-forward-merges to `main` at cutover.
- **D-37:** Phase 2 does NOT touch DNS or domain config. `realufo.org` continues to resolve to GitHub Pages (`185.199.108-111.153`). CF Pages preview URLs (`*.pages.dev`) are sufficient for all Phase 2/3/4/5 work.
- **D-38:** No SSG code, no Astro install, no `pnpm install` in this phase. `package.json` is a skeleton with empty `scripts` + `devDependencies`. Plan 02-03 adds Playwright dev-dep; plan 02-07 adds lighthouse-ci.

## Soft followup — operator finishes git-integration

The Cloudflare Pages GitHub App install requires an interactive browser session
against the CF dashboard. `wrangler` does not expose this step (CF treats the
GH App handshake as account-level OAuth and the create-project CLI cannot
substitute for it). To complete D-01:

1. Visit `https://dash.cloudflare.com/f1868a071996e836eae6da2b65f37929/pages/view/realufo`
2. Click "Connect to Git" (Settings → Builds & deployments) → "Connect a Git provider" → GitHub
3. Authorize CF Pages GitHub App for the `hectorchanht/gov-ufo-archive` repo (repo-scoped, NOT org-wide — T-02-04 mitigation)
4. Confirm production branch reads `ssg-migration` (already set from `wrangler` step; UI may ask to re-confirm)
5. CF Pages auto-triggers a first build on the latest `ssg-migration` commit. Wait for Deployments tab → row "Success".
6. Smoke-test:
   ```
   curl -sI https://realufo.pages.dev/sw.js | grep -i cache-control
   curl -sI https://realufo.pages.dev/ | grep -iE 'strict-transport|content-type-options'
   ```
   Expected: `Cache-Control: no-cache, no-store, must-revalidate` on `/sw.js`; `Strict-Transport-Security: max-age=31536000; includeSubDomains` + `X-Content-Type-Options: nosniff` on `/`.

Until step 1-6 complete, Phase 2 plans 02-03..02-08 that depend on a live preview URL must either (a) defer to direct-upload bootstrap via `wrangler pages deploy`, or (b) wait for the operator action. Plan 02-08's CI gate-suite specifically depends on this — flag in 02-08-PLAN.md if still pending at that point.

## Future-phase hooks

- **Phase 3 (Astro install)** edits this doc's `## Build configuration` section: build command becomes `pnpm build`, output dir switches `/` → `dist/`, framework preset becomes `Astro`.
- **Phase 5 (scrape automation)** introduces a separate Workers project (not Pages) for the scheduled cron; does NOT touch this Pages project's settings.
- **Phase 6 (cutover)** flips DNS at Cloudflare DNS dash (D-37) — apex `A` records change from `185.199.108-111.153` (GitHub Pages) to the CF Pages CNAME-flattening target. This decision doc gets a new `## Cutover Log` section at that point.
