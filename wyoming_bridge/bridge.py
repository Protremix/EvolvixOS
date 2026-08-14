"""
EvolvixOS Wyoming Protocol Bridge.

Bridges Home Assistant's Wyoming protocol to EvolvixOS REST API endpoints.
Implements three Wyoming services in one process:
  - STT service (port 10300): audio → EvolvixOS /api/v1/voice → transcript
  - Conversation service (port 10301): text → EvolvixOS /api/v1/chat → response
  - TTS service (port 10302): text → EvolvixOS /api/v1/audio/tts → audio

Usage:
  python -m wyoming_bridge.bridge --evolvix-url http://localhost:5000
  python -m wyoming_bridge.bridge --evolvix-url http://62.238.61.145:5000 --api-key YOUR_KEY --language ru

Environment variables:
  EVOLVIXOS_URL     Base URL of EvolvixOS server (default: http://localhost:5000)
  EVOLVIX_API_KEY   API key for authentication (optional)
  VOICE_LANGUAGE    Default language code (default: en)
  WYOMING_STT_PORT  STT service port (default: 10300)
  WYOMING_CONV_PORT Conversation service port (default: 10301)
  WYOMING_TTS_PORT  TTS service port (default: 10302)
"""

import argparse
import asyncio
import io
import json
import logging
import os
import struct
import sys
import tempfile
import time
import uuid
import wave
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: pip install requests", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("evolvix-wyoming")

# ─── Wyoming Protocol (minimal implementation) ───────────────────────
# The Wyoming protocol uses TCP with newline-delimited JSON for events
# and raw binary for audio chunks. We implement a minimal version that
# is compatible with Home Assistant's Wyoming integration.

WYOMING_VERSION = "1.0"

# Event types we handle
EVENT_DESCRIBE = "describe"
EVENT_INFO = "info"
EVENT_AUDIO_START = "audio-start"
EVENT_AUDIO_CHUNK = "audio-chunk"
EVENT_AUDIO_STOP = "audio-stop"
EVENT_TRANSCRIPT = "transcript"
EVENT_SYNTHESIZE = "synthesize"
EVENT_AUDIO = "audio"  # binary audio response
EVENT_ERROR = "error"
EVENT_DIALOGUE_START = "dialogue-start"
EVENT_DIALOGUE_TEXT = "dialogue-text"
EVENT_DIALOGUE_END = "dialogue-end"


async def read_wyoming_event(reader: asyncio.StreamReader):
    """Read a single Wyoming event (JSON line) from the stream."""
    line = await reader.readline()
    if not line:
        return None
    try:
        return json.loads(line.decode("utf-8").strip())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


async def read_binary(reader: asyncio.StreamReader, length: int) -> bytes:
    """Read exactly `length` bytes from the stream."""
    data = b""
    while len(data) < length:
        chunk = await reader.read(length - len(data))
        if not chunk:
            break
        data += chunk
    return data


def write_event(writer: asyncio.StreamWriter, event: dict):
    """Write a Wyoming event as a JSON line."""
    writer.write((json.dumps(event) + "\n").encode("utf-8"))


def write_binary(writer: asyncio.StreamWriter, data: bytes):
    """Write raw binary data."""
    writer.write(data)


# ─── EvolvixOS API Client ────────────────────────────────────────────

class EvolvixOSClient:
    """Thin HTTP client for EvolvixOS REST API."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, language: str = "en"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.language = language
        self.session = requests.Session()
        if api_key:
            self.session.headers["X-API-Key"] = api_key
        self._session_id = None

    def health_check(self) -> bool:
        """Check if EvolvixOS is reachable."""
        try:
            r = self.session.get(f"{self.base_url}/api/v1/health", timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def transcribe(self, audio_path: str, language: str = None) -> str:
        """Send audio to EvolvixOS STT endpoint."""
        lang = language or self.language
        with open(audio_path, "rb") as f:
            files = {"audio": (os.path.basename(audio_path), f, "audio/wav")}
            r = self.session.post(
                f"{self.base_url}/api/v1/voice",
                files=files,
                timeout=120,
            )
        r.raise_for_status()
        return r.json().get("text", "").strip()

    def chat(self, message: str, session_id: str = None) -> dict:
        """Send text to EvolvixOS chat endpoint."""
        payload = {"message": message}
        if session_id:
            payload["session_id"] = session_id
        r = self.session.post(
            f"{self.base_url}/api/v1/chat",
            json=payload,
            timeout=180,
        )
        r.raise_for_status()
        return r.json()

    def synthesize(self, text: str, voice: str = "af") -> bytes:
        """Send text to EvolvixOS TTS endpoint, return WAV bytes."""
        r = self.session.post(
            f"{self.base_url}/api/v1/audio/tts",
            json={"text": text, "voice": voice},
            timeout=60,
        )
        r.raise_for_status()
        return r.content

    def voice_session(self, audio_path: str, session_id: str = None, language: str = None) -> dict:
        """Full voice round-trip via /api/v1/voice/session."""
        lang = language or self.language
        with open(audio_path, "rb") as f:
            files = {"audio": (os.path.basename(audio_path), f, "audio/wav")}
            data = {"language": lang}
            if session_id:
                data["session_id"] = session_id
            r = self.session.post(
                f"{self.base_url}/api/v1/voice/session",
                files=files,
                data=data,
                timeout=180,
            )
        r.raise_for_status()
        return r.json()


# ─── STT Service (Wyoming → EvolvixOS /api/v1/voice) ──────────────────

class STTService:
    """Wyoming STT service that forwards audio to EvolvixOS Whisper."""

    def __init__(self, client: EvolvixOSClient, port: int = 10300, language: str = "en"):
        self.client = client
        self.port = port
        self.language = language
        self._server = None

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        logger.info(f"STT: Client connected from {peer}")

        audio_chunks = []
        audio_format = None
        sample_rate = 16000
        channels = 1
        sample_width = 2

        try:
            while True:
                event = await read_wyoming_event(reader)
                if event is None:
                    break

                event_type = event.get("type")

                if event_type == EVENT_DESCRIBE:
                    info = {
                        "type": EVENT_INFO,
                        "stt": {
                            "name": "evolvixos-stt",
                            "description": "EvolvixOS Whisper STT via Wyoming bridge",
                            "languages": [self.language, "en", "ru"],
                            "samples_per_chunk": 1024,
                        },
                        "version": WYOMING_VERSION,
                    }
                    write_event(writer, info)
                    await writer.drain()

                elif event_type == EVENT_AUDIO_START:
                    audio_format = event.get("audio_format", {})
                    sample_rate = audio_format.get("sample_rate", 16000)
                    channels = audio_format.get("channels", 1)
                    sample_width = audio_format.get("sample_width", 2)
                    audio_chunks = []
                    logger.info(f"STT: Audio start (rate={sample_rate}, ch={channels}, width={sample_width})")

                elif event_type == EVENT_AUDIO_CHUNK:
                    # Read binary audio data
                    chunk_length = event.get("length", 0)
                    if chunk_length > 0:
                        # Read the binary data that follows the JSON event
                        audio_data = await read_binary(reader, chunk_length)
                        audio_chunks.append(audio_data)

                elif event_type == EVENT_AUDIO_STOP:
                    logger.info(f"STT: Audio stop, {len(audio_chunks)} chunks received")

                    # Assemble WAV file
                    raw_audio = b"".join(audio_chunks)
                    temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                    try:
                        with wave.open(temp_wav.name, "wb") as wf:
                            wf.setnchannels(channels)
                            wf.setsampwidth(sample_width)
                            wf.setframerate(sample_rate)
                            wf.writeframes(raw_audio)

                        # Send to EvolvixOS for transcription
                        transcript = self.client.transcribe(temp_wav.name, language=self.language)
                        logger.info(f"STT: Transcript = '{transcript}'")

                        # Send transcript back to HA
                        write_event(writer, {
                            "type": EVENT_TRANSCRIPT,
                            "text": transcript,
                        })
                        await writer.drain()

                    finally:
                        os.unlink(temp_wav.name)

        except Exception as e:
            logger.error(f"STT: Error: {e}")
            try:
                write_event(writer, {"type": EVENT_ERROR, "text": str(e)})
                await writer.drain()
            except Exception:
                pass
        finally:
            writer.close()
            logger.info(f"STT: Client disconnected from {peer}")

    async def start(self):
        self._server = await asyncio.start_server(
            self.handle_client, "0.0.0.0", self.port
        )
        logger.info(f"STT service listening on port {self.port}")

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()


# ─── Conversation Service (Wyoming → EvolvixOS /api/v1/chat) ─────────

class ConversationService:
    """Wyoming conversation service that forwards to EvolvixOS AgentCore."""

    def __init__(self, client: EvolvixOSClient, port: int = 10301, language: str = "en"):
        self.client = client
        self.port = port
        self.language = language
        self._server = None
        self._sessions = {}  # Maps HA conversation ID to EvolvixOS session_id

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        logger.info(f"Conversation: Client connected from {peer}")

        try:
            while True:
                event = await read_wyoming_event(reader)
                if event is None:
                    break

                event_type = event.get("type")

                if event_type == EVENT_DESCRIBE:
                    info = {
                        "type": EVENT_INFO,
                        "conversation": {
                            "name": "evolvixos-conversation",
                            "description": "EvolvixOS AgentCore via Wyoming bridge",
                            "languages": [self.language, "en", "ru"],
                        },
                        "version": WYOMING_VERSION,
                    }
                    write_event(writer, info)
                    await writer.drain()

                elif event_type == EVENT_DIALOGUE_START:
                    conv_id = event.get("conversation_id", str(uuid.uuid4()))
                    self._sessions[conv_id] = event.get("session_id")
                    logger.info(f"Conversation: Dialogue start (conv_id={conv_id})")

                elif event_type == EVENT_DIALOGUE_TEXT:
                    text = event.get("text", "")
                    conv_id = event.get("conversation_id", "")
                    session_id = self._sessions.get(conv_id)

                    logger.info(f"Conversation: Text = '{text}' (session={session_id})")

                    # Forward to EvolvixOS chat
                    result = self.client.chat(text, session_id=session_id)
                    response_text = result.get("response", "")

                    # Update session ID
                    new_session_id = result.get("session_id")
                    if new_session_id:
                        self._sessions[conv_id] = new_session_id

                    logger.info(f"Conversation: Response = '{response_text[:100]}'")

                    # Send response back to HA
                    write_event(writer, {
                        "type": EVENT_DIALOGUE_TEXT,
                        "text": response_text,
                        "conversation_id": conv_id,
                    })
                    await writer.drain()

                elif event_type == EVENT_DIALOGUE_END:
                    conv_id = event.get("conversation_id", "")
                    logger.info(f"Conversation: Dialogue end (conv_id={conv_id})")

        except Exception as e:
            logger.error(f"Conversation: Error: {e}")
            try:
                write_event(writer, {"type": EVENT_ERROR, "text": str(e)})
                await writer.drain()
            except Exception:
                pass
        finally:
            writer.close()
            logger.info(f"Conversation: Client disconnected from {peer}")

    async def start(self):
        self._server = await asyncio.start_server(
            self.handle_client, "0.0.0.0", self.port
        )
        logger.info(f"Conversation service listening on port {self.port}")

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()


# ─── TTS Service (Wyoming → EvolvixOS /api/v1/audio/tts) ─────────────

class TTSService:
    """Wyoming TTS service that forwards to EvolvixOS Kokoro TTS."""

    def __init__(self, client: EvolvixOSClient, port: int = 10302, voice: str = "af"):
        self.client = client
        self.port = port
        self.voice = voice
        self._server = None

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        logger.info(f"TTS: Client connected from {peer}")

        try:
            while True:
                event = await read_wyoming_event(reader)
                if event is None:
                    break

                event_type = event.get("type")

                if event_type == EVENT_DESCRIBE:
                    info = {
                        "type": EVENT_INFO,
                        "tts": {
                            "name": "evolvixos-tts",
                            "description": "EvolvixOS Kokoro TTS via Wyoming bridge",
                            "voices": [
                                {"id": "af", "name": "American Female", "language": "en"},
                                {"id": "am", "name": "American Male", "language": "en"},
                                {"id": "bf", "name": "British Female", "language": "en"},
                                {"id": "bm", "name": "British Male", "language": "en"},
                            ],
                            "sample_rate": 24000,
                        },
                        "version": WYOMING_VERSION,
                    }
                    write_event(writer, info)
                    await writer.drain()

                elif event_type == EVENT_SYNTHESIZE:
                    text = event.get("text", "")
                    voice = event.get("voice", self.voice)
                    raw_audio_format = event.get("audio_format", {})

                    logger.info(f"TTS: Synthesize '{text[:80]}' (voice={voice})")

                    # Call EvolvixOS TTS
                    wav_bytes = self.client.synthesize(text, voice=voice)

                    # Parse WAV to get raw PCM
                    wf = wave.open(io.BytesIO(wav_bytes), "rb")
                    sample_rate = wf.getframerate()
                    channels = wf.getnchannels()
                    sample_width = wf.getsampwidth()
                    raw_pcm = wf.readframes(wf.getnframes())
                    wf.close()

                    # Send audio-start event
                    write_event(writer, {
                        "type": EVENT_AUDIO_START,
                        "audio_format": {
                            "sample_rate": sample_rate,
                            "channels": channels,
                            "sample_width": sample_width,
                        },
                    })
                    await writer.drain()

                    # Send audio in chunks (1024 samples per chunk)
                    chunk_size = 1024 * sample_width * channels
                    offset = 0
                    while offset < len(raw_pcm):
                        chunk = raw_pcm[offset:offset + chunk_size]
                        write_event(writer, {
                            "type": EVENT_AUDIO_CHUNK,
                            "length": len(chunk),
                        })
                        await writer.drain()
                        write_binary(writer, chunk)
                        await writer.drain()
                        offset += chunk_size

                    # Send audio-stop
                    write_event(writer, {"type": EVENT_AUDIO_STOP})
                    await writer.drain()
                    logger.info(f"TTS: Sent {len(raw_pcm)} bytes of audio")

        except Exception as e:
            logger.error(f"TTS: Error: {e}")
            try:
                write_event(writer, {"type": EVENT_ERROR, "text": str(e)})
                await writer.drain()
            except Exception:
                pass
        finally:
            writer.close()
            logger.info(f"TTS: Client disconnected from {peer}")

    async def start(self):
        self._server = await asyncio.start_server(
            self.handle_client, "0.0.0.0", self.port
        )
        logger.info(f"TTS service listening on port {self.port}")

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()


# ─── Main Bridge Runner ──────────────────────────────────────────────

async def run_bridge(
    evolvix_url: str,
    api_key: Optional[str] = None,
    language: str = "en",
    stt_port: int = 10300,
    conv_port: int = 10301,
    tts_port: int = 10302,
    voice: str = "af",
):
    """Run all three Wyoming bridge services concurrently."""
    client = EvolvixOSClient(evolvix_url, api_key=api_key, language=language)

    # Health check
    logger.info(f"Connecting to EvolvixOS at {evolvix_url}...")
    if client.health_check():
        logger.info("✅ EvolvixOS is healthy")
    else:
        logger.warning("⚠ EvolvixOS health check failed — bridge will still start")

    stt = STTService(client, port=stt_port, language=language)
    conv = ConversationService(client, port=conv_port, language=language)
    tts = TTSService(client, port=tts_port, voice=voice)

    await stt.start()
    await conv.start()
    await tts.start()

    logger.info("🧬 EvolvixOS Wyoming Bridge is running")
    logger.info(f"   STT:          port {stt_port}")
    logger.info(f"   Conversation: port {conv_port}")
    logger.info(f"   TTS:          port {tts_port}")
    logger.info(f"   Language:     {language}")
    logger.info(f"   EvolvixOS:   {evolvix_url}")
    logger.info("Press Ctrl+C to stop")

    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await stt.stop()
        await conv.stop()
        await tts.stop()
        logger.info("Bridge stopped")


def main():
    parser = argparse.ArgumentParser(description="EvolvixOS Wyoming Bridge")
    parser.add_argument("--evolvix-url", default=os.environ.get("EVOLVIXOS_URL", "http://localhost:5000"),
                        help="EvolvixOS base URL")
    parser.add_argument("--api-key", default=os.environ.get("EVOLVIX_API_KEY", ""),
                        help="API key for EvolvixOS")
    parser.add_argument("--language", default=os.environ.get("VOICE_LANGUAGE", "en"),
                        help="Default language code (en, ru, etc.)")
    parser.add_argument("--voice", default=os.environ.get("TTS_VOICE", "af"),
                        help="Default TTS voice")
    parser.add_argument("--stt-port", type=int, default=int(os.environ.get("WYOMING_STT_PORT", "10300")),
                        help="STT service TCP port")
    parser.add_argument("--conv-port", type=int, default=int(os.environ.get("WYOMING_CONV_PORT", "10301")),
                        help="Conversation service TCP port")
    parser.add_argument("--tts-port", type=int, default=int(os.environ.get("WYOMING_TTS_PORT", "10302")),
                        help="TTS service TCP port")
    args = parser.parse_args()

    asyncio.run(run_bridge(
        evolvix_url=args.evolvix_url,
        api_key=args.api_key or None,
        language=args.language,
        stt_port=args.stt_port,
        conv_port=args.conv_port,
        tts_port=args.tts_port,
        voice=args.voice,
    ))


if __name__ == "__main__":
    main()
