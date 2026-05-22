/* realufo.org case citation export — BibTeX / RIS / CSL JSON.
 *
 * Looks up metadata from the page's JSON-LD <script type="application/ld+json">
 * Article block, falls back to OpenGraph meta tags, and renders a small panel
 * of copy-to-clipboard buttons in the element with id="cite-mount".
 *
 * Vanilla JS, no deps. CSP-safe (uses navigator.clipboard).
 */
(function() {
  'use strict';

  function pickJsonLd() {
    var scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (var i = 0; i < scripts.length; i++) {
      try {
        var d = JSON.parse(scripts[i].textContent.trim());
        if (d && (d['@type'] === 'Article' || d['@type'] === 'NewsArticle' || d['@type'] === 'ScholarlyArticle')) {
          return d;
        }
      } catch (e) { /* skip */ }
    }
    return null;
  }

  function metaContent(prop, isName) {
    var sel = isName ? 'meta[name="' + prop + '"]' : 'meta[property="' + prop + '"]';
    var el = document.querySelector(sel);
    return el ? el.getAttribute('content') : '';
  }

  function gather() {
    var ld = pickJsonLd() || {};
    var pub = (ld.publisher && ld.publisher.name) || 'realufo.org';
    var src = (ld.sourceOrganization && ld.sourceOrganization.name) || '';
    var title = ld.headline || document.title.split(' · ')[0] || metaContent('og:title');
    var url   = ld.url || metaContent('og:url') || window.location.href;
    var date  = ld.datePublished || '';
    var desc  = ld.description || metaContent('og:description') || metaContent('description', true) || '';
    var year  = (date.match(/^\d{4}/) || ['n.d.'])[0];
    var slug  = (url.match(/\/([^/]+)\.html$/) || ['', 'case'])[1];
    return {
      key: 'realufo-' + slug + '-' + year,
      title: title.trim(),
      url: url, date: date, year: year, desc: desc,
      pub: pub, src: src,
    };
  }

  function bibtex(c) {
    return (
      '@misc{' + c.key + ',\n' +
      '  title       = {{' + c.title.replace(/[{}]/g, '') + '}},\n' +
      '  author      = {{realufo.org}},\n' +
      '  year        = {' + c.year + '},\n' +
      (c.src ? '  organization= {{' + c.src + '}},\n' : '') +
      '  howpublished= {\\url{' + c.url + '}},\n' +
      '  note        = {' + (c.desc ? c.desc.slice(0, 200).replace(/[{}]/g, '') : 'Mirrored case file') + '}\n' +
      '}'
    );
  }

  function ris(c) {
    return (
      'TY  - GEN\n' +
      'TI  - ' + c.title + '\n' +
      'AU  - realufo.org\n' +
      (c.src ? 'PB  - ' + c.src + '\n' : '') +
      (c.date ? 'PY  - ' + c.year + '\n' + 'DA  - ' + c.date.slice(0,10) + '\n' : '') +
      'UR  - ' + c.url + '\n' +
      (c.desc ? 'AB  - ' + c.desc.replace(/\n/g, ' ') + '\n' : '') +
      'ER  -'
    );
  }

  function csl(c) {
    var obj = {
      id: c.key,
      type: 'webpage',
      title: c.title,
      author: [{ literal: 'realufo.org' }],
      issued: c.date ? { 'date-parts': [c.year ? [parseInt(c.year, 10)] : []] } : undefined,
      URL: c.url,
      abstract: c.desc || undefined,
      publisher: c.src || c.pub,
    };
    return JSON.stringify(obj, null, 2);
  }

  function copyToClipboard(text, btn) {
    var done = function() {
      var orig = btn.textContent;
      btn.textContent = 'Copied ✓';
      btn.classList.add('copied');
      setTimeout(function(){ btn.textContent = orig; btn.classList.remove('copied'); }, 1400);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(function() {
        fallback(text); done();
      });
    } else {
      fallback(text); done();
    }
  }
  function fallback(text) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.left = '-9999px';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
  }

  function init() {
    var mount = document.getElementById('cite-mount');
    if (!mount) return;
    var c = gather();
    if (!c.title) return;

    var html = (
      '<div class="cite-box">' +
      '<h3>Cite this case</h3>' +
      '<div class="cite-buttons">' +
      '<button type="button" data-fmt="bibtex">BibTeX</button>' +
      '<button type="button" data-fmt="ris">RIS</button>' +
      '<button type="button" data-fmt="csl">CSL JSON</button>' +
      '<button type="button" data-fmt="url">Permalink</button>' +
      '</div>' +
      '<pre class="cite-out" id="cite-out" tabindex="0"></pre>' +
      '<div class="cite-hint">For academic, journalistic, and FOIA chain-of-source use. Cite the source agency too — we are mirrors, not authors.</div>' +
      '</div>'
    );
    mount.innerHTML = html;

    var out = document.getElementById('cite-out');
    var current = bibtex(c);
    out.textContent = current;

    mount.querySelector('.cite-buttons').addEventListener('click', function(e) {
      var btn = e.target.closest('button[data-fmt]');
      if (!btn) return;
      var fmt = btn.dataset.fmt;
      if (fmt === 'bibtex') current = bibtex(c);
      else if (fmt === 'ris') current = ris(c);
      else if (fmt === 'csl') current = csl(c);
      else if (fmt === 'url') current = c.url;
      out.textContent = current;
      copyToClipboard(current, btn);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
