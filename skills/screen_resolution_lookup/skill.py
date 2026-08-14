#!/usr/bin/env python3
"""Screen Resolution Lookup - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        name = args.get("resolution", "1080p").lower()
        SPECS = {"720p": {"width": 1280, "height": 720}, "1080p": {"width": 1920, "height": 1080}, "1440p": {"width": 2560, "height": 1440}, "4k": {"width": 3840, "height": 2160}}
        return SPECS.get(name, {"width": 1920, "height": 1080})

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
