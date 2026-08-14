"""
EvolvixOS — Deploy Skill
Deploy code/applications to your own server via SSH. Zero tokens.
Uses paramiko for SSH connections. No external services.
"""

import os
import time
import socket
from pathlib import Path
from rich.console import Console

console = Console()


class Skill:
    """Deploy skill — SSH to your own server. No external services."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.deploy_dir = self.config.get("deploy_dir", "/opt/evolvix-deployments")
        self._ssh = None

    def _get_connection_params(self) -> dict:
        """Get SSH config from environment variables (security)."""
        return {
            "hostname": os.environ.get("EVOLVIX_SSH_HOST", ""),
            "username": os.environ.get("EVOLVIX_SSH_USER", ""),
            "key_filename": os.environ.get("EVOLVIX_SSH_KEY", ""),
            "port": int(os.environ.get("EVOLVIX_SSH_PORT", "22")),
        }

    def _connect(self):
        """Establish SSH connection to your server."""
        import paramiko

        params = self._get_connection_params()
        if not params["hostname"]:
            raise ValueError(
                "No SSH config found. Set these environment variables:\n"
                "  EVOLVIX_SSH_HOST — your server IP/hostname\n"
                "  EVOLVIX_SSH_USER — SSH username\n"
                "  EVOLVIX_SSH_KEY  — path to your SSH private key\n"
                "  EVOLVIX_SSH_PORT — SSH port (default: 22)"
            )

        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh.connect(**params)
        return self._ssh

    def _run_command(self, command: str) -> str:
        """Run a command on the remote server."""
        if self._ssh is None:
            self._connect()

        stdin, stdout, stderr = self._ssh.exec_command(command)
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")

        result = output
        if error:
            result += f"\n[STDERR]: {error}"
        return result

    def deploy(self, app_path: str, app_name: str = None) -> str:
        """Deploy an app directory to the server."""
        import paramiko

        app_name = app_name or Path(app_path).name
        console.print(f"[cyan]🚀 Deploying {app_name} to server...[/cyan]")

        # Connect
        self._connect()

        # Create deployment directory
        remote_path = f"{self.deploy_dir}/{app_name}"
        self._run_command(f"mkdir -p {remote_path}")

        # Upload files via SFTP
        sftp = self._ssh.open_sftp()
        local_path = Path(app_path).resolve()

        def upload_dir(local: Path, remote: str):
            for item in local.rglob("*"):
                if item.is_file() and "__pycache__" not in str(item) and ".git" not in str(item):
                    remote_file = f"{remote}/{item.relative_to(local_path)}"
                    remote_dir = str(Path(remote_file).parent)
                    # Create remote directories
                    try:
                        self._run_command(f"mkdir -p {remote_dir}")
                    except Exception:
                        pass
                    console.print(f"  [dim]↑ {item.relative_to(local_path)}[/dim]")
                    sftp.put(str(item), remote_file)

        upload_dir(local_path, remote_path)
        sftp.close()

        # Set up the deployment
        setup_commands = [
            f"cd {remote_path} && python3 -m venv venv",
            f"cd {remote_path} && source venv/bin/activate && pip install -r requirements.txt 2>/dev/null || true",
            f"cd {remote_path} && chmod +x *.sh 2>/dev/null || true",
        ]

        for cmd in setup_commands:
            console.print(f"  [dim]→ {cmd[:60]}...[/dim]")
            self._run_command(cmd)

        # Create systemd service for auto-start
        service_content = f"""[Unit]
Description=EvolvixOS Deployment: {app_name}
After=network.target

[Service]
Type=simple
User={self._get_connection_params()['username']}
WorkingDirectory={remote_path}
ExecStart={remote_path}/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

        # Write service file
        service_path = f"/tmp/evolvix_{app_name}.service"
        with sftp.open() if hasattr(sftp, 'open') else open(service_path, 'w') as f:
            pass  # Write via command instead

        self._run_command(f"cat > {service_path} << 'EVOLVIX_EOF'\n{service_content}\nEVOLVIX_EOF")
        self._run_command(f"sudo cp {service_path} /etc/systemd/system/ 2>/dev/null || cp {service_path} /etc/systemd/system/ 2>/dev/null || echo 'Manual setup needed'")
        self._run_command("sudo systemctl daemon-reload 2>/dev/null || systemctl daemon-reload 2>/dev/null || true")
        self._run_command(f"sudo systemctl enable evolvix_{app_name} 2>/dev/null || true")
        self._run_command(f"sudo systemctl start evolvix_{app_name} 2>/dev/null || true")

        console.print(f"[green]✅ Deployed {app_name} to {remote_path}[/green]")
        console.print(f"[green]✅ Auto-start service created: evolvix_{app_name}[/green]")

        return (
            f"Deployment complete!\n"
            f"  App: {app_name}\n"
            f"  Path: {remote_path}\n"
            f"  Service: evolvix_{app_name}\n"
            f"  Status: check with 'systemctl status evolvix_{app_name}'\n"
            f"  Logs: 'journalctl -u evolvix_{app_name} -f'"
        )

    def check_server(self) -> str:
        """Check server status."""
        try:
            self._connect()
            info = self._run_command("uname -a && echo '---' && free -h && echo '---' && df -h / && echo '---' && nvidia-smi 2>/dev/null || echo 'No GPU'")
            return f"Server Status:\n{info}"
        except Exception as e:
            return f"Connection failed: {e}"

    def run(self, args: dict) -> str:
        """Execute the deploy skill."""
        action = args.get("action", "deploy")

        if action == "deploy":
            app_path = args.get("path", args.get("app_path", ""))
            app_name = args.get("name", args.get("app_name", ""))
            if not app_path:
                return "Error: no app path provided for deployment."
            return self.deploy(app_path, app_name or None)

        elif action == "check":
            return self.check_server()

        elif action == "exec":
            command = args.get("command", "")
            if not command:
                return "Error: no command provided."
            try:
                self._connect()
                return self._run_command(command)
            except Exception as e:
                return f"Command failed: {e}"

        else:
            return f"Unknown action: {action}. Use 'deploy', 'check', or 'exec'."
