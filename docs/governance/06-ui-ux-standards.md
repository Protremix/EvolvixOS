# VERDIS GOVERNANCE DOCUMENT 06: UI/UX STANDARDS

**Document Reference:** VERDIS-GOV-06  
**Status:** PERMANENT GOVERNANCE STANDARD  
**Version:** 1.0.0  
**Ratified:** August 5, 2026  
**Scope:** All User Interfaces, Web Applications, Mobile Applications, Desktop Apps, and Component Libraries across the Verdis Ecosystem.

---

## 1. OVERVIEW AND MANDATE

### 1.1 Purpose
This document defines the permanent UI/UX design standards for all digital products, interfaces, web applications, mobile interfaces, desktop clients, developer tools, and public portals across the Verdis Ecosystem. To maintain a world-class user experience competitive with top-tier technology platforms, every product in the Verdis Ecosystem must adhere strictly to these standards.

### 1.2 Scope
These UI/UX standards apply to all seven core products in the Verdis Ecosystem:
1. **Verdis Chain Explorer & Public Portal** (`explorer.verdis.network`, `verdis.network`)
2. **AegisOS AI Engineering Dashboard** (`aegis.verdis.network`)
3. **Verdis Applications** (Mobile Android/iOS, Desktop Windows/macOS/Linux, Web Wallet `wallet.verdis.network`)
4. **Verdis Trust Layer & Identity Portal** (`id.verdis.network`)
5. **Verdis Developer Cloud Console** (`cloud.verdis.network`)
6. **Verdis Marketplace** (`marketplace.verdis.network`)
7. **Verdis Developer Platform & Documentation Portal** (`docs.verdis.network`, `api.verdis.network`, `dev.verdis.network`)

---

## 2. CORE DESIGN PHILOSOPHY

The Verdis visual identity combines futuristic high-tech precision with natural, organic decentralized principles. The design language is defined by four core aesthetic pillars:

1. **Deep Space Dark Theme Base (`#0a0e0a`)**: A dark, low-fatigue background reminiscent of deep night and sovereign security.
2. **Vibrant Emerald Accent (`#00ff88`)**: A high-contrast electric green signature accent representing vitality, growth, cryptographic verification, and speed.
3. **Hexagonal Leaf Symbolism**: Geometric precision combined with natural organic structures. Hexagonal containers and leaf motifs signify resilience, modularity, and interconnectivity.
4. **Glassmorphism & Particle Networks**: Subtle translucent frosted glass layers (`backdrop-filter: blur(12px)`) overlaid on dynamic, ambient background particle networks that depict live decentralized node connections.

```
+-----------------------------------------------------------------------+
|  BACKGROUND: #0a0e0a (Deep Dark Obsidian)                             |
|  +-----------------------------------------------------------------+  |
|  | GLASS CARD: #18181a / rgba(24, 24, 26, 0.75)                     |  |
|  | BORDER: 1px solid rgba(0, 255, 136, 0.15)                         |  |
|  | ACCENT: #00ff88 (Verdis Electric Green)                         |  |
|  | TEXT: #ffffff (Primary) / #a0aec0 (Secondary)                   |  |
|  +-----------------------------------------------------------------+  |
+-----------------------------------------------------------------------+
```

---

## 3. DESIGN TOKENS & COLOR PALETTE SPECIFICATION

Every color and sizing variable used in the Verdis Ecosystem is standardized through CSS custom properties and design tokens. Raw, unstandardized hex codes or arbitrary pixel margins are strictly prohibited in application stylesheets.

### 3.1 Primary & Brand Colors
| Color Tokens | Hex Value | RGB / RGBA Value | Usage Description |
| :--- | :--- | :--- | :--- |
| `--verdis-bg-primary` | `#0a0e0a` | `rgb(10, 14, 10)` | Global application background (Deep Obsidian Dark) |
| `--verdis-bg-secondary` | `#121612` | `rgb(18, 22, 18)` | Secondary background, sidebar, navigation panels |
| `--verdis-surface-card` | `#18181a` | `rgba(24, 24, 26, 0.8)` | Glassmorphic cards, modal containers, popovers |
| `--verdis-surface-elevated`| `#222225` | `rgba(34, 34, 37, 0.9)` | Dropdown menus, tooltips, active floating layers |
| `--verdis-accent-primary` | `#00ff88` | `rgb(0, 255, 136)` | Signature Verdis Electric Green, CTAs, active states |
| `--verdis-accent-secondary`| `#1a2a1a` | `rgb(26, 42, 26)` | Deep emerald subtle fill, container hover backgrounds |
| `--verdis-accent-glow` | `#00ff8833` | `rgba(0, 255, 136, 0.2)` | Outer glow shadows, active selection halos |

### 3.2 Border & Divider Colors
| Color Tokens | Hex Value | RGBA Value | Usage Description |
| :--- | :--- | :--- | :--- |
| `--verdis-border-subtle` | `#1f291f` | `rgba(31, 41, 31, 0.6)` | Subtle table dividers, card separator lines |
| `--verdis-border-standard`| `#2a3a2a` | `rgba(42, 58, 42, 0.8)` | Default card borders, form input borders |
| `--verdis-border-active` | `#00ff88` | `rgba(0, 255, 136, 1.0)` | Focused inputs, selected items, active tabs |
| `--verdis-border-glow` | `#00ff8866` | `rgba(0, 255, 136, 0.4)` | Hover states for interactive glass cards |

### 3.3 Text & Iconography Hierarchy
| Color Tokens | Hex Value | Contrast Ratio | Usage Description |
| :--- | :--- | :--- | :--- |
| `--verdis-text-primary` | `#ffffff` | 17.8:1 (Pass AAA) | Headings, primary body text, titles, values |
| `--verdis-text-secondary` | `#a0aec0` | 9.2:1 (Pass AAA) | Subtitles, labels, secondary information |
| `--verdis-text-muted` | `#64748b` | 4.8:1 (Pass AA) | Timestamps, table column headers, disabled text |
| `--verdis-text-accent` | `#00ff88` | 13.5:1 (Pass AAA) | Monospaced hashes, highlighted values, links |

### 3.4 Functional & Status Colors
| Status Type | Hex Code | RGBA Fill (10%) | Usage Context |
| :--- | :--- | :--- | :--- |
| **Success / Active** | `#00ff88` | `rgba(0, 255, 136, 0.1)` | Confirmed tx, active validator, healthy node |
| **Warning / Pending** | `#ffb800` | `rgba(255, 184, 0, 0.1)` | Mempool tx, sync in progress, pending review |
| **Error / Failed** | `#ff3366` | `rgba(255, 51, 102, 0.1)` | Reverted tx, offline node, critical security alert |
| **Info / System** | `#00ccff` | `rgba(0, 204, 255, 0.1)` | Informational notifications, RPC metadata |
| **Consensus Special** | `#9945ff` | `rgba(153, 69, 255, 0.1)` | Solscan-inspired validator authority badges |

### 3.5 Spacing & Elevation Tokens
| Token Name | Pixel Value | Application |
| :--- | :--- | :--- |
| `--verdis-space-1` | `4px` | Fine padding, badge inner spacing |
| `--verdis-space-2` | `8px` | Gap between icon and text, compact button padding |
| `--verdis-space-3` | `12px` | Form field inner padding, list item gaps |
| `--verdis-space-4` | `16px` | Standard card inner padding, grid layout gaps |
| `--verdis-space-6` | `24px` | Section margins, container padding |
| `--verdis-space-8` | `32px` | Page header padding, major section gaps |
| `--verdis-space-12` | `48px` | Hero section padding, modal margins |
| `--verdis-z-dropdown` | `1000` | Floating dropdown menus and popovers |
| `--verdis-z-sticky` | `1020` | Sticky table headers and navigation bars |
| `--verdis-z-modal` | `1050` | Overlay modals and dialog backdrops |
| `--verdis-z-toast` | `1100` | Global notification toast alerts |

---

## 4. TYPOGRAPHY SYSTEM

Verdis uses a clean, highly legible typography stack designed for dense blockchain data, code, financial metrics, and dashboard analytics.

### 4.1 Font Families
- **Primary Body & Display Font**: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Monospace & Code Font**: `'JetBrains Mono', 'Fira Code', 'Roboto Mono', monospace`

```css
:root {
  --verdis-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --verdis-font-mono: 'JetBrains Mono', 'Fira Code', 'Roboto Mono', monospace;
}
```

### 4.2 Typography Scale & Responsive Specifications
| Scale Level | Desktop Size / Line-Height | Mobile Size / Line-Height | Weight | Tracking / Letter Spacing |
| :--- | :--- | :--- | :--- | :--- |
| **Display XL** | 48px / 1.1 | 32px / 1.2 | 800 (ExtraBold) | `-0.02em` |
| **Heading 1 (H1)**| 32px / 1.2 | 24px / 1.25 | 700 (Bold) | `-0.015em` |
| **Heading 2 (H2)**| 24px / 1.3 | 20px / 1.3 | 600 (SemiBold) | `-0.01em` |
| **Heading 3 (H3)**| 20px / 1.4 | 16px / 1.4 | 600 (SemiBold) | `0em` |
| **Body Large** | 16px / 1.5 | 14px / 1.5 | 400 (Regular) | `0em` |
| **Body Base** | 14px / 1.5 | 13px / 1.5 (Mobile Base) | 400 / 500 | `0em` |
| **Body Small** | 12px / 1.5 | 11px / 1.5 | 400 / 500 | `0.01em` |
| **Micro Tag** | 10px / 1.4 | 10px / 1.4 | 600 (SemiBold) | `0.05em UPPERCASE` |

---

## 5. BRANDING & ICONOGRAPHY SYSTEM

### 5.1 The Hexagonal Leaf Logo
The official Verdis logo features a sharp, geometric 6-sided polygon containing an stylized organic leaf structure with an electric green gradient (`linear-gradient(135deg, #00ff88, #1a2a1a)`).

```
        /       /        / /\      | |  | |
     |  \/  |
      \    /
       \  /
        \/
```

#### Logo Usage Rules
1. **Clear Space**: Always maintain a minimum clear space equal to 50% of the logo height around all four edges.
2. **Background Context**: The logo must only appear on dark backgrounds (`#0a0e0a`, `#121612`, `#18181a`). Placing the logo on white or light backgrounds is prohibited.
3. **Primary Accent**: The green gradient path must maintain full opacity. Scaling or altering aspect ratios without constraints is forbidden.

### 5.2 Iconography Guidelines
- **Icon Library**: Lucide Icons or custom SVG stroke icons.
- **Stroke Width**: Standard 1.5px stroke, 2.0px stroke for active/focused states.
- **Sizing Scale**:
  - Small: 16px (inline tables, micro tags)
  - Medium: 20px (standard buttons, form icons)
  - Large: 24px (navigation headers, page titles)
  - Display: 32px or 48px (hero sections, empty state illustrations)

---

## 6. COMPONENT LIBRARY STANDARDS

All UI components must be implemented as modular, reusable components adhering strictly to the specifications below.

### 6.1 Glassmorphism Cards (`.verdis-card`)
Cards are the primary container for data display. They feature dark translucent background fills with backdrop blurring and dynamic subtle hover borders.

```css
.verdis-card {
  background: rgba(24, 24, 26, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.verdis-card:hover {
  border-color: rgba(0, 255, 136, 0.4);
  box-shadow: 0 12px 40px 0 rgba(0, 255, 136, 0.1);
  transform: translateY(-2px);
}
```

### 6.2 Buttons & Interactive Triggers

#### 6.2.1 Button Hierarchy Matrix
| Type | Background | Text Color | Border | Usage Context |
| :--- | :--- | :--- | :--- | :--- |
| **Primary CTA** | `#00ff88` | `#0a0e0a` (Dark) | None | Main user action (Send Tx, Deploy, Sign) |
| **Secondary Glass** | `rgba(26, 42, 26, 0.6)` | `#00ff88` | `1px solid #00ff8844` | Secondary actions, filters, sub-menus |
| **Outline** | `transparent` | `#ffffff` | `1px solid #2a3a2a` | Cancel, close, secondary navigation |
| **Ghost / Flat** | `transparent` | `#a0aec0` | None | Icon buttons, inline table actions |
| **Destructive** | `rgba(255, 51, 102, 0.2)`| `#ff3366` | `1px solid #ff3366` | Revoke keys, purge data, delete project |

```css
.verdis-btn-primary {
  background-color: #00ff88;
  color: #0a0e0a;
  font-family: var(--verdis-font-sans);
  font-weight: 600;
  font-size: 14px;
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.verdis-btn-primary:hover {
  background-color: #33ff99;
  box-shadow: 0 0 25px rgba(0, 255, 136, 0.6);
  transform: translateY(-1px);
}

.verdis-btn-primary:disabled {
  background-color: #1f291f;
  color: #64748b;
  box-shadow: none;
  cursor: not-allowed;
  transform: none;
}
```

### 6.3 Form Controls & Inputs

Forms in Verdis applications must provide unambiguous feedback, dark glass styling, and active emerald glow rings.

```css
.verdis-input {
  background: rgba(18, 22, 18, 0.8);
  border: 1px solid #2a3a2a;
  border-radius: 8px;
  color: #ffffff;
  font-family: var(--verdis-font-sans);
  font-size: 14px;
  padding: 12px 16px;
  width: 100%;
  transition: all 0.2s ease;
}

.verdis-input:focus {
  outline: none;
  border-color: #00ff88;
  box-shadow: 0 0 12px rgba(0, 255, 136, 0.25);
}

.verdis-input-error {
  border-color: #ff3366 !important;
  box-shadow: 0 0 12px rgba(255, 51, 102, 0.25) !important;
}

.verdis-input-mono {
  font-family: var(--verdis-font-mono);
  font-size: 13px;
  letter-spacing: -0.01em;
}
```

### 6.4 Badges & Status Indicators
Status badges indicate live real-time conditions (block production, validation status, transaction outcome).

```css
.verdis-badge-active {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 255, 136, 0.1);
  color: #00ff88;
  border: 1px solid rgba(0, 255, 136, 0.3);
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.verdis-badge-active::before {
  content: "";
  width: 6px;
  height: 6px;
  background-color: #00ff88;
  border-radius: 50%;
  box-shadow: 0 0 8px #00ff88;
  animation: verdis-pulse 2s infinite;
}

@keyframes verdis-pulse {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
  100% { opacity: 1; transform: scale(1); }
}
```

### 6.5 Solscan-Inspired Data Tables & Explorer Grids
Blockchain and system metrics require high-density data presentation with instant readability.

1. **Monospaced Addresses & Hashes**: All cryptographic hashes, block hashes, and wallet addresses must use `JetBrains Mono` with middle truncation (`0x1234...5678`) and a built-in quick-copy clipboard button.
2. **Row Interactivity**: Hover states highlight rows with `#121612` fill and subtle left accent bar `#00ff88`.
3. **Sticky Header**: Table headers stick to top on scroll (`background: #0a0e0a`, `border-bottom: 1px solid #2a3a2a`).

```html
<table class="verdis-table">
  <thead>
    <tr>
      <th>Block Height</th>
      <th>Block Hash</th>
      <th>Validator</th>
      <th>Tx Count</th>
      <th>Time</th>
    </tr>
  </thead>
  <tbody>
    <tr class="verdis-table-row">
      <td class="verdis-mono-text font-bold text-accent">#1,482,910</td>
      <td class="verdis-mono-text">0x8f3a...b921 <button class="copy-btn">📋</button></td>
      <td class="verdis-validator-cell"><span class="badge-leaf">🍃</span> Node-Alpha-01</td>
      <td>142 txs</td>
      <td class="text-muted">2s ago</td>
    </tr>
  </tbody>
</table>
```

### 6.6 Charts & Data Visualizations
Charts in the Explorer, AegisOS, and Developer Cloud must follow specific visualization guidelines:
- Line charts must use gradient fills transitioning from `#00ff88` (30% opacity at top) to `#00ff88` (0% opacity at bottom).
- Grid lines must be subtle (`rgba(255, 255, 255, 0.05)`).
- Tooltips must use the glass card style (`#18181a` background, `#00ff88` border).

### 6.7 Modals & Drawer Overlays

Overlays must trap focus, blur the background, and provide clear exit triggers.

```css
.verdis-modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(10, 14, 10, 0.85);
  backdrop-filter: blur(8px);
  z-index: var(--verdis-z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
}

.verdis-modal-container {
  background: #18181a;
  border: 1px solid rgba(0, 255, 136, 0.25);
  border-radius: 16px;
  width: 100%;
  max-width: 560px;
  padding: 32px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
  animation: verdis-modal-enter 0.25s ease-out;
}

@keyframes verdis-modal-enter {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
```

---

## 7. ACCESSIBILITY & USABILITY (WCAG 2.1 AA)

All Verdis interfaces must comply fully with WCAG 2.1 Level AA standards. Accessibility is mandatory for all core components.

### 7.1 Contrast Ratio Requirements
- **Standard Body Text**: Minimum contrast ratio of 4.5:1 against any dark surface background.
- **Large Text (18px+ or 14px bold+)**: Minimum contrast ratio of 3.0:1.
- **UI Controls & Icons**: Minimum contrast ratio of 3.0:1 against adjacent colors.

### 7.2 Focus States & Keyboard Navigation
Every interactive component must display a visible, high-contrast emerald focus ring when focused via keyboard navigation. Default browser outline removal without replacement is strictly forbidden.

```css
*:focus-visible {
  outline: 2px solid #00ff88 !important;
  outline-offset: 2px !important;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.5) !important;
}
```

### 7.3 Screen Reader & ARIA Standards
- All non-text elements (buttons with icons, status dots, interactive charts) must include descriptive `aria-label` or `aria-labelledby` attributes.
- Dynamic data updates (e.g., live incoming blocks, AI CTO streaming response) must use `aria-live="polite"` or `aria-live="assertive"`.
- Modal dialogs must trap focus and expose `role="dialog"` with proper keyboard ESC listeners.

---

## 8. RESPONSIVE BREAKPOINTS & LAYOUT MATRIX

Interfaces must seamlessly adjust to mobile, tablet, desktop, and ultra-wide monitor displays.

### 8.1 Breakpoint Definitions
| Breakpoint Name | Screen Width Range | Grid Columns | Target Devices | Base Font |
| :--- | :--- | :--- | :--- | :--- |
| **Mobile** | `320px` to `639px` | 4 columns | Smartphones, Mobile Wallet | 13px |
| **Tablet** | `640px` to `1023px` | 8 columns | Tablets, Foldables, Small Laptops | 14px |
| **Desktop** | `1024px` to `1439px` | 12 columns | Standard Monitors, Laptops | 14px |
| **Wide Desktop** | `1440px` and above | 12 columns (max 1600px container)| Ultra-wide Displays, Workstations | 14px |

### 8.2 Mobile-First Guidelines
- **Mobile Base Font**: Mobile typography defaults to 13px base body text to maximize data density while retaining legibility.
- **Touch Targets**: Minimum interactive touch area on mobile is `44px x 44px`.
- **Navigation**: Desktop sidebar navigations collapse into a bottom glass navigation bar or top drawer menu on mobile displays.

---

## 9. ANIMATION & PERFORMANCE GUIDELINES

Micro-interactions enhance feedback without sacrificing UI performance.

### 9.1 Motion Standards & Cubic Bezier Curves
- **Standard Transition Duration**: 150ms to 250ms for UI hover and click interactions.
- **Modal / Overlay Transitions**: 300ms ease-out.
- **Timing Function**: `cubic-bezier(0.4, 0, 0.2, 1)` (Standard Smooth Ease).

### 9.2 Ambient Particle Network Canvas
The ambient background particle canvas simulates live node peer-to-peer messaging:
- **FPS Cap**: Canvas animations must be capped at 60 FPS using `requestAnimationFrame`.
- **Low-Power Fallback**: Detect `navigator.hardwareConcurrency` and battery API. If the user device is low-power or in battery-saver mode, disable particle connections and render static subtle gradient backgrounds.
- **Reduced Motion**: Respect `prefers-reduced-motion: reduce`. When set, disable particle physics and card tilt effects entirely.

```css
@media (prefers-reduced-motion: reduce) {
  *, ::before, ::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  .verdis-particle-canvas {
    display: none !important;
  }
}
```

---

## 10. BRAND CONSISTENCY ACROSS ALL 7 PRODUCTS

Every Verdis product must reflect unified design tokens, dark theme `#0a0e0a`, emerald accent `#00ff88`, and hexagonal brand assets.

| Product | Dominant Interface Style | Key UI Feature | Branding Accent |
| :--- | :--- | :--- | :--- |
| **1. Verdis Chain Explorer** | Solscan-inspired dark grid | Live block streamer, hash copy, transaction graph | `#00ff88` Green + `#9945ff` Validator |
| **2. AegisOS AI Dashboard** | Dual-pane AI workbench | Streaming agent pipeline, 9-gate quality progress bar | `#00ff88` Green + `#00ccff` AI Glow |
| **3. Verdis Apps (Wallet/Mobile)** | Mobile-first clean glass card | Hexagonal asset switcher, fast transfer sheet | `#00ff88` Green + `#121612` Deep Surface |
| **4. Verdis Trust Layer** | Compact security verification | Verdis ID badge, cryptographic signature inspector | `#00ff88` Shield Badge |
| **5. Verdis Developer Cloud** | Terminal & metric hybrid | 21-target Prometheus telemetry charts, container log stream | `#00ff88` Metric Lines |
| **6. Verdis Marketplace** | Grid card marketplace | Hexagonal extension tiles, star ratings, installer modal | `#00ff88` Card Hover |
| **7. Verdis Developer Platform** | Dual-column docs portal | Runnable code executor, API playground, copy buttons | `#00ff88` Code Syntax Highlights |

---

## 11. COMPREHENSIVE UI CODE TEMPLATE & STYLESHEET

Below is the canonical React/Tailwind/CSS HTML template for a Verdis Ecosystem application wrapper:

```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Verdis Ecosystem Portal</title>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" />
  <style>
    :root {
      --verdis-bg: #0a0e0a;
      --verdis-surface: #18181a;
      --verdis-accent: #00ff88;
      --verdis-accent-dark: #1a2a1a;
      --verdis-border: #2a3a2a;
      --verdis-text-main: #ffffff;
      --verdis-text-sub: #a0aec0;
      --verdis-font-sans: 'Inter', sans-serif;
      --verdis-font-mono: 'JetBrains Mono', monospace;
    }
    body {
      background-color: var(--verdis-bg);
      color: var(--verdis-text-main);
      font-family: var(--verdis-font-sans);
      margin: 0;
      padding: 0;
      overflow-x: hidden;
    }
    .verdis-glass-panel {
      background: rgba(24, 24, 26, 0.75);
      backdrop-filter: blur(12px);
      border: 1px solid var(--verdis-border);
      border-radius: 12px;
    }
    .verdis-hex-logo {
      clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
      background: linear-gradient(135deg, #00ff88, #1a2a1a);
    }
    /* Skeleton Shimmer Loading Placeholder */
    .verdis-skeleton {
      background: linear-gradient(90deg, #18181a 25%, #222225 50%, #18181a 75%);
      background-size: 200% 100%;
      animation: verdis-shimmer 1.5s infinite;
      border-radius: 6px;
    }
    @keyframes verdis-shimmer {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }
  </style>
</head>
<body>
  <div id="root">
    <!-- Verdis Standard Application Shell -->
    <header class="verdis-glass-panel flex items-center justify-between p-4 m-4">
      <div class="flex items-center gap-3">
        <div class="verdis-hex-logo w-10 h-10 flex items-center justify-center">
          <span class="text-black font-bold">V</span>
        </div>
        <h1 class="text-xl font-bold tracking-tight">Verdis <span class="text-[#00ff88]">Portal</span></h1>
      </div>
      <nav class="flex gap-6 text-sm text-[#a0aec0]">
        <a href="#" class="hover:text-[#00ff88] transition-colors">Explorer</a>
        <a href="#" class="hover:text-[#00ff88] transition-colors">AegisOS</a>
        <a href="#" class="hover:text-[#00ff88] transition-colors">Developer Cloud</a>
      </nav>
      <div>
        <button class="verdis-btn-primary">Connect Verdis ID</button>
      </div>
    </header>

    <main class="p-6 max-w-7xl mx-auto">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="verdis-glass-panel p-6">
          <h2 class="text-sm font-semibold text-[#a0aec0] uppercase tracking-wider mb-2">Block Height</h2>
          <div class="text-3xl font-bold text-[#00ff88] font-mono">#1,482,910</div>
          <p class="text-xs text-[#64748b] mt-2">BABE Consensus • Slot Time 6.0s</p>
        </div>
        <div class="verdis-glass-panel p-6">
          <h2 class="text-sm font-semibold text-[#a0aec0] uppercase tracking-wider mb-2">Active TPS</h2>
          <div class="text-3xl font-bold text-white font-mono">2,450 TPS</div>
          <p class="text-xs text-[#00ff88] mt-2">↑ 12% from previous epoch</p>
        </div>
        <div class="verdis-glass-panel p-6">
          <h2 class="text-sm font-semibold text-[#a0aec0] uppercase tracking-wider mb-2">AegisOS Quality Gate</h2>
          <div class="text-3xl font-bold text-[#00ff88] font-mono">9 / 9 Passed</div>
          <p class="text-xs text-[#00ccff] mt-2">GPT-4o CTO Verified</p>
        </div>
      </div>
    </main>
  </div>
</body>
</html>
```

---

## 12. ANTI-PATTERNS & FORBIDDEN DESIGN PRACTICES

To prevent brand erosion and maintain quality, the following practices are strictly banned across all repositories:

1. **Light Mode Fallbacks**: White backgrounds (`#ffffff`) or light-gray surface cards are prohibited. All applications must remain strictly dark-themed.
2. **Generic Blue Buttons**: Using standard primary blue (`#0066ff`, `#3b82f6`) for actions is forbidden. The primary CTA color is strictly `#00ff88`.
3. **Truncation Without Copy Button**: Rendering truncated hashes (`0x123...`) without a click-to-copy button or full tooltip preview is prohibited.
4. **Unconstrained Width Containers**: Full-width text paragraphs on wide desktop displays (>1440px) without a max-width wrapper (`max-w-7xl` or `1200px`) are forbidden due to readability loss.
5. **Layout Shift During Loading**: Asynchronous data elements must use skeleton shimmer placeholders matching target element height to avoid layout cumulative shifts (CLS).

---

## 13. UI GOVERNANCE CHECKLIST & AUDIT VERDICT

Before any front-end pull request or release artifact is approved by the GPT-4o CTO review pipeline, it must satisfy the following checklist:

- [ ] **Background Check**: Main container background is `#0a0e0a`.
- [ ] **Accent Uniformity**: Primary CTAs, active highlights, and live indicators use `#00ff88`.
- [ ] **Card Styling**: All container cards implement glassmorphism (`backdrop-filter: blur(12px)`) with subtle green border `#2a3a2a` or `rgba(0, 255, 136, 0.15)`.
- [ ] **Font Standards**: Body font is `Inter` (13px mobile, 14px desktop base). Cryptographic hashes and metrics use `JetBrains Mono`.
- [ ] **Accessibility Audit**: All interactive text elements pass 4.5:1 WCAG 2.1 AA contrast check. Focus rings are present for keyboard navigation.
- [ ] **Mobile Responsiveness**: Checked across 320px, 640px, 1024px, and 1440px viewports without horizontal scroll overflow.
- [ ] **Performance Cap**: Background canvas or animation loops capped at 60 FPS with low-power and `prefers-reduced-motion` fallbacks.
- [ ] **Copy Buttons**: Monospaced address/hash fields include interactive click-to-copy functionality.
- [ ] **No Raw Unapproved Hex Colors**: Stylesheets use standard CSS variables (`var(--verdis-*)`).
- [ ] **AegisOS & GPT Quality Gate**: UI pull request has been evaluated and approved by GPT-4o code review without Critical/High UI violations.
