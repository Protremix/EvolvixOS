"""
AI Core for EvolvixOS — Phase 3.

Provides LLM-powered agents for engineering automation:
- BaseAgent: Common interface for all AI agents
- AIWorkflowEngine: Orchestrates agent task routing
- Agents: CTO, Architect, Security, QA, Memory, Planner, Reviewer, Documentation

Architecture (per GPT-4o consultation):
- Base agent class + specialized agents
- Celery for async execution
- Redis event bus for inter-agent communication
- pgvector for knowledge base and semantic retrieval
- GPT-4o as the LLM (temperature 0.3 for analysis, 0.1 for security)
"""

__version__ = "0.1.0"
