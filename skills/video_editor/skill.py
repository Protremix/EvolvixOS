#!/usr/bin/env python3
"""Video Editor - MoviePy (MIT) - 100% Free"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        action = args.get("action", "info")
        try:
            from moviepy import VideoFileClip, concatenate_videoclips
            if action == "info":
                clip = VideoFileClip(args["file"])
                info = {"duration": clip.duration, "size": clip.size, "fps": clip.fps}
                clip.close()
                return info
            elif action == "cut":
                clip = VideoFileClip(args["file"]).subclip(args["start"], args["end"])
                out = args.get("output", "clip.mp4")
                clip.write_videofile(out, codec="libx264", audio_codec="aac", verbose=False, logger=None)
                clip.close()
                return {"output": out}
            elif action == "merge":
                clips = [VideoFileClip(f) for f in args["files"]]
                final = concatenate_videoclips(clips)
                out = args.get("output", "merged.mp4")
                final.write_videofile(out, codec="libx264", audio_codec="aac", verbose=False, logger=None)
                for c in clips: c.close()
                final.close()
                return {"output": out}
            elif action == "extract_audio":
                clip = VideoFileClip(args["file"])
                out = args.get("output", "audio.wav")
                clip.audio.write_audiofile(out, verbose=False, logger=None)
                clip.close()
                return {"output": out}
            return {"error": f"unknown: {action}"}
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "moviepy"], capture_output=True)
            return self.run(args)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
