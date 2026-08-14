#!/usr/bin/env python3
"""Word Counter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        text = args.get("text", "")
        words = re.findall(r'\b\w+\b', text)
        sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        chars_with_spaces = len(text)
        chars_no_spaces = len(re.sub(r'\s+', '', text))
        reading_time_mins = round(len(words) / 200.0, 2)
        return {"words": len(words), "characters_with_spaces": chars_with_spaces, "characters_no_spaces": chars_no_spaces, "sentences": len(sentences), "paragraphs": len(paragraphs), "estimated_reading_time_minutes": reading_time_mins}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
