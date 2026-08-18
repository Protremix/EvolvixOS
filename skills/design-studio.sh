#!/bin/bash
# Create logos, brand identities, UI/UX designs, social media graphics
# Usage: ./design-studio.sh "logo for tech startup"

PROMPT="$1"
OUTPUT_DIR="/opt/evolvixos/output/design"
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🎨 Design Studio: $PROMPT"

# Generate design variants
python3 -c "
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

TIMESTAMP = '$TIMESTAMP'
OUTPUT_DIR = '$OUTPUT_DIR'
PROMPT = '''$PROMPT'''

# Color palettes
palettes = [
    [(139, 92, 246), (236, 72, 153), (15, 13, 20)],  # Purple-Pink
    [(59, 130, 246), (16, 185, 129), (15, 23, 42)],  # Blue-Green
    [(251, 191, 36), (239, 68, 68), (15, 13, 20)],   # Gold-Red
    [(6, 182, 212), (139, 92, 246), (15, 13, 20)],   # Cyan-Purple
]

for i, (c1, c2, bg) in enumerate(palettes):
    img = Image.new('RGB', (1024, 1024), color=bg)
    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 64)
        font_med = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 32)
    except:
        font_big = ImageFont.load_default()
        font_med = font_big
    
    # Gradient circle
    cx, cy, r = 512, 400, 200
    for y in range(cy-r, cy+r):
        for x in range(cx-r, cx+r):
            if (x-cx)**2 + (y-cy)**2 < r**2:
                t = ((x-cx)**2 + (y-cy)**2) / (r**2)
                color = tuple(int(c1[j] + (c2[j]-c1[j])*t) for j in range(3))
                img.putpixel((x, y), color)
    
    # Text
    lines = textwrap.wrap(PROMPT[:60], width=25)
    y = 660
    for line in lines[:3]:
        bbox = draw.textbbox((0,0), line, font=font_big)
        w = bbox[2]-bbox[0]
        draw.text(((1024-w)//2, y), line, fill=(255,255,255), font=font_big)
        y += 80
    
    draw.text((512, 750), 'EvolvixOS Design', fill=(150,150,150), font=font_med, anchor='mm')
    
    fname = f'{OUTPUT_DIR}/design_variant_{i+1}_{TIMESTAMP}.png'
    img.save(fname)
    print(f'Saved: {fname}')

print(f'Generated 4 design variants')
"

echo "Done! Files in $OUTPUT_DIR"
ls -la "$OUTPUT_DIR/" | tail -5
