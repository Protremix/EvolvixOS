# Contributing to EvolvixOS

> EvolvixOS is 100% open source. We welcome contributions from everyone.

## Ways to Contribute

### 1. Add a Skill 🧩
Skills are the core of EvolvixOS. Each skill is a Python module in `skills/` that follows this structure:

```
skills/your_skill/
├── __init__.py
└── skill.py      # Must implement the Skill class
```

**Minimal skill template:**
```python
"""EvolvixOS Skill — Your Skill Name"""
from rich.console import Console
console = Console()


class Skill:
    def __init__(self, config=None):
        self.config = config or {}
        self.name = "your_skill"

    def run(self, args: dict) -> str:
        action = args.get("action", "default")
        # Your logic here
        return "Result"
```

Submit a PR with your skill. It will be auto-discovered by the agent.

### 2. Improve the Agent Core 🧠
The agent loop lives in `agent/core.py`. Improvements to:
- Planning and reasoning quality
- Self-reflection accuracy
- Skill routing decisions
- Memory and context management

### 3. Add GitHub Discovery Topics 🔍
Found a great GitHub topic with AI tools? Add it to `skills/github_discovery/skill.py` in the `search_topics` list.

### 4. Improve Documentation 📝
- Fix typos, add examples, improve clarity
- Write tutorials in `docs/`
- Add architecture diagrams

### 5. Report Bugs 🐛
Open an issue with:
- What you expected
- What happened
- Steps to reproduce
- Your OS and Python version

## Development Setup

```bash
git clone https://github.com/Protremix/EvolvixOS.git
cd EvolvixOS
pip install -r requirements.txt
./setup.sh
python main.py
```

## Coding Standards

- **Python 3.10+**
- Type hints where possible
- Docstrings on all public functions
- Keep skills modular and self-contained
- Zero external API calls — everything must run locally
- Test your changes before submitting

## Pull Request Process

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/amazing-skill`
3. Commit with clear messages
4. Test locally: `python main.py "test your feature"`
5. Open a PR — describe what you added and why

## Core Principle

**Zero tokens. Zero external APIs. Zero cloud dependencies.**

Everything in EvolvixOS must work on a machine with no internet connection (after initial setup). If your contribution requires an API key or external service, it won't be accepted. Use local models (Ollama), local tools, and open-source libraries only.
