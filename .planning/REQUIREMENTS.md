# Requirements: realufo.org — SSG Migration Milestone

**Defined:** 2026-05-25
**Core Value:** Every official government UAP release is preserved and viewable offline-first, with content matching the official source verbatim — durable, free, resistant to source-site takedowns.

## v1 Requirements

Requirements for this milestone. Each maps to a roadmap phase.

### Pre-Migration Safety (PMS)

- [ ] **PMS-01**: `URL-CONTRACT.txt` snapshot of all current routes/anchors generated from `main` before any SSG code lands (CI gate against drift)
- [ ] **PMS-02**: SW kill-switch deployed to current GH Pages origin at least 14 days before cutover (deregisters old SW so users don't serve stale shells)
- [ ] **PMS-03**: 1-day Akamai egress spike — compare Cloudflare Workers vs GitHub Actions runners against war.gov / aaro.mil; outcome decides Phase 5 scrape architecture
- [ ] **PMS-04**: DNS TTL on `realufo.org` dropped to 300 s prior to cutover window
- [ ] **PMS-05**: Fix `scripts/sync.sh:144` (broken `$ROOT/download.py` path → `scripts/download-war.gov.py`)
- [ ] **PMS-06**: Reconcile `CLAUDE.md §5.1` URL pattern with actual remote `hectorchanht/gov-ufo-archive` (currently says `war-gov-ufo-release`)

### Infrastructure & CI Scaffolding (INF)

- [ ] **INF-01**: Cloudflare Pages project created, connected to repo, building from a long-running `ssg-migration` branch
- [ ] **INF-02**: `_headers` + `_redirects` files scaffolded with CSP, HSTS, MIME types, explicit 301 redirects (CF Pages default is 302)
- [ ] **INF-03**: Cloudflare Workers Paid plan activated ($5/mo — Free is unusable: 10 ms CPU cap)
- [ ] **INF-04**: Playwright visual-regression suite — baselines captured against current `main` for all 15 archives × 4 viewports (360/768/1024/1440)
- [ ] **INF-05**: `verify-fidelity.py` CI gate — byte-equivalent check on a sample of verbatim text (hero ledes, FAQ answers, license footers, official titles)
- [ ] **INF-06**: Tone-colour smoke test — CI reads each archive's `--caution` CSS variable and asserts it matches `CLAUDE.md §3.1` table
- [ ] **INF-07**: JS-off rendering test — each archive page renders meaningful content with JS disabled (proves pre-render works)
- [ ] **INF-08**: Lighthouse mobile + 4× CPU throttle budgets (LCP ≤ 2.5 s, total transfer ≤ 500 KB per page)

### SSG Foundation (SSG)

- [ ] **SSG-01**: Astro 5.x scaffold (`~5.x.y` pin, NOT `^5`) installed alongside existing Python build scripts; both build trees coexist during migration
- [ ] **SSG-02**: Content Collections defined — one collection per archive, `file()` loader reading from `data/<slug>.json` (committed; normalized from current CSV/scraped sources)
- [ ] **SSG-03**: Shared layout (`RootLayout.astro`, `BaseHead.astro`, `Nav.astro`, `Footer.astro`) — replaces `sync-nav.py`/`sync-footer.py` and their CI drift gates
- [ ] **SSG-04**: Pre-rendered cards (no client hydration of card data) — Astro template emits HTML; runtime JS is progressive enhancement only (lightbox, filter, sort) reading `data-*` attributes
- [ ] **SSG-05**: First archive (wargov — smallest stable surface) fully ported, passing all INF gates
- [ ] **SSG-06**: Remaining 14 archives (AARO, NASA, NARA, GEIPAN, UK, Brazil, Chile, Argentina, Canada, Italy, NZ, Peru, Spain, Uruguay) ported, all passing visual-regression + fidelity
- [ ] **SSG-07**: Bundle weight target — every archive page ≤ 500 KB HTML+inline (currently GEIPAN 3.3 MB, UK 512 KB, root 479 KB)
- [ ] **SSG-08**: Mobile-first invariants preserved — 360 px baseline, 44 px touch targets, no horizontal scroll (CLAUDE.md §8)
- [ ] **SSG-09**: JS invariants from `CLAUDE.md §7` preserved — hamburger toggle, lightbox prev/next + arrow keys + swipe, image/video/PDF fallback, `/` keydown focuses search, `?q=` persists
- [ ] **SSG-10**: All Python build scripts deleted (`build-*.py`, `sync-nav.py`, `sync-footer.py`, `parse-aaro.py`, `extract-evidence.py`, `spider.py`) — replaced by SSG
- [ ] **SSG-11**: Public-domain license footnotes preserved verbatim per source jurisdiction (CLAUDE.md §9)
- [ ] **SSG-12**: Per-archive seal + tone-colour design system preserved (CLAUDE.md §3.1 table is the spec)

### Search (SRC)

- [ ] **SRC-01**: Pagefind 1.x integrated; builds at the end of Astro build; outputs sharded WASM index to `dist/pagefind/`
- [ ] **SRC-02**: Cross-archive search at `/search.html` migrated from Lunr to Pagefind (drops the 4.6 MB `api/all.json` blob)
- [ ] **SRC-03**: Per-archive filter UI preserved — operates on already-rendered DOM via `data-*` attributes, no re-fetch
- [ ] **SRC-04**: Search result links use stable `#card-<id>` anchors (per-document permalink — Features.md P1)
- [ ] **SRC-05**: SW precaches Pagefind core; chunk shards lazy-fetched on use

### Service Worker & Offline (SW)

- [ ] **SW-01**: `@vite-pwa/astro` `injectManifest` strategy wired; preserves bespoke 2xx-only nav-caching logic from commit `dcbc0d7`
- [ ] **SW-02**: SW registered structurally from `BaseHead.astro` — every page inherits registration, eliminates the 12-of-32-pages gap from CONCERNS.md
- [ ] **SW-03**: Full-catalog offline cache — all HTML pages + all card thumbnails precached
- [ ] **SW-04**: PDFs / videos NOT in SW precache (still on-demand from GitHub Releases / R2; size-prohibitive)
- [ ] **SW-05**: Tiered cache strategies — network-first for HTML nav, stale-while-revalidate for JSON, cache-first for images/fonts, no-cache for `/admin*` and dev-only paths
- [ ] **SW-06**: Cache-name versioning (`realufo-v<sha>`) — old caches purged on new SW activation; `updateViaCache: 'none'` on all registrations
- [ ] **SW-07**: Self-hosted fonts via `@fontsource/source-serif-4` + `@fontsource/jetbrains-mono` (current Google Fonts setup breaks offline-first)

### Hosting & Cutover (HOST)

- [ ] **HOST-01**: Cloudflare Pages preview deploy on `ssg-migration` branch stable for ≥ 7 days
- [ ] **HOST-02**: Optional `preview.realufo.org` custom-domain alias for 1–2 weeks of public staging
- [ ] **HOST-03**: DNS cutover — `realufo.org` swapped from GitHub Pages to Cloudflare Pages
- [ ] **HOST-04**: Post-cutover monitoring window — 7 days of Umami traffic + Lighthouse + SW-error tracking, all stable
- [ ] **HOST-05**: GitHub Pages deployment workflow archived (kept in git history; not deleted)
- [ ] **HOST-06**: `CLAUDE.md` updated — design-system status, build process, hosting source-of-truth all post-migration

### Scrape Automation (SCRP)

- [ ] **SCRP-01**: Cloudflare Worker cron skeleton — invokes per-source scrape lanes; KV stores per-source fingerprints (last-seen ETag + content-hash)
- [ ] **SCRP-02**: Hybrid Akamai-fronted source strategy — sources blocked from Workers IP (per PMS-03 spike result) fall through to a GitHub Actions runner with `curl_cffi`; others stay on Workers
- [ ] **SCRP-03**: R2 staging bucket for in-flight scraped binaries before promotion to GitHub Releases
- [ ] **SCRP-04**: `repository_dispatch` payload from Worker → GitHub Action triggers ingest pipeline (normalize JSON, commit manifest deltas)
- [ ] **SCRP-05**: `release-upload.py` helper with SHA idempotency + delete-then-upload + retry; serialized to avoid `gh release upload --clobber` race
- [ ] **SCRP-06**: Per-archive release tags from day one (e.g. `wargov-pdfs-2026q2`); avoid the 1000-asset ceiling on shared `pdfs-v1`/`videos-v1`
- [ ] **SCRP-07**: Cron-lock in KV — prevents overlapping cron invocations from racing
- [ ] **SCRP-08**: Remove all `|| true` from `curl_cffi` install steps in scrape CI (current pattern silently swallows install failures)
- [ ] **SCRP-09**: Manual trigger path — `gh workflow run scrape.yml` still works for ad-hoc/back-fill use
- [ ] **SCRP-10**: R2 overflow for any single asset > 2 GB (GitHub Releases per-asset ceiling); URL-rewrite layer makes physical storage transparent to SSG

### Performance & Quality Gates (PERF)

- [ ] **PERF-01**: GEIPAN page LCP ≤ 2.5 s on mobile + 4× CPU throttle (currently 3.3 MB inline JSON)
- [ ] **PERF-02**: Inline-JSON refactor uses ≤ 3 chunks per page (not naive atomization → request waterfall)
- [ ] **PERF-03**: First paint contains useful card content (cards pre-rendered, not hydrated)
- [ ] **PERF-04**: No regression in current Lighthouse scores at the smaller archives (NZ, Uruguay, Peru baselines)

## v2 Requirements

Deferred to next milestone (after SSG cutover is stable for ≥ 30 days).

### Social / Curation (SOCL)

- **SOCL-01**: Anonymous "interesting" tags on cards (no ranking, no engagement metrics)
- **SOCL-02**: Comments on case-detail prose pages only (NOT on raw documents — preserves verbatim archive ethos)
- **SOCL-03**: Named-curator collections (manually edited, not crowdsourced)
- **SOCL-04**: Write-path infra — Workers + KV/D1; this milestone *sets up* CF Workers but does NOT consume it for social writes
- **SOCL-05**: Governance design — written before any social-feature code lands

### Federation & Discovery (FED)

- **FED-01**: JSON-LD per page (`Dataset` / `Article` / `CreativeWork` mapping per record type)
- **FED-02**: RSS/Atom feed of new releases per archive (subscribe to mirror activity)
- **FED-03**: Bulk-download ZIP per archive (build-time artifact vs gh-auto-zip — design subquestion)
- **FED-04**: Wayback "as captured" link recorded at scrape-time (no Save-Page-Now API write-cost)

### OCR & Accessibility (A11Y)

- **A11Y-01**: Scanned PDFs OCR'd (separate workstream; HIGH cost, HIGH value but orthogonal to SSG)
- **A11Y-02**: Screen-reader patterns for image evidence
- **A11Y-03**: Transcription for video evidence

## Out of Scope

Explicitly excluded — documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Adding archive #16+ (Australia / Russia / China / etc.) | Future milestone after SSG is stable; current 15 only |
| i18n / translation | English only this milestone; `templates/i18n.py` stays inactive; pure-i18n is a future milestone |
| Mandatory visual redesign | Pixel-equivalent or modest evolution acceptable; major redesign deferred |
| User accounts, login, profiles | Outside read-only archive mission |
| Engagement metrics, infinite scroll, AI summaries, push notifications | Anti-features — preserve verbatim / neutral archive ethos |
| Comments on raw documents | Erodes verbatim contract; restrict comments (if added later) to case-detail prose only |
| Hosting on Vercel / Netlify / self-host | Cloudflare Pages chosen; revisit only if CF Pages bandwidth/limits become a problem |
| SPA framework (Next.js / Remix / SvelteKit / Gatsby) | Hydration-required SPAs break offline-first + zero-JS archival viewing |

## Traceability

Empty initially. Populated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PMS-01 → PMS-06 | Phase 1 | Pending |
| INF-01 → INF-08 | Phase 2 | Pending |
| SSG-01 → SSG-05 | Phase 3 | Pending |
| SSG-06 → SSG-12, SRC-*, SW-*, PERF-* | Phase 4 | Pending |
| SCRP-* | Phase 5 | Pending |
| HOST-* | Phase 6 | Pending |

**Coverage (tentative):**
- v1 requirements: 56 total
- Mapped to phases: 56 (provisional — roadmapper will refine)
- Unmapped: 0

---
*Requirements defined: 2026-05-25*
*Last updated: 2026-05-25 after initialization*
