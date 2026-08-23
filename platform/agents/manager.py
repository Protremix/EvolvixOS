"""Agent management — create, invoke, and manage AI agents (Base44-style)."""
import json
import os
import urllib.request
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class AgentManager:
    """Manages AI agents with custom prompts, models, and tools."""

    @staticmethod
    async def create_agent(db: AsyncSession, name: str, system_prompt: str,
                          model: str = "qwen2.5:7b", temperature: float = 0.7,
                          tools: list = None, created_by: str = None):
        if not name or not system_prompt:
            raise ValueError("Name and system_prompt are required")
        result = await db.execute(
            text("SELECT id FROM platform_agents WHERE name = :name"), {"name": name}
        )
        if result.fetchone():
            raise ValueError(f"Agent '{name}' already exists")
        await db.execute(text("""
            INSERT INTO platform_agents (name, system_prompt, model, temperature, tools, created_by)
            VALUES (:name, :prompt, :model, :temp, :tools, :created_by)
        """), {
            "name": name, "prompt": system_prompt, "model": model,
            "temp": temperature, "tools": json.dumps(tools or []),
            "created_by": created_by
        })
        await db.commit()
        return {"name": name, "model": model, "tools": tools or [], "message": f"Agent '{name}' created"}

    @staticmethod
    async def list_agents(db: AsyncSession):
        result = await db.execute(text(
            "SELECT name, model, temperature, tools, status, created_date FROM platform_agents ORDER BY created_date DESC"
        ))
        rows = result.fetchall()
        return [{
            "name": r[0], "model": r[1], "temperature": r[2],
            "tools": r[3] if isinstance(r[3], list) else json.loads(r[3] or "[]"),
            "status": r[4], "created_date": r[5].isoformat() if r[5] else None
        } for r in rows]

    @staticmethod
    async def get_agent(db: AsyncSession, name: str):
        result = await db.execute(text(
            "SELECT name, system_prompt, model, temperature, tools, memory, status FROM platform_agents WHERE name = :name"
        ), {"name": name})
        row = result.fetchone()
        if not row:
            return None
        return {
            "name": row[0], "system_prompt": row[1], "model": row[2],
            "temperature": row[3],
            "tools": row[4] if isinstance(row[4], list) else json.loads(row[4] or "[]"),
            "memory": row[5] if isinstance(row[5], list) else json.loads(row[5] or "[]"),
            "status": row[6]
        }

    @staticmethod
    async def update_agent(db: AsyncSession, name: str, updates: dict):
        set_clauses = []
        params = {"name": name}
        if "system_prompt" in updates:
            set_clauses.append("system_prompt = :prompt")
            params["prompt"] = updates["system_prompt"]
        if "model" in updates:
            set_clauses.append("model = :model")
            params["model"] = updates["model"]
        if "temperature" in updates:
            set_clauses.append("temperature = :temp")
            params["temp"] = updates["temperature"]
        if "tools" in updates:
            set_clauses.append("tools = :tools")
            params["tools"] = json.dumps(updates["tools"])
        if "status" in updates:
            set_clauses.append("status = :status")
            params["status"] = updates["status"]
        if not set_clauses:
            raise ValueError("No fields to update")
        set_clauses.append("updated_date = NOW()")
        await db.execute(text(
            f"UPDATE platform_agents SET {', '.join(set_clauses)} WHERE name = :name"
        ), params)
        await db.commit()
        return {"name": name, "message": "Agent updated"}

    @staticmethod
    async def delete_agent(db: AsyncSession, name: str):
        result = await db.execute(text(
            "DELETE FROM platform_agents WHERE name = :name RETURNING id"
        ), {"name": name})
        if not result.fetchone():
            raise ValueError(f"Agent '{name}' not found")
        await db.commit()
        return {"name": name, "deleted": True}

    @staticmethod
    async def invoke_agent(db: AsyncSession, name: str, message: str, context: dict = None):
        agent = await AgentManager.get_agent(db, name)
        if not agent:
            raise ValueError(f"Agent '{name}' not found")
        if agent["status"] != "active":
            raise ValueError(f"Agent '{name}' is not active")

        messages = [{"role": "system", "content": agent["system_prompt"]}]
        memory = agent.get("memory", [])
        for mem in memory[-10:]:
            if isinstance(mem, dict) and mem.get("role") and mem.get("content"):
                messages.append({"role": mem["role"], "content": mem["content"]})
        if context and context.get("system_context"):
            messages.append({"role": "system", "content": f"Context: {context['system_context']}"})
        messages.append({"role": "user", "content": message})

        ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
        payload = json.dumps({
            "model": agent["model"],
            "messages": messages,
            "stream": False,
            "options": {"temperature": agent["temperature"]}
        }).encode()

        try:
            req = urllib.request.Request(
                f"{ollama_url}/api/chat", data=payload,
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=60)
            data = json.loads(resp.read())
            response_text = data.get("message", {}).get("content", "")
            eval_count = data.get("eval_count", 0)
        except Exception as e:
            raise ValueError(f"LLM error: {str(e)}")

        memory.append({"role": "user", "content": message})
        memory.append({"role": "assistant", "content": response_text})
        memory = memory[-20:]

        await db.execute(text(
            "UPDATE platform_agents SET memory = :memory, updated_date = NOW() WHERE name = :name"
        ), {"memory": json.dumps(memory), "name": name})
        await db.commit()

        return {
            "agent": name, "response": response_text,
            "model": agent["model"], "tokens": eval_count,
            "memory_size": len(memory)
        }

    @staticmethod
    async def clear_memory(db: AsyncSession, name: str):
        await db.execute(text(
            "UPDATE platform_agents SET memory = '[]', updated_date = NOW() WHERE name = :name"
        ), {"name": name})
        await db.commit()
        return {"name": name, "memory": "cleared"}
