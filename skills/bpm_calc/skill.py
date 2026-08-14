#!/usr/bin/env python3
"""BPM Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        bpm = args.get("bpm", 120)
        ms_per_beat = 60000 / bpm
        ms_per_quarter = ms_per_beat
        ms_per_eighth = ms_per_beat / 2
        ms_per_sixteenth = ms_per_beat / 4
        ms_per_half = ms_per_beat * 2
        ms_per_whole = ms_per_beat * 4
        hz = bpm / 60
        return {"bpm": bpm, "ms_per_beat": round(ms_per_beat, 2), "ms_per_quarter": round(ms_per_quarter, 2), "ms_per_eighth": round(ms_per_eighth, 2), "ms_per_sixteenth": round(ms_per_sixteenth, 2), "ms_per_half": round(ms_per_half, 2), "ms_per_whole": round(ms_per_whole, 2), "hz": round(hz, 4)}
