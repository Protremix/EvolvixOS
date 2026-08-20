#!/usr/bin/env python3
"""
EvolvixOS Logo Service v7 — SVG Vector Design
- Groq designs the logo as SVG code (clean vector graphics)
- cairosvg renders to PNG at 1600x1600
- No AI image generation — precise, professional, crisp
- Dark premium presentation
"""
import time, io, os, asyncio, httpx, tempfile, re
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pydantic import BaseModel
import uvicorn
import cairosvg

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
FONT_DIR = "/opt/evolvixos/fonts"

app = FastAPI(title="EvolvixOS Logo Service v7")

async def generate_svg_icon(brand_name, description, palette_colors):
    """Have Groq design a professional logo icon as SVG code"""
    colors = [c.strip() for c in palette_colors.split(",")]
    
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": f"""You are a professional logo designer. You design logo icons as SVG code.

DESIGN PRINCIPLES:
- SIMPLE: 1-3 shapes maximum. Think Nike swoosh, Apple apple, Twitter bird.
- BOLD: Thick strokes, solid fills, strong silhouette
- SYMMETRIC: Perfect geometric balance
- SCALABLE: Must look good at 32px and 3200px
- MEMORABLE: Unique, not generic

TECHNICAL RULES:
- SVG viewBox: "0 0 512 512"
- Use ONLY these colors: {colors}
- Use <defs> for gradients (linearGradient, radialGradient)
- Use geometric shapes: <path>, <circle>, <rect>, <polygon>, <line>
- NO <text>, NO <tspan> — icon only
- NO <image>, NO <filter> with complex effects
- Simple <filter> for subtle drop shadow is OK
- Center the icon in the viewBox
- Make it LARGE — fill 70-80% of the viewBox
- Use smooth curves with bezier paths where appropriate
- For gradients, use stops with the brand colors

OUTPUT: Return ONLY valid SVG code, starting with <svg and ending with </svg>. No explanation, no markdown."""},
                    {"role": "user", "content": f"Design a logo icon for: {brand_name}\nConcept: {description}\nColors: {colors}\nMake it bold, simple, and professional."}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        # Extract SVG from response
        svg_match = re.search(r'<svg.*?</svg>', content, re.DOTALL)
        if svg_match:
            return svg_match.group(0)
        # If no match, try wrapping
        if '<svg' in content:
            return content
        return None

async def generate_svg_logo_full(brand_name, description, palette_colors, tagline=""):
    """Have Groq design the ENTIRE logo (icon + text) as SVG"""
    colors = [c.strip() for c in palette_colors.split(",")]
    c1 = colors[0] if len(colors) > 0 else "#0066FF"
    c2 = colors[1] if len(colors) > 1 else c1
    c3 = colors[2] if len(colors) > 2 else c2
    
    tagline_text = tagline.upper() if tagline else ""
    
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": f"""You are a world-class logo designer. You create complete logos as SVG code.

The logo has TWO parts:
1. ICON: A bold, simple, geometric symbol — 1-3 shapes max
2. WORDMARK: The brand name in clean, bold text below the icon
3. TAGLINE: A small spaced tagline below the wordmark (if provided)

DESIGN REFERENCES: Stripe, Airbnb, NVIDIA, Discord, Notion
- Clean, minimal, professional
- Strong geometric forms
- Perfect alignment and spacing
- Brand colors used as gradient fills

TECHNICAL SPECIFICATIONS:
- SVG viewBox: "0 0 1200 1200"
- Background: Dark (#0a0a0f)
- Icon: Centered horizontally, top 45% of canvas, fill 70-80% of that space
- Brand name: Below icon, centered, font-size 80-90, font-weight 800, fill #f5f5fa
- Tagline: Below brand name, centered, font-size 24-28, letter-spacing 8-12px, fill with brand gradient color
- Use <defs> for gradients:
  - Icon gradient using {c1}, {c2}, {c3}
  - Tagline gradient using {c1}, {c2}
- Use <text> with font-family="Arial, sans-serif" font-weight="800"
- Use smooth bezier curves for organic shapes
- Use precise geometry for geometric shapes
- Add subtle inner glow on icon using <filter> with feGaussianBlur if appropriate

COLORS TO USE:
- Primary: {c1}
- Secondary: {c2}  
- Accent: {c3}
- Background: #0a0a0f
- Text: #f5f5fa

OUTPUT: Return ONLY valid SVG code starting with <svg and ending with </svg>. No explanation, no markdown, no code blocks."""},
                    {"role": "user", "content": f"Brand: {brand_name}\nConcept: {description}\nTagline: {tagline_text}\n\nDesign a complete professional logo. Icon on top, brand name below, tagline at bottom. Dark background. Use brand colors as gradient on the icon."}
                ],
                "temperature": 0.7,
                "max_tokens": 3000
            }
        )
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        # Extract SVG
        svg_match = re.search(r'<svg.*?</svg>', content, re.DOTALL)
        if svg_match:
            return svg_match.group(0)
        if '<svg' in content:
            # Remove markdown code blocks if present
            content = re.sub(r'```[a-z]*\n?', '', content)
            content = re.sub(r'```', '', content)
            return content.strip()
        return None

class LogoRequest(BaseModel):
    brand_name: str
    description: str
    palette_colors: str = "#0066FF, #7C3AED, #00CCFF"
    tagline: str = ""

@app.post("/generate")
async def generate_logo(req: LogoRequest):
    start = time.time()
    
    # Generate full logo as SVG
    svg_code = await generate_svg_logo_full(req.brand_name, req.description, req.palette_colors, req.tagline)
    
    if not svg_code:
        return JSONResponse({"error": "Failed to generate SVG"}, status_code=500)
    
    print(f"[LOGO] SVG generated ({len(svg_code)} chars)", flush=True)
    
    # Fix font references — use system fonts
    svg_code = svg_code.replace('font-family="Arial, sans-serif"', 'font-family="Poppins, Arial, sans-serif"')
    svg_code = svg_code.replace('font-family="Arial"', 'font-family="Poppins, Arial, sans-serif"')
    svg_code = svg_code.replace("font-family='Arial'", "font-family='Poppins, Arial, sans-serif'")
    
    # Ensure viewBox exists
    if 'viewBox' not in svg_code:
        svg_code = svg_code.replace('<svg', '<svg viewBox="0 0 1200 1200"')
    
    try:
        # Render SVG to PNG at 1600x1600
        png_data = cairosvg.svg2png(
            bytestring=svg_code.encode('utf-8'),
            output_width=1600,
            output_height=1600,
            background_color="#0a0a0f"
        )
        
        # Save
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        with open(temp_path, 'wb') as f:
            f.write(png_data)
        
        gen_time = time.time() - start
        size_kb = os.path.getsize(temp_path) // 1024
        print(f"[LOGO] Rendered in {gen_time:.1f}s, {size_kb}KB", flush=True)
        
        return {"path": temp_path, "generation_time": round(gen_time, 1), "method": "svg-vector"}
    
    except Exception as e:
        print(f"[LOGO] Render error: {e}", flush=True)
        # Save SVG for debugging
        fd, svg_path = tempfile.mkstemp(suffix=".svg")
        os.close(fd)
        with open(svg_path, 'w') as f:
            f.write(svg_code)
        return JSONResponse({"error": f"Render failed: {str(e)}", "svg_path": svg_path}, status_code=500)

@app.get("/health")
async def health():
    return {"status": "ready", "model": "svg-vector-v7"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5003, log_level="info")
