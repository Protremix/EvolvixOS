#!/usr/bin/env python3
"""Generate the EvolvixOS legal pages (terms, refund, privacy).

One shared template so all three stay visually consistent with the landing page
brand tokens (cream/terracotta, Newsreader + Inter). Writes into WEB_DIR.

Placeholders that MUST be filled before Paddle review:
    {{LEGAL_ENTITY}}   registered company or sole-trader name
    {{REG_ADDRESS}}    registered address
    {{TAX_ID}}         NIF / CIF / VAT number
"""
import os

WEB_DIR = os.environ.get("WEB_DIR", "/opt/evolvixos/web")
EFFECTIVE = "29 August 2026"
SUPPORT = "info@evolvixos.com"
PRIVACY_EMAIL = "info@evolvixos.com"

MARK = (
    '<svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" '
    'role="img" aria-label="EvolvixOS"><defs><linearGradient id="gL" x1="0.05" '
    'y1="0" x2="0.95" y2="1"><stop offset="0" stop-color="#EE8A52"/><stop '
    'offset="0.42" stop-color="#D9663A"/><stop offset="1" stop-color="#7B3FA0"/>'
    '</linearGradient></defs><path d="M26.77,5.20 Q24.00,3.60 21.23,5.20 '
    'L9.10,12.20 Q6.33,13.80 6.33,17.00 L6.33,31.00 Q6.33,34.20 9.10,35.80 '
    'L21.23,42.80 Q24.00,44.40 26.77,42.80 L38.90,35.80 Q41.67,34.20 41.67,31.00 '
    'L41.67,17.00 Q41.67,13.80 38.90,12.20 Z M13.20,28.40 L24.00,16.80 '
    'L34.80,28.40 L34.80,33.40 L24.00,21.80 L13.20,33.40 Z" fill="url(#gL)" '
    'fill-rule="evenodd"/></svg>'
)

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#FAF9F6; --bg-soft:#F5F4EE; --bg-card:#FFF; --bg-warm:#F0EDE5;
  --text:#1A1915; --text-secondary:#6B6862; --text-muted:#9C9890;
  --accent:#C96442; --accent-hover:#B5563A; --accent-light:#F4E6DE;
  --border:#E5E2DA; --border-light:#EFECE4; --purple:#7C6F9E;
  --sans:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;
  --serif:'Newsreader',Georgia,serif;
}
html{scroll-behavior:smooth}
body{font-family:var(--sans);background:var(--bg);color:var(--text);
  line-height:1.7;-webkit-font-smoothing:antialiased;font-size:16px}
a{color:var(--accent);text-decoration:none;transition:color .18s ease}
a:hover{color:var(--accent-hover);text-decoration:underline}
a:focus-visible,button:focus-visible{outline:2px solid var(--accent);
  outline-offset:3px;border-radius:3px}

/* header */
.nav{position:sticky;top:0;z-index:50;background:rgba(250,249,246,.86);
  backdrop-filter:blur(14px);border-bottom:1px solid var(--border-light)}
.nav-inner{max-width:1100px;margin:0 auto;padding:14px 28px;display:flex;
  align-items:center;justify-content:space-between;gap:20px}
.brand{display:flex;align-items:center;gap:10px;font-weight:600;color:var(--text)}
.brand:hover{text-decoration:none;color:var(--text)}
.brand svg{width:30px;height:30px;display:block}
.brand-name{font-family:var(--serif);font-size:1.22rem;font-weight:600;
  letter-spacing:-.01em}
.brand-name .os{background:linear-gradient(100deg,var(--accent),var(--purple));
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.nav-links{display:flex;gap:24px;font-size:.9rem}
.nav-links a{color:var(--text-secondary)}
.nav-links a:hover{color:var(--accent);text-decoration:none}

/* layout */
.wrap{max-width:1100px;margin:0 auto;padding:56px 28px 96px;
  display:grid;grid-template-columns:224px 1fr;gap:56px;align-items:start}
.toc{position:sticky;top:92px;font-size:.86rem}
.toc h4{font-size:.72rem;text-transform:uppercase;letter-spacing:.09em;
  color:var(--text-muted);margin-bottom:14px;font-weight:600}
.toc ol{list-style:none;counter-reset:t}
.toc li{counter-increment:t;margin-bottom:2px}
.toc a{display:block;padding:5px 10px;border-radius:6px;color:var(--text-secondary);
  border-left:2px solid transparent;line-height:1.45}
.toc a:hover{background:var(--bg-warm);color:var(--accent);
  border-left-color:var(--accent);text-decoration:none}
.toc a::before{content:counter(t) ".";color:var(--text-muted);
  margin-right:7px;font-variant-numeric:tabular-nums}

.doc{min-width:0}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:.72rem;
  text-transform:uppercase;letter-spacing:.11em;font-weight:600;
  color:var(--accent);background:var(--accent-light);padding:6px 13px;
  border-radius:100px;margin-bottom:20px}
h1{font-family:var(--serif);font-size:clamp(2.1rem,5vw,3.1rem);font-weight:600;
  letter-spacing:-.025em;line-height:1.1;margin-bottom:16px}
h1 em{font-style:italic;background:linear-gradient(100deg,var(--accent),var(--purple));
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.lede{font-size:1.09rem;color:var(--text-secondary);max-width:62ch;margin-bottom:22px}
.meta{font-size:.84rem;color:var(--text-muted);padding-bottom:26px;
  border-bottom:1px solid var(--border);margin-bottom:14px}

h2{font-family:var(--serif);font-size:1.52rem;font-weight:600;letter-spacing:-.015em;
  margin:44px 0 14px;padding-top:14px;scroll-margin-top:96px}
h2 .num{color:var(--accent);font-size:1.05rem;margin-right:11px;
  font-family:var(--sans);font-weight:600;font-variant-numeric:tabular-nums}
h3{font-size:1.02rem;font-weight:600;margin:26px 0 9px;color:var(--text)}
p{margin-bottom:14px;color:var(--text-secondary);max-width:70ch}
ul,ol{margin:0 0 15px 22px;color:var(--text-secondary);max-width:68ch}
li{margin-bottom:7px}
strong{color:var(--text);font-weight:600}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.87em;
  background:var(--bg-warm);padding:2px 6px;border-radius:4px;color:var(--text)}

.callout{background:var(--bg-card);border:1px solid var(--border);
  border-left:3px solid var(--accent);border-radius:10px;padding:18px 22px;
  margin:22px 0;max-width:70ch}
.callout p:last-child{margin-bottom:0}
.callout.warm{background:var(--accent-light);border-color:var(--accent-light);
  border-left-color:var(--accent)}
.callout h3{margin-top:0}

table{width:100%;border-collapse:collapse;margin:20px 0;font-size:.92rem;
  background:var(--bg-card);border:1px solid var(--border);border-radius:10px;
  overflow:hidden}
th,td{text-align:left;padding:11px 15px;border-bottom:1px solid var(--border-light);
  vertical-align:top}
th{background:var(--bg-soft);font-weight:600;font-size:.8rem;
  text-transform:uppercase;letter-spacing:.05em;color:var(--text-secondary)}
tbody tr:last-child td{border-bottom:none}
td{color:var(--text-secondary)}

.fill{background:#FFF8E6;border:1px dashed #D9A441;color:#8A6410;
  padding:1px 7px;border-radius:4px;font-size:.87em;font-weight:600;
  font-family:ui-monospace,monospace}

/* footer */
footer{border-top:1px solid var(--border);background:var(--bg-soft);
  padding:38px 28px;text-align:center;font-size:.86rem;color:var(--text-muted)}
.foot-links{display:flex;gap:22px;justify-content:center;flex-wrap:wrap;
  margin-bottom:14px}
.foot-links a{color:var(--text-secondary)}

@media(max-width:880px){
  .wrap{grid-template-columns:1fr;gap:28px;padding:36px 22px 72px}
  .toc{position:static;background:var(--bg-card);border:1px solid var(--border);
    border-radius:10px;padding:18px 20px;order:-1}
  .nav-links{display:none}
}
@media print{.nav,.toc,footer{display:none}.wrap{display:block;max-width:none}}
"""


def page(slug, title, eyebrow, lede, sections, intro_html=""):
    toc = "\n".join(
        f'        <li><a href="#s{i}">{h}</a></li>'
        for i, (h, _) in enumerate(sections, 1))
    body = "\n".join(
        f'      <h2 id="s{i}"><span class="num">{i:02d}</span>{h}</h2>\n{c}'
        for i, (h, c) in enumerate(sections, 1))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} &middot; EvolvixOS</title>
<meta name="description" content="{lede}">
<meta name="robots" content="index,follow">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Newsreader:ital,wght@0,500;0,600;1,500&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<nav class="nav">
  <div class="nav-inner">
    <a href="/" class="brand">{MARK}<span class="brand-name">Evolvix<span class="os">OS</span></span></a>
    <div class="nav-links">
      <a href="/#pricing">Pricing</a>
      <a href="/terms">Terms</a>
      <a href="/refund-policy">Refunds</a>
      <a href="/privacy">Privacy</a>
      <a href="/platform/">Studio</a>
    </div>
  </div>
</nav>

<div class="wrap">
  <aside class="toc">
    <h4>On this page</h4>
    <ol>
{toc}
    </ol>
  </aside>

  <main class="doc">
    <span class="eyebrow">{eyebrow}</span>
    <h1>{title}</h1>
    <p class="lede">{lede}</p>
    <p class="meta">Effective {EFFECTIVE} &middot; Last updated {EFFECTIVE}</p>
{intro_html}
{body}
  </main>
</div>

<footer>
  <div class="foot-links">
    <a href="/">Home</a>
    <a href="/terms">Terms of Service</a>
    <a href="/refund-policy">Refund Policy</a>
    <a href="/privacy">Privacy Policy</a>
    <a href="https://github.com/Protremix/EvolvixOS">GitHub</a>
  </div>
  <p>&copy; 2026 EvolvixOS &middot; Software open-source under the MIT License</p>
</footer>
</body>
</html>
"""


ENTITY = ('<span class="fill">{{LEGAL_ENTITY}}</span>')
ADDRESS = ('<span class="fill">{{REG_ADDRESS}}</span>')
TAXID = ('<span class="fill">{{TAX_ID}}</span>')

# ══ TERMS OF SERVICE ═════════════════════════════════════════════════════════
TERMS = [
("Who we are and what these terms cover", f"""
      <p>EvolvixOS ("EvolvixOS", "we", "us") is an AI engineering platform operated by
      {ENTITY}, registered at {ADDRESS}, tax identification number {TAXID}, Spain.</p>
      <p>These Terms of Service ("Terms") form a binding agreement between you and us and
      govern your use of the hosted EvolvixOS service at evolvixos.com, including the
      Studio dashboard, the REST API, and any associated services (together, the
      "Service"). By creating an account or using the Service you accept these Terms.
      If you do not accept them, do not use the Service.</p>
      <div class="callout">
        <h3>The hosted Service and the open-source project are different things</h3>
        <p>The EvolvixOS source code is published under the MIT License and you may
        self-host it under that licence alone &mdash; these Terms do not restrict that.
        These Terms apply only to the <strong>hosted Service we operate</strong>, which
        includes managed infrastructure, model routing, and paid credits.</p>
      </div>
"""),
("Definitions", """
      <ul>
        <li><strong>Account</strong> &mdash; your registered access to the Service.</li>
        <li><strong>Credits</strong> &mdash; the unit used to meter consumption of compute
        and AI model usage on the Service.</li>
        <li><strong>Plan</strong> &mdash; a subscription tier that includes a recurring
        monthly Credit allowance.</li>
        <li><strong>Credit Pack</strong> &mdash; a one-time purchase of additional Credits.</li>
        <li><strong>Input</strong> &mdash; prompts, files, code, and other content you
        submit to the Service.</li>
        <li><strong>Output</strong> &mdash; content the Service generates in response to
        your Input.</li>
        <li><strong>Paddle</strong> &mdash; Paddle.com Market Ltd and its affiliates, our
        reseller and merchant of record (see section 4).</li>
      </ul>
"""),
("Eligibility and your account", """
      <p>You must be at least 18 years old and legally able to enter a contract. If you
      use the Service for an organisation, you confirm you are authorised to bind it, and
      "you" means that organisation.</p>
      <p>You agree to provide accurate registration details and keep them current. You are
      responsible for all activity under your Account and for keeping your credentials and
      API keys confidential. Tell us promptly at <a href="mailto:{support}">{support}</a>
      if you believe your Account has been compromised.</p>
      <p>One person or organisation may not operate multiple free Accounts to circumvent
      Credit allowances or rate limits.</p>
""".replace("{support}", SUPPORT)),
("Plans, billing, and our merchant of record", f"""
      <div class="callout warm">
        <p><strong>Payments are processed by Paddle, not by us.</strong> Paddle is the
        merchant of record and the reseller of the Service. Your purchase contract for
        payment is with Paddle, Paddle's own terms additionally apply to the transaction,
        and Paddle appears on your bank or card statement. Paddle calculates, collects and
        remits any applicable VAT, GST and sales tax.</p>
      </div>
      <p>Prices are shown in euro (EUR) and, where Paddle supports it, may be presented in
      your local currency. Applicable taxes are added at checkout by Paddle according to
      your billing location.</p>
      <h3>Renewal</h3>
      <p>Subscriptions renew automatically at the end of each billing period &mdash;
      monthly or annually, as selected &mdash; at the then-current price, until cancelled.
      We will give at least 30 days' notice before any price change affecting your
      renewal, and you may cancel before it takes effect.</p>
      <h3>Cancellation</h3>
      <p>You may cancel at any time from your Account or by contacting
      <a href="mailto:{SUPPORT}">{SUPPORT}</a>. Cancellation stops future renewals; your
      Plan remains active until the end of the period already paid for. Cancelling is not
      the same as requesting a refund &mdash; see our
      <a href="/refund-policy">Refund Policy</a>.</p>
      <h3>Failed payment</h3>
      <p>If a renewal payment fails, we may suspend paid features until payment succeeds.
      We will attempt to notify you before any suspension.</p>
"""),
("How Credits work", f"""
      <p>Credits meter your consumption of compute and AI models. Different models and
      operations consume Credits at different rates; current rates are shown in the
      Studio.</p>
      <table>
        <thead><tr><th>Credit type</th><th>Source</th><th>Expiry</th></tr></thead>
        <tbody>
          <tr><td>Plan allowance</td><td>Included monthly with a paid or free Plan</td>
              <td>Resets at the start of each billing period; unused allowance does
              <strong>not</strong> carry over</td></tr>
          <tr><td>Purchased Credits</td><td>Bought as a one-time Credit Pack</td>
              <td>Do not expire while your Account remains active</td></tr>
        </tbody>
      </table>
      <p>Credits have no cash value, are not a stored-value or payment instrument, and
      cannot be transferred between Accounts, sold, or exchanged for money except as
      required by law or as stated in our <a href="/refund-policy">Refund Policy</a>.</p>
      <p>If your Credit balance is exhausted, metered features stop working until your
      allowance resets or you purchase more. We may apply fair-use rate limits to protect
      platform stability, and will tell you if your usage pattern requires this.</p>
"""),
("Acceptable use", """
      <p>You must not use the Service to:</p>
      <ul>
        <li>break any applicable law, or infringe anyone's intellectual property,
        privacy, or other rights;</li>
        <li>generate or distribute malware, phishing content, or material designed to
        gain unauthorised access to systems;</li>
        <li>create sexual content involving minors, non-consensual sexual content, or
        content that incites violence or hatred;</li>
        <li>produce deepfakes, realistic synthetic likenesses of real people, or face-swap
        material intended to deceive;</li>
        <li>attempt to circumvent Credit metering, rate limits, security controls, or
        access controls, or probe or load-test the Service without our written consent;</li>
        <li>resell, sublicense, or provide the hosted Service to third parties as your own
        offering, or use it to train a competing model or service;</li>
        <li>scrape or bulk-extract the Service other than through the documented API and
        within its limits;</li>
        <li>submit personal data of others without a lawful basis, or submit special
        category data unless you have made your own assessment that doing so is lawful.</li>
      </ul>
      <p>Automated abuse detection may flag activity for review. We may investigate
      suspected breaches and take the steps described in section 11.</p>
"""),
("Third-party AI models, and your responsibility for Output", """
      <p>The Service routes requests to AI models. Depending on the model you select and
      your privacy mode, this may include models we run on our own infrastructure and
      models operated by third-party providers. When you select a third-party model, your
      Input is transmitted to that provider and handled under their terms. Our
      <a href="/privacy">Privacy Policy</a> lists current providers.</p>
      <div class="callout">
        <p><strong>AI Output can be wrong.</strong> Outputs are generated
        probabilistically and may be inaccurate, outdated, biased, insecure, or
        unintentionally similar to existing material. You are responsible for reviewing
        and testing Output before relying on it. Do not use Output as a substitute for
        professional legal, medical, financial, or safety-critical advice, and review any
        generated code for security before deploying it.</p>
      </div>
      <p>We make no claim of ownership over Output produced for you. Because identical or
      similar Output may be generated for other users, we cannot guarantee Output is
      unique or that it is free of third-party rights.</p>
"""),
("Intellectual property", f"""
      <h3>Your content</h3>
      <p>You keep all rights in your Input. You grant us a worldwide, non-exclusive,
      royalty-free licence to host, copy, transmit, and process your Input and Output
      strictly as needed to operate, secure, and support the Service. This licence ends
      when you delete the content or close your Account, except for backups pending
      deletion and anything we must keep by law.</p>
      <p><strong>We do not use your Input or Output to train our own models</strong>
      without your separate, explicit opt-in.</p>
      <h3>Our content</h3>
      <p>The hosted Service, its interfaces, and our trade marks and branding remain ours
      or our licensors'. Source code released under the MIT License is governed by that
      licence. Nothing here grants you rights in our branding.</p>
      <h3>Feedback</h3>
      <p>If you send us suggestions, we may use them freely without obligation to you.</p>
"""),
("Availability, support, and changes", f"""
      <p>We aim for high availability but do not guarantee the Service will be
      uninterrupted or error-free. Maintenance, updates, third-party provider outages, and
      circumstances beyond our reasonable control can all cause downtime. We publish
      operational status on the Service.</p>
      <p>Support is provided by email at <a href="mailto:{SUPPORT}">{SUPPORT}</a>. No
      specific response time is guaranteed unless separately agreed in writing.</p>
      <p>We may add, change, or remove features. If we discontinue a feature you actively
      rely on, or make a change that materially reduces core functionality, we will give
      reasonable advance notice where practicable and, for material reductions affecting a
      paid Plan, you may cancel and request a pro-rata refund of the unused paid period.</p>
"""),
("Your data and privacy", f"""
      <p>Our handling of personal data is described in the
      <a href="/privacy">Privacy Policy</a>, which forms part of these Terms. If you use
      the Service to process personal data of third parties as a controller, you are
      responsible for having a lawful basis and for meeting your own obligations; contact
      <a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a> if you require a data
      processing agreement.</p>
      <p>You are responsible for keeping your own backups of anything you cannot afford to
      lose. We maintain backups for operational resilience, not as a guaranteed archive
      service for you.</p>
"""),
("Suspension and termination", f"""
      <p>You may stop using the Service and close your Account at any time.</p>
      <p>We may suspend or limit your Account if we reasonably believe it is necessary to
      protect the Service, other users, or a third party &mdash; for example on suspected
      breach of section 6, security risk, non-payment, or a legal requirement. Where
      practicable we will notify you first and give you an opportunity to fix the problem;
      where we cannot, we will notify you as soon as we reasonably can and explain why.</p>
      <p>We may terminate for material breach that is not remedied within 14 days of
      notice, or immediately for serious breaches such as illegal use or a security
      attack. We may also terminate a free Account that has been inactive for over 12
      months after notifying you.</p>
      <p>On termination your right to use the Service ends and we may delete your data
      after a reasonable retention window (see the Privacy Policy). If we terminate
      without your breach, we will refund the unused portion of any prepaid period.
      Unused Credits are handled under the <a href="/refund-policy">Refund Policy</a>.</p>
"""),
("Disclaimers", """
      <p>Except as expressly stated in these Terms and as required by law, the Service is
      provided "as is" and "as available", and we exclude all implied warranties,
      including fitness for a particular purpose, merchantability, non-infringement, and
      that Output will be accurate or complete.</p>
      <p>We do not warrant that the Service will meet your requirements, that defects will
      be corrected, or that the Service or any third-party model is free of harmful
      components.</p>
      <p>Nothing in these Terms excludes or limits your statutory rights as a consumer.</p>
"""),
("Limitation of liability", """
      <p>Nothing in this section limits liability that cannot be limited by law, including
      liability for death or personal injury caused by negligence, or for fraud or
      fraudulent misrepresentation.</p>
      <p>Subject to that, we are not liable for indirect or consequential loss, loss of
      profits, revenue, business, goodwill, anticipated savings, or loss or corruption of
      data, however arising.</p>
      <p>Subject to the above, our total aggregate liability arising out of or in
      connection with the Service and these Terms is limited to the greater of (a) the
      total amounts you paid for the Service in the 12 months immediately before the event
      giving rise to the claim, and (b) EUR 100.</p>
      <p>These limits apply to the fullest extent permitted by law and do not affect the
      statutory rights of consumers.</p>
"""),
("Indemnity (business users)", """
      <p>If you use the Service other than as a consumer, you agree to indemnify us
      against claims, losses, and reasonable costs arising from your breach of these
      Terms, your unlawful use of the Service, your Input, or your use of Output &mdash;
      except to the extent caused by our own breach or negligence.</p>
"""),
("Changes to these Terms", """
      <p>We may update these Terms. For material changes affecting your rights or
      obligations we will give at least 30 days' notice by email or in-product notice
      before they take effect. Continuing to use the Service after that date means you
      accept the updated Terms; if you do not accept them, you may cancel before the
      effective date and request a pro-rata refund of any unused prepaid period.</p>
      <p>Non-material changes, such as clarifications or corrections, take effect when
      published. The effective date at the top of this page always reflects the current
      version.</p>
"""),
("Governing law and disputes", f"""
      <p>These Terms are governed by the laws of Spain, excluding its conflict-of-laws
      rules. The courts of Spain have jurisdiction.</p>
      <p>If you are a consumer resident in the European Union, you keep the protection of
      the mandatory consumer law of your country of residence, and you may bring
      proceedings in the courts of your own country.</p>
      <p>Before starting formal proceedings, please contact
      <a href="mailto:{SUPPORT}">{SUPPORT}</a> so we can try to resolve the matter
      directly. EU consumers may also use the European Commission's online dispute
      resolution platform.</p>
"""),
("Other terms", """
      <p><strong>Entire agreement.</strong> These Terms, the Refund Policy, and the
      Privacy Policy are the whole agreement between us about the Service.</p>
      <p><strong>Severability.</strong> If any provision is unenforceable, the rest stays
      in force.</p>
      <p><strong>No waiver.</strong> Not enforcing a right immediately does not waive it.</p>
      <p><strong>Assignment.</strong> You may not assign these Terms without our consent.
      We may assign them to an affiliate or in connection with a merger or sale of assets,
      provided your rights are not reduced.</p>
      <p><strong>Force majeure.</strong> Neither party is liable for delay or failure
      caused by events beyond its reasonable control.</p>
"""),
("Contact", f"""
      <p>General and billing support: <a href="mailto:{SUPPORT}">{SUPPORT}</a><br>
      Privacy and data protection: <a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a></p>
      <p>{ENTITY}<br>{ADDRESS}<br>Tax ID {TAXID} &middot; Spain</p>
"""),
]

# ══ REFUND POLICY ════════════════════════════════════════════════════════════
REFUND = [
("Summary", """
      <div class="callout warm">
        <p><strong>The short version.</strong> EU and UK consumers get a 14-day right to
        withdraw. Beyond that, we offer a 14-day goodwill refund on first-time
        subscription purchases, pro-rata refunds if we cause a material problem, and
        refunds of unused purchased Credits within 14 days. Credits you have already
        consumed cannot be refunded, because the compute behind them is already spent.</p>
      </div>
      <p>This policy sits alongside our <a href="/terms">Terms of Service</a> and never
      reduces your statutory rights.</p>
"""),
("Who processes your refund", f"""
      <p>Paddle is our reseller and merchant of record, so Paddle holds the payment
      transaction and issues refunds. You can request a refund either way:</p>
      <ul>
        <li>email us at <a href="mailto:{SUPPORT}">{SUPPORT}</a> and we will authorise it
        with Paddle; or</li>
        <li>contact Paddle directly using the order reference in your receipt email.</li>
      </ul>
      <p>Coming to us first is usually faster, and it lets us fix the underlying problem
      if there is one.</p>
"""),
("Your 14-day right of withdrawal (EU and UK consumers)", """
      <p>If you are a consumer in the EU or UK, you have a statutory right to withdraw
      from a distance purchase within <strong>14 days</strong> without giving a reason.</p>
      <div class="callout">
        <p><strong>One important exception to understand.</strong> For digital services
        that begin immediately, the law lets you consent to starting straight away and
        acknowledge that you lose the withdrawal right once the service is fully
        performed. At checkout you may be asked to give that consent so you can use the
        Service without waiting 14 days.</p>
        <p>Where you have given it, we do not treat the withdrawal right as lost outright.
        Instead we refund the portion you have not used, and deduct only the value of what
        you actually consumed &mdash; which is the fair outcome the law is aiming at.</p>
      </div>
      <p>To withdraw, email <a href="mailto:{support}">{support}</a> within 14 days of
      purchase with your account email and order reference. A clear statement is enough;
      no particular form is required.</p>
""".replace("{support}", SUPPORT)),
("Subscription plans", """
      <table>
        <thead><tr><th>Situation</th><th>What you get</th></tr></thead>
        <tbody>
          <tr><td>Within 14 days of your <strong>first</strong> paid subscription</td>
              <td>Full refund, less the value of Credits consumed beyond the free
              allowance</td></tr>
          <tr><td>Monthly renewal you did not intend</td>
              <td>Full refund if requested within 7 days of the charge and consumption in
              the new period was minimal</td></tr>
          <tr><td>Annual plan, after 14 days</td>
              <td>Pro-rata refund of complete unused months, at our discretion</td></tr>
          <tr><td>Mid-period cancellation</td>
              <td>No automatic refund &mdash; your plan stays active to the end of the
              paid period</td></tr>
          <tr><td>We materially reduce or discontinue a feature you rely on</td>
              <td>Pro-rata refund of the unused paid period</td></tr>
          <tr><td>Verified outage or defect that prevented substantial use</td>
              <td>Pro-rata credit or refund for the affected period</td></tr>
        </tbody>
      </table>
      <p>Cancelling and refunding are different actions. Cancelling stops the next
      renewal; a refund returns money already charged. If you want both, say so.</p>
"""),
("Credit packs", """
      <p>Purchased Credits are one-time purchases of consumable capacity.</p>
      <ul>
        <li><strong>Unused Credits</strong> &mdash; refundable in full within 14 days of
        purchase.</li>
        <li><strong>Partly used packs</strong> &mdash; within 14 days we refund the unused
        proportion, rounded in your favour to the nearest whole euro.</li>
        <li><strong>Consumed Credits</strong> &mdash; not refundable. The compute and
        third-party model calls behind them have already been paid for and cannot be
        reversed.</li>
        <li><strong>After 14 days</strong> &mdash; purchased Credits do not expire while
        your Account is active, so they stay available to use rather than being refunded.</li>
      </ul>
      <p>If Credits were consumed by a defect on our side, a runaway retry loop in the
      Service, or unauthorised access to your Account that you reported promptly, tell us
      &mdash; we will restore the Credits rather than treat them as consumed.</p>
"""),
("When we may decline a refund", """
      <p>We may refuse a refund where:</p>
      <ul>
        <li>the request falls outside the windows above and no statutory right applies;</li>
        <li>the Account breached the acceptable use rules in our
        <a href="/terms">Terms of Service</a>;</li>
        <li>there is evidence of refund abuse, such as repeatedly buying, consuming, and
        reclaiming the same product, or serial free-trial and refund cycling;</li>
        <li>Credits were consumed in substantial volume before the request, other than in
        the fault cases described in section 5;</li>
        <li>the purchase was made by a business rather than a consumer, and no contractual
        right to refund applies.</li>
      </ul>
      <p>If we decline, we will tell you why and point to the specific ground. You can ask
      us to reconsider with additional context, and you retain any statutory rights and
      the ability to escalate to Paddle.</p>
"""),
("How to request a refund", f"""
      <p>Email <a href="mailto:{SUPPORT}">{SUPPORT}</a> with:</p>
      <ul>
        <li>the email address on your Account;</li>
        <li>the order or receipt reference from Paddle;</li>
        <li>what you bought and roughly when;</li>
        <li>the reason &mdash; brief is fine, and required only outside the statutory
        withdrawal window.</li>
      </ul>
      <h3>Timescales</h3>
      <ul>
        <li>We acknowledge requests within <strong>2 business days</strong>.</li>
        <li>We decide within <strong>5 business days</strong>, sooner for clear-cut
        statutory withdrawals.</li>
        <li>Approved refunds are issued by Paddle to the original payment method,
        typically arriving within <strong>5&ndash;10 business days</strong> depending on
        your bank.</li>
      </ul>
      <p>Refunds go back to the original payment method. We cannot redirect a refund to a
      different card or account.</p>
"""),
("Chargebacks", f"""
      <p>If something has gone wrong, please contact us before raising a chargeback with
      your bank. Chargebacks are slow for you, costly for us, and usually resolvable in a
      single email.</p>
      <p>While a chargeback is open on your Account we may suspend paid features until it
      is resolved. If a chargeback is decided in our favour and the Account shows a
      pattern of abuse, we may decline future service.</p>
      <p>We would rather fix the problem. Start with
      <a href="mailto:{SUPPORT}">{SUPPORT}</a>.</p>
"""),
("Changes to this policy", """
      <p>We may update this policy. Changes apply to purchases made after the new
      effective date and never retroactively reduce rights attached to a purchase you have
      already made. Material changes will be announced at least 30 days in advance.</p>
"""),
]

# ══ PRIVACY POLICY ═══════════════════════════════════════════════════════════
PRIVACY = [
("Who is responsible for your data", f"""
      <p>The data controller is {ENTITY}, {ADDRESS}, tax identification number {TAXID},
      Spain. We are responsible for the personal data described in this policy.</p>
      <p>Questions, or to exercise any right below:
      <a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a>.</p>
      <p>This policy covers the hosted EvolvixOS service at evolvixos.com. If you
      self-host the open-source software, we receive no data from your instance and this
      policy does not apply to it.</p>
"""),
("What we collect", """
      <h3>You give us</h3>
      <ul>
        <li><strong>Account data</strong> &mdash; email address, display name, password
        hash, and any organisation details you add.</li>
        <li><strong>Content</strong> &mdash; prompts, files, code, project data, and
        generated outputs you create using the Service.</li>
        <li><strong>Support correspondence</strong> &mdash; messages you send us.</li>
        <li><strong>Optional messaging identifiers</strong> &mdash; your Telegram or
        WhatsApp identifier, only if you connect those channels.</li>
      </ul>
      <h3>We generate or observe</h3>
      <ul>
        <li><strong>Usage and metering</strong> &mdash; requests made, models selected,
        Credits consumed, timestamps, feature usage.</li>
        <li><strong>Technical data</strong> &mdash; IP address, browser and device type,
        approximate location derived from IP, session and authentication tokens.</li>
        <li><strong>Security logs</strong> &mdash; sign-in attempts, one-time-code
        verifications, rate-limit and abuse-detection events.</li>
      </ul>
      <h3>We receive from others</h3>
      <ul>
        <li><strong>Payment confirmations</strong> from Paddle &mdash; order reference,
        product, amount, billing country, and partial card details such as the last four
        digits and card brand. <strong>We never receive your full card number.</strong></li>
      </ul>
      <p>We do not deliberately collect special category data. Please do not submit health,
      biometric, or similar sensitive data unless you have satisfied yourself that doing so
      is lawful.</p>
"""),
("Why we use it, and our legal basis", """
      <table>
        <thead><tr><th>Purpose</th><th>Data</th><th>Legal basis</th></tr></thead>
        <tbody>
          <tr><td>Create and operate your account, deliver the Service</td>
              <td>Account, content, technical</td><td>Performance of a contract</td></tr>
          <tr><td>Meter Credits and bill correctly</td><td>Usage, payment confirmations</td>
              <td>Performance of a contract</td></tr>
          <tr><td>Authenticate you, including email one-time codes</td>
              <td>Account, security logs</td><td>Performance of a contract</td></tr>
          <tr><td>Prevent fraud, abuse, and attacks; keep the platform stable</td>
              <td>Technical, security logs, usage</td><td>Legitimate interests</td></tr>
          <tr><td>Provide support and respond to you</td><td>Account, correspondence</td>
              <td>Performance of a contract</td></tr>
          <tr><td>Improve reliability and diagnose faults</td>
              <td>Aggregated usage, error logs</td><td>Legitimate interests</td></tr>
          <tr><td>Service and security announcements</td><td>Account</td>
              <td>Legitimate interests</td></tr>
          <tr><td>Marketing emails, if you opt in</td><td>Account</td><td>Consent</td></tr>
          <tr><td>Meet accounting, tax, and legal obligations</td>
              <td>Account, payment records</td><td>Legal obligation</td></tr>
        </tbody>
      </table>
      <div class="callout">
        <p><strong>We do not sell your personal data</strong>, and we do not use your
        prompts or generated outputs to train our own models unless you explicitly opt in.
        We do not use your content for advertising.</p>
      </div>
"""),
("AI models and where your prompts go", """
      <p>This matters more than anything else in this policy, so it gets its own section.</p>
      <p>When you send a request, EvolvixOS routes it to a model. Which model, and
      therefore where your data goes, depends on the model you pick and your configured
      privacy mode:</p>
      <ul>
        <li><strong>Local models</strong> &mdash; run on infrastructure we control. Your
        prompt is not sent to any third-party model provider.</li>
        <li><strong>Third-party models</strong> &mdash; your prompt and relevant context
        are transmitted to that provider so they can generate a response. They process it
        under their own terms and privacy policy.</li>
      </ul>
      <p>Third-party model providers currently reachable through the Service include Groq,
      Google (Gemini), OpenRouter, and Moonshot AI (Kimi). The set may change as models are
      added or retired; the Studio shows which provider serves each model before you use
      it.</p>
      <p>If you need prompts to stay off third-party infrastructure entirely, set your
      privacy mode to local-only. If you handle other people's personal data in prompts,
      choose your model accordingly and contact us for a data processing agreement.</p>
"""),
("Who else processes your data", f"""
      <p>We use a small number of providers who process data on our behalf under
      contract:</p>
      <table>
        <thead><tr><th>Provider</th><th>Role</th><th>Location</th></tr></thead>
        <tbody>
          <tr><td>Hetzner Online GmbH</td><td>Server hosting and infrastructure</td>
              <td>Germany (EU)</td></tr>
          <tr><td>Paddle.com Market Ltd</td><td>Merchant of record, payments, invoicing,
              tax</td><td>United Kingdom</td></tr>
          <tr><td>Brevo</td><td>Transactional email, including sign-in codes</td>
              <td>France (EU)</td></tr>
          <tr><td>AI model providers</td><td>Generating responses to your prompts
              (section 4)</td><td>Varies, including United States</td></tr>
        </tbody>
      </table>
      <p>We may also disclose data where legally required, to establish or defend legal
      claims, or to a successor entity in a merger or acquisition &mdash; in which case we
      will tell you before your data becomes subject to a different policy.</p>
"""),
("International transfers", """
      <p>Our core infrastructure is in the European Union. Some providers, particularly AI
      model providers, are outside the EEA, including in the United States.</p>
      <p>Where data leaves the EEA we rely on an adequacy decision where one covers the
      provider, or otherwise on the European Commission's Standard Contractual Clauses
      together with additional safeguards such as encryption in transit and data
      minimisation. You can request details of the safeguards for a specific transfer.</p>
"""),
("How long we keep it", """
      <table>
        <thead><tr><th>Data</th><th>Retention</th></tr></thead>
        <tbody>
          <tr><td>Account data</td><td>While your Account is active, then up to 90 days
              after closure</td></tr>
          <tr><td>Content (prompts, projects, outputs)</td><td>Until you delete it, or up
              to 30 days after Account closure</td></tr>
          <tr><td>Usage and Credit metering records</td><td>24 months, for billing
              accuracy and dispute resolution</td></tr>
          <tr><td>Security and access logs</td><td>12 months</td></tr>
          <tr><td>Invoices and payment records</td><td>As required by Spanish tax law,
              generally 6 years</td></tr>
          <tr><td>Support correspondence</td><td>24 months after the case closes</td></tr>
          <tr><td>Backups</td><td>Rolling, overwritten within 35 days</td></tr>
        </tbody>
      </table>
"""),
("Your rights", f"""
      <p>Under the GDPR you can ask us to:</p>
      <ul>
        <li><strong>Access</strong> &mdash; get a copy of your personal data.</li>
        <li><strong>Rectify</strong> &mdash; correct data that is wrong or incomplete.</li>
        <li><strong>Erase</strong> &mdash; delete your data, where no legal obligation
        requires us to keep it.</li>
        <li><strong>Restrict</strong> &mdash; pause processing while a dispute is
        resolved.</li>
        <li><strong>Port</strong> &mdash; receive your data in a machine-readable format,
        or have it sent to another provider.</li>
        <li><strong>Object</strong> &mdash; to processing based on legitimate interests,
        and to marketing at any time.</li>
        <li><strong>Withdraw consent</strong> &mdash; where consent is the basis, without
        affecting past processing.</li>
      </ul>
      <p>Email <a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a>. We respond within one
      month, extendable by two further months for complex requests, and we will tell you if
      we need longer. We may ask you to confirm your identity. Exercising these rights is
      free unless a request is manifestly excessive.</p>
      <p>You can close your Account and delete your content yourself at any time from the
      Studio.</p>
      <h3>Complaints</h3>
      <p>Please raise concerns with us first. You also have the right to complain to the
      Spanish supervisory authority, the Agencia Espa&ntilde;ola de Protecci&oacute;n de
      Datos (AEPD, aepd.es), or to the authority in your EU country of residence.</p>
"""),
("Cookies and similar technologies", """
      <p>We keep this minimal. We use:</p>
      <ul>
        <li><strong>Strictly necessary cookies and local storage</strong> &mdash; to keep
        you signed in, hold session and authentication tokens, remember your interface
        preferences such as theme, and protect against cross-site request forgery. These
        are required for the Service to work and do not need consent.</li>
      </ul>
      <p>We do not use advertising cookies, cross-site tracking pixels, or third-party
      analytics that profile you across other websites. If we introduce non-essential
      cookies we will ask for your consent first and update this section.</p>
      <p>You can clear cookies and local storage in your browser, but doing so will sign
      you out.</p>
"""),
("Security", """
      <p>We protect your data with measures including encryption in transit over TLS,
      hashed passwords, scoped API keys, authentication on all platform endpoints,
      row-level access controls so users only reach their own records, rate limiting,
      input validation against injection and server-side request forgery, audit logging of
      privileged actions, and restricted administrative access.</p>
      <p>No system is perfectly secure. If a breach occurs that is likely to result in a
      risk to your rights, we will notify the AEPD within 72 hours and inform you without
      undue delay where the risk to you is high.</p>
      <p>Please report suspected vulnerabilities to
      <a href="mailto:{privacy}">{privacy}</a>. We will not pursue good-faith security
      research that respects user privacy and avoids service disruption.</p>
""".replace("{privacy}", PRIVACY_EMAIL)),
("Children", """
      <p>The Service is not intended for anyone under 18 and we do not knowingly collect
      their data. If you believe a minor has created an Account, contact us and we will
      delete it.</p>
"""),
("Changes to this policy", f"""
      <p>We may update this policy. For material changes we will notify you by email or
      in-product notice at least 30 days before they take effect. The effective date at the
      top always reflects the current version, and we keep prior versions available on
      request from <a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a>.</p>
"""),
]

PAGES = [
    ("terms.html", "Terms of Service", "Legal",
     "The agreement between you and EvolvixOS covering the hosted platform, "
     "subscriptions, credits, and acceptable use.", TERMS),
    ("refund-policy.html", "Refund Policy", "Legal",
     "When you can get your money back, how to ask, and how long it takes.", REFUND),
    ("privacy.html", "Privacy Policy", "Legal",
     "What data EvolvixOS collects, why, who processes it, where your prompts go, "
     "and the rights you have over it.", PRIVACY),
]


def main():
    os.makedirs(WEB_DIR, exist_ok=True)
    for filename, title, eyebrow, lede, sections in PAGES:
        html = page(filename[:-5], title, eyebrow, lede, sections)
        path = os.path.join(WEB_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  wrote {path}  ({len(html):,} bytes, {len(sections)} sections)")


if __name__ == "__main__":
    main()
