#!/usr/bin/env python3
"""Metronome Click Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        bpm = float(args.get("bpm", 120.0))
        interval_ms = 60000.0 / bpm
        return {"bpm": bpm, "interval_ms": round(interval_ms, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
