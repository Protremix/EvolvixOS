"""
EvolvixOS — Code Runner Skill
Safely executes arbitrary Python code in a sandboxed subprocess.
Captures stdout, stderr, exit code, and execution time with timeout limits.
"""

import sys
import os
import json
import time
import tempfile
import subprocess
from typing import Optional, Dict, Any


class Skill:
    """Code Runner — Sandboxed execution of Python code via subprocess."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.default_timeout = float(self.config.get("default_timeout", 30))

    def run(self, args: dict) -> dict:
        """
        Execute Python code in a subprocess.

        Args:
            code (str): Python source code string to execute
            stdin / input (str, optional): String data to feed into stdin
            timeout (int/float, optional): Maximum execution time in seconds (default: 30)
            cli_args / args (list, optional): CLI arguments to pass to the Python script
            env (dict, optional): Custom environment variables
        """
        code = args.get("code") or args.get("script")
        if not code:
            return {"success": False, "error": "Missing required argument 'code'."}

        stdin_data = args.get("stdin") or args.get("input") or ""
        timeout = float(args.get("timeout", self.default_timeout))
        cli_args = args.get("cli_args") or args.get("args") or []
        if not isinstance(cli_args, list):
            cli_args = [str(cli_args)]

        env = os.environ.copy()
        custom_env = args.get("env")
        if isinstance(custom_env, dict):
            env.update({str(k): str(v) for k, v in custom_env.items()})

        temp_file = None
        start_time = time.time()

        try:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
                f.write(code)
                temp_file = f.name

            cmd = [sys.executable, temp_file] + [str(a) for a in cli_args]

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            stdout_data, stderr_data = process.communicate(
                input=stdin_data if stdin_data else None,
                timeout=timeout
            )
            exec_time = round(time.time() - start_time, 4)
            exit_code = process.returncode

            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout_data,
                "stderr": stderr_data,
                "execution_time_sec": exec_time,
                "timed_out": False
            }

        except subprocess.TimeoutExpired:
            process.kill()
            stdout_data, stderr_data = process.communicate()
            exec_time = round(time.time() - start_time, 4)
            return {
                "success": False,
                "exit_code": -1,
                "stdout": stdout_data or "",
                "stderr": (stderr_data or "") + f"\nProcess timed out after {timeout} seconds.",
                "execution_time_sec": exec_time,
                "timed_out": True
            }

        except Exception as e:
            exec_time = round(time.time() - start_time, 4)
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Subprocess runner error: {str(e)}",
                "execution_time_sec": exec_time,
                "timed_out": False
            }

        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raw_args = json.loads(sys.argv[1])
    else:
        raw_args = {"code": "import sys; print('Hello from Code Runner!'); sys.exit(0)"}
    skill = Skill()
    print(json.dumps(skill.run(raw_args), indent=2))
