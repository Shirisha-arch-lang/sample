// app.js — global UI helpers

// Auto-dismiss flash messages
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 3500);
  });

  // Animate goal bars on load
  document.querySelectorAll('.goal-fill, .progress-fill, .mini-fill').forEach(el => {
    const w = el.style.width;
    el.style.width = '0';
    setTimeout(() => { el.style.transition = 'width .8s ease'; el.style.width = w; }, 100);
  });

  // Close sidebar on overlay click (mobile)
  document.addEventListener('click', e => {
    const sidebar = document.getElementById('sidebar');
    if (sidebar && sidebar.classList.contains('open') && !sidebar.contains(e.target) && !e.target.classList.contains('hamburger')) {
      sidebar.classList.remove('open');
    }
  });
});
