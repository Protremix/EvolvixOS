#!/usr/bin/env python3
"""
Sub-Agent Manager for EvolvixOS.
Spawns background AI workers to execute skills concurrently.
"""

import json
import sys
import os
import time
import uuid
import threading
import importlib.util
from pathlib import Path


class SubAgentManager:
    """Manages background sub-agents running skills concurrently."""

    _agents = {}       # agent_id -> info dict
    _threads = {}      # agent_id -> Thread
    _stop_events = {}  # agent_id -> Event
    _lock = threading.Lock()
    _semaphore = threading.BoundedSemaphore(10)  # Max 10 concurrent active sub-agents

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.skills_dir = self._find_skills_dir()

    def _find_skills_dir(self) -> Path:
        """Locate the EvolvixOS skills directory."""
        if self.config and "skills_dir" in self.config:
            p = Path(self.config["skills_dir"]).resolve()
            if p.exists():
                return p
        # Default relative to this file: skills/sub_agents/skill.py -> skills
        this_file = Path(__file__).resolve()
        skills_dir = this_file.parent.parent
        if skills_dir.exists() and skills_dir.name == "skills":
            return skills_dir
        cwd_skills = Path.cwd() / "skills"
        if cwd_skills.exists():
            return cwd_skills
        return skills_dir

    def _resolve_skill_file(self, skill_name: str) -> Path:
        """Find the skill.py file for a given skill name."""
        if not skill_name:
            raise ValueError("Skill name cannot be empty")

        # 1. Exact match folder
        exact = self.skills_dir / skill_name
        if exact.exists() and (exact / "skill.py").exists():
            return exact / "skill.py"

        # 2. Normalized folder name (lowercased, spaces/dashes to underscores)
        norm_name = skill_name.lower().replace(" ", "_").replace("-", "_")
        norm = self.skills_dir / norm_name
        if norm.exists() and (norm / "skill.py").exists():
            return norm / "skill.py"

        # 3. Search directory for folder name or skill.json name match
        if self.skills_dir.exists():
            for folder in self.skills_dir.iterdir():
                if folder.is_dir():
                    if folder.name.lower() == norm_name:
                        skill_py = folder / "skill.py"
                        if skill_py.exists():
                            return skill_py

                    sjson = folder / "skill.json"
                    if sjson.exists():
                        try:
                            data = json.loads(sjson.read_text(encoding="utf-8"))
                            if data.get("name", "").lower() == skill_name.lower():
                                skill_py = folder / "skill.py"
                                if skill_py.exists():
                                    return skill_py
                        except Exception:
                            pass

        raise FileNotFoundError(f"Skill '{skill_name}' not found in {self.skills_dir}")

    def _execute_skill(self, skill_name: str, args: dict, stop_event: threading.Event) -> dict:
        """Load and execute a skill dynamically."""
        skill_py_path = self._resolve_skill_file(skill_name)

        # Ensure project root is in sys.path for relative imports within skills
        project_root = str(self.skills_dir.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        module_name = f"skills.{skill_py_path.parent.name}.skill"
        spec = importlib.util.spec_from_file_location(module_name, str(skill_py_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for skill at {skill_py_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        skill_class = getattr(module, "Skill", None)
        if skill_class is None:
            raise AttributeError(f"Skill class not found in {skill_py_path}")

        try:
            skill_instance = skill_class(config=self.config)
        except TypeError:
            skill_instance = skill_class()

        if stop_event.is_set():
            return {"status": "stopped", "message": "Execution stopped before skill run"}

        result = skill_instance.run(args or {})
        if result is None:
            result = {}
        elif not isinstance(result, dict):
            result = {"output": result}

        return result

    def spawn(self, task_name: str, skill_name: str, args: dict = None) -> str:
        """Spawn a background sub-agent worker for a task."""
        args = args or {}
        agent_id = f"subagent_{uuid.uuid4().hex[:10]}"
        stop_event = threading.Event()

        with SubAgentManager._lock:
            SubAgentManager._agents[agent_id] = {
                "agent_id": agent_id,
                "task_name": task_name,
                "skill_name": skill_name,
                "args": args,
                "status": "running",
                "result": None,
                "error": None,
                "created_at": time.time(),
                "started_at": time.time(),
                "finished_at": None,
            }
            SubAgentManager._stop_events[agent_id] = stop_event

        def worker():
            # Respect max 10 concurrent active sub-agents
            acquired = SubAgentManager._semaphore.acquire(timeout=60)
            if not acquired:
                with SubAgentManager._lock:
                    SubAgentManager._agents[agent_id]["status"] = "failed"
                    SubAgentManager._agents[agent_id]["error"] = "Max concurrency limit reached (10 concurrent agents)"
                    SubAgentManager._agents[agent_id]["finished_at"] = time.time()
                return

            try:
                if stop_event.is_set():
                    with SubAgentManager._lock:
                        SubAgentManager._agents[agent_id]["status"] = "stopped"
                        SubAgentManager._agents[agent_id]["finished_at"] = time.time()
                    return

                res = self._execute_skill(skill_name, args, stop_event)

                with SubAgentManager._lock:
                    if stop_event.is_set():
                        SubAgentManager._agents[agent_id]["status"] = "stopped"
                    else:
                        SubAgentManager._agents[agent_id]["status"] = "completed"
                        SubAgentManager._agents[agent_id]["result"] = res
                    SubAgentManager._agents[agent_id]["finished_at"] = time.time()

            except Exception as e:
                with SubAgentManager._lock:
                    SubAgentManager._agents[agent_id]["status"] = "failed"
                    SubAgentManager._agents[agent_id]["error"] = str(e)
                    SubAgentManager._agents[agent_id]["finished_at"] = time.time()
            finally:
                SubAgentManager._semaphore.release()

        t = threading.Thread(target=worker, daemon=True)
        with SubAgentManager._lock:
            SubAgentManager._threads[agent_id] = t
        t.start()

        return agent_id

    def run_parallel(self, tasks: list) -> list:
        """Run multiple tasks in parallel and collect all results."""
        if not tasks:
            return []

        agent_ids = []
        for i, task in enumerate(tasks):
            if isinstance(task, dict):
                t_name = task.get("task_name") or task.get("name") or f"task_{i+1}"
                s_name = task.get("skill_name") or task.get("skill") or ""
                t_args = task.get("args") or task.get("parameters") or {}
            elif isinstance(task, (list, tuple)):
                t_name = str(task[0]) if len(task) > 0 else f"task_{i+1}"
                s_name = str(task[1]) if len(task) > 1 else ""
                t_args = task[2] if len(task) > 2 and isinstance(task[2], dict) else {}
            elif isinstance(task, str):
                t_name = f"task_{i+1}"
                s_name = task
                t_args = {}
            else:
                continue

            agent_id = self.spawn(t_name, s_name, t_args)
            agent_ids.append(agent_id)

        # Wait for all spawned threads to complete
        start_wait = time.time()
        max_timeout = 120  # seconds timeout for parallel tasks
        while time.time() - start_wait < max_timeout:
            all_done = True
            with SubAgentManager._lock:
                for aid in agent_ids:
                    st = SubAgentManager._agents.get(aid, {}).get("status")
                    if st in ("running", "queued"):
                        all_done = False
                        break
            if all_done:
                break
            time.sleep(0.05)

        # Collect results in order
        results = []
        for aid in agent_ids:
            results.append(self.get_result(aid))

        return results

    def get_status(self, agent_id: str) -> str:
        """Get the status of a specific agent."""
        with SubAgentManager._lock:
            info = SubAgentManager._agents.get(agent_id)
            if not info:
                return "not_found"
            return info["status"]

    def get_result(self, agent_id: str) -> dict:
        """Get the result dict of a completed or failed agent."""
        with SubAgentManager._lock:
            info = SubAgentManager._agents.get(agent_id)
            if not info:
                return {"agent_id": agent_id, "status": "not_found", "error": "Agent not found", "result": None}

            status = info["status"]
            ret = {
                "agent_id": agent_id,
                "task_name": info["task_name"],
                "skill_name": info["skill_name"],
                "status": status,
                "result": info["result"],
                "error": info["error"],
            }
            # Merge skill output into return dict if result is a dict
            if isinstance(info["result"], dict):
                for k, v in info["result"].items():
                    if k not in ret:
                        ret[k] = v
            return ret

    def list_active(self) -> list:
        """List all currently active (running) agents."""
        with SubAgentManager._lock:
            active = []
            for aid, info in SubAgentManager._agents.items():
                if info["status"] in ("running", "queued"):
                    active.append({
                        "agent_id": aid,
                        "task_name": info["task_name"],
                        "skill_name": info["skill_name"],
                        "status": info["status"],
                        "started_at": info["started_at"],
                    })
            return active

    def stop(self, agent_id: str) -> bool:
        """Stop a running agent."""
        with SubAgentManager._lock:
            if agent_id not in SubAgentManager._agents:
                return False

            stop_evt = SubAgentManager._stop_events.get(agent_id)
            if stop_evt:
                stop_evt.set()

            info = SubAgentManager._agents[agent_id]
            if info["status"] in ("running", "queued"):
                info["status"] = "stopped"
                info["finished_at"] = time.time()
                return True
            return False


class Skill:
    """Sub-Agent Manager Skill wrapper for EvolvixOS."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.manager = SubAgentManager(config=self.config)

    def run(self, args: dict) -> dict:
        """Execute sub-agent manager actions."""
        action = args.get("action", "")

        if action == "spawn" or ("skill_name" in args and "tasks" not in args and not action):
            task_name = args.get("task_name") or args.get("name", "task")
            skill_name = args.get("skill_name") or args.get("skill", "")
            sub_args = args.get("args") or args.get("parameters", {})
            agent_id = self.manager.spawn(task_name, skill_name, sub_args)
            return {"agent_id": agent_id, "status": "running"}

        elif action == "run_parallel" or "tasks" in args:
            tasks = args.get("tasks", [])
            results = self.manager.run_parallel(tasks)
            return {"results": results, "count": len(results)}

        elif action == "get_status":
            agent_id = args.get("agent_id", "")
            return {"agent_id": agent_id, "status": self.manager.get_status(agent_id)}

        elif action == "get_result" or ("agent_id" in args and not action):
            agent_id = args.get("agent_id", "")
            return self.manager.get_result(agent_id)

        elif action == "list_active":
            active = self.manager.list_active()
            return {"agents": active, "count": len(active)}

        elif action == "stop":
            agent_id = args.get("agent_id", "")
            stopped = self.manager.stop(agent_id)
            return {"stopped": stopped, "agent_id": agent_id}

        else:
            active = self.manager.list_active()
            return {
                "status": "active",
                "active_agents": len(active),
                "message": "SubAgentManager ready. Supported actions: spawn, run_parallel, get_status, get_result, list_active, stop."
            }


if __name__ == "__main__":
    cli_args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(cli_args)))
