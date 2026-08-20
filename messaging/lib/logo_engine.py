#!/usr/bin/env python3
"""
EvolvixOS Professional Logo Engine
Two-stage pipeline: AI-generated icon (no text) + programmatic typography compositing.
This avoids the garbled-text problem diffusion models have and produces crisp,
professional wordmarks that match commercial logo maker quality.
"""
import os
import httpx, asyncio, hashlib, io, re
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
FONT_DIR = "/opt/evolvixos/fonts"

async def design_icon_concept(brand_name, description):
    """Use Groq to design just the ICON concept (no text/letters in the image itself)"""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": (
                        "You are a professional logo icon designer. Design ONLY the icon/symbol for a brand - "
                        "NOT the text/wordmark (that gets added separately with real typography). "
                        "Rules:\n"
                        "1. The icon must be a CONCRETE, MEMORABLE geometric symbol - abstract ribbon/ribbon-letter "
                        "shapes, interlocking geometric forms, or a literal object tied to the brand meaning. "
                        "Think Nike swoosh, Airbnb symbol, Slack hashtag - iconic and simple, not generic.\n"
                        "2. NEVER include any text, letters, or words as part of the icon image itself.\n"
                        "3. Explicitly end the prompt with: 'no text, no letters, no words, icon only'\n"
                        "4. Specify exact colors (hex codes) as a smooth gradient if appropriate.\n"
                        "5. Specify: vector style, flat design, clean sharp edges, centered composition, "
                        "isolated on pure white background, professional branding icon.\n"
                        "Output ONLY the prompt text, no explanation, no quotes."
                    )},
                    {"role": "user", "content": f"Brand: {brand_name}\nConcept: {description}"}
                ],
                "temperature": 0.9,
                "max_tokens": 600
            }
        )
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

async def generate_icon_image(prompt, size=1024):
    """Generate the icon via Pollinations Flux"""
    url = f"https://image.pollinations.ai/prompt/{quote(prompt, safe='')}?width={size}&height={size}&nologo=true&model=flux"
    async with httpx.AsyncClient(timeout=120, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as client:
        resp = await client.get(url)
        if resp.status_code == 200 and len(resp.content) > 5000:
            return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    return None

def remove_white_background(img, threshold=245):
    """Make near-white pixels transparent so the icon composites cleanly"""
    img = img.convert("RGBA")
    datas = img.getdata()
    new_data = []
    for r, g, b, a in datas:
        if r > threshold and g > threshold and b > threshold:
            new_data.append((r, g, b, 0))
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)
    return img

def trim_transparent_border(img):
    """Crop to the bounding box of non-transparent content"""
    bbox = img.getbbox()
    if bbox:
        return img.crop(bbox)
    return img

def compose_logo(icon_img, brand_name, tagline, canvas_size=(1024, 1024), 
                  text_color=(10, 15, 30), tagline_color=(120, 120, 130)):
    """Composite icon + crisp typography into a final professional logo, Nexora-style layout"""
    W, H = canvas_size
    canvas = Image.new("RGBA", canvas_size, (255, 255, 255, 255))

    # Clean up icon: remove white bg, trim, resize
    icon = remove_white_background(icon_img)
    icon = trim_transparent_border(icon)
    
    icon_target_h = int(H * 0.30)
    ratio = icon_target_h / icon.height
    icon_target_w = int(icon.width * ratio)
    icon = icon.resize((icon_target_w, icon_target_h), Image.LANCZOS)

    icon_x = (W - icon_target_w) // 2
    icon_y = int(H * 0.12)
    canvas.paste(icon, (icon_x, icon_y), icon)

    draw = ImageDraw.Draw(canvas)

    # Wordmark - bold, big, tight
    wordmark_font_size = int(H * 0.10)
    wordmark_font = ImageFont.truetype(f"{FONT_DIR}/Poppins-ExtraBold.ttf", wordmark_font_size)
    bbox = draw.textbbox((0, 0), brand_name, font=wordmark_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (W - text_w) // 2
    text_y = icon_y + icon_target_h + int(H * 0.04)
    draw.text((text_x, text_y), brand_name, font=wordmark_font, fill=text_color)

    # Tagline - letter-spaced small caps below
    if tagline:
        tagline_font_size = int(H * 0.025)
        tagline_font = ImageFont.truetype(f"{FONT_DIR}/Poppins-Medium.ttf", tagline_font_size)
        spaced_tagline = " ".join(list(tagline.upper()))  # crude letter-spacing via spaces
        # Better: use tracking by drawing char by char
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
        tagline_y = text_y + text_h + int(H * 0.035)
        for ch, w in zip(tagline_upper, char_widths):
            draw.text((cursor_x, tagline_y), ch, font=tagline_font, fill=tagline_color)
            cursor_x += w + letter_spacing

    return canvas.convert("RGB")

async def create_professional_logo(brand_name, description, tagline=""):
    """Full pipeline: design icon concept -> generate -> composite with typography"""
    icon_prompt = await design_icon_concept(brand_name, description)
    print(f"Icon prompt: {icon_prompt}")
    icon_img = await generate_icon_image(icon_prompt)
    if icon_img is None:
        raise RuntimeError("Icon generation failed")
    final = compose_logo(icon_img, brand_name, tagline)
    return final, icon_prompt

# === TEST ===
async def main():
    logo, prompt = await create_professional_logo(
        "Nexora", 
        "modern tech company, AI and innovation, blue gradient ribbon forming an abstract N shape, smooth flowing curves",
        "BUILDING A SMARTER TOMORROW"
    )
    logo.save("/tmp/nexora_test.png")
    print("Saved /tmp/nexora_test.png")

if __name__ == "__main__":
    asyncio.run(main())
