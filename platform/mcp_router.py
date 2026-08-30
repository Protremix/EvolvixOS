"""
EvolvixOS MCP Tool Router
Inspired by awesome-llm-apps multi_mcp_agent_router pattern.

Routes queries to specialized agents, each with their own MCP server configs.
Supports: GitHub, Filesystem, Browser, Notion, and custom MCP servers.
"""
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MCPAgent:
    """A specialized agent with MCP server access."""
    name: str
    description: str
    system_prompt: str
    icon: str = "🤖"
    mcp_servers: List[Dict] = field(default_factory=list)
    model: str = "auto"


class MCPRouter:
    """Routes queries to specialized MCP-powered agents."""

    # Pre-built agent templates
    TEMPLATES = {
        "code_reviewer": MCPAgent(
            name="Code Reviewer",
            description="Reviews code for bugs, anti-patterns, and maintainability",
            icon="🔍",
            system_prompt="You are an expert code reviewer. Analyze code for bugs, anti-patterns, performance, and security. Be specific. Reference line numbers. Suggest fixes.",
            mcp_servers=[
                {"name": "github", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
                {"name": "filesystem", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]},
            ],
        ),
        "security_auditor": MCPAgent(
            name="Security Auditor",
            description="Scans for OWASP Top 10, injection, XSS, secrets, and auth issues",
            icon="🛡️",
            system_prompt="You are a security auditor. Check for OWASP Top 10, injection, XSS, hardcoded secrets, auth flaws. Rate findings: Critical/High/Medium/Low.",
            mcp_servers=[
                {"name": "github", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
                {"name": "fetch", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-fetch"]},
            ],
        ),
        "researcher": MCPAgent(
            name="Researcher",
            description="Web research and information gathering",
            icon="🔬",
            system_prompt="You are a research agent. Find relevant sources, extract key information, and synthesize findings into clear reports.",
            mcp_servers=[
                {"name": "fetch", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-fetch"]},
                {"name": "browser", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-puppeteer"]},
            ],
        ),
        "data_analyst": MCPAgent(
            name="Data Analyst",
            description="Analyzes CSV, Excel, and database data",
            icon="📊",
            system_prompt="You are a data analyst. Analyze data files, create summaries, find patterns, and generate insights.",
            mcp_servers=[
                {"name": "filesystem", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]},
            ],
        ),
        "devops": MCPAgent(
            name="DevOps Agent",
            description="Manages deployments, monitors services, and handles infrastructure",
            icon="🚀",
            system_prompt="You are a DevOps agent. Manage deployments, check service health, handle infrastructure tasks, and automate operations.",
            mcp_servers=[
                {"name": "filesystem", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/opt/evolvixos"]},
            ],
        ),
    }

    def __init__(self):
        self.agents: Dict[str, MCPAgent] = {}
        # Load templates
        for key, agent in self.TEMPLATES.items():
            self.agents[key] = agent

    def list_agents(self) -> List[dict]:
        """List all available MCP agents."""
        return [
            {
                "key": k,
                "name": a.name,
                "description": a.description,
                "icon": a.icon,
                "mcp_servers": [s["name"] for s in a.mcp_servers],
                "model": a.model
            }
            for k, a in self.agents.items()
        ]

    def get_agent(self, key: str) -> Optional[MCPAgent]:
        """Get an agent by key."""
        return self.agents.get(key)

    def route(self, query: str) -> dict:
        """Route a query to the best agent based on keywords."""
        query_lower = query.lower()
        scores = {}

        for key, agent in self.agents.items():
            # Simple keyword matching (production would use embeddings)
            keywords = agent.description.lower().split() + agent.name.lower().split()
            score = sum(1 for kw in keywords if kw in query_lower)
            scores[key] = score

        best_key = max(scores, key=scores.get) if scores else None
        if not best_key or scores[best_key] == 0:
            return {"routed_to": "general", "reason": "No specific match found"}

        agent = self.agents[best_key]
        return {
            "routed_to": best_key,
            "agent_name": agent.name,
            "agent_description": agent.description,
            "mcp_servers": [s["name"] for s in agent.mcp_servers],
            "system_prompt": agent.system_prompt,
            "model": agent.model,
            "confidence": scores[best_key]
        }

    def add_agent(self, key: str, agent: dict) -> bool:
        """Add a custom MCP agent."""
        self.agents[key] = MCPAgent(**agent)
        return True

    def remove_agent(self, key: str) -> bool:
        """Remove an agent."""
        if key in self.agents and key not in self.TEMPLATES:
            del self.agents[key]
            return True
        return False


# Singleton
mcp_router = MCPRouter()
