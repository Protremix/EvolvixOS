#!/usr/bin/env python3
"""Ideal Gas Law Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        # P = nRT / V
        n = float(args.get("moles", 1.0))
        T = float(args.get("temp_K", 298.15))
        V = float(args.get("volume_m3", 0.0224))
        R = 8.314
        P = (n * R * T) / V
        return {"pressure_Pa": round(P, 2), "moles": n, "temp_K": T}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
