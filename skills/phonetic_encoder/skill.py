#!/usr/bin/env python3
"""Phonetic Encoder (Soundex) - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        word = args.get("word", "Smith").upper()
        if not word: return {"soundex": "0000"}
        code = word[0]
        mapping = {"BFPV": "1", "CGJKQSXZ": "2", "DT": "3", "L": "4", "MN": "5", "R": "6"}
        for char in word[1:]:
            for keys, digit in mapping.items():
                if char in keys:
                    if digit != code[-1]: code += digit
                    break
        code = (code + "0000")[:4]
        return {"word": word, "soundex": code}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
