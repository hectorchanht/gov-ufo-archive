---
phase: quick-261001-qex
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/pages/index.astro
  - src/components/Card.astro
  - tests/pagination.spec.ts
  - README.md
  - humans.txt
  - CHANGELOG.md
  - scripts/sync.sh
  - scripts/build-og.py
  - scripts/download-war.gov.py
  - assets/og.svg
  - legacy/glossary.html
  - legacy/compare.html
  - .agents/skills/wargov-release-ingest/SKILL.md
  - scripts/build-pdf-thumbs.py   # conditional, Task 3 step 3 only
autonomous: true
requirements: [QUICK-261001-qex-SWEEP, QUICK-261001-qex-SHIP, QUICK-261001-qex-SKILL]

must_haves:
  truths:
    - "Every user-visible place that names the war.gov release range or archive total now says Releases 01–06 / 450 records (landing stamp, footer Last-updated, /glossary/, default OG image, README, humans.txt, sync.sh picker)"
    - "pnpm build exits 0 and data/ + public/data/ are byte-unchanged by it"
    - "Every assets.realufo.org key under pdfs/wargov/, videos/wargov/, pdf-thumbs/wargov/ listed in dist/watchdog.json exists in R2 bucket realufo"
    - "origin/main == the pushed branch HEAD (fast-forward, no force) and the Deploy to Cloudflare Pages workflow run for it succeeded"
    - "https://realufo.pages.dev/ serves RELEASES 01–06 and 450 unresolved records; R06 big video DOD_111985823.mp4 HEADs 200 with 802522487 bytes"
    - "A tracked, discoverable skill at .agents/skills/wargov-release-ingest/SKILL.md tells a future agent how to ingest R07+ end to end"
  artifacts:
    - path: ".agents/skills/wargov-release-ingest/SKILL.md"
      provides: "R07+ release-ingest runbook"
      contains: "name: wargov-release-ingest"
    - path: "src/pages/index.astro"
      provides: "landing copy"
      contains: "RELEASES 01–06 / 2026"
    - path: "legacy/glossary.html"
      provides: "/glossary/ PURSUE entry"
      contains: "Releases 01–06 (450 records"
  key_links:
    - from: "legacy/glossary.html"
      to: "dist/glossary/index.html"
      via: "src/pages/glossary.astro extracts legacy text at build"
      pattern: "Releases 01–06"
    - from: "assets/og.svg"
      to: "dist/assets/og.svg"
      via: "copy-legacy-archives.sh root assets loop; BaseHead default og:image"
      pattern: "Releases 01–06"
    - from: "git push origin HEAD:main"
      to: ".github/workflows/deploy-cf-pages.yml"
      via: "push-to-main trigger (paths src/**, scripts/**)"
      pattern: "pages deploy dist/"
---

<objective>
Correct every stale war.gov release mention to current truth (Releases 01–06, 450 rows), finish the R2 upload for R05/R06, ship to Cloudflare Pages via a fast-forward of main, and package the release-ingest workflow as a reusable project skill.

Purpose: the R05/R06 ingest (261001-p8k) left the landing stamp, glossary, OG image, README, test constants and helper text claiming Releases 01–02/01–03/01–04 and 222 records. The next release should not need this archaeology again.
Output: one sweep commit, one skill commit, (conditional) one thumb-script fix commit, pushed + deployed + live-verified.
</objective>

<execution_context>
@/Users/laichan/.claude/plugins/cache/gsd-plugin/gsd/4.5.3/workflows/execute-plan.md
@/Users/laichan/.claude/plugins/cache/gsd-plugin/gsd/4.5.3/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/STATE.md
@.planning/quick/261001-p8k-ingest-war-gov-pursue-release-05-and-06/261001-p8k-SUMMARY.md
@.planning/quick/260615-3e3-fetch-third-war-gov-ufo-release-and-upda/260615-3e3-SUMMARY.md
@/Users/laichan/.claude/projects/-Users-laichan-code-tung-war-gov-ufo-release/memory/release-03-pending-blocker.md

## Ground truth (verified by planner 2026-10-01 from uap-data.csv, csv.DictReader utf-8-sig)

| Release | Release Date | Rows | Cumulative |
| --- | --- | ---: | ---: |
| 01 | 5/8/26 | 158 | 158 |
| 02 | 5/22/26 | 64 | 222 |
| 03 | 6/12/26 | 72 | 294 |
| 04 | 7/10/26 | 40 | 334 |
| 05 | 8/7/26 | 41 | 375 |
| 06 | 9/18/26 | 75 | 450 |

R03–R06 combined = 228 rows. Slideshow highlights 17+10+10+10+9 = 56 (R05 shipped no rotator, so there is no slideshow-5/). DVIDS hydrated videos = 150. The executor re-derives the row counts in Task 1 step 0 before editing anything.

## State discovered while planning (affects Task 3)

- **origin/main is already at b079cfc** (the R05/R06 ingest). A concurrent session pushed it and the deploy workflow succeeded at 2026-10-02T00:47Z. The current branch `quick/261001-p8k-wargov-release-05-06` is a fast-forward of origin/main and is 5 commits ahead: bc49f5b watchdog Worker, the 261001-q6n commits (8ac09b4, c636d8f, ea444a0) and af428f0 merge. Pushing to main ships these too. That is intended: they are on the branch the user asked to ship.
- **R2: every pdfs/wargov/ and videos/wargov/ key in dist/watchdog.json is already in the bucket.** That includes DOD_111985823.mp4 (802522487 bytes, uploaded 00:53Z). Only 36 `pdf-thumbs/wargov/*.jpg` were missing, and two `scripts/build-pdf-thumbs.py --slug wargov` processes from another session were running at planning time (PIDs 58257, 64276). 4 of the missing thumb keys contain a literal space; see Task 3 step 3.
- **https://release.realufo.org/ returns 525** (SSL handshake). STATE.md says the 261001-q6n custom domain needs a DNS CNAME release→realufo.pages.dev. This is out of scope: verify live on **https://realufo.pages.dev/** and report the 525.
- realufo.pages.dev already shows "450 unresolved records" but still shows "RELEASES 01 + 02 + 03 + 04 / 2026". That is the stamp this plan fixes.
- The watchdog's known-release list is **automatic**. `scripts/build-watchdog-index.py` (run by postbuild `scripts/copy-legacy-archives.sh:291`) writes `dist/watchdog.json` `wargovReleaseDates` from uap-data.csv. Nothing to edit in `workers/watchdog/`.

<interfaces>
Deploy: `.github/workflows/deploy-cf-pages.yml`. Trigger: push to main touching src/**, public/**, scripts/**, data/**, uap-data.csv, etc. Build: `pnpm build`, then `wrangler pages deploy dist/ --project-name=realufo --branch=main` in CI (secrets already set). Nothing is deployed locally with wrangler: the local wrangler login is on the wrong CF account (memory).
Merge convention: quick branches land on main by **fast-forward** (main history is linear for 260615-3e3 / 261001-p8k). Use `git push origin HEAD:main`. Never pass --force.
R2: bucket `realufo`, endpoint https://f1868a071996e836eae6da2b65f37929.r2.cloudflarestorage.com, aws CLI `--profile r2`, env AWS_REQUEST_CHECKSUM_CALCULATION=when_required AWS_RESPONSE_CHECKSUM_VALIDATION=when_required. Key layout: pdfs/wargov/<basename>, videos/wargov/DOD_<id>.mp4, pdf-thumbs/wargov/<basename-no-ext>.jpg (exact case as in data URLs). Public CDN: https://assets.realufo.org/<key>.
Canonical key inventory: `dist/watchdog.json` → `assets` (unquoted R2 keys scraped from data/*.json). Filter it with `'/wargov/' in key`.
Thumb script: `scripts/build-pdf-thumbs.py --slug wargov` reads creds from env (no --profile flag). Use the pattern the other session used: eval "$(aws configure export-credentials --profile r2 --format env)" plus the two checksum env vars and AWS_DEFAULT_REGION=auto. It is idempotent (head-object skip). For PDFs not in LOCAL_SOURCES it downloads from `https://assets.realufo.org/pdfs/wargov/<basename>` via curl in `_download_from_r2()` (≈line 166). The basename is NOT URL-quoted there.
Local R05/R06 binaries (gitignored, main tree only): bundles/release_05_Aug_07_documents/, bundles/uap_videos_080726/, bundles/documents_release_06_sept_18_2026/documents_release_06_sept_18_2026/ (skip the __MACOSX sibling and .DS_Store), bundles/pursue_vids_091826/.
</interfaces>
</context>

<execution_constraints>
- Run in the MAIN working tree (no worktree). bundles/ binaries are gitignored and exist only here.
- Unrelated dirty files belong to another session. NEVER stage, commit, revert or stash these: `SECURITY.md`, `.planning/HANDOFF.json`, `.planning/.pending-auth-captures.jsonl`, `.planning/quick/261001-q6n-*/261001-q6n-SUMMARY.md`. Always `git add <explicit paths>`; never `git add -A` / `.` / `-u`.
- Commits are atomic per task, conventional: `docs(261001-qex): …` / `feat(261001-qex): …` / `fix(261001-qex): …`. End each message with the line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Order: Task 1 (sweep + build + commit), then Task 2 (skill + commit), then Task 3 (R2 finish, then a single push of branch + fast-forward main, then deploy watch, then live verify). One push covers everything.
- Do NOT edit CLAUDE.md. Agent instructions forbid an agent changing CLAUDE.md on another agent's say-so. It has one stale cell (line 41, `War.gov / PURSUE — Release 01`). Put the proposed replacement (`War.gov / PURSUE — Releases 01–06`) in the SUMMARY for the user to apply.
- Do NOT touch `.gitignore` or anything under `.claude/`.
- If R2 creds fail, `gh` auth fails, the deploy run fails, or origin/main is not an ancestor of HEAD at push time: STOP that step and report. Never work around auth, never force-push.
- A concurrent session is active in this repo. Do not kill its processes. Wait for them (bounded poll, see Task 3).
- No prose in user-facing copy may say "mirror" (CLAUDE.md §11). Official war.gov text stays verbatim (§9). Only our own derived ranges, counts and dates change.
</execution_constraints>

<tasks>

<task type="auto">
  <name>Task 1: Release-mention sweep — correct every stale range/total, build</name>
  <files>src/pages/index.astro, src/components/Card.astro, tests/pagination.spec.ts, README.md, humans.txt, CHANGELOG.md, scripts/sync.sh, scripts/build-og.py, scripts/download-war.gov.py, assets/og.svg, legacy/glossary.html, legacy/compare.html</files>
  <action>
Step 0 (truth check): re-derive the per-Release-Date row counts from uap-data.csv with python csv.DictReader (encoding utf-8-sig) and confirm they match the Ground truth table in context (450 total; 158/64/72/40/41/75). If they differ, STOP and report. Do not edit with stale numbers.

Then make exactly these edits. Use Edit for exact replacements and keep the surrounding markup unchanged:

1. src/pages/index.astro
   - line ≈183: lastUpdated="2026-05-27" becomes lastUpdated="2026-10-01". The footer shows "Last updated …". The previous value was the R02 ingest date, so the convention is the archive's last ingest date, and R05/R06 was ingested 2026-10-01. Change ONLY the wargov page. aaro/nasa/nara/nz/uruguay also carry 2026-05-27, but that is their own date and not release-derived.
   - line ≈222 classified stamp: `RELEASES 01 + 02 + 03 + 04 / 2026` becomes `RELEASES 01–06 / 2026` (en dash). Use the short range, not a six-item "+" list, so the stamp stays inside 360 px (CLAUDE.md §8).
   - line ≈442 comment: `(50 cards/shard, 222 total)` becomes `(50 cards/shard)`. Line ≈922 comment: `222 cards, after which` becomes `card, after which` (reword so it reads "materialises every card"). Make these release-agnostic so they never drift again.
   - Leave the following unchanged; they are already correct, so just confirm them: description (≈151), jsonLd name/description/keywords (≈165-170), HeroCarousel label "Releases 01 + 02 + 03 + 04 + 06" (≈233; correct because R05 has no imagery), head-cards Release 01..06, "450 unresolved records", filter options 01..06, and the historical example in the ≈47-48 comment.
2. src/components/Card.astro line ≈102 comment: "silently exclude 222 wargov cards" becomes "silently exclude every wargov card".
3. tests/pagination.spec.ts: set `TOTAL_CARDS = 450` with comment `// 50 SSR + 8 shards (wargov-shard-2..9) at Release 06 (D-32)`. Update the derived comments: total pages = 23 (Math.ceil(450 / 20)), "pages 2..23", "Page 1..23" in the header comment (≈line 7). Change the ≈24/34/62/252 comments that say "222" to say "all TOTAL_CARDS". First grep the spec for any hard-coded `12` page assertion; if one exists, change it to 23.
4. README.md
   - line 19: `**PURSUE — Department of War / Release 01–03**` becomes `**PURSUE — Department of War / Releases 01–06**`.
   - line 80: replace the tree line with `├── slideshow/ slideshow-2/ 3/ 4/ 6/  # hero-carousel imagery for Releases 01–04 + 06 (R05 shipped none; git-tracked)`.
   - lines ≈277-281, the stale "Release 03 … await an S3-multipart upload path … 404" bullet. First run curl -sI on https://assets.realufo.org/videos/wargov/DOD_111764796.mp4 and on DOD_111764902.mp4. If both return 200, replace the bullet with: "**Releases 03–06** (war.gov, 12 Jun – 18 Sep 2026) added 228 rows (72 + 40 + 41 + 75). All linked PDFs and videos are on R2. Files over wrangler's 300 MiB single-PUT cap (e.g. `DOD_111764796.mp4` ≈ 2.99 GiB, `DOD_111985823.mp4` ≈ 765 MiB) go up by S3 multipart with the aws CLI. Ingest recipe: `.agents/skills/wargov-release-ingest/SKILL.md`." If either is not 200, keep a one-line note naming the 404 key instead of claiming everything is on R2.
   - line 84 ("original Release 01 manifest (158 records)") is correct. Leave it.
5. humans.txt line 19: `Department of War / PURSUE — Release 01` becomes `Department of War / PURSUE — Releases 01–06`. Trim padding spaces so the trailing `— war.gov/UFO/` stays in the same column as its neighbours.
6. scripts/sync.sh line 76: `war.gov / UFO Release 01` becomes `war.gov / UFO Releases 01–06`.
7. scripts/build-og.py line 33 wargov tagline: `'Department of War · Releases 01 + 02'` becomes `'Department of War · Releases 01–06'`. In assets/og.svg line 39, replace the text node `Releases 01 + 02` with `Releases 01–06` by a direct string edit. Do NOT run build-og.py: it regenerates all 15 og.svg files and rewrites meta tags in legacy HTML, which is out of scope. assets/og.svg is the default og:image for every page (src/layouts/BaseHead.astro:32).
8. scripts/download-war.gov.py lines ≈215-216 comment ("As of Release 02 … includes both Release 01 and 02 rows") becomes "war.gov serves a single combined CSV (uap-data.csv) holding every release's rows (01–06 as of 9/18/26)."
9. legacy/glossary.html line 328 (shipped as /glossary/ via src/pages/glossary.astro): the dd text becomes `U.S. Department of War's UAP release programme. Releases 01–06 (450 records, May 8 – September 18 2026) are archived at the <a href="/">realufo.org</a> root.` This also removes the banned word "mirrored" (§11). First grep tests/fidelity-samples.json for a glossary/PURSUE sample asserting the old text; if one exists, update its expected_text to match.
10. legacy/compare.html line 339: `Releases 01 + 02 disclosure track` becomes `Releases 01–06 disclosure track`. Line 342: `Releases 01 + 02 (222 records: 158 + 64)` becomes `Releases 01–06 (450 records: 158 + 64 + 72 + 40 + 41 + 75)`. The page is not shipped, but it is tracked and states the release, so it gets fixed too.
11. CHANGELOG.md: under `## [Unreleased]`, directly above the existing "Release 02" entry (leave that history untouched), add `### Added — War.gov / PURSUE Releases 03–06 (June 12 – September 18, 2026)` with terse factual bullets: R03 6/12/26 +72, R04 7/10/26 +40, R05 8/7/26 +41 (no rotator imagery), R06 9/18/26 +75; `uap-data.csv` now 450 rows; DVIDS maps `scripts/dvids2dod-r03.json`..`r06.json`; release filter covers Releases 01–06; hero imagery `slideshow-3/`, `slideshow-4/`, `slideshow-6/`. State facts only, no marketing copy.

Explicitly EXCLUDED (list them in the SUMMARY as reviewed, not changed): .planning/** (history); dormant archives (legacy/{geipan,uk,brazil,chile,argentina,canada,italy,nz,peru,spain,uruguay}/**, scripts/build-{brazil,chile,geipan,uk}.py, scripts/build_batch3.py, scripts/templates/lightbox.py RELEASE_BY_DATE, which is consumed only by dormant builders via scripts/_site_template.py); legacy/index.html (retired pre-Astro landing, not shipped, superseded by src/pages/index.astro); api/ + feeds/ (outputs of the retired build-api/build-feeds pipeline; api/stats.json has been all-zero since 2026-06-02, which is a pre-existing broken pipeline, so flag it as a follow-up); uap-data.csv / uap-release001.csv (source of truth); the CHANGELOG R02 entry (history); CLAUDE.md:41 (report only, see constraints).

Then run `pnpm build` (prebuild runs scripts/normalize-csv.py; postbuild copies assets + writes dist/watchdog.json). Afterwards `git status --porcelain data public/data` must be empty. If the normaliser changed data files, STOP and report; do not commit regenerated data.

Commit with explicit paths only (the 12 files above that actually changed): `docs(261001-qex): correct war.gov release mentions to Releases 01–06 / 450 records`.
  </action>
  <verify>
    <automated>cd /Users/laichan/code/tung/war-gov-ufo-release && python3 -c "import csv,collections;r=list(csv.DictReader(open('uap-data.csv',encoding='utf-8-sig')));c=collections.Counter(x['Release Date'] for x in r);assert len(r)==450 and c=={'5/8/26':158,'5/22/26':64,'6/12/26':72,'7/10/26':40,'8/7/26':41,'9/18/26':75},c;print('truth ok')" && ! git grep -n -I -E -e 'Release 01–03' -e 'Releases 01 \+ 02( [^+]|[^ +]|$)' -e 'RELEASES 01 \+ 02 \+ 03 \+ 04 /' -e '222 (wargov|total|cards)' -e 'TOTAL_CARDS = 222' -e 'UFO Release 01"' -e 'PURSUE — Release 01 ' -e 'Releases 01 \(158' -e 'lastUpdated="2026-05-27"' -e 'Release 01 / 02 / 03' -- README.md humans.txt assets/og.svg scripts/build-og.py scripts/sync.sh legacy/glossary.html legacy/compare.html src/pages/index.astro src/components/Card.astro tests/pagination.spec.ts && ! grep -q 'await an' README.md && grep -q 'Releases 03–06' CHANGELOG.md && grep -q 'RELEASES 01–06 / 2026' dist/index.html && grep -q '450 unresolved records' dist/index.html && grep -q 'Last updated 2026-10-01' dist/index.html && grep -q 'Releases 01–06' dist/glossary/index.html && grep -q 'Releases 01–06' dist/assets/og.svg && test -z "$(git status --porcelain data public/data)" && echo T1 OK</automated>
  </verify>
  <done>The gate grep prints nothing. dist/ carries the new stamp, footer date, glossary text and OG text. data/ is unchanged. One commit contains only the swept files, and none of the 4 foreign dirty files are in it.</done>
</task>

<task type="auto">
  <name>Task 2: Package the war.gov release-ingest workflow as a project skill</name>
  <files>.agents/skills/wargov-release-ingest/SKILL.md</files>
  <action>
Location decision: put the skill at `.agents/skills/wargov-release-ingest/SKILL.md`. Reasons: `.claude/` is gitignored wholesale (.gitignore line ≈86), and un-ignoring it would be a Claude-config change that agents must not make unprompted. `.agents/skills/` is tracked, is scanned by the GSD planner/executor ("Project skills"), and the README bullet from Task 1 links to it. Do NOT add `.claude/skills/` or symlinks. Mention in the SUMMARY that the user can symlink it into `.claude/skills/` if they want Claude Code auto-loading.

Write the file. Frontmatter: `name: wargov-release-ingest` and `description:` saying when to use it: "A new war.gov/UFO PURSUE release has been published (new Release Date in war.gov uap-data.csv, or a realufo-watchdog 'New war.gov release detected' GitHub issue). Ingests release N end to end: CSV append, assets, DVIDS→DOD, normalise, landing copy, release-mention sweep, R2 upload, ship." The body is concise and imperative, a numbered runbook referencing REAL paths. Base it on what 260615-3e3 (R03/R04) and 261001-p8k (R05/R06) did. Read `git log --grep 260615-3e3` / `--grep 261001-p8k` and the two SUMMARYs plus the memory file listed in context. Steps:

1. Baseline: count rows per `Release Date` in uap-data.csv (csv.DictReader, utf-8-sig) and keep that fingerprint.
2. Fetch the upstream CSV with curl_cffi Chrome impersonation, using the `fetch()` helper in scripts/download-war.gov.py (URL `https://www.war.gov/Portals/1/Interactive/2026/UFO/uap-data.csv`, cache-buster `?release=…`). Never run download-war.gov.py `main()` end to end. Append ONLY the new-date rows verbatim and never pull upstream edits to older rows. Watch for header drift (R03 added a `Featured` column, documented leniently in src/content.config.ts). Commit the CSV alone FIRST: normalize's `_assert_csv_unchanged` runs `git diff --quiet`. Do not touch uap-release001.csv.
3. Assets: discover the real URLs from the live war.gov/UFO/ markup (rotator `/MMDDYY/Rotator/`, docs zip, cloudfront video zip) and HEAD-200 each one; never guess. Add `SLIDES_N`/`SLIDES_N_DIR` + `BUNDLES` tuples in scripts/download-war.gov.py, fetch slideshow-N images (tracked), download + extract bundles under bundles/ and add .gitignore lines for them. Watch for nested dirs and `__MACOSX`. Some releases have no rotator (R05).
4. DVIDS: copy scripts/resolve-dvids-r06.py to resolve-dvids-r0N.py and run it to produce scripts/dvids2dod-r0N.json. Wire that into `DVIDS_MAP_PATHS` in scripts/normalize-csv.py. Never fabricate IDs. Check each DOD id exists in the video zip.
5. Release batch (D-10 parity): add `'<m/d/yy>' → '0N'` in BOTH scripts/normalize-csv.py (`render_card_html` release mapping, ≈line 581) and src/components/Card.astro `releaseBatch()` (≈line 82).
6. Normalise: `python3 scripts/normalize-csv.py`, then `--check` must be clean. Note the VID hydration total it prints.
7. Landing copy in src/pages/index.astro: filter `<option>`, head-card for Release N (substantive, §9 no filler), hero slides with captions from the CSV Title verbatim, description + jsonLd (total, DVIDS video count, slideshow count), classified stamp range (`RELEASES 01–0N / 2026`), carousel label, `lastUpdated` = ingest date.
8. Postbuild: add `slideshow-N` to the dir loop in scripts/copy-legacy-archives.sh (≈line 216).
9. Release-mention sweep. Copy in the checklist of files Task 1 touched, with the reason for each (landing stamp + lastUpdated, Card.astro comment, tests/pagination.spec.ts TOTAL_CARDS + page count, README release row + slideshow tree + notes bullet, humans.txt, CHANGELOG entry, scripts/sync.sh picker, scripts/build-og.py tagline + assets/og.svg text, scripts/download-war.gov.py CSV comment, legacy/glossary.html (/glossary/), legacy/compare.html) and the exclusion list. Add a gate grep modelled on Task 1's verify that must print nothing, with the range updated to the new N. Remind the reader that CLAUDE.md §2 table row is a user edit.
10. Build: `pnpm build`. Check dist/index.html (stamp, total, filter option), dist/data/wargov-shard-*.json for `data-release="0N"`, dist/slideshow-N/, Pagefind fragment hit, dist/watchdog.json `wargovReleaseDates` includes the new date.
11. R2 upload: diff the `/wargov/` keys in dist/watchdog.json against `aws s3api list-objects-v2 --bucket realufo --prefix {pdfs,videos,pdf-thumbs}/wargov/` (profile `r2`, endpoint, the two checksum env vars). Upload only missing keys from bundles/ with the right `--content-type`. `aws s3 cp` handles >300 MiB by multipart (wrangler caps at 300 MiB, and the local wrangler login is the wrong CF account). Then thumbs: export creds via `aws configure export-credentials --profile r2 --format env` and run `python3 scripts/build-pdf-thumbs.py --slug wargov`. Re-diff to zero, then HEAD-check the big files' ContentLength against the local sizes. Optional cold-storage GH release `wargov-r0N-v1` (no asset > 2 GiB).
12. Ship: commit with explicit paths, `git push origin HEAD`, and confirm `git merge-base --is-ancestor origin/main HEAD`. Then `git push origin HEAD:main` (fast-forward; never force). CI `.github/workflows/deploy-cf-pages.yml` builds and deploys: `gh run list --workflow deploy-cf-pages.yml --limit 1`, then `gh run watch <id> --exit-status`.
13. Verify live on https://realufo.pages.dev/ (and the custom domain once its SSL is active): landing stamp/total, a new card's asset on https://assets.realufo.org/… returns 200, `/watchdog.json` lists the new date.
14. Watchdog: nothing to edit. `scripts/build-watchdog-index.py` (postbuild) derives the release dates from uap-data.csv, so the next daily run goes quiet once deployed. Close the watchdog issue if one was opened.
15. Record the run in a quick SUMMARY and the STATE.md quick-task table.

Keep it under ~150 lines. Use no placeholder language. Every `scripts/…` path that is not a `0N` template must exist.

Commit: `docs(261001-qex): add wargov-release-ingest project skill`.
  </action>
  <verify>
    <automated>cd /Users/laichan/code/tung/war-gov-ufo-release && f=.agents/skills/wargov-release-ingest/SKILL.md && head -5 "$f" | grep -q '^name: wargov-release-ingest' && head -6 "$f" | grep -q '^description: .*war.gov' && python3 -c "import re,os,sys;t=open('$f').read();p=sorted({m for m in re.findall(r'(?:scripts|src|tests|workers)/[A-Za-z0-9_./\[\]-]+\.(?:py|sh|astro|ts|json|yml)',t) if '0N' not in m and 'r0N' not in m});bad=[x for x in p if not os.path.exists(x)];print(len(p),'paths','MISSING',bad);sys.exit(bool(bad))" && test $(wc -l < "$f") -le 200 && git ls-files --error-unmatch "$f" >/dev/null && echo T2 OK</automated>
  </verify>
  <done>The skill is tracked in git, has name + description frontmatter, and every concrete path it references exists. It covers CSV append → assets → DVIDS → batch parity → normalise → landing → postbuild → sweep checklist + gate → build → R2 diff-upload + thumbs → ff-push/deploy → live verify → watchdog (automatic).</done>
</task>

<task type="auto">
  <name>Task 3: Finish R2 upload (diff-driven), push + fast-forward main, deploy, verify live</name>
  <files>scripts/build-pdf-thumbs.py (conditional only)</files>
  <action>
All R2 commands use: `--profile r2 --endpoint-url https://f1868a071996e836eae6da2b65f37929.r2.cloudflarestorage.com` with env AWS_REQUEST_CHECKSUM_CALCULATION=when_required AWS_RESPONSE_CHECKSUM_VALIDATION=when_required. Never echo credentials.

1. Concurrency: run `pgrep -fl build-pdf-thumbs`. If any process is running (another session's thumb upload), do NOT kill it. Wait with a bounded poll: a background/Monitor until-loop checking every 30 s, max 30 min. If it is still running after 30 min, continue anyway; head-object makes the script idempotent.
2. Diff: list keys for prefixes pdfs/wargov/, videos/wargov/, pdf-thumbs/wargov/ with `aws s3api list-objects-v2 --bucket realufo --prefix <p> --query 'Contents[].Key' --output text`. The listing may paginate; the aws CLI auto-paginates. Write the result to the session scratchpad. Compare it with the `/wargov/` keys in `dist/watchdog.json` (from Task 1's build) and print the missing keys grouped by prefix.
   - Missing pdfs/ or videos/ keys: find the local file by case-insensitive basename across bundles/release_05_Aug_07_documents, bundles/documents_release_06_sept_18_2026/documents_release_06_sept_18_2026, bundles/uap_videos_080726, bundles/pursue_vids_091826 (then the other bundles/* dirs), skipping `__MACOSX` and `.DS_Store`. Upload each with `aws s3 cp <file> s3://realufo/<exact key> --content-type application/pdf|video/mp4|image/jpeg`. A key with no local file goes into the report and is not invented.
   - Missing pdf-thumbs/ keys: run the thumb script once: eval "$(aws configure export-credentials --profile r2 --format env)", export the two checksum vars and AWS_DEFAULT_REGION=auto, then `python3 scripts/build-pdf-thumbs.py --slug wargov`. Exit 1 only means some source PDF was unreachable; read its output.
3. Conditional root-cause fix: if thumb keys still missing after step 2 contain a space (planner saw 4, e.g. `DOW-UAP-D114_AAWSAP-Contract-Modification-P00003-May-18- 2010.jpg`), the cause is `_download_from_r2()` in scripts/build-pdf-thumbs.py. It builds `f'{ASSETS_BASE}/pdfs/{slug}/{basename}'` without URL-quoting, so curl gets a literal space. Fix it in that one place: quote the basename with `urllib.parse.quote` (import alongside the existing `unquote`). Leave the R2 upload key unchanged (raw). Rerun the script, then commit with an explicit path: `fix(261001-qex): URL-quote PDF basename in build-pdf-thumbs R2 fallback download`. Skip this step entirely if no space keys remain.
4. Re-diff: zero missing across all three wargov prefixes. HEAD-check `videos/wargov/DOD_111985823.mp4` (ContentLength must be 802522487) plus one R05 video (`DOD_111887376.mp4`, 33427558), and compare against the local sizes in bundles/.
5. Push (single push for all commits): `git fetch origin`, then `git merge-base --is-ancestor origin/main HEAD`. If that fails, STOP and report: someone moved main, and force-push is forbidden. Then `git push origin HEAD` (the branch), `git push origin HEAD:main` (fast-forward), and `git fetch origin main:main` to sync the local main ref. Confirm `git status` still shows the 4 foreign dirty files untouched.
6. Deploy: `gh run list --workflow deploy-cf-pages.yml --limit 1 --json databaseId,headSha,status` must show headSha == `git rev-parse HEAD` (allow ~60 s to appear), then `gh run watch <id> --exit-status`. On failure, collect `gh run view <id> --log-failed | tail -40` and STOP.
7. Live verify on https://realufo.pages.dev/ (allow a minute for propagation, bounded retry):
   - `/`: contains `RELEASES 01–06 / 2026`, `450 unresolved records`, `Last updated 2026-10-01`, and option value 06.
   - `/glossary/` contains `Releases 01–06`. `/assets/og.svg` contains `Releases 01–06`.
   - `/watchdog.json` has 6 wargovReleaseDates including `9/18/26`.
   - Assets: `curl -sI https://assets.realufo.org/videos/wargov/DOD_111985823.mp4` returns 200 and content-length 802522487. One R05 PDF (`pdfs/wargov/CIA-UAP-D022_Unidentified-Flying-Object-Reported-near-Puerto-Rico_1965.pdf`) returns 200. One R06 thumb (`pdf-thumbs/wargov/LLE-UAP-D001_Transcript-of-an-Unresolved-UAP-Report-Colorado-October-2023.jpg`) returns 200.
   - Also record the `https://release.realufo.org/` status code. Expect 525 until the q6n DNS CNAME is set. Report it; do not try to fix DNS or the CF domain.
  </action>
  <verify>
    <automated>cd /Users/laichan/code/tung/war-gov-ufo-release && test "$(git rev-parse origin/main)" = "$(git rev-parse HEAD)" && curl -s https://realufo.pages.dev/ | grep -q 'RELEASES 01–06 / 2026' && curl -s https://realufo.pages.dev/ | grep -q '450 unresolved records' && curl -s https://realufo.pages.dev/glossary/ | grep -q 'Releases 01–06' && curl -s https://realufo.pages.dev/watchdog.json | grep -q '9/18/26' && curl -sI https://assets.realufo.org/videos/wargov/DOD_111985823.mp4 | grep -qi '^content-length: 802522487' && test "$(curl -s -o /dev/null -w '%{http_code}' https://assets.realufo.org/pdf-thumbs/wargov/LLE-UAP-D001_Transcript-of-an-Unresolved-UAP-Report-Colorado-October-2023.jpg)" = 200 && echo T3 OK</automated>
  </verify>
  <done>The R2 diff shows 0 missing wargov keys. origin/main == HEAD by fast-forward. The deploy run for HEAD succeeded. realufo.pages.dev serves the corrected copy, and the R06 assets serve 200. The release.realufo.org status is recorded.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| local shell → R2 (S3 API) | write-scoped `r2` credentials leave the machine |
| local repo → origin/main | push triggers a production deploy |
| CI → Cloudflare Pages | GH secrets CLOUDFLARE_API_TOKEN / ACCOUNT_ID |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-qex-01 | Information disclosure | R2 creds via `aws configure export-credentials` | mitigate | eval into the subshell env only; never echo/print, never write to files or commit; the SUMMARY names the profile, never the keys |
| T-qex-02 | Tampering | origin/main history | mitigate | ancestor check before push; `git push origin HEAD:main` without --force so the server rejects non-ff |
| T-qex-03 | Tampering | foreign dirty files committed by accident | mitigate | explicit-path `git add` only; post-commit `git show --stat HEAD` must not list SECURITY.md / HANDOFF.json / .pending-auth-captures.jsonl / 261001-q6n-SUMMARY.md |
| T-qex-04 | Tampering | wrong R2 key overwrites | mitigate | upload only keys absent from the listing (diff-driven); exact key strings from dist/watchdog.json; no recursive sync/delete |
| T-qex-05 | Repudiation/integrity | content fidelity (§9) | mitigate | only our derived ranges/counts/dates change; official war.gov text untouched; truth re-derived from CSV before editing |
| T-qex-SC | Tampering | package installs | accept | no new packages installed (aws CLI, pdftoppm, curl_cffi already present) |
</threat_model>

<verification>
- T1 OK, T2 OK, T3 OK automated lines all print.
- `git log origin/main --oneline -5` shows the 261001-qex commits on top of af428f0. `git show --stat` for each qex commit lists only planned paths.
- The foreign dirty files are still modified/untracked and were never committed.
</verification>

<success_criteria>
- No stale release range or total remains in any non-excluded tracked file (gate grep clean); CLAUDE.md:41 change proposed to the user in the SUMMARY.
- R2 holds every wargov key the site links to (0 missing).
- Production (realufo.pages.dev) shows Releases 01–06 / 450, deployed by fast-forward of main via CI.
- `.agents/skills/wargov-release-ingest/SKILL.md` is tracked and lets a fresh agent ingest R07 without re-reading old summaries.
</success_criteria>

<output>
Create `.planning/quick/261001-qex-release-mention-content-sweep-r2-upload-/261001-qex-SUMMARY.md` with: the sweep table (file:line, old → new), the exclusion list with reasons, the R2 diff before/after counts, the deploy run id + URL, live verify results, the release.realufo.org status (expected 525, which needs the q6n DNS CNAME), the proposed CLAUDE.md:41 edit for the user, the api/ + feeds/ broken-pipeline follow-up, and the STATE.md TODO lines (R05/R06 upload, R03 large videos) that are now resolved, so the orchestrator can clear them.
</output>
