#!/usr/bin/env python3
"""Color Blindness Simulator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        rgb = args.get("rgb", [255, 0, 0])
        # Protanopia simulation (red weak)
        sim_rgb = [int(0.566*rgb[0] + 0.433*rgb[1]), int(0.558*rgb[0] + 0.442*rgb[1]), int(0.242*rgb[1] + 0.758*rgb[2])]
        return {"original_rgb": rgb, "protanopia_simulated_rgb": sim_rgb}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
