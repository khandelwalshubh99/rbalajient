document.addEventListener('DOMContentLoaded', function () {
  var toggleBtn = document.querySelector('.nav-toggle');
  var mobileNav = document.querySelector('.mobile-nav');
  if (toggleBtn && mobileNav) {
    toggleBtn.addEventListener('click', function () {
      mobileNav.classList.toggle('open');
    });
    mobileNav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { mobileNav.classList.remove('open'); });
    });
  }

  function val(id) {
    var el = document.getElementById(id);
    return el ? el.value : '';
  }

  function mailto(subject, lines) {
    return 'mailto:sales@rbalajient.com?subject=' + encodeURIComponent(subject) +
      '&body=' + encodeURIComponent(lines.join('\n'));
  }

  // Homepage quote form.
  var form = document.getElementById('quote-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var company = val('qf-company');
      window.location.href = mailto('Quote Request' + (company ? ' - ' + company : ''), [
        'Name: ' + val('qf-name'),
        'Company: ' + company,
        'Phone / Email: ' + val('qf-contact'),
        '',
        'Requirement:',
        val('qf-message')
      ]);
    });
  }

  // Enquiry form on the generated industry, catalogue and product-type pages.
  // The segment (or product type) it was sent from travels with the message so
  // the quote comes back in context.
  var enquiry = document.querySelector('.enquiry-form');
  if (enquiry) {
    enquiry.addEventListener('submit', function (e) {
      e.preventDefault();
      var company = val('ef-company');
      var segment = val('ef-segment');
      var tag = enquiry.getAttribute('data-segment') || '';
      window.location.href = mailto(
        'Enquiry' + (segment ? ' - ' + segment : '') + (company ? ' - ' + company : ''), [
          'Name: ' + val('ef-name'),
          'Company / Plant: ' + company,
          'Phone / Email: ' + val('ef-contact'),
          'Segment: ' + (segment || '—'),
          'Page: ' + tag,
          '',
          'Requirement:',
          val('ef-message')
        ]);
    });
  }
});
