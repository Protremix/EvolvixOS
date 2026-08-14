#!/usr/bin/env python3
"""
EvolvixOS Template Generator — 10,000+ website templates.
Every template is responsive, modern, self-contained HTML+CSS.
100% free, $0 forever.
"""
import os, json, random, hashlib

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
random.seed(42)

# === Design System ===
PALETTES = [
    {"name": "Violet Dream", "primary": "#7C5CFF", "secondary": "#00D4AA", "bg": "#0F0F1A", "surface": "#1A1A2E", "text": "#E0E0E0", "muted": "#8888AA"},
    {"name": "Ocean Blue", "primary": "#0066FF", "secondary": "#00C6FF", "bg": "#001020", "surface": "#002040", "text": "#E0E8FF", "muted": "#6080A0"},
    {"name": "Sunset Orange", "primary": "#FF6B35", "secondary": "#F7931E", "bg": "#1A0F0A", "surface": "#2A1A10", "text": "#FFE0CC", "muted": "#AA8866"},
    {"name": "Forest Green", "primary": "#00A86B", "secondary": "#7CCD7C", "bg": "#0A1A0F", "surface": "#102A1A", "text": "#D0E8D0", "muted": "#669966"},
    {"name": "Royal Purple", "primary": "#9D00FF", "secondary": "#FF00AA", "bg": "#0F0A1A", "surface": "#1A102A", "text": "#E8D0FF", "muted": "#8866AA"},
    {"name": "Crimson Red", "primary": "#DC143C", "secondary": "#FF6B6B", "bg": "#1A0A0A", "surface": "#2A1010", "text": "#FFD0D0", "muted": "#AA6666"},
    {"name": "Midnight", "primary": "#1976D2", "secondary": "#42A5F5", "bg": "#0A0A0A", "surface": "#1A1A1A", "text": "#E0E0E0", "muted": "#666666"},
    {"name": "Golden Hour", "primary": "#FFB300", "secondary": "#FF8F00", "bg": "#1A1505", "surface": "#2A2010", "text": "#FFF0CC", "muted": "#AA9966"},
    {"name": "Mint Fresh", "primary": "#00C9A7", "secondary": "#00D4AA", "bg": "#0A1A18", "surface": "#102A28", "text": "#CCF0E8", "muted": "#669988"},
    {"name": "Rose Pink", "primary": "#E91E63", "secondary": "#FF80AB", "bg": "#1A0A10", "surface": "#2A1020", "text": "#FFD0E0", "muted": "#AA6688"},
    {"name": "Cyber Neon", "primary": "#00FFFF", "secondary": "#FF00FF", "bg": "#050510", "surface": "#0F0F20", "text": "#E0FFFF", "muted": "#506080"},
    {"name": "Earth Brown", "primary": "#8B4513", "secondary": "#D2691E", "bg": "#1A1005", "surface": "#2A1A10", "text": "#F0DCC0", "muted": "#88664A"},
    {"name": "Arctic Ice", "primary": "#00B4D8", "secondary": "#90E0EF", "bg": "#0A1015", "surface": "#152030", "text": "#D0E8F0", "muted": "#608090"},
    {"name": "Deep Indigo", "primary": "#3D5A80", "secondary": "#98C1D9", "bg": "#0A0F1A", "surface": "#141F30", "text": "#D0D8E8", "muted": "#506880"},
    {"name": "Lava Glow", "primary": "#FF4500", "secondary": "#FFD700", "bg": "#1A0500", "surface": "#2A0F05", "text": "#FFE0C0", "muted": "#AA6650"},
    {"name": "Mono Dark", "primary": "#FFFFFF", "secondary": "#AAAAAA", "bg": "#000000", "surface": "#111111", "text": "#FFFFFF", "muted": "#555555"},
    {"name": "Mono Light", "primary": "#000000", "secondary": "#444444", "bg": "#FFFFFF", "surface": "#F5F5F5", "text": "#1A1A1A", "muted": "#888888"},
    {"name": "Teal Deep", "primary": "#008080", "secondary": "#40E0D0", "bg": "#0A1A1A", "surface": "#102A2A", "text": "#C0E8E8", "muted": "#509090"},
    {"name": "Lavender", "primary": "#9B59B6", "secondary": "#E0AAFF", "bg": "#100A15", "surface": "#1A1025", "text": "#E8D0F0", "muted": "#806090"},
    {"name": "Coral Reef", "primary": "#FF7F50", "secondary": "#FF6347", "bg": "#1A0A05", "surface": "#2A1510", "text": "#FFE0D0", "muted": "#AA7755"},
]

FONTS = [
    ("Inter', sans-serif", "Inter"),
    ("Georgia, serif", "Georgia"),
    ("'Courier New', monospace", "Mono"),
    ("'Helvetica Neue', sans-serif", "Helvetica"),
    ("'Times New Roman', serif", "Times"),
    ("Arial, sans-serif", "Arial"),
    ("'Trebuchet MS', sans-serif", "Trebuchet"),
    ("'Palatino Linotype', serif", "Palatino"),
    ("Verdana, sans-serif", "Verdana"),
    ("'Segoe UI', sans-serif", "Segoe"),
    ("'Roboto', sans-serif", "Roboto"),
    ("'Open Sans', sans-serif", "Open Sans"),
    ("'Lato', sans-serif", "Lato"),
    ("'Montserrat', sans-serif", "Montserrat"),
    ("'Playfair Display', serif", "Playfair"),
]

LAYOUTS = ["hero", "sidebar", "split", "grid", "fullwidth", "boxed", "centered", "magazine"]

# === Content generators ===
BUSINESS_NAMES = ["Nexus", "Quantum", "Vertex", "Apex", "Flux", "Pulse", "Cipher", "Nova", "Zenith", "Echo", "Orbit", "Spark", "Forge", "Prism", "Atlas", "Vortex", "Helix", "Catalyst", "Momentum", "Spectrum", "Resonance", "Apex", "Titan", "Stellar", "Infinity", "Pinnacle", "Horizon", "Cascade", "Beacon", "Vanguard"]
TAGLINES = ["Build the future", "Ship faster", "Scale infinitely", "Code smarter", "Deploy anywhere", "Think different", "Move fast", "Stay ahead", "Do more", "Less code, more impact", "Simplify everything", "Power your ideas", "Transform your workflow", "Accelerate growth", "Unlock potential", "Engineer success", "Create boldly", "Innovate daily", "Lead the way", "Dream big, build bigger"]
FEATURES = ["AI-Powered Analytics", "Real-time Collaboration", "Auto-scaling Infrastructure", "Advanced Security", "Smart Automation", "Cloud-native", "API-first Design", "Zero-config Setup", "Instant Deployments", "Live Monitoring", "Custom Workflows", "Team Management", "Version Control", "Code Review", "Issue Tracking", "Wiki & Docs", "CI/CD Pipeline", "Load Balancing", "Edge Caching", "Global CDN", "SSL Certificates", "DDoS Protection", "Daily Backups", "99.9% Uptime", "24/7 Support"]
SECTIONS = ["hero", "features", "pricing", "testimonials", "about", "team", "stats", "cta", "faq", "contact", "gallery", "blog", "newsletter", "footer", "navbar", "sidebar", "cards", "timeline", "comparison", "screenshots"]
COMPONENTS = ["button", "card", "badge", "alert", "modal", "tab", "accordion", "carousel", "dropdown", "navbar", "sidebar", "footer", "form", "input", "table", "progress", "breadcrumb", "pagination", "tooltip", "toast"]

def gen_css(palette, font):
    return f"""
:root {{
  --primary: {palette['primary']};
  --secondary: {palette['secondary']};
  --bg: {palette['bg']};
  --surface: {palette['surface']};
  --text: {palette['text']};
  --muted: {palette['muted']};
  --radius: 12px;
  --radius-sm: 8px;
  --radius-lg: 20px;
  --font: {font};
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; }}
a {{ color: var(--primary); text-decoration: none; transition: opacity 0.2s; }}
a:hover {{ opacity: 0.8; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 0 24px; }}
.btn {{ display: inline-block; padding: 12px 28px; border-radius: var(--radius-sm); font-weight: 600; border: none; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }}
.btn-primary {{ background: var(--primary); color: var(--bg); }}
.btn-secondary {{ background: var(--secondary); color: var(--bg); }}
.btn-outline {{ background: transparent; border: 2px solid var(--primary); color: var(--primary); }}
.btn:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }}
.card {{ background: var(--surface); border-radius: var(--radius); padding: 32px; border: 1px solid rgba(255,255,255,0.05); transition: transform 0.2s, border-color 0.2s; }}
.card:hover {{ transform: translateY(-4px); border-color: var(--primary); }}
.grid {{ display: grid; gap: 24px; }}
.grid-2 {{ grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }}
.grid-3 {{ grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }}
.grid-4 {{ grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
section {{ padding: 80px 0; }}
h1 {{ font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 800; line-height: 1.1; margin-bottom: 16px; }}
h2 {{ font-size: clamp(1.5rem, 3vw, 2.5rem); font-weight: 700; margin-bottom: 12px; }}
h3 {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 8px; }}
p {{ color: var(--muted); margin-bottom: 16px; }}
.badge {{ display: inline-block; padding: 4px 12px; border-radius: 100px; font-size: 0.85rem; font-weight: 600; background: rgba(255,255,255,0.1); color: var(--primary); }}
.navbar {{ position: sticky; top: 0; z-index: 100; background: rgba(0,0,0,0.5); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.05); }}
.navbar .container {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; }}
.navbar .logo {{ font-weight: 800; font-size: 1.25rem; color: var(--primary); }}
.navbar nav {{ display: flex; gap: 32px; }}
.navbar nav a {{ color: var(--text); font-weight: 500; font-size: 0.95rem; }}
.hero {{ text-align: center; padding: 120px 0 80px; }}
.hero h1 {{ background: linear-gradient(135deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
.hero .btn {{ margin: 8px; }}
.footer {{ border-top: 1px solid rgba(255,255,255,0.05); padding: 40px 0; text-align: center; color: var(--muted); }}
.footer a {{ margin: 0 12px; }}
.testimonial {{ background: var(--surface); border-radius: var(--radius); padding: 32px; border-left: 4px solid var(--primary); }}
.testimonial .quote {{ font-size: 1.1rem; font-style: italic; margin-bottom: 16px; }}
.testimonial .author {{ font-weight: 600; color: var(--text); }}
.testimonial .role {{ font-size: 0.9rem; color: var(--muted); }}
.stat {{ text-align: center; }}
.stat .number {{ font-size: 3rem; font-weight: 800; color: var(--primary); }}
.stat .label {{ color: var(--muted); margin-top: 8px; }}
.pricing-card {{ background: var(--surface); border-radius: var(--radius); padding: 40px; text-align: center; border: 1px solid rgba(255,255,255,0.05); position: relative; }}
.pricing-card.featured {{ border-color: var(--primary); transform: scale(1.05); }}
.pricing-card .price {{ font-size: 3rem; font-weight: 800; color: var(--primary); }}
.pricing-card .period {{ color: var(--muted); }}
.pricing-card ul {{ list-style: none; margin: 24px 0; text-align: left; }}
.pricing-card li {{ padding: 8px 0; color: var(--muted); }}
.pricing-card li:before {{ content: "✓"; color: var(--secondary); margin-right: 12px; font-weight: 700; }}
.form-group {{ margin-bottom: 16px; }}
.form-group label {{ display: block; margin-bottom: 6px; font-weight: 500; }}
.form-group input, .form-group textarea {{ width: 100%; padding: 12px 16px; border-radius: var(--radius-sm); background: var(--surface); border: 1px solid rgba(255,255,255,0.1); color: var(--text); font-family: var(--font); }}
.form-group input:focus, .form-group textarea:focus {{ outline: none; border-color: var(--primary); }}
.faq-item {{ background: var(--surface); border-radius: var(--radius-sm); padding: 20px; margin-bottom: 12px; }}
.faq-item h3 {{ cursor: pointer; color: var(--text); }}
.faq-item p {{ margin-top: 8px; }}
.tag {{ display: inline-block; padding: 4px 12px; border-radius: var(--radius-sm); background: var(--surface); color: var(--primary); font-size: 0.85rem; margin: 4px; }}
.progress {{ height: 8px; border-radius: 100px; background: var(--surface); overflow: hidden; }}
.progress-bar {{ height: 100%; border-radius: 100px; background: linear-gradient(90deg, var(--primary), var(--secondary)); }}
.avatar {{ width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, var(--primary), var(--secondary)); display: inline-flex; align-items: center; justify-content: center; font-weight: 700; color: var(--bg); }}
.team-member {{ text-align: center; }}
.team-member .avatar {{ width: 96px; height: 96px; font-size: 2rem; margin-bottom: 16px; }}
.feature-icon {{ width: 56px; height: 56px; border-radius: var(--radius-sm); background: linear-gradient(135deg, var(--primary), var(--secondary)); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin-bottom: 16px; }}
.screenshot {{ border-radius: var(--radius); overflow: hidden; border: 1px solid rgba(255,255,255,0.05); background: var(--surface); }}
.screenshot img {{ width: 100%; display: block; }}
.timeline-item {{ display: flex; gap: 24px; padding: 20px 0; border-left: 3px solid var(--primary); padding-left: 24px; position: relative; }}
.timeline-item:before {{ content: ""; position: absolute; left: -9px; top: 28px; width: 15px; height: 15px; border-radius: 50%; background: var(--primary); }}
@media (max-width: 768px) {{
  .navbar nav {{ display: none; }}
  .grid-2, .grid-3, .grid-4 {{ grid-template-columns: 1fr; }}
  .pricing-card.featured {{ transform: none; }}
  section {{ padding: 48px 0; }}
  .hero {{ padding: 60px 0 40px; }}
}}
"""

def gen_navbar(biz_name):
    return f"""
  <div class="navbar">
    <div class="container">
      <a href="#" class="logo">{biz_name}</a>
      <nav>
        <a href="#features">Features</a>
        <a href="#pricing">Pricing</a>
        <a href="#about">About</a>
        <a href="#contact">Contact</a>
      </nav>
      <a href="#" class="btn btn-primary">Get Started</a>
    </div>
  </div>"""

def gen_footer(biz_name):
    return f"""
  <div class="footer">
    <div class="container">
      <p>&copy; 2024 {biz_name}. All rights reserved.</p>
      <p>
        <a href="#">Privacy</a>
        <a href="#">Terms</a>
        <a href="#">Docs</a>
        <a href="#">Blog</a>
      </p>
    </div>
  </div>"""

def gen_hero(title, tagline, palette):
    return f"""
  <div class="hero">
    <div class="container">
      <span class="badge">✨ New: AI-Powered Features</span>
      <h1>{title}</h1>
      <p style="font-size: 1.25rem; max-width: 600px; margin: 0 auto 32px;">{tagline}</p>
      <a href="#" class="btn btn-primary">Start Free Trial</a>
      <a href="#" class="btn btn-outline">View Demo</a>
    </div>
  </div>"""

def gen_features(n=6):
    items = []
    for i in range(n):
        feat = random.choice(FEATURES)
        icon = random.choice(["⚡", "🚀", "🔒", "📊", "🤖", "☁️", "🔗", "🎯", "💡", "⭐"])
        items.append(f"""
    <div class="card">
      <div class="feature-icon">{icon}</div>
      <h3>{feat}</h3>
      <p>Powerful {feat.lower()} that scales with your business. Built for modern teams.</p>
    </div>""")
    return f"""
  <section id="features">
    <div class="container">
      <h2 style="text-align: center;">Everything you need to succeed</h2>
      <p style="text-align: center; max-width: 600px; margin: 0 auto 48px;">Built with modern technology and designed for scale.</p>
      <div class="grid grid-3">
        {"".join(items)}
      </div>
    </div>
  </section>"""

def gen_pricing():
    plans = [("Starter", "$0", "Perfect for getting started", ["1 project", "5 team members", "2GB storage", "Community support"]),
             ("Pro", "$29", "For growing teams", ["10 projects", "25 team members", "50GB storage", "Priority support", "Advanced analytics", "Custom domains"]),
             ("Enterprise", "$99", "For large organizations", ["Unlimited projects", "Unlimited members", "1TB storage", "24/7 support", "SSO & SAML", "SLA guarantee"])]
    cards = []
    for i, (name, price, desc, features) in enumerate(plans):
        featured = "featured" if i == 1 else ""
        feat_html = "".join(f"<li>{f}</li>" for f in features)
        badge = '<span class="badge" style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%);">Popular</span>' if i == 1 else ""
        cards.append(f"""
      <div class="pricing-card {featured}">
        {badge}
        <h3>{name}</h3>
        <p>{desc}</p>
        <div class="price">{price}<span class="period">/mo</span></div>
        <ul>{feat_html}</ul>
        <a href="#" class="btn btn-primary">Choose {name}</a>
      </div>""")
    return f"""
  <section id="pricing">
    <div class="container">
      <h2 style="text-align: center;">Simple, transparent pricing</h2>
      <p style="text-align: center; margin-bottom: 48px;">Start free, upgrade when you need.</p>
      <div class="grid grid-3">
        {"".join(cards)}
      </div>
    </div>
  </section>"""

def gen_testimonials(n=3):
    names = ["Sarah Chen", "Marcus Johnson", "Elena Rodriguez", "David Kim", "Aisha Patel", "Tom Anderson"]
    roles = ["CTO at TechFlow", "Founder at StartupXYZ", "Lead Dev at BigCorp", "Designer at Pixel", "PM at Agile", "Dev at CloudNine"]
    quotes = ["This transformed our workflow completely.", "Best decision we made this year.", "Our team productivity doubled overnight.", "The ROI was immediate and massive.", "Finally, a tool that just works.", "We can't imagine working without it now."]
    items = []
    for i in range(n):
        items.append(f"""
      <div class="testimonial">
        <div class="quote">"{random.choice(quotes)}"</div>
        <div class="author">random.choice(names)</div>
        <div class="role">random.choice(roles)</div>
      </div>""")
    return f"""
  <section>
    <div class="container">
      <h2 style="text-align: center;">Loved by teams worldwide</h2>
      <div class="grid grid-3" style="margin-top: 48px;">
        {"".join(items)}
      </div>
    </div>
  </section>"""

def gen_stats():
    return f"""
  <section style="padding: 40px 0;">
    <div class="container">
      <div class="grid grid-4">
        <div class="stat"><div class="number">50K+</div><div class="label">Active Users</div></div>
        <div class="stat"><div class="number">99.9%</div><div class="label">Uptime</div></div>
        <div class="stat"><div class="number">150+</div><div class="label">Countries</div></div>
        <div class="stat"><div class="number">24/7</div><div class="label">Support</div></div>
      </div>
    </div>
  </section>"""

def gen_cta(title="Ready to get started?"):
    return f"""
  <section id="contact" style="text-align: center;">
    <div class="container">
      <h2>{title}</h2>
      <p style="max-width: 500px; margin: 0 auto 32px;">Join thousands of teams already building with us.</p>
      <a href="#" class="btn btn-primary" style="font-size: 1.1rem; padding: 16px 40px;">Start Free →</a>
    </div>
  </section>"""

def gen_team(n=4):
    names = ["Alex Rivera", "Jordan Lee", "Sam Taylor", "Casey Morgan", "Riley Brooks", "Jamie Fox"]
    roles = ["CEO & Founder", "CTO", "Head of Design", "Lead Engineer", "VP Marketing", "Head of Product"]
    items = []
    for i in range(n):
        initials = "".join(w[0] for w in random.choice(names).split())
        items.append(f"""
      <div class="team-member">
        <div class="avatar">{initials}</div>
        <h3>random.choice(names)</h3>
        <p>random.choice(roles)</p>
      </div>""")
    return f"""
  <section id="about">
    <div class="container">
      <h2 style="text-align: center;">Meet the team</h2>
      <div class="grid grid-4" style="margin-top: 48px;">
        {"".join(items)}
      </div>
    </div>
  </section>"""

def gen_faq(n=5):
    qa = [
        ("How does the free trial work?", "You get full access to all features for 14 days. No credit card required."),
        ("Can I cancel anytime?", "Yes, you can cancel your subscription at any time with no penalties."),
        ("Is my data secure?", "We use enterprise-grade encryption and security practices to protect your data."),
        ("Do you offer refunds?", "Yes, we offer a 30-day money-back guarantee on all paid plans."),
        ("Can I upgrade or downgrade later?", "Absolutely! You can change your plan at any time from your dashboard."),
        ("Do you offer discounts for startups?", "Yes! We offer special pricing for early-stage startups. Contact us for details."),
        ("What integrations are available?", "We integrate with 100+ tools including Slack, GitHub, Jira, and more."),
        ("Is there an API?", "Yes, we offer a full REST API and webhooks for custom integrations."),
    ]
    items = []
    for i in range(min(n, len(qa))):
        q, a = qa[i]
        items.append(f"""
      <div class="faq-item">
        <h3>{q}</h3>
        <p>{a}</p>
      </div>""")
    return f"""
  <section>
    <div class="container" style="max-width: 800px;">
      <h2 style="text-align: center; margin-bottom: 48px;">Frequently asked questions</h2>
      {"".join(items)}
    </div>
  </section>"""

def gen_contact():
    return f"""
  <section id="contact">
    <div class="container" style="max-width: 600px;">
      <h2 style="text-align: center;">Get in touch</h2>
      <p style="text-align: center; margin-bottom: 40px;">We'd love to hear from you.</p>
      <div class="card">
        <div class="form-group">
          <label>Name</label>
          <input type="text" placeholder="Your name">
        </div>
        <div class="form-group">
          <label>Email</label>
          <input type="email" placeholder="you@example.com">
        </div>
        <div class="form-group">
          <label>Message</label>
          <textarea rows="5" placeholder="Tell us what you need..."></textarea>
        </div>
        <button class="btn btn-primary" style="width: 100%;">Send Message</button>
      </div>
    </div>
  </section>"""

def gen_newsletter():
    return f"""
  <section style="text-align: center;">
    <div class="container" style="max-width: 500px;">
      <h2>Stay in the loop</h2>
      <p>Subscribe for product updates and tips.</p>
      <div style="display: flex; gap: 8px;">
        <input type="email" placeholder="you@example.com" style="flex: 1; padding: 12px 16px; border-radius: var(--radius-sm); background: var(--surface); border: 1px solid rgba(255,255,255,0.1); color: var(--text);">
        <button class="btn btn-primary">Subscribe</button>
      </div>
    </div>
  </section>"""

def gen_blog_cards(n=6):
    titles = ["Getting Started with AI", "10 Tips for Better Code", "The Future of DevOps", "Building Scalable APIs", "Design Systems 101", "Why TypeScript Wins", "Cloud Migration Guide", "Microservices Explained", "The Art of Testing", "Zero to Production", "Modern CSS Tricks", "Database Optimization"]
    categories = ["Tutorial", "Opinion", "Guide", "News", "Review", "Deep Dive"]
    items = []
    for i in range(n):
        t = random.choice(titles)
        c = random.choice(categories)
        items.append(f"""
      <div class="card">
        <span class="badge">{c}</span>
        <h3 style="margin-top: 12px;">{t}</h3>
        <p>A comprehensive guide to {t.lower()} with practical examples and expert tips.</p>
        <a href="#" style="font-weight: 600;">Read more →</a>
      </div>""")
    return f"""
  <section id="blog">
    <div class="container">
      <h2 style="text-align: center;">From the blog</h2>
      <div class="grid grid-3" style="margin-top: 48px;">
        {"".join(items)}
      </div>
    </div>
  </section>"""

def gen_timeline(n=4):
    events = [("Jan 2024", "Founded", "Company incorporated with vision to transform the industry."),
              ("Mar 2024", "First Product", "Launched MVP with 100 beta users."),
              ("Jul 2024", "Series A", "Raised $10M to scale the team and product."),
              ("Dec 2024", "Global Launch", "Expanded to 50+ countries with 50K users."),
              ("Mar 2025", "Series B", "Raised $50M, reached 500K active users."),
              ("Aug 2025", "Enterprise", "Launched enterprise tier with Fortune 500 clients.")]
    items = []
    for i in range(min(n, len(events))):
        date, title, desc = events[i]
        items.append(f"""
      <div class="timeline-item">
        <span class="badge">{date}</span>
        <h3 style="margin-top: 8px;">{title}</h3>
        <p>{desc}</p>
      </div>""")
    return f"""
  <section>
    <div class="container" style="max-width: 700px;">
      <h2 style="text-align: center; margin-bottom: 48px;">Our journey</h2>
      {"".join(items)}
    </div>
  </section>"""

# === Template builders per category ===

def build_landing(palette, font, idx):
    biz = random.choice(BUSINESS_NAMES)
    title = random.choice(TAGLINES)
    tagline = f"{biz} helps you {title.lower()}. The all-in-one platform for modern teams."
    sections = [gen_navbar(biz), gen_hero(title, tagline, palette), gen_stats(),
                gen_features(random.randint(4, 9)), gen_pricing(),
                gen_testimonials(3), gen_cta(), gen_footer(biz)]
    return "".join(sections)

def build_portfolio(palette, font, idx):
    names = ["Alex Creative", "Jordan Design", "Sam Studio", "Casey Art"]
    name = random.choice(names)
    sections = [gen_navbar(name), f"""
  <div class="hero">
    <div class="container">
      <div class="avatar" style="width:120px;height:120px;font-size:3rem;margin:0 auto 24px;">{"".join(w[0] for w in name.split())}</div>
      <h1>Hi, I'm {name.split()[0]}</h1>
      <p style="font-size:1.25rem;max-width:500px;margin:0 auto 32px;">Designer & Developer crafting beautiful digital experiences.</p>
      <a href="#work" class="btn btn-primary">View Work</a>
      <a href="#contact" class="btn btn-outline">Get in Touch</a>
    </div>
  </div>""",
    f"""
  <section id="work">
    <div class="container">
      <h2 style="text-align:center;">Selected Projects</h2>
      <div class="grid grid-2" style="margin-top:48px;">
        {''.join(f'<div class="screenshot"><div style="height:200px;background:linear-gradient(135deg,{palette["primary"]},{palette["secondary"]});"></div><div style="padding:20px;"><h3>Project {i+1}</h3><p>Beautiful design project description.</p></div></div>' for i in range(random.randint(4, 8)))}
      </div>
    </div>
  </section>""",
    gen_stats(), gen_contact(), gen_footer(name)]
    return "".join(sections)

def build_blog(palette, font, idx):
    name = random.choice(BUSINESS_NAMES) + " Blog"
    sections = [gen_navbar(name), f"""
  <div class="hero">
    <div class="container">
      <h1>The {name}</h1>
      <p style="font-size:1.25rem;max-width:600px;margin:0 auto 32px;">Thoughts on technology, design, and building great products.</p>
    </div>
  </div>""",
    gen_blog_cards(random.randint(6, 12)), gen_newsletter(), gen_footer(name)]
    return "".join(sections)

def build_dashboard(palette, font, idx):
    sections = [gen_navbar("Dashboard"), f"""
  <div class="hero" style="padding:40px 0;">
    <div class="container" style="text-align:left;">
      <h1 style="font-size:2rem;">Dashboard</h1>
      <p>Welcome back! Here's your overview.</p>
    </div>
  </div>
  <section style="padding:0 0 40px;">
    <div class="container">
      <div class="grid grid-4">
        {''.join(f'<div class="card"><h3 style="color:var(--muted);font-size:0.9rem;">{m}</h3><div class="stat"><div class="number">{random.randint(100,9999)}</div></div><div style="color:var(--secondary);font-size:0.9rem;">↑ {random.randint(5,30)}% this month</div></div>' for m in ["Total Users", "Revenue", "Active Sessions", "Conversion Rate"])}
      </div>
      <div class="grid grid-2" style="margin-top:24px;">
        <div class="card"><h3>Recent Activity</h3>{'<div style="display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.05);"><div class="avatar">U</div><div><div style="font-weight:600;">User action</div><div style="color:var(--muted);font-size:0.9rem;">2 hours ago</div></div></div>' * 5}</div>
        <div class="card"><h3>Quick Actions</h3>{'<div style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.05);"><a href="#" style="display:flex;justify-content:space-between;align-items:center;"><span>Action item</span><span style="color:var(--muted);">→</span></a></div>' * 6}</div>
      </div>
    </div>
  </section>""",
    gen_footer("Dashboard")]
    return "".join(sections)

def build_ecommerce(palette, font, idx):
    name = random.choice(BUSINESS_NAMES) + " Store"
    products = ["Premium Hoodie", "Designer Mug", "Wireless Earbuds", "Smart Watch", "Leather Bag", "Sunglasses", "Backpack", "Sneakers", "Water Bottle", "Phone Case", "Desk Lamp", "Notebook"]
    items = []
    for i in range(8):
        p = random.choice(products)
        price = random.randint(19, 199)
        items.append(f"""
      <div class="card" style="padding:0;overflow:hidden;">
        <div style="height:180px;background:linear-gradient(135deg,{palette['primary']},{palette['secondary']});"></div>
        <div style="padding:20px;">
          <h3>{p}</h3>
          <p style="font-size:1.5rem;font-weight:700;color:var(--primary);">${price}.00</p>
          <a href="#" class="btn btn-primary" style="width:100%;">Add to Cart</a>
        </div>
      </div>""")
    sections = [gen_navbar(name), f"""
  <div class="hero" style="padding:60px 0;">
    <div class="container">
      <h1>New Collection</h1>
      <p style="font-size:1.25rem;max-width:600px;margin:0 auto 32px;">Discover products you'll love, at prices you'll adore.</p>
      <a href="#products" class="btn btn-primary">Shop Now</a>
    </div>
  </div>
  <section id="products" style="padding:40px 0;">
    <div class="container">
      <div class="grid grid-4">
        {"".join(items)}
      </div>
    </div>
  </section>""",
    gen_newsletter(), gen_footer(name)]
    return "".join(sections)

def build_resume(palette, font, idx):
    names = ["Alex Thompson", "Jordan Lee", "Sam Williams", "Casey Davis"]
    name = random.choice(names)
    skills = ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker", "PostgreSQL", "TypeScript", "Go", "Rust", "Kubernetes", "GraphQL"]
    exp = [("Senior Developer", "TechCorp", "2022-2024", "Led development of core platform serving 1M+ users."),
           ("Full Stack Developer", "StartupXYZ", "2020-2022", "Built and shipped 20+ features from scratch."),
           ("Software Engineer", "BigCo", "2018-2020", "Maintained legacy systems and modernized infrastructure.")]
    sections = [f"""
  <section style="padding:60px 0;">
    <div class="container" style="max-width:800px;">
      <div class="card">
        <h1>{name}</h1>
        <p style="font-size:1.25rem;">Full-Stack Developer</p>
        <p>{name.lower().replace(' ','')}@email.com | +1 555-0100 | San Francisco, CA</p>
        <div style="margin:24px 0;">
          {''.join(f'<span class="tag">{s}</span>' for s in random.sample(skills, 8))}
        </div>
        <h2 style="margin-top:32px;">Experience</h2>
        {''.join(f'<div style="margin:16px 0;padding:16px;background:var(--surface);border-radius:8px;"><div style="display:flex;justify-content:space-between;"><h3>{t}</h3><span class="badge">{d}</span></div><p style="color:var(--muted);">{c}</p><p>{desc}</p></div>' for t,c,d,desc in exp)}
        <h2 style="margin-top:32px;">Education</h2>
        <p>B.S. Computer Science — University of Technology (2014-2018)</p>
      </div>
    </div>
  </section>"""]
    return "".join(sections)

def build_coming_soon(palette, font, idx):
    name = random.choice(BUSINESS_NAMES)
    return f"""
  <div class="hero" style="min-height:100vh;display:flex;align-items:center;justify-content:center;">
    <div class="container" style="text-align:center;">
      <span class="badge">Coming Soon</span>
      <h1>{name}</h1>
      <p style="font-size:1.25rem;max-width:500px;margin:0 auto 32px;">Something amazing is on the way. Be the first to know.</p>
      <div style="display:flex;gap:8px;max-width:400px;margin:0 auto;">
        <input type="email" placeholder="Enter your email" style="flex:1;padding:12px 16px;border-radius:8px;background:var(--surface);border:1px solid rgba(255,255,255,0.1);color:var(--text);">
        <button class="btn btn-primary">Notify Me</button>
      </div>
      <div style="display:flex;gap:32px;justify-content:center;margin-top:48px;">
        <div class="stat"><div class="number" style="font-size:2rem;">30</div><div class="label">Days</div></div>
        <div class="stat"><div class="number" style="font-size:2rem;">12</div><div class="label">Hours</div></div>
        <div class="stat"><div class="number" style="font-size:2rem;">45</div><div class="label">Minutes</div></div>
      </div>
    </div>
  </div>"""

def build_404(palette, font, idx):
    return f"""
  <div class="hero" style="min-height:100vh;display:flex;align-items:center;justify-content:center;">
    <div class="container" style="text-align:center;">
      <h1 style="font-size:8rem;">404</h1>
      <p style="font-size:1.5rem;">Oops! This page got lost in the void.</p>
      <a href="/" class="btn btn-primary">← Back to Home</a>
    </div>
  </div>"""

def build_auth(palette, font, idx):
    action = "Sign In" if idx % 2 == 0 else "Create Account"
    return f"""
  <div class="hero" style="min-height:100vh;display:flex;align-items:center;justify-content:center;">
    <div class="container" style="max-width:400px;">
      <div class="card">
        <h1 style="font-size:2rem;">{action}</h1>
        <p style="margin-bottom:24px;">Welcome back! Please enter your details.</p>
        <div class="form-group"><label>Email</label><input type="email" placeholder="you@example.com"></div>
        <div class="form-group"><label>Password</label><input type="password" placeholder="••••••••"></div>
        <button class="btn btn-primary" style="width:100%;margin-top:8px;">{action}</button>
        <p style="text-align:center;margin-top:16px;">{'New here? <a href="#">Create account</a>' if idx%2==0 else 'Already have an account? <a href="#">Sign in</a>'}</p>
      </div>
    </div>
  </div>"""

def build_pricing_page(palette, font, idx):
    name = random.choice(BUSINESS_NAMES)
    return "".join([gen_navbar(name), f"""
  <div class="hero" style="padding:80px 0 40px;">
    <div class="container">
      <h1>Pricing</h1>
      <p style="max-width:500px;margin:0 auto;">Simple, honest pricing. No hidden fees. Cancel anytime.</p>
    </div>
  </div>""",
    gen_pricing(), gen_faq(5), gen_cta("Still have questions?"), gen_footer(name)])

def build_about(palette, font, idx):
    name = random.choice(BUSINESS_NAMES)
    return "".join([gen_navbar(name), f"""
  <div class="hero" style="padding:80px 0 40px;">
    <div class="container">
      <h1>About {name}</h1>
      <p style="max-width:600px;margin:0 auto;">We're on a mission to make great software accessible to everyone.</p>
    </div>
  </div>""",
    gen_stats(), gen_team(random.randint(3, 6)), gen_timeline(4), gen_cta(), gen_footer(name)])

def build_contact_page(palette, font, idx):
    name = random.choice(BUSINESS_NAMES)
    return "".join([gen_navbar(name), f"""
  <div class="hero" style="padding:80px 0 40px;">
    <div class="container">
      <h1>Contact Us</h1>
      <p style="max-width:500px;margin:0 auto;">We'd love to hear from you. Reach out anytime.</p>
    </div>
  </div>""",
    gen_contact(), gen_footer(name)])

def build_gallery(palette, font, idx):
    name = random.choice(BUSINESS_NAMES) + " Gallery"
    items = []
    for i in range(12):
        items.append(f'<div class="screenshot"><div style="height:{random.randint(200,400)}px;background:linear-gradient({random.randint(0,360)}deg,{palette["primary"]},{palette["secondary"]});"></div></div>')
    return "".join([gen_navbar(name), f"""
  <div class="hero" style="padding:60px 0 20px;">
    <div class="container"><h1>Gallery</h1><p>A collection of our finest work.</p></div>
  </div>
  <section style="padding:20px 0 60px;">
    <div class="container">
      <div class="grid grid-3" style="gap:16px;">
        {"".join(items)}
      </div>
    </div>
  </section>""",
    gen_footer(name)])

def build_docs(palette, font, idx):
    name = random.choice(BUSINESS_NAMES) + " Docs"
    return "".join([gen_navbar(name), f"""
  <div class="hero" style="padding:40px 0;text-align:left;">
    <div class="container" style="max-width:900px;">
      <span class="badge">Documentation</span>
      <h1 style="font-size:2.5rem;">Getting Started</h1>
      <p>Welcome to the {name} documentation. Everything you need to build with our platform.</p>
    </div>
  </div>
  <section style="padding:0 0 60px;">
    <div class="container" style="max-width:900px;">
      <div style="display:grid;grid-template-columns:240px 1fr;gap:32px;">
        <div style="position:sticky;top:80px;">
          <h3 style="margin-bottom:16px;">Contents</h3>
          {''.join(f'<a href="#" style="display:block;padding:8px 0;color:var(--muted);border-bottom:1px solid rgba(255,255,255,0.05);">{s}</a>' for s in ["Introduction","Installation","Quick Start","Configuration","API Reference","Examples","FAQ"])}
        </div>
        <div>
          <h2>Introduction</h2>
          <p>{name} is a powerful platform for building modern applications. This guide will help you get started quickly.</p>
          <h3 style="margin-top:24px;">Installation</h3>
          <div class="card" style="background:#0A0A0A;font-family:monospace;padding:16px;"><code>pip install {name.lower().replace(' ','-')}</code></div>
          <h3 style="margin-top:24px;">Quick Start</h3>
          <div class="card" style="background:#0A0A0A;font-family:monospace;padding:16px;"><code>import {name.lower().split()[0]}<br>app = {name.lower().split()[0]}.App()<br>app.run()</code></div>
        </div>
      </div>
    </div>
  </section>""",
    gen_footer(name)])

def build_profile(palette, font, idx):
    return f"""
  <div class="hero" style="padding:60px 0;min-height:100vh;">
    <div class="container" style="max-width:600px;">
      <div class="card" style="text-align:center;">
        <div class="avatar" style="width:96px;height:96px;font-size:2.5rem;margin:0 auto 16px;">U</div>
        <h1>John Doe</h1>
        <p>Software Engineer at TechCorp</p>
        <div style="margin:16px 0;">{''.join(f'<span class="tag">{s}</span>' for s in ["Python","React","AWS","Docker"])}</div>
        <div class="grid grid-2" style="margin-top:24px;text-align:left;">
          <div><h3>Stats</h3><p>Projects: 42</p><p>Followers: 1.2K</p><p>Following: 350</p></div>
          <div><h3>Activity</h3><p>Joined: Jan 2023</p><p>Last active: Now</p><p>Streak: 15 days</p></div>
        </div>
      </div>
    </div>
  </div>"""

def build_event(palette, font, idx):
    name = random.choice(["DevCon", "TechSummit", "AIConf", "CloudExpo", "CodeFest"])
    return "".join([gen_navbar(name), f"""
  <div class="hero" style="padding:100px 0 60px;">
    <div class="container">
      <span class="badge">{random.choice(["October 15-17, 2025","November 5-7, 2025","December 1-3, 2025"])}</span>
      <h1>{name} 2025</h1>
      <p style="font-size:1.25rem;max-width:600px;margin:0 auto 32px;">The biggest tech conference of the year. 3 days. 50+ speakers. 5000+ attendees.</p>
      <a href="#" class="btn btn-primary">Get Tickets</a>
      <a href="#" class="btn btn-outline">View Schedule</a>
    </div>
  </div>""",
    gen_stats(),
    f"""
  <section>
    <div class="container">
      <h2 style="text-align:center;">Featured Speakers</h2>
      <div class="grid grid-4" style="margin-top:48px;">
        {''.join(f'<div class="team-member"><div class="avatar">{"".join(w[0] for w in n.split())}</div><h3>{n}</h3><p>{r}</p></div>' for n,r in [("Dr. Sarah Chen","AI Researcher"),("Marc Goldberg","CTO Stripe"),("Ada Lovelace","Engineer"),("Linus Torvalds","Kernel Dev")])}
      </div>
    </div>
  </section>""",
    gen_cta("Ready to join?"), gen_footer(name)])

def build_newsletter_page(palette, font, idx):
    name = random.choice(BUSINESS_NAMES)
    return f"""
  <div class="hero" style="min-height:100vh;display:flex;align-items:center;justify-content:center;">
    <div class="container" style="max-width:500px;text-align:center;">
      <span class="badge">📰 Newsletter</span>
      <h1>Subscribe to {name}</h1>
      <p style="font-size:1.2rem;max-width:400px;margin:0 auto 32px;">Join 50,000+ readers getting our weekly digest of the best content, straight to your inbox.</p>
      <div style="display:flex;gap:8px;max-width:400px;margin:0 auto 24px;">
        <input type="email" placeholder="you@example.com" style="flex:1;padding:14px 18px;border-radius:8px;background:var(--surface);border:1px solid rgba(255,255,255,0.1);color:var(--text);font-size:1rem;">
        <button class="btn btn-primary">Subscribe Free</button>
      </div>
      <p style="font-size:0.9rem;">No spam. Unsubscribe anytime. We respect your privacy.</p>
    </div>
  </div>"""

def build_testimonial_page(palette, font, idx):
    name = random.choice(BUSINESS_NAMES)
    return "".join([gen_navbar(name), f"""
  <div class="hero" style="padding:60px 0 20px;">
    <div class="container"><h1>Customer Stories</h1><p>Don't just take our word for it.</p></div>
  </div>""",
    gen_testimonials(9), gen_cta("Join them today →"), gen_footer(name)])

def build_feature_page(palette, font, idx):
    name = random.choice(BUSINESS_NAMES)
    feat = random.choice(FEATURES)
    return "".join([gen_navbar(name), f"""
  <div class="hero" style="padding:80px 0 40px;">
    <div class="container">
      <span class="badge">Feature</span>
      <h1>{feat}</h1>
      <p style="max-width:600px;margin:0 auto 32px;">Everything you need to know about our {feat.lower()} capabilities.</p>
      <a href="#" class="btn btn-primary">Try it Free</a>
    </div>
  </div>
  <section>
    <div class="container">
      <div class="grid grid-2">
        <div class="card">
          <div class="feature-icon">⚡</div>
          <h3>Lightning Fast</h3>
          <p>Optimized for speed at every level.</p>
        </div>
        <div class="card">
          <div class="feature-icon">🔒</div>
          <h3>Secure by Default</h3>
          <p>Enterprise-grade security built in.</p>
        </div>
        <div class="card">
          <div class="feature-icon">📊</div>
          <h3>Analytics Built-in</h3>
          <p>Track everything that matters.</p>
        </div>
        <div class="card">
          <div class="feature-icon">🚀</div>
          <h3>Auto-scaling</h3>
          <p>From 0 to millions of users.</p>
        </div>
      </div>
    </div>
  </section>""",
    gen_cta(), gen_footer(name)])

def build_timeline_page(palette, font, idx):
    name = random.choice(BUSINESS_NAMES)
    return "".join([gen_navbar(name), f"""
  <div class="hero" style="padding:60px 0 20px;">
    <div class="container"><h1>Our Story</h1><p>The journey of {name}.</p></div>
  </div>""",
    gen_timeline(6), gen_cta("Join our journey"), gen_footer(name)])

def build_comparison_page(palette, font, idx):
    name = random.choice(BUSINESS_NAMES)
    return "".join([gen_navbar(name), f"""
  <div class="hero" style="padding:60px 0 20px;">
    <div class="container"><h1>How we compare</h1><p>See why teams choose {name}.</p></div>
  </div>
  <section>
    <div class="container" style="max-width:800px;">
      <div class="card" style="padding:0;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:var(--surface);">
              <th style="padding:16px;text-align:left;">Feature</th>
              <th style="padding:16px;color:var(--primary);">{name}</th>
              <th style="padding:16px;color:var(--muted);">Competitor A</th>
              <th style="padding:16px;color:var(--muted);">Competitor B</th>
            </tr>
          </thead>
          <tbody>
            {''.join(f'<tr style="border-bottom:1px solid rgba(255,255,255,0.05);"><td style="padding:16px;">{feat}</td><td style="padding:16px;text-align:center;color:var(--secondary);">✓</td><td style="padding:16px;text-align:center;color:var(--muted);">{random.choice(["✓","✗"])}</td><td style="padding:16px;text-align:center;color:var(--muted);">{random.choice(["✓","✗"])}</td></tr>' for feat in random.sample(FEATURES, 10))}
          </tbody>
        </table>
      </div>
    </div>
  </section>""",
    gen_cta(), gen_footer(name)])

# === Category config ===
CATEGORIES = {
    "landing": (build_landing, 1000),
    "portfolio": (build_portfolio, 1000),
    "blog": (build_blog, 1000),
    "dashboard": (build_dashboard, 1000),
    "ecommerce": (build_ecommerce, 1000),
    "resume": (build_resume, 500),
    "coming_soon": (build_coming_soon, 500),
    "404": (build_404, 500),
    "auth": (build_auth, 500),
    "pricing": (build_pricing_page, 500),
    "about": (build_about, 500),
    "contact": (build_contact_page, 500),
    "gallery": (build_gallery, 500),
    "documentation": (build_docs, 500),
    "profile": (build_profile, 500),
    "event": (build_event, 500),
    "newsletter": (build_newsletter_page, 500),
    "testimonial": (build_testimonial_page, 500),
    "feature": (build_feature_page, 500),
    "timeline": (build_timeline_page, 500),
    "comparison": (build_comparison_page, 500),
}

def generate():
    total = 0
    for category, (builder, count) in CATEGORIES.items():
        cat_dir = os.path.join(TEMPLATES_DIR, category)
        os.makedirs(cat_dir, exist_ok=True)
        for i in range(count):
            palette = PALETTES[i % len(PALETTES)]
            font = FONTS[i % len(FONTS)]
            random.seed(i * 100 + hash(category) % 1000)
            body = builder(palette, font, i)
            font_family = font[0]
            css = gen_css(palette, font_family)
            biz = random.choice(BUSINESS_NAMES)
            title = biz + " — " + random.choice(TAGLINES)
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{random.choice(TAGLINES)}">
  <style>{css}</style>
</head>
<body>
{body}
</body>
</html>"""
            template_dir = os.path.join(cat_dir, f"tpl_{i+1:04d}")
            os.makedirs(template_dir, exist_ok=True)
            with open(os.path.join(template_dir, "index.html"), "w") as f:
                f.write(html)
            meta = {
                "name": f"{category.title()} Template {i+1}",
                "category": category,
                "tags": [category, palette["name"].lower().replace(" ","-"), font[1].lower()],
                "layout": random.choice(LAYOUTS),
                "colors": palette,
                "responsive": True,
                "version": "1.0.0",
                "free": True,
            }
            with open(os.path.join(template_dir, "template.json"), "w") as f:
                json.dump(meta, f, indent=2)
            total += 1
        print(f"  ✅ {category}: {count} templates")
    return total

if __name__ == "__main__":
    print("🎨 EvolvixOS Template Generator — 10,000+ templates")
    print("=" * 50)
    total = generate()
    print("=" * 50)
    print(f"✅ Generated {total} templates!")
    print(f"📁 Location: {TEMPLATES_DIR}")
