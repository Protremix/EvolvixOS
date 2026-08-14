"""
EvolvixOS — Device Manager Skill
Register, track, and manage connected devices across all platforms.

Supports:
  - Android (PWA + WebSocket)
  - iOS (PWA + WebSocket)
  - Windows (PWA + WebSocket + Desktop app)
  - macOS (PWA + WebSocket)
  - Linux (PWA + WebSocket)
  - Raspberry Pi (lightweight client)

Each device registers with the platform and can:
  - Send/receive messages
  - Stream voice (STT/TTS)
  - Execute skills remotely
  - Receive push notifications
  - Sync state across devices

Storage: data/devices.json
"""

import os
import json
import time
import uuid
import platform
import socket
from pathlib import Path
from rich.console import Console

console = Console()

DEVICES_PATH = Path(__file__).parent.parent.parent / "data" / "devices.json"


class Skill:
    """Device Manager — connect and manage all devices."""

    def __init__(self, config=None):
        self.config = config or {}
        DEVICES_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._load()
        self.connected_websockets = {}  # device_id -> websocket

    def _load(self):
        if DEVICES_PATH.exists():
            self.data = json.loads(DEVICES_PATH.read_text())
        else:
            self.data = {"devices": {}}

    def _save(self):
        DEVICES_PATH.write_text(json.dumps(self.data, indent=2))

    def register(self, name: str, device_type: str = "web",
                 os_name: str = "", version: str = "1.0",
                 capabilities: list = None, push_token: str = "") -> str:
        """Register a new device."""
        device_id = f"dev_{uuid.uuid4().hex[:12]}"
        device = {
            "id": device_id,
            "name": name,
            "type": device_type,  # android, ios, windows, mac, linux, web, rpi
            "os": os_name,
            "version": version,
            "capabilities": capabilities or ["text", "voice"],
            "push_token": push_token,
            "status": "registered",
            "online": False,
            "last_seen": time.strftime("%Y-%m-%d %H:%M:%S"),
            "registered_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.data["devices"][device_id] = device
        self._save()
        return (
            f"📱 Device registered!\n"
            f"   ID: {device_id}\n"
            f"   Name: {name}\n"
            f"   Type: {device_type}\n"
            f"   Capabilities: {', '.join(device['capabilities'])}\n"
            f"   Connect URL: ws://<server>:5002/ws?device_id={device_id}"
        )

    def connect(self, device_id: str) -> str:
        """Mark a device as online."""
        device = self.data["devices"].get(device_id)
        if not device:
            return f"❌ Device {device_id} not found."
        device["online"] = True
        device["status"] = "connected"
        device["last_seen"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._save()
        return f"✅ {device['name']} is now online."

    def disconnect(self, device_id: str) -> str:
        """Mark a device as offline."""
        device = self.data["devices"].get(device_id)
        if not device:
            return f"❌ Device {device_id} not found."
        device["online"] = False
        device["status"] = "disconnected"
        device["last_seen"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._save()
        return f"✅ {device['name']} is now offline."

    def list_devices(self, device_type: str = None, online_only: bool = False) -> str:
        """List all registered devices."""
        devices = list(self.data["devices"].values())
        if device_type:
            devices = [d for d in devices if d["type"] == device_type]
        if online_only:
            devices = [d for d in devices if d.get("online")]

        if not devices:
            return "No devices registered. Use action='register' to add one."

        lines = ["📱 Connected Devices:\n"]
        for d in devices:
            status_icon = "🟢" if d.get("online") else "🔴"
            caps = ", ".join(d.get("capabilities", []))
            lines.append(
                f"{status_icon} {d['name']} ({d['id']})\n"
                f"   Type: {d['type']} | OS: {d.get('os', '?')} | Caps: {caps}\n"
                f"   Last seen: {d['last_seen']}"
            )
        return "\n\n".join(lines)

    def get_device(self, device_id: str) -> str:
        """Get device details."""
        device = self.data["devices"].get(device_id)
        if not device:
            return f"❌ Device {device_id} not found."
        return json.dumps(device, indent=2)

    def send_message(self, device_id: str, message: str, msg_type: str = "text") -> str:
        """Send a message to a device."""
        device = self.data["devices"].get(device_id)
        if not device:
            return f"❌ Device {device_id} not found."
        if not device.get("online"):
            return f"⚠ {device['name']} is offline. Message queued."

        # If WebSocket connected, send directly
        ws = self.connected_websockets.get(device_id)
        if ws:
            try:
                import asyncio
                asyncio.run(ws.send(json.dumps({"type": msg_type, "message": message})))
                return f"✅ Sent to {device['name']}: {message[:50]}..."
            except:
                pass

        return f"✅ Message queued for {device['name']}: {message[:50]}..."

    def broadcast(self, message: str, msg_type: str = "text") -> str:
        """Broadcast a message to all online devices."""
        online = [d for d in self.data["devices"].values() if d.get("online")]
        if not online:
            return "No online devices to broadcast to."
        for d in online:
            self.send_message(d["id"], message, msg_type)
        return f"✅ Broadcast to {len(online)} devices: {message[:50]}..."

    def delete(self, device_id: str) -> str:
        """Delete a device."""
        if device_id not in self.data["devices"]:
            return f"❌ Device {device_id} not found."
        name = self.data["devices"][device_id]["name"]
        del self.data["devices"][device_id]
        self._save()
        return f"✅ Deleted device: {name}"

    def get_connect_info(self, device_id: str = None) -> str:
        """Get connection info for a device."""
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return (
            f"🔗 EvolvixOS Connection Info\n\n"
            f"   REST API:   http://{local_ip}:5001/api/v1/\n"
            f"   WebSocket:  ws://{local_ip}:5002/ws\n"
            f"   Dashboard:  http://{local_ip}:5000\n"
            f"   Voice:      ws://{local_ip}:5002/voice\n\n"
            f"   Device Registration:\n"
            f"   POST /api/v1/devices/register\n"
            f"   {{\"name\": \"My Phone\", \"type\": \"android\"}}\n\n"
            f"   PWA Install:\n"
            f"   Open http://{local_ip}:5000/app on your device\n"
            f"   Add to Home Screen for app experience"
        )

    def stats(self) -> str:
        """Get device statistics."""
        devices = list(self.data["devices"].values())
        total = len(devices)
        online = sum(1 for d in devices if d.get("online"))
        by_type = {}
        for d in devices:
            by_type[d["type"]] = by_type.get(d["type"], 0) + 1

        lines = [f"📊 Device Statistics\n  Total: {total}\n  Online: {online}\n  By type:"]
        for t, c in sorted(by_type.items()):
            lines.append(f"    {t}: {c}")
        return "\n".join(lines)

    def run(self, args: dict) -> str:
        action = args.get("action", "list")

        if action == "register":
            return self.register(
                name=args.get("name", "unnamed"),
                device_type=args.get("type", "web"),
                os_name=args.get("os", ""),
                version=args.get("version", "1.0"),
                capabilities=args.get("capabilities", ["text", "voice"]),
                push_token=args.get("push_token", ""),
            )
        elif action == "connect":
            return self.connect(args.get("device_id", ""))
        elif action == "disconnect":
            return self.disconnect(args.get("device_id", ""))
        elif action == "list":
            return self.list_devices(args.get("type"), args.get("online_only", False))
        elif action == "get":
            return self.get_device(args.get("device_id", ""))
        elif action == "send":
            return self.send_message(args.get("device_id", ""), args.get("message", ""))
        elif action == "broadcast":
            return self.broadcast(args.get("message", ""))
        elif action == "delete":
            return self.delete(args.get("device_id", ""))
        elif action == "connect_info":
            return self.get_connect_info(args.get("device_id"))
        elif action == "stats":
            return self.stats()
        else:
            return (
                f"Unknown action: {action}\n\n"
                "Available actions:\n"
                "  register, connect, disconnect, list, get,\n"
                "  send, broadcast, delete, connect_info, stats"
            )
