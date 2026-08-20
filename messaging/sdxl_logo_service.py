#!/usr/bin/env python3
"""
EvolvixOS Logo Service v9 — Template-Based Premium SVG
- Pre-designed professional templates with advanced effects
- Groq picks the best template style for the brand
- Parametric customization (colors, brand letter, shapes)
- cairosvg renders at 2000x2000
- Guaranteed premium quality, no AI image generation
"""
import time, io, os, asyncio, httpx, tempfile, re, math
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import cairosvg

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
app = FastAPI(title="EvolvixOS Logo Service v9")

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_str(rgb):
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"

def lighten(rgb, amt=0.3):
    return (min(255, int(rgb[0] + (255-rgb[0])*amt)),
            min(255, int(rgb[1] + (255-rgb[1])*amt)),
            min(255, int(rgb[2] + (255-rgb[2])*amt)))

def darken(rgb, amt=0.3):
    return (int(rgb[0]*(1-amt)), int(rgb[1]*(1-amt)), int(rgb[2]*(1-amt)))

# ═══════════════════════════════════════════════════════
# PREMIUM SVG TEMPLATES
# ═══════════════════════════════════════════════════════

def template_gem(brand, tagline, c1, c2, c3, rgb1, rgb2, rgb3):
    """Hexagonal gem with glass material"""
    return f'''<svg viewBox="0 0 1200 1200" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="iconGrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="{c1}"/>
    <stop offset="40%" stop-color="{c2}"/>
    <stop offset="100%" stop-color="{c3}"/>
  </linearGradient>
  <linearGradient id="iconHighlight" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="#ffffff" stop-opacity="0.4"/>
    <stop offset="50%" stop-color="#ffffff" stop-opacity="0.1"/>
    <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="glowBg" cx="50%" cy="35%" r="35%">
    <stop offset="0%" stop-color="{c2}" stop-opacity="0.25"/>
    <stop offset="60%" stop-color="{c1}" stop-opacity="0.08"/>
    <stop offset="100%" stop-color="{c1}" stop-opacity="0"/>
  </radialGradient>
  <filter id="dropShadow" x="-30%" y="-30%" width="160%" height="160%">
    <feDropShadow dx="0" dy="12" stdDeviation="20" flood-color="{c1}" flood-opacity="0.4"/>
  </filter>
  <filter id="glassEffect" x="-10%" y="-10%" width="120%" height="120%">
    <feGaussianBlur stdDeviation="3" result="blur"/>
    <feSpecularLighting in="blur" surfaceScale="4" specularConstant="0.9" specularExponent="25" lighting-color="#ffffff" result="spec">
      <fePointLight x="600" y="150" z="300"/>
    </feSpecularLighting>
    <feComposite in="spec" in2="SourceAlpha" operator="in" result="specMask"/>
    <feComposite in="SourceGraphic" in2="specMask" operator="arithmetic" k1="0" k2="0.8" k3="1" k4="0"/>
  </filter>
</defs>
<rect width="1200" height="1200" fill="#0a0a0f"/>
<ellipse cx="600" cy="320" rx="280" ry="280" fill="url(#glowBg)"/>
<!-- Hexagonal gem -->
<g filter="url(#dropShadow)">
  <polygon points="600,120 820,247 820,500 600,627 380,500 380,247" fill="url(#iconGrad)" filter="url(#glassEffect)"/>
  <polygon points="600,120 820,247 820,500 600,627 380,500 380,247" fill="url(#iconHighlight)"/>
  <polygon points="600,120 820,247 820,500 600,627 380,500 380,247" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-opacity="0.25"/>
</g>
<!-- Inner detail lines -->
<polygon points="600,200 740,283 740,440 600,523 460,440 460,283" fill="none" stroke="#ffffff" stroke-width="1" stroke-opacity="0.15"/>
<text x="600" y="780" font-family="Poppins, Arial, sans-serif" font-size="88" font-weight="800" fill="#f5f5fa" text-anchor="middle">{brand}</text>
<text x="600" y="830" font-family="Poppins, Arial, sans-serif" font-size="26" font-weight="500" fill="{c2}" text-anchor="middle" letter-spacing="10">{tagline}</text>
</svg>'''

def template_orbit(brand, tagline, c1, c2, c3, rgb1, rgb2, rgb3):
    """Orbital rings with gradient — cosmic/premium"""
    return f'''<svg viewBox="0 0 1200 1200" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="ring1" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="{c1}"/>
    <stop offset="100%" stop-color="{c2}"/>
  </linearGradient>
  <linearGradient id="ring2" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="{c2}"/>
    <stop offset="100%" stop-color="{c3}"/>
  </linearGradient>
  <radialGradient id="core" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="{c2}" stop-opacity="0.9"/>
    <stop offset="50%" stop-color="{c1}" stop-opacity="0.5"/>
    <stop offset="100%" stop-color="{c1}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="glowBg" cx="50%" cy="35%" r="40%">
    <stop offset="0%" stop-color="{c2}" stop-opacity="0.2"/>
    <stop offset="100%" stop-color="{c1}" stop-opacity="0"/>
  </radialGradient>
  <filter id="blur1"><feGaussianBlur stdDeviation="8"/></filter>
  <filter id="dropShadow" x="-50%" y="-50%" width="200%" height="200%">
    <feDropShadow dx="0" dy="10" stdDeviation="15" flood-color="{c1}" flood-opacity="0.5"/>
  </filter>
</defs>
<rect width="1200" height="1200" fill="#0a0a0f"/>
<ellipse cx="600" cy="340" rx="300" ry="300" fill="url(#glowBg)"/>
<!-- Outer ring -->
<ellipse cx="600" cy="340" rx="250" ry="100" fill="none" stroke="url(#ring1)" stroke-width="14" filter="url(#dropShadow)" transform="rotate(-20 600 340)"/>
<!-- Inner ring -->
<ellipse cx="600" cy="340" rx="190" ry="76" fill="none" stroke="url(#ring2)" stroke-width="10" transform="rotate(30 600 340)" stroke-opacity="0.7"/>
<!-- Core -->
<circle cx="600" cy="340" r="60" fill="url(#core)"/>
<circle cx="600" cy="340" r="45" fill="{c2}" filter="url(#dropShadow)"/>
<circle cx="600" cy="325" r="15" fill="#ffffff" fill-opacity="0.4"/>
<!-- Orbit dots -->
<circle cx="840" cy="280" r="8" fill="{c3}"/>
<circle cx="370" cy="400" r="6" fill="{c1}" fill-opacity="0.8"/>
<text x="600" y="780" font-family="Poppins, Arial, sans-serif" font-size="88" font-weight="800" fill="#f5f5fa" text-anchor="middle">{brand}</text>
<text x="600" y="830" font-family="Poppins, Arial, sans-serif" font-size="26" font-weight="500" fill="{c2}" text-anchor="middle" letter-spacing="10">{tagline}</text>
</svg>'''

def template_prism(brand, tagline, c1, c2, c3, rgb1, rgb2, rgb3):
    """3D faceted prism — angular, bold, tech"""
    def facet(x, y, w, h, color, opacity=1.0):
        return f'<polygon points="{x},{y} {x+w/2},{y-h*0.3} {x+w},{y} {x+w/2},{y+h*0.3}" fill="{color}" fill-opacity="{opacity}"/>'
    
    return f'''<svg viewBox="0 0 1200 1200" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="prismGrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="{c1}"/>
    <stop offset="50%" stop-color="{c2}"/>
    <stop offset="100%" stop-color="{c3}"/>
  </linearGradient>
  <linearGradient id="prismLight" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/>
    <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="glowBg" cx="50%" cy="35%" r="35%">
    <stop offset="0%" stop-color="{c2}" stop-opacity="0.2"/>
    <stop offset="100%" stop-color="{c1}" stop-opacity="0"/>
  </radialGradient>
  <filter id="dropShadow" x="-30%" y="-30%" width="160%" height="160%">
    <feDropShadow dx="0" dy="14" stdDeviation="22" flood-color="{c1}" flood-opacity="0.4"/>
  </filter>
  <filter id="glassEffect" x="-10%" y="-10%" width="120%" height="120%">
    <feGaussianBlur stdDeviation="2" result="blur"/>
    <feSpecularLighting in="blur" surfaceScale="5" specularConstant="0.8" specularExponent="30" lighting-color="#ffffff" result="spec">
      <fePointLight x="600" y="100" z="350"/>
    </feSpecularLighting>
    <feComposite in="spec" in2="SourceAlpha" operator="in" result="specMask"/>
    <feComposite in="SourceGraphic" in2="specMask" operator="arithmetic" k1="0" k2="0.7" k3="1.2" k4="0"/>
  </filter>
</defs>
<rect width="1200" height="1200" fill="#0a0a0f"/>
<ellipse cx="600" cy="350" rx="320" ry="320" fill="url(#glowBg)"/>
<!-- Main prism shape -->
<g filter="url(#dropShadow)">
  <polygon points="600,100 850,280 750,560 450,560 350,280" fill="url(#prismGrad)" filter="url(#glassEffect)"/>
  <polygon points="600,100 850,280 750,560 450,560 350,280" fill="url(#prismLight)"/>
</g>
<!-- Facet lines -->
<polygon points="600,100 850,280 750,560 450,560 350,280" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-opacity="0.2"/>
<line x1="600" y1="100" x2="600" y2="560" stroke="#ffffff" stroke-width="1" stroke-opacity="0.15"/>
<line x1="350" y1="280" x2="850" y2="280" stroke="#ffffff" stroke-width="1" stroke-opacity="0.1"/>
<!-- Inner prism -->
<polygon points="600,200 770,310 700,480 500,480 430,310" fill="none" stroke="{c3}" stroke-width="2" stroke-opacity="0.3"/>
<text x="600" y="780" font-family="Poppins, Arial, sans-serif" font-size="88" font-weight="800" fill="#f5f5fa" text-anchor="middle">{brand}</text>
<text x="600" y="830" font-family="Poppins, Arial, sans-serif" font-size="26" font-weight="500" fill="{c2}" text-anchor="middle" letter-spacing="10">{tagline}</text>
</svg>'''

def template_monogram(brand, tagline, c1, c2, c3, rgb1, rgb2, rgb3):
    """Bold letter monogram with gradient and glass"""
    letter = brand[0].upper() if brand else "E"
    
    return f'''<svg viewBox="0 0 1200 1200" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="letterGrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="{c1}"/>
    <stop offset="50%" stop-color="{c2}"/>
    <stop offset="100%" stop-color="{c3}"/>
  </linearGradient>
  <linearGradient id="letterShine" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="#ffffff" stop-opacity="0.5"/>
    <stop offset="50%" stop-color="#ffffff" stop-opacity="0.1"/>
    <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="glowBg" cx="50%" cy="35%" r="35%">
    <stop offset="0%" stop-color="{c2}" stop-opacity="0.3"/>
    <stop offset="100%" stop-color="{c1}" stop-opacity="0"/>
  </radialGradient>
  <filter id="dropShadow" x="-30%" y="-30%" width="160%" height="160%">
    <feDropShadow dx="0" dy="12" stdDeviation="20" flood-color="{c1}" flood-opacity="0.45"/>
  </filter>
  <filter id="glassEffect" x="-10%" y="-10%" width="120%" height="120%">
    <feGaussianBlur stdDeviation="3" result="blur"/>
    <feSpecularLighting in="blur" surfaceScale="4" specularConstant="0.9" specularExponent="25" lighting-color="#ffffff" result="spec">
      <fePointLight x="600" y="150" z="300"/>
    </feSpecularLighting>
    <feComposite in="spec" in2="SourceAlpha" operator="in" result="specMask"/>
    <feComposite in="SourceGraphic" in2="specMask" operator="arithmetic" k1="0" k2="0.8" k3="1" k4="0"/>
  </filter>
</defs>
<rect width="1200" height="1200" fill="#0a0a0f"/>
<ellipse cx="600" cy="320" rx="280" ry="280" fill="url(#glowBg)"/>
<!-- Circle background -->
<circle cx="600" cy="340" r="240" fill="{c1}" fill-opacity="0.08"/>
<circle cx="600" cy="340" r="240" fill="none" stroke="{c2}" stroke-width="2" stroke-opacity="0.2"/>
<!-- Letter -->
<g filter="url(#dropShadow)">
  <text x="600" y="450" font-family="Poppins, Arial, sans-serif" font-size="380" font-weight="900" fill="url(#letterGrad)" text-anchor="middle" filter="url(#glassEffect)">{letter}</text>
</g>
<text x="600" y="450" font-family="Poppins, Arial, sans-serif" font-size="380" font-weight="900" fill="url(#letterShine)" text-anchor="middle">{letter}</text>
<text x="600" y="780" font-family="Poppins, Arial, sans-serif" font-size="88" font-weight="800" fill="#f5f5fa" text-anchor="middle">{brand}</text>
<text x="600" y="830" font-family="Poppins, Arial, sans-serif" font-size="26" font-weight="500" fill="{c2}" text-anchor="middle" letter-spacing="10">{tagline}</text>
</svg>'''

def template_wave(brand, tagline, c1, c2, c3, rgb1, rgb2, rgb3):
    """Flowing gradient wave/ribbon — organic, modern"""
    return f'''<svg viewBox="0 0 1200 1200" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="waveGrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="{c1}"/>
    <stop offset="50%" stop-color="{c2}"/>
    <stop offset="100%" stop-color="{c3}"/>
  </linearGradient>
  <linearGradient id="waveGrad2" x1="100%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="{c3}"/>
    <stop offset="100%" stop-color="{c1}"/>
  </linearGradient>
  <radialGradient id="glowBg" cx="50%" cy="35%" r="35%">
    <stop offset="0%" stop-color="{c2}" stop-opacity="0.25"/>
    <stop offset="100%" stop-color="{c1}" stop-opacity="0"/>
  </radialGradient>
  <filter id="dropShadow" x="-30%" y="-30%" width="160%" height="160%">
    <feDropShadow dx="0" dy="10" stdDeviation="18" flood-color="{c1}" flood-opacity="0.4"/>
  </filter>
  <filter id="glassEffect" x="-10%" y="-10%" width="120%" height="120%">
    <feGaussianBlur stdDeviation="2" result="blur"/>
    <feSpecularLighting in="blur" surfaceScale="3" specularConstant="0.8" specularExponent="20" lighting-color="#ffffff" result="spec">
      <fePointLight x="600" y="100" z="250"/>
    </feSpecularLighting>
    <feComposite in="spec" in2="SourceAlpha" operator="in" result="specMask"/>
    <feComposite in="SourceGraphic" in2="specMask" operator="arithmetic" k1="0" k2="0.7" k3="1" k4="0"/>
  </filter>
</defs>
<rect width="1200" height="1200" fill="#0a0a0f"/>
<ellipse cx="600" cy="340" rx="300" ry="300" fill="url(#glowBg)"/>
<!-- Flowing wave ribbon -->
<g filter="url(#dropShadow)">
  <path d="M 350,200 C 350,200 500,150 600,250 C 700,350 850,300 850,300 C 850,400 700,450 600,400 C 500,350 350,400 350,400 C 350,300 350,200 350,200 Z" 
        fill="url(#waveGrad)" filter="url(#glassEffect)"/>
  <path d="M 420,280 C 420,280 550,230 620,310 C 690,390 780,350 780,350 C 780,350 720,380 630,340 C 540,300 420,330 420,330 Z" 
        fill="url(#waveGrad2)" fill-opacity="0.5"/>
</g>
<!-- Highlight -->
<path d="M 350,200 C 350,200 500,150 600,250 C 700,350 850,300 850,300" 
      fill="none" stroke="#ffffff" stroke-width="2" stroke-opacity="0.4"/>
<text x="600" y="780" font-family="Poppins, Arial, sans-serif" font-size="88" font-weight="800" fill="#f5f5fa" text-anchor="middle">{brand}</text>
<text x="600" y="830" font-family="Poppins, Arial, sans-serif" font-size="26" font-weight="500" fill="{c2}" text-anchor="middle" letter-spacing="10">{tagline}</text>
</svg>'''

def template_shield(brand, tagline, c1, c2, c3, rgb1, rgb2, rgb3):
    """Premium shield/badge — trust, security, authority"""
    return f'''<svg viewBox="0 0 1200 1200" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="{c1}"/>
    <stop offset="50%" stop-color="{c2}"/>
    <stop offset="100%" stop-color="{c3}"/>
  </linearGradient>
  <linearGradient id="shieldLight" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/>
    <stop offset="60%" stop-color="#ffffff" stop-opacity="0.05"/>
    <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="glowBg" cx="50%" cy="35%" r="35%">
    <stop offset="0%" stop-color="{c2}" stop-opacity="0.25"/>
    <stop offset="100%" stop-color="{c1}" stop-opacity="0"/>
  </radialGradient>
  <filter id="dropShadow" x="-30%" y="-30%" width="160%" height="160%">
    <feDropShadow dx="0" dy="14" stdDeviation="22" flood-color="{c1}" flood-opacity="0.4"/>
  </filter>
  <filter id="glassEffect" x="-10%" y="-10%" width="120%" height="120%">
    <feGaussianBlur stdDeviation="3" result="blur"/>
    <feSpecularLighting in="blur" surfaceScale="5" specularConstant="0.9" specularExponent="25" lighting-color="#ffffff" result="spec">
      <fePointLight x="600" y="120" z="300"/>
    </feSpecularLighting>
    <feComposite in="spec" in2="SourceAlpha" operator="in" result="specMask"/>
    <feComposite in="SourceGraphic" in2="specMask" operator="arithmetic" k1="0" k2="0.8" k3="1" k4="0"/>
  </filter>
</defs>
<rect width="1200" height="1200" fill="#0a0a0f"/>
<ellipse cx="600" cy="340" rx="280" ry="280" fill="url(#glowBg)"/>
<!-- Shield -->
<g filter="url(#dropShadow)">
  <path d="M 600,100 L 820,180 L 820,400 C 820,520 720,600 600,640 C 480,600 380,520 380,400 L 380,180 Z" 
        fill="url(#shieldGrad)" filter="url(#glassEffect)"/>
  <path d="M 600,100 L 820,180 L 820,400 C 820,520 720,600 600,640 C 480,600 380,520 380,400 L 380,180 Z" 
        fill="url(#shieldLight)"/>
</g>
<!-- Inner shield border -->
<path d="M 600,140 L 780,200 L 780,400 C 780,490 700,560 600,590 C 500,560 420,490 420,400 L 420,200 Z" 
      fill="none" stroke="#ffffff" stroke-width="2" stroke-opacity="0.2"/>
<!-- Center emblem -->
<circle cx="600" cy="370" r="50" fill="none" stroke="#ffffff" stroke-width="3" stroke-opacity="0.4"/>
<circle cx="600" cy="370" r="20" fill="#ffffff" fill-opacity="0.3"/>
<text x="600" y="780" font-family="Poppins, Arial, sans-serif" font-size="88" font-weight="800" fill="#f5f5fa" text-anchor="middle">{brand}</text>
<text x="600" y="830" font-family="Poppins, Arial, sans-serif" font-size="26" font-weight="500" fill="{c2}" text-anchor="middle" letter-spacing="10">{tagline}</text>
</svg>'''

def template_cube(brand, tagline, c1, c2, c3, rgb1, rgb2, rgb3):
    """3D isometric cube — bold, modern, tech"""
    return f'''<svg viewBox="0 0 1200 1200" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="topFace" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="{rgb_str(lighten(rgb1, 0.3))}"/>
    <stop offset="100%" stop-color="{c1}"/>
  </linearGradient>
  <linearGradient id="leftFace" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="{c2}"/>
    <stop offset="100%" stop-color="{rgb_str(darken(rgb2, 0.3))}"/>
  </linearGradient>
  <linearGradient id="rightFace" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="{c3}"/>
    <stop offset="100%" stop-color="{rgb_str(darken(rgb3, 0.3))}"/>
  </linearGradient>
  <radialGradient id="glowBg" cx="50%" cy="35%" r="35%">
    <stop offset="0%" stop-color="{c2}" stop-opacity="0.25"/>
    <stop offset="100%" stop-color="{c1}" stop-opacity="0"/>
  </radialGradient>
  <filter id="dropShadow" x="-30%" y="-30%" width="160%" height="160%">
    <feDropShadow dx="0" dy="12" stdDeviation="20" flood-color="{c1}" flood-opacity="0.4"/>
  </filter>
</defs>
<rect width="1200" height="1200" fill="#0a0a0f"/>
<ellipse cx="600" cy="340" rx="300" ry="300" fill="url(#glowBg)"/>
<g filter="url(#dropShadow)">
  <!-- Top face -->
  <polygon points="600,100 820,230 600,360 380,230" fill="url(#topFace)"/>
  <!-- Left face -->
  <polygon points="380,230 600,360 600,580 380,450" fill="url(#leftFace)"/>
  <!-- Right face -->
  <polygon points="820,230 600,360 600,580 820,450" fill="url(#rightFace)"/>
</g>
<!-- Edge highlights -->
<polygon points="600,100 820,230 600,360 380,230" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-opacity="0.3"/>
<line x1="600" y1="360" x2="600" y2="580" stroke="#ffffff" stroke-width="1" stroke-opacity="0.15"/>
<!-- Inner cube lines -->
<polygon points="600,160 760,240 600,320 440,240" fill="none" stroke="#ffffff" stroke-width="1" stroke-opacity="0.15"/>
<text x="600" y="780" font-family="Poppins, Arial, sans-serif" font-size="88" font-weight="800" fill="#f5f5fa" text-anchor="middle">{brand}</text>
<text x="600" y="830" font-family="Poppins, Arial, sans-serif" font-size="26" font-weight="500" fill="{c2}" text-anchor="middle" letter-spacing="10">{tagline}</text>
</svg>'''

TEMPLATES = {
    "gem": ("Hexagonal gem with glass material", template_gem),
    "orbit": ("Orbital rings, cosmic premium", template_orbit),
    "prism": ("3D faceted prism, angular tech", template_prism),
    "monogram": ("Bold letter monogram with glass", template_monogram),
    "wave": ("Flowing gradient ribbon, organic", template_wave),
    "shield": ("Premium shield/badge, authority", template_shield),
    "cube": ("3D isometric cube, bold tech", template_cube),
}

async def select_template(brand_name, description):
    """Let Groq pick the best template style for the brand"""
    template_list = "\n".join([f"- {k}: {v[0]}" for k, v in TEMPLATES.items()])
    
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": f"You pick the best logo template for a brand. Available templates:\n{template_list}\n\nRespond with ONLY the template name (one of: gem, orbit, prism, monogram, wave, shield, cube). No other text."},
                    {"role": "user", "content": f"Brand: {brand_name}\nDescription: {description}\n\nWhich template fits best?"}
                ],
                "temperature": 0.3,
                "max_tokens": 20
            }
        )
        data = resp.json()
        choice = data["choices"][0]["message"]["content"].strip().lower()
        for k in TEMPLATES:
            if k in choice:
                return k
        return "gem"  # default

class LogoRequest(BaseModel):
    brand_name: str
    description: str = ""
    palette_colors: str = "#0066FF, #7C3AED, #00CCFF"
    tagline: str = ""
    template: str = ""

@app.post("/generate")
async def generate_logo(req: LogoRequest):
    start = time.time()
    
    colors = [c.strip() for c in req.palette_colors.split(",")]
    c1 = colors[0] if len(colors) > 0 else "#0066FF"
    c2 = colors[1] if len(colors) > 1 else c1
    c3 = colors[2] if len(colors) > 2 else c2
    rgb1 = hex_to_rgb(c1)
    rgb2 = hex_to_rgb(c2)
    rgb3 = hex_to_rgb(c3)
    
    # Pick best template
    template_key = req.template if req.template and req.template in TEMPLATES else await select_template(req.brand_name, req.description)
    template_func = TEMPLATES[template_key][1]
    print(f"[LOGO] Template: {template_key}", flush=True)
    
    # Generate SVG from template
    tagline_upper = req.tagline.upper() if req.tagline else ""
    svg_code = template_func(req.brand_name, tagline_upper, c1, c2, c3, rgb1, rgb2, rgb3)
    
    print(f"[LOGO] SVG generated ({len(svg_code)} chars)", flush=True)
    
    try:
        # Render at 2000x2000
        png_data = cairosvg.svg2png(
            bytestring=svg_code.encode('utf-8'),
            output_width=2000,
            output_height=2000,
            background_color="#0a0a0f"
        )
        
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        with open(temp_path, 'wb') as f:
            f.write(png_data)
        
        gen_time = time.time() - start
        size_kb = os.path.getsize(temp_path) // 1024
        print(f"[LOGO] Rendered in {gen_time:.1f}s, {size_kb}KB, template={template_key}", flush=True)
        
        return {"path": temp_path, "generation_time": round(gen_time, 1), 
                "method": f"template-{template_key}", "size_kb": size_kb}
    
    except Exception as e:
        print(f"[LOGO] Render error: {e}", flush=True)
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    return {"status": "ready", "model": "template-v9", "templates": list(TEMPLATES.keys())}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5003, log_level="info")
