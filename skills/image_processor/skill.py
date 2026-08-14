#!/usr/bin/env python3
"""Image Processor - Pillow + OpenCV (HPND/Apache 2.0) - 100% Free"""
import json, sys, subprocess, os


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        action = args.get("action", "info")
        path = args.get("file", "")
        try:
            from PIL import Image, ImageFilter
            if action == "info":
                img = Image.open(path)
                return {"size": img.size, "mode": img.mode, "format": img.format}
            elif action == "resize":
                img = Image.open(path)
                w, h = args.get("width"), args.get("height")
                if w and h: img = img.resize((w, h))
                elif w: img = img.resize((w, int(img.height * w / img.width)))
                out = args.get("output", path.replace(".", "_resized."))
                img.save(out)
                return {"output": out, "size": img.size}
            elif action == "convert":
                img = Image.open(path)
                fmt = args.get("format", "PNG")
                out = os.path.splitext(path)[0] + "." + fmt.lower()
                img.save(out, format=fmt)
                return {"output": out}
            elif action == "filter":
                img = Image.open(path)
                f = args.get("filter", "blur")
                if f == "grayscale": img = img.convert("L")
                elif f == "blur": img = img.filter(ImageFilter.Blur())
                elif f == "sharpen": img = img.filter(ImageFilter.SHARPEN())
                elif f == "edge": img = img.filter(ImageFilter.FIND_EDGES())
                out = args.get("output", path.replace(".", f"_{f}."))
                img.save(out)
                return {"output": out}
            return {"error": f"unknown: {action}"}
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "Pillow", "opencv-python-headless"], capture_output=True)
            return self.run(args)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
