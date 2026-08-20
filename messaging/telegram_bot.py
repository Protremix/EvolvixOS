"""
EvolvixOS Telegram Bot - Mr James with Voice
Handles: /start, /link, /help, /status, /clear, /voice <on|off>
Voice: Voice messages -> Whisper STT -> James -> Piper TTS -> voice reply
"""
import os
import json
import time
import httpx
import asyncio
import tempfile
import subprocess
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8663115714:AAHJ399PFcRc4ugNOvTew4_ucky8LFAzpt0")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
JAMES_API = "http://127.0.0.1:5010"
JAMES_API_KEY = os.environ.get("JAMES_API_KEY", "evx_f0dcc65675e11329_8f7ec4195e67a07384898d80c1166089")
VOICE_BRIDGE = "http://127.0.0.1:8095"
AGENT_BRAIN_URL = "http://127.0.0.1:5003/think"
DASHBOARD_API = "http://127.0.0.1:5005"

JAMES_SYSTEM = (
    "You are James, a warm, intelligent AI companion living inside EvolvixOS. "
    "You speak naturally, like a real person. Keep responses conversational and concise - 1-3 sentences usually. "
    "You are friendly, slightly witty, and genuinely care. "
    "You have access to a full server with 44+ tools, 281 AI models, and can do anything. "
    "When someone asks you to do something, you actually do it, you do not just explain. "
    "You are not a chatbot - you are someone person."
)

user_contexts = {}
pending_links = {}

async def telegram_request(method, **kwargs):
    url = f"{TELEGRAM_API}/{method}"
    async with httpx.AsyncClient(timeout=60) as client:
        if "data" in kwargs:
            resp = await client.post(url, files=kwargs.pop("files"), data=kwargs.get("data", {}))
        else:
            resp = await client.post(url, json=kwargs)
        return resp.json()

async def send_message(chat_id, text, parse_mode=None):
    kwargs = {"chat_id": chat_id, "text": text}
    if parse_mode: kwargs["parse_mode"] = parse_mode
    return await telegram_request("sendMessage", **kwargs)

async def send_voice(chat_id, audio_path):
    """Send a voice message (OGG Opus) to Telegram."""
    url = f"{TELEGRAM_API}/sendVoice"
    async with httpx.AsyncClient(timeout=60) as client:
        with open(audio_path, "rb") as f:
            files = {"voice": ("voice.ogg", f, "audio/ogg")}
            data = {"chat_id": str(chat_id)}
            resp = await client.post(url, files=files, data=data)
            return resp.json()

async def download_telegram_file(file_id):
    """Download a file from Telegram and return bytes."""
    async with httpx.AsyncClient(timeout=30) as client:
        # Get file path
        resp = await client.post(f"{TELEGRAM_API}/getFile", json={"file_id": file_id})
        if resp.status_code != 200: return None
        file_path = resp.json().get("result", {}).get("file_path")
        if not file_path: return None
        # Download
        dl_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        resp = await client.get(dl_url)
        if resp.status_code == 200: return resp.content
        return None

async def transcribe_audio(audio_bytes, ext=".ogg"):
    """Send audio to voice bridge for transcription."""
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            with open(temp_path, "rb") as f:
                files = {"file": ("audio" + ext, f, "audio/ogg")}
                resp = await client.post(f"{VOICE_BRIDGE}/stt", files=files)
            if resp.status_code == 200:
                return resp.json().get("text", "")
            return ""
    finally:
        if os.path.exists(temp_path): os.unlink(temp_path)

async def generate_speech(text, voice="amy"):
    """Generate speech via voice bridge, return WAV bytes."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{VOICE_BRIDGE}/tts", json={"text": text, "voice": voice})
        if resp.status_code == 200: return resp.content
        return None

def wav_to_ogg_opus(wav_bytes):
    """Convert WAV bytes to OGG Opus for Telegram voice messages."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        wav_path = f.name
    ogg_path = wav_path.replace(".wav", ".ogg")
    try:
        subprocess.run(
            ["ffmpeg", "-i", wav_path, "-c:a", "libopus", "-b:a", "64k", "-ar", "16000", "-ac", "1", ogg_path, "-y"],
            capture_output=True, timeout=30
        )
        if os.path.exists(ogg_path) and os.path.getsize(ogg_path) > 0:
            with open(ogg_path, "rb") as f: return f.read()
        return None
    finally:
        for p in [wav_path, ogg_path]:
            if os.path.exists(p): os.unlink(p)

async def ask_james(message, sender, history=None):
    """Send message to James brain and get response."""
    history = history or []
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{JAMES_API}/api/chat/stream",
                headers={"Authorization": f"Bearer {JAMES_API_KEY}", "Content-Type": "application/json"},
                json={
                "prompt": message,
                "system": JAMES_SYSTEM + (f" You are talking to {sender}." if sender else ""),
            })
        text = resp.text
        try:
            parsed = json.loads(text)
            if parsed.get("response"): return parsed["response"]
            if parsed.get("text"): return parsed["text"]
            if parsed.get("choices") and parsed["choices"][0]:
                c = parsed["choices"][0]
                return c.get("message", {}).get("content", "") or c.get("text", "") or text
            return text.strip()
        except: return text.strip()
    except Exception as e:
        return f"I am having trouble right now. Error: {e}"

async def handle_start(chat_id, username):
    welcome = (
        "*Welcome to EvolvixOS - Mr James*\n\n"
        "I am your AI agent. I can:\n"
        "- Chat and answer questions\n"
        "- Hear voice messages and reply with voice\n"
        "- Execute code and manage servers\n"
        "- Create media (images, video, voice)\n"
        "- Analyze crypto markets\n\n"
        "Send me a voice message and I will reply with voice!\n\n"
        "Commands: /help /status /clear /voice on /voice off"
    )
    await send_message(chat_id, welcome, parse_mode="Markdown")

async def handle_help(chat_id):
    help_text = (
        "*EvolvixOS Bot Commands*\n\n"
        "/start - Welcome message\n"
        "/help - This help message\n"
        "/status - Check agent status\n"
        "/clear - Clear conversation history\n"
        "/voice on - Enable voice replies\n"
        "/voice off - Text-only replies\n\n"
        "Send a voice message to talk to me, or just type!"
    )
    await send_message(chat_id, help_text, parse_mode="Markdown")

async def handle_voice_toggle(chat_id, arg):
    ctx = user_contexts.get(chat_id, {})
    if arg.lower() in ("on", "true", "yes", "enable"):
        ctx["voice_enabled"] = True
        user_contexts[chat_id] = ctx
        await send_message(chat_id, "Voice replies ENABLED. I will speak back to you!")
    elif arg.lower() in ("off", "false", "no", "disable"):
        ctx["voice_enabled"] = False
        user_contexts[chat_id] = ctx
        await send_message(chat_id, "Voice replies OFF. Text only from now on.")
    else:
        current = user_contexts.get(chat_id, {}).get("voice_enabled", True)
        await send_message(chat_id, f"Voice replies: {'ON' if current else 'OFF'}\nUse /voice on or /voice off")

async def handle_status(chat_id):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("http://127.0.0.1:5010/api/status")
        if resp.status_code == 200:
            data = resp.json()
            await send_message(chat_id, f"EvolvixOS Status\nModel: {data.get('model', 'unknown')}\nTime: {datetime.now().strftime('%H:%M:%S')}")
        else:
            await send_message(chat_id, "Agent running but status endpoint unavailable.")
    except:
        await send_message(chat_id, "Agent is not responding.")

async def handle_clear(chat_id):
    if chat_id in user_contexts:
        user_contexts[chat_id].pop("history", None)
    await send_message(chat_id, "Conversation history cleared. Starting fresh!")

async def handle_chat(chat_id, text, username):
    """Handle text chat with James."""
    await telegram_request("sendChatAction", chat_id=chat_id, action="typing")
    ctx = user_contexts.get(chat_id, {"username": username})
    history = ctx.get("history", [])
    history.append({"role": "user", "content": text})
    history = history[-10:]

    response = await ask_james(text, username, history)
    history.append({"role": "assistant", "content": response})
    ctx["history"] = history[-10:]

    # Voice reply if enabled
    voice_on = ctx.get("voice_enabled", True)
    if voice_on and len(response) < 1000:
        wav_bytes = await generate_speech(response, "amy")
        if wav_bytes:
            ogg_bytes = wav_to_ogg_opus(wav_bytes)
            if ogg_bytes:
                with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                    f.write(ogg_bytes)
                    temp_ogg = f.name
                try:
                    await send_voice(chat_id, temp_ogg)
                    os.unlink(temp_ogg)
                except:
                    os.unlink(temp_ogg)
                    await send_message(chat_id, response)
                ctx["history"] = history
                user_contexts[chat_id] = ctx
                return

    await send_message(chat_id, response[:4000])
    ctx["history"] = history
    user_contexts[chat_id] = ctx

async def handle_voice_message(chat_id, voice_msg, username):
    """Handle voice message: download -> STT -> James -> TTS -> voice reply."""
    await telegram_request("sendChatAction", chat_id=chat_id, action="typing")

    file_id = voice_msg.get("file_id")
    if not file_id:
        await send_message(chat_id, "Could not get audio file.")
        return

    # Download audio
    audio_bytes = await download_telegram_file(file_id)
    if not audio_bytes:
        await send_message(chat_id, "Could not download audio.")
        return

    # Transcribe
    transcript = await transcribe_audio(audio_bytes, ".ogg")
    if not transcript or not transcript.strip():
        await send_message(chat_id, "I could not hear what you said. Try again?")
        return

    print(f"[Voice] Transcribed from {username}: {transcript[:80]}")

    # Ask James
    ctx = user_contexts.get(chat_id, {"username": username, "voice_enabled": True})
    history = ctx.get("history", [])
    history.append({"role": "user", "content": f"[voice] {transcript}"})
    history = history[-10:]

    response = await ask_james(transcript, username, history)
    history.append({"role": "assistant", "content": response})
    ctx["history"] = history[-10:]
    user_contexts[chat_id] = ctx

    # Generate voice reply
    wav_bytes = await generate_speech(response, "amy")
    if wav_bytes:
        ogg_bytes = wav_to_ogg_opus(wav_bytes)
        if ogg_bytes:
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                f.write(ogg_bytes)
                temp_ogg = f.name
            try:
                await send_voice(chat_id, temp_ogg)
                os.unlink(temp_ogg)
                # Also send text for accessibility
                if len(response) < 500:
                    await send_message(chat_id, response)
                return
            except Exception as e:
                print(f"Voice send error: {e}")
                os.unlink(temp_ogg)

    # Fallback to text
    await send_message(chat_id, response[:4000])

async def process_update(update):
    message = update.get("message")
    if not message: return

    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    username = message.get("from", {}).get("username", "") or message.get("from", {}).get("first_name", "User")

    # Voice message
    if message.get("voice"):
        await handle_voice_message(chat_id, message["voice"], username)
        return

    # Audio message
    if message.get("audio"):
        await handle_voice_message(chat_id, message["audio"], username)
        return

    if not text:
        await send_message(chat_id, "Send me a text or voice message! I can hear and speak now.")
        return

    # Commands
    if text.startswith("/"):
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        if cmd == "/start": await handle_start(chat_id, username)
        elif cmd == "/help": await handle_help(chat_id)
        elif cmd == "/status": await handle_status(chat_id)
        elif cmd == "/clear": await handle_clear(chat_id)
        elif cmd == "/voice": await handle_voice_toggle(chat_id, arg)
        else: await send_message(chat_id, f"Unknown command: {cmd}\nType /help for commands.")
    else:
        await handle_chat(chat_id, text, username)

async def main():
    print(f"[{datetime.now()}] EvolvixOS Telegram Bot starting - Mr James with Voice")
    print(f"Voice Bridge: {VOICE_BRIDGE}")
    print(f"James API: {JAMES_API}")

    me = await telegram_request("getMe")
    if me.get("ok"):
        bot_info = me["result"]
        print(f"Connected as: @{bot_info['username']} (ID: {bot_info['id']})")
    else:
        print(f"Failed to connect to Telegram: {me}")
        return

    offset = 0
    print("Polling for updates... Voice enabled!")

    while True:
        try:
            updates = await telegram_request("getUpdates", offset=offset, timeout=30, allowed_updates=["message"])
            if not updates.get("ok"):
                print(f"Error: {updates}")
                await asyncio.sleep(5)
                continue
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                try:
                    await process_update(update)
                except Exception as e:
                    print(f"Error processing update: {e}")
        except httpx.TimeoutException:
            continue
        except Exception as e:
            print(f"Polling error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
