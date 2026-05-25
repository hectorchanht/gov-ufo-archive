# Codebase Structure

**Analysis Date:** 2026-05-25

## Directory Layout

```
war-gov-ufo-release/
├── index.html                   # War.gov / PURSUE landing page (479 KB)
├── search.html                  # Cross-archive Lunr search
├── timeline.html                # Timeline viewer
├── map.html                     # Leaflet world map (reads /api/geo.json)
├── about.html                   # About / FAQ
├── donate.html                  # Support page
├── glossary.html                # UAP glossary
├── stats.html                   # Stats dashboard
├── foia.html                    # FOIA guide
├── compare.html                 # Cross-archive comparison
├── whatsnew.html                # Recent changes
├── embed.html                   # Embed widget
├── 404.html                     # Custom offline / fallback page
├── sw.js                        # Service worker (root scope)
├── manifest.webmanifest         # PWA manifest
├── CNAME                        # realufo.org
├── robots.txt
├── sitemap.xml
├── humans.txt
├── release-manifest.json        # Basename → GH-release URL map
├── uap-data.csv                 # Combined R01+R02 manifest (source of truth)
├── uap-release001.csv           # Legacy R01-only CSV (DO NOT EDIT)
├── dead-links.json              # Output of scripts/check-sources.py
├── dead-links.md
├── CLAUDE.md                    # Master spec (read first)
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── .htmlvalidate.json           # html-validate config
├── .lycheeignore                # lychee link-checker ignore
├── .lighthouserc.json           # Lighthouse CI budget
├── .gitignore                   # Pinned policy (CLAUDE.md §5.2)
│
├── assets/                      # Root-level shared assets
│   ├── favicon.svg              # Shared classic-disk-UFO favicon
│   ├── og.svg                   # Default Open Graph image
│   ├── DOD-Icon-Header.png
│   ├── DOW-Icon-Header.png
│   ├── ln-qr.svg / ln-qr.png
│   └── vendor/                  # Vendored third-party JS (offline)
│       ├── leaflet/             # Leaflet 1.x for /map.html
│       ├── lunr/                # Lunr.js for /search.html
│       ├── hotkeys.js           # "/" focus + shortcuts
│       ├── citation.js          # Case-page citation copier
│       ├── share.js             # Share button
│       └── related-media.js     # Cross-link related cards
│
├── api/                         # Baked cross-archive JSON dumps
│   ├── all.json                 # Every record flat
│   ├── by-archive.json          # Grouped by archive slug
│   ├── stats.json               # Totals per archive
│   ├── geo.json                 # Lat/lon for /map.html
│   ├── pages-index.json         # Case + story prose for /search.html
│   └── README.md                # Consumer docs
│
├── feeds/                       # Atom 1.0 feeds (one per archive + all)
│   ├── all.xml
│   ├── wargov.xml, aaro.xml, nasa.xml, nara.xml, geipan.xml, uk.xml, …
│
├── slideshow/                   # War.gov Release 01 imagery (tracked)
├── slideshow-2/                 # War.gov Release 02 imagery (tracked)
│
├── bundles/                     # Heavy assets — mostly gitignored
│   ├── Release_1/               # R01 PDFs (gitignored *.pdf)
│   ├── release_02_document_bundle/  # R02 PDFs (gitignored)
│   ├── uapvideos/               # R01 DVIDS videos (gitignored)
│   ├── uap052226/               # R02 DVIDS videos (gitignored)
│   ├── Release_1.zip            # Bundle zips (gitignored)
│   ├── uapvideos.zip
│   ├── uap052226.zip
│   └── release_02_document_bundle.zip
│
├── aaro/                        # AARO archive (US, blue)
│   ├── index.html
│   ├── details.html             # Long-form per-section pages
│   ├── story.html
│   ├── tic-tac.html, gimbal.html, phoenix-lights.html,
│   │ belgian-wave.html, cash-landrum.html, coyne.html, jal-1628.html,
│   │ ohare-2006.html, stephenville.html, tehran.html, travis-walton.html
│   ├── assets/
│   │   ├── favicon.svg          # Shared favicon copy
│   │   ├── og.svg               # Per-archive OG card
│   │   └── images/              # Tracked imagery
│   ├── pages/                   # Wayback page snapshots (tracked)
│   ├── pdfs/                    # Gitignored — pdfs-v1 release
│   └── videos/                  # Gitignored — videos-v1 release
│
├── nasa/                        # NASA UAP (red #fc3d21)
│   ├── index.html, story.html
│   ├── assets/{favicon.svg,og.svg,images/}
│   └── pdfs/
│
├── nara/                        # NARA (silver #cbd5e1)
│   ├── index.html, story.html
│   ├── roswell.html, socorro.html, mantell.html, chiles-whitted.html,
│   │ mcminnville.html, lubbock-lights.html, levelland.html,
│   │ robertson-panel.html, condon-committee.html
│   ├── pages/                   # Wayback snapshots
│   ├── assets/{favicon.svg,og.svg}
│   └── pdfs/
│
├── geipan/                      # France GEIPAN (#0055a4)
│   ├── index.html, story.html
│   ├── trans-en-provence.html, valensole.html
│   ├── cases.json               # Paginated catalog data (3334 records)
│   ├── assets/{favicon.svg,og.svg,images/}
│   ├── pdfs/, videos/
│
├── uk/                          # UK National Archives (#012169)
│   ├── index.html, story.html
│   ├── rendlesham.html, cosford.html
│   ├── assets/, pdfs/
│
├── brazil/                      # Brazil FAB (#009c3b)
│   ├── index.html, story.html
│   ├── operacao-prato.html, varginha.html, trindade.html
│   ├── assets/, pdfs/
│
├── chile/                       # Chile SEFAA (#d52b1e)
│   ├── index.html, story.html, el-bosque.html
│   ├── assets/, pdfs/
│
├── argentina/                   # Argentina CEFAe (#74acdf)
│   ├── index.html, story.html
│   ├── assets/, pdfs/
│
├── canada/                      # Canada LAC / Project Magnet (#ff6b6b)
│   ├── index.html, story.html
│   ├── shag-harbour.html, falcon-lake.html
│   ├── assets/, pdfs/
│
├── italy/                       # Italy Aeronautica Militare (#5cb85c)
│   ├── index.html, story.html
│   ├── assets/, pdfs/
│
├── nz/                          # NZ NZDF (#5b8def)
│   ├── index.html, story.html, kaikoura.html
│   ├── assets/, pdfs/
│
├── peru/                        # Peru OIFAA (#ff6b6b)
│   ├── index.html, story.html
│   ├── assets/, pdfs/
│
├── spain/                       # Spain Ejército del Aire (#f4c542)
│   ├── index.html, story.html, manises.html
│   ├── assets/, pdfs/
│
├── uruguay/                     # Uruguay CRIDOVNI (#3ba0d8)
│   ├── index.html, story.html
│   ├── assets/, pdfs/
│
├── scripts/                     # All build tooling (Python + bash)
│   ├── sync.sh                  # Master orchestrator
│   ├── _site_template.py        # Compat shim — re-exports templates/*
│   ├── _mirror_shared.py        # Catalog-style mirror SHARED_JS+ARCHIVE_JS
│   ├── _release_manifest.py     # Basename → release-URL rewriter
│   ├── _cases.json              # Case detail data for build-cases.py
│   ├── _stories.json            # Per-archive story data for build-stories.py
│   ├── dvids2dod-r01.json       # DVIDS Video ID → DOD record-id map
│   ├── dvids2dod-r02.json
│   ├── templates/               # Canonical template package
│   │   ├── __init__.py
│   │   ├── nav.py               # PINNED · SITE_PAGES · MORE · STORIES · make_nav
│   │   ├── footer.py            # make_footer · make_footer_sources
│   │   ├── head.py              # make_head
│   │   ├── shared.py            # SHARED_CSS · SHARED_JS · EXTRA_CSS
│   │   ├── lightbox.py          # LIGHTBOX_HTML · LIGHTBOX_CSS · LIGHTBOX_JS
│   │   ├── archive.py           # ARCHIVE_JS (card render + filter driver)
│   │   └── i18n.py              # 6-lang dict
│   │
│   ├── dl-aaro.sh, dl-brazil.sh, dl-chile.sh, dl-geipan.sh,
│   │ dl-nara.sh, dl-nasa.sh, dl-uk.sh                  # Downloaders
│   ├── download-war.gov.py                              # War.gov fetcher (curl_cffi)
│   │
│   ├── build-aaro.py, build-brazil.py, build-chile.py,
│   │ build-geipan.py, build-nara.py, build-nasa.py, build-uk.py,
│   │ build-wargov.py                                    # Per-archive builders
│   ├── build_batch3.py                                  # 7 small mirrors
│   ├── build-cases.py                                   # Case detail pages
│   ├── build-stories.py                                 # story.html pages
│   ├── build-details.py                                 # aaro/details.html
│   ├── build-api.py                                     # api/*.json
│   ├── build-feeds.py                                   # feeds/*.xml
│   ├── build-geo.py                                     # api/geo.json
│   ├── build-pages-index.py                             # api/pages-index.json
│   ├── build-og.py                                      # <slug>/assets/og.svg
│   ├── build-sw.py                                      # Version-stamp sw.js
│   │
│   ├── parse-aaro.py                                    # AARO HTML → JSON
│   ├── extract-evidence.py                              # AARO evidence map
│   ├── scrape-aaro.py, scrape-brazil.py, scrape-chile.py,
│   │ scrape-geipan.py, scrape-nara.py, scrape-nasa.py, scrape-uk.py
│   ├── spider.py                                        # Generic config-driven crawler
│   ├── harvest-tna.py                                   # UK TNA harvester
│   │
│   ├── sync-nav.py                                      # Drift-gate: nav
│   ├── sync-footer.py                                   # Drift-gate: footer
│   ├── validate-manifests.py                            # Schema check
│   ├── check-sources.py                                 # External URL HEAD ping
│   ├── extract-pdf-text.py                              # PDF → .pdftext/ for search
│   ├── append-changelog.py                              # Auto-bump CHANGELOG
│   ├── backfill-release.py                              # Build release-manifest.json
│   ├── resolve-dvids-r01.py                             # DVIDS → DOD resolver
│   ├── fix-a11y-sweep.py                                # Accessibility fixes
│   ├── fix-body-style.py                                # Move body <style> → head
│   ├── update_all.sh                                    # Convenience wrapper
│   └── __pycache__/
│
├── .github/
│   ├── workflows/
│   │   ├── scrape.yml           # Weekly cron rebuild
│   │   ├── sync-nav.yml         # Drift gate
│   │   ├── sync-footer.yml      # Drift gate
│   │   ├── html-validate.yml
│   │   ├── lighthouse.yml
│   │   └── links.yml            # lychee broken-link check
│   ├── ISSUE_TEMPLATE/
│   └── FUNDING.yml
│
├── .well-known/
│   └── security.txt
│
├── .planning/                   # GSD planning + codebase docs
│   └── codebase/                # This document lives here
│
└── .claude/                     # Local Claude config (gitignored)
```

## Directory Purposes

**Root (`/`):**
- Purpose: Hand-tuned War.gov landing page + cross-archive utility pages.
- Contains: `index.html`, `search.html`, `timeline.html`, `map.html`, `about.html`, `donate.html`, `glossary.html`, `stats.html`, `foia.html`, `compare.html`, `whatsnew.html`, `embed.html`, `404.html`.
- Key files: `index.html` (479 KB — large because R01+R02 manifest is inlined; CLAUDE.md §4); `sw.js` (service worker, root scope); `manifest.webmanifest` (PWA).
- Special: `uap-release001.csv` is locked by CLAUDE.md §11 — never edit; `uap-data.csv` is the active source.

**`assets/`:**
- Purpose: Root-level shared assets used by utility pages.
- Contains: `favicon.svg` (master copy; per-archive copies are duplicates), `og.svg`, header PNGs, `vendor/` (offline copies of Leaflet, Lunr, hotkeys.js, citation.js, share.js, related-media.js).
- Special: Per-archive `<slug>/assets/favicon.svg` is the same SVG (per CLAUDE.md §3.4).

**`api/`:**
- Purpose: Baked cross-archive JSON dumps consumed by `/search.html`, `/map.html`, `/stats.html`.
- Contains: `all.json`, `by-archive.json`, `stats.json`, `geo.json`, `pages-index.json`.
- Generated: Yes — by `scripts/build-api.py`, `scripts/build-geo.py`, `scripts/build-pages-index.py`.
- Committed: Yes (small, JSON, useful for offline + external API consumers).

**`feeds/`:**
- Purpose: Atom 1.0 syndication.
- Generated: `scripts/build-feeds.py`.
- Committed: Yes.

**`bundles/`:**
- Purpose: War.gov heavyweight PDF/video bundles.
- Contains: 4 subdirs (`Release_1`, `release_02_document_bundle`, `uapvideos`, `uap052226`) + 4 corresponding `.zip` files.
- Generated: By `scripts/download-war.gov.py` (via `sync.sh`).
- Committed: **No** — all PDFs/videos/zips are gitignored. Files live in GitHub Release tags (`pdfs-v1`, `pdfs-v2`, `videos-v1`, `wargov-r02-v1`).

**`slideshow/` + `slideshow-2/`:**
- Purpose: War.gov R01 + R02 thumbnail / hero images.
- Committed: Yes (small JPGs, used on root `index.html` carousel + cards).

**`<archive>/` (15 archive folders):**
- Purpose: One self-contained mirror per official source.
- Contains: `index.html` (catalog page · ALL ~14 of 15 use `<script id="arch-data">`; root uses `id="archive-manifest"`), `story.html` (verbatim agency mission text), zero-or-more case detail HTML pages, `assets/` (favicon, OG, optional images), `pdfs/` (gitignored), optional `videos/` (gitignored), optional `pages/` (Wayback HTML snapshots, tracked), optional `.cache/` (parser intermediates, gitignored).
- Special: `aaro/` has the richest content (videos + 11 case pages + `details.html`); `geipan/` has the largest catalog (3334 records, paginated client-side via `cases.json`).

**`scripts/`:**
- Purpose: All build, scrape, validate, and sync tooling.
- Contains: Python + bash, **no Node**, no `package.json`, no compiled artifacts. Stdlib-only except `curl_cffi` for Akamai-fronted war.gov.
- Special: `scripts/templates/` is the single source of truth for nav/footer/head/shared-CSS/JS/lightbox/i18n/archive-JS. `scripts/_site_template.py` is a compat shim that re-exports everything for older builders' import paths.

**`.github/workflows/`:**
- Purpose: CI gates.
- Contains: 6 workflows. The drift gates (`sync-nav.yml`, `sync-footer.yml`) are load-bearing — they block PRs that drift from the canonical nav/footer.

**`.planning/`:**
- Purpose: GSD-style planning artifacts.
- Contains: `codebase/` (architecture / structure docs — this file).

## Key File Locations

**Entry Points:**
- `scripts/sync.sh`: Master orchestrator with interactive picker (CLAUDE.md §6.3).
- `index.html`: Root landing page (war.gov).
- `<slug>/index.html`: Per-archive landing page.
- `sw.js`: Service worker registered by every root utility page.

**Configuration:**
- `CLAUDE.md`: Master design / build spec (read first).
- `.gitignore`: Pinned PDF/video gitignore policy (CLAUDE.md §5.2).
- `release-manifest.json`: Basename → GH-release URL map; read by `scripts/_release_manifest.py`.
- `manifest.webmanifest`: PWA install manifest.
- `CNAME`: `realufo.org`.
- `.htmlvalidate.json`: html-validate rules.
- `.lighthouserc.json`: Lighthouse CI budget.
- `.lycheeignore`: Link checker ignore list.

**Core Logic — build templates (canonical):**
- `scripts/templates/nav.py`: PINNED, SITE_PAGES, MORE, STORIES, `make_nav()`.
- `scripts/templates/footer.py`: `make_footer()`, `make_footer_sources()`.
- `scripts/templates/head.py`: `make_head()`.
- `scripts/templates/shared.py`: `SHARED_CSS`, `SHARED_JS`, `EXTRA_CSS`.
- `scripts/templates/lightbox.py`: `LIGHTBOX_HTML`, `LIGHTBOX_CSS`, `LIGHTBOX_JS`.
- `scripts/templates/archive.py`: `ARCHIVE_JS` — catalog-page card renderer.
- `scripts/templates/i18n.py`: 6-language `I18N` dict.
- `scripts/_site_template.py`: Backwards-compat shim re-exporting templates.
- `scripts/_mirror_shared.py`: Catalog mirrors' `SHARED_JS = SHARED_JS + ARCHIVE_JS`.

**Core Logic — per-archive builders:**
- `scripts/build-wargov.py`: Splice-only — rewrites `<script id="archive-manifest">` in root `index.html` from `uap-data.csv`.
- `scripts/build-aaro.py`: Reads `aaro/.cache/{parsed,evidence}.json`, emits `aaro/index.html` (1313 lines).
- `scripts/build-details.py`: Emits `aaro/details.html` long-form pages.
- `scripts/build-nasa.py`, `scripts/build-nara.py`, `scripts/build-geipan.py`, `scripts/build-uk.py`, `scripts/build-brazil.py`, `scripts/build-chile.py`: Per-archive page builders.
- `scripts/build_batch3.py`: Driver for 7 small mirrors (NZ, Canada, Argentina, Uruguay, Peru, Spain, Italy).
- `scripts/build-cases.py`: Case detail HTML from `scripts/_cases.json`.
- `scripts/build-stories.py`: `<slug>/story.html` from `scripts/_stories.json`.

**Core Logic — scrapers / parsers:**
- `scripts/parse-aaro.py`: AARO HTML snapshots → `aaro/.cache/parsed.json`.
- `scripts/extract-evidence.py`: parsed.json → `aaro/.cache/evidence.json` (videos + PDFs + captions).
- `scripts/scrape-<slug>.py`: Per-archive scrapers (NASA, NARA, GEIPAN, UK, Brazil, Chile, AARO).
- `scripts/spider.py`: Generic config-driven BFS crawler with Wayback fallback.
- `scripts/harvest-tna.py`: UK TNA Discovery catalog harvester.

**Core Logic — post-build derivatives:**
- `scripts/build-api.py`: api/all.json + by-archive + stats.
- `scripts/build-feeds.py`: feeds/<slug>.xml + feeds/all.xml.
- `scripts/build-geo.py`: api/geo.json from "◉ DD.DDDD°" hero coord lines.
- `scripts/build-pages-index.py`: api/pages-index.json for cross-archive full-text search.
- `scripts/build-og.py`: per-archive 1200×630 OG SVG.
- `scripts/build-sw.py`: Stamp `const VERSION` in `sw.js` with git short SHA.

**Core Logic — drift gates / utilities:**
- `scripts/sync-nav.py [--check]`: Rewrites every page's `<nav>` to canonical output.
- `scripts/sync-footer.py [--check]`: Same pattern for `<footer>`.
- `scripts/validate-manifests.py [--strict]`: Schema-validates every inline manifest.
- `scripts/check-sources.py`: HEAD-pings external URLs, writes `dead-links.{json,md}`.
- `scripts/fix-a11y-sweep.py`: Idempotent accessibility regex fixes.
- `scripts/fix-body-style.py`: Move body-level `<style>` into `<head>` for validator.
- `scripts/extract-pdf-text.py`: `pdftotext` → `<archive>/.pdftext/`.
- `scripts/backfill-release.py`: Build `release-manifest.json`.
- `scripts/append-changelog.py`: Auto-bump CHANGELOG.md.

**Testing:**
- No unit-test framework in repo. Validation is done via the CI gates above (`validate-manifests.py`, `check-sources.py`, `sync-nav.py --check`, `sync-footer.py --check`, html-validate, Lighthouse, lychee).

## Naming Conventions

**Files:**
- HTML pages: kebab-case (`tic-tac.html`, `el-bosque.html`, `chiles-whitted.html`, `rendlesham.html`).
- Build / scrape scripts: `<verb>-<slug>.py` or `<verb>-<slug>.sh` (`build-aaro.py`, `dl-aaro.sh`, `scrape-nasa.py`).
- Underscore-prefixed scripts are private helpers / shims: `_site_template.py`, `_mirror_shared.py`, `_release_manifest.py`, `_cases.json`, `_stories.json`.
- Snake_case is allowed for multi-archive batches: `build_batch3.py`.
- JSON intermediates live in dot-prefixed dirs: `<slug>/.cache/parsed.json`, `<slug>/.pdftext/*.txt`.

**Directories:**
- Archive folders: lowercase ISO-ish slug (`aaro`, `nara`, `geipan`, `uk`, `nz`, `argentina`). Match the per-archive nav slug in `scripts/templates/nav.py:PINNED`/`MORE`.
- Hidden / generated dirs prefixed with `.`: `.cache`, `.pdftext`, `.planning`, `.well-known`.
- Vendor JS: `assets/vendor/<lib>/`.

**Python imports:**
- Builders prepend `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` so they can `from _site_template import ...`. See `scripts/build-aaro.py:11-12`, `scripts/build-nasa.py:8-10`.
- Templates package imports are `from .nav import _href`, `from .lightbox import LIGHTBOX_CSS`, etc. (`scripts/templates/footer.py:15`, `scripts/templates/shared.py:9-10`).

**Asset record keys (inline JSON):**
- Short form: `t, ti, de, ag, cat, date, region, l, u, s, th` — chosen for byte economy in the inlined blob.
- Long form (legacy compat): `type, title, desc, agency, category, date, region, local, url, src, thumb`.

## Where to Add New Code

**New national archive mirror:**
- Pick the tone colour (see CLAUDE.md §3.1; do not deviate).
- Create folder: `<slug>/` with subfolders `<slug>/assets/`, `<slug>/pdfs/`.
- Drop in the shared favicon: `cp assets/favicon.svg <slug>/assets/favicon.svg`.
- Downloader: `scripts/dl-<slug>.sh` (model after `scripts/dl-nasa.sh` for small archives or `scripts/dl-aaro.sh` for two-phase pages+assets).
- Builder: `scripts/build-<slug>.py` (model after `scripts/build-nasa.py` for small; `scripts/build-uk.py` for catalog-style with `_mirror_shared.SHARED_JS`).
- Add to nav: `scripts/templates/nav.py` → append to `MORE` list (line ~35) if non-US, or `PINNED` if a major US archive.
- Add to sync.sh: `scripts/sync.sh` → add `DO_<SLUG>` flag (line 23 area) + interactive picker entry (line 80 area) + dispatch block.
- Add to feeds: `scripts/build-feeds.py` → add to `ARCHIVES` list.
- Add to API: `scripts/build-api.py` → add to its archive table.
- Add to OG: `scripts/build-og.py` → add to `ARCHIVES` table.
- Add to validation: `scripts/validate-manifests.py` → append to `ARCHIVES` list.
- Add to gitignore: `.gitignore` → `<slug>/pdfs/` + optional `<slug>/videos/`.
- Update CLAUDE.md §2 (sources table) and §3.1 (tone colours).
- Run `python3 scripts/sync-nav.py` + `python3 scripts/sync-footer.py` to propagate nav/footer.

**New case detail page (one of the 11 PINNED stories):**
- Append entry to `scripts/_cases.json` (model after existing cases).
- Run `python3 scripts/build-cases.py`.
- Add to `scripts/templates/nav.py:STORIES` list so it appears in the "Story ▾" dropdown.
- Run `python3 scripts/sync-nav.py` to propagate to every page.
- Add lat/lon to `scripts/build-geo.py:CASE_PAGES` list for `/map.html` pin.

**New utility / top-level page (e.g., another `/foo.html`):**
- Create the file at the repo root.
- Inline the SW registration `<script>` (copy from `index.html:27`).
- Inline the canonical nav by running `scripts/sync-nav.py` (after adding to `SITE_PAGES` if it belongs in "Site ▾").
- Inline the canonical footer by running `scripts/sync-footer.py` (after registering in `PAGES` dict).
- Add to `sw.js`'s `SHELL` array so it's precached.
- Add to `sitemap.xml`.

**New template / shared snippet:**
- Add it under `scripts/templates/<name>.py`.
- Re-export from `scripts/_site_template.py` for backwards compat.
- Updating SHARED_CSS / SHARED_JS / LIGHTBOX_* propagates on next builder rerun — no per-page edits needed.

**New CI gate:**
- Add `.github/workflows/<name>.yml` modelled on `sync-nav.yml`.
- Provide a `--check` mode in the underlying script so it returns non-zero on drift.

**New scraped data source (new field on records):**
- Add to scraper output (`scripts/scrape-<slug>.py` or `scripts/spider.py` config).
- Add to manifest schema in `scripts/validate-manifests.py`.
- Add to renderer in `scripts/templates/archive.py:ARCHIVE_JS` (cardHtml + metaFor functions).
- Rebuild affected archives; let the API builder pick it up automatically.

## Special Directories

**`bundles/`:**
- Purpose: War.gov heavy PDFs + DVIDS videos.
- Generated: Via `scripts/download-war.gov.py` and `sync.sh`.
- Committed: **No** — all PDFs, videos, and zip files are gitignored. Lives in GitHub Releases.

**`<slug>/pdfs/`, `<slug>/videos/`:**
- Purpose: Per-archive PDF / video local cache.
- Generated: Per-archive downloader.
- Committed: **No** — gitignored. Lives in `pdfs-v1` / `videos-v1` GH-release tags.

**`<slug>/pages/` (aaro/, nara/):**
- Purpose: Wayback HTML snapshots used by parsers.
- Generated: `scripts/dl-aaro.sh pages`, `scripts/scrape-nara.py`.
- Committed: Yes (small text files; reproducible inputs for parsers).

**`<slug>/.cache/` (aaro/, geipan/, etc.):**
- Purpose: Parser intermediates (`parsed.json`, `evidence.json`, `spider-index.json`).
- Generated: Parsers / spiders.
- Committed: **No** — gitignored. Regenerated by re-running parsers.

**`<slug>/.pdftext/`:**
- Purpose: Extracted plain text per PDF (used by full-text search).
- Generated: `scripts/extract-pdf-text.py` (requires `pdftotext` / poppler).
- Committed: **No** — gitignored.

**`api/`:**
- Purpose: Baked cross-archive JSON dumps.
- Generated: `scripts/build-api.py`, `scripts/build-geo.py`, `scripts/build-pages-index.py`.
- Committed: **Yes** — small, useful for external API consumers, served as CORS-permissive static JSON by GitHub Pages.

**`feeds/`:**
- Purpose: Atom syndication.
- Generated: `scripts/build-feeds.py`.
- Committed: Yes.

**`assets/vendor/`:**
- Purpose: Offline copies of third-party JS / CSS (Leaflet, Lunr, hotkeys, citation, share, related-media).
- Generated: Vendored once per release; not auto-updated.
- Committed: Yes.

**`scripts/__pycache__/`:**
- Purpose: Python bytecode cache.
- Committed: No (gitignored).

---

*Structure analysis: 2026-05-25*
