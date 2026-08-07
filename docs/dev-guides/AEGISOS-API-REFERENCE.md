# AegisOS API Reference

## Base URL
```
https://api.aegisos.local/v1  (local)
https://api.aegisos.io/v1      (production, when deployed)
```

## Authentication

All endpoints require JWT authentication:
```bash
curl -H "Authorization: Bearer $TOKEN" https://api.aegisos.io/v1/projects
```

### Login
```bash
POST /auth/login
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

## Core Endpoints (276 total)

### Projects
| Method | Path | Description |
|---|---|---|
| GET | /projects | List all projects |
| POST | /projects | Create a project |
| GET | /projects/{id} | Get project details |
| PUT | /projects/{id} | Update project |
| DELETE | /projects/{id} | Delete project |

### Multi-Project Management
| Method | Path | Description |
|---|---|---|
| GET | /multi-project/projects | List managed projects |
| POST | /multi-project/projects | Register a project |
| GET | /multi-project/projects/{id} | Get project |
| POST | /multi-project/projects/{id}/pause | Pause project |
| POST | /multi-project/projects/{id}/resume | Resume project |
| POST | /multi-project/projects/{id}/archive | Archive project |
| GET | /multi-project/stats | Multi-project stats |

### AI Agents
| Method | Path | Description |
|---|---|---|
| POST | /ai/agents/{name}/execute | Execute agent task |
| GET | /ai/agents/{name}/config | Get agent config |
| PUT | /ai/agents/{name}/config | Update agent config |
| GET | /ai/executor/status | Executor status |
| GET | /ai/health | AI system health |

### Agent Learning Loop
| Method | Path | Description |
|---|---|---|
| POST | /agent-learning/executions | Record execution |
| GET | /agent-learning/executions | Get execution history |
| POST | /agent-learning/analyze | Run learning analysis |
| GET | /agent-learning/insights | Get learning insights |
| GET | /agent-learning/prompt-optimizations | Get prompt suggestions |
| GET | /agent-learning/performance | All agent performance |
| GET | /agent-learning/performance/{name} | Agent performance |
| GET | /agent-learning/feedback/{name} | Get learning feedback |
| GET | /agent-learning/summary | Learning system summary |

### Feature Pipeline
| Method | Path | Description |
|---|---|---|
| POST | /pipelines | Create pipeline |
| GET | /pipelines | List pipelines |
| GET | /pipelines/{id} | Get pipeline |
| POST | /pipelines/{id}/execute | Execute pipeline |
| POST | /pipelines/{id}/cancel | Cancel pipeline |
| GET | /pipelines/{id}/events | Get pipeline events |
| GET | /pipelines/events/recent | Recent events (WebSocket) |

### Pipeline Templates
| Method | Path | Description |
|---|---|---|
| GET | /pipeline-templates | List templates |
| POST | /pipeline-templates | Create template |
| GET | /pipeline-templates/{id} | Get template |

### Pipeline Analytics
| Method | Path | Description |
|---|---|---|
| GET | /pipeline-analytics/summary | Pipeline summary |
| GET | /pipeline-analytics/stages | Stage metrics |
| GET | /pipeline-analytics/agents | Agent metrics |
| GET | /pipeline-analytics/throughput | Throughput data |
| GET | /pipeline-analytics/bottlenecks | Bottleneck detection |

### Knowledge Base
| Method | Path | Description |
|---|---|---|
| GET | /knowledge | Search knowledge |
| POST | /knowledge | Add entry |
| GET | /knowledge/patterns | Detected patterns |
| GET | /knowledge/stats | KB statistics |

### Agent Collaboration
| Method | Path | Description |
|---|---|---|
| GET | /collab-monitor/patterns | Collaboration patterns |
| POST | /collab-monitor/sessions | Create session |
| POST | /collab-monitor/sessions/{id}/simulate | Simulate session |
| POST | /collab-monitor/sessions/{id}/execute | Execute real LLM |

### Real-Time Monitor
| Method | Path | Description |
|---|---|---|
| GET | /collab-monitor/live | Live feed |
| GET | /collab-monitor/metrics | System metrics |
| GET | /collab-monitor/system-stats | System stats |

### Verdis Integration
| Method | Path | Description |
|---|---|---|
| GET | /verdis/health | Chain health |
| GET | /verdis/network | Network info |
| GET | /verdis/validators | Validator list |
| GET | /verdis/summary | Verdis summary |

### System
| Method | Path | Description |
|---|---|---|
| GET | /health | System health |
| GET | /health/detail | Detailed health |
| GET | /system/settings | System settings |
| POST | /system/backup/export | Export backup |
| POST | /system/backup/restore | Restore backup |

## WebSocket
```
ws://api.aegisos.io/ws
```
Events: pipeline.started, stage_started, stage_passed, stage_failed,
pipeline.completed, pipeline.failed, agent_started, agent_completed,
collaboration_started, collaboration_completed

## Error Codes
| Code | Meaning |
|---|---|
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 429 | Rate limited |
| 500 | Internal error |

---

*Last updated: August 5, 2026*

## API Usage Examples

### Create and Execute a Pipeline
```bash
# 1. Create a pipeline
curl -X POST https://api.aegisos.io/v1/pipelines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Verdis Security Audit",
    "template": "security_patch",
    "project_id": "verdis-project-id"
  }'

# 2. Execute it
curl -X POST https://api.aegisos.io/v1/pipelines/{pipeline_id}/execute \
  -H "Authorization: Bearer $TOKEN"

# 3. Check status
curl https://api.aegisos.io/v1/pipelines/{pipeline_id} \
  -H "Authorization: Bearer $TOKEN"

# 4. Stream events via WebSocket
wscat -c "wss://api.aegisos.io/ws" \
  -H "Authorization: Bearer $TOKEN"
```

### Record Agent Execution for Learning
```bash
# Record an agent's performance
curl -X POST https://api.aegisos.io/v1/agent-learning/executions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "cto_agent",
    "task_type": "architecture_review",
    "score": 8.5,
    "verdict": "GO",
    "tokens_used": 1200,
    "latency_ms": 3500,
    "findings_count": 2,
    "recommendations_count": 3
  }'

# Get learning feedback for next execution
curl https://api.aegisos.io/v1/agent-learning/feedback/cto_agent \
  -H "Authorization: Bearer $TOKEN"
```

### Register a Project
```bash
curl -X POST https://api.aegisos.io/v1/multi-project/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My DApp",
    "type": "blockchain",
    "description": "DeFi application on Verdis",
    "repository": "https://github.com/user/my-dapp",
    "domain": "mydapp.verdischain.com",
    "tags": ["defi", "verdis"]
  }'
```

### Search Knowledge Base
```bash
curl "https://api.aegisos.io/v1/knowledge?q=carbon+credit+security" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Verdis Chain Health
```bash
curl https://api.aegisos.io/v1/verdis/health \
  -H "Authorization: Bearer $TOKEN"
# Returns: { "status": "healthy", "peers": 14, "block": 1234567, ... }
```
