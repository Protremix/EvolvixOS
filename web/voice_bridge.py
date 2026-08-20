"""
EvolvixOS Voice Bridge — Speech-to-Text and Text-to-Speech microservice

Handles voice transcription (Whisper) and speech synthesis (Piper)
for Mr James to hear and speak like a human.

POST /stt  — receives audio file (ogg/mp3/wav/webm), returns {text}
POST /tts  — receives {text, voice?}, returns audio file (wav)
GET  /health
"""
import os, io, tempfile, subprocess, asyncio
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="EvolvixOS Voice Bridge", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

PIPER_VOICES = "/opt/piper-voices"
DEFAULT_VOICE = os.environ.get("JAMES_VOICE", "en_US-ryan-high")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")

# Available voices
VOICES = {
    "ryan": "en_US-ryan-high",
    "lessac": "en_US-lessac-high",
    "amy": "en_US-amy-medium",
    "lessac_med": "en_US-lessac-medium",
    "alba": "en_GB-alba-medium",
    "claude": "es_MX-claude-medium",
    "kareem": "ar_JO-kareem-medium",
    "siwon": "fr_FR-siwon-medium",
    "thorsten": "de_DE-thorsten-medium",
    "irina": "ru_RU-irina-medium",
}

def get_voice_model(voice_name):
    """Get the Piper model path for a voice name"""
    if voice_name in VOICES:
        voice_name = VOICES[voice_name]
    model = os.path.join(PIPER_VOICES, f"{voice_name}.onnx")
    config = os.path.join(PIPER_VOICES, f"{voice_name}.onnx.json")
    if os.path.exists(model) and os.path.exists(config):
        return model, config
    # Fallback to default
    model = os.path.join(PIPER_VOICES, f"{DEFAULT_VOICE}.onnx")
    config = os.path.join(PIPER_VOICES, f"{DEFAULT_VOICE}.onnx.json")
    return model, config

@app.get("/")
async def root():
    return {"service": "Voice Bridge", "voices": list(VOICES.keys()), "default": DEFAULT_VOICE}

@app.get("/health")
async def health():
    model, config = get_voice_model(DEFAULT_VOICE)
    return {
        "status": "healthy",
        "whisper_model": WHISPER_MODEL,
        "piper_voice": DEFAULT_VOICE,
        "piper_model_exists": os.path.exists(model),
        "piper_config_exists": os.path.exists(config)
    }

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """Transcribe audio file to text using Whisper"""
    try:
        # Save uploaded audio to temp file
        audio_data = await file.read()
        suffix = os.path.splitext(file.filename or "audio.ogg")[1] or ".ogg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(audio_data)
            temp_input = f.name

        # Convert to wav if needed (whisper prefers wav/mp3)
        if not suffix.endswith(".wav"):
            temp_wav = temp_input.replace(suffix, ".wav")
            subprocess.run(["ffmpeg", "-i", temp_input, "-ar", "16000", "-ac", "1", "-y", temp_wav],
                         capture_output=True, timeout=30)
            os.unlink(temp_input)
            temp_input = temp_wav

        # Run Whisper transcription
        result = subprocess.run(
            ["whisper", temp_input, "--model", WHISPER_MODEL, "--language", "en", "--output_format", "txt", "--output_dir", "/tmp"],
            capture_output=True, text=True, timeout=60
        )

        # Read the output
        txt_file = temp_input.rsplit(".", 1)[0] + ".txt"
        if os.path.exists(txt_file):
            with open(txt_file) as f:
                text = f.read().strip()
            os.unlink(txt_file)
        else:
            # Fallback: parse from stderr/stdout
            text = result.stdout.strip() if result.stdout else ""

        # Cleanup
        if os.path.exists(temp_input):
            os.unlink(temp_input)

        if not text:
            return JSONResponse({"text": "", "error": "No speech detected"}, status_code=422)

        return {"text": text, "language": "en"}

    except subprocess.TimeoutExpired:
        return JSONResponse({"error": "Transcription timed out"}, status_code=408)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/stt/raw")
async def speech_to_text_raw(request: Request):
    """Transcribe raw audio bytes (for internal use)"""
    try:
        audio_data = await request.body()
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(audio_data)
            temp_input = f.name

        # Convert to wav
        temp_wav = temp_input.replace(".ogg", ".wav")
        subprocess.run(["ffmpeg", "-i", temp_input, "-ar", "16000", "-ac", "1", "-y", temp_wav],
                     capture_output=True, timeout=30)
        os.unlink(temp_input)

        # Whisper
        subprocess.run(
            ["whisper", temp_wav, "--model", WHISPER_MODEL, "--language", "en", "--output_format", "txt", "--output_dir", "/tmp"],
            capture_output=True, text=True, timeout=60
        )

        txt_file = temp_wav.rsplit(".", 1)[0] + ".txt"
        text = ""
        if os.path.exists(txt_file):
            with open(txt_file) as f:
                text = f.read().strip()
            os.unlink(txt_file)
        os.unlink(temp_wav)

        return {"text": text}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/tts")
async def text_to_speech(request: Request):
    """Convert text to speech using Piper"""
    try:
        body = await request.json()
        text = body.get("text", "")
        voice = body.get("voice", DEFAULT_VOICE)

        if not text.strip():
            return JSONResponse({"error": "text required"}, status_code=400)

        model, config = get_voice_model(voice)

        # Generate speech with Piper — tuned for natural human prosody
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_output = f.name

        subprocess.run(
            ["piper", "-m", model, "-c", config,
             "--length-scale", "1.15",     # slightly slower = more deliberate/natural
             "--noise-scale", "0.85",       # more pitch variation = expressive
             "--noise-w", "0.6",            # less timing jitter = smoother flow
             "-f", temp_output],
            input=text,
            capture_output=True, text=True, timeout=30
        )

        if not os.path.exists(temp_output) or os.path.getsize(temp_output) == 0:
            return JSONResponse({"error": "TTS generation failed"}, status_code=500)

        # Post-process with ffmpeg: normalize + warm EQ + light compression
        processed_output = temp_output.replace(".wav", "_processed.wav")
        subprocess.run([
            "ffmpeg", "-i", temp_output,
            "-af", "loudnorm=I=-16:LRA=11:TP=-1.5,"    # broadcast loudness norm
                   "bass=g=+2:f=80:w=1,"                # warm up low end (deeper male voice)
                   "treble=g=-1:f=4000:w=1,"             # soften harsh highs
                   "acompressor=threshold=-20dB:ratio=2:attack=5:release=80,"  # gentle compression
                   "aresample=22050",
            "-y", processed_output
        ], capture_output=True, timeout=15)

        # Use processed if it exists, otherwise fall back to raw
        final_output = processed_output if os.path.exists(processed_output) and os.path.getsize(processed_output) > 0 else temp_output

        with open(final_output, "rb") as f:
            audio = f.read()

        # Cleanup
        for p in [temp_output, processed_output]:
            if os.path.exists(p):
                os.unlink(p)

        return StreamingResponse(
            io.BytesIO(audio),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=speech.wav"}
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/voices")
async def list_voices():
    """List available voices"""
    return {"voices": VOICES, "default": DEFAULT_VOICE}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8095)
