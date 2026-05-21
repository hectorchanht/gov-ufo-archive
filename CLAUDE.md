# CLAUDE.md — project rules, design system, build process

This file is the master spec for the **PURSUE × AARO × NASA × NARA × …**
offline-UAP-mirror project. Read it before changing anything. New mirrors
follow these rules to the letter.

---

## 1. Goals (in order)

1. **Faithful archive** of every official government UAP source — content
   matches the official site verbatim.
2. **Eye-catching presentation** — declassified-archive aesthetic, hero
   carousel of actual evidence, headlines strip, evidence browser.
3. **Offline by default** — every committed asset works without network.
4. **Mobile-first** — every interaction tested at 360 px first, then scaled
   up. No horizontal scroll. No overflow. Touch targets ≥ 44 px.
5. **Replicable** — `./scripts/sync.sh` reproduces the full mirror locally,
   idempotent, schedulable.

When two goals conflict: pick **mobile-first** over desktop polish, and
**offline by default** over inline streaming.

---

## 2. Design system

### 2.1 Tone colours (per mirror)

Each mirror picks ONE primary accent (`--caution`). Everything else is
shared.

| Mirror | Primary | Seal gradient |
| --- | --- | --- |
| **war.gov / UFO** | `#d4a017` (gold) | radial `#b91c1c → #6b1010 → #2a0606` |
| **AARO** | `#4a9eff` (blue) | radial `#1e3a8a → #102560 → #061238` |
| **NASA** | `#fc3d21` (NASA red) | radial `#fc3d21 → #a01818 → #400606` |
| **NARA** | `#cbd5e1` (silver) | radial `#9ca3af → #4b5563 → #1f2937` |
| **France GEIPAN** | `#0055a4` (French blue) | radial `#0055a4 → #003278 → #001f4d` |
| **UK National Archives** | `#012169` (Royal Navy) | radial `#012169 → #001440 → #000820` |
| **Brazil FAB** | `#009c3b` (Brazilian green) | radial `#ffdc00 → #009c3b → #002776` |
| **Chile CEFAA** | `#d52b1e` (Chilean red) | radial `#d52b1e → #8b1413 → #3d0908` |

### 2.2 Shared palette (do not deviate)

```
--bg:        #0a0a0c   page background
--bg-2:      #111114   card background, lightbox meta
--panel:     #15151a   header strip, sidebars
--ink:       #e8e3d8   primary text
--ink-dim:   #a8a298   secondary
--ink-faint: #6b665d   tertiary, labels
--rule:      rgba(232,227,216,0.12)
--rule-strong: rgba(232,227,216,0.28)
--stamp:     #b91c1c   red accent for ◉ marker
--warm:      #d4a017   gold accent — LOCAL badge
--classified:#c9362c
--serif:     "Source Serif 4"
--mono:      "JetBrains Mono"
```

### 2.3 Typography

- **Serif** for prose, hero titles, card titles
- **Mono** for nav, metadata labels, badges, code
- **Body size**: 16 px desktop, 15 px mobile
- **Letter-spacing on mono**: 0.08–0.24 em
- **No third font.** No Google Fonts beyond what's already preconnected.

---

## 3. Page architecture

Every mirror has the same skeleton:

```
<scanlines>           — fixed 2 px noise overlay
<header-wrap>          — sticky 64 px tall, blurred bg
   ↳ <.brand>           seal + name
   ↳ <.nav-toggle>      hamburger (☰), hidden ≥ 720 px
   ↳ <nav.primary>      sections + mirror-to-mirror cross-links
<hero>
   ↳ .coords           ◉ short locator
   ↳ h1.hero-title     italic accent on one word
   ↳ p.hero-sub        65 ch lede paragraph with source link
   ↳ .classified-stamp (optional)
   ↳ .hero-carousel    16:9 aspect, ≥ 4 slides, dots + arrows + caption + autoplay
<section.headlines>    — 4–6 "head-card" tiles distilling the mirror
<section.archive>      — evidence/records browser
   ↳ stats-grid        Total / Local / per-type counts
   ↳ arch-controls-bar (sticky 64 px under header)
       — tabs
       — sort dropdown
       — search input
   ↳ filter-bar        — agency / status / region / per-page
   ↳ result-count
   ↳ arch-grid         — cards, minmax(280px, 1fr) desktop / 1fr mobile
   ↳ pagination
<footer>               — Source list = OFFICIAL URLs only
<lightbox>             — close, prev/next, counter, arrow-keys, swipe
```

### 3.1 Mirror navigation rule

- **Top sticky header**: project-internal links (mirror → mirror, intra-page anchors)
- **Footer "Source" list**: official site URLs (war.gov, aaro.mil, science.nasa.gov, archives.gov, …)
- **No top "OFFLINE MIRROR" gov-banner row.** Removed by design.

### 3.2 Card schema

Every asset card has at least:

```
title         full official title, verbatim
desc          substantive context. NEVER filler ('click to play').
              If no context available, omit. Title + metadata carries weight.
agency        primary releasing body
category      Document / Imagery / Video / Catalog / etc.
date          incident date or release date
status        Unresolved / Resolved / Undergoing Analysis / Closed (videos)
region        geographic context (optional)
local         repo-relative path if file is tracked in git
              (NEVER os.path.exists alone — use `git ls-files`)
url           download URL: local path OR GitHub Release URL OR live source
src           official source page URL (Source ↗ button)
```

### 3.3 Action buttons (consistent everywhere)

| Button | Routes to | When shown |
| --- | --- | --- |
| **Open PDF / Play / View / Open** | `data-action="open"` → lightbox at this card | Whenever `a.local` or `a.url` exists |
| **Download** | `a.local` if present, else `a.url` (release URL) | Whenever a downloadable URL exists |
| **Source ↗** | `a.src` (official site URL) | Whenever `a.src` is known |
| **DVIDS ↗** | DVIDS page for that video | Only for VID type with `a.dvidsId` |
| **Catalog ↗** | Catalog / Archive deep-link | Only for CATALOG type |

**Never** show a button that returns HTML (404 page). If `a.local` is empty
on the deployed site, the Download button must point at the release URL —
never at the bare local path.

---

## 4. Storage layout

```
.
├── index.html             war.gov / PURSUE
├── slideshow/             all 30+ image assets (small, tracked)
├── bundles/
│   └── Release_1/         gitignored (PDFs); restored via sync.sh
├── aaro-mirror/
├── nasa-mirror/
├── nara-mirror/
├── geipan-mirror/         (batch 2)
├── uk-mirror/             (batch 2)
├── brazil-mirror/         (batch 2)
├── chile-mirror/          (batch 2)
└── scripts/
    ├── sync.sh                  master entry, interactive picker
    ├── dl-<mirror>.sh           per-mirror downloader
    ├── build-<mirror>.py        per-mirror site generator
    ├── build-wargov.py          main page rebuild
    ├── parse-aaro.py            AARO-only page parser
    └── extract-evidence.py      AARO-only evidence-map builder
```

### 4.1 GitHub Releases

| Tag | Contents |
| --- | --- |
| `videos-v1` | 60 mp4 (war.gov + AARO) |
| `pdfs-v1` | 165 PDFs (all mirrors) |
| Future: per-mirror release tags as needed (`geipan-v1`, etc.) |

URL pattern: `https://github.com/hectorchanht/war-gov-ufo-release/releases/download/<tag>/<filename>` — referenced from manifest as `a.url`.

### 4.2 `.gitignore` policy

- Any single file > 100 MB: ignore. Period (GitHub hard limit).
- PDF directories: ignore all PDFs (migrate to `pdfs-v1` release).
- Video directories: ignore all videos (`videos-v1`).
- Images: track them (small, frequently shown).
- Page HTML snapshots: track (tiny).

---

## 5. Build & sync rules

### 5.1 Per-mirror download script

Each `scripts/dl-<mirror>.sh` is **idempotent**:

- Cache hit (file on disk + non-zero size): skip.
- Cache miss: try direct URL with realistic Chrome UA + timeout.
- If direct blocked (Akamai): fall back to Wayback `https://web.archive.org/web/<ts>id_/<url>`.
- Failures `rm -f` the partial file.

### 5.2 Per-mirror build script

Each `scripts/build-<mirror>.py`:

- Uses `git ls-files <mirror>/<subdir>/` (not `os.listdir`) for `a.local`.
- Falls back to `os.listdir` if git is unavailable.
- Embeds the manifest as a single inline `<script id="arch-data" type="application/json">` block.
- Generates a self-contained `.html` (CSS inline, JS inline). Zero build tooling.

### 5.3 sync.sh

- Interactive picker (multi-select via comma) when run on a TTY.
- Flags: `--all`, `--<mirror>-only`, `--no-videos`, `--no-build`.
- Always rebuilds all HTML at the end.
- Friendly stats summary at the bottom.

---

## 6. JavaScript invariants

Every mirror's inline script includes these patterns. Don't diverge.

```js
// (1) Hamburger toggle
const navToggle = document.getElementById('nav-toggle');
const primaryNav = document.getElementById('primary-nav');
if (navToggle && primaryNav) {
  navToggle.addEventListener('click', () => {
    const open = primaryNav.classList.toggle('open');
    navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  primaryNav.addEventListener('click', e => {
    if (e.target.tagName === 'A') {
      primaryNav.classList.remove('open');
      navToggle.setAttribute('aria-expanded', 'false');
    }
  });
}

// (2) Lightbox with navigation
let lbList = [], lbIdx = 0;
function openAt(idx) { /* renderLb + lb.classList.add('open') */ }
function navLb(delta) { /* wraps mod lbList.length */ }
function closeLb() { /* lb.classList.remove('open') */ }
// Arrow keys: ← → / Escape
// Swipe: > 50 px horizontal, < 800 ms = nav

// (3) Image fallback: <img onerror> swaps to a.src
// (4) Video fallback: <video> with TWO <source> children (local + remote)
// (5) PDF lightbox: iframe ONLY for local files. Release URLs open in new tab
//     (Content-Disposition: attachment).
// (6) Card render uses BOTH data-idx (for openAt) and data-action="open"
```

---

## 7. Mobile-first specifics

- **Base styles assume 360 px viewport.**
- Single-column card grid below 720 px.
- Hamburger (☰) below 720 px. Above: inline nav.
- Sticky filter bar: vertical stack with full-width inputs below 720 px.
- Tab strip **wraps** to multiple rows on mobile — never horizontal-scrolls. Predictable layout, no hidden overflow.
- Touch targets ≥ 44 × 44 px. Use `padding: 12px 0` for nav links.
- Lightbox nav buttons: 52 × 52 desktop, 40 × 40 mobile, edge-pinned (`left/right: 8px`).
- All `<input>` / `<select>` reach full container width on mobile.
- No element exceeds `100vw`. Use `overflow-wrap: anywhere` on long titles.
- `body { overflow-x: hidden; }` as last-resort guard rail.

---

## 8. Content rules

- **No filler.** "Click to play", "View file", "Released document — see source for context" — all banned. Either substantive context or leave `desc` blank.
- **Verbatim official text** for hero lede, headlines, FAQ accordion answers.
- **Public-domain attribution** per source jurisdiction:
  - **USA** — 17 U.S.C. § 105
  - **France** — Loi n° 78-753 (Information Publique)
  - **UK** — Open Government Licence v3
  - **Brazil** — Lei nº 12.527/2011 (LAI)
  - **Chile** — Ley nº 20.285 sobre Acceso a la Información Pública

---

## 9. Adding a new national mirror — checklist

1. Pick the tone colour (see § 2.1 — keep both palette and seal gradient).
2. Make `scripts/dl-<mirror>.sh` for source pages + representative PDFs / imagery.
3. Make `scripts/build-<mirror>.py` modelled on `build-nasa.py` (small) or `build-aaro.py` (large).
4. Make `<mirror>-mirror/assets/favicon.svg` using the seal gradient.
5. Add the mirror's nav link to every other mirror's header + footer.
6. Update `scripts/sync.sh` to include the new mirror in the picker.
7. Document source URL + licensing in `README.md`.
8. Commit & push (no force-push, no history rewrite without explicit asking).

---

## 10. House-style "don'ts"

- ❌ Inline arrow ↗ inside header nav links. Save for explicit external links.
- ❌ "OFFLINE MIRROR" banner — removed everywhere.
- ❌ `crossorigin="anonymous"` on `<video>` — kills cloudfront playback.
- ❌ Single-`<source>` `<video>` for assets where you have BOTH local and remote.
- ❌ Filler description sentences.
- ❌ `gh release upload` from main without checking the previous upload finished.
- ❌ Skipping mobile testing — 360 px is the canonical first viewport.
- ❌ Force-pushes to main. Ever.
- ❌ Touching the user's CSV (`uap-release001.csv`) — that's the source of truth.

---

## 11. Useful commands

```bash
# Full sync + rebuild
./scripts/sync.sh --all

# Add a new release asset
gh release upload <tag> <files…>

# Rebuild every mirror without downloading
python3 scripts/build-wargov.py && python3 scripts/build-aaro.py && \
  python3 scripts/build-nasa.py && python3 scripts/build-nara.py && \
  python3 scripts/build-details.py

# Check what's tracked in a folder
git ls-files <dir>/ | wc -l

# View a release
gh release view <tag>
```
