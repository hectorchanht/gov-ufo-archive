# Phase 3: SSG Foundation - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Bring Astro 5.x up alongside the existing Python build scripts. Define Content Collections schema for all 15 archives (Zod + file() loader on normalized `data/<slug>.json`). Build shared layout components (`RootLayout`, `BaseHead`, `Nav`, `Footer`). Port one small archive (wargov, at root `/`) end-to-end as a working proof — passes all Phase 2 gates (visual regression, fidelity byte-match, tone colour, JS-off, Lighthouse mobile budget).

**In scope:** Astro scaffold + schema for all 15 + shared layouts + wargov port.
**Out of scope:** Other 14 archives (Phase 4 SSG-06). Pagefind search (Phase 4 SRC). injectManifest SW (Phase 4 SW). PERF-01 GEIPAN sharding (Phase 4). DNS swap (Phase 6).

Scope: SSG-01..05 (5 requirements).

</domain>

<decisions>
## Implementation Decisions

### Data extraction & content collections

- **D-01:** **Build `data/<slug>.json` from CSV sources directly.** No HTML extraction pass. The content-collection loader normalizes at build time from `uap-release001.csv` (wargov source-of-truth, untouchable per CLAUDE.md §11) + per-archive scraped JSON in `<slug>/.cache/`. Reuses normalize logic already proven in current Python `build-*.py` scripts (port to TypeScript or invoke Python from Astro integration).
- **D-02:** Content Collections defined for **all 15 archives** in Phase 3 (per SSG-02), even though only wargov ships rendered HTML. Schema covers `assets[]` (catalog shape — AARO, NASA, NARA, etc.) AND `rows[]` (CSV-keyed shape — wargov, NARA-style rows). Use Zod `union` or per-archive variant types. Phase 4 14-archive port uses the same schema without modification.
- **D-03:** Zod schema lives at `src/content.config.ts`. `file()` loader reads `data/<slug>.json` for each archive. Build fails LOUDLY (not silently) on schema-incompatible rows per SSG-02 — Zod throws + Astro propagates.
- **D-04:** `data/<slug>.json` is committed (not gitignored). Build-time CSV→JSON normalization runs as `pnpm prebuild` script before Astro build. Re-runnable + idempotent.

### URL structure

- **D-05:** **wargov stays at `/`** (root) per CLAUDE.md §2 + URL-CONTRACT.txt. `src/pages/index.astro` renders the wargov archive page. NO URL drift.
- **D-06:** Other 14 archives (Phase 4) live at `/[archive]/` via dynamic `src/pages/[archive]/index.astro`. wargov is the special case — its route maps to the wargov content collection.
- **D-07:** Utility pages (`/search.html`, `/timeline.html`, `/map.html`, `/about.html`, etc.) — Phase 3 leaves on GH Pages (Python-built). Astro port deferred to Phase 4 / Phase 6.

### Card pre-render strategy

- **D-08:** **Pre-render first 50 cards as HTML + lazy-load rest** (per Phase 2 D-04 pre-rendered invariant). wargov is ~200 records; rendering 50 keeps initial HTML weight ≤ Phase 2's 500 KB target while proving the lazy-load pattern Phase 4 will need for GEIPAN (3.3 MB).
- **D-09:** JS lazy-load reads `data/wargov-page-2.json` (etc.) on idle/filter — same shard pattern Phase 4 PERF-01 will apply at scale. Phase 3 establishes the seam.
- **D-10:** Lazy-loaded cards STILL pre-rendered server-side as HTML strings stored in shards (not raw data — keeps the no-hydration invariant).
- **D-11:** Cards' `data-*` attributes power progressive enhancement (lightbox, filter, sort) per CLAUDE.md §7 JS invariants. No client-side card data manipulation — filter operates on rendered DOM `data-*`.

### Build coexistence

- **D-12:** **Astro `dist/` is CF Pages' build output.** Python-built `<slug>/index.html` files stay tracked in git on `ssg-migration` but CF Pages ignores them (build command = `pnpm build` → `dist/`).
- **D-13:** Existing Python build artifacts remain on `main` for GH Pages until Phase 6 cutover. Two origins serve the same domain via different builds during migration:
  - `realufo.org` → GH Pages (main, Python output)
  - `<commit>.realufo.pages.dev` → CF Pages (ssg-migration, Astro `dist/`)
- **D-14:** `pnpm build` command in Phase 3 emits ONLY wargov + utility chrome. Other 14 archive folders inside `dist/` either absent (404s gracefully) OR populated from Python build via prebuild copy hook (decision: planner's discretion based on CF Pages 4xx routing).
- **D-15:** `.gitignore` adds `dist/` (per Phase 2 02-01 commit). NOT ignored: `_headers`, `_redirects` (CF Pages reads from repo root).

### Shared layout components

- **D-16:** **Four components**: `RootLayout.astro`, `BaseHead.astro`, `Nav.astro`, `Footer.astro` (per ROADMAP SC#3). Standard Astro pattern.
- **D-17:** `RootLayout.astro` — top-level wrapper. Imports `BaseHead`, `Nav`, `Footer`. Takes props: `title`, `description`, `archiveSlug` (drives tone colour CSS variable + seal gradient + canonical/og meta).
- **D-18:** `BaseHead.astro` — `<head>` content: meta tags, favicon, `<script>` SW registration with `{ updateViaCache: 'none' }` (per Phase 2 D-08 / Phase 1 SW kill-switch invariant), preconnect to fonts, CSS link tag.
- **D-19:** `Nav.astro` — sticky 64 px header per CLAUDE.md §4. Hamburger toggle (CLAUDE.md §7 invariant). Archive-to-archive cross-links. Single source of truth — eliminates `sync-nav.py` (deletion deferred to Phase 4 per SSG-10).
- **D-20:** `Footer.astro` — Source-list (official URLs), public-domain license per archive (CLAUDE.md §9). Single source of truth — eliminates `sync-footer.py`.

### JS invariants port

- **D-21:** **`<script is:inline>` blocks in shared layout components.** Vanilla JS bundled inline. Matches current CLAUDE.md §7 architecture. Zero hydration cost. Survives JS-off test (cards pre-rendered, JS is progressive enhancement only).
- **D-22:** Inline scripts cover: hamburger toggle, lightbox prev/next/swipe/arrow-keys/Escape, image-fallback `onerror`, video dual-source, PDF lightbox iframe-vs-newtab, `/` keydown focus search input, `?q=` URL persistence on search input, search-result-link `#card-<id>` anchor scroll.
- **D-23:** NO React / Vue / Svelte islands. NO `client:load` / `client:visible` directives. Pure Astro `<script is:inline>`. Reject any framework-hydration proposal at planning gate.

### Search behavior in Phase 3

- **D-24:** **NO search on wargov in Phase 3.** Pagefind (Phase 4 SRC-01) deferred. wargov has filter inputs (per-page filter/sort on already-rendered DOM) but no cross-archive search box.
- **D-25:** `/search.html` stays on GH Pages (Python-built, Lunr-based) until Phase 4 SRC-02. wargov's nav links to `/search.html` continue working via GH Pages.

### Fidelity strictness

- **D-26:** **Byte-exact fidelity required.** All 115 fidelity samples (Phase 2 INF-05) MUST match byte-for-byte per Phase 2 D-20 — strip leading/trailing whitespace ONLY, no other normalization. Smart quotes, em-dashes, accents (é/ñ/ç), zero-width chars round-trip exact through Astro templates.
- **D-27:** `verify-fidelity.py` is HARD-fail on Phase 3 wargov port. If Astro emits typographer-rewritten quotes (`"` → `"`) — STOP and fix the template/MDX processor, do NOT soften the gate.
- **D-28:** Markdown processors that auto-rewrite typography (smartypants, remark-smartypants) are BANNED for archive card data. Reserved only for prose pages (about, FAQ — Phase 4 scope).

### Astro version

- **D-29:** **Pinned `~5.18.0`** (NOT `^5`, NOT `5.x`). Defends against accidental Astro 6 upgrade (CF adapter regression per research/PITFALLS.md). Re-verify [astro#15684](https://github.com/withastro/astro/issues/15684) status during Phase 3 planning; if fixed, can pin `~5.x` (latest).
- **D-30:** `@astrojs/cloudflare` adapter pinned to compatible 5.x version. Document version in `.planning/decisions/astro-version-pin.md` (new ADR).
- **D-31:** Build command in CF Pages: `pnpm install --frozen-lockfile && pnpm prebuild && pnpm build`. Output dir: `dist/`.

### Build pipeline ordering

- **D-32:** `pnpm prebuild` runs CSV→JSON normalization (D-04). Reads `uap-release001.csv` + `<slug>/.cache/*.json`. Writes `data/*.json`. Idempotent.
- **D-33:** `pnpm build` runs Astro build. Reads `data/*.json` via content-collection loader. Emits `dist/`. Astro 5 incremental builds OK.
- **D-34:** Phase 2 `_redirects` auto-gen (scripts/build-redirects.py) becomes part of CF Pages build hook OR runs separately on push. Decision: planner's call.

### Phase 3 wargov port acceptance

- **D-35:** wargov port passes EVERY Phase 2 gate before Phase 3 closes:
  - Visual regression: 4 viewports (360/768/1024/1440), pixel-diff ≤ 0.001 vs `tests/visual-baselines/wargov-*.png`
  - Fidelity: 115/115 samples match byte-equivalent
  - Tone colour: `--caution: #d4a017` (wargov gold per CLAUDE.md §3.1)
  - JS-off rendering: cards + headings visible without JS
  - Lighthouse mobile: LCP ≤ 2.5 s, transfer ≤ 500 KB (soft warn for Phase 3 per Phase 2 D-28)
- **D-36:** CF Pages preview URL (e.g. `<commit>.realufo.pages.dev`) hits all 6 quality-gates.yml CI jobs on PR. Hard-fail gates (visual / fidelity / tone / js-off / redirects) must be green.

### Cross-cutting

- **D-37:** No DNS / domain changes in Phase 3 (CONTEXT-02 D-37 invariant). `realufo.org` stays on GH Pages until Phase 6.
- **D-38:** No SW changes in Phase 3 beyond the BaseHead registration (already present from Phase 1 kill-switch on main). injectManifest SW lands in Phase 4 SW-01.
- **D-39:** No Python build script deletion in Phase 3 (SSG-10 = Phase 4 scope). Coexistence per D-12..D-15.
- **D-40:** wargov port must NOT regress URL-CONTRACT.txt entries for `/` or any `#card-<id>` anchor (Phase 1 PMS-01 contract).

### Claude's Discretion

- Exact Zod schema shape (union types vs discriminated unions vs per-archive variants)
- TypeScript vs Python for `pnpm prebuild` CSV normalizer (Python easier — reuses existing logic; TS more idiomatic for Astro)
- Lazy-load trigger (idle vs filter-event vs IntersectionObserver)
- Card shard size (50 records is starting point; planner may tune)
- @astrojs/cloudflare adapter version (latest compatible with Astro 5.18.x)
- `<style>` strategy: scoped Astro styles vs single global stylesheet
- Whether `pnpm prebuild` lives in package.json scripts or as Astro integration hook
- Whether `data/*.json` is per-archive single file or split (e.g., `wargov.json` + `wargov-page-2.json` for shards)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & milestone
- `.planning/PROJECT.md` — Locked stack (Astro 5 / CF Pages / Workers cron / Cloudflare DNS / big-bang migration)
- `.planning/REQUIREMENTS.md` — SSG-01..05 (this phase); SSG-06..12 + SRC + SW + PERF (Phase 4 — informs schema design)
- `.planning/ROADMAP.md` §Phase 3 — Goal + 5 success criteria

### Research informing this phase
- `.planning/research/STACK.md` — Astro 5.x pinning rationale + `@astrojs/cloudflare` + `@vite-pwa/astro` (Phase 4 dep)
- `.planning/research/ARCHITECTURE.md` — Content Collections per archive, file() loader, pre-rendered cards, shared layout components
- `.planning/research/PITFALLS.md` — Pitfall #1 (SW cache → BaseHead SW registration), #6 (markdown typographer drift → D-28 BAN smartypants), #15 (DNS TTL — informs Phase 6, not Phase 3)
- `.planning/research/SUMMARY.md` — phase ordering

### Phase 1 + 2 outputs Phase 3 consumes
- `URL-CONTRACT.txt` — Phase 3 wargov port must preserve every `/` and `#card-<id>` entry (D-40)
- `_headers` (Phase 2) — `/sw.js` no-cache + HSTS + asset immutable; CF Pages reads this
- `_redirects` (Phase 2) — auto-gen from URL-CONTRACT.txt; trailing-slash rewrites
- `tests/visual-baselines/wargov-*.png` (60 PNGs) — Phase 3 wargov port must match these (D-35)
- `tests/fidelity-samples.json` (115 records) — Phase 3 must NOT drift (D-26..D-27)
- `tests/playwright.config.ts` + `tests/visual-regression.spec.ts` + `tests/tone-colours.spec.ts` + `tests/js-off.spec.ts` — Phase 3 wargov tested against these
- `scripts/verify-fidelity.py` (Phase 2 INF-05) — hard-fail gate on wargov port
- `.lighthouserc.cf.json` + `scripts/verify-lighthouse-budgets.py` (Phase 2 INF-08) — soft-warn budgets
- `.github/workflows/quality-gates.yml` (Phase 2 02-08) — 7 jobs run on every Phase 3 PR
- `.planning/decisions/cf-pages-project.md` — CF Pages project `realufo` + production branch `ssg-migration`
- `.planning/decisions/workers-paid.md` — Workers Paid active (Phase 5 dep, not Phase 3)

### Existing project conventions
- `CLAUDE.md` §2 (Sources covered — wargov at `/`)
- `CLAUDE.md` §3 (design system — locked; tone colour fixture)
- `CLAUDE.md` §3.1 — wargov primary = `#d4a017` (gold), seal gradient
- `CLAUDE.md` §4 (Page architecture — Astro components mirror this skeleton)
- `CLAUDE.md` §7 (JS invariants — D-21..D-23 ports verbatim)
- `CLAUDE.md` §8 (mobile-first 360 px / 44 px touch targets)
- `CLAUDE.md` §9 (content rules — verbatim text, no filler, license attribution)
- `CLAUDE.md` §11 (don'ts — esp. no force-push, no `crossorigin="anonymous"` on `<video>`)
- `CLAUDE.md` §13 (SSG migration in progress — points back at this CONTEXT)
- `uap-release001.csv` — wargov source-of-truth (UNTOUCHABLE per §11)

### External docs (planner reads on-demand)
- Astro Content Collections — <https://docs.astro.build/en/guides/content-collections/>
- Astro Content Layer API — <https://docs.astro.build/en/reference/content-loader-reference/>
- `@astrojs/cloudflare` adapter — <https://docs.astro.build/en/guides/integrations-guide/cloudflare/>
- Astro `<script is:inline>` — <https://docs.astro.build/en/guides/client-side-scripts/>
- Cloudflare Pages build configuration — <https://developers.cloudflare.com/pages/configuration/build-configuration/>

### Outputs of this phase (new artifacts)
- `astro.config.mjs` — Astro 5 config (CF adapter, integrations)
- `src/content.config.ts` — Zod schema + 15 file() loaders
- `src/layouts/RootLayout.astro` + `BaseHead.astro` + `Nav.astro` + `Footer.astro`
- `src/pages/index.astro` — wargov port
- `data/wargov.json` (+ optional shards `data/wargov-page-N.json`)
- `data/<slug>.json` × 14 — schema-validated even if pages not built in Phase 3
- `scripts/normalize-csv.{py,ts}` — CSV → `data/*.json` normalizer
- `.planning/decisions/astro-version-pin.md` — Astro + adapter version ADR

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/templates/archive.py` + `templates/nav.py` + `templates/footer.py` + `templates/head.py` (Python build) — reference patterns for the Astro components D-16..D-20 replace. Read for: card markup shape, hamburger HTML, lightbox markup, search form, filter UI shape.
- `scripts/templates/lightbox.py` — lightbox markup + inline JS. D-22 ports this.
- `scripts/templates/i18n.py` — i18n strings dict. Stays inactive (Out of Scope per PROJECT.md).
- Current `index.html` (root, wargov) — visual + interaction reference. Tests/visual-baselines/wargov-*.png captured from this exact output.
- Current inline `<script id="archive-manifest">` JSON in root index.html — wargov data shape (CSV-keyed `rows[]` with `Title`, `Type`, `Release Date`, etc.). D-02 schema accommodates this.
- `scripts/build-wargov.py` — current Python build for wargov. CSV-read + manifest-emit logic to port to D-32 prebuild.
- `uap-release001.csv` — wargov SOURCE-OF-TRUTH. UNTOUCHABLE.
- `scripts/build-sw.py` — version stamper. Phase 3 BaseHead SW registration uses kill-switch sw.js (already on main); Phase 4 swaps to injectManifest SW.

### Established Patterns
- Mobile-first 360 px CSS (CLAUDE.md §8). Astro CSS scoped per layout. Media queries match existing breakpoints.
- Per-archive `--caution` CSS variable (CLAUDE.md §3.1). Astro `RootLayout` props → `style="--caution: var(--archive-color)"` set on `<html>` or `<body>`.
- Inline JSON manifest pattern → CHANGING to Astro Content Collections (D-01..D-04 supersedes).
- `git ls-files` HTML traversal (current Python scripts) — D-32 prebuild may reuse this for any HTML-walking logic.
- Public-domain attribution per jurisdiction (CLAUDE.md §9) — Footer.astro hard-codes per archiveSlug prop.

### Integration Points
- CF Pages build trigger: push to `ssg-migration`. Build command: `pnpm install --frozen-lockfile && pnpm prebuild && pnpm build`. Output: `dist/`.
- GitHub repository: `hectorchanht/gov-ufo-archive` (per CLAUDE.md §13 / cf-pages-project.md).
- GH Pages: serves `main` branch (Python build artifacts). Stays live until Phase 6 DNS cutover.
- CF Pages preview URL: `<commit>.realufo.pages.dev` — visible to quality-gates.yml CI via `deployment_status` event (Phase 2 02-08 wiring).
- GitHub Releases: binary CDN (videos-v1, pdfs-v1, wargov-pdfs-2026q2 etc.). Astro template embeds release URLs in card data; CF Pages serves HTML, releases serve binaries.

### Things Phase 3 ADDS (planner inventory)
- `astro.config.mjs`
- `src/content.config.ts`
- `src/layouts/RootLayout.astro`, `BaseHead.astro`, `Nav.astro`, `Footer.astro`
- `src/pages/index.astro` (wargov)
- `src/components/Card.astro` (+ maybe ArchiveCard.astro, Lightbox.astro — planner discretion)
- `src/styles/global.css` (shared palette per CLAUDE.md §3.2)
- `src/styles/wargov.css` (or scoped in component — discretion)
- `data/wargov.json` + shards
- `data/<slug>.json` × 14 (schema-validated, content can be skeleton in Phase 3)
- `scripts/normalize-csv.{py,ts}`
- `package.json` extends with Astro + `@astrojs/cloudflare` + content tooling
- `tsconfig.json`
- `.planning/decisions/astro-version-pin.md`

### Things Phase 3 does NOT TOUCH
- `<slug>/index.html` × 14 (Python-built, stays on main for GH Pages)
- `scripts/build-*.py` × 15 (deletion = Phase 4 SSG-10)
- `scripts/sync-nav.py` / `scripts/sync-footer.py` (deletion = Phase 4 SSG-10; Nav/Footer.astro is sole source of truth for any new HTML, but the Python scripts keep policing the old HTML on `main`)
- `sw.js` (kill-switch already on main; injectManifest = Phase 4 SW-01)
- `/search.html` (Lunr-based, stays until Phase 4 SRC-02)

</code_context>

<specifics>
## Specific Ideas

- Astro 5.18.x is current latest; planner re-verifies astro#15684 (Cloudflare adapter v6 regression) status BEFORE committing the pin — if fixed in Astro 6.x by now (research dated ~3 weeks ago), can choose to pin `~5.18` defensively or upgrade. Defensive pin is the safe default.
- wargov's hero carousel (16:9 aspect, ≥ 4 slides per CLAUDE.md §4) — `Carousel.astro` component reuse opportunity in Phase 4 for other archives. Phase 3 implementation should leave this seam visible.
- 50-card initial render boundary (D-08) — choose so wargov first paint stays under Phase 2 Lighthouse soft budget (500 KB transfer). If individual wargov cards average 4 KB rendered, 50 = 200 KB cards + 100 KB chrome = within budget. Planner verifies during execution.
- Lazy-load trigger preference: `IntersectionObserver` on scroll-near-end + idle prefetch. Avoid filter-event-only — filter on lazy-loaded data needs all shards loaded eventually.
- Inline `<script is:inline>` should reference Phase 2's existing JS invariants — copy from current `index.html` `<script>` block verbatim where possible, refactor only what's required for Astro context.

</specifics>

<deferred>
## Deferred Ideas

- **Astro Server Islands** — considered for hero carousel; rejected per D-23 (no hydration). Revisit only if Phase 4 PERF investigation shows static-only doesn't hit budget.
- **MDX for archive cards** — rejected per D-28 (typographer drift risk). Reserved for prose pages (about, FAQ) in Phase 4.
- **i18n / multi-language content** — Out of Scope per PROJECT.md (current milestone English-only).
- **React/Vue/Svelte component integration** — rejected per D-23.
- **Pagefind search** — Phase 4 SRC-01.
- **injectManifest SW + full-catalog offline cache** — Phase 4 SW-01..03.
- **Self-hosted fonts via `@fontsource/*`** — Phase 4 SW-07 (paired with SW work for proper offline behavior).
- **GEIPAN 3.3 MB shard refactor** — Phase 4 PERF-01.
- **Other 14 archive ports** — Phase 4 SSG-06.
- **`sync-nav.py` / `sync-footer.py` retirement** — Phase 4 SSG-10 (components exist in Phase 3 but drift gates stay until 14-archive port complete).
- **CF Pages git-integration UI click** — operator follow-up from Phase 2 02-01 cf-pages-project.md (still pending; not Phase 3 deliverable but blocks Phase 3 testing on per-PR preview URL).

### Reviewed Todos (not folded)
None — no pending todos matched this phase.

</deferred>

---

*Phase: 03-ssg-foundation*
*Context gathered: 2026-05-25*
