---
phase: 01-pre-migration-safety
plan: 02
subsystem: infra
tags: [url-contract, snapshot, python, stdlib, ci-prep, ssg-migration]

# Dependency graph
requires:
  - phase: 01-pre-migration-safety
    provides: "Planning context (01-CONTEXT.md decisions D-01..D-04 — format, scope, generator-as-Python)"
provides:
  - "scripts/snapshot-urls.py — stdlib-only Python generator that walks tracked HTML + parses inline JSON manifests"
  - "URL-CONTRACT.txt — immutable snapshot of every public route + #card-<id> anchor on the current GH Pages deployment"
  - "Idempotent --check CLI mode ready for the Phase 2 CI drift gate"
affects: [02-ssg-foundation, 06-cutover, ssg-migration, url-redirects, ci-drift-gate]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "stdlib-only Python build helper (CLAUDE.md §6.2 convention)"
    - "git ls-files first, glob fallback for tracked-file detection"
    - "Inline-JSON manifest extraction via single non-greedy re.compile (no BS4/lxml)"
    - "Slugifier with collision suffixing for stable per-card anchor namespace"

key-files:
  created:
    - scripts/snapshot-urls.py
    - URL-CONTRACT.txt
  modified: []

key-decisions:
  - "Used `re` rather than BeautifulSoup/lxml — stdlib-only mandate from CLAUDE.md §6.2 + 01-CONTEXT.md Claude's-discretion note"
  - "Per-card slug derived from `ti` (archive shape) OR `Title` (root war.gov rows shape) — no asset carries an explicit `id` field in the current build, so slug-from-title is the only deterministic identity available"
  - "Collision handling: -2/-3/… suffix in order of appearance — keeps slugs stable across re-runs"
  - "Header SHA is captured AT GENERATION TIME from `git rev-parse --short HEAD` — re-running after a new commit will refresh the header (intentional; idempotent against current HEAD, not against historical state)"
  - "Output sorted lexicographically (plain `sorted()`) — matches D-02 'diff-friendly plain text'"

patterns-established:
  - "URL-contract generator: stdlib-only Python, walk git ls-files, parse inline manifests, sort + dedupe + write to repo root"
  - "Provenance header (`# Snapshot taken from main @ <sha> on <date>`) on generated text artifacts"
  - "`--check` CLI flag on idempotent generators for future CI gates"

requirements-completed: [PMS-01]

# Metrics
duration: ~18min
completed: 2026-05-25
---

# Phase 01 Plan 02: URL-Contract Snapshot Summary

**stdlib-only Python generator (`scripts/snapshot-urls.py`) walks 95 tracked HTML files, parses inline `arch-data`/`archive-manifest` JSON, and emits a 4937-entry sorted `URL-CONTRACT.txt` with provenance header — the immutable regression target for the Phase 2 SSG-migration URL-drift gate.**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-05-25T04:05:00Z
- **Completed:** 2026-05-25T04:23:39Z
- **Tasks:** 2
- **Files modified:** 2 (both newly created)

## Accomplishments

- Built `scripts/snapshot-urls.py` (302 lines, stdlib only — `os`/`sys`/`re`/`json`/`glob`/`subprocess`/`datetime`/`argparse`), mirroring `sync-nav.py`'s traversal style and `build-sw.py`'s short-SHA pattern.
- Generated `URL-CONTRACT.txt` at repo root: **4937 total entries** = 95 page routes + 4842 `#card-<slug>` anchors.
- Verified idempotency: a second run produces byte-identical output; `--check` mode exits 0 on the committed file.
- Covers all 14 archive roots (`/aaro/` through `/uruguay/`) + the root `/` + 13 top-level utility pages (`/search.html`, `/timeline.html`, `/map.html`, `/about.html`, `/donate.html`, `/foia.html`, `/glossary.html`, `/stats.html`, `/compare.html`, `/embed.html`, `/whatsnew.html`, `/404.html`) + 28 story / case-detail subpages + 19 `aaro/pages/` and `nara/pages/` two-level-deep static catalog pages.
- Handles BOTH inline-JSON shapes detected in the codebase:
  - **Archive catalog shape** (`assets[].ti`) — used by all 14 archive `index.html` files (aaro 112 assets … geipan 3343 assets).
  - **Root war.gov shape** (`rows[].Title`) — used by `/index.html` only; rows are keyed by CSV column names, not the catalog schema.

## Task Commits

Each task committed atomically inside the parallel worktree:

1. **Task 1: Create scripts/snapshot-urls.py** — `3205f0a` (feat)
2. **Task 2: Generate and commit URL-CONTRACT.txt** — `c600c77` (feat)
3. **Self-check follow-up: fix `--check` chicken-and-egg** — `3bffef0` (fix, Rule 1)

_Plan-metadata commit handled by orchestrator on merge-back (per parallel-executor protocol)._

## Files Created/Modified

- `scripts/snapshot-urls.py` (302 lines, +x) — Snapshot generator. Walks `git ls-files '*.html'` (glob fallback), excludes build-artifact dirs (`.git/`, `.cache/`, `.pdftext/`, `__pycache__/`, `node_modules/`, `bundles/`, `assets/vendor/`, `_site/`), maps HTML paths to public URLs (`index.html` → `/`, `<slug>/index.html` → `/<slug>/`, else `/<path>`), parses any `<script id="arch-data|archive-manifest" type="application/json">` block per page, derives `#card-<slug>` anchors from `id` / `ti` / `Title` / `title` / `Video Title` (in preference order). Sorted, deduped, written to `URL-CONTRACT.txt` with header.
- `URL-CONTRACT.txt` (4941 lines, 158 KB, plain text at repo root) — Output. Header: `# URL-CONTRACT.txt` / `# Snapshot taken from main @ <sha> on 2026-05-25` / `# Total routes + anchors: 4937` / `# Generator: scripts/snapshot-urls.py (idempotent — re-run to refresh)`. Body sorted ASCII.

## Decisions Made

- **Slug source preference order: `id` → `ti` → `Title` → `title` → `Video Title`.** The plan only mentioned `id` and `ti`; the root war.gov manifest uses `rows[].Title` (CSV-keyed) so the script must also recognize `Title` to extract anchors from `/`. Adding `title` (lowercase) and `Video Title` as further fallbacks is forward-compatible — costs nothing if absent.
- **Two-level-deep glob fallback (`*/*/*.html`)** added beyond what the plan described as "root + one level deep" — required to cover the existing `aaro/pages/*.html` and `nara/pages/*.html` static catalog pages. Without it, the `git ls-files` fallback would miss 19 pages. The git path picks them up automatically.
- **Excluded `_site/` and `.pdftext/` directories** in addition to the plan-specified exclusions (`.git/`, `node_modules/`, `bundles/`, `assets/vendor/`, `.cache/`, `__pycache__/`) — defensive coverage for build-artifact dirs that exist in some checkouts.
- **Header `Total routes + anchors:` line** included on top of the plan-specified provenance line. Cheap to compute, useful at-a-glance signal for the CI gate and humans reading drift diffs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Support `rows[].Title` shape for the root war.gov manifest**

- **Found during:** Task 1 implementation (inspecting actual JSON contents of `/index.html`)
- **Issue:** Plan §interfaces documents only the `assets[].ti` catalog shape, but inspection showed `/index.html` uses `<script id="archive-manifest">` with a `rows[]` array keyed by CSV column names (`Title`, `Type`, `Video Title`, …). If the script only handled `assets[].ti`, it would emit only the bare `/` URL with zero anchors for the root landing — silently dropping 222 cards' worth of contract.
- **Fix:** Made `extract_card_anchors` accept either `data['assets']` or `data['rows']` as the records list, and extended `asset_identity` to walk `id → ti → Title → title → Video Title` looking for the first non-empty string field.
- **Files modified:** scripts/snapshot-urls.py
- **Verification:** Spot-checked output — `/#card-<slug>` anchors derived from row Titles are present (e.g., `/#card-18-100754-general-1946-7-vol-2` from a tracked NARA folder Title).
- **Committed in:** `3205f0a`

**2. [Rule 3 - Blocking] Two-level-deep glob fallback for `aaro/pages/*.html` + `nara/pages/*.html`**

- **Found during:** Designing the glob fallback path
- **Issue:** Plan called for "root + one level deep" via glob, but 19 tracked HTML pages live two levels deep (`aaro/pages/faq.html`, `nara/pages/topic.html`, …). If git is unavailable AND we only glob `*.html` + `*/*.html`, these pages drop out of the contract — would corrupt the snapshot only when git is unavailable, hiding the bug from local testing.
- **Fix:** Added `*/*/*.html` to the glob fallback patterns. No effect when git is available (the git path lists all tracked HTML regardless of depth). Pure defense in depth for the unusual fallback case.
- **Files modified:** scripts/snapshot-urls.py
- **Verification:** With git path active, `URL-CONTRACT.txt` contains all 19 `pages/` subroutes.
- **Committed in:** `3205f0a`

**3. [Rule 1 - Bug] `--check` chicken-and-egg vs the snapshot's own SHA**

- **Found during:** Plan-level self-check, after Tasks 1+2 had been committed
- **Issue:** The generator stamps `# Snapshot taken from main @ <short-sha>` into the file header at write time. When the snapshot is then committed, HEAD advances to that new commit, so the next `--check` reads the on-disk file (recording the pre-commit SHA), regenerates against the new HEAD (recording the post-commit SHA), sees the headers differ, and reports "stale". The plan's acceptance criterion `python3 scripts/snapshot-urls.py --check exits 0 against the committed file` was therefore unsatisfiable for the snapshot commit itself. Future Phase-2 CI use of `--check` would have always reported stale on the commit that introduces it.
- **Fix:** Added `_strip_volatile_header()` — `--check` now compares structural body (sorted URL list + static `# URL-CONTRACT.txt` + `# Generator: ...` markers) while ignoring the SHA and count lines. The full provenance still gets written to the file on regen; it's just not part of the drift comparison.
- **Verification:**
  - `python3 scripts/snapshot-urls.py --check` against the committed file (HEAD `c600c77`, file SHA `3205f0a`) → exits 0 with `URL-CONTRACT.txt up-to-date (4937 entries...)`.
  - Manually appending `/synthetic-drift-route` to the file → exits 1 with `URL-CONTRACT.txt is stale ...`.
  - Restoring the file → exits 0 again.
- **Files modified:** scripts/snapshot-urls.py
- **Committed in:** `3bffef0`

---

**Total deviations:** 3 auto-fixed (1 Rule-1 bug, 1 Rule-2 missing-critical, 1 Rule-3 blocking)
**Impact on plan:** All three fixes essential. (1) makes the contract complete for the root war.gov page, (2) covers the 2-level-deep pages on the fallback path, (3) makes the script's own primary acceptance criterion satisfiable in the steady state. No scope creep — all stay strictly inside the URL-contract generator's mandate.

## Issues Encountered

- **Parallel-executor cwd drift (recovered).** The orchestrator spawned this agent inside a Claude Code worktree at `/Users/laichan/code/war-gov-ufo-release/.claude/worktrees/agent-af95d1fa9e4f9988e/`, but the first Write to `/Users/laichan/code/war-gov-ufo-release/scripts/snapshot-urls.py` accidentally targeted the main checkout (relative `cd` in Bash calls had popped me out of the worktree). Recovered by copying the script into the worktree, removing the stray copy from the main repo, and running all subsequent generator commands + commits from inside the worktree. No work lost; commits `3205f0a` and `c600c77` correctly live on the per-agent branch `worktree-agent-af95d1fa9e4f9988e`. Documented as a reminder that absolute paths into the worktree must be used for Write/Edit when the orchestrator runs the agent from a non-worktree spawn point.
- **No JSON parse errors encountered.** All 15 inline-manifest pages parsed cleanly on the first pass — the T-02-02 try/except in `extract_card_anchors` did not trigger. (It remains the defensive backstop for a future malformed-manifest regression.)

## Known Stubs

None. Both deliverables ship complete:
- `scripts/snapshot-urls.py` is fully wired and exercised in three modes (default write, `--stdout`, `--check`).
- `URL-CONTRACT.txt` is the regenerated output of that script against current HEAD — no placeholder data.

## Next Phase Readiness

- Phase 2 SSG migration can now diff post-migration build output against `URL-CONTRACT.txt` and fail any PR that drops or renames a URL without a corresponding `_redirects` entry (D-04). The `--check` CLI flag is the gate primitive.
- Phase 2 should add `python3 scripts/snapshot-urls.py --check` to a GitHub Actions workflow (or equivalent CI runner) gating PRs into `ssg-migration`.
- Phase 4 (per-card permalink work, SRC-04) can extend the slugifier into a build-time `id=` attribute emitter — the contract here is the namespace it must preserve.

## Self-Check: PASSED

- ✓ `scripts/snapshot-urls.py` exists (worktree path), `chmod +x`, stdlib-only.
- ✓ `URL-CONTRACT.txt` exists at repo root, 4941 lines (4 header + 4937 entries).
- ✓ All 14 archive roots + root `/` present (15 total).
- ✓ 4842 `#card-<slug>` anchors present.
- ✓ Body sorted: `tail -n +5 URL-CONTRACT.txt | LC_ALL=C sort -c` exits 0.
- ✓ `python3 scripts/snapshot-urls.py --check` exits 0 (after Rule-1 fix).
- ✓ `python3 -c "import ast; ast.parse(open('scripts/snapshot-urls.py').read())"` exits 0.
- ✓ Commits `3205f0a` (Task 1), `c600c77` (Task 2), `3bffef0` (Rule-1 fix) all in `git log` on branch `worktree-agent-af95d1fa9e4f9988e`.
- ✓ No BS4/lxml — `grep -nE '\bBeautifulSoup\b|\blxml\b' scripts/snapshot-urls.py` empty.

---
*Phase: 01-pre-migration-safety*
*Completed: 2026-05-25*
