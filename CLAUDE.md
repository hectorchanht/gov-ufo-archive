# CLAUDE.md — project rules, design system, build process

This file is the master spec for **realufo.org** — an offline-first archive
of every official government UAP source. Read it before changing anything.
New archives follow these rules to the letter.

---

## 1. Goals (in order)

1. **Faithful archive** of every official government UAP source — content
   matches the official site verbatim.
2. **Eye-catching presentation** — declassified-archive aesthetic, hero
   carousel of actual evidence, headlines strip, evidence browser.
3. **Offline by default** — every committed asset works without network.
4. **Mobile-first** — every interaction tested at 360 px first, then scaled
   up. No horizontal scroll. No overflow. Touch targets ≥ 44 px.
5. **Replicable** — `./scripts/sync.sh` reproduces the full archive locally,
   idempotent, schedulable.

When two goals conflict: pick **mobile-first** over desktop polish, and
**offline by default** over inline streaming.

---

## 2. Sources covered

15 official government archives in the long-term plan. **Scope status
(2026-05-28):** realufo.org currently ships **4 ACTIVE** archives linked
from Nav + Footer + Pagefind search. The remaining **11 DORMANT**
archives have full code + data + content-collection + tone-colour entries
preserved in the repo but are not user-navigable from the active surface.
Direct-URL access still works (NZ + Uruguay via Astro pages; the other 9
via legacy `scripts/copy-legacy-archives.sh` postbuild). Re-activating any
dormant archive = adding its slug to `Nav.astro` `ARCHIVES`, `Footer.astro`
`ACTIVE_ARCHIVES`, and `RootLayout.astro` `ACTIVE_ARCHIVES` (one line each).

| Slug | Path | Source | Official site | Status |
| --- | --- | --- | --- | --- |
| `wargov` | `/` | War.gov / PURSUE — Release 01 | <https://www.war.gov/UFO/> | **ACTIVE** |
| `aaro` | `/aaro/` | All-domain Anomaly Resolution Office | <https://www.aaro.mil/> | **ACTIVE** |
| `nasa` | `/nasa/` | NASA UAP Independent Study Team | <https://science.nasa.gov/uap/> | **ACTIVE** |
| `nara` | `/nara/` | National Archives & Records Administration (Project Blue Book + JFK + …) | <https://catalog.archives.gov/> | **ACTIVE** |
| `geipan` | `/geipan/` | France — GEIPAN (CNES) | <https://www.cnes-geipan.fr/> | dormant |
| `uk` | `/uk/` | UK National Archives (MoD UAP files) | <https://discovery.nationalarchives.gov.uk/> | dormant |
| `brazil` | `/brazil/` | Brazil FAB / Operação Prato | <https://www.fab.mil.br/> | dormant |
| `chile` | `/chile/` | Chile CEFAA / SEFAA (DGAC) | <https://www.sefaa.cl/> | dormant |
| `argentina` | `/argentina/` | Argentina CEFAe (Fuerza Aérea) | <https://www.argentina.gob.ar/fuerzaaerea/cefae> | dormant |
| `canada` | `/canada/` | Library & Archives Canada — Project Magnet | <https://www.bac-lac.gc.ca/> | dormant |
| `italy` | `/italy/` | Italy Aeronautica Militare | <https://www.aeronautica.difesa.it/> | dormant |
| `nz` | `/nz/` | NZ Defence Force | <https://www.nzdf.mil.nz/> | dormant |
| `peru` | `/peru/` | Peru OIFAA (Fuerza Aérea) | <https://www.gob.pe/fap> | dormant |
| `spain` | `/spain/` | Spain Ejército del Aire | <https://ejercitodelaire.defensa.gob.es/> | dormant |
| `uruguay` | `/uruguay/` | Uruguay CRIDOVNI | <https://www.fau.mil.uy/> | dormant |

Cross-archive search lives at `/search.html`. Top-level `index.html` is the
War.gov / PURSUE landing page (historical reasons — it predates the others).
Dormant pages emit `data-pagefind-ignore` on `<main>` (RootLayout) so Plan
04-19 Pagefind never indexes them while the dormant flag is set.

---

## 3. Design system

> **Status (2026-05-25)**: This design system is the **starting point** for the
> in-flight SSG migration (see §13). Visual identity (§3.1 tone colours, §3.2
> palette, per-archive seals) is **locked** — must survive migration verbatim.
> Markup, class names, and CSS structure (§4 skeleton, §7 JS invariants) may
> evolve to fit Astro idioms, but mobile-first rules (§8) and content rules
> (§9) remain non-negotiable.

### 3.1 Tone colours (per archive)

Each archive picks ONE primary accent (`--caution`). Everything else is
shared.

| Archive | Primary | Seal gradient |
| --- | --- | --- |
| **war.gov / UFO** | `#d4a017` (gold) | radial `#b91c1c → #6b1010 → #2a0606` |
| **AARO** | `#4a9eff` (blue) | radial `#1e3a8a → #102560 → #061238` |
| **NASA** | `#fc3d21` (NASA red) | radial `#fc3d21 → #a01818 → #400606` |
| **NARA** | `#cbd5e1` (silver) | radial `#9ca3af → #4b5563 → #1f2937` |
| **France GEIPAN** | `#0055a4` (French blue) | radial `#0055a4 → #003278 → #001f4d` |
| **UK National Archives** | `#012169` (Royal Navy) | radial `#012169 → #001440 → #000820` |
| **Brazil FAB** | `#009c3b` (Brazilian green) | radial `#ffdc00 → #009c3b → #002776` |
| **Chile CEFAA / SEFAA** | `#d52b1e` (Chilean red) | radial `#d52b1e → #8b1413 → #3d0908` |
| **NZ NZDF** | `#5b8def` | radial `#000000 → #333 → #000` |
| **Canada (LAC Magnet)** | `#ff6b6b` | radial `#ff0000 → #990000 → #330000` |
| **Argentina CEFAe** | `#74acdf` (sky blue) | radial `#74acdf → #3d6a9c → #1e3a5e` |
| **Uruguay CRIDOVNI** | `#3ba0d8` | radial `#3ba0d8 → #1e5d80 → #0d2c3e` |
| **Peru OIFAA** | `#ff6b6b` | radial `#d91023 → #7d0b14 → #3a0508` |
| **Spain Ejército del Aire** | `#f4c542` | radial `#aa151b → #700c10 → #350608` |
| **Italy Aeronautica Militare** | `#5cb85c` | radial `#009246 → #005a2b → #002612` |

### 3.2 Shared palette (do not deviate)

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

### 3.3 Typography

- **Serif** for prose, hero titles, card titles
- **Mono** for nav, metadata labels, badges, code
- **Body size**: 16 px desktop, 15 px mobile
- **Letter-spacing on mono**: 0.08–0.24 em
- **No third font.** No Google Fonts beyond what's already preconnected.

### 3.4 Favicon

A single shared classic-disk-UFO favicon lives at `<archive>/assets/favicon.svg`
(and `/assets/favicon.svg` at the root). Identical SVG across every page —
brand recognition trumps per-archive variation. Per-archive seals stay in
the page header.

---

## 4. Page architecture

Every archive page has the same skeleton:

```
<scanlines>           — fixed 2 px noise overlay
<header-wrap>          — sticky 64 px tall, blurred bg
   ↳ <.brand>           seal + name
   ↳ <.nav-toggle>      hamburger (☰), hidden ≥ 720 px
   ↳ <nav.primary>      sections + archive-to-archive cross-links
<hero>
   ↳ .coords           ◉ short locator
   ↳ h1.hero-title     italic accent on one word
   ↳ p.hero-sub        65 ch lede paragraph with source link
   ↳ .classified-stamp (optional)
   ↳ .hero-carousel    16:9 aspect, ≥ 4 slides, dots + arrows + caption + autoplay
<section.headlines>    — 4–6 "head-card" tiles distilling the archive
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

### 4.1 Navigation rule

- **Top sticky header**: project-internal links (archive → archive, intra-page anchors)
- **Footer "Source" list**: official site URLs (war.gov, aaro.mil, science.nasa.gov, archives.gov, …)
- **No top "OFFLINE MIRROR" banner.** Removed by design.

### 4.2 Card schema

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
thumb         repo-relative path to a small preview image (optional)
local         repo-relative path if file is tracked in git
              (NEVER os.path.exists alone — use `git ls-files`)
url           download URL: local path OR GitHub Release URL OR live source
src           official source page URL (Source ↗ button)
```

### 4.3 Action buttons (consistent everywhere)

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

## 5. Storage layout

```
.
├── index.html              war.gov / PURSUE landing
├── search.html             cross-archive search
├── slideshow/              war.gov highlight images
├── bundles/
│   └── Release_1/          gitignored (PDFs); restored via sync.sh
├── assets/favicon.svg      shared classic-disk-UFO favicon
├── aaro/                   AARO archive
├── nasa/                   NASA UAP
├── nara/                   NARA Blue Book + JFK + UAP
├── geipan/                 France GEIPAN
├── uk/                     UK National Archives MoD
├── brazil/                 Brazil FAB
├── chile/                  Chile SEFAA
├── argentina/              CEFAe
├── canada/                 LAC / Project Magnet
├── italy/                  Aeronautica Militare
├── nz/                     NZDF
├── peru/                   OIFAA
├── spain/                  Ejército del Aire
├── uruguay/                CRIDOVNI
└── scripts/
    ├── sync.sh                  master entry, interactive picker
    ├── dl-<slug>.sh             per-archive downloader
    ├── normalize-<slug>.py      per-archive normaliser (CSV/JSON → content collection)
    ├── copy-legacy-archives.sh  postbuild: copies 11 dormant archives + partial-port sub-pages
    ├── build-redirects.py       URL-CONTRACT.txt → _redirects (quality-gates.yml drift gate)
    ├── verify-redirects.sh      curl harness for canonical routes
    ├── verify-fidelity.py       fidelity-samples vs live preview text-node diff
    ├── verify-lighthouse-budgets.py  LHCI output parser (HARD-fail at Phase 4 close)
    ├── verify-python-retired.sh Phase 4 close invariant guard (Plan 04-20)
    └── spider.py                generic source-page crawler (Phase 5 SCRP scope)
```

### 5.1 GitHub Releases

| Tag | Contents |
| --- | --- |
| `videos-v1` | 60 mp4 (war.gov + AARO) |
| `pdfs-v1` | 165 PDFs across all archives |
| Per-archive tags as the catalogue grows (`geipan-v1`, `uk-v1`, …) |

URL pattern: `https://github.com/hectorchanht/gov-ufo-archive/releases/download/<tag>/<filename>` — referenced from manifest as `a.url`. (Local folder name `war-gov-ufo-release` is historical; the remote canonical name is `gov-ufo-archive`.)

### 5.2 `.gitignore` policy

- Any single file > 100 MB: ignore. Period (GitHub hard limit).
- PDF directories: ignore all PDFs (migrate to `pdfs-v1` release).
- Video directories: ignore all videos (`videos-v1`).
- Images: track them (small, frequently shown).
- Page HTML snapshots: track (tiny).

---

## 6. Build & sync rules

### 6.1 Per-archive download script

Each `scripts/dl-<slug>.sh` is **idempotent**:

- Cache hit (file on disk + non-zero size): skip.
- Cache miss: try direct URL with realistic Chrome UA + timeout.
- If direct blocked (Akamai): fall back to Wayback `https://web.archive.org/web/<ts>id_/<url>`.
- Failures `rm -f` the partial file.

### 6.2 Per-archive build (Phase 4+)

The 4 active archives (wargov, aaro, nasa, nara) are built by Astro
from `src/pages/**` + content collections (`src/content/`) populated
by `scripts/normalize-<slug>.py`. The 11 dormant archives ship as
git-tracked HTML via `scripts/copy-legacy-archives.sh` (postbuild).
The pre-Phase-4 per-archive `scripts/build-<slug>.py` builders were
retired by Plan 04-20; see `.planning/decisions/python-build-retired.md`.

Surviving Python under `scripts/`:
- `normalize-<slug>.py` — CSV/JSON normalisers feeding content collections
- `build-redirects.py` — URL-CONTRACT.txt → `_redirects` (drift-gated)
- `spider.py` + `scrape-<slug>.py` — Phase 5 SCRP scope
- `verify-fidelity.py`, `verify-lighthouse-budgets.py`,
  `verify-python-retired.sh` — verification utilities

### 6.3 sync.sh

- Interactive picker (multi-select via comma) when run on a TTY.
- Flags: `--all`, `--<slug>-only`, `--no-videos`, `--no-build`.
- Always rebuilds all HTML at the end.
- Friendly stats summary at the bottom.

---

## 7. JavaScript invariants

Every archive's inline script includes these patterns. Don't diverge.

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
// (7) `/` keydown anywhere on page focuses the search input (when one exists),
//     unless the user is already typing in an input/textarea/contenteditable.
// (8) Search query persists in `?q=`; restored on load, debounced-pushed on input.
```

---

## 8. Mobile-first specifics

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

## 9. Content rules

- **No filler.** "Click to play", "View file", "Released document — see source for context" — all banned. Either substantive context or leave `desc` blank.
- **Verbatim official text** for hero lede, headlines, FAQ accordion answers.
- **Public-domain attribution** per source jurisdiction:
  - **USA** — 17 U.S.C. § 105
  - **France** — Loi n° 78-753 (Information Publique)
  - **UK** — Open Government Licence v3
  - **Brazil** — Lei nº 12.527/2011 (LAI)
  - **Chile** — Ley nº 20.285 sobre Acceso a la Información Pública
  - **Argentina** — Ley nº 27.275 (Acceso a la Información Pública)
  - **Italy** — D.lgs. 33/2013 (FOIA)
  - **Spain** — Ley 19/2013 (Transparencia)
  - **Uruguay** — Ley nº 18.381

---

## 10. Adding a new national archive — checklist

1. Pick the tone colour (see § 3.1 — keep both palette and seal gradient).
2. Make `scripts/dl-<slug>.sh` for source pages + representative PDFs / imagery.
3. Make `scripts/build-<slug>.py` modelled on `build-nasa.py` (small) or `build-aaro.py` (large).
4. Use the shared classic-disk-UFO favicon at `<slug>/assets/favicon.svg`.
   Put the per-archive seal in the page header, not in the favicon.
5. Add the new archive's nav link to every other archive's header + footer.
6. Update `scripts/sync.sh` to include the new archive in the picker.
7. Document source URL + licensing in `README.md`.
8. Commit & push (no force-push, no history rewrite without explicit asking).

---

## 11. House-style "don'ts"

- ❌ Inline arrow ↗ inside header nav links. Save for explicit external links.
- ❌ "OFFLINE MIRROR" banner — removed everywhere.
- ❌ `crossorigin="anonymous"` on `<video>` — kills cloudfront playback.
- ❌ Single-`<source>` `<video>` for assets where you have BOTH local and remote.
- ❌ Filler description sentences.
- ❌ `gh release upload` from main without checking the previous upload finished.
- ❌ Skipping mobile testing — 360 px is the canonical first viewport.
- ❌ Force-pushes to main. Ever.
- ❌ Touching the user's CSV (`uap-release001.csv`) — that's the source of truth.
- ❌ Calling archive pages "mirrors" in user-facing copy. The project IS the
  archive. "Source" and "Archive" — never "mirror" outside this doc and
  legacy commit history.

---

## 12. Useful commands

```bash
# Full sync + rebuild
./scripts/sync.sh --all

# Add a new release asset
gh release upload <tag> <files…>

# Rebuild every archive without downloading (Phase 4+ Astro pipeline)
pnpm build  # Astro builds the 4 active archives; postbuild copies the
            # 11 dormant archives + partial-port sub-pages; Pagefind
            # indexes dist/ — full dist/ ready for deploy.

# Check what's tracked in a folder
git ls-files <dir>/ | wc -l

# View a release
gh release view <tag>
```

---

## 13. SSG migration — Phase 4 COMPLETE (2026-05-28)

The project migrated from plain HTML + Python build scripts to Astro 5 /
Cloudflare Pages. Phase 4 (this milestone) closed 2026-05-28 by Plan
04-20. The design rules in §3–§11 are the **starting contract**; this
section points at the migration source-of-truth so agents picking up
work know where the latest decisions live.

**v1 ships 4 ACTIVE archives** (wargov, aaro, nasa, nara — all US
jurisdiction, all 17 U.S.C. § 105) wired into Nav + Footer + Pagefind.
The 11 dormant archives stay in the repo (full code, data, content
collections, tone-colour entries, NZ + Uruguay Astro page templates) as
a **future-milestone re-add pool**. See `.planning/phases/04-full-
migration-search-offline-performance/04-SCOPE-PIVOT-SUMMARY.md` for
rationale + mechanics; Plans 04-15..04-17 ported AARO/NASA/NARA;
Plan 04-19 shipped Pagefind; Plan 04-20 closed Phase 4 by HARD-flipping
Lighthouse and retiring the active-surface Python build legacy.

**Python build retirement (Plan 04-20):** the active-surface builders
are gone (`build-wargov.py`, `build-details.py`, `sync-nav.py`,
`sync-footer.py`). Carve-outs that survive Phase 4: `scripts/spider.py`
(Phase 5 SCRP), `scripts/build-redirects.py` (quality-gates.yml drift
gate), `scripts/build-{brazil,chile,geipan,uk,api,cases,feeds,geo,og,
pages-index,stories,sw}.py` + `scripts/build_batch3.py` (still
referenced by `scrape.yml` — retired in Phase 5 when scrape.yml is
rewritten), and `scripts/copy-legacy-archives.sh` (ships the 11 dormant
archives + partial-port sub-pages — retired when dormant archives are
hard-deleted in a future milestone). See ADR
`.planning/decisions/python-build-retired.md`.

| Artifact | Path | Purpose |
| --- | --- | --- |
| Project context | `.planning/PROJECT.md` | Core value, constraints, active requirements, key decisions |
| Requirements | `.planning/REQUIREMENTS.md` | 56 v1 requirements with REQ-IDs (PMS / INF / SSG / SRC / SW / HOST / SCRP / PERF) |
| Roadmap | `.planning/ROADMAP.md` | 6 phases, dependencies, success criteria |
| Research summary | `.planning/research/SUMMARY.md` | Synthesized findings (stack / arch / features / pitfalls) |
| Codebase map | `.planning/codebase/*.md` | STACK, ARCHITECTURE, STRUCTURE, CONVENTIONS, TESTING, INTEGRATIONS, CONCERNS |
| Phase artifacts | `.planning/phases/NN-name/` | Per-phase CONTEXT, RESEARCH, PLAN, VERIFICATION |
| State | `.planning/STATE.md` | Current phase / plan / progress |

**Target stack** (research-decided, see `.planning/research/STACK.md`):
- **SSG**: Astro 5.x (pinned `~5.x.y`, NOT 6.x)
- **Hosting**: Cloudflare Pages (replaces GitHub Pages)
- **Binary CDN**: GitHub Releases stays (R2 for >2 GB overflow)
- **Search**: Pagefind (replaces Lunr `api/all.json`)
- **Scrape automation**: Cloudflare Workers cron + GH Actions hybrid (Akamai egress spike pending — `.planning/decisions/akamai-spike.md`)
- **Service worker**: `@vite-pwa/astro` `injectManifest`; structurally registered from shared `BaseHead.astro` on every page

**House rules that survive migration** (non-negotiable):
- §3.1 per-archive tone colours + seal gradients
- §7 JS invariants (lightbox, hamburger, search-focus on `/`, `?q=` persist)
- §8 mobile-first (360 px baseline, 44 px touch targets)
- §9 content fidelity (verbatim official text, no filler, public-domain attribution per jurisdiction)
- §11 don'ts (no force-push, no inline `↗` in nav, no horizontal scroll)

**House rules that may evolve**:
- §4 page-skeleton DOM (Astro components may rearrange wrappers)
- Class names, file paths, inline-script structure
- Python build scripts disappear (replaced by SSG + content collections)

When in doubt: read `.planning/PROJECT.md`, then this file. PROJECT.md decisions
override sections of CLAUDE.md they explicitly supersede.

