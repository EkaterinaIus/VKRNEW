/* ============================================================
   SIDEBAR TOGGLE (mobile)
   ============================================================ */
document.addEventListener('DOMContentLoaded', function () {
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebarOverlay');
  var toggleBtn = document.getElementById('sidebarToggle');
  var closeBtn = document.getElementById('sidebarClose');

  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add('show');
    if (overlay) { overlay.classList.remove('d-none'); }
  }

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove('show');
    if (overlay) { overlay.classList.add('d-none'); }
  }

  if (toggleBtn) toggleBtn.addEventListener('click', openSidebar);
  if (closeBtn) closeBtn.addEventListener('click', closeSidebar);
  if (overlay) overlay.addEventListener('click', closeSidebar);

  /* ============================================================
     ACCESS CODE MODAL
     ============================================================ */
  var accessModal = null;
  var pendingTargetUrl = '';
  var modalEl = document.getElementById('accessCodeModal');

  if (modalEl && typeof bootstrap !== 'undefined') {
    accessModal = new bootstrap.Modal(modalEl);
  }

  // Handle protected sidebar links
  document.querySelectorAll('.protected-link').forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      var targetUrl = this.dataset.targetUrl || this.getAttribute('href');
      var section = this.dataset.section || 'раздел';

      if (!DJANGO_CONTEXT.isAuthenticated) {
        window.location.href = '/accounts/login/?next=' + encodeURIComponent(targetUrl);
        return;
      }

      // If no access code set OR already verified → go directly
      if (!DJANGO_CONTEXT.hasAccessCode || DJANGO_CONTEXT.accessVerified) {
        window.location.href = targetUrl;
        return;
      }

      // Show modal
      pendingTargetUrl = targetUrl;
      var nameEl = document.getElementById('modalSectionName');
      if (nameEl) nameEl.textContent = '«' + section + '»';
      var errEl = document.getElementById('accessCodeError');
      if (errEl) errEl.classList.add('d-none');
      var inp = document.getElementById('accessCodeInput');
      if (inp) inp.value = '';
      if (accessModal) {
        accessModal.show();
        setTimeout(function () { if (inp) inp.focus(); }, 300);
      }
    });
  });

  // Submit code from modal
  var submitBtn = document.getElementById('accessCodeSubmit');
  if (submitBtn) {
    submitBtn.addEventListener('click', function () {
      verifyCode(pendingTargetUrl);
    });
  }

  var codeInput = document.getElementById('accessCodeInput');
  if (codeInput) {
    codeInput.addEventListener('keyup', function (e) {
      if (e.key === 'Enter') verifyCode(pendingTargetUrl);
      // Hide error on typing
      var err = document.getElementById('accessCodeError');
      if (err) err.classList.add('d-none');
    });
  }

  function verifyCode(targetUrl) {
    var inp = document.getElementById('accessCodeInput');
    var errEl = document.getElementById('accessCodeError');
    var code = inp ? inp.value.trim() : '';

    if (!code) {
      if (errEl) { errEl.textContent = 'Введите код'; errEl.classList.remove('d-none'); }
      return;
    }

    fetch(DJANGO_CONTEXT.verifyUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': DJANGO_CONTEXT.csrfToken,
      },
      body: JSON.stringify({ code: code }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          DJANGO_CONTEXT.accessVerified = true;
          if (accessModal) accessModal.hide();
          window.location.href = targetUrl;
        } else {
          if (errEl) {
            errEl.textContent = data.error || 'Неверный код';
            errEl.classList.remove('d-none');
          }
          if (inp) inp.select();
        }
      })
      .catch(function () {
        if (errEl) { errEl.textContent = 'Ошибка соединения'; errEl.classList.remove('d-none'); }
      });
  }

  /* ============================================================
     ACTIVE SIDEBAR LINK HIGHLIGHT
     ============================================================ */
  var path = window.location.pathname;
  document.querySelectorAll('.sidebar-link').forEach(function (link) {
    var href = link.getAttribute('href');
    if (href && href !== '#' && path.startsWith(href) && href.length > 1) {
      link.classList.add('active');
    }
  });
});
