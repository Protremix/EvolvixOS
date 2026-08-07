"""GitHub integration service shim for health check."""
import os

def get_github_client():
    """Return a GitHub client if configured, else raise."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set")
    return token
