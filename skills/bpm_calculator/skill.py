#!/usr/bin/env python3
"""BPM Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        beats = float(args.get("beats", 16))
        duration_seconds = float(args.get("duration_seconds", 8.0))
        bpm = (beats / duration_seconds) * 60.0
        return {"bpm": round(bpm, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
