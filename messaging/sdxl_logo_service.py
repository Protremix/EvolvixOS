#!/usr/bin/env python3
"""
EvolvixOS Logo Service v6 — Premium Dark Presentation
- Flux model via Pollinations
- Dark premium background matching EvolvixOS identity
- Icon as hero with natural glow (no artificial effects)
- Clean white typography on dark
- rembg AI background removal
"""
import time, io, os, asyncio, httpx, tempfile
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pydantic import BaseModel
import uvicorn

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
FONT_DIR = "/opt/evolvixos/fonts"

app = FastAPI(title="EvolvixOS Logo Service v6")

async def enhance_prompt_for_icon(brand_name, description, palette_colors):
    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": """You write image generation prompts for PROFESSIONAL LOGO ICONS for premium tech brands.
Think: NVIDIA, Discord, Spotify, Twitch — bold, glossy, premium 3D renders.
Rules:
1. ONLY the icon/symbol — NO text, NO letters, NO words.
2. Style: "glossy 3D render, premium, polished, studio lighting"
3. The icon should be a SINGLE bold shape or symbol — not a complex scene.
4. Use the brand's colors as gradients on the icon surface.
5. Material: "polished glass" or "metallic" or "glossy plastic" — pick ONE that fits.
6. Under 55 words.
7. End with: "centered, on pure white background, single icon, no text, no letters"
Output ONLY the prompt text."""},
                    {"role": "user", "content": f"Brand: {brand_name}\nConcept: {description}\nColors: {palette_colors}"}
                ],
                "temperature": 0.85,
                "max_tokens": 800
            }
        )
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        if not content or len(content) < 20:
            content = f"Premium 3D logo icon for {brand_name}: {description}. {palette_colors}. Glossy 3D render, polished, studio lighting, centered, white background, no text, no letters"
        return content

async def generate_flux_icon(prompt, seed=None):
    from urllib.parse import quote
    if seed is None:
        seed = int(time.time()) % 1000000
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"
    
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.content) > 5000:
                    img = Image.open(io.BytesIO(resp.content))
                    return img.convert("RGB")
            print(f"[LOGO] Flux attempt {attempt+1}: HTTP {resp.status_code} ({len(resp.content)} bytes)", flush=True)
        except Exception as e:
            print(f"[LOGO] Flux attempt {attempt+1} error: {e}", flush=True)
        await asyncio.sleep(3)
    raise RuntimeError("Flux API failed after 3 attempts")

class LogoRequest(BaseModel):
    brand_name: str
    description: str
    palette_colors: str = "#0066FF, #7C3AED, #00CCFF"
    tagline: str = ""

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def ai_remove_bg(img):
    from rembg import remove
    result = remove(img)
    return result.convert("RGBA")

def compose_logo(icon_img, brand_name, tagline="", palette_colors="#0066FF, #7C3AED",
                 canvas_size=(1600, 1600)):
    """Premium dark presentation — icon as hero"""
    W, H = canvas_size
    
    # Dark premium background with subtle radial gradient
    colors = [c.strip() for c in palette_colors.split(",")]
    c1 = hex_to_rgb(colors[0])
    c2 = hex_to_rgb(colors[1] if len(colors) > 1 else colors[0])
    
    # Base dark background
    canvas = Image.new("RGBA", canvas_size, (10, 10, 15, 255))
    
    # Radial gradient — subtle brand-tinted glow from center
    radial = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    radial_draw = ImageDraw.Draw(radial)
    cx, cy = W // 2, int(H * 0.30)
    max_r = int(H * 0.5)
    for r in range(max_r, 0, -2):
        alpha = int(15 * (1 - r / max_r) ** 2)
        radial_draw.ellipse([cx - r, cy - r, cx + r, cy + r], 
                           fill=(c1[0], c1[1], c1[2], alpha))
    radial = radial.filter(ImageFilter.GaussianBlur(radius=40))
    canvas = Image.alpha_composite(canvas, radial)
    
    # AI background removal
    icon = ai_remove_bg(icon_img)
    
    # Trim to content
    bbox = icon.getbbox()
    if bbox:
        pad = 20
        bbox = (max(0, bbox[0]-pad), max(0, bbox[1]-pad),
                min(icon.width, bbox[2]+pad), min(icon.height, bbox[3]+pad))
        icon = icon.crop(bbox)
    
    # Resize icon — large, it's the hero
    icon_target_h = int(H * 0.42)
    ratio = icon_target_h / icon.height
    icon_target_w = int(icon.width * ratio)
    icon_resized = icon.resize((icon_target_w, icon_target_h), Image.LANCZOS)
    
    icon_x = (W - icon_target_w) // 2
    icon_y = int(H * 0.08)
    
    # Natural glow — icon's own colors bleeding into dark background
    glow = icon_resized.copy()
    glow_data = [(r, g, b, min(a, 40)) for r, g, b, a in glow.getdata()]
    glow.putdata(glow_data)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=35))
    canvas.paste(glow, (icon_x - 10, icon_y - 10), glow)
    
    # Main icon
    canvas.paste(icon_resized, (icon_x, icon_y), icon_resized)
    
    draw = ImageDraw.Draw(canvas)
    
    # Brand name — white on dark, bold and clean
    wordmark_color = (245, 245, 250)
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
    
    # Tagline — brand gradient color, letter-spaced
    if tagline:
        tagline_font_size = int(H * 0.022)
        try:
            tagline_font = ImageFont.truetype(f"{FONT_DIR}/Poppins-Medium.ttf", tagline_font_size)
        except:
            tagline_font = ImageFont.load_default()
        
        tagline_upper = tagline.upper()
        letter_spacing = int(tagline_font_size * 0.40)
        char_widths = []
        total_w = 0
        for ch in tagline_upper:
            w = draw.textlength(ch, font=tagline_font)
            char_widths.append(w)
            total_w += w + letter_spacing
        total_w -= letter_spacing
        
        cursor_x = (W - total_w) // 2
        tagline_y = text_y + text_h + int(H * 0.02)
        
        # Gradient tagline
        for i, (ch, w) in enumerate(zip(tagline_upper, char_widths)):
            t = i / max(len(tagline_upper) - 1, 1)
            r = int(c1[0] * (1-t) + c2[0] * t)
            g = int(c1[1] * (1-t) + c2[1] * t)
            b = int(c1[2] * (1-t) + c2[2] * t)
            draw.text((cursor_x, tagline_y), ch, font=tagline_font, fill=(r, g, b, 255))
            cursor_x += w + letter_spacing
    
    return canvas

@app.post("/generate")
async def generate_logo(req: LogoRequest):
    icon_prompt = await enhance_prompt_for_icon(req.brand_name, req.description, req.palette_colors)
    print(f"[LOGO] Prompt: {icon_prompt[:120]}...", flush=True)
    
    start = time.time()
    image = await generate_flux_icon(icon_prompt)
    gen_time = time.time() - start
    print(f"[LOGO] Flux generated in {gen_time:.1f}s", flush=True)
    
    final = compose_logo(image, req.brand_name, req.tagline, req.palette_colors)
    
    fd, temp_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    final.save(temp_path, "PNG")
    
    size_kb = os.path.getsize(temp_path) // 1024
    print(f"[LOGO] Final saved ({size_kb}KB)", flush=True)
    return {"path": temp_path, "generation_time": round(gen_time, 1), "prompt": icon_prompt}

@app.get("/health")
async def health():
    return {"status": "ready", "model": "flux-v6-dark"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5003, log_level="info")
