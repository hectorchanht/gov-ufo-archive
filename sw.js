/*  realufo.org service worker — KILL-SWITCH (Phase 1 of SSG migration).
 *
 *  DO NOT REMOVE — installed __SW_VERSION__ as part of realufo.org →
 *  Cloudflare Pages migration (Phase 1, see .planning/ROADMAP.md).
 *  Replaced by real SW on cutover (Phase 6).
 *
 *  This file used to be the offline-first versioned-shell SW. As of Phase 1
 *  of the SSG migration, it is intentionally degenerate: it self-deregisters,
 *  nukes every cache from the old SW, and signals all open windows to soft-
 *  reload. Per .planning/research/PITFALLS.md Pitfall #1, this is the only
 *  safe path to a GH-Pages → CF-Pages cutover that does NOT serve returning
 *  users a stale shell against the new origin.
 *
 *  Behaviour (per 01-CONTEXT.md decision D-05 — full nuke):
 *    install   → self.skipWaiting()
 *    activate  → self.registration.unregister()
 *              + caches.keys() → caches.delete(name) for every cache
 *              + clients.matchAll({type:'window'}) → postMessage({type:'sw-killswitch-reload'})
 *              + self.clients.claim()
 *    fetch     → no handler (kill-switch must stop intercepting requests)
 *    message   → no handler (one-shot; pages do not need to send 'skipWaiting')
 *
 *  Coexistence (D-06): replaces the prior /sw.js in-place. Same scope, same
 *  URL. The browser auto-installs over the old SW on next visit. No sidecar
 *  /sw-kill.js. The cache-name tag below uses the prefix `realufo-killswitch-`
 *  so the Phase 6 real SW (with a different prefix) can never collide.
 *
 *  Lifespan (D-07): kill-switch stays installed at the old origin until
 *  Phase 6 cutover. No self-disable timer.
 *
 *  Phase 6 gate (D-08): the 14-day countdown to Phase 6 cutover measures
 *  from the deploy-to-`main` timestamp recorded in
 *  .planning/phases/01-pre-migration-safety/01-05-SUMMARY.md.
 *
 *  Version stamping: scripts/build-sw.py rewrites the __SW_VERSION__
 *  placeholder below with a `<short-sha>-<YYYYMMDD>` stamp on every deploy.
 *  The placeholder MUST stay literal in the source so the stamper is
 *  idempotent and the build can be reproduced.
 */

const VERSION = '915157a-20260525';

// DevTools-identifiable tag. The kill-switch maintains NO caches — this
// constant exists only so a developer reading Application → Cache Storage
// can name the build that ran. After activate runs, no entry should remain.
const KILLSWITCH_TAG = 'realufo-killswitch-' + VERSION;

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    // (1) unregister self — future page loads see no SW controller.
    try {
      await self.registration.unregister();
    } catch (_) { /* best-effort */ }

    // (2) delete every cache (the old realufo-shell-/data-/img- caches
    //     plus any orphans from earlier deploys). NOT only the named ones;
    //     caches.keys() returns all caches in this origin's scope.
    try {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
    } catch (_) { /* best-effort */ }

    // (3) signal every window client to soft-reload so they pick up
    //     the no-controller state immediately. Pages without a listener
    //     ignore this silently — acceptable per D-05.
    try {
      const windows = await self.clients.matchAll({ type: 'window' });
      for (const client of windows) {
        try {
          client.postMessage({ type: 'sw-killswitch-reload', tag: KILLSWITCH_TAG });
        } catch (_) { /* best-effort */ }
      }
    } catch (_) { /* best-effort */ }

    // (4) claim so any controlled tabs see the kill-switch as the active
    //     SW immediately, then unregister applies on next navigation.
    try {
      await self.clients.claim();
    } catch (_) { /* best-effort */ }
  })());
});

// No fetch handler — the kill-switch must NOT intercept requests. After
// activate finishes, the SW is unregistered and the page is no longer
// SW-controlled on the next navigation.

// No message handler — kill-switch is one-shot.
