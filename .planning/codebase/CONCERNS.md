# Codebase Concerns

**Analysis Date:** 2026-05-25

> Strategic question this report informs: *should the project move to a frontend
> framework as it grows, keep offline capability, and gain optional scrape →
> release upload automation?* The concerns below are ordered to make that call.

---

## Scalability Ceilings of the Plain-HTML Approach

**Per-page bundle weight is already large and unbounded:**
- `index.html` — **479 KB** (2,237 lines), embeds full Release 01 + Release 02 manifest inline as `<script id="archive-manifest">`
- `geipan/index.html` — **3.3 MB** (largest page in the repo), all 3,000+ GEIPAN case rows inlined as JSON
- `uk/index.html` — **512 KB**
- `aaro/details.html` — **156 KB** (1,156 lines)
- `aaro/index.html` — **120 KB** (1,313 lines)
- `chile/index.html` — **100 KB**
- `search.html` — **72 KB**, fetches `/api/all.json` (4.6 MB) once on load (recent perf win, commit 7294b29)

**Impact:** Mobile users on slow 3G pay the full inlined manifest on every per-archive page visit. The 3.3 MB GEIPAN page already requires a bespoke paginator (`#pagination` sentinel in `scripts/templates/archive.py:38`) to avoid a 3000-node initial paint. The pattern does not generalise: every future archive with >500 records will need a one-off paginator or a similar bail-out.

**Per-page inline JS duplication:** The same lightbox/archive renderer is inlined into ~15 archive pages plus search/timeline/map. `scripts/templates/lightbox.py` (211 lines) and `scripts/templates/archive.py` (154 lines) get duplicated into every output HTML at build time — recent commits 4fe2134, c823efb, 0c36c7f extracted `LIGHTBOX_JS` and `ARCHIVE_JS` precisely to *delete ~250 lines of duplicated inline JS*. The refactor is partial: `build-wargov.py`, `build-aaro.py`, `build-nasa.py`, `build-nara.py` still each carry their own `innerHTML` writers (counts: 0, 11, 6, 3 — wargov has its own pattern).

**Manual nav sync across 15+ archives:** `scripts/sync-nav.py` (194 lines) and `scripts/sync-footer.py` (171 lines) exist solely to push canonical nav/footer HTML into every page. Two dedicated CI workflows (`.github/workflows/sync-nav.yml`, `sync-footer.yml`) act as drift gates because the cost of nav drift across 30+ HTML files is real. Adding archive #16 requires touching:
- `scripts/sync.sh` (interactive picker case statement, lines 73–122)
- `scripts/_site_template.py` re-exports → `scripts/templates/nav.py` (PINNED, SITE_PAGES)
- A new `scripts/dl-<slug>.sh`
- A new `scripts/build-<slug>.py` OR an entry in `scripts/build_batch3.py` CONFIG (already 762 lines, 7 countries)
- 15 footers (auto), 15 nav strips (auto)
- `sw.js` shell list if the archive ships utility pages

**Cognitive load curve:** `scripts/` already contains **18 build-*.py**, **7 scrape-*.py**, **7 dl-*.sh**, plus shared/template modules. `build-aaro.py` alone is 1,360 lines. The codebase has visibly bowed toward extraction (templates/ split started in commits fcaf9bc, 33ea247, 0c36c7f, c823efb, 4fe2134) and the trajectory is the standard pre-framework refactor curve.

**Files / evidence:**
- `index.html`, `geipan/index.html`, `uk/index.html`
- `scripts/build-aaro.py`, `scripts/build_batch3.py`, `scripts/build-wargov.py`
- `scripts/templates/archive.py:38` (paginator bail-out)
- `scripts/templates/shared.py`, `scripts/templates/lightbox.py`, `scripts/templates/nav.py`
- `.github/workflows/sync-nav.yml`, `.github/workflows/sync-footer.yml`

**Fix approach (strategic):** A framework move is justifiable *only* if it keeps offline-first intact. Recommended path is a static-export framework (Astro, Eleventy, or Next.js `output: 'export'`) that:
1. Replaces inline-JSON-in-HTML with a single `/api/all.json` (already exists, 4.6 MB) fetched + cached by the service worker.
2. Pre-renders per-archive shells (preserving HTML-first / no-JS-render-blocking guarantee).
3. Reuses existing `templates/*.py` logic via a Python pre-step that emits MDX/Markdown frontmatter, or migrates the templating to JS once.
4. Leaves `bundles/`, `sw.js`, GitHub Releases as the binary CDN exactly as today.

The cost is real (rewrite 18 build scripts) but the alternative — adding a 16th archive — will likely require another paginator one-off and another nav-drift gate. The slope is steep.

---

## Offline-First Fragility

### Service Worker Registered on Only 12 of ~32 Pages

**Critical gap:** `sw.js` is registered ONLY on the 12 top-level utility pages:
- ✓ Registered: `index.html`, `search.html`, `timeline.html`, `map.html`, `about.html`, `donate.html`, `glossary.html`, `stats.html`, `foia.html`, `compare.html`, `whatsnew.html`, `404.html`, and a handful of story pages (`nara/*.html`, `brazil/*.html`, `nz/story.html`)
- ✗ **NOT registered: every per-archive `index.html`** — `aaro/`, `nasa/`, `nara/`, `geipan/`, `uk/`, `brazil/`, `chile/`, `italy/`, `nz/`, `argentina/`, `canada/`, `peru/`, `spain/`, `uruguay/`

**Impact:** A user visiting `/aaro/` first will never install the service worker. Subsequent offline access to *any* page (including pages that would register the SW) fails until they happen to land on a root-level utility page. The "offline by default" promise of CLAUDE.md §1.3 is structurally broken for first-time visitors to archive subpages.

**Verify:**
```bash
grep -c "serviceWorker" aaro/index.html nasa/index.html nara/index.html
# → all zero
```

**Files:** Every `<slug>/index.html`. The fix lives in `scripts/templates/head.py` — emit the SW registration snippet from `make_head()` so it lands in every page the templates produce.

**Fix approach:** Add a single line to `templates/head.py:make_head()` returning the same `<script>if("serviceWorker" in navigator)…</script>` block already used on root pages. Re-run every `build-*.py`. Add a sync-script (`scripts/sync-sw-registration.py`) similar to `sync-footer.py` and a drift gate workflow.

### Shell Precache Excludes Every Archive Index

`sw.js` SHELL list (lines 23–40) caches `/`, `/search.html`, `/timeline.html`, `/map.html`, the seven utility pages, leaflet vendor, and the favicon — **but not** `/aaro/`, `/nasa/`, `/nara/`, `/geipan/`, etc. Offline navigation to an archive root that the user hasn't visited online first will fall through to `/404.html` (see `sw.js:87`).

**File:** `sw.js:23-40` (SHELL constant).

**Fix:** Add every archive root to SHELL. Cost: ~600 bytes precache delta. Trivial.

### Recent SW Bug Pattern Indicates Cache Strategy Is Still Settling

Three of the last 30 commits touched offline behaviour:
- `dcbc0d7` — fix(sw): don't cache 404/non-2xx navigation responses (had been serving stale 404s after deploys)
- `f3de6b9` — fix: service worker — bump version, expand SHELL, auto-stamp on deploy
- `25cd124` — perf+a11y: timeline /api/all.json fast-path, CLS reservations

The `extract-pdf-text.py` workflow generates `**/.pdftext/*.txt` (`extract-pdf-text.py:50`) and the `api/all.json` is **4.6 MB**. Stale-while-revalidate on a 4.6 MB JSON over a hostile network is functional but heavy; users will refetch the whole blob whenever the timestamp shifts.

**Fix approach:** Split `api/all.json` into per-archive shards (which `by-archive.json` already conceptually has — but it's also 4.6 MB, suggesting it's the same data re-keyed). Cache them independently. Versions can be ETag-based per shard.

---

## Scraping Pipeline Fragility

### Hardcoded UA String Repeated Across Every Downloader

The same realistic Chrome UA literal is repeated 8 times across `scripts/dl-*.sh` and `scripts/scrape-*.py`:

```
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36
```

**Files:** `scripts/dl-chile.sh:6`, `dl-aaro.sh:21`, `dl-uk.sh:14`, `dl-nara.sh:15`, `dl-geipan.sh:12`, `dl-nasa.sh:15`, `scripts/scrape-geipan.py:20`, `scrape-brazil.py:18`, `scrape-chile.py:18`.

**Impact:** Chrome 131 will start to look anomalous to bot-detectors as Chrome ships 140+. Bumping requires touching 8 files. Akamai-fronted hosts (war.gov, some DoD) need `curl_cffi` (`.github/workflows/scrape.yml:27`) — and this is installed with `|| true`, so a failed install silently falls back to plain curl, which will quietly 403 on Akamai sites and the rebuild won't notice until pages go stale.

**Fix:** Centralise UA + curl flags in `scripts/_http.sh` (sourced from every dl-*.sh) and `scripts/_http.py` (imported from every scrape-*.py).

### Wayback Fallback Is Single-Snapshot, Hardcoded Year

`scrape-chile.py:88`, `scrape-brazil.py:78`, `scrape-uk.py:121` all hardcode:
```python
'https://web.archive.org/web/2024id_/' + url
```

`scrape-aaro.py:55` hardcodes `2025id_/`. The Wayback CDX-driven fallback in `dl-aaro.sh:45` is the only one that queries for the best snapshot dynamically.

**Impact:** As source sites change URLs, the 2024 / 2025 snapshots will increasingly fail to exist for newly-discovered URLs. No alarming yet — these are tolerant fallbacks (`|| true` in the workflow at `.github/workflows/scrape.yml:31-38`).

**Fix:** Promote the CDX-API pattern from `dl-aaro.sh:45` into a shared helper used by every scraper.

### Every Scraper Step in CI is `|| true`

`.github/workflows/scrape.yml` runs every scraper and every build step with `|| true` (lines 31-48, 67-98). The pipeline cannot ever fail. Combined with `git push origin main || true` at the end, a fully broken weekly run still completes "successfully" — drift is invisible until a user notices a stale page.

**Mitigation:** `scripts/check-sources.py` runs at line 98 and produces `dead-links.json`/`dead-links.md`, but those land alongside the broken data, not as a CI red.

**Fix:** Aggregate scraper successes/failures into a single summary that fails the workflow if >N sources broke, but allows transient single-host failures. Slack/issue-create on hard failure.

### `download.py` Path Mismatch in `sync.sh`

`scripts/sync.sh:144` calls `python3 "$ROOT/download.py"` but the file is at `$ROOT/scripts/download-war.gov.py`. There is **no** `download.py` at repo root.

**Impact:** Running `./scripts/sync.sh --wargov-only` (or any path that reaches the war.gov stage) fails with `python3: can't open file '.../download.py'`. The wargov download step is broken at the entrypoint.

**File:** `scripts/sync.sh:144`.

**Fix:** Change to `python3 "$ROOT/scripts/download-war.gov.py"`.

---

## Release-Upload Pipeline Gaps

### Release Upload Is Manual / Local-Only

The pipeline you described — "scrape the latest release and download to local optionally and upload to GitHub release for online viewing" — is **partly** implemented:

- ✓ Scrape exists: `scripts/scrape-*.py`, weekly via `scrape.yml` workflow
- ✓ Download exists: `scripts/dl-*.sh`, `scripts/sync.sh --all`
- ✓ Local rebuild exists: `scripts/update_all.sh` chains all of it
- ⚠ **Release upload runs only from `update_all.sh` (local, requires `gh` CLI)** — `scripts/update_all.sh:45-63`
- ✗ **No CI step uploads new binaries to GitHub Releases** — `.github/workflows/scrape.yml` runs the scrapers and rebuilds HTML, but never calls `gh release upload`

**Files:** `scripts/update_all.sh:44-63` (local-only path); `.github/workflows/scrape.yml` (CI path, no upload step).

**Impact:** Any new mp4 / PDF that lands during the weekly scrape stays only inside the GitHub Actions runner sandbox. The runner doesn't commit binary blobs (they're `.gitignore`d by design — `.gitignore:6-32`). So new sources discovered by the spider produce HTML cards whose `Download` button points at release URLs that **do not exist**.

**Mitigation:** `scripts/backfill-release.py` exists (54 lines), apparently to detect drift and emit a `gh release upload` command — but it's a *suggestion-printer*, not an automation.

**Fix approach (high priority for the strategic question):**
1. Add a CI step to `scrape.yml` after `Run wide spider…` that runs `gh release upload <tag> <new-files> --clobber` using `secrets.GITHUB_TOKEN`. The token is already available; `permissions: contents: write` is already set.
2. The downloader scripts must save new binaries to a known path (`bundles/incoming/` or similar) that the CI step then uploads and prunes.
3. After upload, the script deletes the local file (it's gitignored anyway) so the runner doesn't accumulate state.

### Hardcoded Release Repo Mismatch (Latent Bug)

`scripts/build-details.py:42` points at:
```
https://github.com/hectorchanht/gov-ufo-archive/releases/download/pdfs-v1/
```
Every other script uses `hectorchanht/war-gov-ufo-release`. The `gov-ufo-archive` repo name appears to be a typo/legacy reference and will produce 404 download links from AARO detail pages.

**File:** `scripts/build-details.py:42`.

**Fix:** Change to `hectorchanht/war-gov-ufo-release`.

### Hardcoded Asset Lists Don't Auto-Discover

`scripts/build-wargov.py:70-78` hardcodes the 28 Release 01 DVIDS IDs. Release 02 IDs are loaded from JSON (`dvids2dod-r02.json`). If War.gov publishes Release 03 with a new bundle, a human must:
1. Run `scripts/resolve-dvids-r01.py`-style resolver against the new DVIDS Video IDs
2. Hand-edit `dvids2dod-r03.json` or `EXPECTED_VIDEOS_R03` constant
3. Modify the CSV path constants in `build-wargov.py:27-29` to include the new CSV

**Files:** `scripts/build-wargov.py:70-98`.

**Fix:** Generalise to scan `scripts/dvids2dod-*.json` for all release maps and merge automatically.

---

## CLAUDE.md Spec vs Reality Drift

### Recent Feature Commits Are Consistent with Spec

Audited the last 8 commits against CLAUDE.md rules:
- `915157a` (CSV row metadata for loose videos) — adheres to §4.2 ("substantive context. NEVER filler")
- `a45225e` (rich meta panel) — extends §4.2 card schema; consistent with §4.3 actions
- `dcbc0d7` (SW cache fix) — directly addresses §1.3 offline-by-default goal
- `99b2fda`, `2f67feb` (DVIDS map fixes) — fixes broken Download buttons, consistent with §4.3 "Never show a button that returns HTML (404 page)"
- `34d0461` (Release 02 ingest) — added without rewriting CLAUDE.md to mention Release 02; **CLAUDE.md §5.1 still lists `wargov` tag set as the original R01-only `pdfs-v1`+`videos-v1`** — `wargov-r02-v1` tag now in use but not documented

**Drift:**
- CLAUDE.md §5.1 release-tag table is out of date (missing `wargov-r02-v1`)
- CLAUDE.md §2 source table doesn't note that several countries (Argentina, Italy, Peru, Spain, Uruguay) are now generated by `build_batch3.py` rather than a per-country build script
- CLAUDE.md §6.3 describes `sync.sh` as having `--<slug>-only` flags for "war.gov, AARO, NASA, NARA"; the sync.sh now has flags for all 15 archives — spec lags reality

**Fix:** Update CLAUDE.md §5.1 (release tags), §6.3 (flags), §2 (which archive has its own build script vs batch3) on the next housekeeping commit.

### Anti-Patterns Spec Forbids Are Present (Minor)

CLAUDE.md §11 forbids `crossorigin="anonymous"` on `<video>`. Verified: zero occurrences across all index.html files. ✓

CLAUDE.md §4 requires consistent action buttons; `scripts/templates/archive.py:91-101` implements them correctly.

CLAUDE.md §9 forbids filler descriptions. Could not spot-check 4000+ records, but the build scripts do not inject filler — they pass CSV `Description Blurb` through verbatim.

---

## CSV Source of Truth

### Two CSVs Exist; One Is Authoritative, One Is "Untouchable Legacy"

- `uap-release001.csv` — **194 KB** — the original R01 dump from War.gov. CLAUDE.md §11 declares it untouchable.
- `uap-data.csv` — **298 KB** — combined R01 + R02 dump, fetched from `war.gov/Portals/1/Interactive/2026/UFO/uap-data.csv` (`scripts/download-war.gov.py:136`)

**Consumers:**
- `scripts/build-wargov.py:27-29` — prefers `uap-data.csv`, falls back to `uap-release001.csv` on clean clone
- `scripts/resolve-dvids-r01.py:29` — reads `uap-data.csv`
- `scripts/download-war.gov.py:136-139` — downloads both

**Concern:** Both CSVs are committed (193 KB + 298 KB = ~491 KB of CSV in git). The combined CSV is fetched fresh on every sync — there is no diff/merge logic. If War.gov ever rotates the CSV format, the build silently regenerates a malformed manifest because there's no schema validation.

**Files:** `scripts/build-wargov.py`, `uap-release001.csv`, `uap-data.csv`.

**Fix approach:**
1. Add a header-row check at the top of `build-wargov.py` — fail loudly if CSV columns drift.
2. Consider whether `uap-release001.csv` still needs to be committed (it's a subset of `uap-data.csv` now). Keeping it is harmless but the rule "untouchable" should be re-evaluated.

---

## Security

### No Leaked Secrets in Source

Audited:
- `grep -rn "API_KEY\|SECRET\|TOKEN\|password" scripts/ .github/workflows/` — only legitimate `${{ secrets.GITHUB_TOKEN }}` and `${{ secrets.LHCI_GITHUB_APP_TOKEN }}` references
- No `.env` files present in repo root (`.gitignore` does not currently list `.env*` — see fix below)
- No `*.pem`, `*.key`, credentials files committed

### Missing `.env*` Pattern in `.gitignore`

`.gitignore` does not include `.env`, `.env.*`, `*.pem`, `*.key`. Project does not appear to use env files today, but if a future contributor introduces one, it will be auto-staged.

**File:** `.gitignore`.

**Fix:** Add a "secrets" section to `.gitignore`:
```
.env
.env.*
*.pem
*.key
serviceAccountKey.json
```

### XSS Risk: Verbatim Government-Source HTML Injection

CLAUDE.md §9 says "verbatim official text for hero lede, headlines, FAQ accordion answers." Several JSON files embed already-HTML-formatted content:

- `scripts/_cases.json:993` — case `lede` field contains `<strong>`, `<em>` tags. Built into `aaro/details.html` via `build-details.py`.
- Build scripts emit titles, descriptions, and case content from CSV / JSON straight into HTML.

**Verified escaping:**
- `scripts/templates/archive.py:42` — `esc(s)` properly escapes `& < > " '` on the client side before `innerHTML` (lines 50, 61, 78, 89, 100, 108, 112, 113, 117, 135).
- `scripts/templates/shared.py:374-409` and `templates/lightbox.py:182-187` use `esc()` consistently on user-routed paths.
- `scripts/templates/shared.py:280` (`btn.innerHTML = TAB_MAP[key] + countText;`) — `TAB_MAP[key]` is a build-time constant, `countText` is a number, so safe.

**Latent risk:** When `_cases.json` content is rendered into HTML via Python f-strings server-side in `build-details.py`, the **`<strong>` and `<em>` tags are intentionally preserved** — this is by design (they're already trusted markup). But if a future contributor adds non-trusted CSV content into a similar f-string-rendered field, the trust boundary will quietly break. The build scripts have no clear "this field is trusted markup" vs "this field is user/source text and must be escaped" convention in Python.

**Files:** `scripts/build-details.py`, `scripts/_cases.json`, all `build-*.py`.

**Fix approach:** Adopt a naming convention in build scripts — e.g. fields ending in `_html` are pass-through, all other fields go through `html.escape()` before being f-stringed. Document in CLAUDE.md §9.

### `data-action="open"` + `card.dataset.idx` — Client-Side Trust Boundary

`scripts/templates/archive.py:140-152`:
```js
const a = (window._lb ? window._lb.getList() : [])[parseInt(card.dataset.idx, 10)];
if (a && a.t === 'CATALOG') { window.open(a.u || a.s, '_blank'); }
```

`a.u` and `a.s` are URLs from the build-time manifest (escaped on render). `window.open(escapedHtmlContent, …)` is fine for ordinary URLs but if a malicious source page ever supplied `javascript:` schemes, this would execute. The HTML `esc()` does NOT prevent `javascript:` URL injection (it only escapes `& < > " '`).

**Fix:** Add a URL-scheme allowlist in `esc()` or a separate `escUrl()` that rejects anything not in `https:`, `http:`, `mailto:`, relative paths.

---

## Performance Bottlenecks

### Initial Paint on Large Archives Is JSON-Bound, Not Network-Bound

`geipan/index.html` weighs **3.3 MB** entirely because every case is inlined as JSON in `<script id="arch-data">`. On a 5 Mbps mobile connection, that's a 5-second First-Contentful-Paint delay before JS can render anything. The recent commit 25cd124 ("perf+a11y: timeline /api/all.json fast-path") shows the team has begun moving toward "fetch JSON separately" but only on timeline.html.

**File:** `geipan/index.html`, plus the GEIPAN-specific paginator branch in `scripts/templates/archive.py:38`.

**Fix:** Migrate the GEIPAN page to the same `/api/all.json` fast-path used by `search.html` and `timeline.html` (commit 7294b29).

### `api/all.json` and `api/by-archive.json` Are Both 4.6 MB

These two files together are **9.2 MB**. They appear to contain the same data, just re-keyed:
- `api/all.json` — 4,584,960 bytes (`build-api.py`)
- `api/by-archive.json` — 4,585,111 bytes (151-byte delta = re-keying overhead)

**File:** `scripts/build-api.py`.

**Fix:** Generate `by-archive.json` as a shallow index pointing into a single `all.json`, or split per-archive shards so consumers fetch only what they need.

### Inline JSON in Index.html Defeats SW Stale-While-Revalidate

The benefit of stale-while-revalidate for `/api/*.json` (sw.js:93-106) is **bypassed** for the archive index pages because their manifest is embedded inline in the HTML response — the HTML cache invalidates and refetches the whole manifest on every deploy.

**Fix:** Externalise the manifest to a separate JSON file per archive. Cache the HTML shell + JSON independently.

### Images Lack `loading="lazy"` on the Hero Carousel

`grep` of `index.html` for `<img...src=` returned only one image without `loading="lazy"` — the hero carousel imagery. CLAUDE.md §4 requires hero carousel autoplay, so the first frame must be eager-loaded, but slides 2+ should be lazy.

**File:** `index.html` hero-carousel.

**Fix approach:** Mark all carousel slides except slide 1 as `loading="lazy"`.

---

## Fragile Areas

### `build-aaro.py` — 1,360 Lines, Monolithic

The single largest builder. Contains its own manifest, HTML template, case data, and rendering logic. Recent refactor commits (4fe2134, c823efb) extracted lightbox/archive JS but the file itself remains 1,360 lines including hand-written hero HTML and case data. Changes are diff-noisy and review-risky.

**File:** `scripts/build-aaro.py`.

**Why fragile:** Touching any subsection (hero, headlines, archive, FAQ) requires understanding the file's full structure. A typo in a triple-quoted Python string silently produces broken HTML in `aaro/index.html` (the build doesn't validate output).

**Safe modification:** Use the html-validate workflow (`.github/workflows/html-validate.yml`) as a gate. CI already verifies "0 errors across all own pages" (commit 1c737d6).

**Test coverage:** No unit tests anywhere in the repo. The CI workflows (html-validate, lighthouse, links via lychee) are the only safety net.

### `parse-aaro.py` + `extract-evidence.py` — Run Order Matters, Implicit

`scripts/sync.sh:210-212`:
```bash
python3 "$ROOT/scripts/build-wargov.py"
python3 "$ROOT/scripts/parse-aaro.py"
python3 "$ROOT/scripts/extract-evidence.py"
python3 "$ROOT/scripts/build-aaro.py"
```

`parse-aaro.py` and `extract-evidence.py` produce intermediate state that `build-aaro.py` reads. The dependency is not declared anywhere except this script's ordering. `update_all.sh:68-70` repeats the same ordering. Running build-aaro.py first will silently produce a stale page.

**Fix:** Document the dependency in `build-aaro.py`'s docstring or have `build-aaro.py` invoke the prerequisites itself.

### `scripts/sync.sh` and `update_all.sh` Are 90% Overlapping

Both scripts orchestrate "download → build → done." `sync.sh` adds an interactive picker; `update_all.sh` adds release upload + sitemap + commit + push. They both maintain their own copy of the build-script ordering. A new build step must be added to both.

**Files:** `scripts/sync.sh:206-222`, `scripts/update_all.sh:67-78`.

**Fix:** Extract the build-step list into a single function or array sourced by both.

---

## Scaling Limits

### GitHub Releases Per-Asset / Per-Release Quotas

GitHub Releases have a 2 GB per-file limit and unlimited size per release in practice, but per-tag asset *counts* are not unlimited (~1000 assets per release tag in practice). Current state:
- `pdfs-v1` — 165 PDFs across all archives (CLAUDE.md §5.1)
- `videos-v1` — 60 mp4 files
- `wargov-r02-v1` — Release 02 binaries (count unknown without `gh release view`)

**Fix path:** Per-archive tags (already started: `geipan-v1`, `uk-v1` mentioned in CLAUDE.md §5.1).

### Inline JSON Manifest Hits ~5 MB Hard Wall

Browsers parse inline JSON faster than fetched JSON for moderate sizes, but `<script id="…" type="application/json">` blocks above ~10 MB start to hit V8 string-length / parse-time issues on mobile. `geipan/index.html` is already at 3.3 MB with 3000 records. Adding the UK National Archives full catalog (~70k records) would blow past this ceiling.

**Fix:** Migrate to fetched JSON for any archive with >1000 records.

---

## Dependencies at Risk

### `curl_cffi` — Required for Akamai-Fronted Hosts, Soft-Installed

`.github/workflows/scrape.yml:27`:
```yaml
- name: Install dependencies (curl_cffi for Akamai-fronted hosts)
  run: pip install --upgrade pip && pip install curl_cffi || true
```

The `|| true` means a failed install (e.g. PyPI outage, wheel-build failure on a new Python release) silently downgrades the war.gov downloader from "works on Akamai" to "403 Forbidden." Combined with `python3 scripts/scrape-aaro.py || true`, an Akamai-blocked run looks identical to a successful one in the CI log.

**File:** `.github/workflows/scrape.yml:27`.

**Fix:** Drop the `|| true` from the dependency install. Fail loudly if `curl_cffi` won't install — these are paramount for war.gov access.

### No `requirements.txt` / `pyproject.toml`

`scripts/` uses `curl_cffi` (mentioned in workflow), `subprocess`, `csv`, `json`, `urllib`, plus `lxml` likely. There is no declared Python dependency manifest at the repo root.

**Impact:** A fresh clone + `python3 scripts/sync.sh --all` will fail with `ModuleNotFoundError: curl_cffi` and no clear remediation path. CLAUDE.md §10 step 3 doesn't mention dependency install.

**Fix:** Add `requirements.txt` listing `curl_cffi`, `beautifulsoup4` (if used), any other runtime deps.

---

## Missing Critical Features

### No Automated Diff-and-Notify on Source Drift

The pipeline regenerates HTML from scratch every week. If a source page changes substantively (new file, removed file, renamed catalog), the user is never alerted — they just see different content next time they visit.

**Fix:** `scripts/check-sources.py` already emits `dead-links.json`/`dead-links.md`. Extend it to emit "new files since last run" → could feed `CHANGELOG.md` (commit a098534 added `append-changelog.py` partly for this).

### No Automated "New Release Detected" Trigger

The weekly cron at 06:00 UTC Monday (`.github/workflows/scrape.yml:5`) is the only trigger. Releases that drop mid-week (which Release 02 did, May 22 — commit 34d0461) are 7 days late to surface unless someone runs `workflow_dispatch` manually.

**Fix:** A lightweight daily "fingerprint check" workflow that hits a handful of source-page URLs, computes a content hash, and triggers the full scrape if any source has changed.

---

## Test Coverage Gaps

### Zero Unit Tests Repo-Wide

No `tests/`, `__tests__/`, `test/`, or `*.test.*` directories anywhere in the repo. The build scripts are tested only by:
1. CI HTML validation (`.github/workflows/html-validate.yml`)
2. CI Lighthouse (category-gated, `.github/workflows/lighthouse.yml`)
3. CI link checking (`.github/workflows/links.yml` via lychee)
4. CI nav/footer drift gates (`sync-nav.yml`, `sync-footer.yml`)
5. Manual schema-ish checks in `scripts/validate-manifests.py` (warnings allowed)

**Untested:**
- CSV parsing logic (`build-wargov.py:_load_dvids_map`, ID resolution)
- DVIDS map fallback paths (recent commits 99b2fda, 2f67feb show this is bug-prone)
- Lightbox URL routing (local vs release vs source)
- Service worker cache strategy (just patched in dcbc0d7)
- `git ls-files` vs `os.listdir` fallback (CLAUDE.md §6.2)

**Risk:** Every recent fix commit (37 of the last 88 commits over 30 days = **42% of commits are fixes**) addresses a regression that a unit test would have caught.

**Files:** All `scripts/build-*.py`, `scripts/_*.py`, `scripts/templates/*.py`.

**Priority:** **HIGH.** A 6-fix-commits-per-week rate indicates the lack of tests is now an active cost.

**Fix approach:**
1. Add `tests/test_build_wargov.py` covering: CSV row → JSON manifest entry transformation; DVIDS ID → DOD URL resolution; local-file detection via `git ls-files`.
2. Add `tests/test_sw.py` (Node-based or browser via Playwright) covering: install, fetch handler for 200/404/non-2xx navigation, JSON stale-while-revalidate.
3. Gate `main` on the test suite.

---

## Recent Bug Pattern — Trend Analysis

**Last 30 commits:**
- Fix commits: **37 of 88** (~42%) — based on `git log --grep="fix"`
- Refactor commits extracting inline JS to shared templates: 4 (fcaf9bc, 33ea247, 0c36c7f, c823efb, 4fe2134)
- CI fix commits: 7 (lychee, lighthouse, html-validate, scrape.yml YAML)
- Feat commits adding archive content: ~10
- The pattern is: **add archive → discover an inline-JS/link/CSV/manifest edge case → fix individually**.

**Trend implication for the strategic question:** Each new archive is producing a long tail of edge-case fixes (DVIDS resolution, AUD rows, CSV row metadata, lightbox meta panel). The cost-per-new-archive is rising, not falling, even with the templates/ refactor in progress. This is the most concrete data point in favour of a framework migration — *not* because the current architecture can't scale, but because the **rate of regression fixes** is climbing faster than features.

---

*Concerns audit: 2026-05-25*
