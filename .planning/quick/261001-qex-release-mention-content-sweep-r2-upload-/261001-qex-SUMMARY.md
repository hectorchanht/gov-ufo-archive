---
phase: quick-261001-qex
plan: 01
subsystem: wargov content + R2 assets + agent skills
tags: [wargov, release-sweep, r2, skill]
requires: [261001-p8k]
provides: [Releases 01–06 copy everywhere, wargov-release-ingest skill, R2 wargov keys complete]
affects: [src/pages/index.astro, /glossary/, default og:image, README, tests/pagination.spec.ts]
key-files:
  created: [.agents/skills/wargov-release-ingest/SKILL.md]
  modified: [src/pages/index.astro, src/components/Card.astro, tests/pagination.spec.ts, README.md, humans.txt, CHANGELOG.md, scripts/sync.sh, scripts/build-og.py, scripts/download-war.gov.py, assets/og.svg, legacy/glossary.html, legacy/compare.html]
decisions:
  - "Release-mention sweep uses the short range `Releases 01–06` (en dash), not a + list, so the stamp fits 360 px"
  - "Project skill lives at .agents/skills/ (tracked); .claude/ stays gitignored"
  - "build-pdf-thumbs.py URL-quote fix skipped: plan made it conditional on missing space keys, and none were missing"
metrics:
  started: 2026-10-02T01:11:51Z
  completed: 2026-10-02T01:16Z
  tasks: "2 of 3 complete; Task 3 R2 part complete, push/deploy/live-verify HELD"
---

# Quick 261001-qex: release-mention sweep, R2 check, ingest skill — Summary

Every war.gov release range and total the site shows now reads Releases 01–06 / 450 records. The R2 diff shows all 689 wargov keys already in the bucket (0 missing). A tracked R07+ runbook skill was added. Push, deploy and live verify are **HELD — awaiting user decision on q6n**.

## Commits

| Task | Commit | Message |
| --- | --- | --- |
| 1 | 1169f41 | docs(261001-qex): correct war.gov release mentions to Releases 01–06 / 450 records |
| 2 | 31bbb4d | docs(261001-qex): add wargov-release-ingest project skill |
| 3 | none | R2 already complete; the conditional thumb-script fix was not needed |

`git show --stat` on both commits lists only the planned paths. SECURITY.md, .planning/HANDOFF.json, .planning/.pending-auth-captures.jsonl and the 261001-q6n SUMMARY were not staged. HANDOFF.json and .pending-auth-captures.jsonl are still dirty/untracked. SECURITY.md was not dirty at start.

## Task 1: sweep (old → new)

Step 0 truth check from uap-data.csv: 450 rows, 158/64/72/40/41/75. Matches the plan.

| File:line | Old | New |
| --- | --- | --- |
| src/pages/index.astro:183 | `lastUpdated="2026-05-27"` | `lastUpdated="2026-10-01"` |
| src/pages/index.astro:222 | `RELEASES 01 + 02 + 03 + 04 / 2026` | `RELEASES 01–06 / 2026` |
| src/pages/index.astro:442 | `(50 cards/shard, 222 total)` | `(50 cards/shard)` |
| src/pages/index.astro:921-922 | `materialises all // 222 cards, after which` | `materialises every // card, after which` |
| src/components/Card.astro:102 | `silently exclude 222 wargov cards` | `silently exclude every wargov card` |
| tests/pagination.spec.ts:7 | `Page 1..12` | `Page 1..23` |
| tests/pagination.spec.ts:24,34,62,252 | `222` in comments | `TOTAL_CARDS` |
| tests/pagination.spec.ts:30 | `TOTAL_CARDS = 222; // 50 SSR + 50 + 50 + 50 + 22 across 4 shards` | `TOTAL_CARDS = 450; // 50 SSR + 8 shards (wargov-shard-2..9) at Release 06 (D-32)` |
| tests/pagination.spec.ts:31-32 | `12 (Math.ceil(222 / 20))`, `pages 2..12` | `23 (Math.ceil(450 / 20))`, `pages 2..23` |
| README.md:19 | `Release 01–03` | `Releases 01–06` |
| README.md:80 | `slideshow/ slideshow-2/ 3/ … Release 01 / 02 / 03` | `slideshow/ slideshow-2/ 3/ 4/ 6/ … Releases 01–04 + 06 (R05 shipped none; git-tracked)` |
| README.md:277-281 | Release 03 "await an S3-multipart upload … 404" bullet | Releases 03–06 bullet (228 rows, all on R2, multipart note, skill link). Before the edit, both R03 big videos were checked and return 200: DOD_111764796 = 3212901468 B, DOD_111764902 = 1281077153 B |
| humans.txt:19 | `PURSUE — Release 01` | `PURSUE — Releases 01–06`, with padding trimmed so `—` stays at column 56 |
| scripts/sync.sh:76 | `war.gov / UFO Release 01` | `war.gov / UFO Releases 01–06` |
| scripts/build-og.py:33 | `Releases 01 + 02` | `Releases 01–06` (padding kept aligned) |
| assets/og.svg:39 | `Releases 01 + 02` | `Releases 01–06` (direct edit; build-og.py was not run) |
| scripts/download-war.gov.py:215-216 | "As of Release 02 … both Release 01 and 02 rows" | "war.gov serves a single combined CSV (uap-data.csv) holding every release's rows (01–06 as of 9/18/26)." |
| legacy/glossary.html:328 | `Releases 01 (158 …) and 02 (64 …) are mirrored at … root.` | `Releases 01–06 (450 records, May 8 – September 18 2026) are archived at the realufo.org root.` (also removes the banned word "mirrored") |
| legacy/compare.html:339,342 | `Releases 01 + 02 …`, `(222 records: 158 + 64)` | `Releases 01–06 …`, `(450 records: 158 + 64 + 72 + 40 + 41 + 75)` |
| CHANGELOG.md:12 | none | New `### Added — War.gov / PURSUE Releases 03–06` entry above the R02 entry |

Confirmed already correct, so not changed: index.astro description, jsonLd, HeroCarousel label `Releases 01 + 02 + 03 + 04 + 06`, head-cards, `450 unresolved records`, filter options 01..06, the comment at ≈47. tests/fidelity-samples.json has no glossary/PURSUE sample to update; its PURSUE entry is the h1, which did not change. The spec has no hard-coded `12` page assertion.

`pnpm build` exited 0. `git status --porcelain data public/data` was empty. Postbuild reported `dist/watchdog.json (943 assets, 6 release dates)`. The Task 1 verify printed `truth ok` and `T1 OK`.

### Reviewed, not changed (excluded)
- `.planning/**`: history.
- Dormant archives: `legacy/{geipan,uk,brazil,chile,argentina,canada,italy,nz,peru,spain,uruguay}/**`, `scripts/build-{brazil,chile,geipan,uk}.py`, `scripts/build_batch3.py`, and `scripts/templates/lightbox.py` RELEASE_BY_DATE (used only by dormant builders via `_site_template.py`).
- `legacy/index.html`: retired pre-Astro landing, not shipped.
- `api/` + `feeds/`: outputs of the retired pipeline. See the follow-up below.
- `uap-data.csv` / `uap-release001.csv`: source of truth.
- CHANGELOG R02 entry: history.
- CLAUDE.md:41: see the proposal below.

## Task 2: skill

`.agents/skills/wargov-release-ingest/SKILL.md` is 153 lines and tracked. It has `name` and `description` frontmatter. All 15 concrete `scripts/`, `src/`, `tests/` and `workers/` paths it cites exist. The Task 2 verify printed `T2 OK`. The sweep gate grep in the skill was tested under bash. With `PREV=06 TOTAL_OLD=450` it hits every swept target line (11 lines), so it will catch them at R07. It needs bash because zsh does not word-split `set -- $args`. To have Claude Code load the skill automatically, the user can symlink it: `ln -s ../../.agents/skills/wargov-release-ingest .claude/skills/wargov-release-ingest`. `.claude/` is gitignored, so this stays a local choice.

## Task 3: R2 (done) and ship (HELD)

- **Concurrency:** At the start, the other session's `build-pdf-thumbs.py --slug wargov` (PID 70461, with the 4 space-key R06 PDFs pre-cached into `/tmp/pdf-thumb-cache/wargov/`) was running. By the time Task 2 was committed it had exited on its own. It was not killed and no wait was needed.
- **R2 diff:** dist/watchdog.json lists 689 wargov keys (270 pdfs, 149 videos, 270 pdf-thumbs). The bucket holds 901 keys under those prefixes. **Missing before = 0, missing after = 0**, so nothing was uploaded by this session. All 14 keys containing a space, including the 4 R06 AAWSAP thumbs, are present.
- **Step 3 (thumb-script URL-quote fix): skipped**, because no space keys were missing. The latent bug is still there: `scripts/build-pdf-thumbs.py:170` builds `f'{ASSETS_BASE}/pdfs/{slug}/{basename}'` without `urllib.parse.quote`. The other session worked around it by pre-caching the PDFs. Follow-up: fix it with a one-line quote before R07 if any new PDF name has a space.
- **Size checks (head-object vs local bundles/):**
  - DOD_111985823.mp4: R2 802522487, local 802522487.
  - DOD_111887376.mp4: R2 33427558, local 33427558.
- **Public CDN, read-only check, all 200:**
  - `videos/wargov/DOD_111985823.mp4` (content-length 802522487).
  - R05 PDF `CIA-UAP-D022_…Puerto-Rico_1965.pdf`.
  - R06 thumb `LLE-UAP-D001_…October-2023.jpg`.
  - Space-key thumb `DOW-UAP-D114_…May-18-%202010.jpg`.
- **Push / fast-forward main / deploy watch / live verify on realufo.pages.dev: HELD — awaiting user decision on q6n.** The branch also carries the 261001-q6n commits, which move the canonical origin to https://release.realufo.org. Pre-push state:
  - `git fetch origin` done.
  - `git merge-base --is-ancestor origin/main HEAD` passes (origin/main = b079cfc). The push would be a fast-forward.
  - Branch HEAD = 31bbb4d.
  - No push of any ref was made.
- **https://release.realufo.org/ status: 525** (SSL handshake). It needs the q6n DNS CNAME `release → realufo.pages.dev`.

## Proposed CLAUDE.md edit (user to apply)

CLAUDE.md:41 should change from `War.gov / PURSUE — Release 01` to `War.gov / PURSUE — Releases 01–06`.

## Follow-ups
- `api/stats.json` has been all-zero since `generatedAt 2026-06-02T08:00:22Z` (`totalRecords: 0`). The retired build-api/build-feeds pipeline is broken, and `feeds/` is in the same state. Either retire it or repair it.
- Fix the `build-pdf-thumbs.py:170` URL-quote bug (above).

## STATE.md TODO lines now resolved (for the orchestrator to clear)
- Line 106 (**wargov R05/R06** upload of 162 PDFs + 32 videos, DOD_111985823 multipart): the R2 part is done, with 0 wargov keys missing. "Then push … merge, deploy" is still open and HELD on q6n.
- Line 107 (**wargov R03** 2 large videos): resolved. DOD_111764796 and DOD_111764902 both serve 200 from assets.realufo.org.
- Quick-table rows 100 (260615-3e3, "2 large videos pending") and 101 (261001-p8k, "R2 upload … pending") can have their status updated the same way.

## Deviations from Plan
None in executed scope. Following the orchestrator scope override, Task 3 steps 5–7 (push, deploy, live verify) were not run, so the T3 automated verify was not run either. That verify needs `origin/main == HEAD` and the deployed copy.

## Self-Check: PASSED
- FOUND: .agents/skills/wargov-release-ingest/SKILL.md
- FOUND commits: 1169f41, 31bbb4d
