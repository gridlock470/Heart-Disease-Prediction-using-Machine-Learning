/* HeartGuard AI — Main JavaScript v3.0 */

/* ══ Navbar Scroll Effect ══ */
const navbar = document.querySelector('.navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 40);
  });
}

/* ══ Mobile Nav Toggle ══ */
const hamburger = document.querySelector('.nav-hamburger');
const navLinks  = document.querySelector('.nav-links');
if (hamburger && navLinks) {
  hamburger.addEventListener('click', () => {
    navLinks.classList.toggle('open');
  });
}

/* ══ Scroll Reveal ══ */
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => entry.target.classList.add('visible'), i * 80);
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });

document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

/* ══ Counter Animation ══ */
function animateCounter(el) {
  const target = parseFloat(el.dataset.target || el.textContent.replace(/[^0-9.]/g,''));
  const suffix = el.dataset.suffix || '';
  const duration = 1800;
  const start = performance.now();
  const isFloat = target % 1 !== 0;

  function update(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = target * eased;
    el.textContent = (isFloat ? current.toFixed(1) : Math.floor(current).toLocaleString()) + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      animateCounter(entry.target);
      counterObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('.counter').forEach(el => counterObserver.observe(el));

/* ══ 3D Tilt Effect on Cards ══ */
document.querySelectorAll('.tilt-card').forEach(card => {
  card.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width  - 0.5;
    const y = (e.clientY - rect.top)  / rect.height - 0.5;
    card.style.transform = `perspective(700px) rotateX(${-y * 10}deg) rotateY(${x * 10}deg) translateZ(4px)`;
  });
  card.addEventListener('mouseleave', () => {
    card.style.transform = '';
  });
});

/* ══ Feature Slider (3 slides) ══ */
function initFeatureSlider(sliderId) {
  const container = document.getElementById(sliderId);
  if (!container) return;

  const inner   = container.querySelector('.feature-slider-inner');
  const slides  = container.querySelectorAll('.feature-slide');
  const dots    = container.querySelectorAll('.slider-dot');
  const prevBtn = container.querySelector('.slider-prev');
  const nextBtn = container.querySelector('.slider-next');

  let current = 0;
  const total = Math.max(1, slides.length - 2); // groups of 3

  function go(idx) {
    current = ((idx % total) + total) % total;
    const offset = current * (100 / 3);
    inner.style.transform = `translateX(-${offset}%)`;
    dots.forEach((d, i) => d.classList.toggle('active', i === current));
  }

  if (prevBtn) prevBtn.addEventListener('click', () => go(current - 1));
  if (nextBtn) nextBtn.addEventListener('click', () => go(current + 1));
  dots.forEach((d, i) => d.addEventListener('click', () => go(i)));

  // Auto-advance
  let timer = setInterval(() => go(current + 1), 4000);
  container.addEventListener('mouseenter', () => clearInterval(timer));
  container.addEventListener('mouseleave', () => { timer = setInterval(() => go(current + 1), 4000); });

  go(0);
}

document.addEventListener('DOMContentLoaded', () => {
  initFeatureSlider('featureSlider');
  initFeatureSlider('infoSlider');
  spawnHeartParticles();
});

/* ══ Floating Heart Particles ══ */
function spawnHeartParticles() {
  const container = document.querySelector('.hearts-bg');
  if (!container) return;

  function createParticle() {
    const p = document.createElement('div');
    p.className = 'heart-particle';
    const size = 16 + Math.random() * 28;
    p.style.left    = Math.random() * 100 + 'vw';
    p.style.width   = size + 'px';
    p.style.height  = size + 'px';
    p.style.animationDuration  = (12 + Math.random() * 18) + 's';
    p.style.animationDelay     = (Math.random() * 5) + 's';
    p.innerHTML = `<svg viewBox="0 0 24 24" width="${size}" height="${size}"><path d="M12 21.593c-5.63-5.539-11-10.297-11-14.402 0-3.791 3.068-5.191 5.281-5.191 1.312 0 4.151.501 5.719 4.457 1.59-3.968 4.464-4.447 5.726-4.447 2.54 0 5.274 1.621 5.274 5.181 0 4.069-5.136 8.625-11 14.402z" fill="rgba(244,63,94,0.15)"/></svg>`;
    container.appendChild(p);
    setTimeout(() => p.remove(), 30000);
  }

  setInterval(createParticle, 1800);
  for (let i = 0; i < 5; i++) setTimeout(createParticle, i * 400);
}

/* ══ ECG Canvas Draw ══ */
function drawECG(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let offset = 0;

  function ecgPoint(x) {
    const t = ((x + offset * 2) % 300) / 300;
    if (t < 0.15) return Math.sin(t / 0.15 * Math.PI) * 5;
    if (t > 0.35 && t < 0.38) return -15;
    if (t > 0.38 && t < 0.42) return 60;
    if (t > 0.42 && t < 0.48) return -25;
    if (t > 0.48 && t < 0.52) return 10;
    if (t > 0.6  && t < 0.72) return Math.sin((t - 0.6) / 0.12 * Math.PI) * 8;
    return 0;
  }

  function draw() {
    canvas.width  = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    const W = canvas.width, H = canvas.height, mid = H / 2;

    ctx.clearRect(0, 0, W, H);
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(244,63,94,0.6)';
    ctx.lineWidth   = 2;
    ctx.shadowBlur  = 10;
    ctx.shadowColor = 'rgba(244,63,94,0.4)';

    for (let x = 0; x < W; x++) {
      const y = mid - ecgPoint(x);
      x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
    offset = (offset + 0.6) % 300;
    requestAnimationFrame(draw);
  }
  draw();
}

// Auto-init ECG
document.addEventListener('DOMContentLoaded', () => {
  drawECG('ecgCanvas');
});

/* ══ Flash Message Auto-dismiss ══ */
document.querySelectorAll('.flash-msg').forEach(msg => {
  msg.addEventListener('click', () => msg.remove());
  setTimeout(() => {
    msg.style.opacity    = '0';
    msg.style.transform  = 'translateX(60px)';
    msg.style.transition = 'all 0.4s ease';
    setTimeout(() => msg.remove(), 400);
  }, 5000);
});

/* ══ FAQ Accordion ══ */
document.querySelectorAll('.faq-question').forEach(btn => {
  btn.addEventListener('click', () => {
    const item = btn.closest('.faq-item');
    const wasOpen = item.classList.contains('open');
    document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
    if (!wasOpen) item.classList.add('open');
  });
});

/* ══ Form Loading State ══ */
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', () => {
    const btn = form.querySelector('[type=submit]');
    if (btn && !btn.dataset.noLoader) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Processing...';
    }
  });
});

/* ══ Role Toggle in Register ══ */
window.updateTheme = function(radio) {
  const spec = document.getElementById('specialty_section');
  const btn  = document.getElementById('submitBtn');
  if (!btn) return;
  if (radio.value === 'doctor') {
    if (spec) spec.classList.remove('hidden');
    btn.className = 'btn btn-blue w-full mt-6';
    btn.textContent = 'Create Doctor Account';
  } else {
    if (spec) spec.classList.add('hidden');
    btn.className = 'btn btn-rose w-full mt-6';
    btn.textContent = 'Create Patient Account';
  }
};

// Pre-select role from URL
document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  if (params.get('role') === 'doctor') {
    const dr = document.querySelector('input[value="doctor"]');
    if (dr) { dr.checked = true; window.updateTheme(dr); }
  }
});
