#!/usr/bin/env python3
"""Speed Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        speed = args.get("speed", None)
        distance = args.get("distance", None)
        time = args.get("time", None)
        if speed is None and distance is not None and time is not None:
            speed = distance / time
        elif distance is None and speed is not None and time is not None:
            distance = speed * time
        elif time is None and speed is not None and distance is not None:
            time = distance / speed
        return {"speed": speed, "distance": distance, "time": time}
