# Phase 1: Pre-Migration Safety - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Capture an immutable snapshot of the current contract (URLs, source-fetch viability, latent FIX bugs) and ship the SW kill-switch to the OLD origin (GitHub Pages serving `realufo.org`) BEFORE any SSG code lands — so a botched cutover in Phase 6 can never serve a stale shell to returning users.

Scope: PMS-01..06 (6 requirements). Pure process / safety work against current `main`. No SSG code lands in this phase.

</domain>

<decisions>
## Implementation Decisions

### URL-CONTRACT.txt scope & format

- **D-01:** URL-CONTRACT.txt captures every public route AND every `#card-<id>` anchor on the deployed site. Per-card permalink drift is a real risk; the contract must catch it.
- **D-02:** Format is plain text, one URL per line, sorted. Diff-friendly. CI gate just compares sorted lists.
- **D-03:** Generator is a Python script (`scripts/snapshot-urls.py`) that walks git-tracked HTML files and parses `#card-<id>` from each page's inline JSON manifest (`<script id="arch-data">` / `<script id="archive-manifest">`). Reuses current Python tooling; no new runtime dependency.
- **D-04:** CI gate (added in Phase 2, not Phase 1) fails any PR that drops or renames a URL without a corresponding `_redirects` entry. Phase 1 just produces the file and commits it on `main`.

### SW kill-switch strategy

- **D-05:** Kill-switch behavior is **full nuke**: `self.registration.unregister()` + iterate `caches.keys()` and `caches.delete(name)` for every cache + `clients.matchAll({type:'window'})` then `client.postMessage({type:'sw-killswitch-reload'})` for a soft reload + `self.skipWaiting()` + `clients.claim()`. Returning users get a clean slate fast.
- **D-06:** Coexist strategy: **replace in-place** at `/sw.js` on GH Pages. Same scope, same URL — browser auto-installs over the old SW on next visit. No sidecar `/sw-kill.js`. Existing `sw.js` (versioned shell precache, network-first nav) is replaced entirely by the kill-switch on the GH Pages branch.
- **D-07:** No self-disable timer. Kill-switch SW stays installed at the old origin until cutover. When CF Pages takes over `realufo.org` in Phase 6, the new (real) SW takes over the same `/sw.js` URL and supersedes the kill-switch.
- **D-08:** The 14-day gate ([Pitfall #1, research/PITFALLS.md]) measures from kill-switch DEPLOY date on GH Pages, not from kill-switch INSTALL on individual user browsers. Phase 6 cutover may not occur earlier than (deploy date + 14 days).

### Akamai spike methodology

- **D-09:** Probe scope is war.gov + aaro.mil + 3 random samples from the other 13 source domains (chosen at spike-run time by seeded `random.sample()`). Decisive on the known-Akamai cases; samples surface non-Akamai surprises.
- **D-10:** Methodology is **bilateral, 100 fetches each, over 1 hour**. From a Cloudflare Worker: 100 fetches across 1 hour. From a GitHub Actions runner: 100 fetches across the same 1-hour window. Record per-source: 200 / 403 / 429 / other counts + p50/p95 latency.
- **D-11:** Pass/fail threshold: **Workers is viable if its success rate is ≥ 95% AND ≥ Actions success rate**. Otherwise, that source falls through to the hybrid Actions+`curl_cffi` lane in Phase 5. The decision is per-source (some sources may be Workers-friendly, others Actions-only).
- **D-12:** Decision written to `.planning/decisions/akamai-spike.md` (project's first ADR-style file under a new `.planning/decisions/` folder; reusable for cross-phase decisions).

### CLAUDE.md refresh scope

- **D-13:** **Sectional updates only**, no full regeneration. `gsd-sdk query generate-claude-md` is rejected — it would overwrite 12 sections of project-specific design system with default GSD project guidance.
- **D-14:** Three concrete edits applied as part of Phase 1 closure (already committed alongside this CONTEXT.md):
  1. **§3 header note** — design system tagged as "starting point"; visual identity locked, markup may evolve.
  2. **§5.1 URL pattern fix** — `hectorchanht/war-gov-ufo-release` → `hectorchanht/gov-ufo-archive` (closes PMS-06). Note added: local folder name `war-gov-ufo-release` is historical.
  3. **§13 SSG Migration in Progress** — new section appended pointing at `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/research/SUMMARY.md`, target stack, and house-rule survivability.
- **D-15:** `.planning/PROJECT.md` decisions override CLAUDE.md sections they explicitly supersede. Recorded in the new §13 last paragraph.

### Cross-cutting

- **D-16:** PMS-05 (`scripts/sync.sh:144` broken `$ROOT/download.py` path) is a one-line edit. Verify the correct target is `scripts/download-war.gov.py` (or whichever file exists) — gsd-planner should confirm during plan-phase.
- **D-17:** DNS TTL drop (PMS-04) — verify which DNS provider serves `realufo.org` (likely Cloudflare DNS or domain registrar). Provider-specific; planner determines steps. TTL must be 300 s and verified via `dig +noall +answer realufo.org` for ≥ 7 consecutive days before Phase 6 cutover.
- **D-18:** Phase 1 deliverables stay on `main`. No `ssg-migration` branch yet — that's Phase 2.

### Claude's Discretion

- Exact filename of `scripts/snapshot-urls.py` (could be `scripts/url-snapshot.py`, `scripts/build-url-contract.py`, etc.)
- HTML parsing strategy in the snapshot script (BeautifulSoup vs `re` vs lxml — pick consistent with current scripts/ style)
- Kill-switch SW filename comments / banner (cosmetic)
- Spike runner — whether Worker spike code lives in `scripts/spike-akamai/worker.ts` or `.planning/spikes/01-akamai/worker.ts` (lean toward `.planning/spikes/` if the spike is purely investigative)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & milestone
- `.planning/PROJECT.md` — Core value, constraints, key decisions; especially the §Decisions table (locks Astro 5 / CF Pages / Workers cron / Cloudflare Pages hosting / big-bang migration choices)
- `.planning/REQUIREMENTS.md` — PMS-01..06 are this phase; INF / SSG / SRC / SW / HOST / SCRP / PERF are downstream context
- `.planning/ROADMAP.md` §Phase 1 — Goal + success criteria + hard sequencing constraints

### Research informing this phase
- `.planning/research/PITFALLS.md` — Pitfall #1 (SW cache poisoning on cutover) and #2 (URL drift) drive this phase's existence; Pitfall #5 (Akamai egress blocks) drives PMS-03
- `.planning/research/STACK.md` — Documents why Workers Paid is mandatory ($5/mo CPU budget); informs PMS-03 spike framing
- `.planning/research/SUMMARY.md` — Critical Top-5 Pitfalls and roadmap-phase ordering rationale

### Existing codebase artifacts touched
- `CLAUDE.md` — Project design system + content rules; §5.1 corrected in this phase; new §13 added
- `sw.js` (repo root) — Current versioned-shell SW; replaced by kill-switch on GH Pages branch in Phase 1
- `scripts/sync.sh` line 144 — Broken `$ROOT/download.py` reference; PMS-05 fix
- `scripts/build-sw.py` — Existing SW build helper; informs kill-switch deploy mechanics
- `.planning/codebase/CONCERNS.md` — Documents the SW-not-on-subpages issue and `|| true` masks; supplies background for kill-switch design

### Decisions output of this phase
- `.planning/decisions/akamai-spike.md` — To be written during PMS-03 spike (does not exist yet); Phase 5 reads this before architecting scrape Workers

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `sw.js` (root): well-commented versioned SW with `VERSION` constant rewritten by `scripts/build-sw.py`. Kill-switch can reuse this build-stamping mechanism so it identifies itself in DevTools (`realufo-killswitch-<sha>`).
- `scripts/build-sw.py`: Python helper that stamps SW version. Adapt to stamp the kill-switch instead of the real SW for the duration of the GH Pages tenure.
- `scripts/sync-nav.py` / `scripts/sync-footer.py`: existing Python scripts that walk all HTML files and parse them — same traversal pattern needed for `snapshot-urls.py`.
- `scripts/templates/archive.py`: defines the `<script id="arch-data">` JSON manifest contract; URL snapshot must parse this shape.

### Established Patterns
- All scrapers (`dl-*.sh`) hit sources with realistic Chrome UA + Wayback fallback. Akamai-spike Worker should mirror this UA stance for fair comparison.
- All Python build scripts use `git ls-files` for tracked-file detection. URL snapshot follows suit.
- All shell scripts are idempotent (cache hit = skip). Spike runners should be re-runnable safely.
- ADR / decision docs do NOT exist yet — `.planning/decisions/` is new; akamai-spike.md is the first entry.

### Integration Points
- GH Pages serves from `main` directly (no `gh-pages` branch — confirmed via `gh repo view`); kill-switch SW must land in a commit on `main`.
- DNS for `realufo.org` — provider not yet confirmed in repo; planner must inspect via `dig +trace realufo.org` or ask user. Common case: Cloudflare DNS (since user has chosen Cloudflare Pages for Phase 2+).
- `URL-CONTRACT.txt` lives at repo root (so CI gate in Phase 2 can `diff` against it without traversing subdirs).

</code_context>

<specifics>
## Specific Ideas

- Spike script preference: keep under `.planning/spikes/01-akamai/` (Worker code + Action runner script + result JSON), so the artifact lives next to the decision file at `.planning/decisions/akamai-spike.md`.
- Kill-switch SW banner comment must include: "DO NOT REMOVE — installed 2026-MM-DD as part of realufo.org → Cloudflare Pages migration (Phase 1, see .planning/ROADMAP.md). Replaced by real SW on cutover."
- URL-CONTRACT.txt header line: a comment line `# Snapshot taken from main @ <commit-sha> on <date>` so CI drift reports include provenance.

</specifics>

<deferred>
## Deferred Ideas

- **CI gate that diffs URL-CONTRACT.txt against PR builds** — belongs to Phase 2 (INF-02 / `_redirects` verification). Phase 1 just produces the contract file.
- **`sitemap.xml` standards-compliant alternative format** — considered, rejected as primary; could be added as a downstream artifact in Phase 4 (post-SSG) if SEO benefit justifies. Belongs to backlog.
- **Per-archive Akamai spike for all 15 source domains** — considered, scoped down to war.gov + aaro.mil + 3 random samples for time-box. If Phase 5 reveals more blocks, add a Phase 5 sub-task to extend the spike.
- **Full CLAUDE.md regeneration via gsd-sdk** — rejected; would lose 12 sections of project-specific spec. Documented here so a future agent doesn't re-attempt.
- **Annotating every CLAUDE.md section with LOCKED / EVOLVING / WILL CHANGE** — considered, rejected for now (single §3 header note is sufficient). Revisit at Phase 4 close.

### Reviewed Todos (not folded)
None — no pending todos matched this phase.

</deferred>

---

*Phase: 01-pre-migration-safety*
*Context gathered: 2026-05-25*
