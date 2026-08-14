#!/usr/bin/env python3
"""Grammar Checker - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        issues = []
        if not text:
            return {"error": "text is required"}
        words = text.split()
        for i in range(len(words)-1):
            if words[i].lower() == words[i+1].lower() and len(words[i]) > 1:
                issues.append(f"Repeated word: '{words[i]}'")
        if text and not text[0].isupper():
            issues.append("Sentence should start with a capital letter.")
        if "  " in text:
            issues.append("Contains double spaces.")
        if text and text[-1] not in ".!?":
            issues.append("Missing end punctuation.")
        return {"original": text, "issues": issues, "issue_count": len(issues)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
