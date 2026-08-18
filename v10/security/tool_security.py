"""
EvolvixOS v10 — Tool Security Framework
========================================
Every dangerous tool must declare:
  - permission required
  - input validation rules
  - timeout
  - rate limit
  - audit log entry
  - allowed paths/hosts/commands
  - error handling

AI must NOT get unrestricted root/system access.
"""

from __future__ import annotations
import enum
import re
import os
import time
import json
import shlex
import logging
import ipaddress
import subprocess
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("evolvixos.v10.security")


# --- Permission Levels ---

class Permission(enum.Enum):
    """Tool permission levels — escalating trust."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    SYSTEM = "system"
    NETWORK = "network"
    ADMIN = "admin"

    @classmethod
    def from_str(cls, s: str) -> "Permission":
        try:
            return cls[s.upper()]
        except KeyError:
            raise ValueError(f"Invalid permission: {s!r}")


# --- Tool Definition ---

@dataclass
class ToolSpec:
    """Security specification for a tool."""
    name: str
    permission: Permission
    timeout: int = 120
    rate_limit: int = 30
    allowed_paths: list = field(default_factory=list)
    allowed_hosts: list = field(default_factory=list)
    blocked_commands: list = field(default_factory=list)
    allowed_commands: list = field(default_factory=list)
    requires_user_scope: bool = False


# --- Tool Registry ---

TOOL_SPECS: dict[str, ToolSpec] = {}


def register_tool(spec: ToolSpec):
    TOOL_SPECS[spec.name] = spec
    logger.info(f"Registered tool: {spec.name} (permission={spec.permission.value})")


def get_tool_spec(name: str) -> Optional[ToolSpec]:
    return TOOL_SPECS.get(name)


def check_permission(name: str, user_role: str = "user") -> tuple[bool, str]:
    """Check if user role allows using this tool."""
    spec = get_tool_spec(name)
    if not spec:
        return False, f"Unknown tool: {name}"

    if user_role == "admin":
        return True, "OK"

    if spec.permission in (Permission.SYSTEM, Permission.ADMIN):
        return False, f"Permission denied: {name} requires admin role"

    return True, "OK"


# --- Audit Log ---

@dataclass
class AuditEntry:
    timestamp: float
    user_id: str
    tool_name: str
    permission: str
    args_summary: str
    result: str
    duration_ms: float
    detail: str = ""


_audit_log: list[AuditEntry] = []
_audit_lock = __import__("threading").Lock()


def log_audit(user_id: str, tool_name: str, permission: str,
              args_summary: str, result: str, duration_ms: float, detail: str = ""):
    with _audit_lock:
        entry = AuditEntry(
            timestamp=time.time(),
            user_id=user_id,
            tool_name=tool_name,
            permission=permission,
            args_summary=args_summary[:200],
            result=result,
            duration_ms=duration_ms,
            detail=detail[:500]
        )
        _audit_log.append(entry)
        if len(_audit_log) > 10000:
            del _audit_log[:5000]
    logger.info(f"AUDIT: user={user_id} tool={tool_name} result={result} "
                f"duration={duration_ms:.0f}ms")


def get_audit_log(limit: int = 100, user_id: str = None) -> list[dict]:
    with _audit_lock:
        entries = _audit_log[-limit:]
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        return [
            {
                "timestamp": e.timestamp,
                "user_id": e.user_id,
                "tool": e.tool_name,
                "permission": e.permission,
                "result": e.result,
                "duration_ms": e.duration_ms,
                "detail": e.detail,
            }
            for e in entries
        ]


# --- Path Validation ---

def validate_path(path: str, allowed_bases: list, user_scope: str = None) -> tuple[bool, str]:
    """
    Validate a filesystem path is within allowed directories.
    Returns (ok, resolved_path or error_message).
    """
    if not path:
        return False, "Empty path"

    try:
        resolved = os.path.realpath(os.path.expanduser(path))
    except Exception as e:
        return False, f"Path resolution error: {e}"

    for base in allowed_bases:
        base_resolved = os.path.realpath(base)
        if resolved.startswith(base_resolved):
            if user_scope:
                user_dir = os.path.join(base_resolved, user_scope)
                if not resolved.startswith(user_dir):
                    return False, f"Path outside user scope: {resolved}"
            return True, resolved

    return False, f"Path '{path}' resolves to '{resolved}' — outside allowed directories"


# --- Command Validation ---

# Dangerous command patterns (extended from v9)
DANGEROUS_PATTERNS = [
    # rm -rf in all forms
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+~",
    r"rm\s+-rf\s+--no-preserve-root",
    r"rm\s+-rf\s+\*",
    r"rm\s+-rf\s+\$HOME",
    # disk operations
    r"m\W*k\W*f\W*s",
    r"dd\s+if=",
    r"dd\s+.*of=\s*/dev/sd",
    r">\s*/dev/sd",
    # system control
    r"shutdown|reboot|halt",
    r"\binit\s+[06]\b",
    r"kill\s+-9\s+1\b",
    r"killall\s+",
    # privilege escalation
    r"\bsudo\s",
    r"\bsu\s+root\b",
    r"chmod\s+777\s+/",
    r"chmod\s+\+s\s",
    r"chown\s+.*\s+/",
    # network exfiltration
    r"curl\s+http",
    r"wget\s+http",
    r"nc\s+-e\s",
    r"netcat\s",
    r"bash\s+-i\s+>&\s*/dev/tcp",
    r"/dev/tcp/",
    # fork bomb
    r":\(\)\{\s*:\s*\|\s*:&\s*\};:",
    # pipe to shell
    r"curl.*\|\s*(bash|sh)",
    r"wget.*\|\s*(bash|sh)",
    # python code injection via command
    r"python3?\s+-c\s+.*import\s+os",
    r"python3?\s+-c\s+.*import\s+subprocess",
    r"python3?\s+-c\s+.*__import__",
    # dangerous functions in command context
    r"eval\s*\(",
    r"exec\s*\(",
    r"subprocess.*shell=True",
    r"os\.system\s*\(",
    r"__import__",
    # sensitive files
    r"/etc/passwd",
    r"/etc/shadow",
    r"/etc/sudoers",
    r"/proc/self/environ",
    r"\.env\b.*grep",
    # file manipulation of system files
    r"mv\s+/etc/",
    r"cp\s+/etc/",
    r"ln\s+-s\s+/etc/",
    r"ln\s+-s\s+/proc/",
    # persistence
    r"crontab\s+-",
    r"echo.*\|\s*crontab",
    # firewall flush
    r"iptables\s+-F",
    # service management
    r"systemctl\s+(stop|disable)\s+(ssh|nginx|evolvix)",
    # env var exfiltration
    r"printenv\s+\w*API",
    r"env\s+\|\s*grep\s+API",
    r"\$\{?\w*API_KEY\}?",
    r"grep.*-i.*key.*model_api",
    # backslash-escaped dangerous commands
    r"rm[\s\\]+-rf[\s\\]+/",
    # .env file access
    r"\.env\b.*(?:cat|grep|less|more|head|tail)",
    r"cat\s+\S*\.env\b",
    # hex-encoded rm -rf (\x72 = r, \x6d = m)
    r"\\x72\\x6d",
    # source file key extraction
    r"grep.*key.*\.py",
    r"grep.*-i.*key.*model_api",
    # broader grep for API keys
    r"\|\s*grep\s+-i.*key",
    r"grep\s+.*\bkey\b.*\.py",
]

_dangerous_re = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]


def validate_command(cmd: str) -> tuple[bool, str]:
    """
    Validate a shell command is safe.
    Returns (ok, command or error_message).
    """
    if not cmd:
        return False, "Empty command"

    for pattern in _dangerous_re:
        if pattern.search(cmd):
            return False, "Blocked: dangerous pattern detected in command"

    try:
        parts = shlex.split(cmd)
    except ValueError as e:
        return False, f"Command parsing error: {e}"

    return True, cmd


def execute_command(cmd: str, timeout: int = 120) -> tuple[str, int]:
    """
    Safely execute a shell command.
    Returns (output, exit_code).
    """
    ok, result = validate_command(cmd)
    if not ok:
        return result, -1

    try:
        parts = shlex.split(cmd)
        proc = subprocess.run(
            parts, shell=False, capture_output=True, text=True, timeout=timeout
        )
        output = proc.stdout
        if proc.stderr:
            output += f"\n[STDERR]\n{proc.stderr}"
        if proc.returncode != 0:
            output += f"\n[EXIT: {proc.returncode}]"
        return output[:8000] if output else "(no output)", proc.returncode
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s", -1
    except Exception as e:
        return f"Error: {e}", -1


# --- URL Validation (SSRF Protection) ---

def validate_url(url: str, allowed_schemes: tuple = ("https", "http")) -> tuple[bool, str]:
    """
    Validate a URL is safe from SSRF attacks.
    Uses the same logic as models/ssrf_guard.py but as a simple sync function.
    """
    if not url:
        return False, "Empty URL"

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in allowed_schemes:
        return False, f"Scheme '{parsed.scheme}' not allowed (must be {allowed_schemes})"

    host = parsed.hostname
    if not host:
        return False, "Missing hostname"

    # Check for IP literals
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False, f"Private/reserved IP address blocked: {host}"
    except ValueError:
        pass

    if host.lower() in ("localhost", "0.0.0.0", "::1", "::"):
        return False, f"Localhost blocked: {host}"

    if host == "169.254.169.254":
        return False, "Cloud metadata endpoint blocked"

    # Block cloud metadata endpoints
    if host.lower() in ("metadata.google.internal", "metadata.azure.com",
                        "100.100.100.200"):
        return False, f"Cloud metadata endpoint blocked: {host}"

    # Block link-local (169.254.x.x) — already caught by is_link_local above
    # but add explicit check for DNS names that resolve to link-local
    try:
        import socket
        resolved = socket.getaddrinfo(host, None, socket.AF_INET)
        for family, _, _, _, sockaddr in resolved:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False, f"Host {host} resolves to private/reserved IP: {sockaddr[0]}"
    except (socket.gaierror, OSError, ValueError):
        pass  # DNS resolution failed — allow but log
    except Exception:
        pass  # Don't block on resolution errors

    return True, url


# --- Python Code Validation ---

PYTHON_DANGEROUS = [
    # imports of dangerous modules
    r"__import__\s*\(",
    r"\bimport\s+os\b",
    r"\bimport\s+subprocess\b",
    r"\bimport\s+pickle\b",
    r"\bimport\s+marshal\b",
    r"\bimport\s+socket\b",
    r"\bfrom\s+os\s+import",
    r"\bfrom\s+subprocess\s+import",
    # dangerous function calls
    r"os\.system\s*\(",
    r"os\.popen\s*\(",
    r"subprocess\.(call|run|Popen)\s*\(",
    r"subprocess\.(call|run|Popen)\s*\(.*shell\s*=\s*True",
    r"eval\s*\(",
    r"exec\s*\(",
    r"compile\s*\(",
    r"pickle\.loads?\s*\(",
    r"marshal\.loads?\s*\(",
    # file access to sensitive paths
    r"open\s*\(\s*['\"]/(etc|proc|sys)",
    r"shutil\.rmtree\s*\(\s*['\"]/",
    r"os\.remove\s*\(\s*['\"]/",
    # network exfiltration from Python
    r"urllib\.request\.urlopen\s*\(\s*['\"]http",
    r"socket\.socket\s*\(",
    r"requests\.get\s*\(\s*['\"]http",
    # env var access
    r"os\.environ\s*\[\s*['\"]\w*API_KEY",
    r"os\.getenv\s*\(\s*['\"]\w*API_KEY",
]

_python_dangerous_re = [re.compile(p, re.IGNORECASE) for p in PYTHON_DANGEROUS]


def validate_python_code(code: str) -> tuple[bool, str]:
    """
    Validate Python code is safe to execute.
    Returns (ok, code or error_message).
    """
    if not code:
        return False, "Empty code"

    for pattern in _python_dangerous_re:
        if pattern.search(code):
            return False, "Blocked: dangerous pattern detected in Python code"

    return True, code


def execute_python(code: str, timeout: int = 120) -> tuple[str, int]:
    """
    Safely execute Python code.
    Returns (output, exit_code).
    """
    ok, result = validate_python_code(code)
    if not ok:
        return result, -1

    try:
        proc = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True, timeout=timeout
        )
        output = proc.stdout
        if proc.stderr:
            output += f"\n[STDERR]\n{proc.stderr}"
        if proc.returncode != 0:
            output += f"\n[EXIT: {proc.returncode}]"
        return output[:8000] if output else "(no output)", proc.returncode
    except subprocess.TimeoutExpired:
        return f"Error: code timed out after {timeout}s", -1
    except Exception as e:
        return f"Error: {e}", -1


# --- Rate Limiting per Tool ---

_tool_rate_limits: dict = {}
_tool_rate_lock = __import__("threading").Lock()


def check_tool_rate(user_id: str, tool_name: str, max_per_min: int = 30) -> bool:
    """Check if user has exceeded rate limit for a specific tool."""
    with _tool_rate_lock:
        key = (user_id, tool_name)
        now = time.time()
        if key not in _tool_rate_limits:
            _tool_rate_limits[key] = []
        _tool_rate_limits[key] = [t for t in _tool_rate_limits[key] if now - t < 60]
        if len(_tool_rate_limits[key]) >= max_per_min:
            return False
        _tool_rate_limits[key].append(now)
        return True


# --- Initialize Default Tool Specs ---

def init_default_tools():
    """Register security specs for all tools."""

    # Read-only tools
    register_tool(ToolSpec("file_read", Permission.READ, timeout=30, rate_limit=60))
    register_tool(ToolSpec("file_list", Permission.READ, timeout=15, rate_limit=60))
    register_tool(ToolSpec("service_check", Permission.READ, timeout=10, rate_limit=30))
    register_tool(ToolSpec("docker_ps", Permission.READ, timeout=10, rate_limit=30))
    register_tool(ToolSpec("system_info", Permission.READ, timeout=10, rate_limit=30))
    register_tool(ToolSpec("web_search", Permission.READ, timeout=30, rate_limit=20))
    register_tool(ToolSpec("web_fetch", Permission.NETWORK, timeout=30, rate_limit=20))

    # Write tools (user-scoped)
    register_tool(ToolSpec("file_write", Permission.WRITE, timeout=30, rate_limit=30,
                           requires_user_scope=True))
    register_tool(ToolSpec("file_edit", Permission.WRITE, timeout=30, rate_limit=30,
                           requires_user_scope=True))
    register_tool(ToolSpec("file_upload", Permission.WRITE, timeout=60, rate_limit=20,
                           requires_user_scope=True))

    # Execute tools
    register_tool(ToolSpec("bash", Permission.EXECUTE, timeout=120, rate_limit=20))
    register_tool(ToolSpec("python_exec", Permission.EXECUTE, timeout=120, rate_limit=20))

    # Network tools
    register_tool(ToolSpec("smart_api_call", Permission.NETWORK, timeout=60, rate_limit=20))
    register_tool(ToolSpec("http_request", Permission.NETWORK, timeout=60, rate_limit=20))
    register_tool(ToolSpec("api_auto_route", Permission.READ, timeout=15, rate_limit=30))
    register_tool(ToolSpec("call_free_llm", Permission.NETWORK, timeout=60, rate_limit=20))

    # System tools (admin only)
    register_tool(ToolSpec("service_restart", Permission.SYSTEM, timeout=30, rate_limit=5))
    register_tool(ToolSpec("docker_restart", Permission.SYSTEM, timeout=30, rate_limit=5))
    register_tool(ToolSpec("sandbox_exec", Permission.EXECUTE, timeout=120, rate_limit=10))

    # Admin tools
    register_tool(ToolSpec("git", Permission.ADMIN, timeout=30, rate_limit=10,
                           allowed_commands=["status", "log", "add", "commit", "push", "pull",
                                             "diff", "branch", "checkout", "fetch", "show"]))

    # Additional admin/system tools
    register_tool(ToolSpec("pip_install", Permission.ADMIN, timeout=120, rate_limit=5))
    register_tool(ToolSpec("skill_exec", Permission.EXECUTE, timeout=120, rate_limit=20))
    register_tool(ToolSpec("process_startup_check", Permission.READ, timeout=10, rate_limit=30))
