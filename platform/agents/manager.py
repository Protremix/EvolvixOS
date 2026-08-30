"""Agent management — create, invoke, and manage AI agents (Base44-style)."""
import json
import os
import urllib.request
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from entities.manager import EntityManager
from plugins.registry import PluginRegistry

class AgentManager:
    """Manages AI agents with custom prompts, models, and tools."""

    @staticmethod
    async def create_agent(db: AsyncSession, name: str, system_prompt: str,
                          model: str = "auto", temperature: float = 0.7,
                          tools: list = None, created_by: str = None,
                          max_tokens: int = 4096, top_p: float = 0.9,
                          memory_enabled: bool = True, stream: bool = False,
                          automation_model: str = "auto", cross_app_access: bool = False,
                          avatar: str = None, identity_doc: str = None,
                          allow_update_data: bool = False, allow_delete_data: bool = False,
                          auto_detect_secrets: bool = True):
        if not name or not system_prompt:
            raise ValueError("Name and system_prompt are required")
        result = await db.execute(
            text("SELECT id FROM platform_agents WHERE name = :name"), {"name": name}
        )
        if result.fetchone():
            raise ValueError(f"Agent '{name}' already exists")
        await db.execute(text("""
            INSERT INTO platform_agents (name, system_prompt, model, temperature, tools, created_by, max_tokens, top_p, memory_enabled, stream, automation_model, cross_app_access, avatar, identity_doc, allow_update_data, allow_delete_data, auto_detect_secrets, api_key)
            VALUES (:name, :prompt, :model, :temp, :tools, :created_by, :max_tokens, :top_p, :memory_enabled, :stream, :auto_model, :cross_app, :avatar, :identity, :allow_update, :allow_delete, :auto_secrets, :api_key)
        """), {
            "name": name, "prompt": system_prompt, "model": model,
            "temp": temperature, "tools": json.dumps(tools or []),
            "created_by": created_by, "max_tokens": max_tokens,
            "top_p": top_p, "memory_enabled": memory_enabled, "stream": stream,
            "auto_model": automation_model, "cross_app": cross_app_access,
            "avatar": avatar, "identity": identity_doc,
            "allow_update": allow_update_data, "allow_delete": allow_delete_data,
            "auto_secrets": auto_detect_secrets, "api_key": "evo_" + __import__("secrets").token_hex(16)
        })
        await db.commit()
        return {"name": name, "model": model, "tools": tools or [], "message": f"Agent '{name}' created"}

    @staticmethod
    async def list_agents(db: AsyncSession, user_id: int = None):
        # User isolation: only show agents created by this user, plus shared/system agents
        if user_id:
            result = await db.execute(text(
                "SELECT name, model, temperature, tools, status, created_date, max_tokens, top_p, memory_enabled, stream, avatar, share_enabled FROM platform_agents WHERE created_by = :uid OR share_enabled = true ORDER BY created_date DESC"
            ), {"uid": str(user_id)})
        else:
            result = await db.execute(text(
                "SELECT name, model, temperature, tools, status, created_date, max_tokens, top_p, memory_enabled, stream, avatar, share_enabled FROM platform_agents ORDER BY created_date DESC"
            ))
        rows = result.fetchall()
        return [{
            "name": r[0], "model": r[1], "temperature": r[2],
            "tools": r[3] if isinstance(r[3], list) else json.loads(r[3] or "[]"),
            "status": r[4], "created_date": r[5].isoformat() if r[5] else None,
            "max_tokens": r[6] if r[6] else 4096,
            "top_p": r[7] if r[7] else 0.9,
            "memory_enabled": r[8] if r[8] is not None else True,
            "stream": r[9] if r[9] is not None else False,
            "avatar": r[10] or "",
            "share_enabled": r[11] if r[11] is not None else False
        } for r in rows]

    @staticmethod
    async def get_agent(db: AsyncSession, name: str, user_id: int = None):
        if user_id:
            result = await db.execute(text(
                "SELECT name, system_prompt, model, temperature, tools, memory, status, max_tokens, top_p, memory_enabled, stream, automation_model, cross_app_access, avatar, identity_doc, share_enabled, share_link, collaborators, channel_config, allow_update_data, allow_delete_data, auto_detect_secrets, agent_secrets, api_key, created_date, created_by FROM platform_agents WHERE name = :name AND (created_by = :uid OR share_enabled = true)"
            ), {"name": name, "uid": str(user_id)})
        else:
            result = await db.execute(text(
                "SELECT name, system_prompt, model, temperature, tools, memory, status, max_tokens, top_p, memory_enabled, stream, automation_model, cross_app_access, avatar, identity_doc, share_enabled, share_link, collaborators, channel_config, allow_update_data, allow_delete_data, auto_detect_secrets, agent_secrets, api_key, created_date, created_by FROM platform_agents WHERE name = :name"
            ), {"name": name})
        row = result.fetchone()
        if not row:
            return None
        return {
            "name": row[0], "system_prompt": row[1], "model": row[2],
            "temperature": row[3],
            "tools": row[4] if isinstance(row[4], list) else json.loads(row[4] or "[]"),
            "memory": row[5] if isinstance(row[5], list) else json.loads(row[5] or "[]"),
            "status": row[6],
            "max_tokens": row[7] if row[7] else 4096,
            "top_p": row[8] if row[8] else 0.9,
            "memory_enabled": row[9] if row[9] is not None else True,
            "stream": row[10] if row[10] is not None else False,
            "automation_model": row[11] or "auto",
            "cross_app_access": row[12] if row[12] is not None else False,
            "avatar": row[13] or "",
            "identity_doc": row[14] or "",
            "share_enabled": row[15] if row[15] is not None else False,
            "share_link": row[16] or "",
            "collaborators": row[17] if isinstance(row[17], (list, dict)) else (json.loads(row[17]) if row[17] else []),
            "channel_config": row[18] if isinstance(row[18], (list, dict)) else (json.loads(row[18]) if row[18] else {}),
            "allow_update_data": row[19] if row[19] is not None else False,
            "allow_delete_data": row[20] if row[20] is not None else False,
            "auto_detect_secrets": row[21] if row[21] is not None else True,
            "agent_secrets": row[22] if isinstance(row[22], (list, dict)) else (json.loads(row[22]) if row[22] else {}),
            "api_key": row[23] or "",
            "created_date": row[24].isoformat() if row[24] else None,
            "created_by": str(row[25]) if row[25] else ""
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
        if "max_tokens" in updates:
            set_clauses.append("max_tokens = :max_tokens")
            params["max_tokens"] = updates["max_tokens"]
        if "top_p" in updates:
            set_clauses.append("top_p = :top_p")
            params["top_p"] = updates["top_p"]
        if "memory_enabled" in updates:
            set_clauses.append("memory_enabled = :memory_enabled")
            params["memory_enabled"] = updates["memory_enabled"]
        if "stream" in updates:
            set_clauses.append("stream = :stream")
            params["stream"] = updates["stream"]
        if "automation_model" in updates:
            set_clauses.append("automation_model = :auto_model")
            params["auto_model"] = updates["automation_model"]
        if "cross_app_access" in updates:
            set_clauses.append("cross_app_access = :cross_app")
            params["cross_app"] = updates["cross_app_access"]
        if "avatar" in updates:
            set_clauses.append("avatar = :avatar")
            params["avatar"] = updates["avatar"]
        if "identity_doc" in updates:
            set_clauses.append("identity_doc = :identity")
            params["identity"] = updates["identity_doc"]
        if "share_enabled" in updates:
            set_clauses.append("share_enabled = :share_enabled")
            params["share_enabled"] = updates["share_enabled"]
            if updates["share_enabled"] and not params.get("share_link"):
                import uuid as _uuid
                set_clauses.append("share_link = :share_link")
                params["share_link"] = str(_uuid.uuid4())
        if "collaborators" in updates:
            set_clauses.append("collaborators = :collaborators")
            params["collaborators"] = json.dumps(updates["collaborators"])
        if "channel_config" in updates:
            set_clauses.append("channel_config = :channel_config")
            params["channel_config"] = json.dumps(updates["channel_config"])
        if "allow_update_data" in updates:
            set_clauses.append("allow_update_data = :allow_update")
            params["allow_update"] = updates["allow_update_data"]
        if "allow_delete_data" in updates:
            set_clauses.append("allow_delete_data = :allow_delete")
            params["allow_delete"] = updates["allow_delete_data"]
        if "auto_detect_secrets" in updates:
            set_clauses.append("auto_detect_secrets = :auto_secrets")
            params["auto_secrets"] = updates["auto_detect_secrets"]
        if "agent_secrets" in updates:
            set_clauses.append("agent_secrets = :agent_secrets")
            params["agent_secrets"] = json.dumps(updates["agent_secrets"])
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

        model = agent["model"]
        temperature = agent.get("temperature", 0.7)

        # Build messages with system prompt + real builder tool schema
        existing_entities = await EntityManager.list_entities(db)
        existing_names = [e["name"] for e in existing_entities] if existing_entities else []
        existing_summary = ", ".join(existing_names) if existing_names else "none yet"

        builder_tools = f"""\n\n─── PLATFORM TOOLS ───
You are not just chatting — you can actually DO things on the EvolvixOS platform for the user. Entities that already exist: {existing_summary}.

To take an action, respond with ONLY a JSON object (no other text):
- Create entity: {{"action": "create_entity", "name": "Task", "schema": {{"type": "object", "properties": {{"title": {{"type": "string"}}, "done": {{"type": "boolean"}}}}, "required": ["title"]}}}}
- List entities: {{"action": "list_entities"}}
- Create backend function: {{"action": "create_function", "name": "getJoke", "code": "def handler(input):\n    return {{'joke': 'hello'}}"}}
- Create workflow: {{"action": "create_workflow", "name": "Daily Report", "trigger_type": "scheduled", "definition": {{}}}}
- Run a plugin/tool: {{"action": "plugin", "plugin": "web_search", "params": {{"query": "search term"}}}}
  Available plugins: web_search, web_fetch, email_send, http_request, code_exec, github, crypto, weather, image_gen, translate
- Just reply in chat: {{"action": "chat", "message": "your response"}}

RULES:
1. If the user asks you to build/create something, DO IT immediately with create_entity/create_function/create_workflow — don't just describe it.
2. Check the existing entities list first — never create a duplicate; if one already fits, say so via {{"action": "chat", ...}}.
3. If the user just wants to talk, or asks a question you can answer directly, use {{"action": "chat", "message": "..."}}.
4. Always respond with EXACTLY ONE JSON object, nothing else — no markdown fences, no extra prose outside the JSON."""

        messages = [{"role": "system", "content": agent["system_prompt"] + builder_tools}]

        # Load persistent memory (PlatformMemory) into system context
        try:
            mem_result = await db.execute(text(
                "SELECT content FROM entity_platformmemory ORDER BY created_date DESC LIMIT 20"
            ))
            mem_rows = mem_result.fetchall()
            if mem_rows:
                memory_items = [r[0] for r in mem_rows if r[0]]
                if memory_items:
                    messages[0]["content"] += "\n\nUSER MEMORY — Things to remember:\n" + "\n".join(f"- {m}" for m in memory_items)
        except Exception:
            pass

        # Load conversation memory
        memory = agent.get("memory", [])
        for mem in memory[-10:]:
            if isinstance(mem, dict) and mem.get("role") and mem.get("content"):
                messages.append({"role": mem["role"], "content": mem["content"]})
        if context and context.get("system_context"):
            messages.append({"role": "system", "content": f"Context: {context['system_context']}"})
        messages.append({"role": "user", "content": message})

        # ─── Unified routing via V10 ModelRouter (respects privacy mode) ───
        from routing_bridge import unified_chat
        llm_result = await unified_chat(
            messages, model=model, temperature=temperature,
            max_tokens=agent.get("max_tokens", 4096), prefer_cloud=True
        )
        response_text = llm_result.get("content", "")
        eval_count = 0
        used_model = llm_result.get("model", model)
        used_provider = llm_result.get("provider", "auto")

        # Save conversation memory
        memory.append({"role": "user", "content": message})
        memory.append({"role": "assistant", "content": response_text})
        memory = memory[-20:]

        await db.execute(text(
            "UPDATE platform_agents SET memory = :memory, updated_date = NOW() WHERE name = :name"
        ), {"memory": json.dumps(memory), "name": name})
        await db.commit()

        # Auto-extract preferences from user message
        try:
            user_lower = message.lower()
            triggers = ["prefer", "always", "never", "use ", "don't", "remember", "should", "want", "need", "like"]
            is_question = "?" in message or message.strip().startswith(("what", "how", "why", "where", "when", "who", "can you", "do you"))
            should_save = any(t in user_lower for t in triggers) and len(message) > 10 and not is_question
            if should_save:
                import asyncpg
                conn = await asyncpg.connect(
                    host="127.0.0.1", port=5432,
                    database="evolvixos", user="evolvixos", password="evolvixos"
                )
                await conn.execute(
                    "INSERT INTO entity_platformmemory (content, category, scope, confidence, source, timestamp, created_date, updated_date) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())",
                    message[:200], "preference", name, "inferred", f"agent:{name}", datetime.now().isoformat()
                )
                await conn.close()
        except Exception:
            pass

        # ─── Parse and execute the tool action ───
        tool_action = None
        tool_result = None
        final_message = response_text

        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(response_text[json_start:json_end])
                action_type = parsed.get("action")

                if action_type == "create_entity":
                    entity_name = parsed.get("name", "")
                    existing = await EntityManager.get_entity(db, entity_name)
                    if existing:
                        final_message = f"You already have a '{entity_name}' entity — no need to create it again. Want me to add fields to it, or build something else?"
                        tool_action = "create_entity"
                        tool_result = {"already_existed": True, "name": entity_name}
                    else:
                        result = await EntityManager.create_entity(db, entity_name, parsed.get("schema", {}))
                        fields = ", ".join(parsed.get("schema", {}).get("properties", {}).keys())
                        final_message = f"Created the '{entity_name}' entity with fields: {fields}. You can start adding records to it now."
                        tool_action = "create_entity"
                        tool_result = {"name": entity_name, "fields": fields}

                elif action_type == "list_entities":
                    entities = await EntityManager.list_entities(db)
                    names = ", ".join([e["name"] for e in entities]) if entities else "none yet"
                    final_message = f"Current entities: {names}"
                    tool_action = "list_entities"
                    tool_result = {"entities": entities}

                elif action_type == "create_function":
                    fn_name = parsed.get("name", "")
                    await db.execute(text("""
                        INSERT INTO platform_functions (name, code, env_vars)
                        VALUES (:name, :code, '{}')
                        ON CONFLICT (name) DO UPDATE SET code = EXCLUDED.code
                    """), {"name": fn_name, "code": parsed.get("code", "")})
                    await db.commit()
                    final_message = f"Function '{fn_name}' deployed! Callable at /api/fn/{fn_name}"
                    tool_action = "create_function"
                    tool_result = {"name": fn_name, "url": f"/api/fn/{fn_name}"}

                elif action_type == "create_workflow":
                    wf_name = parsed.get("name", "")
                    await db.execute(text("""
                        INSERT INTO platform_workflows (name, definition, trigger_type, trigger_config)
                        VALUES (:name, :def, :type, '{}')
                        ON CONFLICT (name) DO UPDATE SET definition = EXCLUDED.definition
                    """), {"name": wf_name, "def": json.dumps(parsed.get("definition", {})), "type": parsed.get("trigger_type", "scheduled")})
                    await db.commit()
                    final_message = f"Workflow '{wf_name}' created!"
                    tool_action = "create_workflow"
                    tool_result = {"name": wf_name}

                elif action_type == "plugin":
                    plugin_id = parsed.get("plugin", "")
                    plugin_params = parsed.get("params", {})
                    plugin_res = await PluginRegistry.execute_plugin(plugin_id, plugin_params, db)
                    final_message = f"Ran {plugin_id}. Result: " + json.dumps(plugin_res.get("result", plugin_res), default=str)[:800]
                    tool_action = "plugin"
                    tool_result = {"plugin": plugin_id, "result": plugin_res}

                elif action_type == "chat":
                    final_message = parsed.get("message", response_text)
                    tool_action = "chat"
        except (json.JSONDecodeError, KeyError, TypeError):
            # Not a tool call — just plain chat text
            final_message = response_text
        except Exception as tool_err:
            final_message = f"I tried to do that but hit an error: {str(tool_err)}"
            tool_result = {"error": str(tool_err)}

        # Overwrite the stored memory turn with the clean final message (not raw JSON)
        if memory and memory[-1].get("role") == "assistant":
            memory[-1]["content"] = final_message
            await db.execute(text(
                "UPDATE platform_agents SET memory = :memory WHERE name = :name"
            ), {"memory": json.dumps(memory), "name": name})
            await db.commit()

        return {
            "agent": name, "response": final_message,
            "model": model, "tokens": eval_count,
            "memory_size": len(memory),
            "tool_action": tool_action, "tool_result": tool_result,
            "model": used_model,
            "provider": used_provider
        }

    @staticmethod
    async def clear_memory(db: AsyncSession, name: str):
        await db.execute(text(
            "UPDATE platform_agents SET memory = '[]', updated_date = NOW() WHERE name = :name"
        ), {"name": name})
        await db.commit()
        return {"name": name, "memory": "cleared"}
