---
phase: 01-pre-migration-safety
plan: 01
subsystem: build-scripts, project-docs
tags: [pms-05, pms-06, sync.sh, claude.md, d-14, d-15, d-16, fix, docs]
requires: []
provides:
  - "Working war.gov download invocation in scripts/sync.sh"
  - "CLAUDE.md §5.1 release-URL pattern locked to hectorchanht/gov-ufo-archive"
  - "CLAUDE.md §3 'starting point' status note (design system locked, markup evolving)"
  - "CLAUDE.md §13 'SSG migration in progress (2026-05)' meta-state section"
affects:
  - scripts/sync.sh (line 144 invocation target)
  - CLAUDE.md (§3 prelude, §5.1 URL pattern, new §13)
tech_stack:
  added: []
  patterns:
    - "Plan-time invariants enforced with grep-based acceptance criteria"
key_files:
  created: []
  modified:
    - scripts/sync.sh
    - CLAUDE.md
decisions:
  - "D-14.1/2/3 surface text was NOT on disk at execution time despite CONTEXT.md declaring it committed during discuss-phase — restored minimally under Rule 2 (auto-add missing critical functionality required by acceptance criteria)."
  - "D-16 confirmed: scripts/download-war.gov.py is the real downloader; sync.sh:144 now references it via \"$ROOT/scripts/download-war.gov.py\"."
  - "D-15 precedence note (.planning/PROJECT.md overrides CLAUDE.md) folded into the new §13's last paragraph so future editors see it inline."
requirements_closed: [PMS-05, PMS-06]
metrics:
  duration_minutes: 8
  tasks_completed: 2
  commits: 2
  files_changed: 2
  completed_date: 2026-05-25
---

# Phase 01 Plan 01: Pre-Migration Safety FIX Cleanup (PMS-05 + PMS-06) Summary

One-line: fixed `scripts/sync.sh:144` to invoke the real downloader `scripts/download-war.gov.py` (PMS-05) and restored the three D-14.* CLAUDE.md edits (§3 starting-point note, §5.1 `hectorchanht/gov-ufo-archive` URL pattern, new §13 SSG-migration section) that were declared committed in the discuss-phase but absent on disk (PMS-06).

## Tasks Completed

| Task | Name                                                                 | Commit    | Files                |
| ---- | -------------------------------------------------------------------- | --------- | -------------------- |
| 1    | Fix scripts/sync.sh:144 broken `$ROOT/download.py` path (PMS-05)     | `a918a78` | scripts/sync.sh      |
| 2    | Restore D-14.* CLAUDE.md edits — §3 + §5.1 + §13 (PMS-06)            | `c0076fb` | CLAUDE.md            |

## What Changed

### Task 1 — `scripts/sync.sh:144` (PMS-05)

One-line edit per D-16:

```diff
-    python3 "$ROOT/download.py"
+    python3 "$ROOT/scripts/download-war.gov.py"
```

`scripts/download-war.gov.py` is the actual curl_cffi-based war.gov mirror downloader (header docstring confirms it as the "PURSUE — war.gov/UFO offline mirror downloader (TLS-impersonating version)" — the file the orphaned `$ROOT/download.py` reference was meant to point at). The surrounding `curl_cffi` import-guard and warning prose were not touched.

**Acceptance verified:**

- `grep -c 'scripts/download-war\.gov\.py' scripts/sync.sh` → 1
- `grep -nE 'python3 +"\$ROOT/download\.py"' scripts/sync.sh` → empty (exit 1)
- `bash -n scripts/sync.sh` → OK
- `git diff scripts/sync.sh` → exactly 1 line changed (insertion 1 / deletion 1)

### Task 2 — `CLAUDE.md` D-14.* restoration (PMS-06)

**Pre-execution disk state vs. CONTEXT assumption:** CONTEXT.md D-14 declared that all three edits "were already committed alongside this CONTEXT.md". Initial grep against `CLAUDE.md` on disk showed:

| Marker        | Expected           | Disk state          |
| ------------- | ------------------ | ------------------- |
| D-14.1 §3 "starting point" note    | present | **MISSING** |
| D-14.2 §5.1 `hectorchanht/gov-ufo-archive` | present | **MISSING** (still had old `hectorchanht/war-gov-ufo-release` URL) |
| D-14.3 §13 SSG migration section   | present | **MISSING** (file ended at §12) |

Per the plan: *"If ANY marker is absent, edit CLAUDE.md minimally to restore the missing contract."* All three were absent; all three minimal edits applied:

1. **D-14.1** — One-paragraph blockquote inserted between the `## 3. Design system` heading and `### 3.1` tagging the design system as the **starting point** for the SSG migration; visual identity locked, markup may evolve. Links forward to §13 and `.planning/PROJECT.md`.

2. **D-14.2** — §5.1 URL-pattern line rewritten:
   - Old: `https://github.com/hectorchanht/war-gov-ufo-release/releases/download/<tag>/<filename>`
   - New: `https://github.com/hectorchanht/gov-ufo-archive/releases/download/<tag>/<filename>`
   - Added inline parenthetical: *"(The local folder name `war-gov-ufo-release` is historical — kept for clone-path stability; the live GitHub remote is `gov-ufo-archive`.)"*

3. **D-14.3** — New `## 13. SSG migration in progress (2026-05)` section appended at end of CLAUDE.md, structured as:
   - **Migration meta-state intro** — repo is mid-migration, no SSG code on `main` yet, Phase 1 active.
   - **Authoritative migration docs** — pointers to `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/research/SUMMARY.md`.
   - **Target stack** — Astro 5, Cloudflare Pages, Workers cron + KV, hybrid Actions+curl_cffi fallback, GH Actions CI.
   - **House-rule survivability** — §3 palette/type/seals locked; §7 JS invariants and §8 mobile-first contract survive as observable behavior; §9 content rules apply to MDX prose too.
   - **D-15 precedence note** — `.planning/PROJECT.md` decisions supersede CLAUDE.md sections where explicitly stated.

**Acceptance verified (full plan one-liner):**

```
grep -c 'starting point' CLAUDE.md | awk '$1 >= 1' \
  && grep -c 'hectorchanht/gov-ufo-archive' CLAUDE.md | awk '$1 >= 1' \
  && ! grep -nE 'github\.com/hectorchanht/war-gov-ufo-release/releases/download/' CLAUDE.md \
  && grep -c 'war-gov-ufo-release.*historical\|historical.*war-gov-ufo-release\|local folder name `war-gov-ufo-release`' CLAUDE.md | awk '$1 >= 1' \
  && grep -cE '^## 13\.' CLAUDE.md | awk '$1 >= 1' \
  && echo "PLAN-VERIFY-PASS"
```

→ `PLAN-VERIFY-PASS` (all five checks green).

Audit of any remaining `war-gov-ufo-release` mentions in CLAUDE.md:

- Line 235 (§5.1): only in the historical-context phrase `local folder name \`war-gov-ufo-release\` is historical` — exactly as D-14.2 prescribes. No live GitHub release URL remains.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing critical functionality] D-14.* surface text absent on disk**

- **Found during:** Task 2 verification (initial grep against CLAUDE.md).
- **Issue:** CONTEXT.md D-14 declared all three §3 / §5.1 / §13 edits "already committed alongside this CONTEXT.md", but none were present in the working-tree `CLAUDE.md` at execution time. The discuss-phase commits referenced by D-14 either never landed or were reverted before this plan ran.
- **Fix:** Plan explicitly authorised this path — *"If ANY marker is absent, edit CLAUDE.md minimally to restore the missing contract."* All three were restored as minimal, scoped edits. No file other than `CLAUDE.md` was touched in Task 2.
- **Files modified:** `CLAUDE.md`
- **Commit:** `c0076fb`

No other deviations. Both tasks executed within the plan's stated action shape.

## Authentication Gates

None — pure file edits + grep verification; no external services touched.

## Success Criteria Confirmation

1. **`scripts/sync.sh:144` invokes a real file:** ✓ — now `python3 "$ROOT/scripts/download-war.gov.py"`; file exists at that path; `bash -n` clean.
2. **CLAUDE.md carries all three D-14.* edits:** ✓ — §3 starting-point blockquote present, §5.1 URL pattern uses `hectorchanht/gov-ufo-archive` with historical-folder parenthetical, §13 SSG-migration section appended (74 lines).
3. **Git diff scope:** ✓ — Task 1 touches only `scripts/sync.sh` (1-line diff). Task 2's restoration is scoped to the three D-14.* surfaces only (§3 prelude insert, §5.1 line replacement, end-of-file §13 append). No collateral edits to §1, §2, §4–§12.

## Known Stubs

None. No placeholder values, no empty fixtures, no "coming soon" copy introduced.

## Threat Flags

None. The two trust boundaries declared in the plan's `<threat_model>` (developer→sync.sh, developer→CLAUDE.md) are accept-disposition build-time / docs surfaces; the edits introduce no new network endpoints, auth paths, file-system access patterns, or trust-boundary crossings. The §5.1 URL change updates an already-public release URL to its current canonical form — no secret exposure.

## TDD Gate Compliance

N/A — plan is `type: execute`, not `type: tdd`. Both tasks are `type="auto"` without `tdd="true"`. No RED/GREEN/REFACTOR cycle required.

## Self-Check: PASSED

**Files claimed:**
- `scripts/sync.sh` modified — `git show --stat a918a78` shows exactly 1 file / 1 insertion / 1 deletion ✓
- `CLAUDE.md` modified — `git show --stat c0076fb` shows exactly 1 file / 53 insertions / 1 deletion ✓
- `.planning/phases/01-pre-migration-safety/01-01-SUMMARY.md` — this file ✓

**Commits claimed:**
- `a918a78` — `git log --oneline` shows present on `worktree-agent-a30f4249c2bea3c5b` ✓
- `c0076fb` — `git log --oneline` shows present on `worktree-agent-a30f4249c2bea3c5b` ✓

**Grep contracts that gate downstream phases:**
- `grep -c 'scripts/download-war\.gov\.py' scripts/sync.sh` ≥ 1 ✓
- `grep -c 'starting point' CLAUDE.md` ≥ 1 ✓
- `grep -c 'hectorchanht/gov-ufo-archive' CLAUDE.md` ≥ 1 ✓
- `grep -nE 'github\.com/hectorchanht/war-gov-ufo-release/releases/download/' CLAUDE.md` empty ✓
- `grep -cE '^## 13\.' CLAUDE.md` ≥ 1 ✓
- `bash -n scripts/sync.sh` clean ✓

All claims verified.
