"""EvolvixOS Python SDK Client"""
import requests
import json
from typing import Optional, Dict, Any, Iterator


class EvolvixOS:
    """Client for the EvolvixOS platform API."""

    def __init__(self, api_key: str, base_url: str = "https://evolvixos.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.entities = _Entities(self)
        self.agents = _Agents(self)
        self.functions = _Functions(self)
        self.workflows = _Workflows(self)

    def _post(self, path: str, data: dict) -> dict:
        resp = requests.post(f"{self.base_url}/platform/api{path}", json=data, headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def _get(self, path: str, params: dict = None) -> dict:
        resp = requests.get(f"{self.base_url}/platform/api{path}", headers=self._headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def chat(self, message: str, model: str = "auto", system: str = None,
             temperature: float = 0.7, max_tokens: int = 1000) -> dict:
        """Send a message and get a response."""
        data = {"message": message, "model": model, "temperature": temperature, "max_tokens": max_tokens}
        if system:
            data["system_prompt"] = system
        return self._post("/playground", data)

    def stream(self, message: str, model: str = "auto", system: str = None,
               temperature: float = 0.7, max_tokens: int = 1000) -> Iterator[str]:
        """Stream a response via SSE. Yields text chunks."""
        data = {"message": message, "model": model, "temperature": temperature, "max_tokens": max_tokens}
        if system:
            data["system_prompt"] = system
        resp = requests.post(f"{self.base_url}/platform/api/playground/stream",
                             json=data, headers=self._headers, stream=True)
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line and line.startswith(b"data: "):
                chunk = json.loads(line[6:])
                if chunk.get("done"):
                    break
                if chunk.get("chunk"):
                    yield chunk["chunk"]

    def models(self, category: str = None) -> list:
        """List all available models."""
        params = {"category": category} if category else {}
        return self._get("/models", params).get("models", [])

    def credits(self) -> dict:
        """Check credit balance."""
        return self._get("/credits")

    def health(self) -> dict:
        """Check platform health."""
        return self._get("/health")


class _Entities:
    def __init__(self, client):
        self.client = client

    def create(self, name: str, schema: dict) -> dict:
        """Create a new entity (database table)."""
        return self.client._post("/entities", {"name": name, "schema": schema})

    def list(self) -> list:
        """List all entities."""
        return self.client._get("/entities").get("entities", [])

    def records(self, entity_name: str) -> "_Records":
        return _Records(self.client, entity_name)


class _Records:
    def __init__(self, client, entity_name):
        self.client = client
        self.name = entity_name

    def create(self, data: dict) -> dict:
        return self.client._post(f"/entities/{self.name}/records", data)

    def list(self, limit: int = 50, skip: int = 0) -> dict:
        return self.client._get(f"/entities/{self.name}/records", {"limit": limit, "skip": skip})

    def get(self, record_id: str) -> dict:
        return self.client._get(f"/entities/{self.name}/records/{record_id}")

    def update(self, record_id: str, data: dict) -> dict:
        return self.client._post(f"/entities/{self.name}/records/{record_id}", data)

    def delete(self, record_id: str) -> dict:
        resp = requests.delete(f"{self.client.base_url}/platform/api/entities/{self.name}/records/{record_id}",
                              headers=self.client._headers)
        resp.raise_for_status()
        return resp.json()


class _Agents:
    def __init__(self, client):
        self.client = client

    def create(self, name: str, system_prompt: str, model: str = "auto") -> dict:
        return self.client._post("/agents", {"name": name, "system_prompt": system_prompt, "model": model})

    def list(self) -> list:
        return self.client._get("/agents").get("agents", [])

    def chat(self, name: str, message: str) -> dict:
        return self.client._post(f"/agents/{name}/chat", {"message": message})


class _Functions:
    def __init__(self, client):
        self.client = client

    def deploy(self, name: str, code: str) -> dict:
        return self.client._post("/functions", {"name": name, "code": code})

    def call(self, name: str, data: dict = None) -> dict:
        return self.client._post(f"/fn/{name}", data or {})

    def list(self) -> list:
        return self.client._get("/functions").get("functions", [])


class _Workflows:
    def __init__(self, client):
        self.client = client

    def create(self, name: str, trigger_type: str, definition: dict, schedule: str = None) -> dict:
        data = {"name": name, "trigger_type": trigger_type, "definition": definition}
        if schedule:
            data["schedule"] = schedule
        return self.client._post("/workflows", data)

    def list(self) -> list:
        return self.client._get("/workflows").get("workflows", [])
