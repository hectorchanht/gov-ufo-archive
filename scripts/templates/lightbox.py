"""Lightbox component — HTML markup + CSS + JS as named constants.

Single source of truth for the media viewer (image / video / PDF iframe).
Consumed by every build-*.py and by the SHARED_CSS body in _site_template.py
(which substitutes __LIGHTBOX_CSS__ at module load).
"""
from __future__ import annotations

LIGHTBOX_HTML = '''\
<div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Media viewer">
  <div class="lb-inner" id="lb-inner"></div>
  <button class="lb-rotate" id="lb-rotate" aria-label="Rotate view" title="Rotate">⟳</button>
  <button class="lb-close" id="lb-close" aria-label="Close (Escape)">✕</button>
  <button class="lb-nav prev" id="lb-prev" aria-label="Previous (←)">‹</button>
  <button class="lb-nav next" id="lb-next" aria-label="Next (→)">›</button>
  <div class="lb-counter" id="lb-counter"></div>
</div>'''


LIGHTBOX_CSS = r'''
.lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.96); display: none; align-items: center; justify-content: center; z-index: 200; padding: 16px; }
@media (min-width: 720px) { .lightbox { padding: 32px; } }
.lightbox.open { display: flex; }
.lb-inner { max-width: 92vw; max-height: 92vh; display: flex; flex-direction: column; gap: 10px; align-items: center; }
.lb-inner img, .lb-inner video { max-width: 90vw; max-height: 78vh; border: 1px solid var(--rule-strong); background: #000; }
/* Rotate-to-landscape button (mobile only) */
.lb-rotate { position: absolute; top: 12px; left: 12px; width: 40px; height: 40px; background: var(--bg-2); border: 1px solid var(--rule-strong); color: var(--ink); display: none; place-items: center; cursor: pointer; font-family: var(--mono); font-size: 18px; z-index: 3; transition: color .15s, border-color .15s; }
.lb-rotate:hover { color: var(--caution); border-color: var(--caution); }
@media (max-width: 719px) {
  .lightbox.open .lb-rotate { display: grid; }
  .lightbox.lb-rotated .lb-inner video,
  .lightbox.lb-rotated .lb-inner img { transform: rotate(90deg); max-width: 88vh; max-height: 88vw; width: auto; height: auto; }
  .lightbox.lb-rotated .lb-inner { max-height: none; max-width: none; }
}
.lb-inner iframe { width: 92vw; height: 84vh; border: 1px solid var(--rule-strong); background: #fff; }
.lb-meta { font-family: var(--mono); font-size: 11px; color: var(--ink); background: var(--bg-2); border: 1px solid var(--rule-strong); padding: 8px 14px; max-width: 90vw; text-align: center; }
.lb-meta a { color: var(--caution); }
.lb-close { position: absolute; top: 12px; right: 12px; width: 40px; height: 40px; background: var(--bg-2); border: 1px solid var(--rule-strong); color: var(--ink); display: grid; place-items: center; cursor: pointer; font-family: var(--mono); font-size: 22px; z-index: 2; }
.lb-nav { position: absolute; top: 50%; transform: translateY(-50%); width: 40px; height: 40px; background: rgba(20,20,24,0.6); border: 1px solid var(--rule-strong); color: var(--ink); display: grid; place-items: center; cursor: pointer; font-family: var(--serif); font-size: 24px; z-index: 2; transition: background .15s, color .15s, border-color .15s; }
@media (min-width: 720px) { .lb-nav { width: 52px; height: 52px; font-size: 32px; } }
.lb-nav:hover { background: rgba(0,0,0,0.85); color: var(--caution); border-color: var(--caution); }
.lb-nav.prev { left: 8px; } .lb-nav.next { right: 8px; }
@media (min-width: 720px) { .lb-nav.prev { left: 16px; } .lb-nav.next { right: 16px; } }
.lb-counter { position: absolute; top: 16px; left: 50%; transform: translateX(-50%); font-family: var(--mono); font-size: 11px; letter-spacing: 0.16em; color: var(--ink-dim); background: var(--bg-2); border: 1px solid var(--rule); padding: 4px 12px; z-index: 2; }
'''


LIGHTBOX_JS = r'''
/* Lightbox open/close/nav/rotate. Consumed inline by every page that
   embeds LIGHTBOX_HTML. The host page also exposes `window._lb` so build
   scripts can drive `openAt(idx)` from their per-page card grids. */
(function() {
  var lb     = document.getElementById('lightbox');
  if (!lb) return;
  var lbI    = document.getElementById('lb-inner');
  var lbC    = document.getElementById('lb-close');
  var lbP    = document.getElementById('lb-prev');
  var lbN    = document.getElementById('lb-next');
  var lbR    = document.getElementById('lb-rotate');
  var lbCnt  = document.getElementById('lb-counter');
  var list = [], idx = 0;
  function esc(s){return String(s||'').replace(/[&<>"']/g,function(c){return({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]})}
  function render() {
    var a = list[idx]; if (!a) return;
    var href = a.local || a.l || a.url || a.u || '';
    if (a.l) href = a.l.startsWith('http') ? a.l : './' + a.l;
    var t = href.toLowerCase().split('?')[0].split('#')[0];
    var title = a.title || a.ti || '';
    var meta = '<div class="lb-meta">' + esc(title) + '</div>';
    var html = '';
    /* Pre-baked YouTube/Vimeo embed (NASA UAP videos use this field). */
    if (a.embed) {
      html = '<iframe src="' + esc(a.embed) + (a.embed.indexOf('?')>=0?'&':'?') + 'autoplay=1" allow="autoplay; encrypted-media" allowfullscreen></iframe>' + meta;
    }
    /* CATALOG records (live web pages — CSP often blocks iframe). */
    else if (a.t === 'CATALOG' || a.type === 'CATALOG') {
      window.open(a.u || a.url || a.s || a.src, '_blank'); close(); return;
    }
    else if (/\.(jpe?g|png|gif|webp|avif)$/.test(t)) html = '<img src="'+esc(href)+'" alt="'+esc(title)+'">' + meta;
    else if (/\.(mp4|webm|mov)$/.test(t))            html = '<video controls autoplay playsinline><source src="'+esc(href)+'" type="video/mp4"></video>' + meta;
    else if (/\.(mp3|wav|ogg|m4a)$/.test(t))         html = '<audio controls autoplay src="'+esc(href)+'"></audio>' + meta;
    else if (/\.pdf$/.test(t)) {
      /* GitHub Release URLs serve with Content-Disposition: attachment so
         iframe-embed fails. Local PDFs render fine. Route release URLs to
         a new tab instead of attempting an embed that just downloads. */
      if (a.l) html = '<iframe src="'+esc(href)+'#view=FitH"></iframe>' + meta;
      else { window.open(href, '_blank'); close(); return; }
    }
    else if (/\.html?$/.test(t))                     html = '<iframe src="'+esc(href)+'" sandbox="allow-same-origin allow-popups"></iframe>' + meta;
    else                                             html = meta + '<a class="lb-meta" href="'+esc(href)+'" target="_blank" rel="noopener">Open ↗</a>';
    lbI.innerHTML = html;
    if (lbCnt) lbCnt.textContent = (idx+1) + ' / ' + list.length;
  }
  function open(i){ if (!list.length) return; idx = (i + list.length) % list.length; render(); lb.classList.add('open'); lb.setAttribute('aria-hidden','false'); }
  function nav(d){ if (!list.length) return; idx = (idx + d + list.length) % list.length; render(); }
  function close(){ lb.classList.remove('open'); lb.classList.remove('lb-rotated'); lb.setAttribute('aria-hidden','true'); lbI.innerHTML = ''; }
  if (lbC) lbC.addEventListener('click', close);
  if (lbP) lbP.addEventListener('click', function(e){ e.stopPropagation(); nav(-1); });
  if (lbN) lbN.addEventListener('click', function(e){ e.stopPropagation(); nav(1); });
  if (lbR) lbR.addEventListener('click', function(e){ e.stopPropagation(); lb.classList.toggle('lb-rotated'); });
  lb.addEventListener('click', function(e){ if (e.target === lb) close(); });
  document.addEventListener('keydown', function(e){
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowRight') nav(1);
    else if (e.key === 'ArrowLeft')  nav(-1);
  });
  /* swipe — horizontal > 50 px in < 800 ms */
  var sx=0,sy=0,st=0;
  lb.addEventListener('touchstart', function(e){ var t=e.changedTouches[0]; sx=t.clientX; sy=t.clientY; st=Date.now(); }, {passive:true});
  lb.addEventListener('touchend',   function(e){ var t=e.changedTouches[0]; var dx=t.clientX-sx, dy=t.clientY-sy, dt=Date.now()-st;
    if (dt < 800 && Math.abs(dx) > 50 && Math.abs(dy) < 60) nav(dx < 0 ? 1 : -1);
  }, {passive:true});
  window._lb = {
    open: open, close: close, nav: nav,
    setList: function(items){ list = items || []; },
    getList: function(){ return list; }
  };
})();
'''
