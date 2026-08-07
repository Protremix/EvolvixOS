# Pipeline Guide

The EvolvixOS Feature Delivery Pipeline is a 10-stage autonomous workflow that takes a feature from concept to release.

## Pipeline Stages

```
PRD → Architecture → Decomposition → Implementation → QA → Security → Performance → Documentation → Review → Release
```

### Stage Details

| Stage | Agent | Input | Output |
|-------|-------|-------|--------|
| 1. PRD | CTO | Feature description | Requirements analysis |
| 2. Architecture | Architect | Requirements | System design, API contracts |
| 3. Decomposition | Planner | Architecture | Task list with dependencies |
| 4. Implementation | Manual/External | Task list | Code changes |
| 5. QA | QA Agent | Implementation | Test results, coverage |
| 6. Security | Security Agent | Implementation | Security assessment |
| 7. Performance | CTO | Implementation | Performance analysis |
| 8. Documentation | Documentation Agent | Implementation | API docs, guides |
| 9. Review | Reviewer Agent | All stages | Review findings |
| 10. Release | Manual/Automated | Review approval | Deployment |

## Creating a Pipeline Run

```bash
# Create a new pipeline
POST /api/v1/feature-pipeline/
{
  "title": "Implement token transfer",
  "description": "Add token transfer functionality to the wallet",
  "project_type": "blockchain",
  "priority": "high",
  "constraints": [
    "Must maintain 100B total supply",
    "Must pass all existing tests"
  ],
  "acceptance_criteria": [
    "Users can transfer tokens",
    "Transfers are atomic",
    "Events emitted on transfer"
  ]
}
```

## Using Templates

Pre-configured templates for common feature types:

| Template | Category | Stages Skipped | Complexity |
|----------|----------|----------------|------------|
| Bugfix | bugfix | Architecture | Low |
| New Feature | feature | None | Medium |
| Refactor | refactor | Architecture, Security | Medium |
| Security Patch | security | None (extra security) | High |
| Infrastructure | infra | QA, Documentation | High |
| API Endpoint | api | Architecture | Medium |
| DB Migration | db | Documentation | Medium |
| Hotfix | hotfix | Architecture, Decomposition, QA, Performance | Low |

```bash
# List templates
GET /api/v1/pipeline-templates/

# Apply template to pipeline
POST /api/v1/pipeline-templates/{template_id}/apply/{pipeline_id}
```

## Event Streaming

Pipeline events are streamed in real-time via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'stage_started') {
        console.log(`Stage ${data.stage} started`);
    }
};
```

Event types:
- `pipeline.started`
- `stage_started`
- `stage_passed`
- `stage_failed`
- `pipeline.completed`
- `pipeline.failed`
- `pipeline.cancelled`

## Analytics

```bash
# Pipeline summary
GET /api/v1/pipeline-analytics/summary

# Per-stage metrics
GET /api/v1/pipeline-analytics/stages

# Bottleneck detection
GET /api/v1/pipeline-analytics/bottlenecks

# 7-day trend
GET /api/v1/pipeline-analytics/trends
```

## Scheduling

```bash
# Create recurring pipeline
POST /api/v1/pipeline-scheduler/
{
  "pipeline_id": "...",
  "template_id": "...",
  "schedule_type": "weekly",
  "day_of_week": 1,  # Monday
  "hour": 9,
  "enabled": true
}
```

## Pipeline Comparison

Compare two pipeline runs side-by-side:

```bash
GET /api/v1/pipeline-comparison/{run_id_1}/{run_id_2}
```

Returns stage-by-stage diff with improvements and regressions.
