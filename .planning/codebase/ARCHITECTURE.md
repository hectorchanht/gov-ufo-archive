<!-- refreshed: 2026-05-25 -->
# Architecture

**Analysis Date:** 2026-05-25

## System Overview

```text
┌────────────────────────────────────────────────────────────────────────┐
│                       OFFICIAL GOVERNMENT SOURCES                       │
│  war.gov · aaro.mil · science.nasa.gov · catalog.archives.gov           │
│  cnes-geipan.fr · nationalarchives.gov.uk · fab.mil.br · sefaa.cl …     │
└──────────┬────────────────────────────────────────────────┬────────────┘
           │ Wayback fallback                                │
           ▼                                                 ▼
┌──────────────────────────────────┐   ┌──────────────────────────────────┐
│   DOWNLOADERS (per archive)      │   │   SCRAPERS / SPIDER              │
│   `scripts/dl-<slug>.sh`         │   │   `scripts/scrape-<slug>.py`     │
│   curl + Akamai-aware UA         │   │   `scripts/spider.py` (generic)  │
│   idempotent cache-then-fetch    │   │   `scripts/harvest-tna.py`       │
└──────────┬───────────────────────┘   └──────────┬───────────────────────┘
           │                                       │
           ▼                                       ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       LOCAL ASSET CACHE (on disk)                       │
│   `bundles/Release_1/*.pdf`     `aaro/pdfs/*.pdf`   `aaro/videos/*.mp4` │
│   `slideshow/*.jpg`             `<slug>/pdfs/*`     `<slug>/.cache/`    │
│   `uap-data.csv` (war.gov · source of truth)                            │
│   `aaro/.cache/parsed.json` + `evidence.json` (intermediates)           │
└──────────┬─────────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       PARSE / NORMALIZE STAGE                           │
│   `scripts/parse-aaro.py`     → aaro/.cache/parsed.json                 │
│   `scripts/extract-evidence.py` → aaro/.cache/evidence.json             │
│   `scripts/_release_manifest.py` rewrites URLs to GH-release downloads  │
└──────────┬─────────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       BUILD STAGE  (Python, stdlib only)                │
│   `scripts/build-wargov.py`   → root `index.html` (splice-only)         │
│   `scripts/build-aaro.py`     → `aaro/index.html`                       │
│   `scripts/build-nasa.py`     → `nasa/index.html`                       │
│   `scripts/build-nara.py`     → `nara/index.html`                       │
│   `scripts/build-geipan.py`   → `geipan/index.html`                     │
│   `scripts/build-uk.py`       → `uk/index.html`                         │
│   `scripts/build-brazil.py`   → `brazil/index.html`                     │
│   `scripts/build-chile.py`    → `chile/index.html`                      │
│   `scripts/build_batch3.py`   → 7 mirrors (nz, canada, argentina, …)    │
│   `scripts/build-cases.py`    → case-detail HTML from `_cases.json`     │
│   `scripts/build-stories.py`  → story.html from `_stories.json`         │
│   `scripts/build-details.py`  → `aaro/details.html` long-form           │
│                                                                         │
│   Shared template surface:  `scripts/_site_template.py`                 │
│     re-exports from `scripts/templates/`:                               │
│       nav.py (PINNED / SITE_PAGES / MORE / STORIES · make_nav)          │
│       footer.py (make_footer, make_footer_sources)                      │
│       head.py (make_head — <head>+<style> opening)                      │
│       shared.py (SHARED_CSS · SHARED_JS · EXTRA_CSS)                    │
│       lightbox.py (LIGHTBOX_HTML · LIGHTBOX_CSS · LIGHTBOX_JS)          │
│       archive.py (ARCHIVE_JS — card-render + filter UI driver)          │
│       i18n.py (I18N dict · 6 langs)                                     │
│   Catalog-style mirrors import `scripts/_mirror_shared.py`              │
│     (SHARED_JS + ARCHIVE_JS appended)                                   │
└──────────┬─────────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    SELF-CONTAINED STATIC HTML PAGES                     │
│   Each `<slug>/index.html` has:                                         │
│     • Full inline CSS (no external stylesheet)                          │
│     • Full inline JS  (no external script bundle; vendor only for       │
│       lunr/leaflet/hotkeys on root utility pages)                       │
│     • Embedded JSON manifest:                                           │
│         <script id="arch-data" type="application/json">…</script>       │
│         (root index.html uses id="archive-manifest")                    │
└──────────┬─────────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────────────────────┐
│              POST-BUILD DERIVATIVE INDEXES (read every arch-data)       │
│   `scripts/build-api.py`         → `api/all.json` · by-archive · stats  │
│   `scripts/build-pages-index.py` → `api/pages-index.json` (case prose)  │
│   `scripts/build-geo.py`         → `api/geo.json` (map pins)            │
│   `scripts/build-feeds.py`       → `feeds/<slug>.xml` · `feeds/all.xml` │
│   `scripts/build-og.py`          → `<slug>/assets/og.svg` social cards  │
│   `scripts/build-sw.py`          → version-stamps `sw.js`               │
└──────────┬─────────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       OFFLINE-FIRST RUNTIME                             │
│   `sw.js` (root)                                                        │
│     · Precache: app shell (root, search, timeline, map, utility pages,  │
│       favicon, leaflet vendor, manifest.webmanifest)                    │
│     · Navigations  → network-first, cache 2xx only, fall back to /404   │
│     · JSON (*.json) → stale-while-revalidate (DATA_CACHE)               │
│     · Images/fonts → cache-first (IMG_CACHE)                            │
│     · Versioned cache names invalidate on each deploy                   │
└────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| War.gov landing | Largest archive, R01+R02 manifest splice | `index.html` + `scripts/build-wargov.py` |
| AARO archive | Evidence-first; videos + case-resolution PDFs | `aaro/index.html` + `scripts/build-aaro.py` |
| Per-archive build script | Generates ONE self-contained HTML page | `scripts/build-<slug>.py` |
| Per-archive downloader | Idempotent fetch with Wayback fallback | `scripts/dl-<slug>.sh` |
| Multi-archive batch builder | 7 small mirrors (nz/canada/arg/uy/peru/spain/italy) | `scripts/build_batch3.py` |
| Cross-archive search | Lunr-powered runtime search over all manifests | `search.html` |
| Map viewer | Leaflet renderer of `api/geo.json` | `map.html` + `api/geo.json` |
| Service worker | Offline shell + runtime caching | `sw.js` (root only) |
| Nav single source | Canonical nav HTML, sync'd into every page | `scripts/templates/nav.py` + `scripts/sync-nav.py` |
| Footer single source | Canonical footer HTML, sync'd into every page | `scripts/templates/footer.py` + `scripts/sync-footer.py` |
| Shared CSS/JS template | SHARED_CSS, SHARED_JS, lightbox, i18n | `scripts/templates/shared.py` + `lightbox.py` + `i18n.py` |
| Release-URL rewriter | Maps basenames → GH-release download URLs | `scripts/_release_manifest.py` + `release-manifest.json` |
| Asset normalizer (AARO) | Two-stage parse: HTML → parsed.json → evidence.json | `scripts/parse-aaro.py` + `scripts/extract-evidence.py` |
| Generic spider | Config-driven BFS crawler for catalog sources | `scripts/spider.py` |
| API baker | Flat cross-archive JSON dump | `scripts/build-api.py` |
| Feeds baker | Atom 1.0 per-archive + combined | `scripts/build-feeds.py` |
| Pages index baker | Case-page prose for full-text search | `scripts/build-pages-index.py` |
| Geo baker | Lat/lon per case for `/map.html` | `scripts/build-geo.py` |
| OG card baker | Per-archive 1200×630 social SVG | `scripts/build-og.py` |
| SW version stamp | Replaces `const VERSION` with commit short SHA | `scripts/build-sw.py` |
| Master orchestrator | Interactive picker + per-archive driver | `scripts/sync.sh` |

## Pattern Overview

**Overall:** Static-site generator with **per-archive isolation but shared build templates**.

Each archive folder is a self-contained, fully-static HTML+CSS+JS package — no shared CSS or JS files are referenced at runtime by archive pages. Instead, sharing happens at *build time*: every `build-<slug>.py` imports from `scripts/_site_template.py` (which re-exports the modular `scripts/templates/` package) and **inlines** the shared CSS/JS/HTML strings into each page during generation.

**Key Characteristics:**
- Pure static-HTML output — zero JS framework, zero build tooling (no webpack / vite / npm). Python stdlib only on the build side.
- Per-page data lives in an inline `<script id="arch-data" type="application/json">…</script>` block, parsed at runtime by inlined `ARCHIVE_JS`.
- Cross-cutting concerns (nav, footer, CSS variables, lightbox, i18n) are **single-source-of-truth Python modules** that get sprayed into every page at build, then *kept* canonical by CI drift gates (`sync-nav.yml`, `sync-footer.yml`).
- Offline-first is non-negotiable: every per-archive page works without network. The root-level `sw.js` precaches the app shell and applies network-first / stale-while-revalidate / cache-first policies by response type.
- Idempotency is a hard rule: every downloader, parser, builder, and `sync.sh` is safe to re-run.

## Layers

**Source layer (external):**
- Purpose: Official government archives — the legal source of truth.
- Location: 15 sites listed in `CLAUDE.md` §2.
- Contains: HTML pages, scanned PDFs, DVIDS videos, image galleries.
- Used by: downloaders and scrapers.

**Acquisition layer:**
- Purpose: Pull official content to local disk with Wayback fallback.
- Location: `scripts/dl-<slug>.sh` (per archive) and `scripts/scrape-<slug>.py` + `scripts/spider.py` for catalog crawls.
- Contains: bash + curl + a realistic Chrome UA; Python urllib for spider; `harvest-tna.py` for UK catalog.
- Depends on: `set -uo pipefail`; `curl_cffi` for Akamai-fronted war.gov; standard `curl`/`urllib` otherwise.
- Used by: build scripts (via on-disk filesystem and `<slug>/.cache/`).

**Storage / cache layer:**
- Purpose: Pinned local copy of all assets.
- Location: `bundles/Release_1/` (war.gov R01 PDFs · gitignored), `bundles/release_02_document_bundle/` (R02 PDFs · gitignored), `bundles/uapvideos/` (R01 DVIDS · gitignored), `bundles/uap052226/` (R02 DVIDS · gitignored), `slideshow/` + `slideshow-2/` (war.gov R01/R02 imagery · tracked), `<slug>/pdfs/` (gitignored), `<slug>/videos/` (gitignored), `<slug>/assets/images/` (tracked).
- Manifest sources: `uap-data.csv` (combined R01+R02 war.gov manifest), `uap-release001.csv` (legacy R01-only; do not touch), `<slug>/.cache/*.json` (parser intermediates).

**Transform layer (parse / normalize):**
- Purpose: Convert raw HTML snapshots into structured JSON.
- Location: `scripts/parse-aaro.py` → `aaro/.cache/parsed.json`; `scripts/extract-evidence.py` → `aaro/.cache/evidence.json`; `scripts/_release_manifest.py` mutates asset URLs in place.
- Used by: every `build-<slug>.py`.

**Build / template layer:**
- Purpose: Generate self-contained HTML pages.
- Location: `scripts/build-*.py` + `scripts/_site_template.py` (compat shim) + `scripts/templates/` (canonical modules).
- Output: one `<slug>/index.html` per archive (plus root `index.html`, story / case pages, `details.html`).
- Depends on: git-tracking detection (`git ls-files`) to decide LOCAL vs SOURCE badges; `release-manifest.json` to rewrite primary URLs to GH-release download links.

**Output layer (static HTML):**
- Purpose: The deployed site.
- Location: `*.html` at root + `<slug>/index.html` per archive + case/story HTML files.
- Contains: inlined CSS, inlined JS, inline JSON manifest, embedded i18n dict.

**Derivative-index layer:**
- Purpose: Cross-archive APIs and feeds derived from the inline manifests.
- Location: `api/all.json`, `api/by-archive.json`, `api/stats.json`, `api/geo.json`, `api/pages-index.json`, `feeds/<slug>.xml`, `feeds/all.xml`, `<slug>/assets/og.svg`, version-stamped `sw.js`.

**Runtime / offline layer:**
- Purpose: Make every page work offline, cache shell, never serve stale 404s.
- Location: `sw.js` (root), registration shim in `<head>` of every page (`navigator.serviceWorker.register('/sw.js')`).
- Vendor JS (root utility pages only): `assets/vendor/leaflet/`, `assets/vendor/lunr/`, `assets/vendor/hotkeys.js`, `assets/vendor/citation.js`, `assets/vendor/share.js`, `assets/vendor/related-media.js`.

## Data Flow

### Primary Build Path (per archive)

1. `scripts/dl-<slug>.sh` writes raw HTML / PDFs / videos under `<slug>/` and `bundles/` (idempotent; cache-then-fetch with Wayback fallback). (`scripts/dl-aaro.sh`)
2. `scripts/scrape-<slug>.py` or `scripts/spider.py` may parse the downloaded HTML into `<slug>/.cache/*.json`. (`scripts/parse-aaro.py:1`, `scripts/extract-evidence.py:1`)
3. `scripts/build-<slug>.py` imports `make_nav`, `LIGHTBOX_HTML`, `SHARED_CSS`, `SHARED_JS` from `_site_template`. (`scripts/build-aaro.py:11`, `scripts/build-nasa.py:10`, `scripts/build-uk.py:14-16`)
4. The builder enumerates local files via `git ls-files <slug>/<dir>/` so the LOCAL badge reflects what GitHub Pages will actually serve. (`scripts/build-aaro.py:31-44`, `scripts/build-nasa.py:16-26`)
5. `apply_manifest()` (from `scripts/_release_manifest.py`) rewrites primary URLs to GH-release download links when basenames match `release-manifest.json`. (`scripts/_release_manifest.py:29-54`)
6. The builder assembles the final HTML by string-templating into a single inline document: shared CSS replaces `__LIGHTBOX_CSS__`, shared JS replaces `__I18N_JSON__`, then the inline `<script id="arch-data">` JSON blob is dumped.
7. The output file is written atomically to `<slug>/index.html`.

### Root War.gov Splice Path

1. `scripts/build-wargov.py` reads `uap-data.csv` (or legacy `uap-release001.csv`). (`scripts/build-wargov.py:27-29`)
2. Each row is enriched with `local` (basename → `bundles/Release_1/...` or `slideshow/...` if git-tracked) and rewritten URL (release URL when basename in `release-manifest.json`). (`scripts/build-wargov.py:143-170`)
3. DVIDS Video IDs are resolved to playable DOD URLs via `scripts/dvids2dod-r01.json` + `scripts/dvids2dod-r02.json`. (`scripts/build-wargov.py:83-98`, `scripts/build-wargov.py:147-155`)
4. The final manifest JSON is **spliced** into the existing `index.html` by regex-replacing the body of `<script id="archive-manifest">…</script>`. CSS / structure / JS in `index.html` are never touched by this script. (`scripts/build-wargov.py:188-199`)

### Cross-archive Derivative Path

1. `scripts/build-api.py` walks every `<slug>/index.html`, extracts the inline `arch-data` JSON, normalizes to a flat schema, and writes `api/all.json`, `api/by-archive.json`, `api/stats.json`. (`scripts/build-api.py:1-30`)
2. `scripts/build-pages-index.py` parses case + story HTML for prose, emits `api/pages-index.json` consumed by `/search.html`. (`scripts/build-pages-index.py:1-30`)
3. `scripts/build-geo.py` reads "◉ DD.DDDD° N · DD.DDDD° W" coord lines from case detail pages, falls back to per-archive HQ centroid, emits `api/geo.json` consumed by `/map.html`. (`scripts/build-geo.py:1-30`)
4. `scripts/build-feeds.py` emits Atom 1.0 feeds under `feeds/<slug>.xml` + `feeds/all.xml`. (`scripts/build-feeds.py:1-30`)
5. `scripts/build-sw.py` stamps `const VERSION` in `sw.js` with the current git short SHA + UTC date so a deploy invalidates user caches. (`scripts/build-sw.py:31-49`)

### Page Render Path (client)

1. Browser requests `<slug>/index.html`.
2. Inline `<script>` registers `/sw.js` (root scope). (`index.html:27`, `search.html:26`, `timeline.html:22`)
3. Inlined `SHARED_JS` runs: applies saved `localStorage.realufo_lang`, wires hamburger toggle, dropdown coordination, lightbox key/swipe handlers. (`scripts/templates/shared.py:249-434`)
4. Inlined `ARCHIVE_JS` reads `<script id="arch-data">`, paints stats, tabs, search, and the card grid into `#arch-grid`. Bails out early if `#pagination` is present (host page provides its own paginator — GEIPAN). (`scripts/templates/archive.py:33-38`)
5. Card click → `window._lb.open(idx)` → media renders in lightbox; arrow keys + swipe navigate.

**State Management:**
- No client-side state framework. Per-page JS uses module-scoped variables + DOM as state.
- Persisted state: `localStorage.realufo_lang` (current i18n locale), search query in `?q=` URL param (cross-archive search only).
- Server-side state: none. Site is purely static.

## Key Abstractions

**Asset record (canonical short-form keys):**
- Purpose: One row in the inline `arch-data` JSON.
- Examples: every `<script id="arch-data">` block (e.g., `aaro/index.html`).
- Shape: `{ t, ti, de, ag, cat, date, region, l, u, s, th }` — type, title, description, agency, category, date, region, local path, primary URL, source URL, thumbnail. Long-form keys `{type, title, desc, agency, category, date, region, local, url, src, thumb}` are also accepted by the lightbox renderer for backwards compat. (`scripts/templates/archive.py:24-26`)

**Make-* template builders:**
- `make_nav(current_slug, depth)` — returns `<nav>` HTML; sole source of nav across every page. (`scripts/templates/nav.py:165-235`)
- `make_footer(variant, depth, meta)` — three variants: `minimal` / `mirror` / `root`. (`scripts/templates/footer.py:18-78`)
- `make_footer_sources(source_links, license_text, colophon)` — multi-column source-list footer for mirror pages. (`scripts/templates/footer.py:81-119`)
- `make_head(...)` — opens `<head>` through start of `<style>`; caller closes. (`scripts/templates/head.py:14-54`)

**SHARED_CSS / SHARED_JS / LIGHTBOX_***:
- Module-level strings concatenated at import time. `SHARED_CSS` injects `__LIGHTBOX_CSS__` placeholder; `SHARED_JS` injects `__I18N_JSON__`. (`scripts/templates/shared.py:1-12`, `scripts/templates/shared.py:233-434`)

**Release manifest (`release-manifest.json`):**
- Basename → GH-release download URL map. Read by `apply_manifest()` to rewrite per-record `u:` URLs so deployed pages always have a working download link when the file lives in a release tag. (`scripts/_release_manifest.py:14-54`)

**Git-tracking-aware local detection:**
- Every builder uses `git ls-files <slug>/<dir>/` (not `os.listdir`) to decide LOCAL vs SOURCE badge. A file present on disk but gitignored stays routed through the source URL, so Download buttons never 404 on GitHub Pages. (`scripts/build-aaro.py:31-44`, `scripts/build-nasa.py:16-26`, `scripts/build-wargov.py:34-50`)

## Entry Points

**Master orchestrator:**
- Location: `scripts/sync.sh`
- Triggers: developer CLI; cron / launchd schedule.
- Responsibilities: interactive multi-select picker → per-archive downloader → rebuild all HTML.

**Per-archive downloaders:**
- Location: `scripts/dl-aaro.sh`, `scripts/dl-nasa.sh`, `scripts/dl-nara.sh`, `scripts/dl-geipan.sh`, `scripts/dl-uk.sh`, `scripts/dl-brazil.sh`, `scripts/dl-chile.sh`.
- Triggers: `sync.sh` or invoked individually.
- Responsibilities: idempotent download with Wayback fallback.

**Per-archive builders:**
- Location: `scripts/build-aaro.py`, `scripts/build-nasa.py`, `scripts/build-nara.py`, `scripts/build-geipan.py`, `scripts/build-uk.py`, `scripts/build-brazil.py`, `scripts/build-chile.py`, `scripts/build_batch3.py` (covers 7 small mirrors), `scripts/build-wargov.py` (root splice).
- Triggers: `sync.sh --no-videos`, manual `python3 scripts/build-<slug>.py`.

**Drift-gate CLIs:**
- `scripts/sync-nav.py [--check]` — rewrites or verifies every page's `<nav>` block. (`scripts/sync-nav.py:1-30`)
- `scripts/sync-footer.py [--check]` — same pattern for `<footer>`. (`scripts/sync-footer.py:1-25`)
- `scripts/validate-manifests.py [--strict]` — schema-validates every inline manifest. (`scripts/validate-manifests.py:1-30`)
- `scripts/check-sources.py` — HEAD-pings every external URL across all manifests, writes `dead-links.json` / `dead-links.md`. (`scripts/check-sources.py:1-30`)

**CI workflows:**
- `.github/workflows/scrape.yml` — weekly cron (`Mon 06:00 UTC`): scrape → spider → API → feeds → commit.
- `.github/workflows/sync-nav.yml` — drift gate.
- `.github/workflows/sync-footer.yml` — drift gate.
- `.github/workflows/html-validate.yml` — HTML validation.
- `.github/workflows/lighthouse.yml` — perf budget.
- `.github/workflows/links.yml` — broken-link sweep (`lychee`).

**Service worker:**
- Location: `/sw.js` (root scope).
- Triggers: registered by every page via inline `<script>`. (`index.html:27` and equivalents)

## Architectural Constraints

- **Threading:** Build scripts are single-threaded synchronous Python; `scripts/check-sources.py` is the only multi-threaded build-time script (uses `concurrent.futures.ThreadPoolExecutor`).
- **Global state:** Module-level constants in `scripts/templates/*.py` (PINNED, SITE_PAGES, MORE, STORIES, I18N, SHARED_CSS, SHARED_JS, LIGHTBOX_*) are read by every builder at import. Mutating any of them propagates to the next full rebuild.
- **Circular imports:** `scripts/templates/head.py` lazy-imports `_site_template` to avoid a circular dependency during the in-progress refactor. See note in `scripts/templates/head.py:18-22`.
- **Per-archive isolation at runtime:** No archive page loads CSS or JS from any other archive's folder. The only cross-archive runtime resources are root-level vendor scripts (`/assets/vendor/lunr/lunr.min.js`, `/assets/vendor/leaflet/`, `/assets/vendor/hotkeys.js`) referenced by root utility pages only.
- **SW scope:** `sw.js` is at repository root (scope = `/`); only the root and root-utility pages (`search.html`, `timeline.html`, `map.html`, `about.html`, `donate.html`, `glossary.html`, `stats.html`, `foia.html`, `compare.html`, `whatsnew.html`) currently register it. Per-archive pages do not register the SW themselves — they inherit it once the user has visited any root page.
- **Forbidden:** Touching `uap-release001.csv` (locked by CLAUDE.md §11); force-pushing main; introducing a JS framework or external CSS file referenced from a mirror page.

## Anti-Patterns

### Reading file lists with `os.listdir` instead of `git ls-files`

**What happens:** A builder picks up a file present on disk but gitignored, marks it LOCAL, then the Download button 404s on the deployed site.
**Why it's wrong:** PDFs and videos live in GitHub Releases (`pdfs-v1`, `videos-v1`, `pdfs-v2`, `wargov-r02-v1`) and are gitignored from the source tree.
**Do this instead:** Use the `git_tracked(rel_dir)` helper present in every builder. See `scripts/build-aaro.py:31-44` for the canonical implementation.

### Single-`<source>` `<video>` for assets with both local + remote

**What happens:** Lightbox plays only one path; if local is missing on deploy, video silently fails.
**Why it's wrong:** Offline-first contract is broken; CLAUDE.md §11 explicitly forbids it.
**Do this instead:** Emit `<video><source src="./local.mp4"><source src="https://github.com/.../releases/.../local.mp4"></video>`. See `scripts/templates/shared.py:386-389`.

### Inline `<style>` blocks placed inside `<body>`

**What happens:** html-validate's `element-permitted-content` rule rejects the page.
**Why it's wrong:** Modern browsers tolerate this but the validator does not.
**Do this instead:** Run `python3 scripts/fix-body-style.py` to move body-level `<style>` into `<head>`. See `scripts/fix-body-style.py:1-20`.

### Hand-edited `<nav>` or `<footer>` in any HTML page

**What happens:** `sync-nav.yml` / `sync-footer.yml` CI gate fails on the next push.
**Why it's wrong:** Nav and footer are single-source-of-truth. Drift breaks the cross-archive navigation contract.
**Do this instead:** Edit `scripts/templates/nav.py` (or `footer.py`) and run `python3 scripts/sync-nav.py` / `python3 scripts/sync-footer.py` to rewrite every page.

### Caching every fetch (including 404s) in the service worker

**What happens:** A transient pre-deploy 404 gets pinned in the user's cache; the page stays broken even after the file lands.
**Why it's wrong:** Previously caused stale-404 reports; explicitly fixed in commit `dcbc0d7`.
**Do this instead:** Only cache `res.ok` responses. See `sw.js:81-83` and the `// CRITICAL:` comment block above it.

### Touching `index.html` CSS or HTML structure from `scripts/build-wargov.py`

**What happens:** The hand-tuned war.gov landing page gets clobbered.
**Why it's wrong:** `build-wargov.py` is a **splice-only** script — it ONLY rewrites the inline `<script id="archive-manifest">` JSON body.
**Do this instead:** Edit `index.html` by hand for structural changes. Edit only `uap-data.csv` for content. See `scripts/build-wargov.py:188-199`.

## Error Handling

**Strategy:** Defensive degradation. Every fetch path has a fallback; every image / video tag has an `onerror` swap; every PDF iframe has a "open in new tab" link; every release-URL lookup falls back to the original source URL.

**Patterns:**
- Downloaders: `set -uo pipefail` (no `-e` — failures are isolated per file); `curl --fail --max-time` then Wayback `https://web.archive.org/web/<ts>id_/<url>` fallback; `rm -f` partials.
- Builders: `try ... except subprocess.CalledProcessError, FileNotFoundError` around `git ls-files` (falls back to `os.listdir`). See `scripts/build-aaro.py:40-44`.
- Service worker install: `Promise.all(SHELL.map(url => cache.add(url).catch(() => {})))` — one 404 doesn't break the entire install. See `sw.js:47`.
- Service worker navigation: `fetch(req).then(...).catch(() => caches.match(req).then(hit => hit || caches.match('/404.html')))`. See `sw.js:79-88`.
- Client-side image fallback: `<img onerror="this.onerror=null;this.src='${esc(a.u||a.url)}';">`. See `scripts/templates/shared.py:384`.
- Client-side video fallback: `<video><source src="./local.mp4"><source src="release-url.mp4"></video>`. See `scripts/templates/shared.py:389`.
- CSP: `default-src 'self'`; only `umami.is` for analytics, `fonts.googleapis.com`/`fonts.gstatic.com` for fonts, `web.archive.org` for source-link clicks. See `index.html:5`.

## Cross-Cutting Concerns

**Logging:** None server-side (no server). Build scripts `print()` to stdout. Client side uses `console` sparingly; analytics via Umami (`https://cloud.umami.is/script.js`, site ID baked into pages).

**Validation:**
- `scripts/validate-manifests.py` — schema-checks every inline manifest in CI.
- `scripts/check-sources.py` — HEAD-pings every external URL, emits `dead-links.{json,md}`.
- `scripts/sync-nav.py --check` + `scripts/sync-footer.py --check` — block PRs that drift from canonical nav/footer.
- `.htmlvalidate.json` — html-validate config.
- `.lycheeignore` — link-checker ignore list.
- `.lighthouserc.json` — Lighthouse CI budget.

**Authentication:** None — the site has no auth surface. Public-domain content, no user accounts, no comments, no forms beyond mailto links.

**Internationalization:** Single shared `I18N` dict at `scripts/templates/i18n.py` covers 6 languages (en/fr/es/pt/zh/ja). Inlined into every page; runtime applies via `localStorage.realufo_lang` and `data-i18n` attributes.

**Accessibility:** `scripts/fix-a11y-sweep.py` applies idempotent regex fixes (role attributes on decorative divs, aria-label on `<nav class="toc">`, `<nav class="pagination">`).

**Asset / size discipline:**
- `bundles/*.zip` and per-archive `pdfs/` + `videos/` are gitignored — files live in GitHub Release tags (`pdfs-v1`, `videos-v1`, `pdfs-v2`, `wargov-r02-v1`).
- Single files >100 MB are hard-banned (GitHub limit).
- Images stay tracked (small, used for thumbnails and slideshow).

---

*Architecture analysis: 2026-05-25*
