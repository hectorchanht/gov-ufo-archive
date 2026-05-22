"""Shared CSS + JS strings used by every mirror build script.

SHARED_CSS depends on LIGHTBOX_CSS (injected at the __LIGHTBOX_CSS__
placeholder). SHARED_JS depends on _I18N_JSON (injected at
__I18N_JSON__). Both resolutions happen at module load.
"""
from __future__ import annotations

from .i18n import _I18N_JSON
from .lightbox import LIGHTBOX_CSS


SHARED_CSS = r'''
:root {
  --bg:#0a0a0c; --bg-2:#111114; --panel:#15151a;
  --ink:#e8e3d8; --ink-dim:#a8a298; --ink-faint:#6b665d;
  --rule:rgba(232,227,216,0.12); --rule-strong:rgba(232,227,216,0.28);
  --stamp:#b91c1c; --warm:#d4a017; --classified:#c9362c;
  --serif:"Source Serif 4","Iowan Old Style",Georgia,serif;
  --mono:"JetBrains Mono","SF Mono",Consolas,monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; scroll-padding-top: 70px; }
body { background: var(--bg); color: var(--ink); font-family: var(--serif); font-size: 15px; line-height: 1.65; overflow-x: hidden; }
@media (min-width: 720px) { body { font-size: 16px; } }
.scanlines { position: fixed; inset: 0; background: repeating-linear-gradient(to bottom, transparent 0, transparent 2px, rgba(255,255,255,0.012) 3px, transparent 4px); pointer-events: none; z-index: 50; }
@media (prefers-reduced-motion: reduce) { .scanlines { display: none; } *, *::before, *::after { animation-duration: 0.001ms !important; animation-iteration-count: 1 !important; transition-duration: 0.001ms !important; scroll-behavior: auto !important; } }
.container { max-width: 1200px; margin: 0 auto; padding: 0 16px; position: relative; z-index: 2; }
@media (min-width: 720px) { .container { padding: 0 32px; } }

/* ── Header ─────────────────────────────────────────────────────────── */
.header-wrap { position: sticky; top: 0; z-index: 40; background: rgba(10,10,12,0.96); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid var(--rule); }
header { padding: 12px 0; }
header .container { display: flex; align-items: center; gap: 12px; }
.brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--ink); flex-shrink: 0; min-width: 0; }
.seal { width: 38px; height: 38px; border-radius: 50%; display: grid; place-items: center; box-shadow: 0 0 0 2px var(--ink), 0 0 0 4px var(--bg), 0 0 0 5px var(--ink-faint); font-family: var(--mono); font-weight: 700; font-size: 9px; color: var(--ink); flex-shrink: 0; }
.brand-text { display: flex; flex-direction: column; line-height: 1.1; min-width: 0; }
.brand-text .super { font-family: var(--mono); font-size: 8.5px; letter-spacing: 0.14em; color: var(--ink-dim); text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 180px; }
.brand-text .name { font-family: var(--serif); font-size: 15px; font-weight: 600; margin-top: 1px; }
@media (min-width: 720px) { .seal { width: 42px; height: 42px; } .brand-text .name { font-size: 17px; } .brand-text .super { max-width: none; } }

/* Hamburger — right-most, never pushed to next line */
.nav-toggle { display: none; background: transparent; border: 1px solid var(--rule-strong); width: 38px; height: 38px; cursor: pointer; padding: 0; flex-direction: column; justify-content: center; align-items: center; gap: 4px; flex-shrink: 0; margin-left: auto; }
.nav-toggle span { display: block; width: 18px; height: 2px; background: var(--ink); transition: transform .2s, opacity .2s; }
.nav-toggle[aria-expanded="true"] span:nth-child(1) { transform: translateY(6px) rotate(45deg); }
.nav-toggle[aria-expanded="true"] span:nth-child(2) { opacity: 0; }
.nav-toggle[aria-expanded="true"] span:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }

/* ── Primary nav ─────────────────────────────────────────────────────── */
/* Mobile: fixed overlay below sticky header so brand+toggle stay top-pinned. */
nav.primary { display: none; font-family: var(--mono); font-size: 11px; letter-spacing: 0.07em; }
nav.primary.open { display: block; position: fixed; top: 64px; left: 0; right: 0; background: var(--panel); border-bottom: 1px solid var(--rule-strong); padding: 8px 16px 16px; max-height: calc(100vh - 64px); overflow-y: auto; -webkit-overflow-scrolling: touch; overscroll-behavior: contain; z-index: 800; }
nav.primary > ul { display: flex; flex-direction: column; gap: 0; list-style: none; padding-top: 0; margin-top: 0; border-top: 0; }
nav.primary > ul > li { width: 100%; }
nav.primary > ul > li.nav-sep { display: none; }
nav.primary a { color: var(--ink-dim); text-decoration: none; text-transform: uppercase; display: block; padding: 11px 0; border-bottom: 1px solid var(--rule); }
nav.primary a:hover, nav.primary a.active { color: var(--caution); }

@media (min-width: 720px) {
  .nav-toggle { display: none !important; }
  nav.primary { display: flex !important; position: static; padding: 0; max-height: none; overflow: visible; background: transparent; border: 0; flex-basis: auto; flex: 1; align-items: center; justify-content: flex-end; }
  nav.primary > ul { flex-direction: row; align-items: center; gap: 2px 18px; flex-wrap: nowrap; padding-top: 0; margin-top: 0; border: 0; }
  nav.primary > ul > li { width: auto; }
  nav.primary a { padding: 0; border: 0; font-size: 10.5px; }
  nav.primary > ul > li.nav-sep { display: block; width: 1px; height: 16px; background: var(--rule-strong); flex-shrink: 0; }
}

/* mobile hamburger visible only below 720px */
@media (max-width: 719px) {
  .nav-toggle { display: flex; }
}

/* ── "More" dropdown ─────────────────────────────────────────────────── */
/* ── Dropdowns: native <details>/<summary> ─────────────────────────────── */
/* The browser owns open/close state via the [open] attribute. CSS just
   styles the summary like a button and hides the native marker. JS only
   coordinates "close peers when one opens" — no stuck-open state possible. */
.has-dropdown { position: relative; }
.has-dropdown > details { display: block; }
.has-dropdown > details > summary { list-style: none; cursor: pointer; }
.has-dropdown > details > summary::-webkit-details-marker { display: none; }
.has-dropdown > details > summary::marker { content: ''; }
.nav-more-btn {
  background: none; border: none; color: var(--ink-dim); cursor: pointer;
  font-family: var(--mono); font-size: 11px; letter-spacing: 0.07em;
  text-transform: uppercase; padding: 11px 0; display: block; width: 100%;
  text-align: left; border-bottom: 1px solid var(--rule);
}
.nav-more-btn:hover, .nav-more-btn.active { color: var(--caution); }
.nav-dropdown {
  list-style: none;
  background: var(--panel); border: 1px solid var(--rule-strong);
  padding: 6px 0; z-index: 200; margin: 0;
}
.nav-dropdown li a { border: 0 !important; padding: 9px 16px !important; font-size: 10.5px; white-space: nowrap; }
/* Mobile: inline expansion under summary */
@media (max-width: 719px) {
  .nav-dropdown { position: static; min-width: 0; width: 100%; border: 0; background: transparent; box-shadow: none; padding: 0; margin: 0 0 0 12px; }
}
/* Desktop: floating panel anchored right of summary */
@media (min-width: 720px) {
  .nav-more-btn { padding: 0; border: 0; width: auto; font-size: 10.5px; }
  .nav-dropdown { position: absolute; right: 0; top: calc(100% + 10px); min-width: 240px; max-height: 70vh; overflow-y: auto; box-shadow: 0 8px 24px rgba(0,0,0,0.6); }
}

/* ── Language picker ─────────────────────────────────────────────────── */
.lang-picker { position: relative; }
.lang-btn {
  background: transparent; border: 1px solid var(--rule-strong);
  color: var(--ink-dim); cursor: pointer; font-family: var(--mono);
  font-size: 9.5px; letter-spacing: 0.12em; padding: 4px 8px;
  text-transform: uppercase; transition: color .15s, border-color .15s;
  display: block; width: 100%; text-align: left; margin: 8px 0;
}
.lang-btn:hover { color: var(--caution); border-color: var(--caution); }
.lang-menu { display: none; list-style: none; background: var(--panel); border: 1px solid var(--rule-strong); padding: 6px 0; z-index: 300; }
.lang-menu button { background: none; border: none; color: var(--ink-dim); cursor: pointer; font-family: var(--mono); font-size: 10.5px; padding: 8px 16px; width: 100%; text-align: left; }
.lang-menu button:hover { color: var(--caution); }
.lang-picker.open .lang-menu { display: block; }
@media (max-width: 719px) {
  .lang-btn { border: 0; margin: 0; padding: 11px 0; font-size: 11px; border-bottom: 1px solid var(--rule); }
  .lang-picker.open .lang-menu { margin-left: 12px; border: 0; background: transparent; }
}
@media (min-width: 720px) {
  .lang-btn { width: auto; margin: 0; padding: 3px 8px; }
  .lang-menu { position: absolute; right: 0; top: calc(100% + 10px); min-width: 130px; }
}

/* ── Hero ────────────────────────────────────────────────────────────── */
.hero { padding: 48px 0 32px; border-bottom: 1px solid var(--rule); }
@media (min-width: 720px) { .hero { padding: 64px 0 48px; } }
.coords { font-family: var(--mono); font-size: 11px; color: var(--caution); letter-spacing: 0.12em; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.coords::before { content: "◉"; color: var(--stamp); }
h1.hero-title { font-family: var(--serif); font-weight: 700; font-size: clamp(26px,5.5vw,52px); line-height: 1.05; letter-spacing: -0.02em; max-width: 24ch; margin-bottom: 18px; word-break: break-word; }
h1.hero-title em { color: var(--caution); font-style: italic; }
.hero-sub { max-width: 65ch; color: var(--ink-dim); font-size: 16px; line-height: 1.65; }
.hero-sub a { color: var(--caution); }

/* ── Headlines ───────────────────────────────────────────────────────── */
.headlines { padding: 32px 0; border-bottom: 1px solid var(--rule); }
.head-grid { display: grid; gap: 14px; grid-template-columns: 1fr; }
@media (min-width: 540px) { .head-grid { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; } }
.head-card { padding: 18px 20px; background: var(--panel); border: 1px solid var(--rule); border-left: 3px solid var(--caution); }
.head-card .h-label { font-family: var(--mono); font-size: 10px; color: var(--caution); letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 10px; }
.head-card .h-text { font-size: 16px; line-height: 1.4; color: var(--ink); }
.head-card .h-num { font-family: var(--mono); font-size: 28px; color: var(--ink); font-weight: 600; display: block; margin-bottom: 4px; }

/* ── Archive section ─────────────────────────────────────────────────── */
section { padding: 40px 0; border-bottom: 1px solid var(--rule); }
@media (min-width: 720px) { section { padding: 56px 0; } }
.section-label { font-family: var(--mono); font-size: 11px; letter-spacing: 0.24em; text-transform: uppercase; color: var(--ink-faint); display: flex; align-items: center; gap: 14px; margin-bottom: 18px; }
.section-label::before { content: ""; width: 28px; height: 1px; background: var(--ink-faint); }
h2 { font-family: var(--serif); font-size: clamp(22px,3.5vw,34px); font-weight: 700; letter-spacing: -0.015em; margin-bottom: 18px; max-width: 28ch; word-break: break-word; }
.lede { max-width: 70ch; color: var(--ink); font-size: 16px; }
.lede a { color: var(--caution); }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1px; background: var(--rule); border: 1px solid var(--rule); margin: 20px 0 24px; }
@media (min-width: 540px) { .stats-grid { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); } }
.stat { background: var(--panel); padding: 14px 18px; font-family: var(--mono); }
.stat b { display: block; font-size: 24px; color: var(--ink); font-weight: 500; }
.stat small { display: block; font-size: 10px; color: var(--ink-faint); letter-spacing: 0.16em; text-transform: uppercase; margin-top: 6px; }

/* ── Archive controls (tabs + search) — stays sticky ─────────────────── */
.arch-controls-bar {
  position: sticky; top: 64px; z-index: 30;
  background: rgba(10,10,12,0.96); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule);
  margin: 24px -16px 0; padding: 10px 16px;
  display: flex; flex-direction: column; gap: 8px;
  transition: top 0.28s ease;
}
@media (min-width: 720px) {
  .arch-controls-bar { margin: 24px -32px 0; padding: 12px 32px; flex-direction: row; align-items: center; gap: 14px; }
}
.arch-controls-bar.bar-hidden { top: -160px; }

.tabs { display: flex; gap: 6px; flex-wrap: wrap; width: 100%; }
.tab { font-family: var(--mono); font-size: 10px; padding: 6px 10px; border: 1px solid var(--rule-strong); background: var(--panel); color: var(--ink-dim); cursor: pointer; letter-spacing: 0.08em; text-transform: uppercase; }
@media (min-width: 720px) { .tab { font-size: 11px; padding: 8px 14px; } .tabs { width: auto; } }
.tab:hover { color: var(--ink); border-color: var(--ink-faint); }
.tab.active { background: var(--caution); color: var(--bg); border-color: var(--caution); font-weight: 700; }
.tab .count { opacity: 0.6; margin-left: 6px; font-size: 10px; }

.search-wrap { display: flex; align-items: center; gap: 8px; background: var(--panel); border: 1px solid var(--rule-strong); padding: 6px 12px; width: 100%; }
@media (min-width: 720px) { .search-wrap { margin-left: auto; min-width: 240px; width: auto; } }
.search-wrap::before { content: "⌕"; color: var(--ink-faint); font-family: var(--mono); }
.search-wrap input { background: transparent; border: 0; outline: 0; color: var(--ink); font-family: var(--mono); font-size: 12px; flex: 1; min-width: 0; }
.search-wrap input::placeholder { color: var(--ink-faint); }

/* ── Cards ───────────────────────────────────────────────────────────── */
.arch-grid { display: grid; grid-template-columns: 1fr; gap: 14px; padding: 16px 0 24px; }
@media (min-width: 540px) { .arch-grid { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 18px; } }
.card { background: var(--panel); border: 1px solid var(--rule); display: flex; flex-direction: column; overflow: hidden; transition: border-color .2s, transform .2s; }
.card:hover { border-color: var(--caution); transform: translateY(-2px); }
.card-media { aspect-ratio: 16/9; background: var(--bg-2); position: relative; overflow: hidden; display: grid; place-items: center; border-bottom: 1px solid var(--rule); cursor: pointer; }
.card-media img { width: 100%; height: 100%; object-fit: cover; display: block; }
.pdf-glyph { font-family: var(--mono); font-size: 12px; color: var(--ink-faint); background: repeating-linear-gradient(45deg,#1a1a1f,#1a1a1f 8px,#15151a 8px,#15151a 16px); width: 100%; height: 100%; display: grid; place-items: center; text-align: center; padding: 16px; }
.pdf-glyph .ico { font-size: 22px; color: var(--caution); margin-bottom: 6px; border: 2px solid var(--caution); padding: 4px 10px; font-weight: 700; letter-spacing: 0.04em; display: inline-block; }
.glyph-cat { background: linear-gradient(135deg, rgba(212,160,23,0.12), transparent); }
.glyph-cat .ico { color: var(--warm); border-color: var(--warm); }
.badge { position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.78); color: var(--caution); font-family: var(--mono); font-size: 9px; padding: 3px 8px; letter-spacing: 0.14em; text-transform: uppercase; }
.badge.local { bottom: 8px; left: 8px; top: auto; color: var(--warm); }
.badge.source { bottom: 8px; left: 8px; top: auto; color: var(--ink-faint); }
.card-body { padding: 14px 16px; flex: 1; display: flex; flex-direction: column; gap: 6px; }
.card-title { font-family: var(--serif); font-size: 14px; font-weight: 600; line-height: 1.35; color: var(--ink); overflow-wrap: anywhere; }
.card-desc { font-family: var(--serif); font-size: 12.5px; color: var(--ink-dim); line-height: 1.5; margin-top: 4px; }
.card-meta { display: grid; grid-template-columns: 72px 1fr; gap: 4px 12px; margin-top: 8px; padding: 10px 0; border-top: 1px solid var(--rule); }
.card-meta dt { font-family: var(--mono); font-size: 9px; color: var(--ink-faint); letter-spacing: 0.14em; text-transform: uppercase; }
.card-meta dd { font-family: var(--serif); color: var(--ink); font-size: 12px; line-height: 1.4; }
.card-actions { display: flex; gap: 8px; margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--rule); flex-wrap: wrap; }
.card-actions a, .card-actions button { font-family: var(--mono); font-size: 10px; color: var(--caution); text-decoration: none; letter-spacing: 0.12em; text-transform: uppercase; padding: 6px 10px; border: 1px solid var(--rule-strong); min-height: 30px; display: inline-flex; align-items: center; background: none; cursor: pointer; }
.card-actions a:hover, .card-actions button:hover { background: var(--caution); color: var(--bg); border-color: var(--caution); }
.card-actions .warn { color: var(--ink-faint); }
.card-actions .warn:hover { background: var(--ink-faint); color: var(--bg); }
.empty { padding: 60px 0; text-align: center; color: var(--ink-faint); font-family: var(--mono); font-size: 13px; }

/* ── Lightbox ─────────────────────────────────────────────────────────── */
/* Body of this rule set is the LIGHTBOX_CSS constant defined below; it is
   injected here at module load via .replace('__LIGHTBOX_CSS__', ...). */
__LIGHTBOX_CSS__
.lb-counter { position: absolute; top: 16px; left: 50%; transform: translateX(-50%); font-family: var(--mono); font-size: 11px; letter-spacing: 0.16em; color: var(--ink-dim); background: var(--bg-2); border: 1px solid var(--rule); padding: 4px 12px; z-index: 2; }

/* ── Footer ──────────────────────────────────────────────────────────── */
footer { background: #060608; padding: 32px 0 24px; color: var(--ink-dim); font-family: var(--mono); font-size: 12px; }
footer .container { display: grid; grid-template-columns: 1fr; gap: 24px; }
@media (min-width: 720px) { footer .container { grid-template-columns: 1.4fr 1fr 1fr; gap: 40px; } }
footer h4 { font-family: var(--mono); font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--ink); margin-bottom: 14px; }
footer ul { list-style: none; display: flex; flex-direction: column; gap: 8px; }
footer a { color: var(--ink-dim); text-decoration: underline; text-decoration-color: var(--rule-strong); text-underline-offset: 2px; }
footer a:hover { color: var(--caution); }
footer .colophon { grid-column: 1 / -1; border-top: 1px solid var(--rule); padding-top: 20px; margin-top: 12px; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 16px; font-size: 10px; color: var(--ink-faint); letter-spacing: 0.1em; }
'''.replace('__LIGHTBOX_CSS__', LIGHTBOX_CSS.strip())


EXTRA_CSS = r'''
/* fix: flat mobile nav + desktop dropdown safety */
@media (max-width: 719px) {
  .nav-more-btn { display: none !important; }
  .has-dropdown .nav-dropdown { display: block !important; position: static !important; margin: 0 !important; padding: 0 !important; border: 0 !important; background: transparent !important; box-shadow: none !important; min-width: 0 !important; }
  .has-dropdown .nav-dropdown li a { padding: 11px 0 !important; border-bottom: 1px solid var(--rule) !important; font-size: 11px !important; }
}
@media (min-width: 720px) {
  .has-dropdown:not(.open) > .nav-dropdown { display: none !important; }
}
'''


SHARED_JS = r'''
(() => {
  /* ── i18n ─────────────────────────────────────────────────────────── */
  const I18N = __I18N_JSON__;
  let lang = localStorage.getItem('realufo_lang') || 'en';
  if (!I18N[lang]) lang = 'en';

  function applyLang(code) {
    lang = code;
    localStorage.setItem('realufo_lang', code);
    const t = I18N[code];
    // Update all data-i18n elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (t[key] !== undefined) el.textContent = t[key];
    });
    // Update lang button label
    const lb = document.getElementById('lang-btn');
    if (lb) lb.textContent = t.code || code.toUpperCase();
    // Update tab labels if archive page
    updateTabLabels(t);
  }

  function updateTabLabels(t) {
    const TAB_MAP = { ALL: t.all, PDF: t.docs, VID: t.videos,
                      IMG: t.imagery, CATALOG: t.catalog };
    document.querySelectorAll('.tab[data-key]').forEach(btn => {
      const key = btn.dataset.key;
      if (TAB_MAP[key]) {
        const count = btn.querySelector('.count');
        const countText = count ? count.outerHTML : '';
        btn.innerHTML = TAB_MAP[key] + countText;
        if (count) btn.appendChild(btn.querySelector('.count'));
      }
    });
    const si = document.getElementById('arch-search');
    if (si) si.setAttribute('placeholder', t.search || 'Search…');
    const empty = document.getElementById('arch-empty');
    if (empty) empty.textContent = t.no_results || 'No results.';
  }

  /* ── Language picker ──────────────────────────────────────────────── */
  const langPicker = document.getElementById('lang-picker');
  const langBtn    = document.getElementById('lang-btn');
  const langMenu   = document.getElementById('lang-menu');
  if (langBtn && langPicker) {
    langBtn.addEventListener('click', e => {
      e.stopPropagation();
      const open = langPicker.classList.toggle('open');
      langBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    if (langMenu) {
      langMenu.addEventListener('click', e => {
        const btn = e.target.closest('button[data-lang]');
        if (!btn) return;
        applyLang(btn.dataset.lang);
        langPicker.classList.remove('open');
        langBtn.setAttribute('aria-expanded', 'false');
      });
    }
  }

  /* ── Native <details> dropdown coordination ────────────────────────────
     Each .has-dropdown contains its own <details>. Browser owns open state.
     We only enforce: opening one closes the others, outside click closes all.
     Avoids stuck-open bugs from class-based toggling. */
  const navDetails = Array.from(document.querySelectorAll('.has-dropdown > details'));
  navDetails.forEach(d => {
    d.addEventListener('toggle', () => {
      if (!d.open) return;
      navDetails.forEach(other => { if (other !== d) other.open = false; });
    });
  });
  document.addEventListener('click', e => {
    if (langPicker) { langPicker.classList.remove('open'); if (langBtn) langBtn.setAttribute('aria-expanded','false'); }
    if (!e.target.closest('.has-dropdown')) {
      navDetails.forEach(d => { d.open = false; });
    }
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') navDetails.forEach(d => { d.open = false; });
  });

  /* ── Hamburger toggle ─────────────────────────────────────────────── */
  const navToggle = document.getElementById('nav-toggle');
  const primaryNav = document.getElementById('primary-nav');
  if (navToggle && primaryNav) {
    navToggle.addEventListener('click', () => {
      const open = primaryNav.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    primaryNav.addEventListener('click', e => {
      if (e.target.tagName === 'A') {
        primaryNav.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ── Scroll-hide controls bar (mobile) ───────────────────────────── */
  const ctrlBar = document.querySelector('.arch-controls-bar');
  if (ctrlBar) {
    let lastY = window.scrollY;
    window.addEventListener('scroll', () => {
      if (window.innerWidth >= 720) { ctrlBar.classList.remove('bar-hidden'); return; }
      const y = window.scrollY;
      if (y < 80) { ctrlBar.classList.remove('bar-hidden'); }
      else if (y > lastY + 4) { ctrlBar.classList.add('bar-hidden'); }
      else if (y < lastY - 4) { ctrlBar.classList.remove('bar-hidden'); }
      lastY = y;
    }, { passive: true });
  }

  /* Apply saved language */
  applyLang(lang);

  /* ── Lightbox ─────────────────────────────────────────────────────── */
  let lbList = [], lbIdx = 0;
  const lb      = document.getElementById('lightbox');
  const lbI     = document.getElementById('lb-inner');
  const lbC     = document.getElementById('lb-close');
  const lbPrev  = document.getElementById('lb-prev');
  const lbNext  = document.getElementById('lb-next');
  const lbCount = document.getElementById('lb-counter');

  function esc(s) {
    return (s||'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function renderLb() {
    const a = lbList[lbIdx]; if (!a) return;
    const title = a.ti || a.title || '';
    let html;
    if (a.t === 'IMG' || a.type === 'IMG') {
      const src = a.l || a.local ? './' + (a.l || a.local) : (a.u || a.url);
      const fb  = (a.u || a.url) && (a.l || a.local) ? `onerror="this.onerror=null;this.src='${esc(a.u||a.url)}';"` : '';
      html = `<img src="${esc(src)}" alt="${esc(title)}" ${fb}><div class="lb-meta">${esc(title)}</div>`;
    } else if (a.t === 'VID' || a.type === 'VID') {
      const loc = a.l || a.local; const rem = a.u || a.url;
      if (loc) {
        html = `<video controls autoplay style="max-width:90vw;max-height:78vh"><source src="./${esc(loc)}"><source src="${esc(rem)}"></video><div class="lb-meta">${esc(title)}</div>`;
      } else if (a.embed) {
        html = `<iframe src="${esc(a.embed)}?autoplay=1" allow="autoplay;encrypted-media" allowfullscreen></iframe><div class="lb-meta">${esc(title)}</div>`;
      } else { window.open(rem,'_blank'); closeLb(); return; }
    } else if (a.t === 'PDF' || a.type === 'PDF') {
      const loc = a.l || a.local;
      if (loc) {
        html = `<iframe src="./${esc(loc)}#view=FitH" sandbox="allow-same-origin allow-popups"></iframe><div class="lb-meta">${esc(title)} — <a href="./${esc(loc)}" target="_blank">open in new tab ↗</a></div>`;
      } else { window.open(a.u || a.url,'_blank'); closeLb(); return; }
    } else {
      const target = (a.l||a.local) ? './'+(a.l||a.local) : (a.u||a.url);
      window.open(target,'_blank'); closeLb(); return;
    }
    lbI.innerHTML = html;
    if (lbCount) lbCount.textContent = (lbIdx+1) + ' / ' + lbList.length;
    if (lbPrev) lbPrev.style.visibility = lbList.length > 1 ? 'visible' : 'hidden';
    if (lbNext) lbNext.style.visibility = lbList.length > 1 ? 'visible' : 'hidden';
  }
  function openAt(idx) { if (!lbList.length) return; lbIdx = (idx+lbList.length)%lbList.length; renderLb(); lb && lb.classList.add('open'); }
  function navLb(d)  { if (!lbList.length) return; lbIdx = (lbIdx+d+lbList.length)%lbList.length; renderLb(); }
  function closeLb() { lb && lb.classList.remove('open'); lb && lb.classList.remove('lb-rotated'); lbI && (lbI.innerHTML=''); }

  if (lb) {
    if (lbC)    lbC.addEventListener('click', closeLb);
    if (lbPrev) lbPrev.addEventListener('click', e => { e.stopPropagation(); navLb(-1); });
    if (lbNext) lbNext.addEventListener('click', e => { e.stopPropagation(); navLb(1); });
    const lbR = document.getElementById('lb-rotate');
    if (lbR) lbR.addEventListener('click', e => { e.stopPropagation(); lb.classList.toggle('lb-rotated'); });
    lb.addEventListener('click', e => { if (e.target === lb) closeLb(); });
  }
  document.addEventListener('keydown', e => {
    if (!lb || !lb.classList.contains('open')) return;
    if (e.key==='Escape') closeLb();
    else if (e.key==='ArrowRight') navLb(1);
    else if (e.key==='ArrowLeft')  navLb(-1);
  });
  let tx=0, ty=0, tt=0;
  if (lb) {
    lb.addEventListener('touchstart', e => { if (!e.touches.length) return; tx=e.touches[0].clientX; ty=e.touches[0].clientY; tt=Date.now(); }, {passive:true});
    lb.addEventListener('touchend',   e => { if (!e.changedTouches.length) return; const dx=e.changedTouches[0].clientX-tx, dy=e.changedTouches[0].clientY-ty; if(Date.now()-tt<800&&Math.abs(dx)>50&&Math.abs(dx)>Math.abs(dy)) navLb(dx<0?1:-1); }, {passive:true});
  }

  /* Export for caller scripts that need openAt/lbList */
  window._lb = { open: openAt, setList: l => { lbList = l; }, getList: () => lbList };
})();
'''.replace('__I18N_JSON__', _I18N_JSON)
