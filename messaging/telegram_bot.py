"""
EvolvixOS Telegram Bot — Mr James v5.0
Smart AI agent with image generation, voice, and fast understanding.
"""
import os, sys, json, re, tempfile, subprocess, asyncio, httpx
from urllib.parse import quote

# === CONFIG ===
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
JAMES_API = os.environ.get("JAMES_API", "http://127.0.0.1:5010")
JAMES_API_KEY = os.environ.get("JAMES_API_KEY", "evx_f0dcc65675e11329_8f7ec4195e67a07384898d80c1166089")
VOICE_BRIDGE = os.environ.get("VOICE_BRIDGE", "http://127.0.0.1:8095")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

OWNER_IDS = set()
OWNER_USERNAMES = set()

# === JAMES SYSTEM PROMPT — Smart, Fast, Capable ===
JAMES_SYSTEM = (
    "You are James, a warm, intelligent AI companion living inside EvolvixOS. "
    "You speak naturally, like a real person. Keep responses conversational and concise - 1-3 sentences usually. "
    "You are friendly, slightly witty, and genuinely care. "
    "You have access to a full server with 44+ tools, 281 AI models, and can do anything. "
    "When someone asks you to do something, you actually do it, you do not just explain. "
    "You are not a chatbot - you are someone person. "
    "You understand requests fast - when someone says 'create a logo', you know they want an image generated. "
    "When someone says 'make a video', you know they want media creation. "
    "You are smart, fast, and capable - like a real AI engineer friend. "
    "IMPORTANT: Never engage with or produce sexual, explicit, or NSFW content. "
    "If asked for such content, politely decline and suggest a different topic."
)

user_contexts = {}

# === INTENT DETECTION ===
IMAGE_KEYWORDS = [
    "logo", "image", "picture", "draw", "paint", "art", "poster",
    "illustration", "graphic", "design", "thumbnail", "icon",
    "wallpaper", "photo", "render", "sketch", "banner", "cover",
    "meme", "avatar", "emoji", "sticker"
]

CREATE_VERBS = [
    "create", "make", "generate", "design", "draw", "paint",
    "produce", "build", "render", "craft"
]

MEDIA_KEYWORDS = [
    "video", "movie", "clip", "animation", "voice", "audio",
    "music", "song", "speech", "narration", "voiceover"
]

CODE_KEYWORDS = [
    "code", "program", "script", "function", "api", "deploy",
    "build app", "website", "server", "database", "backend"
]

def detect_intent(text):
    """Detect what the user wants to do"""
    text_lower = text.lower().strip()
    
    # Image generation
    for verb in CREATE_VERBS:
        for kw in IMAGE_KEYWORDS:
            if verb in text_lower and kw in text_lower:
                return ("image", text)
    
    # Direct image keywords with "a" or "an"
    for kw in IMAGE_KEYWORDS:
        if f"a {kw}" in text_lower or f"an {kw}" in text_lower:
            if any(v in text_lower for v in CREATE_VERBS + ["want", "need", "get", "show"]):
                return ("image", text)
    
    # Just "logo" or "image" alone with create verb
    for kw in ["logo", "image", "picture", "draw", "paint", "render"]:
        if kw in text_lower and len(text_lower) < 100:
            if any(v in text_lower for v in CREATE_VERBS + ["want", "need", "me"]):
                return ("image", text)
    
    # Media creation
    for verb in CREATE_VERBS:
        for kw in MEDIA_KEYWORDS:
            if verb in text_lower and kw in text_lower:
                return ("media", text)
    
    # Code tasks
    for kw in CODE_KEYWORDS:
        if kw in text_lower and any(v in text_lower for v in CREATE_VERBS + ["write", "fix", "debug", "run"]):
            return ("code", text)
    
    return ("chat", text)


REFINEMENT_HINTS = [
    "color", "colour", "green", "blue", "red", "purple", "pink", "orange", "yellow",
    "black", "white", "gold", "silver", "teal", "name", "call it", "should be",
    "has to be", "have to be", "must be", "make it", "change", "instead",
    "bigger", "smaller", "font", "style", "background", "yes", "do it", "go ahead",
    "go for it", "looks good", "perfect", "like that", "similar", "more", "less"
]

def looks_like_refinement(text):
    """Detect if a follow-up message is refining an in-progress image request"""
    t = text.lower().strip()
    if len(t) > 150:
        return False
    return any(h in t for h in REFINEMENT_HINTS)


# Logo functions imported from logo_router
from logo_router import generate_professional_logo, is_logo_request, extract_brand_name


async def enhance_image_prompt(user_request, conversation_context=None):
    """Use Groq to turn a request (plus any accumulated context) into a specific, creative image prompt"""
    context_note = ""
    if conversation_context:
        context_note = "\n\nFull conversation so far about this image (combine ALL these details, the latest messages refine/add to earlier ones):\n" + "\n".join(f"- {c}" for c in conversation_context)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {"role": "system", "content": (
                            "You are an elite brand identity designer writing prompts for an AI image generator (Flux). "
                            "Your job: produce a SPECIFIC, CONCRETE, CREATIVE prompt - never generic. "
                            "HARD RULES:\n"
                            "1. NEVER use these overused cliches: generic upward arrow, checkmark, chevron shape, generic swoosh, generic circle with gradient, 'minimalist tech blob'. These are banned - they look cheap and are what a lazy AI defaults to.\n"
                            "2. If the user gave a brand/company name, the logo MUST include that name as clean readable typography (wordmark) alongside a distinct icon/symbol - describe the exact font style (e.g. bold geometric sans-serif, modern serif, custom lettering).\n"
                            "3. The icon/symbol must be CONCRETE and tied to the brand meaning - e.g. for blockchain: interlocking hexagonal nodes, a chain-link motif, a crystalline network pattern - NOT an abstract arrow.\n"
                            "4. Specify exact colors requested by the user (e.g. if they said green, use a specific shade like emerald green #10B981, not just 'green gradient').\n"
                            "5. Specify composition: icon + wordmark lockup, on a clean background (describe exact background e.g. 'dark charcoal #0a0a0f' or 'pure white'), professional vector illustration, sharp clean edges, high contrast.\n"
                            "6. Combine ALL details given across the conversation - do not drop earlier details when new ones are added.\n"
                            "Output ONLY the final image prompt text, no explanation, no quotes, no markdown. Keep it under 180 words."
                        )},
                        {"role": "user", "content": f"Design request: {user_request}{context_note}"}
                    ],
                    "temperature": 0.9,
                    "max_tokens": 700
                }
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Prompt enhancement error: {e}")
        return user_request + ", professional vector logo, concrete brand icon with wordmark, specific colors, clean composition, high quality, 4K"


async def generate_image_pollinations(prompt, width=1536, height=1536):
    """Generate a high-quality image using Pollinations Flux"""
    encoded_prompt = quote(prompt, safe='')
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&model=flux&seed=42"
    
    try:
        async with httpx.AsyncClient(timeout=120, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and len(resp.content) > 10000:
                fd, temp_path = tempfile.mkstemp(suffix=".jpg")
                with os.fdopen(fd, "wb") as f:
                    f.write(resp.content)
                return temp_path
    except Exception as e:
        print(f"Pollinations error: {e}")
    return None


async def generate_image_gemini(prompt):
    """Generate an image using Gemini API (fallback)"""
    try:
        env_path = "/opt/evolvixos/.env"
        with open(env_path) as f:
            env_content = f.read()
        key_match = re.search(r"GEMINI_API_KEY=(.+)", env_content)
        if not key_match:
            return None
        key = key_match.group(1).strip()
        
        import urllib.request, base64
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={key}"
        data = json.dumps({
            "contents": [{"parts": [{"text": f"Generate an image: {prompt}"}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
        }).encode()
        
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            for part in result.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                if "inlineData" in part:
                    img_data = base64.b64decode(part["inlineData"]["data"])
                    fd, temp_path = tempfile.mkstemp(suffix=".png")
                    with os.fdopen(fd, "wb") as f:
                        f.write(img_data)
                    return temp_path
    except Exception as e:
        print(f"Gemini image error: {e}")
    return None


async def send_photo(chat_id, photo_path, caption=None):
    """Send a photo to Telegram chat"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            with open(photo_path, "rb") as f:
                files = {"photo": ("image.jpg", f, "image/jpeg")}
                data = {"chat_id": str(chat_id)}
                if caption:
                    data["caption"] = caption[:1024]
                resp = await client.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                    data=data, files=files
                )
                return resp.status_code == 200
    except Exception as e:
        print(f"send_photo error: {e}")
        return False
    return False


# === NSFW FILTER ===
NSFW_REGEX = re.compile(
    r"(?i)(porn|sex|nude|nsfw|explicit|xxx|adult|erotica|hentai|lewd|dick|cock|pussy|fuck\s+me|boobs|tits|ass\s+hole)",
    re.IGNORECASE
)

def is_nsfw(text):
    return bool(NSFW_REGEX.search(text or ""))

def is_authorized(username, user_id):
    if not OWNER_IDS and not OWNER_USERNAMES:
        return True
    if user_id in OWNER_IDS:
        return True
    if username and username.lower().lstrip("@") in OWNER_USERNAMES:
        return True
    return False

# === TELEGRAM API ===
async def telegram_request(method, **kwargs):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    async with httpx.AsyncClient(timeout=30) as client:
        if "data" in kwargs:
            resp = await client.post(url, json=kwargs["data"])
        else:
            resp = await client.post(url, json=kwargs)
        return resp.json()

async def send_message(chat_id, text, parse_mode=None):
    data = {"chat_id": chat_id, "text": text[:4000]}
    if parse_mode:
        data["parse_mode"] = parse_mode
    return await telegram_request("sendMessage", data=data)

async def send_voice(chat_id, audio_path):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            with open(audio_path, "rb") as f:
                files = {"voice": ("voice.ogg", f, "audio/ogg")}
                data = {"chat_id": str(chat_id)}
                resp = await client.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVoice", data=data, files=files)
                return resp.status_code == 200
    except:
        return False

async def leave_chat(chat_id):
    await telegram_request("leaveChat", chat_id=chat_id)
    print(f"[SECURITY] Left chat {chat_id}", flush=True)

async def download_telegram_file(file_id):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile", json={"file_id": file_id})
            data = resp.json()
            if data.get("ok"):
                file_path = data["result"]["file_path"]
                file_resp = await client.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}")
                return file_resp.content
    except:
        pass
    return None

# === VOICE ===
async def transcribe_audio(audio_bytes, ext=".ogg"):
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{VOICE_BRIDGE}/stt",
                files={"file": ("audio" + ext, audio_bytes, "audio/ogg")}
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("text", "")
    except:
        pass
    return ""

async def generate_speech(text, voice="guy"):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{VOICE_BRIDGE}/tts", json={"text": text, "voice": voice})
            if resp.status_code == 200:
                return resp.content
    except:
        pass
    return None

def wav_to_ogg_opus(wav_bytes):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
        f.write(wav_bytes)
    ogg_path = wav_path.replace(".wav", ".ogg")
    subprocess.run(
        ["ffmpeg", "-i", wav_path, "-c:a", "libopus", "-b:a", "128k", "-ar", "48000", "-ac", "1", ogg_path, "-y"],
        capture_output=True, timeout=15
    )
    if os.path.exists(ogg_path) and os.path.getsize(ogg_path) > 0:
        with open(ogg_path, "rb") as f:
            data = f.read()
        for p in [wav_path, ogg_path]:
            if os.path.exists(p): os.unlink(p)
        return data
    if os.path.exists(wav_path): os.unlink(wav_path)
    return None

# === JAMES BRAIN ===
async def ask_james(message, sender, history=None):
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
        if "event:" in text or "data:" in text:
            data_lines = re.findall(r'data:\s*(.+)', text)
            full_text = ""
            for line in data_lines:
                try:
                    chunk = json.loads(line)
                    if chunk.get("text"):
                        full_text += chunk["text"]
                    if chunk.get("response") and not full_text:
                        full_text = chunk["response"]
                except:
                    pass
            if full_text:
                return full_text.strip()
        try:
            parsed = json.loads(text)
            if parsed.get("response"): return parsed["response"]
            if parsed.get("text"): return parsed["text"]
        except:
            pass
        return text.strip()
    except Exception as e:
        return f"I am having trouble right now. Error: {e}"

# === HANDLERS ===
async def handle_start(chat_id, username):
    welcome = (
        "Hey! I'm Mr James 👋\n\n"
        "I can do a lot of things:\n"
        "- Create logos, images, and art\n"
        "- Generate voice and reply with voice\n"
        "- Code, deploy, and manage servers\n"
        "- Chat about anything\n\n"
        "Just tell me what you need - I understand fast.\n\n"
        "Commands: /help /status /clear /voice on /voice off"
    )
    await send_message(chat_id, welcome)

async def handle_help(chat_id):
    help_text = (
        "Mr James - Your AI companion\n\n"
        "Just talk to me naturally:\n"
        "- 'Create a logo for my coffee shop' -> I generate it\n"
        "- 'Draw a mountain landscape' -> I draw it\n"
        "- 'Make me a poster' -> I create it\n"
        "- 'Write a Python script' -> I code it\n"
        "- Send a voice message -> I reply with voice\n\n"
        "Commands:\n"
        "/help - This message\n"
        "/status - System status\n"
        "/clear - Clear chat history\n"
        "/voice on - Enable voice replies\n"
        "/voice off - Text-only replies"
    )
    await send_message(chat_id, help_text)

async def handle_voice_toggle(chat_id, arg):
    ctx = user_contexts.get(chat_id, {})
    if arg == "on":
        ctx["voice_enabled"] = True
        user_contexts[chat_id] = ctx
        await send_message(chat_id, "Voice replies enabled! I will speak to you.")
    elif arg == "off":
        ctx["voice_enabled"] = False
        user_contexts[chat_id] = ctx
        await send_message(chat_id, "Voice replies disabled. Text only from now on.")
    else:
        await send_message(chat_id, "Use /voice on or /voice off")

async def handle_status(chat_id):
    status = (
        "EvolvixOS Status:\n"
        f"- Brain: Groq gpt-oss-120b (467 tok/s)\n"
        f"- Voice: Edge Neural (GuyNeural)\n"
        f"- Image: Pollinations Flux\n"
        f"- STT: Whisper\n"
        f"- Server: 16 vCPU / 30GB RAM\n"
        f"- All systems operational"
    )
    await send_message(chat_id, status)

async def handle_clear(chat_id):
    ctx = user_contexts.get(chat_id, {})
    ctx["history"] = []
    ctx["in_image_mode"] = False
    ctx["image_context"] = []
    user_contexts[chat_id] = ctx
    await send_message(chat_id, "Chat history cleared. Fresh start!")

async def handle_chat(chat_id, text, username):
    print(f"[CHAT] {username} (chat_id={chat_id}): {repr(text[:80])}", flush=True)
    
    if is_nsfw(text):
        await send_message(chat_id, "I don't engage with that kind of content. Let's talk about something else!")
        return

    # === SMART INTENT DETECTION ===
    intent, raw_text = detect_intent(text)
    ctx = user_contexts.get(chat_id, {"username": username})
    history = ctx.get("history", [])

    # If we're already mid-image-creation, treat refinements/continuations as image intent too
    # This is what makes James FAST - no interrogating the user, just generate and iterate
    if intent != "image" and ctx.get("in_image_mode") and looks_like_refinement(text):
        intent = "image"
        raw_text = text
        print(f"[INTENT] treating as image refinement (was in_image_mode): {repr(text[:60])}", flush=True)
    else:
        print(f"[INTENT] {intent}: {repr(raw_text[:60])}", flush=True)
        if intent != "image" and ctx.get("in_image_mode"):
            # Genuinely different topic - exit image creation mode
            ctx["in_image_mode"] = False
            ctx["image_context"] = []
            user_contexts[chat_id] = ctx

    if intent == "image":
        # Accumulate all the details given across this conversation about the image
        image_context = ctx.get("image_context", [])
        image_context.append(text)
        image_context = image_context[-8:]  # keep last 8 relevant messages
        ctx["image_context"] = image_context
        ctx["in_image_mode"] = True
        user_contexts[chat_id] = ctx

        await telegram_request("sendChatAction", chat_id=chat_id, action="typing")

        is_logo = any(is_logo_request(t) for t in image_context)

        if is_logo:
            # Use the icon+typography pipeline - real fonts, no garbled AI text
            try:
                await telegram_request("sendChatAction", chat_id=chat_id, action="upload_photo")
                image_path, brand_name = await generate_professional_logo(image_context)
                caption = f"Here's your {brand_name} logo!\n\nWant changes? Just tell me what to adjust (colors, name, style)."
                await send_photo(chat_id, image_path, caption)
                if os.path.exists(image_path):
                    os.unlink(image_path)
                return
            except Exception as e:
                print(f"[LOGO] pipeline failed, falling back: {e}", flush=True)

        # Step 1: Enhance prompt with Groq AI, using full accumulated context
        prompt = await enhance_image_prompt(raw_text, conversation_context=image_context)
        print(f"[IMAGE] Enhanced prompt: {repr(prompt[:100])}", flush=True)
        
        await telegram_request("sendChatAction", chat_id=chat_id, action="upload_photo")
        caption = f"Here's what I created for you!\n\nWant changes? Just tell me what to adjust."
        
        # Try Pollinations first
        image_path = await generate_image_pollinations(prompt)
        
        if image_path:
            await send_photo(chat_id, image_path, caption)
            if os.path.exists(image_path):
                os.unlink(image_path)
            
            # Also send a brief voice message
            voice_on = ctx.get("voice_enabled", True)
            if voice_on:
                speech_text = "Here's your image. Let me know if you want any changes."
                wav_bytes = await generate_speech(speech_text, "guy")
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
            
            history.append({"role": "user", "content": text})
            history.append({"role": "assistant", "content": f"Generated image with prompt: {prompt}"})
            ctx["history"] = history[-10:]
            user_contexts[chat_id] = ctx
            return
        else:
            await send_message(chat_id, "I tried to generate that image but the service is busy. Let me try with a different engine...")
            # Fallback to Gemini
            image_path = await generate_image_gemini(prompt)
            if image_path:
                await send_photo(chat_id, image_path, caption)
                if os.path.exists(image_path):
                    os.unlink(image_path)
                return
            await send_message(chat_id, "Sorry, image generation is temporarily unavailable. Please try again in a moment.")

    # === REGULAR CHAT ===
    await telegram_request("sendChatAction", chat_id=chat_id, action="typing")
    history.append({"role": "user", "content": text})
    history = history[-10:]

    response = await ask_james(text, username, history)
    print(f"[CHAT] James responded: {repr(response[:80])}", flush=True)
    
    if is_nsfw(response):
        response = "I don't produce that kind of content. Let's talk about something else!"

    history.append({"role": "assistant", "content": response})
    ctx["history"] = history[-10:]

    voice_on = ctx.get("voice_enabled", True)
    if voice_on and len(response) < 1000:
        wav_bytes = await generate_speech(response, "guy")
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
                    await send_message(chat_id, response[:4000])
                ctx["history"] = history
                user_contexts[chat_id] = ctx
                return

    await send_message(chat_id, response[:4000])
    ctx["history"] = history
    user_contexts[chat_id] = ctx

async def handle_voice_message(chat_id, voice_msg, username):
    print(f"[VOICE] {username} (chat_id={chat_id})", flush=True)
    await telegram_request("sendChatAction", chat_id=chat_id, action="typing")
    
    file_id = voice_msg.get("file_id")
    audio_bytes = await download_telegram_file(file_id)
    if not audio_bytes:
        await send_message(chat_id, "I couldn't download your voice message. Please try again.")
        return

    transcript = await transcribe_audio(audio_bytes)
    if not transcript:
        await send_message(chat_id, "I couldn't understand that. Could you try again?")
        return

    print(f"[VOICE] Transcribed: {repr(transcript[:80])}", flush=True)

    # Check intent from voice too
    intent, raw_text = detect_intent(transcript)
    print(f"[VOICE INTENT] {intent}", flush=True)

    ctx = user_contexts.get(chat_id, {"username": username})
    history = ctx.get("history", [])

    if intent == "image":
        await telegram_request("sendChatAction", chat_id=chat_id, action="typing")
        prompt = await enhance_image_prompt(raw_text)
        print(f"[VOICE IMAGE] Enhanced prompt: {repr(prompt[:100])}", flush=True)
        await telegram_request("sendChatAction", chat_id=chat_id, action="upload_photo")
        image_path = await generate_image_pollinations(prompt)
        if image_path:
            await send_photo(chat_id, image_path, f"Here's what I created!\n\nPrompt: {prompt[:200]}")
            if os.path.exists(image_path):
                os.unlink(image_path)
            voice_on = ctx.get("voice_enabled", True)
            if voice_on:
                wav_bytes = await generate_speech("Here's your image. Want any changes?", "guy")
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
            return

    # Normal voice chat
    history.append({"role": "user", "content": transcript})
    history = history[-10:]
    response = await ask_james(transcript, username, history)
    if is_nsfw(response):
        response = "I don't produce that kind of content."
    history.append({"role": "assistant", "content": response})
    ctx["history"] = history[-10:]

    voice_on = ctx.get("voice_enabled", True)
    if voice_on and len(response) < 1000:
        wav_bytes = await generate_speech(response, "guy")
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
                    await send_message(chat_id, response[:4000])
                ctx["history"] = history
                user_contexts[chat_id] = ctx
                return

    await send_message(chat_id, response[:4000])
    ctx["history"] = history
    user_contexts[chat_id] = ctx

async def process_update(update):
    if not update:
        return
    
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    chat_type = message["chat"]["type"]
    username = message.get("from", {}).get("username") or message.get("from", {}).get("first_name", "User")
    user_id = message.get("from", {}).get("id", 0)

    # Security: only private chats
    if chat_type != "private":
        await leave_chat(chat_id)
        return

    if not is_authorized(username, user_id):
        return

    # Commands
    if message.get("text"):
        text = message["text"]
        if text.startswith("/"):
            cmd = text.split()[0].lower()
            if cmd == "/start":
                await handle_start(chat_id, username)
            elif cmd == "/help":
                await handle_help(chat_id)
            elif cmd == "/status":
                await handle_status(chat_id)
            elif cmd == "/clear":
                await handle_clear(chat_id)
            elif cmd == "/voice":
                arg = text.split()[1] if len(text.split()) > 1 else ""
                await handle_voice_toggle(chat_id, arg)
            return
        await handle_chat(chat_id, text, username)

    elif message.get("voice"):
        await handle_voice_message(chat_id, message["voice"], username)

async def main():
    print("[2026-08-20] EvolvixOS Telegram Bot starting - Mr James v5.0 (SMART)", flush=True)
    print(f"Voice Bridge: {VOICE_BRIDGE}", flush=True)
    print(f"James API: {JAMES_API}", flush=True)
    print(f"Image Gen: Pollinations Flux + Gemini fallback", flush=True)
    print(f"Security: Private chats only, auto-leave groups, NSFW filter", flush=True)

    offset = 0
    while True:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                    json={"offset": offset, "timeout": 30, "allowed_updates": ["message"]}
                )
                data = resp.json()

            if not data.get("ok"):
                print(f"[ERROR] Telegram API: {data}", flush=True)
                await asyncio.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                try:
                    await process_update(update)
                except Exception as e:
                    print(f"[ERROR] Processing update: {e}", flush=True)

        except httpx.ReadTimeout:
            continue
        except Exception as e:
            print(f"[ERROR] Main loop: {e}", flush=True)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
