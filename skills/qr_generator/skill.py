#!/usr/bin/env python3
"""QR Code Generator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        data = args.get("data", "EvolvixOS")
        if not data:
            return {"error": "data required"}
        try:
            import qrcode
            import io
            img = qrcode.make(data)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            import base64
            b64 = base64.b64encode(buf.getvalue()).decode()
            return {"qr_base64": b64, "data": data, "size": img.size}
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "qrcode[pil]"], capture_output=True)
            import qrcode, io, base64
            img = qrcode.make(data)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            return {"qr_base64": b64, "data": data, "size": img.size}
