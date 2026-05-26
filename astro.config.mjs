// @ts-check
import { defineConfig } from 'astro/config';
import cloudflare from '@astrojs/cloudflare';

// Phase 3 Plan 03-01 — Astro 5.18.x scaffold alongside the legacy Python build.
// See .planning/decisions/astro-version-pin.md for the framework + adapter pin
// rationale, and .planning/phases/03-ssg-foundation/03-CONTEXT.md for the
// D-12..D-39 invariants this config honors.
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

  // D-23: NO React / Vue / Svelte islands. NO @vite-pwa/astro until Phase 4
  // SW-01. Keep the integrations list empty until a specific plan opens it.
  integrations: [],

  // Production canonical (CONTEXT.md §URL structure — wargov stays at /).
  site: 'https://realufo.org',

  // Matches current GH Pages behaviour; _redirects already handles trailing
  // slash 301s (Phase 2 plan 02-05). Setting 'ignore' lets Astro accept both
  // /path and /path/ during the migration coexistence window (D-12..D-14).
  trailingSlash: 'ignore',
});
