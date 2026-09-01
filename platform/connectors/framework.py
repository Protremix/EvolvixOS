"""
Connector Framework — External service integrations for EvolvixOS.

Provides a unified interface for connecting to developer tools:
  - Vercel (deployments, projects)
  - Supabase (database, auth, storage)
  - Slack (notifications, approvals)
  - Docker Hub (container management)
  - Hugging Face (model hub)
  - Linear (issue tracking)
  - Generic webhook (any HTTP service)
"""

import json
import os
import urllib.request
import urllib.error
import logging
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod

logger = logging.getLogger("connectors")


class BaseConnector(ABC):
    """Base class for all connectors."""
    name: str = "base"
    display_name: str = "Base Connector"
    auth_type: str = "api_key"
    required_env: List[str] = []
    capabilities: List[str] = []

    def __init__(self, credentials: Optional[dict] = None):
        self.credentials = credentials or self._load_credentials()
        self._validate_credentials()

    def _load_credentials(self) -> dict:
        creds = {}
        for env_var in self.required_env:
            val = os.environ.get(env_var)
            if val:
                creds[env_var] = val
        return creds

    def _validate_credentials(self):
        missing = [v for v in self.required_env if v not in self.credentials]
        if missing:
            logger.warning(f"Connector '{self.name}' missing credentials: {missing}")
            self._available = False
        else:
            self._available = True

    @property
    def available(self) -> bool:
        return self._available

    def _request(self, method, url, headers=None, data=None, timeout=30):
        all_headers = {"Content-Type": "application/json"}
        if headers:
            all_headers.update(headers)
        payload = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=payload, method=method, headers=all_headers)
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            body = resp.read().decode()
            return json.loads(body) if body else {"status": "ok"}
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            return {"error": True, "status": e.code, "message": body[:500]}
        except Exception as e:
            return {"error": True, "message": str(e)}

    @abstractmethod
    async def execute(self, action: str, params: dict) -> dict:
        pass

    def info(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "auth_type": self.auth_type,
            "available": self.available,
            "capabilities": self.capabilities,
        }


class VercelConnector(BaseConnector):
    name = "vercel"
    display_name = "Vercel"
    required_env = ["VERCEL_TOKEN"]
    capabilities = ["list_projects", "get_project", "list_deployments",
                    "create_deployment", "get_deployment", "delete_deployment",
                    "list_env_vars", "set_env_var"]
    BASE_URL = "https://api.vercel.com/v1"

    def _auth_headers(self):
        token = self.credentials.get("VERCEL_TOKEN", "")
        return {"Authorization": "Bearer " + token}

    async def execute(self, action, params):
        headers = self._auth_headers()
        if action == "list_projects":
            return self._request("GET", self.BASE_URL + "/projects?limit=" + str(params.get("limit", 20)), headers=headers)
        elif action == "get_project":
            return self._request("GET", self.BASE_URL + "/projects/" + params.get("project_id", ""), headers=headers)
        elif action == "list_deployments":
            return self._request("GET", self.BASE_URL + "/deployments?projectId=" + params.get("project_id", "") + "&limit=" + str(params.get("limit", 20)), headers=headers)
        elif action == "create_deployment":
            return self._request("POST", self.BASE_URL + "/deployments", headers=headers, data=params)
        elif action == "get_deployment":
            return self._request("GET", self.BASE_URL + "/deployments/" + params.get("deployment_id", ""), headers=headers)
        elif action == "delete_deployment":
            return self._request("DELETE", self.BASE_URL + "/deployments/" + params.get("deployment_id", ""), headers=headers)
        elif action == "list_env_vars":
            return self._request("GET", self.BASE_URL + "/projects/" + params.get("project_id", "") + "/env", headers=headers)
        elif action == "set_env_var":
            return self._request("POST", self.BASE_URL + "/projects/" + params.get("project_id", "") + "/env", headers=headers,
                                 data={"key": params.get("key", ""), "value": params.get("value", ""),
                                       "type": "encrypted", "target": params.get("target", ["production"])})
        return {"error": True, "message": "Unknown action: " + action}


class SupabaseConnector(BaseConnector):
    name = "supabase"
    display_name = "Supabase"
    required_env = ["SUPABASE_ACCESS_TOKEN"]
    capabilities = ["list_projects", "get_project", "create_project", "run_sql"]
    BASE_URL = "https://api.supabase.com/v1"

    def _auth_headers(self):
        token = self.credentials.get("SUPABASE_ACCESS_TOKEN", "")
        return {"Authorization": "Bearer " + token}

    async def execute(self, action, params):
        headers = self._auth_headers()
        if action == "list_projects":
            return self._request("GET", self.BASE_URL + "/projects", headers=headers)
        elif action == "get_project":
            return self._request("GET", self.BASE_URL + "/projects/" + params.get("project_id", ""), headers=headers)
        elif action == "create_project":
            return self._request("POST", self.BASE_URL + "/projects", headers=headers, data=params)
        elif action == "run_sql":
            project_id = params.get("project_id", "")
            return self._request("POST", self.BASE_URL + "/projects/" + project_id + "/database/query",
                                 headers=headers, data={"query": params.get("query", "")})
        return {"error": True, "message": "Unknown action: " + action}


class SlackConnector(BaseConnector):
    name = "slack"
    display_name = "Slack"
    required_env = ["SLACK_BOT_TOKEN"]
    capabilities = ["send_message", "list_channels", "create_channel", "get_history", "send_approval"]
    BASE_URL = "https://slack.com/api"

    def _auth_headers(self):
        token = self.credentials.get("SLACK_BOT_TOKEN", "")
        return {"Authorization": "Bearer " + token}

    async def execute(self, action, params):
        headers = self._auth_headers()
        if action == "send_message":
            return self._request("POST", self.BASE_URL + "/chat.postMessage", headers=headers,
                                 data={"channel": params.get("channel", "#general"),
                                       "text": params.get("text", ""), "blocks": params.get("blocks", [])})
        elif action == "list_channels":
            return self._request("GET", self.BASE_URL + "/conversations.list?limit=" + str(params.get("limit", 100)), headers=headers)
        elif action == "create_channel":
            return self._request("POST", self.BASE_URL + "/conversations.create", headers=headers,
                                 data={"name": params.get("name", "")})
        elif action == "get_history":
            return self._request("GET", self.BASE_URL + "/conversations.history?channel=" + params.get("channel", "") + "&limit=" + str(params.get("limit", 50)), headers=headers)
        elif action == "send_approval":
            blocks = [
                {"type": "section", "text": {"type": "mrkdwn", "text": "*Approval Request*\n" + params.get("text", "")}},
                {"type": "actions", "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "style": "primary", "value": "approve"},
                    {"type": "button", "text": {"type": "plain_text", "text": "Reject"}, "style": "danger", "value": "reject"},
                ]}
            ]
            return self._request("POST", self.BASE_URL + "/chat.postMessage", headers=headers,
                                 data={"channel": params.get("channel", "#approvals"),
                                       "text": "Approval: " + params.get("text", ""), "blocks": blocks})
        return {"error": True, "message": "Unknown action: " + action}


class DockerHubConnector(BaseConnector):
    name = "docker_hub"
    display_name = "Docker Hub"
    required_env = ["DOCKERHUB_USERNAME", "DOCKERHUB_TOKEN"]
    capabilities = ["list_repositories", "get_repository", "list_tags"]
    BASE_URL = "https://hub.docker.com/v2"

    async def execute(self, action, params):
        if action == "list_repositories":
            return self._request("GET", self.BASE_URL + "/repositories/" + self.credentials.get("DOCKERHUB_USERNAME", "") + "/?page_size=" + str(params.get("limit", 20)))
        elif action == "get_repository":
            return self._request("GET", self.BASE_URL + "/repositories/" + params.get("repo", ""))
        elif action == "list_tags":
            return self._request("GET", self.BASE_URL + "/repositories/" + params.get("repo", "") + "/tags?page_size=" + str(params.get("limit", 20)))
        return {"error": True, "message": "Unknown action: " + action}


class HuggingFaceConnector(BaseConnector):
    name = "huggingface"
    display_name = "Hugging Face"
    required_env = ["HF_TOKEN"]
    capabilities = ["search_models", "get_model", "list_datasets"]
    BASE_URL = "https://huggingface.co/api"

    def _auth_headers(self):
        token = self.credentials.get("HF_TOKEN", "")
        return {"Authorization": "Bearer " + token}

    async def execute(self, action, params):
        headers = self._auth_headers()
        if action == "search_models":
            return self._request("GET", self.BASE_URL + "/models?search=" + params.get("query", "") + "&limit=" + str(params.get("limit", 20)))
        elif action == "get_model":
            return self._request("GET", self.BASE_URL + "/models/" + params.get("model_id", ""), headers=headers)
        elif action == "list_datasets":
            return self._request("GET", self.BASE_URL + "/datasets?search=" + params.get("query", "") + "&limit=" + str(params.get("limit", 20)))
        return {"error": True, "message": "Unknown action: " + action}


class LinearConnector(BaseConnector):
    name = "linear"
    display_name = "Linear"
    required_env = ["LINEAR_API_KEY"]
    capabilities = ["list_issues", "create_issue", "list_teams"]
    BASE_URL = "https://api.linear.app/graphql"

    def _auth_headers(self):
        return {"Authorization": self.credentials.get("LINEAR_API_KEY", "")}

    async def execute(self, action, params):
        headers = self._auth_headers()
        if action == "list_teams":
            return self._request("POST", self.BASE_URL, headers=headers, data={"query": "{ teams { nodes { id name key } } }"})
        elif action == "create_issue":
            team_id = params.get("team_id", "")
            title = params.get("title", "")
            return self._request("POST", self.BASE_URL, headers=headers,
                                 data={"query": 'mutation { issueCreate(input: { teamId: "' + team_id + '", title: "' + title + '" }) { success issue { id } } }'})
        return {"error": True, "message": "Unknown action: " + action}


class WebhookConnector(BaseConnector):
    name = "webhook"
    display_name = "Webhook"
    required_env = []
    capabilities = ["send", "get", "post", "put", "delete"]

    async def execute(self, action, params):
        url = params.get("url", "")
        headers = params.get("headers", {})
        data = params.get("data", {})
        method = action.upper() if action in ["get", "post", "put", "delete"] else "POST"
        return self._request(method, url, headers=headers, data=data if method != "GET" else None)


class ConnectorRegistry:
    """Registry for all connectors."""
    _connector_classes: Dict[str, type] = {
        "vercel": VercelConnector,
        "supabase": SupabaseConnector,
        "slack": SlackConnector,
        "docker_hub": DockerHubConnector,
        "huggingface": HuggingFaceConnector,
        "linear": LinearConnector,
        "webhook": WebhookConnector,
    }

    @classmethod
    def list_connectors(cls) -> List[dict]:
        result = []
        for name, cls_ in cls._connector_classes.items():
            try:
                conn = cls_()
                result.append(conn.info())
            except Exception:
                result.append({"name": name, "display_name": cls_.display_name,
                               "available": False, "capabilities": cls_.capabilities})
        return result

    @classmethod
    async def execute(cls, connector_name: str, action: str, params: dict) -> dict:
        cls_ = cls._connector_classes.get(connector_name)
        if not cls_:
            return {"error": True, "message": "Unknown connector: " + connector_name}
        conn = cls_()
        if not conn.available:
            return {"error": True, "message": "Connector '" + connector_name + "' not configured. Set env vars: " + str(conn.required_env)}
        return await conn.execute(action, params)

    @classmethod
    def register(cls, name: str, connector_class: type):
        cls._connector_classes[name] = connector_class
