# AI Agents Guide

EvolvixOS includes 11 autonomous AI agents that handle different aspects of the software development lifecycle.

## Agent Roster

| Agent | Role | Specialization |
|-------|------|----------------|
| **CTO Agent** | Strategic decisions | Architecture, technology choices, trade-off analysis |
| **Architect Agent** | System design | Component design, API contracts, data models |
| **Security Agent** | Security analysis | Vulnerability detection, OWASP compliance, crypto review |
| **QA Agent** | Quality assurance | Test planning, test execution, coverage analysis |
| **Planner Agent** | Task decomposition | Breaking features into implementable tasks |
| **Reviewer Agent** | Code review | Quality, maintainability, best practices |
| **Documentation Agent** | Documentation | API docs, README, developer guides |
| **Memory Agent** | Knowledge retention | Pattern detection, lesson extraction, knowledge base |
| **Test Generator Agent** | Test creation | Generates pytest/jest test suites from source |
| **CI Healer Agent** | CI/CD repair | Diagnoses failures, generates fixes |
| **Workflow Engine** | Orchestration | Routes tasks, manages pipelines |

## How Agents Work

### Task Dispatch

```bash
# Dispatch a single task to an agent
curl -X POST http://localhost:8000/api/v1/ai/dispatch   -H "Authorization: Bearer <token>"   -d '{
    "agent_name": "cto",
    "task_type": "architecture_review",
    "context": {
      "project": "verdis",
      "files": ["runtime/src/lib.rs"],
      "description": "Review runtime configuration"
    }
  }'

# Batch dispatch
curl -X POST http://localhost:8000/api/v1/ai/dispatch/batch   -H "Authorization: Bearer <token>"   -d '{
    "tasks": [
      {"agent_name": "security", "task_type": "security_audit", "context": {...}},
      {"agent_name": "qa", "task_type": "test_review", "context": {...}}
    ]
  }'
```

### Agent Configuration

Each agent has configurable settings:

```bash
# Get all agent configs
GET /api/v1/agent-config/

# Get specific agent
GET /api/v1/agent-config/cto

# Update global config
PUT /api/v1/agent-config/cto
{
  "model": "gpt-4o",
  "temperature": 0.3,
  "max_tokens": 4000,
  "enabled": true
}

# Per-project override
PUT /api/v1/agent-config/cto/projects/verdis
{
  "model": "gpt-4o",
  "temperature": 0.1,
  "max_tokens": 8000,
  "enabled": true
}
```

### Agent Context

When working on a managed project, agents receive project-specific context:

```bash
# Get Verdis-specific context
GET /api/v1/verdis-project/agent-context
```

This returns the full Verdis ecosystem knowledge (consensus, pallets, supply, validators, eco features, tokenomics, review guidelines) that gets injected into agent prompts.

## Task Types

The workflow engine routes tasks by type:

| Task Type | Default Agent | Description |
|----------|---------------|-------------|
| `architecture_review` | CTO | Review system architecture |
| `system_design` | Architect | Design new components |
| `security_audit` | Security | Security vulnerability scan |
| `test_review` | QA | Review test coverage |
| `test_generation` | Test Generator | Generate test suites |
| `ci_heal` | CI Healer | Diagnose and fix CI failures |
| `task_decomposition` | Planner | Break down features |
| `code_review` | Reviewer | Review implementation |
| `documentation` | Documentation | Generate docs |
| `pattern_detection` | Memory | Detect patterns from runs |
| `lesson_extraction` | Memory | Extract lessons from failures |

## Pipeline Integration

Agents are invoked at each stage of the 10-stage pipeline:

1. **PRD Analysis** → CTO Agent
2. **Architecture** → Architect Agent
3. **Decomposition** → Planner Agent
4. **Implementation** → (manual or external)
5. **QA** → QA Agent
6. **Security** → Security Agent
7. **Performance** → CTO Agent
8. **Documentation** → Documentation Agent
9. **Review** → Reviewer Agent
10. **Release** → (manual or automated)

## LLM Configuration

```python
# Default LLM settings
MODEL = "gpt-4o"
TEMPERATURE = 0.3      # Architecture/review
MAX_TOKENS = 4000      # Consultation
                     # 8000 for review, 6000 for audit
```

## Distributed Execution

EvolvixOS uses a ThreadPoolExecutor for parallel agent execution:

```bash
# Check executor status
GET /api/v1/ai/executor/status
```

Features:
- Thread-safe task dispatch
- Batch execution
- Progress tracking
- Result aggregation
