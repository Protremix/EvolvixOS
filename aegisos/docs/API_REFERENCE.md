# API Reference

Base URL: `http://localhost:8000/api/v1`

## Authentication

All endpoints (except `/auth/login`, `/auth/register`, `/health`) require a JWT token:

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login   -H "Content-Type: application/json"   -d '{"email":"admin@example.com","password":"password"}'

# Use token
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/users/me
```

## API Routers (30 total)

### Authentication (`/auth`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get JWT |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout |
| GET | `/auth/me` | Get current user |

### Users (`/users`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/` | List all users (admin) |
| GET | `/users/{id}` | Get user by ID |
| PUT | `/users/{id}` | Update user |

### Organizations (`/organizations`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/organizations/` | Create organization |
| GET | `/organizations/` | List organizations |
| GET | `/organizations/{id}` | Get organization |
| PUT | `/organizations/{id}` | Update organization |
| DELETE | `/organizations/{id}` | Delete organization |
| POST | `/organizations/{id}/members` | Add member |
| GET | `/organizations/{id}/members` | List members |
| DELETE | `/organizations/{id}/members/{user_id}` | Remove member |

### Projects (`/projects`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/projects/` | List projects |
| POST | `/projects/` | Create project |
| GET | `/projects/{id}` | Get project |
| PUT | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |

### Tasks (`/tasks`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/tasks/` | List tasks |
| POST | `/tasks/` | Create task |
| GET | `/tasks/{id}` | Get task |
| PUT | `/tasks/{id}` | Update task |
| DELETE | `/tasks/{id}` | Delete task |

### AI (`/ai`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/ai/agents` | List all AI agents |
| POST | `/ai/tasks` | Dispatch AI task |
| POST | `/ai/pipelines` | Start AI pipeline |
| POST | `/ai/dispatch` | Dispatch single task |
| POST | `/ai/dispatch/batch` | Batch dispatch |
| GET | `/ai/dispatch/{id}/result` | Get task result |
| GET | `/ai/executor/status` | Get executor status |

### Feature Pipeline (`/feature-pipeline`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/feature-pipeline/` | Create pipeline run |
| GET | `/feature-pipeline/` | List pipeline runs |
| GET | `/feature-pipeline/{id}` | Get pipeline run |
| POST | `/feature-pipeline/{id}/cancel` | Cancel pipeline |
| GET | `/feature-pipeline/{id}/events` | Get pipeline events |
| GET | `/feature-pipeline/events/recent` | Get recent events |

### Pipeline Templates (`/pipeline-templates`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/pipeline-templates/` | List templates |
| GET | `/pipeline-templates/{id}` | Get template |
| POST | `/pipeline-templates/` | Create custom template |
| GET | `/pipeline-templates/categories` | List categories |
| POST | `/pipeline-templates/{id}/apply/{pipeline_id}` | Apply template |

### Pipeline Analytics (`/pipeline-analytics`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/pipeline-analytics/summary` | Pipeline summary stats |
| GET | `/pipeline-analytics/stages` | Per-stage metrics |
| GET | `/pipeline-analytics/agents` | Per-agent metrics |
| GET | `/pipeline-analytics/throughput` | Daily throughput |
| GET | `/pipeline-analytics/bottlenecks` | Detect bottlenecks |
| GET | `/pipeline-analytics/trends` | 7-day trend analysis |

### Pipeline Scheduler (`/pipeline-scheduler`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/pipeline-scheduler/` | Create schedule |
| GET | `/pipeline-scheduler/` | List schedules |
| PUT | `/pipeline-scheduler/{id}` | Update schedule |
| DELETE | `/pipeline-scheduler/{id}` | Delete schedule |
| POST | `/pipeline-scheduler/{id}/trigger` | Trigger scheduled run |

### Knowledge Base (`/knowledge`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/knowledge/` | List entries |
| POST | `/knowledge/` | Create entry |
| GET | `/knowledge/{id}` | Get entry |
| PUT | `/knowledge/{id}` | Update entry |
| DELETE | `/knowledge/{id}` | Delete entry |
| GET | `/knowledge/search` | Search entries |
| GET | `/knowledge/patterns` | Get detected patterns |
| GET | `/knowledge/stats` | Knowledge statistics |
| POST | `/knowledge/extract/{pipeline_id}` | Extract lessons from pipeline |

### Agent Configuration (`/agent-config`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/agent-config/` | List agent defaults |
| GET | `/agent-config/{agent_name}` | Get agent config |
| PUT | `/agent-config/{agent_name}` | Update global config |
| GET | `/agent-config/{agent_name}/projects` | Get per-project configs |
| PUT | `/agent-config/{agent_name}/projects/{project_id}` | Update project config |

### Dashboard (`/dashboard`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/` | System overview |
| GET | `/dashboard/performance` | Performance metrics |
| GET | `/dashboard/export/{type}` | Export data (JSON/CSV) |

### Webhooks (`/webhooks`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/webhooks/` | List webhooks |
| POST | `/webhooks/` | Create webhook |
| PUT | `/webhooks/{id}` | Update webhook |
| DELETE | `/webhooks/{id}` | Delete webhook |
| POST | `/webhooks/{id}/test` | Test webhook delivery |
| GET | `/webhooks/{id}/deliveries` | Get delivery history |
| POST | `/webhooks/{id}/activate` | Activate webhook |
| POST | `/webhooks/{id}/deactivate` | Deactivate webhook |
| GET | `/webhooks/stats` | Webhook statistics |

### System Settings (`/system-settings`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/system-settings/` | List all settings |
| GET | `/system-settings/{key}` | Get setting |
| PUT | `/system-settings/{key}` | Update setting |
| GET | `/system-settings/categories` | List categories |
| POST | `/system-settings/export` | Export settings |
| POST | `/system-settings/import` | Import settings |

### Activity Log (`/activity-log`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/activity-log/` | List activities |
| GET | `/activity-log/stats` | Activity statistics |
| GET | `/activity-log/search` | Search activities |

### Rate Limiter (`/rate-limiter`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/rate-limiter/stats` | Rate limit stats |
| PUT | `/rate-limiter/config` | Update config |

### Global Search (`/search`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/search/?q=...` | Search (query param) |
| POST | `/search/` | Search (body) |
| GET | `/search/types` | Get searchable types |

### System Health (`/health`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (no auth) |
| GET | `/health/detail` | Detailed health (auth) |

### Backup & Restore (`/backup`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/backup/` | Create backup |
| POST | `/backup/restore` | Restore from backup |
| GET | `/backup/history` | Backup history |
| GET | `/backup/stats` | Backup statistics |
| GET | `/backup/last` | Last backup info |

### Verdis Project (`/verdis-project`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/verdis-project/register` | Register Verdis as managed project |
| POST | `/verdis-project/health-check` | Run health check |
| GET | `/verdis-project/overview` | Get project overview |
| GET | `/verdis-project/health` | Latest health snapshot |
| GET | `/verdis-project/health/history` | Health history |
| GET | `/verdis-project/components` | Ecosystem components |
| PUT | `/verdis-project/components` | Update component status |
| GET | `/verdis-project/alerts` | Get alerts |
| POST | `/verdis-project/alerts/resolve` | Resolve alert |
| GET | `/verdis-project/agent-context` | AI agent context |
| GET | `/verdis-project/health-summary` | Human-readable summary |
| GET | `/verdis-project/pipeline-template` | Verdis audit template |
| GET | `/verdis-project/stats` | Monitoring stats |
| POST | `/verdis-project/monitoring/{bool}` | Toggle monitoring |

### Verdis Benchmarking (`/verdis-benchmark`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/verdis-benchmark/rpc-latency` | Run RPC latency benchmark |
| POST | `/verdis-benchmark/validator-score` | Run validator benchmark |
| POST | `/verdis-benchmark/block-time` | Run block time benchmark |
| POST | `/verdis-benchmark/all` | Run all benchmarks |
| GET | `/verdis-benchmark/results` | Get results history |

### Other Routers
- **GitHub** (`/github`) — Repository monitoring, issues, PRs, CI/CD
- **CodeOps** (`/code-ops`) — Test generation, CI healing
- **Dependency Graph** (`/dependency-graph`) — Import analysis, circular detection
- **AST Diff** (`/ast-diff`) — Semantic code diffing
- **Spec Compiler** (`/spec-compiler`) — OpenAPI/AsyncAPI to code generation
- **Project Adapters** (`/project-adapters`) — 7 built-in project type adapters
- **Pipeline Comparison** (`/pipeline-comparison`) — Side-by-side run comparison
- **Feedback** (`/feedback`) — Agent feedback and improvements
- **Config** (`/config`) — Per-project configuration
- **Events** (`/events`) — System event log
- **WebSocket** (`/ws`) — Real-time event streaming

## WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Event:', data.type, data);
};
```

Event types: `pipeline.started`, `stage_started`, `stage_passed`, `stage_failed`, `pipeline.completed`, `pipeline.failed`, `pipeline.cancelled`
