#!/usr/bin/env python3
"""Gradient Generator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import colorsys
        hex1 = args.get("from", "#7C5CFF").lstrip("#")
        hex2 = args.get("to", "#00D4AA").lstrip("#")
        steps = args.get("steps", 10)
        r1, g1, b1 = int(hex1[:2], 16), int(hex1[2:4], 16), int(hex1[4:6], 16)
        r2, g2, b2 = int(hex2[:2], 16), int(hex2[2:4], 16), int(hex2[4:6], 16)
        gradient = []
        for i in range(steps):
            t = i / max(1, steps - 1)
            r = round(r1 + (r2 - r1) * t)
            g = round(g1 + (g2 - g1) * t)
            b = round(b1 + (b2 - b1) * t)
            gradient.append(f"#{r:02X}{g:02X}{b:02X}")
        return {"gradient": gradient, "steps": steps, "from": f"#{hex1}", "to": f"#{hex2}"}
