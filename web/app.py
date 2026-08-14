"""
EvolvixOS — Web UI
Simple Flask web interface. Runs locally, zero tokens.
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from rich.console import Console
import threading
import yaml

console = Console()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EvolvixOS — Local AI Agent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0a0a; color: #e0e0e0;
            display: flex; flex-direction: column; height: 100vh;
        }
        header {
            background: #1a1a1a; padding: 16px 24px;
            border-bottom: 1px solid #333;
            display: flex; align-items: center; gap: 12px;
        }
        header h1 { font-size: 20px; color: #00ff88; }
        header .badge {
            font-size: 11px; background: #00ff88; color: #000;
            padding: 2px 8px; border-radius: 4px; font-weight: bold;
        }
        #chat { flex: 1; overflow-y: auto; padding: 24px; }
        .msg { margin-bottom: 16px; max-width: 80%; }
        .msg.user { margin-left: auto; }
        .msg .role { font-size: 12px; color: #888; margin-bottom: 4px; }
        .msg .content {
            padding: 12px 16px; border-radius: 12px;
            white-space: pre-wrap; line-height: 1.6;
        }
        .msg.user .content { background: #1a3a5a; }
        .msg.agent .content { background: #1a2a1a; }
        #input-area {
            padding: 16px 24px; border-top: 1px solid #333;
            display: flex; gap: 12px;
        }
        #input {
            flex: 1; padding: 12px 16px; background: #1a1a1a;
            border: 1px solid #444; border-radius: 8px; color: #e0e0e0;
            font-size: 14px; outline: none;
        }
        #input:focus { border-color: #00ff88; }
        #send {
            padding: 12px 24px; background: #00ff88; color: #000;
            border: none; border-radius: 8px; font-weight: bold; cursor: pointer;
        }
        #send:hover { background: #00cc66; }
        #send:disabled { opacity: 0.5; cursor: not-allowed; }
        .status { font-size: 12px; color: #888; margin-left: auto; }
        .skill-badge {
            display: inline-block; font-size: 11px;
            background: #2a2a2a; padding: 2px 8px;
            border-radius: 4px; margin: 2px; color: #00ff88;
        }
    </style>
</head>
<body>
    <header>
        <h1>🧬 EvolvixOS</h1>
        <span class="badge">100% LOCAL</span>
        <span class="badge">ZERO TOKENS</span>
        <span class="badge">OPEN SOURCE</span>
        <span class="status" id="status">Ready</span>
    </header>
    <div id="chat"></div>
    <div id="input-area">
        <input id="input" placeholder="Ask Evolvix anything..." autocomplete="off">
        <button id="send" onclick="send()">Send</button>
    </div>
    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('input');
        const sendBtn = document.getElementById('send');

        function addMsg(role, content) {
            const div = document.createElement('div');
            div.className = `msg ${role}`;
            div.innerHTML = `<div class="role">${role === 'user' ? 'You' : 'Evolvix'}</div><div class="content">${content}</div>`;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        async function send() {
            const text = input.value.trim();
            if (!text) return;
            addMsg('user', text);
            input.value = '';
            sendBtn.disabled = true;
            document.getElementById('status').textContent = 'Thinking...';

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await res.json();
                addMsg('agent', data.response.replace(/\n/g, '<br>'));
                document.getElementById('status').textContent = 'Ready';
            } catch (e) {
                addMsg('agent', 'Error: ' + e.message);
                document.getElementById('status').textContent = 'Error';
            }
            sendBtn.disabled = false;
            input.focus();
        }

        input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });
    </script>
</body>
</html>
"""


def create_app(config_path: str = "config/config.yaml"):
    app = Flask(__name__)
    CORS(app)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    app.config.update(config)

    # Initialize agent
    from agent.core import AgentCore
    agent = AgentCore(config_path=config_path)

    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE)

    @app.route('/api/chat', methods=['POST'])
    def chat():
        data = request.json
        message = data.get('message', '')
        if not message:
            return jsonify({"response": "No message provided."}), 400

        # Run agent in a separate thread to not block
        result = agent.run(message)
        return jsonify({"response": result})

    @app.route('/api/status', methods=['GET'])
    def status():
        return jsonify({
            "name": "EvolvixOS",
            "model": agent.llm_config.get("primary_model"),
            "skills": list(agent._available_skills.keys()),
            "memory_entries": len(agent.memory.get_recent_memories(limit=999)),
            "mode": "100% local, zero tokens"
        })

    return app
