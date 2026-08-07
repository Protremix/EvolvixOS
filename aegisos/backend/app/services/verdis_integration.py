"""Verdis integration service shim for health check."""
import os
import httpx

class VerdisIntegration:
    """Lightweight wrapper for the Verdis blockchain API."""
    def __init__(self):
        self.base_url = os.getenv("VERDIS_API_URL", "http://localhost:3200/api")
    
    def get_chain_info(self):
        try:
            r = httpx.get(f"{self.base_url}/blockchain/info", timeout=5)
            return r.json()
        except Exception:
            return None
    
    def is_healthy(self) -> bool:
        info = self.get_chain_info()
        return info is not None and info.get("chainValid", False)
