#!/usr/bin/env python3
"""Replace the tools section in landing_new.html with a highly polished, animated version."""

import re

FILE = "/opt/evolvixos/web/landing_new.html"

with open(FILE, "r") as f:
    content = f.read()

# ─── 1. Replace CSS block (from .tools-section to the closing @media) ───
old_css_start = ".tools-section {"
old_css_end = ".tools-section { padding: 80px 20px; }\n}\n"

css_start_idx = content.index(old_css_start)
css_end_idx = content.index(old_css_end, css_start_idx) + len(old_css_end)

NEW_CSS = r""".tools-section {
  padding: 140px 40px 100px;
  max-width: 1280px;
  margin: 0 auto;
  position: relative;
  z-index: 2;
}

/* Radar pulse from section center */
.tools-radar {
  position: absolute;
  top: 25%; left: 50%;
  width: 200px; height: 200px;
  transform: translate(-50%, -50%);
  z-index: -1;
  pointer-events: none;
}
.tools-radar::before,
.tools-radar::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid rgba(168, 85, 247, 0.15);
  animation: radarPulse 4s ease-out infinite;
}
.tools-radar::after {
  animation-delay: 2s;
}
@keyframes radarPulse {
  0% { transform: scale(0.3); opacity: 1; border-width: 2px; }
  100% { transform: scale(4); opacity: 0; border-width: 0.5px; }
}

.tools-bg-glow {
  position: absolute;
  top: 20%; left: 50%;
  width: 700px; height: 500px;
  transform: translateX(-50%);
  background: radial-gradient(ellipse, rgba(168, 85, 247, 0.08) 0%, transparent 70%);
  filter: blur(80px);
  z-index: -1;
  animation: toolsGlow 8s ease-in-out infinite;
}
@keyframes toolsGlow {
  0%, 100% { transform: translateX(-50%) scale(1); opacity: 0.6; }
  50% { transform: translateX(-50%) scale(1.2); opacity: 1; }
}

/* Animated counter for "44" */
.tools-counter {
  display: inline-flex;
  align-items: baseline;
  position: relative;
}
.tools-counter-num {
  background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: inherit;
  font-weight: inherit;
}

/* Category filter pills */
.tools-filters {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin: 32px 0 8px;
}
.tool-filter {
  padding: 8px 18px;
  border-radius: 100px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-dim);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}
.tool-filter::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(168,85,247,0.2), rgba(236,72,153,0.2));
  opacity: 0;
  transition: opacity 0.3s;
}
.tool-filter:hover {
  color: var(--text);
  border-color: rgba(168,85,247,0.3);
  transform: translateY(-2px);
}
.tool-filter.active {
  color: #fff;
  border-color: transparent;
  background: linear-gradient(135deg, rgba(168,85,247,0.3), rgba(236,72,153,0.3));
  box-shadow: 0 4px 15px rgba(168,85,247,0.2);
}
.tool-filter .filter-count {
  font-size: 11px;
  opacity: 0.5;
  margin-left: 4px;
}

/* Marquee */
.marquee-wrapper {
  overflow: hidden;
  width: 100%;
  margin: 24px 0;
  mask-image: linear-gradient(90deg, transparent 0%, black 6%, black 94%, transparent 100%);
  -webkit-mask-image: linear-gradient(90deg, transparent 0%, black 6%, black 94%, transparent 100%);
}
.marquee-wrapper-reverse {
  margin-top: -8px;
}
.marquee {
  display: flex;
  gap: 14px;
  width: max-content;
  animation: marqueeScroll 45s linear infinite;
}
.marquee-right {
  animation: marqueeScrollRight 38s linear infinite;
}
.marquee:hover {
  animation-play-state: paused;
}
@keyframes marqueeScroll {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}
@keyframes marqueeScrollRight {
  from { transform: translateX(-50%); }
  to { transform: translateX(0); }
}
.marquee-item {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 14px 24px;
  border-radius: 100px;
  background: var(--tool-bg, rgba(168, 85, 247, 0.08));
  border: 1px solid rgba(168, 85, 247, 0.15);
  font-family: 'JetBrains Mono', monospace;
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: default;
  position: relative;
  overflow: hidden;
}
/* Holographic shimmer sweep on marquee items */
.marquee-item::after {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
  animation: shimmerSweep 3s ease-in-out infinite;
}
@keyframes shimmerSweep {
  0% { left: -100%; }
  100% { left: 200%; }
}
.marquee-item:hover {
  transform: translateY(-4px) scale(1.08);
  border-color: var(--tool-fg, var(--primary));
  box-shadow: 0 8px 25px rgba(0,0,0,0.3), 0 0 30px var(--tool-bg);
  background: var(--tool-bg);
}
.marquee-item:hover::after {
  display: none;
}
.marquee-icon {
  font-size: 20px;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: inline-block;
  animation: iconFloat 3s ease-in-out infinite;
}
@keyframes iconFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}
.marquee-item:hover .marquee-icon {
  transform: scale(1.3) rotate(-8deg);
  animation: none;
}
.marquee-name {
  color: var(--tool-fg, var(--primary-light));
  letter-spacing: -0.3px;
}

/* Tools Grid */
.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
  margin-top: 32px;
}
.tool-chip {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px;
  border-radius: 18px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
              box-shadow 0.4s ease,
              border-color 0.4s ease;
  position: relative;
  overflow: hidden;
  cursor: default;
  /* Stagger reveal */
  opacity: 0;
  transform: translateY(30px) scale(0.95);
}
.tool-chip.revealed {
  opacity: 1;
  transform: translateY(0) scale(1);
}
/* Animated gradient top border */
.tool-chip::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--tool-fg, var(--primary)), transparent);
  background-size: 200% 100%;
  transform: scaleX(0);
  transform-origin: center;
  transition: transform 0.5s ease;
}
.tool-chip:hover::before {
  transform: scaleX(1);
  animation: borderFlow 2s linear infinite;
}
@keyframes borderFlow {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}
/* Holographic radial glow */
.tool-chip::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at var(--mx, 50%) var(--my, 0%), var(--tool-bg, transparent) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}
.tool-chip:hover {
  border-color: var(--tool-fg, var(--primary));
  box-shadow: 0 12px 40px rgba(0,0,0,0.3), 0 0 30px var(--tool-bg);
}
.tool-chip:hover::after { opacity: 1; }
.tool-chip-icon {
  font-size: 32px;
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: inline-block;
  animation: iconFloatCard 4s ease-in-out infinite;
}
@keyframes iconFloatCard {
  0%, 100% { transform: translateY(0) rotate(0); }
  33% { transform: translateY(-3px) rotate(-2deg); }
  66% { transform: translateY(2px) rotate(2deg); }
}
.tool-chip:hover .tool-chip-icon {
  transform: scale(1.25) rotate(-8deg);
  animation: none;
}
.tool-chip-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 700;
  color: var(--tool-fg, var(--primary-light));
  letter-spacing: -0.3px;
}
.tool-chip-cat {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 1px;
}
/* Power level bar */
.tool-chip-power {
  height: 3px;
  border-radius: 100px;
  background: rgba(255,255,255,0.05);
  overflow: hidden;
  margin-top: 4px;
}
.tool-chip-power-fill {
  height: 100%;
  border-radius: 100px;
  background: linear-gradient(90deg, var(--tool-fg, var(--primary)), transparent);
  width: 0;
  transition: width 1.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tool-chip.revealed .tool-chip-power-fill {
  width: var(--power, 80%);
}
/* Category badge on card */
.tool-chip-badge {
  position: absolute;
  top: 10px; right: 10px;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 3px 8px;
  border-radius: 100px;
  background: var(--tool-bg, rgba(168,85,247,0.1));
  color: var(--tool-fg, var(--primary-light));
  opacity: 0;
  transform: scale(0.8);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tool-chip:hover .tool-chip-badge {
  opacity: 1;
  transform: scale(1);
}

/* Filtered out animation */
.tool-chip.filtered-out {
  opacity: 0.15;
  transform: scale(0.9);
  filter: grayscale(1);
  pointer-events: none;
}

.tools-cta {
  text-align: center;
  margin-top: 48px;
}

/* Stats bar */
.tools-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin: 24px 0 0;
  flex-wrap: wrap;
}
.tools-stat {
  text-align: center;
}
.tools-stat-num {
  font-size: 24px;
  font-weight: 800;
  font-family: 'JetBrains Mono', monospace;
  background: linear-gradient(135deg, #a78bfa, #ec4899);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.tools-stat-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 2px;
}

@media (max-width: 768px) {
  .tools-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
  .tool-chip { padding: 16px; }
  .tool-chip-icon { font-size: 26px; }
  .marquee-item { padding: 10px 18px; font-size: 13px; }
  .tools-section { padding: 80px 20px; }
  .tools-stats { gap: 20px; }
  .tools-stat-num { font-size: 18px; }
}

"""

content = content[:css_start_idx] + NEW_CSS + content[css_end_idx:]

# ─── 2. Replace HTML section ───
section_start = content.index('<section class="tools-section" id="tools">')
# Find the closing </section> for tools
section_end_marker = '</section>'
section_end_idx = content.index(section_end_marker, section_start) + len(section_end_marker)

NEW_HTML = '''<section class="tools-section" id="tools">
  <div class="tools-radar"></div>
  <div class="tools-bg-glow"></div>
  <div class="section-center reveal">
    <div class="section-tag">🛠️ Agent Toolkit</div>
    <h2 class="section-title"><span class="tools-counter"><span class="tools-counter-num" data-count="44">0</span><span>+</span></span> Built-in <span class="grad">Tools</span></h2>
    <p class="section-subtitle">
      Mr. James — the built-in AI agent — has an arsenal of 44+ tools at its disposal.
      From file operations and code execution to cloud management and media production,
      it can autonomously build, deploy, and manage your entire stack.
    </p>
  </div>

  <!-- Stats bar -->
  <div class="tools-stats reveal">
    <div class="tools-stat"><div class="tools-stat-num" data-count="46">0</div><div class="tools-stat-label">Total Tools</div></div>
    <div class="tools-stat"><div class="tools-stat-num" data-count="12">0</div><div class="tools-stat-label">Categories</div></div>
    <div class="tools-stat"><div class="tools-stat-num" data-count="6">0</div><div class="tools-stat-label">AI Models</div></div>
    <div class="tools-stat"><div class="tools-stat-num" data-count="3">0</div><div class="tools-stat-label">Comms Channels</div></div>
  </div>

  <!-- Category Filters -->
  <div class="tools-filters reveal" id="toolFilters">
    <div class="tool-filter active" data-cat="all">All <span class="filter-count">46</span></div>
    <div class="tool-filter" data-cat="FILE OPS">File Ops</div>
    <div class="tool-filter" data-cat="EXECUTION">Execution</div>
    <div class="tool-filter" data-cat="SYSTEM">System</div>
    <div class="tool-filter" data-cat="WEB & API">Web & API</div>
    <div class="tool-filter" data-cat="AI MODELS">AI Models</div>
    <div class="tool-filter" data-cat="MEMORY">Memory</div>
    <div class="tool-filter" data-cat="CLOUD">Cloud</div>
    <div class="tool-filter" data-cat="DEVOPS">DevOps</div>
    <div class="tool-filter" data-cat="MEDIA">Media</div>
    <div class="tool-filter" data-cat="BLOCKCHAIN">Blockchain</div>
    <div class="tool-filter" data-cat="COMMS">Comms</div>
    <div class="tool-filter" data-cat="ANALYTICS">Analytics</div>
  </div>

  <!-- Marquee Row 1 (left to right) -->
  <div class="marquee-wrapper">
    <div class="marquee marquee-left">
      <div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">📁</span><span class="marquee-name">file_read</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">📁</span><span class="marquee-name">file_list</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">✏️</span><span class="marquee-name">file_edit</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">📝</span><span class="marquee-name">file_write</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">📤</span><span class="marquee-name">file_upload</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">💻</span><span class="marquee-name">bash</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">🐍</span><span class="marquee-name">python_exec</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">📦</span><span class="marquee-name">sandbox_exec</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">🔧</span><span class="marquee-name">pip_install</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">🔍</span><span class="marquee-name">code_analyze</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">⚙️</span><span class="marquee-name">service_check</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">🔄</span><span class="marquee-name">service_restart</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">🐳</span><span class="marquee-name">docker_ps</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">🚀</span><span class="marquee-name">docker_restart</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">📊</span><span class="marquee-name">system_info</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">🩺</span><span class="marquee-name">process_startup_check</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🌐</span><span class="marquee-name">web_search</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🔗</span><span class="marquee-name">web_fetch</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">📡</span><span class="marquee-name">http_request</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🧠</span><span class="marquee-name">smart_api_call</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🛤️</span><span class="marquee-name">api_auto_route</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🤖</span><span class="marquee-name">call_free_llm</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">👁️</span><span class="marquee-name">gemini_vision</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">🗣️</span><span class="marquee-name">gemini_tts</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">🎭</span><span class="marquee-name">set_persona</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">🔎</span><span class="marquee-name">search_subagents</span></div>
<div class="marquee-item" style="--tool-bg:rgba(245, 158, 11, 0.1);--tool-fg:#f59e0b"><span class="marquee-icon">🧩</span><span class="marquee-name">team_memory_search</span></div>
<div class="marquee-item" style="--tool-bg:rgba(245, 158, 11, 0.1);--tool-fg:#f59e0b"><span class="marquee-icon">💾</span><span class="marquee-name">team_memory_save</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">☁️</span><span class="marquee-name">tencent_cloud</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">🌿</span><span class="marquee-name">git</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">⚡</span><span class="marquee-name">skill_exec</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">🎨</span><span class="marquee-name">ui_generate</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🎬</span><span class="marquee-name">video_generate</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🖼️</span><span class="marquee-name">image_generate</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🎤</span><span class="marquee-name">voice_command</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🎵</span><span class="marquee-name">audio_synthesize</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🔤</span><span class="marquee-name">logo_generate</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">💎</span><span class="marquee-name">3d_render</span></div>
<div class="marquee-item" style="--tool-bg:rgba(245, 158, 11, 0.1);--tool-fg:#f59e0b"><span class="marquee-icon">₿</span><span class="marquee-name">crypto_analyze</span></div>
<div class="marquee-item" style="--tool-bg:rgba(245, 158, 11, 0.1);--tool-fg:#f59e0b"><span class="marquee-icon">⛓️</span><span class="marquee-name">defi_scan</span></div>
<div class="marquee-item" style="--tool-bg:rgba(245, 158, 11, 0.1);--tool-fg:#f59e0b"><span class="marquee-icon">👛</span><span class="marquee-name">wallet_track</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">💬</span><span class="marquee-name">telegram_send</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">📱</span><span class="marquee-name">whatsapp_send</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">📧</span><span class="marquee-name">email_send</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">📈</span><span class="marquee-name">analytics_query</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">📉</span><span class="marquee-name">entity_aggregate</span></div>
      <!-- Duplicate for seamless loop -->
      <div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">📁</span><span class="marquee-name">file_read</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">📁</span><span class="marquee-name">file_list</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">✏️</span><span class="marquee-name">file_edit</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">📝</span><span class="marquee-name">file_write</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">📤</span><span class="marquee-name">file_upload</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">💻</span><span class="marquee-name">bash</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">🐍</span><span class="marquee-name">python_exec</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">📦</span><span class="marquee-name">sandbox_exec</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">🔧</span><span class="marquee-name">pip_install</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">🔍</span><span class="marquee-name">code_analyze</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">⚙️</span><span class="marquee-name">service_check</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">🔄</span><span class="marquee-name">service_restart</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">🐳</span><span class="marquee-name">docker_ps</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">🚀</span><span class="marquee-name">docker_restart</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">📊</span><span class="marquee-name">system_info</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">🩺</span><span class="marquee-name">process_startup_check</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🌐</span><span class="marquee-name">web_search</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🔗</span><span class="marquee-name">web_fetch</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">📡</span><span class="marquee-name">http_request</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🧠</span><span class="marquee-name">smart_api_call</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🛤️</span><span class="marquee-name">api_auto_route</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🤖</span><span class="marquee-name">call_free_llm</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">👁️</span><span class="marquee-name">gemini_vision</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">🗣️</span><span class="marquee-name">gemini_tts</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">🎭</span><span class="marquee-name">set_persona</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">🔎</span><span class="marquee-name">search_subagents</span></div>
<div class="marquee-item" style="--tool-bg:rgba(245, 158, 11, 0.1);--tool-fg:#f59e0b"><span class="marquee-icon">🧩</span><span class="marquee-name">team_memory_search</span></div>
<div class="marquee-item" style="--tool-bg:rgba(245, 158, 11, 0.1);--tool-fg:#f59e0b"><span class="marquee-icon">💾</span><span class="marquee-name">team_memory_save</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">☁️</span><span class="marquee-name">tencent_cloud</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">🌿</span><span class="marquee-name">git</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">⚡</span><span class="marquee-name">skill_exec</span></div>
<div class="marquee-item" style="--tool-bg:rgba(52, 211, 153, 0.1);--tool-fg:#34d399"><span class="marquee-icon">🎨</span><span class="marquee-name">ui_generate</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🎬</span><span class="marquee-name">video_generate</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🖼️</span><span class="marquee-name">image_generate</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🎤</span><span class="marquee-name">voice_command</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🎵</span><span class="marquee-name">audio_synthesize</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">🔤</span><span class="marquee-name">logo_generate</span></div>
<div class="marquee-item" style="--tool-bg:rgba(236, 72, 153, 0.1);--tool-fg:#ec4899"><span class="marquee-icon">💎</span><span class="marquee-name">3d_render</span></div>
<div class="marquee-item" style="--tool-bg:rgba(245, 158, 11, 0.1);--tool-fg:#f59e0b"><span class="marquee-icon">₿</span><span class="marquee-name">crypto_analyze</span></div>
<div class="marquee-item" style="--tool-bg:rgba(245, 158, 11, 0.1);--tool-fg:#f59e0b"><span class="marquee-icon">⛓️</span><span class="marquee-name">defi_scan</span></div>
<div class="marquee-item" style="--tool-bg:rgba(245, 158, 11, 0.1);--tool-fg:#f59e0b"><span class="marquee-icon">👛</span><span class="marquee-name">wallet_track</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">💬</span><span class="marquee-name">telegram_send</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">📱</span><span class="marquee-name">whatsapp_send</span></div>
<div class="marquee-item" style="--tool-bg:rgba(129, 140, 248, 0.1);--tool-fg:#818cf8"><span class="marquee-icon">📧</span><span class="marquee-name">email_send</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">📈</span><span class="marquee-name">analytics_query</span></div>
<div class="marquee-item" style="--tool-bg:rgba(168, 85, 247, 0.1);--tool-fg:#c084fc"><span class="marquee-icon">📉</span><span class="marquee-name">entity_aggregate</span></div>
    </div>
  </div>

  <!-- Interactive Grid -->
  <div class="tools-grid" id="toolsGrid">
    <div class="tool-chip" data-tilt data-cat="FILE OPS" style="--tool-bg:rgba(168,85,247,0.1);--tool-fg:#c084fc;--power:95%"><span class="tool-chip-badge">FILE OPS</span><span class="tool-chip-icon">📁</span><span class="tool-chip-name">file_read</span><span class="tool-chip-cat">File Ops</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="FILE OPS" style="--tool-bg:rgba(168,85,247,0.1);--tool-fg:#c084fc;--power:90%"><span class="tool-chip-badge">FILE OPS</span><span class="tool-chip-icon">📁</span><span class="tool-chip-name">file_list</span><span class="tool-chip-cat">File Ops</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="FILE OPS" style="--tool-bg:rgba(168,85,247,0.1);--tool-fg:#c084fc;--power:88%"><span class="tool-chip-badge">FILE OPS</span><span class="tool-chip-icon">✏️</span><span class="tool-chip-name">file_edit</span><span class="tool-chip-cat">File Ops</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="FILE OPS" style="--tool-bg:rgba(168,85,247,0.1);--tool-fg:#c084fc;--power:85%"><span class="tool-chip-badge">FILE OPS</span><span class="tool-chip-icon">📝</span><span class="tool-chip-name">file_write</span><span class="tool-chip-cat">File Ops</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="FILE OPS" style="--tool-bg:rgba(168,85,247,0.1);--tool-fg:#c084fc;--power:82%"><span class="tool-chip-badge">FILE OPS</span><span class="tool-chip-icon">📤</span><span class="tool-chip-name">file_upload</span><span class="tool-chip-cat">File Ops</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="EXECUTION" style="--tool-bg:rgba(52,211,153,0.1);--tool-fg:#34d399;--power:98%"><span class="tool-chip-badge">EXECUTION</span><span class="tool-chip-icon">💻</span><span class="tool-chip-name">bash</span><span class="tool-chip-cat">Execution</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="EXECUTION" style="--tool-bg:rgba(52,211,153,0.1);--tool-fg:#34d399;--power:95%"><span class="tool-chip-badge">EXECUTION</span><span class="tool-chip-icon">🐍</span><span class="tool-chip-name">python_exec</span><span class="tool-chip-cat">Execution</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="EXECUTION" style="--tool-bg:rgba(52,211,153,0.1);--tool-fg:#34d399;--power:90%"><span class="tool-chip-badge">EXECUTION</span><span class="tool-chip-icon">📦</span><span class="tool-chip-name">sandbox_exec</span><span class="tool-chip-cat">Execution</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="EXECUTION" style="--tool-bg:rgba(52,211,153,0.1);--tool-fg:#34d399;--power:85%"><span class="tool-chip-badge">EXECUTION</span><span class="tool-chip-icon">🔧</span><span class="tool-chip-name">pip_install</span><span class="tool-chip-cat">Execution</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="EXECUTION" style="--tool-bg:rgba(52,211,153,0.1);--tool-fg:#34d399;--power:80%"><span class="tool-chip-badge">EXECUTION</span><span class="tool-chip-icon">🔍</span><span class="tool-chip-name">code_analyze</span><span class="tool-chip-cat">Execution</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="SYSTEM" style="--tool-bg:rgba(129,140,248,0.1);--tool-fg:#818cf8;--power:92%"><span class="tool-chip-badge">SYSTEM</span><span class="tool-chip-icon">⚙️</span><span class="tool-chip-name">service_check</span><span class="tool-chip-cat">System</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="SYSTEM" style="--tool-bg:rgba(129,140,248,0.1);--tool-fg:#818cf8;--power:88%"><span class="tool-chip-badge">SYSTEM</span><span class="tool-chip-icon">🔄</span><span class="tool-chip-name">service_restart</span><span class="tool-chip-cat">System</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="SYSTEM" style="--tool-bg:rgba(129,140,248,0.1);--tool-fg:#818cf8;--power:85%"><span class="tool-chip-badge">SYSTEM</span><span class="tool-chip-icon">🐳</span><span class="tool-chip-name">docker_ps</span><span class="tool-chip-cat">System</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="SYSTEM" style="--tool-bg:rgba(129,140,248,0.1);--tool-fg:#818cf8;--power:82%"><span class="tool-chip-badge">SYSTEM</span><span class="tool-chip-icon">🚀</span><span class="tool-chip-name">docker_restart</span><span class="tool-chip-cat">System</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="SYSTEM" style="--tool-bg:rgba(129,140,248,0.1);--tool-fg:#818cf8;--power:78%"><span class="tool-chip-badge">SYSTEM</span><span class="tool-chip-icon">📊</span><span class="tool-chip-name">system_info</span><span class="tool-chip-cat">System</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="SYSTEM" style="--tool-bg:rgba(129,140,248,0.1);--tool-fg:#818cf8;--power:75%"><span class="tool-chip-badge">SYSTEM</span><span class="tool-chip-icon">🩺</span><span class="tool-chip-name">process_startup_check</span><span class="tool-chip-cat">System</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="WEB & API" style="--tool-bg:rgba(236,72,153,0.1);--tool-fg:#ec4899;--power:96%"><span class="tool-chip-badge">WEB & API</span><span class="tool-chip-icon">🌐</span><span class="tool-chip-name">web_search</span><span class="tool-chip-cat">Web & API</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="WEB & API" style="--tool-bg:rgba(236,72,153,0.1);--tool-fg:#ec4899;--power:92%"><span class="tool-chip-badge">WEB & API</span><span class="tool-chip-icon">🔗</span><span class="tool-chip-name">web_fetch</span><span class="tool-chip-cat">Web & API</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="WEB & API" style="--tool-bg:rgba(236,72,153,0.1);--tool-fg:#ec4899;--power:88%"><span class="tool-chip-badge">WEB & API</span><span class="tool-chip-icon">📡</span><span class="tool-chip-name">http_request</span><span class="tool-chip-cat">Web & API</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="WEB & API" style="--tool-bg:rgba(236,72,153,0.1);--tool-fg:#ec4899;--power:85%"><span class="tool-chip-badge">WEB & API</span><span class="tool-chip-icon">🧠</span><span class="tool-chip-name">smart_api_call</span><span class="tool-chip-cat">Web & API</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="WEB & API" style="--tool-bg:rgba(236,72,153,0.1);--tool-fg:#ec4899;--power:80%"><span class="tool-chip-badge">WEB & API</span><span class="tool-chip-icon">🛤️</span><span class="tool-chip-name">api_auto_route</span><span class="tool-chip-cat">Web & API</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="WEB & API" style="--tool-bg:rgba(236,72,153,0.1);--tool-fg:#ec4899;--power:75%"><span class="tool-chip-badge">WEB & API</span><span class="tool-chip-icon">🤖</span><span class="tool-chip-name">call_free_llm</span><span class="tool-chip-cat">Web & API</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="AI MODELS" style="--tool-bg:rgba(168,85,247,0.1);--tool-fg:#c084fc;--power:98%"><span class="tool-chip-badge">AI MODELS</span><span class="tool-chip-icon">👁️</span><span class="tool-chip-name">gemini_vision</span><span class="tool-chip-cat">AI Models</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="AI MODELS" style="--tool-bg:rgba(168,85,247,0.1);--tool-fg:#c084fc;--power:95%"><span class="tool-chip-badge">AI MODELS</span><span class="tool-chip-icon">🗣️</span><span class="tool-chip-name">gemini_tts</span><span class="tool-chip-cat">AI Models</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="AI MODELS" style="--tool-bg:rgba(168,85,247,0.1);--tool-fg:#c084fc;--power:85%"><span class="tool-chip-badge">AI MODELS</span><span class="tool-chip-icon">🎭</span><span class="tool-chip-name">set_persona</span><span class="tool-chip-cat">AI Models</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="AI MODELS" style="--tool-bg:rgba(168,85,247,0.1);--tool-fg:#c084fc;--power:80%"><span class="tool-chip-badge">AI MODELS</span><span class="tool-chip-icon">🔎</span><span class="tool-chip-name">search_subagents</span><span class="tool-chip-cat">AI Models</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="MEMORY" style="--tool-bg:rgba(245,158,11,0.1);--tool-fg:#f59e0b;--power:90%"><span class="tool-chip-badge">MEMORY</span><span class="tool-chip-icon">🧩</span><span class="tool-chip-name">team_memory_search</span><span class="tool-chip-cat">Memory</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="MEMORY" style="--tool-bg:rgba(245,158,11,0.1);--tool-fg:#f59e0b;--power:88%"><span class="tool-chip-badge">MEMORY</span><span class="tool-chip-icon">💾</span><span class="tool-chip-name">team_memory_save</span><span class="tool-chip-cat">Memory</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="CLOUD" style="--tool-bg:rgba(129,140,248,0.1);--tool-fg:#818cf8;--power:92%"><span class="tool-chip-badge">CLOUD</span><span class="tool-chip-icon">☁️</span><span class="tool-chip-name">tencent_cloud</span><span class="tool-chip-cat">Cloud</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="DEVOPS" style="--tool-bg:rgba(52,211,153,0.1);--tool-fg:#34d399;--power:95%"><span class="tool-chip-badge">DEVOPS</span><span class="tool-chip-icon">🌿</span><span class="tool-chip-name">git</span><span class="tool-chip-cat">DevOps</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="DEVOPS" style="--tool-bg:rgba(52,211,153,0.1);--tool-fg:#34d399;--power:90%"><span class="tool-chip-badge">DEVOPS</span><span class="tool-chip-icon">⚡</span><span class="tool-chip-name">skill_exec</span><span class="tool-chip-cat">DevOps</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="DEVOPS" style="--tool-bg:rgba(52,211,153,0.1);--tool-fg:#34d399;--power:85%"><span class="tool-chip-badge">DEVOPS</span><span class="tool-chip-icon">🎨</span><span class="tool-chip-name">ui_generate</span><span class="tool-chip-cat">DevOps</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="MEDIA" style="--tool-bg:rgba(236,72,153,0.1);--tool-fg:#ec4899;--power:98%"><span class="tool-chip-badge">MEDIA</span><span class="tool-chip-icon">🎬</span><span class="tool-chip-name">video_generate</span><span class="tool-chip-cat">Media</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="MEDIA" style="--tool-bg:rgba(236,72,153,0.1);--tool-fg:#ec4899;--power:95%"><span class="tool-chip-badge">MEDIA</span><span class="tool-chip-icon">🖼️</span><span class="tool-chip-name">image_generate</span><span class="tool-chip-cat">Media</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="MEDIA" style="--tool-bg:rgba(236,72,153,0.1);--tool-fg:#ec4899;--power:92%"><span class="tool-chip-badge">MEDIA</span><span class="tool-chip-icon">🎤</span><span class="tool-chip-name">voice_command</span><span class="tool-chip-cat">Media</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="MEDIA" style="--tool-bg:rgba(236,72,153,0.1);--tool-fg:#ec4899;--power:88%"><span class="tool-chip-badge">MEDIA</span><span class="tool-chip-icon">🎵</span><span class="tool-chip-name">audio_synthesize</span><span class="tool-chip-cat">Media</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="MEDIA" style="--tool-bg:rgba(236,72,153,0.1);--tool-fg:#ec4899;--power:85%"><span class="tool-chip-badge">MEDIA</span><span class="tool-chip-icon">🔤</span><span class="tool-chip-name">logo_generate</span><span class="tool-chip-cat">Media</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="MEDIA" style="--tool-bg:rgba(236,72,153,0.1);--tool-fg:#ec4899;--power:80%"><span class="tool-chip-badge">MEDIA</span><span class="tool-chip-icon">💎</span><span class="tool-chip-name">3d_render</span><span class="tool-chip-cat">Media</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="BLOCKCHAIN" style="--tool-bg:rgba(245,158,11,0.1);--tool-fg:#f59e0b;--power:92%"><span class="tool-chip-badge">BLOCKCHAIN</span><span class="tool-chip-icon">₿</span><span class="tool-chip-name">crypto_analyze</span><span class="tool-chip-cat">Blockchain</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="BLOCKCHAIN" style="--tool-bg:rgba(245,158,11,0.1);--tool-fg:#f59e0b;--power:88%"><span class="tool-chip-badge">BLOCKCHAIN</span><span class="tool-chip-icon">⛓️</span><span class="tool-chip-name">defi_scan</span><span class="tool-chip-cat">Blockchain</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="BLOCKCHAIN" style="--tool-bg:rgba(245,158,11,0.1);--tool-fg:#f59e0b;--power:85%"><span class="tool-chip-badge">BLOCKCHAIN</span><span class="tool-chip-icon">👛</span><span class="tool-chip-name">wallet_track</span><span class="tool-chip-cat">Blockchain</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="COMMS" style="--tool-bg:rgba(129,140,248,0.1);--tool-fg:#818cf8;--power:95%"><span class="tool-chip-badge">COMMS</span><span class="tool-chip-icon">💬</span><span class="tool-chip-name">telegram_send</span><span class="tool-chip-cat">Comms</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="COMMS" style="--tool-bg:rgba(129,140,248,0.1);--tool-fg:#818cf8;--power:92%"><span class="tool-chip-badge">COMMS</span><span class="tool-chip-icon">📱</span><span class="tool-chip-name">whatsapp_send</span><span class="tool-chip-cat">Comms</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="COMMS" style="--tool-bg:rgba(129,140,248,0.1);--tool-fg:#818cf8;--power:88%"><span class="tool-chip-badge">COMMS</span><span class="tool-chip-icon">📧</span><span class="tool-chip-name">email_send</span><span class="tool-chip-cat">Comms</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="ANALYTICS" style="--tool-bg:rgba(168,85,247,0.1);--tool-fg:#c084fc;--power:90%"><span class="tool-chip-badge">ANALYTICS</span><span class="tool-chip-icon">📈</span><span class="tool-chip-name">analytics_query</span><span class="tool-chip-cat">Analytics</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
<div class="tool-chip" data-tilt data-cat="ANALYTICS" style="--tool-bg:rgba(168,85,247,0.1);--tool-fg:#c084fc;--power:85%"><span class="tool-chip-badge">ANALYTICS</span><span class="tool-chip-icon">📉</span><span class="tool-chip-name">entity_aggregate</span><span class="tool-chip-cat">Analytics</span><div class="tool-chip-power"><div class="tool-chip-power-fill"></div></div></div>
  </div>

  <div class="tools-cta">
    <a href="/platform/" class="btn-magnetic primary" data-magnetic>Try All Tools in Studio <span class="arrow">→</span></a>
  </div>
</section>'''

content = content[:section_start] + NEW_HTML + content[section_end_idx:]

# ─── 3. Add JS for tool chip reveals, filters, and enhanced tilt ───
# Insert before the closing </script> tag
js_marker = "// ─── Parallax orbs on mouse ───"
js_idx = content.index(js_marker)

NEW_JS = '''
// ─── Tool chip staggered reveal ───
const toolObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      const chips = entry.target.querySelectorAll('.tool-chip');
      chips.forEach((chip, i) => {
        setTimeout(() => chip.classList.add('revealed'), i * 50);
      });
      toolObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.05, rootMargin: '0px 0px -50px 0px' });
const toolsGrid = document.getElementById('toolsGrid');
if (toolsGrid) toolObserver.observe(toolsGrid);

// ─── Category filter pills ───
document.querySelectorAll('.tool-filter').forEach(filter => {
  filter.addEventListener('click', () => {
    document.querySelectorAll('.tool-filter').forEach(f => f.classList.remove('active'));
    filter.classList.add('active');
    const cat = filter.dataset.cat;
    document.querySelectorAll('.tool-chip').forEach(chip => {
      if (cat === 'all' || chip.dataset.cat === cat) {
        chip.classList.remove('filtered-out');
      } else {
        chip.classList.add('filtered-out');
      }
    });
  });
});

// ─── Enhanced 3D tilt for tool chips ───
document.querySelectorAll('.tool-chip[data-tilt]').forEach(card => {
  card.addEventListener('mousemove', e => {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const cx = rect.width / 2;
    const cy = rect.height / 2;
    const rotateX = ((y - cy) / cy) * -10;
    const rotateY = ((x - cx) / cx) * 10;
    card.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-6px) scale(1.02)`;
    card.style.setProperty('--mx', `${(x / rect.width) * 100}%`);
    card.style.setProperty('--my', `${(y / rect.height) * 100}%`);
  });
  card.addEventListener('mouseleave', () => {
    card.style.transform = '';
  });
});

'''

content = content[:js_idx] + NEW_JS + content[js_idx:]

with open(FILE, "w") as f:
    f.write(content)

print("OK — tools section fully upgraded")
