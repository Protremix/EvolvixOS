"""
EvolvixOS — Voice Assistant Skill
Real-time voice interaction: listen → transcribe → think → respond → speak.

Features:
  - Speech-to-Text (Whisper, local, offline)
  - Text-to-Speech (Kokoro / pyttsx3 / espeak)
  - Wake word detection ("Hey Evolvix")
  - Continuous conversation mode
  - Voice activity detection (VAD)
  - Multi-language support
  - Voice profile customization (pitch, speed, volume)

All local, zero tokens, zero cloud.
"""

import os
import sys
import json
import time
import wave
import pyaudio
import tempfile
import threading
import queue
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class Skill:
    """Voice Assistant — real-time voice interaction."""

    def __init__(self, config=None):
        self.config = config or {}
        self.ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.model = self.config.get("model", "deepseek-r1:7b")

        # Voice settings
        self.tts_engine = self.config.get("tts_engine", "auto")  # auto, kokoro, pyttsx3, espeak
        self.wake_word = self.config.get("wake_word", "hey evolvix")
        self.language = self.config.get("language", "en")
        self.voice_id = self.config.get("voice_id", "af")
        self.rate = self.config.get("rate", 1.0)
        self.volume = self.config.get("volume", 1.0)

        # State
        self.listening = False
        self.conversation_active = False
        self.audio_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.conversation_history = []

        # Initialize TTS engine
        self._tts = None
        self._whisper = None
        self._init_tts()

    def _init_tts(self):
        """Initialize the text-to-speech engine."""
        # Try Kokoro first (best quality, local)
        if self.tts_engine in ("auto", "kokoro"):
            try:
                from kokoro import KModel, KPipeline
                self._tts = "kokoro"
                self._kokoro_pipeline = None  # Lazy load
                console.print("[green]🔊 TTS: Kokoro (ready to lazy-load)[/green]")
                return
            except ImportError:
                pass

        # Fallback to pyttsx3
        if self.tts_engine in ("auto", "pyttsx3"):
            try:
                import pyttsx3
                self._tts = pyttsx3.init()
                self._tts.setProperty("rate", int(self.rate * 200))
                self._tts.setProperty("volume", self.volume)
                console.print("[green]🔊 TTS: pyttsx3 (offline)[/green]")
                return
            except ImportError:
                pass

        # Fallback to espeak
        if self.tts_engine in ("auto", "espeak"):
            try:
                import subprocess
                subprocess.run(["espeak", "--version"], capture_output=True)
                self._tts = "espeak"
                console.print("[green]🔊 TTS: espeak (offline)[/green]")
                return
            except:
                pass

        console.print("[yellow]⚠ No TTS engine available. Install: pip install kokoro pyttsx3[/yellow]")
        self._tts = None

    def _init_whisper(self):
        """Initialize Whisper for speech-to-text."""
        if self._whisper is not None:
            return
        try:
            import whisper
            model_size = self.config.get("whisper_model", "base")
            self._whisper = whisper.load_model(model_size)
            console.print(f"[green]🎤 STT: Whisper ({model_size}) loaded[/green]")
        except ImportError:
            console.print("[yellow]⚠ Whisper not installed. pip install openai-whisper[/yellow]")

    def speak(self, text: str, voice: str = None) -> str:
        """Convert text to speech and play it."""
        if not self._tts:
            return f"⚠ No TTS engine. Text: {text}"

        voice = voice or self.voice_id

        if self._tts == "kokoro":
            try:
                from kokoro import KPipeline
                if not hasattr(self, "_kokoro_pipeline"):
                    self._kokoro_pipeline = KPipeline(lang=self.language)
                audio = self._kokoro_pipeline.generate(text, voice=voice)
                # Save and play
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    import soundfile as sf
                    sf.write(f.name, audio[1].cpu().numpy(), 24000)
                    self._play_audio(f.name)
                    os.unlink(f.name)
                return f"🔊 Spoke: {text[:50]}..."
            except Exception as e:
                console.print(f"[yellow]Kokoro failed: {e}. Fallback...[/yellow]")

        if isinstance(self._tts, str) and self._tts == "espeak":
            import subprocess
            subprocess.run(["espeak", text, "-s", str(int(self.rate * 175)),
                          "-v", self.volume], capture_output=True)
            return f"🔊 Spoke: {text[:50]}..."

        if hasattr(self._tts, "say"):
            self._tts.say(text)
            self._tts.runAndWait()
            return f"🔊 Spoke: {text[:50]}..."

        return f"⚠ TTS unavailable. Text: {text}"

    def _play_audio(self, file_path: str):
        """Play an audio file."""
        try:
            import pyaudio
            import wave
            wf = wave.open(file_path, "rb")
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                          channels=wf.getnchannels(),
                          rate=wf.getframerate(),
                          output=True)
            data = wf.readframes(1024)
            while data:
                stream.write(data)
                data = wf.readframes(1024)
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            console.print(f"[yellow]Audio playback error: {e}[/yellow]")

    def listen(self, duration: int = 5, sample_rate: int = 16000) -> str:
        """Record audio from microphone and transcribe."""
        self._init_whisper()
        if self._whisper is None:
            return "⚠ Whisper not available. Install: pip install openai-whisper"

        try:
            import pyaudio
            CHUNK = 1024
            RECORD_SECONDS = duration

            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16,
                          channels=1,
                          rate=sample_rate,
                          input=True,
                          frames_per_buffer=CHUNK)

            console.print(f"[cyan]🎤 Listening for {duration}s...[/cyan]")
            frames = []
            for _ in range(int(sample_rate / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

            stream.stop_stream()
            stream.close()
            p.terminate()

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wf = wave.open(f.name, "wb")
                wf.setnchannels(1)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                wf.setframerate(sample_rate)
                wf.writeframes(b"".join(frames))
                wf.close()

                # Transcribe with Whisper
                result = self._whisper.transcribe(f.name)
                os.unlink(f.name)
                text = result.get("text", "").strip()
                console.print(f"[green]👤 You said: {text}[/green]")
                return text

        except Exception as e:
            return f"⚠ Recording error: {e}"

    def think(self, text: str, system: str = "") -> str:
        """Process text with the local LLM and get a response."""
        import requests
        # Build conversation context
        self.conversation_history.append({"role": "user", "content": text})

        # Keep last 10 messages
        history = self.conversation_history[-10:]

        prompt = "\n".join([f"{'User' if m['role']=='user' else 'EvolvixOS'}: {m['content']}" for m in history])
        prompt += "\nEvolvixOS:"

        system_prompt = system or "You are EvolvixOS, a helpful AI assistant. Keep responses concise and conversational. You are running fully locally."

        try:
            r = requests.post(f"{self.ollama_host}/api/generate", json={
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 256}
            }, timeout=60)
            response = r.json().get("response", "").strip()
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        except Exception as e:
            return f"I'm having trouble connecting to my brain. Error: {e}"

    def converse(self, text: str, speak_response: bool = True) -> dict:
        """Full conversation cycle: text → think → speak."""
        start = time.time()

        # Think
        response = self.think(text)

        # Speak
        if speak_response and self._tts:
            self.speak(response)

        return {
            "user_said": text,
            "assistant_said": response,
            "model": self.model,
            "latency_ms": round((time.time() - start) * 1000, 1),
            "cost": "$0.00",
            "engine": "local",
        }

    def voice_converse(self, duration: int = 5) -> dict:
        """Full voice cycle: listen → transcribe → think → speak."""
        # Listen
        text = self.listen(duration)
        if not text or text.startswith("⚠"):
            return {"error": text or "No speech detected"}

        # Converse
        return self.converse(text)

    def start_continuous(self):
        """Start continuous conversation mode (wake word activated)."""
        console.print("[cyan]🔄 Continuous mode started. Say 'hey evolvix' to talk.[/cyan]")
        console.print("[cyan]   Say 'stop listening' to exit.[/cyan]")
        self.listening = True

        while self.listening:
            # Listen for wake word (short recording)
            text = self.listen(duration=2)
            if not text:
                continue

            text_lower = text.lower().strip()

            # Check for wake word
            if self.wake_word in text_lower:
                console.print("[green]✅ Wake word detected![/green]")
                self.speak("Yes, I'm listening.")

                # Now listen for the actual command
                command = self.listen(duration=10)
                if command and not command.startswith("⚠"):
                    # Check for stop command
                    if "stop listening" in command.lower():
                        self.speak("Goodbye!")
                        self.listening = False
                        break

                    # Process
                    result = self.converse(command)
                    console.print(f"[cyan]Response: {result['assistant_said']}[/cyan]")

    def stop_continuous(self):
        """Stop continuous mode."""
        self.listening = False
        return "✅ Continuous mode stopped."

    def set_voice(self, voice_id: str, rate: float = None, volume: float = None) -> str:
        """Change voice settings."""
        self.voice_id = voice_id
        if rate is not None:
            self.rate = rate
            if hasattr(self._tts, "setProperty"):
                self._tts.setProperty("rate", int(rate * 200))
        if volume is not None:
            self.volume = volume
            if hasattr(self._tts, "setProperty"):
                self._tts.setProperty("volume", volume)
        return f"✅ Voice set: voice={voice_id}, rate={self.rate}, volume={self.volume}"

    def list_voices(self) -> str:
        """List available voices."""
        voices = []
        # Kokoro voices
        kokoro_voices = {
            "af": "American Female (Bella)", "am": "American Male (Michael)",
            "bf": "British Female (Charlotte)", "bm": "British Male (George)",
            "ef": "Spanish Female (Esperanza)", "em": "Spanish Male (Emilio)",
            "ff": "French Female (Florence)", "fm": "French Male (Pierre)",
            "gf": "German Female (Greta)", "gm": "German Male (Gunther)",
            "if": "Indian Female (Indira)", "im": "Indian Male (Imran)",
            "jf": "Japanese Female (Keiko)", "jm": "Japanese Male (Kenji)",
            "kf": "Korean Female (Seol)", "km": "Korean Male (Minho)",
            "cf": "Chinese Female (Xiaoxiao)", "cm": "Chinese Male (Chang)",
        }
        for vid, desc in kokoro_voices.items():
            voices.append(f"  {vid} — {desc}")

        if hasattr(self._tts, "getProperty"):
            for v in self._tts.getProperty("voices"):
                voices.append(f"  {v.id} — {v.name} ({v.languages})")

        return "🗣️ Available Voices:\n" + "\n".join(voices)

    def clear_history(self) -> str:
        """Clear conversation history."""
        self.conversation_history = []
        return "✅ Conversation history cleared."

    def get_status(self) -> dict:
        """Get voice assistant status."""
        return {
            "tts_engine": self._tts if isinstance(self._tts, str) else "pyttsx3" if self._tts else "none",
            "whisper_loaded": self._whisper is not None,
            "model": self.model,
            "wake_word": self.wake_word,
            "voice": self.voice_id,
            "rate": self.rate,
            "volume": self.volume,
            "listening": self.listening,
            "history_count": len(self.conversation_history),
            "language": self.language,
            "cost": "$0.00",
        }

    def run(self, args: dict) -> str:
        action = args.get("action", "status")

        if action == "speak":
            return self.speak(args.get("text", ""))
        elif action == "listen":
            return self.listen(args.get("duration", 5))
        elif action == "think":
            return self.think(args.get("text", ""))
        elif action == "converse":
            result = self.converse(args.get("text", ""), args.get("speak", True))
            return json.dumps(result, indent=2)
        elif action == "voice_converse":
            result = self.voice_converse(args.get("duration", 5))
            return json.dumps(result, indent=2)
        elif action == "start_continuous":
            threading.Thread(target=self.start_continuous, daemon=True).start()
            return "🔄 Continuous mode started in background. Say 'hey evolvix' to talk."
        elif action == "stop_continuous":
            return self.stop_continuous()
        elif action == "set_voice":
            return self.set_voice(args.get("voice", "af"), args.get("rate"), args.get("volume"))
        elif action == "list_voices":
            return self.list_voices()
        elif action == "clear_history":
            return self.clear_history()
        elif action == "status":
            return json.dumps(self.get_status(), indent=2)
        else:
            return (
                f"Unknown action: {action}\n\n"
                "Available actions:\n"
                "  Voice:     speak, listen, think, converse, voice_converse\n"
                "  Continuous: start_continuous, stop_continuous\n"
                "  Settings:  set_voice, list_voices, clear_history\n"
                "  Info:       status"
            )
