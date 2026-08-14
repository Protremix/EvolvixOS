#!/usr/bin/env python3
"""Color Name Finder — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        hex_color = args.get("hex", "#000000").lstrip("#")
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        colors = {"Black": (0, 0, 0), "White": (255, 255, 255), "Red": (255, 0, 0), "Green": (0, 128, 0), "Blue": (0, 0, 255), "Yellow": (255, 255, 0), "Cyan": (0, 255, 255), "Magenta": (255, 0, 255), "Gray": (128, 128, 128), "Silver": (192, 192, 192), "Maroon": (128, 0, 0), "Olive": (128, 128, 0), "Lime": (0, 255, 0), "Purple": (128, 0, 128), "Teal": (0, 128, 128), "Navy": (0, 0, 128), "Orange": (255, 165, 0), "Pink": (255, 192, 203), "Brown": (165, 42, 42), "Gold": (255, 215, 0)}
        def dist(c1, c2):
            return sum((a - b) ** 2 for a, b in zip(c1, c2))
        closest = min(colors.items(), key=lambda x: dist(x[1], (r, g, b)))
        return {"input": f"#{hex_color}", "rgb": [r, g, b], "closest_name": closest[0], "closest_rgb": list(closest[1]), "distance": int(dist((r, g, b), closest[1]))}
