# Phase 2: Infrastructure & CI Scaffolding - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Stand up Cloudflare Pages + Workers Paid plan + freeze fidelity baselines against the current `main` (GitHub Pages production) so every subsequent phase (3 → 6) has objective regression gates to fail against. No SSG code lands in this phase — Astro install is Phase 3. No content migration — that's Phase 4.

Scope: INF-01..08 (8 requirements). Outputs: CF Pages project, `ssg-migration` long-running branch, `_headers` + `_redirects`, Playwright baselines (60 PNGs), `verify-fidelity.py` + samples, tone/JS-off smoke tests, Lighthouse budgets, single `quality-gates.yml` CI workflow.

</domain>

<decisions>
## Implementation Decisions

### CF Pages deploy connection

- **D-01:** **Cloudflare git integration.** CF Pages watches the repo. Every push to `ssg-migration` auto-triggers a build + serves at a stable `*.realufo.pages.dev` preview URL. Simplest path. Secrets live in CF dash, not in GH Actions.
- **D-02:** Production branch in CF Pages settings = `ssg-migration` (NOT `main`). `main` stays on GitHub Pages until the Phase 6 DNS cutover. Two origins coexist for the duration of the migration.
- **D-03:** Build output directory = `dist/` (Astro default — will start populating in Phase 3). Build command stays empty for Phase 2 (no SSG yet); CF Pages will deploy the bare repo as static until Phase 3 installs Astro.
- **D-04:** No wrangler-based GH-Actions deploy step. Wrangler used only for Workers cron (Phase 5), not Pages deploys.

### Cloudflare Workers Paid plan

- **D-05:** **Operator activates Workers Paid plan ASAP** ($5/mo). CF dash → Workers & Pages → upgrade. Required for Phase 5's 15-min CPU cron budget; activating now lets Phase 2 verify limits are live before Phase 5 architecture commits.
- **D-06:** Phase 2 surfaces this as a `checkpoint:human-action` task — Claude can't activate billing. Without activation, Phase 5 cannot start.

### `_headers` content

- **D-07:** **Phase 2 `_headers` = MIME + HSTS + SW cache-control only.** Skip CSP for Phase 2 — the current site is inline-CSS+JS heavy and strict CSP would break it. CSP added in Phase 6 (cutover phase) once SSG markup is settled.
- **D-08:** Explicit pinned rules:
  - `/sw.js` → `Cache-Control: no-cache, no-store, must-revalidate` (prevents browser HTTP-caching of the kill-switch / future real SW — invariant from CONTEXT-01.md D-05..D-08 + research/PITFALLS.md Pitfall #1)
  - Global `Strict-Transport-Security: max-age=31536000; includeSubDomains` (HSTS; preload deferred until Phase 6 verifies all subdomains)
  - `Cache-Control: public, max-age=31536000, immutable` for `/assets/*`, `/_astro/*` (when Phase 3+ generates them)
  - `X-Content-Type-Options: nosniff` globally

### `_redirects` source

- **D-09:** **Auto-generate `_redirects` from URL-CONTRACT.txt.** Script `scripts/build-redirects.py` reads URL-CONTRACT.txt, emits one line per route as `<path> <path> 200` (CF Pages syntax — `200` keeps URL in browser bar, no 30x). Regenerate on every push as a CI step.
- **D-10:** CF Pages default is 302 for missing routes — explicit 301/200 entries override. Phase 4 SSG output may reshape URLs; the auto-regen script ensures `_redirects` stays in sync with whatever URL-CONTRACT.txt says is canonical at build time.
- **D-11:** No hand-written entries in `_redirects` for Phase 2. If a URL ever needs a true 301 (e.g., a folded archive page), add to URL-CONTRACT.txt with a `→ target 301` annotation; `build-redirects.py` parses the annotation.

### Playwright visual-regression baselines

- **D-12:** **Capture baselines against live <https://realufo.org>** (GitHub Pages production). Hits the real-user-served version. Pixel-true to what users see today. This is the lock — the SSG output in Phase 3+ must match these PNGs.
- **D-13:** Baselines stored as raw PNGs in `tests/visual-baselines/<archive>-<viewport>.png` (15 archives × 4 viewports = **60 PNGs**). Tracked in git directly (not LFS) — PNG file size is small at these viewports (~50–200 KB each, ~6 MB total, acceptable).
- **D-14:** Viewports: 360 / 768 / 1024 / 1440 (mobile / tablet / desktop / wide — per ROADMAP SC#4).
- **D-15:** Playwright runs in headless Chromium only for Phase 2. No Firefox / WebKit cross-browser matrix yet (defer to Phase 4 if needed).
- **D-16:** Pixel-diff threshold = 0.1 % (per ROADMAP SC#4). Larger diffs hard-fail the PR.
- **D-17:** Baselines NEVER regenerated automatically. Operator must explicitly delete + re-capture to acknowledge an intentional visual change (this is the entire point of the gate).

### `verify-fidelity.py` byte-equivalent gate

- **D-18:** **Fidelity sample list (hand-curated, locked):**
  - Hero ledes (h1.hero-title + p.hero-sub) for all 15 archive pages
  - FAQ accordion answers (where present — at minimum root index.html FAQ)
  - License footer text per archive (public-domain attribution per jurisdiction — CLAUDE.md §9)
  - Official titles in card data (sampled — first 5 per archive)
- **D-19:** Samples extracted ONCE from current `main` via `scripts/extract-fidelity-samples.py` → `tests/fidelity-samples.json`. Committed and frozen. Phase 3+ output must match byte-equivalent.
- **D-20:** `scripts/verify-fidelity.py` compares each sample against the corresponding text on the SSG output (CF Pages preview). Strips leading/trailing whitespace ONLY — no other normalization. Smart quotes, em-dashes, accents must round-trip exactly.
- **D-21:** Fails loudly with a unified diff per mismatched sample.

### Tone-colour smoke test

- **D-22:** `scripts/test-tone-colours.py` (or `.js` running in Playwright context) reads each archive page, queries `getComputedStyle(document.documentElement).getPropertyValue('--caution')`, asserts the result matches the `CLAUDE.md §3.1` table for that archive.
- **D-23:** Runs in CI as a Playwright job. One assertion per archive. Hard fail.

### JS-off rendering test

- **D-24:** Playwright job launches Chromium with `javaScriptEnabled: false`, visits each archive page, asserts:
  - At least one card is visible (page has rendered card markup, not just a loader)
  - At least one heading is visible
  - No "Enable JavaScript" or "loading" placeholder text dominates the viewport
- **D-25:** Hard fail. Required because Phase 3 SSG must pre-render cards, not hydrate from JSON (per PROJECT.md core architecture).

### Lighthouse budgets

- **D-26:** Lighthouse mobile profile + 4× CPU throttle (per ROADMAP SC#6).
- **D-27:** Budgets: LCP ≤ 2.5 s, total transfer ≤ 500 KB per archive page.
- **D-28:** **Soft fail (warn only) for Phase 2 and Phase 3.** Hard-fail switch-over happens at Phase 4 close once PERF-01 GEIPAN refactor lands. Phase 2/3 budget warnings appear in PR but don't block merge — lets iteration happen.

### CI workflow structure

- **D-29:** **Single workflow file**: `.github/workflows/quality-gates.yml`. Triggers on every push + every PR.
- **D-30:** Parallel jobs (5):
  - `visual-regression` (Playwright vs `tests/visual-baselines/*.png`)
  - `fidelity` (Python `verify-fidelity.py` vs `tests/fidelity-samples.json`)
  - `tone-colours` (Playwright getComputedStyle vs CLAUDE.md §3.1)
  - `js-off` (Playwright with JS disabled)
  - `lighthouse` (lighthouse-ci action, mobile + throttle, soft fail per D-28)
- **D-31:** Each job runs against the CF Pages preview URL for the PR's branch (CF Pages exposes a per-PR preview URL via webhook → GH Actions can read it from the PR's deployment status).
- **D-32:** Existing CI workflows (`html-validate`, `lychee`, `lighthouse`, `sync-nav-drift`, `sync-footer-drift`) stay running on `main` during Phase 2. Phase 4 deletes the sync-nav / sync-footer drift gates (replaced by Astro shared components).

### Branch strategy

- **D-33:** **`ssg-migration` long-running branch** created from `main` at start of Phase 2. All Phase 2..5 commits land here. Phase 6 fast-forward-merges to `main` at cutover.
- **D-34:** `main` continues to receive Phase 1 follow-up commits (DNS verification log, Akamai spike results, SW deploy timestamp) — those don't touch the SSG, so no merge conflicts expected.
- **D-35:** Rebase `ssg-migration` against `main` weekly (or whenever a non-SSG main commit lands) to keep merge cost zero.

### Cross-cutting

- **D-36:** Workers Paid plan activation (D-05) is the only operator action gating Phase 2 completion. Everything else Claude can execute.
- **D-37:** Phase 2 does NOT touch the DNS swap or domain config — `realufo.org` stays pointed at GH Pages until Phase 6. CF Pages preview URLs (`*.pages.dev`) are sufficient for all Phase 2/3/4/5 work.
- **D-38:** No SSG code commits in this phase. Any temptation to "install Astro while I'm here" → reject, that's Phase 3.

### Claude's Discretion

- Exact filenames of helper scripts (`build-redirects.py`, `extract-fidelity-samples.py`, `test-tone-colours.{py,js}`, `verify-redirects.sh`) — name to match `scripts/` conventions
- Whether tone-colour test lives in Python or Playwright JS — pick whichever maps cleanly
- GH Actions runner choice (`ubuntu-latest` likely)
- Lighthouse-CI action version
- Whether to share Playwright config across all jobs or duplicate
- Specific GitHub event triggers (push to ssg-migration vs PR vs both)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & milestone
- `.planning/PROJECT.md` — Locked stack: Astro 5 / CF Pages / Workers cron / Cloudflare DNS / pre-rendered cards
- `.planning/REQUIREMENTS.md` — INF-01..08 (this phase); SSG-* (Phase 3 — informs what gates must catch); PERF-* (Phase 4 — informs Lighthouse budget targets)
- `.planning/ROADMAP.md` §Phase 2 — Goal + 6 success criteria

### Research informing this phase
- `.planning/research/STACK.md` — CF Pages limits (25 MiB file, 100k files, 20 min build, 500 builds/month); Workers Paid plan rationale ($5/mo, 15 min CPU); `@vite-pwa/astro` (Phase 3 dep); Pagefind (Phase 4 dep)
- `.planning/research/PITFALLS.md` — Pitfall #1 (SW cache poisoning → drives `/sw.js` no-cache header in D-08); Pitfall #2 (URL drift → drives `_redirects` auto-gen in D-09..D-11); Pitfall #6 (markdown typographer drift → drives strict `verify-fidelity.py` in D-20); Pitfall #11 (CF Pages `_redirects` syntax gotchas); CF Pages defaults to 302 (D-10)
- `.planning/research/ARCHITECTURE.md` — pre-rendered cards architecture (drives JS-off test in D-24..D-25)
- `.planning/research/SUMMARY.md` — phase ordering rationale

### Phase 1 outputs feeding Phase 2
- `URL-CONTRACT.txt` — input to `build-redirects.py` (D-09) and `extract-fidelity-samples.py` (D-19)
- `scripts/snapshot-urls.py` — pattern reference for URL-walking conventions
- `sw.js` — kill-switch SW; `/sw.js` cache-control rule (D-08) MUST land in `_headers` before any user receives the kill-switch
- `.planning/phases/01-pre-migration-safety/01-CONTEXT.md` — D-05..D-08 (SW invariants Phase 2 must preserve)
- `.planning/decisions/dns-ttl.md` — DNS migration to Cloudflare path (informs Phase 6, not Phase 2 directly)

### Existing project conventions
- `CLAUDE.md` §3.1 (tone colour table — fixture for D-22 smoke test)
- `CLAUDE.md` §7 (JS invariants — Phase 2 doesn't touch these, but Phase 3+ Astro output must preserve them)
- `CLAUDE.md` §8 (mobile-first; 360 px baseline matches D-14 viewport list)
- `CLAUDE.md` §9 (content rules; verbatim text is fixture for D-18 fidelity samples)
- `.planning/codebase/CONVENTIONS.md` — Python script style + GH Actions patterns

### External docs (planner reads on-demand)
- Cloudflare Pages limits (`https://developers.cloudflare.com/pages/platform/limits/`)
- Cloudflare Pages `_headers` syntax (`https://developers.cloudflare.com/pages/configuration/headers/`)
- Cloudflare Pages `_redirects` syntax (`https://developers.cloudflare.com/pages/configuration/redirects/`)
- Cloudflare Pages preview deployments (`https://developers.cloudflare.com/pages/configuration/preview-deployments/`)
- Playwright visual comparisons (`https://playwright.dev/docs/test-snapshots`)
- Lighthouse-CI GitHub Action (`https://github.com/treosh/lighthouse-ci-action`)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/snapshot-urls.py` (Phase 1) — file-walking + JSON-manifest parsing pattern. `build-redirects.py` follows the same shape. `extract-fidelity-samples.py` also extends it (walks tracked HTML, extracts specific text nodes).
- `scripts/sync-nav.py` / `scripts/sync-footer.py` (legacy) — example of tracked-HTML mutators with `git ls-files` traversal. Useful pattern reference. They get deleted in Phase 4.
- `scripts/build-sw.py` — version-stamping pattern (sha + date). `build-redirects.py` could borrow this to stamp `_redirects` with origin sha.
- 15 archive `index.html` files + root `index.html` + `search.html` + utility pages (timeline, map, whatsnew, etc.) — all already on disk for baseline capture.

### Established Patterns
- All Python scripts: stdlib-only, `git ls-files` for tracked detection, `os.listdir` fallback, idempotent re-runs
- All shell scripts: realistic Chrome UA, idempotent, Wayback fallback (only relevant for scraper, not Phase 2)
- GH Actions workflows currently in `.github/workflows/` — existing patterns to study before adding `quality-gates.yml`
- No existing Playwright setup — Phase 2 introduces it from scratch (`playwright.config.ts` + `tests/` folder)
- No existing Lighthouse-CI — Phase 2 introduces

### Integration Points
- CF Pages preview URLs accessible to GH Actions via the PR's `deployment_status` event payload (CF Pages → GH Pages-style deployment integration). Workflow waits for `state: success` then reads `environment_url`.
- CF Pages account: `f1868a071996e836eae6da2b65f37929` (from user-supplied dash URL)
- CF Pages project name: `realufo` (proposed — operator confirms during INF-01 execution)
- Webhook: GH ↔ CF Pages — CF Pages installs a GH App into the repo automatically; no manual webhook config

### Things Phase 2 ADDS to the repo (planner inventory)
- `.github/workflows/quality-gates.yml`
- `tests/visual-baselines/*.png` (60 files)
- `tests/fidelity-samples.json`
- `tests/playwright.config.ts`
- `tests/visual-regression.spec.ts`
- `tests/tone-colours.spec.ts`
- `tests/js-off.spec.ts`
- `scripts/build-redirects.py`
- `scripts/extract-fidelity-samples.py`
- `scripts/verify-fidelity.py`
- `scripts/verify-redirects.sh` (curl harness against preview URL)
- `_headers` (repo root)
- `_redirects` (repo root — auto-generated, may be `.gitignore`d in Phase 4 if regen-on-build is fast enough)
- `package.json` + `pnpm-lock.yaml` (Playwright + lighthouse-ci dev deps; NO Astro yet — Astro = Phase 3)

</code_context>

<specifics>
## Specific Ideas

- CF Pages project name: `realufo` (short, matches the domain). Preview URL pattern: `<commit-sha>.realufo.pages.dev` + production-branch URL `realufo.pages.dev`.
- The `_redirects` builder MUST handle the trailing-slash equivalence — CF Pages treats `/aaro` and `/aaro/` as distinct. Generator emits both → canonical form (with-slash) explicitly.
- For visual regression, tile diff images into a single side-by-side preview in PR comments via `actions/upload-artifact` + a comment bot. Optional polish — defer if planner sees scope creep risk.
- `verify-fidelity.py` should output diffs in `--color=always` so PR logs are readable.
- Baseline capture script (`scripts/capture-baselines.py` or similar) — operator runs ONCE against live realufo.org. Subsequent CI uses the captured PNGs as fixtures, never re-captures.

</specifics>

<deferred>
## Deferred Ideas

- **Cross-browser visual regression matrix (Firefox + WebKit)** — defer to Phase 4 if Chromium-only proves insufficient.
- **CSP enforcement** — defer to Phase 6 (cutover phase) per D-07.
- **HSTS preload submission** — defer until Phase 6 verifies all subdomains carry HSTS.
- **CF Pages-native lighthouse hook** — rejected (D-29 stays GH Actions for portability).
- **Wrangler-based Pages deploy** — rejected (D-01 uses CF git integration).
- **Hard-fail Lighthouse budgets** — deferred to Phase 4 close per D-28.
- **PR comment bot for visual diff previews** — optional polish per §specifics; planner's discretion.
- **R2 for visual-baseline storage** — overkill at 60 PNGs ~6 MB; raw git tracking is fine (D-13).
- **`_headers` for `/api/*` paths** — no APIs in this project; if added in Phase 5 (scrape pipeline), revisit.
- **Workers Paid plan auto-activation via API** — not possible; billing requires UI interaction.

### Reviewed Todos (not folded)
None — no pending todos matched this phase.

</deferred>

---

*Phase: 02-infrastructure-ci-scaffolding*
*Context gathered: 2026-05-25*
