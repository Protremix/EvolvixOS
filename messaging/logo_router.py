"""Logo routing module for EvolvixOS Telegram bot"""
import os, re, httpx

SDXL_LOGO_API = os.environ.get("SDXL_LOGO_API", "http://127.0.0.1:5003")

LOGO_PALETTES = {
    "green": "#00A86B, #34D399",
    "blue": "#0066FF, #7C3AED",
    "purple": "#7C3AED, #A855F7",
    "orange": "#FF6B35, #F7B538",
    "red": "#EF4444, #DC2626",
    "gold": "#D4AF37, #FFD700",
    "dark": "#1A1A2E, #16213E",
    "teal": "#0077BE, #00B4D8",
}

def detect_palette(text):
    t = text.lower()
    for color, palette in LOGO_PALETTES.items():
        if color in t:
            return palette
    return LOGO_PALETTES["blue"]

def is_logo_request(text):
    t = text.lower()
    return "logo" in t or "wordmark" in t or "brand mark" in t

def extract_brand_name(conversation_context):
    combined = " ".join(conversation_context)
    m = re.search(r'(?:call(?:ed)?\s+it|named?|for)\s+([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)?)', combined)
    if m:
        return m.group(1).strip()
    words = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', combined)
    stop = {"Create", "Make", "Design", "Draw", "Logo", "Modern", "Digital", "Blockchain", "Yes", "Green", "Blue"}
    candidates = [w for w in words if w not in stop]
    if candidates:
        return candidates[-1]
    return "Brand"

async def generate_professional_logo(conversation_context):
    """Call the SDXL Turbo logo service for professional quality"""
    combined_desc = " ".join(conversation_context)
    brand_name = extract_brand_name(conversation_context)
    tagline = ""
    m = re.search(r'tagline[:\s]+["\']?([^"\'\n]{3,60})', combined_desc, re.IGNORECASE)
    if m:
        tagline = m.group(1).strip()
    palette = detect_palette(combined_desc)
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{SDXL_LOGO_API}/generate", json={
            "brand_name": brand_name,
            "description": combined_desc,
            "palette_colors": palette,
            "tagline": tagline
        })
        data = resp.json()
        if "path" in data:
            print(f"[LOGO] SDXL generated in {data.get('generation_time', '?')}s", flush=True)
            return data["path"], brand_name
        raise RuntimeError(f"SDXL service error: {data.get('error', 'unknown')}")
