#!/usr/bin/env python3
"""Audio Editor - pydub (MIT) - 100% Free"""
import json, sys, subprocess, os


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        action = args.get("action", "info")
        try:
            from pydub import AudioSegment
            if action == "info":
                a = AudioSegment.from_file(args["file"])
                return {"duration_sec": len(a)/1000, "channels": a.channels, "sample_rate": a.frame_rate}
            elif action == "cut":
                a = AudioSegment.from_file(args["file"])
                clip = a[args.get("start_ms",0):args.get("end_ms",len(a))]
                out = args.get("output", "clip.wav")
                clip.export(out, format="wav")
                return {"output": out, "duration_sec": len(clip)/1000}
            elif action == "merge":
                segments = [AudioSegment.from_file(f) for f in args["files"]]
                combined = sum(segments)
                out = args.get("output", "merged.wav")
                combined.export(out, format="wav")
                return {"output": out}
            elif action == "convert":
                a = AudioSegment.from_file(args["file"])
                fmt = args.get("format", "mp3")
                out = os.path.splitext(args["file"])[0] + "." + fmt
                a.export(out, format=fmt)
                return {"output": out}
            return {"error": f"unknown: {action}"}
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pydub"], capture_output=True)
            return self.run(args)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
