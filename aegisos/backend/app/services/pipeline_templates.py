"""
Pipeline Templates — Post-MVP Phase 4

Pre-configured pipeline templates for common feature types.
Each template defines:
- Default constraints and acceptance criteria
- Stage overrides (skip stages, adjust retries)
- Priority and project type defaults
- Estimated duration and complexity

Templates make it quick to start a pipeline without manually
specifying all the details each time.
"""

from typing import Optional
from pydantic import BaseModel, Field
from app.core.logging import get_logger

logger = get_logger("service.pipeline_templates")


class PipelineTemplate(BaseModel):
    """A pre-configured pipeline template."""
    id: str
    name: str
    description: str
    icon: str = "📦"
    category: str = "general"  # general, bugfix, feature, infra, security
    default_title_prefix: str = ""
    default_priority: str = "medium"
    default_project_type: str = "generic"
    default_constraints: list[str] = Field(default_factory=list)
    default_acceptance_criteria: list[str] = Field(default_factory=list)
    skip_stages: list[str] = Field(default_factory=list)  # stage names to skip
    stage_overrides: dict = Field(default_factory=dict)  # stage -> {max_retries, agent}
    estimated_duration_hours: float = 4.0
    complexity: str = "medium"  # low, medium, high, critical
    tags: list[str] = Field(default_factory=list)


# Built-in templates
BUILTIN_TEMPLATES: list[PipelineTemplate] = [
    PipelineTemplate(
        id="bugfix",
        name="Bug Fix",
        description="Quick bug fix with focused QA and security review",
        icon="🐛",
        category="bugfix",
        default_title_prefix="Fix:",
        default_priority="high",
        default_constraints=[
            "Must not break existing functionality",
            "Include regression test for the bug",
            "Minimal code changes only",
        ],
        default_acceptance_criteria=[
            "Bug is reproducible before fix",
            "Bug is not reproducible after fix",
            "All existing tests still pass",
        ],
        skip_stages=["performance_review"],  # skip perf for bugfixes
        estimated_duration_hours=2.0,
        complexity="low",
        tags=["bugfix", "quick", "patch"],
    ),
    PipelineTemplate(
        id="new_feature",
        name="New Feature",
        description="Full pipeline for a new feature from PRD to release",
        icon="✨",
        category="feature",
        default_title_prefix="Feat:",
        default_priority="medium",
        default_constraints=[
            "Follow existing code patterns",
            "Include comprehensive test coverage",
            "Update documentation",
        ],
        default_acceptance_criteria=[
            "Feature works as described in PRD",
            "Test coverage > 80%",
            "Documentation updated",
            "No security vulnerabilities",
        ],
        estimated_duration_hours=8.0,
        complexity="medium",
        tags=["feature", "new", "full-pipeline"],
    ),
    PipelineTemplate(
        id="refactor",
        name="Refactoring",
        description="Code refactoring with architecture review and QA",
        icon="🔧",
        category="feature",
        default_title_prefix="Refactor:",
        default_priority="low",
        default_constraints=[
            "No behavioral changes",
            "Improve code readability or performance",
            "All existing tests must pass",
        ],
        default_acceptance_criteria=[
            "No behavioral changes detected",
            "Code quality improved (measured)",
            "All tests pass",
            "No new dependencies added",
        ],
        skip_stages=["prd_generation"],  # refactoring doesn't need a PRD
        stage_overrides={
            "architecture_design": {"max_retries": 2},
        },
        estimated_duration_hours=4.0,
        complexity="medium",
        tags=["refactor", "cleanup", "tech-debt"],
    ),
    PipelineTemplate(
        id="security_patch",
        name="Security Patch",
        description="Critical security patch with enhanced security review",
        icon="🔒",
        category="security",
        default_title_prefix="Security:",
        default_priority="critical",
        default_constraints=[
            "Fix the specific vulnerability",
            "Include security test for the fix",
            "No new attack surface introduced",
            "Follow OWASP best practices",
        ],
        default_acceptance_criteria=[
            "Vulnerability is patched",
            "No regressions in security tests",
            "Security audit passes",
            "Penetration test shows no exploit",
        ],
        stage_overrides={
            "security_review": {"max_retries": 3},  # extra retries for security
        },
        estimated_duration_hours=3.0,
        complexity="critical",
        tags=["security", "critical", "vulnerability", "patch"],
    ),
    PipelineTemplate(
        id="infra_change",
        name="Infrastructure Change",
        description="Infrastructure or deployment configuration change",
        icon="🏗️",
        category="infra",
        default_title_prefix="Infra:",
        default_priority="high",
        default_project_type="infrastructure",
        default_constraints=[
            "Zero downtime deployment",
            "Rollback plan required",
            "Infrastructure as code",
            "Monitor after deployment",
        ],
        default_acceptance_criteria=[
            "Deployment succeeds in staging",
            "No service interruption",
            "Monitoring shows healthy state",
            "Rollback tested",
        ],
        skip_stages=["implementation", "qa_testing"],  # infra doesn't need code gen
        stage_overrides={
            "architecture_design": {"max_retries": 2},
            "performance_review": {"max_retries": 2},
        },
        estimated_duration_hours=3.0,
        complexity="high",
        tags=["infrastructure", "deployment", "devops"],
    ),
    PipelineTemplate(
        id="api_endpoint",
        name="New API Endpoint",
        description="Add a new REST API endpoint with full pipeline",
        icon="🔌",
        category="feature",
        default_title_prefix="API:",
        default_priority="medium",
        default_project_type="web_backend",
        default_constraints=[
            "Follow REST conventions",
            "Include input validation",
            "Add OpenAPI documentation",
            "Rate limiting enabled",
        ],
        default_acceptance_criteria=[
            "Endpoint returns correct status codes",
            "Input validation works",
            "OpenAPI spec updated",
            "Integration tests pass",
        ],
        estimated_duration_hours=4.0,
        complexity="medium",
        tags=["api", "rest", "endpoint", "backend"],
    ),
    PipelineTemplate(
        id="db_migration",
        name="Database Migration",
        description="Database schema migration with rollback support",
        icon="🗄️",
        category="infra",
        default_title_prefix="DB:",
        default_priority="high",
        default_project_type="web_backend",
        default_constraints=[
            "Backward compatible if possible",
            "Rollback migration required",
            "Data integrity checks",
            "Zero data loss",
        ],
        default_acceptance_criteria=[
            "Migration applies cleanly",
            "Rollback migration works",
            "No data loss",
            "Performance not degraded",
        ],
        skip_stages=["prd_generation"],
        stage_overrides={
            "qa_testing": {"max_retries": 2},
        },
        estimated_duration_hours=2.0,
        complexity="high",
        tags=["database", "migration", "schema"],
    ),
    PipelineTemplate(
        id="hotfix",
        name="Hotfix",
        description="Emergency hotfix — minimal stages, fast turnaround",
        icon="🚨",
        category="bugfix",
        default_title_prefix="Hotfix:",
        default_priority="critical",
        default_constraints=[
            "Fix the issue immediately",
            "Minimal changes",
            "Deploy as soon as QA passes",
        ],
        default_acceptance_criteria=[
            "Issue is resolved",
            "Critical path tests pass",
        ],
        skip_stages=["prd_generation", "task_decomposition", "performance_review", "documentation"],
        stage_overrides={
            "qa_testing": {"max_retries": 0},
            "security_review": {"max_retries": 0},
            "code_review": {"max_retries": 0},
        },
        estimated_duration_hours=1.0,
        complexity="critical",
        tags=["hotfix", "emergency", "critical", "fast"],
    ),
]


# Custom template store (production would use DB)
_custom_templates: dict[str, PipelineTemplate] = {}


def list_templates(category: Optional[str] = None) -> list[PipelineTemplate]:
    """List all available templates, optionally filtered by category."""
    templates = list(BUILTIN_TEMPLATES) + list(_custom_templates.values())
    if category:
        templates = [t for t in templates if t.category == category]
    return templates


def get_template(template_id: str) -> Optional[PipelineTemplate]:
    """Get a template by ID."""
    for t in BUILTIN_TEMPLATES:
        if t.id == template_id:
            return t
    return _custom_templates.get(template_id)


def register_custom_template(template: PipelineTemplate) -> PipelineTemplate:
    """Register a custom template."""
    _custom_templates[template.id] = template
    logger.info("custom_template_registered", template_id=template.id, name=template.name)
    return template


def delete_custom_template(template_id: str) -> bool:
    """Delete a custom template. Built-in templates cannot be deleted."""
    if template_id in _custom_templates:
        del _custom_templates[template_id]
        return True
    return False


def apply_template(template_id: str, title: str, description: str,
                   extra_constraints: list[str] = None,
                   extra_acceptance: list[str] = None) -> Optional[dict]:
    """
    Apply a template to create feature request data.
    
    Returns a dict suitable for FeatureRequest construction,
    or None if template not found.
    """
    template = get_template(template_id)
    if not template:
        return None

    # Build title with prefix
    full_title = title
    if template.default_title_prefix and not title.startswith(template.default_title_prefix):
        full_title = f"{template.default_title_prefix} {title}"

    # Merge constraints
    constraints = list(template.default_constraints)
    if extra_constraints:
        constraints.extend(extra_constraints)

    # Merge acceptance criteria
    acceptance = list(template.default_acceptance_criteria)
    if extra_acceptance:
        acceptance.extend(extra_acceptance)

    return {
        "title": full_title,
        "description": description,
        "project_type": template.default_project_type,
        "priority": template.default_priority,
        "constraints": constraints,
        "acceptance_criteria": acceptance,
        "_template": {
            "id": template.id,
            "name": template.name,
            "skip_stages": template.skip_stages,
            "stage_overrides": template.stage_overrides,
        },
    }


def get_template_categories() -> list[dict]:
    """Get all template categories with counts."""
    templates = list(BUILTIN_TEMPLATES) + list(_custom_templates.values())
    categories = {}
    for t in templates:
        if t.category not in categories:
            categories[t.category] = {"name": t.category, "count": 0, "templates": []}
        categories[t.category]["count"] += 1
        categories[t.category]["templates"].append(t.id)
    return list(categories.values())
