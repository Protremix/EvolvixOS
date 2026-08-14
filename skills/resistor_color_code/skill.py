#!/usr/bin/env python3
"""Resistor Color Code Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        bands = args.get("bands", ["brown", "black", "red", "gold"])
        COLORS = {"black": 0, "brown": 1, "red": 2, "orange": 3, "yellow": 4, "green": 5, "blue": 6, "violet": 7, "gray": 8, "white": 9}
        val = (COLORS.get(bands[0].lower(), 0) * 10) + COLORS.get(bands[1].lower(), 0)
        mult = 10 ** COLORS.get(bands[2].lower(), 0)
        resistance = val * mult
        return {"resistance_ohms": resistance, "formatted": f"{resistance} Ohms"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
