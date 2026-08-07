# 10. DATABASE ARCHITECTURE

## 1. Executive Summary & Core Infrastructure
AegisOS is an enterprise-grade universal AI Engineering Operating System designed for multi-tenant, autonomous AI agent execution, collaborative code generation, security compliance, and long-term memory management. Primary transactional storage relies on **PostgreSQL 16+**, utilizing **pgvector** for high-performance vector embeddings, **Redis 7.x** for ephemeral cache and pub/sub signaling, and **PgBouncer** for high-throughput connection pooling.

### System Architecture Diagram
```
+-----------------------------------------------------------------------------------+
|                                  AegisOS Services                                 |
|  +------------------+  +-------------------+  +-----------------+  +------------+ |
|  |  Agent Execution |  | Orchestration Engine|  | Plugin Runtime  |  | API Gateway| |
|  +--------+---------+  +---------+---------+  +--------+--------+  +-----+------+ |
+-----------|----------------------|---------------------|-----------------|--------+
            |                      |                     |                 |
            +----------------------+----------+----------+-----------------+
                                              |
                                     +--------v--------+
                                     |   PgBouncer     | (Transaction Pooling)
                                     +--------+--------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
            +--------v--------+                               +--------v--------+
            |  Primary DB     | (Read/Write)                  | Read Replica DB | (Read Only)
            |  PostgreSQL 16  |======== Streaming Sync ======>| PostgreSQL 16   |
            |  + pgvector     |                               |  + pgvector     |
            +--------+--------+                               +-----------------+
                     |
            +--------v--------+
            | S3 / GCS WAL    | (WAL Archiving & PITR)
            | Object Storage  |
            +-----------------+
```

---

## 2. PostgreSQL Schema Design (23 Core Tables)

The database schema enforces strict relational integrity, UUIDv7 primary keys for time-ordered uniqueness, tenant isolation, fine-grained audit logging, and JSONB document structures for extensible configuration storage.

### 2.1 Table Specifications & DDL Statements

#### 1. `users`
Stores system users, developers, administrators, and automated system identity accounts.
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    role VARCHAR(50) NOT NULL DEFAULT 'developer' CHECK (role IN ('admin', 'developer', 'auditor', 'system_agent', 'viewer')),
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'pending_activation')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role_status ON users(role, status);
CREATE INDEX idx_users_metadata_gin ON users USING gin(metadata);
```

#### 2. `projects`
Represents software projects, repositories, or engineering workspaces managed by AegisOS.
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    repository_url VARCHAR(1024),
    default_branch VARCHAR(100) NOT NULL DEFAULT 'main',
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_slug ON projects(slug);
CREATE INDEX idx_projects_archived ON projects(is_archived) WHERE is_archived = FALSE;
```

#### 3. `tasks`
Work items, tickets, feature requests, or bug reports assigned to AI agents or human developers.
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(512) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'backlog' CHECK (status IN ('backlog', 'todo', 'in_progress', 'in_review', 'blocked', 'completed', 'cancelled')),
    priority VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    assignee_id UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_agent_id UUID, -- Foreign key added after agents table
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    labels TEXT[] NOT NULL DEFAULT '{}',
    due_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_status_priority ON tasks(status, priority);
CREATE INDEX idx_tasks_assignee ON tasks(assignee_id);
CREATE INDEX idx_tasks_labels_gin ON tasks USING gin(labels);
```

#### 4. `agents`
Catalog of AI agent definitions, persona profiles, model capabilities, and tool permissions.
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE, -- NULL for global system agents
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) NOT NULL, -- e.g., 'code_architect', 'security_auditor', 'test_generator'
    system_prompt TEXT NOT NULL,
    model_provider VARCHAR(50) NOT NULL DEFAULT 'anthropic',
    model_name VARCHAR(100) NOT NULL DEFAULT 'claude-3-5-sonnet',
    temperature NUMERIC(3, 2) NOT NULL DEFAULT 0.20 CHECK (temperature >= 0.0 AND temperature <= 2.0),
    max_tokens INT NOT NULL DEFAULT 8192,
    enabled_tools TEXT[] NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agents_project ON agents(project_id);
CREATE INDEX idx_agents_type ON agents(agent_type);
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_assigned_agent FOREIGN KEY (assigned_agent_id) REFERENCES agents(id) ON DELETE SET NULL;
```

#### 5. `agent_runs`
Execution logs and lifecycle state for each discrete agent execution session.
```sql
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    triggered_by UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'awaiting_approval', 'completed', 'failed', 'cancelled')),
    input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_payload JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    token_usage JSONB NOT NULL DEFAULT '{"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}'::jsonb,
    cost_usd NUMERIC(10, 6) NOT NULL DEFAULT 0.000000,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Partition template setup
CREATE TABLE agent_runs_2026_q3 PARTITION OF agent_runs
    FOR VALUES FROM ('2026-07-01 00:00:00+00') TO ('2026-10-01 00:00:00+00');

CREATE INDEX idx_agent_runs_agent ON agent_runs(agent_id);
CREATE INDEX idx_agent_runs_task ON agent_runs(task_id);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);
```

#### 6. `decisions`
Explicit architectural, code generation, or execution decisions made by agents or human review.
```sql
CREATE TABLE decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    decision_type VARCHAR(100) NOT NULL, -- e.g., 'architecture_change', 'dependency_addition', 'security_override'
    title VARCHAR(512) NOT NULL,
    rationale TEXT NOT NULL,
    alternatives_considered JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed', 'approved', 'rejected', 'superseded')),
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_decisions_project ON decisions(project_id);
CREATE INDEX idx_decisions_agent_run ON decisions(agent_run_id);
CREATE INDEX idx_decisions_status ON decisions(status);
```

#### 7. `code_reviews`
Automated and agent-assisted code review findings, line comments, and pull request suggestions.
```sql
CREATE TABLE code_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    commit_sha VARCHAR(40) NOT NULL,
    pull_request_number INT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'passed', 'changes_requested', 'failed')),
    summary TEXT,
    diff_hunk TEXT,
    findings JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of line-level comments and severities
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_code_reviews_project_pr ON code_reviews(project_id, pull_request_number);
CREATE INDEX idx_code_reviews_sha ON code_reviews(commit_sha);
```

#### 8. `security_reviews`
SAST, DAST, dependency scan, and agentic vulnerability analysis results.
```sql
CREATE TABLE security_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    scan_type VARCHAR(50) NOT NULL CHECK (scan_type IN ('sast', 'dast', 'dependency', 'secret', 'agentic_threat')),
    status VARCHAR(50) NOT NULL DEFAULT 'passed' CHECK (status IN ('running', 'passed', 'vulnerabilities_found', 'error')),
    critical_count INT NOT NULL DEFAULT 0,
    high_count INT NOT NULL DEFAULT 0,
    medium_count INT NOT NULL DEFAULT 0,
    low_count INT NOT NULL DEFAULT 0,
    vulnerabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_security_reviews_project ON security_reviews(project_id);
CREATE INDEX idx_security_reviews_counts ON security_reviews(critical_count, high_count) WHERE critical_count > 0 OR high_count > 0;
```

#### 9. `deployments`
Deployment executions across development, staging, preview, and production environments.
```sql
CREATE TABLE deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    environment VARCHAR(50) NOT NULL CHECK (environment IN ('development', 'staging', 'preview', 'production')),
    commit_sha VARCHAR(40) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'building', 'deploying', 'success', 'failed', 'rolled_back')),
    triggered_by UUID REFERENCES users(id) ON DELETE SET NULL,
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    target_url VARCHAR(1024),
    logs_url TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_deployments_project_env ON deployments(project_id, environment);
CREATE INDEX idx_deployments_status ON deployments(status);
```

#### 10. `releases`
Versioned release milestones grouping deployments, changelogs, and approved decisions.
```sql
CREATE TABLE releases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version_tag VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    changelog TEXT,
    released_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_project_release_tag UNIQUE(project_id, version_tag)
);

CREATE INDEX idx_releases_project ON releases(project_id);
```

#### 11. `agent_memory`
Agent-specific episodic, semantic, and procedural long-term memory utilizing **pgvector**.
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    memory_type VARCHAR(50) NOT NULL CHECK (memory_type IN ('episodic', 'semantic', 'procedural')),
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL, -- OpenAI / Anthropic default vector dimensions
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    relevance_score NUMERIC(5, 4) DEFAULT 1.0000,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_memory_agent ON agent_memory(agent_id, memory_type);
-- HNSW Vector Index for Cosine Similarity Search
CREATE INDEX idx_agent_memory_vector ON agent_memory USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

#### 12. `project_memory`
Shared workspace memory across all agents operating within a specific project.
```sql
CREATE TABLE project_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_project_memory_key UNIQUE(project_id, key)
);

CREATE INDEX idx_project_memory_project ON project_memory(project_id);
CREATE INDEX idx_project_memory_vector ON project_memory USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

#### 13. `global_memory`
Platform-wide shared knowledge, best practices, framework patterns, and universal agent memories.
```sql
CREATE TABLE global_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(100) NOT NULL, -- e.g., 'security_pattern', 'react_best_practices', 'python_optimizations'
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_global_memory_cat ON global_memory(category);
CREATE INDEX idx_global_memory_vector ON global_memory USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

#### 14. `events`
Partitioned immutable log of all event bus events for auditing and historical replay.
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(255) NOT NULL,
    target VARCHAR(255) NOT NULL DEFAULT '*',
    payload JSONB NOT NULL,
    metadata JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
) PARTITION BY RANGE (timestamp);

-- Initial quarterly partition
CREATE TABLE events_2026_q3 PARTITION OF events
    FOR VALUES FROM ('2026-07-01 00:00:00+00') TO ('2026-10-01 00:00:00+00');

CREATE INDEX idx_events_type_timestamp ON events(event_type, timestamp DESC);
CREATE INDEX idx_events_payload_gin ON events USING gin(payload);
CREATE INDEX idx_events_metadata_gin ON events USING gin(metadata);
```

#### 15. `audit_logs`
Compliance, security, and administrative action audit trails.
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL, -- e.g., 'user.login', 'api_key.create', 'plugin.install'
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

CREATE TABLE audit_logs_2026 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
```

#### 16. `api_keys`
API tokens for CLI, external automation, and third-party platform integrations.
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(10) NOT NULL, -- e.g., 'aegis_live_'
    scopes TEXT[] NOT NULL DEFAULT '{"read", "write"}',
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);
```

#### 17. `sessions`
Web application and gateway user session management.
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    ip_address INET,
    user_agent TEXT,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_token ON sessions(token_hash) WHERE is_revoked = FALSE;
CREATE INDEX idx_sessions_user ON sessions(user_id);
```

#### 18. `plugins`
Installed plugin registry for system expansion.
```sql
CREATE TABLE plugins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_identifier VARCHAR(255) NOT NULL UNIQUE, -- e.g., 'aegis-official-github'
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    plugin_type VARCHAR(50) NOT NULL CHECK (plugin_type IN ('agent', 'tool', 'integration', 'ui')),
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    manifest JSONB NOT NULL,
    installed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_plugins_type ON plugins(plugin_type);
CREATE INDEX idx_plugins_enabled ON plugins(is_enabled);
```

#### 19. `plugin_configs`
Per-project or global configuration parameters for active plugins.
```sql
CREATE TABLE plugin_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE, -- NULL for global config
    config_data JSONB NOT NULL DEFAULT '{}'::jsonb, -- Sensitive keys stored encrypted
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_plugin_project_config UNIQUE(plugin_id, project_id)
);

CREATE INDEX idx_plugin_configs_plugin ON plugin_configs(plugin_id);
CREATE INDEX idx_plugin_configs_project ON plugin_configs(project_id);
```

#### 20. `marketplace_items`
Catalog of discoverable plugins, extensions, agents, and toolpacks from the AegisOS ecosystem.
```sql
CREATE TABLE marketplace_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    latest_version VARCHAR(50) NOT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    download_count INT NOT NULL DEFAULT 0,
    rating NUMERIC(3, 2) DEFAULT 0.00,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_marketplace_cat_rating ON marketplace_items(category, rating DESC);
CREATE INDEX idx_marketplace_verified ON marketplace_items(is_verified);
```

#### 21. `comments`
Threaded discussion comments on tasks, decisions, code reviews, and agent runs.
```sql
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_type VARCHAR(50) NOT NULL CHECK (target_type IN ('task', 'decision', 'code_review', 'security_review')),
    target_id UUID NOT NULL,
    author_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    author_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    parent_comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_comment_author CHECK (
        (author_user_id IS NOT NULL AND author_agent_id IS NULL) OR
        (author_user_id IS NULL AND author_agent_id IS NOT NULL)
    )
);

CREATE INDEX idx_comments_target ON comments(target_type, target_id);
```

#### 22. `attachments`
Uploaded files, logs, artifacts, and diff patches linked to platform entities.
```sql
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    storage_path VARCHAR(1024) NOT NULL, -- S3 key URI
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_attachments_project ON attachments(project_id);
```

#### 23. `notifications`
Real-time and persistent notification delivery queue for developers and admins.
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL, -- e.g., 'agent_approval_required', 'task_assigned', 'security_alert'
    link_url VARCHAR(1024),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read, created_at DESC);
```

---

## 3. Migration Strategy
AegisOS employs **versioned schema migrations** using `golang-migrate` (or SQLx/Flyway equivalent), mandating backward-compatible forward migrations (`V<version>__<description>.up.sql`) alongside explicit rollback scripts (`V<version>__<description>.down.sql`).

### 3.1 Migration Rules & Guidelines
1. **Never Drop Columns/Tables directly**: Follow the **Expand-Contract Pattern**:
   - *Phase 1 (Expand)*: Add new columns as nullable or with defaults. Deploy code that writes to both old and new columns.
   - *Phase 2 (Migrate)*: Backfill historical data via asynchronous batch scripts.
   - *Phase 3 (Contract)*: Remove legacy code paths, mark old columns deprecated, and drop them in a subsequent release window.
2. **Non-blocking Index Creation**: Use `CREATE INDEX CONCURRENTLY` for all production migrations to prevent exclusive table locks (`ACCESS EXCLUSIVE`) during schema updates.
3. **Transactional Migrations**: Every migration script executes inside an explicit transaction block (`BEGIN ... COMMIT`) except where `CONCURRENTLY` index creation is required.

---

## 4. Backup & Recovery Strategy
AegisOS ensures 99.99% data durability using physical streaming backups, continuous Write-Ahead Log (WAL) archiving, and automated logical snapshots.

```
+------------------+         +---------------------+         +----------------------+
| Primary DB Node  |=======> | WAL Archive (wal-g) |=======> | AWS S3 / Glacier     |
| PostgreSQL 16    |         | Streaming WAL Logs  |         | Encrypted Immutable  |
+--------+---------+         +---------------------+         +----------------------+
         |
         | Daily Base Snapshot
         v
+------------------+
| Base Backup      |
| Full Snapshot    |
+------------------+
```

### 4.1 Backup Specifications
- **Logical Backup (`pg_dump`)**: Nightly logical backups for emergency schema extraction and developer seed generation.
- **Physical Backup & WAL Archiving (`wal-g` / `pg_backrest`)**:
  - Full Base Backup taken every 24 hours.
  - WAL segments archived continuously to encrypted Object Storage (AWS S3 / GCS) every 60 seconds.
- **Point-In-Time Recovery (PITR)**: Enables recovery to any exact millisecond within a 35-day retention window.
- **Service Level Objectives**:
  - **RPO (Recovery Point Objective)**: < 1 minute (WAL loss exposure).
  - **RTO (Recovery Time Objective)**: < 15 minutes for primary node failover; < 2 hours for full disaster recovery restore from base snapshot + WAL replay.

---

## 5. Read Replicas & Scaling Strategy
To handle heavy vector memory searches and query-heavy dashboard reads, AegisOS splits read and write workloads.

### 5.1 Replica Configuration & Sizing
- **Replication Type**: Asynchronous Physical Streaming Replication with hot standby replicas.
- **Scaling Thresholds**:
  - Add Read Replica when Primary CPU usage exceeds **65% average over 15 minutes**.
  - Add Read Replica when Primary Read IOPS exceed **70% of storage baseline**.
  - Split Read traffic when Read-to-Write ratio exceeds **4:1**.
- **Lag-Aware Routing**:
  - Replicas report `pg_wal_lsn_diff()`.
  - Application query routers (ORMs / PgBouncer) divert read traffic back to Primary if replica replication lag exceeds **5 seconds** or **64 MB**.

---

## 6. Connection Pooling Architecture (PgBouncer)
Direct connections to PostgreSQL incur heavy memory overhead (~10MB per backend process). AegisOS utilizes **PgBouncer** sitting in front of Primary and Replica instances.

```
[ Application Workers ] (1,000+ Concurrent Client Conns)
         |
         v
[ PgBouncer (Transaction Pooling) ]
         |
         | Sized DB Pool (50-100 Active Conns)
         v
[ PostgreSQL Primary Engine ]
```

### 6.1 PgBouncer Sizing & Configuration
- **Pooling Mode**: **Transaction Mode** (`pool_mode = transaction`). Connections are returned to the pool immediately upon transaction completion.
- **Connection Sizing Formula**:
  $$	ext{Max DB Connections} = (	ext{CPU Cores} 	imes 2) + 	ext{Effective Spindle Count}$$
  *For a 16-vCPU database instance*: Pool size = $(16 	imes 2) + 16 = 48$ active connections.
- **Prepared Statements Setup**: Because Transaction Mode breaks standard client-side prepared statements, PgBouncer is configured with `protocol_prepared_statements = true` or `prep_stmt_cleanup = true` (PgBouncer 1.21+).

---

## 7. Query Optimization & Indexing Guidelines

### 7.1 Vector Indexing Optimization
- **HNSW Index Parameters**:
  - `m = 16` (Number of bidirectional links per vector node).
  - `ef_construction = 64` (Size of the dynamic candidate list for building index).
  - Cosine Distance (`vector_cosine_ops`) used for all semantic embeddings.

### 7.2 Declarative Table Partitioning
- High-volume, time-series tables (`events`, `audit_logs`, `agent_runs`) are partitioned using `RANGE (created_at)` / `RANGE (timestamp)` quarterly.
- Partition pruning enabled (`enable_partition_pruning = on`) to eliminate non-relevant partitions during execution plans.

---

## 8. Data Retention Policies & Archiving

| Table | Live Retention Period | Archive Strategy | Dropping Method |
| :--- | :--- | :--- | :--- |
| `events` | 90 Days | Offloaded to S3 Parquet via AWS Athena / DuckDB | `DROP TABLE events_2026_q1;` |
| `audit_logs` | 7 Years (Regulatory) | Cold Glacier Lock Object Storage | Automated partition lifecycle |
| `agent_runs` | 1 Year | Compressed Parquet in Cold Storage | Quarterly partition rotation |
| `sessions` | 30 Days | Purged automatically via cron | `DELETE WHERE expires_at < NOW()` |
| `notifications`| 60 Days (Read) | Deleted | `DELETE WHERE is_read = TRUE AND created_at < NOW() - INTERVAL '60 days'` |

---

# 12. EVENT BUS ARCHITECTURE

## 1. Executive Summary & Core Philosophy
The Event Bus forms the asynchronous nervous system of AegisOS, decoupling AI agent runtimes, background task orchestrators, code synthesis engines, security scanners, webhook bridges, and real-time user interfaces. As an AI Engineering Operating System, AegisOS must handle thousands of concurrent agent steps, continuous code generation events, high-frequency token usage tracking, and multi-step human-in-the-loop approval requests without sacrificing system responsiveness or losing critical state telemetry.

```
+-----------------------------------------------------------------------------------+
|                                  EVENT PRODUCERS                                  |
|  +--------------------+   +---------------------+   +--------------------------+  |
|  | Agent Execution    |   | Webhook Receivers   |   | UI Action Gateway        |  |
|  +---------+----------+   +----------+----------+   +------------+-------------+  |
+------------|-------------------------|---------------------------|----------------+
             |                         |                           |
             v                         v                           v
+-----------------------------------------------------------------------------------+
|                            EVENT BUS CORE ROUTER                                  |
|  +-----------------------------------------------------------------------------+  |
|  | Standard Event Envelope Validation (JSON Schema Registry)                   |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        |                                          |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | Message Broker Tier                                                         |  |
|  | - MVP: Redis 7.x Streams & Pub/Sub                                           |  |
|  | - Enterprise Scale: NATS JetStream / Apache Kafka                           |  |
|  +-------------------+-------------------------------------+------------------+  |
+----------------------|--------------------------------------|---------------------+
                       |                                      |
                       v                                      v
+------------------------------------------+   +------------------------------------+
|            EVENT CONSUMERS               |   |            EVENT STORE             |
|  +------------------------------------+  |   |  +------------------------------+  |
|  | Agent Task Orchestrator            |  |   |  | PostgreSQL Partitioned Log   |  |
|  | Security Scanner Pipeline          |  |   |  | S3 Long-term Event Archive    |  |
|  | Webhook Broadcaster / Websockets    |  |   |  | Deterministic Replay Engine   |  |
|  +------------------------------------+  |   |  +------------------------------+  |
+------------------------------------------+   +------------------------------------+
```

---

## 2. Technology Selection & Architectural Justification

### 2.1 Architectural Evaluation
When selecting an event bus broker for an AI Operating System, four distinct message queue technology models were evaluated:
1. **In-Memory Pub/Sub + Streams (Redis 7.x)**
2. **Cloud-Native Subject Broker (NATS JetStream)**
3. **Distributed Immutable Commit Log (Apache Kafka)**
4. **Traditional AMQP Message Broker (RabbitMQ)**

#### Detailed Technology Comparison Matrix

| Architectural Dimension | Redis 7.x Streams / Pub/Sub (MVP) | NATS JetStream (Scale Target) | Apache Kafka (Enterprise Scale) | RabbitMQ (AMQP 0-9-1) |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Paradigm** | In-memory log + transient channels | Lightweight distributed streams & subjects | Distributed partitioned commit log | Smart broker / dumb consumer queues |
| **Max Throughput** | ~100,000 msgs/sec per node | > 1,000,000 msgs/sec per node | ~500,000 msgs/sec per partition | ~50,000 msgs/sec per queue |
| **End-to-End Latency** | Sub-millisecond (<0.5ms) | Sub-millisecond (<0.8ms) | Low (2ms – 10ms) | Low (1ms – 5ms) |
| **Stream Persistence** | Append-Only File (AOF) + RDB | Disk & Memory persistent streams | Native disk segment log | Erlang ETS / Mnesia disk queues |
| **Consumer Groups** | Supported via XGROUP | Built-in push/pull durable consumers | Consumer groups with partition rebalancing | Queue worker consumers |
| **Subject Wildcards** | Limited in Streams; full in Pub/Sub | Universal native hierarchy (`*`, `>`) | Topic regex matching only | Topic exchange routing keys (`*`, `#`) |
| **Cluster Complexity** | Minimal (Redis Sentinel / Cluster) | Single-binary, Raft consensus | High (Requires KRaft / Zookeeper) | Medium (Erlang cluster Mnesia) |
| **Footprint / Memory** | Very Low (~30MB base) | Micro (~20MB binary, low RAM) | Heavy (JVM, multi-GB heap) | Medium (~200MB Erlang BEAM) |
| **Verdict** | **Selected for MVP** | **Selected for Enterprise Production**| **Optional for ultra-large tenants**| **Rejected** |

### 2.2 Justification & Multi-Phase Progression Path
- **Phase 1: MVP (Redis 7.x Streams & Pub/Sub)**
  - *Rationale*: During the initial MVP phase, minimizing infrastructure operational overhead is critical. AegisOS already deploys Redis 7.x for primary caching and rate limiting. Redis Streams provides ordered append logs, consumer group acknowledgement mechanics (`XREADGROUP`, `XACK`), and historical sequence IDs (`XADD`). Redis Pub/Sub concurrently delivers sub-millisecond ephemeral updates to the WebSockets gateway for real-time frontend terminal updates.
- **Phase 2: Enterprise Scale Transition (NATS JetStream)**
  - *Rationale*: As concurrent agent executions scale beyond 10,000 active execution pipelines, Redis memory constraints become a bottleneck for historical stream retention. NATS JetStream is chosen as the target scale broker due to its single-binary simplicity, native Raft-based distributed streaming consensus, zero-dependency clustering, subject hierarchy routing (`aegis.tenant.project.domain.action`), and built-in support for exact-once message deduplication windows.

---

## 3. Universal Event Envelope Specification

To guarantee strict contract compliance, interoperability, and automated validation across all microservices and third-party plugins, every event published on the AegisOS bus MUST conform to the standardized **JSON Event Envelope Specification**.

### 3.1 Envelope Schema Definition (`aegis.event.envelope.json`)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AegisOSEventEnvelope",
  "type": "object",
  "required": [
    "event_id",
    "type",
    "timestamp",
    "source",
    "target",
    "payload",
    "metadata"
  ],
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique UUIDv7 identifier containing embedded millisecond timestamp."
    },
    "type": {
      "type": "string",
      "pattern": "^[a-z0-9_]+(\.[a-z0-9_]+)+$",
      "description": "Dot-separated hierarchical event type (e.g., agent.started, code.generated)."
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO-8601 UTC timestamp of original event creation."
    },
    "source": {
      "type": "string",
      "description": "Fully qualified identifier of the producing service, agent, or plugin."
    },
    "target": {
      "type": "string",
      "default": "*",
      "description": "Target audience topic or broadcast wildcard (*)."
    },
    "payload": {
      "type": "object",
      "description": "Domain payload object conforming to the schema of the specific event type."
    },
    "metadata": {
      "type": "object",
      "required": ["correlation_id", "schema_version"],
      "properties": {
        "correlation_id": { "type": "string", "format": "uuid" },
        "trace_id": { "type": "string" },
        "span_id": { "type": "string" },
        "user_id": { "type": "string", "format": "uuid" },
        "tenant_id": { "type": "string", "format": "uuid" },
        "project_id": { "type": "string", "format": "uuid" },
        "schema_version": { "type": "string", "pattern": "^\d+\.\d+\.\d+$" }
      }
    }
  }
}
```

### 3.2 Concrete Event Payload Examples

#### Example A: `agent.started` Event
```json
{
  "event_id": "018f3d8a-1111-7123-89ab-123456789aaa",
  "type": "agent.started",
  "timestamp": "2026-08-05T08:52:01.100Z",
  "source": "aegis:service:orchestrator",
  "target": "aegis:project:prj_987654",
  "payload": {
    "agent_run_id": "11223344-5566-7788-9900-aabbccddeeff",
    "agent_id": "99887766-5544-3322-1100-ffaabbaacc00",
    "agent_name": "Security Auditor Agent",
    "agent_type": "security_auditor",
    "task_id": "88776655-4433-2211-0099-aabbccddeeff",
    "system_prompt_version": "v2.1.0",
    "model": "claude-3-5-sonnet"
  },
  "metadata": {
    "correlation_id": "33445566-7788-9900-aabb-ccddeeff1122",
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "user_id": "aabbccdd-1122-3344-5566-77889900aabb",
    "tenant_id": "00112233-4455-6677-8899-aabbccddeeff",
    "project_id": "prj_987654",
    "schema_version": "1.0.0"
  }
}
```

#### Example B: `security.vulnerability_found` Event
```json
{
  "event_id": "018f3d8a-2222-7123-89ab-123456789bbb",
  "type": "security.vulnerability_found",
  "timestamp": "2026-08-05T08:52:04.450Z",
  "source": "aegis:plugin:semgrep-scanner",
  "target": "aegis:project:prj_987654",
  "payload": {
    "review_id": "55667788-9900-1122-3344-aabbccddeeff",
    "cve_id": "CVE-2026-21432",
    "severity": "CRITICAL",
    "file_path": "src/api/auth_controller.py",
    "line_number": 84,
    "rule_id": "python-lang-sql-injection",
    "description": "Unsanitized user input formatted directly into raw SQL query execution string.",
    "remediation_suggestion": "Use parameterized queries or ORM statement abstraction."
  },
  "metadata": {
    "correlation_id": "33445566-7788-9900-aabb-ccddeeff1122",
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "user_id": "aabbccdd-1122-3344-5566-77889900aabb",
    "tenant_id": "00112233-4455-6677-8899-aabbccddeeff",
    "project_id": "prj_987654",
    "schema_version": "1.0.0"
  }
}
```

---

## 4. Comprehensive Event Catalog (27 Detailed Core Events)

The following matrix documents the complete catalog of 27 standard core events supported natively by the AegisOS kernel.

| # | Domain Category | Event Type Identifier | Primary Publisher Source | Subscriber Action & Trigger Conditions |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Agent** | `agent.started` | Orchestrator Engine | Initializes execution timer, updates UI status to running, locks task status. |
| 2 | **Agent** | `agent.completed` | Agent Execution Worker | Releases task locks, records token usage/cost, triggers downstream review steps. |
| 3 | **Agent** | `agent.failed` | Agent Execution Worker | Log stack trace, alerts team via notification bus, releases agent lock. |
| 4 | **Agent** | `agent.needs_approval` | Policy Gatekeeper | Suspends agent run, generates interactive approval ticket in Slack/UI. |
| 5 | **Task** | `task.created` | API Gateway / Plugin | Enqueues task into project backlog, triggers agent auto-assignment rules. |
| 6 | **Task** | `task.assigned` | Dispatcher Service | Binds task to human user or AI agent profile, triggers notification. |
| 7 | **Task** | `task.completed` | Agent / Developer | Verifies acceptance criteria, updates task workflow status to done. |
| 8 | **Task** | `task.failed` | Agent / Developer | Logs verification failure reason, re-enqueues task or marks blocked. |
| 9 | **Code** | `code.generated` | Code Generation Agent | Emits code patch diff, triggers automated static analysis and unit testing. |
| 10 | **Code** | `code.reviewed` | Reviewer Agent | Attaches inline diff comments, sets code review status flag. |
| 11 | **Code** | `code.approved` | Human / Policy Engine | Unblocks pull request merge gate, triggers automated staging deployment. |
| 12 | **Code** | `code.rejected` | Human / Reviewer Agent| Sends feedback diff back to Code Agent for automated iteration cycle. |
| 13 | **Test** | `test.run` | CI Test Runner | Provisions isolated test container sandbox, begins test execution. |
| 14 | **Test** | `test.passed` | CI Test Runner | Marks code review test check passed, emits quality milestone metrics. |
| 15 | **Test** | `test.failed` | CI Test Runner | Extracts stack trace diff, routes back to Agent for patch generation. |
| 16 | **Security** | `security.scan_started` | Security Scanner | Initiates SAST, DAST, dependency, and secret leak scanning routines. |
| 17 | **Security** | `security.scan_completed`| Security Scanner | Summarizes vulnerability findings and compliance score. |
| 18 | **Security** | `security.vulnerability_found` | Security Scanner | Evaluates severity; critical findings halt deployment pipeline immediately. |
| 19 | **Deployment** | `deployment.started` | Continuous Delivery Engine| Triggers container image build and environment cluster release sequence. |
| 20 | **Deployment** | `deployment.completed` | Deployment Agent | Conducts live health checks, routes traffic, updates release record. |
| 21 | **Deployment** | `deployment.failed` | Deployment Agent | Triggers automated rollback to last stable commit SHA. |
| 22 | **Project** | `project.created` | Project Management Engine| Allocates project vector namespace, initializes git repository hooks. |
| 23 | **Project** | `project.updated` | Project Management Engine| Updates project settings, team member roles, and repository mappings. |
| 24 | **Memory** | `memory.stored` | Vector Memory Subsystem | Generates vector embedding via OpenAI/Anthropic API, indexes into pgvector. |
| 25 | **Memory** | `memory.retrieved` | Vector Memory Subsystem | Queries semantic context, attaches retrieved facts to agent LLM prompt. |
| 26 | **User** | `user.action` | Frontend Gateway | Logs developer UI interactions for audit trail and context tracking. |
| 27 | **User** | `user.approval` | Web UI / Slack Plugin | Resumes suspended agent execution run with human approval signature. |

---

## 5. Routing Architecture & Filtering Mechanisms

AegisOS employs a multi-tiered routing topology combining **Topic-Based Subject Hierarchies** with **Content-Based Metadata Filtering**.

```
Event Published on Topic:
"aegis.tenant_45.project_101.security.vulnerability_found"
                         |
      +------------------+------------------+
      |                                     |
[ Subject Hierarchy Matching ]      [ Content Filter Gateway ]
Matching Wildcards:                 Filter Rule:
- aegis.tenant_45.>                 Check: payload.severity == "CRITICAL"
- aegis.*.*.security.*              Matched Action: Immediate SMS / PagerDuty Alert
```

### 5.1 Topic-Based Hierarchies
Subject names follow strict multi-tenant structural boundaries:
`aegis.<tenant_id>.<project_id>.<domain_category>.<action>`

*Routing Wildcard Semantics (NATS Compatible)*:
- `*` Matches a single token element in the hierarchy (e.g., `aegis.tenant_45.*.agent.started`).
- `>` Matches one or more remaining token elements (e.g., `aegis.tenant_45.project_101.>`).

### 5.2 Content-Based Metadata Filtering
Consumers can attach dynamic filter expressions evaluated at the Event Bus Router prior to delivery:
```cel
// Common Expression Language (CEL) Content Filter Rule
metadata.tenant_id == "00112233-4455-6677-8899-aabbccddeeff" && 
payload.severity IN ["CRITICAL", "HIGH"]
```

---

## 6. Event Store, Replay Engine & Time-Travel Debugging

### 6.1 Transactional Outbox & Event Store
To ensure zero event loss during host crashes, state updates and event records execute inside a single transactional database block using the **Transactional Outbox Pattern**:

```sql
BEGIN;

-- 1. Update Core Domain State
UPDATE tasks SET status = 'in_review' WHERE id = '88776655-4433-2211-0099-aabbccddeeff';

-- 2. Stage Event to Outbox Table
INSERT INTO events (event_id, event_type, source, target, payload, metadata, timestamp)
VALUES (
    '018f3d8a-3333-7123-89ab-123456789ccc',
    'task.completed',
    'aegis:service:task_manager',
    'aegis:project:prj_987654',
    '{"task_id": "88776655-4433-2211-0099-aabbccddeeff"}'::jsonb,
    '{"correlation_id": "33445566-7788-9900-aabb-ccddeeff1122", "schema_version": "1.0.0"}'::jsonb,
    NOW()
);

COMMIT;
```
An asynchronous CDC (Change Data Capture) or polling worker reads from `events` and pushes records to the active message broker (Redis/NATS).

### 6.2 Replay Engine for Non-Deterministic AI Debugging
AI agents are notoriously difficult to debug due to LLM response non-determinism. AegisOS solves this with the **Deterministic Replay Engine**:

```
+-----------------------------------------------------------------------------------+
|                            DETERMINISTIC REPLAY ENGINE                            |
|                                                                                   |
| 1. Query Event Store for agent_run_id between [T_start, T_end]                    |
| 2. Re-hydrate exact initial memory context & workspace snapshot                   |
| 3. Mock LLM completion endpoints using recorded original payloads                 |
| 4. Execute agent steps in isolated sandbox container                              |
| 5. Compare state transition diffs line-by-line                                    |
+-----------------------------------------------------------------------------------+
```

---

## 7. Dead Letter Queue (DLQ) & Resilience Management

### 7.1 Exponential Backoff Retry Policy
When a consumer worker fails to process an event (e.g., due to database timeout or external API rate limit), the event bus executes an automatic retry strategy:
$$T_{	ext{backoff}} = \min\left(T_{	ext{max}}, \; T_{	ext{base}} 	imes 2^{	ext{attempt}} + 	ext{jitter}ight)$$
- $T_{	ext{base}} = 100	ext{ ms}$, $T_{	ext{max}} = 30	ext{ seconds}$, $	ext{Max Attempts} = 3$.

### 7.2 DLQ Routing & Manual Remediation
If processing fails after 3 attempts, the consumer emits a `NACK` (Negative Acknowledgement) with terminal status. The broker moves the poison message to `aegis.dlq.<tenant_id>.<domain>`.

```
[ Primary Event Channel ] ===(3 Failed Retries)===> [ Dead Letter Queue (DLQ) ]
                                                            |
                                                            v
                                                  [ DLQ Inspection Dashboard ]
                                                            |
                                           +----------------+----------------+
                                           |                                 |
                                  [ Manual Payload Fix ]            [ Discard Poison ]
                                           |
                                           v
                                [ Re-drive / Re-queue ]
```

---

## 8. Delivery Guarantees & Application Idempotency

### 8.1 At-Least-Once Delivery
Network timeouts, node evictions, and container restarts make physical exactly-once network transmission impossible without catastrophic latency penalties. AegisOS enforces **At-Least-Once Delivery** at the messaging layer.

### 8.2 Consumer Idempotency Key Tracking
To guarantee idempotent processing, all consumers maintain a **Deduplication Key Store**:

```typescript
async function processEventWithIdempotency(event: AegisEvent, handler: Function): Promise<void> {
  const idempotencyKey = `idempotency:${event.metadata.tenant_id}:${event.event_id}`;
  
  // Atomically set key in Redis with 24-hour expiration if not exists
  const isNew = await redis.set(idempotencyKey, "processing", "NX", "EX", 86400);
  if (!isNew) {
    logger.info(`Duplicate event received [${event.event_id}]. Skipping processing.`);
    return;
  }
  
  try {
    await handler(event);
    await redis.set(idempotencyKey, "completed", "XX", "EX", 86400);
  } catch (error) {
    await redis.del(idempotencyKey); // Clear key on error to allow retry
    throw error;
  }
}
```

---

## 9. Schema Versioning & CQRS Pattern

### 9.1 Semantic Schema Evolution Rules
- **Patch Changes (1.0.1)**: Purely cosmetic or documentation edits. No runtime validation impact.
- **Minor Changes (1.1.0)**: Adding optional payload fields or default values. Fully backward compatible.
- **Major Changes (2.0.0)**: Breaking changes (field removal, structural rename).
  - *Dual-Publish Strategy*: The event producer MUST dual-publish both `v1.x` and `v2.x` envelopes simultaneously for a mandatory 30-day migration window until all consumer services upgrade.

### 9.2 Command Query Responsibility Segregation (CQRS)
In AegisOS, writes are handled via **Commands** (`ExecuteAgentTaskCommand`, `CreateCodeReviewCommand`) that execute state transitions, emitting immutable **Events**. Read models (such as agent execution progress bars, dashboard summaries, and semantic memory vectors) are asynchronously rendered into specialized Redis caches and pgvector indices.

---

# 11. PLUGIN ARCHITECTURE

## 1. Executive Summary & Core Philosophy
AegisOS is built from the ground up as a universal, highly customizable AI Engineering Operating System. To prevent vendor lock-in, enable bespoke enterprise workflows, and foster a thriving ecosystem of developer tools, AegisOS enforces a strict **Micro-Kernel Architecture**. Core kernel services (Database, Event Bus, Authentication Gateway, and LLM Router) remain lean, stable, and unburdened by domain-specific logic. All external SaaS connectors, specialized AI agent personas, custom developer tools, and web interface dashboards are implemented as **Plugins**.

```
+-----------------------------------------------------------------------------------+
|                                 AegisOS Core Kernel                               |
|  +--------------------+   +---------------------+   +--------------------------+  |
|  | Event Bus Core     |   | Memory (pgvector)   |   | Security & RBAC Gateway  |  |
|  +---------+----------+   +----------+----------+   +------------+-------------+  |
+------------|-------------------------|---------------------------|----------------+
             |                         |                           |
             |  Plugin Extension Hook APIs (gRPC / WASM / REST)    |
             v                         v                           v
+-----------------------------------------------------------------------------------+
|                                PLUGIN RUNTIME SANDBOX                             |
|  +-------------------+  +--------------------+  +------------------+  +---------+ |
|  | AI Agent Plugins  |  | Tool Plugins       |  | Integration Plugs|  | UI Plugs| |
|  | (Wasm Isolation)  |  | (gRPC Process)     |  | (Node.js Container) | (React) | |
|  +-------------------+  +--------------------+  +------------------+  +---------+ |
+-----------------------------------------------------------------------------------+
```

---

## 2. Plugin Types Taxonomy

AegisOS categorizes plugins into four distinct architectural types based on their execution context, API requirements, and user interaction surface:

### 2.1 AI Agent Plugins
AI Agent Plugins introduce custom agent personas, multi-step reasoning frameworks (e.g., ReAct, Plan-And-Solve, Reflexion, Tree-of-Thought), prompt chain definitions, and system persona constraints.
- *Primary Role*: Define how an agent perceives context, reasons through technical challenges, and invokes tool capabilities.
- *Example*: `SecurityAuditorAgent`, `DatabaseMigrationAgent`, `ReactComponentGenerator`.

### 2.2 Tool Plugins
Tool Plugins expose executable code functions directly to AI agent reasoning loops.
- *Primary Role*: Grant agents physical capabilities to interact with local filesystems, execute shell commands, run database queries, or query third-party APIs.
- *Example*: `BashSandboxTool`, `SemgrepScannerTool`, `PostgreSQLQueryRunner`, `DockerBuildTool`.

### 2.3 Integration Plugins
Integration Plugins handle bi-directional event synchronization and authentication mechanics between AegisOS and external enterprise SaaS platforms.
- *Primary Role*: Ingest external webhooks, map foreign payloads to AegisOS event bus formats, and trigger remote platform actions.
- *Example*: `GitHubIntegrationPlugin`, `SlackNotifierPlugin`, `JiraSyncPlugin`, `DatadogAlertPlugin`.

### 2.4 UI Plugins
UI Plugins extend the AegisOS frontend interface by injecting custom React components, widget panels, status dashboards, and interactive step-approval modals.
- *Primary Role*: Provide custom visual feedback and human-in-the-loop controls for complex domain workflows using Shadow DOM micro-frontend containers.
- *Example*: `VulnerabilityHeatmapWidget`, `AgentThoughtProcessVisualizer`, `PRReviewDiffViewer`.

---

## 3. Plugin API Surface & Software Development Kit (SDK)

Plugins interact with host system resources exclusively through the `@aegisos/plugin-sdk` (TypeScript) and `aegisos-plugin-sdk` (Python) libraries.

### 3.1 SDK Capabilities Summary
The SDK exposes structured namespaces for system access:
- `ctx.eventBus`: Publish and subscribe to AegisOS event bus topics.
- `ctx.memory`: Perform vector similarity search and store episodic/semantic embeddings.
- `ctx.tasks`: Create, update, assign, or query workspace tasks.
- `ctx.secrets`: Securely retrieve encrypted API keys and OAuth tokens.
- `ctx.logger`: Structured JSON logging with trace context correlation.

### 3.2 TypeScript SDK Interface Core Definition
```typescript
export interface PluginContext {
  readonly pluginId: string;
  readonly projectId?: string;
  readonly tenantId: string;
  readonly logger: PluginLogger;
  readonly eventBus: PluginEventBus;
  readonly memory: PluginMemoryStore;
  readonly secrets: PluginSecretManager;
  getConfig<T = Record<string, any>>(): Promise<T>;
}

export interface PluginEventBus {
  publish(eventType: string, payload: Record<string, any>): Promise<void>;
  subscribe(topicPattern: string, handler: (event: AegisEvent) => Promise<void>): Promise<SubscriptionHandle>;
}

export interface PluginMemoryStore {
  query(vector: number[], topK?: number): Promise<MemoryMatch[]>;
  store(content: string, metadata?: Record<string, any>): Promise<string>;
}
```

---

## 4. Comprehensive Plugin Manifest Format

Every AegisOS plugin MUST package a `plugin.json` (or `plugin.yaml`) manifest at its root directory. This manifest defines metadata, entrypoints, permissions, required configurations, and event hook bindings.

### 4.1 Manifest Specification Schema (`plugin.manifest.v1.json`)
```json
{
  "$schema": "https://aegisos.dev/schemas/plugin.manifest.v1.json",
  "id": "aegis-official-github",
  "name": "GitHub Integration Plugin",
  "version": "1.2.0",
  "description": "Bi-directional GitHub sync for webhooks, PR code reviews, and issue tracking.",
  "author": "AegisOS Core Team <support@aegisos.dev>",
  "homepage": "https://github.com/aegisos/plugin-github",
  "plugin_type": "integration",
  "entrypoint": "dist/index.js",
  "wasm_binary": "bin/plugin.wasm",
  "permissions": [
    "network:outbound",
    "filesystem:read",
    "filesystem:write",
    "event:subscribe",
    "event:publish",
    "secrets:read"
  ],
  "dependencies": {
    "aegis-core-sdk": ">=1.0.0"
  },
  "config_schema": {
    "type": "object",
    "required": ["github_app_id", "webhook_secret"],
    "properties": {
      "github_app_id": {
        "type": "string",
        "title": "GitHub App ID"
      },
      "webhook_secret": {
        "type": "string",
        "title": "Webhook Secret",
        "secret": true
      },
      "auto_review_prs": {
        "type": "boolean",
        "default": true
      }
    }
  },
  "hooks": [
    "on_task_created",
    "on_code_generated",
    "on_agent_approval_required"
  ]
}
```

---

## 5. Plugin Lifecycle Management & Updating Mechanisms

The `PluginManager` host service manages plugin instances through a deterministic finite state machine (FSM).

```
 +-------------+       +---------------+       +--------------+
 | Installed   | ====> | Configured    | ====> | Active       |
 +-------------+       +---------------+       +--------------+
        |                      ^                      |
        |                      |                      v
        |                      +------------------ + Disabled   |
        v                                          +--------------+
 +-------------+                                          |
 | Uninstalled | <========================================+
 +-------------+
```

### 5.1 Lifecycle Lifecycle Hooks
Plugins implement standard lifecycle hooks executed by the runtime during state transitions:
1. `onInstall(ctx)`: Initializes database schemas, registers default configuration parameters.
2. `onConfigure(config)`: Validates user-provided setup values against `config_schema`.
3. `onActivate(ctx)`: Connects event listeners, establishes outbound socket channels.
4. `onDeactivate(ctx)`: Gracefully drains active requests, closes socket connections.
5. `onUninstall(ctx)`: Cleans up ephemeral storage and revokes dynamic webhooks.
6. `onUpdate(oldVer, newVer)`: Executes schema or state migration scripts.

### 5.2 Dynamic Hot-Reloading & Zero-Downtime Updates
AegisOS supports hot-reloading for TypeScript/WASM plugins without restarting core kernel services:
- **Hot-Swapping**: The host spawns a secondary worker runtime running version $V_{new}$ alongside $V_{old}$.
- **Drain Phase**: $V_{old}$ stops accepting new event subscriptions while completing active in-flight requests.
- **Switch Phase**: Upon complete drain, $V_{old}$ is terminated and state context is atomically transferred to $V_{new}$.

---

## 6. Security Sandboxing & Permissions Model

To protect the host system and multi-tenant workspaces against malicious code execution, remote code exfiltration, or resource exhaustion, AegisOS implements **Dual-Layer Sandboxing** combined with **Capability-Based Fine-Grained Permissions**.

```
+-----------------------------------------------------------------------------------+
|                            HOST OPERATING SYSTEM & KERNEL                         |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Capability Enforcement Gateway (Validates Permissions Matrix)                |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        |                                          |
|            +---------------------------+---------------------------+              |
|            |                                                       |              |
|            v                                                       v              |
|  +----------------------------------+            +-----------------------------+  |
|  | WASM Sandbox (Wasmtime/Extism)     |            | gRPC Out-of-Process Sidecar |  |
|  | - Memory Bound: 256MB              |            | - Isolated Docker Container |  |
|  | - CPU Instruction Limit (Fuel)    |            | - Restricted Cgroups        |  |
|  | - Zero Direct I/O Access           |            | - Read-Only Root Filesystem |  |
|  +----------------------------------+            +-----------------------------+  |
+-----------------------------------------------------------------------------------+
```

### 6.1 Sandboxing Mechanisms
1. **WebAssembly (WASM) Isolation (Extism / Wasmtime)**: Lightweight tool plugins run inside WASM sandboxes. Hosts pre-allocate linear memory bounds (e.g., 256MB) and enforce execution limits via WASM CPU instruction fuel counters.
2. **Out-of-Process gRPC Sidecars**: Complex integration plugins execute in separate containerized sidecar processes, communicating exclusively over encrypted local UNIX domain sockets via gRPC.

### 6.2 Capabilities Matrix

| Permission Capability | Description / Scope | Security Risk Classification |
| :--- | :--- | :--- |
| `network:outbound` | Permits outbound HTTPS communication to external domains. | **High** |
| `filesystem:read` | Grants read access to project workspace files. | **Medium** |
| `filesystem:write` | Grants write and patch modification access to files. | **High** |
| `agent:spawn` | Authorizes the plugin to trigger sub-agent executions. | **High** |
| `memory:read` | Allows semantic search queries over vector memory. | **Medium** |
| `memory:write` | Allows inserting or updating vector embeddings. | **Medium** |
| `secrets:read` | Grants access to decrypted environment secrets. | **CRITICAL** |
| `ui:inject` | Permits injecting visual React components into web UI. | **Low** |

---

## 7. Configuration Storage, Discovery & Dependency Resolution

### 7.1 Configuration Storage & Encryption
Plugin configurations are stored in the `plugin_configs` database table. Any parameter marked with `"secret": true` in the `config_schema` is encrypted before persistence using **AES-256-GCM envelope encryption** backed by AWS KMS or HashiCorp Vault.

### 7.2 Discovery & Installation CLI
Engineers manage plugins via the AegisOS CLI:
```bash
# Search registry marketplace
aegis plugin search github

# Install verified plugin
aegis plugin install aegis-official-github --version 1.2.0

# Configure credentials
aegis plugin config set aegis-official-github github_app_id="123456"

# Activate plugin
aegis plugin enable aegis-official-github
```

### 7.3 Dependency Resolution & Conflict Management
When installing plugins, AegisOS constructs a **Directed Acyclic Graph (DAG)** to verify SemVer constraints and identify conflicts:
1. **Hook Collisions**: If two plugins attempt to claim exclusive priority hooks on the same event stream, the host enforces explicit priority weights (`priority: 100`).
2. **Port Allocation Collisions**: Sidecar plugins request dynamic port bindings assigned by the host port allocator gateway.
3. **Diamond Dependency Management**: When two active plugins require differing minor versions of a shared SDK dependency, the AegisOS module loader uses isolated dynamic import scopes (`vm.Module` or ES dynamic imports) to load both versions side-by-side without global namespace leakage.

---

## 8. Marketplace Integration & Distribution

The AegisOS Marketplace (`marketplace_items` catalog) provides a secure ecosystem for discovering, distributing, and licensing plugins.

```
[ Developer Author ] ===> [ CLI Publish ] ===> [ Automated SAST & Sandbox Scan ]
                                                             |
                                                     (Verification Passed)
                                                             v
[ End-User Deployment ] <=== [ Marketplace Catalog ] <=== [ Ed25519 Code Signing ]
```

### 8.1 Distribution Pipeline
1. **Automated Verification**: Submitted plugins undergo SAST scanning, dependency vulnerability audit, and sandbox execution checks.
2. **Code Signing**: Approved plugins are signed using Ed25519 private keys. The AegisOS runtime verifies signatures against official public keys prior to installation.
3. **Monetization & License Verification**: Enterprise plugins can enforce license checks via JWT entitlement signatures issued by the AegisOS Marketplace billing engine.

---

## 9. Comprehensive Concrete Plugin Examples (3 Full Implementations)

### 9.1 Example 1: GitHub Integration Plugin

#### Manifest File (`plugin.json`)
```json
{
  "id": "aegis-official-github",
  "name": "GitHub Integration Plugin",
  "version": "1.2.0",
  "plugin_type": "integration",
  "entrypoint": "dist/index.js",
  "permissions": [
    "network:outbound",
    "filesystem:read",
    "event:subscribe",
    "event:publish",
    "secrets:read"
  ],
  "config_schema": {
    "type": "object",
    "required": ["github_app_id", "webhook_secret"],
    "properties": {
      "github_app_id": { "type": "string" },
      "webhook_secret": { "type": "string", "secret": true },
      "auto_review_prs": { "type": "boolean", "default": true }
    }
  }
}
```

#### TypeScript Implementation (`src/index.ts`)
```typescript
import { PluginContext, AegisEvent } from '@aegisos/plugin-sdk';

export class GitHubIntegrationPlugin {
  async onActivate(ctx: PluginContext): Promise<void> {
    const config = await ctx.getConfig();
    ctx.logger.info(`Activating GitHub Plugin for App ID: ${config.github_app_id}`);

    // Subscribe to Event Bus code generation events
    await ctx.eventBus.subscribe('code.generated', async (event: AegisEvent) => {
      if (config.auto_review_prs) {
        await this.handleCodeGenerated(ctx, event);
      }
    });
  }

  async handleIncomingWebhook(ctx: PluginContext, headers: Record<string, string>, body: any): Promise<void> {
    const eventType = headers['x-github-event'];
    
    if (eventType === 'pull_request' && body.action === 'opened') {
      ctx.logger.info(`Processing new GitHub PR #${body.number}`);
      
      // Publish task.created event to AegisOS Event Bus
      await ctx.eventBus.publish('task.created', {
        title: `Review PR #${body.number}: ${body.pull_request.title}`,
        description: body.pull_request.body,
        metadata: {
          github_pr_id: body.pull_request.id,
          repo: body.repository.full_name,
          commit_sha: body.pull_request.head.sha
        }
      });
    }
  }

  private async handleCodeGenerated(ctx: PluginContext, event: AegisEvent): Promise<void> {
    ctx.logger.info(`Posting automated review comment for task: ${event.payload.task_id}`);
    // Interacts with GitHub REST/GraphQL API to post code review inline comments
  }
}
```

---

### 9.2 Example 2: Slack Notifications Plugin

#### Manifest File (`plugin.yaml`)
```yaml
id: "aegis-official-slack"
name: "Slack Notifications Plugin"
version: "2.0.0"
plugin_type: "integration"
entrypoint: "src/slack_plugin.py"
permissions:
  - "network:outbound"
  - "event:subscribe"
  - "secrets:read"
config_schema:
  type: "object"
  required: ["slack_webhook_url"]
  properties:
    slack_webhook_url:
      type: "string"
      secret: true
```

#### Python Implementation (`src/slack_plugin.py`)
```python
import json
import urllib.request
from aegisos_sdk import PluginBase, PluginContext, AegisEvent

class SlackNotificationPlugin(PluginBase):
    def on_activate(self, ctx: PluginContext):
        self.webhook_url = ctx.secrets.get("slack_webhook_url")
        ctx.logger.info("Slack Notifications Plugin active.")
        
        # Subscribe to high-priority events
        ctx.event_bus.subscribe("agent.needs_approval", self.send_approval_card)
        ctx.event_bus.subscribe("security.vulnerability_found", self.send_security_alert)

    def send_approval_card(self, ctx: PluginContext, event: AegisEvent):
        payload = event.payload
        card_data = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚠️ *Agent Approval Required*
*Agent:* {payload.get('agent_name')}
*Run ID:* `{payload.get('agent_run_id')}`"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Approve Action"},
                            "style": "primary",
                            "value": f"approve:{payload.get('agent_run_id')}"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Reject"},
                            "style": "danger",
                            "value": f"reject:{payload.get('agent_run_id')}"
                        }
                    ]
                }
            ]
        }
        self._post_to_slack(card_data)

    def send_security_alert(self, ctx: PluginContext, event: AegisEvent):
        payload = event.payload
        alert_data = {
            "text": f"🚨 *Critical Security Vulnerability Detected!*
*CVE:* {payload.get('cve_id')}
*File:* `{payload.get('file_path')}:{payload.get('line_number')}`
*Description:* {payload.get('description')}"
        }
        self._post_to_slack(alert_data)

    def _post_to_slack(self, data: dict):
        req = urllib.request.Request(
            self.webhook_url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req)
```

---

### 9.3 Example 3: Custom Security Auditor AI Agent Type Plugin

#### Manifest & Definition File (`agent_plugin.yaml`)
```yaml
id: "aegis-agent-security-auditor"
name: "Security Auditor Agent Persona"
version: "2.1.0"
plugin_type: "agent"
agent_definition:
  agent_type: "security_auditor"
  system_prompt: |
    You are an expert DevSecOps Security Auditor Agent operating inside AegisOS.
    Your objective is to inspect generated code diffs for security vulnerabilities, OWASP Top 10 flaws, hardcoded secrets, and unsafe dependencies.
    Execution Workflow:
    1. Analyze modified code files using static analysis AST rules.
    2. Query global security vector memory for historical CVE mitigations.
    3. Generate a structured security review payload with critical/high/medium vulnerability counts.
    4. If critical issues exist, emit a security.vulnerability_found event and block the deployment pipeline.
  model_provider: "anthropic"
  model_name: "claude-3-5-sonnet"
  temperature: 0.0
  max_tokens: 8192
  enabled_tools:
    - "semgrep_scanner"
    - "dependency_checker"
    - "memory_vector_search"
    - "patch_generator"
permissions:
  - "filesystem:read"
  - "memory:read"
  - "event:publish"
```

---