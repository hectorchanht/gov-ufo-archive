# realufo.org — every official UAP archive, in one place

**Live at [realufo.org](https://realufo.org/)** · 15 government UAP archives
side-by-side, offline-first, mobile-first, zero build tooling.

| # | Archive | Source | Entry point |
| --: | --- | --- | --- |
| 1 | **PURSUE — Department of War / Release 01** | <https://www.war.gov/UFO/> | [`/`](index.html) |
| 2 | **AARO — All-domain Anomaly Resolution Office** | <https://www.aaro.mil/> | [`/aaro/`](aaro/index.html) |
| 3 | **NASA UAP Independent Study Team** | <https://science.nasa.gov/uap/> | [`/nasa/`](nasa/index.html) |
| 4 | **NARA — Project Blue Book + JFK + UAP** | <https://catalog.archives.gov/> | [`/nara/`](nara/index.html) |
| 5 | **France — GEIPAN (CNES)** | <https://www.cnes-geipan.fr/> | [`/geipan/`](geipan/index.html) |
| 6 | **UK — National Archives MoD files** | <https://discovery.nationalarchives.gov.uk/> | [`/uk/`](uk/index.html) |
| 7 | **Brazil — Força Aérea Brasileira** | <https://www.fab.mil.br/> | [`/brazil/`](brazil/index.html) |
| 8 | **Chile — CEFAA / SEFAA (DGAC)** | <https://www.sefaa.cl/> | [`/chile/`](chile/index.html) |
| 9 | **Argentina — CEFAe** | <https://www.argentina.gob.ar/fuerzaaerea/cefae> | [`/argentina/`](argentina/index.html) |
| 10 | **Canada — LAC / Project Magnet** | <https://www.bac-lac.gc.ca/> | [`/canada/`](canada/index.html) |
| 11 | **Italy — Aeronautica Militare** | <https://www.aeronautica.difesa.it/> | [`/italy/`](italy/index.html) |
| 12 | **NZ — NZ Defence Force** | <https://www.nzdf.mil.nz/> | [`/nz/`](nz/index.html) |
| 13 | **Peru — OIFAA (Fuerza Aérea)** | <https://www.gob.pe/fap> | [`/peru/`](peru/index.html) |
| 14 | **Spain — Ejército del Aire** | <https://ejercitodelaire.defensa.gob.es/> | [`/spain/`](spain/index.html) |
| 15 | **Uruguay — CRIDOVNI** | <https://www.fau.mil.uy/> | [`/uruguay/`](uruguay/index.html) |

Cross-archive search lives at [`/search.html`](search.html).

Every archive shares the same visual language and control logic — a
cinematic hero carousel of real declassified imagery, a headlines strip,
and a filterable, sortable, paginated **evidence browser** that surfaces
every artifact with full context (agency, location, incident date,
VIRIN / DVIDS ID, redaction status, case status). Every file you can see
is served from the local archive when present — and falls back to the
official source URL otherwise.

---

## What's in the box

```
.
├── index.html               # PURSUE — war.gov/UFO landing
├── search.html              # cross-archive search
├── uap-release001.csv       # official Release 01 manifest (158 records)
├── slideshow/               # 17 highlight images
├── bundles/
│   ├── Release_1/           # 130 docs + images (gitignored — restored via sync)
│   ├── Release_1.zip        # official zip (gitignored)
│   ├── uapvideos/           # 28 DVIDS UAP videos (gitignored)
│   └── uapvideos.zip        # official zip (gitignored)
├── assets/                  # site chrome + shared favicon.svg (classic disk UFO)
│
├── aaro/                    # AARO archive (cases, FOIA, videos, details.html)
├── nasa/                    # NASA UAP study + briefings
├── nara/                    # NARA Blue Book / JFK / UAP catalog
├── geipan/                  # France — 3343 GEIPAN cases
├── uk/                      # UK National Archives — TNA Discovery API
├── brazil/                  # Brazil FAB / Operação Prato
├── chile/                   # Chile SEFAA
├── argentina/               # CEFAe
├── canada/                  # LAC / Project Magnet
├── italy/                   # Aeronautica Militare
├── nz/                      # NZDF
├── peru/                    # OIFAA
├── spain/                   # Ejército del Aire
├── uruguay/                 # CRIDOVNI
│
├── download.py              # war.gov downloader (TLS-impersonating curl_cffi)
└── scripts/
    ├── sync.sh              # ⭐ master entry — run this
    ├── dl-<slug>.sh         # per-archive downloader
    ├── build-<slug>.py      # per-archive site generator
    ├── build-details.py     # long-form text pages
    ├── parse-aaro.py        # parse AARO page HTML → structured JSON
    ├── extract-evidence.py  # build the AARO evidence map
    └── spider.py            # generic source-page crawler
```

> Every `index.html` is **self-contained** — no build step, no web server.
> Open in any browser. The only reason to run the downloader is to populate
> the bulky payloads (PDFs, videos) excluded from Git.

---

## Quick start

### 1. Clone

```bash
git clone https://github.com/<you>/war-gov-ufo-release
cd war-gov-ufo-release
```

### 2. Install the one dependency

```bash
pip install curl_cffi
```

`curl_cffi` is required for the war.gov + AARO sides because both Akamai
hosts use TLS-fingerprint bot protection. `curl_cffi` wraps
`curl-impersonate`, which replicates a real Chrome handshake byte-for-byte.

Everything else uses only the Python and POSIX shell standard libraries.

### 3. Populate the archive

```bash
./scripts/sync.sh
```

That single command:

1. Runs `download.py` to pull the war.gov payloads
2. Snapshots all aaro.mil pages via the Wayback Machine
3. Downloads every official AARO UAP video from the DVIDS CDN
4. Crawls every other national archive (GEIPAN, TNA, FAB, SEFAA, …)
5. Re-parses everything and rebuilds every `index.html` so the
   `LOCAL / SOURCE` badges match what's actually on disk

It's **idempotent** — files already on disk are skipped. Re-running it picks
up only what's new.

### 4. Open in a browser

```bash
open index.html                   # macOS
xdg-open index.html               # Linux
start index.html                  # Windows
```

That's it. Every archive works offline from this point on.

---

## Dev loop (optional but recommended)

Zero build tooling required. The two helpers below make iteration faster
without locking the repo into a JS framework.

### live-server — auto-reload browser on file save

```bash
# One-time install:
npm install -g live-server

# Run from repo root — opens http://localhost:8765 and reloads on every save
live-server --port=8765 --no-browser .
```

Plain alternative if you don't want npm:

```bash
python3 -m http.server 8765
```

Static-only, no reload, but zero dependencies.

### watchexec — rebuild HTML on `.py` / `.csv` change

```bash
# One-time install (Homebrew):
brew install watchexec

# Watch the build sources; rebuild every mirror on change:
watchexec -w scripts -w uap-release001.csv -e py,csv -- \
  bash -c 'python3 scripts/build-wargov.py \
        && python3 scripts/build-aaro.py \
        && python3 scripts/build-nasa.py \
        && python3 scripts/build-nara.py'
```

Pair the two: `live-server` reloads the browser the moment `watchexec`
finishes regenerating HTML — full dev loop without a bundler.

### Continuous integration (already wired)

| Workflow | Trigger | Job |
| --- | --- | --- |
| `scrape.yml`        | Monday 06:00 UTC + manual | Re-scrape every source, rebuild HTML, auto-commit. |
| `links.yml`         | every push to `*.html`, weekly Monday 07:00 UTC, manual | [lychee] broken-link check across all 44 pages. Ignored hosts in `.lycheeignore`. |
| `html-validate.yml` | every push to `*.html`, manual | [html-validate] HTML5 validation. Config: `.htmlvalidate.json`. |
| `lighthouse.yml`    | every push to `*.html` / `*.css` / `*.js`, manual | [Lighthouse CI] Core Web Vitals + a11y + SEO on 8 representative URLs. Config: `.lighthouserc.json`. |

No tokens needed for the first three. For Lighthouse CI report comments
on PRs, add `LHCI_GITHUB_APP_TOKEN` repo secret (optional — runs anyway).

---

## How this project works

Static HTML. Zero runtime dependencies. Zero JS bundlers. Every page is
generated from one of three sources:

1. **Per-mirror build scripts** (`scripts/build-<slug>.py`) — emit
   `<slug>/index.html` by merging a curated `ASSETS` list with discovered
   records from the cache and the GitHub release manifest.
2. **Hand-written HTML** for utility + story pages — kept as plain HTML
   in the repo. Shared components (`<nav>`, `<footer>`) get rewritten by
   `sync-*.py` scripts so every page stays in lock-step with the canonical
   builder functions in `scripts/_site_template.py`.
3. **One-off generators** — `build-api.py`, `build-feeds.py`,
   `build-geo.py`, etc. emit ancillary JSON / Atom / SVG artifacts.

### Pipeline (bottom-up)

```
┌─ external sources ──────────────────────────────────────────────────┐
│  uap-release001.csv       (Department of War CSV, hand-curated)     │
│  KNOWN_RECORDS in scrape-*.py  (per-archive seed lists)             │
│  aaro.mil  · science.nasa.gov  · catalog.archives.gov               │
│  discovery.nationalarchives.gov.uk  · cnes-geipan.fr  · etc.        │
└────────────────────────┬────────────────────────────────────────────┘
                         │
            ┌────────────┼────────────────┐
            │            │                │
   ┌────────▼─┐   ┌──────▼───────┐  ┌────▼────────────┐
   │ scrape-* │   │ harvest-tna  │  │  spider.py      │
   │  .py     │   │  .py (UK)    │  │  (catalog BFS)  │
   └────┬─────┘   └──────┬───────┘  └────┬────────────┘
        │                │               │
        └─→  <mirror>/.cache/{scraped-index, tna-index, spider-index}.json
                         │
                         ▼
┌─ release backfill ──────────────────────────────────────────────────┐
│  scripts/backfill-release.py  --upload                              │
│    Diffs every PDF/MP4 URL across mirrors against pdfs-v1 + videos-v1│
│    Downloads missing → uploads to GitHub Releases                   │
│    Writes release-manifest.json  (basename → release-download URL)  │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─ build (per-mirror HTML) ───────────────────────────────────────────┐
│  scripts/build-aaro.py        scripts/build-geipan.py               │
│  scripts/build-nasa.py        scripts/build-uk.py                   │
│  scripts/build-nara.py        scripts/build-brazil.py               │
│  scripts/build-chile.py       scripts/build_batch3.py  (7 smaller)  │
│  scripts/build-details.py     scripts/build-wargov.py               │
│                                                                     │
│  Each merges:                                                       │
│    - hand-curated ASSETS list                                       │
│    - <mirror>/.cache/*-index.json   (scrape/spider/harvest results) │
│    - release-manifest.json          (URL rewrites for downloadable) │
│  Then imports scripts/_site_template.py for nav, head, lightbox,    │
│  shared CSS, shared JS, and emits the final HTML.                   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─ canonicalise shared components in hand-written HTML ───────────────┐
│  scripts/sync-nav.py     — rewrites <nav class="primary">           │
│  scripts/sync-footer.py  — rewrites <footer>                        │
│  (more to come: lightbox, archive grid)                             │
│                                                                     │
│  Both expose a `--check` mode used as a CI gate so drift can't      │
│  decay silently.                                                    │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─ ancillary artifacts ───────────────────────────────────────────────┐
│  build-api.py   → api/all.json, api/by-archive.json, api/stats.json │
│  build-feeds.py → feeds/<mirror>.xml  (Atom)                        │
│  build-geo.py   → api/geo.json  (case-pin coordinates for /map.html)│
│  build-og.py    → */assets/og.svg  (per-archive Open Graph)         │
│  validate-manifests.py — sanity-check every embedded JSON           │
│  check-sources.py      — HEAD every external URL, write dead-links.*│
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
            git push  →  GitHub Pages
            (static HTML served direct, no build at edge)
```

### Single source of truth

`scripts/_site_template.py` holds the canonical builders for every
shared UI piece:

| Builder | What it returns | Used by |
| --- | --- | --- |
| `make_nav(slug, depth)` | `<nav class="primary">…</nav>` with USA pins + Site ▾ + Story ▾ + Nations ▾ | every build script + `sync-nav.py` |
| `make_footer(variant, depth, meta)` | minimal / mirror / root footer | `sync-footer.py`, build scripts |
| `make_head(title, …)` | full `<head>` with meta + fonts + CSS injection | build scripts |
| `SHARED_CSS` / `SHARED_JS` | drop-in CSS + JS string | every build script |
| `LIGHTBOX_HTML` | media viewer markup | every build script |
| `PINNED` / `SITE_PAGES` / `STORIES` / `MORE` | lookup tables for the nav | `make_nav()` |
| `I18N` | translation dictionary (6 languages) | `make_nav`, `SHARED_JS` |

Change `PINNED` (or `STORIES`) once → run `sync-nav.py` → every page
across the repo updates. CI fails the build if anyone hand-edits a
`<nav>` block out of sync.

### Order of operations on a full sync

```bash
./scripts/sync.sh --all          # = the wrapper for everything below

# 1. Bulk file fetch (local mirror — gitignored, not deployed)
scripts/dl-aaro.sh   scripts/dl-nasa.sh   scripts/dl-nara.sh   …

# 2. External source discovery → write per-mirror .cache JSON
scripts/scrape-nasa.py    scripts/scrape-nara.py
scripts/scrape-aaro.py    scripts/scrape-geipan.py
scripts/scrape-uk.py      scripts/scrape-brazil.py
scripts/scrape-chile.py   scripts/harvest-tna.py
scripts/spider.py         # generic BFS crawler, ~10 site configs

# 3. Release backfill — download missing PDFs, upload to GH release,
#    refresh release-manifest.json
scripts/backfill-release.py --upload

# 4. Emit per-mirror HTML (consumes step 2 + 3 results)
scripts/build-nasa.py    scripts/build-nara.py
scripts/build-aaro.py    scripts/build-geipan.py
scripts/build-uk.py      scripts/build-brazil.py
scripts/build-chile.py   scripts/build_batch3.py
scripts/build-details.py scripts/build-wargov.py

# 5. Canonicalise nav + footer across the 44 hand-written HTML files
scripts/sync-nav.py
scripts/sync-footer.py

# 6. Ancillary outputs
scripts/build-api.py     scripts/build-feeds.py
scripts/build-geo.py     scripts/build-og.py
scripts/validate-manifests.py
scripts/check-sources.py

# 7. Ship
git push origin main
```

`scripts/update_all.sh` wraps the typical subset; `sync.sh` is the
interactive entry point.

### CI pipeline (`.github/workflows/`)

| Workflow | Trigger | Stages run |
| --- | --- | --- |
| `scrape.yml`        | Monday 06:00 UTC + manual | scrapers → spider → builds → api/feed/geo → sitemap → commit & push |
| `sync-nav.yml`      | push / PR touching *.html or template | `sync-nav.py --check` (drift gate) |
| `sync-footer.yml`   | push / PR touching *.html or template | `sync-footer.py --check` (drift gate) |
| `html-validate.yml` | push / PR on *.html | `npx html-validate` over every file |
| `links.yml`         | push, PR, weekly Mon 07:00 UTC | lychee link check + `.lycheeignore` |
| `lighthouse.yml`    | push / PR on *.html / *.css / *.js | Lighthouse CI on 8 representative URLs |

All workflows fail the build on regression — no nav drift, no broken
links, no malformed HTML, no Core Web Vitals collapse can land silently.

---

## Hosting on GitHub Pages

The repo is **GitHub-Pages-ready** out of the box.

The `.gitignore` keeps the repo under 1 GB by excluding the bulky payloads:

- `bundles/Release_1.zip`, `bundles/uapvideos.zip` (~2.5 GB combined)
- `bundles/uapvideos/` (DVIDS bulk videos, 1.2 GB)
- `aaro/videos/` (32 AARO videos, 2.7 GB)
- Any single PDF over GitHub's 100 MB single-file limit

Result: a `git push`-friendly repo of about 150 MB.

On the live site, any asset that wasn't committed shows a `SOURCE` badge and
links straight back to the official URL. Visitors who want a fully local
copy just clone the repo and run `./scripts/sync.sh`.

### How the local-vs-source switch actually works

Every asset card carries **both** a local relative path and the original
source URL. The page chooses dynamically:

- **Images** use `<img src="./local.jpg" onerror="this.src='source_url'">` —
  if the local file is missing (e.g. on GitHub Pages where the file was
  gitignored), the browser silently swaps in the official URL.
- **Buttons** always show a `Source ↗` chip alongside the `Download` chip
  when both a local file and a source URL exist. Two routes, always one
  that works.
- **The HTML never has to change**. The build scripts regenerate the
  embedded manifest from current disk state on every run — newly-downloaded
  files automatically pick up local routing, missing files automatically
  fall back to source.

So the workflow is:

```bash
./scripts/sync.sh        # downloads new files, rebuilds manifests
git add -A && git commit # commit whatever the .gitignore lets through
git push                 # ship — visitors get the right route per asset
```

### Enable Pages

```bash
git init
git add .
git commit -m "Initial archive"
gh repo create war-gov-ufo-release --public --source=. --push
# then in repo Settings → Pages, set Source = main branch, root.
```

---

## Keeping the archive current (cron / scheduled)

Multiple governments release new materials on a rolling basis. Re-run
`sync.sh` periodically to capture new tranches:

### Weekly cron (Linux / macOS)

```cron
# Every Monday at 03:00 local time
0 3 * * 1   cd /path/to/war-gov-ufo-release && ./scripts/sync.sh >> sync.log 2>&1
```

### Faster, with auto-commit (optional)

Wrap `sync.sh` to commit and push any new files automatically:

```bash
#!/usr/bin/env bash
cd "$(dirname "$0")"
./scripts/sync.sh >> sync.log 2>&1
git add -A
git diff --quiet --staged || git commit -m "sync: $(date -u +%Y-%m-%dT%H:%MZ)"
git push
```

### macOS launchd

```xml
<!-- ~/Library/LaunchAgents/com.user.uap-archive-sync.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
  <key>Label</key><string>com.user.uap-archive-sync</string>
  <key>WorkingDirectory</key><string>/Users/you/code/war-gov-ufo-release</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string>
    <string>scripts/sync.sh</string>
  </array>
  <key>StartCalendarInterval</key><dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>3</integer>
  </dict>
  <key>StandardOutPath</key><string>sync.log</string>
  <key>StandardErrorPath</key><string>sync.log</string>
</dict></plist>
```

`launchctl load ~/Library/LaunchAgents/com.user.uap-archive-sync.plist`

### GitHub Actions (archive + auto-publish)

For a hands-off, public archive: schedule sync in GitHub Actions and let it
push directly to Pages.

```yaml
# .github/workflows/sync.yml
name: Weekly sync
on:
  schedule: [{ cron: "0 3 * * 1" }]
  workflow_dispatch:
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install curl_cffi
      - run: ./scripts/sync.sh --no-videos    # videos are too large for Pages
      - name: Commit any new files
        run: |
          git config user.name "uap-archive"
          git config user.email "uap-archive@users.noreply.github.com"
          git add -A
          git diff --quiet --staged || git commit -m "sync: $(date -u +%Y-%m-%d)"
          git push
```

---

## Selective sync flags

```bash
./scripts/sync.sh                # interactive picker (multi-select)
./scripts/sync.sh --all          # full run
./scripts/sync.sh --aaro-only    # one archive only (replace slug)
./scripts/sync.sh --no-videos    # skip the big AARO videos (≈2.7 GB)
./scripts/sync.sh --no-build     # download only, no HTML rebuild
```

Useful combos:

```bash
# Day 1: quick browsable archive without the multi-gig video downloads
./scripts/sync.sh --no-videos

# Day 2: pull the videos in a background terminal
bash scripts/dl-aaro.sh assets

# Anytime: refresh just one archive after a new case release
./scripts/sync.sh --chile-only
```

---

## Why two source strategies?

| Source | Why it's hard | What we use |
| --- | --- | --- |
| `www.war.gov`, `www.aaro.mil` | Akamai TLS fingerprinting blocks `curl`, `wget`, `requests`. | `curl_cffi` (Chrome TLS impersonation), Wayback fallback. |
| `cdn.dvidshub.net`, AARO cloudfront | None — public CDN. | Direct `curl`. |
| `discovery.nationalarchives.gov.uk` | Official Discovery JSON API — well-mannered. | Direct paged JSON. |
| `cnes-geipan.fr`, `sefaa.cl`, `fab.mil.br`, … | Plain HTML; sometimes Cloudflare-fronted. | `spider.py` (BFS crawl + rate limit). |

If `curl_cffi` still gets 403 from war.gov, you're probably on a known
data-center / VPN IP that Akamai blocks. Run from a residential or
corporate-office connection.

---

## Page features (every archive)

- **Cinematic hero carousel** rotating through declassified imagery and
  official UAP videos
- **Headlines strip** — the mission distilled into 6 cards
- **Evidence browser** with shared control logic:
  - 5–8 type tabs
  - Sort by status / title / date / agency
  - Filter by region, agency, case status, redaction
  - Full-text search across title, description, location, VIRIN, DVIDS ID
  - 12 / 24 / 48 / 96 per page
  - Pagination with "1 2 … 6 7 8 … N" + page info
- **Full context per asset** — agency, incident date & location, release
  date, VIRIN, DVIDS ID, PDF / video pairings, alt text, case status badge
  (Unresolved / Undergoing Analysis / Resolved / Closed)
- **Click-to-preview lightbox** — images, videos, audio, and PDFs all open
  in-place; `Esc` to close, ←/→ to navigate, swipe on mobile
- **`LOCAL` / `SOURCE` badges** so it's always clear whether a file is on
  disk or links back to the official URL
- **Cross-archive search** at `/search.html` with `?q=` deep links and
  `/` hotkey to focus the input

---

## Notes & limits

- Public-domain attribution per source jurisdiction (US 17 U.S.C. § 105,
  UK OGL v3, France Loi 78-753, Brazil LAI 12.527/2011, Chile 20.285,
  Argentina 27.275, Italy D.lgs. 33/2013, Spain 19/2013, Uruguay 18.381,
  …). Page content reproduced verbatim from the original publications.
- About 22 / 58 AARO PDFs and 13 / 21 AARO images **were never archived by
  the Wayback Machine** and no longer resolve from aaro.mil directly because
  of Akamai. They appear with the `SOURCE` badge and link to the original
  URL; click-through may 403.
- The Vercel/Next/React skill hints in the commit history come from
  unrelated tooling — this project is a pure static HTML archive. No build
  step. No runtime. No framework.

---

## License

Code in `scripts/` and `download.py`: MIT.
Archived content: each source's national public-domain regime (see above).
