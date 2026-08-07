"""
EvolvixOS User Onboarding Service.

Provides a guided setup wizard for new users:
1. Account creation (existing auth)
2. Profile setup (name, role, preferences)
3. Organization setup (create or join)
4. First project setup (blockchain, web, mobile, etc.)
5. Agent configuration (select AI agents)
6. Verdis blockchain connection (optional)
"""

import time
import logging
import uuid
from typing import Optional

logger = logging.getLogger("evolvixos")


class OnboardingService:
    """Manages user onboarding flow and progress tracking."""

    ONBOARDING_STEPS = [
        {"id": "welcome", "title": "Welcome to EvolvixOS", "required": True, "order": 1},
        {"id": "profile", "title": "Set Up Your Profile", "required": True, "order": 2},
        {"id": "organization", "title": "Create or Join Organization", "required": True, "order": 3},
        {"id": "first_project", "title": "Create Your First Project", "required": True, "order": 4},
        {"id": "agents", "title": "Configure AI Agents", "required": False, "order": 5},
        {"id": "verdis_connect", "title": "Connect Verdis Blockchain", "required": False, "order": 6},
        {"id": "complete", "title": "Onboarding Complete", "required": True, "order": 7},
    ]

    PROJECT_TEMPLATES = [
        {"id": "blockchain", "name": "Blockchain Project", "icon": "link", "description": "Substrate-based blockchain development"},
        {"id": "web_backend", "name": "Web Backend", "icon": "server", "description": "API and microservices development"},
        {"id": "frontend", "name": "Frontend Application", "icon": "layout", "description": "React/Vue/web app development"},
        {"id": "mobile", "name": "Mobile App", "icon": "smartphone", "description": "iOS/Android app development"},
        {"id": "infra", "name": "Infrastructure", "icon": "cloud", "description": "DevOps and infrastructure setup"},
        {"id": "ai_ml", "name": "AI/ML Project", "icon": "cpu", "description": "Machine learning and AI development"},
        {"id": "generic", "name": "Generic Project", "icon": "folder", "description": "General-purpose software project"},
    ]

    AGENT_PRESETS = [
        {"id": "architect", "name": "AI Architect", "description": "System design and architecture review", "recommended_for": ["blockchain", "web_backend", "infra"]},
        {"id": "security", "name": "Security Agent", "description": "Vulnerability scanning and security audit", "recommended_for": ["blockchain", "web_backend", "infra"]},
        {"id": "developer", "name": "AI Developer", "description": "Code generation and refactoring", "recommended_for": ["web_backend", "frontend", "mobile", "ai_ml"]},
        {"id": "tester", "name": "Test Agent", "description": "Automated testing and QA", "recommended_for": ["web_backend", "frontend", "mobile"]},
        {"id": "devops", "name": "DevOps Agent", "description": "CI/CD and deployment automation", "recommended_for": ["infra", "web_backend"]},
        {"id": "reviewer", "name": "Code Reviewer", "description": "PR review and code quality", "recommended_for": ["web_backend", "frontend", "mobile", "ai_ml"]},
    ]

    def __init__(self):
        # In-memory store (would be DB in production)
        self._onboarding_state: dict[str, dict] = {}

    def get_onboarding_steps(self) -> list[dict]:
        """Get all onboarding steps."""
        return self.ONBOARDING_STEPS

    def get_project_templates(self) -> list[dict]:
        """Get available project templates."""
        return self.PROJECT_TEMPLATES

    def get_agent_presets(self) -> list[dict]:
        """Get available AI agent presets."""
        return self.AGENT_PRESETS

    def start_onboarding(self, user_id: str) -> dict:
        """Start the onboarding flow for a new user."""
        if user_id not in self._onboarding_state:
            self._onboarding_state[user_id] = {
                "user_id": user_id,
                "started_at": int(time.time()),
                "current_step": "welcome",
                "completed_steps": [],
                "profile": {},
                "organization": {},
                "project": {},
                "agents": [],
                "verdis_connected": False,
            }
        return self._onboarding_state[user_id]

    def get_progress(self, user_id: str) -> dict:
        """Get onboarding progress for a user."""
        if user_id not in self._onboarding_state:
            return self.start_onboarding(user_id)

        state = self._onboarding_state[user_id]
        total_steps = len(self.ONBOARDING_STEPS)
        completed = len(state["completed_steps"])
        progress_pct = (completed / total_steps) * 100

        return {
            **state,
            "progress_percent": round(progress_pct, 1),
            "total_steps": total_steps,
            "completed_count": completed,
            "remaining_steps": [s for s in self.ONBOARDING_STEPS if s["id"] not in state["completed_steps"]],
        }

    def complete_step(self, user_id: str, step_id: str, data: dict = None) -> dict:
        """Complete an onboarding step."""
        if user_id not in self._onboarding_state:
            self.start_onboarding(user_id)

        state = self._onboarding_state[user_id]

        if step_id not in [s["id"] for s in self.ONBOARDING_STEPS]:
            return {"error": "Invalid step ID"}

        if step_id not in state["completed_steps"]:
            state["completed_steps"].append(step_id)

        # Store step-specific data
        if data:
            if step_id == "profile":
                state["profile"] = data
            elif step_id == "organization":
                state["organization"] = data
            elif step_id == "first_project":
                state["project"] = data
            elif step_id == "agents":
                state["agents"] = data.get("agent_ids", [])
            elif step_id == "verdis_connect":
                state["verdis_connected"] = data.get("connected", False)

        # Determine next step
        current_order = next((s["order"] for s in self.ONBOARDING_STEPS if s["id"] == step_id), 0)
        next_step = next((s for s in self.ONBOARDING_STEPS if s["order"] == current_order + 1), None)
        state["current_step"] = next_step["id"] if next_step else "complete"

        # Check if onboarding is complete
        required_steps = [s["id"] for s in self.ONBOARDING_STEPS if s["required"]]
        if all(s in state["completed_steps"] for s in required_steps):
            state["completed_at"] = int(time.time())

        return self.get_progress(user_id)

    def skip_step(self, user_id: str, step_id: str) -> dict:
        """Skip an optional onboarding step."""
        step = next((s for s in self.ONBOARDING_STEPS if s["id"] == step_id), None)
        if step and not step["required"]:
            return self.complete_step(user_id, step_id, {})
        return {"error": "Cannot skip required step"}

    def get_recommended_agents(self, project_type: str) -> list[dict]:
        """Get recommended AI agents for a project type."""
        return [a for a in self.AGENT_PRESETS if project_type in a.get("recommended_for", [])]

    def create_sample_project(self, user_id: str, template_id: str, name: str, description: str = "") -> dict:
        """Create a sample project from a template."""
        template = next((t for t in self.PROJECT_TEMPLATES if t["id"] == template_id), None)
        if not template:
            return {"error": "Invalid template ID"}

        project = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description or template["description"],
            "type": template_id,
            "template_name": template["name"],
            "created_by": user_id,
            "created_at": int(time.time()),
            "status": "active",
            "health_score": 100,
            "agent_count": 0,
            "pipeline_count": 0,
        }
        return project


# Singleton
onboarding = OnboardingService()
