// Hydrates any [data-em] link into a real mailto: at runtime, so the address
// never sits in plaintext in the HTML a scraper downloads. A JS-executing
// visitor (or Google's own renderer) sees a normal, clickable email link;
// a plain-text harvester sees an opaque base64 token and no "@" anywhere.
//
// Markup contract:
//   data-em          required, base64 of the address
//   data-subject     optional, mailto ?subject=
//   data-body        optional, mailto &body=
//   class="js-email-text"   also replace the link's visible text with the
//                           decoded address (omit to keep existing text,
//                           e.g. a "Request a Quote" button)
//
// The [data-em] markup is server-rendered HTML on most pages, but on the
// home page it's produced client-side by a separate component framework
// (support.js) whose own render timing this script has no visibility into
// -- a single DOMContentLoaded-or-immediate pass can lose that race and
// silently hydrate nothing. A MutationObserver alongside the immediate pass
// makes this correct regardless of when (or how many times) that framework
// renders, instead of depending on a guessed-right moment.
(function () {
  function hydrateOne(el) {
    var addr = atob(el.getAttribute('data-em'));
    var q = [];
    var subject = el.getAttribute('data-subject');
    var body = el.getAttribute('data-body');
    if (subject) q.push('subject=' + encodeURIComponent(subject));
    if (body) q.push('body=' + encodeURIComponent(body));
    el.href = 'mailto:' + addr + (q.length ? '?' + q.join('&') : '');
    if (el.classList.contains('js-email-text')) el.textContent = addr;
    el.removeAttribute('data-em');
  }

  function sweep() {
    document.querySelectorAll('[data-em]').forEach(hydrateOne);
  }

  sweep();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', sweep);
  }
  window.addEventListener('load', sweep);

  if (window.MutationObserver && document.documentElement) {
    var observer = new MutationObserver(sweep);
    observer.observe(document.documentElement, { childList: true, subtree: true });
    // Nothing plausibly renders new [data-em] markup after the page has
    // been idle this long; stop watching rather than run forever.
    setTimeout(function () { observer.disconnect(); }, 15000);
  }
})();
