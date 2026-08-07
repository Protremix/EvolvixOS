"""
Documentation & Deployment Manifests — Phase 51

Comprehensive documentation compilation, deployment manifests,
API reference generation, and knowledge base management.
"""

import secrets
import time
import json
import os
import threading
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from app.core.logging import get_logger

logger = get_logger("service.deployment_docs")


class DocCategory(str, Enum):
    ARCHITECTURE = "architecture"
    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    DEPLOYMENT = "deployment"
    TROUBLESHOOTING = "troubleshooting"
    FAQ = "faq"
    RUNBOOK = "runbook"
    WHITEPAPER = "whitepaper"


class DocStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    OUTDATED = "outdated"


class ManifestType(str, Enum):
    DOCKER_COMPOSE = "docker-compose"
    KUBERNETES = "kubernetes"
    SYSTEMD = "systemd"
    NGINX = "nginx"
    ENV_TEMPLATE = "env-template"
    DOCKERFILE = "dockerfile"


@dataclass
class DocEntry:
    id: str
    title: str
    category: str
    description: str
    content: str = ""
    version: str = "1.0.0"
    status: str = DocStatus.PUBLISHED.value
    author: str = "EvolvixOS"
    tags: list = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    word_count: int = 0
    sections: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DeploymentManifest:
    id: str
    name: str
    type: str
    component: str
    filename: str
    content: str = ""
    description: str = ""
    env_vars: list = field(default_factory=list)
    dependencies: list = field(default_factory=list)
    port: int = 0
    health_check: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FAQEntry:
    id: str
    question: str
    answer: str
    category: str = "general"
    helpful_count: int = 0
    tags: list = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RunbookEntry:
    id: str
    name: str
    scenario: str
    severity: str = "medium"
    steps: list = field(default_factory=list)
    rollback_steps: list = field(default_factory=list)
    estimated_time: str = ""
    owner: str = "DevOps"
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class DeploymentDocsService:
    """Documentation and deployment manifest management."""

    def __init__(self):
        self._docs: dict[str, DocEntry] = {}
        self._manifests: dict[str, DeploymentManifest] = {}
        self._faqs: dict[str, FAQEntry] = {}
        self._runbooks: dict[str, RunbookEntry] = {}
        self._lock = threading.Lock()
        self._init_docs()
        self._init_manifests()
        self._init_faqs()
        self._init_runbooks()

    def _init_docs(self):
        """Initialize comprehensive documentation."""
        docs_data = [
            {
                "title": "Architecture Overview",
                "category": DocCategory.ARCHITECTURE.value,
                "description": "Complete system architecture for Verdis + EvolvixOS",
                "content": "## Verdis Blockchain\n- DPoS consensus with 14 validators\n- 13 Substrate pallets\n- EVM compatibility (chain ID 909)\n- Native AMM DEX\n- SDK + CLI\n- Bridge (5 chains)\n- Android wallet + web wallet\n- Verdiscan explorer\n\n## EvolvixOS\n- 11 AI agents\n- Feature delivery pipeline (10 stages)\n- Knowledge base\n- Multi-project manager\n- 61 frontend pages\n- 775 API endpoints",
                "tags": ["architecture", "verdis", "evolvixos", "blockchain", "dp"],
                "sections": ["Overview", "Blockchain Core", "EvolvixOS", "Infrastructure", "Security"],
            },
            {
                "title": "API Reference",
                "category": DocCategory.API_REFERENCE.value,
                "description": "Complete API reference for all 775 endpoints",
                "content": "## Authentication\nAll endpoints require JWT bearer token.\n\n## Rate Limiting\n- General: 100 req/min\n- Auth: 5 req/min per IP\n\n## Endpoints by Module\n- Wallet, Staking, Governance, Identity\n- Analytics, Bridge, NFT, Faucet\n- Explorer, Mobile, Readiness, Security\n- Notifications, Tokenomics, Validators\n- Compliance, API Gateway, Plugins\n- Smart Contracts, Deployment Dashboard",
                "tags": ["api", "rest", "endpoints", "openapi"],
                "sections": ["Authentication", "Rate Limiting", "Modules", "WebSocket", "Error Codes"],
            },
            {
                "title": "User Guide",
                "category": DocCategory.USER_GUIDE.value,
                "description": "End-user guide for Verdis wallet and ecosystem",
                "content": "## Getting Started\n1. Create a wallet (Android or Web)\n2. Get testnet tokens from faucet\n3. Explore on Verdiscan\n\n## Staking\n1. Choose a validator (green score recommended)\n2. Stake VRS tokens\n3. Earn 12% base + 5% green bonus APY\n4. Unstake (7-day unbonding)\n\n## Governance\n1. View active proposals\n2. Vote (aye/nay/abstain)\n3. Track treasury spending",
                "tags": ["user", "wallet", "staking", "governance", "nft"],
                "sections": ["Wallet Setup", "Staking", "Governance", "NFT", "Bridge", "Identity"],
            },
            {
                "title": "Developer Guide",
                "category": DocCategory.DEVELOPER_GUIDE.value,
                "description": "Developer onboarding guide for building on Verdis",
                "content": "## Quick Start\n1. Clone the repo\n2. Install Rust + Node.js\n3. Run cargo build --release\n4. Start EvolvixOS backend: python -m uvicorn app.main:app\n5. Start frontend: npm run dev\n\n## Smart Contracts\n- Use Solidity 0.8.20+\n- Deploy via Foundry/Hardhat\n- Chain ID: 909\n\n## Testing\n- Rust: cargo test --release --workspace\n- Python: pytest\n- Frontend: npm run build",
                "tags": ["developer", "setup", "sdk", "smart-contracts", "testing"],
                "sections": ["Setup", "Smart Contracts", "SDK", "Testing", "Deployment"],
            },
            {
                "title": "Deployment Guide",
                "category": DocCategory.DEPLOYMENT.value,
                "description": "Production deployment guide for Verdis + EvolvixOS",
                "content": "## Prerequisites\n- Linux server (Ubuntu 22.04+)\n- 16GB RAM, 8 cores, 500GB SSD\n- Docker + Docker Compose\n- Nginx (reverse proxy)\n- SSL certificates\n\n## Components\n1. Verdis node (Rust binary)\n2. EvolvixOS backend (Python/FastAPI)\n3. EvolvixOS frontend (React/Vite)\n4. PostgreSQL\n5. Redis\n6. Nginx (reverse proxy + SSL)\n\n## Deployment Steps\n1. Copy manifests to server\n2. Configure environment variables\n3. Build Docker images\n4. Start with docker-compose.prod.yml\n5. Configure nginx\n6. Setup systemd services\n7. Run health checks",
                "tags": ["deployment", "docker", "nginx", "ssl", "systemd"],
                "sections": ["Prerequisites", "Docker", "Nginx", "Systemd", "Monitoring"],
            },
            {
                "title": "Troubleshooting Guide",
                "category": DocCategory.TROUBLESHOOTING.value,
                "description": "Common issues and solutions",
                "content": "## Node Won't Start\n- Check port 30333 not in use\n- Verify genesis.json matches network\n- Check disk space\n\n## API Returns 401\n- Verify JWT token not expired (1h expiry)\n- Use refresh token for new access token\n\n## Frontend Blank Page\n- Check API_URL in .env\n- Verify backend is running\n\n## Staking Rewards Not Showing\n- Check epoch transition\n- Verify validator is active",
                "tags": ["troubleshooting", "issues", "fixes", "debug"],
                "sections": ["Node Issues", "API Issues", "Frontend Issues", "Staking Issues"],
            },
            {
                "title": "Verdis Whitepaper",
                "category": DocCategory.WHITEPAPER.value,
                "description": "Comprehensive Verdis blockchain whitepaper",
                "content": "## Abstract\nVerdis is the world's first fully green, carbon-negative blockchain ecosystem.\n\n## Consensus\nDPoS with 101 max validator slots, green scoring (0-100).\n\n## Tokenomics\n100B total supply (VRS), 12B investor allocation.\n\n## Eco Features\n- Carbon credit tracking on-chain\n- Reforestation logging\n- Green validator scoring\n- Carbon-negative operations\n\n## EVM\n101 EVM opcodes, chain ID 909, native AMM DEX.\n\n## Bridge\nCross-chain transfers (Ethereum, BSC, Polygon, Avalanche).",
                "tags": ["whitepaper", "blockchain", "green", "carbon", "dp"],
                "sections": ["Abstract", "Consensus", "Tokenomics", "Eco Features", "EVM", "Bridge"],
            },
        ]

        for d in docs_data:
            did = f"doc-{secrets.token_hex(8)}"
            self._docs[did] = DocEntry(
                id=did, title=d["title"], category=d["category"],
                description=d["description"], content=d["content"],
                tags=d["tags"], sections=d["sections"],
                word_count=len(d["content"].split()),
            )

    def _init_manifests(self):
        """Initialize deployment manifests."""
        manifests = [
            ("Docker Compose Production", ManifestType.DOCKER_COMPOSE.value, "all",
             "docker-compose.prod.yml",
             """version: '3.8'
services:
  verdis-node:
    build: ./verdis
    ports: ["30333:30333", "9933:9933", "9944:9944"]
    volumes: ["verdis-data:/data"]
    restart: always
    deploy:
      resources:
        limits: { cpus: '4', memory: 8G }

  evolvixos-backend:
    build: ./evolvixos/backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis]
    restart: always
    deploy:
      resources:
        limits: { cpus: '2', memory: 4G }

  evolvixos-frontend:
    build: ./evolvixos/frontend
    ports: ["3000:3000"]
    restart: always

  postgres:
    image: postgres:16
    ports: ["5432:5432"]
    volumes: ["pg-data:/var/lib/postgresql/data"]
    restart: always

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    restart: always

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes: ["./nginx.conf:/etc/nginx/nginx.conf", "./ssl:/etc/nginx/ssl"]
    depends_on: [evolvixos-backend, evolvixos-frontend]
    restart: always

volumes:
  verdis-data:
  pg-data:""",
             "Production Docker Compose with all services",
             ["DATABASE_URL", "REDIS_URL", "JWT_SECRET", "VERDIS_RPC_URL"],
             ["verdis-node", "postgres", "redis"], 8000, "/health"),

            ("Kubernetes Deployment", ManifestType.KUBERNETES.value, "evolvixos-backend",
             "k8s-backend.yaml",
             """apiVersion: apps/v1
kind: Deployment
metadata:
  name: evolvixos-backend
spec:
  replicas: 3
  selector:
    matchLabels: { app: evolvixos-backend }
  template:
    spec:
      containers:
      - name: backend
        image: verdis/evolvixos-backend:latest
        ports: [{ containerPort: 8000 }]
        resources:
          requests: { cpu: '500m', memory: '1Gi' }
          limits: { cpu: '2', memory: '4Gi' }
        livenessProbe:
          httpGet: { path: /health, port: 8000 }
        readinessProbe:
          httpGet: { path: /health/detail, port: 8000 }""",
             "Kubernetes manifest for EvolvixOS backend with 3 replicas",
             ["DATABASE_URL", "REDIS_URL", "JWT_SECRET"],
             [], 8000, "/health"),

            ("Systemd Service", ManifestType.SYSTEMD.value, "verdis-node",
             "verdis-node.service",
             """[Unit]
Description=Verdis Blockchain Node
After=network.target

[Service]
Type=simple
User=verdis
ExecStart=/opt/verdis/verdis-node --chain mainnet --port 30333 --rpc-port 9933 --ws-port 9944
Restart=always
RestartSec=10
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target""",
             "Systemd service for Verdis blockchain node",
             [],
             [], 30333, ""),

            ("Nginx Reverse Proxy", ManifestType.NGINX.value, "nginx",
             "nginx.conf",
             """upstream evolvixos_backend {
    server 127.0.0.1:8000;
}
upstream evolvixos_frontend {
    server 127.0.0.1:3000;
}

server {
    listen 443 ssl http2;
    server_name verdischain.com;

    ssl_certificate /etc/nginx/ssl/verdis.crt;
    ssl_certificate_key /etc/nginx/ssl/verdis.key;
    ssl_protocols TLSv1.3;

    location /api/ {
        proxy_pass http://evolvixos_backend;
        limit_req zone=api burst=20 nodelay;
    }

    location /ws {
        proxy_pass http://evolvixos_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        proxy_pass http://evolvixos_frontend;
    }
}

limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;""",
             "Nginx with SSL, WebSocket, and rate limiting",
             [],
             [], 443, "/health"),

            ("Environment Template", ManifestType.ENV_TEMPLATE.value, "all",
             ".env.example",
             """# Verdis Blockchain
VERDIS_RPC_URL=https://testnet.verdischain.com
VERDIS_CHAIN_ID=909
VERDIS_EXPLORER_URL=https://verdiscan.verdischain.com

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/evolvixos
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=<generate-64-char-hex>
OPENAI_API_KEY_2=<your-openai-key>

# API
API_V1_PREFIX=/api/v1
CORS_ORIGINS=https://verdischain.com

# Monitoring
SENTRY_DSN=
PROMETHEUS_PORT=9090""",
             "Environment variables template",
             ["VERDIS_RPC_URL", "DATABASE_URL", "JWT_SECRET", "OPENAI_API_KEY_2"],
             [], 0, ""),

            ("Backend Dockerfile", ManifestType.DOCKERFILE.value, "evolvixos-backend",
             "Dockerfile.backend",
             """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]""",
             "Dockerfile for EvolvixOS backend",
             [], [], 8000, "/health"),

            ("Frontend Dockerfile", ManifestType.DOCKERFILE.value, "evolvixos-frontend",
             "Dockerfile.frontend",
             """FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]""",
             "Dockerfile for EvolvixOS frontend (multi-stage build)",
             [], [], 3000, ""),
        ]

        for name, mtype, component, filename, content, desc, env_vars, deps, port, health in manifests:
            mid = f"man-{secrets.token_hex(8)}"
            self._manifests[mid] = DeploymentManifest(
                id=mid, name=name, type=mtype, component=component,
                filename=filename, content=content, description=desc,
                env_vars=env_vars, dependencies=deps,
                port=port, health_check=health,
            )

    def _init_faqs(self):
        """Initialize FAQ entries."""
        faqs = [
            ("What is Verdis?", "Verdis is the world's first fully green, carbon-negative blockchain ecosystem with DPoS consensus, EVM compatibility, and native AMM DEX.", "general"),
            ("How do I get testnet tokens?", "Use the faucet at /faucet. You need to solve a captcha and wait 24 hours between claims. Each claim gives 100 VRS.", "getting-started"),
            ("What is the total supply?", "100 billion VRS tokens. 12 billion allocated to investors. See the tokenomics dashboard for full breakdown.", "tokenomics"),
            ("How does green scoring work?", "Validators receive a 0-100 green score based on energy source, carbon offset, and uptime. Scores >= 80 are auto-certified with 5% bonus APY.", "validators"),
            ("How do I stake?", "Choose a validator, delegate VRS tokens, earn 12% base + 5% green bonus APY. Unbonding period is 7 days.", "staking"),
            ("What is EvolvixOS?", "EvolvixOS is the universal AI Engineering Operating System managing the Verdis ecosystem with 11 AI agents, autonomous pipelines, and multi-project support.", "evolvixos"),
            ("How do I deploy smart contracts?", "Use Solidity 0.8.20+, deploy via Foundry or Hardhat. Chain ID is 909. See the developer guide for templates.", "developers"),
            ("Is there a mobile wallet?", "Yes, the Android wallet (v2.5.3) supports all EvolvixOS features including staking, governance, identity, and NFT marketplace.", "wallet"),
            ("How does the bridge work?", "Cross-chain transfers between Ethereum, Verdis, BSC, Polygon, and Avalanche with M-of-N validator signatures (default 3).", "bridge"),
            ("What are VRC token standards?", "VRC-20 (fungible), VRC-721 (NFT), VRC-1155 (multi-token). All compatible with EVM on Verdis.", "developers"),
            ("How do I become a validator?", "Register through the validator management UI. Max 101 slots. Need to maintain uptime and green score.", "validators"),
            ("What is the block time?", "6 seconds. TPS depends on network conditions. See the on-chain analytics dashboard for live metrics.", "technical"),
        ]

        for question, answer, category in faqs:
            fid = f"faq-{secrets.token_hex(8)}"
            self._faqs[fid] = FAQEntry(
                id=fid, question=question, answer=answer, category=category,
            )

    def _init_runbooks(self):
        """Initialize operational runbooks."""
        runbooks = [
            ("Node Crash Recovery", "Verdis blockchain node crashes or becomes unresponsive",
             "high", ["Check process status", "Review logs", "Restart service", "Verify sync", "Check peer count"],
             ["Stop service", "Revert to backup", "Restart with --chain backup"], "15 min"),
            ("Database Failure", "PostgreSQL database is down or corrupt",
             "critical", ["Check PostgreSQL service", "Verify disk space", "Check connections", "Restore from backup if needed"],
             ["Failover to replica", "Restore from latest backup"], "30 min"),
            ("API Outage", "EvolvixOS API returning 5xx errors",
             "high", ["Check backend process", "Review error logs", "Check database connection", "Check Redis", "Restart if needed"],
             ["Rollback to previous version", "Switch to backup instance"], "10 min"),
            ("Frontend Down", "EvolvixOS frontend not loading",
             "medium", ["Check nginx status", "Verify frontend build", "Check DNS", "Test locally"],
             ["Revert to previous build", "Switch DNS to backup"], "5 min"),
            ("Bridge Stuck", "Cross-chain transfers not completing",
             "high", ["Check relayer status", "Verify signatures", "Check destination chain", "Manual replay if needed"],
             ["Pause bridge", "Refund pending transfers"], "20 min"),
            ("High Memory Usage", "Server memory usage above 90%",
             "medium", ["Check process memory", "Restart EvolvixOS backend", "Clear Redis cache", "Check for memory leaks"],
             [], "10 min"),
        ]

        for name, scenario, severity, steps, rollback, est_time in runbooks:
            rid = f"rb-{secrets.token_hex(8)}"
            self._runbooks[rid] = RunbookEntry(
                id=rid, name=name, scenario=scenario,
                severity=severity, steps=steps,
                rollback_steps=rollback, estimated_time=est_time,
            )

    # === Docs ===

    def list_docs(self, category: str = None, status: str = None,
                  limit: int = 50) -> list[DocEntry]:
        docs = list(self._docs.values())
        if category:
            docs = [d for d in docs if d.category == category]
        if status:
            docs = [d for d in docs if d.status == status]
        docs.sort(key=lambda d: d.updated, reverse=True)
        return docs[:limit]

    def get_doc(self, doc_id: str) -> Optional[DocEntry]:
        return self._docs.get(doc_id)

    def search_docs(self, query: str, limit: int = 20) -> list[DocEntry]:
        query_lower = query.lower()
        results = []
        for doc in self._docs.values():
            score = 0
            if query_lower in doc.title.lower():
                score += 3
            if query_lower in doc.description.lower():
                score += 2
            if query_lower in doc.content.lower():
                score += 1
            for tag in doc.tags:
                if query_lower in tag.lower():
                    score += 2
            if score > 0:
                results.append((score, doc))
        results.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in results[:limit]]

    def create_doc(self, title: str, category: str, description: str,
                   content: str = "", tags: list = None) -> DocEntry:
        did = f"doc-{secrets.token_hex(8)}"
        doc = DocEntry(
            id=did, title=title, category=category,
            description=description, content=content,
            tags=tags or [], word_count=len(content.split()),
        )
        self._docs[did] = doc
        return doc

    def update_doc(self, doc_id: str, **kwargs) -> Optional[DocEntry]:
        doc = self._docs.get(doc_id)
        if not doc:
            return None
        for k, v in kwargs.items():
            if hasattr(doc, k):
                setattr(doc, k, v)
        doc.updated = datetime.utcnow().isoformat()
        if "content" in kwargs:
            doc.word_count = len(kwargs["content"].split())
        return doc

    def delete_doc(self, doc_id: str) -> bool:
        if doc_id in self._docs:
            del self._docs[doc_id]
            return True
        return False

    # === Manifests ===

    def list_manifests(self, type: str = None, component: str = None, limit: int = 50) -> list[DeploymentManifest]:
        manifests = list(self._manifests.values())
        if type:
            manifests = [m for m in manifests if m.type == type]
        if component:
            manifests = [m for m in manifests if m.component == component]
        return manifests[:limit]

    def get_manifest(self, manifest_id: str) -> Optional[DeploymentManifest]:
        return self._manifests.get(manifest_id)

    def get_manifest_by_filename(self, filename: str) -> Optional[DeploymentManifest]:
        for m in self._manifests.values():
            if m.filename == filename:
                return m
        return None

    def create_manifest(self, name: str, mtype: str, component: str,
                       filename: str, content: str, **kwargs) -> DeploymentManifest:
        mid = f"man-{secrets.token_hex(8)}"
        manifest = DeploymentManifest(
            id=mid, name=name, type=mtype, component=component,
            filename=filename, content=content, **kwargs,
        )
        self._manifests[mid] = manifest
        return manifest

    # === FAQs ===

    def list_faqs(self, category: str = None, limit: int = 50) -> list[FAQEntry]:
        faqs = list(self._faqs.values())
        if category:
            faqs = [f for f in faqs if f.category == category]
        return faqs[:limit]

    def get_faq(self, faq_id: str) -> Optional[FAQEntry]:
        return self._faqs.get(faq_id)

    def search_faqs(self, query: str, limit: int = 20) -> list[FAQEntry]:
        query_lower = query.lower()
        results = [f for f in self._faqs.values()
                   if query_lower in f.question.lower() or query_lower in f.answer.lower()]
        return results[:limit]

    def create_faq(self, question: str, answer: str, category: str = "general") -> FAQEntry:
        fid = f"faq-{secrets.token_hex(8)}"
        faq = FAQEntry(id=fid, question=question, answer=answer, category=category)
        self._faqs[fid] = faq
        return faq

    def mark_faq_helpful(self, faq_id: str) -> Optional[FAQEntry]:
        faq = self._faqs.get(faq_id)
        if faq:
            faq.helpful_count += 1
            return faq
        return None

    # === Runbooks ===

    def list_runbooks(self, severity: str = None, limit: int = 50) -> list[RunbookEntry]:
        runbooks = list(self._runbooks.values())
        if severity:
            runbooks = [r for r in runbooks if r.severity == severity]
        return runbooks[:limit]

    def get_runbook(self, runbook_id: str) -> Optional[RunbookEntry]:
        return self._runbooks.get(runbook_id)

    def create_runbook(self, name: str, scenario: str, steps: list,
                       rollback_steps: list = None, severity: str = "medium",
                       estimated_time: str = "") -> RunbookEntry:
        rid = f"rb-{secrets.token_hex(8)}"
        runbook = RunbookEntry(
            id=rid, name=name, scenario=scenario, severity=severity,
            steps=steps, rollback_steps=rollback_steps or [],
            estimated_time=estimated_time,
        )
        self._runbooks[rid] = runbook
        return runbook

    # === Dashboard ===

    def get_dashboard(self) -> dict:
        return {
            "stats": {
                "total_docs": len(self._docs),
                "total_manifests": len(self._manifests),
                "total_faqs": len(self._faqs),
                "total_runbooks": len(self._runbooks),
                "total_words": sum(d.word_count for d in self._docs.values()),
                "published_docs": sum(1 for d in self._docs.values() if d.status == "published"),
                "doc_categories": len(set(d.category for d in self._docs.values())),
            },
            "recent_docs": [d.to_dict() for d in self.list_docs(limit=5)],
            "manifests": [m.to_dict() for m in self._manifests.values()],
            "faq_categories": list(set(f.category for f in self._faqs.values())),
            "runbook_count": len(self._runbooks),
        }


_service: Optional[DeploymentDocsService] = None

def get_deployment_docs_service() -> DeploymentDocsService:
    global _service
    if _service is None:
        _service = DeploymentDocsService()
    return _service
