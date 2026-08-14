#!/usr/bin/env python3
"""OCR Scanner - EasyOCR (Apache 2.0) - 100% Free"""
import json, sys, subprocess, os


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        img = args.get("image", "")
        if not img or not os.path.exists(img):
            return {"error": "image required"}
        try:
            import easyocr
            reader = easyocr.Reader(args.get("languages", ["en"]))
            results = reader.readtext(img)
            return {"text": " ".join([r[1] for r in results]), "regions": len(results)}
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "easyocr"], capture_output=True)
            return self.run(args)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
