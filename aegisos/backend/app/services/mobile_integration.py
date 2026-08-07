"""
Mobile Wallet EvolvixOS Integration — Phase 48

Bridges the Verdis Android mobile wallet with EvolvixOS features:
staking, governance, identity, analytics, bridge, NFT marketplace,
faucet, block explorer, and notifications.
"""

import secrets
import time
import threading
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from app.core.logging import get_logger

logger = get_logger("service.mobile_integration")


class DevicePlatform(str, Enum):
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"


class SyncStatus(str, Enum):
    SYNCED = "synced"
    PENDING = "pending"
    FAILED = "failed"
    CONFLICT = "conflict"


class FeatureKey(str, Enum):
    STAKING = "staking"
    GOVERNANCE = "governance"
    IDENTITY = "identity"
    ANALYTICS = "analytics"
    BRIDGE = "bridge"
    NFT = "nft"
    FAUCET = "faucet"
    EXPLORER = "explorer"
    NOTIFICATIONS = "notifications"
    WALLET = "wallet"
    TOKENOMICS = "tokenomics"
    VALIDATORS = "validators"


@dataclass
class MobileSession:
    id: str
    wallet_address: str
    device_id: str
    platform: str = DevicePlatform.ANDROID.value
    app_version: str = "2.5.3"
    push_token: str = ""
    features_enabled: list = field(default_factory=lambda: [f.value for f in FeatureKey])
    last_sync: str = ""
    last_seen: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    battery_level: int = 100
    network_type: str = "wifi"
    language: str = "en"
    biometric_enabled: bool = False
    pin_enabled: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MobileFeature:
    key: str
    name: str
    description: str
    icon: str = ""
    available: bool = True
    requires_auth: bool = True
    requires_biometric: bool = False
    min_app_version: str = "2.5.0"
    api_base: str = ""
    enabled_by_default: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SyncRecord:
    id: str
    session_id: str
    feature: str
    status: str = SyncStatus.SYNCED.value
    data_size: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MobileNotification:
    id: str
    session_id: str
    title: str
    body: str
    feature: str = ""
    priority: str = "normal"  # low, normal, high
    read: bool = False
    action_url: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    read_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WalletQuickAction:
    key: str
    label: str
    icon: str = ""
    feature: str = ""
    api_endpoint: str = ""
    params: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class MobileIntegrationService:
    """Mobile wallet EvolvixOS integration service."""

    def __init__(self, max_history: int = 10000):
        self._sessions: dict[str, MobileSession] = {}
        self._sessions_by_wallet: dict[str, list[str]] = defaultdict(list)
        self._sync_history: deque = deque(maxlen=max_history)
        self._notifications: dict[str, list[MobileNotification]] = defaultdict(list)
        self._quick_actions: list[WalletQuickAction] = []
        self._features: dict[str, MobileFeature] = {}
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._init_features()
        self._init_quick_actions()
        self._init_sample_sessions()

    def _init_features(self):
        """Initialize EvolvixOS features available to mobile."""
        features = [
            (FeatureKey.WALLET.value, "Wallet", "Send, receive, and manage VRS tokens", "💰", True, True, False, "2.5.0", "/api/v1/wallet"),
            (FeatureKey.STAKING.value, "Staking", "Stake VRS, view rewards, manage delegations", "🔒", True, True, False, "2.5.0", "/api/v1/staking"),
            (FeatureKey.GOVERNANCE.value, "Governance", "Vote on proposals, view treasury", "🗳️", True, True, True, "2.5.2", "/api/v1/governance"),
            (FeatureKey.IDENTITY.value, "Identity", "Manage DIDs, verifiable credentials", "🪪", True, True, True, "2.5.1", "/api/v1/identity"),
            (FeatureKey.ANALYTICS.value, "Analytics", "On-chain metrics and dashboards", "📊", True, False, False, "2.5.0", "/api/v1/analytics"),
            (FeatureKey.BRIDGE.value, "Bridge", "Cross-chain transfers and monitoring", "🌉", True, True, False, "2.5.2", "/api/v1/bridge"),
            (FeatureKey.NFT.value, "NFT Marketplace", "Mint, buy, sell, and trade NFTs", "🎨", True, True, False, "2.5.3", "/api/v1/nft"),
            (FeatureKey.FAUCET.value, "Faucet", "Get testnet VRS tokens", "🚰", True, False, False, "2.5.0", "/api/v1/faucet"),
            (FeatureKey.EXPLORER.value, "Explorer", "Search blocks, transactions, addresses", "🔍", True, False, False, "2.5.0", "/api/v1/explorer"),
            (FeatureKey.NOTIFICATIONS.value, "Notifications", "Push notifications for events", "🔔", True, False, False, "2.5.0", "/api/v1/notifications"),
            (FeatureKey.TOKENOMICS.value, "Tokenomics", "Token supply, vesting, distribution", "📈", True, False, False, "2.5.1", "/api/v1/tokenomics"),
            (FeatureKey.VALIDATORS.value, "Validators", "Validator management and green scoring", "🌱", True, True, False, "2.5.2", "/api/v1/validators"),
        ]
        for key, name, desc, icon, avail, auth, bio, min_ver, api in features:
            self._features[key] = MobileFeature(
                key=key, name=name, description=desc, icon=icon,
                available=avail, requires_auth=auth, requires_biometric=bio,
                min_app_version=min_ver, api_base=api,
            )

    def _init_quick_actions(self):
        """Initialize mobile quick actions."""
        self._quick_actions = [
            WalletQuickAction(key="send", label="Send", icon="📤", feature="wallet", api_endpoint="/api/v1/wallet/send"),
            WalletQuickAction(key="receive", label="Receive", icon="📥", feature="wallet", api_endpoint="/api/v1/wallet/receive"),
            WalletQuickAction(key="stake", label="Stake", icon="🔒", feature="staking", api_endpoint="/api/v1/staking/stake"),
            WalletQuickAction(key="claim", label="Claim Rewards", icon="🎁", feature="staking", api_endpoint="/api/v1/staking/claim"),
            WalletQuickAction(key="faucet", label="Get Tokens", icon="🚰", feature="faucet", api_endpoint="/api/v1/faucet/claim"),
            WalletQuickAction(key="scan", label="Scan QR", icon="📷", feature="wallet", api_endpoint="/api/v1/wallet/scan"),
            WalletQuickAction(key="vote", label="Vote", icon="🗳️", feature="governance", api_endpoint="/api/v1/governance/vote"),
            WalletQuickAction(key="bridge", label="Bridge", icon="🌉", feature="bridge", api_endpoint="/api/v1/bridge/transfer"),
        ]

    def _init_sample_sessions(self):
        """Initialize sample mobile sessions."""
        import random
        random.seed(42)
        for i in range(20):
            session_id = f"ses-{secrets.token_hex(8)}"
            wallet = f"0x{secrets.token_hex(20)}"
            session = MobileSession(
                id=session_id, wallet_address=wallet,
                device_id=f"dev-{secrets.token_hex(8)}",
                platform="android", app_version=random.choice(["2.5.3", "2.5.2", "2.5.1"]),
                battery_level=random.randint(15, 100),
                network_type=random.choice(["wifi", "4g", "5g", "3g"]),
                biometric_enabled=random.random() > 0.5,
            )
            self._sessions[session_id] = session
            self._sessions_by_wallet[wallet].append(session_id)

    # === Sessions ===

    def register_session(self, wallet_address: str, device_id: str,
                         platform: str = DevicePlatform.ANDROID.value,
                         app_version: str = "2.5.3", push_token: str = "",
                         language: str = "en", biometric: bool = False) -> MobileSession:
        """Register a new mobile session."""
        session_id = f"ses-{secrets.token_hex(8)}"
        session = MobileSession(
            id=session_id, wallet_address=wallet_address,
            device_id=device_id, platform=platform,
            app_version=app_version, push_token=push_token,
            language=language, biometric_enabled=biometric,
        )
        with self._lock:
            self._sessions[session_id] = session
            self._sessions_by_wallet[wallet_address].append(session_id)
        logger.info("mobile_session_registered", session_id=session_id, wallet=wallet_address, platform=platform)
        return session

    def get_session(self, session_id: str) -> Optional[MobileSession]:
        return self._sessions.get(session_id)

    def get_wallet_sessions(self, wallet_address: str) -> list[MobileSession]:
        session_ids = self._sessions_by_wallet.get(wallet_address, [])
        return [self._sessions[sid] for sid in session_ids if sid in self._sessions]

    def update_session(self, session_id: str, **kwargs) -> Optional[MobileSession]:
        session = self._sessions.get(session_id)
        if not session:
            return None
        for k, v in kwargs.items():
            if hasattr(session, k):
                setattr(session, k, v)
        session.last_seen = datetime.utcnow().isoformat()
        return session

    def deactivate_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        if session_id in self._sessions_by_wallet.get(session.wallet_address, []):
            self._sessions_by_wallet[session.wallet_address].remove(session_id)
        del self._sessions[session_id]
        return True

    def list_sessions(self, platform: str = None, limit: int = 50) -> list[MobileSession]:
        sessions = list(self._sessions.values())
        if platform:
            sessions = [s for s in sessions if s.platform == platform]
        sessions.sort(key=lambda s: s.last_seen, reverse=True)
        return sessions[:limit]

    # === Features ===

    def list_features(self, app_version: str = "2.5.3") -> list[MobileFeature]:
        """List features available for the app version."""
        available = []
        for f in self._features.values():
            # Check version compatibility
            if self._version_compatible(app_version, f.min_app_version):
                available.append(f)
        return available

    def get_feature(self, key: str) -> Optional[MobileFeature]:
        return self._features.get(key)

    def _version_compatible(self, app_ver: str, min_ver: str) -> bool:
        app_parts = [int(x) for x in app_ver.split(".")]
        min_parts = [int(x) for x in min_ver.split(".")]
        while len(app_parts) < 3: app_parts.append(0)
        while len(min_parts) < 3: min_parts.append(0)
        return app_parts >= min_parts

    def toggle_feature(self, session_id: str, feature_key: str, enabled: bool) -> Optional[MobileSession]:
        session = self._sessions.get(session_id)
        if not session:
            return None
        if enabled and feature_key not in session.features_enabled:
            session.features_enabled.append(feature_key)
        elif not enabled and feature_key in session.features_enabled:
            session.features_enabled.remove(feature_key)
        return session

    # === Quick Actions ===

    def list_quick_actions(self) -> list[WalletQuickAction]:
        return self._quick_actions

    # === Sync ===

    def sync_feature(self, session_id: str, feature: str, data_size: int = 0) -> SyncRecord:
        """Record a sync event for a feature."""
        record = SyncRecord(
            id=f"sync-{secrets.token_hex(8)}",
            session_id=session_id, feature=feature,
            status=SyncStatus.SYNCED.value, data_size=data_size,
        )
        self._sync_history.append(record)

        # Update session last sync
        session = self._sessions.get(session_id)
        if session:
            session.last_sync = datetime.utcnow().isoformat()

        return record

    def get_sync_history(self, session_id: str = None, feature: str = None,
                         limit: int = 50) -> list[SyncRecord]:
        records = list(self._sync_history)
        if session_id:
            records = [r for r in records if r.session_id == session_id]
        if feature:
            records = [r for r in records if r.feature == feature]
        records.reverse()
        return records[:limit]

    # === Notifications ===

    def send_notification(self, session_id: str, title: str, body: str,
                          feature: str = "", priority: str = "normal",
                          action_url: str = "") -> Optional[MobileNotification]:
        session = self._sessions.get(session_id)
        if not session:
            return None
        notif_id = f"ntf-{secrets.token_hex(8)}"
        notif = MobileNotification(
            id=notif_id, session_id=session_id,
            title=title, body=body, feature=feature,
            priority=priority, action_url=action_url,
        )
        self._notifications[session_id].append(notif)
        return notif

    def broadcast_notification(self, wallet_address: str, title: str, body: str,
                               feature: str = "", priority: str = "normal") -> list[MobileNotification]:
        """Send notification to all sessions for a wallet."""
        session_ids = self._sessions_by_wallet.get(wallet_address, [])
        results = []
        for sid in session_ids:
            n = self.send_notification(sid, title, body, feature, priority)
            if n:
                results.append(n)
        return results

    def get_notifications(self, session_id: str, unread_only: bool = False,
                         limit: int = 50) -> list[MobileNotification]:
        notifs = self._notifications.get(session_id, [])
        if unread_only:
            notifs = [n for n in notifs if not n.read]
        notifs.sort(key=lambda n: n.created, reverse=True)
        return notifs[:limit]

    def mark_read(self, session_id: str, notification_id: str) -> bool:
        notifs = self._notifications.get(session_id, [])
        for n in notifs:
            if n.id == notification_id:
                n.read = True
                n.read_at = datetime.utcnow().isoformat()
                return True
        return False

    def mark_all_read(self, session_id: str) -> int:
        notifs = self._notifications.get(session_id, [])
        count = 0
        for n in notifs:
            if not n.read:
                n.read = True
                n.read_at = datetime.utcnow().isoformat()
                count += 1
        return count

    # === Mobile Dashboard ===

    def get_mobile_dashboard(self, session_id: str) -> dict:
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        return {
            "session": session.to_dict(),
            "features": [f.to_dict() for f in self.list_features(session.app_version)],
            "quick_actions": [a.to_dict() for a in self._quick_actions],
            "unread_notifications": len(self.get_notifications(session_id, unread_only=True)),
            "last_sync": session.last_sync,
            "sync_count": len([r for r in self._sync_history if r.session_id == session_id]),
        }

    # === App Config ===

    def get_app_config(self, app_version: str = "2.5.3") -> dict:
        return {
            "min_version": "2.5.0",
            "latest_version": "2.5.3",
            "update_required": self._version_compatible(app_version, "2.5.0") == False,
            "features": [f.to_dict() for f in self.list_features(app_version)],
            "quick_actions": [a.to_dict() for a in self._quick_actions],
            "network": {
                "chain_id": 909,
                "rpc_url": "https://testnet.verdischain.com",
                "explorer_url": "https://verdiscan.verdischain.com",
                "faucet_url": "https://faucet.verdischain.com",
            },
            "settings": {
                "default_currency": "VRS",
                "language": "en",
                "theme": "dark",
                "biometric_supported": True,
            },
        }

    # === Stats ===

    def get_stats(self) -> dict:
        total_sessions = len(self._sessions)
        android = sum(1 for s in self._sessions.values() if s.platform == "android")
        ios = sum(1 for s in self._sessions.values() if s.platform == "ios")
        biometric = sum(1 for s in self._sessions.values() if s.biometric_enabled)
        total_syncs = len(self._sync_history)
        total_notifs = sum(len(n) for n in self._notifications.values())
        unread = sum(1 for n_list in self._notifications.values() for n in n_list if not n.read)
        unique_wallets = len(self._sessions_by_wallet)

        return {
            "total_sessions": total_sessions,
            "android_sessions": android,
            "ios_sessions": ios,
            "biometric_enabled": biometric,
            "unique_wallets": unique_wallets,
            "total_syncs": total_syncs,
            "total_notifications": total_notifs,
            "unread_notifications": unread,
            "total_features": len(self._features),
            "quick_actions": len(self._quick_actions),
        }

    def get_dashboard(self) -> dict:
        return {
            "stats": self.get_stats(),
            "recent_sessions": [s.to_dict() for s in self.list_sessions(limit=10)],
            "features": [f.to_dict() for f in self._features.values()],
            "quick_actions": [a.to_dict() for a in self._quick_actions],
            "monitoring": self._monitoring,
        }

    # === Monitoring ===

    def start_monitoring(self, interval: int = 120):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("mobile_monitoring_started", interval=interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int):
        while self._monitoring:
            try:
                # Auto-sync all active sessions
                now = datetime.utcnow()
                for session in self._sessions.values():
                    last = datetime.fromisoformat(session.last_seen.replace("Z", "")) if session.last_seen else now
                    if (now - last).total_seconds() < 300:  # Active in last 5 min
                        self.sync_feature(session.id, "wallet", 1024)
            except Exception as e:
                logger.error("monitor_error", error=str(e))
            time.sleep(interval)

    def is_monitoring(self) -> bool:
        return self._monitoring


_service: Optional[MobileIntegrationService] = None

def get_mobile_integration_service() -> MobileIntegrationService:
    global _service
    if _service is None:
        _service = MobileIntegrationService()
    return _service
