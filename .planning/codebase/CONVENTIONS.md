# Coding Conventions

**Analysis Date:** 2026-05-25

This project has three distinct code surfaces, each with its own conventions:

1. **HTML/CSS/JS** — one self-contained `index.html` per archive (15 archives + 10 cross-site pages). CSS and JS are inline; zero build tooling.
2. **Python build scripts** — `scripts/build-*.py` regenerate the HTML manifests.
3. **Shell download scripts** — `scripts/dl-*.sh` mirror upstream assets idempotently.

CLAUDE.md §3, §4, §7, §8, §9, §11 is the canonical spec. The conventions below are extracted from comparing CLAUDE.md against the actual code in `aaro/index.html`, `nasa/index.html`, `search.html`, and the `scripts/` directory.

## Naming Patterns

**Files:**
- Archive HTML: `<slug>/index.html` (one per archive — `aaro/index.html`, `nasa/index.html`, `geipan/index.html`, …)
- Story pages: `<slug>/<case-slug>.html` lowercase-hyphen (`aaro/tic-tac.html`, `aaro/jal-1628.html`, `uk/rendlesham.html`)
- Top-level utility pages: `<name>.html` lowercase (`search.html`, `timeline.html`, `map.html`, `glossary.html`, `compare.html`, `whatsnew.html`)
- Python build scripts: `scripts/build-<slug>.py`
- Python scrapers: `scripts/scrape-<slug>.py`
- Shell downloaders: `scripts/dl-<slug>.sh`
- Helper Python modules (private to scripts dir): `_underscore_prefix.py` (`_site_template.py`, `_release_manifest.py`, `_mirror_shared.py`)
- Shared template package: `scripts/templates/<module>.py`

**Directories:**
- Archive root: lowercase slug matching CLAUDE.md §2 (e.g. `aaro/`, `nasa/`, `geipan/`, `uk/`, `brazil/`, …)
- Per-archive subdirs (consistent across all archives): `pdfs/`, `videos/`, `assets/images/`, `pages/` (Wayback HTML snapshots), `.cache/` (gitignored parser output)
- `bundles/Release_1/`, `bundles/uapvideos/`, `bundles/release_02_document_bundle/` — gitignored war.gov payloads
- `slideshow/`, `slideshow-2/` — war.gov hero imagery (tracked)

**CSS classes:**
- Single-word lowercase for layout primitives: `.container`, `.hero`, `.seal`, `.brand`, `.scanlines`, `.coords`
- Hyphenated for compound roles: `.hero-carousel`, `.carousel-slide`, `.arch-grid`, `.arch-controls-bar`, `.head-card`, `.classified-stamp`, `.gov-banner`, `.flag-dot`, `.nav-toggle`, `.header-wrap`
- Lightbox prefix `lb-` for lightbox internals: `.lb-inner`, `.lb-close`, `.lb-prev`, `.lb-next`, `.lb-counter`, `.lb-rotate`, `.lbm-title`, `.lbm-desc` (meta panel)
- BEM-ish modifier: `.carousel-btn.prev`, `.tab.active`, `.carousel-slide.active`

**HTML IDs:**
- Single canonical instance per page: `id="nav-toggle"`, `id="primary-nav"`, `id="hero-carousel"`, `id="carousel-track"`, `id="carousel-dots"`, `id="carousel-caption"`, `id="lightbox"`, `id="lb-inner"`, `id="arch-data"`, `id="arch-grid"`, `id="arch-search"`, `id="arch-sort"`, `id="filter-region"`, `id="filter-status"`, `id="filter-perpage"`
- The embedded JSON manifest is always `<script id="arch-data" type="application/json">` (legacy war.gov uses `<script id="archive-manifest">` — both are accepted by `scripts/validate-manifests.py`).

**JavaScript:**
- `const`/`let` over `var` in newer code (post-aaro JS uses `const`); the lightbox IIFE still uses `var` (older idiom — kept for consistency within that block).
- Lower camelCase for functions and locals: `openAt`, `navLb`, `closeLb`, `goTo`, `applyLang`, `mediaFor`, `renderPagination`, `cardHtml`, `statusBadge`.
- Single-letter variable names accepted inside tight scopes / template literals: `D`, `i`, `e`, `t`, `b`, `g`, `q`, `a`, `r`, `s` — typical when iterating manifest records or building DOM.
- IIFEs wrap all page-level scripts: `(function(){ … })();` — see `aaro/index.html:834` and `aaro/index.html:1140`. No top-level identifiers escape into `window` except deliberate exports (e.g. `window._lb`).

**Python:**
- `snake_case` everywhere: `git_tracked()`, `lsdir_present()`, `validate_record()`, `apply_manifest()`, `make_nav()`.
- `UPPER_SNAKE` for module-level constants: `REPO`, `ROOT`, `CACHE`, `ARCHIVES`, `ALIASES`, `KNOWN_FIELDS`, `PDF_RELEASE_BASE`, `SCRIPT_IDS`, `EXPECTED_VIDEOS_R01`.
- Single-letter helpers acceptable for terse builders: `L()` for "local path", `R()` for "release URL" (`scripts/build-nasa.py:32`, `:40`).
- Private helper modules use `_underscore_prefix` (`scripts/_site_template.py`, `scripts/_release_manifest.py`).

**Manifest record keys (the single most important naming contract):**
Two short-key shapes coexist across archives because the codebase grew incrementally. Both are valid; `scripts/validate-manifests.py` enforces the alias table at `scripts/validate-manifests.py:55`. Prefer **short keys** for new archives — they cut inline JSON size by ~40%:

| Long key (verbose) | Short key (preferred) | Meaning |
|--------------------|----------------------|---------|
| `title` | `ti` | Card title (verbatim official) |
| `desc` / `description` | `de` | Card body; **leave empty rather than fill** (CLAUDE.md §9) |
| `agency` | `ag` | Primary releasing body |
| `category` / `type` | `t` or `cat` | `PDF` / `VID` / `IMG` / `AUD` / `CATALOG` / `SLIDE` |
| `date` | `dt` or `date` | Incident or release date |
| `region` | `re` | Geographic context |
| `status` | `st` | `Unresolved` / `Resolved` / `Undergoing Analysis` / `Closed` |
| `url` | `u` | Download URL (release URL OR live source) |
| `src` | `s` | Official source page (used for Source ↗ button) |
| `local` | `l` | Repo-relative path if file is in git, else `''` |
| `thumb` | `th` | Small preview image path |
| `dvidsId` | `di` / `dvidsId` | DVIDS video numeric ID |
| `embed` | `embed` | YouTube/Vimeo embed URL (NASA only) |

## Code Style

**Formatting:**
- No linter or formatter is enforced for HTML/CSS/JS — Prettier/ESLint not present, no `package.json`.
- CSS: properties on single lines, related rules grouped, comment dividers between sections (e.g. `/* HERO CAROUSEL */`, `/* HEADLINES */`). 2-space indent.
- HTML: 2-space indent, attributes on one line, `<meta>` block in `<head>` ordered: charset → viewport → title → description → canonical → og:* → twitter:* → favicon → preconnect → fonts.
- Python: PEP 8 broadly, 4-space indent, but **inline-imports are common** inside functions (e.g. `import subprocess` mid-script). Docstrings use triple-double-quotes; module docstring at the top of every `scripts/build-*.py`.
- Shell: 2-space indent inside function bodies, `#` comment headers with `# ====...====` boxes for section banners (see `scripts/dl-aaro.sh`).

**Linting (HTML only):**
- `.htmlvalidate.json` runs in CI via `.github/workflows/html-validate.yml`. Recommended ruleset with these overrides off: `no-inline-style`, `no-redundant-role`, `no-trailing-whitespace`, `no-implicit-button-type`, `void-style`, `attribute-boolean-style`, `require-sri`, `no-raw-characters`, `long-title`.
- Warning level: `wcag/h32`, `wcag/h36`, `wcag/h37`, `wcag/h67`, `element-required-attributes`, `prefer-native-element`.
- Scraped upstream HTML (`aaro/pages/`, `nara/pages/`) is excluded — they ship malformed asp.net markup.

**Lighthouse thresholds (`.lighthouserc.json`):**
- Performance: warn < 0.80
- Accessibility: **error** < 0.90 (hard gate)
- Best-practices: warn < 0.85
- SEO: **error** < 0.90 (hard gate)

## Import Organization

**HTML `<head>` order (every archive):**
1. `<meta charset>` + `<meta name="viewport">`
2. `<title>` (format: `<Archive> — <Full Name> | realufo.org` or `<Archive> — <Tagline> (Offline Mirror)`)
3. `<meta name="description">`
4. `<link rel="canonical">`
5. `og:*` Open Graph block (title, description, image, url, type, site_name)
6. `twitter:*` Twitter Card block
7. `<link rel="icon" type="image/svg+xml" href="./assets/favicon.svg">` + apple-touch-icon
8. `<link rel="preconnect">` to fonts.googleapis.com and fonts.gstatic.com
9. `<link>` to Google Fonts CSS (Source Serif 4 + JetBrains Mono — **no third font** per CLAUDE.md §3.3)
10. Inline `<style>` block

**JavaScript:**
- No ES modules, no `import` statements anywhere in shipped JS — every script is an inline IIFE in `index.html`.
- Cross-script communication via `window._lb` (lightbox), `window.NAV_*` (rare), and `document.getElementById('arch-data').textContent` (manifest).

**Python:**
- Stdlib first, then `from __future__ import annotations` (in newer files: `scripts/build-api.py`, `scripts/build-cases.py`, `scripts/build-feeds.py`, `scripts/build-geo.py`, `scripts/build-og.py`, `scripts/build-pages-index.py`, `scripts/build-stories.py`).
- Sibling-script imports use a `sys.path.insert(0, …)` shim at the top: `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` — see `scripts/build-aaro.py:11`, `scripts/build-nasa.py:8`.
- Local imports from `_site_template`, `_release_manifest`, `templates.nav`, `templates.footer`, `templates.head`, `templates.lightbox`, `templates.shared`, `templates.i18n`.

**Path Aliases:** None. All paths are repo-relative, computed from `REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` in every Python script.

## Error Handling

**JavaScript:**
- **Image fallback** is the canonical pattern (CLAUDE.md §7 invariant #3): every `<img>` rendered from manifest data carries an `onerror` that swaps `this.src` to the remote URL (`a.u` or `a.url`) and then nulls itself so it can't loop. See `aaro/index.html:498`, `aaro/index.html:549`, `aaro/index.html:1237`.
  ```js
  const fb = a.u ? `onerror="this.onerror=null;this.src='${esc(a.u)}';"` : '';
  ```
- **Video fallback** uses two `<source>` children — local first, remote second — inside one `<video>` element (CLAUDE.md §7 invariant #4, CLAUDE.md §11 "don't use single-source video"). See `aaro/index.html:1241`.
- **PDF lightbox** routes local PDFs to an `<iframe src="…#view=FitH">` and release-URL PDFs to `window.open(href, '_blank')` because GitHub Release URLs serve `Content-Disposition: attachment` which breaks iframe embed (`aaro/index.html:1250`).
- **JSON parse** of the embedded manifest is unguarded — failure should crash the page loud (`const D = JSON.parse(document.getElementById('arch-data').textContent);` at `aaro/index.html:868`). This is intentional: if `arch-data` is malformed the page is broken anyway and silent failure would hide it.
- **search.html** catches a single fetch failure and falls back to per-mirror scrape: `console.warn('search: /api/all.json unreachable, falling back to per-mirror scrape', err)` (`search.html:1215`).
- **HTML escaping** is universal — every value that enters innerHTML goes through `esc()`:
  ```js
  function esc(s){return (s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  ```
  Defined identically at `aaro/index.html:873` and `aaro/index.html:1150`.

**Python:**
- Build scripts treat git unavailability as recoverable — `git ls-files` is wrapped in `try/except (subprocess.CalledProcessError, FileNotFoundError)` and falls back to `os.listdir`. See `scripts/build-aaro.py:31-44`, `scripts/build-nasa.py:16-26`, `scripts/build-uk.py:21-28`, `scripts/build-brazil.py:18-26`. **This pattern is mandatory** for all new build scripts (CLAUDE.md §6.2).
- File-not-found on cache JSON is allowed to bubble — `json.load(open(...))` without guard, because the build cannot proceed without parsed evidence.
- Validation (`scripts/validate-manifests.py`) collects errors/warnings into lists, exits non-zero on errors, supports `--strict` to fail on warnings too.
- `KeyboardInterrupt` caught at top level and exits `130` (`scripts/validate-manifests.py:220`).

**Shell:**
- `set -uo pipefail` everywhere (not `-e` — failures are individually inspected so the rest of the run continues). See `scripts/dl-aaro.sh:17`, `scripts/dl-nasa.sh:11`, `scripts/sync.sh:18`.
- The `fetch` / `fetch_url` helper deletes partial files on failure (`rm -f "$dest"`) before returning non-zero — see `scripts/dl-aaro.sh:79`, `scripts/dl-nasa.sh:24`.
- Cache hit detection: `[ -s "$dest" ] && return 0` — file exists *and* is non-empty (`-s`, not `-f`). This is the **idempotency contract** (CLAUDE.md §6.1).

## Logging

**Framework:** None. Plain stdout.

**JavaScript:**
- `console.warn` reserved for fallback paths the user might care about (`search.html:1215`).
- No `console.log` in shipped pages — searched repo, only one `console.warn` total.

**Python:**
- `print()` statements at the end of every build script announce what was written:
  ```python
  print(f'wrote {ROOT}/index.html ({len(PAGE):,} bytes)')
  print(f'  total assets: {stats["total"]}, local: {stats["local_total"]}')
  ```
  See `scripts/build-nasa.py:747`, `scripts/build-aaro.py:1357`. **Match this style** in new build scripts.

**Shell:**
- Indented status lines with bracketed verbs: `[ok]`, `[cache]`, `[FAIL]`. Example: `echo "  [ok]    $slug ($(wc -c <"$dest" | tr -d ' ') bytes)"` (`scripts/dl-aaro.sh:107`).
- Section banners use `»` glyph: `echo "» NASA PDFs"`, `echo "» AARO page snapshots → aaro/pages/"`.

## Comments

**When to Comment:**
- Block comment at top of every Python script (module docstring) explaining inputs, outputs, side effects.
- Block comment at top of every shell script (`# ====...====` box) explaining purpose, modes, idempotency, usage examples.
- Inline `/* ... */` comments inside CSS for design-system landmarks (`/* HERO */`, `/* HEADLINES */`, `/* HERO CAROUSEL */`).
- Inline `// ...` comments inside JS to document why-not-what, especially around fallback paths (e.g. `aaro/index.html:1106` `/* Lightbox lifecycle delegated to LIGHTBOX_JS … */`).
- HTML-style `<!-- ... -->` markers wrap shared blocks injected by `scripts/sync-nav.py` and `scripts/sync-footer.py`: `<!-- NAV-SCRIPT:SHARED -->` … `<!-- /NAV-SCRIPT:SHARED -->`.

**JSDoc/TSDoc:** Not used.

**Python docstrings:**
- Every script and helper module has a module-level triple-quoted docstring.
- Function docstrings are common but not universal — present on non-obvious helpers (`L()`, `git_tracked()`, `lsdir()`, `validate_record()`), omitted on trivial ones.

## Function Design

**Size:**
- JS functions are typically 5–40 lines; the lightbox `render()` function (`aaro/index.html:1219`) is the longest at ~40 lines and contains the type-dispatch logic that's intentionally kept in one place.
- Python build scripts are flat — heavy use of module-level code (constants, asset list literals, loops). `scripts/build-aaro.py` is 1360 lines with most of the work inline; `scripts/build-nasa.py` is 750 lines with the asset list inline. **This is by design** — each build script is the single source of truth for one archive.

**Parameters:**
- JS: small fixed positional parameters, e.g. `openAt(idx)`, `navLb(delta)`, `goTo(i)`, `statusBadge(st)`, `mediaFor(a)`, `cardHtml(a)`.
- Python: positional, with light use of defaults. Type hints only in newer files (those with `from __future__ import annotations`).

**Return Values:**
- Python build helpers return primitives (`str`, `set[str]`) or `None`. No exotic return shapes.
- JS render functions either return a string (HTML to splice) or mutate the DOM directly — never both.

## Module Design

**Exports:**
- Python: re-exports through `scripts/_site_template.py` for backward compat (`scripts/_site_template.py:23-49`) — when the implementation moved into `scripts/templates/`, the old import paths kept working. Pattern: `from templates.nav import (PINNED, SITE_PAGES, MORE, STORIES, _href, make_nav, NAV_STYLE, NAV_SCRIPT)  # noqa: E402,F401`.
- JS: explicit single export point — `window._lb = { open, close, nav, setList, getList }` (`aaro/index.html:1282`). Other inline scripts read `window._lb` and never define competing globals.

**Barrel Files:** `scripts/_site_template.py` acts as the canonical barrel for the `templates/` package. `scripts/templates/__init__.py` exists but is empty — individual modules are imported by name.

## Mobile-First Specifics (CLAUDE.md §8)

Every page satisfies these without exception:
- Base styles assume **360 px viewport**. Body is `font-size: 16px` desktop (`aaro/index.html:38`), `15px` on mobile (`aaro/index.html:111`). NASA uses `16px → 15px`.
- **Single breakpoint at 720 px** for the hamburger flip: `@media (max-width: 720px) { .nav-toggle { display: flex; } nav.primary { display: none; } … }` (`aaro/index.html:97-112`, `nasa/index.html:82-95`). A secondary breakpoint at `719px` covers fine details (`aaro/index.html:448`).
- Hamburger button is **38 × 38 px** (`aaro/index.html:92`) / **40 × 40 px** (`nasa/index.html:77`) — both above the 36 px DOM minimum; mobile nav links are `padding: 12px 0` (CLAUDE.md §8 calls for ≥ 44 × 44 px touch targets — `12px` vertical padding on `display: block` links delivers that).
- Lightbox nav buttons: **52 × 52 px desktop, 40 × 40 mobile**, edge-pinned (`aaro/index.html:441`).
- `body { overflow-x: hidden; }` is set as the last-resort guard rail (`aaro/index.html:43`).
- `<input>` and `<select>` reach `width: 100%` below 720 px (`aaro/index.html:107`).
- Tab strip wraps with `flex-wrap: wrap` — never horizontal-scrolls (`aaro/index.html:105`).

## JavaScript Invariants (CLAUDE.md §7 — applied across every archive)

Every archive's inline script implements these. Audit checklist for new archives:

1. **Hamburger toggle** — gets `nav-toggle` + `primary-nav` elements, toggles `.open` class, sets `aria-expanded`, collapses on inner link click. Pattern at `aaro/index.html:855-866`.
2. **Lightbox** — opens at index, wraps with modulo arithmetic on prev/next, closes on Escape and outside click. Pattern at `aaro/index.html:1262-1287`.
3. **Arrow-key + swipe navigation** — `keydown` listener with `ArrowLeft`/`ArrowRight`/`Escape`; touch swipe > 50 px horizontal, < 800 ms duration, < 60 px vertical drift = navigate. `aaro/index.html:1270-1281`.
4. **Image fallback** via `<img onerror>` — see Error Handling above.
5. **Video multi-source** — local `<source>` first, remote `<source>` second, inside one `<video>` element. `aaro/index.html:1241-1247`.
6. **PDF lightbox** — iframe ONLY for local files; release URLs open in a new tab. `aaro/index.html:1250-1256`.
7. **Card click delegation** — uses both `data-idx` (for `openAt`) and `data-action="open"` (`aaro/index.html:1122-1134`).
8. **`/` keydown focuses search input** — guarded against typing-in-input and against modifier keys. Pattern at `search.html:1134-1143`.
9. **Search query persists in `?q=`** — restored on load via `URLSearchParams`, debounced-pushed via `history.replaceState`. Pattern at `search.html:1099-1131`.
10. **Carousel autoplay** — `setInterval(goTo, 6500)`, pauses on `mouseenter`, resumes on `mouseleave`. `aaro/index.html:932-937`.

## Python Conventions (Build Scripts)

**Git-tracking-aware local detection (mandatory):**

```python
def git_tracked(rel_dir):
    """Set of filenames committed under <repo>/<slug>/<rel_dir>/."""
    try:
        out = subprocess.run(
            ['git', '-C', REPO, 'ls-files', f'{slug}/{rel_dir}/'],
            capture_output=True, text=True, check=True,
        ).stdout
        prefix = f'{slug}/{rel_dir}/'
        return {ln[len(prefix):] for ln in out.splitlines() if ln.startswith(prefix)}
    except (subprocess.CalledProcessError, FileNotFoundError):
        p = os.path.join(ROOT, rel_dir)
        return set(os.listdir(p)) if os.path.isdir(p) else set()
```
**Why:** GitHub Pages only serves git-tracked files. If a gitignored file exists on the dev machine but not in the repo, `os.listdir()` would falsely mark it `local` and the Download button would 404 on the deployed site. Used in `scripts/build-aaro.py:31`, `scripts/build-nasa.py:16`, `scripts/build-uk.py:21`, `scripts/build-brazil.py:18`, `scripts/build-chile.py:18`, `scripts/build-geipan.py:17`, `scripts/build-nara.py:19`, `scripts/build-wargov.py:34`. **One exception:** `scripts/build-details.py:34-36` uses `os.listdir` because it builds story pages that only run locally during development.

**Manifest embedding:**
- One `<script id="arch-data" type="application/json">…</script>` block per archive, inline.
- JSON shape is either a flat list `[{...}, {...}, ...]` or `{"assets": [...], "carousel": [...], "stats": {...}}` (aaro). Both are accepted by the lightbox JS and by `scripts/validate-manifests.py`.

**Release URL builder:**
```python
PDF_RELEASE_BASE = 'https://github.com/hectorchanht/war-gov-ufo-release/releases/download/pdfs-v1/'
def R(fname): return PDF_RELEASE_BASE + urllib.parse.quote(fname)
```
Per archive, use the matching tag (`videos-v1`, `pdfs-v1`, `geipan-v1`, …) per CLAUDE.md §5.1.

## Shell Conventions (Download Scripts)

**Mandatory boilerplate at top of every `scripts/dl-*.sh`:**
```bash
#!/usr/bin/env bash
# ============================================================
# <Archive> downloader.
# <one-paragraph purpose statement>
# Idempotent.
# ============================================================
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
```

**Realistic Chrome UA is required** — many upstream hosts (especially Akamai-fronted `.mil` and `.gov`) block default `curl` UA. Same UA string used across all `scripts/dl-*.sh` files for consistency.

**Idempotent `fetch` helper:**
```bash
fetch() {
  local url="$1" dest="$2"
  [ -s "$dest" ] && { echo "  [cache] $(basename "$dest")"; return 0; }
  if curl -fsSL --max-time 120 --connect-timeout 15 -A "$UA" -o "$dest" "$url"; then
    echo "  [ok]    $(basename "$dest") $(wc -c <"$dest" | tr -d ' ') bytes"
  else
    rm -f "$dest"; echo "  [FAIL]  $(basename "$dest")"; return 1
  fi
}
```
The non-zero return on failure plus `set -uo pipefail` (note: no `-e`) means callers see the failure but the run continues.

**Wayback fallback** (for Akamai-blocked sources):
```bash
# Direct fetch fails → look up Wayback snapshot → retry with web.archive.org/web/<ts>id_/<url>
# Format flags: if_ (frames), im_ (image), id_ (identity bytes)
```
Full implementation at `scripts/dl-aaro.sh:53-82`. Use `id_` for binary downloads (PDFs, mp4), `im_` for images.

## House-Style "Don'ts" (CLAUDE.md §11 — strict)

- ❌ Inline arrow `↗` inside header nav links (save for explicit external links)
- ❌ "OFFLINE MIRROR" banner above the header
- ❌ `crossorigin="anonymous"` on `<video>` (kills cloudfront playback)
- ❌ Single-`<source>` `<video>` when both local and remote URLs are known
- ❌ Filler `desc` strings ("click to play", "view file", "released document"). Empty is fine.
- ❌ `os.listdir()` alone for local detection — always wrap in `git_tracked()`
- ❌ Skipping mobile testing — 360 px is the canonical first viewport
- ❌ Force-pushes to main
- ❌ Touching `uap-release001.csv` (legacy source of truth)
- ❌ Calling archive pages "mirrors" in user-facing copy

## Shared Design Tokens (CLAUDE.md §3.2 — do not deviate)

Every archive's inline CSS opens with the same `:root` block. The only variable that changes per archive is `--caution`. CLAUDE.md §3.1 enumerates the 15 approved `--caution` values; the seal `radial-gradient` is per-archive too. Everything else (palette, fonts, rule colors, classified red, gold warm) is shared.

```css
:root {
  --bg:#0a0a0c; --bg-2:#111114; --panel:#15151a;
  --ink:#e8e3d8; --ink-dim:#a8a298; --ink-faint:#6b665d;
  --rule:rgba(232,227,216,0.12); --rule-strong:rgba(232,227,216,0.28);
  --stamp:#b91c1c; --caution:<archive-accent>; --warm:#d4a017; --classified:#c9362c;
  --serif:"Source Serif 4","Iowan Old Style",Georgia,serif;
  --mono:"JetBrains Mono","SF Mono",Consolas,monospace;
}
```

**Typography rules:**
- Serif for prose, hero titles, card titles
- Mono for nav, metadata labels, badges, code
- Mono letter-spacing 0.08–0.24em
- **No third font.** No Google Fonts beyond Source Serif 4 + JetBrains Mono.

## Accessibility

- Every interactive `<button>` has an `aria-label` (nav-toggle, carousel-prev/next, lb-rotate, lb-prev, lb-next).
- `<nav>` carries `aria-label="Main navigation"`.
- `<div class="lightbox">` toggles `aria-hidden="true"`/`"false"` on open/close.
- Hamburger toggles `aria-expanded="true"`/`"false"` on click.
- Dropdown menus use `role="menu"` on the `<ul>`.
- Carousel container has `aria-label="Featured … imagery"` describing the gallery.
- `<img>` always has an `alt` attribute, even if computed from `a.ti`.
- Lighthouse accessibility score is a **hard CI gate at 0.90** — drop below and CI fails.

## Drift Observed (aaro vs. nasa)

Comparing `aaro/index.html` against `nasa/index.html` against CLAUDE.md §3-§4:

- **Container max-width differs:** aaro uses `max-width: 1280px` (`aaro/index.html:55`); nasa uses `max-width: 1200px` (`nasa/index.html:44`). CLAUDE.md does not pin a width; both are acceptable.
- **Body font-size on desktop differs:** aaro `17px` (`aaro/index.html:38`), nasa `16px` (`nasa/index.html:37`). CLAUDE.md §3.3 says "16 px desktop, 15 px mobile" — aaro drifts +1px on desktop. Low priority but flagged.
- **Hamburger button size differs:** aaro `38×38` (`:92`), nasa `40×40` (`:77`). Both above the 36 px DOM floor; both deliver ≥ 44 px effective touch area via padding. CLAUDE.md §8 floor is satisfied either way.
- **Scroll-padding differs:** aaro `64px` (`:35`), nasa `70px` (`:34`) — matches each page's sticky-header height. Correct per-page.
- **`flex-wrap` on header `.container`:** aaro `nowrap` (`:77`), nasa `wrap` (`:64`). nasa's wrap is the more forgiving choice on small viewports.

None of these block a build. The drift is normal evolution; the JS invariants and design tokens are consistent.

---

*Convention analysis: 2026-05-25*
