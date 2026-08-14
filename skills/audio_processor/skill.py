"""
EvolvixOS — Audio Processor Skill
Process audio: trim, merge, convert, speed, volume, effects.
100% local using pydub + ffmpeg. Zero tokens.

Pip: pip install pydub (also requires ffmpeg installed)
License: MIT (pydub), LGPL (ffmpeg)
"""

import os
import time
import json
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class Skill:
    """Audio processor — trim, merge, convert, effects. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/audio_processed"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, args: dict) -> str:
        action = args.get("action", "info")

        if action == "info":
            return self.audio_info(args.get("file", ""))
        elif action == "trim":
            return self.trim(args.get("file", ""), args.get("start", 0),
                             args.get("end", 30))
        elif action == "merge":
            return self.merge(args.get("files", []))
        elif action == "convert":
            return self.convert(args.get("file", ""), args.get("to_format", "mp3"))
        elif action == "speed":
            return self.speed(args.get("file", ""), args.get("rate", 1.5))
        elif action == "volume":
            return self.change_volume(args.get("file", ""), args.get("db", 10))
        elif action == "fade_in":
            return self.fade_in(args.get("file", ""), args.get("duration", 2000))
        elif action == "fade_out":
            return self.fade_out(args.get("file", ""), args.get("duration", 2000))
        elif action == "reverse":
            return self.reverse(args.get("file", ""))
        elif action == "normalize":
            return self.normalize(args.get("file", ""))
        elif action == "split":
            return self.split(args.get("file", ""), args.get("segment_seconds", 60))
        else:
            return (f"Unknown action: {action}. Use: info, trim, merge, convert, "
                    "speed, volume, fade_in, fade_out, reverse, normalize, split")

    def audio_info(self, file_path: str) -> str:
        try:
            from pydub.utils import mediainfo
            info = mediainfo(file_path)
            result = {
                "file": file_path,
                "duration_seconds": round(float(info.get("duration", 0)), 1),
                "bit_rate": info.get("bit_rate", "unknown"),
                "format": info.get("format_name", "unknown"),
                "channels": info.get("channels", "unknown"),
                "sample_rate": info.get("sample_rate", "unknown"),
                "file_size_kb": round(os.path.getsize(file_path) / 1024, 1),
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {e}\n(Requires ffmpeg: sudo apt install ffmpeg)"

    def trim(self, file_path: str, start: float = 0, end: float = 30) -> str:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            trimmed = audio[int(start * 1000):int(end * 1000)]
            out = self.output_dir / f"trimmed_{int(time.time())}.mp3"
            trimmed.export(str(out), format="mp3")
            return f"Trimmed {start}s-{end}s: {out}"
        except Exception as e:
            return f"Error: {e}"

    def merge(self, files: List[str]) -> str:
        try:
            from pydub import AudioSegment
            combined = AudioSegment.empty()
            for f in files:
                if os.path.exists(f):
                    combined += AudioSegment.from_file(f)
            out = self.output_dir / f"merged_{int(time.time())}.mp3"
            combined.export(str(out), format="mp3")
            return f"Merged {len(files)} files → {out}"
        except Exception as e:
            return f"Error: {e}"

    def convert(self, file_path: str, to_format: str = "mp3") -> str:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            base = Path(file_path).stem
            out = self.output_dir / f"{base}.{to_format}"
            audio.export(str(out), format=to_format)
            return f"Converted: {out}"
        except Exception as e:
            return f"Error: {e}"

    def speed(self, file_path: str, rate: float = 1.5) -> str:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            altered = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * rate)
            }).set_frame_rate(audio.frame_rate)
            out = self.output_dir / f"speed_{rate}x_{int(time.time())}.mp3"
            altered.export(str(out), format="mp3")
            return f"Speed {rate}x: {out}"
        except Exception as e:
            return f"Error: {e}"

    def change_volume(self, file_path: str, db: float = 10) -> str:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path) + db
            out = self.output_dir / f"volume_{db}db_{int(time.time())}.mp3"
            audio.export(str(out), format="mp3")
            return f"Volume +{db}dB: {out}"
        except Exception as e:
            return f"Error: {e}"

    def fade_in(self, file_path: str, duration: int = 2000) -> str:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path).fade_in(duration)
            out = self.output_dir / f"fadein_{int(time.time())}.mp3"
            audio.export(str(out), format="mp3")
            return f"Fade in: {out}"
        except Exception as e:
            return f"Error: {e}"

    def fade_out(self, file_path: str, duration: int = 2000) -> str:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path).fade_out(duration)
            out = self.output_dir / f"fadeout_{int(time.time())}.mp3"
            audio.export(str(out), format="mp3")
            return f"Fade out: {out}"
        except Exception as e:
            return f"Error: {e}"

    def reverse(self, file_path: str) -> str:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path).reverse()
            out = self.output_dir / f"reversed_{int(time.time())}.mp3"
            audio.export(str(out), format="mp3")
            return f"Reversed: {out}"
        except Exception as e:
            return f"Error: {e}"

    def normalize(self, file_path: str) -> str:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            normalized = audio.apply_gain(-audio.max_dBFS)
            out = self.output_dir / f"normalized_{int(time.time())}.mp3"
            normalized.export(str(out), format="mp3")
            return f"Normalized: {out}"
        except Exception as e:
            return f"Error: {e}"

    def split(self, file_path: str, segment_seconds: int = 60) -> str:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            segment_ms = segment_seconds * 1000
            results = []
            for i, start in enumerate(range(0, len(audio), segment_ms)):
                segment = audio[start:start + segment_ms]
                out = self.output_dir / f"{Path(file_path).stem}_part_{i+1}.mp3"
                segment.export(str(out), format="mp3")
                results.append(str(out))
            return f"Split into {len(results)} segments of {segment_seconds}s each"
        except Exception as e:
            return f"Error: {e}"
