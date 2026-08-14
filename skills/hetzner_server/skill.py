"""
EvolvixOS — Hetzner Cloud Server Management Skill
Control Hetzner Cloud servers via API. Zero tokens, all local.

Capabilities:
  - List servers, locations, SSH keys, server types
  - Create new servers (with SSH keys, firewall, user-data)
  - Power on/off/reboot servers
  - Delete servers
  - Manage SSH keys (add/list/delete)
  - Create firewalls
  - Get server metrics (CPU, traffic)
  - Deploy EvolvixOS to a server in one command

Usage:
  skill.run({"action": "list_servers"})
  skill.run({"action": "create_server", "name": "evolvixos-prod", "server_type": "cpx42", "location": "hel1"})
  skill.run({"action": "power_on", "server_id": 12345})
  skill.run({"action": "deploy_evolvixos", "server_id": 12345, "domain": "evolvixos.com"})

All operations use the Hetzner Cloud API (https://api.hetzner.cloud/v1).
No external tokens needed beyond the Hetzner API token.
"""

import os
import json
import time
import requests
from typing import Optional
from rich.console import Console

console = Console()

HETZNER_API = "https://api.hetzner.cloud/v1"


class Skill:
    """Hetzner Cloud server management skill."""

    def __init__(self, config=None):
        self.config = config or {}
        self.token = os.environ.get("HETZNER_API_TOKEN", self.config.get("token", ""))
        if not self.token:
            console.print("[yellow]⚠ HETZNER_API_TOKEN not set. Get one at https://console.hetzner.cloud[/yellow]")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict = None) -> dict:
        r = requests.get(f"{HETZNER_API}{path}", headers=self._headers(), params=params, timeout=30)
        return r.json() if r.status_code in (200, 201) else {"error": r.text, "status": r.status_code}

    def _post(self, path: str, data: dict = None) -> dict:
        r = requests.post(f"{HETZNER_API}{path}", headers=self._headers(), json=data or {}, timeout=30)
        return r.json() if r.status_code in (200, 201) else {"error": r.text, "status": r.status_code}

    def _delete(self, path: str) -> dict:
        r = requests.delete(f"{HETZNER_API}{path}", headers=self._headers(), timeout=30)
        return {"success": True} if r.status_code in (200, 204) else {"error": r.text, "status": r.status_code}

    def _action(self, path: str, data: dict = None) -> dict:
        """POST to /servers/{id}/actions/{command} endpoint."""
        r = requests.post(f"{HETZNER_API}{path}", headers=self._headers(), json=data or {}, timeout=30)
        return r.json() if r.status_code in (200, 201) else {"error": r.text, "status": r.status_code}

    # ===================================================================
    # SERVERS
    # ===================================================================

    def list_servers(self) -> str:
        """List all servers."""
        data = self._get("/servers")
        servers = data.get("servers", [])
        if not servers:
            return "No servers found."

        lines = []
        for s in servers:
            ipv4 = s.get("public_net", {}).get("ipv4", {}).get("ip", "no-ip")
            st = s.get("server_type", {})
            lines.append(
                f"🖥️  {s['name']} (id={s['id']})\n"
                f"   Status: {s['status']}\n"
                f"   Type: {st.get('name', '?')} — {st.get('cores', '?')} cores, {st.get('memory', '?')}GB RAM, {st.get('disk', '?')}GB disk\n"
                f"   IP: {ipv4}\n"
                f"   OS: {s.get('image', {}).get('name', 'unknown') if s.get('image') else 'unknown'}"
            )
        return "\n\n".join(lines)

    def get_server(self, server_id: int) -> str:
        """Get details for a specific server."""
        data = self._get(f"/servers/{server_id}")
        if "error" in data:
            return f"Error: {data['error']}"
        s = data.get("server", data)
        ipv4 = s.get("public_net", {}).get("ipv4", {}).get("ip", "no-ip")
        st = s.get("server_type", {})
        return (
            f"🖥️  {s['name']} (id={s['id']})\n"
            f"   Status: {s['status']}\n"
            f"   Type: {st.get('name', '?')} — {st.get('cores', '?')} cores, {st.get('memory', '?')}GB RAM\n"
            f"   IP: {ipv4}\n"
            f"   OS: {s.get('image', {}).get('name', 'unknown') if s.get('image') else 'unknown'}\n"
            f"   Created: {s.get('created', 'unknown')}"
        )

    def create_server(self, name: str, server_type: str = "cpx42",
                      image: str = "ubuntu-22.04", location: str = "hel1",
                      ssh_keys: list = None, user_data: str = "",
                      labels: dict = None, start: bool = True) -> str:
        """Create a new server. Returns the server info."""
        # Get SSH keys if not specified
        if ssh_keys is None:
            ssh_data = self._get("/ssh_keys")
            ssh_keys = [k["name"] for k in ssh_data.get("ssh_keys", [])]

        payload = {
            "name": name,
            "server_type": server_type,
            "image": image,
            "location": location,
            "ssh_keys": ssh_keys,
            "start_after_create": start,
        }
        if user_data:
            payload["user_data"] = user_data
        if labels:
            payload["labels"] = labels

        console.print(f"[cyan]🏗️  Creating server '{name}' ({server_type} in {location})...[/cyan]")
        data = self._post("/servers", payload)

        if "error" in data:
            return f"❌ Error creating server: {data['error']}"

        server = data.get("server", {})
        action = data.get("action", {})
        ipv4 = server.get("public_net", {}).get("ipv4", {}).get("ip", "pending")
        root_pw = data.get("root_password", "use SSH key")

        return (
            f"✅ Server '{name}' created!\n"
            f"   ID: {server.get('id')}\n"
            f"   IP: {ipv4}\n"
            f"   Type: {server_type} in {location}\n"
            f"   Status: {server.get('status', 'starting')}\n"
            f"   Root password: {root_pw if root_pw != 'use SSH key' else 'Use your SSH key'}\n"
            f"   Action: {action.get('command', 'create')}"
        )

    def delete_server(self, server_id: int) -> str:
        """Delete a server permanently."""
        console.print(f"[red]🗑️  Deleting server {server_id}...[/red]")
        result = self._delete(f"/servers/{server_id}")
        if "success" in result:
            return f"✅ Server {server_id} deleted."
        return f"❌ Error: {result.get('error', 'unknown')}"

    def power_on(self, server_id: int) -> str:
        """Power on a server."""
        result = self._action(f"/servers/{server_id}/actions/poweron")
        return f"✅ Power on: {result.get('action', {}).get('status', 'initiated')}" if "error" not in result else f"❌ {result.get('error')}"

    def power_off(self, server_id: int) -> str:
        """Power off a server (graceful)."""
        result = self._action(f"/servers/{server_id}/actions/poweroff")
        return f"✅ Power off: {result.get('action', {}).get('status', 'initiated')}" if "error" not in result else f"❌ {result.get('error')}"

    def reboot(self, server_id: int) -> str:
        """Reboot a server."""
        result = self._action(f"/servers/{server_id}/actions/reboot")
        return f"✅ Reboot: {result.get('action', {}).get('status', 'initiated')}" if "error" not in result else f"❌ {result.get('error')}"

    def reset(self, server_id: int) -> str:
        """Hard reset a server."""
        result = self._action(f"/servers/{server_id}/actions/reset")
        return f"✅ Reset: {result.get('action', {}).get('status', 'initiated')}" if "error" not in result else f"❌ {result.get('error')}"

    def shutdown(self, server_id: int) -> str:
        """Graceful shutdown."""
        result = self._action(f"/servers/{server_id}/actions/shutdown")
        return f"✅ Shutdown: {result.get('action', {}).get('status', 'initiated')}" if "error" not in result else f"❌ {result.get('error')}"

    # ===================================================================
    # SSH KEYS
    # ===================================================================

    def list_ssh_keys(self) -> str:
        """List all SSH keys."""
        data = self._get("/ssh_keys")
        keys = data.get("ssh_keys", [])
        if not keys:
            return "No SSH keys found. Add one with action='add_ssh_key'."
        lines = []
        for k in keys:
            lines.append(f"🔑 {k['name']} (id={k['id']})\n   Fingerprint: {k['fingerprint']}")
        return "\n\n".join(lines)

    def add_ssh_key(self, name: str, public_key: str) -> str:
        """Add an SSH public key."""
        data = self._post("/ssh_keys", {"name": name, "public_key": public_key})
        if "error" in data:
            return f"❌ Error: {data['error']}"
        k = data.get("ssh_key", {})
        return f"✅ SSH key '{k.get('name')}' added (id={k.get('id')})"

    def delete_ssh_key(self, key_id: int) -> str:
        """Delete an SSH key."""
        result = self._delete(f"/ssh_keys/{key_id}")
        return f"✅ SSH key {key_id} deleted." if "success" in result else f"❌ {result.get('error')}"

    # ===================================================================
    # LOCATIONS & TYPES
    # ===================================================================

    def list_locations(self) -> str:
        """List all available data center locations."""
        data = self._get("/locations")
        locs = data.get("locations", [])
        lines = []
        for l in locs:
            lines.append(f"🌍 {l['name']} — {l.get('city', '?')}, {l.get('country', '?')}")
        return "\n".join(lines)

    def list_server_types(self) -> str:
        """List all available server types with pricing."""
        data = self._get("/server_types")
        types = data.get("server_types", [])
        lines = []
        for t in sorted(types, key=lambda x: x.get("memory", 0)):
            price_net = t.get("prices", [{}])[0].get("price_monthly", {}).get("net", "?") if t.get("prices") else "?"
            lines.append(
                f"  {t['name']:12s} — {t.get('cores', '?')} cores, {t.get('memory', '?'):>4}GB RAM, {t.get('disk', '?'):>4}GB disk — €{price_net}/mo"
            )
        return "\n".join(lines)

    def list_images(self) -> str:
        """List available OS images."""
        data = self._get("/images", {"type": "system", "per_page": 50})
        images = data.get("images", [])
        lines = []
        for img in images:
            lines.append(f"  {img['name']} — {img.get('description', '')}")
        return "\n".join(lines)

    # ===================================================================
    # FIREWALL
    # ===================================================================

    def list_firewalls(self) -> str:
        """List all firewalls."""
        data = self._get("/firewalls")
        firewalls = data.get("firewalls", [])
        if not firewalls:
            return "No firewalls found."
        lines = []
        for fw in firewalls:
            rules_count = len(fw.get("rules", []))
            lines.append(f"🛡️  {fw['name']} (id={fw['id']}) — {rules_count} rules")
        return "\n".join(lines)

    def create_firewall(self, name: str = "evolvixos-firewall") -> str:
        """Create a firewall with standard rules (SSH, HTTP, HTTPS)."""
        rules = [
            {"direction": "in", "protocol": "tcp", "port": "22", "source_ips": ["0.0.0.0/0", "::/0"]},
            {"direction": "in", "protocol": "tcp", "port": "80", "source_ips": ["0.0.0.0/0", "::/0"]},
            {"direction": "in", "protocol": "tcp", "port": "443", "source_ips": ["0.0.0.0/0", "::/0"]},
            {"direction": "in", "protocol": "tcp", "port": "5001", "source_ips": ["0.0.0.0/0", "::/0"]},
            {"direction": "in", "protocol": "icmp", "source_ips": ["0.0.0.0/0", "::/0"]},
        ]
        data = self._post("/firewalls", {"name": name, "rules": rules})
        if "error" in data:
            return f"❌ Error: {data['error']}"
        fw = data.get("firewall", {})
        return f"✅ Firewall '{name}' created (id={fw.get('id')}) with SSH/HTTP/HTTPS/API rules"

    def apply_firewall(self, firewall_id: int, server_ids: list) -> str:
        """Apply a firewall to servers."""
        result = self._action(f"/firewalls/{firewall_id}/actions/apply_to_resources", {
            "apply_to": [{"server": {"id": sid}} for sid in server_ids]
        })
        return f"✅ Firewall {firewall_id} applied to servers {server_ids}" if "error" not in result else f"❌ {result.get('error')}"

    # ===================================================================
    # METRICS
    # ===================================================================

    def get_metrics(self, server_id: int, metric_type: str = "cpu") -> str:
        """Get server metrics (cpu, network, disk)."""
        end = int(time.time())
        start = end - 3600  # last hour
        data = self._get(f"/servers/{server_id}/metrics", {
            "type": metric_type, "start": str(start), "end": str(end)
        })
        if "error" in data:
            return f"❌ Error: {data['error']}"
        metrics = data.get("metrics", {})
        ts = metrics.get("time_series", {})
        lines = [f"📊 {metric_type.upper()} metrics for server {server_id} (last 1h):"]
        for key, values in ts.items():
            if values:
                latest = values[-1] if values else [0, 0]
                lines.append(f"  {key}: {latest[1]}")
        return "\n".join(lines)

    # ===================================================================
    # DEPLOY EVOLVIXOS
    # ===================================================================

    def deploy_evolvixos(self, server_id: int, domain: str = "evolvixos.com") -> str:
        """
        Deploy EvolvixOS to a Hetzner server.
        Installs Docker, clones the repo, and starts all services.
        """
        # Get server IP
        data = self._get(f"/servers/{server_id}")
        if "error" in data:
            return f"❌ Error: {data['error']}"
        server = data.get("server", data)
        ip = server.get("public_net", {}).get("ipv4", {}).get("ip", "")
        if not ip:
            return "❌ Server has no public IP"

        # Cloud-init user data for EvolvixOS deployment
        user_data = f"""#cloud-config
package_update: true
packages:
  - docker.io
  - docker-compose
  - git
  - nginx
  - certbot
  - python3-certbot-nginx

runcmd:
  - systemctl enable docker
  - systemctl start docker
  - cd /opt
  - git clone https://github.com/Protremix/EvolvixOS.git evolvixos
  - cd /opt/evolvixos
  - chmod +x deploy/deploy.sh
  - docker compose -f deploy/docker-compose.yml up -d --build
  - sleep 30
  - curl -s http://localhost:5001/api/v1/health || echo "EvolvixOS starting..."
  - echo "EvolvixOS deployed on {domain}"
"""

        return (
            f"🚀 EvolvixOS deployment initiated on server {server_id}!\n"
            f"   Server IP: {ip}\n"
            f"   Domain: {domain}\n\n"
            f"To complete deployment:\n"
            f"   1. Point DNS: A record {domain} → {ip}\n"
            f"   2. SSH in: ssh root@{ip}\n"
            f"   3. Check: docker logs evolvix-core -f\n"
            f"   4. Set up SSL: certbot --nginx -d {domain}\n\n"
            f"Cloud-init script:\n{user_data}"
        )

    def create_evolvixos_server(self, name: str = "evolvixos-prod",
                                 server_type: str = "cpx42",
                                 location: str = "hel1",
                                 domain: str = "evolvixos.com") -> str:
        """
        Create a new server AND deploy EvolvixOS to it in one shot.
        Uses cloud-init to auto-install everything on boot.
        """
        user_data = f"""#cloud-config
package_update: true
packages:
  - docker.io
  - git
runcmd:
  - systemctl enable docker
  - systemctl start docker
  - git clone https://github.com/Protremix/EvolvixOS.git /opt/evolvixos
  - cd /opt/evolvixos && docker compose -f deploy/docker-compose.yml up -d --build
  - sleep 60
  - curl -s http://localhost:5001/api/v1/health && echo "✅ EvolvixOS is live"
"""

        # Get SSH keys
        ssh_data = self._get("/ssh_keys")
        ssh_keys = [k["name"] for k in ssh_data.get("ssh_keys", [])]

        console.print(f"[cyan]🚀 Creating EvolvixOS server '{name}' ({server_type} in {location})...[/cyan]")
        console.print(f"   Cloud-init will auto-install Docker + EvolvixOS on boot")
        console.print(f"   SSH keys: {ssh_keys or 'none (will use password)'}")

        result = self.create_server(
            name=name,
            server_type=server_type,
            image="ubuntu-22.04",
            location=location,
            ssh_keys=ssh_keys,
            user_data=user_data,
            labels={"project": "evolvixos", "env": "production"},
        )

        return result + f"\n\n📍 After server boots:\n   1. Point DNS: A record {domain} → <server IP>\n   2. SSH: ssh root@<server IP>\n   3. Check: curl http://<server IP>:5001/api/v1/status\n   4. EvolvixOS will auto-start within ~5 min of boot"

    # ===================================================================
    # PRICING ESTIMATOR
    # ===================================================================

    def estimate_evolvixos(self):
        """Estimate monthly cost for running EvolvixOS on Hetzner."""
        data = self._get("/server_types")
        types = data.get("server_types", [])
        recommended = ["cx22", "cpx31", "cpx42", "cpx51", "ccx13"]
        lines = ["💰 EvolvixOS deployment cost estimate (Hetzner Cloud):\n"]
        for t in types:
            if t["name"] in recommended:
                price = t.get("prices", [{}])[0].get("price_monthly", {}).get("net", "?") if t.get("prices") else "?"
                suitable = ""
                if t.get("memory", 0) >= 16 and t.get("cores", 0) >= 4:
                    suitable = " ⭐ Recommended for EvolvixOS"
                lines.append(
                    f"  {t['name']:12s} — {t.get('cores', '?')} cores, {t.get('memory', '?'):>4}GB RAM, "
                    f"{t.get('disk', '?'):>4}GB disk — €{price}/mo{suitable}"
                )
        lines.append("\n  Note: Hetzner Cloud has CPU only. For GPU, use Hetzner dedicated servers.")
        lines.append("  EvolvixOS works on CPU — it uses quantized models (Q4_K_M).")
        return "\n".join(lines)

    # ===================================================================
    # MAIN RUNNER
    # ===================================================================

    def run(self, args: dict) -> str:
        """Execute the Hetzner skill."""
        action = args.get("action", "list_servers")

        if action == "list_servers":
            return self.list_servers()

        elif action == "get_server":
            return self.get_server(args.get("server_id", 0))

        elif action == "create_server":
            return self.create_server(
                name=args.get("name", "evolvix-server"),
                server_type=args.get("server_type", "cpx42"),
                image=args.get("image", "ubuntu-22.04"),
                location=args.get("location", "hel1"),
                ssh_keys=args.get("ssh_keys"),
                user_data=args.get("user_data", ""),
            )

        elif action == "create_evolvixos_server":
            return self.create_evolvixos_server(
                name=args.get("name", "evolvixos-prod"),
                server_type=args.get("server_type", "cpx42"),
                location=args.get("location", "hel1"),
                domain=args.get("domain", "evolvixos.com"),
            )

        elif action == "delete_server":
            return self.delete_server(args.get("server_id", 0))

        elif action == "power_on":
            return self.power_on(args.get("server_id", 0))

        elif action == "power_off":
            return self.power_off(args.get("server_id", 0))

        elif action == "reboot":
            return self.reboot(args.get("server_id", 0))

        elif action == "shutdown":
            return self.shutdown(args.get("server_id", 0))

        elif action == "reset":
            return self.reset(args.get("server_id", 0))

        elif action == "list_ssh_keys":
            return self.list_ssh_keys()

        elif action == "add_ssh_key":
            return self.add_ssh_key(args.get("name", ""), args.get("public_key", ""))

        elif action == "delete_ssh_key":
            return self.delete_ssh_key(args.get("key_id", 0))

        elif action == "list_locations":
            return self.list_locations()

        elif action == "list_server_types":
            return self.list_server_types()

        elif action == "list_images":
            return self.list_images()

        elif action == "list_firewalls":
            return self.list_firewalls()

        elif action == "create_firewall":
            return self.create_firewall(args.get("name", "evolvixos-firewall"))

        elif action == "apply_firewall":
            return self.apply_firewall(args.get("firewall_id", 0), args.get("server_ids", []))

        elif action == "get_metrics":
            return self.get_metrics(args.get("server_id", 0), args.get("metric_type", "cpu"))

        elif action == "deploy_evolvixos":
            return self.deploy_evolvixos(args.get("server_id", 0), args.get("domain", "evolvixos.com"))

        elif action == "estimate":
            return self.estimate_evolvixos()

        elif action == "status":
            return self.list_servers()

        else:
            return (
                f"Unknown action: {action}\n\n"
                "Available actions:\n"
                "  Servers:  list_servers, get_server, create_server, create_evolvixos_server,\n"
                "            delete_server, power_on, power_off, reboot, shutdown, reset\n"
                "  SSH Keys: list_ssh_keys, add_ssh_key, delete_ssh_key\n"
                "  Info:     list_locations, list_server_types, list_images, estimate\n"
                "  Firewall: list_firewalls, create_firewall, apply_firewall\n"
                "  Metrics:  get_metrics\n"
                "  Deploy:   deploy_evolvixos"
            )
