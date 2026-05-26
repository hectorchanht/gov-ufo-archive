// JS invariants per CLAUDE.md §7 (1-8) — source-of-truth string for `<script is:inline>` injection.
//
// D-21..D-23: this string is inlined VERBATIM into RootLayout.astro's bottom-of-body
// `<script is:inline set:html={INVARIANTS_JS}>` block. is:inline guarantees:
//   - no Vite bundler touch (no minification, no module hoisting)
//   - no TypeScript transform (the template body is plain ES2020)
//   - runs as a plain inline script, identical to current index.html behaviour
//
// The TS file itself is a typed export only — it is NEVER imported as runtime JS;
// Astro reads it at build time, extracts the string literal, and emits it inline.
//
// Maintenance rule: every behaviour numbered (1)-(8) below maps to a CLAUDE.md §7
// invariant. If you add a new behaviour, update CLAUDE.md §7 first.

// Inline JS template literal — KEEP this a single string. No TypeScript syntax
// inside the backticks; only ES2020.
export const INVARIANTS_JS: string = String.raw`
(function () {
  'use strict';

  /* (1) CLAUDE.md §7 — Hamburger toggle (mobile nav).
     Wires #nav-toggle ↔ #primary-nav. Click any link inside the open drawer
     to dismiss it. Component-level Nav.astro ships its own copy of this
     handler (defence-in-depth — Nav.astro may render without RootLayout in
     story / preview contexts), so this block is idempotent if both run. */
  var navToggle = document.getElementById('nav-toggle');
  var primaryNav = document.getElementById('primary-nav');
  if (navToggle && primaryNav && !navToggle.dataset.wired) {
    navToggle.dataset.wired = '1';
    navToggle.addEventListener('click', function () {
      var open = primaryNav.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    primaryNav.addEventListener('click', function (e) {
      if (e.target && e.target.tagName === 'A') {
        primaryNav.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* (2) CLAUDE.md §7 — Unified lightbox with prev/next/swipe/arrow-keys/Escape.
     openAt(idx), navLb(delta), closeLb(). Wrap-around via modulo. */
  var lb = document.getElementById('lightbox');
  var lbInner = document.getElementById('lb-inner');
  var lbPrev = document.getElementById('lb-prev');
  var lbNext = document.getElementById('lb-next');
  var lbClose = document.getElementById('lb-close');
  var lbCounter = document.getElementById('lb-counter');

  /* lbList is the array of asset objects the current page renders. Pages
     populate it after their card-render pass (Plan 03-05's wargov index will
     set window.__lbList = assets after pre-rendering the first 50 cards). */
  var lbList = (typeof window !== 'undefined' && window.__lbList) || [];
  var lbIdx = 0;

  function renderLb() {
    if (!lb || !lbInner) return;
    var a = lbList[lbIdx];
    if (!a) { lbInner.innerHTML = ''; return; }
    /* (5) CLAUDE.md §7 — PDF lightbox: iframe ONLY for local files.
       Remote PDFs open in a new tab via Content-Disposition: attachment so
       the user gets a real download instead of an inline render that may
       fail under CSP. Same rule as the legacy index.html @ ~line 1735. */
    var local = a.local || '';
    var remote = a.url || '';
    var target = local || remote;
    var ext = (target || '').toLowerCase().split('?')[0].split('#')[0].split('.').pop();
    if (ext === 'pdf') {
      if (local) {
        lbInner.innerHTML = '<iframe src="' + local + '" title="' + (a.title || 'PDF') + '" loading="lazy"></iframe>';
      } else if (remote) {
        // Remote → new tab (handled by anchor target=_blank); the lightbox
        // shows a metadata panel + Download link as a fallback.
        lbInner.innerHTML = '<div class="lb-meta">Remote PDF — open in new tab.<br><a href="' + remote + '" target="_blank" rel="noopener">Open ' + (a.title || 'PDF') + ' ↗</a></div>';
      }
    } else if (ext === 'mp4' || ext === 'webm' || ext === 'mov') {
      /* (4) CLAUDE.md §7 — Video dual-source.
         Two <source> children when both local + remote exist. NEVER add
         crossorigin="anonymous" (CLAUDE.md §11 — kills cloudfront playback). */
      var srcs = '';
      if (local) srcs += '<source src="' + local + '" type="video/' + ext + '">';
      if (remote && remote !== local) srcs += '<source src="' + remote + '" type="video/' + ext + '">';
      lbInner.innerHTML = '<video controls preload="metadata" playsinline>' + srcs + '</video>';
    } else if (ext === 'mp3' || ext === 'wav' || ext === 'ogg') {
      lbInner.innerHTML = '<audio controls preload="metadata"><source src="' + target + '"></audio>';
    } else {
      /* (3) CLAUDE.md §7 — Image fallback via <img onerror>.
         When local 404s, swap src to the official source URL. */
      var fb = remote ? 'onerror="this.onerror=null;this.src=\'' + remote + '\';"' : '';
      lbInner.innerHTML = '<img src="' + target + '" alt="' + (a.title || '') + '" ' + fb + '>';
    }
    if (lbCounter) lbCounter.textContent = (lbIdx + 1) + ' / ' + lbList.length;
  }

  function openAt(idx) {
    if (!lb) return;
    /* Refresh lbList in case the page mutated it after first paint
       (e.g. filter/sort recomputes lazy-loaded shards). */
    lbList = (window.__lbList && window.__lbList.length) ? window.__lbList : lbList;
    if (!lbList.length) return;
    lbIdx = ((idx % lbList.length) + lbList.length) % lbList.length;
    renderLb();
    lb.classList.add('open');
    lb.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function navLb(delta) {
    if (!lb || !lb.classList.contains('open') || !lbList.length) return;
    lbIdx = ((lbIdx + delta) % lbList.length + lbList.length) % lbList.length;
    renderLb();
  }

  function closeLb() {
    if (!lb) return;
    lb.classList.remove('open');
    lb.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (lbInner) lbInner.innerHTML = '';
  }

  if (lb && lbClose) lbClose.addEventListener('click', closeLb);
  if (lbPrev) lbPrev.addEventListener('click', function (e) { e.stopPropagation(); navLb(-1); });
  if (lbNext) lbNext.addEventListener('click', function (e) { e.stopPropagation(); navLb(1); });
  if (lb) lb.addEventListener('click', function (e) { if (e.target === lb) closeLb(); });

  /* Keyboard: ArrowLeft / ArrowRight / Escape. */
  document.addEventListener('keydown', function (e) {
    if (!lb || !lb.classList.contains('open')) return;
    if (e.key === 'Escape') closeLb();
    else if (e.key === 'ArrowRight') navLb(1);
    else if (e.key === 'ArrowLeft') navLb(-1);
  });

  /* Touch swipe: > 50 px horizontal, < 800 ms = nav. */
  if (lb) {
    var touchX = 0;
    var touchY = 0;
    var touchT = 0;
    lb.addEventListener('touchstart', function (e) {
      if (!e.touches.length) return;
      touchX = e.touches[0].clientX;
      touchY = e.touches[0].clientY;
      touchT = Date.now();
    }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      if (!e.changedTouches.length) return;
      var dx = e.changedTouches[0].clientX - touchX;
      var dy = e.changedTouches[0].clientY - touchY;
      if (Date.now() - touchT < 800 && Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
        navLb(dx < 0 ? 1 : -1);
      }
    }, { passive: true });
  }

  /* (6) CLAUDE.md §7 — data-action="open" delegated click handler.
     Cards emit <a href="#" data-action="open" data-idx="N"> alongside their
     download/source anchors; this listener intercepts ONLY data-action="open"
     and routes to openAt() — every other anchor keeps native behaviour
     (Download, Source ↗, DVIDS ↗). Reads data-idx from the action OR from
     its closest .card ancestor (legacy index.html supports both). */
  document.addEventListener('click', function (e) {
    var action = e.target.closest && e.target.closest('a[data-action="open"]');
    if (!action) return;
    e.preventDefault();
    var raw = action.dataset.idx;
    if (raw === undefined) {
      var card = action.closest('.card');
      raw = card && card.dataset.idx;
    }
    var idx = parseInt(raw, 10);
    if (!isNaN(idx)) openAt(idx);
  });

  /* (3) Image fallback — delegated. Any <img data-fallback="..."> swaps src on
     load failure. Plan 03-05's Card.astro emits data-fallback for every
     thumbnail; this listener fires once per failure, with onerror=null logic
     applied via a Set-tracker so the same image doesn't loop. */
  var fallbackFired = new WeakSet();
  document.addEventListener('error', function (e) {
    var img = e.target;
    if (!img || img.tagName !== 'IMG') return;
    if (fallbackFired.has(img)) return;
    var fb = img.getAttribute('data-fallback');
    if (!fb) return;
    fallbackFired.add(img);
    img.src = fb;
  }, true /* capture phase — error events don't bubble */);

  /* (4) Video dual-source sanity check — at runtime, every <video> that has a
     data-remote attribute but only one <source> child gets a second <source>
     injected. Defensive against any page that forgets the dual-source rule. */
  document.querySelectorAll('video[data-remote]').forEach(function (v) {
    var sources = v.querySelectorAll('source');
    if (sources.length >= 2) return;
    var remote = v.getAttribute('data-remote');
    if (!remote) return;
    var s = document.createElement('source');
    s.setAttribute('src', remote);
    s.setAttribute('type', 'video/' + remote.split('.').pop().toLowerCase());
    v.appendChild(s);
  });

  /* (7) CLAUDE.md §7 — '/' keydown focuses the search input.
     Bail out if the user is already typing in an input/textarea/contenteditable.
     If the page has no search input (Phase 3 wargov per D-24 / checker W4), the
     handler still attaches but the early-return at the top makes it a no-op. */
  document.addEventListener('keydown', function (e) {
    if (e.key !== '/') return;
    var t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || (t.isContentEditable))) return;
    var q = document.querySelector('input[type="search"], input[name="q"], #q, #arch-search');
    if (!q) return;
    e.preventDefault();
    q.focus();
    if (typeof q.select === 'function') q.select();
  });

  /* (8) CLAUDE.md §7 — ?q= URL persistence.
     Phase 3 NOTE (per checker W4): wargov has NO cross-archive search input
     (D-24 defers Pagefind to Phase 4 SRC). This handler queries for the same
     selectors as (7); if no input matches, the early-return makes the whole
     block a no-op. Phase 4 will add the input and this handler activates
     automatically — no code change required at that point.

     Behaviour when an input IS present:
       - On page load: read ?q= and populate the input + dispatch 'input' so
         downstream filter handlers run.
       - On input event: debounced (180 ms) history.replaceState pushing
         ?q=<encoded> while the user types. */
  var qInput = document.querySelector('input[type="search"], input[name="q"], #q, #arch-search');
  if (qInput) {
    try {
      var params = new URLSearchParams(window.location.search);
      var existing = params.get('q');
      if (existing) {
        qInput.value = existing;
        qInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
    } catch (_) { /* malformed URL → ignore */ }

    var qTimer = 0;
    qInput.addEventListener('input', function () {
      window.clearTimeout(qTimer);
      qTimer = window.setTimeout(function () {
        try {
          var u = new URL(window.location.href);
          var v = qInput.value || '';
          if (v) u.searchParams.set('q', v); else u.searchParams.delete('q');
          window.history.replaceState({}, '', u.toString());
        } catch (_) { /* ignore — pushState/replaceState may be disabled */ }
      }, 180);
    });
  }

  /* Expose the lightbox functions for pages that need to call them directly
     (e.g. carousel "click image to open in lightbox" pattern in current
     index.html @ ~line 1637). Names match the legacy IIFE so porting is
     a search-and-replace, not a refactor. */
  window.__lightbox = { openAt: openAt, navLb: navLb, closeLb: closeLb };
})();
`;

// Compile-time sanity — TypeScript can typecheck this without ever running it.
// Astro reads the string via the named export at build time.
export default INVARIANTS_JS;
