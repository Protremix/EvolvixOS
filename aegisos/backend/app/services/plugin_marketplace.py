"""
Plugin Marketplace — Phase 39

Plugin submission, approval workflow, browsing, installation,
ratings/reviews, versioning, and developer profiles.
"""

import secrets
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import threading
from app.core.logging import get_logger

logger = get_logger("service.plugin_marketplace")


class PluginStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"


class PluginCategory(str, Enum):
    ANALYTICS = "analytics"
    SECURITY = "security"
    DEVELOPER_TOOLS = "developer_tools"
    WALLET = "wallet"
    GOVERNANCE = "governance"
    DEFI = "defi"
    NFT = "nft"
    BRIDGE = "bridge"
    IDENTITY = "identity"
    MONITORING = "monitoring"
    AI = "ai"
    UTILITY = "utility"


class License(str, Enum):
    FREE = "free"
    FREEMIUM = "freemium"
    PAID = "paid"
    OPEN_SOURCE = "open_source"


@dataclass
class Plugin:
    id: str
    name: str
    slug: str
    description: str
    author: str
    version: str
    category: str
    license: str = License.FREE.value
    status: str = PluginStatus.SUBMITTED.value
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    price: float = 0.0
    tags: list[str] = field(default_factory=list)
    homepage: str = ""
    repository: str = ""
    documentation: str = ""
    icon: str = ""
    screenshots: list[str] = field(default_factory=list)
    min_version: str = "1.0.0"
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    approved_at: str = ""
    rejection_reason: str = ""
    checksum: str = ""
    size_bytes: int = 0
    changelog: list[dict] = field(default_factory=list)
    installs: list[str] = field(default_factory=list)  # list of user addresses who installed
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PluginReview:
    id: str
    plugin_id: str
    reviewer: str
    rating: float  # 1-5
    comment: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    helpful: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Developer:
    address: str
    name: str
    verified: bool = False
    plugins_published: int = 0
    total_downloads: int = 0
    joined: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    bio: str = ""
    website: str = ""
    avatar: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class PluginMarketplaceService:
    """Plugin marketplace with submission, approval, and installation."""

    def __init__(self):
        self._plugins: dict[str, Plugin] = {}
        self._slug_index: dict[str, str] = {}
        self._reviews: dict[str, list[PluginReview]] = defaultdict(list)
        self._developers: dict[str, Developer] = {}
        self._lock = threading.Lock()
        self._init_default_plugins()

    def _init_default_plugins(self):
        """Initialize with some default plugins."""
        defaults = [
            ("Verdis Carbon Tracker", "carbon-tracker", "Track carbon credits and offsets on-chain", "Verdis Team", "1.2.0", PluginCategory.MONITORING.value, License.OPEN_SOURCE.value, ["carbon", "eco", "green"], 4500, 4.8, 23),
            ("EvolvixOS Pipeline Builder", "pipeline-builder", "Visual pipeline builder for EvolvixOS agents", "Verdis Team", "2.0.1", PluginCategory.DEVELOPER_TOOLS.value, License.FREE.value, ["pipeline", "automation", "ai"], 8200, 4.9, 45),
            ("Green Validator Dashboard", "green-validator-dash", "Monitor validator green scores and energy sources", "Verdis Team", "1.5.0", PluginCategory.MONITORING.value, License.FREE.value, ["validator", "green", "staking"], 3100, 4.7, 18),
            ("Bridge Analytics", "bridge-analytics", "Cross-chain transfer analytics and visualization", "Verdis Team", "1.0.0", PluginCategory.BRIDGE.value, License.FREEMIUM.value, ["bridge", "analytics", "cross-chain"], 1800, 4.5, 12),
            ("Identity Verifier", "identity-verifier", "W3C DID verification and credential checking", "Verdis Team", "1.3.0", PluginCategory.IDENTITY.value, License.OPEN_SOURCE.value, ["did", "identity", "credentials"], 2600, 4.6, 15),
            ("Token Vesting Manager", "vesting-manager", "Manage token vesting schedules and releases", "Verdis Team", "1.1.0", PluginCategory.DEFI.value, License.FREEMIUM.value, ["vesting", "tokens", "treasury"], 1500, 4.4, 8),
            ("Smart Contract Scanner", "contract-scanner", "Security scanner for Solidity smart contracts", "Verdis Team", "2.1.0", PluginCategory.SECURITY.value, License.PAID.value, ["security", "solidity", "audit"], 4200, 4.9, 31),
            ("Governance Proposal Builder", "gov-proposal-builder", "Create and manage governance proposals", "Verdis Team", "1.0.0", PluginCategory.GOVERNANCE.value, License.FREE.value, ["governance", "voting", "treasury"], 980, 4.3, 6),
        ]
        for name, slug, desc, author, ver, cat, lic, tags, downloads, rating, rc in defaults:
            p = Plugin(
                id=f"plg-{secrets.token_hex(6)}", name=name, slug=slug,
                description=desc, author=author, version=ver, category=cat,
                license=lic, tags=tags, downloads=downloads,
                rating=rating, rating_count=rc, status=PluginStatus.APPROVED.value,
                approved_at=datetime.utcnow().isoformat(),
                homepage=f"https://github.com/Protremix/{slug}",
                repository=f"https://github.com/Protremix/{slug}",
            )
            self._plugins[p.id] = p
            self._slug_index[slug] = p.id

        # Register default developer
        dev = Developer(address="0xverdis", name="Verdis Team", verified=True, plugins_published=8, total_downloads=26880)
        self._developers["0xverdis"] = dev

    # === Plugins ===

    def submit_plugin(
        self, name: str, description: str, author: str, version: str,
        category: str, license: str = License.FREE.value, price: float = 0.0,
        tags: list[str] = None, homepage: str = "", repository: str = "",
        documentation: str = "", min_version: str = "1.0.0", checksum: str = "",
        size_bytes: int = 0, metadata: dict = None,
    ) -> Plugin:
        """Submit a new plugin for review."""
        slug = name.lower().replace(" ", "-").replace("_", "-")
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while slug in self._slug_index:
            slug = f"{base_slug}-{counter}"
            counter += 1

        plugin_id = f"plg-{secrets.token_hex(6)}"
        plugin = Plugin(
            id=plugin_id, name=name, slug=slug, description=description,
            author=author, version=version, category=category, license=license,
            price=price, tags=tags or [], homepage=homepage, repository=repository,
            documentation=documentation, min_version=min_version,
            checksum=checksum, size_bytes=size_bytes, metadata=metadata or {},
        )

        with self._lock:
            self._plugins[plugin_id] = plugin
            self._slug_index[slug] = plugin_id

            # Register/update developer
            if author not in self._developers:
                self._developers[author] = Developer(address=author, name=author)

        logger.info("plugin_submitted", id=plugin_id, name=name, author=author)
        return plugin

    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        return self._plugins.get(plugin_id)

    def get_plugin_by_slug(self, slug: str) -> Optional[Plugin]:
        pid = self._slug_index.get(slug)
        return self._plugins.get(pid) if pid else None

    def list_plugins(
        self, status: str = None, category: str = None, author: str = None,
        search: str = None, sort_by: str = "downloads", limit: int = 50,
    ) -> list[Plugin]:
        plugins = list(self._plugins.values())
        if status:
            plugins = [p for p in plugins if p.status == status]
        if category:
            plugins = [p for p in plugins if p.category == category]
        if author:
            plugins = [p for p in plugins if p.author == author]
        if search:
            s = search.lower()
            plugins = [p for p in plugins if s in p.name.lower() or s in p.description.lower() or any(s in t.lower() for t in p.tags)]

        sort_map = {
            "downloads": lambda p: p.downloads,
            "rating": lambda p: p.rating,
            "newest": lambda p: p.created,
            "name": lambda p: p.name,
        }
        reverse = sort_by != "name"
        plugins.sort(key=sort_map.get(sort_by, lambda p: p.downloads), reverse=reverse)
        return plugins[:limit]

    def approve_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Approve a submitted plugin."""
        plugin = self._plugins.get(plugin_id)
        if not plugin or plugin.status not in (PluginStatus.SUBMITTED.value, PluginStatus.UNDER_REVIEW.value):
            return None
        plugin.status = PluginStatus.APPROVED.value
        plugin.approved_at = datetime.utcnow().isoformat()
        plugin.updated = datetime.utcnow().isoformat()

        # Update developer stats
        if plugin.author in self._developers:
            self._developers[plugin.author].plugins_published += 1

        return plugin

    def reject_plugin(self, plugin_id: str, reason: str = "") -> Optional[Plugin]:
        """Reject a submitted plugin."""
        plugin = self._plugins.get(plugin_id)
        if not plugin or plugin.status not in (PluginStatus.SUBMITTED.value, PluginStatus.UNDER_REVIEW.value):
            return None
        plugin.status = PluginStatus.REJECTED.value
        plugin.rejection_reason = reason
        plugin.updated = datetime.utcnow().isoformat()
        return plugin

    def suspend_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Suspend an approved plugin."""
        plugin = self._plugins.get(plugin_id)
        if not plugin or plugin.status != PluginStatus.APPROVED.value:
            return None
        plugin.status = PluginStatus.SUSPENDED.value
        plugin.updated = datetime.utcnow().isoformat()
        return plugin

    def deprecate_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Deprecate a plugin."""
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return None
        plugin.status = PluginStatus.DEPRECATED.value
        plugin.updated = datetime.utcnow().isoformat()
        return plugin

    def update_plugin(self, plugin_id: str, **kwargs) -> Optional[Plugin]:
        """Update plugin metadata."""
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return None
        for k, v in kwargs.items():
            if hasattr(plugin, k) and k not in ("id", "created"):
                setattr(plugin, k, v)
        plugin.updated = datetime.utcnow().isoformat()
        return plugin

    # === Installation ===

    def install_plugin(self, plugin_id: str, user_address: str) -> Optional[Plugin]:
        """Install a plugin for a user."""
        plugin = self._plugins.get(plugin_id)
        if not plugin or plugin.status != PluginStatus.APPROVED.value:
            return None
        if user_address not in plugin.installs:
            plugin.installs.append(user_address)
            plugin.downloads += 1
            plugin.updated = datetime.utcnow().isoformat()
        return plugin

    def uninstall_plugin(self, plugin_id: str, user_address: str) -> bool:
        """Uninstall a plugin for a user."""
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        if user_address in plugin.installs:
            plugin.installs.remove(user_address)
            return True
        return False

    def get_installed_plugins(self, user_address: str) -> list[Plugin]:
        """Get all plugins installed by a user."""
        return [p for p in self._plugins.values() if user_address in p.installs]

    # === Reviews ===

    def add_review(self, plugin_id: str, reviewer: str, rating: float, comment: str = "") -> Optional[PluginReview]:
        """Add a review for a plugin."""
        plugin = self._plugins.get(plugin_id)
        if not plugin or plugin.status != PluginStatus.APPROVED.value:
            return None
        if rating < 1 or rating > 5:
            return None

        # Check if already reviewed
        existing = [r for r in self._reviews[plugin_id] if r.reviewer == reviewer]
        if existing:
            return None

        review_id = f"rev-{secrets.token_hex(6)}"
        review = PluginReview(
            id=review_id, plugin_id=plugin_id, reviewer=reviewer,
            rating=rating, comment=comment,
        )
        self._reviews[plugin_id].append(review)

        # Update plugin rating
        all_ratings = [r.rating for r in self._reviews[plugin_id]]
        plugin.rating = round(sum(all_ratings) / len(all_ratings), 2)
        plugin.rating_count = len(all_ratings)
        plugin.updated = datetime.utcnow().isoformat()

        return review

    def get_reviews(self, plugin_id: str, limit: int = 20) -> list[PluginReview]:
        return self._reviews.get(plugin_id, [])[-limit:]

    def mark_review_helpful(self, review_id: str) -> bool:
        """Mark a review as helpful."""
        for reviews in self._reviews.values():
            for r in reviews:
                if r.id == review_id:
                    r.helpful += 1
                    return True
        return False

    # === Developers ===

    def register_developer(self, address: str, name: str, bio: str = "", website: str = "") -> Developer:
        """Register a new developer."""
        if address in self._developers:
            dev = self._developers[address]
            if bio:
                dev.bio = bio
            if website:
                dev.website = website
            return dev
        dev = Developer(address=address, name=name, bio=bio, website=website)
        self._developers[address] = dev
        return dev

    def verify_developer(self, address: str) -> bool:
        """Verify a developer."""
        dev = self._developers.get(address)
        if not dev:
            return False
        dev.verified = True
        return True

    def get_developer(self, address: str) -> Optional[Developer]:
        return self._developers.get(address)

    def list_developers(self, verified_only: bool = False) -> list[Developer]:
        devs = list(self._developers.values())
        if verified_only:
            devs = [d for d in devs if d.verified]
        return devs

    # === Categories ===

    def list_categories(self) -> list[dict]:
        counts = defaultdict(int)
        for p in self._plugins.values():
            if p.status == PluginStatus.APPROVED.value:
                counts[p.category] += 1
        return [
            {"value": c.value, "name": c.value.replace("_", " ").title(), "count": counts.get(c.value, 0)}
            for c in PluginCategory
        ]

    # === Stats ===

    def get_stats(self) -> dict:
        plugins = list(self._plugins.values())
        approved = [p for p in plugins if p.status == PluginStatus.APPROVED.value]
        return {
            "total_plugins": len(plugins),
            "approved": len(approved),
            "pending": sum(1 for p in plugins if p.status == PluginStatus.SUBMITTED.value),
            "suspended": sum(1 for p in plugins if p.status == PluginStatus.SUSPENDED.value),
            "total_downloads": sum(p.downloads for p in plugins),
            "total_developers": len(self._developers),
            "verified_developers": sum(1 for d in self._developers.values() if d.verified),
            "total_reviews": sum(len(r) for r in self._reviews.values()),
            "avg_rating": round(sum(p.rating for p in approved) / max(1, len(approved)), 2),
            "by_category": dict(defaultdict(int, {c: sum(1 for p in approved if p.category == c) for c in set(p.category for p in approved)})),
        }

    def get_dashboard(self) -> dict:
        return {
            "stats": self.get_stats(),
            "featured": [p.to_dict() for p in self.list_plugins(status="approved", sort_by="rating", limit=5)],
            "popular": [p.to_dict() for p in self.list_plugins(status="approved", sort_by="downloads", limit=5)],
            "newest": [p.to_dict() for p in self.list_plugins(status="approved", sort_by="newest", limit=5)],
            "categories": self.list_categories(),
        }


_service: Optional[PluginMarketplaceService] = None

def get_plugin_marketplace_service() -> PluginMarketplaceService:
    global _service
    if _service is None:
        _service = PluginMarketplaceService()
    return _service
