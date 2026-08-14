#!/usr/bin/env python3
"""Color Palette Generator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import colorsys, random
        base_hex = args.get("base", "#7C5CFF").lstrip("#")
        mode = args.get("mode", "complementary")
        count = args.get("count", 5)
        r, g, b = int(base_hex[:2], 16), int(base_hex[2:4], 16), int(base_hex[4:6], 16)
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        palette = []
        if mode == "complementary":
            hues = [h, h + 0.5]
        elif mode == "analogous":
            hues = [h + i * 0.083 for i in range(-count//2, count//2 + 1)]
        elif mode == "triadic":
            hues = [h, h + 1/3, h + 2/3]
        elif mode == "monochromatic":
            hues = [h]
            for i in range(count):
                new_l = max(0.1, min(0.9, l + (i - count//2) * 0.15))
                r2, g2, b2 = colorsys.hls_to_rgb(h, new_l, s)
                palette.append(f"#{int(r2*255):02X}{int(g2*255):02X}{int(b2*255):02X}")
            return {"palette": palette, "mode": mode, "base": f"#{base_hex}"}
        elif mode == "random":
            hues = [random.random() for _ in range(count)]
        else:
            hues = [h]
        for hue in hues:
            for i in range(max(1, count // len(hues))):
                new_l = max(0.15, min(0.85, l + random.uniform(-0.2, 0.2)))
                new_s = max(0.3, min(1.0, s + random.uniform(-0.2, 0.2)))
                r2, g2, b2 = colorsys.hls_to_rgb(hue % 1.0, new_l, new_s)
                palette.append(f"#{int(r2*255):02X}{int(g2*255):02X}{int(b2*255):02X}")
                if len(palette) >= count:
                    break
            if len(palette) >= count:
                break
        return {"palette": palette[:count], "mode": mode, "base": f"#{base_hex}"}
