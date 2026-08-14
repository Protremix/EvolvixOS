"""
EvolvixOS — Image Editor Skill
Edit images: resize, crop, rotate, filter, watermark, convert formats.
100% local using Pillow. Zero tokens. Zero cloud.

Pip: pip install Pillow
License: HPND (Pillow/PIL)
"""

import os
import time
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class Skill:
    """Image editor — manipulate images with Pillow. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/images_edited"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, args: dict) -> str:
        action = args.get("action", "resize")

        if action == "resize":
            return self.resize(args.get("image", ""), args.get("width", 800),
                               args.get("height", None))
        elif action == "crop":
            return self.crop(args.get("image", ""), args.get("box", []))
        elif action == "rotate":
            return self.rotate(args.get("image", ""), args.get("angle", 90))
        elif action == "filter":
            return self.apply_filter(args.get("image", ""), args.get("filter", "blur"))
        elif action == "watermark":
            return self.watermark(args.get("image", ""), args.get("text", "EvolvixOS"),
                                  args.get("opacity", 128))
        elif action == "convert":
            return self.convert_format(args.get("image", ""), args.get("to_format", "png"))
        elif action == "compress":
            return self.compress(args.get("image", ""), args.get("quality", 85))
        elif action == "thumbnail":
            return self.thumbnail(args.get("image", ""), args.get("size", 200))
        elif action == "info":
            return self.image_info(args.get("image", ""))
        elif action == "grayscale":
            return self.grayscale(args.get("image", ""))
        elif action == "batch_resize":
            return self.batch_resize(args.get("images", []), args.get("width", 800))
        else:
            return (f"Unknown action: {action}. Use: resize, crop, rotate, filter, "
                    "watermark, convert, compress, thumbnail, info, grayscale, batch_resize")

    def resize(self, image_path: str, width: int = 800, height: int = None) -> str:
        try:
            from PIL import Image
            img = Image.open(image_path)
            if height:
                img = img.resize((width, height))
            else:
                ratio = width / img.width
                img = img.resize((width, int(img.height * ratio)))
            out = self.output_dir / f"resized_{int(time.time())}.png"
            img.save(str(out))
            return f"Resized: {out}"
        except Exception as e:
            return f"Error: {e}"

    def crop(self, image_path: str, box: list = None) -> str:
        try:
            from PIL import Image
            img = Image.open(image_path)
            if not box or len(box) != 4:
                box = [0, 0, img.width // 2, img.height // 2]
            img = img.crop(tuple(box))
            out = self.output_dir / f"cropped_{int(time.time())}.png"
            img.save(str(out))
            return f"Cropped: {out}"
        except Exception as e:
            return f"Error: {e}"

    def rotate(self, image_path: str, angle: float = 90) -> str:
        try:
            from PIL import Image
            img = Image.open(image_path).rotate(angle, expand=True)
            out = self.output_dir / f"rotated_{int(time.time())}.png"
            img.save(str(out))
            return f"Rotated {angle}°: {out}"
        except Exception as e:
            return f"Error: {e}"

    def apply_filter(self, image_path: str, filter_name: str = "blur") -> str:
        try:
            from PIL import Image, ImageFilter
            img = Image.open(image_path)
            filters = {
                "blur": ImageFilter.BLUR,
                "sharpen": ImageFilter.SHARPEN,
                "edge": ImageFilter.FIND_EDGES,
                "emboss": ImageFilter.EMBOSS,
                "smooth": ImageFilter.SMOOTH,
                "detail": ImageFilter.DETAIL,
                "contour": ImageFilter.CONTOUR,
            }
            f = filters.get(filter_name, ImageFilter.BLUR)
            img = img.filter(f)
            out = self.output_dir / f"filtered_{filter_name}_{int(time.time())}.png"
            img.save(str(out))
            return f"Filtered ({filter_name}): {out}"
        except Exception as e:
            return f"Error: {e}"

    def watermark(self, image_path: str, text: str = "EvolvixOS",
                  opacity: int = 128) -> str:
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.open(image_path).convert("RGBA")
            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            try:
                font = ImageFont.truetype("arial.ttf", max(24, img.width // 20))
            except:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = img.width - tw - 20
            y = img.height - th - 20
            draw.text((x, y), text, (255, 255, 255, opacity), font=font)
            img = Image.alpha_composite(img, overlay).convert("RGB")
            out = self.output_dir / f"watermarked_{int(time.time())}.png"
            img.save(str(out))
            return f"Watermarked: {out}"
        except Exception as e:
            return f"Error: {e}"

    def convert_format(self, image_path: str, to_format: str = "png") -> str:
        try:
            from PIL import Image
            img = Image.open(image_path)
            base = Path(image_path).stem
            out = self.output_dir / f"{base}.{to_format}"
            if to_format in ("jpg", "jpeg"):
                img = img.convert("RGB")
            img.save(str(out), format=to_format.upper())
            return f"Converted: {out}"
        except Exception as e:
            return f"Error: {e}"

    def compress(self, image_path: str, quality: int = 85) -> str:
        try:
            from PIL import Image
            img = Image.open(image_path)
            out = self.output_dir / f"compressed_{int(time.time())}.jpg"
            img.save(str(out), "JPEG", quality=quality, optimize=True)
            orig_size = os.path.getsize(image_path)
            new_size = os.path.getsize(out)
            saved = round((1 - new_size / orig_size) * 100, 1)
            return f"Compressed: {out} (saved {saved}%)"
        except Exception as e:
            return f"Error: {e}"

    def thumbnail(self, image_path: str, size: int = 200) -> str:
        try:
            from PIL import Image
            img = Image.open(image_path)
            img.thumbnail((size, size))
            out = self.output_dir / f"thumb_{int(time.time())}.png"
            img.save(str(out))
            return f"Thumbnail: {out}"
        except Exception as e:
            return f"Error: {e}"

    def image_info(self, image_path: str) -> str:
        try:
            from PIL import Image
            import json
            img = Image.open(image_path)
            info = {
                "file": image_path,
                "format": img.format,
                "size": list(img.size),
                "mode": img.mode,
                "file_size_kb": round(os.path.getsize(image_path) / 1024, 1),
            }
            if hasattr(img, "info") and img.info:
                info["metadata"] = {k: str(v)[:100] for k, v in img.info.items()}
            return json.dumps(info, indent=2)
        except Exception as e:
            return f"Error: {e}"

    def grayscale(self, image_path: str) -> str:
        try:
            from PIL import Image
            img = Image.open(image_path).convert("L")
            out = self.output_dir / f"grayscale_{int(time.time())}.png"
            img.save(str(out))
            return f"Grayscale: {out}"
        except Exception as e:
            return f"Error: {e}"

    def batch_resize(self, images: List[str], width: int = 800) -> str:
        results = []
        for img_path in images:
            results.append(self.resize(img_path, width))
        return "\n".join(results)
