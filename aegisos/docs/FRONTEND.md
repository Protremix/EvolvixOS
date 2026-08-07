# Frontend Guide

## Overview

EvolvixOS frontend is a React 18 application with Vite and TailwindCSS.

## Pages (33 total)

### Core
- **Login/Register** — Authentication
- **Dashboard** — System overview with health grid, pipeline stats, performance metrics
- **Settings** — User preferences

### Project Management
- **Projects** — List and manage projects
- **Project Detail** — Individual project view
- **Tasks** — Task management
- **Agents** — AI agent list and status
- **Agent Detail** — Individual agent configuration

### Pipelines
- **Pipelines** — Feature pipeline management and execution
- **Pipeline Templates** — Pre-configured templates (8 built-in)
- **Pipeline Analytics** — 5-tab analytics (overview, stages, agents, throughput, scheduler)

### Code Operations
- **CodeOps** — Test generation + CI healing
- **Dependency Graph** — Import analysis and visualization
- **AST Diff** — Semantic code diffing
- **Spec Compiler** — OpenAPI/AsyncAPI to code generation
- **Project Adapters** — 7 project type adapters

### Monitoring
- **Verdis** — Live blockchain monitoring
- **Verdis Project** — Verdis as managed project (health, alerts, components)
- **GitHub** — Repository monitoring, issues, PRs, CI/CD
- **Executor Status** — AI executor status
- **Feedback** — Agent feedback and improvements

### System
- **Webhooks** — Webhook subscription management
- **System Settings** — 30+ runtime settings
- **Activity Log** — Audit trail
- **Agent Config** — Per-agent, per-project configuration
- **Backups** — Backup and restore
- **Search** — Global search bar in layout

## Architecture

```
App.jsx (Router)
├── ProtectedRoute (Auth check)
├── Sidebar (Navigation)
├── GlobalSearch (Search bar)
└── Routes
    ├── /dashboard → Dashboard
    ├── /projects → Projects
    ├── /pipelines → Pipelines
    ├── /verdis-project → VerdisProject
    └── ... (33 pages)
```

## API Services

Each service wraps a backend API router:

```javascript
// src/services/api.js — Base Axios instance
const api = axios.create({
  baseURL: '/api/v1',
  headers: { Authorization: `Bearer ${token}` }
});

// src/services/verdisProjectService.js
export default {
  overview: () => api.get('/verdis-project/overview'),
  healthCheck: () => api.post('/verdis-project/health-check'),
  // ...
};
```

## WebSocket

Real-time pipeline events via WebSocket:

```javascript
// WSIndicator component manages connection
// Events flow: pipeline.started → stage_started → stage_passed → pipeline.completed
```

## Design System

- **Theme**: Dark (#0D0D0F background, #1A1A1E panels)
- **Primary color**: #4F46E5 (indigo)
- **Text**: #CCC (primary), #888 (secondary), #666 (muted)
- **Borders**: #333
- **Status colors**: #22C55E (healthy), #FFA500 (warning), #EF4444 (error)
- **Radius**: 6-10px
- **Font size**: 13px base
