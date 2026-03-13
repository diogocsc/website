/* ─── NAV SCROLL ─────────────────────────────────────────────── */
const nav = document.getElementById('nav');
if (nav) {
  window.addEventListener('scroll', () => {
    nav.classList.toggle('nav--scrolled', window.scrollY > 50);
  }, { passive: true });
}

/* ─── MOBILE NAV ─────────────────────────────────────────────── */
const burger = document.querySelector('.nav__burger');
const navLinks = document.querySelector('.nav__links');
if (burger && navLinks) {
  // ensure desktop layout uses CSS, not inline styles
  const isMobile = () => window.innerWidth < 768;

  burger.addEventListener('click', () => {
    const open = navLinks.classList.toggle('nav__links--open');
    if (isMobile()) {
      if (open) {
        Object.assign(navLinks.style, {
          display: 'flex', flexDirection: 'column', position: 'absolute',
          top: '100%', left: '0', right: '0',
          background: 'rgba(247,245,240,0.97)',
          padding: '1.5rem 3rem', gap: '1.25rem',
          borderBottom: '1px solid rgba(0,0,0,0.08)'
        });
      } else {
        navLinks.style.display = 'none';
      }
    } else {
      // on desktop, let CSS control layout
      navLinks.style.display = '';
    }
  });

  navLinks.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      if (isMobile()) {
        navLinks.classList.remove('nav__links--open');
        navLinks.style.display = 'none';
      }
    });
  });

  // Reset inline styles when resizing to desktop
  window.addEventListener('resize', () => {
    if (!isMobile()) {
      navLinks.classList.remove('nav__links--open');
      navLinks.style.display = '';
    }
  });
}

/* ─── REVEAL ON SCROLL ───────────────────────────────────────── */
const revealEls = document.querySelectorAll('.reveal');
if (revealEls.length) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const siblings = [...entry.target.parentElement.querySelectorAll('.reveal:not(.visible)')];
      const idx = siblings.indexOf(entry.target);
      setTimeout(() => entry.target.classList.add('visible'), idx * 80);
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  revealEls.forEach(el => observer.observe(el));
}

/* ─── CONTACT FORM ───────────────────────────────────────────── */
const form = document.getElementById('contactForm');
if (form) {
  const submitBtn  = document.getElementById('submitBtn');
  const formStatus = document.getElementById('formStatus');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    submitBtn.disabled = true;
    submitBtn.querySelector('.btn-text').textContent = 'Sending…';
    formStatus.textContent = '';
    formStatus.className = 'form__status';

    try {
      const res = await fetch('/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name:    document.getElementById('name').value,
          email:   document.getElementById('email').value,
          message: document.getElementById('message').value,
        }),
      });
      const data = await res.json();
      if (data.success) {
        formStatus.textContent = '✓ Message sent — I\'ll be in touch soon.';
        formStatus.classList.add('form__status--success');
        form.reset();
      } else {
        throw new Error(data.error || 'Something went wrong.');
      }
    } catch (err) {
      formStatus.textContent = '✕ ' + err.message;
      formStatus.classList.add('form__status--error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.querySelector('.btn-text').textContent = 'Send message';
    }
  });
}

/* ─── ACTIVE NAV LINK ────────────────────────────────────────── */
const sections   = document.querySelectorAll('section[id]');
const navAnchors = document.querySelectorAll('.nav__links a');
window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(s => { if (window.scrollY >= s.offsetTop - 120) current = s.id; });
  navAnchors.forEach(a => {
    a.style.color = a.getAttribute('href') === `#${current}` ? 'var(--ink)' : '';
  });
}, { passive: true });

/* ─── EMAIL OBFUSCATION ──────────────────────────────────────── */
document.querySelectorAll('.email-link[data-user][data-domain]').forEach(el => {
  const user = el.getAttribute('data-user');
  const domain = el.getAttribute('data-domain');
  if (!user || !domain) return;
  const addr = `${user}@${domain}`;
  el.textContent = addr;
  el.addEventListener('click', (e) => {
    e.preventDefault();
    window.location.href = `mailto:${addr}`;
  });
});

/* ─── PHONE OBFUSCATION ──────────────────────────────────────── */
document.querySelectorAll('.phone-link[data-phone]').forEach(el => {
  const phone = el.getAttribute('data-phone');
  if (!phone) return;
  el.textContent = phone;
  el.addEventListener('click', (e) => {
    e.preventDefault();
    window.location.href = `tel:${phone}`;
  });
});
