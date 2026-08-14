#!/usr/bin/env python3
"""MIDI Note Converter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        midi = int(args.get("midi_number", 60))
        names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        note_name = names[midi % 12]
        octave = (midi // 12) - 1
        freq = 440.0 * (2.0 ** ((midi - 69) / 12.0))
        return {"midi_number": midi, "note_name": f"{note_name}{octave}", "frequency_hz": round(freq, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
