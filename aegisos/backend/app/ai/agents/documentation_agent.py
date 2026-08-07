"""
AI Documentation Agent for EvolvixOS Phase 4.

Auto-generates technical documentation and API documentation for the Verdis ecosystem
across Rust/Substrate, Python/FastAPI, and TypeScript SDK stacks.
"""

import json
import re
from typing import Any, Optional

from structlog import get_logger

from app.ai.agents.base_agent import (
    AgentResult,
    AgentStatus,
    AgentTask,
    BaseAgent,
    TaskType,
)
from app.ai.prompts.system_prompts import DOCUMENTATION_SYSTEM_PROMPT

logger = get_logger(__name__)

VALID_DOC_TYPES = {"readme", "api_doc", "architecture", "user_guide", "developer_guide"}


class AIDocumentationAgent(BaseAgent):
    """
    Technical Documentation Writer for the Verdis ecosystem.

    Responsibilities:
    - Generates documentation from code: README files, architecture docs, user guides, developer guides.
    - Generates API documentation from OpenAPI specs, endpoint descriptions, request/response examples.
    - Documents Substrate pallets, extrinsics, storage items, events, errors, and RPC methods.
    - Documents FastAPI endpoints, Pydantic models, authentication, and error codes.
    - Documents TypeScript SDK classes, methods, types, and usage examples.
    """

    name: str = "documentation_agent"
    description: str = (
        "Technical Documentation Writer for the Verdis ecosystem, generating "
        "READMEs, API documentation, architecture guides, user guides, and developer guides."
    )
    handled_task_types: set[TaskType] = {
        TaskType.DOC_GENERATION,
        TaskType.API_DOC_GENERATION,
    }

    @property
    def system_prompt(self) -> str:
        """Return system prompt for AI Documentation Agent."""
        return DOCUMENTATION_SYSTEM_PROMPT

    def preprocess(self, task: AgentTask) -> str:
        """
        Preprocess task data into a formatted user prompt for the LLM.
        """
        data = task.data or {}
        task_type_str = task.type.value if hasattr(task.type, "value") else str(task.type)

        prompt_parts = [
            f"Task Type: {task_type_str}",
            f"Title: {data.get('title', data.get('name', data.get('api_name', 'Documentation Task')))}",
        ]

        if "doc_type" in data:
            prompt_parts.append(f"Document Type: {data['doc_type']}")
        elif task.type == TaskType.API_DOC_GENERATION:
            prompt_parts.append("Document Type: api_doc")

        if "description" in data:
            prompt_parts.append(f"Description / Context:\n{data['description']}")

        if "audience" in data:
            prompt_parts.append(f"Target Audience: {data['audience']}")

        if "project" in data or "component" in data:
            prompt_parts.append(f"Project/Component: {data.get('project', 'Verdis')} / {data.get('component', 'General')}")

        stack_info = data.get("stack") or data.get("language") or data.get("framework")
        if stack_info:
            prompt_parts.append(f"Technology Stack: {stack_info}")

        # Code / Source code input
        source_code = data.get("source_code") or data.get("code")
        if source_code:
            lang = data.get("language", "")
            prompt_parts.append(f"Source Code:\n```{lang}\n{source_code}\n```")

        # OpenAPI spec
        spec = data.get("openapi_spec") or data.get("spec")
        if spec:
            spec_str = json.dumps(spec, indent=2) if isinstance(spec, (dict, list)) else str(spec)
            prompt_parts.append(f"OpenAPI / API Spec:\n```json\n{spec_str}\n```")

        # Endpoint descriptions
        endpoints = data.get("endpoints")
        if endpoints:
            if isinstance(endpoints, list):
                ep_lines = []
                for ep in endpoints:
                    if isinstance(ep, dict):
                        ep_lines.append(f"  {ep.get('method', 'GET')} {ep.get('path', '/')} - {ep.get('description', '')}")
                    else:
                        ep_lines.append(f"  {ep}")
                prompt_parts.append("Endpoints:\n" + "\n".join(ep_lines))
            elif isinstance(endpoints, dict):
                prompt_parts.append(f"Endpoints:\n```json\n{json.dumps(endpoints, indent=2)}\n```")
            else:
                prompt_parts.append(f"Endpoints:\n{endpoints}")

        if "existing_docs" in data:
            prompt_parts.append(f"Existing Documentation:\n{data['existing_docs']}")

        # Other fields
        other_data = {
            k: v for k, v in data.items()
            if k not in (
                "title", "name", "api_name", "doc_type", "description", "audience",
                "project", "component", "stack", "language", "framework",
                "source_code", "code", "openapi_spec", "spec", "endpoints", "existing_docs"
            )
        }
        if other_data:
            prompt_parts.append(f"Additional Context:\n{json.dumps(other_data, indent=2, default=str)}")

        prompt_parts.append(
            "\nGenerate comprehensive technical documentation in English and Markdown format based on the details above. "
            "Output your response strictly as valid JSON structured with doc_type, title, content, sections, and code_examples."
        )

        return "\n\n".join(prompt_parts)

    def postprocess(self, content: str, task: AgentTask) -> AgentResult:
        """
        Transform LLM output into an AgentResult, extracting structured:
        - doc_type (string: readme, api_doc, architecture, user_guide, developer_guide)
        - title (string)
        - content (string, full markdown)
        - sections (list of dicts with heading, content)
        - code_examples (list of dicts with language, code, description)
        """
        result = super().postprocess(content, task)
        structured = result.structured_data or {}

        # Fallback JSON parsing if base class failed
        if not structured and content:
            match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
            if match:
                try:
                    structured = json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass

            if not structured:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    try:
                        structured = json.loads(content[start:end])
                    except json.JSONDecodeError:
                        pass

        if not isinstance(structured, dict):
            structured = {}

        data = task.data or {}

        # 1. doc_type
        raw_doc_type = structured.get("doc_type")
        if isinstance(raw_doc_type, str) and raw_doc_type.lower() in VALID_DOC_TYPES:
            doc_type = raw_doc_type.lower()
        else:
            if task.type == TaskType.API_DOC_GENERATION:
                doc_type = "api_doc"
            else:
                req_dt = str(data.get("doc_type", "")).lower()
                doc_type = req_dt if req_dt in VALID_DOC_TYPES else "developer_guide"

        # 2. title
        default_title = data.get("title", data.get("name", data.get("api_name", "Technical Documentation")))
        title = str(structured.get("title") or default_title)

        # 3. content (full markdown)
        doc_content = str(structured.get("content") or content)

        # 4. sections
        raw_sections = structured.get("sections", [])
        sections: list[dict[str, str]] = []
        if isinstance(raw_sections, list):
            for item in raw_sections:
                if isinstance(item, dict):
                    sections.append({
                        "heading": str(item.get("heading", item.get("title", "Section"))),
                        "content": str(item.get("content", item.get("body", ""))),
                    })

        # 5. code_examples
        raw_examples = structured.get("code_examples", [])
        code_examples: list[dict[str, str]] = []
        if isinstance(raw_examples, list):
            for item in raw_examples:
                if isinstance(item, dict):
                    code_examples.append({
                        "language": str(item.get("language", item.get("lang", ""))),
                        "code": str(item.get("code", item.get("snippet", ""))),
                        "description": str(item.get("description", item.get("explanation", ""))),
                    })

        updated_structured = {
            "doc_type": doc_type,
            "title": title,
            "content": doc_content,
            "sections": sections,
            "code_examples": code_examples,
        }

        # Preserve any additional keys
        for k, v in structured.items():
            if k not in updated_structured:
                updated_structured[k] = v

        result.structured_data = updated_structured
        return result

    def get_temperature(self, task_type: TaskType) -> float:
        """Get temperature for documentation tasks."""
        return 0.4

    def get_max_tokens(self, task_type: TaskType) -> int:
        """Get max tokens for documentation tasks."""
        return 6000
