"""
EvolvixOS Voice Bridge v2.0 — Edge Neural TTS (primary) + Piper (fallback)
POST /stt  - transcribe audio to text (Whisper)
POST /tts  - text to speech (Edge Neural or Piper)
GET  /health
GET  /voices
"""
import os, io, tempfile, subprocess, asyncio, json
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='EvolvixOS Voice Bridge', version='2.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

PIPER_VOICES_DIR = '/opt/piper-voices'
DEFAULT_VOICE = os.environ.get('JAMES_VOICE', 'guy')
WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'base')

EDGE_VOICES = {
    'guy': 'en-US-GuyNeural',
    'christopher': 'en-US-ChristopherNeural',
    'eric': 'en-US-EricNeural',
    'brian': 'en-US-BrianNeural',
    'roger': 'en-US-RogerNeural',
    'andrew': 'en-US-AndrewNeural',
}

PIPER_FALLBACK = {
    'ryan': 'en_US-ryan-high',
    'lessac': 'en_US-lessac-high',
    'amy': 'en_US-amy-medium',
    'alba': 'en_GB-alba-medium',
    'kareem': 'ar_JO-kareem-medium',
    'thorsten': 'de_DE-thorsten-medium',
    'irina': 'ru_RU-irina-medium',
}


async def generate_edge_tts(text, voice_id):
    import edge_tts
    fd, temp_mp3 = tempfile.mkstemp(suffix='.mp3')
    os.close(fd)
    try:
        communicate = edge_tts.Communicate(text, voice_id)
        await communicate.save(temp_mp3)
        if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 0:
            wav_path = temp_mp3.replace('.mp3', '.wav')
            subprocess.run(
                ['ffmpeg', '-i', temp_mp3, '-ar', '22050', '-ac', '1', '-y', wav_path],
                capture_output=True, timeout=10)
            os.unlink(temp_mp3)
            if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                return wav_path
        return None
    except Exception as e:
        print(f'Edge TTS error: {e}')
        if os.path.exists(temp_mp3):
            os.unlink(temp_mp3)
        return None


def generate_piper_tts(text, voice_key):
    model_name = PIPER_FALLBACK.get(voice_key, 'en_US-ryan-high')
    model = os.path.join(PIPER_VOICES_DIR, model_name + '.onnx')
    config = os.path.join(PIPER_VOICES_DIR, model_name + '.onnx.json')
    if not os.path.exists(model):
        model = os.path.join(PIPER_VOICES_DIR, 'en_US-ryan-high.onnx')
        config = os.path.join(PIPER_VOICES_DIR, 'en_US-ryan-high.onnx.json')
    fd, temp_wav = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    subprocess.run(
        ['piper', '-m', model, '-c', config,
         '--length-scale', '1.15',
         '--noise-scale', '0.85',
         '--noise-w', '0.6',
         '-f', temp_wav],
        input=text, capture_output=True, text=True, timeout=30)
    if os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 0:
        return temp_wav
    return None


def post_process_audio(wav_path):
    processed = wav_path.replace('.wav', '_proc.wav')
    subprocess.run(
        ['ffmpeg', '-i', wav_path,
         '-af', 'loudnorm=I=-16:LRA=11:TP=-1.5,bass=g=+2:f=80:w=1,treble=g=-1:f=4000:w=1,acompressor=threshold=-20dB:ratio=2:attack=5:release=80,aresample=22050',
         '-y', processed],
        capture_output=True, timeout=15)
    if os.path.exists(processed) and os.path.getsize(processed) > 0:
        os.unlink(wav_path)
        return processed
    return wav_path


@app.get('/')
async def root():
    return {'service': 'Voice Bridge v2.0', 'primary': 'edge-neural', 'fallback': 'piper', 'voices': list(EDGE_VOICES.keys()), 'default': DEFAULT_VOICE}


@app.get('/health')
async def health():
    return {'status': 'healthy', 'engine': 'edge-neural (primary), piper (fallback)', 'default_voice': DEFAULT_VOICE, 'edge_voice': EDGE_VOICES.get(DEFAULT_VOICE, 'en-US-GuyNeural'), 'whisper_model': WHISPER_MODEL}


@app.get('/voices')
async def list_voices():
    return {'edge_neural': EDGE_VOICES, 'piper_fallback': PIPER_FALLBACK, 'default': DEFAULT_VOICE}


@app.post('/stt')
async def speech_to_text(file: UploadFile = File(...)):
    try:
        audio_data = await file.read()
        suffix = os.path.splitext(file.filename or 'audio.ogg')[1] or '.ogg'
        fd, temp_input = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        with open(temp_input, 'wb') as f:
            f.write(audio_data)

        if not suffix.endswith('.wav'):
            temp_wav = temp_input.replace(suffix, '.wav')
            subprocess.run(['ffmpeg', '-i', temp_input, '-ar', '16000', '-ac', '1', '-y', temp_wav], capture_output=True, timeout=30)
            os.unlink(temp_input)
            temp_input = temp_wav

        subprocess.run(['whisper', temp_input, '--model', WHISPER_MODEL, '--language', 'en', '--output_format', 'txt', '--output_dir', '/tmp'], capture_output=True, text=True, timeout=60)
        txt_file = temp_input.rsplit('.', 1)[0] + '.txt'
        text = ''
        if os.path.exists(txt_file):
            with open(txt_file) as f:
                text = f.read().strip()
            os.unlink(txt_file)
        if os.path.exists(temp_input):
            os.unlink(temp_input)
        if not text:
            return JSONResponse({'text': '', 'error': 'No speech detected'}, status_code=422)
        return {'text': text, 'language': 'en'}
    except subprocess.TimeoutExpired:
        return JSONResponse({'error': 'Transcription timed out'}, status_code=408)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@app.post('/stt/raw')
async def speech_to_text_raw(request: Request):
    try:
        audio_data = await request.body()
        fd, temp_input = tempfile.mkstemp(suffix='.ogg')
        os.close(fd)
        with open(temp_input, 'wb') as f:
            f.write(audio_data)
        temp_wav = temp_input.replace('.ogg', '.wav')
        subprocess.run(['ffmpeg', '-i', temp_input, '-ar', '16000', '-ac', '1', '-y', temp_wav], capture_output=True, timeout=30)
        os.unlink(temp_input)
        subprocess.run(['whisper', temp_wav, '--model', WHISPER_MODEL, '--language', 'en', '--output_format', 'txt', '--output_dir', '/tmp'], capture_output=True, text=True, timeout=60)
        txt_file = temp_wav.rsplit('.', 1)[0] + '.txt'
        text = ''
        if os.path.exists(txt_file):
            with open(txt_file) as f:
                text = f.read().strip()
            os.unlink(txt_file)
        os.unlink(temp_wav)
        return {'text': text}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@app.post('/tts')
async def text_to_speech(request: Request):
    try:
        body = await request.json()
        text = body.get('text', '')
        voice = body.get('voice', DEFAULT_VOICE)
        if not text.strip():
            return JSONResponse({'error': 'text required'}, status_code=400)

        audio_path = None
        engine_used = None
        edge_voice = EDGE_VOICES.get(voice, EDGE_VOICES.get(DEFAULT_VOICE, 'en-US-GuyNeural'))

        try:
            audio_path = await generate_edge_tts(text, edge_voice)
            if audio_path:
                engine_used = 'edge-neural'
        except Exception as e:
            print(f'Edge failed: {e}')

        if not audio_path:
            audio_path = generate_piper_tts(text, voice)
            engine_used = 'piper'

        if not audio_path or not os.path.exists(audio_path):
            return JSONResponse({'error': 'TTS failed'}, status_code=500)

        audio_path = post_process_audio(audio_path)
        with open(audio_path, 'rb') as f:
            audio = f.read()
        os.unlink(audio_path)

        return StreamingResponse(
            io.BytesIO(audio),
            media_type='audio/wav',
            headers={'Content-Disposition': 'attachment; filename=speech.wav', 'X-Engine': engine_used})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8095)
