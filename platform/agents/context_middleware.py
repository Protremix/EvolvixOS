"""
Agent Context Middleware — Bridges OpenViking context DB into the agent execution loop.

This module provides:
  1. Pre-task context recall: fetch relevant memories + code context before agent runs
  2. Post-task session commit: store conversation for automatic memory extraction
  3. Knowledge injection: relevant knowledge is injected into the system prompt

This closes the self-improvement loop: every agent interaction learns and recalls.
"""

import json
import logging
from typing import Optional, Dict, List

logger = logging.getLogger("agent_context")

# Import the bridge
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openviking_bridge import (
    recall_for_agent as ov_recall,
    create_session as ov_create_session,
    add_messages_batch as ov_add_messages,
    commit_session as ov_commit_session,
    get_session_context as ov_get_session_context,
    store_knowledge as ov_store_knowledge,
    get_memory_stats as ov_get_memory_stats,
)

# Track active sessions per agent
_active_sessions: Dict[str, str] = {}


async def pre_task_recall(agent_name: str, user_message: str, max_context_items: int = 5) -> str:
    """Recall relevant context from OpenViking before the agent processes a task.
    
    Returns a formatted context string to inject into the system prompt.
    """
    try:
        # Create a session for this interaction
        session = ov_create_session(title=f"{agent_name}: {user_message[:80]}")
        if session.get("status") == "ok" and session.get("result", {}).get("session_id"):
            session_id = session["result"]["session_id"]
            _active_sessions[agent_name] = session_id

        # Recall relevant context
        results = ov_recall(query=user_message, limit=max_context_items)
        
        context_parts = []
        
        if results.get("status") == "ok" and results.get("result"):
            result = results["result"]
            
            # Add memories
            for mem in result.get("memories", []):
                abstract = mem.get("abstract", "")
                if abstract and "not ready" not in abstract.lower():
                    context_parts.append(f"[Memory] {abstract}")
            
            # Add resources (code context)
            for res in result.get("resources", []):
                abstract = res.get("abstract", "")
                uri = res.get("uri", "")
                if abstract and "not ready" not in abstract.lower():
                    context_parts.append(f"[Context: {uri}] {abstract}")
            
            # Add skills
            for skill in result.get("skills", []):
                context_parts.append(f"[Skill: {skill.get('name', '')}] {skill.get('description', '')}")
        
        if context_parts:
            return "\n\n─── RELEVANT CONTEXT (from project memory) ───\n" + "\n".join(context_parts)
        return ""
        
    except Exception as e:
        logger.warning(f"Pre-task recall failed: {e}")
        return ""


async def post_task_commit(agent_name: str, user_message: str, assistant_response: str):
    """Commit the conversation to OpenViking for automatic memory extraction.
    
    Called after the agent has processed the task. This triggers:
    - Session archiving
    - Memory extraction (preferences, entities, events)
    - Semantic indexing for future recall
    """
    try:
        session_id = _active_sessions.get(agent_name)
        if not session_id:
            # Create a session if one wasn't created in pre_task
            session = ov_create_session(title=f"{agent_name}")
            if session.get("status") == "ok" and session.get("result", {}).get("session_id"):
                session_id = session["result"]["session_id"]
            else:
                return
        
        # Add the messages to the session
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_response},
        ]
        ov_add_messages(session_id, messages)
        
        # Commit — triggers async memory extraction
        result = ov_commit_session(session_id)
        
        # Clean up the active session
        if agent_name in _active_sessions:
            del _active_sessions[agent_name]
        
        logger.info(f"Session {session_id} committed for agent {agent_name}")
        return result
        
    except Exception as e:
        logger.warning(f"Post-task commit failed: {e}")
        return None


async def inject_context(system_prompt: str, agent_name: str, user_message: str) -> str:
    """High-level: recall context and inject it into the system prompt."""
    context = await pre_task_recall(agent_name, user_message)
    if context:
        return system_prompt + context
    return system_prompt


async def learn_preference(agent_name: str, content: str, category: str = "preference"):
    """Explicitly store a learned preference/knowledge in OpenViking."""
    try:
        key = f"{agent_name}-{category}-{hash(content) % 100000}"
        return ov_store_knowledge(key=key, content=content, category=category)
    except Exception as e:
        logger.warning(f"Learn preference failed: {e}")
        return None


async def get_agent_evolution(agent_name: str) -> dict:
    """Get agent evolution data — outcomes and trajectories for self-improvement."""
    try:
        from openviking_bridge import get_evolution_outcomes, get_evolution_trajectories
        outcomes = get_evolution_outcomes()
        trajectories = get_evolution_trajectories()
        return {
            "outcomes": outcomes.get("result", []),
            "trajectories": trajectories.get("result", []),
        }
    except Exception as e:
        return {"error": str(e)}
