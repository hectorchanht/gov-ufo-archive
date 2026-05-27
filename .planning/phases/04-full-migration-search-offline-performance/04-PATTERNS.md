# Phase 4: Full Migration, Search, Offline, Performance — Pattern Map

**Mapped:** 2026-05-27
**Files analyzed:** ~45 new/modified files across ~19 Phase 4 plans
**Analogs found:** 38/45 (84%) with strong analogs; 7 files have no direct analog (Pagefind UI, sw.ts, r2-sync.yml — new infrastructure)

Phase 4 introduces three distinct file categories:

1. **Cross-cutting infrastructure** (lightbox-fix, R2, SW, Pagefind, pagination) — surgical patches OR brand-new files with no in-repo analog
2. **14 archive ports** — every port plan copies the same wargov template (Plan 03-05 outputs)
3. **Phase 4 close** — deletion-only commits (no new code; analog = "absence of file")

The dominant pattern: **wargov-everything-as-template**. Plan 03-05's `src/pages/index.astro` + `Card.astro` + `normalize-csv.py` + `wargov.css` are the byte-for-byte template for 14 archive ports. The catalogEnvelopeSchema (Plan 03-02) is already wired in `src/content.config.ts` — Phase 4 normalizers just need to fill it.

---

## File Classification

### Cross-cutting Phase 4 plans (5 plans, ~15 files)

| New/Modified File | Plan | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|------|-----------|----------------|---------------|
| `src/components/Card.astro` (PATCH) | 04-01-lightbox-fix | component | event-driven | `src/components/Card.astro` (itself, Plan 03-05) | exact (surgical patch) |
| `scripts/normalize-csv.py` (PATCH) | 04-01-lightbox-fix | utility/normalizer | transform | `scripts/normalize-csv.py` (itself, Plan 03-03) | exact (mirror Card.astro patch) |
| `src/scripts/invariants.ts` (PATCH) | 04-01-lightbox-fix | utility | event-driven | `src/scripts/invariants.ts` (itself, Plan 03-04) | exact (surgical patch) |
| `tests/lightbox.spec.ts` (NEW) | 04-01-lightbox-fix | test | request-response | `tests/visual-regression.spec.ts` | role-match |
| `r2-cors.json` (NEW) | 04-02-r2-setup | config | n/a | none (CF-specific) | no analog |
| `.github/workflows/r2-sync.yml` (NEW) | 04-02-r2-setup | config (CI) | event-driven | `.github/workflows/quality-gates.yml` | role-match |
| `scripts/_archive_common.py` (NEW) | 04-02-r2-setup | utility | transform | helper module pattern; `scripts/normalize-csv.py` _slugify+_e | partial |
| `tests/r2-urls.spec.ts` (NEW) | 04-02-r2-setup | test | request-response | `scripts/verify-redirects.sh` | partial |
| `astro.config.mjs` (PATCH) | 04-03-sw-injectmanifest | config | n/a | `astro.config.mjs` (itself, Plan 03-01) | exact (add integration) |
| `src/sw.ts` (NEW) | 04-03-sw-injectmanifest | utility (worker) | event-driven | `src/scripts/invariants.ts` (template-literal pattern, not behaviour) | partial |
| `src/layouts/BaseHead.astro` (PATCH) | 04-03-sw-injectmanifest | component | request-response | `src/layouts/BaseHead.astro` (itself, Plan 03-04) | exact (swap fonts) |
| `tests/sw.spec.ts` (NEW) | 04-03-sw-injectmanifest | test | event-driven | `tests/visual-regression.spec.ts` | role-match (different scope) |
| `src/pages/index.astro` (PATCH — repaging) | 04-04-wargov-repaging | component (page) | request-response | `src/pages/index.astro` (itself, Plan 03-05) | exact (replace IO block) |
| `tests/pagination.spec.ts` (NEW) | 04-04-wargov-repaging | test | request-response | `tests/visual-regression.spec.ts` | role-match |
| `src/pages/search.astro` (NEW) | 04-NN-pagefind | component (page) | request-response | `src/pages/index.astro` | role-match (different content) |
| `src/layouts/RootLayout.astro` (PATCH) | 04-NN-pagefind | component | n/a | `src/layouts/RootLayout.astro` (itself, Plan 03-04) | exact (add data-pagefind-body) |
| `scripts/copy-legacy-archives.sh` (PATCH) | 04-NN-pagefind | config (script) | transform | `scripts/copy-legacy-archives.sh` (itself, Plan 03-06) | exact (append pagefind command) |
| `tests/search.spec.ts` (NEW) | 04-NN-pagefind | test | request-response | `tests/visual-regression.spec.ts` | role-match |

### 14 archive port plans (each plan creates ~3-4 files, total ~50 files)

| New File (per slug, repeat 14×) | Plan | Role | Data Flow | Closest Analog | Match Quality |
|---------------------------------|------|------|-----------|----------------|---------------|
| `src/pages/<slug>/index.astro` | 04-NN-<slug> | component (page) | request-response | `src/pages/index.astro` | exact (template) |
| `src/components/CatalogCard.astro` (created in first port plan, reused after) | 04-NN-<first-port> | component | event-driven | `src/components/Card.astro` | role-match (different schema) |
| `scripts/normalize-<slug>.py` | 04-NN-<slug> | utility (normalizer) | transform | `scripts/normalize-csv.py` | role-match (catalog shape) |
| `src/styles/<slug>.css` (optional) | 04-NN-<slug> | config (style) | n/a | `src/styles/wargov.css` | exact (template) |

### Phase 4 close (deletions, no new code)

| Modified | Plan | Role | Analog |
|----------|------|------|--------|
| `.lighthouserc.cf.json` (HARD-flip) | 04-NN-close | config | itself (Phase 2 02-08) — flip `warn → error` |
| `scripts/copy-legacy-archives.sh` (DELETE) | 04-NN-close | n/a | n/a |
| `scripts/sync-nav.py` + `scripts/sync-footer.py` (DELETE) | 04-NN-close | n/a | n/a |
| `scripts/build-*.py` (each DELETE) | individual port plans | n/a | n/a |
| `api/all.json` (DELETE, 4.6 MB) | 04-NN-pagefind | n/a | n/a |
| 14 legacy `<slug>/index.html` (DELETE on port) | individual port plans | n/a | n/a |

---

## Pattern Assignments

### 1. `src/pages/<slug>/index.astro` (14× — one per archive)

**Role:** component (page) · **Data flow:** request-response · **Analog:** `src/pages/index.astro` (Plan 03-05)

This is the highest-frequency pattern in Phase 4. Every port copies this template.

**Imports + getEntry pattern** (`src/pages/index.astro` lines 29-43):
```astro
import RootLayout from '../../layouts/RootLayout.astro';
import CatalogCard from '../../components/CatalogCard.astro';  // NEW — created in first port
import Lightbox from '../../components/Lightbox.astro';
import { getEntry } from 'astro:content';
import '../../styles/<slug>.css';  // per-archive CSS (optional)

const entry = await getEntry('<slug>', 'v1');
if (!entry) {
  throw new Error(
    '<slug> collection entry "v1" missing — run `pnpm prebuild` to regenerate data/<slug>.json',
  );
}
const { assets, stats } = entry.data;
```

**Slugify helper** (`src/pages/index.astro` lines 51-55) — copy verbatim:
```typescript
function slugify(text: string): string {
  if (!text) return '';
  const s = text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  return s.slice(0, 80).replace(/^-+|-+$/g, '');
}
```

**RootLayout invocation** (`src/pages/index.astro` lines 122-128) — change archiveSlug only:
```astro
<RootLayout
  archiveSlug="<slug>"      {/* NEW per port */}
  title={title}
  description={description}
  totalRecords={stats.total}
  lastUpdated="2026-05-27"
>
```

**Server-rendered card grid** (`src/pages/index.astro` lines 272-280) — adapt to assets[]:
```astro
<div class="arch-grid" id="<slug>-grid">
  {assets.map((asset, idx) => (
    <CatalogCard asset={asset} idx={idx} slug={slugify(asset.ti)} archiveSlug="<slug>" />
  ))}
</div>
```

**Lightbox + pagination script blocks:** copy lines 282-476 from wargov index.astro, AFTER `04-04-wargov-repaging` lands. Pre-repaging wargov uses IntersectionObserver lazy-load (D-33 retires this); per-archive ports must adopt the `?page=N` client-side windowing pattern (see §3 below).

**HeroCarousel inclusion:** OPTIONAL per archive. Default OFF. Only include for archives with ≥4 representative images (AARO, NASA, NARA candidates per 04-RESEARCH.md §8). When included, reuse `HeroCarousel.astro` verbatim (no edits).

---

### 2. `scripts/normalize-<slug>.py` (14× — one per archive)

**Role:** utility (normalizer) · **Data flow:** transform · **Analog:** `scripts/normalize-csv.py` (Plan 03-03)

Each per-archive normalizer follows the same structure as `normalize-csv.py` but emits the `catalogEnvelopeSchema` shape instead of wargov's CSV-keyed shape.

**Header docstring pattern** (`scripts/normalize-csv.py` lines 1-89) — adapt source path:
```python
"""<slug> source → data/<slug>.json normaliser (Plan 04-NN / SSG-06).

Reads <source> (e.g. <slug>/.cache/parsed.json) and writes:
  data/<slug>.json
    Astro `file()` loader entries-object form:
      { "v1": { "schemaVersion": 1, "slug": "<slug>",
                "assets": [<catalog assets>],
                "stats": {...} } }
    Validated against `catalogEnvelopeSchema` from `src/content.config.ts`.

Invariants (from CLAUDE.md §11 + 04-CONTEXT.md):
- Source data is READ-ONLY (CSV/cache untouchable per CLAUDE.md §11)
- D-04: deterministic JSON (sort_keys=True, ensure_ascii=False, indent=2 + \\n)
- D-26..D-28: zero text-field transforms beyond html.escape on render
- D-01..D-06 (Phase 4 R2): rewrite_to_r2() called on every PDF/video URL
"""
```

**Stdlib-only imports + REPO constant** (`scripts/normalize-csv.py` lines 90-115):
```python
from __future__ import annotations
import argparse, html, json, re, subprocess, sys
from pathlib import Path
from typing import Any
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _archive_common import rewrite_to_r2, slugify  # NEW shared helper (Plan 04-02)

REPO = Path(__file__).resolve().parent.parent
OUT_PRIMARY = REPO / 'data' / '<slug>.json'
PUBLIC_DATA_DIR = REPO / 'public' / 'data'
```

**Deterministic JSON write** (`scripts/normalize-csv.py` lines 385-401) — copy verbatim:
```python
def _serialise(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n'

def _write_json(path: Path, data: Any) -> None:
    path.write_text(_serialise(data), encoding='utf-8')
```

**catalogEnvelopeSchema envelope shape** (per `src/content.config.ts` lines 63-107):
```python
def _build_envelope(assets: list[dict], total: int, local: int, pdf: int, catalog: int) -> dict:
    return {
        'v1': {
            'schemaVersion': 1,
            'slug': '<slug>',
            'assets': assets,
            'stats': {
                'total': total,
                'local_total': local,
                'pdf_total': pdf,
                'catalog_total': catalog,
            },
        },
    }
```

**Asset shape per `catalogAssetSchema.strict()`** (each asset dict MUST contain exactly these keys):
```python
{
    't':      'PDF' | 'VID' | 'IMG' | 'CATALOG' | 'AUDIO' | 'CASE' | 'PAGE',
    'ti':     str,  # title — verbatim, no transform
    'de':     str,  # description — verbatim or ''
    'ag':     str,  # agency
    'cat':    str,  # category
    'date':   str,  # date
    'region': str,  # geographic context
    'l':      str,  # local path ('' if not committed)
    'u':      str,  # URL — Phase 4: R2 URL via rewrite_to_r2()
    's':      str,  # source page URL (optional in schema, emit '')
    'th':     str,  # thumbnail path
}
```

**R2 URL rewrite** (NEW Phase 4 pattern, per 04-RESEARCH.md §4) — every PDF/video URL goes through:
```python
asset_url = rewrite_to_r2(local_filename, '<slug>', 'pdfs' if is_pdf else 'videos')
# e.g. -> 'https://assets.realufo.org/pdfs/<slug>/<file>.pdf'
```

**Source-data-untouchable guard** (`scripts/normalize-csv.py` lines 355-379) — adapt path:
```python
def _assert_source_unchanged() -> None:
    """Fail if normaliser accidentally mutated <slug>/.cache/* source."""
    try:
        rc = subprocess.run(
            ['git', '-C', str(REPO), 'diff', '--quiet', '--', '<slug>/.cache/'],
            check=False,
        ).returncode
    except FileNotFoundError:
        return
    if rc != 0:
        sys.stderr.write('[error] source mutation detected — CLAUDE.md §11 forbids\n')
        sys.exit(1)
```

**Public/data mirror** (`scripts/normalize-csv.py` lines 506-514) — copy verbatim:
```python
PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
_write_json(PUBLIC_DATA_DIR / '<slug>.json', primary)
```

---

### 3. `src/components/CatalogCard.astro` (NEW, created in first port plan, reused 13×)

**Role:** component · **Data flow:** event-driven · **Analog:** `src/components/Card.astro` (Plan 03-05)

Catalog-shape Card. Takes a `catalogAssetSchema`-validated asset instead of `WargovRow`. Field names short (`t`, `ti`, `de`, `ag`, `cat`, `date`, `region`, `l`, `u`, `s`, `th`) — they come from existing Python `scripts/templates/archive.py` shape preserved by `src/content.config.ts` schema.

**Props interface pattern** (`src/components/Card.astro` lines 30-57):
```astro
---
interface CatalogAsset {
  t: 'PDF' | 'VID' | 'IMG' | 'CATALOG' | 'AUDIO' | 'CASE' | 'PAGE';
  ti: string;
  de: string;
  ag: string;
  cat: string;
  date: string;
  region: string;
  l: string;   // local path
  u: string;   // R2 URL post-Phase-4
  s?: string;  // source page URL
  th: string;  // thumbnail
}

interface Props {
  asset: CatalogAsset;
  idx: number;
  slug: string;
  archiveSlug: string;  // NEW — drives data-pagefind-filter
}

const { asset, idx, slug, archiveSlug } = Astro.props;
const rowId = `r${String(idx + 1).padStart(3, '0')}`;
---
```

**Article markup — copy structure from Card.astro lines 79-122, MODIFIED per 04-RESEARCH.md §7 lightbox-fix:**
```astro
<article
  class="arch-card"
  id={`card-${slug}`}
  data-id={rowId}
  data-row-id={rowId}                {/* NEW — lightbox fix patch A */}
  data-action="open"
  data-type={asset.t}
  data-agency={asset.ag}
  data-date={asset.date}
  data-pagefind-filter={`archive:${archiveSlug},type:${asset.t},agency:${asset.ag}`}
  data-pagefind-meta={`title:${asset.ti},agency:${asset.ag},date:${asset.date}`}
>
  {asset.th && (
    <img
      loading="lazy"
      src={asset.th}
      data-fallback={asset.u}
      alt={asset.ti}
      onerror="this.onerror=null;this.src=this.dataset.fallback||''"
    />
  )}
  <h3 class="card-title">{asset.ti}</h3>
  {asset.de && <p class="card-desc">{asset.de}</p>}
  <dl class="card-meta">
    <dt>Agency</dt><dd>{asset.ag}</dd>
    <dt>Date</dt><dd>{asset.date}</dd>
    <dt>Type</dt><dd>{asset.t}</dd>
  </dl>
  <div class="card-actions">
    {asset.u && (
      <a
        href="#"                       {/* CHANGED — patch A: btn-open no longer carries URL */}
        class="btn-open"
        data-action="open"
        data-row-id={rowId}            {/* NEW — patch A */}
        data-url={asset.u}             {/* NEW — explicit URL field */}
        data-local={asset.l || ''}     {/* NEW — separate local field (patch A) */}
      >Open</a>
    )}
    {asset.u && (
      <a
        href={asset.l || asset.u}      {/* CHANGED — download prefers local */}
        class="btn-download"
        data-url={asset.u}
        data-local={asset.l || ''}
        download
      >Download</a>
    )}
    {asset.s && (
      <a href={asset.s} class="btn-source" target="_blank" rel="noopener">Source ↗</a>
    )}
  </div>
</article>
```

---

### 4. `src/components/Card.astro` (PATCH — Plan 04-01 lightbox-fix)

**Role:** component · **Data flow:** event-driven · **Analog:** `src/components/Card.astro` (itself)

**Reference patches** — see 04-RESEARCH.md §7 Patches A–D for the exact diffs. Summary:

Three new data attributes on `<article>` and on `<a class="btn-open">`:
- `data-row-id={rowId}` (replaces reliance on `data-idx` for lightbox lookup)
- `data-url={url}` (separate from anchor href, which can change for download)
- `data-local={row.local || ''}` (explicit local-vs-remote PDF branching)

The `<a class="btn-open" href={url}>` becomes `<a class="btn-open" href="#" data-url={url} data-local={local}>` — preventDefault is already in invariants.ts click delegate.

**CRITICAL pairing per 04-RESEARCH.md Pitfall #12:** `scripts/normalize-csv.py:render_card_html()` (lines 209-307) MUST receive the byte-equivalent patch in the same commit. The shard HTML strings must match Card.astro's compiled output exactly (D-10 LOCKED). The Python function already mirrors line-by-line — apply the same three new attributes.

---

### 5. `src/scripts/invariants.ts` (PATCH — Plan 04-01 lightbox-fix)

**Role:** utility · **Data flow:** event-driven · **Analog:** `src/scripts/invariants.ts` (itself, Plan 03-04)

**Reference patches** — see 04-RESEARCH.md §7 Patches C–D. Surgical edits to two functions:

`openAt(rowIdOrIdx)` — lookup by `data-row-id` first, fall back to numeric idx (preserves Phase 3 invariants behaviour):
```javascript
function openAt(rowIdOrIdx) {
  if (!lb) return;
  lbList = (window.__lbList && window.__lbList.length) ? window.__lbList : lbList;
  if (!lbList.length) return;
  let foundIdx = lbList.findIndex(x => x.rowId === rowIdOrIdx);
  if (foundIdx < 0) {
    const n = parseInt(rowIdOrIdx, 10);
    if (!isNaN(n)) foundIdx = ((n % lbList.length) + lbList.length) % lbList.length;
  }
  if (foundIdx < 0) return;
  lbIdx = foundIdx;
  renderLb();
  lb.classList.add('open');
  lb.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
}
```

Click delegate (lines 163-174) — pass `dataset.rowId` with `dataset.idx` fallback:
```javascript
document.addEventListener('click', function (e) {
  var action = e.target.closest && e.target.closest('a[data-action="open"]');
  if (!action) return;
  e.preventDefault();
  var rowId = action.dataset.rowId || action.dataset.idx;
  if (rowId === undefined) {
    var card = action.closest('.card, .arch-card');
    rowId = card && (card.dataset.rowId || card.dataset.idx);
  }
  if (rowId) openAt(rowId);
});
```

**Bug 2 fix is fully covered by Card.astro patch** — once `data-local` is separate from `data-url`, the existing `renderLb()` lines 65-92 work correctly (local → iframe; remote → "Open in new tab" panel).

---

### 6. `src/pages/index.astro` (PATCH — Plan 04-04 wargov-repaging)

**Role:** component (page) · **Data flow:** request-response · **Analog:** `src/pages/index.astro` (itself, Plan 03-05)

Replace the IntersectionObserver block (lines 302-351) with the `?page=N` client-side pagination handler — see 04-RESEARCH.md §6 for the 80-line skeleton. Key behaviour:

- PAGE_SIZE = 20 (D-27)
- Reads `URLSearchParams.get('page')` on load
- Fetches all shards upfront (~250 KB for wargov) via `Promise.all`
- `insertAdjacentHTML('beforeend', ...)` for each card (D-10 LOCKED preserved)
- `display:none` toggle for off-page cards (lightbox prev/next still sees all cards per Pitfall #6)
- `history.pushState` on pagination link clicks
- `popstate` listener for browser back/forward
- Hash-aware: `#card-<id>` resolves cross-page

**Pagination nav markup** — add inside `<section class="archive">`:
```astro
<nav class="pagination" id="wargov-pagination" data-pagefind-ignore aria-label="Pagination"></nav>
```

**`refreshLbList` MUST walk ALL `.arch-card`** (not just visible) per Pitfall #6:
```javascript
function refreshLbList() {
  const list = [];
  // Walk ALL cards regardless of display:none (lightbox prev/next crosses pages).
  for (const c of grid.querySelectorAll('.arch-card')) {
    const rowId = c.dataset.rowId;
    const openA = c.querySelector('a.btn-open');
    list.push({
      rowId,
      title: (c.querySelector('.card-title')?.textContent) || '',
      url: openA ? openA.dataset.url : '',
      local: openA ? (openA.dataset.local || '') : '',
    });
  }
  window.__lbList = list;
}
```

---

### 7. `astro.config.mjs` (PATCH — Plan 04-03 sw-injectmanifest)

**Role:** config · **Data flow:** n/a · **Analog:** `astro.config.mjs` (itself, Plan 03-01)

**Current state** (line 31): `integrations: []`. Phase 4 fills it with `AstroPWA({...})`.

**Full integrations block** — copy verbatim from 04-RESEARCH.md §3:

```javascript
import AstroPWA from '@vite-pwa/astro';
const cacheVersion = process.env.COMMIT_SHA?.slice(0, 7) || 'dev';

integrations: [
  AstroPWA({
    strategies: 'injectManifest',
    srcDir: 'src',
    filename: 'sw.ts',
    registerType: 'autoUpdate',
    injectRegister: false,  // BaseHead.astro handles registration (D-19)
    injectManifest: {
      globPatterns: [
        '**/*.{html,css,js,svg,webp,png,jpg,jpeg,woff2,ico}',
        'pagefind/pagefind*.{js,css}',
      ],
      globIgnores: [
        '**/*.{pdf,mp4,webm,mov,mp3,wav,zip}',
        'sw.js', 'sw.js.map', 'workbox-*.js',  // Pitfall #1
        'pagefind/index/**',
        'pagefind/fragment/**',
      ],
      maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
    },
    manifest: { /* ... see RESEARCH §3 ... */ },
  }),
],
```

**Preserve** lines 22-27 (markdown smartypants:false — fidelity guard) and lines 36-39 (trailingSlash:'ignore').

---

### 8. `src/sw.ts` (NEW — Plan 04-03 sw-injectmanifest)

**Role:** utility (service worker) · **Data flow:** event-driven · **Analog:** no in-repo analog (closest is `src/scripts/invariants.ts` for the inline-pattern aesthetic, but behaviour is unrelated)

**Reference:** 04-RESEARCH.md §3 has the full 90-line `sw.ts` skeleton with all 5 runtime cache strategies (NetworkFirst HTML, SWR JSON, CacheFirst images/fonts, NetworkOnly PDFs/videos, NetworkOnly /admin*).

**Critical patterns to copy verbatim from RESEARCH §3:**
- Cache prefix `realufo-v${COMMIT_SHA.slice(0,7)}` (D-22)
- Activate handler purges old `realufo-v*` caches before claim
- Install handler gated by `ALLOW_SKIP_WAITING` constant (Pitfall #4 — start FALSE)
- `IMAGE_ORIGINS = [self.location.origin, 'https://assets.realufo.org']` for R2 cache-first
- `CacheableResponsePlugin({ statuses: [0, 200] })` on every cross-origin route (Pitfall #2)

---

### 9. `src/layouts/BaseHead.astro` (PATCH — Plan 04-03 SW + fonts)

**Role:** component · **Data flow:** request-response · **Analog:** `src/layouts/BaseHead.astro` (itself, Plan 03-04)

**Two surgical edits:**

(a) **Replace Google Fonts** (current lines 50-56) with `@fontsource/*` imports in frontmatter (per 04-RESEARCH.md §3):
```astro
---
import '../styles/global.css';
import '@fontsource/source-serif-4/400.css';
import '@fontsource/source-serif-4/600.css';
import '@fontsource/source-serif-4/400-italic.css';
import '@fontsource/jetbrains-mono/400.css';
import '@fontsource/jetbrains-mono/500.css';
import '@fontsource/jetbrains-mono/700.css';
---
```
Delete the `<link rel="preconnect">` × 2 + `<link href="...fonts.googleapis.com...">` lines.

(b) **Keep SW registration block as-is** (lines 65-71) — the kill-switch SW from Phase 1 simply gets replaced by the new injectManifest-emitted `/sw.js`. The `updateViaCache: 'none'` invariant must remain.

---

### 10. `scripts/copy-legacy-archives.sh` (PATCH — Plan 04-NN-pagefind + per-port plans)

**Role:** config (script) · **Data flow:** transform · **Analog:** `scripts/copy-legacy-archives.sh` (itself, Plan 03-06)

**Two changes over Phase 4 lifecycle:**

(a) **Each port plan drops its slug from line 53:**
```bash
# Phase 3 baseline:
for slug in aaro nasa nara geipan uk brazil chile argentina canada italy nz peru spain uruguay; do

# After 04-06-aaro port (example):
for slug in nasa nara geipan uk brazil chile argentina canada italy nz peru spain uruguay; do
```

(b) **Pagefind plan appends after copy step:**
```bash
# At end of script, before final echo:
echo "[postbuild] pagefind: indexing dist/ ..."
pnpm exec pagefind --site dist
```

(c) **Phase 4 close (Plan 04-NN-close) DELETES the file** when all 14 slugs are ported. `package.json scripts.postbuild` then either deletes entirely or becomes `pnpm exec pagefind --site dist` only.

---

### 11. `.github/workflows/r2-sync.yml` (NEW — Plan 04-02 r2-setup)

**Role:** config (CI) · **Data flow:** event-driven · **Analog:** `.github/workflows/quality-gates.yml` (Phase 2 02-08)

**Reference:** 04-RESEARCH.md §5 has the full 80-line workflow. Copy verbatim.

**Patterns shared with quality-gates.yml:**
- `permissions: contents: read` (line 1 of quality-gates.yml block)
- `concurrency: group: r2-sync, cancel-in-progress: false` (Phase 2 uses `cancel-in-progress: true`; r2-sync uses `false` because uploads must complete)
- `runs-on: ubuntu-latest`, `timeout-minutes: 30`
- Secrets via `${{ secrets.CLOUDFLARE_API_TOKEN }}` + `${{ secrets.CLOUDFLARE_ACCOUNT_ID }}`

**New pattern (no existing analog):** `rclone sync --checksum --progress` for R2 bulk upload.

---

### 12. `src/pages/search.astro` (NEW — Plan 04-NN-pagefind)

**Role:** component (page) · **Data flow:** request-response · **Analog:** `src/pages/index.astro` (skeleton); no analog for Pagefind UI itself

**Page skeleton from `src/pages/index.astro`** lines 122-128 (RootLayout invocation pattern):
```astro
---
import RootLayout from '../layouts/RootLayout.astro';
---
<RootLayout
  archiveSlug="wargov"   {/* wargov tone — search lives at /search */}
  title="Search · realufo.org"
  description="Search 15 government UAP archives"
>
  <section class="search-container">
    <div id="pagefind-search"></div>
  </section>

  <link rel="stylesheet" href="/pagefind/pagefind-ui.css" />
  <script is:inline src="/pagefind/pagefind-ui.js"></script>
  <script is:inline>
    window.addEventListener('DOMContentLoaded', () => {
      new PagefindUI({
        element: '#pagefind-search',
        showSubResults: true,
        showImages: false,
        translations: { placeholder: 'Search 15 archives...' },
        filters: { archive: 'Archive', type: 'Type', agency: 'Agency' },
        processResult: (result) => {
          // Pitfall #9 — append #card-<id> to result URL
          if (result.sub_results?.[0]?.anchor?.id) {
            result.sub_results[0].url = `${result.url}#${result.sub_results[0].anchor.id}`;
          }
          return result;
        },
      });
    });
  </script>
</RootLayout>
```

---

### 13. `src/layouts/RootLayout.astro` (PATCH — Plan 04-NN-pagefind)

**Role:** component · **Data flow:** n/a · **Analog:** `src/layouts/RootLayout.astro` (itself, Plan 03-04)

**Single-line surgical edit at line 95-97:**
```astro
{/* Before: */}
<main>
  <slot />
</main>

{/* After (per 04-RESEARCH.md §2): */}
<main data-pagefind-body>
  <slot />
</main>
```

Per Pitfall #5: this edit lands AFTER all 14 archive ports complete. Otherwise legacy postbuild-copied HTML would be silently excluded from the index.

---

### 14. `tests/lightbox.spec.ts` (NEW — Plan 04-01)

**Role:** test · **Data flow:** request-response · **Analog:** Playwright spec pattern in `tests/visual-regression.spec.ts` (Phase 2 02-03)

**No exact analog in current repo** — Phase 4 introduces 5 new spec files (lightbox, search, sw, pagination, r2-urls) all following the same Playwright pattern. Copy structure from existing `tests/visual-regression.spec.ts` (Playwright `test()` blocks, `PREVIEW_URL` env var per Phase 2 02-03 contract).

**Required test cases per 04-RESEARCH.md §7 validation plan:**
- Click `.btn-open` on card #1 → `#lightbox.open` visible + correct title in iframe/img
- Press → arrow → counter advances + card #2 content
- Press Escape → lightbox closed
- Filter "Documents" tab + click Open on first visible card → THAT card opens (not card #1)
- Click remote PDF Open → `lb-meta` "Remote PDF" panel (not iframe — Bug 2 verification)
- `/?page=3` smoke (after 04-04 lands): card #41's Open button opens card #41's asset (Bug 1 verification)

---

## Shared Patterns (cross-cutting)

### Pattern A: Astro page skeleton (15 archives use this)

**Source:** `src/pages/index.astro` (Plan 03-05)
**Apply to:** Every `src/pages/<slug>/index.astro` (14 new) + `src/pages/search.astro` (1 new)

**Skeleton:**
```astro
---
import RootLayout from '<relative>/layouts/RootLayout.astro';
import { getEntry } from 'astro:content';
const entry = await getEntry('<slug>', 'v1');
if (!entry) throw new Error('...');
const { assets, stats } = entry.data;
---
<RootLayout archiveSlug="<slug>" title={title} description={description}>
  <!-- hero, headlines, archive grid, lightbox -->
</RootLayout>
```

### Pattern B: Stdlib-only Python normalizer (14 archives)

**Source:** `scripts/normalize-csv.py` (Plan 03-03)
**Apply to:** Every `scripts/normalize-<slug>.py`

**Anchors:** deterministic JSON serialization, source-data-unchanged guard, public/data mirror, `_archive_common.py` shared helpers (rewrite_to_r2, slugify).

### Pattern C: `<script is:inline>` progressive enhancement (every component with JS)

**Source:** `src/scripts/invariants.ts` (Plan 03-04) — exported string literal injected via `<script is:inline set:html={INVARIANTS_JS}>` in `RootLayout.astro` line 104.
**Apply to:** Pagination handler (Plan 04-04), Pagefind UI bootstrap (Plan 04-NN-pagefind), SW registration (already in BaseHead.astro lines 65-71).

**Invariants (D-21..D-23 from Phase 3):**
- NO `client:*` directives
- NO framework imports
- Plain ES2020 inside the template literal
- TypeScript types live OUTSIDE the literal (typecheck only — no transform)

### Pattern D: 15-archive TONE map respect

**Source:** `src/layouts/RootLayout.astro` lines 55-73 (TONE record) + Plan 03-04 contract
**Apply to:** Every `src/pages/<slug>/index.astro` passes correct `archiveSlug` to `<RootLayout>`. Tone-colour bugs for geipan/uk/brazil/chile (per Plan 03-06 SUMMARY) auto-resolve when each port deletes the legacy HTML from `copy-legacy-archives.sh` — the TONE map values are already correct in RootLayout.astro per Phase 3 audit.

### Pattern E: D-10 LOCKED — pre-rendered HTML strings in shards

**Source:** `scripts/normalize-csv.py:render_card_html()` lines 209-307 + lazy-load runtime in `src/pages/index.astro` lines 302-351
**Apply to:** Every per-archive normalizer that produces sharded data. The runtime ONLY calls `insertAdjacentHTML('beforeend', card.html)` — NO client-side templating, NO row-data-to-HTML construction in JS. GEIPAN (Wave 3, ~60 shards) is the largest consumer.

**Critical:** Card.astro patches (Plan 04-01) MUST mirror render_card_html() patches byte-for-byte (Pitfall #12). Visual-regression catches drift.

### Pattern F: Action button matrix (CLAUDE.md §4.3)

**Source:** `src/components/Card.astro` lines 105-121 (wargov shape) + CLAUDE.md §4.3 (verbatim contract)
**Apply to:** `src/components/CatalogCard.astro` and every card-rendering path.

| Button | Routes to | When shown |
|--------|-----------|------------|
| Open | `data-action="open"` → lightbox | Whenever asset.u OR asset.l exists |
| Download | asset.l if present, else asset.u | Whenever any downloadable URL exists |
| Source ↗ | asset.s (official site URL) | Whenever asset.s is known |
| DVIDS ↗ | DVIDS page | Only VID with `dvidsId` (wargov only currently) |

### Pattern G: Schema-strict envelope (Plan 03-02 contract)

**Source:** `src/content.config.ts` lines 63-107 (catalogAssetSchema with `.strict()`)
**Apply to:** Every per-archive normalizer's output. Unknown fields in `assets[]` FAIL the Astro build via Zod. If a scrape source emits a new column, the normalizer must either drop or remap — schema is locked.

### Pattern H: CLAUDE.md §11 source untouchability

**Source:** `scripts/normalize-csv.py` lines 355-379 (`_assert_csv_unchanged`)
**Apply to:** Every per-archive normalizer must guard its source data (`<slug>/.cache/*`, scraped JSON). Post-write `git diff --quiet -- <slug>/.cache/` check; exit 1 on diff.

### Pattern I: Per-archive Python retirement chain (SSG-10)

**Source:** Phase 4 D-09 + 04-RESEARCH.md §10
**Apply to:** Each `04-NN-<slug>` plan deletes in the same commit chain:
1. `scripts/build-<slug>.py`
2. `<slug>/index.html` (legacy HTML)
3. Slug from `scripts/copy-legacy-archives.sh` (line 53)
4. Slug from `scripts/sync-nav.py` policed-archives list (if applicable)
5. Slug from `scripts/sync-footer.py` policed-archives list (if applicable)

### Pattern J: CI workflow shape (Phase 4 r2-sync + future automation)

**Source:** `.github/workflows/quality-gates.yml` (Phase 2 02-08)
**Apply to:** `.github/workflows/r2-sync.yml` (Plan 04-02). Shared idioms: trigger type (push paths + workflow_dispatch), concurrency group, timeout-minutes, secrets via `${{ secrets.* }}`, `actions/checkout@v4`. Differs in `cancel-in-progress: false` (uploads MUST complete) and `fetch-depth: 2` (needs HEAD^ for diff).

---

## No Analog Found

Files with no close in-repo match (planner should use 04-RESEARCH.md examples directly):

| File | Role | Data Flow | Reason | RESEARCH section |
|------|------|-----------|--------|------------------|
| `src/sw.ts` | utility (worker) | event-driven | No existing service worker code; Phase 1 kill-switch SW lives in legacy `index.html` only | 04-RESEARCH.md §3 |
| `r2-cors.json` | config | n/a | CF-specific JSON format; no analog in repo | 04-RESEARCH.md §4 |
| `src/pages/search.astro` Pagefind UI block | component | request-response | No prior search UI in Astro form; `/search.html` is Lunr legacy | 04-RESEARCH.md §2 |
| `.github/workflows/r2-sync.yml` | config (CI) | event-driven | Closest is quality-gates.yml but rclone+R2 sync is novel | 04-RESEARCH.md §5 |
| `tests/sw.spec.ts` SW DevTools assertions | test | event-driven | No prior SW lifecycle tests in Playwright | 04-RESEARCH.md §11 |
| `tests/r2-urls.spec.ts` cross-origin HEAD check | test | request-response | `verify-redirects.sh` is closest (curl-based path 200 check) but R2 needs HEAD 200 + CORS check | 04-RESEARCH.md §11 + §4 |
| `scripts/_archive_common.py` shared helper | utility | transform | New shared module; `normalize-csv.py` _slugify+_e are inline copies that this module will consolidate | 04-RESEARCH.md §4 + §8 |

---

## Per-Plan Pattern Summary (one-line per plan)

| Plan | Primary Analog(s) | Concrete Files Touched |
|------|-------------------|------------------------|
| 04-01-lightbox-fix | `src/components/Card.astro` + `scripts/normalize-csv.py` + `src/scripts/invariants.ts` (all 3 patched in same commit) | Card.astro, normalize-csv.py render_card_html(), invariants.ts openAt() + click delegate, tests/lightbox.spec.ts NEW |
| 04-02-r2-setup | `.github/workflows/quality-gates.yml` (workflow shape only) | r2-cors.json NEW, .github/workflows/r2-sync.yml NEW, scripts/_archive_common.py NEW, tests/r2-urls.spec.ts NEW |
| 04-03-sw-injectmanifest | `astro.config.mjs` (Plan 03-01) + `src/layouts/BaseHead.astro` (Plan 03-04) | astro.config.mjs PATCH (AstroPWA integration), src/sw.ts NEW, BaseHead.astro PATCH (fonts), tests/sw.spec.ts NEW |
| 04-04-wargov-repaging | `src/pages/index.astro` (Plan 03-05) | index.astro PATCH (replace IO block with `?page=N` windowing per RESEARCH §6), tests/pagination.spec.ts NEW |
| 04-NN-<slug> ×14 (waves) | `src/pages/index.astro` + `scripts/normalize-csv.py` + `src/styles/wargov.css` | src/pages/<slug>/index.astro NEW, scripts/normalize-<slug>.py NEW (catalog shape), src/styles/<slug>.css NEW (optional), DELETE scripts/build-<slug>.py + <slug>/index.html, drop slug from copy-legacy-archives.sh |
| 04-NN-<first-port> only | `src/components/Card.astro` (Plan 03-05) | src/components/CatalogCard.astro NEW (catalog asset shape; reused by remaining 13 plans) |
| 04-NN-pagefind | `src/pages/index.astro` + `src/layouts/RootLayout.astro` (RootLayout edit + new search page) | src/pages/search.astro NEW, src/layouts/RootLayout.astro PATCH (data-pagefind-body on main), scripts/copy-legacy-archives.sh PATCH (append pagefind step), tests/search.spec.ts NEW, DELETE api/all.json + search.html legacy |
| 04-NN-close | `.lighthouserc.cf.json` (Phase 2 02-08 toggle), Phase 4 D-40 | .lighthouserc.cf.json warn→error flip, DELETE scripts/copy-legacy-archives.sh + sync-nav.py + sync-footer.py + nav-sync.yml + footer-sync.yml (if exist) |

---

## Metadata

**Analog search scope:** `src/`, `scripts/`, `.github/workflows/`, `data/`, `tests/`, `astro.config.mjs`, `package.json`, `src/content.config.ts`, sample `aaro/index.html` + `nasa/index.html`
**Files scanned:** 18 analog files Read in full or in targeted ranges
**Pattern extraction date:** 2026-05-27
**Notes:**
- Plan 03-05 wargov is the dominant analog — referenced by 16 of 19 Phase 4 plans
- Phase 4 introduces zero new frameworks beyond `@vite-pwa/astro`, `@fontsource/*`, `pagefind`, `workbox-*`, `rclone` (CI-side)
- 7 of ~45 new files have no in-repo analog; all are documented in 04-RESEARCH.md §2-§5 with verbatim code skeletons
- The catalogEnvelopeSchema in `src/content.config.ts` (Plan 03-02) is the SHAPE CONTRACT for all 14 archive ports — Phase 4 normalizers just need to fill the `assets[]` array
