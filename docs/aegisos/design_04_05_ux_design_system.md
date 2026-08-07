# AEGISOS: UX ARCHITECTURE & DESIGN SYSTEM SPECIFICATION
*Document Version: 1.0.0 | Enterprise AI Engineering Operating System*
*Primary Palette: Deep Dark Theme | Eco-Green Brand Accent (#00ff88)*

---

## 4. UX ARCHITECTURE

### 4.1 Interaction Model

AegisOS is built from the ground up to support high-bandwidth, multi-agent AI engineering workflows. Unlike traditional developer tools that treat AI as a sidecar chat widget, AegisOS places autonomous AI agents, human software engineers, and automated CI/CD pipelines into a unified, spatial execution interface. The interaction architecture prioritizes low-latency keyboard controls, streaming real-time feedback, non-blocking asynchronous multi-agent delegation, and safety-critical human-in-the-loop (HITL) approval mechanics.

#### Primary Interaction Patterns
1. **Direct Spatial Manipulation**: Users interact with agent tasks, DAG nodes, code diffs, and infrastructure pipelines as direct physical objects. Dragging tasks across Kanban swimlanes recalculates agent execution priorities in real time; clicking a node in a deployment DAG expands live streaming telemetry and container logs.
2. **Declarative Prompting & Dynamic Steering**: Rather than writing static code or raw terminal commands, human engineers issue high-level declarative goals to autonomous agent swarms (e.g., `@Architect refactor auth middleware to support WebAuthn and pass security benchmarks`). Users steer agent swarms during execution by injecting live guidance, adjusting constraints, or pausing agent branches mid-thought.
3. **Command-First Flow**: Inspired by Linear and Raycast, every platform action, page navigation, agent invocation, configuration tweak, and repository query is accessible within two keystrokes via a unified Command Palette (`Cmd+K`).
4. **Human-in-the-Loop (HITL) Safety Gates**: High-risk agent actions—such as merging code into production branches, executing infrastructure migrations, or modifying security permissions—are gated by interactive approval cards. These cards present security impact scores, code diffs, automated test results, and one-click authorization controls.
5. **Multi-Agent Supervision**: The interface provides a macro view of active agent swarms, showing real-time token consumption velocity, working context windows, current reasoning steps (Chain-of-Thought), and active file locks.

```
+-----------------------------------------------------------------------------------+
|                                 GLOBAL HEADER BAR                                 |
| Workspace Switcher | Active Agents (14) | System Status: OK | Quick Action | User   |
+-----------------------------------------------------------------------------------+
| SIDEBAR      | MAIN VIEWSPACE                                    | AGENT CONSOLE  |
| - Overview   | [Breadcrumb: Projects / Aegis Core / Task-204]    | (@Architect)   |
| - Projects   | +-----------------------------------------------+ | Real-time CoT  |
| - Agent Mesh | | TASK DETAILS & LIVE AGENT WORKFLOW DAG         | | Streaming...   |
| - Code & PRs | | [Agent Swarm Working: 3 sub-tasks running]   | | Tool: edit_file|
| - Deploy     | +-----------------------------------------------+ | [Inject Input] |
| - Knowledge  | | CODE DIFF VIEWER / LIVE AGENT OUTPUT STREAM   | | [Pause Agent]  |
| - Metrics    | |                                               | |                |
| - Settings   | +-----------------------------------------------+ |                |
+-----------------------------------------------------------------------------------+
| FOOTER: Command Hint (Cmd+K) | Memory Sync: 100% | Token Rate: 1.2k/s | UTC 08:46 |
+-----------------------------------------------------------------------------------+
```

#### Command Palette Architecture
The Command Palette is the central nervous system of AegisOS. It operates as a global modal overlay triggered by `Cmd+K` (macOS) or `Ctrl+K` (Linux/Windows). It features instant fuzzy search across all system entities, active agents, codebase files, deployment logs, and documentation.

- **Trigger Mechanisms**:
  - `Cmd + K` / `Ctrl + K`: Global palette launch in default command mode.
  - `Cmd + P` / `Ctrl + P`: Launches palette directly in File Quick-Open mode.
  - `Cmd + Shift + A`: Launches palette in Agent Steering mode (pre-filled with `@` trigger).
  - `Cmd + Shift + F`: Launches palette in Cross-Repository Search mode.

- **Palette Execution Modes**:
  1. *Navigation Mode*: Fuzzy search page routes, project dashboards, and settings.
  2. *Action Mode*: Instantly trigger platform commands (e.g., `Deploy Staging`, `Create Task`, `Flush Agent Memory`).
  3. *Entity Switcher*: Search and jump to specific Projects, Tasks, Pull Requests, Agents, or Microservices.
  4. *Agent Prompt Mode*: Type natural language instructions directly to the active project context (e.g., `> @Tester run mutation tests on payment service`).
  5. *Contextual Selection Mode*: When text or code is highlighted in the editor/diff viewer, pressing `Cmd+K` opens a localized palette with transformation presets (e.g., `Refactor for performance`, `Add TypeScript types`, `Generate unit tests`).

- **Fuzzy Search Engine Specs**:
  - Implemented using client-side WebAssembly Indexing (`fuzzysort` / `flexsearch`) backed by persistent WebWorker indexing.
  - Queries are scored against weighted attributes: Exact Symbol Match (weight 1.0), Entity Name (0.8), Recent Access (0.6), Tags/Metadata (0.4).
  - Sub-15ms response latency guaranteed across up to 100,000 indexed records.

- **Keyboard Navigation Standard**:
  - `Up Arrow` / `Down Arrow` or `Ctrl + N` / `Ctrl + P`: Move focus through result items.
  - `Tab`: Autocomplete selected item into search bar (for multi-level breadcrumb navigation).
  - `Enter`: Execute highlighted command or navigate to selected entity.
  - `Cmd + Enter`: Execute command in background / secondary split pane.
  - `Escape`: Instantly dismiss palette, returning focus to previous element.

```
+-----------------------------------------------------------------------------------+
|  COMMAND PALETTE                                                       [Esc]      |
|  > @Architect refactor auth middleware|                                          |
+-----------------------------------------------------------------------------------+
|  SUGGESTED ACTIONS                                                                |
|  > @Architect Refactor File           Issue instruction to Architect agent       |
|  > Jump to AuthMiddleware.ts          File in aegis-core/src/auth               |
|  > Run Security Audit Workflow        Triggers Agent-Sec-01                     |
|                                                                                   |
|  RECENT COMMANDS                                                                  |
|    Switch Workspace -> Enterprise Prod                                           |
|    Toggle Dark Mode                                                               |
+-----------------------------------------------------------------------------------+
|  [Up/Down] Navigate  |  [Enter] Select  |  [Tab] Autocomplete  |  [Cmd+Enter] Split |
+-----------------------------------------------------------------------------------+
```

#### Keyboard Shortcuts Matrix
AegisOS offers a full vim-inspired and modern IDE shortcut system designed for zero-mouse operations.

| Category | Shortcut (macOS) | Shortcut (Win/Linux) | Action / Function |
| :--- | :--- | :--- | :--- |
| **Global Navigation** | `G` then `D` | `G` then `D` | Jump to Global Overview Dashboard |
| | `G` then `P` | `G` then `P` | Jump to Projects List |
| | `G` then `A` | `G` then `A` | Jump to Agent Status Mesh |
| | `G` then `C` | `G` then `C` | Jump to Code Review & PR View |
| | `G` then `M` | `G` then `M` | Jump to Engineering Metrics |
| | `G` then `S` | `G` then `S` | Jump to System Settings |
| **Command & Search** | `Cmd + K` | `Ctrl + K` | Open Command Palette |
| | `Cmd + P` | `Ctrl + P` | Quick Open File |
| | `Cmd + Shift + A` | `Ctrl + Shift + A` | Target Agent Prompt |
| | `/` | `/` | Focus search bar in active table/view |
| **Task Board (Kanban)**| `N` | `N` | Create new Task |
| | `E` | `E` | Edit highlighted Task |
| | `A` | `A` | Assign Task to Agent/Human |
| | `M` | `M` | Move Task to next column |
| | `Space` | `Space` | Toggle preview drawer for highlighted Task |
| **Code Review & Diffs** | `J` / `K` | `J` / `K` | Jump to Next / Previous Diff Hunk |
| | `C` | `C` | Add line comment at current selection |
| | `Cmd + Enter` | `Ctrl + Enter` | Submit Review / Approve PR |
| | `R` | `R` | Request AI Agent Refactor on current diff |
| **Agent Steering** | `Cmd + Shift + P` | `Ctrl + Shift + P` | Pause all active agents on current task |
| | `Cmd + Shift + R` | `Ctrl + Shift + R` | Retry failed agent execution step |
| | `Cmd + Shift + X` | `Ctrl + Shift + X` | Abort active agent execution thread |
| | `M` | `M` | Open Agent Vector Memory Inspector |

#### Natural Language Interface (Chat with Agents)
The Natural Language Interface is not an isolated chatbot, but an agent control console deeply connected to the active UI state.

- **Interface Ergonomics**:
  - *Persistent Split-Pane Console*: Docked to the right side of the workspace (width: 380px, collapsible to 48px rail).
  - *Full-Screen Steer View*: Triggered when conducting deep research, complex DAG creation, or architectural debates with agent teams.
  - *Floating Context Bubble*: Available on code review and Kanban views for swift inline instructions.

- **Real-Time Streaming Protocol**:
  - Powered by Server-Sent Events (SSE) / WebSockets delivering JSON patch operations.
  - Streams raw text, structured tool invocation accordions, execution status pills, and code block artifacts.
  - Expandable Chain-of-Thought (CoT) blocks let engineers inspect the agent's step-by-step reasoning before tool execution.

- **Prompt Interpolation & Syntactic Sugar**:
  - `@` Mention Agents: `@Architect`, `@CodeSynth`, `@QA-Bot`, `@SecOps`.
  - `#` Reference Tasks & Issues: `#TASK-402`, `#BUG-109`.
  - `$` Reference Files & Symbols: `$src/auth/jwt.ts`, `$PaymentController`.
  - `%` Reference Environments & Deployments: `%staging-us-east`, `%prod-canary`.

- **Agent Memory Inspector**:
  - Clicking any agent message opens the Memory Inspector drawer, revealing the exact system prompt, injected context chunks, token count usage (e.g., 42,150 / 128,000 tokens), and retrieved vector embeddings from RAG memory.

---

### 4.2 Navigation Structure

AegisOS employs a hierarchical, multi-tier spatial navigation architecture engineered for complex multi-project engineering environments.

```
+----------------------------------------------------------------------------------+
| LAYER 1: GLOBAL HEADER (Workspace Switcher | Tenant Context | Agent Telemetry)    |
+----------------------------------------------------------------------------------+
| LAYER 2: PRIMARY SIDEBAR    | LAYER 3: BREADCRUMB BAR & SUB-NAV                   |
|  - Enterprise Workspace     | AegisOS > Projects > Core-Platform > Sprint 42     |
|  - Tier 1 Navigation        +----------------------------------------------------+
|  - Tier 2 Recent Items      | LAYER 4: MAIN WORKSPACE CONTENT VIEW               |
|  - Agent Status Rail        | (Dashboard / Board / Code Diff / Terminal / Docs)  |
+----------------------------------------------------------------------------------+
```

#### Top-Level Navigation Items
1. **Global Overview (`/dashboard`)**: Macro view of engineering health, active agent workforce, deployment status, and urgent human approvals.
2. **Projects (`/projects`)**: Workspace project repository hierarchy, sprint planning, task backlogs, and milestone tracking.
3. **Agent Mesh (`/agents`)**: Real-time operational map of all AI agents, workforce allocation, model settings, and memory knowledge bases.
4. **Code & PRs (`/code`)**: Cross-repository code browser, agent pull request review queue, automated code quality analysis.
5. **Deployments (`/deployments`)**: CI/CD pipeline visualizer, environment management (Dev, Staging, Production), canary rollouts, and rollback controls.
6. **Knowledge Base (`/knowledge`)**: System documentation, architectural decision records (ADRs), agent vector memory graphs, and API specs.
7. **Telemetry & Metrics (`/metrics`)**: Engineering velocity, DORA metrics, token budget economics, agent accuracy metrics, and error rates.
8. **Settings & Governance (`/settings`)**: RBAC, security guardrails, API keys, AI model provider integrations, and billing.

#### Sub-Navigation, Breadcrumbs & Sidebar Architecture

- **Primary Sidebar (Left, Width: 240px expanded / 64px collapsed)**:
  - *Header*: Tenant logo, Enterprise Workspace selector dropdown (`Aegis Enterprise v2.4`).
  - *Main Navigation Group*: Icons with clear text labels and badge count overlays (e.g., PRs badge showing `3 Pending Approval` in eco-green accent).
  - *Pinned / Recent Projects*: Quick-access accordion showing top 5 active projects with live agent execution indicators (pulsing green dot).
  - *Saved Filters & Views*: Custom saved queries (e.g., `My Approvals`, `Failed Agent Builds`).
  - *Sidebar Footer*: Agent Swarm Status pill (`14/16 Active`), system performance metric (`Latency: 24ms`), collapsed toggle button (`Cmd+\`).

- **Sub-Navigation Tabs**:
  - Situated horizontally directly under the Breadcrumb Header on detail pages.
  - Example for Project Detail: `[ Overview | Task Board | Agent Swarm | Pull Requests | Deployments | Settings ]`.
  - Uses underline indicator in `#00ff88` with smooth layout spring transitions.

- **Breadcrumb Hierarchy**:
  - Formatted as interactive inline paths: `Workspace` / `Project Name` / `Resource Type` / `Specific Entity`.
  - Example: `Acme Corp / Aegis-Core / Pull Requests / PR-104 (@Synthesizer: Add WebAuthn)`.
  - Each breadcrumb segment features a hover dropdown menu allowing immediate switching to parallel resources without returning to higher-level lists.

---

### 4.3 Page Layouts

AegisOS features 10 core layout designs optimized for dark theme visual clarity and high information density.

```
+----------------------------------------------------------------------------------+
| PAGE LAYOUT COMPONENT STRUCTURE MATRIX                                            |
+-------------------+----------------------------------+---------------------------+
| Layout Name       | Primary Pane Composition         | Secondary / Auxiliary Pane|
+-------------------+----------------------------------+---------------------------+
| 1. Overview       | 4-Column Metric Grid + Feed      | Approval Queue Drawer     |
| 2. Projects List  | Data Grid / Card Matrix          | Project Filter Sidebar    |
| 3. Project Detail | Header Summary + Sub-tab View    | Active Agent Mesh Rail    |
| 4. Task Board     | Multi-column Kanban (Horizontal) | Task Inspector Drawer     |
| 5. Agent Status   | Spatial Node Graph / Table       | Agent Telemetry Side-Pane |
| 6. Code Review    | File Tree (Left) + Split Diff    | AI Code Suggestions Rail  |
| 7. Deployment     | Pipeline DAG + Container Terminal| Environmental Health Meter|
| 8. Documentation  | Doc Tree + Markdown Render       | Vector Graph / TOC        |
| 9. Settings       | Vertical Navigation + Form Cards | Policy Validation Rail    |
| 10. Marketplace   | Search Hero + Grid Matrix        | Agent Specification Modal |
+-------------------+----------------------------------+---------------------------+
```

#### 1. Dashboard / Overview Layout
- **Header**: Workspace title, global date range picker, system operational status badge (`All Systems Operational`).
- **Top Metric Row**: 4 KPI cards (Active Agents, Sprint Completion %, Production Deployment Status, Token Expenditure Rate).
- **Central Area (2-Column Grid, 65% / 35% Split)**:
  - *Left Column*: Real-time Agent Activity Feed displaying live streaming actions, file edits, and execution milestones.
  - *Right Column*: Urgent Human-In-The-Loop Approval Queue (code merge requests, deployment authorization cards).
- **Bottom Section**: Cross-project velocity sparklines and system infrastructure health map.

#### 2. Projects List Layout
- **Header**: Project search bar, Filter tags (`Active`, `Archived`, `High Priority`), `+ New Project` primary action button.
- **View Toggle**: Segmented control switching between Grid Card view and High-Density Table view.
- **Project Cards Matrix**:
  - Card displays Project Name, Repository Link, Active Agent Team avatars, Progress bar (Task completion), Last Agent Action timestamp, Health status indicator pill.

#### 3. Project Detail Layout
- **Header Summary**: Project Title, Branch tag (`main`), Environment status, Lead Agent avatar, Quick Action buttons (`Assign Task`, `Run CI Pipeline`).
- **Tab Navigation Bar**: `Overview`, `Kanban Board`, `Agent Workforce`, `Code & PRs`, `Pipelines`, `Settings`.
- **Main Viewport**: Dynamic container rendering selected sub-tab layout.
- **Right Rail (Collapsible)**: Live project activity log and agent resource monitor.

#### 4. Task Board (Kanban) Layout
- **Header Bar**: Sprint selector dropdown, Filter by Agent/Human, Group by (Status, Priority, Assignee, Agent Capability), Search tasks.
- **Kanban Columns**: Horizontal scroll container rendering 5 default columns: `Backlog`, `Ready for Agent`, `Agent In-Progress`, `Human Review (HITL)`, `Done`.
- **Task Cards**:
  - Displays Task ID (`#TASK-204`), Title, Priority tag (P0, P1, P2), Assigned Agent badge with live animated pulse if executing, Sub-task progress (`4/5 completed`), Complexity score.
- **Slide-Over Task Inspector**: Clicking a card opens a 480px slide-over drawer with full task description, agent CoT execution trail, sub-task DAG, and comment history.

#### 5. Agent Status & Mesh Layout
- **Header**: Workforce filter (`Architects`, `Coders`, `Testers`, `SecOps`), Global pause/resume toggle, Token rate indicator.
- **Top View Switch**: Toggle between *Spatial Node Graph* view (showing agent communication networks) and *Grid Table* view.
- **Agent Grid Cards**:
  - Each card represents an agent: Agent Name (`@Architect-01`), Model (`Claude-3.5-Sonnet`), Status pill (`Busy`, `Idle`, `Error`, `Waiting Approval`), Current Action string, Token usage gauge, Memory context bar.

#### 6. Code Review View Layout
- **Header**: Pull Request Title (`PR-104: Add WebAuthn Auth`), Author (`@CodeSynth-Alpha`), Target branch (`main`), CI Build status badge, Risk Rating pill (`Low Risk - 98% Test Pass`).
- **Layout Split (3 Panes)**:
  - *Pane 1 (Left, 220px)*: Changed files tree with addition/deletion line metrics (`+142 / -28`).
  - *Pane 2 (Center, Flex)*: High-performance Syntax-Highlighted Diff Viewer (Side-by-side or Unified mode). Support for line comments, AI refactor triggers, and code expansion.
  - *Pane 3 (Right, 320px)*: AI Code Review Summary, Security Scan results, Automated Test Matrix, and Approval action box (`Approve & Merge`, `Request Agent Revision`).

#### 7. Deployment Pipeline View Layout
- **Header**: Deployment Target (`Production US-East`), Active Build Version (`v2.4.12`), Rolling status indicator, Emergency Rollback button.
- **Main Pipeline DAG View**: Interactive node graph displaying sequential build stages (`Build Artifact` -> `Unit Tests` -> `Security Audit` -> `Staging Deploy` -> `Canary 10%` -> `Prod Deploy`). Nodes flash green on success, red on failure, pulse eco-green while executing.
- **Bottom Split Pane**: Live Docker / Kubernetes container terminal log stream with search and severity filtering (`INFO`, `WARN`, `ERROR`).

#### 8. Documentation & Knowledge View Layout
- **Header**: Knowledge Base Search, Sync with Repo button, `+ New ADR` button.
- **Layout Split (3 Panes)**:
  - *Pane 1 (Left, 260px)*: Navigation tree of system documentation, ADRs, API references, and Agent Vector Memory indices.
  - *Pane 2 (Center, Flex)*: Rich Markdown viewer/editor with live rendering, mathematical equations, rendered Mermaid.js diagrams, and code snippets.
  - *Pane 3 (Right, 240px)*: Vector Knowledge Graph preview, showing semantic backlinks and related agent memory nodes.

#### 9. Settings & Governance Layout
- **Left Rail**: Settings navigation categories (`General Workspace`, `Agent Guardrails & RBAC`, `Model Providers & API Keys`, `Token Budgets`, `Integrations`, `Audit Logs`).
- **Main Viewport**: Clean form-card layout with distinct action sections, inline validation, CSS toggle switches, and secret-key mask inputs.

#### 10. Marketplace & Agent Hub Layout (Future)
- **Header**: Agent Template Search, Category filters (`Security`, `Frontend`, `Database`, `DevOps`), Popularity sort.
- **Grid Matrix**: Displaying community and enterprise pre-built agent swarms with rating stars, model base, capabilities tags, and 1-click `Install to Workspace` button.

---

### 4.4 Dashboards

AegisOS provides four distinct domain-tailored dashboards to serve different enterprise roles.

```
+----------------------------------------------------------------------------------+
| DASHBOARD DOMAIN ARCHITECTURE                                                     |
+----------------------------------------------------------------------------------+
| 1. GLOBAL ENTERPRISE DASHBOARD    --> C-Level / VP of Engineering View              |
|    [System Health] [Agent Workforce Load] [Cross-Project Telemetry] [Approvals]   |
+----------------------------------------------------------------------------------+
| 2. PROJECT DASHBOARD             --> Engineering Lead / Tech Lead View           |
|    [Sprint Burn-Down] [Agent vs Human Commits] [Active Blockers] [PR Pipeline]    |
+----------------------------------------------------------------------------------+
| 3. AGENT OPERATIONS DASHBOARD    --> AI Infrastructure / MLOps View               |
|    [Token Consumption Rate] [Model Latency] [Execution Stack] [Error Rates]      |
+----------------------------------------------------------------------------------+
| 4. METRICS & INTELLIGENCE        --> DevOps / QA / Security View                 |
|    [DORA Metrics] [Code Quality Index] [Token ROI Economics] [MTTR Trends]        |
+----------------------------------------------------------------------------------+
```

#### 1. Global Enterprise Dashboard
Designed for CTOs, VPs of Engineering, and System Administrators who require high-level cross-project oversight.
- **Widgets**:
  - *System Operational Health Gauge*: Overall system state, active alerts, service status.
  - *Active Agent Swarm Allocation*: Donut chart showing agent distribution across projects (e.g., 40% Security, 30% Feature Development, 20% QA, 10% Maintenance).
  - *Enterprise Token Burn Rate*: Real-time cost accumulator vs monthly budget ceiling.
  - *Priority Approval Queue*: High-risk production actions requiring executive sign-off.
  - *Cross-Project Delivery Velocity*: Comparative bar charts showing task velocity across all enterprise teams.

#### 2. Project Dashboard
Tailored for Tech Leads, Engineering Managers, and Scrum Masters focused on a specific repository or service.
- **Widgets**:
  - *Sprint Velocity & Burn-Down Chart*: Interactive area chart showing completed vs remaining story points.
  - *Code Authorship Distribution*: Pie chart contrasting human-written code vs agent-generated code merged.
  - *Active Task Flow Matrix*: Micro Kanban snapshot highlighting bottleneck columns.
  - *Recent Pull Requests*: Live list of active PRs with automated AI security audit scores.
  - *Active Agent Workforce*: List of agents assigned to this project with current live task status.

#### 3. Agent Operations Dashboard
Engineered for AI Engineers and MLOps Leads monitoring agent performance and resource consumption.
- **Widgets**:
  - *Real-time Token Consumption Velocity*: Live line chart plotting input/output tokens per second across model providers (Anthropic, OpenAI, Local vLLM).
  - *Model Latency & Time-To-First-Token (TTFT)*: Percentile distribution graphs (p50, p95, p99).
  - *Agent Error Rate & Retry Barometer*: Stacked bar chart categorizing agent failures (Context window overflow, Tool call timeout, Syntax error, Failed test).
  - *Active Context Window Utilization*: Heatmap showing context memory fill state across active agent instances.

#### 4. Metrics & Engineering Intelligence Dashboard
Designed for DevOps leads and Quality Assurance Directors measuring platform effectiveness and ROI.
- **Widgets**:
  - *DORA Metrics Panel*:
    1. *Deployment Frequency*: Daily/weekly production release count.
    2. *Lead Time for Changes*: Duration from first commit/agent prompt to production deploy.
    3. *Mean Time to Recovery (MTTR)*: Average resolution time for production incidents.
    4. *Change Failure Rate*: Percentage of deployments causing degraded service.
  - *Automated Test Pass Rates*: Line graph showing unit, integration, and E2E test success trends over time.
  - *Engineering Hours Saved Estimator*: ROI metric calculating estimated manual engineering hours offset by autonomous agent execution.

---

### 4.5 Key Widgets

Each widget in AegisOS is an autonomous visual component with built-in WebSocket telemetry streams and interactive controls.

#### 1. Agent Activity Feed
- **Purpose**: Displays a live, continuous audit stream of all agent thoughts, tool calls, file writes, and test runs.
- **Structure**: Vertical timeline with time-stamped log items.
- **States**: Streaming (animated pulsing eco-green left border), Completed (solid neutral border), Failed (solid red border), Interrupted (orange border).
- **Interactions**: Click any feed item to expand/collapse Chain-of-Thought (CoT) details, inspect raw JSON tool payloads, or jump directly to modified files.

```
+----------------------------------------------------------------------------------+
| AGENT ACTIVITY FEED WIDGET                                                       |
+----------------------------------------------------------------------------------+
| 08:45:12  [@CodeSynth-Alpha] Executing Tool: edit_file                           |
|           File: src/auth/jwt.ts (+14, -2)                                        |
|           > Added HMAC-SHA256 signature validation check.                       |
|           [View Diff]  [Inspect Tool Payload]                                    |
|----------------------------------------------------------------------------------|
| 08:45:02  [*Thought Process - Click to collapse*]                                |
|           "The user requested JWT validation. I must check ifjsonwebtoken library|
|           is present in package.json and import verification method..."          |
|----------------------------------------------------------------------------------|
| 08:44:50  [@QA-Bot] Executing Tool: run_test                                     |
|           Command: npm test -- src/auth/jwt.test.ts                              |
|           Status: SUCCESS (3/3 Tests Passed in 142ms)                            |
+----------------------------------------------------------------------------------+
```

#### 2. Task Progress Tracker
- **Purpose**: Visualizes multi-stage sub-task execution for complex agent workflows.
- **Structure**: Horizontal multi-segmented progress bar combined with an expandable DAG tree.
- **Data Binding**: Binds directly to task execution state machines. Displays overall completion percentage, estimated time remaining, assigned agents, and blocker alerts.

#### 3. Code Diff Viewer
- **Purpose**: High-performance line-by-line or side-by-side code diff viewer designed for reviewing agent-generated code.
- **Features**: Syntax highlighting (PrismJS/Shiki integration), line number gutters, inline AI refactor toolbar, inline comment threads, word-level diff highlight.
- **Interactions**: Hover line numbers to click `+` and leave inline comments or trigger `@Agent fix this line`.

#### 4. Deployment Timeline Graph
- **Purpose**: Visualizes CI/CD execution pipelines as interactive directed acyclic graphs (DAGs).
- **Features**: Nodes represent stages (`Lint`, `Build`, `Security Scan`, `Deploy`). Status badges update live over WebSockets. Hovering a node displays execution duration and container memory usage; clicking opens log streams.

#### 5. Metrics Sparklines & Charts
- **Purpose**: Ultra-compact vector sparklines and interactive time-series area graphs.
- **Implementation**: Built with SVG and Canvas API for sub-millisecond renders.
- **Interactions**: Hover scrubbers display detailed tooltips with precise timestamp value readouts; period toggles (`1H`, `24H`, `7D`, `30D`).

#### 6. Human-In-The-Loop (HITL) Approval Queue
- **Purpose**: Centralized queue card presenting high-risk agent operations requiring human clearance.
- **Structure**: Card container featuring Risk Level Badge (`High Risk - Production Database Migration`), Agent author, Executive Summary of changes, automated security rating, and primary action controls (`Approve & Execute`, `Reject with Instructions`, `Modify Parameters`).

---

### 4.6 User Workflows

Detailed step-by-step operational workflows demonstrating human-agent execution flows.

```
+----------------------------------------------------------------------------------+
| WORKFLOW EXECUTION ARCHITECTURE                                                  |
+----------------------------------------------------------------------------------+
| [Human Prompt / Action] --> [Agent DAG Decomposition] --> [Parallel Execution]    |
|                                                                    |             |
| [Production Deployment] <-- [HITL Approval Gate] <-- [AI Review & QA Validation] |
+----------------------------------------------------------------------------------+
```

#### Workflow 1: Create a New Project
1. **Initiation**: User navigates to `/projects` and clicks `+ New Project` button or presses `Cmd+K` and selects `Action: Create New Project`.
2. **Configuration Modal**: User selects between *Import Repository* (GitHub/GitLab), *Scaffold from Template* (Next.js, Rust Microservice, Python AI Service), or *Prompt-Driven AI Generation*.
3. **Prompt Specification**: User inputs project intent: `"Build a resilient payment service with Stripe webhook verification, Redis rate-limiting, and PostgreSQL transaction logging"`.
4. **Agent Team Selection**: User selects default agent team presets (`Standard Dev Team: Architect, Coder, QA, SecOps`).
5. **Execution**: Platform provisions repository, injects security guardrails, initializes agent vector memory indices, and builds initial task breakdown DAG.
6. **Completion**: User is redirected to Project Dashboard with initial scaffold ready for inspection.

#### Workflow 2: Assign Work to Agents
1. **Task Creation**: User hits `N` on Kanban board or types in chat console: `@Architect decompose issue #TASK-302 into sub-tasks`.
2. **DAG Generation**: Architect agent processes prompt, analyzes codebase vector memory, and drafts a sub-task execution tree (`Task 302.1: Schema Update`, `Task 302.2: API Route Implementation`, `Task 302.3: Unit Tests`).
3. **Assignment & Review**: User inspects generated DAG in Task Inspector drawer, adjusts priority weights, and clicks `Confirm & Dispatch Swarm`.
4. **Parallel Execution**: Assignee agents (`@CodeSynth`, `@QA-Bot`) transition task status to `Agent In-Progress`, acquire file locks, and stream edits in real time.

#### Workflow 3: Review Agent Output
1. **Notification**: Agent completes sub-tasks, runs unit tests, and submits Pull Request (`PR-88`). User receives toast alert and PR queue notification.
2. **Opening PR View**: User opens Code Review View (`G` then `C`).
3. **AI Automated Summary Inspection**: User reviews AI-generated changelog, security vulnerability scan (`0 Critical, 0 High`), and test results (`100% Pass`).
4. **Diff Inspection**: User inspects syntax-highlighted code diff hunks using `J`/`K` keys.
5. **Inline Guidance**: User selects a block of code, presses `Cmd+K`, and inputs: `Refactor this try-catch block to use custom PaymentException class`.
6. **Agent Auto-Fix**: Assignee agent receives instruction, applies modification hunks inline within 5 seconds, and updates PR.
7. **Approval**: User presses `Cmd+Enter` to approve PR and trigger automated merge.

#### Workflow 4: Approve Deployment
1. **Pipeline Trigger**: Merged PR automatically triggers staging deployment pipeline.
2. **Staging Verification**: `@QA-Bot` runs automated end-to-end synthetic tests against staging URL (`%staging-payment-v2`).
3. **HITL Risk Gate**: Platform creates a Production Approval Card in the Approval Queue. Risk engine assesses score: `Medium Risk (Schema migration detected)`.
4. **Human Review**: Engineering Lead inspects Staging Verification Report, schema rollback scripts, and canary release plan.
5. **Execution Authorization**: Lead clicks `Approve & Execute Canary Deploy` and confirms via WebAuthn biometric touch ID.
6. **Deployment & Telemetry**: Deployment Timeline Graph visualizes canary rollout (10% -> 50% -> 100%) while telemetry sparklines monitor error rate spikes.

#### Workflow 5: Handle Failure Alert
1. **Alert Generation**: An agent encounters a recurring execution exception (`ToolExecutionError: Redis connection refused in src/cache.ts`).
2. **System Intervention**: Platform automatically halts agent thread, prevents infinite loop token burn, sets status to `Error`, and fires system alert toast.
3. **Root Cause Analysis (RCA) Drawer**: User clicks alert to open RCA drawer containing: exact stack trace, agent reasoning log immediately prior to failure, and environment status.
4. **Resolution Options**:
   - Option A: User edits environment variable configuration and clicks `Retry Step` (`Cmd+Shift+R`).
   - Option B: User types inline correction into chat console: `Use fallback mock cache if Redis host is unreachable`.
   - Option C: User clicks `Abort Agent & Revert File Edits`.
5. **Resume**: Agent ingests correction, clears error state, and resumes execution seamlessly.

#### Workflow 6: Browse Agent Memory & Decisions
1. **Launch Inspector**: User clicks `Memory` icon in sidebar or presses `M` on any agent profile card.
2. **Memory Graph Exploration**: Interface renders interactive 3D/2D spatial node graph of agent long-term memory (RAG vector store). Nodes represent codebase ADRs, past bug fixes, system architecture patterns, and user preferences.
3. **Semantic Query**: User types into memory search bar: `Why did we select HMAC-SHA256 over RSA for webhook signing?`.
4. **Decision Audit**: System highlights relevant memory node and displays full provenance: original Slack discussion snippet, ADR document link, author timestamp, and confidence score (94.2%).
5. **Memory Management**: User can edit outdated memory records, adjust vector relevance weights, or purge invalid memory entries.

---

### 4.7 Mobile Considerations

Although AegisOS is a desktop-first engineering platform, its mobile experience is fully functional, ensuring engineering leads and on-call responders can approve deployments, handle alerts, and steer agents from smartphones and tablets.

- **Mobile Navigation Pattern**:
  - The left sidebar collapses into a slide-out drawer accessible via a top-left hamburger menu or swipe-right gesture.
  - A fixed **Bottom Navigation Bar** provides quick access to 4 core touchpoints: `Overview`, `Approvals` (with badge counter), `Agents`, and `Alerts`.
  - The Command Palette trigger is accessible as a quick-action Floating Action Button (FAB) displaying the brand eco-green `#00ff88` glow icon.

- **Touch-Friendly Hit Targets**:
  - Minimum touch hit target size of **44px x 44px** enforced across all interactive buttons, tabs, table rows, and form inputs.
  - Increased padding between Kanban cards and list action icons to prevent accidental taps.

- **Adaptive View Transformations**:
  - *Kanban Board*: Transforms from a horizontal multi-column layout into a single-column tabbed view (`[Backlog] [In Progress] [Review] [Done]`) with horizontal swipe gestures between columns.
  - *Code Diff Viewer*: Automatically toggles from Side-by-Side mode to Unified Single-Column Diff mode. File tree collapses into a top drop-down select element.
  - *Pipeline DAG*: Switches from horizontal node graph to vertical sequential timeline graph.

- **Network Resilience & Degradation**:
  - Mobile web client implements Service Worker caching for core UI shell and design tokens.
  - Real-time WebSocket connections gracefully degrade to HTTP long-polling on poor cellular connections.
  - Unsent user actions (approvals, chat prompts) are saved in local IndexedDB and processed automatically upon network restoration.


## 5. DESIGN SYSTEM

### 5.1 Typography

The typography of AegisOS is engineered for high legibility, strict vertical alignment, and maximum density during prolonged engineering sessions.

#### Font Family Stack
- **Primary Interface Font**: `Inter Variable`, `-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, `Roboto`, `sans-serif`.
  - Chosen for its exceptional screen legibility, neutral aesthetic, extensive font weight range, and optical size adjustments.
- **Monospace Code / Data Font**: `JetBrains Mono`, `Fira Code`, `ui-monospace`, `SFMono-Regular`, `Consolas`, `monospace`.
  - Custom font features enabled: Ligatures (`font-variant-ligatures: contextual`), tabular slash zero (`font-feature-settings: "zero"`). Used for code diffs, terminal outputs, JSON payloads, token readouts, and task IDs.

#### Type Scale Specification (8 Levels)

```css
/* AegisOS Design System Type Scale */
:root {
  --text-xs:   0.75rem;   /* 12px / Line Height: 1rem (16px)   / Tracking: +0.01em */
  --text-sm:   0.875rem;  /* 14px / Line Height: 1.25rem (20px)/ Tracking: 0      */
  --text-base: 1.0rem;    /* 16px / Line Height: 1.5rem (24px) / Tracking: -0.011em */
  --text-lg:   1.125rem;  /* 18px / Line Height: 1.75rem (28px)/ Tracking: -0.014em */
  --text-xl:   1.25rem;   /* 20px / Line Height: 1.75rem (28px)/ Tracking: -0.017em */
  --text-2xl:  1.5rem;    /* 24px / Line Height: 2.0rem (32px) / Tracking: -0.019em */
  --text-3xl:  2.0rem;    /* 32px / Line Height: 2.5rem (40px) / Tracking: -0.021em */
  --text-4xl:  3.0rem;    /* 48px / Line Height: 3.5rem (56px) / Tracking: -0.022em */
}
```

| Token Name | Size (px / rem) | Line Height | Font Weight Options | Usage & Hierarchy |
| :--- | :--- | :--- | :--- | :--- |
| `text-xs` | 12px / 0.75rem | 16px / 1.0rem | 400 (Regular), 500 (Medium), 600 (Semibold) | Table headers, badges, timestamps, micro labels, code line numbers |
| `text-sm` | 14px / 0.875rem | 20px / 1.25rem | 400 (Regular), 500 (Medium), 600 (Semibold) | Primary UI body text, table cells, form controls, sidebar items, log text |
| `text-base`| 16px / 1.0rem | 24px / 1.5rem | 400 (Regular), 500 (Medium), 600 (Semibold) | Card titles, article content, modal body text, primary chat messages |
| `text-lg` | 18px / 1.125rem | 28px / 1.75rem | 500 (Medium), 600 (Semibold) | Section headers, drawer titles, sub-heading elements |
| `text-xl` | 20px / 1.25rem | 28px / 1.75rem | 600 (Semibold), 700 (Bold) | Page headers, modal headers, major metric value displays |
| `text-2xl` | 24px / 1.5rem | 32px / 2.0rem | 600 (Semibold), 700 (Bold) | Major section titles, project dashboard titles |
| `text-3xl` | 32px / 2.0rem | 40px / 2.5rem | 700 (Bold) | Display KPI numbers, overview stat metrics |
| `text-4xl` | 48px / 3.0rem | 56px / 3.5rem | 700 (Bold), 800 (Extrabold) | Hero displays, high-impact marketing/onboarding titles |

#### Font Weights, Line Heights & Letter Spacing Rules
- **Regular (400)**: Used exclusively for body prose, long-form documentation, and descriptions.
- **Medium (500)**: Used for interactive controls, tab labels, button text, and table data.
- **Semibold (600)**: Used for section headers, card titles, badges, and active navigation indicators.
- **Bold (700)**: Used for primary page titles, display KPIs, and metric values.
- **Line Heights**: Formulated strictly to align with the 4px/8px baseline grid to eliminate text rendering jitter during component layout.

---

### 5.2 Spacing System

AegisOS employs a strict **4px / 8px Base Grid Unit** spacing architecture. All margins, padding, gap utility values, and component dimensions are integer multiples of 4px.

#### Spacing Scale Matrix

```css
/* AegisOS Design System Spacing Tokens */
:root {
  --space-0:     0px;
  --space-0-5:   2px;   /* 0.125rem */
  --space-1:     4px;   /* 0.25rem  */
  --space-1-5:   6px;   /* 0.375rem */
  --space-2:     8px;   /* 0.5rem   */
  --space-3:     12px;  /* 0.75rem  */
  --space-4:     16px;  /* 1.0rem   */
  --space-5:     20px;  /* 1.25rem  */
  --space-6:     24px;  /* 1.5rem   */
  --space-8:     32px;  /* 2.0rem   */
  --space-10:    40px;  /* 2.5rem   */
  --space-12:    48px;  /* 3.0rem   */
  --space-16:    64px;  /* 4.0rem   */
  --space-20:    80px;  /* 5.0rem   */
  --space-24:    96px;  /* 6.0rem   */
}
```

| Token Name | Value (px / rem) | Applied Layout Context |
| :--- | :--- | :--- |
| `--space-0-5` | 2px / 0.125rem | Micro borders, focus ring offsets, status dot positioning |
| `--space-1` | 4px / 0.25rem | Compact badge internal padding Y, tight icon-to-text gap |
| `--space-1-5` | 6px / 0.375rem | Standard badge padding Y, button compact padding Y |
| `--space-2` | 8px / 0.5rem | Button default padding Y, input field padding Y, card element gaps |
| `--space-3` | 12px / 0.75rem | Compact card padding, dropdown menu padding, button padding X |
| `--space-4` | 16px / 1.0rem | Standard card internal padding, table cell padding, grid gap default |
| `--space-6` | 24px / 1.5rem | Large card padding, modal content padding, main section gaps |
| `--space-8` | 32px / 2.0rem | Container padding desktop, major layout column separation |
| `--space-12` | 48px / 3.0rem | Top header height compact, drawer sidebar header padding |
| `--space-16` | 64px / 4.0rem | Global top bar height, hero container spacing |
| `--space-24` | 96px / 6.0rem | Maximum viewport margin spacing on ultra-wide monitors |

#### Layout Spacing Rules
1. **Component Padding Contract**: Buttons and input controls must always use symmetric horizontal padding (`--space-3` or `--space-4`) and strict vertical padding aligned to the 4px grid.
2. **Card Grid Gaps**: Grid layouts enforce `--space-4` (16px) on standard density views and `--space-6` (24px) on overview dashboards.
3. **Container Viewport Margins**: Main content viewport padding scales dynamically: `--space-4` on mobile (`<768px`), `--space-6` on tablet (`768-1024px`), and `--space-8` on desktop (`>1024px`).

---

### 5.3 Color Palette

AegisOS features a dark-first color space inspired by VS Code, Linear, and Vercel, optimized for high contrast, minimal eye strain, and vibrant semantic feedback. The brand accent is **Eco-Green (`#00ff88`)**.

#### Primary CSS Custom Properties (Dark Mode Spec)

```css
:root, [data-theme="dark"] {
  /* Core Backgrounds & Surfaces */
  --background:             #090a0f; /* Deep space dark base */
  --foreground:             #f0f3f8; /* Crisp off-white primary text */
  --card:                   #12141d; /* Elevated card surface */
  --card-foreground:        #f0f3f8; /* Card text */

  /* Brand Eco-Green Accent Palette */
  --primary:                #00ff88; /* Brand Eco-Green Accent */
  --primary-foreground:     #021a0e; /* Ultra-dark green text on primary */
  --primary-hover:          #00e67a; /* Slightly deeper green for hover */
  --primary-active:         #00cc6d; /* Pressed state green */
  --primary-subtle:         rgba(0, 255, 136, 0.10); /* 10% alpha fill */
  --primary-border:         #004d29; /* Dark green accent border */
  --primary-glow:           rgba(0, 255, 136, 0.25); /* Glowing shadow */

  /* Secondary & Muted Surfaces */
  --secondary:              #1a1e2e; /* Sub-surface elements / hover states */
  --secondary-foreground:    #d0d7e5; /* Secondary text */
  --muted:                  #1e2235; /* Muted background fill */
  --muted-foreground:        #8a93a8; /* Muted sub-text / placeholder */
  
  /* Interactive Accents & Focus */
  --accent:                 #00ff88; /* Eco-green brand accent */
  --accent-foreground:        #021a0e;
  --destructive:            #ff453a; /* High-alert error red */
  --destructive-foreground:   #ffffff;

  /* Borders & Inputs */
  --border:                 #23283b; /* Subtle card border */
  --input:                  #171a26; /* Form input surface */
  --ring:                   rgba(0, 255, 136, 0.50); /* Focus ring glow */
}
```

#### Light Mode Equivalents (Secondary Theme Spec)

```css
[data-theme="light"] {
  /* Core Backgrounds & Surfaces */
  --background:             #f8fafc; /* Slate light base */
  --foreground:             #0f172a; /* Dark slate text */
  --card:                   #ffffff; /* Pure white card surface */
  --card-foreground:        #0f172a;

  /* Brand Eco-Green Accent Palette (Adjusted for contrast) */
  --primary:                #00a859; /* Deeper eco-green for light mode readability */
  --primary-foreground:     #ffffff;
  --primary-hover:          #008f4c;
  --primary-active:         #00753e;
  --primary-subtle:         rgba(0, 168, 89, 0.10);
  --primary-border:         #a3e6cd;
  --primary-glow:           rgba(0, 168, 89, 0.20);

  /* Secondary & Muted Surfaces */
  --secondary:              #f1f5f9;
  --secondary-foreground:    #334155;
  --muted:                  #f1f5f9;
  --muted-foreground:        #64748b;

  /* Interactive Accents & Focus */
  --accent:                 #00a859;
  --accent-foreground:        #ffffff;
  --destructive:            #dc2626;
  --destructive-foreground:   #ffffff;

  /* Borders & Inputs */
  --border:                 #e2e8f0;
  --input:                  #f8fafc;
  --ring:                   rgba(0, 168, 89, 0.40);
}
```

#### Semantic Status Palette
- **Success**: Dark `#00ff88` / Light `#10b981` (Completed tasks, passing tests, clean builds).
- **Warning**: Dark `#ffb800` / Light `#f59e0b` (Pending approvals, high resource usage, non-blocking alerts).
- **Error / Destructive**: Dark `#ff453a` / Light `#ef4444` (Build failures, agent exceptions, security vulnerabilities).
- **Info**: Dark `#0a84ff` / Light `#3b82f6` (System announcements, active informational popovers).

#### Agent Status Palette

```
+----------------------------------------------------------------------------------+
| AGENT STATUS COLOR SPECIFICATION                                                  |
+-------------------+--------------------+------------------+----------------------+
| Status Identifier | HEX Code (Dark)    | Hex Code (Light) | Visual Indicator     |
+-------------------+--------------------+------------------+----------------------+
| Idle              | #8a93a8 (Slate)    | #64748b          | Solid Static Dot     |
| Busy / Executing  | #00ff88 (Eco Green)| #00a859          | Pulsing Radar Ring   |
| Error / Exception | #ff453a (Crimson)  | #dc2626          | Flashing Warning Dot |
| Offline / Unassigned| #48484a (Charcoal)| #94a3b8          | Hollow Gray Circle   |
| Waiting HITL      | #bf5af2 (Violet)   | #9333ea          | Glowing Pulse Ring   |
+-------------------+--------------------+------------------+----------------------+
```

---

### 5.4 Components

Comprehensive technical specification for 16 core AegisOS UI components.

#### 1. Card Component
- **Anatomy**: `CardContainer`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`.
- **CSS Spec**:
  - `background`: `var(--card)`;
  - `border`: `1px solid var(--border)`;
  - `border-radius`: `8px` (`0.5rem`);
  - `box-shadow`: `0 4px 12px rgba(0, 0, 0, 0.3)`;
- **States**: `Default`, `Hover` (border transitions to `var(--primary-border)`, slight Y lift of -1px), `Active`, `Focused` (outline `2px solid var(--ring)`).
- **Variants**: `Default` (bordered card), `Interactive` (clickable with hover elevation), `Subtle` (no border, muted background), `Glow` (brand green ambient shadow).

#### 2. Button Component
- **Anatomy**: `Button` -> `ButtonIconLeft`? + `ButtonText` + `ButtonIconRight`?.
- **Height Scale**: `sm` (32px), `md` (40px default), `lg` (48px).
- **Variants**:
  - `Primary`: `background: var(--primary); color: var(--primary-foreground); font-weight: 600;`
  - `Secondary`: `background: var(--secondary); color: var(--secondary-foreground); border: 1px solid var(--border);`
  - `Ghost`: `background: transparent; color: var(--foreground); hover: background: var(--muted);`
  - `Destructive`: `background: var(--destructive); color: var(--destructive-foreground);`
  - `Outline`: `background: transparent; border: 1px solid var(--primary); color: var(--primary);`
- **States**: `Default`, `Hover` (brightness boost 10%), `Active` (scale 0.98), `Disabled` (opacity 0.5, pointer-events: none), `Loading` (replaces left icon with spinning eco-green loader).

#### 3. Badge Component
- **Anatomy**: `BadgeContainer` -> `StatusDot`? + `BadgeLabel`.
- **Variants**: `Success` (green background fill 10%, green border), `Warning` (amber fill), `Error` (red fill), `Info` (blue fill), `Neutral` (slate fill), `Agent` (violet fill for HITL).
- **CSS Spec**: `border-radius: 9999px; padding: 2px 8px; font-size: 12px; font-weight: 500; font-family: JetBrains Mono;`

#### 4. Input / Textarea Component
- **Anatomy**: `InputWrapper` -> `InputIconLeft`? + `StyledInput` + `InputActionRight`?.
- **CSS Spec**: `background: var(--input); border: 1px solid var(--border); color: var(--foreground); border-radius: 6px; padding: 8px 12px;`
- **States**:
  - `Default`: Subtle border `#23283b`.
  - `Hover`: Border darkens to `#323850`.
  - `Focus`: Border transitions to `var(--primary)`, `box-shadow: 0 0 0 2px var(--ring)`.
  - `Error`: Border transitions to `var(--destructive)`.

#### 5. Table Component
- **Anatomy**: `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableCell`, `TableHead`.
- **Spec**: High-density engineering grid. Header sticky with `background: var(--card)`. Row height fixed to 40px. Alternating row background support (`var(--muted)` 30% alpha).
- **Interactions**: Row hover highlighting in `var(--secondary)`, row selection checkbox, sorting column indicator arrows.

#### 6. Modal / Dialog Component
- **Anatomy**: `DialogOverlay` (backdrop-filter blur 4px, background rgba(0,0,0,0.7)), `DialogContent` (max-width 560px, centered, animated scale up), `DialogHeader`, `DialogBody`, `DialogFooter`.
- **Accessibility**: Trap focus inside modal, close on `Escape` key, auto-focus primary action button.

#### 7. Tab / Segmented Control Component
- **Anatomy**: `TabList` -> `TabTrigger`[] + `TabIndicator` (animated layout spring sliding indicator).
- **Variants**: `Underline` (horizontal bar under active tab in `#00ff88`), `Pill / Segmented` (capsule background fill in `var(--secondary)`).

#### 8. Progress Bar Component
- **Anatomy**: `ProgressTrack` (background `var(--muted)`, height 6px, border-radius 9999px) -> `ProgressFill` (background `var(--primary)`, CSS transition on width).
- **Variants**: `Linear` (solid color fill), `Indeterminate` (animated shimmering gradient wave across track for active agent processing).

#### 9. Avatar & Agent Avatar Group Component
- **Anatomy**: `AvatarContainer` (32px x 32px, rounded-full) -> `AvatarImage` + `StatusIndicatorDot` (pulsing dot offset bottom-right).
- **Agent Avatar Distinctive Styling**: Agent avatars feature a distinct hexagonal clip-path or green glow ring to instantly distinguish them from human team members.

#### 10. Activity Feed Item Component
- **Anatomy**: `FeedItemRow` -> `Timestamp` + `AgentBadge` + `ActionDescription` + `ArtifactExpandButton`.
- **CSS Spec**: Left vertical continuous line in `var(--border)` connecting timeline nodes. Hovering an item highlights the execution step in `var(--secondary)`.

#### 11. Code Block Component
- **Anatomy**: `CodeBlockContainer` -> `CodeHeader` (Language pill, Copy Code button) + `CodeViewport` (Shiki syntax highlighted lines).
- **Spec**: Font family `JetBrains Mono`, background `#0c0e17`, line numbering gutter, highlighted code line background fill (`rgba(0, 255, 136, 0.08)`).

#### 12. Diff Viewer Component
- **Anatomy**: `DiffContainer` -> `DiffHeader` (File path, line count metrics `+14/-2`) + `DiffGutter` + `DiffLineContent`.
- **CSS Spec**:
  - Addition Line: `background: rgba(0, 255, 136, 0.12); color: #00ff88;`
  - Deletion Line: `background: rgba(255, 69, 58, 0.12); color: #ff453a;`
  - Hunk Header: `background: var(--secondary); color: var(--muted-foreground);`

#### 13. Chart Container Component
- **Anatomy**: `ChartWrapper` -> `ChartHeader` (Title, Metric Value, Period Selector) + `ChartCanvas` (Recharts / HTML5 Canvas container) + `ChartLegend`.
- **Spec**: Integrated grid lines in `var(--border)` (opacity 0.4), custom dark-mode SVG tooltips with `#00ff88` values.

#### 14. Kanban Column & Card Component
- **Anatomy**: `KanbanColumn` (Width 300px, background `var(--muted)` 50% opacity, rounded-lg) -> `ColumnHeader` (Title, Task Count Badge, `+` Add Button) + `CardList` (Vertical gap 8px).
- **Card Drag-and-Drop State**: Dragged card scaled 1.02, box-shadow `0 12px 24px rgba(0,0,0,0.5)`, drop target column highlighted with eco-green dashed border.

#### 15. Command Palette Component
- **Anatomy**: `PaletteOverlay` -> `PaletteModal` (Width 640px, top 15vh) -> `PaletteInput` (Icon + Input) + `ResultList` (Grouped by section: Actions, Files, Agents) + `PaletteFooter` (Keyboard shortcuts legend).

#### 16. Toast / Notification Banner Component
- **Anatomy**: `ToastContainer` (Bottom-right fixed) -> `ToastCard` -> `ToastIcon` + `ToastBody` (Title, Message) + `ToastCloseButton` + `ToastProgressBar`.
- **Variants**: `Success` (Eco-green border), `Error` (Red border), `Info` (Blue border), `Agent Message` (Violet border).

---

### 5.5 Icon System

AegisOS standardizes on **Lucide Icons** (`lucide-react`) for general system interface glyphs, supplemented by a custom SVG icon set tailored for AI agent execution concepts.

#### Icon Sizing Scale Matrix
- `icon-xs`: 12px x 12px (Micro inline indicators, table sorting arrows)
- `icon-sm`: 16px x 16px (Standard button icons, badge icons, input icons)
- `icon-md`: 20px x 20px (Default sidebar menu icons, section header icons)
- `icon-lg`: 24px x 24px (Page header icons, modal headers, metric card icons)
- `icon-xl`: 32px x 32px (Hero display icons, empty-state illustrations)

#### Stroke Width Guidelines
- Default UI Icons: `1.5px` stroke width for sleek modern clarity.
- Active / Focused Icons: `2.0px` stroke width to emphasize selection.

#### AegisOS Custom SVG Icon Set Specifications

```
1. icon-agent-mesh:
   Hexagonal interconnect network representing multi-agent swarms.
   SVG: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <polygon points="12 2 2 7 2 17 12 22 22 17 22 7 12 2"/>
          <circle cx="12" cy="12" r="3" fill="#00ff88"/>
        </svg>

2. icon-memory-node:
   Brain neural cluster intersecting a vector database matrix.
   Representing long-term vector memory indices.

3. icon-dag-workflow:
   Three directed acyclic graph nodes connected by directional arrows.
   Representing task decomposition execution trees.

4. icon-code-synth:
   Sparkle spark glyph intersecting code brackets `</ >`.
   Representing autonomous AI code synthesis.

5. icon-execution-node:
   Container pod glyph encircled by a continuous pulse loop.
   Representing active container runner environments.

6. icon-safety-shield:
   Shield glyph containing an inner biometric touch checkmark.
   Representing Human-in-the-Loop safety approval gates.
```

---

### 5.6 Animations & Micro-Interactions

Animations in AegisOS are designed to be fast, utilitarian, and informative—providing physical feedback for system state transitions without delaying developer execution.

#### Transition Duration Tokens

```css
/* AegisOS Motion Duration Specifications */
:root {
  --dur-fast:       75ms;   /* Instant feedback: button hover, checkbox toggle */
  --dur-normal:     150ms;  /* Standard UI transitions: dropdowns, tooltips */
  --dur-medium:     200ms;  /* Layout expansion: accordion, sidebar collapse */
  --dur-slow:       300ms;  /* Modal entrance, view page cross-fades */
  --dur-deliberate: 500ms;  /* Complex graph transitions, DAG node reorganizations */
}
```

#### Easing Timing Functions
- **Standard Ease-Out**: `cubic-bezier(0.16, 1, 0.3, 1)` - Smooth decelerating entry for modals, drawers, and menus.
- **Spring Elastic Bounce**: `cubic-bezier(0.34, 1.56, 0.64, 1)` - Applied to active tab sliding indicators and toast popups.
- **Linear Streaming**: `linear` - Used for continuous progress bars and streaming loading shimmers.

#### Loading States & Skeleton Shimmers
Components fetching data or waiting on initial agent streams display dark skeleton placeholder cards with a subtle eco-green sweeping shimmer gradient.

```css
@keyframes skeleton-shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.skeleton-card {
  background: linear-gradient(
    90deg,
    var(--card) 25%,
    rgba(0, 255, 136, 0.05) 37%,
    var(--card) 63%
  );
  background-size: 400% 100%;
  animation: skeleton-shimmer 1.8s ease-in-out infinite;
}
```

#### Live Agent Activity Animations
1. **Radar Beacon Pulse**: Active agent avatars display an outer radar ring pulsing infinitely (`@keyframes agent-pulse`: scale 1.0 to 1.6, opacity 0.8 to 0).
2. **Streaming Glowing Border**: Active agent feed cards feature a top-to-bottom eco-green glowing border gradient sweep (`@keyframes border-glow`).
3. **Live Agent Cursor Trails**: In collaborative code review, active agent cursors render with labeled flags (`@CodeSynth-Alpha`) and smooth position interpolation.

---

### 5.7 Dark Mode & Theme Management

While dark theme is the primary native interface for AegisOS, full theme switching is supported to accommodate variable ambient lighting conditions and accessibility guidelines.

#### Technical Implementation Architecture
Theme management is implemented using CSS custom property overrides driven by a root `data-theme` attribute on the `<html>` element.

```typescript
// AegisOS Theme Switcher Core Utility
type Theme = 'dark' | 'light' | 'system';

export function setTheme(theme: Theme) {
  const root = document.documentElement;
  if (theme === 'system') {
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.setAttribute('data-theme', systemDark ? 'dark' : 'light');
  } else {
    root.setAttribute('data-theme', theme);
  }
  localStorage.setItem('aegis-theme', theme);
}
```

#### Zero-FOUC (Flash of Unstyled Content) Mitigation
To eliminate white/dark flashes during initial page hydration, a lightweight blocking inline script is injected directly inside the HTML `<head>` before rendering:

```html
<script>
  (function() {
    var saved = localStorage.getItem('aegis-theme') || 'dark';
    var theme = saved === 'system' 
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') 
      : saved;
    document.documentElement.setAttribute('data-theme', theme);
  })();
</script>
```

#### WCAG AAA Contrast Ratio Audit Score Matrix
- **Primary Text (`#f0f3f8`) on Dark Base (`#090a0f`)**: Contrast Ratio **17.8:1** (Passes WCAG AAA).
- **Eco-Green Accent (`#00ff88`) on Dark Base (`#090a0f`)**: Contrast Ratio **14.2:1** (Passes WCAG AAA).
- **Muted Text (`#8a93a8`) on Card Surface (`#12141d`)**: Contrast Ratio **5.2:1** (Passes WCAG AA for standard text, AAA for large text).
- **Destructive Red (`#ff453a`) on Dark Base (`#090a0f`)**: Contrast Ratio **6.1:1** (Passes WCAG AA).

---

### 5.8 Responsive Layout & Grid Architecture

AegisOS delivers a responsive layout system structured on a 12-column dynamic flexbox and CSS Grid architecture.

#### Breakpoint Scale Specification Matrix

```css
/* AegisOS Breakpoint Definitions */
--breakpoint-sm:  640px;   /* Mobile Devices (Portrait / Landscape) */
--breakpoint-md:  768px;   /* Tablets & Small Laptops              */
--breakpoint-lg:  1024px;  /* Standard Desktop / Laptops           */
--breakpoint-xl:  1440px;  /* High-Resolution Wide Desktops        */
--breakpoint-2xl: 1920px;  /* Ultra-Wide Workstation Displays     */
```

| Breakpoint Identifier | Range (Width px) | Navigation Layout Behavior | Main Content Layout Behavior |
| :--- | :--- | :--- | :--- |
| **Mobile (`sm`)** | `< 768px` | Sidebar hidden, Bottom Tab Bar active, FAB for `Cmd+K` | 1-Column vertical stacking, tabbed Kanban, full-screen diff |
| **Tablet (`md`)** | `768px - 1023px` | Sidebar collapsed to 64px icon rail, header compact | 2-Column responsive grid, slide-over drawers |
| **Desktop (`lg`)** | `1024px - 1439px` | Full 240px Sidebar, persistent right console drawer | 12-Column grid default, split-pane code diff |
| **Wide Desktop (`xl`)**| `>= 1440px` | Unrestricted layout, dual-docked sidebars active | Multi-column dashboard grid, 3-pane code review, active DAG |

#### Grid System & Container Limits
- **12-Column Grid System**:
  - CSS Grid utility classes: `.grid-12 { display: grid; grid-template-columns: repeat(12, 1fr); gap: var(--space-4); }`
  - Column spans scale adaptively: `.col-span-12 .col-md-6 .col-lg-4 .col-xl-3`.
- **Container Max-Width Controls**:
  - Standard App Viewport: `max-width: 100%;` (Fluid edge-to-edge desktop utilization).
  - Documentation / ADR Content Container: `max-width: 860px;` (Enforces optimal reading line length of 65-75 characters).
  - Modal Dialog Containers: `sm` (400px), `md` (560px default), `lg` (800px), `xl` (1140px full diff inspector).

