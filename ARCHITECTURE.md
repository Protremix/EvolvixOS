# EvolvixOS Architecture

## Overview

EvolvixOS is a 100% local, open-source AI agent system. It uses Ollama for LLM inference (zero tokens) and a modular skill system for capabilities. It gets smarter by discovering and learning from open-source tools on GitHub.

## Core Design Principles

1. **Zero tokens** — No external API calls, no cloud, no paid services
2. **Fully local** — Everything runs on your hardware
3. **Modular skills** — Each capability is a self-contained skill module
4. **Self-extending** — Discovers and learns from new GitHub tools automatically
5. **Privacy-first** — Your data never leaves your machine

## System Architecture

```
                    ┌──────────────────────────────────┐
                    │          User / External App       │
                    │  (CLI / Web UI / API / Voice)     │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │          Agent Core               │
                    │  (Think → Plan → Act → Observe    │
                    │   → Reflect → Loop)               │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │          Skill Router              │
                    │  (Built-in + GitHub-installed)    │
                    └──────────────┬───────────────────┘
                                   │
          ┌────────────┬───────────┼───────────┬────────────┐
          ▼            ▼           ▼           ▼            ▼
     ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
     │Research│  │Coding  │  │Video   │  │GitHub  │  │  ...   │
     │Skill   │  │Skill   │  │Skill   │  │Discov. │  │  Skills│
     └────────┘  └────────┘  └────────┘  └────────┘  └────────┘
          │            │           │           │
          ▼            ▼           ▼           ▼
     ┌──────────────────────────────────────────────┐
     │              Ollama (Local LLM)                │
     │  deepseek-r1 | qwen2.5-coder | llama3.2      │
     └──────────────────────────────────────────────┘
          │
          ▼
     ┌──────────────────────────────────────────────┐
     │              Memory (SQLite)                  │
     │  Conversations | Tasks | Learned Knowledge   │
     └──────────────────────────────────────────────┘
```

## Agent Loop

The agent core (`agent/core.py`) runs a ReAct-style loop:

1. **PERCEIVE** — Receive user request or continue from previous step
2. **THINK** — LLM reasons about the task and decides what skill to use
3. **ACT** — Execute a skill via `<skill name="...">...</skill>` XML tags
4. **OBSERVE** — Review the skill's output
5. **REFLECT** — Self-assess whether the result was good (optional)
6. **LOOP** — Continue until the agent says COMPLETE or max steps reached

## Skill System

### Built-in Skills
Located in `skills/<name>/skill.py`. Each implements a `Skill` class with a `run(args: dict) -> str` method.

| Skill | What it does |
|-------|-------------|
| `research` | Web search via SearXNG, scraping, deep research reports |
| `coding` | Generate, execute, and debug code |
| `video` | Text-to-video generation (Wan 2.1, AnimateDiff) |
| `audio` | Text-to-speech (Kokoro) and music generation (MusicGen) |
| `image` | Text-to-image generation (FLUX.1, Stable Diffusion) |
| `voice` | Speech-to-text (Whisper) and text-to-speech (Kokoro) |
| `project_learner` | Scan and understand any codebase |
| `github_discovery` | Find, install, and learn from GitHub AI tools |
| `deploy` | SSH deployment to any server |

### GitHub-Installed Skills
Auto-generated wrappers (`evolvix_skill.py`) for repos discovered on GitHub. The agent can use them like built-in skills.

### Skill Interface
```python
class Skill:
    def __init__(self, config: dict = None): ...
    def run(self, args: dict) -> str: ...
```

The agent calls skills using XML in its LLM response:
```
<skill name="research">{"action": "search", "query": "quantum computing"}</skill>
```

## GitHub Discovery Engine

The GitHub discovery engine (`skills/github_discovery/skill.py`) is what makes EvolvixOS unique:

1. **DISCOVER** — Searches GitHub API across 50+ topics for open-source AI tools
2. **INSTALL** — `git clone` repos with 100+ stars into `skills/github_<name>/`
3. **LEARN** — Local LLM studies the repo's source code and README
4. **USE** — Agent can invoke any learned skill in its workflow
5. **UPDATE** — Periodically pulls updates from GitHub

This means EvolvixOS gets smarter every time new AI tools are published on GitHub.

## Memory System

Local SQLite database (`data/evolvix_memory.db`) stores:
- User requests and task results
- Conversation history
- Learned skill knowledge
- GitHub discovery registry

## API Server

The REST API server (`api_server.py`) runs on port 5001 and exposes:
- Chat (with streaming SSE support)
- Voice (speech-to-text, text-to-speech)
- Project loading and representation
- System status and memory search

External projects connect using `evolvix_client.py` — a single-file SDK.

## Deployment

### Docker
One command: `docker-compose up`
- EvolvixOS container (Python + Ollama + skills)
- SearXNG container (local search engine)

### Manual
```bash
./setup.sh && python main.py
```

## Data Flow

```
User Request
    ↓
Agent Core (LLM reasoning)
    ↓
Skill Selection (based on task type)
    ↓
Skill Execution (local computation)
    ↓
Result → Agent Core (observation)
    ↓
Memory Store (persistent)
    ↓
Response to User
```

## Extension Points

1. **Add a skill** — Drop a Python module in `skills/`
2. **Add a GitHub topic** — Add to `search_topics` in the discovery engine
3. **Add an LLM** — Pull a new model in Ollama, update `config.yaml`
4. **Add an API endpoint** — Add a route in `api_server.py`
