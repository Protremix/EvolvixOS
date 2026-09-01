"""
import re
import re
Agent Orchestrator — Multi-step task planning, execution, and self-correction.

Inspired by:
  - CrewAI: task delegation with role-based agents
  - LangGraph: graph-based execution with conditional branching
  - AutoGen: multi-agent conversation for complex tasks
  - SWE-agent: iterative code execution with error recovery

Architecture:
  1. PLAN: Break down user goal into ordered steps
  2. EXECUTE: Run each step using available tools/plugins
  3. VERIFY: Check if the step achieved its objective
  4. CORRECT: If failed, analyze error and retry with adjusted approach
  5. SYNTHESIZE: Combine results into final output

The orchestrator uses the existing V10 ModelRouter for LLM calls
and the OpenViking context DB for recall/commit.
"""
import re

import json
import logging
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger("orchestrator")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routing_bridge import unified_chat
from agents.context_middleware import pre_task_recall, post_task_commit


MAX_RETRIES = 3
MAX_STEPS = 10

ORCHESTRATOR_PROMPT = """You are an AI task orchestrator. Break down the user's goal into a sequence of actionable steps.

For each step, specify:
- step_id: unique identifier
- description: what to do
- tool: which tool to use (one of: {available_tools})
- params: parameters for the tool
- success_criteria: how to know it worked
- depends_on: list of step_ids this depends on (empty if first)

Respond with ONLY a JSON array of step objects:
[
  {{
    step_id: 1,
    description: Search for the relevant code,
    tool: semantic_search,
    params: {{query: authentication logic}},
    success_criteria: Returns at least one relevant result,
    depends_on: []
  }}
]

Rules:
- Maximum {max_steps} steps
- Each step must be concrete and verifiable
- Prefer fewer, high-impact steps
- Include a verification step at the end
- Be specific about tool parameters
"""
import re


VERIFICATION_PROMPT = """You are a task verification engine. Given a step's objective and its result, determine if it succeeded.

Step: {step_description}
Success criteria: {success_criteria}
Result: {result}

Respond with JSON:
{{success: true/false, reason: why, next_action: proceed or retry or skip}}
"""
import re


CORRECTION_PROMPT = """You are an error correction engine. A step failed. Analyze the error and suggest a corrected approach.

Step: {step_description}
Attempt: {attempt_number}
Error: {error}
Previous params: {params}

Respond with JSON:
{{corrected_params: {{...}}, strategy: what changed and why}}
"""
import re


class AgentOrchestrator:
    """Orchestrates multi-step agent tasks with planning, execution, and self-correction."""

    def __init__(self, available_tools: List[str] = None):
        self.tools = available_tools or [
            "semantic_search", "code_exec", "web_search", "web_fetch",
            "github", "create_entity", "create_function", "create_workflow",
            "http_request", "email_send", "image_gen", "translate",
        ]
        self.execution_log: List[dict] = []
        self.step_results: Dict[int, dict] = {}

    async def plan(self, goal: str, context: str = "") -> List[dict]:
        """Break down a goal into executable steps."""
        prompt = ORCHESTRATOR_PROMPT.format(
            available_tools=", ".join(self.tools),
            max_steps=MAX_STEPS,
        )
        
        # Recall relevant context for planning
        recalled = await pre_task_recall("orchestrator", goal, max_context_items=3)
        
        messages = [
            {"role": "system", "content": prompt + recalled},
            {"role": "user", "content": f"Goal: {goal}\n\nContext: {context}"},
        ]
        
        result = await unified_chat(messages, model="auto", temperature=0.3, prefer_cloud=True)
        content = result.get("content", "")
        
        try:
            # Extract JSON array
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                steps = json.loads(content[start:end])
                logger.info(f"Planned {len(steps)} steps for: {goal[:80]}")
                return steps
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Plan parsing failed: {e}")
        
        # Fallback: single-step plan
        return [{
            "step_id": 1,
            "description": goal,
            "tool": "chat",
            "params": {},
            "success_criteria": "Task is complete",
            "depends_on": [],
        }]

    async def execute_step(self, step: dict, tool_executor) -> dict:
        """Execute a single step using the provided tool executor."""
        step_id = step.get("step_id", 0)
        description = step.get("description", "")
        tool = step.get("tool", "chat")
        params = step.get("params", {})
        
        logger.info(f"Executing step {step_id}: {description[:80]}")
        
        result = {
            "step_id": step_id,
            "description": description,
            "tool": tool,
            "started_at": datetime.now().isoformat(),
            "status": "pending",
        }
        
        try:
            tool_result = await tool_executor(tool, params)
            result["result"] = tool_result
            result["status"] = "executed"
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "failed"
        
        result["completed_at"] = datetime.now().isoformat()
        self.step_results[step_id] = result
        self.execution_log.append(result)
        return result

    async def verify_step(self, step: dict, result: dict) -> dict:
        """Verify if a step achieved its objective."""
        # Try LLM verification, but default to success if parsing fails
        try:
            prompt = VERIFICATION_PROMPT.format(
                step_description=step.get("description", ""),
                success_criteria=step.get("success_criteria", ""),
                result=json.dumps(result.get("result", result.get("error", "")), default=str)[:1000],
            )
            messages = [
                {"role": "system", "content": "Respond ONLY with a JSON object like {success: true, reason: text, next_action: proceed}. No preamble."},
                {"role": "user", "content": prompt},
            ]
            llm_result = await unified_chat(messages, model="auto", temperature=0.2, prefer_cloud=True)
            content_str = llm_result.get("content", "")
            # Find valid JSON with success key
            for match in re.finditer(r"\{[^{}]*\}", content_str, re.DOTALL):
                try:
                    obj = json.loads(match.group())
                    if "success" in obj:
                        return obj
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.warning(f"Verification LLM call failed: {e}")

        # Default: assume success if no error
        return {
            "success": result.get("status") == "executed",
            "reason": "No error detected",
            "next_action": "proceed",
        }

    async def correct_step(self, step: dict, error: str, attempt: int) -> dict:
        """Analyze error and suggest corrected parameters."""
        try:
            prompt = CORRECTION_PROMPT.format(
                step_description=step.get("description", ""),
                attempt_number=attempt,
                error=error,
                params=json.dumps(step.get("params", {})),
            )
            messages = [
                {"role": "system", "content": "Respond ONLY with a JSON object. No preamble."},
                {"role": "user", "content": prompt},
            ]
            llm_result = await unified_chat(messages, model="auto", temperature=0.3, prefer_cloud=True)
            content_str = llm_result.get("content", "")
            for match in re.finditer(r"\{[^{}]*\}", content_str, re.DOTALL):
                try:
                    correction = json.loads(match.group())
                    if "corrected_params" in correction:
                        step["params"] = correction["corrected_params"]
                    return correction
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.warning(f"Correction LLM call failed: {e}")

        return {"corrected_params": step.get("params", {}), "strategy": "retry as-is"}

    async def run(self, goal: str, tool_executor, context: str = "") -> dict:
        """Execute a full orchestration cycle: plan → execute → verify → correct → synthesize."""
        
        # 1. PLAN
        steps = await self.plan(goal, context)
        
        results = []
        completed_steps = set()
        
        for step in steps:
            step_id = step.get("step_id", 0)
            
            # Check dependencies
            deps = step.get("depends_on", [])
            if deps and not all(d in completed_steps for d in deps):
                logger.warning(f"Step {step_id} skipped — dependencies not met: {deps}")
                results.append({"step_id": step_id, "status": "skipped", "reason": "dependencies not met"})
                continue
            
            # 2. EXECUTE with retry loop
            attempt = 0
            step_success = False
            
            while attempt < MAX_RETRIES and not step_success:
                attempt += 1
                result = await self.execute_step(step, tool_executor)
                
                if result.get("status") == "executed":
                    # 3. VERIFY
                    verification = await self.verify_step(step, result)
                    
                    if verification.get("success"):
                        step_success = True
                        result["verification"] = verification
                        completed_steps.add(step_id)
                        logger.info(f"Step {step_id} verified successfully")
                    else:
                        # 4. CORRECT
                        logger.warning(f"Step {step_id} failed verification (attempt {attempt})")
                        if attempt < MAX_RETRIES:
                            correction = await self.correct_step(step, verification.get("reason", "unknown"), attempt)
                            logger.info(f"Step {step_id} correction: {correction.get('strategy', '')}")
                        else:
                            result["verification"] = verification
                            result["status"] = "failed_final"
                else:
                    # Execution error — try correction
                    if attempt < MAX_RETRIES:
                        correction = await self.correct_step(step, result.get("error", "unknown"), attempt)
                        logger.info(f"Step {step_id} error correction: {correction.get('strategy', '')}")
                    else:
                        result["status"] = "failed_final"
                
                results.append(result)
            
            if not step_success:
                logger.error(f"Step {step_id} failed after {MAX_RETRIES} attempts")
        
        # 5. SYNTHESIZE — commit to OpenViking for learning
        await post_task_commit("orchestrator", goal, json.dumps(results, default=str)[:2000])
        
        return {
            "goal": goal,
            "steps_planned": len(steps),
            "steps_completed": len(completed_steps),
            "steps_failed": len(steps) - len(completed_steps),
            "results": results,
            "execution_log": self.execution_log,
        }


# Convenience function for the platform API
async def orchestrate(goal: str, tool_executor=None, context: str = "") -> dict:
    """Run a full orchestration cycle."""
    orchestrator = AgentOrchestrator()
    
    if tool_executor is None:
        # Default tool executor — uses platform plugins
        from plugins.registry import PluginRegistry
        from database import async_session
        
        async def default_executor(tool: str, params: dict) -> dict:
            # Map orchestration tools to platform plugins
            plugin_map = {
                "semantic_search": None,  # handled specially
                "code_exec": "code_exec",
                "web_search": "web_search",
                "web_fetch": "web_fetch",
                "github": "github",
                "http_request": "http_request",
                "email_send": "email_send",
                "image_gen": "image_gen",
                "translate": "translate",
            }
            
            if tool == "semantic_search":
                from openviking_bridge import search
                return search(params.get("query", ""), limit=params.get("limit", 5), mode="list")
            
            if tool == "chat":
                messages = [{"role": "user", "content": params.get("message", "")}]
                return await unified_chat(messages, prefer_cloud=True)
            
            plugin_id = plugin_map.get(tool)
            if plugin_id:
                async with async_session() as db:
                    return await PluginRegistry.execute_plugin(plugin_id, params, db)
            
            return {"error": f"Unknown tool: {tool}"}
        
        tool_executor = default_executor
    
    return await orchestrator.run(goal, tool_executor, context)
