# Feature Research

**Domain:** Offline-first government-document archive (UAP / declassified records)
**Researched:** 2026-05-25
**Confidence:** MEDIUM-HIGH (HIGH for table stakes & anti-features grounded in named peer archives; MEDIUM for offline-UX patterns and federation, which are partly synthesized from PWA best-practice + archival-science sources)

## Context: What This Research Is For

This feeds the SSG-migration milestone for realufo.org. The site already
ships most of the "credible archive" feature set — the question is which
features must be **preserved** through the migration, which are
**low-cost wins** worth picking up while the build pipeline is being
rewritten, and which the user has flagged as future (social/curation
features in a follow-up milestone). Findings are framed against the
existing capability surface in `.planning/codebase/ARCHITECTURE.md` so the
roadmap doesn't waste cycles re-researching things the codebase already
does well (lightbox, swipe, lunr search, atom feeds, leaflet map,
service worker, OG cards, dead-link sweep, drift gates).

## Reference Archives Surveyed

The feature taxonomy below is anchored to named peers. Confidence in each
recommendation reflects how many of these actually ship the feature.

| Archive | URL | What they're known for |
|---------|-----|------------------------|
| **CIA Electronic Reading Room** | cia.gov/readingroom | Full-text + advanced metadata search, OCR caveat noted to user, FOIA category collections |
| **FBI Vault** | vault.fbi.gov | ~7,000 docs, open-source web document viewer, in-page search, category browse |
| **NSA FOIA Reading Room** | nsa.gov/Helpful-Links/NSA-FOIA/Reading-Room | Topic-grouped index, request-status integration |
| **DIA FOIA Reading Room** | dia.mil/FOIA/FOIA-Electronic-Reading-Room | Plain index, very minimal UX |
| **NARA Electronic Reading Room** | archives.gov/foia/electronic-reading-room | Federated FOIA library, links into Catalog (OPA) |
| **National Security Archive (GWU)** | nsarchive.gwu.edu | Curated chronologies, "briefing books," cited-source links, virtual reading room |
| **Internet Archive (archive.org)** | archive.org | IIIF API, OAI-PMH, item-level permalinks, "save page now" |
| **Wayback Machine** | web.archive.org | Timestamped permalinks, calendar timeline, "as of" snapshots |
| **The Black Vault** | theblackvault.com/documentarchive | Searchable PDFs across text/title/agency/location/filename, downloadable ZIPs per release, OCR processing transparency |
| **NICAP / CUFOS** | nicap.org | Chronological case database, ~6,000 cases, category facets (radar / EM / formation) |
| **MUFON Project Aquarius / UFO Map** | projectaquarius.mufon.com | Map-first browse, NICAP chronology overlay |
| **Imperial War Museum Collections** | iwm.org.uk/collections | 1M+ object search, faceted, citation export to RefWorks/EasyBib |
| **UK National Archives Discovery** | discovery.nationalarchives.gov.uk | 37M+ records, tags (50K tags / 90K records), RSS feeds per category |
| **arXiv** | arxiv.org | Per-category RSS/Atom feeds, daily cadence, structured metadata |

## Feature Landscape

### Table Stakes (Users Expect These for Archive Credibility)

| Feature | Why Expected | Complexity (for *this* codebase) | Notes / Already Have It? |
|---------|--------------|----------------------------------|--------------------------|
| **Full-text search across all documents** | Every peer archive offers it. Single most-cited reason users come to declassified archives. | MEDIUM | **Partial** — site has lunr-powered `/search.html` over manifests + `api/pages-index.json` for case-page prose. PDFs themselves are NOT OCR-indexed. Closes the gap below Black Vault, CIA. |
| **Faceted filters (agency / category / date / status / region)** | NARA, IWM, NSA all expose them. Standard archive UX pattern. | LOW | **Have it** per-archive (`ARCHIVE_JS` filter bar). Preserve through migration. |
| **URL-shareable search state (`?q=`)** | "If a user shares a link, the contents must reflect filters." Universal UX expectation. | LOW | **Partial** — `?q=` persists on cross-archive search. Per-archive pages don't push filter state to URL. Pickup-worthy during migration. |
| **Boolean / phrase operators in search** | CIA, Black Vault both expose AND / OR / NOT and quoted phrases. Power-user table stakes. | LOW | **Missing** — lunr supports field queries natively (`title:foo +agency:nasa`). Just needs UI documentation / a `?` help affordance. |
| **Per-document permalink (deep-linkable card)** | Every credible archive has stable item URLs. Citation depends on it. | MEDIUM | **Partial** — lightbox opens via `?lb=<id>` not currently supported. Cards have no hash anchor. Citation use-case suffers. |
| **"Source ↗" link to official agency page** | Provenance signal. Establishes the archive is not the primary source. | LOW | **Have it** — `Source ↗` button on every card. CLAUDE.md §4.3 codifies it. |
| **Public-domain attribution per source jurisdiction** | Legal requirement (17 USC §105, OGL v3, etc.). Distinguishes "archive" from "scraping". | LOW | **Have it** — CLAUDE.md §9 catalogs 9 jurisdictions; footer shows it. Preserve verbatim. |
| **Last-updated / "as of" date stamp** | Web-archive convention since WebCite (2005). Tells researcher the snapshot is durable. | LOW | **Missing** — sw.js carries a version SHA, but no user-visible "Archive captured: 2026-05-21" stamp. Pickup-worthy. |
| **Download original file (not re-encoded)** | Researchers must cite the *original* binary. Re-encoding breaks hash provenance. | LOW | **Have it** — Download button hits GH-release URL, file untouched. |
| **Open in new tab / no-frames lightbox for large media** | Users print, save-as, screenshot. Iframe sandboxing breaks these flows. | LOW | **Have it** — release-URL PDFs open in new tab via `Content-Disposition: attachment`. CLAUDE.md §7. |
| **Mobile-first responsive (≥360 px, 44 px touch)** | 2026 baseline. >55% archive traffic mobile. | LOW | **Have it** — CLAUDE.md §8 is non-negotiable. |
| **Service-worker offline shell** | "Offline-first" is in the site's tagline. PWA baseline. | LOW | **Partial** — sw.js exists; registered only on root utility pages, NOT on 15 archive subpages. Headline gap. |
| **Atom / RSS feed of new releases** | UK National Archives, arXiv, NSA all offer it. Standard subscription mechanism. | LOW | **Have it** — `scripts/build-feeds.py` emits `feeds/<slug>.xml` + `feeds/all.xml`. Preserve. |
| **Accessible scanned PDFs (text layer present)** | WCAG 2.1, Section 508. Without OCR, screen-readers announce "image, image, image". | HIGH | **Partial/inherited** — depends on whether agency-of-origin already OCRed. CIA Reading Room explicitly warns user. Match that disclosure pattern; don't promise more than upstream delivers. |
| **No login required** | Government records are public. Login = friction + privacy risk. | — | **Have it** — site has zero auth surface. Preserve. |
| **No paywall, no ads** | Same. | — | **Have it.** |
| **Visible "official source" hierarchy** | Footer differentiates "Source" (official URLs) from internal nav. CLAUDE.md §4.1. | LOW | **Have it.** Preserve. |
| **HTTPS + CSP** | Trust signal for gov-document mirror. | LOW | **Have it** — CSP in `index.html`, HTTPS via GitHub Pages. |

### Differentiators (Raises This Above Other UFO Archives)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Multi-jurisdiction coverage (15 archives, one UI)** | Black Vault is US-only. NICAP is US-only. No other public site cross-indexes 15 national archives in one search. | — | **Have it.** This IS the differentiator. Preserve relentlessly through migration. |
| **Per-archive tone colour + seal aesthetic** | Distinguishes from "data dump" feel of CIA reading room. Honors source institutional identity. | LOW | **Have it** (CLAUDE.md §3.1). Cannot be lost in SSG migration. |
| **LOCAL badge — durable mirror promise** | Users can see at-a-glance which records survive source-site takedowns. Unique signal. | LOW | **Have it** — `git ls-files`-based detection. Preserve. |
| **Wayback fallback baked into download path** | Bellingcat-style archival-investigator UX. Robust even when source site dies. | LOW-MEDIUM | **Have it** in download scripts; lightbox has image/video onerror fallback. Make it visible in UI ("via Wayback" badge when triggered) → small win. |
| **Geographic map of cases (`/map.html`)** | Black Vault doesn't have this. NICAP map exists but is cluttered. Leaflet-driven, lightweight. | — | **Have it.** Preserve. |
| **Timeline / chronology of releases** | National Security Archive's flagship UX pattern. | — | **Have it** (`timeline.html`). Preserve. |
| **"What's New" page** | Lets returning users see what changed since last visit. Companion to RSS. | — | **Have it** (`whatsnew.html`). Preserve. |
| **Item-level permalink with hash anchor (`#card-<id>`)** | Citation use-case: "see card #aaro-veracruz-2004 at realufo.org". | LOW | **Pickup-worthy during migration** — SSG content collections make per-item routes natural. |
| **JSON-LD `Dataset` / `Article` per page** | schema.org / DCAT-US discoverability. Powers Google rich-results + makes archive harvestable. | LOW | **Pickup-worthy** — emit during SSG build, almost free. Aligns with data.gov metadata convention. |
| **OAI-PMH endpoint** | Archive-It uses it; lets libraries / academic harvesters pull records. Differentiator vs Black Vault. | MEDIUM | Consider for v1.x. Static-friendly: a single `oai.xml` covering Dublin-Core records is achievable. |
| **Public flat JSON API (`api/all.json` etc.)** | Already partly built. Lets researchers, OSINT tools, Bellingcat etc. consume. Differentiator vs every other UFO archive. | — | **Have it** — `scripts/build-api.py`. Document it; add a small `/api/` index page. |
| **Per-record "cite this" widget (BibTeX / RIS / Chicago / APA)** | IWM offers RefWorks/EasyBib. Academic researchers WILL use this. Differentiator vs every UFO archive. | LOW | `assets/vendor/citation.js` already exists per ARCHITECTURE.md — wire it into card actions. Big credibility win. |
| **"View official source as captured" — link to Wayback snapshot of the source page on the day we ingested** | Chain-of-custody proof. WebCite-style permanence layered on top of the source link. | MEDIUM | Differentiator. Requires recording a Wayback timestamp at ingest. |
| **Bulk download (per-archive ZIP)** | Black Vault offers this for Release #1. Researchers want everything-at-once. | MEDIUM | Pickup-worthy — `gh release` already hosts the binaries; just need a "Download all (ZIP)" affordance that points at the release tag's auto-zip. |
| **OG social cards per archive + per case** | Every shared link looks intentional. | — | **Have it** — `scripts/build-og.py`. Preserve. |
| **Cross-archive sort by date** | Lets user see "all UFO sightings 1947–1980 across countries" — unique. | LOW-MEDIUM | Adjacent to current search; date facet on `/search.html` would do it. |
| **Multi-language i18n scaffolding** | Already 6-language dict baked in. Differentiator vs every English-only archive. | — | **Have scaffold, inactive.** Out-of-scope for SSG milestone per PROJECT.md. |
| **Curated case detail pages with prose context** | National Security Archive's "briefing book" model. Distinguishes from dump-of-PDFs. | — | **Have it** — case-detail and story HTML pages. Preserve. |

### Anti-Features (Commonly Requested, But Wrong for This Archive)

Each row below explicitly anchors to the archive's stated ethos
(CLAUDE.md "no filler", "verbatim official text", "no engagement metrics
beyond Umami") so the SSG migration doesn't accidentally adopt patterns
from generic CMS/media-site templates.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **User accounts / login** | "Personalization, saved searches, history" | Public-domain content has no privacy story for accounts. PII liability. Killing-feature of credibility — archive becomes "yet another platform". | URL-shareable filter state + browser bookmarks + RSS for "saved search". |
| **Comments under documents** | "Discussion / community" | Moderation cost. Conspiracy-spam vector. Mixes user voice with primary-source archive. Defeats "verbatim" principle. | Link to off-site discussion (subreddit, mailing list) in About page if community is wanted. |
| **Engagement metrics on cards ("👁 12K views")** | "Show what's popular" | Steers researcher attention toward viral content vs investigative content (osc.ca dark-patterns research). Anti-neutrality. | If popularity is shown anywhere, do it as a quiet `/stats.html` page, not on cards. (Site already has `stats.html`.) |
| **Algorithmic "recommended next" carousel** | "Discovery" | Black-box ranking is the opposite of "every official source preserved". Becomes a recommender, not an archive. | Curated case-detail "see also" links, hand-authored. Already the pattern. |
| **Infinite scroll** | "More content faster" | Loses pagination state. Breaks back-button. Catastrophic for citation use-case (you can't link to "item #173"). Bad on mobile data. | Numbered pagination + per-page selector (already in `ARCHIVE_JS`). Preserve. |
| **Newsletter signup popup / modal** | "Audience capture" | Dark pattern. Site has no newsletter to send. RSS does this without an email funnel. | The existing RSS/Atom feeds. |
| **In-app PDF annotation / highlight** | "Active research tool" | Researcher use this in Zotero / Mendeley / Acrobat, not in a mirror. Would require accounts (anti-feature #1). | Download original; annotate locally. Provide good citation export instead. |
| **Inline streaming of large videos / autoplay** | "Engaging hero" | Breaks offline-first (cloudfront-served). Bandwidth cost. Autoplay is a dark pattern. | Hero carousel of imagery (current pattern). Click → lightbox → user-initiated play. CLAUDE.md §11 already forbids `crossorigin="anonymous"` on `<video>`. |
| **Push notifications for new releases** | "Re-engagement" | Permission prompt is widely classified as a dark pattern when used for marketing. Government archive has nothing time-sensitive enough to push. | RSS/Atom + an opt-in email (mailto) subscribe link. |
| **Editorial commentary / "what we think this means"** | "Make it readable" | Compromises the "verbatim official text" principle (CLAUDE.md §9). | Stick to verbatim. Curated case pages can stay context-only ("released by X on Y"). |
| **AI summaries on document cards** | "TLDR every record" | Hallucination risk on documents users may cite legally / journalistically. Anti-fidelity. Generates filler ("Click to play"-equivalent). | Show verbatim title + verbatim agency description. Omit if no real context exists (CLAUDE.md §9). |
| **Open-graph "view count" badge** | "Social proof" | Same as engagement metrics — biases discovery, contradicts archive ethos. | None. |
| **Mandatory cookie banner** | "Compliance" | If you don't set non-essential cookies, you don't need it. Umami runs without cookies. | Umami already configured cookieless. No banner needed. |
| **Dark-pattern download gating (email-for-PDF)** | "Lead gen" | Public-domain content. Gating is illegitimate AND breaks offline-first. | Direct download, always. |

### v2 Candidates (User Flagged — Defer to Next Milestone)

User stated during questioning: "thinking to add social features." These
are explicitly deferred until SSG migration ships per PROJECT.md "Considered
but deferred." Categorized here so the requirements doc has a clean
parking-lot. Note the strong tension with the anti-feature list — these
must be designed carefully or they collapse into the patterns the
archive is built to avoid.

| Feature | Rationale | Tension to Resolve | Complexity |
|---------|-----------|---------------------|------------|
| **User-tagged "interesting" cards (anonymous, no account)** | Surfaces community-curated highlights without engagement-metric dark patterns | Must NOT become a popularity ranking. Tag stays an opt-in research label, not a sort key by default. | MEDIUM (needs backend — kvstore / Workers + R2) |
| **Public collections / "playlists" of cards** | Curators (journalists, researchers) build narrative paths through the archive. National Security Archive's "briefing books" pattern. | Risk of editorial drift from verbatim ethos. Mitigate: collections are curated by named human curators, not crowdsourced. | MEDIUM-HIGH |
| **Moderated comments on case-detail pages only (NOT on raw documents)** | Lets discussion happen on the curated prose pages where editorial framing is already permitted. Documents themselves stay clean. | Moderation cost. Spam vector. Mitigate: invite-only or GitHub-issues-as-comments (utterances/giscus). | HIGH |
| **User-submitted transcription corrections (Wikisource-style)** | Wikisource's ProofreadPage extension successfully crowdsources OCR fixes at scale. Could fix the "scanned PDFs not screen-readable" gap. | Verification burden. Mitigate: corrections live in a separate `transcripts/` corpus, never overwrite primary record. | HIGH |
| **Email digest of new releases** | RSS is power-user-only. Email-subscribe widens audience. | Privacy story for email list. Mitigate: use a one-way Buttondown / Listmonk; opt-in only; no analytics. | MEDIUM |
| **Per-card "save to local" with progress** | True offline-first: user pre-downloads a curated subset (e.g., "everything tagged Brazil"). | UX complexity; quota management (browser cache caps). | MEDIUM-HIGH |

## Feature Dependencies

```text
Per-document permalink (#card-<id>)
    └──enables──> Per-record "Cite this" widget
    └──enables──> Public collections (v2)
    └──enables──> JSON-LD per-page
    └──enables──> Wayback "as captured" link

Service worker on all 15 archives
    └──enables──> Full-catalog offline cache
    └──enables──> Per-card "save to local" (v2)
    └──enables──> Offline indicator widget

PDF text-layer (OCR)
    └──enables──> Full-text search inside PDFs (vs only metadata search)
    └──enables──> Screen-reader accessibility
    └──enables──> User-submitted transcription corrections (v2)

JSON-LD per page
    └──enables──> OAI-PMH endpoint
    └──enables──> Google rich-results
    └──enables──> Federation by third-party harvesters

Engagement metrics ──conflicts──> Verbatim / neutral archive ethos
Comments on raw docs ──conflicts──> Verbatim / neutral archive ethos
Algorithmic ranking ──conflicts──> Multi-jurisdiction faithful-mirror promise
```

### Dependency Notes

- **Permalink (`#card-<id>`) is the keystone** — citation widgets, public
  collections, JSON-LD, and the "Wayback as captured" link all assume
  every record has a stable, human-shareable URL. Worth doing in the SSG
  milestone even though the user didn't list it explicitly.
- **Service worker on all 15 archives is a blocker for the offline-first
  story.** PROJECT.md already lists this as OFFLINE-02. Without it,
  "offline-first" is aspirational not actual.
- **OCR / text-layer is gated by what agencies deliver.** CIA's reading
  room warns users that OCR quality varies; Black Vault transparently
  notes the same. Match that disclosure pattern. Don't promise universal
  full-text PDF search unless we're willing to run our own OCR pipeline
  (out of scope for SSG milestone).
- **v2 social features all share one upstream dep**: a write-path
  (Cloudflare Workers + KV or D1). The SSG milestone already migrates
  hosting to Cloudflare Pages, which sets up the runtime for these v2
  features cheaply.

## MVP Definition

### Launch With (SSG Migration — This Milestone)

Preserve all existing capabilities + pick up the small set of cheap wins
the migration unlocks.

- [ ] **Preserve all current table stakes** — per-archive page, lightbox,
      cross-archive search, atom feeds, map, timeline, what's-new, OG
      cards, dead-link sweep, drift gates. Non-negotiable.
- [ ] **Service worker registered on ALL 15 archive subpages** —
      PROJECT.md OFFLINE-02. Closes the headline offline-first gap.
- [ ] **Full-catalog offline cache** (HTML + thumbnails precached;
      PDFs / videos on-demand) — PROJECT.md OFFLINE-03.
- [ ] **Per-archive bundle weight ≤ 500 KB** — PROJECT.md PERF-01. SSG
      content collections + lazy-loaded JSON shards address geipan's
      3.3 MB.
- [ ] **Per-document permalink** (`#card-<id>` URL fragment that opens
      the lightbox) — keystone feature, cheap to add in SSG.
- [ ] **URL-shareable filter state on per-archive pages** — bring all
      pages up to `search.html`'s `?q=` pattern.
- [ ] **JSON-LD `Dataset` / `Article` block per page** — almost-free
      during SSG render; major discoverability win.
- [ ] **Visible "Archive captured" date stamp in footer** — researcher
      provenance signal. Reuses the SW VERSION SHA.

### Add After Validation (v1.x — Same Codebase, Subsequent PRs)

- [ ] **Per-record citation export (BibTeX / RIS / Chicago / APA)** —
      `citation.js` vendor file already in tree.
- [ ] **Bulk download (per-archive ZIP)** — link to GH-release tag's
      auto-ZIP; no infra work.
- [ ] **"View source as captured" Wayback timestamp button** —
      requires ingest-time Wayback API call.
- [ ] **Cross-archive date facet on `/search.html`** — unlocks "all
      sightings 1947–1980 across countries" use-case.
- [ ] **Lightbox boolean/phrase search help affordance** — surface
      lunr's existing query syntax.
- [ ] **Public `/api/` documentation page** — make `api/all.json` and
      friends discoverable, not just enumerated in feeds.

### Future Consideration (v2 — Subsequent Milestone, User-Flagged)

- [ ] **User-tagged "interesting" cards (anonymous)** — requires write
      path on Cloudflare Workers.
- [ ] **Public collections / curator briefing-books** — design carefully
      to avoid editorial drift.
- [ ] **OAI-PMH endpoint** — federation with libraries / harvesters.
- [ ] **Email digest** — broadens beyond RSS power-users.
- [ ] **Wikisource-style OCR correction crowdsource** — closes the
      accessibility gap on poorly-scanned PDFs.
- [ ] **GitHub-issues-as-comments on case-detail pages only** —
      community discussion without document-level pollution.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| SW on all 15 archive pages | HIGH | LOW | P1 |
| Full-catalog offline cache (HTML+thumbs) | HIGH | MEDIUM | P1 |
| Per-archive bundle weight ≤ 500 KB | HIGH | MEDIUM | P1 |
| Per-document permalink (`#card-<id>`) | HIGH | LOW | P1 |
| URL-shareable filter state | MEDIUM | LOW | P1 |
| JSON-LD per page | MEDIUM | LOW | P1 |
| "Archive captured" date in footer | MEDIUM | LOW | P1 |
| Citation export widget | HIGH | LOW | P2 |
| Bulk download (ZIP per archive) | MEDIUM | LOW | P2 |
| Wayback "as captured" link | MEDIUM | MEDIUM | P2 |
| Cross-archive date facet | MEDIUM | LOW-MEDIUM | P2 |
| `/api/` doc page | LOW | LOW | P2 |
| OAI-PMH endpoint | LOW (niche but high-prestige) | MEDIUM | P3 |
| OCR pipeline for unsearchable PDFs | HIGH | HIGH | P3 |
| Social features (v2) | HIGH-IF-DONE-RIGHT | HIGH | P3 (next milestone) |

**Priority key:**
- **P1** — Must ship with SSG migration (already-on-roadmap + cheap pickups while rebuilding)
- **P2** — Strong differentiator; same milestone if scope allows, otherwise immediately after
- **P3** — Defer; either requires infra (OCR), policy (social), or low marginal value (OAI-PMH)

## Competitor Feature Analysis

| Feature | Black Vault | National Security Archive | CIA Reading Room | Our Approach |
|---------|-------------|---------------------------|------------------|--------------|
| Full-text search | YES (PDFs OCRed) | YES | YES (OCR caveat shown) | Manifest + prose; PDFs deferred to P3 |
| Faceted filters | Partial | YES (date / collection) | YES (advanced search) | YES (per-archive) — preserve |
| Boolean operators | YES | YES | YES (AND/OR/NOT) | lunr supports natively; surface in UI |
| Per-document permalink | YES | YES | YES | Pickup (P1) |
| Citation export | NO | NO | NO | **Differentiator** — pickup (P2) |
| Geographic map | NO | NO | NO | **Differentiator** — preserve |
| Timeline | NO (release-list only) | YES (briefing books) | NO | **Differentiator** — preserve |
| Cross-jurisdiction | NO (US-only) | NO (US-only) | NO (US-only) | **Core differentiator** — preserve relentlessly |
| Atom/RSS feed | NO | YES | NO | Preserve |
| Offline-first SW | NO | NO | NO | **Differentiator** — fix to all 15 archives |
| JSON-LD / schema.org | NO | Partial | NO | **Differentiator** — pickup (P1) |
| OAI-PMH | NO | NO | NO | Differentiator (P3) |
| Bulk download (ZIP) | YES (per release) | NO | YES (per collection) | Pickup (P2) |
| Comments / social | NO | NO | NO | NO (defer to v2 with careful design) |
| Engagement metrics on cards | NO | NO | NO | **Explicit anti-feature** |

## Sources

### High-confidence (named archives, official docs)

- [CIA Electronic Reading Room — Search Help](https://www.cia.gov/readingroom/search-help) — boolean/phrase operators, OCR caveat, advanced search facets
- [CIA Electronic Reading Room — Advanced Search Guide (PDF)](https://www.cia.gov/readingroom/docs/Electronic%20Reading%20Room%20Advanced%20Search%20Guide.pdf) — metadata filters
- [FBI Vault](https://vault.fbi.gov/) — ~7,000 docs, web document viewer, category browse
- [FBI Vault — New Records Vault Comes Online](https://www.fbi.gov/news/stories/new-records-vault-comes-online) — feature list
- [NSA FOIA Reading Room](https://www.nsa.gov/Helpful-Links/NSA-FOIA/Reading-Room/) — topic index pattern
- [NARA Electronic Reading Room](https://www.archives.gov/foia/electronic-reading-room) — federated FOIA library
- [National Security Archive Virtual Reading Room](https://nsarchive.gwu.edu/virtual-reading-room) — chronological browse, briefing books
- [National Security Archive — Cyber Vault Ukraine Timeline](https://nsarchive.gwu.edu/document/29562-cyber-vault-ukraine-timeline) — chronology UX pattern
- [The Black Vault — UFO Files Release Archive](https://www.theblackvault.com/documentarchive/the-black-vault-launches-searchable-ufo-files-release-archive/) — searchable text/title/agency/location/filename, ZIP download, OCR transparency
- [Internet Archive IIIF Documentation](https://iiif.archive.org/iiif/documentation) — IIIF Image + Presentation APIs
- [Archive-It OAI-PMH Guide](https://support.archive-it.org/hc/en-us/articles/210510506-How-to-provide-access-to-your-collection-s-metadata-with-OAI-PMH) — Dublin Core federation pattern
- [UK National Archives RSS Feeds](https://www.nationalarchives.gov.uk/rss/) — per-category subscription model
- [UK National Archives Discovery](https://discovery.nationalarchives.gov.uk/) — 37M+ records, tag system
- [Imperial War Museum Collections](https://www.iwm.org.uk/collections/search) — citation export, faceted search at 1M+ items
- [NICAP](https://nicap.org/) + [MUFON UFO Map](https://projectaquarius.mufon.com/ufo-reports-map/) — case-file categorization (radar / EM / formation / chronological)
- [arXiv RSS feeds](https://info.arxiv.org/help/rss.html) — per-category Atom, daily cadence

### Medium-confidence (best-practice / synthesis)

- [Offline UX design guidelines — web.dev](https://web.dev/articles/offline-ux-design-guidelines) — offline indicator, snackbar, download-icon patterns
- [Offline and background operation — MDN](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Offline_and_background_operation) — Background Sync API
- [PWA Service Worker Caching Strategies — MagicBell](https://www.magicbell.com/blog/offline-first-pwas-service-worker-caching-strategies) — selective precache, versioned cache names
- [Offline Support: Foreground Queue vs Background Sync](https://blog.tomaszgil.me/offline-support-in-web-apps-foreground-queue-vs-background-sync) — queue UX patterns
- [Faceted Navigation — Ahrefs](https://ahrefs.com/blog/faceted-navigation/) — URL-shareable filter state expectation
- [Filters vs Facets — Search.io](https://medium.com/sajari/the-definitive-guide-to-the-difference-between-filters-and-facets-5fe45276b17a) — taxonomy
- [Making Scanned PDFs Accessible (OCR + tagging)](https://documenta11y.com/blog/making-scanned-pdf-documents-accessible/) — WCAG 2.1 / Section 508 expectations
- [PDF Screen Reader — Continual Engine](https://www.continualengine.com/blog/pdf-screen-reader/) — screen-reader behavior on un-OCR'd PDFs
- [WCAG 2.0 PDF Techniques — W3C](https://www.w3.org/TR/WCAG20-TECHS/pdf) — accessibility reference
- [WebCite "Going, Going, Still There" — PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC1550686/) — permanent-archive-citation pattern, timestamped permalinks
- [Provenance — Wikipedia](https://en.wikipedia.org/wiki/Provenance) — archival chain-of-custody concept
- [FOIA.gov Developer Resources](https://www.foia.gov/developer/) — JSON API standard for FOIA
- [DCAT-US Metadata Schema — resources.data.gov](https://resources.data.gov/resources/podm-field-mapping/) — government dataset metadata convention
- [Wikisource Annotations](https://en.wikisource.org/wiki/Wikisource:Annotations) — crowdsourced transcription model (objective-annotation rule)
- [Dark Patterns Examples — Eleken](https://www.eleken.co/blog-posts/dark-patterns-examples) — engagement-metric anti-pattern inventory
- [OSC Dark Patterns Report (PDF)](https://www.osc.ca/sites/default/files/2024-02/inv-research_20240223_dark-patterns.pdf) — neutrality-violation taxonomy
- [Bellingcat Wayback Machine Toolkit](https://bellingcat.gitbook.io/toolkit/more/all-tools/internet-archive) — investigator-archive usage pattern

---
*Feature research for: offline-first government-document archive (realufo.org)*
*Researched: 2026-05-25*
