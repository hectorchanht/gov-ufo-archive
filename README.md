# realufo.org — offline mirror of every official UAP archive

**Live at [realufo.org](https://realufo.org/)** · 8 government UAP archives mirrored side-by-side:
war.gov (PURSUE), AARO, NASA, NARA, France GEIPAN, UK MoD,
Brazil FAB, Chile SEFAA.

A self-contained, **offline-first** archival mirror of the two primary U.S.
government UAP transparency portals:

| Mirror | Source | Local entry point |
| --- | --- | --- |
| **PURSUE — Department of War / Release 01** | <https://www.war.gov/UFO/> | [`index.html`](index.html) |
| **AARO — All-domain Anomaly Resolution Office** | <https://www.aaro.mil/> | [`aaro-mirror/index.html`](aaro-mirror/index.html) |

Both pages share the same visual language and the same control logic — a
cinematic hero carousel of real declassified imagery, a headlines strip, and
a filterable, sortable, paginated **evidence browser** that surfaces every
artifact with its full context (agency, location, incident date, VIRIN /
DVIDS ID, redaction status, case status). Every file you can see is served
from the local archive on disk.

---

## What's in the box

```
.
├── index.html                  # PURSUE — war.gov/UFO mirror (single page)
├── uap-release001.csv          # official Release 01 manifest (158 records)
├── slideshow/                  # 17 highlight images shown on the original page
├── bundles/
│   ├── Release_1/              # 130 documents + images (war.gov Release 01)
│   ├── Release_1.zip           # the official zip (gitignored — re-download)
│   ├── uapvideos/              # 28 DVIDS UAP videos (war.gov)
│   └── uapvideos.zip           # the official zip (gitignored)
├── assets/                     # site chrome (DOD/DOW header logos)
│
├── aaro-mirror/
│   ├── index.html              # AARO — evidence-first archive page
│   ├── details.html            # AARO — long-form text (mission, FAQ, …)
│   ├── pages/                  # 12 raw aaro.mil page snapshots (HTML)
│   ├── pdfs/                   # case-resolution reports, FOIA releases, briefs
│   ├── videos/                 # all 32 official AARO UAP videos (gitignored)
│   ├── assets/images/          # case-resolution thumbnails
│   └── .cache/                 # generated manifest JSON (gitignored)
│
├── download.py                 # war.gov downloader (TLS-impersonating curl_cffi)
└── scripts/
    ├── sync.sh                 # ⭐ master entry — run this
    ├── dl-aaro.sh              # AARO page + asset downloader (Wayback + cloudfront)
    ├── parse-aaro.py           # parse page HTML → structured JSON
    ├── extract-evidence.py     # build the AARO evidence map
    ├── build-aaro.py           # write aaro-mirror/index.html
    └── build-details.py        # write aaro-mirror/details.html
```

> Both `index.html` and `aaro-mirror/index.html` are **self-contained** —
> no build step or web server required. Open them in any browser. The only
> reason to run the downloader is to populate the bulky payloads (PDFs,
> videos) that are excluded from Git.

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

`curl_cffi` is required for the war.gov side because `www.war.gov` is fronted
by Akamai with TLS-fingerprint bot protection. `curl_cffi` wraps
`curl-impersonate`, which replicates a real Chrome handshake byte-for-byte.

Everything else uses only the Python and POSIX shell standard libraries.

### 3. Populate the archive

```bash
./scripts/sync.sh
```

That single command:

1. Runs `download.py` to pull the war.gov payloads (slideshow, manifest CSV,
   `Release_1.zip`, `uapvideos.zip`, agency logos)
2. Snapshots all 12 aaro.mil pages via the Wayback Machine
3. Downloads every official AARO UAP video directly from the DVIDS CDN
4. Downloads every PDF / image AARO links to (Wayback fallback when needed)
5. Re-parses everything and rebuilds both `index.html` pages so the
   `LOCAL / SOURCE` badges match what's actually on disk

It's **idempotent** — files already on disk are skipped. Re-running it picks
up only what's new.

### 4. Open in a browser

```bash
open index.html                   # macOS
xdg-open index.html               # Linux
start index.html                  # Windows
```

That's it. Both mirrors work offline from this point on.

---

## Hosting on GitHub Pages

The repo is **GitHub-Pages-ready** out of the box.

The `.gitignore` keeps the repo under 1 GB by excluding the bulky payloads:

- `bundles/Release_1.zip`, `bundles/uapvideos.zip` (~2.5 GB combined)
- `bundles/uapvideos/` (DVIDS bulk videos, 1.2 GB)
- `aaro-mirror/videos/` (32 AARO videos, 2.7 GB)
- The five Release_1 PDFs that exceed GitHub's 100 MB single-file limit

Result: a `git push`-friendly repo of about 150 MB.

On the live site, any asset that wasn't committed shows a `SOURCE` badge and
links straight back to the official URL (war.gov, aaro.mil, the DVIDS CDN).
Visitors who want a fully local copy just clone the repo and run
`./scripts/sync.sh`.

### How the local-vs-source switch actually works

Every asset card carries **both** a local relative path and the original
source URL. The page chooses dynamically:

- **Images** use `<img src="./local.jpg" onerror="this.src='source_url'">` —
  if the local file is missing (e.g. on GitHub Pages where the file was
  gitignored), the browser silently swaps in the official URL.
- **Buttons** always show a `Source ↗` chip alongside the `Download` chip
  when both a local file and a source URL exist. Two routes, always one
  that works.
- **The HTML never has to change**. The build scripts (`build-wargov.py`,
  `build-aaro.py`) regenerate the embedded manifest from current disk
  state on every run — newly-downloaded files automatically pick up
  local routing, missing files automatically fall back to source.

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
git commit -m "Initial mirror"
gh repo create war-gov-ufo-release --public --source=. --push
# then in repo Settings → Pages, set Source = main branch, root.
```

---

## Keeping the archive current (cron / scheduled)

The U.S. government has stated that both PURSUE (war.gov) and AARO release
new materials on a rolling basis. Re-run `sync.sh` periodically to capture
new tranches:

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
<!-- ~/Library/LaunchAgents/com.user.uap-mirror-sync.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
  <key>Label</key><string>com.user.uap-mirror-sync</string>
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

`launchctl load ~/Library/LaunchAgents/com.user.uap-mirror-sync.plist`

### GitHub Actions (mirror + auto-publish)

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
          git config user.name "uap-mirror"
          git config user.email "uap-mirror@users.noreply.github.com"
          git add -A
          git diff --quiet --staged || git commit -m "sync: $(date -u +%Y-%m-%d)"
          git push
```

---

## Selective sync flags

```bash
./scripts/sync.sh                # full run (default)
./scripts/sync.sh --aaro-only    # skip the war.gov side
./scripts/sync.sh --wargov-only  # skip the AARO side
./scripts/sync.sh --no-videos    # skip the big AARO videos (≈2.7 GB)
./scripts/sync.sh --no-build     # download only, no HTML rebuild
```

Useful combos:

```bash
# Day 1: quick browsable mirror without the multi-gig video downloads
./scripts/sync.sh --no-videos

# Day 2: pull the videos in a background terminal
bash scripts/dl-aaro.sh assets

# Anytime: refresh just the AARO side (e.g. after a new case release)
./scripts/sync.sh --aaro-only
```

---

## Why two source strategies?

| Source | Why it's hard | What we use |
| --- | --- | --- |
| `www.war.gov` | Akamai TLS fingerprinting blocks `curl`, `wget`, `requests`. | `curl_cffi` (Chrome TLS impersonation). |
| `cdn.dvidshub.net` | None — public CDN. | Direct `curl`. |
| `www.aaro.mil` | Akamai-blocked exactly the same way; impersonation often still 403s from VPN / cloud IPs. | Wayback Machine (`web.archive.org`) for HTML, PDFs, and images. |
| `d34w7g4gy10iej.cloudfront.net` (AARO videos) | None — public CloudFront origin. | Direct `curl`. |

If `curl_cffi` still gets 403 from war.gov, you're probably on a known
data-center / VPN IP that Akamai blocks. Run from a residential or
corporate-office connection.

---

## Page features (both mirrors)

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
  in-place; `Esc` to close
- **`LOCAL` / `SOURCE` badges** so it's always clear whether a file is on
  disk or links back to the official URL

---

## Notes & limits

- Federal U.S. government works are in the public domain (17 U.S.C. § 105).
  Page content and asset descriptions are reproduced verbatim from the
  original DoD / AARO publications.
- About 22 / 58 AARO PDFs and 13 / 21 AARO images **were never archived by
  the Wayback Machine** and no longer resolve from aaro.mil directly because
  of Akamai. They appear in the page with the `SOURCE` badge and link to
  the original URL; click-through may 403.
- The Vercel/Next/React skill hints you may see in commit history come from
  unrelated tooling — this project is a pure static HTML mirror. No build
  step. No runtime. No framework.

---

## License

Code in `scripts/` and `download.py`: MIT.
Mirrored content: U.S. government public-domain works (17 U.S.C. § 105).
