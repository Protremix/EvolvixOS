"""
EvolvixOS — Audio Skill
Text-to-speech (Kokoro) and music generation (MusicGen). 100% local, zero tokens.
"""

import os
import time
import torch
import numpy as np
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class Skill:
    """Audio skill — TTS and music generation, fully local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/audio"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tts_model = self.config.get("tts_model", "kokoro")
        self.music_model = self.config.get("music_model", "musicgen-small")
        self.sample_rate = self.config.get("sample_rate", 22050)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._tts_pipeline = None
        self._music_pipeline = None

    def text_to_speech(self, text: str, voice: str = "af") -> str:
        """Convert text to speech using Kokoro TTS. Local, zero tokens."""
        console.print(f"[cyan]🔊 Generating speech for: {text[:60]}...[/cyan]")

        if self._tts_pipeline is None:
            console.print("[dim]Loading Kokoro TTS model (first run downloads it)...[/dim]")
            from misaki import espeak_provider
            from misaki import Voice

            # Kokoro — lightweight TTS that runs on CPU, Apache 2.0
            voice = Voice(voice_id=voice, device=self.device)
            self._tts_pipeline = voice

        # Generate audio
        audio = self._tts_pipeline.synthesize(text)

        # Save as WAV
        import soundfile as sf
        filename = self.output_dir / f"tts_{int(time.time())}.wav"
        sf.write(str(filename), audio, self.sample_rate)

        console.print(f"[green]💾 Audio saved: {filename}[/green]")
        return str(filename)

    def generate_music(self, prompt: str, duration_seconds: int = 10) -> str:
        """Generate music from text prompt using MusicGen. Local, zero tokens."""
        console.print(f"[cyan]🎵 Generating music: {prompt[:60]}...[/cyan]")

        if self._music_pipeline is None:
            console.print("[dim]Loading MusicGen model (first run downloads ~2GB)...[/dim]")
            from transformers import MusicgenForConditionalGeneration, AutoProcessor

            model_name = "facebook/musicgen-small" if self.music_model == "musicgen-small" else "facebook/musicgen-medium"
            self._music_pipeline = {
                "model": MusicgenForConditionalGeneration.from_pretrained(model_name).to(self.device),
                "processor": AutoProcessor.from_pretrained(model_name),
            }

        model = self._music_pipeline["model"]
        processor = self._music_pipeline["processor"]

        inputs = processor(text=[prompt], padding=True, return_tensors="pt").to(self.device)

        with torch.inference_mode():
            audio_values = model.generate(
                **inputs,
                max_new_tokens=int(duration_seconds * 50),  # ~50 tokens per second
            )

        audio = audio_values[0, 0].cpu().numpy()
        sampling_rate = model.config.audio_encoder.sampling_rate

        import soundfile as sf
        filename = self.output_dir / f"music_{int(time.time())}.wav"
        sf.write(str(filename), audio, sampling_rate)

        console.print(f"[green]💾 Music saved: {filename}[/green]")
        return str(filename)

    def run(self, args: dict) -> str:
        """Execute the audio skill."""
        action = args.get("action", "tts")

        if action == "tts":
            text = args.get("text", args.get("prompt", ""))
            if not text:
                return "Error: no text provided for TTS."
            result = self.text_to_speech(text, voice=args.get("voice", "af"))
            return f"TTS generated: {result}"

        elif action == "music":
            prompt = args.get("prompt", args.get("text", ""))
            if not prompt:
                return "Error: no prompt provided for music generation."
            duration = args.get("duration", 10)
            result = self.generate_music(prompt, duration)
            return f"Music generated: {result}"

        else:
            return f"Unknown action: {action}. Use 'tts' or 'music'."
