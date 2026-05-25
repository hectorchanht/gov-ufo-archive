# External Integrations

**Analysis Date:** 2026-05-25

## Summary — integration model

realufo.org has **no runtime backend integrations**. Every "integration" is
either:

1. **Build-time** — a Python or Bash scraper hits an upstream government
   source and writes results into a repo file (HTML page, JSON manifest, PDF
   under `<archive>/pdfs/`). All credentials-free, all public URLs.
2. **Static-CDN** — large binaries are mirrored to **GitHub Releases**, and
   the browser fetches them directly via the release-download URL.
3. **Browser-side, no auth** — Google Fonts CSS, Umami analytics beacon,
   Leaflet vendored locally, Lunr index vendored locally.

There are no API keys, no OAuth flows, no webhooks, no databases. The
`.well-known/security.txt` confirms: "We are not running: User
authentication, accounts, or session state; A backend, database, or any
server-side code."

## APIs & External Services

### Runtime (browser fetches these)

**Analytics:**
- **Umami** (`https://cloud.umami.is/script.js`, `data-website-id=
  9c4f36ef-30ad-4d76-947a-1724fe6acdba`)
  - Purpose: cookieless page-view counts.
  - Loaded by: every HTML page in `<head>` via `<script defer>`.
  - Allowed by CSP: `script-src ... https://cloud.umami.is` and
    `connect-src 'self' ... https://cloud.umami.is`.
  - No SDK, just the tag. No client-side identifier.

**Web fonts:**
- **Google Fonts** — `https://fonts.googleapis.com` (CSS) and
  `https://fonts.gstatic.com` (woff2 files)
  - Loaded as `<link rel="stylesheet">` referencing
    `JetBrains+Mono:wght@400;500;700` + `Source+Serif+4:ital,wght@…`.
  - Preconnected in `<head>`.
  - CLAUDE.md §3.3 bans a third font; no other Google Fonts are pulled.

**Wayback Machine** — used by some runtime fallback JS in `search.html` to
re-resolve dead source links (`connect-src 'self' https://web.archive.org
https://*.archive.org` in CSP).

**Embed iframes** — `frame-src 'self' https://www.youtube.com
https://www.youtube-nocookie.com https://player.vimeo.com`. The lightbox
detects YouTube / Vimeo / `youtu.be` URLs and rewrites them to the
nocookie / player embed form before injecting an `<iframe>`. No SDK; just
URL rewriting.

### Build-time (Python / Bash scrapers)

Each upstream archive has at least one scraper. All credentialless. Most
also fall back to the **Wayback Machine** (`web.archive.org`) when the
direct request fails.

**War.gov / PURSUE:**
- Direct URL: `https://www.war.gov/UFO/`
- Akamai-protected — defeats `curl`, `wget`, `requests`.
- Mitigation: `curl_cffi` with rotating Chrome TLS-impersonation profiles
  (chrome124 → chrome120 → chrome116 → chrome110) in
  `download.py` / `scripts/download-war.gov.py`.
- Also hits `cdn.dvidshub.net` and `media.defense.gov` for DVIDS / DOD
  video binaries — both are direct CDN URLs, no auth.

**AARO:**
- `https://www.aaro.mil/` (12 main pages) + cloudfront video host
  `https://d34w7g4gy10iej.cloudfront.net/`
- Aggressive bot protection on aaro.mil itself → mirrored exclusively via
  the Wayback Machine in `scripts/dl-aaro.sh`:
  - `http://archive.org/wayback/available?url=…` to get the closest
    snapshot timestamp;
  - CDX fallback at
    `https://web.archive.org/cdx/search/cdx?url=…&filter=statuscode:200`;
  - Download via `https://web.archive.org/web/<ts>id_/<url>` (or `im_` for
    images, `if_` for video).
- Videos download direct from cloudfront with a Chrome 131 User-Agent.

**NASA UAP:** `https://science.nasa.gov/uap/`, `https://smd-cms.nasa.gov`,
`https://www.nasa.gov` — direct via `scripts/dl-nasa.sh` /
`scripts/scrape-nasa.py`. No bot protection in practice.

**NARA:** `https://catalog.archives.gov/`, `https://www.archives.gov`,
`https://www.cia.gov`, `https://vault.fbi.gov` — direct via
`scripts/dl-nara.sh` / `scripts/scrape-nara.py` /
`scripts/harvest-tna.py`.

**France GEIPAN (CNES):** `https://www.cnes-geipan.fr/` —
`scripts/dl-geipan.sh`. Public-domain PDFs and case videos served direct
from CNES under `/sites/default/files/`. Also imports
`https://www.cnes.fr` references.

**UK National Archives:** `https://discovery.nationalarchives.gov.uk/`,
`https://cdn.nationalarchives.gov.uk` — `scripts/dl-uk.sh`,
`scripts/scrape-uk.py`, `scripts/harvest-tna.py`.

**Brazil:** `https://dibrarq.arquivonacional.gov.br/` (Dibrarq catalogue),
`https://www.fab.mil.br`, `https://www.gov.br` —
`scripts/dl-brazil.sh`, `scripts/scrape-brazil.py`.

**Chile:** `https://sefaa.dgac.gob.cl/`, `https://www.dgac.gob.cl`,
`https://www.bcn.cl` — `scripts/dl-chile.sh`, `scripts/scrape-chile.py`.

**Argentina:** `https://www.argentina.gob.ar/fuerzaaerea/cefae` —
`scripts/spider.py` config `argentina-cefae`.

**Canada (Library & Archives Canada / Project Magnet):**
`https://library-archives.canada.ca/`,
`https://recherche-collection-search.bac-lac.gc.ca`,
`https://www.bac-lac.gc.ca` — `scripts/spider.py` config `canada-lac`.

**Italy:** `https://www.aeronautica.difesa.it/`,
`https://acs.cultura.gov.it`, `https://www.difesa.it` —
`scripts/spider.py` config `italy-am`.

**NZ:** `https://www.nzdf.mil.nz/`, `https://natlib.govt.nz`,
`https://www.archives.govt.nz`, `https://ufocusnz.org.nz` —
`scripts/spider.py` config `nz-nzdf`.

**Peru:** `https://www.gob.pe/fap`, `https://www.fap.mil.pe` —
`scripts/spider.py` config `peru-oifaa`.

**Spain:** `https://ejercitodelaire.defensa.gob.es/`,
`https://www.defensa.gob.es` — `scripts/spider.py` config `spain-ea`.

**Uruguay:** `https://www.fau.mil.uy/`, `https://www.gub.uy` —
`scripts/spider.py` config `uruguay-cridovni`.

**Generic spider** (`scripts/spider.py`):
- BFS crawler with configurable `allowed_hosts`, `link_patterns`,
  `file_extensions`, `max_depth`, `max_pages`, `delay` (1 s default).
- Caches every fetched page under `<mirror>/.cache/spider/<sha>.html`.
- Falls back to `https://web.archive.org/web/2024id_/<url>` on direct
  failure.
- Same Chrome-131 User-Agent string as all other scrapers (CLAUDE.md §6.1).

### Public, outgoing static API

The repo regenerates `api/*.json` weekly and commits the result. Endpoints
(served by GitHub Pages, all CORS-enabled):

| File | Shape |
| --- | --- |
| `api/all.json` | `{_meta, records: [...]}` — every record across every archive |
| `api/by-archive.json` | `{_meta, archives: {slug: [...]}}` |
| `api/stats.json` | `{_meta, perArchive: [...]}` — counts only |
| `api/geo.json` | Per-event geocodes |
| `api/pages-index.json` | Page index for Lunr full-text search |

Generated by `scripts/build-api.py`, `scripts/build-geo.py`,
`scripts/build-pages-index.py`. Schema documented in `api/README.md`.

The browser fetches these client-side from `search.html`, `timeline.html`,
`map.html`, `stats.html`, etc. (`'/api/all.json'`, `'/api/pages-index.json'`
appear in `search.html`).

## Data Storage

**Databases:** None. Confirmed in `.well-known/security.txt`: "No backend,
database, or any server-side code."

**File storage:**
- **GitHub repo (`main` branch)** — committed: every HTML page, every
  thumbnail / slideshow image, `uap-data.csv`, `release-manifest.json`,
  per-archive scraped pages under `<archive>/pages/`, `api/*.json`,
  `feeds/*.xml`, Lunr index, vendored Leaflet + Lunr.
- **GitHub Releases** — binary CDN for files too large for the repo. Tags
  in use:
  - `pdfs-v1` — every PDF, across every archive
    (~165 files at last count; CLAUDE.md §5.1).
  - `videos-v1` — every video (DVIDS + AARO cloudfront), ~60 mp4.
  - `wargov-r02-v1` — War.gov Release 02 (later wave).
  - `aaro-v1` — AARO-specific assets (per `api/stats.json`).
  - Per-archive tags as the catalogue grows (`geipan-v1`, `uk-v1`, …).
  - URL pattern:
    `https://github.com/hectorchanht/war-gov-ufo-release/releases/download/<tag>/<basename>`
  - Manifest helper: `scripts/_release_manifest.py` reads
    `release-manifest.json` and rewrites card `url` fields at build time so
    deployed pages always link to a live URL.
- **Local cache (gitignored)** —
  `bundles/Release_1/`, `bundles/release_02_document_bundle/`,
  `bundles/uapvideos/`, `bundles/uap052226/`, `aaro/videos/`, every
  `<archive>/pdfs/`, every `.pdftext/`, every `.cache/` directory. Re-built
  on demand by `scripts/sync.sh`.

**Caching (browser-side):**
- **Service worker** (`sw.js`) — three versioned caches:
  - `realufo-shell-<VERSION>` — app shell (`/`, `/search.html`,
    `/timeline.html`, `/map.html`, every utility page, vendored Leaflet,
    favicon, `/manifest.webmanifest`). Network-first for navigations,
    cache-fallback, then `/404.html`.
  - `realufo-data-<VERSION>` — JSON manifests + `.webmanifest`,
    stale-while-revalidate.
  - `realufo-img-<VERSION>` — images and fonts, cache-first with no
    explicit expiry.
  - VERSION is `<git-short-sha>-<YYYYMMDD>`, stamped by
    `scripts/build-sw.py` before every deploy. Activate handler deletes
    every cache whose key isn't in the current trio.

## Authentication & Identity

**End-user auth:** None. No login, no sessions, no cookies. Umami is
cookieless. Site is fully public-domain content.

**Developer auth:**
- `gh auth login` — required to push binary assets to releases
  (`scripts/backfill-release.py` uses
  `gh release upload <tag> --clobber <files>`).
- `git push` over SSH or HTTPS — required to publish HTML changes.
- GitHub Actions has `permissions: contents: write` on the scrape workflow
  so the bot can commit weekly rebuilds.

## Monitoring & Observability

**Error tracking:** None. No Sentry, no Rollbar, no Bugsnag.

**Analytics:** Umami (`cloud.umami.is`) — log-only, no behavioural
profiling, no user identifiers.

**Logs:**
- **Build-time:** `scripts/sync.sh` prints a friendly summary table. CI
  workflows log to the GitHub Actions UI. `scripts/check-sources.py`
  writes `dead-links.json` / `dead-links.md` on every weekly run.
- **Runtime:** browser `console` only; no shipping to a service. Service
  worker logs failures locally (`.catch(() => {})` no-ops in `sw.js`).

**Health:**
- `lychee` (`.github/workflows/links.yml`) runs every Monday 07:00 UTC and
  on every push touching HTML, fails the build on broken links not on the
  `.lycheeignore` allowlist.
- `check-sources.py` separately scans every upstream `src` URL each week
  and writes `dead-links.json`. Informational only — never fails the
  build (`|| true` in `scrape.yml`).

## CI/CD & Deployment

**Hosting:**
- **GitHub Pages** on the `main` branch. Custom domain `realufo.org`
  configured via `CNAME` file. HTTPS via GitHub's Let's Encrypt cert.

**CI pipeline:**
- **GitHub Actions** — six workflows (full list in STACK.md). Of note:
  - `scrape.yml` (weekly) is the only one that mutates the repo. It runs
    every scraper with `|| true` (failures tolerated per source), rebuilds
    every archive's HTML, regenerates `api/`, `feeds/`, geocodes, OG
    cards, then commits with `[skip ci]` and pushes to `main`.
  - `links.yml`, `html-validate.yml`, `lighthouse.yml`, `sync-nav.yml`,
    `sync-footer.yml` are validation gates that fail the build on drift /
    broken links / a11y regression.

**Deployment:**
- Pushing to `main` is the deploy. GitHub Pages auto-publishes within
  ~1–2 min. `scripts/build-sw.py` stamps `sw.js` before each commit so the
  service worker invalidates on the next page load.
- Binary assets to a release: `gh release upload <tag> <files>` manually,
  or via `scripts/backfill-release.py`. CLAUDE.md §11 warns: don't fire
  off a second `gh release upload` from main before the first finishes.

## Environment Configuration

**Required env vars (production runtime):** None.

**Required env vars (CI):**
- `GITHUB_TOKEN` — auto-provided to every workflow; used by lychee.
- `LHCI_GITHUB_APP_TOKEN` — Lighthouse CI GitHub App integration
  (`.github/workflows/lighthouse.yml`, optional — used to post results on
  PRs).

**Required env vars (local dev):** None for read-only browsing. For
mutating sync:
- `gh` CLI authenticated (uploads to releases).
- No `.env` file exists or is expected.

**Secrets location:**
- GitHub repo settings → Secrets and variables → Actions:
  `LHCI_GITHUB_APP_TOKEN`.
- Developer machine: `~/.config/gh/hosts.yml` (GH CLI keychain).

## Webhooks & Callbacks

**Incoming:** None. There is no server-side endpoint anywhere — GitHub Pages
serves static files only. The only "trigger" into the system is the
`scrape.yml` cron + manual `workflow_dispatch`.

**Outgoing:** None. The build process pushes to:
- The repo's own `main` branch (via `git push origin main` in
  `scrape.yml`).
- GitHub Releases (via `gh release upload` from `backfill-release.py`).

No third-party POSTs (no Slack, Discord, Zapier, IFTTT, no upstream API
write-backs).

## External-link integrity

Two systems keep upstream URLs honest:

- **`scripts/check-sources.py`** — runs in the weekly scrape workflow;
  walks every embedded manifest's `src` URL, writes status to
  `dead-links.json` / `dead-links.md`.
- **`lychee`** — `.github/workflows/links.yml` validates every link inside
  every `**/*.html` file weekly + on every HTML push. Accepts
  `200, 206, 301, 302, 308, 403, 429`; everything else fails the build
  unless `.lycheeignore`-listed.

When upstream rots, `release-manifest.json` already routes the Download
button at the GitHub Release copy, so the user-visible link never
404's — only the `Source ↗` button does, and that's expected for dead
government pages.

---

*Integration audit: 2026-05-25*
