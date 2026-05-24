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
/* Rich meta panel — title + structured fields + description + source links.
   Sized to keep the media generous; scrolls internally on long descriptions. */
.lb-meta { font-family: var(--mono); font-size: 11px; color: var(--ink); background: var(--bg-2); border: 1px solid var(--rule-strong); padding: 10px 14px; max-width: min(720px, 92vw); width: 100%; text-align: left; box-sizing: border-box; max-height: 32vh; overflow-y: auto; }
.lb-meta a { color: var(--caution); }
.lb-meta .lbm-title { font-family: var(--serif); font-size: 15px; font-weight: 600; color: var(--ink); margin-bottom: 6px; line-height: 1.35; }
.lb-meta .lbm-red { display: inline-block; font-family: var(--mono); font-size: 9px; letter-spacing: 0.14em; color: var(--stamp); border: 1px solid rgba(185,28,28,0.55); padding: 1px 6px; border-radius: 3px; margin-left: 8px; vertical-align: middle; }
.lb-meta .lbm-fields { display: grid; grid-template-columns: max-content 1fr; gap: 3px 12px; margin: 6px 0 8px; font-size: 10.5px; }
.lb-meta .lbm-fields dt { color: var(--ink-faint); letter-spacing: 0.1em; text-transform: uppercase; font-size: 9.5px; }
.lb-meta .lbm-fields dd { color: var(--ink-dim); margin: 0; overflow-wrap: anywhere; }
.lb-meta .lbm-desc { font-family: var(--serif); font-size: 13px; color: var(--ink-dim); line-height: 1.55; margin: 6px 0 8px; white-space: pre-wrap; overflow-wrap: anywhere; }
.lb-meta .lbm-links { display: flex; flex-wrap: wrap; gap: 6px 12px; padding-top: 6px; border-top: 1px solid var(--rule); font-size: 10.5px; letter-spacing: 0.08em; }
.lb-meta .lbm-links a { text-decoration: none; }
.lb-meta .lbm-links a:hover { text-decoration: underline; }
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
  /* Build rich meta panel — every related field on the asset, normalized
     across short (ti/ag/dt/lo/de/u/s/…) and long (title/agency/date/…) key
     variants used by different build scripts. */
  function metaPanel(a) {
    function g() { for (var i=0;i<arguments.length;i++){var k=arguments[i]; if (a && a[k]) return a[k];} return ''; }
    var title = g('title','ti');
    var agency = g('agency','ag');
    var date = g('date','dt','incidentDate','incident_date');
    var releaseDate = g('releaseDate','release_date');
    var location = g('location','lo','region','re','incidentLocation','incident_location');
    var type = g('type','t','category','ca');
    var classification = g('classification','cl','status');
    var virin = g('virin');
    var dvidsId = g('dvidsId','dvids');
    var videoTitle = g('videoTitle');
    var vidPair = g('vidPairing','videoPairing');
    var pdfPair = g('pdfPairing');
    var alt = g('alt','altText','imageAlt');
    var desc = g('desc','de','description','blurb','descriptionBlurb');
    var src = g('src','s','sourceUrl');
    var url = g('url','u','downloadUrl');
    var local = g('local','l');
    var redacted = a && (a.redacted === true || a.r === true || String(a.redaction||'').toUpperCase() === 'TRUE');
    var rows = [];
    function add(k,v){ if (v) rows.push('<div><dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd></div>'); }
    add('Agency', agency);
    add('Type', type);
    add('Date', date);
    if (releaseDate && releaseDate !== date) add('Released', releaseDate);
    add('Location', location);
    add('Classification', classification);
    add('VIRIN', virin);
    if (dvidsId) rows.push('<div><dt>DVIDS</dt><dd><a href="https://www.dvidshub.net/video/' + encodeURIComponent(dvidsId) + '" target="_blank" rel="noopener">' + esc(dvidsId) + ' &#8599;</a></dd></div>');
    add('Video title', videoTitle);
    add('Video pairing', vidPair);
    add('PDF pairing', pdfPair);
    add('Alt text', alt);
    var html = '<div class="lb-meta">';
    if (title) html += '<div class="lbm-title">' + esc(title) + (redacted ? ' <span class="lbm-red">REDACTED</span>' : '') + '</div>';
    if (rows.length) html += '<dl class="lbm-fields">' + rows.join('') + '</dl>';
    if (desc) html += '<div class="lbm-desc">' + esc(desc) + '</div>';
    var links = [];
    if (src) links.push('<a href="' + esc(src) + '" target="_blank" rel="noopener">Source &#8599;</a>');
    var openUrl = url || (local && (String(local).startsWith('http') ? local : './' + local));
    if (openUrl && openUrl !== src) links.push('<a href="' + esc(openUrl) + '" target="_blank" rel="noopener">Open &#8599;</a>');
    if (links.length) html += '<div class="lbm-links">' + links.join(' &middot; ') + '</div>';
    html += '</div>';
    return html;
  }
  function render() {
    var a = list[idx]; if (!a) return;
    var href = a.local || a.l || a.url || a.u || '';
    if (a.l) href = a.l.startsWith('http') ? a.l : './' + a.l;
    var t = href.toLowerCase().split('?')[0].split('#')[0];
    var meta = metaPanel(a);
    var html = '';
    /* Pre-baked YouTube/Vimeo embed (NASA UAP videos use this field). */
    if (a.embed) {
      html = '<iframe src="' + esc(a.embed) + (a.embed.indexOf('?')>=0?'&':'?') + 'autoplay=1" allow="autoplay; encrypted-media" allowfullscreen></iframe>' + meta;
    }
    /* CATALOG records (live web pages — CSP often blocks iframe). */
    else if (a.t === 'CATALOG' || a.type === 'CATALOG') {
      window.open(a.u || a.url || a.s || a.src, '_blank'); close(); return;
    }
    else if (/\.(jpe?g|png|gif|webp|avif|svg)$/.test(t)) {
      /* IMG with remote fallback: when local copy fails, swap to a.url
         (AARO carousel imagery uses this — release URL is the safe net). */
      var fb = (a.l && (a.u || a.url)) ? ' onerror="this.onerror=null;this.src=\''+esc(a.u || a.url)+'\';"' : '';
      html = '<img src="'+esc(href)+'" alt="'+esc(title)+'"' + fb + '>' + meta;
    }
    else if (/\.(mp4|webm|mov)$/.test(t)) {
      /* Multi-source: prefer local, fall back to remote inside the <video>. */
      var srcs = '';
      var loc = a.l ? './' + a.l : '';
      var rem = a.u || a.url || '';
      if (loc) srcs += '<source src="'+esc(loc)+'" type="video/mp4">';
      if (rem && rem !== loc) srcs += '<source src="'+esc(rem)+'" type="video/mp4">';
      html = '<video controls autoplay playsinline>'+srcs+'</video>' + meta;
    }
    else if (/\.(mp3|wav|ogg|m4a)$/.test(t))         html = '<audio controls autoplay src="'+esc(href)+'"></audio>' + meta;
    else if (/\.pdf$/.test(t)) {
      /* GitHub Release URLs serve with Content-Disposition: attachment so
         iframe-embed fails. Local PDFs render fine. Route release URLs to
         a new tab instead of attempting an embed that just downloads. */
      if (a.l) html = '<iframe src="'+esc(href)+'#view=FitH"></iframe>' + meta;
      else { window.open(href, '_blank'); close(); return; }
    }
    else if (/\.html?$/.test(t))                     html = '<iframe src="'+esc(href)+'" sandbox="allow-same-origin allow-popups"></iframe>' + meta;
    else                                             html = meta;
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
