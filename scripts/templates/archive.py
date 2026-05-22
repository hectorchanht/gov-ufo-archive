"""Reusable archive-page client JS.

ARCHIVE_JS is inlined into every catalog-style mirror page (UK, Brazil,
Chile, batch3 family, and any future archive that fits the same shape).
It:

  - reads <script id="arch-data" type="application/json">…</script>
  - renders stats (#arch-stats), tabs (#arch-tabs), search (#arch-search)
  - paints cards into #arch-grid + populates the lightbox list
  - delegates open/nav/close to window._lb (LIGHTBOX_JS)

A page that needs its own paginator (e.g. GEIPAN with 3334 records) signals
this by including #pagination in the DOM — ARCHIVE_JS bails out early so
the host page can drive its own renderer.

Pages using this module need these DOM hooks:
  <script id="arch-data" type="application/json">…</script>
  <div id="arch-stats"></div>     (optional)
  <div id="arch-tabs"></div>      (optional)
  <input id="arch-search">        (optional)
  <div id="arch-grid"></div>
  <div id="arch-empty" hidden></div>

Card data shape (the JSON inside arch-data):
  { assets: [ { t, ti, de, ag, cat, date, region, l, u, s, th }, … ],
    stats:  { total, local_total, pdf_total, catalog_total } }
"""
from __future__ import annotations


ARCHIVE_JS = r'''
(() => {
  const archData = document.getElementById('arch-data');
  if (!archData) return;
  /* Skip the simple catalog renderer if the page provides its own paginated
     archive block (presence of #pagination signals a per-page paginator).
     Prevents a 3000+ node initial paint on large catalogs (GEIPAN). */
  if (document.getElementById('pagination')) return;
  const D = JSON.parse(archData.textContent);
  const items = D.assets;
  const STATS = D.stats;
  function esc(s){return (s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

  const statsEl = document.getElementById('arch-stats');
  if (statsEl) statsEl.innerHTML = [
    ['Total', STATS.total],
    ['Local', STATS.local_total],
    ['Documents', STATS.pdf_total],
    ['Catalog', STATS.catalog_total],
  ].map(([k,v]) => `<div class="stat"><b>${v}</b><small>${k}</small></div>`).join('');

  const TABS = [
    {key:'ALL', label:'All'},
    {key:'PDF', label:'Documents'},
    {key:'CATALOG', label:'Catalog'},
  ];
  const state = { tab: 'ALL', q: '' };
  const tabsEl = document.getElementById('arch-tabs');
  function count(k){ return k === 'ALL' ? items.length : items.filter(a => a.t === k).length; }
  if (tabsEl) {
    tabsEl.innerHTML = TABS.map(t => `<button class="tab${t.key===state.tab?' active':''}" data-key="${t.key}">${t.label}<span class="count">${count(t.key)}</span></button>`).join('');
    tabsEl.addEventListener('click', e => {
      const tab = e.target.closest('.tab'); if (!tab) return;
      state.tab = tab.dataset.key;
      tabsEl.querySelectorAll('.tab').forEach(x => x.classList.toggle('active', x.dataset.key === state.tab));
      render();
    });
  }
  const searchEl = document.getElementById('arch-search');
  if (searchEl) searchEl.addEventListener('input', e => { state.q = e.target.value.trim().toLowerCase(); render(); });

  function glyphFor(a) {
    if (a.th) {
      const lbl = esc(a.cat || a.ag || a.t || '');
      const fb  = (a.t === 'CATALOG')
        ? `<div class=\"pdf-glyph glyph-cat\"><span class=\"ico\">⌕</span><span>${esc(a.cat||'Catalog')}</span></div>`
        : `<div class=\"pdf-glyph\"><span class=\"ico\">PDF</span><span>${esc(a.ag||'Document')}</span></div>`;
      return `<img loading="lazy" decoding="async" src="${esc(a.th)}" alt="${lbl}" onerror="this.outerHTML='${fb}';">`;
    }
    if (a.t === 'CATALOG') return `<div class="pdf-glyph glyph-cat"><span class="ico">⌕</span><span>${esc(a.cat||'Catalog')}</span></div>`;
    return `<div class="pdf-glyph"><span class="ico">PDF</span><span>${esc(a.ag||'Document')}</span></div>`;
  }
  function metaFor(a) {
    const rows = [];
    if (a.ag)     rows.push(['Agency', a.ag]);
    if (a.cat)    rows.push(['Category', a.cat]);
    if (a.region) rows.push(['Region', a.region]);
    if (a.date)   rows.push(['Date', a.date]);
    return `<dl class="card-meta">${rows.map(r=>`<dt>${r[0]}</dt><dd>${esc(r[1])}</dd>`).join('')}</dl>`;
  }
  function actionsFor(a) {
    const out = [];
    if (a.l) {
      out.push(`<a href="#" data-action="open">Open PDF</a>`);
      out.push(`<a href="./${esc(a.l)}" download>Download</a>`);
    } else if (a.u && a.t === 'PDF') {
      out.push(`<a href="${esc(a.u)}" target="_blank" rel="noopener">Open PDF</a>`);
    }
    const src = a.s || a.u;
    if (src) out.push(`<a class="warn" href="${esc(src)}" target="_blank" rel="noopener">${a.t==='CATALOG'?'Open ↗':'Source ↗'}</a>`);
    return `<div class="card-actions">${out.join('')}</div>`;
  }
  function cardHtml(a, gidx) {
    const localBadge = a.l ? '<span class="badge local">LOCAL</span>' : '<span class="badge source">SOURCE</span>';
    return `<article class="card" data-idx="${gidx}">
      <div class="card-media">
        ${glyphFor(a)}
        <span class="badge">${esc(a.t)}</span>
        ${a.t!=='CATALOG'?localBadge:''}
      </div>
      <div class="card-body">
        <div class="card-title">${esc(a.ti)}</div>
        ${a.de?`<div class="card-desc">${esc(a.de)}</div>`:''}
        ${metaFor(a)}
        ${actionsFor(a)}
      </div>
    </article>`;
  }

  function filtered() {
    return items.filter(a => {
      if (state.tab !== 'ALL' && a.t !== state.tab) return false;
      if (state.q) {
        const hay = [a.ti,a.de,a.ag,a.cat,a.date,a.region].join(' ').toLowerCase();
        if (!hay.includes(state.q)) return false;
      }
      return true;
    });
  }
  const grid = document.getElementById('arch-grid');
  const emptyEl = document.getElementById('arch-empty');
  function render() {
    const list = filtered();
    if (window._lb) window._lb.setList(list);
    if (grid) grid.innerHTML = list.map((a,i) => cardHtml(a,i)).join('');
    if (emptyEl) emptyEl.hidden = list.length > 0;
  }
  render();

  if (grid) {
    grid.addEventListener('click', e => {
      const action = e.target.closest('a[data-action]');
      const card   = e.target.closest('.card');
      const media  = e.target.closest('.card-media');
      if (action) e.preventDefault();
      if (card && card.dataset.idx !== undefined && (action || media)) {
        const a = (window._lb ? window._lb.getList() : [])[parseInt(card.dataset.idx, 10)];
        if (a && a.t === 'CATALOG') { window.open(a.u || a.s, '_blank'); return; }
        if (window._lb) window._lb.open(parseInt(card.dataset.idx, 10));
      }
    });
  }
})();
'''
