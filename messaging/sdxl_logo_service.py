#!/usr/bin/env python3
"""
EvolvixOS Logo Service v4 — Professional Quality
- Flux model via Pollinations for state-of-the-art icon quality
- rembg for AI background removal
- Clean minimal composition: solid typography, no cheesy effects
- Professional card layout
"""
import time, io, os, re, asyncio, httpx, tempfile, hashlib
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pydantic import BaseModel
import uvicorn

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
FONT_DIR = "/opt/evolvixos/fonts"

app = FastAPI(title="EvolvixOS Logo Service v4")

async def enhance_prompt_for_icon(brand_name, description, palette_colors):
    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": """You write image generation prompts for PROFESSIONAL LOGO ICONS for tech companies.
Style references: Apple, Stripe, Airbnb, Discord — simple, bold, geometric, memorable.
Rules:
1. Generate ONLY the icon/symbol — NO text, NO letters, NO words.
2. Describe shape, form, colors, material, lighting in vivid detail.
3. Use words like: "minimalist, bold, geometric, clean lines, professional, premium, app icon style"
4. Specify material finish: "glossy 3D render" or "flat vector" based on brand feel.
5. Keep under 65 words.
6. End with: "centered, white background, no text, no letters, icon only"
Output ONLY the prompt text."""},
                    {"role": "user", "content": f"Brand: {brand_name}\nConcept: {description}\nColors: {palette_colors}"}
                ],
                "temperature": 0.9,
                "max_tokens": 1000
            }
        )
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        if not content or len(content) < 20:
            content = f"Minimalist logo icon for {brand_name}: {description}. {palette_colors}. Bold, geometric, clean lines, professional, premium, glossy 3D render, centered, white background, no text, no letters, icon only"
        return content

async def generate_flux_icon(prompt, seed=None):
    """Generate icon using Flux via Pollinations — much higher quality than SDXL Turbo"""
    if seed is None:
        seed = int(time.time()) % 1000000
    
    # Use Flux model with enhanced prompt
    flux_prompt = f"{prompt}, high quality, detailed, professional, 4k"
    encoded = httpx.URL(flux_prompt).path
    url = f"https://image.pollinations.ai/prompt/{httpx.URL(flux_prompt, path='').__str__() if False else flux_prompt.replace(' ', '%20')}?width=1024&height=1024&seed={seed}&model=flux&nologo=true&nsfprompt=true"
    
    # Actually use proper URL encoding
    from urllib.parse import quote
    url = f"https://image.pollinations.ai/prompt/{quote(flux_prompt)}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"
    
    async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code == 200 and len(resp.content) > 5000:
            img = Image.open(io.BytesIO(resp.content))
            return img.convert("RGB")
        raise RuntimeError(f"Flux API returned {resp.status_code} ({len(resp.content)} bytes)")

class LogoRequest(BaseModel):
    brand_name: str
    description: str
    palette_colors: str = "#0066FF, #7C3AED, #00CCFF"
    tagline: str = ""

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def ai_remove_bg(img):
    """AI background removal using rembg"""
    from rembg import remove
    result = remove(img)
    return result.convert("RGBA")

def compose_logo(icon_img, brand_name, tagline="", palette_colors="#0066FF, #7C3AED",
                 canvas_size=(1600, 1600)):
    """Professional composition: clean, minimal, no cheesy effects"""
    W, H = canvas_size
    canvas = Image.new("RGBA", canvas_size, (255, 255, 255, 255))  # White background
    
    # AI background removal
    icon = ai_remove_bg(icon_img)
    
    # Trim to content
    bbox = icon.getbbox()
    if bbox:
        pad = 15
        bbox = (max(0, bbox[0]-pad), max(0, bbox[1]-pad),
                min(icon.width, bbox[2]+pad), min(icon.height, bbox[3]+pad))
        icon = icon.crop(bbox)
    
    # Resize icon to fit — make it large and prominent
    icon_target_h = int(H * 0.42)
    ratio = icon_target_h / icon.height
    icon_target_w = int(icon.width * ratio)
    icon_resized = icon.resize((icon_target_w, icon_target_h), Image.LANCZOS)
    
    icon_x = (W - icon_target_w) // 2
    icon_y = int(H * 0.08)
    
    # Clean, subtle drop shadow (not cheesy glow)
    shadow = Image.new("RGBA", (icon_target_w + 40, icon_target_h + 40), (0, 0, 0, 0))
    shadow_alpha = Image.new("L", (icon_target_w + 40, icon_target_h + 40), 0)
    shadow_icon = icon_resized.copy()
    shadow_data = [(0, 0, 0, min(a, 35)) for r, g, b, a in shadow_icon.getdata()]
    shadow_icon.putdata(shadow_data)
    shadow.paste(shadow_icon, (20, 20), shadow_icon)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=12))
    canvas.paste(shadow, (icon_x - 20, icon_y - 10), shadow)
    
    # Main icon
    canvas.paste(icon_resized, (icon_x, icon_y), icon_resized)
    
    # Typography — SOLID color, no gradients
    colors = [c.strip() for c in palette_colors.split(",")]
    c1 = hex_to_rgb(colors[0])
    c2 = hex_to_rgb(colors[1] if len(colors) > 1 else colors[0])
    
    draw = ImageDraw.Draw(canvas)
    
    # Brand name — solid dark color for professionalism
    wordmark_color = (30, 30, 35)  # Near-black, not gradient
    wordmark_font_size = int(H * 0.075)
    try:
        wordmark_font = ImageFont.truetype(f"{FONT_DIR}/Poppins-ExtraBold.ttf", wordmark_font_size)
    except:
        wordmark_font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), brand_name, font=wordmark_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (W - text_w) // 2
    text_y = icon_y + icon_target_h + int(H * 0.03)
    
    draw.text((text_x, text_y), brand_name, font=wordmark_font, fill=wordmark_color)
    
    # Tagline — solid brand color, letter-spaced
    if tagline:
        tagline_font_size = int(H * 0.024)
        try:
            tagline_font = ImageFont.truetype(f"{FONT_DIR}/Poppins-Medium.ttf", tagline_font_size)
        except:
            tagline_font = ImageFont.load_default()
        
        tagline_upper = tagline.upper()
        letter_spacing = int(tagline_font_size * 0.35)
        char_widths = []
        total_w = 0
        for ch in tagline_upper:
            w = draw.textlength(ch, font=tagline_font)
            char_widths.append(w)
            total_w += w + letter_spacing
        total_w -= letter_spacing
        
        cursor_x = (W - total_w) // 2
        tagline_y = text_y + text_h + int(H * 0.02)
        tagline_color = (*c1, 200)  # Solid brand color, slightly transparent
        
        for ch, w in zip(tagline_upper, char_widths):
            draw.text((cursor_x, tagline_y), ch, font=tagline_font, fill=tagline_color)
            cursor_x += w + letter_spacing
    
    return canvas

@app.post("/generate")
async def generate_logo(req: LogoRequest):
    # Enhance prompt
    icon_prompt = await enhance_prompt_for_icon(req.brand_name, req.description, req.palette_colors)
    print(f"[LOGO] Prompt: {icon_prompt[:120]}...", flush=True)
    
    # Generate icon with Flux
    start = time.time()
    image = await generate_flux_icon(icon_prompt)
    gen_time = time.time() - start
    print(f"[LOGO] Flux generated in {gen_time:.1f}s", flush=True)
    
    # Composite
    final = compose_logo(image, req.brand_name, req.tagline, req.palette_colors)
    
    # Save
    fd, temp_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    final.save(temp_path, "PNG")
    
    size_kb = os.path.getsize(temp_path) // 1024
    print(f"[LOGO] Final saved ({size_kb}KB)", flush=True)
    return {"path": temp_path, "generation_time": round(gen_time, 1), "prompt": icon_prompt}

@app.get("/health")
async def health():
    return {"status": "ready", "model": "flux-via-pollinations"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5003, log_level="info")
