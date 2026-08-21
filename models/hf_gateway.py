#!/usr/bin/env python3
"""
HuggingFace Inference API Gateway for EvolvixOS v8.1
Provides free OpenAI-compatible access to GPT-2, GPT-Neo, GPT-J, Nemotron, etc.
v8.1: Fixed to use ThreadingHTTPServer (was single-threaded, blocking all requests).
      Port changed to 20129 to match Nginx config.
"""
import json
import urllib.request
import urllib.error
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HF_API_URL = "https://api-inference.huggingface.co/models"
HF_TOKEN = os.environ.get("HF_TOKEN", "")

HF_MODELS = {
    "nemotron-340b":   "nvidia/Nemotron-4-340B-Instruct",
    "nemotron-70b":    "nvidia/Nemotron-70B-Instruct",
    "nemotron-nano-8b": "nvidia/NVIDIA-Nemotron-3-Nano-8B",
    "nemotron-mini-4b": "nvidia/NVIDIA-Nemotron-3-Mini-4B",
    "gpt2":            "openai-community/gpt2",
    "gpt2-large":      "openai-community/gpt2-large",
    "gpt-neo-1.3b":   "EleutherAI/gpt-neo-1.3B",
    "gpt-neo-2.7b":   "EleutherAI/gpt-neo-2.7B",
    "gpt-j-6b":       "EleutherAI/gpt-j-6B",
    "falcon-7b":      "tiiuae/falcon-7b",
    "falcon-rw-1b":   "tiiuae/falcon-rw-1b",
    "flan-t5-xl":     "google/flan-t5-xl",
    "bloom-7b":      "bigscience/bloom-7b1",
    "opt-6.7b":      "facebook/opt-6.7b",
}

class HFGatewayHandler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "https://evolvixos.com")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("X-Content-Type-Options", "nosniff")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/models" or self.path == "/v1/models":
            models = [{"id": k, "object": "model", "owned_by": "huggingface"} for k in HF_MODELS]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({"object": "list", "data": models}).encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "models": len(HF_MODELS)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/v1/chat/completions" or self.path == "/chat/completions":
            self._handle_chat()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_chat(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            messages = body.get("messages", [])
            model = body.get("model", "gpt2")
            stream = body.get("stream", False)

            hf_model = HF_MODELS.get(model, HF_MODELS.get("gpt2"))

            prompt = ""
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    prompt += f"[System]: {content}\n"
                elif role == "user":
                    prompt += f"[User]: {content}\n"
                elif role == "assistant":
                    prompt += f"[Assistant]: {content}\n"
            prompt += "[Assistant]: "

            headers = {"Content-Type": "application/json"}
            if HF_TOKEN:
                headers["Authorization"] = f"Bearer {HF_TOKEN}"

            payload = json.dumps({
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": body.get("max_tokens", 500),
                    "temperature": body.get("temperature", 0.7),
                    "return_full_text": False,
                },
                "options": {"wait_for_model": True}
            }).encode()

            req = urllib.request.Request(f"{HF_API_URL}/{hf_model}", data=payload, headers=headers)

            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read())
                    if isinstance(result, list) and result:
                        text = result[0].get("generated_text", "")
                    elif isinstance(result, dict):
                        text = result.get("generated_text", str(result))
                    else:
                        text = str(result)

                    response = {
                        "id": f"hf-{model}-{int(__import__('time').time())}",
                        "object": "chat.completion",
                        "model": model,
                        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                    }

                    if stream:
                        self.send_response(200)
                        self.send_header("Content-Type", "text/event-stream")
                        self._cors()
                        self.end_headers()
                        chunk = f"data: {json.dumps({'choices': [{'delta': {'content': text}, 'index': 0}]})}\n\n"
                        self.wfile.write(chunk.encode())
                        self.wfile.write(b"data: [DONE]\n\n")
                    else:
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self._cors()
                        self.end_headers()
                        self.wfile.write(json.dumps(response).encode())

            except urllib.error.HTTPError as e:
                error_body = e.read().decode(errors="ignore")
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self._cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": {"message": error_body, "type": "api_error"}}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": str(e)}}).encode())

    def log_message(self, format, *args):
        print(f"[HF Gateway] {args[0]}")

if __name__ == "__main__":
    # FIX: Use port 20129 to match Nginx config, and ThreadingHTTPServer
    port = int(os.environ.get("HF_GATEWAY_PORT", "20129"))
    server = ThreadingHTTPServer(("127.0.0.1", port), HFGatewayHandler)
    print(f"🤗 HuggingFace Gateway v8.1 running on port {port} (threaded)")
    print(f"   Models: {', '.join(HF_MODELS.keys())}")
    server.serve_forever()
