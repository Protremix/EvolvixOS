#!/usr/bin/env python3
"""Chord Transposer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        chords = args.get("chords", ["C", "G", "Am", "F"])
        semitones = int(args.get("semitones", 2))
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        transposed = []
        for c in chords:
            root = c[0]
            if len(c) > 1 and c[1] == '#': root = c[:2]
            mod = c[len(root):]
            if root in notes:
                idx = (notes.index(root) + semitones) % 12
                transposed.append(notes[idx] + mod)
            else: transposed.append(c)
        return {"original": chords, "transposed": transposed, "semitones": semitones}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
