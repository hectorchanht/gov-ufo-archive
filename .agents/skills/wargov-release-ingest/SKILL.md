---
name: wargov-release-ingest
description: A new war.gov/UFO PURSUE release has been published (new Release Date in war.gov uap-data.csv, or a realufo-watchdog "New war.gov release detected" GitHub issue). Ingests release N end to end: CSV append, assets, DVIDS→DOD, normalise, landing copy, release-mention sweep, R2 upload, ship.
---

# war.gov PURSUE release ingest (R07+)

Distilled from the R03/R04 (`git log --grep 260615-3e3`) and R05/R06
(`git log --grep 261001-p8k`, `--grep 261001-qex`) runs. Work in the MAIN tree,
not a worktree: `bundles/` binaries are gitignored and live only there.
Below, `N` = the new two-digit release (07, 08, …), `PREV` = N-1.

## 1. Baseline
```bash
python3 -c "import csv,collections;r=list(csv.DictReader(open('uap-data.csv',encoding='utf-8-sig')));print(len(r),collections.Counter(x['Release Date'] for x in r))"
```
Keep the per-date fingerprint. At R06 it was 450 rows: 5/8/26 158, 5/22/26 64,
6/12/26 72, 7/10/26 40, 8/7/26 41, 9/18/26 75.

## 2. CSV append (commit FIRST, alone)
- Fetch with the curl_cffi Chrome-impersonating `fetch()` helper in
  `scripts/download-war.gov.py`, URL
  `https://www.war.gov/Portals/1/Interactive/2026/UFO/uap-data.csv?release=7v1`
  (any cache-buster value). Plain curl gets Akamai-blocked. NEVER run that script's `main()`.
- Append ONLY rows whose `Release Date` is new, byte-verbatim. Never pull upstream
  edits to older rows. Check header drift (R03 added `Featured`; handled leniently
  in `src/content.config.ts`). Never touch `uap-release001.csv`.
- Commit `uap-data.csv` alone before normalising: `_assert_csv_unchanged()` in
  `scripts/normalize-csv.py` runs `git diff --quiet` on it.

## 3. Assets
- Read the live war.gov/UFO/ markup for the real URLs: rotator images
  (`/MMDDYY/Rotator/`), the documents zip, the cloudfront video zip. HEAD each one
  for 200. Never guess URLs. Some releases ship no rotator (R05 → no slideshow-5).
- In `scripts/download-war.gov.py` add `SLIDES_N_DIR`, `SLIDES_N`, the
  `SLIDESHOW_N_BASE` fetch block and `BUNDLES` tuples (model on `SLIDES_6`).
- Fetch slideshow-N images (git-tracked). Download + extract bundles into
  `bundles/`. Zips may nest one dir deeper and carry `__MACOSX/` + `.DS_Store`
  (skip both). Add `bundles/<name>*` lines to `.gitignore` (bundles/ is not
  ignored wholesale).

## 4. DVIDS → DOD
`cp scripts/resolve-dvids-r06.py scripts/resolve-dvids-r0N.py`, change the
release-date filter + output path, run it locally (DVIDS blocks GH Actions IPs).
It writes `scripts/dvids2dod-r0N.json`. Add that path to `DVIDS_MAP_PATHS` in
`scripts/normalize-csv.py`. Never fabricate an ID; confirm every DOD id has a
`DOD_<id>.mp4` in the extracted video bundle.

## 5. Release-batch parity (D-10 LOCKED pair)
Add `'<m/d/yy>' → '0N'` in BOTH `render_card_html` in `scripts/normalize-csv.py`
(the `release_date ==` chain) and `releaseBatch()` in `src/components/Card.astro`.

## 6. Normalise
`python3 scripts/normalize-csv.py`, then `python3 scripts/normalize-csv.py --check`
must print clean. Note the VID hydration total it prints (150 at R06).

## 7. Landing copy — `src/pages/index.astro`
Release filter `<option value="0N">`; a head-card for Release N (substantive,
CLAUDE.md §9, no filler); hero slides with captions = CSV `Title` verbatim;
`description` + jsonLd (record total, DVIDS video count, slideshow count);
classified stamp `RELEASES 01–0N / 2026` (short range keeps it inside 360 px);
HeroCarousel label; `lastUpdated` = ingest date (wargov page only).

## 8. Postbuild
Add `slideshow-N` to the dir loop in `scripts/copy-legacy-archives.sh`
(`for dir in assets slideshow slideshow-2 …`). Without it the images 404 on deploy.

## 9. Release-mention sweep
Each of these names the release range or the total. Update them all:

| File | What |
| --- | --- |
| `src/pages/index.astro` | stamp, `lastUpdated`, filter, head-card, jsonLd, carousel label |
| `src/components/Card.astro` | releaseBatch() (step 5); comments stay release-agnostic |
| `tests/pagination.spec.ts` | `TOTAL_CARDS`, shard count, page count `Math.ceil(total / 20)` |
| `README.md` | archive table row 1, slideshow tree line, Releases notes bullet |
| `humans.txt` | PURSUE line (keep the `— war.gov/UFO/` column aligned) |
| `CHANGELOG.md` | new `### Added — War.gov / PURSUE Release N` under `[Unreleased]` |
| `scripts/sync.sh` | picker label `[1] war.gov / UFO Releases 01–0N` |
| `scripts/build-og.py` + `assets/og.svg` | wargov tagline; edit the svg text node directly, do NOT run build-og.py (it rewrites all 15 OG files + legacy meta) |
| `scripts/download-war.gov.py` | MANIFESTS comment (`01–0N as of <date>`) |
| `legacy/glossary.html` | PURSUE `<dd>` (ships as `/glossary/` via `src/pages/glossary.astro`) |
| `legacy/compare.html` | PURSUE row (not shipped, but tracked) |

Leave alone: `.planning/**` (history); dormant archives (`legacy/<dormant-slug>/`,
`scripts/build-brazil.py` and the other dormant builders, `scripts/templates/lightbox.py`);
`legacy/index.html` (retired landing); `api/` + `feeds/` (retired pipeline);
`uap-data.csv` / `uap-release001.csv`; old CHANGELOG entries. CLAUDE.md §2 table
row 1 (`War.gov / PURSUE — Releases 01–0N`) is a USER edit: propose it, do not
change CLAUDE.md yourself.

Gate, run under bash (must print nothing; PREV/TOTAL_OLD = the range and total being replaced):
```bash
PREV=06 TOTAL_OLD=450
git grep -n -I -E -e "RELEASES 01–$PREV /" -e "Releases 01–$PREV([^0-9]|$)" -e "TOTAL_CARDS = $TOTAL_OLD" \
  -e "UFO Releases 01–$PREV\"" -e "$TOTAL_OLD records" -e "$TOTAL_OLD unresolved" -- \
  README.md humans.txt assets/og.svg scripts/build-og.py scripts/sync.sh \
  legacy/glossary.html legacy/compare.html src/pages/index.astro \
  src/components/Card.astro tests/pagination.spec.ts
```

## 10. Build + check
`pnpm build` (prebuild normalises, postbuild copies assets + writes
`dist/watchdog.json`). Then `git status --porcelain data public/data` must be
empty. Check: `dist/index.html` stamp, total, `<option value="0N">`;
`grep -c 'data-release=\"0N\"' dist/data/wargov-shard-*.json` (new rows land in
the shards, not the 50 SSR cards); `dist/slideshow-N/`; a Pagefind hit for a new
title; `dist/watchdog.json` `wargovReleaseDates` includes the new date.

## 11. R2 upload (diff-driven)
Bucket `realufo`, aws CLI profile `r2`, endpoint
`https://f1868a071996e836eae6da2b65f37929.r2.cloudflarestorage.com`, env
`AWS_REQUEST_CHECKSUM_CALCULATION=when_required AWS_RESPONSE_CHECKSUM_VALIDATION=when_required`.
Never echo credentials. Local wrangler is logged into the wrong CF account; use aws.
```bash
EP=https://f1868a071996e836eae6da2b65f37929.r2.cloudflarestorage.com
for p in pdfs/wargov/ videos/wargov/ pdf-thumbs/wargov/; do
  aws s3api list-objects-v2 --bucket realufo --prefix "$p" --query 'Contents[].Key' --output text \
    --profile r2 --endpoint-url "$EP" | tr '\t' '\n'; done | sort > /tmp/r2.txt
python3 -c "import json;[print(k) for k in json.load(open('dist/watchdog.json'))['assets'] if '/wargov/' in k]" | sort > /tmp/want.txt
comm -13 /tmp/r2.txt /tmp/want.txt   # missing keys
```
- Missing `pdfs/` / `videos/`: find the file in `bundles/` by basename (skip
  `__MACOSX`), `aws s3 cp <file> s3://realufo/<exact key> --content-type
  application/pdf|video/mp4|image/jpeg`. `aws s3 cp` does multipart, so >300 MiB is fine.
  A key with no local file gets reported, never invented.
- Thumbs: `eval "$(aws configure export-credentials --profile r2 --format env)"`,
  export the two checksum vars + `AWS_DEFAULT_REGION=auto`, then
  `python3 scripts/build-pdf-thumbs.py --slug wargov` (idempotent, head-object skip;
  exit 1 = some source PDF unreachable, read the output).
- Re-diff to zero. HEAD the big videos and compare `ContentLength` with local sizes.
- Optional cold storage: GH release `wargov-r0N-v1` (no asset > 2 GiB).

## 12. Ship
Commit with explicit paths only (never `git add -A`). `git push origin HEAD`;
`git fetch origin && git merge-base --is-ancestor origin/main HEAD` must pass;
then `git push origin HEAD:main` (fast-forward, never `--force`). CI
`.github/workflows/deploy-cf-pages.yml` builds + deploys:
`gh run list --workflow deploy-cf-pages.yml --limit 1`, `gh run watch <id> --exit-status`.

## 13. Verify live
On https://realufo.pages.dev/ (and the custom domain once its SSL is active):
landing stamp + total + new filter option; a new card's asset on
`https://assets.realufo.org/<key>` returns 200; `/watchdog.json` lists the new date.

## 14. Watchdog
Nothing to edit in `workers/watchdog/`. `scripts/build-watchdog-index.py` (postbuild)
derives `wargovReleaseDates` from `uap-data.csv`, so the next daily run goes quiet
after deploy. Close the "New war.gov release detected" issue if one was opened.

## 15. Record
Write the quick-task SUMMARY (fingerprint, commits, R2 diff counts, deploy run id,
live checks) and add the row to the STATE.md quick-task table.
