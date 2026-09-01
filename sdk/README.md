# EvolvixOS Python SDK

Python client for the EvolvixOS AI engineering platform.

## Install

```bash
pip install evolvixos
```

## Quick Start

```python
from evolvixos import EvolvixOS

client = EvolvixOS(api_key="your-api-key", base_url="https://evolvixos.com")

# Chat with any of 435+ models
resp = client.chat("Write a haiku about code", model="auto")
print(resp["response"])

# Stream responses
for chunk in client.stream("Tell me a story"):
    print(chunk, end="", flush=True)

# List models
models = client.models()
print(f"{len(models)} models available")

# Create database entities
client.entities.create("Task", {
    "title": {"type": "string"},
    "status": {"type": "string", "enum": ["todo", "doing", "done"]}
})

# Create records
client.entities.records("Task").create({"title": "Ship it", "status": "doing"})

# List records
tasks = client.entities.records("Task").list()
print(tasks)

# Create AI agents
client.agents.create("reviewer", system_prompt="You are a code reviewer")
resp = client.agents.chat("reviewer", "Review: def fib(n): return fib(n-1)+fib(n-2)")
print(resp["response"])

# Deploy backend functions
client.functions.deploy("getWeather", "def handler(input): return {'temp': 22}")
result = client.functions.call("getWeather", {"city": "Madrid"})

# Check credits
print(client.credits())
```

## API Reference

| Method | Description |
|--------|-------------|
| `client.chat(message, model="auto")` | Chat with any model |
| `client.stream(message, model="auto")` | Stream response (generator) |
| `client.models()` | List all models |
| `client.credits()` | Check credit balance |
| `client.health()` | Platform health check |
| `client.entities.create(name, schema)` | Create database table |
| `client.entities.list()` | List all tables |
| `client.entities.records(name).create(data)` | Create record |
| `client.entities.records(name).list()` | List records |
| `client.agents.create(name, system_prompt)` | Create AI agent |
| `client.agents.chat(name, message)` | Chat with agent |
| `client.functions.deploy(name, code)` | Deploy function |
| `client.functions.call(name, data)` | Call function |
| `client.workflows.create(name, ...)` | Create workflow |

License: MIT
