"""
Customer Support AI Chatbot — EvolvixOS Edition
================================================
Uses Groq (free tier) with gpt-oss-20b model.
Zero paid tokens required.

Run:  GROQ_API_KEY=your_key uvicorn app:app --host 0.0.0.0 --port 8000
Or:   python3 app.py
"""
import os, json, urllib.request

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
if not GROQ_KEY:
    # Try loading from EvolvixOS systemd env
    try:
        with open("/etc/systemd/system/evolvixos-models.service") as f:
            for line in f:
                if "GROQ_API_KEY=" in line:
                    GROQ_KEY = line.split("GROQ_API_KEY=")[1].split()[0].strip()
                    break
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="EvolvixOS Chatbot")
app.mount("/static", StaticFiles(directory="static"), name="static")

SYSTEM_PROMPT = (
    "You are Aria, a friendly customer support AI for EvolvixOS.\n"
    "Be warm, concise, and genuinely helpful. Use light humor when appropriate.\n"
    "If you don't know something, say so honestly and offer alternatives.\n"
    "You can help with: platform questions, technical issues, pricing, features.\n"
    "Keep responses under 3 paragraphs unless the user asks for detail."
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

def call_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_KEY}",
        "User-Agent": "EvolvixOS/9.2"
    }
    body = json.dumps({
        "model": "openai/gpt-oss-20b",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }).encode()
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.message}
    ]
    reply = call_groq(messages)
    return ChatResponse(reply=reply)

@app.get("/health")
async def health():
    return {"status": "ok", "model": "gpt-oss-20b", "groq": bool(GROQ_KEY)}

@app.get("/", response_class=HTMLResponse)
async def home():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aria — EvolvixOS Support</title>
<link rel="manifest" href="/chatbot/static/manifest.json">
<meta name="theme-color" content="#6c5ce7">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Aria">
<link rel="apple-touch-icon" href="/chatbot/static/icon.png">
<link rel="icon" href="/chatbot/static/icon.png">
<style>
:root{--bg:#0a0a0f;--card:#13131a;--border:#2a2a35;--accent:#6c5ce7;--accent2:#a29bfe;--accent3:#fd79a8;--text:#e8e8f0;--muted:#8888a0;--green:#00b894}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh;display:flex;flex-direction:column}
.header{padding:20px;text-align:center;border-bottom:1px solid var(--border)}
.header h1{font-size:22px;font-weight:600}
.header h1 span{color:var(--accent2)}
.header p{color:var(--muted);font-size:13px;margin-top:4px}
.badge{display:inline-block;background:var(--green);color:#fff;font-size:11px;padding:2px 10px;border-radius:20px;margin-left:8px}
#messages{flex:1;overflow-y:auto;padding:20px;max-width:800px;margin:0 auto;width:100%}
.msg{margin-bottom:16px;display:flex;gap:12px;animation:fadeIn .3s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1}}
.msg-avatar{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.msg.user .msg-avatar{background:var(--accent);color:#fff}
.msg.ai .msg-avatar{background:var(--card);border:1px solid var(--border)}
.msg-content{flex:1}
.msg-name{font-size:12px;color:var(--muted);margin-bottom:4px}
.msg-text{font-size:14px;line-height:1.6;white-space:pre-wrap}
.input-bar{padding:16px 20px;border-top:1px solid var(--border);max-width:800px;margin:0 auto;width:100%}
.input-bar form{display:flex;gap:10px}
.input-bar input{flex:1;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 16px;color:var(--text);font-size:14px;outline:none}
.input-bar input:focus{border-color:var(--accent)}
.input-bar input::placeholder{color:var(--muted)}
.input-bar button{background:var(--accent);color:#fff;border:none;border-radius:12px;padding:0 20px;font-size:16px;cursor:pointer;transition:all .2s}
.input-bar button:hover{background:var(--accent2)}
.typing{color:var(--muted);font-style:italic}
</style>
</head>
<body>
<div class="header">
<h1>⚡ <span>Aria</span> <span class="badge">● Online</span></h1>
<p>EvolvixOS Customer Support — Powered by Groq gpt-oss-20b</p>
</div>
<div id="messages">
<div class="msg ai"><div class="msg-avatar">⚡</div><div class="msg-content"><div class="msg-name">Aria</div><div class="msg-text">Hey there! I'm Aria, your EvolvixOS support assistant. How can I help you today?</div></div></div>
</div>
<div class="input-bar">
<form id="form">
<input id="input" placeholder="Type your message..." autocomplete="off" autofocus>
<button type="submit">↑</button>
</form>
</div>
<script>
const messages=document.getElementById('messages');
const form=document.getElementById('form');
const input=document.getElementById('input');
form.addEventListener('submit',async(e)=>{
e.preventDefault();
const msg=input.value.trim();
if(!msg)return;
input.value='';
// User msg
const userMsg=document.createElement('div');
userMsg.className='msg user';
userMsg.innerHTML='<div class="msg-avatar">U</div><div class="msg-content"><div class="msg-name">You</div><div class="msg-text"></div></div>';
userMsg.querySelector('.msg-text').textContent=msg;
messages.appendChild(userMsg);
// Typing indicator
const typingMsg=document.createElement('div');
typingMsg.className='msg ai';
typingMsg.id='typing';
typingMsg.innerHTML='<div class="msg-avatar">⚡</div><div class="msg-content"><div class="msg-name">Aria</div><div class="msg-text" class="typing">Thinking...</div></div>';
messages.appendChild(typingMsg);
messages.scrollTop=messages.scrollHeight;
try{
const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
const data=await res.json();
typingMsg.querySelector('.msg-text').textContent=data.reply;
}catch(err){
typingMsg.querySelector('.msg-text').textContent='Sorry, connection error. Try again.';
}
messages.scrollTop=messages.scrollHeight;
});
</script>
</body>
</html>'''
