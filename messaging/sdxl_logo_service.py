#!/usr/bin/env python3
"""
EvolvixOS SDXL Logo Icon Service v3
- rembg for AI background removal (perfect icon cutout)
- 2x upscaling with Lanczos + unsharp mask
- 768x768, 4 steps, ~28s generation
- Enhanced post-processing
"""
import torch, time, io, os, re, asyncio, httpx, tempfile
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pydantic import BaseModel
import uvicorn

pipe = None
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
FONT_DIR = "/opt/evolvixos/fonts"

app = FastAPI(title="EvolvixOS SDXL Logo Service")

@app.on_event("startup")
async def load_model():
    global pipe
    from diffusers import StableDiffusionXLPipeline
    print("Loading SDXL Turbo v3...", flush=True)
    pipe = StableDiffusionXLPipeline.from_single_file(
        '/opt/evolvixos/models/sdxl-turbo/sd_xl_turbo_1.0_fp16.safetensors',
        torch_dtype=torch.float32,
    )
    pipe.to('cpu')
    pipe.set_progress_bar_config(disable=True)
    print("SDXL Turbo v3 loaded!", flush=True)

async def enhance_prompt_for_icon(brand_name, description, palette_colors):
    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": """You write image generation prompts for PROFESSIONAL LOGO ICONS.
Rules:
1. Generate ONLY the icon/symbol — NO text, NO letters, NO words.
2. Describe: shape, form, gradient colors, lighting, material quality, style.
3. Include quality boosters: "ultra detailed, sharp focus, professional, premium branding, studio lighting"
4. Specify material: "glossy", "metallic", "glassmorphism", or "matte" based on the brand feel.
5. Keep under 65 words (CLIP has 77 token limit).
6. End with: "no text, no letters, icon only"
Output ONLY the prompt text."""},
                    {"role": "user", "content": f"Brand: {brand_name}\nConcept: {description}\nColors: {palette_colors}"}
                ],
                "temperature": 0.85,
                "max_tokens": 1000
            }
        )
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        if not content or len(content) < 20:
            content = f"Professional logo icon for {brand_name}: {description}. {palette_colors}. Ultra detailed, sharp focus, premium branding, glossy, studio lighting. no text, no letters, icon only"
        return content

class LogoRequest(BaseModel):
    brand_name: str
    description: str
    palette_colors: str = "#0066FF, #7C3AED, #00CCFF"
    tagline: str = ""

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def ai_remove_bg(img):
    """Use rembg for AI-powered background removal"""
    from rembg import remove
    # rembg returns RGBA with proper alpha channel
    result = remove(img)
    return result

def upscale_icon(img, factor=2):
    """Upscale icon with Lanczos + unsharp mask for crisp detail"""
    w, h = img.size
    new_size = (w * factor, h * factor)
    img = img.resize(new_size, Image.LANCZOS)
    # Unsharp mask for crispness
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=2))
    return img

def postprocess_icon(img):
    """Post-process the SDXL icon for professional quality"""
    # Unsharp mask
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=3))
    # Contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.12)
    # Color saturation
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.08)
    return img

def compose_logo(icon_img, brand_name, tagline="", palette_colors="#0066FF, #7C3AED",
                 canvas_size=(1600, 1600)):
    """Composite icon + gradient typography with professional polish"""
    W, H = canvas_size
    canvas = Image.new("RGBA", canvas_size, (255, 255, 255, 0))
    
    # AI background removal (rembg)
    icon = ai_remove_bg(icon_img)
    icon = icon.convert("RGBA")
    
    # Trim to content
    bbox = icon.getbbox()
    if bbox:
        # Add small padding
        pad = 10
        bbox = (max(0, bbox[0]-pad), max(0, bbox[1]-pad), 
                min(icon.width, bbox[2]+pad), min(icon.height, bbox[3]+pad))
        icon = icon.crop(bbox)
    
    # Upscale 2x for more detail
    icon = upscale_icon(icon, factor=2)
    
    # Resize to target
    icon_target_h = int(H * 0.38)
    ratio = icon_target_h / icon.height
    icon_target_w = int(icon.width * ratio)
    icon_resized = icon.resize((icon_target_w, icon_target_h), Image.LANCZOS)
    
    icon_x = (W - icon_target_w) // 2
    icon_y = int(H * 0.06)
    
    # Soft drop shadow
    shadow = icon_resized.copy()
    shadow_data = [(0, 0, 0, min(a, 45)) for r, g, b, a in shadow.getdata()]
    shadow.putdata(shadow_data)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=18))
    canvas.paste(shadow, (icon_x + 6, icon_y + 10), shadow)
    
    # Subtle brand-colored glow behind icon
    colors = [c.strip() for c in palette_colors.split(",")]
    c1 = hex_to_rgb(colors[0])
    glow = icon_resized.copy()
    glow_data = [(c1[0], c1[1], c1[2], min(a, 25)) for r, g, b, a in glow.getdata()]
    glow.putdata(glow_data)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=30))
    canvas.paste(glow, (icon_x - 5, icon_y - 5), glow)
    
    # Main icon
    canvas.paste(icon_resized, (icon_x, icon_y), icon_resized)
    
    draw = ImageDraw.Draw(canvas)
    
    # Gradient text
    c1 = hex_to_rgb(colors[0])
    c2 = hex_to_rgb(colors[1] if len(colors) > 1 else colors[0])
    
    wordmark_font_size = int(H * 0.085)
    try:
        wordmark_font = ImageFont.truetype(f"{FONT_DIR}/Poppins-ExtraBold.ttf", wordmark_font_size)
    except:
        wordmark_font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), brand_name, font=wordmark_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (W - text_w) // 2
    text_y = icon_y + icon_target_h + int(H * 0.02)
    
    # Gradient text with mask
    text_mask = Image.new("L", (text_w + 60, text_h + 60), 0)
    mask_draw = ImageDraw.Draw(text_mask)
    mask_draw.text((30 - bbox[0], 30 - bbox[1]), brand_name, font=wordmark_font, fill=255)
    text_mask = text_mask.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    gradient = Image.new("RGBA", (text_w + 60, text_h + 60), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(gradient)
    for y in range(text_h + 60):
        t = y / (text_h + 60)
        r = int(c1[0] * (1-t) + c2[0] * t)
        g = int(c1[1] * (1-t) + c2[1] * t)
        b = int(c1[2] * (1-t) + c2[2] * t)
        grad_draw.line([(0, y), (text_w + 60, y)], fill=(r, g, b, 255))
    gradient.putalpha(text_mask)
    canvas.paste(gradient, (text_x - 30, text_y - 30), gradient)
    
    # Tagline
    if tagline:
        tagline_font_size = int(H * 0.022)
        try:
            tagline_font = ImageFont.truetype(f"{FONT_DIR}/Poppins-Medium.ttf", tagline_font_size)
        except:
            tagline_font = ImageFont.load_default()
        
        tagline_upper = tagline.upper()
        letter_spacing = int(tagline_font_size * 0.45)
        char_widths = []
        total_w = 0
        for ch in tagline_upper:
            w = draw.textlength(ch, font=tagline_font)
            char_widths.append(w)
            total_w += w + letter_spacing
        total_w -= letter_spacing
        
        cursor_x = (W - total_w) // 2
        tagline_y = text_y + text_h + int(H * 0.02)
        tagline_color = (*c2, 180)
        for ch, w in zip(tagline_upper, char_widths):
            draw.text((cursor_x, tagline_y), ch, font=tagline_font, fill=tagline_color)
            cursor_x += w + letter_spacing
    
    return canvas

@app.post("/generate")
async def generate_logo(req: LogoRequest):
    global pipe
    if pipe is None:
        return JSONResponse({"error": "Model not loaded yet"}, status_code=503)
    
    # Enhance prompt
    icon_prompt = await enhance_prompt_for_icon(req.brand_name, req.description, req.palette_colors)
    words = icon_prompt.split()
    if len(words) > 65:
        icon_prompt = ' '.join(words[:55]) + ' ' + ' '.join(words[-8:])
    print(f"[LOGO] Prompt: {icon_prompt[:100]}...", flush=True)
    
    # Generate icon
    start = time.time()
    loop = asyncio.get_event_loop()
    image = await loop.run_in_executor(
        None,
        lambda: pipe(
            prompt=icon_prompt,
            negative_prompt="text, letters, words, watermark, signature, low quality, blurry, distorted, ugly, noisy, grainy, pixelated, amateur, cartoon, childish, deformed",
            num_inference_steps=4,
            guidance_scale=1.0,
            width=768,
            height=768,
        ).images[0]
    )
    gen_time = time.time() - start
    print(f"[LOGO] SDXL generated in {gen_time:.1f}s", flush=True)
    
    # Post-process icon
    image = postprocess_icon(image)
    
    # Composite with AI bg removal + upscaling
    final = compose_logo(image, req.brand_name, req.tagline, req.palette_colors)
    
    # Save
    fd, temp_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    final.save(temp_path, "PNG")
    
    print(f"[LOGO] Final saved ({os.path.getsize(temp_path)//1024}KB)", flush=True)
    return {"path": temp_path, "generation_time": round(gen_time, 1), "prompt": icon_prompt}

@app.get("/health")
async def health():
    return {"status": "ready" if pipe is not None else "loading", "model": "sdxl-turbo-v3"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5003, log_level="info")
