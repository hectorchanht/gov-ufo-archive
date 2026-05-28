---
slug: vid-cards-no-thumb-no-play
status: resolved
trigger: "VID cards on https://realufo.pages.dev/ (wargov index) render with no thumbnail + no Play/Open button. Card body shows only title, desc, metadata, and Source ↗ + DVIDS ↗ buttons. User reports 'video is not showing thumbnail and click to play'. Per CLAUDE.md §4.3 VID cards must show Play button when video URL exists; per §4.2 thumb field should populate."
created: "2026-05-28"
updated: "2026-05-29"
phase: "05-scrape-automation"
plan: "post-05-01"
---

# Debug: VID cards missing thumbnail + Play button on wargov index

## Symptoms

- **Expected:** Each VID card on `/` (wargov index) renders with (a) thumbnail poster image, (b) "Play" or "Open" button that opens lightbox to play the mp4. Click-anywhere-on-card opens lightbox per commit `1a563e9`.
- **Actual:** VID cards show only h3 title + p desc + dl meta + Source ↗ + DVIDS ↗. No `<img>` thumb. No `.btn-open`. No `.btn-download`. Huge empty black area below metadata.
- **Error messages:** None. Silent missing-render.
- **Timeline:** Present on current production deploy (`d19572e`, 10h ago). Likely present since Phase 4 wargov port (`1a563e9` commit added click-anywhere but did not add thumb/Play buttons for VID rows).
- **Reproduction:** Visit https://realufo.pages.dev/ → scroll to "Archive" section → filter "Video" tab → any of 78 VID cards.

## Pre-investigation context

### Diagnosis already collected (from orchestrator turn)

**Card.astro markup contract** (`src/components/Card.astro` lines 30-89, 107-152):
```typescript
const url = row['PDF | Image Link'] ?? '';   // line 66
const thumb = row['Modal Image'] ?? '';      // line 67
```
Cards render `<img>` only if `thumb` truthy. Cards render `.btn-open` / `.btn-download` only if `url` truthy.

**CSV inspection** (corrected during investigation — source is `uap-data.csv` (222 rows), NOT `uap-release001.csv`):
- 78 total VID rows
- 78 of 78 VID rows have **EMPTY `Modal Image`** → no thumb rendered for ANY VID
- 66 of 78 VID rows have empty `PDF | Image Link` → no Open/Download
- 12 of 78 have `PDF | Image Link` populated but it points at the PAIRED PDF (`DoW-UAP-D10.pdf`), not the video file — `normalize-csv.py` was rewriting these to `https://assets.realufo.org/videos/wargov/<paired-pdf>.pdf` which 404s in R2's videos prefix.

**Verified actual mechanics:**
- 78 mp4s in R2 at `https://assets.realufo.org/videos/wargov/DOD_<id>.mp4` (Plan 05-01 unblock 2026-05-28)
- Filenames are `DOD_<dvidshub-asset-id>.mp4` — DIFFERENT from the `DVIDS Video ID` column (which carries the *catalog page* ID)
- `scripts/resolve-dvids-r01.py` already exists — it scrapes dvidshub.net per DVIDS ID and emits a catalog→asset lookup JSON
- `scripts/dvids2dod-r01.json` (16 entries) + `scripts/dvids2dod-r02.json` (57 entries) = **73 of 78 VID rows** resolvable today
- The 12 R01 paired-PDF rows correspond to 12 unresolved R01 DVIDS IDs (operator needs to re-run `resolve-dvids-r01.py` to fill them)
- `slideshow-2/` has 10 jpgs (4 directly matching VID PR-IDs), `slideshow/` has 30 jpgs (10 matching VID PR-IDs) → 14 total thumb matches

## Evidence

- timestamp: 2026-05-29 (session-manager run)
  - CSV `uap-data.csv` has 222 rows, 78 VID; PR050 (row 0, DVIDS 1007706) + PR051 (row 1, DVIDS 1007707) confirmed with empty `PDF | Image Link` + empty `Modal Image`.
  - `scripts/dvids2dod-r02.json` resolves 1007706 → DOD_111719709 and 1007707 → DOD_111719715. Both R2 URLs return HTTP 200 (content-type video/mp4, content-length 3MB + 154MB respectively).
  - `slideshow-2/DOW-UAP-PR050_4UAP_Formation_Iran_26_Aug_2022.jpg` + `slideshow-2/DOW-UAP-PR051.jpg` exist on disk.
  - Existing `_archive_common.rewrite_to_r2()` rewrites the paired-PDF URL to `https://assets.realufo.org/videos/wargov/<pdf-basename>.pdf` — broken because the file doesn't exist in the `/videos/` prefix.
  - `scripts/copy-legacy-archives.sh` line 152 copies `slideshow/` to dist/ but does NOT copy `slideshow-2/` → even with correct CSV→JSON wiring the R02 thumbs would 404.
  - `normalize-csv.py:render_card_html()` mirror to `Card.astro` is INTACT and BYTE-EQUIVALENT — no D-10 contract violation needed. Fix is data-side only.

## Eliminated

- **Astro / Card.astro rendering bug** — Card.astro renders correctly when `Modal Image` + `PDF | Image Link` are populated. PDF cards (which have both fields populated by `_archive_common.rewrite_to_r2`) render with thumb + Open + Download buttons just fine. Bug is upstream data population for VID rows.
- **Lightbox VID handling** — `src/scripts/invariants.ts` lines 179-186 already handle `.mp4` URLs with `<video controls preload="metadata" playsinline>` dual-source rendering. No JS change needed.
- **CSV-mutation fix** — VIOLATES CLAUDE.md §11. Confirmed CSV is read-only via `_assert_csv_unchanged()`. Fix must live entirely in `normalize-csv.py` build step.

## Resolution

- **root_cause:** `normalize-csv.py:_read_rows()` did not bridge the `DVIDS Video ID` (catalog ID) → R2 mp4 asset ID (`DOD_<id>.mp4`). For VID rows with empty `PDF | Image Link` (66/78) it left the field empty → Card.astro omitted `<img>` + `.btn-open`. For VID rows with a paired-PDF URL (12/78) it ran `rewrite_to_r2(..., 'videos')` which produced `videos/wargov/<paired-pdf>.pdf` — wrong prefix + wrong file (404). All 78 VID rows had empty `Modal Image`, so no card got a thumbnail.

- **fix:** Three coordinated edits, applied 2026-05-29 (no Card.astro / JS / CSV mutation; D-10 byte-equivalence contract preserved):

  1. `scripts/normalize-csv.py` — added `_load_dvids_to_dod()` (merges `dvids2dod-r01.json` + `dvids2dod-r02.json`), `_load_pr_thumbs()` (scans `slideshow-2/` then `slideshow/` for `PR\d+`-keyed thumbnails), `_hydrate_vid_url()`, `_hydrate_thumb()`. Inside `_read_rows()` VID rows are patched at read time: empty/non-mp4 `PDF | Image Link` → R2 mp4 URL when DVIDS resolves, else cleared (no broken `.pdf` URLs); empty `Modal Image` → slideshow path when PR-ID matches. Source CSVs untouched (T-03-07 guard still holds; `--check` mode confirmed clean).

  2. `scripts/copy-legacy-archives.sh` — added `slideshow-2` to the static-asset copy loop (line 152). Without this the hydrated `Modal Image` paths `/slideshow-2/*.jpg` would 404 on the deployed site.

  3. Regenerated `data/wargov.json` + `data/wargov-shard-{2,3,4}.json` + `public/data/*.json` mirrors via `pnpm prebuild` (chained to `pnpm build`). Hydration log line:
     ```
     [info] VID hydration: 66 mp4 URLs (from DVIDS map), 14 thumbs (from slideshow-folder PR-ID match), 12 stale paired-PDF URLs cleared
     ```

- **verification:**
  - `python3 scripts/normalize-csv.py --check` → clean (no drift, idempotent).
  - `pnpm build` succeeds end-to-end; postbuild copies 178 legacy files including 10 slideshow-2 jpgs; Pagefind indexes 4 pages.
  - `dist/index.html` PR050 card parsed: has `<img src="/slideshow-2/DOW-UAP-PR050_4UAP_Formation_Iran_26_Aug_2022.jpg">` + `<a class="btn-open" data-url="https://assets.realufo.org/videos/wargov/DOD_111719709.mp4">`.
  - Aggregate VID rendering stats across `data/wargov.json` + shards: 78 VID cards total → 66 with Play button (R2 mp4), 14 with thumbnails, 12 graceful-degrade to DVIDS ↗ external only.
  - `curl -sI https://assets.realufo.org/videos/wargov/DOD_111719709.mp4` → HTTP/2 200 (3 MB mp4); `DOD_111719715.mp4` → HTTP/2 200 (154 MB).
  - `dist/slideshow-2/` directory contains all 10 jpgs after rebuild (was 0 before).

- **files_changed:**
  - `scripts/normalize-csv.py` (+215/-1) — VID hydration helpers + read-time patch
  - `scripts/copy-legacy-archives.sh` (+8/-1) — slideshow-2 copy
  - `data/wargov.json` (regenerated)
  - `data/wargov-shard-{2,3,4}.json` (regenerated)
  - `public/data/wargov.json` + `public/data/wargov-shard-{2,3,4}.json` (regenerated mirrors)

- **follow-ups:**
  - To recover the 12 R01 paired-PDF rows, run `python3 scripts/resolve-dvids-r01.py` locally (DVIDS blocks GH Actions egress per Plan 05-02 Akamai spike), then re-run `pnpm prebuild`. Each new entry in `scripts/dvids2dod-r01.json` automatically promotes one card from "DVIDS ↗ only" to full Play button + R2 mp4.
  - 64 VID rows still have no thumbnail (10/30 slideshow PR-ID matches only). Future thumb seeding (extract video poster frames + upload to R2 → reference via `Modal Image`) would close this gap, but is orthogonal to the user-visible blocker resolved here.
