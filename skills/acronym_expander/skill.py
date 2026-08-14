#!/usr/bin/env python3
"""Acronym Expander - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        phrase = args.get("phrase", "")
        words = phrase.split()
        acronym = "".join([w[0].upper() for w in words if w])
        KNOWN = {"API": "Application Programming Interface", "HTTP": "Hypertext Transfer Protocol", "URL": "Uniform Resource Locator", "JSON": "JavaScript Object Notation", "CPU": "Central Processing Unit", "RAM": "Random Access Memory"}
        known_expansion = KNOWN.get(phrase.upper(), "")
        return {"acronym": acronym, "known_expansion": known_expansion}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
