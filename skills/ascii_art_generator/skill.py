#!/usr/bin/env python3
"""ASCII Art Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "HI").upper()
        banners = {"H": "█   █\n█████\n█   █", "I": "███\n yI \n███"}
        res = [banners.get(c, c) for c in text]
        return {"ascii_banner": "\n\n".join(res)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
