
"""
CNCF Serverless Workflow v1.0 Engine — Base44-compatible.
Supports: call, switch, wait task types
Activities: invoke_backend_function, invoke_superagent_step, compute_seconds_until
Triggers: scheduled, entity, connector
Uses jq-style expressions: ${ .field.subfield }
"""
import os
import json
import re
import asyncio
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# ─── jq Expression Evaluator ───
class JQExpression:
    """Minimal jq expression evaluator for ${ .field } style expressions."""
    
    @staticmethod
    def evaluate(expr: str, context: dict) -> Any:
        """
        Evaluate a jq-style expression like '${ .trigger.data.status == "active" }'
        against a context dict.
        """
        if not expr.startswith("${") or not expr.endswith("}"):
            return expr  # Return as literal string
        
        # Extract the expression
        jq_expr = expr[2:-1].strip()
        
        try:
            return JQExpression._eval(jq_expr, context)
        except Exception as e:
            return None
    
    @staticmethod
    def evaluate_in_string(s: str, context: dict) -> Any:
        """Evaluate ${ .field } interpolations within a string."""
        if not isinstance(s, str):
            return s
        
        # Full expression: "${ .something }"
        if s.startswith("${") and s.endswith("}") and s.count("${") == 1:
            return JQExpression.evaluate(s, context)
        
        # Interpolated: "Hello ${ .name }"
        def replace(m):
            expr = m.group(0)
            val = JQExpression.evaluate(expr, context)
            return str(val) if val is not None else ""
        
        return re.sub(r"\$\{[^}]+\}", replace, s)
    
    @staticmethod
    def _eval(expr: str, context: dict) -> Any:
        """Evaluate a single jq expression."""
        # Handle comparisons
        if "==" in expr:
            left, right = expr.split("==", 1)
            return JQExpression._eval_value(left.strip(), context) == JQExpression._eval_value(right.strip(), context)
        
        if "!=" in expr:
            left, right = expr.split("!=", 1)
            return JQExpression._eval_value(left.strip(), context) != JQExpression._eval_value(right.strip(), context)
        
        if " and " in expr:
            parts = expr.split(" and ")
            return all(JQExpression._eval(p.strip(), context) for p in parts)
        
        if " or " in expr:
            parts = expr.split(" or ")
            return any(JQExpression._eval(p.strip(), context) for p in parts)
        
        if expr == "true":
            return True
        if expr == "false":
            return False
        
        return JQExpression._eval_value(expr, context)
    
    @staticmethod
    def _eval_value(expr: str, context: dict) -> Any:
        """Evaluate a value expression (field path or literal)."""
        expr = expr.strip()
        
        # String literal
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        
        # Number
        try:
            if "." in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass
        
        # Boolean
        if expr == "true":
            return True
        if expr == "false":
            return False
        if expr == "null":
            return None
        
        # Field path: .trigger.data.status
        if expr.startswith("."):
            parts = expr.lstrip(".").split(".")
            val = context
            for part in parts:
                if val is None:
                    return None
                if isinstance(val, dict):
                    val = val.get(part)
                elif isinstance(val, list):
                    try:
                        val = val[int(part)]
                    except (ValueError, IndexError):
                        return None
                else:
                    return None
            return val
        
        return expr


# ─── CNCF Workflow Engine ───
class CNCFWorkflowEngine:
    """Execute CNCF Serverless Workflow v1.0 definitions."""
    
    @staticmethod
    async def execute(
        db: AsyncSession, 
        workflow_name: str, 
        trigger_data: dict = None,
        user_id: str = None
    ) -> dict:
        """
        Execute a CNCF SWF v1.0 workflow.
        
        Args:
            db: Database session
            workflow_name: Name of the workflow
            trigger_data: Data from the trigger (entity event, schedule, etc.)
            user_id: User ID for agent steps
        """
        result = await db.execute(
            text("SELECT definition, trigger_type, trigger_config FROM platform_workflows WHERE name = :name AND status = 'active'"),
            {"name": workflow_name}
        )
        row = result.fetchone()
        if not row:
            return {"error": f"Workflow '{workflow_name}' not found or inactive"}
        
        raw_def = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        trigger_type = row[1]
        
        # Support both CNCF format (document + do) and legacy format (steps)
        if "document" in raw_def and "do" in raw_def:
            return await CNCFWorkflowEngine._execute_cncf(db, raw_def, trigger_data or {}, user_id)
        elif "steps" in raw_def:
            # Legacy format — delegate to old engine
            from workflows.engine import WorkflowEngine
            return await WorkflowEngine.execute_workflow(db, workflow_name, trigger_data)
        else:
            return {"error": "Invalid workflow definition: missing 'document' or 'steps'"}
    
    @staticmethod
    async def _execute_cncf(
        db: AsyncSession, 
        definition: dict, 
        trigger_data: dict,
        user_id: str = None
    ) -> dict:
        """Execute a CNCF SWF v1.0 definition."""
        do_list = definition.get("do", [])
        
        # Build initial context
        context = {
            "trigger": trigger_data,
            "task": {},  # Will be populated with task results
        }
        
        results = []
        task_index = 0
        
        while task_index < len(do_list):
            task_entry = do_list[task_index]
            
            # Each entry must be a single-key dict
            if not isinstance(task_entry, dict) or len(task_entry) != 1:
                results.append({"step": task_index, "status": "error", "error": "Invalid task entry: must be single-key dict"})
                break
            
            task_name = list(task_entry.keys())[0]
            task_def = task_entry[task_name]
            
            # Determine task type
            if "call" in task_def:
                task_result = await CNCFWorkflowEngine._execute_call(db, task_def, context, user_id)
                context["task"][task_name] = task_result.get("result", task_result)
                results.append({"step": task_name, "status": task_result.get("status", "success"), "result": task_result})
                
                # Transition
                next_task = task_def.get("then", "end")
                if next_task == "end":
                    break
                # Find next task by name
                task_index = CNCFWorkflowEngine._find_task_index(do_list, next_task)
                if task_index == -1:
                    break
                    
            elif "switch" in task_def:
                next_task = await CNCFWorkflowEngine._execute_switch(task_def, context)
                results.append({"step": task_name, "status": "branch", "next": next_task})
                if next_task == "end":
                    break
                task_index = CNCFWorkflowEngine._find_task_index(do_list, next_task)
                if task_index == -1:
                    break
                    
            elif "wait" in task_def:
                duration = task_def["wait"]
                seconds = CNCFWorkflowEngine._parse_iso_duration(duration)
                await asyncio.sleep(seconds)
                results.append({"step": task_name, "status": "waited", "duration": duration})
                next_task = task_def.get("then", "end")
                if next_task == "end":
                    break
                task_index = CNCFWorkflowEngine._find_task_index(do_list, next_task)
                if task_index == -1:
                    break
            else:
                results.append({"step": task_name, "status": "skipped", "reason": "Unknown task type"})
                break
        
        # Log execution
        try:
            await db.execute(text("""
                INSERT INTO platform_workflow_logs (workflow_name, trigger_type, results, executed_at)
                VALUES (:name, :type, :results, NOW())
            """), {"name": definition.get("document", {}).get("name", "unknown"), 
                   "type": "cncf", 
                   "results": json.dumps(results, default=str)})
            await db.commit()
        except:
            pass
        
        return {"workflow": definition.get("document", {}).get("name"), "steps_executed": len(results), "results": results}
    
    @staticmethod
    def _find_task_index(do_list: list, task_name: str) -> int:
        """Find the index of a task by name in the do list."""
        for i, entry in enumerate(do_list):
            if isinstance(entry, dict) and task_name in entry:
                return i
        return -1
    
    @staticmethod
    async def _execute_call(db: AsyncSession, task_def: dict, context: dict, user_id: str = None) -> dict:
        """Execute a 'call' task — invoke an activity."""
        activity = task_def.get("call")
        with_args = task_def.get("with", {})
        
        # Resolve jq expressions in args
        resolved_args = {}
        for key, val in with_args.items():
            if isinstance(val, str) and val.startswith("${"):
                resolved_args[key] = JQExpression.evaluate(val, context)
            elif isinstance(val, dict):
                resolved_args[key] = {
                    k: JQExpression.evaluate_in_string(v, context) if isinstance(v, str) else v
                    for k, v in val.items()
                }
            else:
                resolved_args[key] = val
        
        if activity == "invoke_backend_function":
            fn_name = resolved_args.get("function_name")
            fn_args = resolved_args.get("args", {})
            return await CNCFWorkflowEngine._call_function(db, fn_name, fn_args, user_id)
        
        elif activity == "invoke_superagent_step":
            message = resolved_args.get("message", "")
            return await CNCFWorkflowEngine._call_agent(message, context, user_id)
        
        elif activity == "compute_seconds_until":
            target = resolved_args.get("target_datetime")
            return CNCFWorkflowEngine._compute_seconds_until(target, context)
        
        else:
            return {"error": f"Unknown activity: {activity}", "status": "error"}
    
    @staticmethod
    async def _execute_switch(task_def: dict, context: dict) -> str:
        """Execute a 'switch' task — conditional branching."""
        cases = task_def.get("switch", [])
        
        for case in cases:
            condition = case.get("when", "${ true }")
            if condition == "${ true }":
                return case.get("then", "end")
            
            result = JQExpression.evaluate(condition, context)
            if result:
                return case.get("then", "end")
        
        # Fallback
        return "end"
    
    @staticmethod
    async def _call_function(db: AsyncSession, fn_name: str, fn_args: dict, user_id: str = None) -> dict:
        """Call a backend function using the sandboxed executor."""
        result = await db.execute(
            text("SELECT code, env_vars FROM platform_functions WHERE name = :name"),
            {"name": fn_name}
        )
        row = result.fetchone()
        if not row:
            return {"error": f"Function '{fn_name}' not found", "status": "error"}
        
        code = row[0]
        env_vars = row[1] if isinstance(row[1], dict) else json.loads(row[1] or "{}")
        
        # Use sandboxed executor
        try:
            from sandbox_executor import SandboxedExecutor
            result = await SandboxedExecutor.execute(code, fn_args, user_id, env_vars, timeout=30)
            return {"result": result.get("result", result), "status": result.get("status", "success")}
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    @staticmethod
    async def _call_agent(message: str, context: dict, user_id: str = None) -> dict:
        """Call the AI agent for reasoning/composition."""
        # Interpolate context variables into message
        full_message = JQExpression.evaluate_in_string(message, context)
        
        # Use local Ollama
        ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
        model = os.environ.get("WORKFLOW_AGENT_MODEL", "qwen2.5:7b")
        
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": full_message}],
            "stream": False
        }).encode()
        
        try:
            req = urllib.request.Request(f"{ollama_url}/api/chat", data=payload, headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=60)
            data = json.loads(resp.read())
            response_text = data.get("message", {}).get("content", "")
            return {"agent_response": response_text, "credits_charged": 1, "status": "success"}
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    @staticmethod
    def _compute_seconds_until(target: str, context: dict) -> dict:
        """Compute seconds from now until a target datetime."""
        target_dt = JQExpression.evaluate(target, context) if target.startswith("${") else target
        try:
            if isinstance(target_dt, str):
                target_dt = datetime.fromisoformat(target_dt.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = (target_dt - now).total_seconds()
            return {"seconds": max(0, int(delta)), "status": "success"}
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    @staticmethod
    def _parse_iso_duration(duration: str) -> int:
        """Parse ISO 8601 duration: PT5M=5min, P3D=3days, PT1H=1hour."""
        import re
        match = re.match(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$", duration)
        if not match:
            # Try simple format: "5s", "2m"
            if duration.endswith("s"):
                return int(duration[:-1])
            elif duration.endswith("m"):
                return int(duration[:-1]) * 60
            elif duration.endswith("h"):
                return int(duration[:-1]) * 3600
            return 0
        
        days, hours, minutes, seconds = match.groups()
        total = 0
        if days: total += int(days) * 86400
        if hours: total += int(hours) * 3600
        if minutes: total += int(minutes) * 60
        if seconds: total += int(seconds)
        return total
    
    @staticmethod
    async def trigger_entity_event(db: AsyncSession, entity_name: str, event_type: str, record: dict, old_data: dict = None):
        """Trigger entity-based workflows."""
        # Find workflows with entity triggers for this entity
        result = await db.execute(
            text("SELECT name, trigger_config FROM platform_workflows WHERE trigger_type = 'entity' AND status = 'active'"),
        )
        rows = result.fetchall()
        
        for wf_name, trigger_config in rows:
            config = trigger_config if isinstance(trigger_config, dict) else json.loads(trigger_config or "{}")
            if config.get("entity_name") != entity_name:
                continue
            if config.get("events") and event_type not in config["events"]:
                continue
            
            # Build trigger data
            trigger_data = {
                "entity_name": entity_name,
                "entity_id": record.get("id"),
                "event_type": event_type,
                "data": record,
                "old_data": old_data or {},
                "changed_fields": list(set(record.keys()) - set((old_data or {}).keys())) if old_data else list(record.keys()),
            }
            
            # Check condition if present
            condition = config.get("condition")
            if condition:
                if not JQExpression.evaluate(condition, {"trigger": trigger_data}):
                    continue
            
            # Execute workflow
            await CNCFWorkflowEngine.execute(db, wf_name, trigger_data)
