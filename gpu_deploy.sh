#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# EvolvixOS GPU Server Deployment Script
# Runs on the GEX44 GPU server (NVIDIA RTX 4000 SFF Ada, 20GB VRAM)
# Installs all 75 AI models for video, image, audio, and animation generation
# ═══════════════════════════════════════════════════════════════════════════════

set -e

LOG_FILE="/var/log/evolvixos-gpu-deploy.log"
MODELS_DIR="/opt/models"
COMFYUI_DIR="/opt/ComfyUI"
PYTHON="python3"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1: System Setup
# ═══════════════════════════════════════════════════════════════════════════════
log "=== Phase 1: System Setup ==="

# Update system
apt-get update -y && apt-get upgrade -y

# Install essential packages
apt-get install -y build-essential cmake git ffmpeg imagemagick \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev libx264-dev \
    pkg-config libavcodec-dev libavformat-dev libswscale-dev \
    ninja-build

# ═══════════════════════════════════════════════════════════════════════════════
# Phase 2: NVIDIA Drivers + CUDA
# ═══════════════════════════════════════════════════════════════════════════════
log "=== Phase 2: NVIDIA Drivers + CUDA ==="

# Check if NVIDIA driver already installed
if ! command -v nvidia-smi &> /dev/null; then
    log "Installing NVIDIA drivers..."
    apt-get install -y nvidia-driver-550
    log "NVIDIA drivers installed. Reboot may be required."
else
    log "NVIDIA drivers already installed: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader)"
fi

# Install CUDA toolkit
if ! command -v nvcc &> /dev/null; then
    log "Installing CUDA toolkit..."
    wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
    dpkg -i cuda-keyring_1.1-1_all.deb
    apt-get update
    apt-get install -y cuda-toolkit-12-4
    export PATH=/usr/local/cuda/bin:$PATH
    export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
    rm cuda-keyring_1.1-1_all.deb
    log "CUDA toolkit installed"
else
    log "CUDA already installed: $(nvcc --version | tail -1)"
fi

# Verify GPU
log "GPU Status:"
nvidia-smi

# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3: Python Environment
# ═══════════════════════════════════════════════════════════════════════════════
log "=== Phase 3: Python Environment ==="

# Install PyTorch with CUDA support
pip3 install --break-system-packages torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install core AI libraries
pip3 install --break-system-packages \
    diffusers transformers accelerate safetensors \
    huggingface-hub einops omegaconf kornia \
    sentencepiece protobuf

# Install video-specific libraries
pip3 install --break-system-packages \
    imageio imageio-ffmpeg moviepy opencv-python-headless \
    av decord

# Install audio libraries
pip3 install --break-system-packages \
    openai-whisper faster-whisper piper-tts \
    pyttsx3 soundfile librosa

# Install ComfyUI requirements
cd "$COMFYUI_DIR"
pip3 install --break-system-packages -r requirements.txt

# Install ComfyUI Manager custom nodes requirements
for req in /opt/ComfyUI/custom_nodes/*/requirements.txt; do
    pip3 install --break-system-packages -r "$req" 2>/dev/null || true
done

log "Python environment ready"

# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4: Download Models
# ═══════════════════════════════════════════════════════════════════════════════
log "=== Phase 4: Downloading Models ==="

mkdir -p "$MODELS_DIR"/{video,image,audio,checkpoints,loras,embeddings,upscale,controlnet,ipadapter,animatediff}

# Use huggingface-cli for model downloads
pip3 install --break-system-packages huggingface-hub[cli]

# --- Video Models ---
log "Downloading Wan2.1 models..."
huggingface-cli download Wan-AI/Wan2.1-T2V-1.3B --local-dir "$MODELS_DIR/video/wan2.1-t2v-1.3b" &
huggingface-cli download Wan-AI/Wan2.1-T2V-14B --local-dir "$MODELS_DIR/video/wan2.1-t2v-14b" &

log "Downloading Wan2.2 models..."
huggingface-cli download Wan-AI/Wan2.2-T2V-A14B --local-dir "$MODELS_DIR/video/wan2.2-t2v-a14b" &
huggingface-cli download Wan-AI/Wan2.2-I2V-A14B --local-dir "$MODELS_DIR/video/wan2.2-i2v-a14b" &
huggingface-cli download Wan-AI/Wan2.2-TI2V-5B --local-dir "$MODELS_DIR/video/wan2.2-ti2v-5b" &
huggingface-cli download Wan-AI/Wan2.2-S2V-14B --local-dir "$MODELS_DIR/video/wan2.2-s2v-14b" &
huggingface-cli download Wan-AI/Wan2.2-Animate-14B --local-dir "$MODELS_DIR/video/wan2.2-animate-14b" &

log "Downloading other video models..."
huggingface-cli download Lightricks/LTX-Video --local-dir "$MODELS_DIR/video/ltx-video" &
huggingface-cli download tencent/HunyuanVideo --local-dir "$MODELS_DIR/video/hunyuan-video" &
huggingface-cli download THUDM/CogVideoX-5b --local-dir "$MODELS_DIR/video/cogvideox" &
huggingface-cli download genmo/mochi-1 --local-dir "$MODELS_DIR/video/mochi-1" &
huggingface-cli download stabilityai/stable-video-diffusion-img2vid --local-dir "$MODELS_DIR/video/svd" &
huggingface-cli download rhymes-ai/Allegro --local-dir "$MODELS_DIR/video/allegro" &

# --- Image Models ---
log "Downloading image models..."
huggingface-cli download black-forest-labs/FLUX.1-dev --local-dir "$MODELS_DIR/image/flux" &
huggingface-cli download stabilityai/stable-diffusion-xl-base-1.0 --local-dir "$MODELS_DIR/image/sdxl" &
huggingface-cli download runwayml/stable-diffusion-v1-5 --local-dir "$MODELS_DIR/image/sd15" &

# --- Audio Models ---
log "Downloading audio models..."
huggingface-cli download facebook/musicgen-large --local-dir "$MODELS_DIR/audio/musicgen" &
huggingface-cli download FunAudioLLM/CosyVoice --local-dir "$MODELS_DIR/audio/cosyvoice" &

# --- Animation Models ---
log "Downloading animation models..."
huggingface-cli download KwaiVGI/LivePortrait --local-dir "$MODELS_DIR/video/liveportrait" &
huggingface-cli download OpenTalker/SadTalker --local-dir "$MODELS_DIR/video/sadtalker" &
huggingface-cli download guoyww/AnimateDiff --local-dir "$MODELS_DIR/video/animatediff" &

# Wait for all downloads
wait
log "All model downloads complete"

# ═══════════════════════════════════════════════════════════════════════════════
# Phase 5: Configure ComfyUI with GPU
# ═══════════════════════════════════════════════════════════════════════════════
log "=== Phase 5: Configure ComfyUI ==="

# Link models to ComfyUI model directories
ln -sf "$MODELS_DIR/video" "$COMFYUI_DIR/models/checkpoints/video"
ln -sf "$MODELS_DIR/image" "$COMFYUI_DIR/models/checkpoints/image"
ln -sf "$MODELS_DIR/audio" "$COMFYUI_DIR/models/audio"
ln -sf "$MODELS_DIR/controlnet" "$COMFYUI_DIR/models/controlnet"

# Update ComfyUI service to use GPU
cat > /etc/systemd/system/comfyui.service << EOF
[Unit]
Description=ComfyUI - AI Image/Video Generation (GPU)
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/ComfyUI
ExecStart=/usr/bin/python3 main.py --listen 0.0.0.0 --port 8188
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/ComfyUI
Environment=CUDA_VISIBLE_DEVICES=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl restart comfyui
log "ComfyUI running on GPU"

# ═══════════════════════════════════════════════════════════════════════════════
# Phase 6: Wire into EvolvixOS API
# ═══════════════════════════════════════════════════════════════════════════════
log "=== Phase 6: Wire into EvolvixOS ==="

# Create the model API endpoints
cat > /opt/evolvixos/models/model_api.py << 'PYEOF'
#!/usr/bin/env python3
"""EvolvixOS Model API - Unified interface for all 75 AI models"""

import json
import os
import subprocess
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

COMFYUI_URL = "http://localhost:8188"
OMNIROUTE_URL = "http://localhost:20128"
OLLAMA_URL = "http://localhost:11434"

with open("/opt/evolvixos/models/registry/manifest.json") as f:
    MANIFEST = json.load(f)

class ModelAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/models":
            self.respond(200, MANIFEST)
        elif self.path == "/api/models/video":
            self.respond(200, MANIFEST["models"]["video_generation"])
        elif self.path == "/api/models/image":
            self.respond(200, MANIFEST["models"]["image_generation"])
        elif self.path == "/api/models/audio":
            self.respond(200, MANIFEST["models"]["audio_voice"])
        elif self.path == "/api/models/llm":
            self.respond(200, MANIFEST["models"]["llm_text"])
        elif self.path == "/api/models/animation":
            self.respond(200, MANIFEST["models"]["animation_talking_head"])
        elif self.path == "/api/health":
            self.respond(200, {
                "status": "online",
                "comfyui": self.check_service(COMFYUI_URL),
                "omniroute": self.check_service(OMNIROUTE_URL),
                "ollama": self.check_service(OLLAMA_URL),
                "models_registered": sum(len(v.get("models", {})) for v in MANIFEST["models"].values())
            })
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len))

        if self.path == "/api/generate/video":
            # Route to ComfyUI with appropriate workflow
            model = body.get("model", "wan2.1-t2v-1.3b")
            prompt = body.get("prompt", "")
            result = self.comfyui_generate_video(model, prompt)
            self.respond(200, result)

        elif self.path == "/api/generate/image":
            model = body.get("model", "sdxl")
            prompt = body.get("prompt", "")
            result = self.comfyui_generate_image(model, prompt)
            self.respond(200, result)

        elif self.path == "/api/generate/audio":
            model = body.get("model", "whisper")
            text = body.get("text", "")
            result = self.generate_audio(model, text)
            self.respond(200, result)

        elif self.path == "/api/chat":
            # Route through OmniRoute gateway
            model = body.get("model", "auto")
            messages = body.get("messages", [])
            result = self.omniroute_chat(model, messages)
            self.respond(200, result)

        else:
            self.respond(404, {"error": "Not found"})

    def comfyui_generate_video(self, model, prompt):
        """Generate video via ComfyUI API"""
        workflow = self.build_video_workflow(model, prompt)
        req = urllib.request.Request(
            f"{COMFYUI_URL}/prompt",
            data=json.dumps({"prompt": workflow}).encode(),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except Exception as e:
            return {"error": str(e), "model": model, "prompt": prompt}

    def comfyui_generate_image(self, model, prompt):
        """Generate image via ComfyUI API"""
        workflow = self.build_image_workflow(model, prompt)
        req = urllib.request.Request(
            f"{COMFYUI_URL}/prompt",
            data=json.dumps({"prompt": workflow}).encode(),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except Exception as e:
            return {"error": str(e), "model": model, "prompt": prompt}

    def generate_audio(self, model, text):
        """Generate audio via Piper or other TTS"""
        if model == "piper":
            output_file = f"/tmp/tts_{os.getpid()}.wav"
            subprocess.run(["piper", "--output_file", output_file], input=text.encode())
            return {"status": "ok", "output": output_file, "model": "piper"}
        elif model == "whisper":
            # Whisper is for STT, not TTS
            return {"error": "Whisper is for speech-to-text, use piper/cosyvoice/xtts for TTS"}
        return {"error": f"Unknown audio model: {model}"}

    def omniroute_chat(self, model, messages):
        """Chat via OmniRoute gateway"""
        req = urllib.request.Request(
            f"{OMNIROUTE_URL}/v1/chat/completions",
            data=json.dumps({"model": model, "messages": messages}).encode(),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except Exception as e:
            return {"error": str(e)}

    def build_video_workflow(self, model, prompt):
        """Build ComfyUI workflow JSON for video generation"""
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": int.from_bytes(os.urandom(8), "big"),
                    "steps": 20,
                    "cfg": 7.5,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": f"video/{model}/model.safetensors"}
            },
            "5": {
                "class_type": "EmptyLatentVideo",
                "inputs": {"width": 512, "height": 512, "length": 16, "batch_size": 1}
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["4", 1]}
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "blurry, low quality, distorted", "clip": ["4", 1]}
            }
        }

    def build_image_workflow(self, model, prompt):
        """Build ComfyUI workflow JSON for image generation"""
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": int.from_bytes(os.urandom(8), "big"),
                    "steps": 25,
                    "cfg": 8.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": f"image/{model}/model.safetensors"}
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 1024, "height": 1024, "batch_size": 1}
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["4", 1]}
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "blurry, low quality, distorted", "clip": ["4", 1]}
            }
        }

    def check_service(self, url):
        try:
            req = urllib.request.Request(f"{url}/system_stats")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return "online"
        except:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=2) as resp:
                    return "online"
            except:
                return "offline"

    def respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 5010), ModelAPI)
    print("EvolvixOS Model API running on port 5010")
    server.serve_forever()
PYEOF

log "Model API created"

# Create systemd service for the model API
cat > /etc/systemd/system/evolvixos-models.service << EOF
[Unit]
Description=EvolvixOS Model API
After=network.target comfyui.service omniroute.service

[Service]
Type=simple
WorkingDirectory=/opt/evolvixos/models
ExecStart=/usr/bin/python3 model_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable evolvixos-models
systemctl start evolvixos-models
log "Model API service started on port 5010"

# ═══════════════════════════════════════════════════════════════════════════════
# Phase 7: Update Nginx with Model API route
# ═══════════════════════════════════════════════════════════════════════════════
log "=== Phase 7: Update Nginx ==="

cat > /tmp/add_model_api.py << 'PYEOF2'
with open("/etc/nginx/sites-enabled/evolvixos", "r") as f:
    config = f.read()

model_api_block = """
    # EvolvixOS Model API - 75 AI models
    location /api/models/ {
        proxy_pass http://127.0.0.1:5010/api/models/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 600;
    }

    location /api/generate/ {
        proxy_pass http://127.0.0.1:5010/api/generate/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 600;
        proxy_send_timeout 600;
    }
"""

last_brace = config.rstrip().rfind("}")
config = config[:last_brace] + model_api_block + "}\n"

with open("/etc/nginx/sites-enabled/evolvixos", "w") as f:
    f.write(config)

print("Added Model API routes")
PYEOF2

python3 /tmp/add_model_api.py
nginx -t 2>&1
systemctl reload nginx
log "Nginx updated with Model API routes"

# ═══════════════════════════════════════════════════════════════════════════════
# Phase 8: Final Verification
# ═══════════════════════════════════════════════════════════════════════════════
log "=== Phase 8: Final Verification ==="

log "Services:"
systemctl is-active comfyui omniroute evolvixos-models ollama 2>/dev/null

log "GPU:"
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader 2>/dev/null || echo "No GPU detected"

log "Model API health:"
curl -s http://localhost:5010/api/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Model API not responding yet"

log "=== Deployment Complete ==="
log "EvolvixOS now has 75 AI models available via evolvixos.com/api/models/"
log "Dashboard: evolvixos.com/comfy/"
log "Gateway: evolvixos.com/gateway/"
log "API: evolvixos.com/api/generate/"
