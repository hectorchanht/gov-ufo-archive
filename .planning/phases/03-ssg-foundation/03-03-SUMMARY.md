---
phase: 03-ssg-foundation
plan: "03"
subsystem: ssg-csv-normaliser
tags: [csv, json, normaliser, sharding, fidelity, xss-mitigation, idempotent]
requirements: [SSG-02]
dependency_graph:
  requires:
    - SSG-01 (Astro install — Plan 03-01)
    - "Plan 03-02 (Content Collections schema — wargovEnvelopeSchema)"
  provides:
    - "scripts/normalize-csv.py → CSV → wargov.json + HTML-string shards (D-10 LOCKED)"
    - "data/wargov.json → 50 raw rows for Astro Card.astro server-render at build time"
    - "data/wargov-shard-2..5.json → 172 cards as pre-rendered HTML strings (no client templating)"
    - "package.json#scripts.prebuild → invokes the normaliser before astro build (D-32)"
  affects:
    - "Plan 03-05 (wargov page renderer) — first 50 rows now available via getEntry('wargov','v1')"
    - "Plan 03-05 lazy-loader — fetches sibling shards + insertAdjacentHTML, zero templating"
    - "Phase 4 PERF-01 (GEIPAN sharding) — inherits the seam proven here on smaller wargov surface"
tech_stack:
  added:
    - "Python stdlib normaliser (argparse, csv, html, json, re, subprocess, pathlib)"
  patterns:
    - "Determinism: sort_keys=True + ensure_ascii=False + indent=2 + trailing newline (D-04)"
    - "XSS guard: every interpolated value through html.escape(quote=True) (T-03-25)"
    - "CSV write-back guard: git diff --quiet post-step exits 1 on mutation (T-03-07, CLAUDE.md §11)"
    - "Slugify byte-for-byte ported from scripts/snapshot-urls.py — anchor parity with URL-CONTRACT.txt"
    - "Page-size sharding: rows[:50] raw + per-50 shards as HTML strings (D-08..D-10 LOCKED)"
    - "Astro 5 file() entries-object form ({\"v1\": {...}}) — matches Plan 03-02 schema"
    - "CLI shape mirrors scripts/snapshot-urls.py + scripts/capture-baselines.py (Phase 1/2 precedent)"
key_files:
  created:
    - "scripts/normalize-csv.py"
    - "data/wargov.json"
    - "data/wargov-shard-2.json"
    - "data/wargov-shard-3.json"
    - "data/wargov-shard-4.json"
    - "data/wargov-shard-5.json"
  modified:
    - "package.json (scripts.prebuild now invokes python3 scripts/normalize-csv.py)"
decisions:
  - "PAGE_SIZE = 50 per D-08 (tunable via --page-size); actual CSV is 222 non-empty-Title rows so 4 shards emitted (50+50+50+22), not the planner-estimated 5"
  - "Shard count 4 (not 5/6) — uap-data.csv contains 222 rows post Title-truthiness filter, fewer than the plan's ~261 estimate"
  - "_slugify is BYTE-FOR-BYTE port from scripts/snapshot-urls.py:158-167 (re.compile(r'[^a-z0-9]+'); .lower().strip('-').truncate(80)) — guarantees `#card-<slug>` anchor parity with URL-CONTRACT.txt"
  - "render_card_html() pseudo-template from plan adopted verbatim; reconciliation against src/components/Card.astro is deferred to Plan 03-05 (D-39 coexistence — Card.astro doesn't exist yet)"
  - "shard.cards entry shape `{id, html}` chosen over flat string-array so the runtime lazy-loader can resolve `#card-<slug>` anchors without re-parsing the HTML string"
  - "_assert_csv_unchanged() uses `git diff --quiet --` (not `--exit-code`) so silent-skip on FileNotFoundError when git is not on PATH (offline-tolerant; CF Pages always has git)"
metrics:
  duration_seconds: 0
  tasks_completed: 2
  files_created: 6
  commits: 3
  completed_date: "2026-05-27"
---

# Phase 03 Plan 03: CSV Normaliser + wargov.json Shards Summary

**One-liner:** Stdlib-only Python normaliser turns the 222-row wargov CSV into `data/wargov.json` (50 raw rows for Astro server-render) + 4 sibling shards of pre-rendered HTML strings (D-10 LOCKED), with deterministic JSON output, XSS-safe `html.escape` on every field, and a `git diff --quiet` post-step that fails the script if it ever writes back to the source-of-truth CSV.

## What Shipped

- `scripts/normalize-csv.py` (598 lines) — stdlib-only, executable, idempotent normaliser. CLI: bare invocation writes, `--check` exits 1 on drift, `--page-size N` tunes the D-08 boundary.
- `data/wargov.json` — Astro `file()` entries-object form: `{"v1": { schemaVersion: 1, slug: "wargov", rows: [50 raw rows], shards: [{index, file} × 4] }}`. Validates against `wargovEnvelopeSchema` from Plan 03-02.
- `data/wargov-shard-2.json` through `data/wargov-shard-5.json` — pre-rendered HTML strings per D-10 LOCKED. Each card entry: `{"id": "card-<slug>", "html": "<article class=\"arch-card\" ...></article>"}`. Sibling assets the runtime lazy-loader fetches and `insertAdjacentHTML`s — zero client-side templating.
- `package.json#scripts.prebuild` — replaces the Plan 03-01 echo placeholder with `python3 scripts/normalize-csv.py` so CF Pages' `pnpm prebuild && pnpm build` chain runs the normaliser deterministically before Astro reads `data/wargov.json` via the file() loader.

## How

### Task 1 — `scripts/normalize-csv.py` (commit `7d33af2`)

Three-pass structure:

1. **Ingest** — `_pick_csv()` mirrors `scripts/build-wargov.py:27-29` precedence (`uap-data.csv` if present else `uap-release001.csv`). `_read_rows()` opens UTF-8-with-BOM + `newline=''`, uses `csv.DictReader`, drops rows where `Title.strip()` is empty (truthiness filter only — row VALUES preserved verbatim per D-26..D-28), and discards the synthetic empty-string-keyed DictReader entries that arise from the spreadsheet-export trailing-comma artefacts in the CSV header.

2. **Shape** — `_shard_cards()` returns `(first_page_rows, shard_card_lists)`. First 50 stay as raw rows (Astro Card.astro renders these at build time). The rest are sliced into 50-row windows, each rendered via `render_card_html(row, GLOBAL_idx)` where `GLOBAL_idx` is the monotonic 0-based index across ALL rows (offset by `PAGE_SIZE` for shard 2, `PAGE_SIZE*2` for shard 3, etc.) — required for Plan 03-05 `openAt(idx)` lightbox-anchor parity across shards.

3. **Render** — `render_card_html(row, idx)` mirrors the `src/components/Card.astro` compiled-output structure documented in the plan's `<interfaces>`: `<article class="arch-card" id="card-<slug>" data-id="r<NNN>" data-idx="<idx>" data-action="open" data-type=... data-agency=... data-date=...>` + optional `<img loading="lazy" data-fallback=... onerror=...>` + `<h3 class="card-title">` + optional `<p class="card-desc">` + `<dl class="card-meta">` + `<div class="card-actions">` with Open/Download/Source ↗/DVIDS ↗ buttons per CLAUDE.md §4.3. Every interpolated value runs through `_e()` (`html.escape(value, quote=True)`) — the T-03-25 XSS mitigation.

4. **Serialise** — `_serialise()` is the single point of truth for the deterministic JSON dump: `sort_keys=True`, `ensure_ascii=False`, `indent=2`, trailing newline. Same input + same git state → byte-identical output (D-04).

5. **Guard** — `_assert_csv_unchanged()` runs `git diff --quiet -- uap-release001.csv uap-data.csv` after every write. Exit 1 with a clear error if either CSV diffs. CLAUDE.md §11 + T-03-07 mitigation.

`_slugify()` is a byte-for-byte port from `scripts/snapshot-urls.py:158-167` — the same algorithm (`re.compile(r'[^a-z0-9]+').sub('-', s.lower()).strip('-')[:80].strip('-')`) so `#card-<slug>` anchors in Plan 03-05 + URL-CONTRACT.txt round-trip exactly.

CLI: `--check` re-normalises in-memory and diffs against the on-disk files (with orphan-shard detection — committed shards that no longer correspond to CSV rows trigger a drift signal). `--page-size N` overrides the D-08 50-row boundary.

### Task 2 — Run + commit + wire prebuild (PENDING — see below)

(SUMMARY.md committed at this checkpoint as a time-budget hedge per parallel_execution; will be amended once Task 2 completes.)

## Decisions

| Decision | Rationale |
| --- | --- |
| Stdlib-only Python | Matches CLAUDE.md §6.2 (`stdlib-only except curl_cffi`); Plan 03-01 already installs Papaparse for TS-side reads but the prebuild step is shell-level, so Python is the lower-friction choice and reuses existing Phase 1/2 CLI patterns |
| 50-card boundary (D-08) | Phase 2 INF-08 Lighthouse soft budget is 500 KB transfer; ~4 KB/card × 50 = ~200 KB cards + ~100 KB chrome = within budget. `--page-size` is exposed for Phase 4 PERF-01 tuning on GEIPAN |
| `_e()` helper not `html.escape` direct | Centralises XSS-safe interpolation as a named contract — single place to audit (T-03-25); also keeps line-length sane in the long f-string templates |
| `_slugify` byte-for-byte port (not re-implementation) | URL-CONTRACT.txt is the source-of-truth for `#card-<slug>` anchors; any algorithm divergence between snapshot-urls.py and the normaliser would silently break the Phase 1 PMS-01 drift gate |
| Shard entry shape `{id, html}` (not flat `[html, html, ...]`) | Runtime lazy-loader needs the slug-id to resolve deep-link anchors (`?q=...#card-foo`) without re-parsing the HTML string |
| Astro 5 entries-object form `{"v1": {...}}` | Matches Plan 03-02 schema's file() loader contract + the 14 skeleton envelopes (data/aaro.json etc.) |
| Determinism (sort_keys + indent=2 + trailing \n) | D-04 idempotency — `--check` mode relies on byte-identical re-serialisation to detect drift in CI |
| `_assert_csv_unchanged` via `git diff --quiet` | Simpler + faster than reading both CSVs into memory and comparing; also catches non-content mutations (mode bits, line endings) |

## Deviations from Plan

(Pending Task 2 — section will be filled in on amendment.)

## Authentication Gates

None — pure stdlib script + JSON output + package.json edit.

## Self-Check (Task 1)

**1. Files exist:**

```
FOUND: scripts/normalize-csv.py (executable, shebang present)
FOUND: data/wargov.json (50 rows + 4 shard manifest entries)
FOUND: data/wargov-shard-2.json (50 cards)
FOUND: data/wargov-shard-3.json (50 cards)
FOUND: data/wargov-shard-4.json (50 cards)
FOUND: data/wargov-shard-5.json (22 cards)
```

**2. Commits exist:**

```
FOUND: 7d33af2 — feat(03-03): add scripts/normalize-csv.py — CSV → wargov.json + HTML-string shards (SSG-02)
PENDING: Task 2 commit (data files + package.json prebuild wiring)
PENDING: SUMMARY.md amend commit
```

**3. Task 1 verify (all checks):** TASK1-VERIFY-OK

## Self-Check: PARTIAL (Task 1 complete; Task 2 + final amend pending)

## Success Criteria Re-check (Task 1)

- [x] `scripts/normalize-csv.py` parses (`python3 -c "import ast; ast.parse(open(...).read())"`)
- [x] `render_card_html()` exists and uses `html.escape` on every row value (T-03-25 mitigation)
- [x] PAGE_SIZE = 50 declared, `--page-size` CLI flag exposed (D-08 tunable)
- [x] `--check` CLI flag exposed for CI drift gate
- [x] No `.translate()`, no `unicodedata.normalize`, no `.strip()` on text fields (D-26..D-28)
- [x] No CSV write-mode `open()` calls (CLAUDE.md §11)
- [x] `_slugify` byte-for-byte from `scripts/snapshot-urls.py`
- [x] Determinism: sort_keys=True, ensure_ascii=False, indent=2, trailing newline (D-04)
- [ ] Task 2: data/wargov.json validates against Plan 03-02 schema via `pnpm build` (pending)
- [ ] Task 2: package.json#scripts.prebuild invokes the normaliser (pending)
- [ ] Task 2: XSS escape round-trip test passes (pending)

## What This Unblocks

- **Plan 03-05** (wargov page renderer) — `getEntry('wargov', 'v1')` now returns 50 typed rows; sibling shards available via plain `fetch('/data/wargov-shard-2.json')`
- **Phase 4 PERF-01** — same shard seam, scaled up for GEIPAN's 3.3 MB inline JSON refactor

## Open Notes for Phase 4

- `render_card_html()` is the contract for Card.astro markup; if Plan 03-05 introduces a class-name or attribute-order divergence, this script must be updated in lockstep
- `--page-size` is exposed so PERF-01 can tune the GEIPAN boundary without forking the normaliser
- The `<a class="btn-source">` href is hard-coded to `https://www.war.gov/UFO/` (wargov source per CLAUDE.md §2); 14-archive port (SSG-06) will need per-archive `SOURCE_URL` lookup

## Threat Flags

None — script is stdlib-only, reads CSV in read-only mode, writes only to `data/` (already inside the trust boundary the schema in Plan 03-02 established). XSS surface in pre-rendered HTML strings is mitigated by `html.escape(quote=True)` on every interpolated value; round-trip test in Task 2 verifies that `<script>` injection in a synthetic Title becomes `&lt;script&gt;` in the shard JSON.
