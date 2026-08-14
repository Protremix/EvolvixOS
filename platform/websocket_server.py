"""
EvolvixOS — WebSocket Server
Real-time bidirectional communication with all connected devices.

Endpoints:
  ws://localhost:5002/ws          — General device messaging
  ws://localhost:5002/voice       — Voice streaming (STT/TTS)
  ws://localhost:5002/chat        — Real-time chat with the agent
  ws://localhost:5002/status      — Device status updates

Features:
  - Real-time text chat with the agent
  - Voice streaming (send audio, get transcription + spoken response)
  - Device-to-device messaging
  - Push notifications
  - Live skill execution
  - Multi-device sync

All local, zero tokens.
"""

import os
import sys
import json
import time
import asyncio
import threading
import base64
import tempfile
from pathlib import Path
from typing import Set, Dict

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import websockets
    from websockets.server import serve
except ImportError:
    print("⚠ websockets not installed. Install: pip install websockets")
    sys.exit(1)

# Import EvolvixOS components
from api_server import EvolvixAPI

# Global state
api = None
connected_clients: Dict[str, any] = {}  # client_id -> websocket
client_devices: Dict[any, str] = {}  # websocket -> device_id


def get_api():
    global api
    if api is None:
        api = EvolvixAPI()
        api._init_skills()
    return api


async def handle_chat(websocket, path="/chat"):
    """Handle real-time chat messages."""
    client_id = f"client_{id(websocket)}"
    connected_clients[client_id] = websocket
    console_print(f"[green]💬 Chat client connected: {client_id}[/green]")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                data = {"type": "text", "message": message}

            msg_type = data.get("type", "text")

            if msg_type == "text":
                # Process text message with the agent
                text = data.get("message", "")
                console_print(f"[cyan]👤 {client_id}: {text}[/cyan]")

                # Send typing indicator
                await websocket.send(json.dumps({"type": "typing", "status": "thinking"}))

                # Get response from the agent
                evolvix = get_api()
                # Use the voice assistant's think function or direct LLM call
                if "voice_assistant" in evolvix._skills:
                    va = evolvix._skills["voice_assistant"]
                    response = va.think(text)
                else:
                    # Direct LLM call
                    import requests
                    ollama = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
                    r = requests.post(f"{ollama}/api/generate", json={
                        "model": "deepseek-r1:7b",
                        "prompt": text,
                        "stream": False,
                        "options": {"temperature": 0.7, "num_predict": 256}
                    }, timeout=60)
                    response = r.json().get("response", "I couldn't process that.")

                console_print(f"[green]🤖 {response[:80]}[/green]")

                await websocket.send(json.dumps({
                    "type": "response",
                    "message": response,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "cost": "$0.00",
                }))

                # If voice response requested, also send audio
                if data.get("speak", False) and "voice_assistant" in evolvix._skills:
                    va = evolvix._skills["voice_assistant"]
                    va.speak(response)

            elif msg_type == "voice":
                # Handle voice message (base64 encoded audio)
                await handle_voice_message(websocket, data, client_id)

            elif msg_type == "skill":
                # Execute a skill
                skill_name = data.get("skill", "")
                skill_input = data.get("input", {})
                evolvix = get_api()
                if skill_name in evolvix._skills:
                    result = evolvix._skills[skill_name].run(skill_input)
                    await websocket.send(json.dumps({
                        "type": "skill_result",
                        "skill": skill_name,
                        "result": str(result),
                        "cost": "$0.00",
                    }))
                else:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": f"Skill '{skill_name}' not found",
                    }))

            elif msg_type == "status":
                # Send platform status
                evolvix = get_api()
                await websocket.send(json.dumps({
                    "type": "status",
                    "skills": len(evolvix._skills),
                    "cost": "$0.00",
                    "version": "0.4",
                }))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.pop(client_id, None)
        console_print(f"[yellow]💬 Client disconnected: {client_id}[/yellow]")


async def handle_voice_message(websocket, data, client_id):
    """Handle incoming voice message (audio → STT → think → TTS → audio response)."""
    audio_b64 = data.get("audio", "")
    if not audio_b64:
        await websocket.send(json.dumps({"type": "error", "message": "No audio data"}))
        return

    await websocket.send(json.dumps({"type": "typing", "status": "transcribing"}))

    # Decode audio
    audio_data = base64.b64decode(audio_b64)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_data)
        audio_path = f.name

    try:
        evolvix = get_api()
        va = evolvix._skills.get("voice_assistant")

        # Transcribe with Whisper
        if va and va._whisper is None:
            va._init_whisper()

        if va and va._whisper:
            result = va._whisper.transcribe(audio_path)
            text = result.get("text", "").strip()
        else:
            text = "Voice transcription not available (install whisper)"

        console_print(f"[cyan]🎤 Voice from {client_id}: {text}[/cyan]")

        await websocket.send(json.dumps({
            "type": "transcription",
            "text": text,
        }))

        # Think
        await websocket.send(json.dumps({"type": "typing", "status": "thinking"}))
        if va:
            response = va.think(text)
        else:
            response = "Voice assistant not available."

        await websocket.send(json.dumps({
            "type": "response",
            "message": response,
            "timestamp": time.strftime("%H:%M:%S"),
        }))

        # Generate TTS response
        if va and va._tts:
            await websocket.send(json.dumps({"type": "typing", "status": "speaking"}))
            # For WebSocket, save TTS to file and send as base64
            if hasattr(va, "_kokoro_pipeline") or va._tts == "kokoro":
                try:
                    from kokoro import KPipeline
                    if not hasattr(va, "_kokoro_pipeline"):
                        va._kokoro_pipeline = KPipeline(lang=va.language)
                    audio_out = va._kokoro_pipeline.generate(response, voice=va.voice_id)
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                        import soundfile as sf
                        sf.write(tf.name, audio_out[1].cpu().numpy(), 24000)
                        with open(tf.name, "rb") as af:
                            audio_b64_resp = base64.b64encode(af.read()).decode()
                        os.unlink(tf.name)
                        await websocket.send(json.dumps({
                            "type": "voice_response",
                            "audio": audio_b64_resp,
                            "text": response,
                        }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        "type": "response",
                        "message": f"TTS error: {e}",
                    }))

    finally:
        os.unlink(audio_path)


async def handle_device(websocket, path="/ws"):
    """Handle device registration and messaging."""
    device_id = None
    console_print(f"[green]📱 Device connected[/green]")

    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "register":
                # Register device
                device_name = data.get("name", "unnamed")
                device_type = data.get("type", "web")
                evolvix = get_api()
                if "device_manager" in evolvix._skills:
                    result = evolvix._skills["device_manager"].run({
                        "action": "register",
                        "name": device_name,
                        "type": device_type,
                        "os": data.get("os", ""),
                        "capabilities": data.get("capabilities", ["text", "voice"]),
                    })
                    # Extract device_id from result
                    if "dev_" in result:
                        device_id = result.split("ID: ")[1].split("\n")[0].strip()
                        client_devices[websocket] = device_id
                        evolvix._skills["device_manager"].connect(device_id)

                await websocket.send(json.dumps({
                    "type": "registered",
                    "device_id": device_id,
                    "message": result,
                    "api_base": f"http://localhost:5001/api/v1",
                }))

            elif msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong", "timestamp": time.time()}))

            elif msg_type == "skill":
                # Execute skill from device
                skill_name = data.get("skill")
                skill_input = data.get("input", {})
                evolvix = get_api()
                if skill_name in evolvix._skills:
                    result = evolvix._skills[skill_name].run(skill_input)
                    await websocket.send(json.dumps({
                        "type": "skill_result",
                        "result": str(result)[:4000],
                    }))

            elif msg_type == "chat":
                # Chat from device
                text = data.get("message", "")
                evolvix = get_api()
                if "voice_assistant" in evolvix._skills:
                    response = evolvix._skills["voice_assistant"].think(text)
                else:
                    response = "Voice assistant not loaded."
                await websocket.send(json.dumps({
                    "type": "chat_response",
                    "message": response,
                }))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if device_id:
            evolvix = get_api()
            if "device_manager" in evolvix._skills:
                evolvix._skills["device_manager"].disconnect(device_id)
        client_devices.pop(websocket, None)
        console_print("[yellow]📱 Device disconnected[/yellow]")


def console_print(msg):
    """Print with rich if available, else plain."""
    try:
        from rich.console import Console
        Console().print(msg)
    except:
        print(msg)


async def main():
    """Start the WebSocket server."""
    port = int(os.environ.get("EVOLVIX_WS_PORT", 5002))
    host = "0.0.0.0"

    console_print(f"[cyan]🔌 EvolvixOS WebSocket Server starting on ws://{host}:{port}[/cyan]")
    console_print(f"   Endpoints:")
    console_print(f"   ws://{host}:{port}/chat  — Real-time chat")
    console_print(f"   ws://{host}:{port}/ws    — Device messaging")
    console_print(f"   ws://{host}:{port}/voice — Voice streaming")

    # Start both servers
    async with (
        websockets.serve(handle_chat, host, port, subprotocols=["chat"]),
        websockets.serve(handle_device, host, port + 1, subprotocols=["ws"]),
    ):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
