# Pitfalls Research

**Domain:** Big-bang SSG migration of a 15-archive offline-first static site, with CI-automated gov-site scraping + GH Releases asset upload + Cloudflare Pages cutover from GitHub Pages
**Researched:** 2026-05-25
**Confidence:** HIGH on items verified against Cloudflare/GitHub/MDN official docs and on the project's own `CONCERNS.md`; MEDIUM on items derived from community post-mortems and cross-source synthesis.

> This list is **specific to this migration** — not generic SSG advice. Pitfalls were selected
> by intersecting the milestone scope (`PROJECT.md` Active list) with the codebase's already-documented
> fragility points (`.planning/codebase/CONCERNS.md`) and verified migration failure modes from
> Cloudflare/GitHub/Workbox/Astro documentation. Every pitfall maps to a roadmap phase.

---

## Critical Pitfalls

### Pitfall 1: SW cache poisoning at cutover (old worker keeps serving prior origin's HTML shell)

**What goes wrong:**
On the day of the GH-Pages → CF-Pages cutover, returning visitors hit the new origin but their browsers still have the **old** service worker installed (registered when they last loaded `realufo.org` on GitHub Pages). The old SW's `fetch` handler intercepts navigations and either (a) returns the precached old shell from `CACHE_NAME = 'rsh-v<old-sha>'`, (b) attempts network-first against the new origin and successfully fetches but then re-caches under the *old* cache name, or (c) — worst case — has a bug that returns a stale `404.html` for the new archive URLs that didn't exist in the old SHELL list. CLAUDE.md §7 already documents the SW as `sw.js:23-40` with a versioned `SHELL` constant; the version is stamped from git SHA at build (`scripts/build-sw.py:31-49`). But version-stamping alone does not solve the **transition** — the old SW must download the new `sw.js`, install it, and *then* the user must reload before the new policies apply. Until then they see a hybrid: new origin, old caching rules. Commit `dcbc0d7` ("don't cache 404/non-2xx navigation responses") already shows this codebase has been bitten by stale-cache 404s before.

**Why it happens:**
Three compounding factors. First, `navigator.serviceWorker.register('/sw.js')` is byte-compared by the browser; if the new build's `sw.js` has the same bytes as the previous (e.g. the version stamp didn't actually update because `scripts/build-sw.py` failed silently), the browser will not install the new worker. Second, the *current* installed SW intercepts the request for the new `sw.js` and may serve a cached copy unless `updateViaCache: 'none'` is set on registration — and currently it is not. Third, `skipWaiting()` + `clientsClaim()` are the standard "fast cutover" tools but they create an inconsistent state where one tab is controlled by the old SW and another by the new one during the activation window.

**How to avoid:**
1. **Ship a "kill switch" SW build to the *old* origin before cutover.** Push a final commit to the GH-Pages branch that replaces `sw.js` with a deregistration script: `self.addEventListener('install', () => self.skipWaiting()); self.addEventListener('activate', e => e.waitUntil((async () => { await self.registration.unregister(); for (const k of await caches.keys()) await caches.delete(k); const cs = await self.clients.matchAll(); cs.forEach(c => c.navigate(c.url)); })()));`. Deploy this 7+ days before the CF-Pages cutover. Returning users self-unregister cleanly.
2. **Add `updateViaCache: 'none'`** to every SW registration so the `sw.js` file itself is never HTTP-cached.
3. **Bump `CACHE_NAME` prefix on cutover** (e.g. `rsh-v` → `rsh-cf-v`) so even a stale SW cannot collide with new-origin caches if it survives. Old caches drop in `activate`.
4. **Re-register on every page** post-migration (already a milestone goal — `OFFLINE-02`) so first-visit installs work for the 14 archive subpages that don't currently register.
5. **Use `skipWaiting()` deliberately, not reflexively.** Only call it for non-breaking SW updates. For the cutover itself, prefer the slower "reload-required" path with a UI banner.

**Warning signs:**
- After deploy, Umami analytics shows traffic on new origin but Chrome DevTools → Application → Service Workers reports `Source: github.io` for the active worker.
- Spike in 404s on the new origin from URLs that were precached with old paths (e.g. trailing-slash differences).
- Users report "the site is empty" / "PDFs say 404" but cache-busted incognito works fine.
- `caches.keys()` in DevTools shows multiple cache versions present 24 hours after cutover (old ones should have been deleted in `activate`).

**Phase to address:**
- **Phase scaffolding (early):** Ship the deregistration `sw.js` to GH Pages.
- **Phase cutover:** Verify new SW with new cache-name prefix.
- **Phase post-cutover:** 7-day monitoring window with explicit Lighthouse + DevTools check on returning-user-simulated profiles.

---

### Pitfall 2: URL drift breaking 95 HTML pages — trailing slashes, lowercase, and `/index.html` vs directory routing

**What goes wrong:**
Today's URLs are flat HTML files on GitHub Pages: `/aaro/`, `/aaro/index.html`, `/nara/index.html`, and root-level files like `/search.html`, `/timeline.html`, `/about.html`, `/foia.html`. GitHub Pages serves `/aaro/` → `aaro/index.html` and treats `/aaro` and `/aaro/` as equivalent (with a 301). When migrating to an SSG like Astro/Eleventy:
- **Astro default**: `trailingSlash: 'ignore'`, but the build emits `dist/aaro/index.html` *or* `dist/aaro.html` depending on layout. Mixing creates dual-indexable URLs.
- **Eleventy default**: directory-style → `dist/aaro/index.html`. Loose `.html` files at root may be regenerated as `/foia/index.html` instead of `/foia.html`, breaking every inbound link.
- **Cloudflare Pages**: Has its own trailing-slash normalisation that differs from GitHub Pages. Pages serves `/foia.html` *and* `/foia/` as separate URLs and will only 301 between them with explicit `_redirects` rules.

Inbound links (Reddit/Hacker News posts, search-engine indices, RSS feed subscribers, the `feeds/all.xml` consumers) will hit dead URLs. Internal links from `nav.py`, the cross-archive footer, and 4,500+ asset cards all assume the current pattern.

**Why it happens:**
SSGs assume "pretty URLs" (`/foia/`) as the modern default; this site predates that convention and has years of `.html` URLs in the wild. The migration is one tool's defaults colliding with another tool's defaults.

**How to avoid:**
1. **Inventory every public URL before migration.** `find . -name '*.html' -not -path './node_modules/*' | sort` against current `main`, save as `URL-CONTRACT.txt`. Compare against post-migration `dist/` listing — diff must be empty for canonical paths or covered by a `_redirects` rule.
2. **Pick one trailing-slash policy and pin it.** Recommendation: keep current behaviour — directory pages (`/aaro/`) and root-level `.html` files (`/foia.html`, `/search.html`, `/timeline.html`). In Astro this means `trailingSlash: 'always'` for directories *and* generating loose `.html` files for the root utility pages (`src/pages/foia.astro` → `dist/foia/index.html` is wrong; use `src/pages/foia.html.astro` to get `dist/foia.html`).
3. **Cloudflare Pages `_redirects` file** must cover every legacy `/aaro/index.html` → `/aaro/` 301. Test that `_redirects` syntax matches CF Pages spec (one redirect per line, source destination status — NOT Netlify's slightly-different syntax).
4. **Add a CI URL-contract gate.** A workflow that diffs the URL list against `URL-CONTRACT.txt` and fails any PR that drops or renames a URL without an explicit `_redirects` entry.
5. **301 (not 302) for every legacy URL.** SEO equity passes through 301, not 302. CF Pages `_redirects` uses status code 301 by default; verify.

**Warning signs:**
- Post-deploy, `curl -sI https://realufo.org/aaro/index.html` returns 200 (it should 301 to `/aaro/`) or 404 (broken).
- Google Search Console Coverage drops in week 2 (when re-crawl happens).
- RSS subscribers' feeds 404 — `feeds/all.xml` consumers (third-party readers) are silent witnesses.

**Phase to address:**
- **Phase planning:** Generate `URL-CONTRACT.txt` from current `main`. Block migration PR until every legacy URL is accounted for.
- **Phase CI scaffolding:** Add the URL-contract drift gate alongside `sync-nav.yml`.

---

### Pitfall 3: Akamai blocks Cloudflare Workers egress IPs more aggressively than GitHub Actions runners

**What goes wrong:**
The milestone assumes moving the scraper from GitHub Actions to Cloudflare Workers cron will *help* with Akamai blocks on war.gov (`SCRAPE-03` in `PROJECT.md` Active). It might do the opposite. Akamai Bot Manager scores requests on five layers: IP reputation, TLS fingerprint, JS challenge, behaviour analysis, session monitoring. Cloudflare's public-facing edge IPs are well-known and **flagged in Akamai's IP reputation database** — they're notorious for hosting scrapers and CF-Workers-based proxies. GitHub Actions runners (Azure-hosted) carry less stigma. The current setup also uses `curl_cffi` (`CONCERNS.md` documents this) which spoofs Chrome's TLS fingerprint — but `curl_cffi` cannot be loaded into a Cloudflare Worker (no native binary support; only WASM and JS). The Worker's `fetch()` runtime uses Cloudflare's own TLS stack, which Akamai detects.

The likely outcome: Worker cron starts succeeding for the easy sources (cnes-geipan.fr, science.nasa.gov, archives.gov), continues to fail for Akamai-fronted ones (war.gov, possibly aaro.mil), and **regresses** compared to the current Actions-runner + `curl_cffi` path. Worse, the silent-failure pattern (`|| true` everywhere) means this could ship and degrade source coverage for weeks before a stale page is noticed.

**Why it happens:**
Conflating "different egress IP" (helpful) with "less-flagged egress IP" (the actual requirement). Cloudflare's reputation for hosting scrapers makes its IPs *more* flagged, not less.

**How to avoid:**
1. **Before moving the scrape runner**, run a 1-day spike: hit war.gov and aaro.mil from a Workers cron and a GH-Actions runner on the same day; compare HTTP status, body size, and `Server`/`Set-Cookie` for Akamai signature (`AKAM_SC`, `bm_sc`, `_abck` cookies = Akamai). Document the result.
2. **Architect hybrid, not replacement.** Workers cron for the 12 easy sources, GH Actions for the 3 hard ones (war.gov, aaro.mil, plus any other Akamai-fronted DOD host found in the spike). The hybrid keeps `curl_cffi` available for hosts that need it.
3. **Use Cloudflare Browser Rendering** (`@cloudflare/puppeteer` binding) for Akamai-fronted hosts only as a fallback — actually executes JS challenges. Cost: per-second billing, slower, but works. Cron-trigger duration caps at 30 s (paid plan: up to 5 min), so the Worker must batch one source per invocation, not all 15.
4. **Drop the `|| true` from `pip install curl_cffi`** in `.github/workflows/scrape.yml:27` (`CONCERNS.md` already calls this out as `FIX-03` blocker). A failed `curl_cffi` install masquerades as success today.
5. **Add a content-fingerprint gate.** Every scrape stores a SHA-256 of the response body keyed by source URL. If the new fingerprint is suddenly the Akamai "Pardon Our Interruption" / "Access Denied" 12 KB block-page HTML (it has a stable fingerprint — first ~50 chars include `<title>Pardon Our Interruption</title>` or `<title>Access Denied</title>`), alert via GitHub Issue creation, *don't* overwrite the prior good capture.

**Warning signs:**
- After cron switch-over, body sizes for war.gov pages drop from ~85 KB to ~12 KB (Akamai block page).
- Response headers contain `Set-Cookie: _abck=` or `Set-Cookie: bm_sc=` or `Server: AkamaiGHost`.
- `dead-links.json` count climbs on the war.gov/aaro.mil rows while other rows stay healthy.

**Phase to address:**
- **Phase research-spike:** 1-day egress-IP comparison before committing to the architecture.
- **Phase scrape-migration:** Hybrid scrape runner (Workers + Actions) — do not replace Actions wholesale.

---

### Pitfall 4: Content-fidelity drift — verbatim official text auto-formatted by markdown/MDX

**What goes wrong:**
CLAUDE.md §9 mandates **verbatim official text** for hero lede, headlines, FAQ accordion answers. The current Python pipeline reads CSV cells and string-templates them into HTML — quotes stay as `"`, em-dashes stay as `—`, French accents stay as `é`. An SSG that processes content through markdown (Astro `.md`/`.mdx`, Eleventy with `markdown-it`) silently rewrites:
- `"straight quotes"` → `"smart quotes"` (typographer plugin)
- `--` → `–` (en-dash), `---` → `—` (em-dash)
- `…` is preserved, but `...` gets typeset as `…`
- `(c)` → `©`
- Bare URLs auto-linkified (changes anchor structure)
- Trailing whitespace inside `<p>` blocks collapsed; soft-wrap inside multi-line French/Spanish text breaks word boundaries on accented chars

Worse, the **mojibake risk**: Astro has open GitHub issues (#4538, #2187, #4695) where accented characters in markdown frontmatter get mangled (`'` → `â€™`, `é` → `Ã©`). This is exactly the failure mode for the 6 archives with non-ASCII text (GEIPAN, Brazil, Chile, Argentina, Italy, Peru, Spain, Uruguay — and English archives quoting non-English place names).

The current Python build also intentionally preserves `<strong>` and `<em>` tags from `_cases.json` (CONCERNS.md notes this as a "trusted markup" pattern). Markdown processors will double-escape them: `<strong>` in source → `&lt;strong&gt;` in output.

**Why it happens:**
SSG defaults assume the input is markdown-like prose authored by humans, not verbatim government text. The "typographer" feature is enabled by default in most markdown configs; UTF-8 round-tripping through file → frontmatter → JS string → HTML has edge cases per-tool.

**How to avoid:**
1. **Do not use markdown for archive content.** Use the SSG's templating language directly with raw string data (Astro: `.astro` components reading from JSON/CSV; Eleventy: `.njk` with `safe` filter). Markdown can stay for prose pages (`about`, `foia`, story pages) where typography improvements are desirable.
2. **Pin source encoding to UTF-8 explicitly** at every layer:
   - SSG config: `output: { charset: 'utf-8' }`
   - `<meta charset="utf-8">` (CLAUDE.md already requires this)
   - CSV reader: `encoding='utf-8'` (Python default but pin it; Node CSV libs default to system locale)
   - File system: verify build runner locale via `locale` in CI; pin to `LANG=en_US.UTF-8` in workflow env.
3. **Disable typographer** in any markdown processor used: Astro `markdown.smartypants: false`; remark-smartypants not installed; Eleventy markdown-it `{ typographer: false }`.
4. **Add a content-fidelity CI gate.** A script (`scripts/verify-fidelity.py`) extracts every `.ti` and `.de` field from `arch-data` JSON in both *pre-migration* HTML (current `main` snapshot) and *post-migration* `dist/`, and fails if any title/description changed. Acceptance: byte-exact match on every cell.
5. **For the case-prose HTML (AARO `_cases.json`'s `lede` with `<strong>` tags)**, pass through an explicit "trusted-html" component in the SSG (Astro: `<Fragment set:html={lede} />`; Eleventy: `{{ lede | safe }}`). Document the convention in the new build code (a Python `_html` suffix convention is also proposed in CONCERNS.md §Security).

**Warning signs:**
- Diff between pre/post `arch-data` JSON shows `"` ↔ `"`, `--` ↔ `–`, `é` ↔ `Ã©`.
- Diff between rendered HTML shows `&amp;lt;strong&amp;gt;` where `<strong>` should be (double-escape).
- French/Spanish locale users report "site is in gibberish."

**Phase to address:**
- **Phase SSG scaffolding (very early):** Pick a non-markdown content path for archive cards. Pin UTF-8 at every layer.
- **Phase migration:** Run `verify-fidelity.py` before merging the migration PR. **Block on byte-mismatch.**

---

### Pitfall 5: GH Releases `--clobber` race + 1000-asset-per-tag ceiling

**What goes wrong:**
The CI-automated release upload (`FIX-03` in `PROJECT.md`) will call `gh release upload <tag> <files…> --clobber` from `.github/workflows/scrape.yml` after the scrape stage discovers new binaries. Two failure modes documented in GitHub CLI issues:
1. **`--clobber` deletes before uploading.** Issue cli/cli#4863: `--clobber` removes existing assets *first*; if the upload fails (network, 2 GB cap, runner OOM), the old asset is gone. Combined with `gh release create` race issue (cli/cli#4270) leaving partial draft releases, a flaky CI run can wipe a previously-working binary and replace it with nothing — and the next visit to that asset's card returns 404 from a Download button.
2. **1000-asset-per-tag ceiling.** GitHub's documented per-release asset limit is 1000. Current state per CLAUDE.md §5.1: `pdfs-v1` has 165 PDFs, `videos-v1` has 60 mp4 — well under 1000, but growth is one-way (Releases 02, 03 + scrapes adding new files weekly). Adding the UK National Archives full catalogue (~70k records, even if only a fraction is PDF-mirrored) blows past 1000 trivially.
3. **2 GB per-asset limit.** Hard limit. Multiple PDFs in the gov-source dumps already approach the limit; a future scanned-record release exceeding 2 GB silently fails the upload.

Parallel `gh release upload` from multiple matrix jobs to the same tag also race — there is no documented locking in the GH API for releases, and the underlying HTTP API can return 422 "asset already exists" on the second uploader.

**Why it happens:**
GitHub Releases was designed for human-curated software releases, not as a CDN for automated weekly drops of hundreds of files.

**How to avoid:**
1. **Never use `--clobber` for "replace if changed."** Instead: check file SHA-256 against asset name; if asset exists and SHA matches, skip; if SHA mismatches, **delete-then-upload as two explicit steps** with a retry-on-failure that re-uploads from the runner's local copy. Make this a `scripts/release-upload.py` helper.
2. **Per-archive tags** (`geipan-v1`, `uk-v1`, `aaro-v1`, …) instead of cross-archive (`pdfs-v1`). CLAUDE.md §5.1 already gestures toward this. Each archive's tag stays well below 1000 assets.
3. **Versioned tag rotation** when one approaches 1000: e.g. `geipan-v1` reaches 950 → freeze; future uploads go to `geipan-v2`. Build-side URL resolution must lookup which tag holds which basename — implement via the existing `release-manifest.json` mechanism.
4. **For files > 2 GB**, use Cloudflare R2 instead (free egress class A operations, S3-compatible). Already gestured at in CLAUDE.md's hosting strategy. Keep R2 as overflow, GH Releases as primary.
5. **Serialise CI uploads to the same tag.** Use GitHub Actions `concurrency: group: release-upload-${{ matrix.tag }}, cancel-in-progress: false` so two scrape runs don't fight over the same release. `cancel-in-progress: false` is critical — `true` would *cancel a successful upload mid-flight*.
6. **Idempotency key** = file SHA-256 in the asset's basename suffix (e.g. `2024-rep01.sha256-abc123.pdf`) when uploading. Card-side URL resolution uses the unsuffixed basename → manifest lookup. This makes re-uploads of identical files no-ops.

**Warning signs:**
- `gh release view <tag>` shows asset count climbing toward 900+ on any tag.
- 422 / 409 errors in CI logs around `gh release upload`.
- A previously-working Download button starts 404'ing after a scrape run.
- Audit script `scripts/backfill-release.py` (already exists per CONCERNS.md) starts emitting non-empty diffs after every weekly cron.

**Phase to address:**
- **Phase scrape-automation:** Implement `scripts/release-upload.py` with delete-then-upload + SHA check + retry.
- **Phase scaling:** Per-archive tag scheme + cutover plan from `pdfs-v1` to per-archive tags.

---

### Pitfall 6: Inline-JSON refactor creates a network waterfall worse than the 3 MB blob

**What goes wrong:**
`PERF-01` targets reducing per-page inline JSON (geipan is 3.3 MB). The naive fix — fetch per-card from `/api/cases/<id>.json` — replaces one large download with thousands of small ones. On mobile 3G with HTTP/1.1 (which CF Pages does support HTTP/2/3, but iOS Safari + corporate proxies sometimes downgrade), 3,000 GEIPAN cases × 1 RTT each = catastrophic. Even with HTTP/2 multiplexing, browser per-origin connection limits + server-side per-request overhead create a tail latency that's *worse* than a single 3.3 MB blob the SW can stream-cache.

Worse: the current per-archive page renders the card grid synchronously from inline JSON. Splitting the JSON out means JS must wait for `fetch()` → JSON parse → render. First Contentful Paint moves from "fast (inline)" to "slow (network-dependent)". Mobile users see a blank skeleton longer than today.

**Why it happens:**
"Reduce bundle size" intuition treats all bytes as equivalent. They are not — inline bytes are paid once with the HTML and parsed synchronously; fetched bytes have a request-overhead toll.

**How to avoid:**
1. **Shard, don't atomise.** Split GEIPAN's 3 MB into 3 × 1 MB shards by year range or by paginator page (page 1 inline in HTML for instant FCP, pages 2-N as separate JSON fetched on tab-click). The existing GEIPAN paginator bail-out (`scripts/templates/archive.py:38`) already provides the hook.
2. **Inline the *first paint's worth* of cards** (e.g. the first 50 by date) directly in the HTML; lazy-fetch the rest from a single per-archive `/<slug>/data.json`.
3. **Measure before optimising.** Lighthouse + WebPageTest before and after; target metric is **LCP / TTI**, not "inline JSON byte count." A 3 MB inline JSON that the V8 parser handles in 80 ms on a mid-tier phone may not be the actual bottleneck.
4. **Service worker stale-while-revalidate** on the per-archive JSON URL means second-visit is instant. Per CONCERNS.md "Inline JSON in Index.html Defeats SW Stale-While-Revalidate" — externalising is the right move *for caching*, but the same warning applies.
5. **Avoid fetching from inside `DOMContentLoaded`** — fetch as a `<link rel="preload" as="fetch" crossorigin>` in `<head>` so JSON arrives in parallel with HTML parsing.
6. **HTTP/2 push is dead; do not rely on it.** Cloudflare deprecated H2 push; use Early Hints (CF Pages supports via `103` responses + `_headers` file).

**Warning signs:**
- Lighthouse LCP regresses post-refactor (was 2.4 s, now 3.8 s).
- WebPageTest waterfall on `/geipan/` shows a long "blocked" phase after HTML download.
- 2nd-visit TTI doesn't beat 1st-visit TTI (SW cache miss → suspect a versioning bug).

**Phase to address:**
- **Phase perf-budget scaffolding:** Set Lighthouse budgets explicitly (LCP ≤ 2.5 s, TTI ≤ 3.5 s on 3G mid-tier emulation) before refactoring.
- **Phase JSON-split:** Implement shard-not-atomise. Measure each shard against budget.

---

### Pitfall 7: Cross-archive consistency drift — 15-way visual/nav/footer regression hides in the migration PR

**What goes wrong:**
The big-bang migration PR will touch every archive's HTML. With 15 archives, a reviewer can spot-check 3–4 and reasonably miss regressions in archives 12, 13, 14, 15 (Peru, Spain, Uruguay, NZ). Today, two CI workflows (`sync-nav.yml`, `sync-footer.yml`) are the drift gates — but they verify the *current* HTML format. After the SSG migration, **the nav/footer HTML output may legitimately change** (because the new template emits semantically equivalent but textually different markup), which means the existing drift gates either:
- (a) **break** during migration (every page differs) and must be temporarily disabled, opening a window where real drift is not caught; or
- (b) **pass falsely** because the canonical-source HTML is rewritten alongside the pages, so drift between archives goes undetected.

The existing `templates/nav.py` (PINNED, SITE_PAGES) and `templates/footer.py` would be ported to SSG components, but the per-archive tone colour (CLAUDE.md §3.1) and per-archive seal gradient are 15 distinct CSS-variable sets that each must remain correct. A single `--caution` variable typo in archive #14 produces a page that looks 95% right and 5% wrong (e.g. Spain shows blue accent instead of `#f4c542` gold) — easy to miss in a 15-page diff.

**Why it happens:**
Reviewer attention is non-linear: drops sharply after the first 3-4 examples of "this is fine." Drift between identical-shape pages is the hardest visual diff to catch.

**How to avoid:**
1. **Visual-regression CI on all 15 archives.** Playwright + `@playwright/test`'s `expect(page).toHaveScreenshot()` against snapshots checked in at PR-creation. Cover: `/`, `/aaro/`, `/nasa/`, …, `/uruguay/`, plus `/search.html`, `/timeline.html`, `/map.html`, `/about.html`, `/foia.html`. 4 viewports each (360, 720, 1024, 1440). Fail on >0.1% pixel diff.
2. **Per-archive tone-colour smoke test.** A script reads each archive's `<style>` for `--caution: #xxxxxx` and asserts against a JSON manifest of expected colours per CLAUDE.md §3.1. Catches the "Spain shows blue" regression in <100 ms.
3. **Migrate one archive per PR.** Big-bang is a milestone goal, but the *PR strategy* can still be incremental: feature-flag the SSG output per archive, migrate one per PR, ship to a staging subdomain (`v2.realufo.org`), gate on visual-regression + manual smoke. Final cutover PR is a single one-line config flip.
4. **Footer source-list verification.** The `make_footer_sources()` function emits per-archive official URLs (CLAUDE.md §4.1). A test asserts every archive's footer contains its declared source URL (the official one from CLAUDE.md §2 table).
5. **Reviewer checklist required in PR template.** Explicit "I have verified archives 1, 5, 10, 14 visually on mobile" forces sampling.

**Warning signs:**
- Visual-regression CI shows pixel diff on archive #11 but you only investigated archives 1-5.
- A user reports "the Peru page looks wrong" 3 days post-cutover.
- One archive's nav shows old links while others updated (the nav-template port missed one consumer).

**Phase to address:**
- **Phase CI scaffolding (early, before migration):** Install Playwright + visual snapshots of *current* `main` as the contract.
- **Phase migration:** Every per-archive PR must pass visual-regression + tone-colour smoke.

---

### Pitfall 8: Cloudflare Pages `_redirects` and `_headers` syntax differences from Netlify break expectations

**What goes wrong:**
Developers familiar with Netlify or older CF Pages docs assume `_redirects` and `_headers` syntax is uniform. Key documented gotchas:
- **`_redirects` infinite-loop detection.** Cloudflare Pages build system silently *drops* redirect rules it considers loops — `/*  /index.html  200` for SPA fallback gets ignored (community thread `cloudflare-pages-redirects/816132`).
- **Status-code defaults.** Netlify defaults to `200` (rewrite); CF Pages defaults to `302`. A blanket `/old/* /new/:splat` without explicit `301` becomes a 302, which doesn't pass SEO equity.
- **404 directory vs file.** CF Pages looks for `404.html` per directory; an SSG that emits `dist/404/index.html` (Astro under some configs) does **not** match — needs to emit `dist/404.html` (Astro issue #6177).
- **`_headers` precedence.** Headers set via `_headers` *override* those set by CF transform rules, but Cloudflare's own security headers (HSTS, etc.) are layered on top and not overridable from `_headers` alone.
- **Service worker `Cache-Control`.** Default CF Pages cache headers on `/sw.js` are static-asset-style (long max-age). The SW must be served with `Cache-Control: no-cache` or browsers will not pick up updates until the cache expires.

**Why it happens:**
Each static-host platform has subtly different config; copy-paste from Netlify tutorials lands in CF Pages with hidden behavioural drift.

**How to avoid:**
1. **Use the official CF Pages docs as the only reference.** Specifically `developers.cloudflare.com/pages/configuration/serving-pages/` and `/redirects/` and `/headers/`.
2. **Test every redirect end-to-end with curl.** A test script (`scripts/verify-redirects.sh`) runs through every URL in `URL-CONTRACT.txt` against the CF Pages preview deployment and asserts the right status code + Location header.
3. **Pin `_headers` for `/sw.js` and `manifest.webmanifest` explicitly.** Example:
   ```
   /sw.js
     Cache-Control: no-cache
     Service-Worker-Allowed: /
   /manifest.webmanifest
     Content-Type: application/manifest+json
   ```
4. **For 404.html, emit at the exact root path.** Verify in the build output: `ls dist/404.html` must succeed.
5. **Use `_redirects` syntax `<from> <to> <status>` (one per line, no commas).** Verify with the CF Pages build log — it prints how many redirects were parsed.

**Warning signs:**
- Preview deploy build log says `Parsed N redirects` where N < expected.
- Redirect tests return 302 instead of 301.
- The 404 page is the CF generic "404 Not Found" instead of custom branded one.
- `curl -I https://realufo.org/sw.js` shows `Cache-Control: public, max-age=14400` (default) instead of `no-cache`.

**Phase to address:**
- **Phase Cloudflare scaffolding:** Build `_redirects`, `_headers` files explicitly tested against preview.

---

### Pitfall 9: Offline-first regression — SW registered too late, no-JS users broken by SSG over-hydration

**What goes wrong:**
The current site is HTML-first: every archive page is fully rendered server-side (build-side) with inline JSON; JS only enhances the lightbox and filters. A user with JS disabled can still read titles, descriptions, and click direct PDF links. CLAUDE.md §1.3 promises "offline by default" and is implicit about "no-JS-render-blocking."

SSG frameworks vary:
- **Astro:** Defaults to zero-JS (islands architecture). Compliant *if* archive cards are written as `.astro` components, not as `<X client:load />` islands.
- **Eleventy:** Zero JS by default. Compliant.
- **Next.js `output: 'export'`:** **Not compliant** — React hydration is mandatory; cards render empty until JS executes.

Service worker registration order also matters. Today the inline `<script>` block in `<head>` calls `navigator.serviceWorker.register('/sw.js')` synchronously. If the SSG defers all JS to `defer` or `module` (async) scripts, registration may not happen until after first contentful paint — fine in practice but means first-visit users go offline-eligible later in the page lifecycle.

The `OFFLINE-03` milestone goal (precache every HTML page + every thumbnail) creates a separate risk: the SW `install` event must `cache.addAll(SHELL)` with 15 archive roots + N utility pages + ~thousands of thumbnails. If `SHELL` exceeds a few MB, the install can fail (especially on iOS) or take so long that the user reloads before installation completes. Today's SHELL is 600 bytes shy of complete (CONCERNS.md notes 12 missing entries); the full-catalog version is orders larger.

**Why it happens:**
"Modern SSG" defaults toward JS-heavy patterns; offline-first promises are easy to break with one careless `client:load` directive.

**How to avoid:**
1. **Reject Next.js export and Gatsby outright.** They require hydration; archive view is broken with JS off. Astro or Eleventy only.
2. **Zero-JS-island contract.** Every archive card renders server-side. JS only enhances: lightbox click handler, filter inputs, hamburger toggle. No `client:load`, `client:idle`, `client:visible` on card components.
3. **JS-off test in CI.** Playwright test with `javaScriptEnabled: false` loads each archive root and asserts (a) card titles are visible, (b) direct asset links are clickable. Fail if either is empty.
4. **SW registration in `<head>` inline.** Per CLAUDE.md §9 the current pattern is `<script>if("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js", { updateViaCache: 'none' });</script>` inline. Preserve verbatim. The SSG's `<head>` slot must accept inline scripts.
5. **Chunk the precache.** Instead of one `cache.addAll(huge_array)`, run `Promise.all(SHELL.map(u => cache.add(u).catch(() => {})))` (already the pattern at `sw.js:47` per CONCERNS.md — preserve it). Each failed precache entry is logged but doesn't fail the install.
6. **Lazy precache.** Precache only critical shell at install time (15 archive roots + 5 utility pages); use `fetch`-time runtime caching for thumbnails on first visit.

**Warning signs:**
- A Playwright JS-off test renders an empty `<main>` on `/aaro/`.
- DevTools → Application → Service Workers shows "install failed" or "timeout."
- iOS Safari users report "white screen on first visit" (SW install racing with page render).

**Phase to address:**
- **Phase SSG-decision (very early):** SSG choice gated on JS-off compliance.
- **Phase offline:** SHELL composition + chunking strategy before enabling SW on the 14 archive subpages.

---

### Pitfall 10: Cloudflare Workers cron retry storms + 1 KV write/sec per key creates a thundering herd

**What goes wrong:**
The scrape Worker writes per-source state to KV (`last-fetched-<source>`, `content-hash-<source>`). If the cron fires every 30 min and a transient source-side 503 causes a retry, the Worker may write the same key multiple times within 1 s — hitting KV's documented "1 write per key per second" rate limit (verified: docs `developers.cloudflare.com/kv/platform/limits/`). The 429 response from KV can cascade: retry → another 429 → exponential backoff that eats the Worker's CPU budget (10 ms free, 30 s paid).

Worker invocation costs: at $0.30 per million on the Paid plan + duration. A cron firing every 5 min × 15 sources × retry storm = ~50k invocations/month from one bad source. Cheap, but plus the KV reads/writes ($0.50/M reads, $5.00/M writes) it accumulates.

Cron triggers also have no built-in "skip if previous still running" lock. Two cron firings overlapping is allowed and can both attempt to overwrite the same KV key.

**Why it happens:**
Defaults assume idempotency on retry; KV's per-key write rate limit is documented but easy to miss.

**How to avoid:**
1. **Lock around cron run.** First line of the cron handler: `const lock = await env.KV.get('cron-lock'); if (lock && (Date.now() - parseInt(lock)) < 60_000) return; await env.KV.put('cron-lock', String(Date.now()), { expirationTtl: 120 });`. Cheap mutex.
2. **Batch source-state writes.** Instead of one write per source, accumulate updates in memory and write a single JSON blob `all-sources-state` at end of run — one write key, never rate-limited.
3. **Distinct cron schedules per source group.** `0 6 * * 1` for slow sources, `*/30 * * * *` for fast — don't pile all 15 sources into one invocation.
4. **Exponential backoff with jitter** on source-side errors. First retry 30 s, then 5 min, then 1 h. No more than 3 retries per cron run.
5. **Budget guardrails.** A monthly $-cap on the Worker via Cloudflare's budget alerts. Workers Paid plan has a $5/month minimum + usage; cap at $20/month and review usage weekly during stabilisation.
6. **Use Durable Objects** for the lock if multi-instance contention emerges (cron triggers can fire from multiple data centres). Single DO instance = single-writer guarantee.

**Warning signs:**
- KV write rate-limit errors (429) in Worker logs.
- Worker invocation count exceeds 100k/month for what should be ~5k.
- Sources show inconsistent "last-fetched" timestamps that go backwards.

**Phase to address:**
- **Phase scrape-worker design:** Lock + batch-writes baked in from day 1.
- **Phase scrape-stabilisation:** Budget guardrails + observability.

---

## Moderate Pitfalls

### Pitfall 11: Mobile-first regression — SSG default templates are desktop-first

**What goes wrong:**
Astro starter templates, Tailwind defaults, and most SSG examples are desktop-first with `min-width` media queries — exactly the opposite of CLAUDE.md §8 which mandates "Base styles assume 360 px viewport." A reviewer eyeballing the desktop preview misses that 360 px is broken (tab strip horizontally scrolling, lightbox nav buttons off-screen, hamburger missing).

**Why it happens:**
SSG community examples optimise for the demo screenshot (desktop).

**How to avoid:**
- Preserve current CSS verbatim (it's already mobile-first). Port to SSG as a single CSS module; do not re-architect.
- **Lighthouse mobile in CI** (already exists per CONCERNS.md `.lighthouserc.json`); ensure it's running with `--preset=mobile` and `--throttling.cpuSlowdownMultiplier=4`.
- **Playwright at 360 × 640** as the default test viewport — every visual snapshot at mobile first.
- Audit hidden overflows: `document.documentElement.scrollWidth === document.documentElement.clientWidth` test in Playwright.

**Phase to address:** Phase CI scaffolding + Phase migration QA.

---

### Pitfall 12: Public-domain attribution dropped during template refactor

**What goes wrong:**
`templates/footer.py` `make_footer_sources(license_text)` carries per-archive licence text (17 USC §105, Loi 78-753, OGL v3, etc. per CLAUDE.md §9). In the SSG port, the footer becomes a component that pulls licence from a per-archive data file. A typo, a `null` instead of empty-string handling, or a developer "consolidating duplicates" can silently delete an archive's licence footnote. Public-domain attribution is a legal/ethical contract, not a UX nicety.

**Why it happens:**
Footers are visual furniture; reviewers skip them.

**How to avoid:**
- **Test per archive: footer contains expected licence string.** A simple Playwright `expect(page.locator('footer')).toContainText(LICENSE_BY_SLUG[slug])` for all 15 archives.
- **Single source of truth for licence strings.** A `LICENSE_BY_JURISDICTION` constant (already in `templates/footer.py`); port as a typed const, not free-text.
- Document in CLAUDE.md §9 as a hard contract.

**Phase to address:** Phase migration QA (licence verification in same Playwright run as visual regression).

---

### Pitfall 13: GitHub Actions ↔ Cloudflare ↔ GH Releases coordination — partial-failure recovery

**What goes wrong:**
The CI flow envisioned in `SCRAPE-02`: scrape → diff → upload to Releases → rebuild → deploy via CF Pages. Each step can fail independently:
- Scrape succeeds, upload fails → manifest references release URL that doesn't exist → 404 on download buttons.
- Upload succeeds, build fails → release has new files but site doesn't reference them.
- Build succeeds, CF Pages deploy fails → site is on stale shell; new releases unreachable.
- Push to git succeeds, but deploy webhook drops → CF Pages doesn't know.

Without idempotency, retrying a failed run can double-upload binaries or commit twice.

**Why it happens:**
Distributed workflow without transactional semantics; each step's failure mode is independent.

**How to avoid:**
- **Idempotency keys at every step.** Release-upload keyed by file SHA-256. Commit message includes scrape run-ID; if a re-run sees the same run-ID already committed, it's a no-op. Deploy webhook is best-effort + a backup polling step.
- **Pre-deploy verification step.** Before merging to main, a CI job hits the preview deploy URL and asserts every release-URL in the manifest is HEAD-able.
- **Resume from where it left off.** Each step writes a `step-N.done` marker to the runner workspace before moving on; a retry checks markers and skips done steps.
- **Concurrency-control the workflow.** `concurrency: group: scrape-deploy, cancel-in-progress: false`. Verified: cancel-in-progress: true would abort an in-flight deploy.

**Phase to address:** Phase scrape-automation design; Phase post-cutover hardening.

---

### Pitfall 14: Wayback Machine fallback URL drift — hardcoded years go stale

**What goes wrong:**
Per CONCERNS.md "Wayback Fallback Is Single-Snapshot, Hardcoded Year": `scrape-chile.py:88`, `scrape-brazil.py:78`, `scrape-uk.py:121` hardcode `web.archive.org/web/2024id_/` and `scrape-aaro.py:55` hardcodes `2025id_/`. In the SSG migration / scraper refactor, easy to copy these constants without updating. Year 2026 / 2027 onwards, the fixed-year snapshot URLs increasingly miss for newly-discovered URLs.

**How to avoid:**
- Promote the CDX-API dynamic pattern from `dl-aaro.sh:45` into a shared helper (Python: `scripts/_wayback.py`; Bash: `scripts/_wayback.sh`).
- Test: a scrape against a known-broken-source URL must fall through to CDX-API and return the latest snapshot.

**Phase to address:** Phase scrape-migration (couple this fix with the runner rewrite).

---

### Pitfall 15: DNS TTL set high pre-cutover — extended downtime / split-brain

**What goes wrong:**
`realufo.org` currently points to GitHub Pages. The DNS A/CNAME record probably has a default TTL (often 3600 s = 1 h). On cutover, dropping the TTL to 300 s should be done **7+ days ahead** (because users / resolvers cached the old TTL); if dropped same-day, propagation can take hours during which half of users hit GH Pages (old, with potentially stale SW) and half hit CF Pages (new). Mixed-traffic period stretches the SW-cache-poisoning risk (Pitfall 1) from hours to a day.

**How to avoid:**
- Drop TTL to 300 s exactly **7 days before** planned cutover.
- Switch DNS during a low-traffic window (Sunday early UTC for a global site).
- After 24 h stable, raise TTL back to 3600 s.
- Cloudflare's "atomic API approach" still expects 2-5 s downtime per recent migration write-ups; communicate via status page if a public one exists.

**Phase to address:** Phase cutover-prep checklist (T-7 days).

---

### Pitfall 16: Search-index drift — `/api/all.json` rebuilt with subtle JSON-key changes

**What goes wrong:**
`search.html` consumes `/api/all.json` (4.6 MB per CONCERNS.md). The new SSG build emits `/api/all.json` from JSON/CSV source. Subtle key renames (`ti` → `title`, `de` → `desc`, or order changes in a `JSON.stringify` ordering) silently break the lunr index or the search-results card render that consumes the same schema. The runtime search degrades to "no results" or "broken layout" without HTML validation flagging it.

**How to avoid:**
- Schema-fingerprint `/api/all.json` before and after migration; key set must be byte-identical.
- Validate-manifests CI step (`scripts/validate-manifests.py` already exists) updated to also validate `/api/all.json` schema.
- Search smoke test in Playwright: `await page.goto('/search.html?q=tic+tac'); await expect(page.locator('.search-result')).toHaveCount(/* known good count */)`.

**Phase to address:** Phase migration verification.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Use `--clobber` to replace release assets blindly | One-liner CI | Race-condition data loss; previously-working Download buttons start 404'ing | Never in CI; OK for one-off local backfills |
| Skip mobile QA on archives 11–15 ("they're small") | Faster PR | Visual regression discovered by users post-cutover, no analytics on per-archive 360 px bug rates | Never — Playwright mobile-viewport coverage is cheap |
| `pip install curl_cffi || true` | Pipeline never red-fails | Akamai blocks slip through invisibly; war.gov content goes stale | Never — fail loudly on missing critical deps |
| Ship CF Pages cutover without deregistering old SW | No "scary" pre-cutover commit | Returning users serve stale shell for hours-to-days; user-reported "site broken" | Never — pre-cutover deregister is non-negotiable |
| Inline 3.3 MB JSON for GEIPAN | Synchronous first paint | First-time mobile users on 3G see 5 s blank screen | Acceptable as a stopgap if `PERF-01` budget allows; revisit by milestone end |
| Markdown-process gov content for "free typography" | Smart quotes, em-dashes look nice | Verbatim contract broken, mojibake on French/Spanish, double-escape on `<strong>` | Never for archive cards; OK for `about.md`, story pages |
| One mega-PR for all 15 archives | "Ship the migration" | Visual regressions on archives 12–15 escape review | Never — feature-flag per archive, ship cutover as one-line PR |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| **Cloudflare Pages** | Assume Netlify-compatible `_redirects` syntax | Use CF Pages docs verbatim; `_redirects` is `<from> <to> <status>`, no commas; status defaults to 302 — write `301` explicitly |
| **CF Pages 404 handling** | Build emits `dist/404/index.html` | Force `dist/404.html` — verify with `ls dist/404.html` in CI |
| **CF Pages `_headers`** | Forget to override default SW caching | Pin `/sw.js → Cache-Control: no-cache` explicitly |
| **Workers KV** | Write same key in a loop | Batch into one write per key per cron run; respect 1/sec/key limit |
| **Workers cron** | Assume "skip if previous still running" | Implement explicit lock in KV; cron can overlap |
| **Workers fetch** | Expect `curl_cffi`-style TLS fingerprint spoofing | Use Cloudflare Browser Rendering binding (Puppeteer) for Akamai-fronted hosts, or fall back to GH Actions runner |
| **GH Releases** | `gh release upload --clobber` for replacement | Two-step: SHA-check, delete-then-upload, with retry; never lose the prior asset |
| **GH Releases** | Single mega-tag (`pdfs-v1`) for everything | Per-archive tags from day one; resolve via `release-manifest.json` |
| **GitHub Actions** | `concurrency: cancel-in-progress: true` on deploy workflow | `false` for deploys (never cancel a release in flight); `true` is OK for test workflows |
| **Astro/Eleventy markdown** | Default typographer/smartypants on | Disable explicitly: `smartypants: false`, `typographer: false` |
| **DNS cutover** | Drop TTL same day | Drop TTL to 300 s **7 days** before cutover |
| **Service worker** | Default `register('/sw.js')` | `register('/sw.js', { updateViaCache: 'none' })` to break HTTP-cache loop |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Atomise inline JSON into per-card fetches | LCP regresses; mobile 3G shows skeleton longer | Shard into ≤3 chunks; inline first paint's worth; lazy-fetch rest | When >50 cards per page on slow networks |
| 4.6 MB `/api/all.json` re-fetched on every deploy | Mobile users' 4G allowance burned | Per-archive shards with ETag-based cache busting | Already a problem (CONCERNS.md flagged) |
| SW `cache.addAll([…huge array…])` on install | Install timeout on iOS Safari; first-visit users uncached | `Promise.all(SHELL.map(u => cache.add(u).catch(() => {})))` + lazy thumbnail precache | At ~50+ SHELL entries, iOS gets flaky |
| Markdown-process every archive page through MDX | Slow build; build-CI minutes balloon on 15 archives × 4500 cards | Native SSG template (no markdown) for cards; markdown for prose only | Eleventy build at >30 s; Astro at >60 s |
| `cache: 'no-store'` on KV reads from Worker | Worker invocation duration blows past 30 s | Use Workers Cache API + KV `cacheTtl` parameter | High-frequency cron |
| Visual-regression CI without throttling | Snapshots match on CI but break in production | Lighthouse mobile + cpuSlowdownMultiplier=4 | Inconsistent across CI runs |
| 1000+ assets in one release tag | `gh release view` slow; upload concurrency degrades | Per-archive tags well below 1000 each | At ~900 assets / tag |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Pass-through `<strong>`/`<em>` from `_cases.json` without naming convention | Future contributor adds untrusted CSV field via same path → XSS | `_html` suffix convention for trusted-html fields; everything else escaped (CONCERNS.md proposes this for Python; port to SSG) |
| `window.open(a.u)` without URL-scheme allowlist | `javascript:` URL injection if a source page is compromised | `escUrl()` rejecting anything not in `https:/http:/mailto:/` and relative paths (CONCERNS.md §Security) |
| Trust `_redirects` is rate-limited at CF edge | Open redirect via `/r?url=…` style | Don't ship open-redirect endpoints; if needed, validate against an allowlist |
| Inline scripts allowed by relaxed CSP for SSG output | Future XSS if a content field bleeds into a template | Tighten CSP post-migration; current `default-src 'self'` is good — preserve verbatim |
| Worker secrets in plain env vars | Secret leaked in logs | Wrangler `secret put`; never `env.X` set from `wrangler.toml` for sensitive values |
| Verbatim gov-source HTML rendered without sanitisation | Stored XSS from a compromised gov source | Sanitise on ingest (build-time) not on render; whitelist `<strong>`, `<em>`, `<a>` only |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Hamburger menu (☰) renders but never opens on first visit | Mobile users can't navigate, bounce | Playwright test: click hamburger, expect `aria-expanded="true"` and nav visible |
| Lightbox arrow keys don't work after migration (event handler regression) | Keyboard users locked into a card | Playwright keyboard nav test (CLAUDE.md §7 invariant) |
| Search-query `?q=` no longer restored on reload | URL-shared search results break (key sharing pattern) | Preserve invariant 8 from CLAUDE.md §7; test |
| 404 page on CF Pages is generic Cloudflare, not branded | Brand discontinuity; users think site is down | `dist/404.html` correctly emitted; tested via `curl -I https://realufo.org/nonexistent` |
| Toast/banner on SW update suggests "Reload to update" but reload doesn't apply update | User confusion; "I clicked reload, still old" | Use `registration.waiting.postMessage('SKIP_WAITING')` + listen for `controllerchange` |
| Per-archive tone colour wrong on one archive (Spain blue not gold) | Brand drift; user assumes wrong jurisdiction | Tone-colour smoke test asserts `--caution` per archive |
| Lightbox swipe direction inverted on mobile post-port | Touch users confused | Preserve `> 50 px && < 800 ms` swipe contract (CLAUDE.md §7) |

---

## "Looks Done But Isn't" Checklist

- [ ] **SW registered on all 15 archive pages:** Verify with `grep -c "serviceWorker" */index.html` — all 15 must be ≥1 (CONCERNS.md confirms current state: ~0).
- [ ] **SW deregistration push to old origin BEFORE cutover:** Verify the GH-Pages branch has the kill-switch SW deployed 7+ days pre-cutover; no merge of CF cutover until then.
- [ ] **Every legacy URL has a 301 in `_redirects`:** Run `scripts/verify-redirects.sh` against preview deploy; zero unaccounted-for URLs.
- [ ] **Visual regression: every archive at 360 px:** Playwright snapshots stored for all 15 archives; PR must pass mobile-viewport snapshots.
- [ ] **Per-archive tone colour correct:** Smoke test `--caution` CSS variable matches CLAUDE.md §3.1 table for all 15 archives.
- [ ] **Footer source URL correct per archive:** Footer of each archive contains its official source URL (matches CLAUDE.md §2 table).
- [ ] **Public-domain licence per archive correct:** Footer of each archive contains the correct licence (US 17 USC §105, France Loi 78-753, etc. per CLAUDE.md §9).
- [ ] **JS-off rendering:** Playwright with `javaScriptEnabled: false` shows card titles + direct links on every archive root.
- [ ] **Verbatim contract: byte-exact title/desc match pre-migration:** `scripts/verify-fidelity.py` shows zero diffs on the `arch-data` JSON `ti` and `de` fields.
- [ ] **`/api/all.json` schema unchanged:** key set + order byte-identical; `search.html` shows same result count on canonical query.
- [ ] **404 page is the branded one:** `curl -I https://realufo.org/this-does-not-exist` returns the project's `404.html` body (not CF generic).
- [ ] **`/sw.js` served with `Cache-Control: no-cache`:** verified via `curl -I https://realufo.org/sw.js`.
- [ ] **Hamburger toggle works on every archive (mobile viewport):** Playwright test.
- [ ] **Lightbox arrow-keys + swipe nav preserved:** Playwright keyboard + touch tests.
- [ ] **Search `?q=` restore on reload preserved:** Playwright test.
- [ ] **GH Releases CI upload tested end-to-end:** Dry-run a fake `weekly` cron in a feature branch and confirm the new file appears in the per-archive tag, the manifest references it, the deployed Download button serves it.
- [ ] **Workers cron lock prevents overlap:** Force two cron firings; verify only one runs (KV lock honoured).
- [ ] **CF Pages `_headers` precedence verified:** `curl -I /sw.js` shows custom header, not CF default.
- [ ] **DNS TTL dropped to 300 s ≥7 days pre-cutover:** dig record TTL.
- [ ] **Post-cutover 7-day Umami / Lighthouse monitoring window:** stable LCP/CLS, no SW-error spike.
- [ ] **Akamai-egress spike completed before deciding cron home:** documented HTTP status comparison Workers-vs-Actions for war.gov, aaro.mil.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| SW poisoning post-cutover | MEDIUM | (1) Deploy a new `sw.js` with bumped cache-name + cleaner activate that `caches.keys() → caches.delete()`. (2) Post a banner on the site instructing returning users to "fully reload (Ctrl+Shift+R) once" or wait 24 h. (3) Monitor Umami for traffic returning to expected pages. |
| URL drift dropping inbound traffic | LOW (if 301s added quickly) → HIGH (if Google de-indexes) | Add missing 301s to `_redirects`. Resubmit sitemap to Google Search Console. Re-crawl can take 2–4 weeks. |
| Akamai blocking Workers egress | LOW (revert to Actions for blocked sources) | Move blocked sources back to GH-Actions runner with `curl_cffi`. Update worker to skip these and emit a no-op success. |
| `gh release upload --clobber` wiped a binary | LOW (if local copy exists) → MEDIUM (if not) | Re-run scrape to re-fetch from source. If source is dead, try Wayback CDX. Worst case: announce missing binary in CHANGELOG. |
| Content fidelity broken (mojibake) | HIGH (if shipped to prod) | Roll back deploy. Re-run `verify-fidelity.py`. Fix encoding/typographer settings. Re-migrate. |
| CF Pages 404 returning generic page | LOW | Ensure `dist/404.html` exists (not `dist/404/index.html`). Re-deploy. |
| Workers cron timeout / runaway cost | LOW | Disable cron via `wrangler.toml`; shift to GH Actions. Investigate offline. |
| Per-archive visual regression discovered post-cutover | LOW–MEDIUM | Hot-patch the offending CSS variable / component. Add visual-regression snapshot to prevent recurrence. |
| Public-domain attribution accidentally dropped | LOW (text) / HIGH (legal-risk on a non-US source) | Hot-patch footer. Audit all 15 footers in same PR. |
| 1000-asset-per-tag hit | MEDIUM | Roll out per-archive tags; update `release-manifest.json`; coordinate `gh release` migrations so Download buttons keep working. |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1. SW cache poisoning at cutover | **Phase: Pre-cutover prep** (deregister SW on old origin) + **Cutover** (new cache-name prefix) | Lighthouse + DevTools on returning-user profile; Umami stable post-cutover |
| 2. URL drift | **Phase: Migration scaffolding** (build `URL-CONTRACT.txt`) + CI gate | `scripts/verify-redirects.sh` green on preview deploy |
| 3. Akamai blocks Workers egress | **Phase: Research-spike** (egress comparison) + **Scrape-migration** (hybrid architecture) | Content-fingerprint gate doesn't detect block-page response |
| 4. Verbatim text auto-formatted | **Phase: SSG scaffolding (very early)** (pick non-markdown path) + **Migration** (`verify-fidelity.py` gate) | Byte-exact `arch-data` JSON diff = zero |
| 5. GH Releases `--clobber` + 1000 ceiling | **Phase: Scrape-automation** (per-archive tags, delete-then-upload helper) + **Scaling** (tag rotation) | CI dry-run confirms idempotent re-runs |
| 6. JSON-split network waterfall | **Phase: Perf-budget scaffolding** (Lighthouse budgets) + **PERF-01 refactor** (shard not atomise) | LCP/TTI not regressed vs current |
| 7. Cross-archive consistency drift | **Phase: CI scaffolding** (Playwright snapshots of current `main`) + **Migration per-archive PR** | Visual-regression CI green across 15 archives × 4 viewports |
| 8. CF Pages `_redirects`/`_headers` syntax | **Phase: Cloudflare scaffolding** | curl-based redirect verification suite |
| 9. Offline-first regression / JS-off | **Phase: SSG decision** + **Phase: Offline** | Playwright JS-off test + chunked SHELL precache |
| 10. Workers cron retry storms / KV rate limit | **Phase: Scrape-worker design** + **Stabilisation** | Forced-overlap cron test honours lock |
| 11. Mobile-first regression | **Phase: CI scaffolding** + **Migration QA** | Playwright 360 px × Lighthouse mobile preset |
| 12. Public-domain attribution dropped | **Phase: Migration QA** | Per-archive licence text test |
| 13. GA ↔ CF ↔ Releases coordination | **Phase: Scrape-automation design** + **Post-cutover hardening** | End-to-end dry run in feature branch |
| 14. Wayback hardcoded year | **Phase: Scrape-migration** | Test against known-dead source uses CDX dynamic fallback |
| 15. DNS TTL not dropped early | **Phase: Cutover-prep checklist (T-7 days)** | `dig +noall +answer realufo.org` TTL ≤300 a week pre-cutover |
| 16. `/api/all.json` schema drift | **Phase: Migration verification** | Schema-fingerprint + search smoke test |

---

## Sources

### Verified — official documentation (HIGH confidence)
- [Cloudflare Pages — Serving Pages (404.html / _redirects / _headers)](https://developers.cloudflare.com/pages/configuration/serving-pages/)
- [Cloudflare Workers — Limits](https://developers.cloudflare.com/workers/platform/limits/)
- [Cloudflare Workers KV — Limits (1 write/sec/key documented)](https://developers.cloudflare.com/kv/platform/limits/)
- [Cloudflare Workers — Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/)
- [MDN — Using Service Workers (scope, register, updateViaCache)](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers)
- [GitHub Docs — REST API rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [GitHub Docs — Pages limits (100 GB soft bandwidth)](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
- [GitHub Docs — Actions concurrency](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency)
- [GitHub CLI Issue cli/cli#4863 — `release upload --clobber` deletes before upload](https://github.com/cli/cli/issues/4863)
- [GitHub CLI Issue cli/cli#4270 — `gh release create` race produces partial drafts](https://github.com/cli/cli/issues/4270)
- [Astro Issue #6177 — Custom 404 doesn't load on Cloudflare Pages](https://github.com/withastro/astro/issues/6177)
- [Astro Issue #4538 — Accented characters in markdown frontmatter mangled](https://github.com/withastro/astro/issues/4538)
- [Astro Issue #4695 — Incorrect encoding for frontmatter via Astro.glob](https://github.com/withastro/astro/issues/4695)
- [Astro Issue #2187 — Apostrophes become `â€™` in raw markdown](https://github.com/withastro/astro/issues/2187)

### Verified — community / migration write-ups (MEDIUM confidence)
- [How to Move from GitHub Pages to Cloudflare Pages (martinuke0.github.io)](https://martinuke0.github.io/posts/2025-12-06-how-to-move-from-github-pages-to-cloudflare-pages/)
- [Cloudflare Pages to Workers Migration with Zero-Downtime Domain Switchover](https://vibecodingwithfred.com/blog/pages-to-workers-migration/)
- [Stuck in Cache Hell — A Service Worker Nightmare (Medium)](https://medium.com/@ankit-kaushal/stuck-in-cache-hell-a-service-worker-nightmare-c878ae33abf4)
- [Service Worker Lifecycle Explained (Felix Gerschau)](https://felixgerschau.com/service-worker-lifecycle-update/)
- [Cloudflare Community — _redirects infinite loop detection](https://community.cloudflare.com/t/cloudflare-pages-redirects/816132)
- [Cloudflare Community — 404 _headers not activating on SPA](https://community.cloudflare.com/t/404-error-on-spa-routes-dashboard-pages-headers-rule-not-activating/869055)
- [Cloudflare Community — Unexpected Long Worker Execution Times in Cron Trigger](https://community.cloudflare.com/t/unexpected-long-worker-execution-times-when-using-browser-rendering-in-cron-trigger/777333)
- [Workbox Issue #2692 — SW stuck in busy state when SSE hits cache](https://github.com/GoogleChrome/workbox/issues/2692)

### Akamai bot-detection landscape (MEDIUM confidence)
- [Scrapfly — How to Bypass Akamai when Web Scraping](https://scrapfly.io/blog/posts/how-to-bypass-akamai-anti-scraping)
- [Bright Data — Akamai Bot Detection Bypass Guide](https://brightdata.com/blog/web-data/bypass-akamai-bot-detection)
- [Akamai — Bot Manager / Bot Detection product page](https://www.akamai.com/products/bot-manager)

### Project-internal sources (HIGH confidence)
- `/Users/laichan/code/war-gov-ufo-release/CLAUDE.md` — §1, §3.1, §4.2, §7, §8, §9, §11
- `/Users/laichan/code/war-gov-ufo-release/.planning/PROJECT.md` — Validated/Active requirements + Constraints
- `/Users/laichan/code/war-gov-ufo-release/.planning/codebase/CONCERNS.md` — SW gap on 14 archive subpages; `curl_cffi || true` mask; hardcoded Wayback years; 3.3 MB GEIPAN inline JSON; 4.6 MB `/api/all.json`; 1000-asset-per-tag ceiling
- `/Users/laichan/code/war-gov-ufo-release/.planning/codebase/ARCHITECTURE.md` — current SW scope, drift gates, splice-only `build-wargov.py`

---
*Pitfalls research for: big-bang SSG + CF Pages + Workers-cron + automated GH-Releases migration of an offline-first 15-archive static site*
*Researched: 2026-05-25*
