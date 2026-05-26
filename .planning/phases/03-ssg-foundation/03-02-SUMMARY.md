---
phase: 03-ssg-foundation
plan: "02"
subsystem: ssg-content-schema
tags: [astro, content-collections, zod, schema, fidelity]
requirements: [SSG-02]
dependency_graph:
  requires:
    - SSG-01 (Astro install — Plan 03-01, in-flight in parallel worktree)
  provides:
    - "src/content.config.ts → 15 Content Collections + Zod schemas + file() loaders"
    - "data/<slug>.json × 14 → schema-valid empty envelopes ready for Phase 4 SSG-06"
    - "data/README.md → envelope shape + writer responsibility + fidelity guard documented"
  affects:
    - "Plan 03-03 (wargov.json producer) — schema contract locked, normaliser writes against this"
    - "Plan 03-05 (wargov page renderer) — getCollection('wargov') key+shape now stable"
    - "Phase 4 SSG-06 (14-archive port) — inherits this schema unchanged; per-archive normalisers fill the empty envelopes"
tech_stack:
  added:
    - "Zod schemas (catalogEnvelopeSchema, wargovEnvelopeSchema)"
  patterns:
    - "Per-archive collection (D-02): no monolithic union; clarity over runtime polymorphism"
    - "Entries-object form for file() loader: {\"v1\": {...payload}}"
    - "Strict asset schema + lenient envelope: unknown fields in assets[] fail build (drift signal); extra envelope fields tolerated"
key_files:
  created:
    - "src/content.config.ts"
    - "data/aaro.json"
    - "data/nasa.json"
    - "data/nara.json"
    - "data/geipan.json"
    - "data/uk.json"
    - "data/brazil.json"
    - "data/chile.json"
    - "data/argentina.json"
    - "data/canada.json"
    - "data/italy.json"
    - "data/nz.json"
    - "data/peru.json"
    - "data/spain.json"
    - "data/uruguay.json"
    - "data/README.md"
  modified: []
decisions:
  - "Catalog asset 't' enum extended to ['PDF','VID','IMG','CATALOG','AUDIO','CASE','PAGE'] after grep of existing arch-data found CASE + PAGE in current Python output"
  - "Loader shape: entries-object form ({\"v1\": {...}}) — canonical Astro 5 file() loader format documented at https://docs.astro.build/en/reference/content-loader-reference/"
  - "catalogAssetSchema uses .strict() so a future scrape pipeline emitting unknown fields fails the build loudly (D-02 / SSG-02)"
  - "wargov 'Type' field stays lenient z.string() in Phase 3; tighten to enum in Phase 4 once CSV stabilises"
  - "wargovRowSchema includes 'local' field — found in current root index.html inline manifest"
  - "Zero z.transform / z.preprocess calls anywhere in schema (D-26..D-28 fidelity guard; PITFALLS.md #6 typographer drift)"
metrics:
  duration_seconds: 244
  duration_human: "~4 minutes"
  tasks_completed: 2
  files_created: 16
  commits: 2
  completed_date: "2026-05-26"
---

# Phase 03 Plan 02: Content Collections Schema (15 archives) Summary

**One-liner:** Astro 5 Content Collections defined for all 15 archives using Zod + `file()` loader, with strict per-asset validation and a CSV-keyed wargov variant — turning CSV/scrape drift into hard build errors per SSG-02 / D-03.

## What Shipped

- `src/content.config.ts` (223 lines): two Zod schemas (`catalogEnvelopeSchema`, `wargovEnvelopeSchema`) + 15 `defineCollection` registrations + JSDoc citing D-02, D-03, D-26..D-28.
- 14 skeleton `data/<slug>.json` files (one per non-wargov archive in CLAUDE.md §2), each a schema-valid empty envelope in Astro 5 entries-object form.
- `data/README.md` documenting envelope shape, writer responsibility per file, fidelity guard rules, and idempotency requirement.

## How

### Task 1 — `src/content.config.ts` (commit `1762053`)

Wrote the schema in three blocks:

1. **`catalogAssetSchema`** — `.strict()` Zod object with abbreviated field names (`t`, `ti`, `de`, `ag`, `cat`, `date`, `region`, `l`, `u`, `s`, `th`) matching `scripts/templates/archive.py`'s `arch-data` JSON shape byte-for-byte. Phase 4 SSG-06's per-archive port consumes this without modification.
2. **`catalogEnvelopeSchema`** — `schemaVersion: z.literal(1)` discriminator + `slug` + `assets[]` + `stats {total, local_total, pdf_total, catalog_total}`.
3. **`wargovEnvelopeSchema`** — CSV-keyed `rows[]` with column names verbatim (`'Release Date'`, `'Description Blurb'`, `'PDF | Image Link'`, …) and an optional `shards[]` manifest for D-10's server-side card shards.

Field findings from existing data:

- The `'t'` enum needed `CASE` and `PAGE` in addition to the originally-planned `['PDF','VID','IMG','CATALOG','AUDIO']`. Confirmed by `grep -rhoE '"t": *"[A-Z]+"' --include="*.html" --include="*.py"` across the repo. Schema extended accordingly.
- The wargov inline manifest (`index.html` L1339) includes a `"local"` field per row that was not in the original `<interfaces>` sketch. `wargovRowSchema` includes it with `z.string().default('')` so the schema round-trips against the existing Python output.
- No `AUDIO` rows found in current data, but kept the enum value since the plan's `<interfaces>` block mentioned it.

### Task 2 — Skeleton data files + README (commit `61b0f91`)

Wrote 14 identical-structure JSON envelopes (only `"slug"` differs) and a ~110-line `data/README.md` covering envelope shape, per-file writer responsibility (mapping who owns each file across Phases 3–5), the fidelity guard (six explicit "no <mutation>" rules tied to CLAUDE.md §9 and D-26..D-28), and the byte-identical idempotency requirement.

## Decisions

| Decision | Rationale |
| --- | --- |
| Entries-object form (`{"v1": {...}}`) over array form | Canonical Astro 5 `file()` loader signature; matches `docs.astro.build/en/reference/content-loader-reference/`; single entry per archive keeps Phase 3 minimal |
| `.strict()` on `catalogAssetSchema`, lenient on envelope | Unknown fields in `assets[]` are drift signals (build-fail); envelope extras are forward-compat-friendly |
| No monolithic `z.union` of envelopes | Per-collection schema attachment (D-02 'planner discretion') keeps error messages clear: a Zod error from `getCollection('wargov')` says `'wargov'`, not "one of these 15 shapes failed" |
| `t` enum extended to 7 values | Real-world grep found `CASE` and `PAGE` in existing arch-data; better to admit them than have build fail when Phase 4 SSG-06 imports real data |
| `Type` field on wargov rows stays `z.string()` | Phase 3 lenient (CSV header churn during research period); tighten to `z.enum` in Phase 4 |
| Zero `z.transform` / `z.preprocess` | Fidelity guard per D-26..D-28; PITFALLS.md #6 (markdown typographer drift). Confirmed via `! grep -q "z\.transform"` in verify block |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — missing critical functionality] Extended `t` enum to include `CASE` and `PAGE`**

- **Found during:** Task 1 (`read_first` step)
- **Issue:** Plan's `<interfaces>` block listed `t: z.enum(['PDF', 'VID', 'IMG', 'CATALOG', 'AUDIO'])` but the plan's own Task 1 action step said "extend the enum if grep of current arch-data finds other types". Grep found `CASE` and `PAGE` actively used in existing arch-data JSON across multiple archives.
- **Fix:** Extended enum to `['PDF', 'VID', 'IMG', 'CATALOG', 'AUDIO', 'CASE', 'PAGE']`. Comment in source cites the grep finding.
- **Files modified:** `src/content.config.ts`
- **Commit:** `1762053`

**2. [Rule 2 — missing critical functionality] Added `local` field to `wargovRowSchema`**

- **Found during:** Task 1 (inspection of `index.html` ~L1339 wargov inline manifest)
- **Issue:** Plan's `<interfaces>` `wargovRowSchema` sketch did not include the `"local"` field, but the existing wargov inline JSON manifest at `index.html` L1339 includes it on every row (currently empty string for all rows). Excluding it would have made the schema fail when Plan 03-03's normalizer round-trips the current data.
- **Fix:** Added `local: z.string().default('')` to `wargovRowSchema`.
- **Files modified:** `src/content.config.ts`
- **Commit:** `1762053`

### Deferred Verification

**3. [Scope boundary — package.json owned by 03-01] `pnpm build` portion of Task 2 automated verify cannot run in this worktree**

- **Issue:** Task 2's automated verify block ends with `&& pnpm build`. The parallel_execution prompt explicitly partitions ownership: "This plan (03-02) does NOT modify package.json — that is owned by 03-01 (in-flight in parallel worktree)." This worktree has `package.json` with no `"build"` script and no Astro installed (`node_modules/astro` absent). Attempting `pnpm build` exits with `ERR_PNPM_RECURSIVE_EXEC_FIRST_FAIL Command "build" not found`.
- **Resolution:** All non-build verify checks ran clean (file existence + JSON parse + slug-literal grep + README content checks + wargov.json absence — see `ALL-STRUCTURAL-CHECKS-OK`). The `pnpm build` step is **deferred to the orchestrator's post-merge verification**: once the orchestrator merges Plan 03-01's worktree (which lands `package.json` + `astro.config.mjs` + Astro install) and Plan 03-02's worktree (this work) onto the same branch, `pnpm install && pnpm build` will execute the schema validation against the 14 skeleton envelopes. This is the intended Wave 1 join point per the phase's plan-ordering, not a scope creep.
- **Action item for orchestrator/verifier:** After merging both Wave 1 worktrees, run `pnpm install --frozen-lockfile && pnpm build` from the merged branch root. Expect: exit 0 with possible "collection X has zero entries" warnings, no schema errors. If schema errors surface, they belong to Plan 03-02 (this plan) — file a fix-up plan.
- **No file modification:** Did not add a `"build"` script to package.json (out of scope per parallel_execution).

## Authentication Gates

None — this plan is pure schema + data scaffolding.

## Self-Check

**1. Files exist:**

```
FOUND: src/content.config.ts
FOUND: data/aaro.json
FOUND: data/nasa.json
FOUND: data/nara.json
FOUND: data/geipan.json
FOUND: data/uk.json
FOUND: data/brazil.json
FOUND: data/chile.json
FOUND: data/argentina.json
FOUND: data/canada.json
FOUND: data/italy.json
FOUND: data/nz.json
FOUND: data/peru.json
FOUND: data/spain.json
FOUND: data/uruguay.json
FOUND: data/README.md
MISSING-AS-INTENDED: data/wargov.json (owned by Plan 03-03)
```

**2. Commits exist:**

```
FOUND: 1762053 — feat(03-02): add Astro Content Collections schema for 15 archives
FOUND: 61b0f91 — feat(03-02): add 14 skeleton data/<slug>.json envelopes + data/README.md
```

**3. Verify blocks (per W1 `set -euo pipefail`):**

```
Task 1 verify: VERIFY-OK
Task 2 verify (structural): ALL-STRUCTURAL-CHECKS-OK
Task 2 verify (pnpm build): DEFERRED — see Deviation #3
```

## Self-Check: PASSED (structural; pnpm build deferred to post-merge orchestrator step)

## Success Criteria Re-check

- [x] `src/content.config.ts` parses (TypeScript surface-level; full validation deferred to post-merge `pnpm build`)
- [x] `export const collections` contains exactly 15 keys matching CLAUDE.md §2 slugs (wargov, aaro, nasa, nara, geipan, uk, brazil, chile, argentina, canada, italy, nz, peru, spain, uruguay) — verified by 15-iteration grep in Task 1 verify
- [x] `catalogEnvelopeSchema` and `wargovEnvelopeSchema` are distinct (no monolithic union)
- [x] Zero `z.transform` / `z.preprocess` invocations (verified by `! grep -q` in Task 1 verify)
- [x] 14 `data/<slug>.json` files present, each declares its `slug` correctly
- [x] `data/wargov.json` is absent (Plan 03-03 will create it)
- [x] `data/README.md` cites D-26..D-28 and names `scripts/normalize-csv.py`
- [x] Per W1: both verify blocks open with `set -euo pipefail` — any silent failure aborts the loop

## What This Unblocks

- **Plan 03-03** (wargov CSV normaliser) can now `import { collections } from '../src/content.config'` and write `data/wargov.json` against a stable schema contract.
- **Plan 03-05** (wargov page render) can `getCollection('wargov')` with a typed return.
- **Phase 4 SSG-06** (14-archive port) inherits this schema unchanged — per-archive normalisers fill `assets[]` and the build validates against the same `catalogEnvelopeSchema` used in skeletons.

## Open Notes for Phase 4

- `wargovRowSchema.Type` should tighten to `z.enum([...])` once CSV column stabilises (currently `z.string()` per Phase 3 lenient policy).
- Watch for new `t` enum members during Phase 4 14-archive import; if grep of `data/*.json` finds new types beyond `['PDF','VID','IMG','CATALOG','AUDIO','CASE','PAGE']`, extend the enum (don't soften to `z.string()`).
- Idempotency requirement in `data/README.md` is enforced by writers (Phase 4 SSG-06) — schema does not check it.

## Threat Flags

None — schema scope is unchanged from plan's `<threat_model>`. T-03-04 (data mutation bypass) mitigation is in place via `.strict()` on `catalogAssetSchema` + `z.enum` on `t`.
