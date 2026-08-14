"""
EvolvixOS — OCR Skill
Extract text from images and scanned documents using Tesseract / EasyOCR.
100% local. Zero tokens. Zero cloud.

Pip: pip install pytesseract Pillow (Tesseract binary also needed)
  OR: pip install easyocr (bundled models, no external binary)
License: Apache-2.0 (Tesseract), Apache-2.0 (EasyOCR)
"""

import os
import time
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class Skill:
    """OCR — extract text from images. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/ocr"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.engine = self.config.get("engine", "tesseract")
        self.lang = self.config.get("lang", "eng")
        self._reader = None

    def run(self, args: dict) -> str:
        action = args.get("action", "extract")

        if action == "extract":
            return self.extract_text(args.get("image", ""), args.get("lang", self.lang))
        elif action == "extract_batch":
            return self.extract_batch(args.get("images", []), args.get("lang", self.lang))
        elif action == "extract_pdf":
            return self.extract_from_pdf(args.get("file", ""))
        else:
            return f"Unknown action: {action}. Use: extract, extract_batch, extract_pdf"

    def extract_text(self, image_path: str, lang: str = None) -> str:
        if not image_path or not os.path.exists(image_path):
            return "Error: Image file not found."

        lang = lang or self.lang

        if self.engine == "easyocr":
            return self._extract_easyocr(image_path, lang)
        else:
            return self._extract_tesseract(image_path, lang)

    def _extract_tesseract(self, image_path: str, lang: str) -> str:
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang=lang)
            return text.strip()
        except ImportError:
            console.print("[yellow]Tesseract not installed, trying EasyOCR...[/yellow]")
            return self._extract_easyocr(image_path, lang)
        except Exception as e:
            return f"Error: {e}"

    def _extract_easyocr(self, image_path: str, lang: str) -> str:
        try:
            import easyocr
            if self._reader is None:
                langs = [lang[:2]] if len(lang) >= 2 else ["en"]
                self._reader = easyocr.Reader(langs)
            results = self._reader.readtext(image_path)
            text = " ".join([r[1] for r in results])
            return text.strip()
        except ImportError:
            return "Error: pip install easyocr OR pip install pytesseract Pillow (+ install tesseract binary)"
        except Exception as e:
            return f"Error: {e}"

    def extract_batch(self, images: List[str], lang: str = None) -> str:
        results = {}
        for img in images:
            results[img] = self.extract_text(img, lang)
        import json
        return json.dumps(results, indent=2)[:10000]

    def extract_from_pdf(self, pdf_path: str) -> str:
        try:
            # Convert PDF pages to images then OCR
            import subprocess
            output_prefix = str(self.output_dir / f"page_{int(time.time())}")

            # Use pdftoppm (from poppler-utils) to convert PDF to images
            subprocess.run(["pdftoppm", "-png", pdf_path, output_prefix],
                          capture_output=True, timeout=60)

            # OCR each page image
            pages = sorted(Path(self.output_dir).glob(f"page_{int(time.time())}*.png"))
            full_text = []
            for page_img in pages:
                text = self.extract_text(str(page_img))
                full_text.append(text)

            return "\n\n--- Page Break ---\n\n".join(full_text)
        except Exception as e:
            return f"Error extracting from PDF: {e}\n(Fallback: use document_processor skill for digital PDFs)"
