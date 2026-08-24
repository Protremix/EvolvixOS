#!/usr/bin/env python3
"""Upgrade the pricing section with 3D tilt, billing toggle, comparison highlights, and more animation."""

FILE = "/opt/evolvixos/web/landing_new.html"

with open(FILE, "r") as f:
    content = f.read()

# ─── 1. Replace pricing CSS ───
old_css_start = "/* ─── Pricing ─── */"
old_css_end = ".pricing-cta.secondary:hover { border-color: var(--primary); background: rgba(168, 85, 247, 0.08); transform: translateY(-2px); }"

css_start_idx = content.index(old_css_start)
css_end_idx = content.index(old_css_end, css_start_idx) + len(old_css_end)

NEW_PRICING_CSS = r"""/* ─── Pricing ─── */
.pricing-section { padding: 140px 40px 100px; max-width: 1280px; margin: 0 auto; position: relative; z-index: 2; }

/* Billing toggle */
.billing-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin: 32px 0 0;
}
.billing-toggle-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-muted);
  transition: color 0.3s;
}
.billing-toggle-label.active { color: var(--text); }
.billing-toggle-switch {
  position: relative;
  width: 56px; height: 30px;
  border-radius: 100px;
  background: rgba(168, 85, 247, 0.15);
  border: 1px solid rgba(168, 85, 247, 0.3);
  cursor: pointer;
  transition: all 0.3s;
}
.billing-toggle-switch::after {
  content: '';
  position: absolute;
  top: 3px; left: 3px;
  width: 22px; height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a855f7, #ec4899);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 2px 8px rgba(168, 85, 247, 0.4);
}
.billing-toggle-switch.annual::after { transform: translateX(26px); }
.billing-save-badge {
  padding: 4px 12px;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 700;
  background: linear-gradient(135deg, rgba(52, 211, 153, 0.2), rgba(34, 197, 94, 0.15));
  color: #34d399;
  border: 1px solid rgba(52, 211, 153, 0.3);
  animation: saveBadgePulse 2s ease-in-out infinite;
}
@keyframes saveBadgePulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

.pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; margin-top: 56px; }
.pricing-card {
  background: var(--bg-card); border: 1px solid var(--border); border-radius: 32px;
  padding: 44px 36px; position: relative;
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
              box-shadow 0.4s ease, border-color 0.4s ease;
  overflow: hidden;
}
.pricing-card:hover { box-shadow: 0 30px 70px rgba(0,0,0,0.4); }

/* Mouse-follow glow on cards */
.pricing-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at var(--mx, 50%) var(--my, 0%), rgba(168, 85, 247, 0.06) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}
.pricing-card:hover::after { opacity: 1; }

/* Animated gradient border on featured card */
.pricing-card.featured {
  border-color: transparent;
  background: linear-gradient(180deg, rgba(168, 85, 247, 0.08) 0%, var(--bg-card) 30%);
  box-shadow: 0 0 50px rgba(168, 85, 247, 0.15);
  animation: featuredPulse 4s ease-in-out infinite;
  position: relative;
}
.pricing-card.featured::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 32px;
  padding: 1px;
  background: linear-gradient(135deg, #a855f7, #ec4899, #8b5cf6, #a855f7);
  background-size: 300% 300%;
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  animation: gradientBorder 4s linear infinite;
  pointer-events: none;
}
@keyframes gradientBorder {
  0% { background-position: 0% 50%; }
  100% { background-position: 300% 50%; }
}
@keyframes featuredPulse {
  0%, 100% { box-shadow: 0 0 50px rgba(168, 85, 247, 0.12); }
  50% { box-shadow: 0 0 80px rgba(168, 85, 247, 0.22); }
}
.pricing-badge {
  position: absolute; top: -14px; left: 50%; transform: translateX(-50%);
  padding: 6px 20px; border-radius: 100px; font-size: 12px; font-weight: 700;
  background: linear-gradient(135deg, #a855f7, #ec4899); color: #fff;
  text-transform: uppercase; letter-spacing: 1.5px;
  box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
  animation: badgeBounce 2s ease-in-out infinite;
  z-index: 3;
  white-space: nowrap;
}
@keyframes badgeBounce { 0%, 100% { transform: translateX(-50%) translateY(0); } 50% { transform: translateX(-50%) translateY(-4px); } }

/* Feature count badge */
.pricing-feature-count {
  position: absolute;
  top: 16px; right: 16px;
  padding: 4px 10px;
  border-radius: 100px;
  font-size: 11px;
  font-weight: 700;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

.pricing-name { font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-muted); margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.pricing-price { display: flex; align-items: baseline; gap: 4px; margin-bottom: 6px; position: relative; }
.pricing-price .amount { font-size: 56px; font-weight: 900; letter-spacing: -2.5px; background: linear-gradient(135deg, #fff, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; transition: transform 0.3s; }
.pricing-card:hover .pricing-price .amount { transform: scale(1.05); }
.pricing-price .currency { font-size: 22px; font-weight: 600; color: var(--text-muted); }
.pricing-price .period { font-size: 18px; color: var(--text-muted); font-weight: 500; }
.pricing-desc { font-size: 15px; color: var(--text-muted); margin-bottom: 28px; line-height: 1.6; }
.pricing-features { list-style: none; margin-bottom: 36px; }
.pricing-features li {
  display: flex; align-items: flex-start; gap: 12px; padding: 12px 0;
  font-size: 15px; color: var(--text); border-bottom: 1px solid rgba(168, 85, 247, 0.06);
  transition: transform 0.2s, color 0.2s;
}
.pricing-features li:hover { transform: translateX(6px); color: #fff; }
.pricing-features li:last-child { border-bottom: none; }
.pricing-features li .check {
  flex-shrink: 0; width: 22px; height: 22px; border-radius: 7px;
  background: rgba(52, 211, 153, 0.12); display: flex; align-items: center; justify-content: center;
  font-size: 13px; color: var(--success); font-weight: 800;
  transition: transform 0.2s;
}
.pricing-features li:hover .check { transform: scale(1.15); }
.pricing-features li .x {
  flex-shrink: 0; width: 22px; height: 22px; border-radius: 7px;
  background: rgba(239, 68, 68, 0.08); display: flex; align-items: center; justify-content: center;
  font-size: 13px; color: #ef4444; font-weight: 800;
}
.pricing-features li .label-muted { color: var(--text-dim); }
.pricing-cta {
  display: block; text-align: center; padding: 16px; border-radius: 100px;
  font-size: 16px; font-weight: 700; transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative; overflow: hidden;
}
.pricing-cta.primary { background: linear-gradient(135deg, #a855f7, #ec4899); color: #fff; box-shadow: 0 6px 25px rgba(168, 85, 247, 0.3); }
.pricing-cta.primary::before {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s;
}
.pricing-cta.primary:hover::before { left: 100%; }
.pricing-cta.primary:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 12px 35px rgba(168, 85, 247, 0.4); }
.pricing-cta.secondary { background: rgba(255,255,255,0.04); border: 1px solid var(--border); color: var(--text); }
.pricing-cta.secondary:hover { border-color: var(--primary); background: rgba(168, 85, 247, 0.08); transform: translateY(-2px); }

/* Price transition animation */
.pricing-price .amount { transition: transform 0.3s, opacity 0.2s; }
.pricing-price.changing .amount { opacity: 0; transform: scale(0.8); }"""

content = content[:css_start_idx] + NEW_PRICING_CSS + content[css_end_idx:]

# ─── 2. Replace pricing HTML to add billing toggle, feature counts, data attributes ───
pricing_start = content.index('<section class="pricing-section" id="pricing">')
# Find closing </section>
pricing_close = content.index('</section>', pricing_start)
pricing_end_idx = pricing_close + len('</section>')

NEW_PRICING_HTML = '''<section class="pricing-section" id="pricing">
  <div class="section-center reveal">
    <div class="section-tag">💎 Subscription Plans</div>
    <h2 class="section-title">Simple, Transparent <span class="grad">Pricing</span></h2>
    <p class="section-subtitle">
      Start free, scale as you grow. Every plan includes the full platform —
      the difference is compute power and model access. No hidden fees, no surprises.
    </p>
  </div>

  <!-- Billing Toggle -->
  <div class="billing-toggle reveal">
    <span class="billing-toggle-label active" id="monthlyLabel">Monthly</span>
    <div class="billing-toggle-switch" id="billingSwitch" role="switch" aria-label="Toggle annual billing"></div>
    <span class="billing-toggle-label" id="annualLabel">Annual</span>
    <span class="billing-save-badge">Save 20%</span>
  </div>

  <div class="pricing-grid">
    <div class="pricing-card reveal" data-tilt>
      <div class="pricing-feature-count">6 features</div>
      <div class="pricing-name">🌱 Starter</div>
      <div class="pricing-price"><span class="currency">$</span><span class="amount" data-count="0" data-monthly="0" data-annual="0">0</span><span class="period">/month</span></div>
      <p class="pricing-desc">Perfect for exploring the platform and building your first AI apps.</p>
      <ul class="pricing-features">
        <li><span class="check">✓</span> 3 Entities / Apps</li>
        <li><span class="check">✓</span> 5 Pages per App</li>
        <li><span class="check">✓</span> Local LLM Access (Ollama)</li>
        <li><span class="check">✓</span> 10 API Calls / minute</li>
        <li><span class="check">✓</span> Community Support</li>
        <li><span class="check">✓</span> Page Builder + App Viewer</li>
        <li><span class="x">✕</span> <span class="label-muted">Cloud AI Models (Groq/Gemini)</span></li>
        <li><span class="x">✕</span> <span class="label-muted">Media Production (4K Video)</span></li>
        <li><span class="x">✕</span> <span class="label-muted">Workflow Automation</span></li>
      </ul>
      <a href="/platform/" class="pricing-cta secondary" data-magnetic>Start Free</a>
    </div>
    <div class="pricing-card featured reveal" data-tilt>
      <div class="pricing-badge">★ Most Popular</div>
      <div class="pricing-feature-count">10 features</div>
      <div class="pricing-name">🚀 Professional</div>
      <div class="pricing-price"><span class="currency">$</span><span class="amount" data-count="29" data-monthly="29" data-annual="23">0</span><span class="period">/month</span></div>
      <p class="pricing-desc">For developers building production AI apps with cloud model access.</p>
      <ul class="pricing-features">
        <li><span class="check">✓</span> Unlimited Entities / Apps</li>
        <li><span class="check">✓</span> Unlimited Pages per App</li>
        <li><span class="check">✓</span> Local + Cloud AI (Groq, Gemini, Kimi)</li>
        <li><span class="check">✓</span> 100 API Calls / minute</li>
        <li><span class="check">✓</span> Workflow Automation</li>
        <li><span class="check">✓</span> Backend Functions (deploy Python)</li>
        <li><span class="check">✓</span> Auto-Generated SDKs (TS/JS)</li>
        <li><span class="check">✓</span> Priority Email Support</li>
        <li><span class="x">✕</span> <span class="label-muted">4K Video Production</span></li>
        <li><span class="x">✕</span> <span class="label-muted">Voice Command Interface</span></li>
      </ul>
      <a href="/platform/" class="pricing-cta primary" data-magnetic>Start Pro Trial →</a>
    </div>
    <div class="pricing-card reveal" data-tilt>
      <div class="pricing-feature-count">10 features</div>
      <div class="pricing-name">💼 Business</div>
      <div class="pricing-price"><span class="currency">$</span><span class="amount" data-count="99" data-monthly="99" data-annual="79">0</span><span class="period">/month</span></div>
      <p class="pricing-desc">Full media production, voice commands, and higher limits for growing teams.</p>
      <ul class="pricing-features">
        <li><span class="check">✓</span> Everything in Professional</li>
        <li><span class="check">✓</span> 4K Video Production (ffmpeg)</li>
        <li><span class="check">✓</span> AI Voiceover + Neural TTS</li>
        <li><span class="check">✓</span> Voice Command Interface</li>
        <li><span class="check">✓</span> 1,000 API Calls / minute</li>
        <li><span class="check">✓</span> 3D Logo Generation (Blender)</li>
        <li><span class="check">✓</span> Analytics Dashboard (Chart.js)</li>
        <li><span class="check">✓</span> Team Memory Hub</li>
        <li><span class="check">✓</span> WhatsApp + Telegram Bots</li>
        <li><span class="x">✕</span> <span class="label-muted">Dedicated GPU Server</span></li>
      </ul>
      <a href="/platform/" class="pricing-cta secondary" data-magnetic>Start Business Trial</a>
    </div>
    <div class="pricing-card reveal" data-tilt>
      <div class="pricing-feature-count">10 features</div>
      <div class="pricing-name">🏆 Enterprise</div>
      <div class="pricing-price"><span class="currency">$</span><span class="amount" data-count="299" data-monthly="299" data-annual="239">0</span><span class="period">/month</span></div>
      <p class="pricing-desc">Dedicated infrastructure, GPU access, and enterprise-grade support.</p>
      <ul class="pricing-features">
        <li><span class="check">✓</span> Everything in Business</li>
        <li><span class="check">✓</span> Dedicated GPU Server (Wan2.1)</li>
        <li><span class="check">✓</span> Unlimited API Calls</li>
        <li><span class="check">✓</span> MicroVM Sandboxing (CubeSandbox)</li>
        <li><span class="check">✓</span> Tencent Cloud Integration</li>
        <li><span class="check">✓</span> Custom AI Model Fine-tuning</li>
        <li><span class="check">✓</span> Dedicated Support + SLA</li>
        <li><span class="check">✓</span> On-Premise Deployment</li>
        <li><span class="check">✓</span> Custom Branding</li>
        <li><span class="check">✓</span> Source Code Access</li>
      </ul>
      <a href="mailto:admin@evolvixos.com" class="pricing-cta secondary" data-magnetic>Contact Sales</a>
    </div>
  </div>
</section>'''

content = content[:pricing_start] + NEW_PRICING_HTML + content[pricing_end_idx:]

# ─── 3. Add billing toggle + pricing tilt JS ───
js_marker = "// ─── Parallax orbs on mouse ───"
js_idx = content.index(js_marker)

PRICING_JS = '''
// ─── Billing toggle (monthly / annual) ───
const billingSwitch = document.getElementById('billingSwitch');
const monthlyLabel = document.getElementById('monthlyLabel');
const annualLabel = document.getElementById('annualLabel');
let isAnnual = false;
if (billingSwitch) {
  billingSwitch.addEventListener('click', () => {
    isAnnual = !isAnnual;
    billingSwitch.classList.toggle('annual', isAnnual);
    monthlyLabel.classList.toggle('active', !isAnnual);
    annualLabel.classList.toggle('active', isAnnual);
    document.querySelectorAll('.pricing-price .amount').forEach(el => {
      const monthly = el.dataset.monthly;
      const annual = el.dataset.annual;
      const target = isAnnual ? annual : monthly;
      el.parentElement.classList.add('changing');
      setTimeout(() => {
        el.textContent = target;
        el.parentElement.classList.remove('changing');
      }, 200);
    });
  });
}

// ─── 3D tilt for pricing cards ───
document.querySelectorAll('.pricing-card[data-tilt]').forEach(card => {
  card.addEventListener('mousemove', e => {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const cx = rect.width / 2;
    const cy = rect.height / 2;
    const rotateX = ((y - cy) / cy) * -6;
    const rotateY = ((x - cx) / cx) * 6;
    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
    card.style.setProperty('--mx', `${(x / rect.width) * 100}%`);
    card.style.setProperty('--my', `${(y / rect.height) * 100}%`);
  });
  card.addEventListener('mouseleave', () => {
    card.style.transform = '';
  });
});

'''

content = content[:js_idx] + PRICING_JS + content[js_idx:]

with open(FILE, "w") as f:
    f.write(content)

print("OK — pricing section upgraded")
