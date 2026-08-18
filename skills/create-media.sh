#!/bin/bash
# Create 4K videos, movies, voiceovers, and images from a prompt
# Usage: ./create-media.sh "prompt"

PROMPT="$1"
OUTPUT_DIR="/opt/evolvixos/output/media"
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🎬 Media Creation: $PROMPT"
echo "Output: $OUTPUT_DIR"

# Generate an image first
python3 -c "
from PIL import Image, ImageDraw, ImageFont
import textwrap
img = Image.new('RGB', (1920, 1080), color=(15, 13, 20))
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 48)
    sub_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
except:
    font = ImageFont.load_default()
    sub_font = font
lines = textwrap.wrap('$PROMPT', width=40)
y = 400
for line in lines:
    draw.text((100, y), line, fill=(255,255,255), font=font)
    y += 60
draw.text((100, y+40), 'EvolvixOS Media', fill=(139,92,246), font=sub_font)
img.save('$OUTPUT_DIR/image_${TIMESTAMP}.png')
print('Image saved: $OUTPUT_DIR/image_${TIMESTAMP}.png')
"

# Generate voiceover
espeak-ng "$PROMPT" -w "$OUTPUT_DIR/voiceover_${TIMESTAMP}.wav" 2>/dev/null || \
python3 -c "
import subprocess
subprocess.run(['espeak', '$PROMPT', '-w', '$OUTPUT_DIR/voiceover_${TIMESTAMP}.wav'])
print('Voiceover saved: $OUTPUT_DIR/voiceover_${TIMESTAMP}.wav')
"

# Create a video combining image + voiceover
ffmpeg -y -loop 1 -i "$OUTPUT_DIR/image_${TIMESTAMP}.png" -i "$OUTPUT_DIR/voiceover_${TIMESTAMP}.wav" \
    -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest \
    "$OUTPUT_DIR/video_${TIMESTAMP}.mp4" -loglevel error 2>/dev/null && \
    echo "Video saved: $OUTPUT_DIR/video_${TIMESTAMP}.mp4"

echo "Done! Files in $OUTPUT_DIR"
ls -la "$OUTPUT_DIR/" | tail -5
