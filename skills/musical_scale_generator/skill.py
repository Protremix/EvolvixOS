#!/usr/bin/env python3
"""Musical Scale Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        root = args.get("root", "C").upper()
        scale_type = args.get("type", "major").lower()
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        idx = notes.index(root) if root in notes else 0
        intervals = [2, 2, 1, 2, 2, 2, 1] if scale_type == "major" else [2, 1, 2, 2, 1, 2, 2]
        res = [notes[idx]]
        curr = idx
        for step in intervals[:-1]:
            curr = (curr + step) % 12
            res.append(notes[curr])
        return {"root": root, "type": scale_type, "notes": res}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
