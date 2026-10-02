---
phase: quick-261001-p8k
plan: 01
subsystem: wargov archive
tags: [wargov, pursue, release-05, release-06, csv, dvids, bundles]
requires: [260615-3e3 R03/R04 ingest pattern]
provides: [450-row wargov archive, dvids2dod-r05/r06 maps, slideshow-6, local R05/R06 bundles]
affects: [uap-data.csv, data/wargov*.json, public/data/wargov*.json, src/pages/index.astro, src/components/Card.astro]
tech-stack:
  added: []
  patterns: [append-only CSV re-serialisation, per-release dvids2dod map, D-10 release-batch parity]
key-files:
  created:
    - scripts/resolve-dvids-r05.py
    - scripts/resolve-dvids-r06.py
    - scripts/dvids2dod-r05.json
    - scripts/dvids2dod-r06.json
    - slideshow-6/ (9 images)
    - data/wargov-shard-8.json, data/wargov-shard-9.json (+ public/data mirrors)
  modified:
    - uap-data.csv
    - scripts/download-war.gov.py
    - scripts/normalize-csv.py
    - src/components/Card.astro
    - src/pages/index.astro
    - scripts/copy-legacy-archives.sh
    - .gitignore
decisions:
  - "R05/R06 VID/AUD hydration uses resolved DVIDS->DOD maps; all 32 IDs resolved on first run, none guessed"
  - "Landing-page '108 DVIDS videos' replaced by the normaliser's hydration total (150)"
metrics:
  completed: 2026-10-01
  tasks: 3
  commits: 5
---

# Quick 261001-p8k: Ingest war.gov PURSUE Release 05 + 06 Summary

Release 05 (8/7/26, 41 rows) and Release 06 (9/18/26, 75 rows) were appended verbatim to `uap-data.csv`. All 32 DVIDS IDs resolved to DOD mp4s, the archive was re-normalised to 450 records (150 hydrated video URLs), and the landing page now covers Releases 05 and 06. All 4 bundles were downloaded and extracted locally. Nothing has been pushed, uploaded or deployed.

## Fingerprint

`[('5/22/26',64),('5/8/26',158),('6/12/26',72),('7/10/26',40),('8/7/26',41),('9/18/26',75)]` — total 450.
`git diff --numstat` on the CSV append: `543 0` (543 physical lines = 116 records with embedded newlines; 0 deletions). The first 334 parsed rows are identical to the previous HEAD.

## Commits

| Hash | Message |
| --- | --- |
| 74e4810 | feat(261001-p8k): append war.gov Release 05 + 06 rows to uap-data.csv (+41, +75) |
| efb6ba1 | feat(261001-p8k): wire Release-05/06 downloader entries (slideshow-6 + 4 bundles) |
| 587c15d | feat(261001-p8k): resolve R05/R06 DVIDS→DOD + normalise Release 05/06 rows (334→450) |
| c14250c | feat(261001-p8k): landing-page Release-05/06 copy + filter + total (334→450); postbuild slideshow-6 |
| 6c983ba | chore(261001-p8k): gitignore Release 05/06 bundle zips + extracted dirs |

## Verification (observed)

- T1 verify printed `CSV OK 450` and `T1 OK`. slideshow-6 fetched 9/9 (all JPEG).
- `normalize-csv.py --check`: `[ok] wargov: --check clean (no drift)`. VID hydration: 150 mp4 URLs, up from 118 (+32). 50 primary + shards 2..9 = 450.
- `pnpm build`: exit 0. `dist/slideshow-6/` has 9 files. `dist/index.html` has filter options 05/06, "450-record archive", and "450 unresolved records". `dist/data/wargov-shard-*.json` hold 41 `data-release="05"` and 75 `data-release="06"` cards.
- Pagefind: 3 fragments in `dist/pagefind/fragment/` contain "Tremonton".
- T3 verify printed `T3 OK`. Apart from `.planning/`, the working tree is clean.

## DVIDS resolution

r05: 16/16 resolved (DOD_111887376..111887460). r06: 16/16 resolved (DOD_111985772..111985855, including AUD 1023407 → 111985823). **Unresolved IDs: none.** Each mapped DOD id has a matching `DOD_<id>.mp4` in its release's video zip. Neither zip has missing or extra files.

## Video size table (all R05/R06 videos)

| File | Release | Bytes | MiB | Flag |
| --- | --- | ---: | ---: | --- |
| DOD_111887376.mp4 | R05 | 33,427,558 | 31.9 | - |
| DOD_111887380.mp4 | R05 | 89,410,590 | 85.3 | - |
| DOD_111887384.mp4 | R05 | 84,195,488 | 80.3 | - |
| DOD_111887390.mp4 | R05 | 52,517,114 | 50.1 | - |
| DOD_111887401.mp4 | R05 | 20,916,447 | 19.9 | - |
| DOD_111887407.mp4 | R05 | 24,280,625 | 23.2 | - |
| DOD_111887413.mp4 | R05 | 12,249,790 | 11.7 | - |
| DOD_111887419.mp4 | R05 | 11,176,881 | 10.7 | - |
| DOD_111887421.mp4 | R05 | 2,132,163 | 2.0 | - |
| DOD_111887426.mp4 | R05 | 55,170,181 | 52.6 | - |
| DOD_111887427.mp4 | R05 | 10,304,701 | 9.8 | - |
| DOD_111887430.mp4 | R05 | 1,230,965 | 1.2 | - |
| DOD_111887439.mp4 | R05 | 23,882,996 | 22.8 | - |
| DOD_111887446.mp4 | R05 | 16,649,610 | 15.9 | - |
| DOD_111887456.mp4 | R05 | 44,368,966 | 42.3 | - |
| DOD_111887460.mp4 | R05 | 64,214,893 | 61.2 | - |
| DOD_111985772.mp4 | R06 | 80,052,070 | 76.3 | - |
| DOD_111985782.mp4 | R06 | 22,766,393 | 21.7 | - |
| DOD_111985790.mp4 | R06 | 64,049,840 | 61.1 | - |
| DOD_111985798.mp4 | R06 | 138,505,272 | 132.1 | - |
| DOD_111985807.mp4 | R06 | 79,818,409 | 76.1 | - |
| DOD_111985818.mp4 | R06 | 24,071,535 | 23.0 | - |
| DOD_111985820.mp4 | R06 | 31,383,900 | 29.9 | - |
| DOD_111985821.mp4 | R06 | 71,519,688 | 68.2 | - |
| DOD_111985822.mp4 | R06 | 3,228,077 | 3.1 | - |
| **DOD_111985823.mp4** | R06 (AUD, Ruppelt 1952 presentation) | 802,522,487 | 765.3 | **>300 MiB (wrangler single-PUT cap — needs S3 multipart)** |
| DOD_111985832.mp4 | R06 | 60,826,819 | 58.0 | - |
| DOD_111985834.mp4 | R06 | 7,383,993 | 7.0 | - |
| DOD_111985835.mp4 | R06 | 20,973,165 | 20.0 | - |
| DOD_111985844.mp4 | R06 | 81,428,767 | 77.7 | - |
| DOD_111985850.mp4 | R06 | 12,614,687 | 12.0 | - |
| DOD_111985855.mp4 | R06 | 6,608,849 | 6.3 | - |

One file is over 300 MiB. No file is over 2 GiB, so every file fits the GitHub release asset limit.

## Extracted bundles (local, gitignored)

| Path | Contents | Size |
| --- | --- | --- |
| `bundles/release_05_Aug_07_documents/` | 44 PDF + 6 JPG | 124 MB |
| `bundles/uap_videos_080726/` | 16 mp4 | 521 MB |
| `bundles/documents_release_06_sept_18_2026/documents_release_06_sept_18_2026/` | 118 PDF (nested dir; a `__MACOSX/` sibling and a `.DS_Store` are zip junk, so skip them on upload) | 2.1 GB |
| `bundles/pursue_vids_091826/` | 16 mp4 | 1.4 GB |

All 84 `PDF | Image Link` basenames in the R05/R06 CSV rows exist in the extracted doc bundles (0 missing). All 4 zips were deleted after extraction. Free disk at the end: 40 GiB (`df -g`).

## Remaining for the operator (NOT done — hard stop)

1. R2 upload `pdfs/wargov/<basename>`: R05 docs (44 PDF + 6 JPG as applicable) and R06 docs (118 PDF).
2. R2 upload `videos/wargov/DOD_<id>.mp4`: 31 files go via wrangler. **DOD_111985823.mp4 (765 MiB) needs an S3 multipart upload** (same recipe as memory `release-03-pending-blocker.md`).
3. GitHub releases `wargov-r05-v1` / `wargov-r06-v1` if you want them. No asset exceeds 2 GiB.
4. Upload PDF thumbnails `pdf-thumbs/wargov/<basename>.jpg` for the new PDFs if that pipeline is in use. The normaliser derives these paths, so they will 404 until uploaded.
5. Push the branch `quick/261001-p8k-wargov-release-05-06`, merge, and deploy to Cloudflare Pages.

## Deviations from Plan

**1. [Rule 3 - Blocking] .gitignore entries for R05/R06 bundles**
- **Found during:** Task 3
- **Issue:** `bundles/` is not ignored wholesale. Existing entries only cover R01/R02 by name, so the extracted R05 docs showed up as untracked and broke the "clean tree" verify.
- **Fix:** Added `bundles/release_05_Aug_07_documents*`, `bundles/uap_videos_080726*`, `bundles/documents_release_06_sept_18_2026*`, `bundles/pursue_vids_091826*`.
- **Commit:** 6c983ba (adds a 5th code commit)

**2. [Rule 1 - Content fidelity] R06 hero-slide caption wording**
- The plan suggested "Archival film of reported UFOs". The CSV Title for DOW-UAP-PR159 says "Historical Film of Reported UFOs, Utah, 1952", so the caption uses "Historical film". The image filename (with `Archival`) is kept verbatim.

**3. [Rule 1 - Verify fix] T2 verify step `grep -c 'data-release="05"' dist/index.html`**
- `dist/index.html` server-renders only the first 50 CSV rows (R01/R03), so R05/R06 cards (like R04 before them) live in `dist/data/wargov-shard-8/9.json`. I confirmed 41 "05" and 75 "06" cards there instead. All other T2 checks passed.

## Assumption Drift (advisory)

- **Found during:** Task 2. **Planned:** VID hydration 108 → 140. **Actual:** 118 → 150. The pre-change baseline was 118 (all VID+AUD rows); the landing-page "108" was already stale. The +32 delta matches the plan.
- **Found during:** Task 3. **Planned:** the extracted R06 docs land directly in `bundles/documents_release_06_sept_18_2026/`. **Actual:** they are nested one level deeper, next to `__MACOSX/`. This matters for upload globbing.

## Known Stubs

None.

## Self-Check: PASSED

- Files: scripts/dvids2dod-r05.json, scripts/dvids2dod-r06.json, scripts/resolve-dvids-r05.py, scripts/resolve-dvids-r06.py, slideshow-6/ (9), data/wargov-shard-8.json, data/wargov-shard-9.json are all present.
- Commits 74e4810, efb6ba1, 587c15d, c14250c, 6c983ba are all present in `git log`.
