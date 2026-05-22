/* realufo.org Web Share API integration.
 *
 * Renders a Share button into #share-mount. On supporting browsers (mobile
 * Safari, Chrome Android, Edge desktop), tap fires navigator.share() with the
 * page title + canonical URL. Elsewhere, falls back to copy-to-clipboard.
 */
(function() {
  'use strict';

  function init() {
    var mount = document.getElementById('share-mount');
    if (!mount) return;

    var canSysShare = typeof navigator.share === 'function';

    var label = canSysShare ? 'Share this case' : 'Copy link';
    mount.innerHTML = (
      '<button type="button" class="share-btn" aria-label="' + label + '">' +
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>' +
      '<line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>' +
      '</svg>' +
      '<span>' + label + '</span>' +
      '</button>'
    );

    var canon = document.querySelector('link[rel="canonical"]');
    var url   = canon ? canon.href : window.location.href;
    var title = document.title.split(' · ')[0];
    var text  = document.querySelector('meta[name="description"]');
    var desc  = text ? text.getAttribute('content') : '';

    mount.querySelector('button').addEventListener('click', function() {
      if (canSysShare) {
        navigator.share({ title: title, text: desc, url: url }).catch(function(){ /* user cancel */ });
        return;
      }
      var btn = mount.querySelector('button');
      var span = btn.querySelector('span');
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(function() {
          var orig = span.textContent;
          span.textContent = 'Copied ✓';
          btn.classList.add('copied');
          setTimeout(function(){ span.textContent = orig; btn.classList.remove('copied'); }, 1400);
        });
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
