# Configuration Reference

## Environment Variables

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | EvolvixOS | Application name |
| `ENVIRONMENT` | development | `development`, `staging`, `production` |
| `DEBUG` | true | Enable debug mode |
| `API_V1_PREFIX` | /api/v1 | API route prefix |
| `LOG_LEVEL` | info | `debug`, `info`, `warn`, `error` |
| `METRICS_ENABLED` | true | Enable Prometheus metrics |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `POSTGRES_USER` | postgres | Database user |
| `POSTGRES_PASSWORD` | - | Database password (required in production) |
| `POSTGRES_DB` | evolvixos | Database name |

### Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection string |

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | - | JWT signing key (64-char hex in production) |
| `ALGORITHM` | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |

### Encryption

| Variable | Default | Description |
|----------|---------|-------------|
| `ENCRYPTION_KEY` | - | Fernet key for encrypting secrets at rest |

Generate with:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | localhost:3000,5173 | Allowed CORS origins |

### AI / OpenAI

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key |
| `OPENAI_MODEL` | gpt-4o | AI model to use |
| `OPENAI_TEMPERATURE` | 0.3 | LLM temperature |

### Plugins

| Variable | Default | Description |
|----------|---------|-------------|
| `PLUGINS_ENABLED` | true | Enable plugin system |
| `PLUGINS_DIR` | app/plugins | Plugin directory |

## System Settings (Runtime Configurable)

EvolvixOS has 30+ runtime-configurable settings accessible via the API and frontend:

### Feature Toggles
| Setting | Default | Description |
|---------|---------|-------------|
| `feature.pipelines.enabled` | true | Enable feature pipelines |
| `feature.knowledge_base.enabled` | true | Enable knowledge base |
| `feature.analytics.enabled` | true | Enable pipeline analytics |
| `feature.scheduler.enabled` | true | Enable pipeline scheduler |
| `feature.webhooks.enabled` | true | Enable webhook subscriptions |
| `feature.github.enabled` | true | Enable GitHub integration |
| `feature.verdis.enabled` | true | Enable Verdis blockchain integration |
| `feature.export.enabled` | true | Enable data export |
| `feature.activity_log.enabled` | true | Enable activity logging |
| `feature.ast_diff.enabled` | true | Enable AST-aware diff |
| `feature.spec_compiler.enabled` | true | Enable spec-driven compiler |
| `feature.dependency_graph.enabled` | true | Enable dependency graph |

### API Settings
| Setting | Default | Description |
|---------|---------|-------------|
| `api.rate_limit.per_minute` | 100 | Requests per minute per user |
| `api.rate_limit.per_hour` | 5000 | Requests per hour per user |
| `api.timeout_seconds` | 30 | API timeout |
| `api.max_request_size_mb` | 10 | Max request body size |
| `api.cors_origins` | * | CORS origins |

### AI Settings
| Setting | Default | Description |
|---------|---------|-------------|
| `ai.default_model` | gpt-4o | Default AI model |
| `ai.default_temperature` | 0.3 | Default temperature |
| `ai.max_tokens` | 4000 | Max tokens per call |
| `ai.timeout_seconds` | 120 | AI call timeout |
| `ai.retry_count` | 2 | Retry count for AI calls |

### Pipeline Settings
| Setting | Default | Description |
|---------|---------|-------------|
| `pipeline.max_concurrent` | 10 | Max concurrent pipelines |
| `pipeline.default_timeout` | 3600 | Default timeout (seconds) |
| `pipeline.retry_attempts` | 2 | Stage retry attempts |
| `pipeline.event_buffer_size` | 1000 | Event buffer size |

### Activity Log
| Setting | Default | Description |
|---------|---------|-------------|
| `activity_log.max_entries` | 10000 | Max log entries |
| `activity_log.retention_days` | 90 | Retention period |

### Knowledge Base
| Setting | Default | Description |
|---------|---------|-------------|
| `knowledge.max_entries` | 10000 | Max entries |
| `knowledge.auto_extract_patterns` | true | Auto-extract patterns from runs |
