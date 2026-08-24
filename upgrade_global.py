#!/usr/bin/env python3
"""Global polish: hero entrance animations, word rotation, back-to-top, nav indicator."""

FILE = "/opt/evolvixos/web/landing_new.html"

with open(FILE, "r") as f:
    content = f.read()

# ─── 1. Add CSS for hero entrance, back-to-top, nav indicator ───
css_marker = ".scroll-progress {"
css_idx = content.index(css_marker)

GLOBAL_CSS = r"""/* Hero entrance animations */
.hero-badge {
  opacity: 0;
  transform: translateY(20px);
  animation: heroFadeIn 0.8s ease-out 0.2s forwards, badgeGlow 3s ease-in-out 1s infinite;
}
@keyframes heroFadeIn {
  to { opacity: 1; transform: translateY(0); }
}
@keyframes badgeGlow {
  0%, 100% { box-shadow: 0 0 0 rgba(34, 197, 94, 0); }
  50% { box-shadow: 0 0 20px rgba(34, 197, 94, 0.15); }
}
#heroTitle {
  opacity: 0;
  transform: translateY(30px);
  animation: heroFadeIn 0.8s ease-out 0.4s forwards;
}
.hero > p {
  opacity: 0;
  transform: translateY(20px);
  animation: heroFadeIn 0.8s ease-out 0.6s forwards;
}
.hero-actions {
  opacity: 0;
  transform: translateY(20px);
  animation: heroFadeIn 0.8s ease-out 0.8s forwards;
}
.hero-stats {
  opacity: 0;
  transform: translateY(20px);
  animation: heroFadeIn 0.8s ease-out 1.0s forwards;
}

/* Back to top button */
.back-to-top {
  position: fixed;
  bottom: 30px; right: 30px;
  width: 48px; height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a855f7, #ec4899);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
  cursor: pointer;
  z-index: 100;
  opacity: 0;
  transform: translateY(20px) scale(0.8);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 20px rgba(168, 85, 247, 0.3);
  border: none;
  pointer-events: none;
}
.back-to-top.visible {
  opacity: 1;
  transform: translateY(0) scale(1);
  pointer-events: auto;
}
.back-to-top:hover {
  transform: translateY(-4px) scale(1.1);
  box-shadow: 0 8px 30px rgba(168, 85, 247, 0.5);
}

/* Nav active section indicator */
.nav a.active-section {
  color: #fff !important;
  position: relative;
}
.nav a.active-section::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, #a855f7, #ec4899);
  border-radius: 100px;
}

/* Feature card icon bounce on reveal */
.feature-card.reveal.active .feature-icon {
  animation: iconBounce 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
@keyframes iconBounce {
  0% { transform: scale(0); }
  60% { transform: scale(1.2); }
  100% { transform: scale(1); }
}

/* Model card counter glow */
.model-card.reveal.active .count::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 100px;
  background: radial-gradient(circle, rgba(168, 85, 247, 0.2), transparent);
  animation: counterGlow 2s ease-out forwards;
  pointer-events: none;
}
@keyframes counterGlow {
  from { opacity: 1; transform: scale(0.8); }
  to { opacity: 0; transform: scale(2); }
}

"""

content = content[:css_idx] + GLOBAL_CSS + content[css_idx:]

# ─── 2. Add back-to-top button HTML ───
bt_marker = '<!-- Particle network canvas -->'
bt_idx = content.index(bt_marker)

BT_HTML = '''<!-- Back to top button -->
<button class="back-to-top" id="backToTop" aria-label="Back to top">&#8593;</button>

'''

content = content[:bt_idx] + BT_HTML + content[bt_idx:]

# ─── 3. Update word rotation phrases ───
content = content.replace(
    "const phrases = ['Without Limits', 'Without Limits', 'Without Limits'];",
    "const phrases = ['Without Limits', 'Without Boundaries', 'Without Compromise', 'Without Limits'];"
)

# ─── 4. Add JS for back-to-top, nav indicator ───
js_marker = "// ─── Parallax orbs on mouse ───"
js_idx = content.index(js_marker)

GLOBAL_JS = '''
// ─── Back to top button ───
const backToTop = document.getElementById('backToTop');
if (backToTop) {
  window.addEventListener('scroll', () => {
    if (window.scrollY > 600) {
      backToTop.classList.add('visible');
    } else {
      backToTop.classList.remove('visible');
    }
  });
  backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

// ─── Nav active section indicator ───
const navLinks2 = document.querySelectorAll('.nav a[href^="#"]');
const navSections = {};
navLinks2.forEach(link => {
  const id = link.getAttribute('href').slice(1);
  const el = document.getElementById(id);
  if (el) navSections[id] = { el, link };
});
const navObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const id = entry.target.id;
      navLinks2.forEach(l => l.classList.remove('active-section'));
      if (navSections[id]) navSections[id].link.classList.add('active-section');
    }
  });
}, { threshold: 0.3, rootMargin: '-80px 0px -50% 0px' });
Object.values(navSections).forEach(s => navObserver.observe(s.el));

'''

content = content[:js_idx] + GLOBAL_JS + content[js_idx:]

with open(FILE, "w") as f:
    f.write(content)

print("OK — global polish applied")
