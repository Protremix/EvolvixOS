# EvolvixOS Voice Preview Edition (Voice PE) Integration Guide

This guide provides comprehensive instructions for integrating the **Home Assistant Voice Preview Edition (HA Voice PE)** physical voice terminal with **EvolvixOS**, a local, zero-token AI platform.

---

## 1. Architecture

The integration connects hardware microphone/speaker terminals to the local EvolvixOS AI brain through Home Assistant and Wyoming protocol bridges.

### Data Flow Diagram

```
+------------------+          +------------------------+          +-------------------------+
|                  |  Audio   |                        | Wyoming  |                         |
|  HA Voice PE     | -------->|    Home Assistant      | -------->| EvolvixOS Wyoming       |
|  (ESP32-S3 Device)          |  (Assist Pipeline)     | TCP      | Bridge Daemon           |
|  ~$50 Hardware   | <--------|                        | <--------| (Ports 10300/10301/10302|
+------------------+  Audio   +------------------------+          +-------------------------+
                                                                               |
                                                                               | REST API
                                                                               | HTTPS + API Key
                                                                               v
+-------------------------------------------------------------------------------------------+
| EvolvixOS Server (Local Zero-Token AI Brain)                                              |
|                                                                                           |
|  +--------------------+     +--------------------+     +-------------------------------+  |
|  |  Whisper STT       | --> |  AgentCore Engine  | --> |  Kokoro TTS Engine            |  |
|  |  (Audio -> Text)   |     |  (Skills & Tools)  |     |  (Text -> 24kHz Audio Output) |  |
|  +--------------------+     +--------------------+     +-------------------------------+  |
+-------------------------------------------------------------------------------------------+
```

### End-to-End Sequence Flow

1. **Wake Word Trigger**: The user says *"Hey Evolvix"*. The local wake-word engine on the ESP32 (or openWakeWord on HA) detects the phrase and illuminates the LED ring.
2. **Audio Capture**: The ESP32 captures audio via its dual microphone array with noise suppression and streams high-quality 16kHz PCM audio over Wi-Fi to Home Assistant.
3. **Home Assistant Assist Routing**: Home Assistant delegates Speech-to-Text, Conversation, and Text-to-Speech processing to external Wyoming services registered at TCP ports `10300` (STT), `10301` (Conversation/Satellite), and `10302` (TTS).
4. **Wyoming Bridge Processing**: The EvolvixOS Wyoming Bridge accepts the TCP connection, packages audio/text payloads, and calls the EvolvixOS Server REST API over secure HTTPS.
5. **EvolvixOS Processing**:
   - `POST /api/v1/voice/session` (or separate STT/Chat/TTS endpoints):
   - **Whisper STT** converts incoming voice audio into text.
   - **AgentCore** executes LLM reasoning, routes requests to available skills/tools, and formats the response.
   - **Kokoro TTS** synthesizes response text into 24kHz high-fidelity speech.
6. **Audio Output**: The Wyoming Bridge streams PCM audio chunks back to Home Assistant, which forwards the audio stream over Wi-Fi to the Voice PE device speaker.

### Component Roles

| Component | Responsibility | Technical Stack |
| :--- | :--- | :--- |
| **HA Voice PE** | Physical hardware capturing user speech and playing audio responses. | ESP32-S3, ES8311 Codec, ESPHome |
| **Home Assistant** | Home automation server running the Assist Pipeline and managing Wyoming adapters. | Home Assistant OS / Container |
| **Wyoming Bridge** | Lightweight daemon translating Wyoming TCP protocol frames to EvolvixOS REST API calls. | Python 3.10+, `wyoming`, `aiohttp` |
| **EvolvixOS Server** | Local AI engine executing Whisper STT, AgentCore intelligence, tools, and Kokoro TTS. | Python 3.10+, PyTorch, Ollama, Whisper, Kokoro |

---

## 2. Required Hardware

### 1. Home Assistant Voice Preview Edition (or ESP32-S3-BOX-3)
* **Device**: HA Voice Preview Edition or ESP32-S3-BOX-3 (~$50).
* **Specs**: Dual microphone array, built-in speaker, ESP32-S3 microcontroller, Wi-Fi 2.4GHz, USB-C power port (5V/1A minimum).

### 2. Home Assistant Host (Optional / Standalone)
* **Hardware**: Raspberry Pi 4/5 (4GB+ RAM), Home Assistant Green, or a Docker/VM instance running on the EvolvixOS server.
* **Storage**: 32GB+ MicroSD or NVMe SSD.

### 3. EvolvixOS Server (Local AI Core)
* **CPU**: Modern x86_64 multi-core processor (8+ physical cores recommended).
* **GPU**: NVIDIA GPU with 8GB+ VRAM recommended (e.g., RTX 3060/4060 or higher) for rapid Whisper STT, Ollama LLM execution, and Kokoro TTS synthesis.
* **RAM**: Minimum 16GB system RAM (32GB+ recommended).
* **Storage**: Fast NVMe SSD with at least 50GB free space for model weights.
* **Network**: Wired Gigabit Ethernet connection recommended for sub-100ms latency.

---

## 3. Server Requirements

To run the voice terminal backend, the EvolvixOS server must meet the following software requirements:

* **OS**: Linux (Ubuntu 22.04 LTS / Debian 12 recommended).
* **Python**: Python 3.10 or higher (`python3 --version`).
* **EvolvixOS Services**:
  * API Server listening on `http://127.0.0.1:5001`.
  * AgentCore service active.
* **AI Models**:
  * **Whisper STT**: Local OpenAI Whisper model (base, small, or large-v3).
  * **Kokoro TTS**: Local Kokoro TTS model operating at 24000Hz sample rate.
* **Web Server / Proxy**: Nginx 1.18+ configured as reverse proxy with TLS/SSL certificate (Let's Encrypt or trusted local CA).
* **Network Ports**:
  * `443` HTTPS (EvolvixOS REST API via Nginx)
  * `10300` TCP (Wyoming STT service)
  * `10301` TCP (Wyoming Conversation service)
  * `10302` TCP (Wyoming TTS service)

---

## 4. Installation

Follow these step-by-step instructions to set up all software components.

### Step 1: Install EvolvixOS Wyoming Bridge

On the EvolvixOS server (or the host machine running the bridge), clone and install the bridge service:

```bash
# Create target directory
sudo mkdir -p /opt/evolvix-wyoming-bridge
cd /opt/evolvix-wyoming-bridge

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install --upgrade pip
pip install wyoming aiohttp pydantic pyyaml
```

Create the python executable script `/opt/evolvix-wyoming-bridge/bridge.py`:

```python
#!/usr/bin/env python3
"""EvolvixOS Wyoming Bridge Daemon"""
import asyncio
import argparse
import logging
import aiohttp
from wyoming.server import AsyncServer
from wyoming.event import Event
from wyoming.asr import Transcript
from wyoming.tts import Synthesize

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evolvix_wyoming")

class EvolvixWyomingHandler:
    def __init__(self, api_url, api_key):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

    async def handle_event(self, event: Event):
        logger.info(f"Received Wyoming event: {event.type}")

if __name__ == "__main__":
    logger.info("Starting EvolvixOS Wyoming Bridge...")
```

Create a systemd service file at `/etc/systemd/system/evolvix-wyoming.service`:

```ini
[Unit]
Description=EvolvixOS Wyoming Bridge Daemon
After=network.target nginx.service evolvix.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/evolvix-wyoming-bridge
ExecStart=/opt/evolvix-wyoming-bridge/venv/bin/python bridge.py \
  --api-url https://localhost/api/v1 \
  --api-key evx_live_sk_8f9a2b4c1d \
  --stt-port 10300 \
  --conv-port 10301 \
  --tts-port 10302
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable evolvix-wyoming
sudo systemctl start evolvix-wyoming
sudo systemctl status evolvix-wyoming
```

### Step 2: Install Home Assistant (if not already running)

If Home Assistant is not already installed, deploy it via Docker on the server or dedicated host:

```bash
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=Europe/Madrid \
  -v /var/lib/homeassistant/config:/config \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

Navigate to `http://<HA_SERVER_IP>:8123` to complete the initial Home Assistant onboarding wizard.

### Step 3: Configure Wyoming Integration in Home Assistant

1. In Home Assistant, open **Settings** → **Devices & Services**.
2. Click **Add Integration** (bottom right).
3. Search for **Wyoming Protocol** and select it.
4. Add the three services exposed by the EvolvixOS Wyoming bridge:
   * **STT Service**: Host: `<EVOLVIX_SERVER_IP>`, Port: `10300`
   * **Conversation Service**: Host: `<EVOLVIX_SERVER_IP>`, Port: `10301`
   * **TTS Service**: Host: `<EVOLVIX_SERVER_IP>`, Port: `10302`

### Step 4: Set up Assist Pipeline in Home Assistant

1. In Home Assistant, navigate to **Settings** → **Voice Assistants**.
2. Click **Add Pipeline**.
3. Configure the fields:
   * **Name**: `EvolvixOS Voice Pipeline`
   * **Language**: `English` (or `Russian`)
   * **Conversation agent**: `EvolvixOS AgentCore`
   * **Speech-to-text**: `EvolvixOS Whisper`
   * **Text-to-speech**: `EvolvixOS Kokoro`
   * **Wake word engine**: `openWakeWord` or `MicroWakeWord`
   * **Wake word model**: `Hey Evolvix`
4. Set **EvolvixOS Voice Pipeline** as the default voice pipeline.

---

## 5. Configuration

### EvolvixOS `config.yaml` (`voice_gateway` section)

Add or update the `voice_gateway` configuration in `/opt/evolvix/config/config.yaml`:

```yaml
config:
  voice_gateway:
    enabled: true
    host: "0.0.0.0"
    port: 5001
    api_key: "evx_live_sk_8f9a2b4c1d"
    session_timeout_seconds: 300
    default_language: "en" # Options: "en", "ru"
    
    stt:
      engine: "whisper"
      model: "base"        # Options: tiny, base, small, medium, large-v3
      language: "en"       # Options: en, ru, auto
      beam_size: 5
      vad_filter: true
      
    tts:
      engine: "kokoro"
      default_voice: "af"  # Options: af, am, bf, bm, ru_alex, ru_m1, ru_f1
      sample_rate: 24000
      speed: 1.0
      format: "wav"
      
    security:
      rate_limit: "60/minute"
      max_upload_size_mb: 25
      allowed_ips:
        - "127.0.0.1"
        - "192.168.1.0/24"
```

### Wyoming Bridge Config File (`/opt/evolvix-wyoming-bridge/config.yaml`)

```yaml
bridge:
  evolvix_api_url: "https://127.0.0.1/api/v1"
  evolvix_api_key: "evx_live_sk_8f9a2b4c1d"
  verify_ssl: false # Set true when using trusted certificates
  log_level: "INFO"

ports:
  stt: 10300
  conversation: 10301
  tts: 10302

audio:
  sample_rate: 16000
  channels: 1
  sample_width: 2 # 16-bit PCM

session:
  timeout: 300
  fallback_voice: "af"
```

### Home Assistant `configuration.yaml` Snippet

```yaml
# /config/configuration.yaml
homeassistant:
  name: Home
  time_zone: Europe/Madrid

conversation:

intent_script:

wyoming:
  - hosts:
      - host: 127.0.0.1
        port: 10300
      - host: 127.0.0.1
        port: 10301
      - host: 127.0.0.1
        port: 10302
```

---

## 6. Environment Variables

The Wyoming Bridge and Voice Gateway recognize the following environment variables:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `EVOLVIX_API_URL` | `https://localhost/api/v1` | Base URL of the EvolvixOS REST API endpoint |
| `EVOLVIX_API_KEY` | `""` | Authentication Bearer token for EvolvixOS API |
| `EVOLVIX_VOICE_STT_PORT` | `10300` | Listening port for Wyoming STT service |
| `EVOLVIX_VOICE_CONVERSATION_PORT` | `10301` | Listening port for Wyoming Conversation service |
| `EVOLVIX_VOICE_TTS_PORT` | `10302` | Listening port for Wyoming TTS service |
| `EVOLVIX_LANGUAGE` | `en` | Default language code (`en` or `ru`) |
| `EVOLVIX_DEFAULT_VOICE` | `af` | Default Kokoro TTS voice ID |
| `EVOLVIX_SESSION_TIMEOUT` | `300` | Inactivity timeout in seconds for voice sessions |
| `EVOLVIX_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `EVOLVIX_VERIFY_SSL` | `true` | Verify TLS certificate on REST requests (`true`/`false`) |
| `EVOLVIX_RATE_LIMIT` | `60` | Maximum API requests allowed per minute |
| `EVOLVIX_MAX_UPLOAD_MB` | `25` | Maximum allowed audio upload payload size in MB |

---

## 7. Voice Preview Edition Configuration

### Hardware Flashing and Pairing Procedure

1. **Connect to Computer**: Connect the HA Voice PE (or ESP32-S3-BOX-3) to a PC using a high-quality USB-C data cable.
2. **Open Web Flasher**: In Google Chrome or Microsoft Edge, navigate to `https://web.esphome.io` or `https://firmware.home-assistant.io/voice-pe`.
3. **Flash ESPHome Firmware**:
   - Click **Connect** and select the Serial/COM port corresponding to the ESP32-S3 device.
   - Click **Install Home Assistant Voice PE**.
   - Wait for the erase and flash process to complete (approx. 2 minutes).
4. **Provision Wi-Fi Credentials**:
   - Once flashed, an **Improv Wi-Fi** pop-up will appear in the browser.
   - Select your 2.4GHz home Wi-Fi SSID and enter the password.
   - Alternatively, connect your smartphone/laptop to the temporary AP `Evolvix-Voice-Setup` and complete the captive portal prompt.
5. **Pair with Home Assistant**:
   - Once connected to Wi-Fi, Home Assistant automatically detects the device via mDNS.
   - A notification will appear in Home Assistant: **"New device discovered: Home Assistant Voice PE"**.
   - Click **Configure**, enter the encryption key if prompted, and assign the device to a room (e.g., *Living Room*).

---

## 8. ESPHome Configuration

If you want to customize the firmware or modify pin mappings, use the following ESPHome configuration snippet:

```yaml
# evolvix-voice-pe.yaml
esphome:
  name: evolvix-voice-pe
  friendly_name: "Evolvix Voice Terminal"
  min_version: 2024.2.0

esp32:
  board: esp32s3box
  framework:
    type: esp-idf

psram:
  mode: octal

logger:
  level: INFO

api:
  encryption:
    key: "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"

ota:
  - platform: esphome

wifi:
  ssid: "Your_Home_WiFi_2.4G"
  password: "Your_WiFi_Password"
  ap:
    ssid: "Evolvix-Voice-Setup"
    password: ""

captive_portal:

i2s_audio:
  - id: i2s_in
    i2s_lrclk_pin: GPIO45
    i2s_bclk_pin: GPIO14

  - id: i2s_out
    i2s_lrclk_pin: GPIO45
    i2s_bclk_pin: GPIO14

microphone:
  - platform: i2s_audio
    id: board_mic
    i2s_audio_id: i2s_in
    i2s_din_pin: GPIO16
    adc_type: external
    pdm: false
    bits_per_sample: 16bit
    sample_rate: 16000

speaker:
  - platform: i2s_audio
    id: board_speaker
    i2s_audio_id: i2s_out
    i2s_dout_pin: GPIO15
    dac_type: external
    bits_per_sample: 16bit
    sample_rate: 16000

voice_assistant:
  micro_wake_word:
    models:
      - model: hey_evolvix
  microphone: board_mic
  speaker: board_speaker
  noise_suppression_level: 2
  auto_gain: 31dB
  volume_multiplier: 2.0

light:
  - platform: esp32_rgb_led
    pin: GPIO38
    name: "Status LED Ring"
    id: led_ring

button:
  - platform: factory_reset
    name: "Factory Reset"
    id: reset_btn
```

Compile and flash via command line:

```bash
esphome run evolvix-voice-pe.yaml
```

---

## 9. Wi-Fi Setup

The voice terminal hardware requires a stable 2.4GHz Wi-Fi connection.

### Initial Provisioning (Captive Portal)

1. Power on the device using a 5V USB-C adapter.
2. If no configured Wi-Fi network is available, the device creates an Access Point named `Evolvix-Voice-Setup`.
3. Connect your phone or laptop to `Evolvix-Voice-Setup`.
4. A captive portal page opens automatically at `http://192.168.4.1`.
5. Select your home 2.4GHz Wi-Fi network from the list, enter the passphrase, and click **Save**.
6. The device restarts, connects to your local network, and acquires an IP address via DHCP.

### Static IP Reservation (Recommended)

To ensure reliable communication between Home Assistant and the voice terminal, assign a static IP address in your router's DHCP reservation table:

* **Device MAC Address**: Found in Home Assistant device details or router client list.
* **Recommended Subnet**: Place voice terminals on a isolated IoT VLAN with access restricted to the Home Assistant host.

---

## 10. Wake Word

The default wake word for the voice terminal is **"Hey Evolvix"**.

### Configuration Options

#### Option A: Local ESP32 Wake Word (microWakeWord)
Processes wake-word detection directly on the ESP32-S3 microcontroller, eliminating network stream latency.

1. Download the pre-trained model file `hey_evolvix.tflite` or `hey_evolvix.onnx`.
2. Place the model file in your ESPHome directory under `micro_wake_word/hey_evolvix.tflite`.
3. Enable `micro_wake_word` in your ESPHome YAML:

```yaml
voice_assistant:
  micro_wake_word:
    models:
      - model: hey_evolvix
        probability_cutoff: 0.75
        sliding_window_average_size: 10
```

#### Option B: Home Assistant openWakeWord Engine
Streams continuous audio to Home Assistant, where `openWakeWord` evaluates incoming streams.

1. In Home Assistant, install the **openWakeWord** add-on.
2. Upload the custom model file `hey_evolvix.onnx` into `/share/openwakeword/`.
3. Go to **Settings** → **Voice Assistants** → **EvolvixOS Voice Pipeline**.
4. Set **Wake word engine** to `openWakeWord` and select `Hey Evolvix`.

### Custom Wake Word Tuning

| Parameter | Recommended Value | Purpose |
| :--- | :--- | :--- |
| `probability_cutoff` | `0.75` | Threshold for wake trigger (higher = fewer false positives, lower = easier activation) |
| `sliding_window_average_size` | `10` | Smooths audio frames over time to avoid transient noise triggers |
| `noise_suppression_level` | `2` | Cleans background ambient room noise prior to model evaluation |

---

## 11. Russian Language

EvolvixOS full-stack voice pipeline natively supports Russian language (`ru`).

### Configuration for Russian Language

1. Update `config.yaml` on EvolvixOS server:

```yaml
config:
  voice_gateway:
    default_language: "ru"
    stt:
      language: "ru"
      model: "small" # Recommended for high Russian accuracy
    tts:
      default_voice: "ru_alex"
```

2. Update Wyoming Bridge environment variables:

```bash
export EVOLVIX_LANGUAGE="ru"
export EVOLVIX_DEFAULT_VOICE="ru_alex"
```

### Available Voices

| Voice ID | Gender / Characteristics | Language | Quality Level |
| :--- | :--- | :--- | :--- |
| `ru_alex` | Male / Natural, authoritative | Russian | High (Kokoro v1.0) |
| `ru_m1` | Male / Conversational | Russian | Standard |
| `ru_f1` | Female / Soft, warm tone | Russian | High |
| `af` | Female / Neutral (Fallback) | English | High |

### Fallback Strategy

If a requested Russian voice key is unavailable or fails to render:
1. Kokoro checks for default secondary Russian voice `ru_f1`.
2. If unavailable, EvolvixOS triggers automatic text-transliteration or falls back to standard English voice engine (`af`) with language auto-detection, preventing silent pipeline failures.

---

## 12. Authentication

To protect the local server from unauthorized access, all API endpoints require authentication using a Bearer token or API key header.

### API Key Setup

1. Generate a secure API key on the EvolvixOS server:

```bash
python3 -c "import secrets; print('evx_live_sk_' + secrets.token_hex(16))"
```

2. Insert the key into `config.yaml`:

```yaml
config:
  voice_gateway:
    api_key: "evx_live_sk_8f9a2b4c1d"
```

### Request Headers

All clients calling EvolvixOS endpoints must supply the API key in one of two formats:

```http
Authorization: Bearer evx_live_sk_8f9a2b4c1d
```

OR

```http
X-API-Key: evx_live_sk_8f9a2b4c1d
```

Requests without a valid key receive an `HTTP 401 Unauthorized` response.

---

## 13. HTTPS

All voice API traffic must be encrypted over TLS/HTTPS. **Never expose internal EvolvixOS ports (5000/5001) directly to external subnets or the internet.**

### Security Rules
* **No Direct Port Exposure**: Bind backend ports to `127.0.0.1` only.
* **Enforce TLS**: Use Nginx to handle SSL termination.
* **Rate Limiting**: Enforce maximum requests per minute.
* **Payload Limits**: Restrict file uploads to 25MB maximum.

### Nginx Reverse Proxy Configuration

Create `/etc/nginx/sites-available/evolvix.conf`:

```nginx
# Rate limiting zone definition
limit_req_zone $binary_remote_addr zone=evolvix_api_limit:10m rate=60r/m;

server {
    listen 80;
    server_name evolvix.local;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name evolvix.local;

    ssl_certificate /etc/letsencrypt/live/evolvix.local/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/evolvix.local/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";

    # Upload Limit
    client_max_body_size 25M;

    location /api/v1/ {
        # Apply Rate Limiting
        limit_req zone=evolvix_api_limit burst=10 nodelay;

        proxy_pass http://127.0.0.1:5001/api/v1/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for voice processing
        proxy_connect_timeout 30s;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
}
```

Enable site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/evolvix.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 14. API Endpoints

The EvolvixOS voice architecture exposes four core REST API endpoints:

### Endpoint Summary Table

| Method | Endpoint | Description | Content-Type |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/voice/session` | Full round-trip: Audio → STT → Chat → TTS → Audio | `multipart/form-data` |
| `POST` | `/api/v1/chat` | Text-based conversation with AgentCore | `application/json` |
| `POST` | `/api/v1/voice` | Speech-To-Text transcription only | `multipart/form-data` |
| `POST` | `/api/v1/audio/tts` | Text-To-Speech audio synthesis only | `application/json` |

---

### Endpoint Reference & Examples

#### 1. POST `/api/v1/voice/session`

Full end-to-end voice session processing. Accepts recorded voice audio, transcribes it via Whisper, passes prompt to AgentCore, synthesizes response via Kokoro TTS, and returns full metadata alongside response audio.

**Headers**:
```http
Authorization: Bearer evx_live_sk_8f9a2b4c1d
```

**Request Payload (multipart/form-data)**:
* `audio`: Audio file binary (WAV, OGG, or MP3)
* `session_id`: String (optional, e.g., `"sess_99a8b7"`)
* `language`: String (optional, default `"en"`)
* `voice`: String (optional, default `"af"`)

**cURL Command**:
```bash
curl -X POST https://evolvix.local/api/v1/voice/session \
  -H "Authorization: Bearer evx_live_sk_8f9a2b4c1d" \
  -F "audio=@user_input.wav" \
  -F "session_id=sess_12345" \
  -F "language=en" \
  -F "voice=af"
```

**JSON Response Example**:
```json
{
  "status": "success",
  "session_id": "sess_12345",
  "transcription": "What is the system temperature?",
  "response_text": "The EvolvixOS server CPU temperature is currently 42°C with GPU at 38°C.",
  "audio_url": "https://evolvix.local/output/audio/tts_resp_9921.wav",
  "audio_format": "audio/wav",
  "duration_seconds": 3.45,
  "metrics": {
    "stt_ms": 210,
    "agent_ms": 450,
    "tts_ms": 320,
    "total_ms": 980
  }
}
```

---

#### 2. POST `/api/v1/chat`

Direct text conversation endpoint for AgentCore reasoning and skill execution.

**Headers**:
```http
Authorization: Bearer evx_live_sk_8f9a2b4c1d
Content-Type: application/json
```

**cURL Command**:
```bash
curl -X POST https://evolvix.local/api/v1/chat \
  -H "Authorization: Bearer evx_live_sk_8f9a2b4c1d" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Turn off living room lights",
    "session_id": "sess_12345",
    "project": "default",
    "voice": true
  }'
```

**JSON Response Example**:
```json
{
  "status": "success",
  "session_id": "sess_12345",
  "response": "Living room lights have been turned off.",
  "skills_executed": ["home_assistant"],
  "voice_audio_url": "https://evolvix.local/output/audio/tts_8812.wav"
}
```

---

#### 3. POST `/api/v1/voice`

Converts audio file to text transcript using local Whisper STT.

**Headers**:
```http
Authorization: Bearer evx_live_sk_8f9a2b4c1d
```

**cURL Command**:
```bash
curl -X POST https://evolvix.local/api/v1/voice \
  -H "Authorization: Bearer evx_live_sk_8f9a2b4c1d" \
  -F "audio=@recording.wav" \
  -F "language=en"
```

**JSON Response Example**:
```json
{
  "status": "success",
  "text": "Check status of backup server",
  "language": "en",
  "confidence": 0.982
}
```

---

#### 4. POST `/api/v1/audio/tts`

Synthesizes speech audio from text using Kokoro TTS.

**Headers**:
```http
Authorization: Bearer evx_live_sk_8f9a2b4c1d
Content-Type: application/json
```

**cURL Command**:
```bash
curl -X POST https://evolvix.local/api/v1/audio/tts \
  -H "Authorization: Bearer evx_live_sk_8f9a2b4c1d" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "EvolvixOS local voice system is fully operational.",
    "voice": "af",
    "sample_rate": 24000
  }' \
  --output response.wav
```

**JSON Response (if headers set to return metadata JSON instead of raw audio stream)**:
```json
{
  "status": "success",
  "audio_url": "https://evolvix.local/output/audio/tts_7721.wav",
  "format": "wav",
  "sample_rate": 24000,
  "duration_seconds": 2.8
}
```

---

## 15. Session Management

Session management allows AgentCore to maintain multi-turn conversational context over voice interfaces.

### Conversation Lifecycle
1. **Session Creation**: When a user speaks, Home Assistant passes a `session_id` (or the Wyoming bridge generates a UUID).
2. **Context Retention**: AgentCore loads past interaction history, user preferences, and active tool states tied to `session_id`.
3. **Session Timeout**: If no new voice command is received within `session_timeout_seconds` (default: `300` seconds / 5 minutes), the session context is archived and memory is committed to SQLite storage.
4. **Explicit Reset**: A user can speak *"Evolvix, start a new conversation"* to clear active context immediately.

### Session Configuration in `config.yaml`

```yaml
config:
  agent:
    memory_enabled: true
    session_timeout_seconds: 300
    max_history_messages: 20
```

---

## 16. Troubleshooting

| Problem | Possible Cause | Solution |
| :--- | :--- | :--- |
| **Device not found in HA** | Device on wrong subnet or mDNS blocked by router. | Check that ESP32 and HA host are on the same 2.4GHz Wi-Fi/LAN segment. Ensure IGMP snooping is disabled on switch. |
| **No audio output from terminal** | Speaker volume set to 0 or bad GPIO pin mapping. | Verify volume setting in HA device panel. Check ESPHome speaker GPIO pins (`GPIO15` output for ES8311 codec). |
| **STT fails / Empty transcription** | Audio format mismatch or low microphone gain. | Ensure audio rate is 16kHz 16-bit PCM. Increase `auto_gain` to `31dB` in ESPHome `voice_assistant` settings. |
| **TTS fails / No response audio** | Kokoro engine error or missing voice weights file. | Verify Kokoro TTS status at `GET /api/v1/voice/status`. Check backend logs: `journalctl -u evolvix-api.service`. |
| **Server unreachable (HTTP 502/Connection Refused)** | Nginx misconfigured or API server daemon down. | Check API status: `systemctl status evolvix.service`. Check Nginx error logs at `/var/log/nginx/error.log`. |
| **Wake word not detected** | High background noise or low model probability setting. | Lower `probability_cutoff` to `0.65` in ESPHome YAML. Ensure noise suppression level is set to `2`. |
| **Russian language not working** | Missing Russian model weights or wrong language code. | Verify `language: ru` in `config.yaml`. Download Whisper `small` or `medium` model weights. Set voice to `ru_alex`. |
| **Authentication Error (HTTP 401 Unauthorized)** | Missing or invalid API key header in bridge config. | Verify `api_key` in `/opt/evolvix-wyoming-bridge/config.yaml` matches `voice_gateway.api_key` in EvolvixOS `config.yaml`. |

---

## 17. Complete Setup Procedure

Follow this summary checklist from unboxing to first voice conversation:

1. **Unbox Hardware**: Plug HA Voice PE hardware into a 5V 1A USB-C power supply.
2. **Flash ESPHome Firmware**: Visit `https://firmware.home-assistant.io/voice-pe` in Chrome and flash the latest firmware onto the ESP32-S3 terminal.
3. **Connect to Wi-Fi**: Use Improv Wi-Fi or connect to `Evolvix-Voice-Setup` AP to enter home 2.4GHz Wi-Fi credentials.
4. **Verify EvolvixOS Backend**: Ensure EvolvixOS server is running with Whisper STT and Kokoro TTS activated on port 5001.
5. **Configure Nginx SSL**: Set up HTTPS reverse proxy with SSL certificate and secure API key authentication.
6. **Deploy Wyoming Bridge Daemon**: Install python virtualenv at `/opt/evolvix-wyoming-bridge`, configure ports `10300-10302`, and start `evolvix-wyoming.service`.
7. **Add Wyoming Integration in HA**: In Home Assistant, navigate to **Settings** → **Devices & Services** → **Add Integration** → **Wyoming** and register `10300`, `10301`, and `10302`.
8. **Configure Voice Pipeline**: Create **EvolvixOS Voice Pipeline** under HA **Voice Assistants** settings and select EvolvixOS STT, AgentCore, and Kokoro TTS.
9. **Set Default Pipeline**: Set **EvolvixOS Voice Pipeline** as default for the HA Voice PE device.
10. **Test First Conversation**:
    - Say: *"Hey Evolvix, what time is it?"*
    - Observe LED ring response, Whisper transcription, AgentCore processing, and Kokoro TTS audio playback through the terminal speaker.

---

## 18. End-to-End Diagram

The complete end-to-end component layout and network layer interaction:

```
+--------------------------------------------------------------------------------------------------+
| PHYSICAL ROOM                                                                                    |
|                                                                                                  |
|   User Speech ----> [ Dual Microphones ]                                                        |
|                           |                                                                      |
|                           v                                                                      |
|                 +-------------------+                                                            |
|                 | HA Voice PE       | (ESP32-S3 Hardware Terminal)                               |
|                 | (ESPHome)         |                                                            |
|                 +-------------------+                                                            |
|                           |                                                                      |
|   Audio Playback <-- [ ES8311 DAC ]                                                              |
+---------------------------|----------------------------------------------------------------------+
                            |
                            | Wi-Fi (2.4GHz WPA2/WPA3)
                            v
+--------------------------------------------------------------------------------------------------+
| LOCAL NETWORK (LAN / VLAN)                                                                       |
|                                                                                                  |
|   +------------------------------------------------------------------------------------------+   |
|   | Home Assistant Host (Raspberry Pi / NUC / VM)                                            |   |
|   |                                                                                          |   |
|   |   +-----------------------+      +---------------------------+                           |   |
|   |   | openWakeWord          | ---> | Assist Voice Pipeline     |                           |   |
|   |   | ('Hey Evolvix')       |      | (STT / Conv / TTS Router) |                           |   |
|   |   +-----------------------+      +---------------------------+                           |   |
|   +------------------------------------------------|-----------------------------------------+   |
|                                                    |                                             |
|                                                    | Wyoming TCP Protocol                        |
|                                                    | Ports: 10300 (STT), 10301 (Conv), 10302 (TTS)|
|                                                    v                                             |
|   +------------------------------------------------------------------------------------------+   |
|   | EvolvixOS Server Machine (x86_64 Linux Host)                                              |   |
|   |                                                                                          |   |
|   |   +----------------------------------------------------------------------------------+   |   |
|   |   | Wyoming Bridge Daemon (/opt/evolvix-wyoming-bridge/bridge.py)                   |   |   |
|   |   +----------------------------------------------------------------------------------+   |   |
|   |                                            |                                             |   |
|   |                                            | Internal REST HTTPS Calls                   |   |
|   |                                            | Authorization: Bearer <API_KEY>             |   |
|   |                                            v                                             |   |
|   |   +----------------------------------------------------------------------------------+   |   |
|   |   | Nginx Reverse Proxy (SSL Termination / Rate Limiting / TLS 1.3)                 |   |   |
|   |   +----------------------------------------------------------------------------------+   |   |
|   |                                            |                                             |   |
|   |                                            | Proxy Pass to http://127.0.0.1:5001         |   |
|   |                                            v                                             |   |
|   |   +----------------------------------------------------------------------------------+   |   |
|   |   | EvolvixOS REST API Server (api_server.py)                                        |   |   |
|   |   |                                                                                  |   |   |
|   |   |   +---------------------+   +----------------------+   +---------------------+   |   |   |
|   |   |   | Whisper STT Engine  |   | AgentCore Engine     |   | Kokoro TTS Engine   |   |   |   |
|   |   |   | (Audio -> Text)     |   | (Skills & Tools)     |   | (Text -> 24kHz PCM) |   |   |   |
|   |   |   +---------------------+   +----------------------+   +---------------------+   |   |   |
|   |   +----------------------------------------------------------------------------------+   |   |
|   +------------------------------------------------------------------------------------------+   |
+--------------------------------------------------------------------------------------------------+
```
