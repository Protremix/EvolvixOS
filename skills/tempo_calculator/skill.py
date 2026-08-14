#!/usr/bin/env python3
"""Tempo & Delay Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        bpm = float(args.get("bpm", 120.0))
        quarter_ms = 60000.0 / bpm
        eighth_ms = quarter_ms / 2.0
        sixteenth_ms = quarter_ms / 4.0
        return {"bpm": bpm, "quarter_note_ms": round(quarter_ms, 2), "eighth_note_ms": round(eighth_ms, 2), "sixteenth_note_ms": round(sixteenth_ms, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
