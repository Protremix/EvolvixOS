#!/usr/bin/env python3
"""Text Formatter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import textwrap
        text = args.get("text", "")
        width = int(args.get("width", 80))
        indent = args.get("indent", "")
        if not text:
            return {"error": "text is required"}
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        formatted = "\n\n".join([textwrap.fill(p, width=width, initial_indent=indent, subsequent_indent=indent) for p in paragraphs])
        return {"formatted": formatted, "paragraph_count": len(paragraphs)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
