#!/usr/bin/env python3
"""Language Detector - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "").lower()
        if "the" in text or "is" in text: lang = "en"
        elif "el" in text or "la" in text or "de" in text: lang = "es"
        elif "le" in text or "la" in text or "et" in text: lang = "fr"
        else: lang = "en"
        return {"detected_language": lang}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
