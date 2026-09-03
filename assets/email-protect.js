// Hydrates any [data-em] link into a real mailto: at runtime, so the address
// never sits in plaintext in the HTML a scraper downloads. A JS-executing
// visitor (or Google's own renderer) sees a normal, clickable email link
// within a frame or two; a plain-text harvester sees an opaque base64 token
// and no "@" anywhere near it.
//
// Markup contract:
//   data-em          required, base64 of the address
//   data-subject     optional, mailto ?subject=
//   data-body        optional, mailto &body=
//   class="js-email-text"   also replace the link's visible text with the
//                           decoded address (omit to keep existing text,
//                           e.g. a "Request a Quote" button)
(function () {
  function hydrate() {
    document.querySelectorAll('[data-em]').forEach(function (el) {
      var addr = atob(el.getAttribute('data-em'));
      var q = [];
      var subject = el.getAttribute('data-subject');
      var body = el.getAttribute('data-body');
      if (subject) q.push('subject=' + encodeURIComponent(subject));
      if (body) q.push('body=' + encodeURIComponent(body));
      el.href = 'mailto:' + addr + (q.length ? '?' + q.join('&') : '');
      if (el.classList.contains('js-email-text')) el.textContent = addr;
      el.removeAttribute('data-em');
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', hydrate);
  } else {
    hydrate();
  }
})();
