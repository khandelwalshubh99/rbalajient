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

  var form = document.getElementById('quote-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = document.getElementById('qf-name').value || '';
      var company = document.getElementById('qf-company').value || '';
      var contact = document.getElementById('qf-contact').value || '';
      var message = document.getElementById('qf-message').value || '';
      var subject = 'Quote Request' + (company ? ' - ' + company : '');
      var body = [
        'Name: ' + name,
        'Company: ' + company,
        'Phone / Email: ' + contact,
        '',
        'Requirement:',
        message
      ].join('\n');
      var mailto = 'mailto:sales@rbalajient.com?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      window.location.href = mailto;
    });
  }
});
