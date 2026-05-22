# Changelog

All notable changes to **realufo.org** are recorded here. Sync runs
(weekly scrapes) append their own entry automatically; manual releases get a
hand-written one.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project loosely adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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
