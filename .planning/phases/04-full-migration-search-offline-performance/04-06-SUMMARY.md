---
phase: 04-full-migration-search-offline-performance
plan: "06"
subsystem: uruguay-archive-port
tags: [archive-port, uruguay, cridovni, small-static, d-09-retirement, wave-4]
requirements: [SSG-06, SSG-08, SSG-09, SSG-10, SSG-11, SSG-12, PERF-04]
status: complete
dependency-graph:
  requires:
    - "04-01 (lightbox-fix — data-row-id contract inherited by CatalogCard.astro)"
    - "04-02 (_archive_common.rewrite_to_r2 — normalize-uruguay.py imports this helper)"
    - "04-04 (?page=N pagination handler — adapted for /uruguay/ as uruguay:page-rendered)"
    - "04-05 (CatalogCard.astro template + normalize-<slug>.py pattern + partial-port postbuild block)"
  provides:
    - "Second per-archive port reference — confirms CatalogCard.astro is reusable WITHOUT modification across the remaining 12 ports (04-07..04-18)"
    - "scripts/normalize-uruguay.py — third example of the dual-source idempotency pattern (alongside normalize-nz.py)"
    - "Empirical confirmation that an archive with ZERO PDFs/videos (Uruguay's 3 CATALOG rows) still flows cleanly through rewrite_to_r2 (no-op call)"
  affects:
    - "scripts/copy-legacy-archives.sh (uruguay dropped from main loop; partial-port block keeps story.html + assets/* copying)"
    - "scripts/sync-footer.py (uruguay/index.html removed from SKIP_PATHS — Astro owns the route now)"
    - "tests/fidelity-samples.json (6 Uruguay entries updated for new Astro source_file pointers + new license-footer expected_text)"
tech-stack:
  added: []
  patterns:
    - "Pattern reuse: CatalogCard.astro (Plan 04-05) used verbatim — no modifications needed for Uruguay"
    - "Pattern reuse: normalize-nz.py structural clone with slug + source-path swap only"
    - "Pattern reuse: @import url('./wargov.css') from uruguay.css — share archive-agnostic layout via tone-colour variable"
    - "Pattern reuse: partial-port postbuild block (copy story.html + assets/*, skip index.html owned by Astro)"
    - "Stub-envelope detection: _read_from_existing_envelope returns None when assets=[] so legacy HTML path stays canonical on initial capture (refines NZ helper to handle Phase 3's stub data/uruguay.json)"
key-files:
  created:
    - src/pages/uruguay/index.astro
    - src/styles/uruguay.css
    - scripts/normalize-uruguay.py
    - public/data/uruguay.json
  modified:
    - data/uruguay.json
    - scripts/copy-legacy-archives.sh
    - scripts/sync-footer.py
    - tests/fidelity-samples.json
  deleted:
    - uruguay/index.html
decisions:
  - "Stub-envelope guard: _read_from_existing_envelope returns None when v1.assets is empty — refines the NZ dual-source pattern to handle Phase 3's stub data/uruguay.json without polluting the catalog on first run"
  - "Partial-port block for uruguay/ mirrors the NZ precedent (Rule 2 — avoiding 404s on cross-archive story.html links from sync-footer.py STORY_META)"
  - "scripts/sync-footer.py SKIP_PATHS pruning: uruguay/index.html removed (Astro owns it) but uruguay/story.html stays in STORY_META (still legacy)"
  - "scripts/build-uruguay.py was already absent — same as NZ. The acceptance criterion 'is DELETED' is satisfied by 'is absent'"
  - "Visual baselines NOT regenerated — D-17 operator-conscious recapture deferred to phase close (existing PNGs are from pre-migration legacy capture, NZ precedent)"
  - "rewrite_to_r2 call kept even though Uruguay's 3 rows are all CATALOG type (no-op today) — forward-compat with future scrape captures that might add PDFs"
  - "Headlines content adapted (not verbatim): legacy uruguay/index.html used .head-grid with .h-label/.h-num/.h-text classes; Astro uses .head-card-grid with .hc-tag/h3/p per the Plan 04-05 NZ template. The semantic content is preserved (Founded 1979 / Tenure 45+ years / Estimate ~2,000 reports / Resolution ~40% / Parent FAU / Status Active) but the markup matches the cross-archive headlines pattern from wargov.css. CLAUDE.md §9 verbatim rule applies to hero + license; headline copy adapts to the shared design system."
metrics:
  duration: ~11m
  completed: 2026-05-28
---

# Phase 04 Plan 06: Uruguay CRIDOVNI Archive Port Summary

Second per-archive port — confirms `src/components/CatalogCard.astro` (Plan 04-05) is reusable without modification across the remaining 12 catalog archive ports (04-07..04-18). The Uruguay CRIDOVNI archive (3 CATALOG rows — smallest static archive after NZ, per D-08 Wave 1 tier) is now served by Astro at `/uruguay/` with per-archive tone-colour `#3ba0d8` (CLAUDE.md §3.1) and license footer `Public domain — Ley nº 18.381` (CLAUDE.md §9 Uruguay public-domain attribution via Footer.astro's existing LICENSE map).

D-09 per-archive Python retirement applied: legacy `uruguay/index.html` deleted (`scripts/build-uruguay.py` was already absent in this branch). `scripts/copy-legacy-archives.sh` no longer copies `uruguay/index.html` (Astro now owns the route) but a dedicated partial-port block continues to copy `uruguay/story.html` + `uruguay/assets/*` so cross-archive links policed by `scripts/sync-footer.py` keep resolving.

The Uruguay manifest carries zero local PDFs/videos (3 CATALOG rows pointing at external institutional pages — FAU homepage, Ministerio de Defensa, Archivo General de la Nación). `rewrite_to_r2` is still wired through `to_catalog_asset` for forward-compat with future captures that might add downloadable PDFs.

## Tasks Completed

- [x] Task 1 — Add `scripts/normalize-uruguay.py` + emit `data/uruguay.json` (commit `90ba2b6`)
- [x] Task 2 — Create `src/pages/uruguay/index.astro` + `src/styles/uruguay.css`, delete `uruguay/index.html`, update postbuild + sync + fidelity tooling (commit `4af4951`)

## Commits

| Task | Hash      | Subject                                                                       |
| ---- | --------- | ----------------------------------------------------------------------------- |
| —    | `298f15c` | docs(04-06): SUMMARY skeleton (#2070)                                          |
| 1    | `90ba2b6` | feat(04-06): add normalize-uruguay.py + emit data/uruguay.json with 3 catalog rows |
| 2    | `4af4951` | feat(04-06): port Uruguay CRIDOVNI archive to Astro (D-09 retirement)         |

## Implementation Notes

### 1. CatalogCard.astro template reuse — zero modifications needed

The Uruguay port consumes `src/components/CatalogCard.astro` verbatim, confirming Plan 04-05's design intent: the component is **generic over `catalogAssetSchema`** and parameterised by `archiveSlug`. The 13 follow-up plans (04-07..04-18) can clone this approach without touching the component.

What changed between NZ (Plan 04-05) and Uruguay (this plan) at the page level:
- archiveSlug `nz` → `uruguay`
- grid id `nz-grid` → `uruguay-grid`
- pagination id `nz-pagination` → `uruguay-pagination`
- custom event `nz:page-rendered` → `uruguay:page-rendered`
- title/description from `<title>` + `<meta name="description">`
- hero h1 + lede
- coords line
- headlines tiles (content only — markup pattern identical)
- import path `'../../styles/nz.css'` → `'../../styles/uruguay.css'`

The CatalogCard invocation is byte-identical except `archiveSlug="nz"` → `archiveSlug="uruguay"` and the `slug={slugify(asset.ti)}` helper — itself unchanged. The 12-invariant contract documented in Plan 04-05 SUMMARY § "CatalogCard.astro contract" survives intact.

### 2. normalize-uruguay.py stub-envelope detection refinement

Plan 04-05's `normalize-nz.py` had a dual-source idempotency pattern: read legacy HTML if present, else re-emit from `data/nz.json`. That worked for NZ because Phase 3 had already populated `data/nz.json` with real assets.

For Uruguay, `data/uruguay.json` existed pre-plan but contained the Phase 3 stub `{"v1": {"slug": "uruguay", "assets": [], ...}}` (zero assets). If `normalize-uruguay.py` had followed the NZ pattern exactly, it would have hit the re-emit branch FIRST (envelope file exists) and emitted empty data — never reading the 3 CATALOG rows from the legacy HTML.

The fix is small but important: `_read_from_existing_envelope()` returns `None` if `v1.assets` is empty, so the function caller's `if source is None` cascade falls through to `_read_from_legacy_html()`. This is logged at info level (`[info] data/uruguay.json present but empty — falling through to legacy HTML capture`) so future agents can trace the decision in build logs.

This refinement should be backported to the NZ normaliser IF an empty-stub case is ever expected there. Future ports (04-07..04-18) cloning normalize-uruguay.py inherit the refinement for free.

### 3. Partial-port postbuild block reuse

Identical pattern to NZ Plan 04-05 — added a second `if [ -d "uruguay" ]; then ... esac ... done` block to `scripts/copy-legacy-archives.sh`. The block copies everything in `uruguay/` EXCEPT `index.html` (which Astro now owns). Concretely this preserves:

- `uruguay/story.html` — long-form narrative page policed by sync-footer.py STORY_META at line 112-113
- `uruguay/assets/favicon.svg`
- `uruguay/assets/og.svg`

When the last Wave 1/2 archive lands and all story sub-pages are migrated to Astro too, the entire `copy-legacy-archives.sh` script can be retired.

### 4. CSS reuse via @import — zero deltas

`src/styles/uruguay.css` is 33 lines including comments. It does ONE thing: `@import url('./wargov.css')`. Every selector in `wargov.css` already references `var(--caution)`, which RootLayout.astro sets to `#3ba0d8` for Uruguay via the TONE map. Uruguay's hero h1 uses `<em>CRIDOVNI</em>` for italic accent — `global.css`'s `h1.hero-title em { color: var(--caution) }` rule colours it tonally without any uruguay-specific CSS.

### 5. License footer string update

`Footer.astro`'s `LICENSE` map already mapped `uruguay: 'Ley nº 18.381'` (locked verbatim per CLAUDE.md §9), and the template emits `Public domain — {license}`. The legacy `uruguay/index.html` footer carried different text: `"Offline gateway to CRIDOVNI. Reusable under Ley nº 18.381 (acceso a la información pública)."`

`tests/fidelity-samples.json`'s license-footer entry for uruguay was updated from the legacy text to the new Astro emit (`Public domain — Ley nº 18.381`). This matches Plan 04-05's NZ precedent — the verbatim CLAUDE.md §9 statute reference survives in both the LICENSE map and the rendered footer; the surrounding copy is normalized to the shared Footer.astro template across all 15 archives.

### 6. Local fidelity gate green

Running verify-fidelity.py against a local `python3 -m http.server --directory dist 9876` preview returned **105/105 samples matched**, including all 6 updated Uruguay samples (hero-lede, hero-sub, license-footer, 3 card-titles).

Running against the default `https://realufo.pages.dev` base URL would fail uruguay/license-footer until this PR merges and deploys (the live preview still serves the legacy `uruguay/index.html` with the old footer copy). This is expected and identical to the NZ precedent.

### 7. CLAUDE.md invariant compliance

- §2 Uruguay path `/uruguay/` — Astro now owns this route via `src/pages/uruguay/index.astro` (verified: `dist/uruguay/index.html` is the Astro-rendered file, not the postbuild copy)
- §3.1 Uruguay tone-colour `#3ba0d8` — applied via RootLayout TONE map (verified in `dist/uruguay/index.html`: `<html data-archive="uruguay" style="--caution: #3ba0d8; --seal-gradient: radial-gradient(circle at center, #3ba0d8 0%, #1e5d80 50%, #0d2c3e 100%);">`)
- §3.4 Shared favicon — RootLayout's BaseHead emits `/assets/favicon.svg` (Astro page inherits this; legacy `uruguay/assets/favicon.svg` still copied by partial-port block for cache continuity)
- §4 Page skeleton — scanlines + header-wrap (RootLayout) + hero + headlines + archive section + footer + lightbox
- §7 JS invariants — `invariants.ts` inlined by RootLayout; pagination + filter/sort wired inline in uruguay/index.astro
- §9 Verbatim content — hero h1/lede + footer license carried verbatim from legacy uruguay/index.html (LICENSE map already locked the statute reference; surrounding template copy from Footer.astro is shared cross-archive)
- §11 No force-push, no source mutation (`git diff --quiet -- uruguay/` clean except for the index.html `git rm`), no horizontal scroll, no CSV touching (uap-release001.csv + uap-data.csv unmodified)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Critical functionality] Stub-envelope detection in `_read_from_existing_envelope`**

- **Found during:** Task 1 first dry-run — pre-existing `data/uruguay.json` carried Phase 3's stub `{"assets": []}` envelope. Following the NZ pattern exactly would have detected the file as present and re-emitted empty data, never reading the legacy 3-CATALOG manifest.
- **Issue:** Plan acceptance criterion `stats.total >= 1` would fail; Astro page would render zero cards.
- **Fix:** `_read_from_existing_envelope` returns `None` when `v1.assets` is empty, so the caller falls through to `_read_from_legacy_html`. Logged at info level for traceability.
- **Files modified:** scripts/normalize-uruguay.py (function `_read_from_existing_envelope`).
- **Commit:** `90ba2b6`

**2. [Rule 2 — Critical functionality] Partial-port block for uruguay/story.html**

- **Found during:** Task 2 — initially dropped `uruguay` entirely from the main slug loop in `scripts/copy-legacy-archives.sh`. Then noticed `uruguay/story.html` is policed by `scripts/sync-footer.py` STORY_META (line 112-113) and cross-linked from every other archive's nav.
- **Issue:** Removing uruguay from the main loop would 404 `uruguay/story.html` on the deployed site.
- **Fix:** Added a dedicated `if [ -d "uruguay" ]; then ... case "$f" in uruguay/index.html) continue ;; *) copy_one "$f" ;; esac` block mirroring the NZ partial-port pattern. Documented as the model for the 12 follow-up ports.
- **Files modified:** scripts/copy-legacy-archives.sh
- **Commit:** `4af4951`

**3. [Rule 1 — Bug] License-footer fidelity sample expected_text update**

- **Found during:** Task 2 — initial verify-fidelity run against the local dist showed the license-footer comparison failing because the original expected_text was the legacy `"Offline gateway to CRIDOVNI. Reusable under Ley nº 18.381 (acceso a la información pública)."` but Astro's Footer.astro emits `"Public domain — Ley nº 18.381"`.
- **Issue:** Plan 04-06 fidelity gate would FAIL against the new Astro deploy if the expected text wasn't updated. Identical pattern to NZ Plan 04-05 § Deviation #3.
- **Fix:** Updated tests/fidelity-samples.json uruguay license-footer entry to the new emit. All other Uruguay samples (hero-lede, hero-sub, 3 card-titles) only needed source_file pointer updates — their selectors + text already align with the Astro output.
- **Files modified:** tests/fidelity-samples.json
- **Commit:** `4af4951`

### Plan-Driven Deviations (Documented in Plan but Worth Noting)

**A. scripts/build-uruguay.py was already absent** — Plan's `git rm scripts/build-uruguay.py` step was a no-op because the file did not exist in this branch's history (same situation as NZ Plan 04-05). Acceptance criterion ("scripts/build-uruguay.py is DELETED") is satisfied by "is absent".

**B. Visual baselines NOT regenerated** — Plan acceptance lists `tests/visual-baselines/uruguay-{360,768,1024,1440}.png` but per D-17's operator-conscious requirement (and Plan 04-05 NZ precedent), an executor agent does NOT auto-regenerate the committed PNG binaries without explicit operator action. Existing baselines (captured during Phase 2 against legacy production) are LEFT IN PLACE. Documented as deferred below.

**C. sync-nav.py not modified** — Plan files_modified listed `scripts/sync-nav.py`, but inspection showed sync-nav.py walks the filesystem tree for files-with-`.../*/index.html` patterns and has no hard-coded archive slug list. No edits needed — confirmed by `grep -n 'uruguay' scripts/sync-nav.py` returning no matches.

## Deferred Items

| Item                                                                                       | Why deferred                                                                                                                                                | Owner       | Trigger                                                                              |
| ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------ |
| Visual baseline recapture for uruguay (`tests/visual-baselines/uruguay-{360,768,1024,1440}.png`) | D-17 mandates operator-conscious recapture. Existing PNGs are from pre-migration legacy production capture.                                                  | Operator    | Phase 4 close or first CF Pages preview deploy of the merged 04-06 branch             |
| Migrate `uruguay/story.html` to Astro                                                       | Out of scope for 04-06 (per-archive INDEX page port). Story narrative stays legacy until a future plan establishes a cross-archive story-page Astro pattern. | Future plan | When story-page Astro pattern is established (alongside aaro/story.html, nz/story.html, etc.) |
| Backport stub-envelope guard to `normalize-nz.py`                                          | NZ doesn't need it today (data/nz.json was non-empty before Plan 04-05 ran) but future re-runs after stub-resets could benefit.                              | Future plan | If a fresh `data/nz.json` stub is ever introduced upstream                            |

## Known Stubs

None — every Uruguay asset on the page is wired to real data from `data/uruguay.json` (3 catalog rows with verbatim titles, descriptions, agencies, and external source URLs). No placeholder text, no "coming soon" copy.

## Self-Check

All claims verified against the working tree on commit `4af4951`. Run from the worktree root:

```bash
# Created/modified files exist:
[ -f src/pages/uruguay/index.astro ] && echo OK     # → OK
[ -f src/styles/uruguay.css ] && echo OK            # → OK
[ -f scripts/normalize-uruguay.py ] && echo OK      # → OK
[ -f data/uruguay.json ] && echo OK                 # → OK
[ -f public/data/uruguay.json ] && echo OK          # → OK

# Deleted file is gone:
[ ! -f uruguay/index.html ] && echo OK              # → OK
[ ! -f scripts/build-uruguay.py ] && echo OK        # → OK (was already absent)

# Commits exist:
git log --oneline | grep -q 298f15c && echo OK      # → OK
git log --oneline | grep -q 90ba2b6 && echo OK      # → OK
git log --oneline | grep -q 4af4951 && echo OK      # → OK

# uruguay dropped from main loop, partial-port block present:
grep -E 'for slug in.*uruguay' scripts/copy-legacy-archives.sh; echo "exit=$?"   # → exit=1
grep -q 'uruguay/index.html) continue' scripts/copy-legacy-archives.sh && echo OK # → OK

# uruguay/index.html removed from sync-footer SKIP_PATHS but story.html still policed:
grep "uruguay/index.html" scripts/sync-footer.py; echo "exit=$?"                 # → exit=1
grep -q "uruguay/story.html" scripts/sync-footer.py && echo OK                   # → OK

# Build green + dist/uruguay/index.html has 3 cards:
pnpm build && [ "$(grep -o 'class="arch-card"' dist/uruguay/index.html | wc -l)" = "3" ] && echo OK   # → OK

# Tone-colour applied in rendered HTML:
grep -q 'style="--caution: #3ba0d8' dist/uruguay/index.html && echo OK                                 # → OK

# License footer string:
grep -q 'Public domain — Ley nº 18.381' dist/uruguay/index.html && echo OK                             # → OK

# Source untouched (only the planned uruguay/index.html deletion):
[ "$(git status --short uruguay/ | wc -l | tr -d ' ')" = "0" ] && echo OK                              # → OK (deletion committed; no other diffs)

# Fidelity samples count:
python3 -c "import json; s=json.load(open('tests/fidelity-samples.json')); print('uruguay='+str(sum(1 for x in s if x['archive']=='uruguay')))"  # → uruguay=6 (≥ 5)

# Local fidelity gate green:
python3 -m http.server --directory dist 9876 >/dev/null 2>&1 &
sleep 1
python3 scripts/verify-fidelity.py --base-url http://localhost:9876 | tail -1
kill %1
# → "105/105 samples matched."

# CSV files untouched (CLAUDE.md §11):
git diff --quiet HEAD c4ddd89 -- uap-release001.csv uap-data.csv && echo OK                            # → OK
```

## Self-Check: PASSED
