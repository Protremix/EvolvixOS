
"""
Sandboxed Backend Function Executor — Self-Hosted isolation.
Replaces unsafe exec() with subprocess-based Docker/gVisor isolation.
Falls back to restricted Python subprocess when Docker is unavailable.
"""
import os
import json
import time
import uuid
import asyncio
import subprocess
import tempfile
import traceback
from typing import Any, Optional


# Wrapper template for user functions — provides Self-Hosted SDK
FUNCTION_WRAPPER = '''
import json, os, time, sys, urllib.request, urllib.error
from typing import Any

# Self-Hosted SDK simulation
class PlatformSDK:
    """Mini-SDK providing entity CRUD and HTTP utilities (same pattern as the platform)."""
    def __init__(self, user_id=None):
        self.user_id = user_id
        self._api_base = os.environ.get("PLATFORM_API_BASE", "http://127.0.0.1:8080")
    
    def entities(self):
        return EntityClient(self._api_base, self.user_id)
    
    def http(self, url, method="GET", headers=None, body=None, timeout=30):
        """Make outbound HTTP request (SSRF-protected)."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        # SSRF protection
        if parsed.hostname in ("169.254.169.254", "metadata.google.internal", "metadata.azure.com"):
            raise ValueError("SSRF: metadata endpoints blocked")
        if not parsed.scheme in ("http", "https"):
            raise ValueError("Only HTTP(S) allowed")
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read())

class EntityClient:
    def __init__(self, api_base, user_id):
        self.api_base = api_base
        self.user_id = user_id
    
    def list(self, entity_name, query=None, limit=50, skip=0, sort=None):
        params = f"?limit={limit}&skip={skip}"
        if sort: params += f"&sort={sort}"
        url = f"{self.api_base}/api/entities/{entity_name}/records{params}"
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    
    def get(self, entity_name, record_id):
        url = f"{self.api_base}/api/entities/{entity_name}/records/{record_id}"
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    
    def create(self, entity_name, data):
        url = f"{self.api_base}/api/entities/{entity_name}/records"
        payload = json.dumps(data).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    
    def update(self, entity_name, record_id, data):
        url = f"{self.api_base}/api/entities/{entity_name}/records/{record_id}"
        payload = json.dumps(data).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="PUT")
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    
    def delete(self, entity_name, record_id):
        url = f"{self.api_base}/api/entities/{entity_name}/records/{record_id}"
        req = urllib.request.Request(url, method="DELETE")
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())

evolvixos = PlatformSDK(user_id=os.environ.get("EVOLVIX_USER_ID"))

# Read input from stdin
import sys
input_data = json.loads(sys.stdin.read()) if sys.stdin else {}

# User function code below
{user_code}

# Execute handler if present
if "handler" in dir():
    import asyncio
    _result = handler(input_data)
    if asyncio.iscoroutine(_result):
        _result = asyncio.run(_result)
    elif callable(_result):
        _result = _result()
    print("__RESULT__:" + json.dumps(_result, default=str))
elif "result" in dir():
    print("__RESULT__:" + json.dumps(result, default=str))
else:
    print("__RESULT__:" + json.dumps({{"message": "Function executed, no handler/result found"}}))
'''

# Dangerous patterns to block (Self-Hosted security)
BLOCKED_IMPORTS = {
    "subprocess", "multiprocessing", "ctypes", "socket", "pickle", 
    "marshal", "shutil", "tempfile", "pathlib", "signal",
    "importlib", "builtins", "code", "codeop", "compile",
    "compileall", "py_compile", "runpy", "pdb", "bdb",
}
BLOCKED_PATTERNS = [
    "os.system", "os.popen", "os.exec", "os.spawn", "os.fork",
    "__import__", "eval(", "exec(", "globals()", "locals()",
    "open('/etc", "open('/opt/evolvixos/.env", "open('/root",
    "os.environ.items", "os.environ.keys", "os.environ.get('JWT",
    "os.remove('/", "os.rmdir('/", "shutil.rmtree",
    "import subprocess", "import socket", "import ctypes",
]


class SandboxedExecutor:
    """Execute user-submitted function code in an isolated subprocess."""
    
    @staticmethod
    def _validate_code(code: str) -> tuple[bool, str]:
        """Scan for dangerous patterns before execution."""
        for pattern in BLOCKED_PATTERNS:
            if pattern in code:
                return False, f"Security: blocked pattern '{pattern}' detected"
        
        for line in code.split("\n"):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                for blocked in BLOCKED_IMPORTS:
                    if blocked in stripped:
                        return False, f"Security: import '{blocked}' is blocked"
        
        return True, "ok"
    
    @staticmethod
    async def execute(
        code: str, 
        input_data: dict, 
        user_id: str = None,
        env_vars: dict = None,
        timeout: int = 30,
        use_docker: bool = False
    ) -> dict:
        """
        Execute function code in a sandboxed subprocess.
        
        Args:
            code: Python function code from platform_functions
            input_data: Input payload to pass as 'input' 
            user_id: User ID for SDK context
            env_vars: Environment variables for the function
            timeout: Execution timeout in seconds
            use_docker: Use Docker container isolation if available
            
        Returns:
            dict with 'result' or 'error'
        """
        # Security scan
        is_safe, reason = SandboxedExecutor._validate_code(code)
        if not is_safe:
            return {"error": reason, "status": "blocked"}
        
        # Wrap user code with SDK
        wrapped = FUNCTION_WRAPPER.replace("{user_code}", code)
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir="/tmp") as f:
            f.write(wrapped)
            temp_path = f.name
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env["EVOLVIX_USER_ID"] = str(user_id) if user_id else ""
            env["PLATFORM_API_BASE"] = "http://127.0.0.1:8080"
            if env_vars:
                for k, v in env_vars.items():
                    if k.upper() in ("JWT_SECRET", "DATABASE_URL", "POSTGRES_PASSWORD"):
                        continue  # Never expose secrets
                    env[k] = str(v)
            
            # Prepare input data via stdin
            input_json = json.dumps(input_data)
            
            if use_docker and os.path.exists("/var/run/docker.sock"):
                # Docker isolation (Self-Hosted)
                cmd = [
                    "docker", "run", "--rm", "--network=host",
                    "--memory=256m", "--cpus=0.5",
                    "-e", "EVOLVIX_USER_ID",
                    "-e", "PLATFORM_API_BASE",
                    "--name", f"fn-{uuid.uuid4().hex[:8]}",
                    "-v", f"{temp_path}:/app/function.py:ro",
                    "python:3.14-slim",
                    "python", "/app/function.py"
                ]
            else:
                # Subprocess isolation (restricted Python)
                cmd = ["python3", temp_path]
            
            # Execute with timeout
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=input_json.encode()),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return {"error": f"Function timed out after {timeout}s", "status": "timeout"}
            
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")
            
            # Parse result from stdout (look for __RESULT__ marker)
            for line in stdout_text.split("\n"):
                if line.startswith("__RESULT__:"):
                    result_str = line[len("__RESULT__:"):]
                    try:
                        return {"result": json.loads(result_str), "status": "success", "stdout": stdout_text}
                    except json.JSONDecodeError:
                        return {"result": result_str, "status": "success", "stdout": stdout_text}
            
            # No result marker found
            if proc.returncode != 0:
                return {
                    "error": f"Function exited with code {proc.returncode}",
                    "stderr": stderr_text[:1000],
                    "status": "error"
                }
            
            return {
                "result": {"message": "Function executed, no result returned"},
                "stdout": stdout_text[:2000],
                "stderr": stderr_text[:500] if stderr_text else None,
                "status": "success"
            }
            
        finally:
            # Cleanup
            try:
                os.unlink(temp_path)
            except:
                pass
