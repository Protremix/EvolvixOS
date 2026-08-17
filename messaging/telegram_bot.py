"""
EvolvixOS Telegram Bot — @EvolvixOsbot
Handles: /start, /link <code>, /help, and general chat with Mr James.
Also receives conversation transfers from the dashboard.
"""
import os
import json
import time
import httpx
import asyncio
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8663115714:AAHJ399PFcRc4ugNOvTew4_ucky8LFAzpt0")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
DASHBOARD_API = "http://localhost:5005"
AGENT_BRAIN_URL = "http://localhost:5003/think"

# In-memory conversation tracking: telegram_chat_id -> {conversation context}
user_contexts = {}

# Pending link codes: code -> {chat_id, username, timestamp}
pending_links = {}


async def telegram_request(method: str, **kwargs):
    """Send a request to Telegram API."""
    url = f"{TELEGRAM_API}/{method}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=kwargs)
        return resp.json()


async def send_message(chat_id: int, text: str, parse_mode: str = None):
    """Send a message to a Telegram chat."""
    kwargs = {"chat_id": chat_id, "text": text}
    if parse_mode:
        kwargs["parse_mode"] = parse_mode
    return await telegram_request("sendMessage", **kwargs)


async def handle_start(chat_id: int, username: str):
    """Handle /start command."""
    welcome = (
        "🤖 *Welcome to EvolvixOS — Mr James*\n\n"
        "I'm your AI agent. I can:\n"
        "• Chat and answer questions\n"
        "• Execute code and manage servers\n"
        "• Create media (images, video, voice)\n"
        "• Analyze crypto markets\n"
        "• And much more!\n\n"
        "Use /link <code> to connect your dashboard account.\n"
        "Use /help to see all commands."
    )
    await send_message(chat_id, welcome, parse_mode="Markdown")


async def handle_help(chat_id: int):
    """Handle /help command."""
    help_text = (
        "*EvolvixOS Bot Commands*\n\n"
        "/start — Welcome message\n"
        "/link <code> — Link your dashboard account\n"
        "/help — This help message\n"
        "/status — Check agent status\n"
        "/clear — Clear conversation history\n\n"
        "Just type a message to chat with Mr James! 🤖"
    )
    await send_message(chat_id, help_text, parse_mode="Markdown")


async def handle_link(chat_id: int, username: str, code: str):
    """Handle /link <code> — link Telegram to dashboard account."""
    code = code.strip().upper()
    if not code:
        await send_message(chat_id, "Usage: /link <code>\n\nGet a code from the dashboard → Connect Telegram.")
        return

    # Call the dashboard API to complete linking
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{DASHBOARD_API}/api/telegram/complete-link",
                json={
                    "code": code,
                    "chat_id": chat_id,
                    "username": username or "unknown"
                }
            )
        
        if resp.status_code == 200 and resp.json().get("status") == "linked":
            await send_message(
                chat_id,
                "✅ *Telegram linked successfully!*\n\n"
                "You can now move conversations from the dashboard to Telegram "
                "and continue chatting here.",
                parse_mode="Markdown"
            )
            # Store this user's context
            user_contexts[chat_id] = {"linked": True, "username": username}
        else:
            data = resp.json() if resp.status_code != 200 else {}
            await send_message(
                chat_id,
                f"❌ Linking failed: {data.get('detail', 'Invalid or expired code')}\n"
                "Make sure you copied the code correctly from the dashboard."
            )
    except Exception as e:
        await send_message(chat_id, f"❌ Error connecting to dashboard: {str(e)}")


async def handle_status(chat_id: int):
    """Handle /status command."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("http://localhost:5001/api/v1/status")
        
        if resp.status_code == 200:
            data = resp.json()
            status_text = (
                f"🟢 *EvolvixOS Status*\n\n"
                f"Model: {data.get('model', 'unknown')}\n"
                f"Pipeline: {data.get('pipeline', 'unknown')}\n"
                f"Features: {', '.join(data.get('features', []))}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            status_text = "🟡 Agent is running but status endpoint unavailable."
    except Exception:
        status_text = "🔴 Agent is not responding."
    
    await send_message(chat_id, status_text, parse_mode="Markdown")


async def handle_clear(chat_id: int):
    """Handle /clear command."""
    if chat_id in user_contexts:
        user_contexts[chat_id].pop("history", None)
    await send_message(chat_id, "🗑 Conversation history cleared. Starting fresh!")


async def handle_chat(chat_id: int, text: str, username: str):
    """Handle a regular chat message — forward to Mr James agent brain."""
    # Send typing indicator
    await telegram_request("sendChatAction", chat_id=chat_id, action="typing")
    
    # Get or create user context
    ctx = user_contexts.get(chat_id, {"linked": False, "username": username})
    
    # Build history
    history = ctx.get("history", [])
    history.append({"role": "user", "content": text})
    # Keep only last 10 messages
    history = history[-10:]
    
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                AGENT_BRAIN_URL,
                json={
                    "message": text,
                    "user_id": f"tg_{chat_id}",
                    "history": history[-6:]
                }
            )
        
        if resp.status_code == 200:
            result = resp.json()
            response = result.get("response", "No response from agent.")
            model = result.get("model", "unknown")
            time_taken = result.get("time", 0)
            tools = result.get("tools_used", [])
            
            # Truncate if too long for Telegram (4096 char limit)
            if len(response) > 4000:
                response = response[:4000] + "\n\n... (truncated, see dashboard for full response)"
            
            # Add model info
            meta = f"\n\n_{model} · {time_taken}s"
            if tools:
                meta += f" · {', '.join(tools[:3])}"
            response += meta
            
            await send_message(chat_id, response, parse_mode="Markdown")
            
            # Update history
            history.append({"role": "assistant", "content": result.get("response", "")})
            ctx["history"] = history[-10:]
            user_contexts[chat_id] = ctx
        else:
            await send_message(chat_id, "⚠️ Agent is temporarily unavailable. Try again in a moment.")
    except httpx.TimeoutException:
        await send_message(chat_id, "⏱ Agent timed out (300s limit). Try a simpler request.")
    except Exception as e:
        await send_message(chat_id, f"❌ Error: {str(e)[:200]}")


async def process_update(update: dict):
    """Process a single update from Telegram."""
    message = update.get("message")
    if not message:
        return
    
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    username = message.get("from", {}).get("username", "") or message.get("from", {}).get("first_name", "User")
    
    if not text:
        await send_message(chat_id, "I can process text messages for now. Type /help for commands.")
        return
    
    # Command handling
    if text.startswith("/"):
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        
        if cmd == "/start":
            await handle_start(chat_id, username)
        elif cmd == "/help":
            await handle_help(chat_id)
        elif cmd == "/link":
            await handle_link(chat_id, username, arg)
        elif cmd == "/status":
            await handle_status(chat_id)
        elif cmd == "/clear":
            await handle_clear(chat_id)
        else:
            await send_message(chat_id, f"Unknown command: {cmd}\nType /help for available commands.")
    else:
        await handle_chat(chat_id, text, username)


async def main():
    """Main polling loop."""
    print(f"[{datetime.now()}] EvolvixOS Telegram Bot starting...")
    print(f"Bot: @EvolvixOsbot")
    
    # Get bot info
    me = await telegram_request("getMe")
    if me.get("ok"):
        bot_info = me["result"]
        print(f"Connected as: {bot_info['username']} (ID: {bot_info['id']})")
    else:
        print(f"Failed to connect to Telegram API: {me}")
        return
    
    # Start polling
    offset = 0
    print("Polling for updates...")
    
    while True:
        try:
            updates = await telegram_request(
                "getUpdates",
                offset=offset,
                timeout=30,
                allowed_updates=["message"]
            )
            
            if not updates.get("ok"):
                print(f"Error getting updates: {updates}")
                await asyncio.sleep(5)
                continue
            
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                try:
                    await process_update(update)
                except Exception as e:
                    print(f"Error processing update: {e}")
                    
        except httpx.TimeoutException:
            # Normal — long polling timeout
            continue
        except Exception as e:
            print(f"Polling error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
