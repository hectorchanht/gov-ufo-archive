// @ts-check
import { defineConfig } from 'astro/config';
import { fileURLToPath } from 'node:url';
import { resolve as pathResolve, join as pathJoin } from 'node:path';
import { copyFile, unlink, stat } from 'node:fs/promises';
import cloudflare from '@astrojs/cloudflare';
import AstroPWA from '@vite-pwa/astro';

// Phase 4 04-03 deviation [Rule 3 - Blocking issue]:
// The @vite-pwa/astro plugin treats `config.output==='server'` (which the
// @astrojs/cloudflare adapter sets, even with our `output:'static'`) as a
// signal to emit the SW into `dist/_worker.js/sw.js`. CF Pages serves static
// files from `dist/` directly — files under `dist/_worker.js/` are bundled
// into the Worker script, not addressable as `/sw.js`. The plugin's
// `injectManifest.swDest` override is honored by workbox-build, but Vite
// still writes its own intermediate sw.mjs into `dist/_worker.js/`, and
// workbox then reads from swDest (which it expects Vite to have populated).
// The least-invasive escape hatch is a tiny inline Astro integration that
// runs at `astro:build:done` and moves the worker-bundled sw.js out into
// dist/ root where BaseHead.astro's `/sw.js` registration can reach it.
const PROJECT_ROOT = fileURLToPath(new URL('.', import.meta.url));
const DIST_DIR = pathResolve(PROJECT_ROOT, 'dist');
const SW_SOURCE = pathJoin(DIST_DIR, '_worker.js', 'sw.js');
const SW_DEST = pathJoin(DIST_DIR, 'sw.js');

/**
 * Inline integration — moves the SW emitted by @vite-pwa/astro out of the
 * CF adapter's _worker.js/ bundle directory into dist/ root.
 * Must run AFTER AstroPWA in the integrations array.
 */
const swRelocator = {
  name: 'realufo:sw-relocator',
  hooks: {
    'astro:build:done': async () => {
      try {
        await stat(SW_SOURCE);
      } catch {
        // SW wasn't produced at the expected location; nothing to relocate.
        return;
      }
      await copyFile(SW_SOURCE, SW_DEST);
      // Remove the bundle-location copy so the CF Worker can't accidentally
      // execute it (it's meant to run in a browser SW context, not a worker).
      try { await unlink(SW_SOURCE); } catch {}
      const sourceMap = `${SW_SOURCE}.map`;
      const destMap = `${SW_DEST}.map`;
      try {
        await stat(sourceMap);
        await copyFile(sourceMap, destMap);
        await unlink(sourceMap);
      } catch {
        // No sourcemap — fine.
      }
    },
  },
};

// Phase 3 Plan 03-01 — Astro 5.18.x scaffold alongside the legacy Python build.
// Phase 4 Plan 04-03 — adds @vite-pwa/astro injectManifest SW integration.
// See .planning/decisions/astro-version-pin.md for the framework + adapter pin
// rationale, and .planning/phases/03-ssg-foundation/03-CONTEXT.md for the
// D-12..D-39 invariants this config honors. Phase 4 D-18..D-26 + SW-01..07
// drive the AstroPWA() block below.

// D-22 + SW-06 — cache name templated from CI commit SHA at build time.
// Surface to sw.ts via Vite's define mechanism so import.meta.env.COMMIT_SHA
// resolves correctly inside the worker bundle. Falls back to 'dev' locally.
const cacheVersion = process.env.COMMIT_SHA?.slice(0, 7) || 'dev';

export default defineConfig({
  // D-12..D-15: CF Pages serves dist/ as static files; no SSR in Phase 3.
  output: 'static',

  // D-30: @astrojs/cloudflare adapter pinned alongside Astro 5.x. The 12.6.x
  // line declares `astro: ^5.7.0` in peerDependencies so this is the safe
  // family while we stay on the 5.18.x patch line.
  adapter: cloudflare(),

  // D-26..D-28 + research/PITFALLS.md §Pitfall #6 — defend content fidelity.
  // The default Astro markdown pipeline ships with smartypants enabled, which
  // would silently rewrite quotes, dashes, and ellipses in any markdown that
  // touches archive card data. Phase 2 INF-05 fidelity samples (115 records)
  // would fail byte-equality if these rewrites slipped through.
  markdown: {
    smartypants: false,
    remarkPlugins: [],
    rehypePlugins: [],
  },

  // D-23: NO React / Vue / Svelte islands.
  // Phase 4 SW-01 (Plan 04-03): @vite-pwa/astro injectManifest. The plugin
  // emits dist/sw.js by compiling src/sw.ts and replacing self.__WB_MANIFEST
  // with the precache list generated from injectManifest.globPatterns.
  //
  // Reference: vite-pwa-org.netlify.app/frameworks/astro
  // + .planning/phases/04-full-migration-search-offline-performance/04-RESEARCH.md §3
  integrations: [
    AstroPWA({
      // D-18 — injectManifest strategy keeps full SW control (vs generateSW).
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.ts',

      // D-22 — registerType auto-updates the SW on each deploy.
      registerType: 'autoUpdate',

      // D-19 — registration handled manually in BaseHead.astro <script is:inline>
      // so the Phase 1 PMS-02 kill-switch invariant updateViaCache:'none' is set
      // explicitly. Disable plugin's auto-injection to avoid duplicate registers.
      injectRegister: false,

      injectManifest: {
        // [Rule 3 fix] — CF adapter forces server mode, which makes the plugin
        // point globDirectory at dist/_worker.js/ (where only the worker bundle
        // lives). The browser-served static files live at dist/ root, so we
        // pin globDirectory there to make the precache manifest reflect what
        // CF Pages actually serves over HTTP. Without this override, the
        // precache would contain only `index.js` (the CF worker entry) and
        // `manifest.webmanifest`, missing all 14 archive HTMLs + assets.
        globDirectory: DIST_DIR,

        // D-20 — precache every HTML + every thumbnail + Pagefind core (SRC-05).
        // D-04 — PDFs/videos NEVER precached (size-prohibitive; on-demand from R2).
        globPatterns: [
          '**/*.{html,css,js,svg,webp,png,jpg,jpeg,woff2,ico}',
          'pagefind/pagefind*.{js,css}',
        ],
        globIgnores: [
          '**/*.{pdf,mp4,webm,mov,mp3,wav,zip}',
          // Pitfall #1 — never precache the SW itself or its sourcemap; would
          // create an infinite update loop where the SW caches a copy of itself.
          'sw.js',
          'sw.js.map',
          'workbox-*.js',
          // The CF adapter's worker bundle stays out of the static precache.
          '_worker.js/**',
          '_routes.json',
          // Pagefind index shards lazy-loaded on query (SRC-05 — only core precached)
          'pagefind/index/**',
          'pagefind/fragment/**',
        ],
        // CF Pages 25 MiB/file cap — anything larger isn't precacheable anyway.
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
      },

      manifest: {
        name: 'realufo.org — Government UAP Archive',
        short_name: 'realufo',
        description: 'Offline-first archive of every official government UAP source',
        theme_color: '#0a0a0c',
        background_color: '#0a0a0c',
        display: 'standalone',
        icons: [
          { src: '/assets/favicon.svg', sizes: 'any', type: 'image/svg+xml' },
        ],
      },

      // workbox option is unused in injectManifest mode — sw.ts owns runtime config.
      workbox: undefined,
    }),
    // [Rule 3 fix] — relocate the SW out of the CF worker bundle.
    // MUST run after AstroPWA so the SW file exists at the source path.
    swRelocator,
  ],

  // Production canonical (CONTEXT.md §URL structure — wargov stays at /).
  site: 'https://realufo.org',

  // Matches current GH Pages behaviour; _redirects already handles trailing
  // slash 301s (Phase 2 plan 02-05). Setting 'ignore' lets Astro accept both
  // /path and /path/ during the migration coexistence window (D-12..D-14).
  trailingSlash: 'ignore',

  // D-22 + SW-06 — expose COMMIT_SHA to src/sw.ts at build time so the
  // cache-name prefix `realufo-v<sha>` is compiled into the SW bundle.
  // Vite's `define` performs a literal substitution at build time.
  vite: {
    define: {
      'import.meta.env.COMMIT_SHA': JSON.stringify(cacheVersion),
    },
  },
});
