
"""EvolvixOS Vercel Integration — deploy generated apps to Vercel."""
import httpx
import json
import os
import asyncio
from datetime import datetime

VERCEL_API = "https://api.vercel.com"

async def vercel_request(method, path, token, body=None):
    """Make an authenticated Vercel API request."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"{VERCEL_API}{path}"
        if method == "GET":
            r = await client.get(url, headers=headers)
        elif method == "POST":
            r = await client.post(url, headers=headers, json=body)
        elif method == "DELETE":
            r = await client.delete(url, headers=headers)
        return {"status": r.status_code, "data": r.json() if r.text else {}}

async def connect_vercel(token):
    """Verify a Vercel access token and store it."""
    result = await vercel_request("GET", "/v2/user", token)
    if result["status"] == 200:
        user = result["data"].get("user", {})
        return {
            "connected": True,
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "message": f"Connected as {user.get('username', 'unknown')}"
        }
    return {"connected": False, "error": "Invalid token or Vercel API error"}

async def list_vercel_projects(token):
    """List all Vercel projects."""
    result = await vercel_request("GET", "/v9/projects?limit=100", token)
    if result["status"] == 200:
        projects = result["data"].get("projects", [])
        return [{
            "id": p.get("id"),
            "name": p.get("name"),
            "framework": p.get("framework"),
            "latestDeployment": p.get("latestDeployment", {}).get("url", ""),
            "createdAt": p.get("createdAt", ""),
            "updatedAt": p.get("updatedAt", "")
        } for p in projects]
    return []

async def list_vercel_deployments(token, project_id=None, limit=10):
    """List recent deployments."""
    path = f"/v6/deployments?limit={limit}"
    if project_id:
        path += f"&projectId={project_id}"
    result = await vercel_request("GET", path, token)
    if result["status"] == 200:
        deployments = result["data"].get("deployments", [])
        return [{
            "id": d.get("id"),
            "url": d.get("url"),
            "state": d.get("state"),
            "target": d.get("target"),
            "createdAt": d.get("createdAt"),
            "meta": d.get("meta", {})
        } for d in deployments]
    return []

async def deploy_to_vercel(token, project_name, files, framework=None):
    """Create a new deployment on Vercel.
    
    files: list of {"file": "path/to/file", "data": "file content"}
    """
    # First create or find the project
    projects = await list_vercel_projects(token)
    project = next((p for p in projects if p["name"] == project_name), None)
    
    if not project:
        # Create the project
        result = await vercel_request("POST", "/v11/projects", token, {
            "name": project_name,
            "framework": framework
        })
        if result["status"] != 200:
            return {"error": f"Failed to create project: {result['data']}"}
        project = result["data"]
    
    # Create deployment
    deployment_body = {
        "name": project_name,
        "files": [{"file": f["file"], "data": f["data"]} for f in files],
        "target": "production"
    }
    if framework:
        deployment_body["projectSettings"] = {"framework": framework}
    
    result = await vercel_request("POST", "/v13/deployments", token, deployment_body)
    if result["status"] in [200, 201]:
        dep = result["data"]
        return {
            "url": f"https://{dep.get('url', '')}",
            "id": dep.get("id"),
            "state": dep.get("state", "queued"),
            "project": project_name
        }
    return {"error": f"Deployment failed: {result['data']}"}

async def get_vercel_deployment_status(token, deployment_id):
    """Check deployment status."""
    result = await vercel_request("GET", f"/v13/deployments/{deployment_id}", token)
    if result["status"] == 200:
        dep = result["data"]
        return {
            "id": dep.get("id"),
            "url": dep.get("url"),
            "state": dep.get("readyState", dep.get("state")),
            "target": dep.get("target")
        }
    return {"error": "Could not fetch deployment status"}
