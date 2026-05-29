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
  /* Scope pivot 2026-05-28 — meta panel + dual action buttons. */
  var lbMeta = document.getElementById('lb-meta');
  var lbActions = document.getElementById('lb-actions');
  var lbDownload = document.getElementById('lb-download');
  var lbSource = document.getElementById('lb-source');
  /* Operator 2026-05-29 — rotate + fullscreen buttons always-on. */
  var lbRotate = document.getElementById('lb-rotate');
  var lbFullscreen = document.getElementById('lb-fullscreen');

  /* lbList is the array of asset objects the current page renders. Pages
     populate it after their card-render pass (Plan 03-05's wargov index will
     set window.__lbList = assets after pre-rendering the first 50 cards).
     Scope pivot 2026-05-28: each entry now MAY carry desc/agency/date/region/
     category/source/type alongside the original rowId/title/url/local. Missing
     fields render as empty (no broken DOM). */
  var lbList = (typeof window !== 'undefined' && window.__lbList) || [];
  var lbIdx = 0;

  function _escAttr(s) {
    /* Minimal attribute escape — used when writing user-controlled strings
       into innerHTML below. The cards' dataset values arrive HTML-escaped
       already (Astro auto-escapes; Python's html.escape mirrors), but we
       re-escape on the lightbox side defensively. */
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function _hideBtn(el) {
    if (!el) return;
    el.setAttribute('aria-hidden', 'true');
    el.setAttribute('hidden', '');
    el.setAttribute('href', '#');
  }

  function _showBtn(el, href, opts) {
    if (!el) return;
    el.removeAttribute('aria-hidden');
    el.removeAttribute('hidden');
    el.setAttribute('href', href);
    if (opts && opts.download) el.setAttribute('download', '');
    else el.removeAttribute('download');
    if (opts && opts.newTab) {
      el.setAttribute('target', '_blank');
      el.setAttribute('rel', 'noopener');
    }
  }

  function renderMeta(a) {
    if (!lbMeta) return;
    var parts = [];
    if (a.title) parts.push('<h3>' + _escAttr(a.title) + '</h3>');
    if (a.desc) parts.push('<p>' + _escAttr(a.desc) + '</p>');
    var rows = [];
    if (a.agency) rows.push('<dt>Agency</dt><dd>' + _escAttr(a.agency) + '</dd>');
    if (a.date) rows.push('<dt>Date</dt><dd>' + _escAttr(a.date) + '</dd>');
    if (a.region) rows.push('<dt>Region</dt><dd>' + _escAttr(a.region) + '</dd>');
    if (a.category) rows.push('<dt>Category</dt><dd>' + _escAttr(a.category) + '</dd>');
    else if (a.type) rows.push('<dt>Type</dt><dd>' + _escAttr(a.type) + '</dd>');
    if (rows.length) parts.push('<dl>' + rows.join('') + '</dl>');
    lbMeta.innerHTML = parts.join('');
  }

  function renderActions(a) {
    /* "Download from realufo" — prefers local file path; falls back to
       data-url (R2 custom-domain URL for ported archives, or the official
       source URL for legacy rows). Hidden when neither is present. */
    var downloadHref = a.local || a.url || '';
    if (downloadHref) {
      _showBtn(lbDownload, downloadHref, { download: true });
    } else {
      _hideBtn(lbDownload);
    }
    /* "View on source" — official archive page URL (a.s in CatalogCard,
       war.gov for wargov rows). Hidden when no source URL is known. */
    var sourceHref = a.source || '';
    if (sourceHref) {
      _showBtn(lbSource, sourceHref, { newTab: true });
    } else {
      _hideBtn(lbSource);
    }
  }

  function renderLb() {
    if (!lb || !lbInner) return;
    var a = lbList[lbIdx];
    if (!a) { lbInner.innerHTML = ''; if (lbMeta) lbMeta.innerHTML = ''; return; }
    /* (5) CLAUDE.md §7 — PDF lightbox: iframe ONLY for local files.
       Remote PDFs open in a new tab via Content-Disposition: attachment so
       the user gets a real download instead of an inline render that may
       fail under CSP. Same rule as the legacy index.html @ ~line 1735. */
    var local = a.local || '';
    var remote = a.url || '';
    var target = local || remote;
    var ext = (target || '').toLowerCase().split('?')[0].split('#')[0].split('.').pop();
    var assetType = (a.type || '').toUpperCase();

    if (assetType === 'CATALOG') {
      /* CLAUDE.md §4.3 — CATALOG cards point at the official archive
         landing page. No inline render; meta panel + Source button do the
         work. innerHTML cleared so previous asset doesn't bleed through. */
      lbInner.innerHTML = '<div class="lb-catalog-note">Catalog gateway — see Source button.</div>';
    } else if (assetType === 'CASE' || assetType === 'PAGE' || ext === 'html') {
      /* Long-form text rendering — legacy /aaro/cases/*.html or /aaro/pages/
         *.html. Iframe loads the static HTML page (same-origin so no
         sandbox restriction). When only a remote URL exists, defer to the
         meta panel + Source button (cross-origin iframe would be blocked
         by X-Frame-Options on most government sites). */
      if (local || (remote && remote.indexOf('://') === -1)) {
        lbInner.innerHTML = '<iframe src="' + _escAttr(target) + '" title="' + _escAttr(a.title || 'Page') + '" loading="lazy"></iframe>';
      } else {
        lbInner.innerHTML = '<div class="lb-catalog-note">External page — see Source button.</div>';
      }
    } else if (ext === 'pdf') {
      /* Plan 04-UAT 2026-05-28: iframe local AND R2 (assets.realufo.org)
         PDFs — R2 serves Content-Type: application/pdf inline so the
         browser PDF reader renders. Only true cross-origin remote PDFs
         (e.g. github.com release URLs with Content-Disposition: attachment)
         fall through to the "open in new tab" hint. CLAUDE.md §7
         invariant #5 was authored under the legacy GH-Releases-only
         binary CDN — Phase 4 D-01 moved PDFs to R2, which is iframable. */
      var iframable = !!local;
      if (!iframable && remote && remote.indexOf('assets.realufo.org') !== -1) {
        iframable = true;
      }
      if (iframable) {
        lbInner.innerHTML = '<iframe src="' + _escAttr(target) + '" title="' + _escAttr(a.title || 'PDF') + '" loading="lazy"></iframe>';
      } else if (remote) {
        lbInner.innerHTML = '<div class="lb-meta">Remote PDF — open in new tab.<br><a href="' + _escAttr(remote) + '" target="_blank" rel="noopener">Open ' + _escAttr(a.title || 'PDF') + ' ↗</a></div>';
      } else {
        lbInner.innerHTML = '';
      }
    } else if (ext === 'mp4' || ext === 'webm' || ext === 'mov') {
      /* (4) CLAUDE.md §7 — Video dual-source.
         Two <source> children when both local + remote exist. NEVER add
         crossorigin="anonymous" (CLAUDE.md §11 — kills cloudfront playback).
         Operator spec 3 (2026-05-29) — autoplay on open. Muted is REQUIRED
         for iOS Safari autoplay to fire without a user gesture; the user
         can unmute via the controls. playsinline keeps iOS in-page. */
      var srcs = '';
      if (local) srcs += '<source src="' + _escAttr(local) + '" type="video/' + ext + '">';
      if (remote && remote !== local) srcs += '<source src="' + _escAttr(remote) + '" type="video/' + ext + '">';
      lbInner.innerHTML = '<video controls autoplay muted preload="metadata" playsinline>' + srcs + '</video>';
    } else if (ext === 'mp3' || ext === 'wav' || ext === 'ogg') {
      lbInner.innerHTML = '<audio controls preload="metadata"><source src="' + _escAttr(target) + '"></audio>';
    } else if (target) {
      /* (3) CLAUDE.md §7 — Image fallback via <img onerror>.
         When local 404s, swap src to the official source URL.
         Operator spec 2 (2026-05-29) — reuse the already-rendered card
         thumbnail URL when present so the browser can hit its memory/disk
         cache (200 from cache) instead of refetching. We prefer the card's
         thumb URL (a.thumb) when it matches the image extension; the
         official remote URL stays as the onerror fallback. */
      var imgSrc = target;
      if (a.thumb && (ext === 'jpg' || ext === 'jpeg' || ext === 'png' || ext === 'webp' || ext === 'gif' || !ext)) {
        imgSrc = a.thumb;
      }
      var fb = remote ? 'onerror="this.onerror=null;this.src=\'' + _escAttr(remote) + '\';"' : '';
      lbInner.innerHTML = '<img src="' + _escAttr(imgSrc) + '" alt="' + _escAttr(a.title || '') + '" ' + fb + '>';
    } else {
      /* No URL at all — meta-only render (CATALOG without a download). */
      lbInner.innerHTML = '';
    }

    renderMeta(a);
    renderActions(a);
    if (lbCounter) lbCounter.textContent = (lbIdx + 1) + ' / ' + lbList.length;
  }

  function openAt(rowIdOrIdx) {
    if (!lb) return;
    /* Refresh lbList in case the page mutated it after first paint
       (e.g. filter/sort recomputes lazy-loaded shards). */
    lbList = (window.__lbList && window.__lbList.length) ? window.__lbList : lbList;
    if (!lbList.length) return;
    /* Plan 04-01 Patch C — prefer stable row-id lookup; fall back to numeric
       idx for backwards compat (any caller still passing 0..N via the legacy
       data-idx attribute). */
    var foundIdx = lbList.findIndex(function (x) { return x.rowId === rowIdOrIdx; });
    if (foundIdx < 0) {
      var n = parseInt(rowIdOrIdx, 10);
      if (!isNaN(n)) foundIdx = ((n % lbList.length) + lbList.length) % lbList.length;
    }
    if (foundIdx < 0) return;
    lbIdx = foundIdx;
    renderLb();
    lb.classList.add('open');
    lb.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    /* Operator spec 6 (2026-05-29) — hide site header while lightbox is open. */
    document.body.classList.add('lb-open');
  }

  function navLb(delta) {
    if (!lb || !lb.classList.contains('open') || !lbList.length) return;
    lbIdx = ((lbIdx + delta) % lbList.length + lbList.length) % lbList.length;
    renderLb();
  }

  function closeLb() {
    if (!lb) return;
    lb.classList.remove('open');
    lb.classList.remove('lb-rotated');
    lb.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    /* Operator spec 6 (2026-05-29) — restore site header on close. */
    document.body.classList.remove('lb-open');
    /* Exit fullscreen if we entered it via the in-lightbox button. */
    try {
      if (document.fullscreenElement) document.exitFullscreen();
    } catch (_) { /* ignore */ }
    if (lbInner) lbInner.innerHTML = '';
    /* Clear meta panel + hide action buttons so the next openAt() starts
       from a clean slate even if a different card has sparse metadata. */
    if (lbMeta) lbMeta.innerHTML = '';
    _hideBtn(lbDownload);
    _hideBtn(lbSource);
  }

  if (lb && lbClose) lbClose.addEventListener('click', closeLb);
  if (lbPrev) lbPrev.addEventListener('click', function (e) { e.stopPropagation(); navLb(-1); });
  if (lbNext) lbNext.addEventListener('click', function (e) { e.stopPropagation(); navLb(1); });
  /* Operator spec 2026-05-29 — close on empty-space click.
     After spec-9 desc-pinned-bottom + spec-5 iframe-fill, the .lb-frame
     element fills the viewport so clicks rarely land on .lightbox root.
     Allow closing when target is the backdrop (lb), the frame shell
     (lb-frame), or the asset-container empty area (lightbox-inner — when
     click misses the asset itself). Interactive children of these
     (.lb-meta-panel, .lb-actions, .lb-btn, .lb-nav, .lb-close, .lb-rotate,
     .lb-fs, .lb-counter, img, video, iframe, audio) absorb their own
     clicks so they won't bubble back here. */
  if (lb) lb.addEventListener('click', function (e) {
    var t = e.target as HTMLElement | null;
    if (!t) return;
    if (t === lb || t.classList.contains('lb-frame') || t.classList.contains('lightbox-inner')) {
      closeLb();
    }
  });

  /* Operator spec 10 (2026-05-29) — rotate-90 toggle (always visible). */
  if (lbRotate && lb) {
    lbRotate.addEventListener('click', function (e) {
      e.stopPropagation();
      lb.classList.toggle('lb-rotated');
    });
  }

  /* Operator spec 10 (2026-05-29) — fullscreen toggle. ESC exits via the
     browser default; fullscreenchange updates the button label. */
  if (lbFullscreen && lb) {
    lbFullscreen.addEventListener('click', function (e) {
      e.stopPropagation();
      try {
        if (!document.fullscreenElement) {
          if (lb.requestFullscreen) lb.requestFullscreen();
        } else {
          if (document.exitFullscreen) document.exitFullscreen();
        }
      } catch (_) { /* fullscreen API unavailable — silent */ }
    });
    document.addEventListener('fullscreenchange', function () {
      if (!lbFullscreen) return;
      if (document.fullscreenElement) {
        lbFullscreen.setAttribute('aria-label', 'Exit fullscreen');
        lbFullscreen.setAttribute('title', 'Exit fullscreen');
        lbFullscreen.textContent = '⤡';
      } else {
        lbFullscreen.setAttribute('aria-label', 'Enter fullscreen');
        lbFullscreen.setAttribute('title', 'Fullscreen');
        lbFullscreen.textContent = '⛶';
      }
    });
  }

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
     Cards emit <a href="#" data-action="open" data-row-id="rNNN"> alongside
     their download/source anchors; this listener intercepts ONLY
     data-action="open" and routes to openAt() — every other anchor keeps
     native behaviour (Download, Source ↗, DVIDS ↗).
     Plan 04-01 Patch D — prefer data-row-id (stable per-row identifier);
     fall back to data-idx (legacy numeric global index) and to the closest
     .card / .arch-card ancestor for either attribute. */
  document.addEventListener('click', function (e) {
    var action = e.target.closest && e.target.closest('a[data-action="open"]');
    if (!action) return;
    e.preventDefault();
    var rowId = action.dataset.rowId || action.dataset.idx;
    if (rowId === undefined || rowId === null || rowId === '') {
      var card = action.closest('.card, .arch-card');
      rowId = card && (card.dataset.rowId || card.dataset.idx);
    }
    if (rowId) openAt(rowId);
  });

  /* Operator 2026-05-28: clicking ANYWHERE on the card opens lightbox.
     PDF/VID cards have no thumbnail <img> AND no .btn-open anchor (only
     article-level data-action="open") so the previous thumb-only +
     a[data-action="open"] delegates left them completely unclickable.
     This delegate fires on any click inside article[data-action="open"]
     EXCEPT clicks on the Download / Source ↗ / btn-open anchors which
     keep their own native (or btn-open-specific) behaviour. */
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t || !t.closest) return;
    // Don't hijack action-button clicks — Download, Source ↗ have hrefs.
    if (t.closest('a.btn-download, a.btn-source')) return;
    // btn-open already handled by the a[data-action="open"] delegate above.
    if (t.closest('a.btn-open')) return;
    var article = t.closest('article[data-action="open"]');
    if (!article) return;
    e.preventDefault();
    var rowId = article.dataset.rowId || article.dataset.idx;
    if (rowId) openAt(rowId);
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

  /* Operator spec 4 (2026-05-29) — arch-controls-bar scroll-direction
     reveal. Hide on scroll-down, show on scroll-up. The bar stays sticky
     when visible (CSS sticky top:64px already in global.css). We toggle a
     bar-hidden class that adds transform:translateY(-100%) so the
     show/hide animation is GPU-accelerated.

     Skip the hide-on-scroll-down toggle when:
       (a) the lightbox is open (body.lb-open) — the header is also hidden
           so leaving the bar in place doesn't matter, and any DOM mutation
           triggers nav listeners we don't want to fire,
       (b) the user is near the top of the page (< 200 px) — nothing to
           hide above the bar anyway,
       (c) the bar is itself off-screen above the viewport (initial state
           before the user scrolls past .archive).
  */
  var archBar = document.getElementById('arch-controls-bar');
  if (archBar) {
    var lastScrollY = window.pageYOffset || 0;
    var scrollTicking = false;

    function updateBarVisibility() {
      var y = window.pageYOffset || 0;
      var dy = y - lastScrollY;
      // Only react past 200px — avoid hiding the bar before the user has
      // any reason to scroll past it.
      if (y < 200) {
        archBar.classList.remove('bar-hidden');
      } else if (document.body.classList.contains('lb-open')) {
        // Lightbox open — leave bar untouched.
      } else if (dy > 4) {
        // Scrolling down → hide.
        archBar.classList.add('bar-hidden');
      } else if (dy < -4) {
        // Scrolling up → show.
        archBar.classList.remove('bar-hidden');
      }
      lastScrollY = y;
      scrollTicking = false;
    }

    window.addEventListener('scroll', function () {
      if (scrollTicking) return;
      scrollTicking = true;
      window.requestAnimationFrame(updateBarVisibility);
    }, { passive: true });
  }
})();
`;

// Compile-time sanity — TypeScript can typecheck this without ever running it.
// Astro reads the string via the named export at build time.
export default INVARIANTS_JS;
