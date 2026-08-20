"""EvolvixOS Agent Execution Engine — Autonomous code writing, running, and fixing"""
import json, os, subprocess, tempfile, time, uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="EvolvixOS Agent Engine", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return {"status": "online", "engine": "Agent Engine v2.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/execute")
async def execute_code(request: Request):
    """Execute Python code in a sandboxed environment"""
    body = await request.json()
    code = body.get("code", "")
    language = body.get("language", "python")
    timeout = min(body.get("timeout", 30), 60)
    if not code:
        return JSONResponse({"error": "code required"}, status_code=400)
    if language != "python":
        return JSONResponse({"error": "only python supported"}, status_code=400)
    # Dangerous patterns check
    dangerous = ["import os", "import subprocess", "import pickle", "os.popen", "os.system", "__import__"]
    for pattern in dangerous:
        if pattern in code:
            return JSONResponse({"error": f"Blocked pattern: {pattern}"}, status_code=403)
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir="/tmp") as f:
            f.write(code)
            f.flush()
            result = subprocess.run(
                ["python3", f.name],
                capture_output=True, text=True, timeout=timeout,
                env={"PATH": "/usr/bin:/usr/local/bin", "HOME": "/tmp"}
            )
            os.unlink(f.name)
            return {
                "stdout": result.stdout[:10000],
                "stderr": result.stderr[:5000],
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
    except subprocess.TimeoutExpired:
        return JSONResponse({"error": f"Execution timed out after {timeout}s"}, status_code=408)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/fix")
async def fix_code(request: Request):
    """Attempt to fix code based on error messages"""
    body = await request.json()
    code = body.get("code", "")
    error = body.get("error", "")
    if not code or not error:
        return JSONResponse({"error": "code and error required"}, status_code=400)
    # Simple auto-fix patterns
    fixes = []
    if "ModuleNotFoundError: No module named" in error:
        import re
        missing = re.search(r"No module named '([^']+)'"  , error)
        if missing:
            mod = missing.group(1)
            fixes.append(f"pip install {mod}")
    if "IndentationError" in error or "SyntaxError" in error:
        fixes.append("Check indentation and syntax — Python requires consistent spacing")
    if "KeyError" in error:
        fixes.append("Add .get() method or try/except for dictionary access")
    if "IndexError" in error:
        fixes.append("Add bounds check before list access")
    if not fixes:
        fixes.append("Review the error message and trace back to the source line")
    return {"fixes": fixes, "original_error": error[:500]}

@app.get("/tasks")
async def list_tasks():
    """List active agent tasks"""
    return {"tasks": [], "total": 0, "status": "no active tasks"}
