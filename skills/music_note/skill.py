#!/usr/bin/env python3
"""Music Note Converter — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import math
        action = args.get("action", "note_to_freq")
        notes = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
        reverse = {v: k for k, v in notes.items()}
        if action == "note_to_freq":
            note = args.get("note", "A4")
            n = note[:-1].replace("b", "#")
            octave = int(note[-1])
            semitones = notes.get(n, 9) + (octave - 4) * 12 - 9
            freq = 440 * (2 ** (semitones / 12))
            return {"note": note, "frequency": round(freq, 2), "midi": 69 + semitones}
        elif action == "freq_to_note":
            freq = args.get("frequency", 440)
            midi = round(12 * math.log2(freq / 440) + 69)
            note_num = midi % 12
            octave = (midi // 12) - 1
            note = reverse.get(note_num, "?")
            return {"frequency": freq, "note": f"{note}{octave}", "midi": midi}
        elif action == "midi_to_note":
            midi = args.get("midi", 69)
            note_num = midi % 12
            octave = (midi // 12) - 1
            note = reverse.get(note_num, "?")
            freq = 440 * (2 ** ((midi - 69) / 12))
            return {"midi": midi, "note": f"{note}{octave}", "frequency": round(freq, 2)}
        return {"error": f"unknown: {action}"}
