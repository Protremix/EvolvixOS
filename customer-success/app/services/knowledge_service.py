"""Knowledge base service."""
import time
import uuid
from app.models import database

# Pre-loaded knowledge entries
INITIAL_ENTRIES = [
    {"id": "kb-001", "title": "Verdis Blockchain Overview", "category": "documentation",
     "content": "Verdis is a carbon-negative blockchain with DPoS consensus, 101 EVM opcodes, native AMM DEX, 100B total supply. Uses Substrate with BABE/GRANDPA consensus.",
     "source": "whitepaper", "verified": True, "tags": ["blockchain", "overview"]},
    {"id": "kb-002", "title": "RPC API Methods", "category": "api_reference",
     "content": "121 RPC methods available: chain_getBlock, chain_getHeader, state_getStorage, system_properties, dex_getPools, dex_getPrices, validator_getList. Base URL: https://evolvixos.com/blockchain/rpc",
     "source": "api_docs", "verified": True, "tags": ["api", "rpc"]},
    {"id": "kb-003", "title": "Validator Setup Guide", "category": "developer_docs",
     "content": "To become a validator: register with minimum 10,000 VRS stake, maintain green score, produce blocks. Use register_validator extrinsic with green_score and energy_source parameters.",
     "source": "docs", "verified": True, "tags": ["validator", "staking"]},
    {"id": "kb-004", "title": "AMM DEX Usage", "category": "developer_docs",
     "content": "The AMM DEX uses x*y=k constant product formula with 0.3% fee. Create pools, add liquidity, swap tokens.",
     "source": "docs", "verified": True, "tags": ["dex", "amm"]},
    {"id": "kb-005", "title": "Carbon Credit Tracking", "category": "documentation",
     "content": "On-chain carbon credit minting, verification, trading, and retirement. Each credit tracks tons of CO2.",
     "source": "whitepaper", "verified": True, "tags": ["eco", "carbon"]},
    {"id": "kb-006", "title": "Wallet Security", "category": "security",
     "content": "Use hardware wallets. Enable 2FA. Never share private keys. Use @noble/secp256k1 for crypto operations.",
     "source": "security_docs", "verified": True, "tags": ["security", "wallet"]},
    {"id": "kb-007", "title": "EvolvixOS Platform", "category": "documentation",
     "content": "EvolvixOS is the universal AI Engineering OS. 768+ API endpoints, dark-themed React frontend.",
     "source": "docs", "verified": True, "tags": ["evolvixos", "platform"]},
    {"id": "kb-008", "title": "Tokenomics", "category": "documentation",
     "content": "100B total supply, 12B investor allocation. Block reward: 16 VRS. Allocations: investors 12B, team 15B, treasury 20B, community 18B, validators 10B, ecosystem 15B, liquidity 10B.",
     "source": "whitepaper", "verified": True, "tags": ["tokenomics", "supply"]},
    {"id": "kb-009", "title": "Staking and Rewards", "category": "developer_docs",
     "content": "12% base APY + 5% green bonus. 7-day unbonding. Auto-compound available. 5% slash penalty.",
     "source": "docs", "verified": True, "tags": ["staking", "rewards"]},
    {"id": "kb-010", "title": "Node Sync Troubleshooting", "category": "runbook",
     "content": "If node not syncing: check peer count, verify bootnodes, check firewall, restart node, check disk space.",
     "source": "runbook", "verified": True, "tags": ["node", "sync"]},
]

class KnowledgeService:
    def __init__(self):
        # Load initial entries
        for entry in INITIAL_ENTRIES:
            if not database.get("knowledge_entries", entry["id"]):
                database.insert("knowledge_entries", entry)
    
    def search(self, query: str, category: str = None, limit: int = 10) -> list:
        entries = database.list_records("knowledge_entries", limit=200)
        q_lower = query.lower()
        scored = []
        for entry in entries:
            if category and entry.get("category") != category:
                continue
            score = 0
            text = (entry.get("title", "") + " " + entry.get("content", "")).lower()
            for word in q_lower.split():
                if word in text:
                    score += 1
            # Also check tags
            for tag in entry.get("tags", []):
                if tag.lower() in q_lower:
                    score += 2
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, entry in scored[:limit]:
            results.append({
                "id": entry["id"],
                "title": entry["title"],
                "content": entry["content"],
                "category": entry["category"],
                "source": entry["source"],
                "verified": entry.get("verified", False),
                "relevance_score": score,
            })
        return results
    
    def create_entry(self, title, content, category, source, tags, verified) -> dict:
        entry_id = f"kb-{uuid.uuid4().hex[:6]}"
        return database.insert("knowledge_entries", {
            "id": entry_id,
            "title": title,
            "content": content,
            "category": category,
            "source": source,
            "tags": tags,
            "verified": verified,
        })
    
    def list_entries(self, category=None, limit=50, offset=0):
        return database.list_records("knowledge_entries",
            filter_fn=lambda r: (not category or r.get("category") == category),
            limit=limit, offset=offset)
    
    def get_entry(self, entry_id):
        return database.get("knowledge_entries", entry_id)
    
    def get_stats(self):
        entries = database.list_records("knowledge_entries", limit=1000)
        categories = {}
        for e in entries:
            cat = e.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total": len(entries),
            "by_category": categories,
            "verified": sum(1 for e in entries if e.get("verified")),
        }
