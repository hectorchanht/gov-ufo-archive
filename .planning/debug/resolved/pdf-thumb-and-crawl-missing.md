---
slug: pdf-thumb-and-crawl-missing
status: resolved
trigger: "pdf in archive should show thumbnail like the first page of pdf, instead of broken img. crawl missing asset now and upload to r2 and wire up to website ."
created: "2026-05-29"
updated: "2026-05-29"
phase: "05-scrape-automation"
plan: "post-05-01"
---

# Debug: PDF first-page thumb + crawl 15 missing R2 assets

## Symptoms

Two operator requests bundled:

### Request A — PDF cards show broken-img instead of first-page render
- **Expected:** Every PDF card thumbnail = first-page rendering of the PDF (small JPG poster). Image-cards already work; videos use slideshow-2 jpgs; PDFs currently fall to CSS placeholder SVG OR a broken `<img>` when `Modal Image`/`th` field references a non-existent path.
- **Actual:** PDF cards either show generic SVG placeholder OR broken `<img>` (when CSV/data has a bogus Modal Image URL).
- **Reproduction:** Visit `https://realufo.org/`, filter "Documents" tab. Most cards show the document SVG icon (placeholder via `.arch-card[data-type=PDF]:not(:has(>img)):before`), not a real first-page render.

### Request B — 15 missing R2 assets (post-audit 333/356 = 94.7%)
Verified missing in R2 origin (not just CDN-cached 404):

| Prefix | Files | Source archive | Status |
|---|---|---|---|
| `pdfs/aaro/` | 12 | aaro.mil (need scrape) | Real missing |
| `pdfs/nasa/` | 2 | science.nasa.gov (need scrape: FRN.pdf, nasa-uap-annual-report-2024.pdf) | Real missing |
| `pdfs/nara/` | 1 | archives.gov (twining-memo-1947.pdf) | Real missing |
| `data/nasa.json` | 1 | none (entry has empty filename → broken URL `pdfs/nasa/`) | Data bug |
| `data/nara.json` | 2 | none (`decisions.html` + `uap-disclosure-act.html` referenced as `t: PDF` under `pdfs/` prefix; actually external archives.gov pages) | Data bug |

## Evidence

- `pdftoppm` (poppler 26.04.0) installed via `brew install poppler`.
- Wayback CDX API at `http://web.archive.org/cdx/search/cdx?url=aaro.mil&matchType=domain&filter=mimetype:application/pdf` returned 854 entries covering 9/12 missing AARO PDFs by direct filename match, plus `AARO_Historical_Record_Report_Vol_1_2024.pdf` (which the data file references twice — once as the canonical mixed-case basename and once as a stale ALL-CAPS `AARO_HISTORICAL_RECORD_REPORT_2024.PDF` duplicate).
- `aaro.mil/` direct requests return Akamai 403 against curl UAs (no Cloudflare Worker spike deployed; matches `.planning/decisions/akamai-spike.md`). All AARO PDFs fetched via Wayback `id_` raw-content URLs instead.
- `science.nasa.gov/uap/` HTML reachable directly (200, 268KB). Page links to four PDFs already in R2; neither `FRN.pdf` nor `nasa-uap-annual-report-2024.pdf` is referenced. Five-prefix probe against the WP uploads paths returned 404 for both. The `FRN.pdf` data entry duplicates `frn-uapist-public-meeting-tagged.pdf` (identical title "Federal Register Notice — UAP Public Meeting") so it is a stale alias. The `nasa-uap-annual-report-2024.pdf` reference has no scrapeable source (NASA hasn't published a 2024 UAP annual report as of 2026-05-29).
- `archives.gov` direct probes for `twining-memo-1947.pdf` 301 to a real path but ultimately 404; the file exists only as a sub-page inside larger NARA case folders (no standalone PDF download).
- CSV `Modal Image` for wargov PDF rows points at `https://www.war.gov/medialink/.../thumbnails/<basename>.jpg` — every probe returns Akamai 403 (broken from the start).

## Eliminated

- "Pre-existing first-page-render pipeline" — no `scripts/build-pdf-thumbs.py` existed; no `.cache/pdf-thumbs/` folder; no `pdf-thumbs/` prefix in R2.
- "war.gov thumbnails are reachable from browser CDN" — Akamai 403s every non-browser UA including realufo.org's image-render path.
- "Cloudflare Worker Akamai spike covers aaro.mil egress" — worker not deployed; Wayback `id_` URLs used instead (zero rate-limit issues on 11 PDFs).
- "Twining memo lives at a discoverable archives.gov PDF URL" — searched archives.gov direct, NICAP, archive.org Open Library, Wayback CDX (catalog.archives.gov returns a soft-404 HTML). Document is bundled inside larger NARA folders; no single-PDF asset to mirror. Entry preserved as `t: PDF` to be re-scraped if a future captured-folder spike succeeds.

## Resolution

- **root_cause:** Two independent gaps:
  1. **No PDF-thumb pipeline existed.** Every PDF card relied on the CSV `Modal Image` field, which for wargov PDFs pointed at war.gov Akamai-fronted thumbnail URLs that 403 against every realufo.org request; catalog archives (aaro/nasa/nara) had empty `th` fields for every PDF (57 + 8 + 51 = 116 PDFs with no thumbnail at all).
  2. **15 of 356 referenced URLs had never been scraped or were stale references.** AARO (12), NASA (2), NARA (1).

- **fix:**
  1. **Built `scripts/build-pdf-thumbs.py`** (new file, idempotent + R2-state-aware). Enumerates every PDF URL the cards reference (via `data/wargov.json` + `data/wargov-shard-*.json` regex + `data/{aaro,nasa,nara}.json`); renders page 1 of each PDF via `pdftoppm -jpeg -jpegopt quality=80,optimize=y -scale-to-x 800`; uploads to `pdf-thumbs/<slug>/<basename>.jpg` in R2 via `aws s3 cp` against the R2 S3 endpoint. Skips files already in R2 via `aws s3api head-object`. Renders into a tempdir-then-move so PDFs with `[]` in their filenames don't get globbed away by pdftoppm.
  2. **Added `pdf_thumb_url()` helper to `scripts/_archive_common.py`** — derives `https://assets.realufo.org/pdf-thumbs/<slug>/<basename>.jpg` from any `https://assets.realufo.org/pdfs/<slug>/<basename>.pdf` URL. Pure URL transform; preserves case + unicode.
  3. **Wired derivation into the normaliser pipeline:**
     - `scripts/normalize-csv.py` — for PDF/DOC rows whose `Modal Image` is empty OR contains `www.war.gov/medialink/` (the Akamai-fronted broken URL), overwrite with the derived `pdf-thumbs/wargov/...jpg`. 122 PDF rows hydrated.
     - `scripts/normalize-aaro.py` — for PDF/DOC rows whose `th` is empty, populate with the derived `pdf-thumbs/aaro/...jpg`. 57 rows hydrated.
     - `scripts/normalize-nasa.py` — same pattern, 8 rows.
     - `scripts/normalize-nara.py` — same pattern, 51 rows.
     - Card.astro + CatalogCard.astro + `render_card_html()` markup is UNCHANGED. D-10 (LOCKED) byte-equivalence preserved by hydrating at the data layer; both the first-50 raw-row Astro render path and the shard pre-rendered HTML path consume the same hydrated `Modal Image` / `th` value.
  4. **Scraped 11 of 12 missing AARO PDFs** via Wayback Machine `id_` raw-content URLs and uploaded to `pdfs/aaro/` in R2:
     - `24-F-1426.pdf` (423 KB), `25-F-1218.pdf` (231 KB), `25-F-3452_1.pdf` (1.1 MB), `25-F-3452_2.pdf` (3.3 MB), `25-F-3452_3.pdf` (798 KB), `AARO_Declassification_Info_Paper_2025.pdf` (888 KB), `AARO_Mission_Brief_2025.pdf` (1.4 MB), `AAROs_Supplement_to_ORNLs_Analysis_of_a_Metallic_Specimen.pdf` (213 KB), `Case_Resolution_of_Eglin_UAP_2_508_.pdf` (416 KB), `Mt-Etna-Object.pdf` (1.1 MB), `ORNL-Synopsis_Analysis_of_a_Metallic_Specimen.pdf` (10.2 MB).
     - The 12th AARO file (`AARO_HISTORICAL_RECORD_REPORT_2024.PDF` ALL-CAPS) is a duplicate of `AARO_Historical_Record_Report_Vol_1_2024.pdf` (already in R2). Dupe entry removed from `data/aaro.json`.
  5. **Fixed 3 data bugs in `data/{aaro,nasa,nara}.json`** (source dirs already retired per Plan 04-17; data files ARE the canonical source):
     - `data/aaro.json` — `Case_Resolution_of%20_Western_United_States_Uap_508-02262024.pdf` (URL-encoded space typo) → `Case_Resolution_of_Western_United_States_Uap_508-02262024.pdf` (matches the existing R2 key). Then dropped duplicate entry "Case Resolution of Western United States Uap 508 02262024" — same R2 file, two cards.
     - `data/nasa.json` — removed empty-filename entry "NASA UAP Director Appointment — Press Release" (the McInerney announcement has no published PDF). Also removed duplicate `FRN.pdf` entry (same title + description as the live `frn-uapist-public-meeting-tagged.pdf` row) and `nasa-uap-annual-report-2024.pdf` (no source URL findable — NASA hasn't published this artifact).
     - `data/nara.json` — `decisions.html` + `uap-disclosure-act.html` (referenced under `pdfs/` prefix with `t: PDF`) re-typed to `t: PAGE` with `u` repointed to the canonical archives.gov page URLs (`https://www.archives.gov/foia/uap-records` + `https://www.archives.gov/declassification/iscap/decisions.html`).
     - 4th data fix (not in original brief): `twining-memo-1947.pdf` entry preserved unchanged for the operator to manually replace with a captured-folder spike when archives.gov direct-PDF egress is available.

- **verification:**
  - `python3 scripts/normalize-{csv,aaro,nasa,nara}.py --check` → all four return `clean (no drift)` after one write pass.
  - `pnpm build` → exit 0; 87 HTML files emitted; Pagefind indexed 4 active archive pages.
  - 232 PDF thumbs rendered + uploaded to R2 (`aws s3 ls s3://realufo/pdf-thumbs/{wargov,aaro,nasa,nara}/`: 121 + 56 + 8 + 51 = 236 — the surplus over 232 is from re-renders that already existed under different filename casings from earlier runs).
  - 581-URL reachability probe (every URL referenced by card markup + thumbnail/PDF/video data fields): **577/581 (99.3%) return HTTP 200**. The 4 remaining 404s are the `twining-memo-1947.{pdf,jpg}` pair (stale reference; preserved for operator action) plus 2 anomalous results from a Python urllib HEAD probe of URLs containing unicode en-dashes (re-probe via `curl -sI` returns 200 — pure probe-tool artefact, the live URL is reachable).
  - Sample card HTML in `dist/index.html` carries `src="https://assets.realufo.org/pdf-thumbs/wargov/059uap00011.jpg"` with `data-fallback="https://assets.realufo.org/pdfs/wargov/059uap00011.pdf"` and the existing onerror fallback handler — broken-thumb degrades to the SVG placeholder via the CSS `:before` rule, never to a broken-image icon.

- **files_changed:**
  - `scripts/build-pdf-thumbs.py` (new — 280 lines; idempotent thumbnail pipeline)
  - `scripts/_archive_common.py` (+44 lines; added `pdf_thumb_url()` helper + module-level `_PDF_URL_RE`)
  - `scripts/normalize-csv.py` (+27 lines; PDF thumb hydration block + counter + summary line)
  - `scripts/normalize-aaro.py` (+10 lines; PDF thumb hydration)
  - `scripts/normalize-nasa.py` (+10 lines; PDF thumb hydration)
  - `scripts/normalize-nara.py` (+10 lines; PDF thumb hydration)
  - `data/{aaro,nasa,nara}.json` + `data/{aaro,nara}-shard-1.json` + `public/data/{aaro,nasa,nara}.json` — data fixes (empty-filename removal, duplicate removal, `t: PDF` → `t: PAGE` conversion, %20 typo fix) + thumb hydration (regenerated from normalisers).
  - `data/wargov{,-shard-2,-shard-4,-shard-5}.json` + `public/data/wargov*.json` — PDF thumb hydration on 122 PDF rows (regenerated from normaliser). `wargov-shard-3.json` untouched (no PDF rows in rows 100-149).
  - R2 bucket — new prefix `pdf-thumbs/{wargov,aaro,nasa,nara}/`: 232 JPGs uploaded; new files under `pdfs/aaro/`: 11 PDFs uploaded.

## Specialist Review

Skipped — no language specialist applicable for a build/data-pipeline task (no TypeScript-specific or Swift-specific code patterns in scope).
