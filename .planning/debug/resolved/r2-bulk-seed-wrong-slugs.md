---
slug: r2-bulk-seed-wrong-slugs
status: resolved
trigger: "r2 bulk seed wrong contents — videos/ folder has only geipan + aaro, missing wargov + nasa + nara. wargov uses special bundles/videos/ layout per CLAUDE.md §5; geipan is dormant but apparently got synced. Suspect r2-sync.yml per-archive loop path mismatch. Check workflow run log + rclone targets in .github/workflows/r2-sync.yml."
created: "2026-05-28"
updated: "2026-05-28"
phase: "05-scrape-automation"
plan: "05-01"
---

# Debug: r2-bulk-seed-wrong-slugs

## Symptoms

- **Expected:** After operator ran `gh workflow run r2-sync.yml -f full_sync=true --repo hectorchanht/gov-ufo-archive`, R2 bucket `realufo` should contain `videos/<slug>/<basename>.mp4` for all 4 ACTIVE archives per CLAUDE.md §2 — `wargov`, `aaro`, `nasa`, `nara`.
- **Actual:** R2 `videos/` has only `geipan/` (DORMANT) and `aaro/` (ACTIVE). Missing: `wargov`, `nasa`, `nara`.
- **Error messages:** None — silent wrong contents. `gh run watch` exited 0 (success).
- **Timeline:** First observed immediately after Plan 05-01 bulk-seed run (commit `2457349` rewrote `r2-sync.yml`).
- **Reproduction:** `rclone ls r2-realufo:realufo/videos/ | awk -F/ '{print $1}' | sort -u` OR equivalent listing.

## Suspected causes (initial hypotheses)

1. **wargov special layout path mismatch** — CLAUDE.md §5 specifies wargov videos live at `bundles/videos/` (not `wargov/videos/`). The rewritten r2-sync.yml per-archive loop may iterate `<slug>/videos/` only, missing wargov.
2. **Per-slug loop iterates dormant archives** — The Phase 4 r2-sync.yml may still iterate all 15 archive slugs (including geipan + 10 other dormant). geipan got synced because `geipan/videos/` exists locally with tracked content; wargov source path mismatch + nasa/nara have no `<slug>/videos/` directory (videos in those archives may be GitHub Releases only, not git-tracked).
3. **nasa/nara videos not git-tracked** — Per CLAUDE.md §5.2, videos generally live in `videos-v1` GH Release; nasa/nara may have no `<slug>/videos/` directory at all, so rclone sync has nothing local to push.
4. **rclone copy filter or `--include` blocked the wargov path** — Less likely; current yml uses per-archive loops, not global filters.

## Current Focus

- **hypothesis:** Combination of #1 + #2 + #3 — r2-sync.yml per-archive loop hardcodes `<slug>/videos/` for all 15 archives; wargov special bundles layout makes it skip; nasa/nara have no local videos so rclone sync source is empty; geipan local videos exist and were swept in despite being DORMANT.
- **test:** Read `.github/workflows/r2-sync.yml` (post-rewrite commit `2457349`); inspect the per-archive sync loop; list local `wargov/videos/`, `nasa/videos/`, `nara/videos/`, `bundles/videos/`, `geipan/videos/` to confirm source presence.
- **expecting:** loop iterates dormant slugs + uses `<slug>/videos/` pattern; `bundles/videos/` present but not aliased to `wargov/`; `nasa/videos/` and `nara/videos/` absent or empty locally.
- **next_action:** Read r2-sync.yml + ls the 5 video paths above. Confirm hypothesis, then propose fix (special-case wargov to map `bundles/videos/` → `videos/wargov/`; restrict per-slug loop to ACTIVE slugs only — `wargov`, `aaro`, `nasa`, `nara`).

## Evidence

- timestamp: 2026-05-28T07:50Z — Read `.github/workflows/r2-sync.yml` post-Plan-05-01. The wargov special-case IS correctly written (lines 280-298 + 237-253 sync `bundles/Release_1/` → `pdfs/wargov/` and `bundles/videos/` → `videos/wargov/`). The per-archive loop (lines 304-305) iterates all 14 non-wargov slugs: `aaro nasa nara geipan uk brazil chile argentina canada italy nz peru spain uruguay` — includes 11 DORMANT slugs that should not be in v1 R2 per CLAUDE.md §2.

- timestamp: 2026-05-28T07:51Z — Local filesystem check (`ls -d <dir>`) of all 15 candidate source dirs. **Result: 14 of 16 source dirs ABSENT on filesystem.**
  - PRESENT: `geipan/videos/` (2 entries), `aaro/videos/` (32 entries), `bundles/Release_1/` (116 entries on disk)
  - ABSENT: `wargov/videos`, `nasa/videos`, `nara/videos`, `bundles/videos`, plus all 11 other `<slug>/videos/` and 14 `<slug>/bundles/`.

- timestamp: 2026-05-28T07:52Z — Git-tracked check (`git ls-files`). **Only 2 video files are tracked in git at all.**
  - `git ls-files | grep -E '\.(mp4|webm|mov)$'` returns ONLY: `geipan/videos/Lyon-2019-12-19.mp4`, `geipan/videos/Saint-Germain-en-Laye-2020-05-30.mp4` (committed before the gitignore rule).
  - `git ls-files bundles/Release_1/` returns 0 — every PDF on local disk is `.gitignored` (per `bundles/Release_1/*.pdf` rule).
  - `git ls-files aaro/videos/` returns 0 — `aaro/videos/` is in `.gitignore`. The 32 local mp4s (2.6 GiB) exist only on operator's machine.

- timestamp: 2026-05-28T07:53Z — `.gitignore` confirms intentional exclusion: `bundles/Release_1/*.pdf`, `aaro/videos/`, `geipan/videos/`, `bundles/uapvideos/`, `bundles/uap052226/` are all excluded. The two geipan/videos mp4s slipped past because they were committed before the rule was added.

- timestamp: 2026-05-28T07:54Z — Inspected workflow run history (`gh run list --workflow=r2-sync.yml`). Three runs today; the bulk-seed run (id 26558706277, 06:29:59Z, success, full_sync=true): **only ONE sync group fired — `Sync geipan/videos/ → videos/geipan/`**, transferring the 2 mp4s (44.381 MiB total). The post-sync `rclone size r2-realufo:realufo` reported `Total objects: 2`. The later 07:42 run with the same payload showed `Total objects: 196 / 2.776 GiB` — meaning ~194 objects in R2 came from a different ingest path (pre-Plan-05-01 manual seed by operator from their local disk, where `aaro/videos/` and `bundles/Release_1/` exist).

- timestamp: 2026-05-28T07:55Z — GH Release inventory: `videos-v1` (62 assets, mostly `DOD_*.mp4` for AARO use), `pdfs-v1` (233 assets, all 4 ACTIVE archive PDFs), `wargov-r02-v1` (63 assets, Release 02), plus per-archive tags (`nasa-v1`, `nara-v1`, etc — but `nasa-v1` and `nara-v1` are EMPTY of assets; `aaro-v1` does NOT exist). Asset filenames inside `videos-v1` are FLAT (no `<slug>/` prefix; e.g. `DOD_108981629.mp4`). `release-manifest.json` confirms the schema is `{ pdfs: { <filename>: <release-url> }, videos: { <filename>: <release-url> } }` — flat, no slug grouping.

- timestamp: 2026-05-28T07:56Z — Cross-reference per-archive asset JSON (`data/<slug>.json` → `v1.assets[]`). The `l` field (local path) shows where each archive expects its assets to live in R2:
  - aaro: 32 videos with `l='https://assets.realufo.org/videos/aaro/DOD_*.mp4'` — 32 expected in R2 `videos/aaro/`
  - nasa: 0 videos, 4 PDFs with `l='https://assets.realufo.org/pdfs/nasa/<file>.pdf'`
  - nara: 0 videos, 49 PDFs with `l='https://assets.realufo.org/pdfs/nara/<file>.pdf'`
  - wargov: data/wargov.json + wargov-shard-{2..5}.json all empty (`v1.assets: []`) — wargov data lives in `bundles/Release_1/` + `uap-release001.csv`, sourced through Astro content collection at build time.

## Eliminated

- **H1 (wargov special path mismatch)** — ELIMINATED. The workflow correctly special-cases wargov: `bundles/Release_1/` → `pdfs/wargov/`, `bundles/videos/` → `videos/wargov/` (lines 237-298). The special-case logic is right; it just never fires on the runner because `bundles/Release_1/` is `.gitignored` and `bundles/videos/` doesn't exist anywhere in the project.

- **H4 (rclone --include filter blocked path)** — ELIMINATED. No global `--include` filter exists; each `rclone sync` invocation has its own `--include` that matches `*.pdf` / `*.mp4` / `*.webm` / `*.mov` correctly. The bug is upstream of rclone — there's nothing on the runner to sync.

## Root Cause

The R2 sync workflow has **two independent, compounding bugs**:

**Primary bug — Wrong source-of-truth model.** The workflow assumes the GitHub Actions runner checkout will materialize `<slug>/bundles/` and `<slug>/videos/` directories containing the binaries, then `rclone sync` will push them to R2. **This assumption is false for every directory except `geipan/videos/`.** Per CLAUDE.md §5.2 + the project's `.gitignore`, every PDF and every MP4 is excluded from git (`bundles/Release_1/*.pdf`, `aaro/videos/`, file >100 MB rule, etc.). The canonical binary store is **GitHub Releases** (`videos-v1`, `pdfs-v1`, `wargov-r02-v1`), NOT the git tree. The runner's checkout sees an empty `bundles/Release_1/` and no `aaro/videos/` at all, so every `[ -d ]` guard fails and every `rclone sync` is silently skipped.

The only file synced by today's bulk-seed run was the **2 geipan/videos/ mp4s** — which slipped past `.gitignore` because they were committed in a much earlier commit, before the `geipan/videos/` ignore rule existed. That accidental inclusion is the ENTIRE explanation for why R2 has `videos/geipan/`.

**Secondary bug — Per-archive loop iterates dormant slugs.** Lines 304-305 iterate all 14 non-wargov slugs including `geipan uk brazil chile argentina canada italy nz peru spain uruguay`. Per CLAUDE.md §2, only `aaro nasa nara` are ACTIVE (plus the special-cased `wargov`). Even after fixing the primary bug, the loop would happily sync `geipan/`, `uk/`, etc. into v1 R2 — pollution of the active surface. (This bug is dormant today only because none of those archives have on-runner files; once the primary bug is fixed, this bug becomes live.)

**Why operator observed `videos/aaro/`:** The bucket already contained 196 objects (2.776 GiB) from a **prior ingest path** — almost certainly the operator's local `rclone sync` from their workstation (where `aaro/videos/` has 2.6 GiB of un-tracked DOD videos sitting on disk, mirrored locally from `videos-v1`). That manual seed happened before Plan 05-01's workflow rewrite. The workflow itself did not push `videos/aaro/`; it merely failed to overwrite/correct the pre-existing state. The "extra geipan, missing wargov/nasa/nara" pattern is the workflow's actual behaviour; the "present aaro" is residue from manual seeding.

## Fix

**Two-part fix** addressing both bugs:

1. **Restrict the per-archive loop to ACTIVE slugs only.** Replace `for slug in aaro nasa nara geipan uk brazil chile argentina canada italy nz peru spain uruguay` with `for slug in aaro nasa nara`. Add a comment pointing at CLAUDE.md §2's active-archive list and noting that re-activating a dormant archive requires adding its slug here AND to `Nav.astro` / `Footer.astro` / `RootLayout.astro`.

2. **Switch the source-of-truth from runner-checkout to GitHub Releases.** Add a new step **before** the rclone sync that downloads from the canonical GH Releases onto the runner into `/tmp/r2-stage/<prefix>/<slug>/`, using `gh release download` with a slug→tag mapping. Then point `rclone sync` at the staging directory instead of the (empty) repo checkout dirs.

The slug→tag mapping (based on current release inventory):

| R2 prefix | Source release tag | Notes |
|---|---|---|
| `pdfs/wargov/` | `pdfs-v1` + `wargov-r02-v1` | r02 is the Release 02 supplement; r01 lives in pdfs-v1 (per the 165-PDF blob description) |
| `videos/wargov/` | `videos-v1` (filter: `^(?!DOD_)` — non-DOD = wargov bundle videos) | OR maintain a manifest mapping. See note below. |
| `pdfs/aaro/` | `pdfs-v1` (filter by manifest entries cat='Document' for aaro) | data/aaro.json declares 16 PDFs but `l` is empty for them; needs manifest enrichment |
| `videos/aaro/` | `videos-v1` (filter: `DOD_*.mp4`) | 32 of the 60 DOD videos per data/aaro.json |
| `pdfs/nasa/` | `pdfs-v1` (4 NASA report PDFs per data/nasa.json) | |
| `pdfs/nara/` | `pdfs-v1` (49 NARA PDFs per data/nara.json) | |

Because `videos-v1` is a **flat** release (no slug-folder structure inside the release), we cannot blindly `gh release download videos-v1 -D videos/aaro/`. We need to drive the download from `data/<slug>.json`'s `v1.assets[].l` field — extract the basename from each `https://assets.realufo.org/videos/<slug>/<basename>` URL, then `gh release download videos-v1 --pattern '<basename>'` into the staging dir. Same approach for PDFs.

**Recommended fix shape** (concrete plan — operator's choice on whether to inline this in r2-sync.yml or split into a helper script):

```yaml
# NEW step inserted between "Configure rclone" and "Detect changed binaries":
- name: Stage binaries from GitHub Releases
  if: inputs.full_sync == true || github.event_name == 'repository_dispatch'
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    set -euo pipefail
    mkdir -p /tmp/r2-stage/pdfs /tmp/r2-stage/videos
    python3 scripts/stage-r2-from-releases.py \
      --out /tmp/r2-stage \
      --slugs wargov,aaro,nasa,nara \
      ${{ inputs.archive && format('--only {0}', inputs.archive) || '' }}
```

Then update the rclone sync to use `/tmp/r2-stage/pdfs/wargov/` etc. as its source instead of `bundles/Release_1/`. The wargov special-case block stays (just repointed), and the per-archive loop becomes:

```bash
for slug in aaro nasa nara; do
  if [ -d "/tmp/r2-stage/pdfs/${slug}" ]; then
    rclone sync "/tmp/r2-stage/pdfs/${slug}/" "r2-realufo:realufo/pdfs/${slug}/" \
      --include '*.pdf' --checksum --progress
  fi
  if [ -d "/tmp/r2-stage/videos/${slug}" ]; then
    rclone sync "/tmp/r2-stage/videos/${slug}/" "r2-realufo:realufo/videos/${slug}/" \
      --include '*.mp4' --include '*.webm' --include '*.mov' --checksum --progress
  fi
done
```

A new helper `scripts/stage-r2-from-releases.py` would read `data/<slug>.json` + `release-manifest.json` (plus `wargov`'s `uap-release001.csv` since wargov.json is empty), resolve each asset to its source release+filename, and `gh release download` them into `/tmp/r2-stage/{pdfs,videos}/<slug>/`.

**Minimum-viable fix** (if the operator wants to unblock Wave 2 quickly without the staging-script complexity): land **just the loop restriction** (`aaro nasa nara`) as commit `fix(05-01): restrict r2-sync loop to active slugs`, then either (a) operator manually `rclone sync` from their workstation for the bulk seed once (treating Plan 05-01 as scaffolding the Worker→GH-Actions trigger surface, not the bulk-seed mechanism itself), or (b) open a follow-up plan 05-01b to implement the GH-Releases-staging step.

**Cleanup needed regardless of fix path:** the current R2 bucket has `videos/geipan/` (dormant — should be removed) and may have other dormant-archive pollution. After fixing, run `rclone purge r2-realufo:realufo/videos/geipan/` and verify only `wargov/ aaro/` prefixes remain under `videos/`, only `wargov/ aaro/ nasa/ nara/` under `pdfs/`.

## Resolution

- root_cause: r2-sync.yml expects `<slug>/{bundles,videos}/` dirs to materialize on the GH Actions runner, but every binary is `.gitignored` (canonical store is GitHub Releases). Runner checkout sees empty source dirs and every rclone sync silently skips. The only sync that fires is `geipan/videos/` (2 mp4s committed pre-gitignore). Secondary bug: per-archive loop iterates 11 DORMANT slugs.
- fix: (1) Restrict per-archive loop in `.github/workflows/r2-sync.yml` lines 304-305 to `aaro nasa nara` only. (2) Add a "Stage binaries from GitHub Releases" step that downloads canonical binaries onto the runner before rclone, driven by a new `scripts/stage-r2-from-releases.py` that reads `data/<slug>.json` + `release-manifest.json` and `gh release download`s each asset into `/tmp/r2-stage/{pdfs,videos}/<slug>/`. Repoint rclone sync sources at the staging dir. (3) Purge `videos/geipan/` from R2 to remove DORMANT pollution.
- verification: After fix, `gh workflow run r2-sync.yml -f full_sync=true` should log 8 sync groups (wargov pdfs+videos, aaro pdfs+videos, nasa pdfs, nara pdfs — nasa/nara have no videos per data/*.json). Post-sync `rclone lsd r2-realufo:realufo/videos/` should return exactly `wargov` + `aaro` (no `geipan`). Post-sync `rclone lsd r2-realufo:realufo/pdfs/` should return exactly `wargov` + `aaro` + `nasa` + `nara`. Object counts should match `data/<slug>.json` v1.assets categorised by `cat='Video'`/`'Document'`.
- files_changed: `.github/workflows/r2-sync.yml` (replace lines 304-305 slug list; add Stage step around line 167; repoint rclone sources at /tmp/r2-stage/); NEW `scripts/stage-r2-from-releases.py`.

## Resolution (final)

- **root_cause:** r2-sync.yml expects `<slug>/{bundles,videos}/` dirs on GH Actions runner, but every binary is `.gitignored` (canonical = GH Releases). Runner sees empty dirs, every rclone sync silently skips. Only `geipan/videos/` (2 mp4s) was committed pre-gitignore + slipped through. Secondary: per-archive loop iterates 11 dormant slugs.
- **fix applied (Path A minimum-viable):**
  - commit `c10dbbf` — `fix(05-01): restrict r2-sync loop to active slugs (aaro nasa nara)` (also implicitly removes future dormant-pollution risk)
  - operator workstation bulk push: 207 files uploaded (116+6=122 wargov PDFs, 28+55=83 wargov mp4s via wrangler r2 object put + 2 large mp4s 513MB + 416MB via aws s3 cp R2 S3-compat multipart with operator-pasted access keys)
  - 2 dormant geipan/videos/*.mp4 purged via wrangler r2 object delete; origin confirmed 404
- **verification:** 5 spot-check curls returned correct HTTP/2 200 + content-type; 1 geipan curl returned cached 200 (origin 404, CDN max-age=14400 self-clears in 4h)
- **files_changed:** `.github/workflows/r2-sync.yml` (commit `c10dbbf`); no source code changes for R2 contents (binary state only).
- **deferred follow-up (backlog):** Plan 05-01b — CI-driven `scripts/stage-r2-from-releases.py` to remove operator-workstation dependency. nasa (4 PDFs) + nara (49 PDFs) seed deferred (source files not present on this workstation).
