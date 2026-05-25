# Technology Stack

**Analysis Date:** 2026-05-25

## Summary — what makes this stack unusual

realufo.org is a **pure-HTML static site with zero frontend build tooling**.
There is no `package.json`, no `requirements.txt`, no `tsconfig.json`, no
bundler, no transpiler, no framework. Every page is a single self-contained
`.html` file with inline `<style>` and inline `<script>` blocks. Python
scripts under `scripts/` generate the HTML by string-templating against
manifests; the browser is handed plain HTML+CSS+JS.

Two complications layered on top of that bare-metal foundation:

1. **Offline-first delivery** — a service worker (`sw.js`) precaches the app
   shell and runtime-caches every JSON manifest and image so the entire site
   keeps working after one cold load. Bundled in `manifest.webmanifest` as
   an installable PWA.
2. **GitHub Releases as a CDN for large binaries** — every PDF and video over
   the GitHub-blob-size threshold is uploaded to a release tag (`pdfs-v1`,
   `videos-v1`, `wargov-r02-v1`, `aaro-v1`, …). The repo only commits
   thumbnails and HTML; `release-manifest.json` maps `basename → release
   download URL` so build scripts can rewrite card `url` fields at
   generate-time.

## Languages

**Primary:**
- **HTML5** — every user-facing page, ~50 files, inline CSS + inline JS, no
  external bundler. Largest: `index.html` (479 KB, 2237 lines) and
  `search.html` (72 KB, 1260 lines).
- **JavaScript (vanilla ES2015+)** — inline in every page. No framework. No
  TypeScript. Pages share copy-pasted helpers (lightbox, nav toggle, search)
  that are kept in sync by `scripts/sync-nav.py` / `scripts/sync-footer.py`
  drift gates.
- **Python 3.11** — every build / scrape / asset script under `scripts/`,
  ~50 files. Standard library only except `curl_cffi`.
- **Bash** — per-archive download orchestrators (`scripts/dl-*.sh`,
  `scripts/sync.sh`).

**Secondary:**
- **CSS** — inline in every HTML page. No external stylesheet (except
  vendored `leaflet.css`).
- **JSON** — `release-manifest.json`, `api/*.json`, per-page embedded
  `<script id="archive-manifest" type="application/json">` blocks.
- **CSV** — `uap-data.csv` (R01+R02 combined, 298 KB) and the legacy
  `uap-release001.csv` are the source of truth for the war.gov manifest;
  `scripts/build-wargov.py` reads them.
- **XML** — `sitemap.xml`, per-archive Atom feeds under `feeds/`.

## Runtime

**Browser runtime:**
- Targets evergreen browsers (Chrome, Safari, Firefox). Service worker
  requires HTTPS in production.
- No transpilation; relies on native ES2015+, `fetch`, `URLSearchParams`,
  `IntersectionObserver`.

**Build / scrape runtime:**
- **Python 3.11** (pinned in `.github/workflows/scrape.yml` via
  `actions/setup-python@v5`).
- **Node 20** (pinned via `actions/setup-node@v4`) — only used in CI for
  `html-validate` and `@lhci/cli`. Not required to develop or build the
  site.
- **Bash** — POSIX-compliant, runs on macOS and Ubuntu CI.
- **`poppler-utils`** (`pdftotext`) — Linux system package, used by
  `scripts/extract-pdf-text.py` for full-text indexing.
- **`librsvg2-bin`** (`rsvg-convert`) — Linux system package, used by the
  weekly CI to rasterise Open Graph SVGs to PNG for Facebook.

**Package Manager:**
- **`pip`** — single Python dependency installed ad-hoc:
  `pip install curl_cffi` (`scripts/sync.sh:139`, `.github/workflows/scrape.yml`).
  No `requirements.txt` is committed.
- **`npm`** — no `package.json`. CI installs `html-validate` and `@lhci/cli`
  with `npm install --no-save` per run. No lockfile.

## Frameworks

**Frontend frameworks:**
- **None.** Explicit design decision (CLAUDE.md §11: "Generates a
  self-contained `.html` (CSS inline, JS inline). Zero build tooling.").
  No React, Vue, Svelte, Astro, Eleventy, Hugo, Jekyll. The build step is
  literally `python3 scripts/build-<slug>.py` doing string substitution
  against a single template per archive type.

**Static site generator:**
- Custom Python templating in `scripts/templates/` —
  `head.py`, `nav.py`, `footer.py`, `lightbox.py`, `i18n.py`, `shared.py`,
  `archive.py`. Re-exported through `scripts/_site_template.py` and
  `scripts/_mirror_shared.py`. Each `scripts/build-<slug>.py` glues these
  together and emits one HTML file per archive root.

**Testing:**
- **No unit-test framework.** No `pytest`, no Jest. Validation is at the
  manifest layer (`scripts/validate-manifests.py`) and the artifact layer
  (HTML validate + Lighthouse + lychee link check in CI).

**Build / dev:**
- **`scripts/sync.sh`** — master interactive picker. Downloads sources +
  rebuilds every archive HTML.
- **`scripts/build-sw.py`** — stamps the service-worker version with the
  current git short SHA + UTC date (`const VERSION = '<sha>-<YYYYMMDD>';`)
  so a deploy invalidates stale caches.
- **`python3 -m http.server 8000`** — local preview (used by Lighthouse CI
  in `.github/workflows/lighthouse.yml`).

## Key Dependencies

**Critical Python:**
- **`curl_cffi`** (latest) — TLS-impersonating HTTP client. Used by
  `scripts/download-war.gov.py` and `download.py` to defeat Akamai bot
  protection on `www.war.gov` (curl/wget/requests all get 403'd by JA3
  fingerprinting). Cycles through Chrome impersonation profiles 124, 120,
  116, 110. Only mirror downloader that needs it; everything else uses
  standard `urllib.request`.

**Critical CLI tools:**
- **`gh` (GitHub CLI)** — used by `scripts/backfill-release.py` and
  `scripts/build-aaro.py` to enumerate (`gh release view <tag> --json
  assets`) and upload (`gh release upload <tag> --clobber <files>`) binary
  assets. Auth via standard `gh auth login`.
- **`git`** — every build script calls `git ls-files <dir>/` (not
  `os.listdir`) so the deployed site only points `a.local` at files that
  are *actually committed* (CLAUDE.md §6.2). Gitignored files route through
  their release URL instead.
- **`curl`** — used by every `scripts/dl-*.sh` bash downloader with a
  Chrome 131 User-Agent spoofed via the `UA=...` constant and a Wayback
  Machine fallback (see INTEGRATIONS.md).

**Vendored browser libraries** (`assets/vendor/`, all served same-origin so
they work offline):
- **`leaflet/leaflet.js` + `leaflet.css`** — used only by `map.html` for
  the global incident map. Vendored so the map works offline (precached in
  `sw.js:37-38`).
- **`lunr/lunr.min.js`** — full-text search index used by `search.html`
  (line ~1 — `<script defer src="/assets/vendor/lunr/lunr.min.js">`).
  Index is built per page from `/api/all.json` plus the PDF text extracts.
- **`hotkeys.js`** — keyboard shortcuts (`/` to focus search, etc.).
- **`citation.js`**, **`related-media.js`**, **`share.js`** — small UI
  helpers loaded on archive detail pages.

**Web fonts:**
- **Source Serif 4** and **JetBrains Mono** — served from Google Fonts
  (`https://fonts.googleapis.com` + `https://fonts.gstatic.com`). The only
  third-party CSS allowed (CSP `style-src 'self' 'unsafe-inline'
  https://fonts.googleapis.com`). Preconnected in `<head>`. CLAUDE.md §3.3
  bans a third font.

**Analytics:**
- **Umami** — cookieless, log-only analytics from `cloud.umami.is`. One
  tag per page: `<script defer src="https://cloud.umami.is/script.js"
  data-website-id="9c4f36ef-30ad-4d76-947a-1724fe6acdba">`. Only third-party
  JS allowed by CSP. No Google Analytics, no Plausible, no Sentry.

**Infrastructure:**
- **GitHub Pages** — hosting. `CNAME` file is just `realufo.org`. Pages
  serves `/api/*.json` with `Access-Control-Allow-Origin: *` per
  `api/README.md`.
- **GitHub Releases** — binary CDN. Tags observed in use: `pdfs-v1`,
  `videos-v1`, `wargov-r02-v1`, `aaro-v1`. Release URL pattern:
  `https://github.com/hectorchanht/war-gov-ufo-release/releases/download/<tag>/<basename>`
  (`scripts/build-aaro.py`, `release-manifest.json`).
- **GitHub Actions** — six workflows (see below).

## Configuration

**Environment:**
- **No `.env` file** — no runtime secrets. The site is pure static HTML
  with no backend. `.well-known/security.txt` explicitly states "We are
  not running: User authentication, accounts, or session state; A backend,
  database, or any server-side code; Vercel, AWS, GCP, or paid
  third-party services."
- **CI secrets** (GitHub repo settings):
  - `LHCI_GITHUB_APP_TOKEN` — Lighthouse CI GitHub App
    (`.github/workflows/lighthouse.yml`).
  - `GITHUB_TOKEN` — auto-provided by Actions; used by the lychee
    link-check workflow.
- **`gh` CLI auth** — required locally for anyone running
  `scripts/backfill-release.py` (uploads to releases). Stored in the
  developer's keychain by `gh auth login`.

**Build / lint config files** (all repo-root):
- `.htmlvalidate.json` — html-validate config. `html-validate:recommended`
  + relaxed WCAG warnings + `no-inline-style: off` (inline style is by
  design). Excludes `aaro/pages/*` and `nara/pages/*` (upstream scraped
  HTML that can't be rewritten).
- `.lighthouserc.json` — desktop preset, 8 URLs, perf ≥ 0.8 (warn),
  a11y ≥ 0.9 (error), best-practices ≥ 0.85 (warn), SEO ≥ 0.9 (error).
- `.lycheeignore` — broken-link allowlist for the weekly lychee run.
- `.gitignore` — large-binary policy: all `*/pdfs/`, `aaro/videos/`,
  `geipan/videos/`, and bundle zips are ignored (CLAUDE.md §5.2).

**Build config:**
- `CLAUDE.md` itself is the master spec — design tokens, layout rules,
  build invariants. New archives are added by following CLAUDE.md §10.
- `release-manifest.json` (54 KB) — basename → release-URL lookup,
  consumed by every build script via `scripts/_release_manifest.py`.
- `scripts/dvids2dod-r01.json`, `scripts/dvids2dod-r02.json` — DVIDS
  Video ID → DOD record-ID maps used by `scripts/build-wargov.py` to
  resolve catalog-only VID/AUD rows to playable URLs.

## Platform Requirements

**Development (local):**
- macOS or Linux. Bash, `python3.11+`, `curl`, `git` on PATH.
- `pip install curl_cffi` if syncing the war.gov manifest.
- `brew install poppler` (macOS) or `apt install poppler-utils` (Linux)
  if regenerating PDF text extracts.
- `gh` CLI authenticated if uploading new binary assets.
- Open `index.html` directly in a browser, or run
  `python3 -m http.server 8000` for service-worker testing.

**CI (GitHub Actions, `ubuntu-latest`):**
- Python 3.11, Node 20.
- `poppler-utils`, `librsvg2-bin` (installed inline per workflow).
- `curl_cffi` installed via pip (`scrape.yml`).

**Production:**
- **GitHub Pages** serving `main` branch. Custom domain `realufo.org` via
  `CNAME` file. HTTPS via GitHub's auto-issued certificate.
- **Service worker** requires HTTPS (no SW on `http://`). Local testing
  works on `http://localhost:8000`.
- **Large binaries** served from GitHub Releases, not Pages — Releases
  bypass the GitHub-blob 100 MB hard limit and the Pages bandwidth caps.

## CI/CD pipeline (six workflows)

| Workflow | File | Trigger | Purpose |
|---|---|---|---|
| Weekly scrape + rebuild | `.github/workflows/scrape.yml` | `cron: '0 6 * * 1'` (Mon 06:00 UTC) + manual | Re-scrapes every upstream archive, rebuilds all HTML, regenerates `/api/*.json` + Atom feeds + Open Graph cards + geocodes, runs `scripts/check-sources.py`, updates `sitemap.xml`, stamps `sw.js`, appends CHANGELOG, commits + pushes |
| Broken-link check | `links.yml` | push to main, PR, `cron: '0 7 * * 1'` | `lycheeverse/lychee-action@v2` against every `**/*.html` |
| HTML validation | `html-validate.yml` | push/PR on `**/*.html` | `npx html-validate` with our config; excludes scraped upstream pages |
| Lighthouse CI | `lighthouse.yml` | push/PR on HTML/CSS/JS | Serves with `python3 -m http.server 8000`, runs `@lhci/cli@0.14.x` |
| Footer drift gate | `sync-footer.yml` | push/PR on HTML/templates | `python3 scripts/sync-footer.py --check` — fails if any HTML footer drifts from canonical |
| Nav drift gate | `sync-nav.yml` | push/PR on HTML/templates | `python3 scripts/sync-nav.py --check` — same idea for nav |

## What is deliberately NOT in the stack

(Useful negative space for the planner.)

- No TypeScript, no JSX, no SCSS, no Tailwind, no PostCSS.
- No bundler (Vite, Webpack, Rollup, esbuild, Parcel).
- No frontend framework (React, Vue, Svelte, Solid, Lit).
- No SSG framework (Astro, Eleventy, Hugo, Jekyll, Next, Nuxt).
- No backend (Node, Fastify, FastAPI, Flask, Django). No database.
- No CDN besides GitHub Pages + GitHub Releases + Google Fonts +
  `cloud.umami.is`.
- No paid hosting. No Vercel, Netlify, Cloudflare Workers, AWS, GCP.
- No CMS (Contentful, Sanity, Strapi, …). Source of truth is the CSV
  (`uap-data.csv`) + per-archive scrapers writing into per-archive
  manifests.
- No auth, no sessions, no cookies (Umami is cookieless).
- No test runner (pytest, Jest, Vitest, Playwright). Only artifact-level
  CI checks.
- No Docker / containers. CI runs directly on `ubuntu-latest`.

---

*Stack analysis: 2026-05-25*
