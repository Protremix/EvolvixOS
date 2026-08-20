#!/usr/bin/env python3
"""
EvolvixOS Logo Service v5 — Professional Grade
- Flux model via Pollinations (single request, reliable)
- Improved prompt: flat vector / minimal 3D, bold and simple
- Clean composition: white bg, solid typography, subtle shadow
- rembg AI background removal
"""
import time, io, os, asyncio, httpx, tempfile
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pydantic import BaseModel
import uvicorn

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
FONT_DIR = "/opt/evolvixos/fonts"

app = FastAPI(title="EvolvixOS Logo Service v5")

async def enhance_prompt_for_icon(brand_name, description, palette_colors):
    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": """You write image generation prompts for PROFESSIONAL LOGO ICONS.
Style references: Stripe, Airbnb, Discord, Notion — simple, bold, memorable.
Rules:
1. ONLY the icon — NO text, NO letters, NO words.
2. Pick ONE style: "flat vector design" OR "minimal 3D render".
3. Keep it BOLD and SIMPLE — max 2-3 visual elements.
4. Describe shape precisely, colors, finish.
5. Under 60 words.
6. End with: "centered composition, plain white background, app icon style, no text, no letters"
Output ONLY the prompt text."""},
                    {"role": "user", "content": f"Brand: {brand_name}\nConcept: {description}\nColors: {palette_colors}"}
                ],
                "temperature": 0.9,
                "max_tokens": 800
            }
        )
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        if not content or len(content) < 20:
            content = f"Minimalist logo icon for {brand_name}: {description}. {palette_colors}. Bold, simple, geometric, flat vector design, centered, white background, app icon style, no text, no letters"
        return content

async def generate_flux_icon(prompt, seed=None):
    """Generate icon using Flux via Pollinations"""
    from urllib.parse import quote
    if seed is None:
        seed = int(time.time()) % 1000000
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"
    
    # Retry up to 3 times
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.content) > 5000:
                    img = Image.open(io.BytesIO(resp.content))
                    return img.convert("RGB")
            print(f"[LOGO] Flux attempt {attempt+1} returned {resp.status_code} ({len(resp.content)} bytes)", flush=True)
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
    """Professional composition — clean, balanced, minimal"""
    W, H = canvas_size
    canvas = Image.new("RGBA", canvas_size, (255, 255, 255, 255))
    
    # AI background removal
    icon = ai_remove_bg(icon_img)
    
    # Trim to content
    bbox = icon.getbbox()
    if bbox:
        pad = 20
        bbox = (max(0, bbox[0]-pad), max(0, bbox[1]-pad),
                min(icon.width, bbox[2]+pad), min(icon.height, bbox[3]+pad))
        icon = icon.crop(bbox)
    
    # Resize icon — prominent but balanced
    icon_target_h = int(H * 0.40)
    ratio = icon_target_h / icon.height
    icon_target_w = int(icon.width * ratio)
    icon_resized = icon.resize((icon_target_w, icon_target_h), Image.LANCZOS)
    
    icon_x = (W - icon_target_w) // 2
    icon_y = int(H * 0.10)
    
    # Subtle drop shadow
    shadow = Image.new("RGBA", (icon_target_w + 60, icon_target_h + 60), (0, 0, 0, 0))
    shadow_icon = icon_resized.copy()
    shadow_data = [(0, 0, 0, min(a, 30)) for r, g, b, a in shadow_icon.getdata()]
    shadow_icon.putdata(shadow_data)
    shadow.paste(shadow_icon, (30, 30), shadow_icon)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=15))
    canvas.paste(shadow, (icon_x - 30, icon_y - 15), shadow)
    
    # Main icon
    canvas.paste(icon_resized, (icon_x, icon_y), icon_resized)
    
    # Typography
    colors = [c.strip() for c in palette_colors.split(",")]
    c1 = hex_to_rgb(colors[0])
    
    draw = ImageDraw.Draw(canvas)
    
    # Brand name — solid near-black
    wordmark_color = (25, 25, 30)
    wordmark_font_size = int(H * 0.072)
    try:
        wordmark_font = ImageFont.truetype(f"{FONT_DIR}/Poppins-ExtraBold.ttf", wordmark_font_size)
    except:
        wordmark_font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), brand_name, font=wordmark_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (W - text_w) // 2
    text_y = icon_y + icon_target_h + int(H * 0.04)
    
    draw.text((text_x, text_y), brand_name, font=wordmark_font, fill=wordmark_color)
    
    # Tagline — solid brand color, letter-spaced
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
        tagline_y = text_y + text_h + int(H * 0.025)
        tagline_color = (*c1, 220)
        
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
    return {"status": "ready", "model": "flux-v5"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5003, log_level="info")
