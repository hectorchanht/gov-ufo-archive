---
phase: 05-scrape-automation
plan: "01"
status: complete
subsystem: scrape-automation
tags: [scrape, r2, github-actions, workflow_dispatch, repository_dispatch]
dependency_graph:
  requires:
    - .github/workflows/r2-sync.yml (Phase 4 Plan 04-02 carryover)
    - .planning/decisions/r2-setup.md
    - .planning/phases/05-scrape-automation/05-CONTEXT.md (D-14, D-16, D-21, D-22)
  provides:
    - .github/workflows/r2-sync.yml (rewritten — accepts scrape-promote events)
    - R2 canonical layout seed (BLOCKED on operator workflow_dispatch — Task 3)
  affects:
    - Plan 05-04 (Worker fires repository_dispatch — trigger surface opens here)
    - Plan 05-05 (GH Action ingest pipeline reuses the per-archive narrow sync)
tech_stack:
  added: []
  patterns:
    - "repository_dispatch event_type 'scrape-promote' as Worker→GH Action bridge"
    - "Per-archive narrow scope via workflow_dispatch.archive OR client_payload.archive"
key_files:
  created:
    - .planning/phases/05-scrape-automation/05-01-SUMMARY.md
  modified:
    - .github/workflows/r2-sync.yml
decisions:
  - "Workflow keeps S3-compat (rclone) auth path; Worker→GH bridge does not introduce a second auth scheme."
  - "Per-archive early-return uses env var NARROW_ARCHIVE coalescing inputs.archive ?? client_payload.archive — single code path for both trigger surfaces."
  - "wargov retained its special bundles/Release_1 + bundles/videos layout inside the narrow-scope branch (other slugs use <slug>/bundles + <slug>/videos)."
metrics:
  duration: "~3 min (executable portion; Task 3 operator-action time excluded)"
  completed_date: "2026-05-28"
requirements: [SCRP-03, SCRP-05, SCRP-09]
---

# Phase 5 Plan 05-01: R2 Bulk Seed + Workflow Rewrite Summary

Status: **COMPLETE** — Task 2 (workflow rewrite) shipped + secondary fix `c10dbbf` restricted per-archive loop to active slugs; Task 3 bulk-seed bypassed via direct operator-workstation push (debug session `r2-bulk-seed-wrong-slugs` revealed CI workflow can never seed binaries because they're gitignored; Path A unblock = manual push completed 2026-05-28).

## Task 3 — Bulk seed via operator workstation (2026-05-28)

Workflow run path was abandoned after `gh workflow run r2-sync.yml -f full_sync=true` (run id 26558706277) produced wrong output — only 2 dormant geipan/videos/*.mp4 made it to R2 because every other binary is `.gitignored` (canonical store = GitHub Releases). Full diagnosis: `.planning/debug/r2-bulk-seed-wrong-slugs.md`.

**Path A unblock — direct R2 push from operator workstation:**

- **207 wargov files uploaded** via wrangler r2 object put (OAuth, 300 MiB cap), parallel-8:
  - 116 PDFs `bundles/Release_1/*.pdf` → `pdfs/wargov/`
  - 6 PDFs `bundles/release_02_document_bundle/*.pdf` → `pdfs/wargov/`
  - 28 mp4s `bundles/uapvideos/*.mp4` → `videos/wargov/`
  - 55 mp4s `bundles/uap052226/*.mp4` (under 300 MiB) → `videos/wargov/`
- **2 large mp4s via aws s3 cp** (R2 S3-compat multipart upload):
  - `DOD_111719718.mp4` (513 MB)
  - `DOD_111721737.mp4` (416 MB)
- **2 dormant geipan/videos/*.mp4 purged** via `wrangler r2 object delete`. CF edge cache holds 4h `max-age`; origin confirmed 404 via `wrangler r2 object get`.
- **aaro/videos/*.mp4 (32 files)** were already in R2 from a prior manual seed and had correct `content-type: video/mp4` — not re-uploaded.

**Final R2 state (post-seed, post-purge):**
- `pdfs/wargov/` — 122 files (R01+R02)
- `videos/wargov/` — 85 files
- `videos/aaro/` — 32 files (pre-existing)
- `videos/geipan/` — empty (purged); CDN cache will catch up in 4h
- `pdfs/nasa/`, `pdfs/nara/` — still empty (no local source on this workstation; pulls from `pdfs-v1` GH Release tag remain pending — separate follow-up)

**Verification curls (2026-05-28T09:01Z):**
```
HTTP/2 200 content-type: application/pdf  pdfs/wargov/059UAP00011.pdf
HTTP/2 200 content-type: video/mp4         videos/wargov/DOD_111719718.mp4 (513 MB multipart)
HTTP/2 200 content-type: video/mp4         videos/wargov/DOD_111720861.mp4 (wrangler upload)
HTTP/2 200 content-type: video/mp4         videos/aaro/DOD_108981629.mp4 (pre-existing)
geipan origin → 404 (CDN cache 4h until purge)
```

## Task 3 — Gap closure (nasa + nara + aaro PDFs, 2026-05-28T13:55Z)

Followed up with second pass to close remaining v1 R2 surface gaps:
- **4 nasa PDFs** downloaded from `pdfs-v1` release + uploaded to `pdfs/nasa/` via wrangler
- **49 nara PDFs** downloaded from `pdfs-v1` release + uploaded to `pdfs/nara/` (P=8 parallel)
- **10 aaro PDFs** downloaded from `pdfs-v1` + uploaded to `pdfs/aaro/`

**Final v1 R2 surface (302 objects across 4 active archives):**
- `pdfs/wargov/` — 122 (R01 116 + R02 6)
- `pdfs/aaro/` — 10
- `pdfs/nasa/` — 4
- `pdfs/nara/` — 49
- `videos/wargov/` — 85 (R01 28 + R02 57)
- `videos/aaro/` — 32 (pre-existing, content-type=video/mp4 confirmed)
- `videos/geipan/` — purged (CDN cache self-clears 4h)

**4 aaro PDFs still missing — referenced in `data/aaro.json` but absent from `pdfs-v1` release tag AND local disk:**
- `AARO_Declassification_Info_Paper_2025.pdf`
- `AARO_HISTORICAL_RECORD_REPORT_2024.PDF`
- `AAROs_Supplement_to_ORNLs_Analysis_of_a_Metallic_Specimen.pdf`
- `ORNL-Synopsis_Analysis_of_a_Metallic_Specimen.pdf`

These need cron scrape from `aaro.mil` once Plan 05-04 lands — that's the natural ingest path (Worker fetches AARO source → R2 staging → release-upload).

**Follow-up backlog:**
- Plan 05-01b (deferred): CI-driven staging script (`scripts/stage-r2-from-releases.py`) reads `data/<slug>.json` + `release-manifest.json`, downloads from GH Releases to `/tmp/r2-stage/`, then rclone syncs. Removes operator-workstation dependency for future seeds.
- 4 aaro PDFs above — defer to Plan 05-04 cron scrape ingest (not a Plan 05-01 gap, since they were never in the release inventory to begin with).

## One-Liner

Rewrote `.github/workflows/r2-sync.yml` to accept `repository_dispatch` events of type `scrape-promote` (forward-compat for Plan 05-05) plus three workflow_dispatch inputs (`full_sync`, `archive`, `asset_keys`); operator must commit/push the file + bulk-seed R2 to finish Wave 0.

## Task 1 — Operator gate (pre-cleared by orchestrator)

Verification outputs captured by the orchestrator at dispatch time (executor did NOT re-run these — gate was pre-cleared per task brief):

| Check | Command | Expected | Observed |
|-------|---------|----------|----------|
| Phase 4 push state | `git log origin/main..HEAD --oneline` (in main checkout, pre-dispatch) | 0 rows | 0 rows |
| gh auth identity | `gh auth status` | "Logged in to github.com account hectorchanht" | active account `hectorchanht` (token scopes include `workflow`) |
| Workflow registry | `gh workflow list --repo hectorchanht/gov-ufo-archive` | includes `r2-sync.yml` | id 284673222 (active) |

Outcome: All three sub-gates GREEN. Plan 05-01 cleared to proceed to Task 2.

## Task 2 — r2-sync.yml rewrite (DONE — commit `4a1c651`)

### Event-trigger diff (the load-bearing additions)

The PUSH paths-filter block, secrets block, `concurrency` group, `timeout-minutes: 30`, and the full rclone install + config + cleanup steps are byte-identical to the Phase 4 version. Only the `on:` block and the diff/sync steps changed.

`on:` block — additions only:

```yaml
  workflow_dispatch:
    inputs:
      full_sync:
        # (unchanged from Phase 4 — preserved verbatim)
        type: boolean
        default: false
      archive:
        description: 'Per-archive narrow scope (slug). Empty = all archives.'
        type: string
        default: ''
      asset_keys:
        description: 'JSON array of staging object keys for incremental promote (Plan 05-05).'
        type: string
        default: ''
  # Phase 5 Plan 05-01 — Worker→GH Action ingest pipeline trigger.
  repository_dispatch:
    types: [scrape-promote]
```

Step 4 (diff detection) — added third branch:

```yaml
elif [ "${{ github.event_name }}" = "repository_dispatch" ]; then
  echo "files=DISPATCH" >> "$GITHUB_OUTPUT"
  echo "diff-mode: repository_dispatch (Plan 05-04 Worker fingerprint-diff already executed; rclone --checksum drives the actual upload set)"
  echo "client_payload.archive=${{ github.event.client_payload.archive }}"
```

Step 5 (sync) — added early-return guard at top of run block:

```yaml
env:
  NARROW_ARCHIVE: ${{ github.event.inputs.archive || github.event.client_payload.archive || '' }}
run: |
  if [ -n "${NARROW_ARCHIVE}" ]; then
    # wargov uses bundles/Release_1 + bundles/videos; all other slugs
    # use <slug>/bundles + <slug>/videos. Sync ONLY the requested slug,
    # then exit 0 (skip the all-archive scaffold loop below).
    ...
    exit 0
  fi
  # ...else fall through to existing all-archive scaffold (unchanged)
```

### Acceptance criteria (Task 2)

| Criterion | Result |
|-----------|--------|
| YAML parses as valid | PASS (python3 YAML safe_load) |
| `grep -c 'repository_dispatch'` ≥ 1 | 9 occurrences |
| `grep -c 'scrape-promote'` ≥ 1 | 3 occurrences |
| `grep -c 'rclone.org/install.sh'` ≥ 1 | 2 occurrences (install + comment) |
| `grep -c 'cancel-in-progress: false'` ≥ 1 | 1 (T-04-07 preserved) |
| `grep -c 'CLOUDFLARE_R2_ACCESS_KEY'` ≥ 1 | 2 occurrences (secret name unchanged) |
| Three workflow_dispatch inputs present | PASS (`full_sync`, `archive`, `asset_keys`) |

yamllint default profile reports line-length errors (>80 chars) on lines that are also flagged in the pre-edit baseline (the existing Phase 4 file + `quality-gates.yml` both have the same default-profile errors). Under the `yamllint relaxed` profile — which is the project's de-facto convention (no `.yamllint` config in repo, no CI yamllint job) — the new file emits only warnings and exits 0. Same shape as the Phase 4 baseline; nothing new introduced.

### Commit

```
4a1c651 feat(05-01): r2-sync.yml — repository_dispatch + per-archive scope
```

## Task 3 — BLOCKED ON OPERATOR

This task is `checkpoint:human-action` and CANNOT be executed by the worktree agent — it requires Hector to commit/push the rewrite to the `hectorchanht/gov-ufo-archive` remote, trigger the bulk-seed `workflow_dispatch`, and curl 3 R2 URLs to confirm HTTP/2 200 + CORS echo.

### Operator runbook

1. **Land the rewrite on remote main:**
   ```bash
   # On Hector's local clone with push access to hectorchanht/gov-ufo-archive
   git add .github/workflows/r2-sync.yml
   git commit -m "feat(05-01): rewrite r2-sync.yml — repository_dispatch + per-archive scope"
   git push origin main
   ```
   (Frank cannot push — D-21. The orchestrator-side commit `4a1c651` was made on the per-worktree branch and merges into the consolidating main branch when the orchestrator closes Wave 0.)

2. **Trigger the bulk seed** (D-15):
   ```bash
   gh workflow run r2-sync.yml -f full_sync=true --repo hectorchanht/gov-ufo-archive
   gh run watch --repo hectorchanht/gov-ufo-archive
   ```
   Expected runtime ~5–10 min per `.planning/decisions/r2-setup.md` §First-run bulk migration method. Final status must be `conclusion: success`.

3. **Spot-check 3 R2 URLs** (one per asset type per archive coverage). Operator picks real filenames from `bundles/Release_1/`, `bundles/videos/`, and one of `aaro/bundles/` / `nasa/bundles/` / `nara/bundles/`:

   ```bash
   # wargov PDF (pick any from `ls bundles/Release_1/*.pdf | head -3`)
   curl -sI -H "Origin: https://realufo.org" \
     "https://assets.realufo.org/pdfs/wargov/<filename>.pdf"

   # wargov video (pick any from `ls bundles/videos/*.mp4 | head -3`)
   curl -sI -H "Origin: https://realufo.org" \
     "https://assets.realufo.org/videos/wargov/<filename>.mp4"

   # one of aaro/nasa/nara PDF — substitute as available
   curl -sI -H "Origin: https://realufo.org" \
     "https://assets.realufo.org/pdfs/aaro/<filename>.pdf"
   ```

   Each MUST return `HTTP/2 200` with `access-control-allow-origin: https://realufo.org` echoed.

4. **Resume signal:** Operator pastes the 3 curl outputs + the dispatched run URL back to the orchestrator (or whoever resumes 05-01). If any URL returns 404, capture the exact filename + folder layout — the rclone sync targets in the new r2-sync.yml may need a fix (most likely the `aaro/bundles/` path doesn't exist in current scope; substitute nasa or nara).

### What blocking does to downstream waves

- **Wave 1 (Plan 05-02 — wrangler.toml + KV namespace + Worker skeleton):** READY. Plan 05-02 has `depends_on: []` per the wave-1 declaration and does NOT depend on Task 3 completion — the wrangler scaffold work is purely local. Wave 1 can start in parallel right now.
- **Wave 3 (Plan 05-05 — release-upload.py + GH Action ingest pipeline):** UNBLOCKED ONLY when operator completes Task 3. Plan 05-05's ingest pipeline assumes R2 has the canonical 4-archive corpus to diff against; without the bulk seed, every Worker promote would treat staging→canonical as an empty-bucket fill and the per-archive narrow-sync path would have nothing to compare against.

## Deviations from Plan

None. Plan 05-01 executed per spec; the partial state is by design (Task 3 is explicitly checkpoint:human-action in the plan and cannot be executor-fulfilled).

## Threat Surface Scan

No new threat surface introduced beyond what the plan's `<threat_model>` already mitigates (T-05-01-01 through T-05-01-SC). The rewrite preserves all Phase 4 mitigations (T-04-05/06/07/SC) and adds one new auth surface — the `repository_dispatch` trigger — which is gated by GitHub's own dispatch ACL per T-05-01-01.

## Known Stubs

None. All wired logic in the rewrite is exercised by either workflow_dispatch (full_sync path or narrow-scope path) OR the existing push-paths-filter path OR the new repository_dispatch path. No placeholder data, no UI rendering.

## Self-Check

- `.github/workflows/r2-sync.yml` exists and contains all required tokens (verified post-edit via grep).
- Commit `4a1c651` exists on branch `worktree-agent-a1dec3595c62baf8a` (verified via `git rev-parse HEAD`).
- SUMMARY.md created at the canonical path `.planning/phases/05-scrape-automation/05-01-SUMMARY.md`.

## Self-Check: PASSED
