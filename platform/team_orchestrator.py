"""
EvolvixOS Multi-Agent Team Orchestrator
Inspired by awesome-llm-apps agent_teams pattern.

Supports:
- Team creation with multiple specialized agents
- Task delegation and routing with real LLM execution
- Live status tracking per agent
- Result aggregation
- Works with local Ollama models
"""
import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TeamAgent:
    name: str
    role: str
    system_prompt: str = ""
    model: str = "auto"
    tools: List[str] = field(default_factory=list)
    memory: bool = True


@dataclass
class AgentTeam:
    name: str
    description: str = ""
    members: List[TeamAgent] = field(default_factory=list)
    orchestrator_model: str = "auto"
    created_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class TeamOrchestrator:
    def __init__(self):
        self.teams: Dict[str, AgentTeam] = {}
        self.executions: Dict[str, dict] = {}  # Live execution tracking

    def create_team(self, name: str, description: str = "", members: List[dict] = None) -> AgentTeam:
        team = AgentTeam(
            name=name,
            description=description,
            members=[TeamAgent(**m) for m in (members or [])]
        )
        self.teams[name] = team
        return team

    def add_member(self, team_name: str, agent: dict) -> bool:
        if team_name not in self.teams:
            return False
        self.teams[team_name].members.append(TeamAgent(**agent))
        return True

    def _ollama_generate(self, system: str, prompt: str, max_tokens: int = 1000) -> str:
        """Synchronous Ollama call."""
        import urllib.request
        data = json.dumps({
            "model": "qwen2.5:7b",
            "system": system,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.5}
        }).encode()
        req = urllib.request.Request("http://localhost:11434/api/generate", data=data)
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("response", "").strip()

    async def execute(self, team_name: str, task: str, context: str = "") -> dict:
        """Execute a task with the team — each agent processes with their specialization."""
        team = self.teams.get(team_name)
        if not team:
            return {"error": f"Team '{team_name}' not found"}

        exec_id = f"exec-{datetime.utcnow().strftime('%H%M%S')}-{len(self.executions)}"
        execution = {
            "id": exec_id,
            "team": team_name,
            "task": task,
            "context": context,
            "status": "running",
            "agent_results": [],
            "final_synthesis": "",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": "",
            "progress": 0,
        }
        self.executions[exec_id] = execution

        # Run in background
        asyncio.create_task(self._run_agents(exec_id, team, task, context))
        return execution

    async def _run_agents(self, exec_id: str, team: AgentTeam, task: str, context: str):
        """Run all agents in parallel, then synthesize."""
        execution = self.executions[exec_id]
        total = len(team.members) + 1  # agents + synthesis

        # Run each agent in a thread (parallel)
        agent_tasks = []
        for i, member in enumerate(team.members):
            agent_tasks.append(self._run_single_agent(exec_id, i, member, task, context, total))

        await asyncio.gather(*agent_tasks)

        # Synthesize all agent results
        results = execution["agent_results"]
        if results:
            try:
                all_outputs = "\n\n".join([
                    f"## {r['agent']} ({r['role']})\n{r['output']}"
                    for r in results if r.get("output")
                ])
                synth_system = "You are a team orchestrator. Synthesize the contributions from all team members into a single cohesive answer. Be concise and clear."
                synth_prompt = f"Task: {task}\n\nTeam member contributions:\n{all_outputs}\n\nSynthesized answer:"
                synthesis = await asyncio.to_thread(self._ollama_generate, synth_system, synth_prompt, 800)
            except Exception as e:
                synthesis = f"[Synthesis error: {e}]"
        else:
            synthesis = "[No agent outputs to synthesize]"

        execution["final_synthesis"] = synthesis
        execution["status"] = "completed"
        execution["progress"] = 100
        execution["completed_at"] = datetime.utcnow().isoformat()

    async def _run_single_agent(self, exec_id: str, idx: int, agent: TeamAgent, task: str, context: str, total: int):
        """Run a single agent."""
        execution = self.executions[exec_id]

        result = {
            "agent": agent.name,
            "role": agent.role,
            "status": "thinking",
            "output": "",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": "",
        }

        # Ensure slot exists
        while len(execution["agent_results"]) <= idx:
            execution["agent_results"].append(None)
        execution["agent_results"][idx] = result

        # Build system prompt
        system = f"You are {agent.name}, a {agent.role}."
        if agent.system_prompt:
            system += f" {agent.system_prompt}"
        system += " Provide a focused, professional response to the task based on your role."

        # Build user prompt
        prompt = f"Task: {task}"
        if context:
            prompt += f"\n\nContext: {context}"
        prompt += f"\n\nAs {agent.name} ({agent.role}), provide your contribution:"

        # Run LLM in thread (non-blocking)
        try:
            output = await asyncio.to_thread(self._ollama_generate, system, prompt, 800)
            result["output"] = output
            result["status"] = "completed"
        except Exception as e:
            result["output"] = f"[Error: {e}]"
            result["status"] = "failed"

        result["completed_at"] = datetime.utcnow().isoformat()
        execution["agent_results"][idx] = result

        # Update progress
        done = sum(1 for r in execution["agent_results"] if r and r.get("status") in ("completed", "failed"))
        execution["progress"] = int((done / total) * 90)

    def get_execution(self, exec_id: str) -> Optional[dict]:
        return self.executions.get(exec_id)

    def list_executions(self) -> List[dict]:
        return [
            {
                "id": eid,
                "team": e["team"],
                "task": e["task"],
                "status": e["status"],
                "progress": e["progress"],
                "agents": len(e["agent_results"]),
                "started_at": e["started_at"],
            }
            for eid, e in self.executions.items()
        ]

    def list_teams(self) -> List[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "members": [{"name": m.name, "role": m.role, "model": m.model} for m in t.members],
                "member_count": len(t.members)
            }
            for t in self.teams.values()
        ]

    def from_template(self, template_name: str) -> Optional[AgentTeam]:
        templates = {
            "finance": {
                "name": "Finance Team",
                "description": "Financial analysis team with web search, data crunching, and synthesis",
                "members": [
                    {"name": "Web Agent", "role": "Search the web for financial news and market data", "model": "auto", "tools": ["web_search"]},
                    {"name": "Data Agent", "role": "Analyze financial metrics and calculate ratios", "model": "auto", "tools": ["code_exec"]},
                    {"name": "Analyst Agent", "role": "Synthesize findings into an investment recommendation", "model": "auto"},
                ]
            },
            "research": {
                "name": "Research Team",
                "description": "Multi-agent research team with source finding, reading, and synthesis",
                "members": [
                    {"name": "Scout Agent", "role": "Find and identify relevant information sources", "model": "auto", "tools": ["web_search"]},
                    {"name": "Reader Agent", "role": "Extract key facts and insights from sources", "model": "auto"},
                    {"name": "Synthesizer Agent", "role": "Synthesize findings into a structured report", "model": "auto"},
                ]
            },
            "legal": {
                "name": "Legal Team",
                "description": "Legal research and strategy team",
                "members": [
                    {"name": "Research Agent", "role": "Find relevant laws, regulations, and precedents", "model": "auto", "tools": ["web_search"]},
                    {"name": "Contract Agent", "role": "Analyze contract terms and identify risks", "model": "auto"},
                    {"name": "Strategy Agent", "role": "Develop legal strategy and recommendations", "model": "auto"},
                ]
            },
            "engineering": {
                "name": "Engineering Team",
                "description": "Software engineering team with architecture, coding, and testing",
                "members": [
                    {"name": "Architect Agent", "role": "Design system architecture and component boundaries", "model": "auto", "tools": ["code_exec"]},
                    {"name": "Code Agent", "role": "Write production-quality code for the system", "model": "auto", "tools": ["code_exec"]},
                    {"name": "Test Agent", "role": "Write comprehensive tests for the implementation", "model": "auto", "tools": ["code_exec"]},
                ]
            },
            "marketing": {
                "name": "Marketing Team",
                "description": "Content marketing and strategy team",
                "members": [
                    {"name": "Strategy Agent", "role": "Develop marketing strategy and target audience", "model": "auto"},
                    {"name": "Content Agent", "role": "Write compelling marketing copy and content", "model": "auto"},
                    {"name": "SEO Agent", "role": "Optimize content for search engines and social media", "model": "auto"},
                ]
            },
            "product": {
                "name": "Product Team",
                "description": "Product design and planning team",
                "members": [
                    {"name": "Research Agent", "role": "Research user needs and market gaps", "model": "auto"},
                    {"name": "Design Agent", "role": "Design user flows and wireframes", "model": "auto"},
                    {"name": "PM Agent", "role": "Create product requirements and roadmap", "model": "auto"},
                ]
            },
        }

        tpl = templates.get(template_name)
        if not tpl:
            return None
        return self.create_team(tpl["name"], tpl.get("description", ""), tpl.get("members", []))


orchestrator = TeamOrchestrator()
