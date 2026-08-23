"""Workflow execution engine — scheduled and entity-triggered workflows."""
import os
import json
import asyncio
import subprocess
import urllib.request
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class WorkflowEngine:
    """Executes workflows on schedule or entity events."""

    @staticmethod
    async def execute_workflow(db: AsyncSession, workflow_name: str, trigger_data: dict = None):
        """Execute a workflow by name."""
        result = await db.execute(
            text("SELECT definition, trigger_type, trigger_config FROM platform_workflows WHERE name = :name AND status = 'active'"),
            {"name": workflow_name}
        )
        row = result.fetchone()
        if not row:
            return {"error": f"Workflow '{workflow_name}' not found or inactive"}

        definition = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        trigger_type = row[1]
        trigger_config = row[2] if isinstance(row[2], dict) else json.loads(row[2] or "{}")

        steps = definition.get("steps", [])
        results = []

        for step in steps:
            step_type = step.get("type", "call")
            step_name = step.get("name", "unnamed")
            
            try:
                if step_type == "function":
                    # Execute a backend function
                    fn_name = step.get("function")
                    fn_input = step.get("input", {})
                    fn_result = await WorkflowEngine._call_function(db, fn_name, fn_input)
                    results.append({"step": step_name, "status": "success", "result": fn_result})
                
                elif step_type == "http":
                    # Make HTTP request
                    url = step.get("url")
                    method = step.get("method", "GET")
                    body = step.get("body", {})
                    http_result = await WorkflowEngine._http_call(url, method, body)
                    results.append({"step": step_name, "status": "success", "result": http_result})
                
                elif step_type == "entity_create":
                    # Create entity record
                    entity_name = step.get("entity")
                    data = step.get("data", {})
                    from ..entities.manager import EntityCRUD
                    create_result = await EntityCRUD.create_record(db, entity_name, data)
                    results.append({"step": step_name, "status": "success", "result": create_result})
                
                elif step_type == "entity_update":
                    entity_name = step.get("entity")
                    record_id = step.get("record_id")
                    data = step.get("data", {})
                    from ..entities.manager import EntityCRUD
                    update_result = await EntityCRUD.update_record(db, entity_name, record_id, data)
                    results.append({"step": step_name, "status": "success", "result": update_result})
                
                elif step_type == "ai":
                    # Call AI (Ollama) for processing
                    prompt = step.get("prompt", "")
                    ai_result = await WorkflowEngine._call_ai(prompt)
                    results.append({"step": step_name, "status": "success", "result": ai_result})
                
                elif step_type == "wait":
                    # Wait for specified duration
                    duration = step.get("duration", "0s")
                    seconds = WorkflowEngine._parse_duration(duration)
                    await asyncio.sleep(seconds)
                    results.append({"step": step_name, "status": "success", "message": f"Waited {duration}"})
                
                else:
                    results.append({"step": step_name, "status": "skipped", "message": f"Unknown step type: {step_type}"})
            
            except Exception as e:
                results.append({"step": step_name, "status": "error", "error": str(e)})
                if step.get("stop_on_error", False):
                    break

        # Log execution
        await db.execute(text("""
            INSERT INTO platform_workflow_logs (workflow_name, trigger_type, results, executed_at)
            VALUES (:name, :type, :results, NOW())
        """), {"name": workflow_name, "type": trigger_type, "results": json.dumps(results)})
        await db.commit()

        return {"workflow": workflow_name, "steps_executed": len(results), "results": results}

    @staticmethod
    async def _call_function(db: AsyncSession, fn_name: str, fn_input: dict):
        """Execute a backend function."""
        result = await db.execute(text("SELECT code FROM platform_functions WHERE name = :name"), {"name": fn_name})
        row = result.fetchone()
        if not row:
            return {"error": f"Function '{fn_name}' not found"}
        
        code = row[0]
        local_vars = {"input": fn_input}
        exec_globals = {"__builtins__": __builtins__, "json": json}
        exec(code, exec_globals, local_vars)
        
        if "handler" in local_vars and callable(local_vars["handler"]):
            return local_vars["handler"](fn_input)
        return local_vars.get("result", {"message": "No result"})

    @staticmethod
    async def _http_call(url: str, method: str, body: dict):
        """Make an HTTP request."""
        payload = json.dumps(body).encode()
        req = urllib.request.Request(url, data=payload if method == "POST" else None,
            headers={"Content-Type": "application/json"}, method=method)
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())

    @staticmethod
    async def _call_ai(prompt: str):
        """Call Ollama for AI processing."""
        ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
        payload = json.dumps({
            "model": "qwen2.5:7b",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }).encode()
        req = urllib.request.Request(f"{ollama_url}/api/chat", data=payload, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        return {"response": data.get("message", {}).get("content", "")}

    @staticmethod
    def _parse_duration(duration: str) -> int:
        """Parse ISO-8601 duration or simple format like '5s', '2m', '1h'."""
        if duration.endswith("s"):
            return int(duration[:-1])
        elif duration.endswith("m"):
            return int(duration[:-1]) * 60
        elif duration.endswith("h"):
            return int(duration[:-1]) * 3600
        return int(duration) if duration.isdigit() else 0

    @staticmethod
    async def trigger_entity_event(db: AsyncSession, entity_name: str, event_type: str, record: dict):
        """Trigger workflows on entity events."""
        result = await db.execute(text("""
            SELECT name FROM platform_workflows 
            WHERE status = 'active' AND trigger_type = 'entity'
            AND trigger_config->>'entity' = :entity
            AND trigger_config->>'event' = :event
        """), {"entity": entity_name, "event": event_type})
        
        for row in result.fetchall():
            await WorkflowEngine.execute_workflow(db, row[0], {"entity": entity_name, "event": event_type, "record": record})
