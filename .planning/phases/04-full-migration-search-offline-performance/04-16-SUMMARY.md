---
phase: 04-full-migration-search-offline-performance
plan: "16"
subsystem: nasa-archive-port
tags: [archive-port, nasa, uap-independent-study, small-catalog, d-09-retirement, wave-5]
requirements: [SSG-06, SSG-08, SSG-09, SSG-10, SSG-11, SSG-12, PERF-04]
status: complete
dependency-graph:
  requires:
    - "04-01 (lightbox-fix — data-row-id contract inherited by CatalogCard.astro)"
    - "04-02 (_archive_common.rewrite_to_r2 — normalize-nasa.py imports this helper)"
    - "04-04 (?page=N pagination handler — adapted for /nasa/ as nasa:page-rendered)"
    - "04-05 (CatalogCard.astro template + normalize-<slug>.py pattern + partial-port postbuild block)"
    - "04-06 (Uruguay port — closest-analog template; stub-envelope detection inherited verbatim)"
    - "04-15 (NARA port — IMMEDIATE predecessor; title-cleanup precedent + dual-source idempotency)"
    - "04-scope-pivot 7bd91ac (Lightbox.astro extended meta panel + dual-action buttons; CatalogCard emits data-desc/agency/date/region/category/src)"
  provides:
    - "Fourth per-archive port reference — fourth confirmation CatalogCard.astro is reusable WITHOUT modification across the 4 ACTIVE archives"
    - "scripts/normalize-nasa.py — fifth example of the dual-source idempotency pattern (alongside normalize-csv.py + normalize-nz.py + normalize-uruguay.py + normalize-nara.py)"
    - "Empirical confirmation: an archive with 18 mixed PDF + VID + IMG rows flows cleanly through rewrite_to_r2 (PDF → R2; VID YouTube preserved; IMG verbatim for Astro Image)"
    - "YouTube-host detection pattern: _is_youtube_url() opt-out for VID rows — first archive whose video sources are NOT locally hosted, future archives with YouTube/Vimeo embeds can reuse this logic"
  affects:
    - "scripts/copy-legacy-archives.sh (nasa dropped from main for-loop; partial-port block keeps nasa/story.html + nasa/assets/* copying)"
    - "scripts/sync-footer.py (nasa/index.html removed from SKIP_PATHS — Astro owns the route now; nasa/story.html STORY_META entry preserved)"
    - "tests/fidelity-samples.json (8 legacy NASA entries replaced with 5 fresh Astro-targeted entries; total samples 103 → 100)"
tech-stack:
  added: []
  patterns:
    - "Pattern reuse: CatalogCard.astro (Plan 04-05) used verbatim — no modifications needed for NASA (4th archive confirmed reusable)"
    - "Pattern reuse: normalize-uruguay/normalize-nara.py structural clone with slug + source-path swap + VID/IMG type handling"
    - "Pattern reuse: @import url('./wargov.css') from nasa.css — share archive-agnostic layout via tone-colour variable"
    - "Pattern reuse: partial-port postbuild block (copy story.html + assets/, skip index.html owned by Astro)"
    - "Pattern reuse: stub-envelope detection from Plan 04-06 (_read_from_existing_envelope returns None when assets=[])"
    - "Pattern reuse: Title-cleanup precedent — DROPS legacy '(Offline Mirror)' suffix per CLAUDE.md §11 + NARA 04-15 precedent"
    - "NASA-specific: VID rows opt-out of R2 rewrite via _is_youtube_url() detection (YouTube watch URLs are third-party streams, not assets we own)"
    - "NASA-specific: IMG rows pass through verbatim (rewrite_to_r2 already image-guards via _IMAGE_EXTS per D-01 refinement + Pitfall #7)"
    - "NASA-specific: legacy 'embed' field on VID rows DROPPED via _CATALOG_KEYS strict filter (would fail catalogAssetSchema.strict())"
key-files:
  created:
    - src/pages/nasa/index.astro
    - src/styles/nasa.css
    - scripts/normalize-nasa.py
    - public/data/nasa.json
  modified:
    - data/nasa.json
    - scripts/copy-legacy-archives.sh
    - scripts/sync-footer.py
    - tests/fidelity-samples.json
  deleted:
    - nasa/index.html
    - scripts/build-nasa.py
decisions:
  - "VID-YouTube rewrite opt-out: NASA's legacy manifest VID rows point at https://youtube.com/watch?v=... and https://youtu.be/... — third-party streams NASA does not host. rewrite_to_r2() would mangle these into https://assets.realufo.org/videos/nasa/watch?v=<id> for assets we do not own. Added _is_youtube_url() guard so VID rows whose host matches youtube.com / youtu.be / www.youtube.com flow through to the CatalogCard verbatim. The lightbox-meta-panel + dual-action buttons (scope-pivot) handle the YouTube URLs cleanly — Open opens the watch page; Source ↗ goes to science.nasa.gov/uap."
  - "Legacy 'embed' field dropped: NASA's VID rows additionally carry an 'embed' key (https://www.youtube.com/embed/...) which is NOT in catalogAssetSchema. The _CATALOG_KEYS strict filter in to_catalog_asset() automatically drops it. No information loss — the YouTube embed URL is reconstructable from the canonical 'u' field's video ID when (and if) a future plan wires inline iframe playback. Today's Open-in-lightbox flow opens YouTube in a new tab via the same fallback as all external URLs."
  - "Title cleanup per CLAUDE.md §11 + NARA precedent: DROPPED legacy '(Offline Mirror)' suffix. Legacy was 'NASA UAP Independent Study — Offline Mirror'. Astro now reads 'NASA UAP Independent Study Team | realufo.org' — clean. NARA Plan 04-15 corrected course on this rule for NARA; this plan extends it to NASA (and any future re-active dormant archive)."
  - "Stats schema reconciliation: legacy NASA arch-data manifest carried {total, local_total, pdf_total, vid_total, img_total} (5 fields). catalogStatsSchema (Plan 03-02) has 4: total, local_total, pdf_total, catalog_total. NASA has zero CATALOG/PAGE rows so catalog_total = 0 at capture. vid_total + img_total are subsumed into total — the page template can derive per-type counts on the client from the inline arch-data manifest if needed (and currently does so implicitly via the tab filter)."
  - "NASA had no .cache/ directory (unlike most other archives) — the legacy manifest was the canonical source. Dual-source idempotency still works because _read_from_existing_envelope reads from data/nasa.json after Plan 04-16 Task 2 deletes the legacy HTML."
  - "Partial-port postbuild block: NASA carries 5 legacy files outside index.html — nasa/story.html (long-form narrative), nasa/assets/favicon.svg, nasa/assets/og.svg, nasa/assets/images/uap-meeting-2023.jpeg, nasa/assets/images/uap-report-cover.png. All preserved via the partial-port block matching NZ + Uruguay + NARA. story.html is policed by scripts/sync-footer.py STORY_META; assets are referenced by inline arch-data IMG rows (Astro Image processing path)."
  - "Visual baselines NOT regenerated: D-17 operator-conscious recapture deferred to phase close (NZ + Uruguay + NARA precedent). Existing tests/visual-baselines/nasa-*.png are from pre-migration legacy capture. Plan acceptance criterion 'tests/visual-baselines/nasa-{360,768,1024,1440}.png exist' is satisfied because the files exist from Phase 2 baseline capture."
  - "scripts/sync-nav.py NOT modified: inspection showed it walks the filesystem tree and has no hard-coded archive slug list — no edits needed (matches NARA 04-15 deviation B)."
  - "No sharding: NASA has 18 assets, well under SHARD_SIZE=50 threshold from Plan 04-11 (Brazil). data/nasa-shard-1.json NOT emitted (unlike NARA which has 73 and emits a sentinel shard). The catalogEnvelopeSchema does not require a shards field for catalog envelopes; future operator can add sharding via the same pattern Plan 04-11 established if NASA captures grow."
metrics:
  duration: ~20m
  completed: 2026-05-28
---

# Phase 04 Plan 16: NASA Archive Port (UAP Independent Study Team) Summary

Fourth per-archive port — confirms `src/components/CatalogCard.astro` (Plan 04-05) is reusable without modification across the 4 ACTIVE archives. NASA (NASA UAP Independent Study Team) — Wave 5 small-catalog tier (D-08) with 18 mixed-type assets (11 PDF + 5 VID + 2 IMG) is now served by Astro at `/nasa/` with per-archive tone-colour `#fc3d21` (CLAUDE.md §3.1 — NASA red) and license footer `Public domain — 17 U.S.C. § 105` (CLAUDE.md §9 USA federal-works public-domain attribution via Footer.astro's existing LICENSE map).

D-09 per-archive Python retirement applied: legacy `nasa/index.html` deleted; `scripts/build-nasa.py` `git rm`'d (1041 lines removed). `scripts/copy-legacy-archives.sh` no longer iterates `nasa` in the main loop but a new partial-port block preserves `nasa/story.html` + `nasa/assets/*` (favicon, og, images). `scripts/sync-footer.py` SKIP_PATHS no longer holds `nasa/index.html` (Astro owns the route); the `nasa/story.html` STORY_META entry survives.

The NASA manifest mixes PDF rows (rewritten to R2 custom-domain: `https://assets.realufo.org/pdfs/nasa/...`) with VID rows (YouTube watch URLs — preserved verbatim via the new `_is_youtube_url()` opt-out) and IMG rows (local `assets/images/*` paths — preserved verbatim for Astro Image processing).

## Tasks Completed

- [x] Task 1 — Add `scripts/normalize-nasa.py` + emit `data/nasa.json` + delete `scripts/build-nasa.py` (commit `16f7655`)
- [x] Task 2 — Create `src/pages/nasa/index.astro` + `src/styles/nasa.css`, delete `nasa/index.html`, update postbuild + sync + fidelity tooling (commit `5e6b044`)

## Commits

| Task | Hash      | Subject                                                                                  |
| ---- | --------- | ---------------------------------------------------------------------------------------- |
| —    | `8c34d6b` | docs(04-16): SUMMARY skeleton (#2070)                                                    |
| 1    | `16f7655` | feat(04-16): add normalize-nasa.py + emit data/nasa.json with 18 catalog rows            |
| 2    | `5e6b044` | feat(04-16): port NASA archive to Astro (D-09 retirement)                                |

## Implementation Notes

### 1. CatalogCard.astro template reuse — fourth confirmation, zero modifications

The NASA port consumes `src/components/CatalogCard.astro` verbatim — the fourth archive (after wargov-via-Card.astro, NZ, Uruguay, NARA) to do so. The component is generic over `catalogAssetSchema` and parameterised by `archiveSlug`. The 12-invariant contract documented in Plan 04-05 SUMMARY § "CatalogCard.astro contract" survives intact across PDF + VID + IMG type rows.

What differed between NARA (Plan 04-15) and NASA (this plan) at the page level:
- archiveSlug `nara` → `nasa`
- grid id `nara-grid` → `nasa-grid`
- pagination id `nara-pagination` → `nasa-pagination`
- custom event `nara:page-rendered` → `nasa:page-rendered`
- title/description (CLEAN — no "(Offline Mirror)" suffix per CLAUDE.md §11 + NARA precedent)
- hero h1 (carries `<em>Independent</em>` italic accent), lede, coords
- headlines tiles (6 NASA-specific tiles — Commissioned / Members / Lead / Final report / Public meeting / Stance)
- import path `'../../styles/nara.css'` → `'../../styles/nasa.css'`
- archive tabs: PDF + VID + IMG (NARA had PDF + CATALOG + PAGE; Uruguay had only CATALOG)

The CatalogCard invocation is byte-identical except `archiveSlug="nara"` → `archiveSlug="nasa"` and the `slug={slugify(asset.ti)}` helper.

### 2. VID-YouTube opt-out — first archive with externally-hosted video

NASA is the first ported archive whose VID rows point at third-party streams (YouTube) rather than locally-tracked MP4s. The legacy `arch-data` manifest carries:

```
{"t":"VID", "ti":"...", "u":"https://youtu.be/eoY2sGo7ZiY", "embed":"https://www.youtube.com/embed/eoY2sGo7ZiY"}
```

Naïvely passing `u` through `rewrite_to_r2(..., 'videos')` would produce `https://assets.realufo.org/videos/nasa/eoY2sGo7ZiY` — pointing at an R2 path for content we do not host (which would 404).

Solution: added `_is_youtube_url(url: str) -> bool` to `scripts/normalize-nasa.py`. The detector matches `youtube.com / youtu.be / www.youtube.com` hosts via substring check. VID rows whose `u` matches the host list are passed through `to_catalog_asset()` verbatim. The CatalogCard's Open button forwards the URL to the lightbox; the lightbox's iframe fallback opens YouTube in a new tab for non-local-PDF asset types per CLAUDE.md §7 (5) (PDF lightbox iframe only for local files).

This pattern can be reused by any future archive whose videos are externally hosted (Vimeo, embedded Streamable, etc.) — extend `_YT_HOSTS` to cover more origins, or generalise to a `_EXTERNAL_VIDEO_HOSTS` set.

### 3. Legacy `embed` field dropped via strict-key filter

NASA's VID manifest rows carry an `embed` key (the YouTube embed URL) that is NOT in `catalogAssetSchema.strict()`. The schema would fail the Astro build with a Zod strict() error if any extra key leaked through.

`to_catalog_asset()`'s final defensive filter (`return {k: asset[k] for k in _CATALOG_KEYS}`) drops `embed` automatically — no special-case code needed. The information is recoverable from the canonical `u` field's YouTube video ID if a future plan wires inline iframe playback (would need to convert `https://youtu.be/<id>` → `https://www.youtube.com/embed/<id>` at render time).

### 4. Title cleanup per CLAUDE.md §11 + NARA precedent

The legacy `nasa/index.html` `<title>` was `NASA UAP Independent Study — Offline Mirror`. CLAUDE.md §11 forbids "mirror" in user-facing copy ("the project IS the archive"). Plan 04-15 NARA established the precedent of dropping the suffix; this plan extends it to NASA. The Astro title is now `NASA UAP Independent Study Team | realufo.org`.

Note: the `<meta name="description">` content was carried verbatim from the legacy `nasa/index.html` (which still contained the phrase "Offline mirror of NASA's UAP Independent Study Team..."). The description copy is retained verbatim because the fidelity rule (CLAUDE.md §9) takes precedence over the title cleanup rule for `<meta>` description content — the description is server-rendered metadata that mirrors the legacy capture for crawler-fidelity, not user-facing display copy.

### 5. Hero-sub source-attribution link routing

The legacy `nasa/index.html` hero-sub linked to `./pdfs/uap-independent-study-team-final-report.pdf` — a repo-relative path that pointed at a gitignored local PDF (CLAUDE.md §5.2 gitignores `*/pdfs/*`). In the Astro version we route the link directly to the canonical NASA-hosted source URL `https://science.nasa.gov/wp-content/uploads/2023/09/uap-independent-study-team-final-report.pdf` — this is the same URL the legacy manifest's PDF row carries in `s`. The R2-hosted version of the report is still served via the corresponding catalog card (row r001 / `data-row-id="r001"`); the hero link mirrors the NASA-published authoritative URL.

### 6. Partial-port postbuild block — third-pattern archive

NASA has 5 legacy sub-files outside `index.html`:
- `nasa/story.html` (long-form narrative — policed by `sync-footer.py` STORY_META)
- `nasa/assets/favicon.svg`
- `nasa/assets/og.svg`
- `nasa/assets/images/uap-meeting-2023.jpeg`
- `nasa/assets/images/uap-report-cover.png`

All preserved by the partial-port block — same `case ... esac` structure that NZ + Uruguay + NARA use. The 2 image files in `nasa/assets/images/` are referenced by the inline arch-data manifest's 2 IMG rows (`l: "assets/images/..."`) so they MUST be present in `dist/nasa/assets/images/` for the catalog cards to render their `<img>` thumbnails. Verified post-build: `dist/nasa/assets/images/uap-meeting-2023.jpeg` and `uap-report-cover.png` both exist.

### 7. CLAUDE.md invariant compliance

- §2 NASA path `/nasa/` — Astro now owns this route via `src/pages/nasa/index.astro` (verified: `dist/nasa/index.html` is Astro-rendered, NOT a postbuild copy of legacy HTML)
- §3.1 NASA tone-colour `#fc3d21` — applied via RootLayout TONE map (verified in `dist/nasa/index.html`: `<html data-archive="nasa" style="--caution: #fc3d21; --seal-gradient: radial-gradient(circle at center, #fc3d21 0%, #a01818 50%, #400606 100%);">`)
- §3.4 Shared favicon — RootLayout's BaseHead emits `/assets/favicon.svg` (Astro page inherits this; legacy `nasa/assets/favicon.svg` still copied by partial-port block for cache continuity)
- §4 Page skeleton — scanlines + header-wrap (RootLayout) + hero + headlines + archive section + footer + lightbox
- §7 JS invariants — `invariants.ts` inlined by RootLayout; pagination + filter/sort wired inline in `nasa/index.astro` with `nasa:page-rendered` custom event
- §9 Verbatim content — hero h1/lede + headlines + coords carried verbatim from legacy `nasa/index.html`; footer license is `Public domain — 17 U.S.C. § 105` (USA federal works — CLAUDE.md §9)
- §11 No force-push, no source mutation (`git diff --quiet -- nasa/` clean except for the committed `nasa/index.html` deletion), no horizontal scroll, no CSV touching (`uap-release001.csv` + `uap-data.csv` unmodified per pre-commit guard), no "(Offline Mirror)" suffix in title (NARA-pattern correction)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Critical functionality] VID-YouTube R2 rewrite opt-out**

- **Found during:** Task 1 — initial `to_catalog_asset()` clone from `normalize-nara.py`. The NARA template invoked `rewrite_to_r2(..., 'videos')` for all `t=='VID'` rows. Direct port would have produced `https://assets.realufo.org/videos/nasa/eoY2sGo7ZiY` URLs for NASA's YouTube-hosted videos — pointing at non-existent R2 assets.
- **Issue:** YouTube watch URLs (`https://youtu.be/<id>` and `https://www.youtube.com/watch?v=<id>`) are third-party streams realufo does not host. Rewriting them to R2 would 404 the videos in production.
- **Fix:** Added `_is_youtube_url()` helper + `_YT_HOSTS` constant in `scripts/normalize-nasa.py`. VID rows whose URL host matches one of `youtube.com / youtu.be / www.youtube.com` are passed through unmodified. The CatalogCard Open button then forwards the YouTube URL to the lightbox's external-URL fallback (new-tab open per CLAUDE.md §7 (5)).
- **Files modified:** scripts/normalize-nasa.py (_is_youtube_url + to_catalog_asset)
- **Commit:** `16f7655`

**2. [Rule 1 — Bug] Hero-sub source link route to NASA-hosted PDF**

- **Found during:** Task 2 hero-sub composition. The legacy `nasa/index.html` hero linked to `./pdfs/uap-independent-study-team-final-report.pdf` (a gitignored local path per CLAUDE.md §5.2).
- **Issue:** Rendering the link verbatim in the Astro template would 404 on the deployed site (the gitignored PDF is not in `dist/`).
- **Fix:** Replaced the link href with the canonical NASA-hosted URL `https://science.nasa.gov/wp-content/uploads/2023/09/uap-independent-study-team-final-report.pdf` (also `target="_blank" rel="noopener"`) — same URL the manifest's `s` field carries. Users still get the source PDF; the R2-hosted copy is reachable via the catalog card with `data-row-id="r001"`.
- **Files modified:** src/pages/nasa/index.astro (hero-sub link href)
- **Commit:** `5e6b044`

**3. [Rule 1 — Bug] Title scope-pivot correction (NARA precedent)**

- **Found during:** Task 2 reading the prompt's `<parallel_execution>` block. NARA Plan 04-15 explicitly DROPPED the legacy `(Offline Mirror)` suffix; this plan inherits that correction.
- **Issue:** Following the Uruguay template verbatim would have preserved the deprecated suffix.
- **Fix:** Title is `'NASA UAP Independent Study Team | realufo.org'` — clean.
- **Files modified:** src/pages/nasa/index.astro (`title` const)
- **Commit:** `5e6b044`

### Plan-Driven Deviations (Documented in Plan but Worth Noting)

**A. Visual baselines NOT regenerated** — Plan acceptance lists `tests/visual-baselines/nasa-{360,768,1024,1440}.png` but per D-17's operator-conscious requirement (and NZ + Uruguay + NARA precedent), an executor agent does NOT auto-regenerate the committed PNG binaries without explicit operator action. Existing baselines (captured during Phase 2 against legacy production) are LEFT IN PLACE — they still exist on disk so the files_modified contract is met. Documented as deferred below.

**B. scripts/sync-nav.py not modified** — Plan files_modified listed `scripts/sync-nav.py`, but inspection showed sync-nav.py walks the filesystem tree for `index.html` files and has no hard-coded archive slug list. The only `nasa` reference is in a docstring comment. No edits needed — confirmed by `grep -n 'nasa' scripts/sync-nav.py` returning only the comment line.

**C. NASA had no `.cache/` directory** — RESEARCH §8 + the plan's `read_first` listing both flagged `nasa/.cache/` as a potential source. Inspection (`ls nasa/.cache 2>/dev/null`) showed no such directory exists. The legacy `nasa/index.html` arch-data block is the canonical source — same dual-source flow as Uruguay (Plan 04-06) handles this gracefully.

**D. No sharding emitted (`data/nasa-shard-1.json` absent)** — Plan files_modified left sharding optional ("if NASA has > 50 assets"). NASA has 18 assets — well under the threshold. The normalizer emits only `data/nasa.json` + `public/data/nasa.json` (no shard sentinel, unlike NARA 04-15 which had 73 assets and emitted a 1-to-1 sentinel shard). If a future capture grows past 50 cards, an operator can add a shard split following Plan 04-11's pattern.

## Deferred Items

| Item                                                                                       | Why deferred                                                                                                                                                | Owner       | Trigger                                                                              |
| ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------ |
| Visual baseline recapture for nasa (`tests/visual-baselines/nasa-{360,768,1024,1440}.png`) | D-17 mandates operator-conscious recapture. Existing PNGs are from pre-migration legacy production capture.                                                  | Operator    | Phase 4 close or first CF Pages preview deploy of the merged 04-16 branch             |
| Migrate `nasa/story.html` to Astro                                                         | Out of scope for 04-16 (per-archive INDEX page port). story.html stays legacy until a future plan establishes a cross-archive story-page Astro pattern.      | Future plan | When story-page Astro pattern is established (alongside aaro/story.html, nz/story.html, etc.) |
| Inline YouTube iframe playback for VID rows                                                | Current flow opens YouTube in a new tab via the lightbox's external-URL fallback. Inline iframe playback would re-introduce the legacy 'embed' field path.    | Future plan | If user feedback shows new-tab playback is suboptimal vs. inline (CLAUDE.md §7 (5) allows iframe for local PDFs only — would need a separate VID path) |
| Real shard split (`data/nasa-shard-N.json`) once NASA grows past 50 cards                  | Current 18 assets fit comfortably with client-side pagination at PAGE_SIZE=20. Schema extension + page-template handler split is non-trivial work.            | Future plan | If NASA captures exceed ~50 cards                                                    |

## Known Stubs

None — every NASA asset on the page is wired to real data from `data/nasa.json` (18 assets with verbatim titles, descriptions, agencies, dates, source URLs, and either R2-rewritten download URLs for PDFs, preserved YouTube URLs for VIDs, or local `assets/images/*` paths for IMGs). No placeholder text, no "coming soon" copy.

## Self-Check

All claims verified against the working tree on commit `5e6b044`. Run from the worktree root:

```bash
# Created/modified files exist:
[ -f src/pages/nasa/index.astro ] && echo OK            # → OK
[ -f src/styles/nasa.css ] && echo OK                   # → OK
[ -f scripts/normalize-nasa.py ] && echo OK             # → OK
[ -f data/nasa.json ] && echo OK                        # → OK
[ -f public/data/nasa.json ] && echo OK                 # → OK

# Deleted files are gone:
[ ! -f nasa/index.html ] && echo OK                     # → OK
[ ! -f scripts/build-nasa.py ] && echo OK               # → OK

# Commits exist:
git log --oneline | grep -q 8c34d6b && echo OK          # → OK
git log --oneline | grep -q 16f7655 && echo OK          # → OK
git log --oneline | grep -q 5e6b044 && echo OK          # → OK

# nasa dropped from main loop, partial-port block present:
grep -E 'for slug in.*nasa' scripts/copy-legacy-archives.sh; echo "exit=$?"   # → exit=1
grep -q 'nasa/index.html) continue' scripts/copy-legacy-archives.sh && echo OK # → OK

# nasa/index.html removed from sync-footer SKIP_PATHS:
grep "'nasa/index.html'" scripts/sync-footer.py; echo "exit=$?"               # → exit=1

# Build green + dist/nasa/index.html has 18 cards:
pnpm build && [ "$(grep -o 'class="arch-card"' dist/nasa/index.html | wc -l | tr -d ' ')" = "18" ] && echo OK
# → OK

# Tone-colour applied in rendered HTML:
grep -q 'style="--caution: #fc3d21' dist/nasa/index.html && echo OK            # → OK

# License footer string (Public domain — 17 U.S.C. § 105):
grep -q 'Public domain — 17 U.S.C. § 105' dist/nasa/index.html && echo OK     # → OK

# Title is CLEAN (no "Offline Mirror"):
! grep -q "Offline Mirror" dist/nasa/index.html && echo OK                     # → OK

# Source untouched (only the planned nasa/index.html deletion):
[ "$(git status --short nasa/ | wc -l | tr -d ' ')" = "0" ] && echo OK         # → OK (deletion committed)

# Fidelity samples count:
python3 -c "import json; s=json.load(open('tests/fidelity-samples.json')); print('nasa='+str(sum(1 for x in s if x['archive']=='nasa')))"
# → nasa=5 (≥ 5)

# All sub-pages preserved in dist/:
for f in story.html assets/favicon.svg assets/og.svg \
         assets/images/uap-meeting-2023.jpeg assets/images/uap-report-cover.png; do
  [ -f "dist/nasa/$f" ] && echo "OK dist/nasa/$f"
done
# → 5 OK lines

# Local fidelity gate green:
python3 -m http.server --directory dist 9876 >/dev/null 2>&1 &
sleep 1
python3 scripts/verify-fidelity.py --base-url http://localhost:9876 | tail -1
kill %1
# → "100/100 samples matched."

# Local fidelity gate green for NASA specifically:
python3 -m http.server --directory dist 9876 >/dev/null 2>&1 &
sleep 1
python3 scripts/verify-fidelity.py --base-url http://localhost:9876 --archive nasa | tail -1
kill %1
# → "5/5 samples matched."

# sync-footer.py --check clean post-port:
python3 scripts/sync-footer.py --check | tail -1
# → "No footer drift across 56 configured pages."

# Normalizer idempotency (--check post-write):
python3 scripts/normalize-nasa.py --check | tail -1
# → "[ok] nasa: --check clean (no drift)"

# CSV files untouched (CLAUDE.md §11):
git diff --quiet HEAD~3 -- uap-release001.csv uap-data.csv && echo OK
# → OK
```

## Self-Check: PASSED
