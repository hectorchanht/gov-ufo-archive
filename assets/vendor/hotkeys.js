/* realufo.org global chord hotkeys.
 *
 *   /     focus the on-page search input (#q or #arch-search)
 *   g h   home (/)
 *   g s   search (/search.html)
 *   g t   timeline (/timeline.html)
 *   g m   map (/map.html)
 *   g a   AARO archive
 *   g g   glossary
 *   ?     show this list
 *
 * Active inputs (input, textarea, contenteditable, etc.) suppress chords.
 * Chord expires after 1.2 seconds with no second keystroke.
 */
(function() {
  'use strict';

  /* Pool of case detail pages — chord `g r` picks one at random. Updated
     by hand when new cases land; alternatively this can be hydrated from
     /api/geo.json's `cases[].href`. */
  var RANDOM_CASES = [
    '/uk/rendlesham.html', '/aaro/tic-tac.html', '/aaro/gimbal.html',
    '/aaro/phoenix-lights.html', '/aaro/belgian-wave.html',
    '/aaro/tehran.html', '/aaro/jal-1628.html', '/aaro/coyne.html',
    '/brazil/operacao-prato.html', '/brazil/varginha.html', '/brazil/trindade.html',
    '/nz/kaikoura.html', '/spain/manises.html',
    '/geipan/trans-en-provence.html',
    '/nara/roswell.html', '/nara/socorro.html',
  ];

  var DEST = {
    h: '/',
    s: '/search.html',
    t: '/timeline.html',
    m: '/map.html',
    a: '/aaro/',
    g: '/glossary.html',
    b: '/about.html',
    d: '/donate.html',
  };

  var pending = null, pendingTimer = null;

  function isEditable(el) {
    if (!el || el === document.body) return false;
    var tag = el.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
    if (el.isContentEditable) return true;
    return false;
  }

  function focusSearch() {
    var el = document.getElementById('q')
          || document.getElementById('arch-search')
          || document.querySelector('input[type="search"]');
    if (el) { el.focus(); el.select && el.select(); return true; }
    return false;
  }

  function showHelp() {
    /* Lightweight in-page overlay; built/destroyed on demand. */
    var old = document.getElementById('hotkey-help');
    if (old) { old.remove(); return; }
    var el = document.createElement('div');
    el.id = 'hotkey-help';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-label', 'Keyboard shortcuts');
    el.style.cssText = (
      'position:fixed;inset:0;z-index:10000;background:rgba(10,10,12,0.85);' +
      'display:flex;align-items:center;justify-content:center;padding:20px;' +
      'font-family:"JetBrains Mono",monospace;font-size:13px;color:#e8e3d8;'
    );
    el.innerHTML = (
      '<div style="background:#15151a;border:1px solid rgba(232,227,216,0.28);' +
      'border-radius:8px;padding:20px 24px;max-width:420px;width:100%;' +
      'box-shadow:0 16px 40px rgba(0,0,0,0.6)">' +
      '<div style="font-size:11px;letter-spacing:0.14em;text-transform:uppercase;color:#d4a017;margin-bottom:14px">◉ Keyboard shortcuts</div>' +
      '<dl style="display:grid;grid-template-columns:auto 1fr;gap:6px 18px;margin:0">' +
      '<dt><kbd style="background:#0a0a0c;border:1px solid rgba(232,227,216,0.28);padding:2px 7px;border-radius:3px">/</kbd></dt><dd>Focus search</dd>' +
      '<dt><kbd>g h</kbd></dt><dd>Home</dd>' +
      '<dt><kbd>g s</kbd></dt><dd>Search</dd>' +
      '<dt><kbd>g t</kbd></dt><dd>Timeline</dd>' +
      '<dt><kbd>g m</kbd></dt><dd>Map</dd>' +
      '<dt><kbd>g a</kbd></dt><dd>AARO</dd>' +
      '<dt><kbd>g g</kbd></dt><dd>Glossary</dd>' +
      '<dt><kbd>g b</kbd></dt><dd>About</dd>' +
      '<dt><kbd>g d</kbd></dt><dd>Support / donate</dd>' +
      '<dt><kbd>g r</kbd></dt><dd>Random case</dd>' +
      '<dt><kbd>?</kbd></dt><dd>This help</dd>' +
      '<dt><kbd>Esc</kbd></dt><dd>Close</dd>' +
      '</dl>' +
      '<style>#hotkey-help dt kbd{font:inherit;background:#0a0a0c;border:1px solid rgba(232,227,216,0.28);padding:1px 7px;border-radius:3px;color:#e8e3d8}</style>' +
      '</div>'
    );
    document.body.appendChild(el);
    el.addEventListener('click', function(e){ if (e.target === el) el.remove(); });
  }

  document.addEventListener('keydown', function(e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (isEditable(e.target)) return;
    var k = e.key;

    if (k === 'Escape') {
      var help = document.getElementById('hotkey-help');
      if (help) { help.remove(); e.preventDefault(); return; }
    }
    if (k === '?') {
      e.preventDefault();
      showHelp();
      return;
    }
    if (k === '/') {
      if (focusSearch()) e.preventDefault();
      return;
    }
    if (pending === 'g' && DEST[k]) {
      clearTimeout(pendingTimer);
      pending = null;
      e.preventDefault();
      window.location.href = DEST[k];
      return;
    }
    if (pending === 'g' && k === 'r') {
      clearTimeout(pendingTimer);
      pending = null;
      e.preventDefault();
      var pick = RANDOM_CASES[Math.floor(Math.random() * RANDOM_CASES.length)];
      window.location.href = pick;
      return;
    }
    if (k === 'g') {
      pending = 'g';
      clearTimeout(pendingTimer);
      pendingTimer = setTimeout(function(){ pending = null; }, 1200);
      return;
    }
    /* unknown key while waiting → cancel pending chord */
    if (pending) {
      pending = null;
      clearTimeout(pendingTimer);
    }
  });
})();
