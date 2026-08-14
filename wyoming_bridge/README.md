# EvolvixOS Wyoming Bridge

Connects Home Assistant Voice Preview Edition to EvolvixOS via the Wyoming protocol.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the bridge (EvolvixOS running locally)
python -m wyoming_bridge.bridge --evolvix-url http://localhost:5000

# For Russian language
python -m wyoming_bridge.bridge --evolvix-url http://localhost:5000 --language ru

# With API key
python -m wyoming_bridge.bridge --evolvix-url http://localhost:5000 --api-key YOUR_KEY
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `EVOLVIXOS_URL` | `http://localhost:5000` | EvolvixOS server URL |
| `EVOLVIX_API_KEY` | (none) | API key for auth |
| `VOICE_LANGUAGE` | `en` | Default language |
| `TTS_VOICE` | `af` | Default TTS voice |
| `WYOMING_STT_PORT` | `10300` | STT service port |
| `WYOMING_CONV_PORT` | `10301` | Conversation service port |
| `WYOMING_TTS_PORT` | `10302` | TTS service port |

## Services

| Service | Port | EvolvixOS Endpoint |
|---|---|---|
| STT | 10300 | POST /api/v1/voice |
| Conversation | 10301 | POST /api/v1/chat |
| TTS | 10302 | POST /api/v1/audio/tts |

## Systemd Service

Create `/etc/systemd/system/evolvix-wyoming-bridge.service`:

```ini
[Unit]
Description=EvolvixOS Wyoming Bridge
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/evolvixos-platform-git
ExecStart=/usr/bin/python3 -m wyoming_bridge.bridge --evolvix-url http://localhost:5000 --language ru
Restart=always
RestartSec=5
Environment=EVOLVIXOS_URL=http://localhost:5000

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now evolvix-wyoming-bridge
```
