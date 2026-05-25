# Stack Research

**Domain:** Offline-first static archive (15 content collections, per-page inline JSON up to 3.3 MB) migrating from plain HTML + Python build scripts to SSG + Cloudflare Pages + Workers cron scrape
**Researched:** 2026-05-25
**Confidence:** HIGH — all version numbers and Cloudflare limits verified against official docs published April–May 2026

---

## Headline Recommendation

**Use Astro 5.x (NOT 6.x) + injectManifest service worker via `@vite-pwa/astro` + Cloudflare Pages (Direct Upload from GitHub Actions) + Cloudflare Workers cron for scrape ingestion → upload to GitHub Releases via Octokit.**

Runner-up: **Eleventy v3.1.5** — viable if Astro 5 still feels too "framework-y"; same shape, less ergonomic for data-driven generation, no zero-JS-by-default story, but plugins are stable and `@vite-pwa/astro`'s job is filled by `eleventy-plugin-pwa` (community).

Rejected: **Hugo** — fastest builder, but Go template language is the wrong abstraction for this codebase's existing Python templating logic, and the maintainer is solo + already fluent in Python/JS, not Go. Build speed is a non-issue at 15 archives / ~10k records — Astro 5 builds 91k pages in ~18 min ([source](https://gautamkhorana.com/blog/static-site-generators-2026-astro-eleventy-hugo-jekyll-gatsby/)), well within Cloudflare Pages' 20-minute build cap.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended (for THIS use case) |
|------------|---------|---------|--------------------------------------|
| **Astro** | **5.x (pin to latest 5.x, do NOT use 6.x)** | Static site generator | Zero-JS-by-default matches CLAUDE.md §1 ("offline by default", "zero build tooling" → keep that ethos, just formalise it). Server-renders cards to HTML so the 3.3 MB GEIPAN inline-JSON disappears. Content Layer API + `file()` loader with custom CSV parser is a direct match for `uap-data.csv`. **Pin to 5.x because Astro 6 broke the Cloudflare adapter prerender** (workerd build environment regression, [astro#15684](https://github.com/withastro/astro/issues/15684)) and shifted Pages deploys toward Workers Assets — both add risk for a solo maintainer migration. |
| **Node.js** | **22 LTS** | Build runtime | Astro 5 requires ≥18.17.1; 22 LTS is the current actively-maintained LTS. Cloudflare Pages auto-detects via `.nvmrc` or env var `NODE_VERSION=22`. |
| **Cloudflare Pages** | n/a (managed) | Hosting + CDN | Free unlimited bandwidth. 25 MiB/file cap is fine (HTML/CSS/JS/thumbnails all <100 KB). 20k file limit on Free plan covers 95 HTML × 15 archives × thumbnails (under 5k total today). 500 builds/month on Free is sufficient — weekly cron + occasional manual = ~10/month. Native `_headers` + `_redirects` files cover service-worker scope, CSP, and cache-control without a build step. |
| **Cloudflare Workers** | Wrangler 4.x | Scrape automation | Cron triggers run at the edge from non-GitHub IPs → defeats Akamai/GH-IP blocks on `war.gov`, `aaro.mil` (current pain point). Paid plan ($5/mo) is required: Free's 10 ms CPU cap is too tight for HTML parsing; Paid gives 15 min wall-clock + 10k subrequests/invocation (plenty for 15 sources). |
| **GitHub Releases** | n/a (managed) | Binary CDN | Stays as today's CDN. 2 GiB/file, **1000 assets/release tag** (hard limit, [GitHub docs](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)). Per-archive tag strategy already started (`pdfs-v1`, `videos-v1`, `wargov-r02-v1`) — continue per-archive sharding before hitting 1000. |
| **Cloudflare R2** | n/a (managed) | Overflow only | Free tier: 10 GB storage + 1M Class A ops + 10M Class B ops/month + **zero egress**. Use ONLY for files that won't fit GitHub Releases (>2 GiB single file). Don't migrate the bulk — GH Releases is durable public-domain mirror semantics that R2 doesn't replicate. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **`@vite-pwa/astro`** | **^1.x** (current) | Service worker integration | Generates the precache manifest at build time. Use **`injectManifest` strategy, NOT `generateSW`** — you keep your hand-rolled `sw.js` logic (network-first navs, 2xx-only caching from commit `dcbc0d7`, stale-while-revalidate for JSON), Workbox just injects the precache list (`self.__WB_MANIFEST`). Requires Vite 5 + Astro ≥4. |
| **`workbox-precaching`** | **^7.x** | Precache routing | Imported by your custom `sw.ts` to consume `self.__WB_MANIFEST`. Provides `precacheAndRoute()` + `cleanupOutdatedCaches()` for free. |
| **`workbox-routing` + `workbox-strategies`** | **^7.x** | Runtime cache strategies | Optional — use if you want `NetworkFirst`, `StaleWhileRevalidate`, `CacheFirst` as named imports rather than hand-rolled `fetch` handlers. Your current `sw.js` already implements these by hand; either keep the hand-rolled patterns (clearer for solo maintainer) or swap for Workbox primitives (less code, more battle-tested). Recommend: keep hand-rolled, gain only precache manifest injection from Workbox. |
| **`@octokit/rest`** | **^21.x** | GitHub API client | Used inside the Cloudflare Worker to upload scraped assets to GitHub Releases (`gh release upload` equivalent). Octokit works in Workers — it's not Node-dependent ([Octokit Workers note](https://dev.to/opensauced/deploy-a-github-application-to-cloudflare-workers-2gpm)). |
| **`papaparse`** | **^5.x** | CSV → JSON for Astro `file()` loader | The `file()` loader supports JSON/YAML/TOML natively; CSV requires a custom `parser` callback ([Astro docs](https://docs.astro.build/en/reference/content-loader-reference/)). Papaparse is the de-facto JS CSV parser, handles quoting/escaping edge cases that the current Python `csv` module already does for `uap-data.csv`. |
| **`zod`** | **^3.x (4.x in Astro 6)** | Content schema validation | Astro 5 ships Zod 3; Astro 6 bumped to Zod 4. Stay on Zod 3 with Astro 5. Validates each archive's manifest entries at build — turns the silent CSV-format-drift risk (CONCERNS.md §"CSV Source of Truth") into a hard build error. |
| **`cloudflare/wrangler-action@v3`** | **v3.x** | GitHub Actions → Pages deploy | Direct-upload model. Build runs on GitHub Actions (where existing scrape/build Python logic lives during transition); `wrangler pages deploy dist --project-name=realufo` uploads to CF Pages. Avoids CF's native build-bots (which would need to install `poppler-utils`, `curl_cffi`, etc.). |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **Wrangler 4.x CLI** | Workers + Pages dev/deploy | `wrangler dev` for local Worker cron testing; `wrangler pages deploy` for production. Triggers locally via `curl http://localhost:8787/cdn-cgi/handler/scheduled`. |
| **`pnpm` 9.x** | Package manager | Faster + disk-efficient vs npm; better workspace support if the project grows scripts/. Optional — `npm` works fine. |
| **TypeScript 5.x** | Type safety for Worker + Astro components | Astro 5 ships first-class TS; the Worker also benefits from typed `env` bindings via `wrangler types`. The Python `scripts/` stays Python — TS only for new Astro/Worker code. |
| **`@cloudflare/workers-types`** | Worker type definitions | Match the wrangler version. |

---

## Installation

```bash
# Astro project bootstrap
npm create astro@latest -- --template minimal --typescript strict --no-install
# Pin Astro to 5.x in package.json: "astro": "^5"

cd realufo
pnpm add astro@^5
pnpm add -D @vite-pwa/astro@^1 workbox-precaching@^7 workbox-routing@^7 workbox-strategies@^7
pnpm add -D papaparse@^5 @types/papaparse
pnpm add zod@^3

# Worker (separate package)
pnpm create cloudflare scrape-worker -- --type cron --ts
cd scrape-worker
pnpm add @octokit/rest@^21

# Dev/deploy
pnpm add -D wrangler@^4 @cloudflare/workers-types
```

GitHub Actions workflow needs only:

```yaml
- uses: actions/setup-node@v4
  with: { node-version: '22' }
- run: pnpm install --frozen-lockfile
- run: pnpm build  # → dist/
- uses: cloudflare/wrangler-action@v3
  with:
    apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
    command: pages deploy dist --project-name=realufo --branch=main
```

---

## Architecture pattern for the 15 content collections

This is the single most important decision after picking the SSG. Three viable shapes:

### Shape A (RECOMMENDED): One Astro content collection per archive, `file()` loader pointing at per-archive JSON

```ts
// src/content.config.ts
import { defineCollection, z } from 'astro:content';
import { file } from 'astro/loaders';
import Papa from 'papaparse';

const recordSchema = z.object({
  id: z.string(),
  title: z.string(),
  desc: z.string().optional(),
  agency: z.string().optional(),
  category: z.enum(['DOC','VID','AUD','IMG','CATALOG']),
  date: z.string().optional(),
  region: z.string().optional(),
  local: z.string().optional(),
  url: z.string(),
  src: z.string().url(),
  thumb: z.string().optional(),
});

const csvParser = (text: string) =>
  Papa.parse(text, { header: true, skipEmptyLines: true }).data;

export const collections = {
  wargov:    defineCollection({ loader: file('data/wargov.csv', { parser: csvParser }), schema: recordSchema }),
  aaro:      defineCollection({ loader: file('data/aaro.json'), schema: recordSchema }),
  nasa:      defineCollection({ loader: file('data/nasa.json'), schema: recordSchema }),
  geipan:    defineCollection({ loader: file('data/geipan.json'), schema: recordSchema }),
  // … 11 more
};
```

Then `[archive]/index.astro` uses `getStaticPaths` + `paginate()` to emit `/<slug>/index.html`, `/<slug>/page/2/`, etc. Cards are **rendered server-side at build time** (Astro's default). The inline-JSON-in-HTML disappears entirely.

For client-side filter/search UI, ship a single `archive.client.ts` (the current `ARCHIVE_JS`) as a `<script>` element with `is:inline` — it fetches `/<slug>/data.json` (emitted alongside HTML) and rehydrates filter state. Total per-page JS: ~5-10 KB. **This solves PERF-01 completely** (geipan goes from 3.3 MB inline to <50 KB HTML + on-demand JSON shard).

### Shape B: Single combined collection + Astro `paginate()` keyed by archive

Simpler config but loses the per-archive Zod schema differentiation (different archives have different fields). Reject for this use case.

### Shape C: No collections — pure `getStaticPaths` over local JSON

Skips Astro's collection layer. Faster to bootstrap but loses Zod validation. Use only if the migration timeline is critical and you'll add collections in a follow-up.

**Recommendation: Shape A.** Solves the bundle-weight ceiling, formalises the schema (the silent CSV drift risk from CONCERNS.md becomes a `pnpm build` failure), and lets each per-archive build script become a single `[archive]/index.astro` file (replacing ~1,360 lines of `build-aaro.py`).

---

## Service worker pattern

**Keep your hand-rolled `sw.js` logic. Use `@vite-pwa/astro` with `injectManifest` strategy purely to generate the precache manifest at build time.**

```ts
// astro.config.mjs
import { defineConfig } from 'astro/config';
import AstroPWA from '@vite-pwa/astro';

export default defineConfig({
  site: 'https://realufo.org',
  integrations: [
    AstroPWA({
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.ts',
      injectManifest: {
        globPatterns: [
          '**/*.{html,css,js,svg,webp,woff2}',
          // exclude videos + pdfs (they live in GH Releases)
          '!**/pdfs/**',
          '!**/videos/**',
        ],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5 MB hardcap per file
      },
      registerType: 'autoUpdate',
      manifest: { /* webmanifest fields */ },
    }),
  ],
});
```

Then `src/sw.ts`:

```ts
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';

cleanupOutdatedCaches();
precacheAndRoute(self.__WB_MANIFEST); // populated at build time

// ─── keep your existing network-first / SWR / cache-first logic verbatim ───
self.addEventListener('fetch', (event) => { /* port current sw.js */ });
```

**Why this and not `generateSW`:** `generateSW` regenerates the whole worker — you'd lose the careful 2xx-only navigation caching fix (commit `dcbc0d7`) and the per-route strategies. `injectManifest` only fills the `__WB_MANIFEST` placeholder.

**OFFLINE-02 (registration on every archive page):** Astro's `<head>` is a single component (`src/components/Head.astro`) included on every layout. The `<script>` that calls `navigator.serviceWorker.register('/sw.js')` lives there → every archive page gets it automatically. The 12-of-32-pages registration gap from CONCERNS.md is structurally impossible after migration.

---

## Cloudflare-side: scrape pipeline

### Cron Worker pattern

```ts
// scrape-worker/src/index.ts
import { Octokit } from '@octokit/rest';

export interface Env {
  GITHUB_TOKEN: string;
  GITHUB_REPO: string; // "hectorchanht/gov-ufo-archive"
  // bindings to KV for run-state, R2 for staging if needed
}

export default {
  async scheduled(controller: ScheduledController, env: Env, ctx: ExecutionContext) {
    const octokit = new Octokit({ auth: env.GITHUB_TOKEN });
    // 1. fetch source page (Worker IP ≠ GitHub IP → Akamai-friendly)
    // 2. diff against last fingerprint (stored in KV)
    // 3. download new binaries (subrequests: up to 10k/invocation paid plan)
    // 4. octokit.repos.uploadReleaseAsset({ owner, repo, release_id, name, data })
    // 5. POST to GitHub repository_dispatch → triggers Pages rebuild via GH Actions
  },
} satisfies ExportedHandler<Env>;
```

`wrangler.toml`:

```toml
name = "realufo-scrape"
main = "src/index.ts"
compatibility_date = "2026-05-01"

[triggers]
crons = ["0 6 * * *"]  # daily 06:00 UTC

[[kv_namespaces]]
binding = "FINGERPRINTS"
id = "..."
```

### Limits to design within (Paid plan, $5/mo)

| Limit | Value | Headroom for this use case |
|-------|-------|----------------------------|
| CPU time (cron, ≥1 hr interval) | **15 min** | Plenty — HTML parse + diff is sub-second per source. |
| Wall clock | **15 min** | Plenty. |
| Subrequests/invocation | **10,000** (configurable to 10M) | 15 sources × ~50 fetches = 750. Comfortable. |
| Memory | **128 MB** | Plenty — stream binaries, don't buffer. |
| Worker size (compressed) | **10 MB** gzip | Octokit + papaparse + workbox ~1 MB. Comfortable. |
| Cron triggers per account | **250 paid** | Way more than needed. |

**Critical:** Don't try this on the Free plan. Free CPU = 10 ms per invocation; HTML parsing exceeds this. The $5/mo Paid plan is a hard requirement for this pipeline.

### Hybrid split: who runs what

| Job | Runner | Why |
|-----|--------|-----|
| **Scrape source HTML + diff + decide what changed** | Cloudflare Worker cron (daily) | Different IPs from GH Actions → Akamai-friendly. The current `\|\| true`-mask CONCERNS.md flagged is fixed by making this its own short-lived job. |
| **Download new binary assets to R2 staging** | Cloudflare Worker (same invocation, or chained via Queues for >15 min) | Workers can stream binaries to R2 directly. |
| **Upload to GitHub Releases** | Cloudflare Worker (Octokit) OR GitHub Actions triggered via `repository_dispatch` | Octokit-in-Worker works for files ≤~100 MB. For larger PDFs, dispatch to GH Actions which has unlimited file-size + native `gh release upload`. |
| **Rebuild Astro site + deploy to CF Pages** | GitHub Actions (triggered by `repository_dispatch` or commit push from Worker) | Build step needs `papaparse`, `astro`, `pnpm` — GH Actions handles this cleanly with caching. Worker isn't designed to run `astro build`. |
| **Validate (HTML, Lighthouse, lychee, schema)** | GitHub Actions | Existing 6 workflows port over directly. |

**Bottom line:** Worker = ingestion. GH Actions = build + deploy + validate.

---

## Cloudflare Pages limits — verbatim from current docs (May 2026)

| Limit | Free | Pro | Notes |
|-------|------|-----|-------|
| File size (per asset) | **25 MiB** | 25 MiB | HTML/CSS/JS/thumb all fine. Anything over goes to Releases or R2. |
| Files per site | **20,000** | 100,000 | 15 archives × ~500 cards × 1 thumbnail = ~7,500. Headroom. |
| Build timeout | 20 min | 20 min | Astro 5 builds 91k pages in ~18 min — we're at ~10k records, so ~2 min builds expected. |
| Builds/month | **500** | 5,000 | ~30/month (daily cron + manual) easily fits Free. |
| Concurrent builds | 1 | 5 | Single-maintainer doesn't need parallel builds. |
| `_headers` rules | 100 | 100 | Use for: SW scope, CSP, immutable cache on hashed assets, no-cache on `sw.js`. |
| `_redirects` static | 2,000 | 2,000 | Plenty for path rewrites if needed during migration. |
| Custom domains/project | 100 | 250 | One domain (`realufo.org`). |

[Source: developers.cloudflare.com/pages/platform/limits](https://developers.cloudflare.com/pages/platform/limits/)

**Pages → Workers migration noise (2026):** Cloudflare is nudging users toward "Workers Static Assets" instead of Pages. For a pure-static site with no SSR, **stay on Pages** — it's still fully supported, the deployment story is simpler, and the official Astro guide still recommends it. Only consider Workers Assets if/when you need to colocate the scrape Worker with the static deploy.

---

## Bundle weight reduction strategy

The current 3.3 MB inline-JSON ceiling is the most concrete pain. Astro 5 + Shape A above solves it three ways:

1. **Server-render the card list at build time.** Each card becomes static `<article>` HTML in the page. No client-side rendering needed for initial paint. Lightbox/filter UI uses progressive enhancement.
2. **Externalise the data shard.** Emit `/<archive>/data.json` (one per archive) alongside the HTML. The client-side filter/search code fetches it lazily (after first paint). Service worker caches it stale-while-revalidate. The HTML itself stays under 100 KB.
3. **Per-archive sharding of `api/all.json`.** The current 4.6 MB combined index becomes 15 × ~300 KB shards. `search.html` lazy-loads only the shards a query touches (or all, but with HTTP/2 multiplexing).

**Target per-page weight (after migration):**
- HTML: ≤ 80 KB (down from 3.3 MB on geipan, 479 KB on root)
- Critical CSS: ≤ 20 KB inline (Astro auto-extracts)
- JS: ≤ 15 KB (filter/lightbox shared, deduped across archives)
- Total above-the-fold transfer: ≤ 120 KB

This is well below CLAUDE.md §1's spirit ("offline by default", "mobile-first @ 360 px") and the original spec's PERF-01 target of ≤500 KB.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Astro 5 | **Eleventy v3.1.5** | If the team prefers Nunjucks/Liquid templates and wants the most JAMstack-flavoured workflow. Eleventy has no zero-JS-by-default narrative (it ships zero JS regardless — there's no client framework concept), simpler mental model, but pagination performance on thousands of items is slower than Astro 5 ([Eleventy went 54s → 17s on a perf-tuned build](https://www.11ty.dev/docs/pagination/)). No first-class TypeScript. Plugin ecosystem mature but smaller than Astro's. **Pick if you regret Astro's complexity within 2 weeks of starting.** |
| Astro 5 | **Hugo 0.155.1** | If build speed is the dominant constraint (10k pages <1 sec). Hugo wins decisively. **Reject for this project** because: (a) Go template language is a hard pivot from existing Python templating logic; (b) solo maintainer has Python+JS fluency, not Go; (c) no zero-JS-island story for the filter/search UI that needs a tiny progressive-enhancement script; (d) reusing the current `templates/i18n.py`, `templates/nav.py` logic is impossible (rewrite from scratch). |
| Astro 5 | **Next.js 15 `output: 'export'`** | Reject. Heavy framework for a static archive, React baggage, ~80 KB client JS minimum per route. Mobile-first @ 360 px takes a real hit. |
| Astro 5 | **Astro 6.x** | Avoid until Cloudflare adapter prerender regression ([issue #15684](https://github.com/withastro/astro/issues/15684)) is resolved AND for at least 3 months after a Cloudflare-compatible patch lands. Astro 5 is the boring-and-stable choice. Revisit at next milestone. |
| Cloudflare Pages | **Cloudflare Workers Static Assets** | If/when you want the scrape Worker and the site colocated under one Worker. Adds complexity now; doesn't add value yet. Defer to a future milestone. |
| Cloudflare Pages | **Netlify free tier** | Netlify free is 100 GB bandwidth/month + 300 build min — tight for a public archive that could go viral once. CF Pages free is *unlimited* bandwidth. No comparison. |
| Cloudflare Pages | **GitHub Pages** (status quo) | Status quo. Reject because: (a) no Workers cron → can't fix Akamai blocks; (b) bandwidth caps (100 GB soft); (c) no R2 escape hatch for >2 GB files. |
| Cloudflare Workers cron | **GitHub Actions cron** (status quo) | Status quo. Reject because GH Actions runners share IP ranges Akamai/CDN-fronted gov sites already block — the precise pain point that triggered SCRAPE-03. |
| GitHub Releases | **Cloudflare R2 (primary)** | Reject for primary storage. GH Releases gives durable public-domain mirror semantics with citable URLs; R2 is private-by-default object storage. Use R2 only for **overflow** (files >2 GiB single-asset GH limit). |
| `injectManifest` SW | **`generateSW`** (Workbox auto-generated) | If you want zero custom SW logic and accept Workbox's default strategies. Reject because the existing `sw.js` has hand-tuned 2xx-only nav caching (commit `dcbc0d7`) — losing that re-opens a fixed bug. |
| `injectManifest` SW | **Hand-rolled SW (status quo)** | Reject for migration. The current `sw.js` requires `scripts/build-sw.py` to stamp a version SHA, and the precache list is hand-maintained — both are drift surfaces. Workbox's `__WB_MANIFEST` injection auto-generates the precache list from the build output and Workbox's `cleanupOutdatedCaches()` replaces the manual SHA-stamp invalidation. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Astro 6.x (May 2026)** | Cloudflare adapter prerender broke in v6 ([astro#15684](https://github.com/withastro/astro/issues/15684)); workerd build env is too restrictive; Zod 4 bump increases migration surface. | **Astro 5.x** — pin major version in `package.json`. Revisit Astro 6 at next milestone. |
| **`generateSW` strategy** | Throws away your hand-rolled SW logic, including the 2xx-only nav-caching fix. | **`injectManifest`** — keep your `sw.ts`, get auto-generated precache list. |
| **Cloudflare Pages built-in build (auto-deploy from git)** | Forces dependency install in CF's build container; harder to install `poppler-utils`, `librsvg2-bin`, `curl_cffi`, custom Python tools during the transition. | **GitHub Actions + `wrangler pages deploy`** (Direct Upload). You control the build env. |
| **Cloudflare Workers Free plan for scrape** | 10 ms CPU per invocation is too tight for HTML parsing + diff. | **Workers Paid ($5/mo)** — 15 min CPU on cron, 10k subrequests. |
| **Inline `<script type="application/json">` for collections >100 KB** | Defeats the entire reason for this migration. Re-opens the PERF-01 pain. | **Per-archive `/<slug>/data.json` shards** fetched lazily by the filter UI; SW caches stale-while-revalidate. |
| **`os.listdir` (Python) or `import.meta.glob` (Vite) for LOCAL badge detection** | Picks up gitignored files → Download buttons 404 in production. CLAUDE.md §6.2 + ARCHITECTURE.md Anti-Patterns. | **`git ls-files` shell-out from the Astro data loader** (or pre-bake a `tracked-files.json` in the GH Actions step before `astro build`). |
| **Single combined `release-manifest.json` at build time only** | OK today, but doesn't survive the Worker-side scrape pipeline. | **Append-only updates from the Worker after each successful `uploadReleaseAsset` call**, committed back to the repo via `repository_dispatch` payload or direct Contents API push. |
| **Hugo + Go templates** | Solo Python+JS maintainer; rewriting 7 template modules from scratch. | **Astro** — TypeScript/JSX-flavoured `.astro` files port more cleanly from current `templates/*.py` mental model. |
| **`@octokit/rest` for files >50 MB inside a Worker** | Octokit buffers the asset; 128 MB Worker memory cap. | **Stream to R2 first, then trigger GitHub Actions via `repository_dispatch` to do the actual `gh release upload`** for large files. |
| **A new third font / Google Fonts beyond current 2** | CLAUDE.md §3.3 bans this. | Source Serif 4 + JetBrains Mono only. Self-host both via `@fontsource/source-serif-4` + `@fontsource/jetbrains-mono` so the site truly works offline (current setup loads Google Fonts at runtime — broken offline). |

---

## Stack Patterns by Variant

**If you start hitting Astro 5 build times > 5 minutes:**
- Profile with `ASTRO_TIMING=verbose astro build`
- Most likely cause: Zod schema validation on a 10k-record collection. Cache the parsed CSV → JSON in `node_modules/.astro` between CI runs.
- Last resort: skip Astro collections for the largest archives, use raw `Astro.glob()` or `import` of pre-built JSON.

**If the scrape Worker exceeds 15 min wall clock:**
- Move to Cloudflare Workflows (durable, multi-step, [docs](https://developers.cloudflare.com/workflows/reference/limits/)) — same Worker model, but state-resumable across multiple 15-min CPU slices.
- Or: split per-archive into N independent Workers, each with its own cron offset.

**If GH Release per-tag asset count approaches 1000:**
- Per-archive tag (already started: `aaro-v1`, `geipan-v1`).
- Then: per-archive per-year tag (`aaro-2025`, `aaro-2026`).
- Last resort: migrate the affected archive to R2 (keeps zero-egress, breaks GH-Releases-as-citable-mirror semantics).

**If you find Astro 5 too "framework-y" after 2 weeks:**
- Eleventy v3.1.5 is the runner-up. Migration cost: rewriting `.astro` files to `.njk` Nunjucks templates (relatively mechanical). Lose: type safety, components. Keep: 80% of the gains.

---

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `astro@^5` | `@vite-pwa/astro@^1` | Both require Vite 5. |
| `astro@^5` | `node@^20 \|\| ^22` | Astro 5 min is 18.17.1; 22 LTS recommended. Astro 6 will require 22+. |
| `astro@^5` | `zod@^3` | Astro 6 bumps to Zod 4 — stay on 3 for now. |
| `@vite-pwa/astro@^1` | `workbox-*@^7` | Workbox 7 is the current major. |
| `wrangler@^4` | `@cloudflare/workers-types@^4` | Match minor versions. |
| `@octokit/rest@^21` | Workers runtime (no Node compat needed) | Octokit core is fetch-based; works natively. |
| Cloudflare Pages | `_headers` v1 syntax | Stable, no version. |

**Single biggest version risk:** Astro 6 broke the Cloudflare adapter ([#15684](https://github.com/withastro/astro/issues/15684)) AND is in active development. Pin `astro` to `~5.x.y` (NOT `^5`) in package.json to prevent accidental Astro 6 upgrades during a `pnpm update`.

---

## Sources

**Cloudflare (HIGH confidence — official docs):**
- [Cloudflare Pages Limits](https://developers.cloudflare.com/pages/platform/limits/) — file size 25 MiB, files 20k free / 100k paid, build timeout 20 min, builds 500/mo free
- [Cloudflare Workers Limits](https://developers.cloudflare.com/workers/platform/limits/) — CPU 10 ms free / 15 min cron paid, 128 MB memory, 10 MB script size
- [Cloudflare Workers Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/) — `scheduled()` handler, wrangler.toml syntax
- [Cloudflare R2 Pricing](https://developers.cloudflare.com/r2/pricing/) — 10 GB free, zero egress
- [Cloudflare changelog: Pages file limit raised to 100k for paid plans (2026-01-23)](https://developers.cloudflare.com/changelog/post/2026-01-23-pages-file-limit-increase/)
- [Cloudflare changelog: Workers subrequest limit raised from 1000 (2026-02-11)](https://developers.cloudflare.com/changelog/post/2026-02-11-subrequests-limit/)
- [Cloudflare Pages Headers](https://developers.cloudflare.com/pages/configuration/headers/) — `_headers` rules limit 100, header size 2000 chars
- [Cloudflare Pages + Astro framework guide](https://developers.cloudflare.com/pages/framework-guides/deploy-an-astro-site/)

**Astro (HIGH confidence — official docs/releases):**
- [Astro Content Collections](https://docs.astro.build/en/guides/content-collections/) — `file()` loader, Zod schemas
- [Astro Content Loader API](https://docs.astro.build/en/reference/content-loader-reference/) — custom CSV parser pattern
- [Astro releases on GitHub](https://github.com/withastro/astro/releases) — current version 6.3.7, but pin to 5.x
- [astro#15684 — v6 Cloudflare prerendering regression](https://github.com/withastro/astro/issues/15684) — reason to pin Astro 5

**Eleventy (HIGH confidence — official):**
- [Eleventy v3.0.0 release notes](https://github.com/11ty/eleventy/releases/tag/v3.0.0) — ESM-first, CJS still works
- [`@11ty/eleventy` on npm](https://www.npmjs.com/package/@11ty/eleventy) — current 3.1.5

**Hugo (HIGH confidence — official):**
- [Hugo on gohugo.io](https://gohugo.io/) — current 0.155.1 (2026), streaming builds
- [Cloudflare Pages + Hugo guide](https://developers.cloudflare.com/pages/framework-guides/deploy-a-hugo-site/)

**Service Workers / PWA (HIGH confidence — official):**
- [Workbox precaching docs](https://developer.chrome.com/docs/workbox/precaching-with-workbox)
- [`@vite-pwa/astro`](https://github.com/vite-pwa/astro) — zero-config Astro PWA
- [Vite PWA injectManifest guide](https://vite-pwa-org.netlify.app/guide/inject-manifest)

**GitHub Releases (HIGH confidence — official):**
- [GitHub Releases asset limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) — 2 GiB/file, 1000 assets/release

**Comparison/analysis (MEDIUM confidence — independent blog posts, cross-referenced where possible):**
- [Static Site Generators in 2026: Astro vs Next.js vs Hugo](https://blended-html.com/learn/static-site-generators-guide/) — independent comparison, May 2026
- [Astro vs Eleventy vs Hugo 2026 (Gautam Khorana blog)](https://gautamkhorana.com/blog/static-site-generators-2026-astro-eleventy-hugo-jekyll-gatsby/) — independent comparison, build speed data
- [Best Static Site Generators 2026 — The Software Scout](https://thesoftwarescout.com/best-static-site-generators-2026-astro-next-js-hugo-more/) — independent comparison

---

*Stack research for: offline-first static archive (15 collections) migrating from custom Python build → SSG + Cloudflare Pages + Workers cron*
*Researched: 2026-05-25 by gsd:research / project-researcher agent*
*Overall confidence: HIGH (all version numbers and Cloudflare limits verified against official docs current as of May 2026)*
