"""
EvolvixOS — Voice Skill
Real voice interaction. Speech-to-text (Whisper, local) + text-to-speech (Kokoro, local).
100% offline, zero tokens, zero external API calls.

Supports:
  - speech_to_text(audio_file) → text
  - text_to_speech(text) → audio file
  - Multiple voices and languages
  - Streaming TTS for long texts
"""

import os
import time
import wave
import tempfile
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class VoiceSkill:
    """Voice skill — real speech-to-text and text-to-speech. Fully local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/audio"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # STT (Speech-to-Text) — Whisper (OpenAI, Apache 2.0, runs locally)
        self.stt_model_name = self.config.get("stt_model", "base")  # tiny, base, small, medium, large
        self._stt_model = None

        # TTS (Text-to-Speech) — Kokoro (Apache 2.0, runs on CPU)
        self.tts_model = self.config.get("tts_model", "kokoro")
        self.default_voice = self.config.get("default_voice", "af")  # af=American female, am=American male, bf=British female, bm=British male
        self.sample_rate = self.config.get("sample_rate", 24000)
        self._tts_model = None

    # === SPEECH TO TEXT ===

    def _load_stt_model(self):
        """Load Whisper model locally. One-time download."""
        if self._stt_model is not None:
            return self._stt_model

        console.print(f"[cyan]🎤 Loading Whisper STT model: {self.stt_model_name}[/cyan]")
        console.print("[dim]First run downloads the model. Then 100% local.[/dim]")

        import whisper  # openai-whisper, Apache 2.0, runs locally
        self._stt_model = whisper.load_model(self.stt_model_name)
        console.print(f"[green]✅ Whisper loaded[/green]")
        return self._stt_model

    def speech_to_text(self, audio_path: str, language: str = None) -> str:
        """Convert audio file to text. 100% local, zero tokens."""
        console.print(f"[cyan]🎤 Transcribing audio: {audio_path}[/cyan]")

        model = self._load_stt_model()

        try:
            options = {}
            if language:
                options["language"] = language

            result = model.transcribe(audio_path, **options)
            text = result["text"].strip()

            console.print(f"[green]✅ Transcribed: {text[:80]}...[/green]")
            return text
        except Exception as e:
            console.print(f"[red]STT error: {e}[/red]")
            return ""

    # === TEXT TO SPEECH ===

    def _load_tts_model(self):
        """Load Kokoro TTS model locally."""
        if self._tts_model is not None:
            return self._tts_model

        console.print(f"[cyan]🔊 Loading Kokoro TTS engine[/cyan]")
        console.print("[dim]Lightweight, runs on CPU. Apache 2.0.[/dim]")

        # Kokoro TTS — best lightweight open-source TTS
        # Uses phonemizer + model, runs entirely locally
        try:
            from kokoro import Kokoro
            self._tts_model = Kokoro()
            console.print(f"[green]✅ Kokoro TTS loaded[/green]")
        except ImportError:
            # Fallback: use pyttsx3 (offline, built into most systems)
            console.print("[yellow]⚠ Kokoro not available, using pyttsx3 fallback[/yellow]")
            try:
                import pyttsx3
                self._tts_model = pyttsx3.init()
                console.print(f"[green]✅ pyttsx3 TTS loaded[/green]")
            except ImportError:
                console.print("[red]No TTS engine available. Install: pip install kokoro or pip install pyttsx3[/red]")
                raise

        return self._tts_model

    def text_to_speech(self, text: str, voice: str = None, output_path: str = None) -> str:
        """Convert text to speech audio file. 100% local, zero tokens."""
        console.print(f"[cyan]🔊 Generating speech: {text[:60]}...[/cyan]")

        if not text.strip():
            return ""

        voice = voice or self.default_voice
        model = self._load_tts_model()

        if output_path is None:
            output_path = str(self.output_dir / f"tts_{int(time.time())}.wav")

        # Kokoro TTS
        if hasattr(model, 'create'):
            import soundfile as sf
            import numpy as np

            # Kokoro returns audio samples
            audio = model.create(text, voice=voice)
            sf.write(output_path, audio, self.sample_rate)

        # pyttsx3 fallback
        elif hasattr(model, 'save_to_file'):
            model.save_to_file(text, output_path)
            model.runAndWait()

        console.print(f"[green]💾 Audio saved: {output_path}[/green]")
        return output_path

    def text_to_speech_stream(self, text: str, voice: str = None):
        """Generator: stream audio chunks for long texts. Local."""
        voice = voice or self.default_voice

        # Split text into sentences for streaming
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sentence in sentences:
            if sentence.strip():
                audio_path = self.text_to_speech(sentence, voice=voice)
                if audio_path:
                    yield audio_path

    def list_voices(self) -> list:
        """List available TTS voices."""
        # Kokoro voices
        kokoro_voices = [
            {"id": "af", "name": "American Female", "lang": "en-US"},
            {"id": "am", "name": "American Male", "lang": "en-US"},
            {"id": "bf", "name": "British Female", "lang": "en-GB"},
            {"id": "bm", "name": "British Male", "lang": "en-GB"},
            {"id": "af_sky", "name": "American Female (Sky)", "lang": "en-US"},
            {"id": "af_bella", "name": "American Female (Bella)", "lang": "en-US"},
            {"id": "am_adam", "name": "American Male (Adam)", "lang": "en-US"},
            {"id": "am_michael", "name": "American Male (Michael)", "lang": "en-US"},
        ]
        return kokoro_voices

    def run(self, args: dict) -> str:
        """Execute the voice skill."""
        action = args.get("action", "tts")

        if action == "stt" or action == "transcribe":
            audio_path = args.get("audio_path", args.get("path", ""))
            if not audio_path:
                return "Error: no audio path provided."
            text = self.speech_to_text(audio_path, language=args.get("language"))
            return f"Transcribed: {text}"

        elif action == "tts" or action == "speak":
            text = args.get("text", args.get("prompt", ""))
            if not text:
                return "Error: no text provided."
            audio_path = self.text_to_speech(text, voice=args.get("voice"))
            return f"Audio generated: {audio_path}"

        elif action == "voices":
            voices = self.list_voices()
            return json.dumps(voices, indent=2) if 'json' in dir() else str(voices)

        else:
            return f"Unknown action: {action}. Use 'tts', 'stt', or 'voices'."


# Skill interface compatibility
Skill = VoiceSkill
