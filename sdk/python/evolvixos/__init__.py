"""
EvolvixOS Python SDK
Self-hostable AI engineering platform — 435+ models, one API.

    from evolvixos import EvolvixOS

    client = EvolvixOS(api_key="your-key", base_url="https://evolvixos.com")

    # Chat with any model
    resp = client.chat("Write a haiku about code")
    print(resp["response"])

    # Create entities
    client.entities.create("Task", {
        "title": {"type": "string"},
        "status": {"type": "string", "enum": ["todo", "done"]}
    })

    # Create records
    client.entities.records("Task").create({"title": "Ship it", "status": "todo"})

    # Create agents
    client.agents.create("code-reviewer", system_prompt="You are a code reviewer")

    # Stream responses
    for chunk in client.stream("Tell me a story"):
        print(chunk, end="", flush=True)
"""

from .client import EvolvixOS

__version__ = "1.0.0"
__all__ = ["EvolvixOS"]
