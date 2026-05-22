/* realufo.org related-media component.
 *
 * Mounts: any element with id="related-media" and data-keywords="..."
 *         (comma-separated). Optional data-archive="aaro" prefers same-archive
 *         records when ranking ties. Optional data-limit="6" caps results.
 *
 * Data:   /api/all.json (4,800+ records across 15 archives).
 *
 * Render: horizontal-scroll row of cards. Each card is a record with title,
 *         site badge, type tag, thumbnail (if `thumb` field) or media glyph,
 *         and an Open button that uses the same in-page lightbox the search
 *         page uses (or new-tab for cross-origin PDFs).
 *
 * Vanilla JS, no deps. CSP-safe. Re-runs are idempotent.
 */
(function() {
  'use strict';

  function esc(s){return String(s||'').replace(/[&<>"']/g,function(c){return({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]})}
  function truncate(s,n){s=String(s||'');return s.length<=n?s:s.slice(0,n).replace(/\s+\S*$/,'')+'…';}

  function detectMedia(url) {
    var u = (url || '').toLowerCase().split('?')[0].split('#')[0];
    if (/\.(mp4|m4v|mov|webm)$/.test(u)) return 'video';
    if (/\.(jpe?g|png|gif|webp|avif)$/.test(u)) return 'image';
    if (/\.pdf$/.test(u)) return 'pdf';
    if (/(youtube\.com|youtu\.be|vimeo\.com)/.test(u)) return 'embed';
    return 'link';
  }

  function resolveUrl(rec, field) {
    var val = rec[field] || '';
    if (!val) return '';
    if (/^https?:\/\//i.test(val)) return val;
    var dir = rec.archiveDir || (rec.archive ? rec.archive + '/' : '');
    if (dir && !/^\//.test(val)) return '/' + dir + val.replace(/^\.?\//,'');
    return val;
  }

  function scoreRecord(rec, terms, preferArchive) {
    var hay = ((rec.title || '') + ' ' +
               (rec.description || '') + ' ' +
               (rec.region || '') + ' ' +
               (rec.agency || '')).toLowerCase();
    var score = 0;
    for (var i = 0; i < terms.length; i++) {
      var t = terms[i].toLowerCase().trim();
      if (!t) continue;
      if (hay.indexOf(t) === -1) continue;
      score += 2;
      if ((rec.title || '').toLowerCase().indexOf(t) !== -1) score += 4;
      if ((rec.region || '').toLowerCase().indexOf(t) !== -1) score += 1;
    }
    if (score && preferArchive && rec.archive === preferArchive) score += 1;
    /* Prefer records with local media or a remote URL — boost actionable ones */
    if (rec.local) score += score ? 1 : 0;
    if (rec.thumb) score += score ? 1 : 0;
    return score;
  }

  function recordKind(rec) {
    var local = (rec.local || '').toLowerCase();
    var url   = (rec.url || '').toLowerCase();
    var type  = (rec.type || rec.category || '').toLowerCase();
    if (/\.(mp4|m4v|mov|webm)$/.test(local) || /\.(mp4|m4v|mov|webm)$/.test(url) || /video|vid/.test(type)) return 'video';
    if (/\.(jpe?g|png|gif|webp)$/.test(local) || /\.(jpe?g|png|gif|webp)$/.test(url) || /imag|photo/.test(type)) return 'image';
    if (/\.pdf$/.test(local) || /\.pdf$/.test(url) || /pdf|report|memo|brief|document/.test(type)) return 'pdf';
    if (/catalog|series|finding aid/.test(type)) return 'catalog';
    return 'item';
  }

  /* Build a once-per-page lightbox. Caller wires .open(rec). */
  function makeLightbox() {
    if (document.getElementById('rm-lb')) return;
    var s = document.createElement('style');
    s.textContent = (
      '#rm-lb{position:fixed;inset:0;z-index:10000;background:rgba(0,0,0,0.92);display:none;align-items:center;justify-content:center;padding:24px}' +
      '#rm-lb.open{display:flex}' +
      '#rm-lb .lb-inner{max-width:96vw;max-height:90vh;display:flex;flex-direction:column;align-items:center;gap:10px}' +
      '#rm-lb img,#rm-lb video{max-width:96vw;max-height:80vh;border:1px solid rgba(232,227,216,0.28);background:#000}' +
      '#rm-lb iframe{width:96vw;height:80vh;background:#fff;border:1px solid rgba(232,227,216,0.28);border-radius:6px}' +
      '#rm-lb .meta{font-family:"JetBrains Mono",monospace;font-size:11px;color:#a8a298;letter-spacing:0.06em;text-align:center;max-width:680px;line-height:1.55}' +
      '#rm-lb .meta strong{color:#e8e3d8;font-family:"Source Serif 4",serif;font-size:14px;font-weight:600;display:block;margin-bottom:4px;text-transform:none;letter-spacing:0}' +
      '#rm-lb .meta a{color:var(--accent,#d4a017);text-decoration:none;border-bottom:1px dotted}' +
      '#rm-lb .close{position:absolute;top:16px;right:16px;background:rgba(0,0,0,0.55);border:1px solid rgba(232,227,216,0.28);width:40px;height:40px;border-radius:50%;color:#e8e3d8;font-size:22px;cursor:pointer;display:flex;align-items:center;justify-content:center}'
    );
    document.head.appendChild(s);
    var d = document.createElement('div');
    d.id = 'rm-lb';
    d.innerHTML = '<button class="close" aria-label="Close">×</button><div class="lb-inner"></div>';
    document.body.appendChild(d);
    d.addEventListener('click', function(e){ if (e.target === d || e.target.classList.contains('close')) close(); });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape') close(); });
    function close(){ d.classList.remove('open'); d.querySelector('.lb-inner').innerHTML = ''; }
    window._rmLb = d;
  }

  function openInLightbox(rec) {
    makeLightbox();
    var d = window._rmLb;
    var inner = d.querySelector('.lb-inner');
    var local = resolveUrl(rec, 'local');
    var url   = resolveUrl(rec, 'url');
    var src   = resolveUrl(rec, 'src');
    var primary = local || url || src;
    if (!primary) return false;
    var kind = detectMedia(local) !== 'link' ? detectMedia(local) : detectMedia(url || src);

    var meta = (
      '<div class="meta"><strong>' + esc(rec.title || '') + '</strong>' +
      esc(rec.archiveLabel || rec.site || rec.archive || '') +
      (rec.date ? ' · ' + esc(rec.date) : '') +
      (src && src !== primary ? '<br><a href="' + esc(src) + '" target="_blank" rel="noopener">Source ↗</a>' : '') +
      '</div>'
    );

    if (kind === 'video') {
      var srcs = '<source src="' + esc(primary) + '" type="video/mp4">';
      if (local && url && local !== url) srcs += '<source src="' + esc(url) + '" type="video/mp4">';
      inner.innerHTML = '<video controls autoplay playsinline>' + srcs + '</video>' + meta;
    } else if (kind === 'image') {
      var fb = (local && url) ? ' onerror="this.onerror=null;this.src=\'' + esc(url) + '\'"' : '';
      inner.innerHTML = '<img src="' + esc(primary) + '" alt="' + esc(rec.title || '') + '"' + fb + '>' + meta;
    } else if (kind === 'pdf' && /^\//.test(primary)) {
      inner.innerHTML = '<iframe src="' + esc(primary) + '#view=FitH" allow="fullscreen"></iframe>' + meta;
    } else if (kind === 'embed') {
      var embed = primary
        .replace(/youtu\.be\/([\w-]+)/, 'www.youtube-nocookie.com/embed/$1')
        .replace(/youtube\.com\/watch\?v=([\w-]+)/, 'www.youtube-nocookie.com/embed/$1')
        .replace(/vimeo\.com\/(\d+)/, 'player.vimeo.com/video/$1');
      inner.innerHTML = '<iframe src="https://' + esc(embed.replace(/^https?:\/\//,'')) + '?autoplay=1" allow="autoplay;encrypted-media;fullscreen" allowfullscreen></iframe>' + meta;
    } else {
      /* Cross-origin PDF / catalog / unknown — new tab */
      window.open(primary, '_blank', 'noopener');
      return true;
    }
    d.classList.add('open');
    return true;
  }

  function glyphFor(kind) {
    var icons = { video: '▶', image: '◐', pdf: 'PDF', catalog: '⌕', item: '◉' };
    return icons[kind] || '◉';
  }

  function renderCard(rec) {
    var kind = recordKind(rec);
    var local = resolveUrl(rec, 'local');
    var url   = resolveUrl(rec, 'url');
    var src   = resolveUrl(rec, 'src');
    var openable = local || url;
    var thumb = rec.thumb || '';
    var media = thumb
      ? '<img class="rm-thumb" src="' + esc(thumb) + '" alt="" loading="lazy" decoding="async" onerror="this.style.display=\'none\'">'
      : '<div class="rm-glyph">' + esc(glyphFor(kind)) + '</div>';
    var datapath = local || url || src;
    return (
      '<a class="rm-card rm-' + kind + '" href="' + esc(openable || src || '#') + '" data-rec-key="' + esc(datapath) + '" target="_blank" rel="noopener">' +
        '<div class="rm-media">' + media +
          '<span class="rm-badge">' + esc(rec.archive || '') + '</span>' +
          '<span class="rm-kind">' + esc(kind.toUpperCase()) + '</span>' +
        '</div>' +
        '<div class="rm-body">' +
          '<div class="rm-title">' + esc(truncate(rec.title || '(Untitled)', 90)) + '</div>' +
          (rec.date ? '<div class="rm-meta">' + esc(rec.date) + '</div>' : '') +
        '</div>' +
      '</a>'
    );
  }

  /* CSS injected once for the entire component. Scoped under #related-media. */
  function injectCss() {
    if (document.getElementById('rm-css')) return;
    var s = document.createElement('style');
    s.id = 'rm-css';
    s.textContent = (
      '#related-media{margin:18px 0 24px}' +
      '#related-media .rm-hdr{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:10px;font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:var(--accent,#d4a017);font-weight:700}' +
      '#related-media .rm-hdr small{color:var(--ink-faint,#6b665d);font-weight:500;letter-spacing:0.08em}' +
      '#related-media .rm-rail{display:grid;grid-auto-flow:column;grid-auto-columns:200px;gap:10px;overflow-x:auto;overflow-y:hidden;scroll-snap-type:x mandatory;padding:4px 4px 14px;scrollbar-width:thin;scrollbar-color:var(--rule-strong,#3a352d) transparent}' +
      '#related-media .rm-rail::-webkit-scrollbar{height:6px}' +
      '#related-media .rm-rail::-webkit-scrollbar-thumb{background:var(--rule-strong,#3a352d);border-radius:3px}' +
      '#related-media .rm-card{flex:0 0 200px;background:var(--bg-2,#111114);border:1px solid var(--rule,rgba(232,227,216,0.12));border-radius:6px;text-decoration:none;color:inherit;scroll-snap-align:start;display:flex;flex-direction:column;overflow:hidden;transition:border-color 0.2s,transform 0.2s}' +
      '#related-media .rm-card:hover{border-color:var(--accent,#d4a017);transform:translateY(-2px)}' +
      '#related-media .rm-media{aspect-ratio:16/10;background:#0a0a0c;position:relative;display:grid;place-items:center;overflow:hidden;border-bottom:1px solid var(--rule,rgba(232,227,216,0.12))}' +
      '#related-media .rm-thumb{width:100%;height:100%;object-fit:cover;display:block}' +
      '#related-media .rm-glyph{font-family:"JetBrains Mono",monospace;font-size:22px;color:var(--accent,#d4a017);background:repeating-linear-gradient(45deg,#1a1a1f,#1a1a1f 8px,#15151a 8px,#15151a 16px);width:100%;height:100%;display:grid;place-items:center;font-weight:700;letter-spacing:0.04em}' +
      '#related-media .rm-badge,#related-media .rm-kind{position:absolute;font-family:"JetBrains Mono",monospace;font-size:8px;letter-spacing:0.1em;text-transform:uppercase;padding:2px 5px;border-radius:2px;font-weight:700;background:rgba(10,10,12,0.85);color:#e8e3d8}' +
      '#related-media .rm-badge{top:6px;left:6px;color:var(--accent,#d4a017);border:1px solid rgba(212,160,23,0.4)}' +
      '#related-media .rm-kind{top:6px;right:6px;color:var(--ink-dim,#a8a298)}' +
      '#related-media .rm-body{padding:10px 12px;display:flex;flex-direction:column;gap:4px}' +
      '#related-media .rm-title{font-family:"Source Serif 4",Georgia,serif;font-size:13px;color:var(--ink,#e8e3d8);font-weight:600;line-height:1.35;overflow:hidden;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical}' +
      '#related-media .rm-meta{font-family:"JetBrains Mono",monospace;font-size:10px;color:var(--ink-faint,#6b665d);letter-spacing:0.06em}' +
      '#related-media .rm-empty{font-family:"JetBrains Mono",monospace;font-size:11px;color:var(--ink-faint,#6b665d);padding:10px 0;letter-spacing:0.06em}'
    );
    document.head.appendChild(s);
  }

  function init() {
    var mount = document.getElementById('related-media');
    if (!mount) return;
    var kws = (mount.dataset.keywords || '').split(',').map(function(x){return x.trim();}).filter(Boolean);
    if (!kws.length) { mount.remove(); return; }
    var preferArc = (mount.dataset.archive || '').trim().toLowerCase();
    var limit = parseInt(mount.dataset.limit || '6', 10);
    injectCss();

    mount.innerHTML = (
      '<div class="rm-hdr">◉ Related media in the archive <small>loading…</small></div>' +
      '<div class="rm-empty">Searching ' + (preferArc ? esc(preferArc) + ' + ' : '') + 'cross-archive records…</div>'
    );

    fetch('/api/all.json', { cache: 'force-cache' })
      .then(function(r){ if (!r.ok) throw 0; return r.json(); })
      .then(function(data) {
        var records = data.records || [];
        var scored = [];
        for (var i = 0; i < records.length; i++) {
          var s = scoreRecord(records[i], kws, preferArc);
          if (s > 0) scored.push({ s: s, r: records[i] });
        }
        scored.sort(function(a,b){ return b.s - a.s; });
        /* De-duplicate by URL */
        var seen = {}; var picked = [];
        for (var j = 0; j < scored.length && picked.length < limit; j++) {
          var rec = scored[j].r;
          var key = (rec.local || rec.url || rec.src || rec.title || '').toString();
          if (seen[key]) continue;
          seen[key] = 1;
          picked.push(rec);
        }
        if (!picked.length) {
          mount.innerHTML = (
            '<div class="rm-hdr">◉ Related media in the archive <small>no matches</small></div>' +
            '<div class="rm-empty">No catalogue records match these keywords yet. Weekly cron will retry the source agencies.</div>'
          );
          return;
        }
        mount.innerHTML = (
          '<div class="rm-hdr">◉ Related media in the archive <small>' + picked.length + ' record' + (picked.length===1?'':'s') + '</small></div>' +
          '<div class="rm-rail">' + picked.map(renderCard).join('') + '</div>'
        );
        /* Click delegate: open in lightbox when same-origin / known media */
        mount.querySelector('.rm-rail').addEventListener('click', function(e) {
          if (e.metaKey || e.ctrlKey || e.shiftKey) return;  /* let modifier-click open new tab */
          var card = e.target.closest('.rm-card');
          if (!card) return;
          var key = card.getAttribute('data-rec-key');
          if (!key) return;
          var rec = null;
          for (var k = 0; k < picked.length; k++) {
            var r = picked[k];
            if ((r.local || r.url || r.src) === key) { rec = r; break; }
          }
          if (!rec) return;
          /* Cross-origin URLs without a known media extension → let browser handle */
          var primary = resolveUrl(rec, 'local') || resolveUrl(rec, 'url') || resolveUrl(rec, 'src');
          var kind = detectMedia(primary);
          if (kind === 'link' && /^https?:\/\//.test(primary)) return;
          e.preventDefault();
          openInLightbox(rec);
        });
      })
      .catch(function() {
        mount.innerHTML = '<div class="rm-empty">/api/all.json not reachable — try a hard refresh.</div>';
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
