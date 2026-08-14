#!/usr/bin/env python3
"""Gradient Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        c1 = args.get("color1", "#FF0000")
        c2 = args.get("color2", "#0000FF")
        deg = args.get("degrees", 90)
        css = f"linear-gradient({deg}deg, {c1}, {c2})"
        return {"css_gradient": css}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
