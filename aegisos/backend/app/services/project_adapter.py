"""
Project Adapter Framework — MVP Feature #13

Adapts EvolvixOS to manage different project types (blockchain, web, mobile, etc.)
with project-type-specific configurations, templates, agent prompt overrides,
and validation rules. This enables EvolvixOS to serve as a universal engineering
platform that adapts its behavior based on the project's domain.
"""

from typing import Optional, Any
from pydantic import BaseModel, Field
from app.core.logging import get_logger

logger = get_logger("service.project_adapter")


# ============================================================
# Project Type Definitions
# ============================================================

class ProjectTypeConfig(BaseModel):
    """Configuration for a specific project type."""
    type_id: str = Field(..., description="Unique type identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field("", description="What this project type is for")
    icon: str = Field("📦", description="Emoji or icon identifier")
    default_language: str = Field("python", description="Primary programming language")
    supported_languages: list[str] = Field(
        default_factory=lambda: ["python", "javascript", "typescript"],
        description="Languages this project type supports",
    )
    file_structure: dict[str, str] = Field(
        default_factory=dict,
        description="Expected directory structure (path → description)",
    )
    agent_overrides: dict[str, str] = Field(
        default_factory=dict,
        description="Agent name → prompt override key",
    )
    task_types: list[str] = Field(
        default_factory=lambda: [
            "code_review", "security_scan", "test_generation",
            "documentation", "refactoring", "bug_fix",
        ],
        description="Task types relevant to this project type",
    )
    quality_gates: list[str] = Field(
        default_factory=lambda: ["lint", "test", "build"],
        description="Quality gate steps for this project type",
    )
    ci_template: dict[str, Any] = Field(
        default_factory=dict,
        description="CI/CD pipeline template",
    )
    monitoring_metrics: list[str] = Field(
        default_factory=lambda: ["cpu", "memory", "response_time"],
        description="Metrics to monitor for this project type",
    )
    security_checks: list[str] = Field(
        default_factory=lambda: ["dependency_scan", "sast"],
        description="Security checks specific to this project type",
    )


# ============================================================
# Built-in Project Type Adapters
# ============================================================

BLOCKCHAIN_ADAPTER = ProjectTypeConfig(
    type_id="blockchain",
    display_name="Blockchain / Web3",
    description="Layer-1/Layer-2 blockchain, DeFi, NFT platforms",
    icon="⛓️",
    default_language="rust",
    supported_languages=["rust", "typescript", "javascript", "python", "solidity"],
    file_structure={
        "runtime/": "Substrate runtime pallets",
        "pallets/": "Custom pallets",
        "node/": "Node service and RPC",
        "sdk/": "Client SDKs (TS, Python, Go)",
        "explorer/": "Block explorer frontend",
        "wallet/": "Wallet application",
        "docs/": "Protocol documentation",
    },
    agent_overrides={
        "cto_agent": "blockchain_architecture",
        "security_agent": "blockchain_security",
        "qa_agent": "blockchain_testing",
    },
    task_types=[
        "code_review", "security_scan", "test_generation",
        "documentation", "consensus_review", "pallet_audit",
        "runtime_upgrade", "storage_migration", "benchmarking",
    ],
    quality_gates=["cargo_test", "cargo_build", "cargo_clippy", "cargo_fmt", "wasm_build"],
    ci_template={
        "stages": ["lint", "test", "build_native", "build_wasm", "security_audit"],
        "test_command": "cargo test --release --workspace",
        "build_command": "cargo build --release",
    },
    monitoring_metrics=["block_height", "peer_count", "validator_count", "tps", "latency"],
    security_checks=["consensus_audit", "key_management", "slashing", "bridge_security", "sast"],
)

WEB_BACKEND_ADAPTER = ProjectTypeConfig(
    type_id="web_backend",
    display_name="Web Backend / API",
    description="FastAPI, Django, Flask, Express, NestJS backends",
    icon="🌐",
    default_language="python",
    supported_languages=["python", "typescript", "javascript", "go"],
    file_structure={
        "app/": "Application code",
        "tests/": "Test suite",
        "migrations/": "Database migrations",
        "docs/": "API documentation",
    },
    task_types=[
        "code_review", "security_scan", "test_generation",
        "documentation", "refactoring", "bug_fix",
        "api_design", "performance_optimization",
    ],
    quality_gates=["lint", "test", "build", "type_check", "security_scan"],
    ci_template={
        "stages": ["lint", "test", "build", "security_scan"],
        "test_command": "pytest --tb=short -q",
    },
    monitoring_metrics=["cpu", "memory", "response_time", "error_rate", "throughput"],
    security_checks=["dependency_scan", "sast", "api_security", "auth_audit"],
)

FRONTEND_ADAPTER = ProjectTypeConfig(
    type_id="frontend",
    display_name="Frontend / SPA",
    description="React, Vue, Angular, Svelte single-page applications",
    icon="🎨",
    default_language="typescript",
    supported_languages=["typescript", "javascript"],
    file_structure={
        "src/": "Source code",
        "public/": "Static assets",
        "tests/": "Test suite",
        "components/": "UI components",
    },
    task_types=[
        "code_review", "test_generation", "documentation",
        "refactoring", "ui_audit", "accessibility_check",
    ],
    quality_gates=["lint", "test", "build", "type_check"],
    ci_template={
        "stages": ["lint", "test", "build"],
        "test_command": "npm test",
        "build_command": "npm run build",
    },
    monitoring_metrics=["bundle_size", "lighthouse_score", "load_time", "error_rate"],
    security_checks=["xss_scan", "dependency_scan", "sast"],
)

MOBILE_ADAPTER = ProjectTypeConfig(
    type_id="mobile",
    display_name="Mobile App",
    description="Flutter, React Native, native iOS/Android applications",
    icon="📱",
    default_language="dart",
    supported_languages=["dart", "typescript", "kotlin", "swift"],
    file_structure={
        "lib/": "Application code",
        "test/": "Test suite",
        "assets/": "Static assets",
    },
    task_types=[
        "code_review", "test_generation", "documentation",
        "refactoring", "ui_audit", "platform_compat",
    ],
    quality_gates=["lint", "test", "build", "analyze"],
    ci_template={
        "stages": ["lint", "test", "build"],
        "test_command": "flutter test",
        "build_command": "flutter build apk",
    },
    monitoring_metrics=["app_size", "startup_time", "frame_rate", "crash_rate"],
    security_checks=["dependency_scan", "sast", "secure_storage"],
)

INFRASTRUCTURE_ADAPTER = ProjectTypeConfig(
    type_id="infrastructure",
    display_name="Infrastructure / DevOps",
    description="Docker, Kubernetes, Terraform, CI/CD pipelines",
    icon="🔧",
    default_language="yaml",
    supported_languages=["yaml", "python", "bash", "hcl"],
    file_structure={
        "docker/": "Docker configurations",
        "k8s/": "Kubernetes manifests",
        "terraform/": "Infrastructure as code",
        "scripts/": "Automation scripts",
    },
    task_types=[
        "code_review", "security_scan", "documentation",
        "config_audit", "deployment_review",
    ],
    quality_gates=["lint", "validate", "plan", "security_scan"],
    ci_template={
        "stages": ["validate", "plan", "apply"],
    },
    monitoring_metrics=["uptime", "latency", "cost", "resource_utilization"],
    security_checks=["config_scan", "secret_scan", "network_audit"],
)

AI_ML_ADAPTER = ProjectTypeConfig(
    type_id="ai_ml",
    display_name="AI / ML Project",
    description="Machine learning, LLM applications, data pipelines",
    icon="🤖",
    default_language="python",
    supported_languages=["python", "typescript"],
    file_structure={
        "models/": "Model definitions",
        "data/": "Data pipelines",
        "training/": "Training scripts",
        "inference/": "Inference services",
        "tests/": "Test suite",
    },
    task_types=[
        "code_review", "test_generation", "documentation",
        "model_audit", "data_validation", "performance_benchmark",
    ],
    quality_gates=["lint", "test", "build", "model_validate"],
    ci_template={
        "stages": ["lint", "test", "train", "validate"],
    },
    monitoring_metrics=["latency", "throughput", "accuracy", "drift_score"],
    security_checks=["data_leak", "model_poisoning", "dependency_scan", "sast"],
)

GENERIC_ADAPTER = ProjectTypeConfig(
    type_id="generic",
    display_name="Generic Project",
    description="Any other project type — uses defaults",
    icon="📦",
    default_language="python",
    supported_languages=["python", "javascript", "typescript"],
    file_structure={},
    task_types=[
        "code_review", "security_scan", "test_generation",
        "documentation", "refactoring", "bug_fix",
    ],
    quality_gates=["lint", "test", "build"],
    ci_template={
        "stages": ["lint", "test", "build"],
    },
    monitoring_metrics=["cpu", "memory", "response_time"],
    security_checks=["dependency_scan", "sast"],
)


# ============================================================
# Adapter Registry
# ============================================================

_ADAPTERS: dict[str, ProjectTypeConfig] = {}


def _register_builtin_adapters():
    """Register all built-in project type adapters."""
    for adapter in [
        BLOCKCHAIN_ADAPTER, WEB_BACKEND_ADAPTER, FRONTEND_ADAPTER,
        MOBILE_ADAPTER, INFRASTRUCTURE_ADAPTER, AI_ML_ADAPTER,
        GENERIC_ADAPTER,
    ]:
        _ADAPTERS[adapter.type_id] = adapter
    logger.info("project_adapters_registered", count=len(_ADAPTERS))


_register_builtin_adapters()


def get_adapter(project_type: str) -> ProjectTypeConfig:
    """Get the adapter for a project type. Falls back to generic."""
    adapter = _ADAPTERS.get(project_type)
    if adapter is None:
        logger.warning("adapter_not_found", project_type=project_type, fallback="generic")
        return _ADAPTERS["generic"]
    return adapter


def list_adapters() -> list[ProjectTypeConfig]:
    """List all registered project type adapters."""
    return list(_ADAPTERS.values())


def register_adapter(adapter: ProjectTypeConfig) -> None:
    """Register a custom project type adapter."""
    _ADAPTERS[adapter.type_id] = adapter
    logger.info("adapter_registered", type_id=adapter.type_id)


def get_adapter_summary(adapter: ProjectTypeConfig) -> dict:
    """Get a summary dict for API responses."""
    return {
        "type_id": adapter.type_id,
        "display_name": adapter.display_name,
        "description": adapter.description,
        "icon": adapter.icon,
        "default_language": adapter.default_language,
        "supported_languages": adapter.supported_languages,
        "task_types": adapter.task_types,
        "quality_gates": adapter.quality_gates,
        "security_checks": adapter.security_checks,
        "monitoring_metrics": adapter.monitoring_metrics,
        "file_structure": adapter.file_structure,
    }


def validate_project_config(project_type: str, config: dict) -> list[str]:
    """Validate a project config against its adapter. Returns list of warnings."""
    adapter = get_adapter(project_type)
    warnings = []

    if "language" in config:
        if config["language"] not in adapter.supported_languages:
            warnings.append(
                f"Language '{config['language']}' is not in the supported list "
                f"for project type '{adapter.display_name}'. "
                f"Supported: {', '.join(adapter.supported_languages)}"
            )

    if "task_type" in config:
        if config["task_type"] not in adapter.task_types:
            warnings.append(
                f"Task type '{config['task_type']}' is not typically used "
                f"for project type '{adapter.display_name}'."
            )

    return warnings


def get_quality_gate_commands(project_type: str) -> dict[str, str]:
    """Get the quality gate commands for a project type."""
    adapter = get_adapter(project_type)
    commands = {}
    gate_command_map = {
        "cargo_test": "cargo test --release --workspace",
        "cargo_build": "cargo build --release",
        "cargo_clippy": "cargo clippy -- -D warnings",
        "cargo_fmt": "cargo fmt --check",
        "wasm_build": "cargo build --release --no-default-features",
        "lint": adapter.ci_template.get("lint_command", "npm run lint || ruff check ."),
        "test": adapter.ci_template.get("test_command", "pytest --tb=short -q"),
        "build": adapter.ci_template.get("build_command", "npm run build || cargo build --release"),
        "type_check": "tsc --noEmit",
        "security_scan": "bandit -r . || npm audit",
        "analyze": "flutter analyze",
        "validate": "terraform validate",
        "plan": "terraform plan",
        "model_validate": "python -m pytest tests/test_models.py",
    }
    for gate in adapter.quality_gates:
        commands[gate] = gate_command_map.get(gate, f"echo 'Run {gate}'")
    return commands
