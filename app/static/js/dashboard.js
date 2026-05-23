document.addEventListener('DOMContentLoaded', function () {

  /* ─── Grid nav toggle ──────────────────────── */
  var gridBtn = document.getElementById('gridNavBtn');
  var gridDropdown = document.getElementById('gridNavDropdown');

  if (gridBtn && gridDropdown) {
    gridBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = gridDropdown.classList.toggle('open');
      gridBtn.classList.toggle('open', open);
    });

    document.addEventListener('click', function () {
      gridDropdown.classList.remove('open');
      gridBtn.classList.remove('open');
    });

    gridDropdown.addEventListener('click', function (e) {
      e.stopPropagation();
    });
  }

  /* ─── Auto-dismiss flash messages ─────────── */
  document.querySelectorAll('.flash').forEach(function (el) {
    setTimeout(function () {
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 300);
    }, 4000);
    el.style.transition = 'opacity 0.3s';
  });

});
