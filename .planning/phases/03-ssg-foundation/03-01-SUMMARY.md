---
phase: 03-ssg-foundation
plan: "01"
subsystem: ssg-scaffold
tags: [astro, cloudflare-adapter, version-pin, zod, papaparse, adr]
requirements: [SSG-01]
dependency_graph:
  requires: []
  provides:
    - "package.json + pnpm-lock.yaml → Astro 5.18.x + @astrojs/cloudflare 12.6.x + Zod + Papaparse installed"
    - "astro.config.mjs → output:'static', cloudflare adapter, smartypants:false, integrations:[]"
    - "tsconfig.json → extends astro/tsconfigs/strict"
    - "ADR .planning/decisions/astro-version-pin.md → defensive ~5.18.0 pin + astro#15684 re-verification"
  affects:
    - "Plan 03-02 (Content Collections schema) — depends on Zod install + Astro 5 file() loader"
    - "Plan 03-03 (CSV normaliser) — depends on Papaparse install"
    - "Plan 03-04 (shared components) — depends on Astro install"
    - "Plan 03-05 (wargov page) — depends on Astro install + adapter"
    - "Phase 4 SSG migration — pin revisited at Phase 4 close per ADR"
tech_stack:
  added:
    - "astro@~5.18.0 (resolved 5.18.2)"
    - "@astrojs/cloudflare@^12.6.0 (resolved 12.6.13, peer ^5.7.0)"
    - "zod@^3"
    - "papaparse@^5 + @types/papaparse"
    - "typescript@~5"
  patterns:
    - "Defensive tilde pin (~5.18.0, NOT ^5) per D-29 — blocks accidental Astro 6 upgrade"
    - "Adapter family pinned alongside framework per D-30 — 12.6.x line declares astro:^5.7.0 peer"
    - "ADR captures re-verification gate at Phase 4 close (not auto-re-decision)"
    - "smartypants:false + remarkPlugins:[] + rehypePlugins:[] per D-28 — defends Pitfall #6 typographer drift"
key_files:
  created:
    - "astro.config.mjs"
    - "tsconfig.json"
    - ".planning/decisions/astro-version-pin.md"
  modified:
    - "package.json (added astro deps + scripts.dev/build/preview/prebuild)"
    - "pnpm-lock.yaml (4152 lines diff — Astro tree + transitive deps)"
    - ".gitignore (added .astro/ types cache)"
decisions:
  - "Tilde pin ~5.18.0 (resolved 5.18.2) — patch-only, no minor drift to 5.19+ without explicit bump"
  - "@astrojs/cloudflare ^12.6.0 (resolved 12.6.13) — 12.6.x line declares astro:^5.7.0 peer, safe within 5.x family"
  - "ADR transitions proposed→accepted (2026-05-25) → revisit at Phase 4 close (gated on wargov + 14-archive + Pagefind + SW + PERF-01 shipping stable)"
  - "output:'static' (D-12..D-15) — CF Pages serves dist/ as static files, no SSR in Phase 3"
  - "integrations:[] (D-23) — NO React/Vue/Svelte islands; NO @vite-pwa/astro until Phase 4 SW-01"
  - "prebuild script is echo placeholder — Plan 03-03 wires scripts/normalize-csv.py"
metrics:
  duration_seconds: 467
  duration_human: "~8 minutes (terminated by API Error: Overloaded after both code commits; SUMMARY written by orchestrator post-merge rescue)"
  tasks_completed: 2
  files_created: 3
  files_modified: 3
  commits: 2
  completed_date: "2026-05-27"
---

# Phase 03 Plan 01: Astro 5.18 Scaffold + Version-Pin ADR Summary

**One-liner:** Astro 5.18.x installed alongside the legacy Python build with a defensive `~5.18.0` tilde pin, `@astrojs/cloudflare` 12.6 adapter, Zod + Papaparse for downstream plans, and an ADR documenting the pin rationale + astro#15684 re-verification per SSG-01 / D-29 / D-30.

## What Shipped

- `astro.config.mjs` (40 lines): `output:'static'` + `cloudflare()` adapter + `markdown.smartypants:false` + `integrations:[]` + `site:'https://realufo.org'`. Comments cite D-12..D-15, D-23, D-28, D-29, D-30.
- `tsconfig.json` (5 lines): extends `astro/tsconfigs/strict` + includes `.astro/types.d.ts`.
- `package.json` extended: `astro@~5.18.0` + `@astrojs/cloudflare@^12.6.0` + `zod@^3` + `papaparse@^5` + `@types/papaparse` + `typescript@~5` + scripts `dev/build/preview/prebuild` (prebuild echo placeholder until Plan 03-03 wires the CSV normaliser).
- `pnpm-lock.yaml` regenerated against the new dependency tree.
- `.gitignore` adds `.astro/` (Astro types cache regenerated each build, must stay generated not tracked).
- `.planning/decisions/astro-version-pin.md` (209 lines): ADR documenting the framework + adapter pin, re-verifying astro#15684 closed status (PR #15711 upstream, closed 2026-03-11), and scheduling a Phase 4 close revisit gate.

## How

### Task 1 — ADR + version-pin decision capture (commit `ea15692`)

Wrote the ADR before touching `package.json` so the rationale is on disk before the pin lands in code. ADR cites:

- D-29 (tilde pin policy)
- D-30 (adapter version pinned alongside framework)
- D-31, D-37, D-39 (Phase 4 revisit gates)
- astro#15684 re-verification (closed upstream via PR #15711, 2026-03-11)

Phase 4 close revisit gated on **all** of: wargov ported + 14-archive port shipped + Pagefind search live + injectManifest SW registered + PERF-01 (≤500 KB/page) hit.

### Task 2 — Astro install + config + verify (commit `196f77d`)

1. Added `astro@~5.18.0` + `@astrojs/cloudflare@^12.6.0` to `package.json#dependencies`. Tilde resolved to 5.18.2 (latest patch in the 5.18 line at pin time).
2. Added `zod@^3` + `papaparse@^5` + `@types/papaparse` + `typescript@~5` to dependencies / devDependencies for downstream plans (03-02 schema, 03-03 normaliser).
3. Wrote `astro.config.mjs` with the static + cloudflare + fidelity-defensive config (smartypants off, empty plugin lists, empty integrations).
4. Wrote `tsconfig.json` extending `astro/tsconfigs/strict`.
5. Added `.astro/` to `.gitignore`.
6. Ran `pnpm install --frozen-lockfile && pnpm build` per commit message: exit 0, `dist/` created. Phase 2 02-01 already gitignored `dist/`; this plan verified persistence.

Zero edits to `scripts/build-*.py` — coexistence invariant per D-12..D-14, D-39.

## Decisions

| Decision | Rationale |
| --- | --- |
| Tilde `~5.18.0` over caret `^5` | D-29 — blocks accidental Astro 6 upgrade. Caret would auto-resolve to 5.19+/6.x on lockfile regen; tilde locks to 5.18.x patches only |
| Adapter `^12.6.0` not pinned exact | 12.6.x line declares `astro:^5.7.0` peer — safe within 5.x family. Caret accepts patches within 12.6 line and minor bumps within 12.x as long as peer remains satisfied |
| ADR before install | Rationale on disk before the pin lands in code — future planner has paper trail even if `package.json` is mid-rewrite |
| `output:'static'` | D-12..D-15 — CF Pages serves `dist/` as static files; Phase 3 ships no SSR |
| `integrations:[]` | D-23 — no React/Vue/Svelte islands; no @vite-pwa/astro until Phase 4 SW-01 |
| `smartypants:false` + empty remark/rehype plugins | D-28 + research/PITFALLS.md §Pitfall #6 — defends content fidelity. Default Astro markdown would silently rewrite quotes/dashes/ellipses, breaking Phase 2 INF-05 fidelity byte-match across 115 archive records |
| `prebuild` is `echo` placeholder | Plan 03-03 wires `scripts/normalize-csv.py`. Empty script would skip the pnpm prebuild hook entirely — explicit echo placeholder preserves the hook surface for 03-03 to overwrite |

## Deviations from Plan

### Mid-flight termination — orchestrator-rescued

**1. Agent died with "API Error: Overloaded" before committing SUMMARY.md**

- **Found during:** Final task — SUMMARY.md write + commit
- **Symptom:** Background executor exited at ~8 minutes with `result: "API Error: Overloaded"`, total_tokens=845 (post-error). 44 tool uses logged.
- **State at termination:** Both task commits landed cleanly (`ea15692` ADR + `196f77d` scaffold). `pnpm install --frozen-lockfile && pnpm build` verified exit 0 per commit message. Working tree clean except untracked `.planning/HANDOFF.json` (stale auto-postool checkpoint, pre-existing). No partial / staged / unstaged code changes.
- **Rescue:** Orchestrator wrote this SUMMARY.md directly in the worktree and committed it before the worktree force-removal step. No production-code changes were attempted by the orchestrator — pure metadata recovery.
- **Risk note:** SUMMARY.md narrative below is reconstructed from commit messages, diffs, and the plan file — not from the agent's own self-report. Verifier should cross-check `must_haves.truths` against actual file state during phase verification.

## Authentication Gates

None — pure install + config + ADR.

## Self-Check

**1. Files exist (in worktree at commit time):**

```
FOUND: astro.config.mjs
FOUND: tsconfig.json
FOUND: package.json (modified)
FOUND: .gitignore (modified — .astro/ added)
FOUND: .planning/decisions/astro-version-pin.md
FOUND: pnpm-lock.yaml (regenerated)
```

**2. Commits exist:**

```
FOUND: ea15692 — docs(03-01): add astro-version-pin ADR (re-verifies astro#15684 closed)
FOUND: 196f77d — feat(03-01): scaffold Astro 5.18 + @astrojs/cloudflare 12.6 (SSG-01)
ORCHESTRATOR-RESCUE: this SUMMARY.md commit (post-merge identifier set by orchestrator)
```

**3. Verify blocks:**

```
Task 1 (ADR write): commit landed
Task 2 (Astro scaffold + pnpm install --frozen-lockfile && pnpm build): VERIFY-OK per commit msg
Task 3 (SUMMARY.md): orchestrator-rescued — see Deviations
```

## Self-Check: PASSED (code complete; SUMMARY orchestrator-rescued)

## Success Criteria Re-check

- [x] Astro 5.18.x pinned as `~5.18.0` in package.json (NOT `^5`, NOT `5.x`) per D-29 — verified in commit `196f77d` diff
- [x] `@astrojs/cloudflare` adapter installed at 12.6.x range per D-30 — verified in commit `196f77d` diff
- [x] `pnpm install --frozen-lockfile && pnpm build` succeeded locally, `dist/index.html` emitted — verified per commit `196f77d` message
- [x] `dist/` gitignored per D-15 — Phase 2 02-01 already added; this plan verified persistence
- [x] ADR `.planning/decisions/astro-version-pin.md` documents pin choice + astro#15684 re-verification (closed 2026-03-11 via PR #15711) — verified in commit `ea15692` diff
- [x] Phase 2 CI gates unaffected — no edits to `_headers`, `_redirects`, `tests/visual-baselines/`, `tests/fidelity-baseline.json`, `tests/tone-colour-baseline.json`, `quality-gates.yml`
- [x] Python build scripts under `scripts/build-*.py` untouched — coexistence invariant per D-12..D-14, D-39

## What This Unblocks

- **Plan 03-02** (Content Collections schema) — Zod installed, Astro 5 `file()` loader from `astro/loaders` reachable
- **Plan 03-03** (CSV normaliser) — Papaparse installed, `pnpm prebuild` hook in place to wire `scripts/normalize-csv.py`
- **Plan 03-04** (shared components) — `src/layouts/` + `src/components/` writable against Astro 5 component API
- **Plan 03-05** (wargov page) — `src/pages/index.astro` renderable; `pnpm build` emits `dist/index.html`
- **Phase 4 close** — pin revisit gated per ADR; not a re-decision, a scheduled re-evaluation

## Open Notes for Phase 4

- Pin revisit at Phase 4 close — review whether 5.18.x is still the latest stable patch line, or if 5.19+/6.x is safe given the all-archives-shipped state
- `prebuild` script overwritten by Plan 03-03 — current placeholder echo is intentional, not a forgotten TODO
- `@types/papaparse` is `devDependencies` (was placed there in install); Papaparse runtime is `dependencies`. Phase 3 build needs both at install time

## Threat Flags

None — install + config + ADR scope. No new attack surface introduced. `@astrojs/cloudflare` is the canonical adapter (audited by Astro maintainers); Zod + Papaparse are widely-used and `@types/papaparse` adds no runtime surface.
