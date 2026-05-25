# realufo.org

## What This Is

An offline-first archive of every official government UAP source — currently 15 national archives
(war.gov, AARO, NASA, NARA, GEIPAN, UK, Brazil, Chile, Argentina, Canada, Italy, NZ, Peru, Spain,
Uruguay) served as static HTML on GitHub Pages with binary assets (PDFs, videos) hosted via
GitHub Releases. The site faithfully mirrors official sources verbatim with a declassified-archive
aesthetic, lightbox evidence browser, cross-archive search, and mobile-first responsive design.

## Core Value

Every official government UAP release is preserved and viewable offline-first, with content matching
the official source verbatim — durable, free, and resistant to source-site takedowns.

## Requirements

### Validated

<!-- Inferred from existing codebase + CLAUDE.md spec. Capabilities shipping today. -->

- ✓ **CAT-01**: 15 national archive pages live with per-archive tone colour and seal — existing
- ✓ **CAT-02**: Cross-archive search at `/search.html` — existing
- ✓ **CAT-03**: Lightbox with prev/next nav, swipe, arrow keys, image/video/PDF support — existing
- ✓ **MOBILE-01**: Mobile-first responsive baseline (360 px, 44 px touch targets) — existing
- ✓ **DIST-01**: GitHub Releases as binary CDN (`videos-v1`, `pdfs-v1` tags) — existing
- ✓ **SCRAPE-01**: Idempotent download scripts with Wayback fallback for blocked sources — existing
- ✓ **OFFLINE-01**: Service worker with network-first navigations, 2xx-only caching — existing (partial)
- ✓ **BUILD-01**: Build-time templating via `scripts/templates/` (nav, footer, head, archive, lightbox, i18n) — existing
- ✓ **CI-01**: Drift gates — HTML-validate, lighthouse, lychee, nav-footer sync workflows — existing
- ✓ **DATA-01**: `git ls-files`-based LOCAL badge detection (no 404 download buttons) — existing

### Active

<!-- Milestone scope: SSG migration + full CI automation + Cloudflare Pages hosting. -->

- [ ] **SSG-01**: Migrate codebase to a formal SSG (Astro / Eleventy / Hugo — researcher-decided)
- [ ] **SSG-02**: All 15 archives rebuilt on chosen SSG (big-bang cutover)
- [ ] **OFFLINE-02**: Service worker registered on ALL 15 archive subpages (currently only root utility pages)
- [ ] **OFFLINE-03**: Full-catalog offline cache — every HTML page + every thumbnail precached; PDFs/videos on-demand
- [ ] **SCRAPE-02**: Full CI automation — scrape sources → diff new files → upload to GitHub Releases → rebuild → deploy
- [ ] **SCRAPE-03**: Move scrape runner to Cloudflare Workers cron (mitigate Akamai/GH-IP blocks on gov sites)
- [ ] **HOST-01**: Migrate hosting from GitHub Pages to Cloudflare Pages
- [ ] **PERF-01**: Reduce per-page inline-JSON bundle weight (target ≤ 500 KB; geipan currently 3.3 MB)
- [ ] **FIX-01**: Fix broken `scripts/sync.sh:144` (`$ROOT/download.py` should be `scripts/download-war.gov.py`)
- [ ] **FIX-02**: Reconcile `CLAUDE.md §5.1` URL pattern (says `war-gov-ufo-release`; actual remote is `hectorchanht/gov-ufo-archive`)
- [ ] **FIX-03**: Add release-upload step to `.github/workflows/scrape.yml` (currently local-only)

### Out of Scope

<!-- Boundaries on this milestone. -->

- Adding new national archives (#16+, e.g. Australia, Russia, China) — future milestone after SSG stable
- i18n / translations — English-only for this milestone; `templates/i18n.py` exists but stays inactive
- Mandatory visual redesign — pixel-equivalent or modest evolution acceptable; major redesign is a future milestone
- User accounts, payments, native mobile app — outside the read-only archive mission

## Context

**Deployment:**
- Live site: <https://realufo.org>
- Source repo: <https://github.com/hectorchanht/gov-ufo-archive> (local folder name `war-gov-ufo-release` is historical)
- Binary assets: GitHub Releases on `hectorchanht/gov-ufo-archive` (`videos-v1`, `pdfs-v1`, etc.)

**Codebase state (brownfield, fully mapped):**
- 95 HTML files, 15 archive directories, 23+ Python build scripts, 15+ shell download scripts
- Plain HTML + inline CSS/JS today; runtime-isolated per-archive pages with build-time sharing via `scripts/templates/`
- Templates refactor in progress but partial — `build-aaro.py` still 1,360 lines
- 42% of last 88 commits are fixes — maintenance churn is the primary driver of this milestone
- See `.planning/codebase/` for full STACK / ARCHITECTURE / STRUCTURE / CONVENTIONS / TESTING / INTEGRATIONS / CONCERNS

**Stakeholder pain (from /gsd:new-project questioning, 2026-05-25):**
- 15-way drift between archives is constant work
- Bundle weight ceiling already hit on geipan (3.3 MB inline JSON)
- Service worker structurally broken — registered on root pages only, not on archive subpages
- New gov releases lag because scrape→release-upload pipeline is local-only

**Public-domain attribution** is per source jurisdiction (US 17 USC §105, France Loi 78-753, UK OGL v3,
Brazil LAI 12.527, Chile Ley 20.285, Argentina Ley 27.275, Italy D.lgs. 33/2013, Spain Ley 19/2013,
Uruguay Ley 18.381). Documented in `README.md` and `CLAUDE.md §9`.

**Considered but deferred to next milestone:**
- Social / community features (user-tagged interesting cards, comments, public collections) — user flagged
  these as "thinking about" during questioning. Defer until SSG migration is shipped and stable so we
  evaluate them with a maintainable codebase.

## Constraints

- **Tech stack — output format**: Must produce static HTML deployable to a CDN. SPAs that require JS to render content are rejected (breaks offline-first + JS-disabled archival).
- **Hosting**: Cloudflare Pages chosen (free unlimited bandwidth, Workers for scrape automation, R2 for blob overflow if needed).
- **Distribution — binaries**: GitHub Releases stays the binary CDN. Files > 100 MB cannot live in git (GitHub hard limit).
- **CLAUDE.md design system**: Treated as starting point; visual refresh permitted but per-archive tone colours + seals must remain recognizable. JS invariants from CLAUDE.md §7 (lightbox, hamburger, search restore from `?q=`) must survive migration.
- **Mobile-first**: 360 px baseline + 44 px touch targets stays non-negotiable (CLAUDE.md §8).
- **Content fidelity**: Verbatim official text. No filler descriptions. (CLAUDE.md §9, §11.)
- **Public-domain attribution**: Preserved per source jurisdiction.
- **Source CSV (`uap-release001.csv`)**: Untouchable — source of truth.
- **No force-push to main, ever** (CLAUDE.md §11).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Stay static + adopt formal SSG (not SPA framework) | Preserves offline-first + GitHub Pages friendliness + zero-JS archival viewing | — Pending |
| SSG choice deferred to research | Astro / Eleventy / Hugo each have different trade-offs for offline-first + 15-archive content collection model | — Pending |
| Big-bang migration (not strangler) | Maintenance churn is the pain — running two systems in parallel makes it worse | — Pending |
| Cloudflare Pages over Netlify / Vercel / GitHub Pages | Free unlimited bandwidth + Workers cron + R2 for blob overflow fits offline-first archive | — Pending |
| Cloudflare Workers cron for scrape | Different egress IPs than GH Actions runners — mitigates Akamai blocks on gov sources | — Pending |
| CI uploads to GitHub Releases (not R2 directly) | Keeps current download URL pattern + public-domain mirror durability | — Pending |
| Full-catalog offline (HTML + thumbnails) | Stronger than "visited only" — matches the archive's offline-first promise even on first visit | — Pending |
| Cutover strategy deferred to plan-phase | Branch+preview vs side-by-side vs hot-swap is implementation detail | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-25 after initialization*
