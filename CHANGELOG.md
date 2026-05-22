# Changelog

All notable changes to **realufo.org** are recorded here. Sync runs
(weekly scrapes) append their own entry automatically; manual releases get a
hand-written one.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project loosely adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added — War.gov / PURSUE Release 02 (May 22, 2026)
- **Release 02 catalogue (64 records)** — second tranche of declassified UAP
  files from the U.S. Department of War, merged into the main archive
  manifest (`uap-data.csv`, now 222 rows: 158 Release 01 + 64 Release 02).
  Breakdown: 51 DVIDS aircrew encounter videos (DOW-UAP-PR050 → PR099),
  7 NASA Apollo / Mercury audio excerpts (NASA-UAP-D008 → D014), 6 documents
  (CIA-UAP-D001 Soviet 1973 intelligence report; ODNI-UAP-D001 USPER narrative;
  DOE-UAP-D001/D002/D003 PANTEX imagery, James Tuck correspondence, Pajarito
  astronomers invitation; DOW-UAP-D017 Sandia Base 1948–1950 correspondence).
- **`bundles/uap052226/`** (5.6 GB, gitignored) — 57 mp4 files, renamed from
  the war.gov bundle's `video_2605_DOD_<id>_DOD_<id>.mp4` form to canonical
  `DOD_<id>.mp4` to match the existing Release 01 naming.
- **`bundles/release_02_document_bundle/`** (70 MB, gitignored) — 6 PDFs.
- **`slideshow-2/`** (10 hero images, ~10 MB, tracked) — Release 02 carousel
  highlights added to the homepage hero strip with `r2: true` flag.
- **Release filter** on `/#archive` — choose All / Release 01 / Release 02.
- **`wargov-r02-v1` GitHub Release tag** — backs all 6 PDFs + 57 mp4 files;
  primary URLs in `release-manifest.json` route through this tag.
- **`scripts/dvids2dod-r02.json`** — DVIDS Video ID → DOD record ID lookup
  table for the 57 Release 02 videos (resolved once against dvidshub.net).
- **`scripts/download-war.gov.py`** rewritten — fixes ROOT to repo root,
  adds Slideshow-2 fetch loop, combined-CSV manifest, and the two new bundle
  archives (`release_02_document_bundle.zip` + `uap052226.zip`).

### Added
- **4 more case detail pages**: Tehran 1976 (AARO), Socorro 1964 (NARA),
  JAL Flight 1628 Alaska 1986 (AARO), Coyne helicopter 1973 (AARO).
  Now 16 case pages total.
- **Programme comparison page** at [`/compare.html`](compare.html) — 15
  national UAP programmes side-by-side. Mandate, host, classification,
  release model, status.
- **How-to-FOIA page** at [`/foia.html`](foia.html) — per-jurisdiction
  guide covering 11 statutes (USA FOIA, UK FOIA, France CADA, Brazil LAI,
  Spain Ley 19/2013, Italy D.lgs. 33/2013, etc.) with sample-letter
  templates.
- **`/api/pages-index.json`** — case + story pages are now Lunr-indexed at
  /search.html. Narrative prose is searchable, not just manifest records.
- **Random-case hotkey** `g r` — picks one of 16 case pages at random.
  Helps casual visitors discover content.
- **Per-archive story.html (14 pages)** mirroring verbatim official-source
  mission text. Sitemap + nav wired.
- **Per-archive GitHub Release tags** (geipan-v1, uk-v1, brazil-v1, …) — empty
  containers ready for >100 MB payloads.
- **Local-vs-source breakdown on /stats.html** — solid bar = mirrored, hatched
  = catalog-entry only. Shows the real harvest gap honestly.
- **Wide spider configs** for argentina-cefae, italy-am, spain-ea,
  uruguay-cridovni, peru-oifaa, nz-nzdf, canada-lac. CI runs all 10 weekly.
- **Bitcoin Lightning donations** via Wallet of Satoshi LNURL on
  [`/donate.html`](donate.html). Anonymous, zero platform fee. QR + copy-button.

### Known gaps (honest disclosure)
- **Most underused-archive seed URLs return 404** as of last test (argentina,
  italy, spain, uruguay, nz). Source agencies relocate frequently; CI will
  retry weekly and catch them when they're up. PRs welcome with current URLs.
- **Chile spider catalogued 60 pages / 276 PDF references** but 274/276 PDFs
  returned 403/404 on direct download. Source URLs preserved in manifest;
  catalog entries remain searchable.
- **AARO + war.gov** are the only archives where the bulk payload (videos,
  PDFs) is locally mirrored. All other archives are predominantly
  catalog-style with source-URL pointers.
- Live public stats dashboard at [`/stats.html`](stats.html).
- Per-event geocode API at [`/api/geo.json`](api/geo.json); `/map.html` now
  shows individual case pins (Rendlesham, Tic-Tac, Gimbal, Phoenix Lights,
  Belgian Wave, Operação Prato, Varginha, Trindade) alongside archive HQs.
- Citation export (BibTeX / RIS / CSL JSON / permalink) on every case page.
- Web Share API button on every case page; clipboard fallback off-mobile.
- Reading-time hint in the meta strip of every case page.
- Three new case detail pages: **Trindade Island 1958**, **Phoenix Lights 1997**,
  **Belgian UFO Wave 1989–90**.
- Glossary at [`/glossary.html`](glossary.html) — 35+ terms, A–Z nav, live filter.
- About page at [`/about.html`](about.html) with editorial rules, licensing.
- Donate page at [`/donate.html`](donate.html) + `.github/FUNDING.yml`. No ad
  networks, ever.
- Global chord hotkeys: `g h / g s / g t / g m / g a / g g / g b / g d`, plus `/` and `?`.
- Atom feeds — [`/feeds/<slug>.xml`](feeds/) per archive + `all.xml` firehose.
- Static API at [`/api/`](api/) — `all.json` (4,778 records), `by-archive.json`,
  `stats.json`. CORS-enabled.
- Service Worker (`sw.js`) + `manifest.webmanifest` → installable PWA, offline-first.
- Vendored Leaflet 1.9.4 locally under `/assets/vendor/leaflet/`. No more unpkg.
- Per-archive Open Graph SVG cards.

### Changed
- **Analytics switched from Plausible to Umami Cloud** (free tier, cookieless).
  Plausible tag fully purged.
- CSP via `<meta http-equiv="Content-Security-Policy">` on every page. Allowlist:
  `'self'`, `cloud.umami.is`, `fonts.googleapis.com`, `fonts.gstatic.com`.
  Tracking-free.
- GEIPAN payload split — 3,343 cases moved into `geipan/cases.json`; main HTML
  shrank from ~3.4 MB to 55 KB. Sync XHR loader keeps the existing render path.
- `prefers-reduced-motion` honoured across every page (scanlines + animations).
- Search at `/search.html` — pill click filters in-page (was: jump); type
  chips (PDF/Video/Imagery/Catalog); year range; `?q=&sites=&types=&from=&to=`
  URL state; `/` hotkey.
- README + CLAUDE.md updated to reflect 15 archives, the "archive" term replacing
  legacy "mirror" wording.

### Security
- `.well-known/security.txt` + [`SECURITY.md`](SECURITY.md) policy.

## [1.0.0] — 2025-12-15

### Added
- Initial public release of realufo.org.
- 8 archives in the first cut: PURSUE (War.gov), AARO, NASA, NARA, GEIPAN,
  UK MoD, FAB Brazil, SEFAA Chile.
- AARO case-detail page (`aaro/details.html`).
- Hero carousel, lightbox, evidence browser per archive.
- Idempotent `scripts/sync.sh` master scraper.

### Notes
- Hosted on GitHub Pages. Large payloads ship via GitHub Releases
  (`videos-v1`, `pdfs-v1`).
