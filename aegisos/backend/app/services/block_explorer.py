"""
Block Explorer API — Phase 47

Programmatic access to Verdis blockchain data: blocks, transactions,
addresses, contracts, events, logs, and network statistics.
"""

import secrets
import time
import threading
import hashlib
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from app.core.logging import get_logger

logger = get_logger("service.block_explorer")


class TxStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class TxType(str, Enum):
    TRANSFER = "transfer"
    STAKE = "stake"
    UNSTAKE = "unstake"
    REWARD = "reward"
    SLASH = "slash"
    CONTRACT_CALL = "contract_call"
    CONTRACT_DEPLOY = "contract_deploy"
    GOVERNANCE = "governance"
    BRIDGE = "bridge"
    NFT_MINT = "nft_mint"
    NFT_TRANSFER = "nft_transfer"
    VALIDATOR = "validator"


@dataclass
class Block:
    height: int
    hash: str
    parent_hash: str
    timestamp: str
    proposer: str
    tx_count: int = 0
    size: int = 0
    gas_used: int = 0
    gas_limit: int = 30_000_000
    validator: str = ""
    epoch: int = 0
    transactions: list = field(default_factory=list)
    extra_data: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Transaction:
    hash: str
    block_height: int
    block_hash: str
    tx_index: int = 0
    from_address: str = ""
    to_address: str = ""
    value: float = 0.0
    gas_price: int = 1
    gas_used: int = 0
    status: str = TxStatus.SUCCESS.value
    tx_type: str = TxType.TRANSFER.value
    nonce: int = 0
    input_data: str = ""
    contract_address: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    fee: float = 0.0
    logs: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AddressInfo:
    address: str
    balance: float = 0.0
    tx_count: int = 0
    sent_count: int = 0
    received_count: int = 0
    first_seen: str = ""
    last_active: str = ""
    is_contract: bool = False
    is_validator: bool = False
    is_contract_creator: bool = False
    contract_name: str = ""
    token_holds: list = field(default_factory=list)
    staked: float = 0.0
    rewards: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ContractInfo:
    address: str
    name: str
    creator: str
    created_at: str
    tx_hash: str
    bytecode_hash: str
    abi: str = ""
    source_verified: bool = False
    standard: str = ""  # VRC-20, VRC-721, etc.
    calls: int = 0
    verified: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EventLog:
    log_index: int
    tx_hash: str
    block_height: int
    address: str
    topic0: str
    topic1: str = ""
    topic2: str = ""
    topic3: str = ""
    data: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class BlockExplorerService:
    """Block explorer with full blockchain data access."""

    def __init__(self, max_history: int = 50000):
        self._blocks: dict[int, Block] = {}
        self._block_by_hash: dict[str, int] = {}
        self._transactions: dict[str, Transaction] = {}
        self._tx_by_block: dict[int, list[str]] = defaultdict(list)
        self._tx_by_address: dict[str, list[str]] = defaultdict(list)
        self._addresses: dict[str, AddressInfo] = {}
        self._contracts: dict[str, ContractInfo] = {}
        self._logs: deque = deque(maxlen=max_history)
        self._current_height = 0
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._init_sample_data()

    def _init_sample_data(self):
        """Initialize with sample blockchain data."""
        import random
        random.seed(42)

        validators = [f"0xval{i:02d}" + secrets.token_hex(18) for i in range(14)]
        addresses = [f"0x{secrets.token_hex(20)}" for _ in range(50)]
        contract_names = ["VerdisToken", "AmmDex", "CarbonCredits", "StakingPool", "Governance", "NFTRegistry", "BridgeRelayer"]
        tx_types = [t.value for t in TxType]

        base_height = 18_000_000

        for i in range(500):
            height = base_height + i
            block_hash = f"0x{secrets.token_hex(32)}"
            parent_hash = f"0x{secrets.token_hex(32)}" if i > 0 else "0x" + "00" * 32
            proposer = random.choice(validators)
            tx_count = random.randint(1, 25)
            block_ts = (datetime.utcnow() - timedelta(seconds=(500 - i) * 6)).isoformat()

            block = Block(
                height=height, hash=block_hash, parent_hash=parent_hash,
                timestamp=block_ts, proposer=proposer, tx_count=tx_count,
                size=random.randint(1000, 50000),
                gas_used=random.randint(100000, 25000000),
                validator=proposer, epoch=i // 1000,
            )

            # Generate transactions for this block
            for j in range(tx_count):
                tx_hash = f"0x{secrets.token_hex(32)}"
                from_addr = random.choice(addresses)
                contract_addrs = [c for c in self._contracts] if i >= 7 else []
                to_addr = random.choice(addresses + contract_addrs) if (addresses + contract_addrs) else random.choice(addresses)
                tx_type = random.choice(tx_types)
                value = round(random.uniform(0, 10000), 4) if tx_type in ["transfer", "stake", "unstake", "reward"] else 0
                gas_used = random.randint(21000, 500000)
                status = random.choices([TxStatus.SUCCESS.value, TxStatus.FAILED.value], weights=[95, 5])[0]

                tx = Transaction(
                    hash=tx_hash, block_height=height, block_hash=block_hash,
                    tx_index=j, from_address=from_addr, to_address=to_addr,
                    value=value, gas_used=gas_used, status=status, tx_type=tx_type,
                    nonce=random.randint(0, 1000),
                    fee=round(gas_used * 1 / 1e9, 6),
                    timestamp=block_ts,
                )
                self._transactions[tx_hash] = tx
                self._tx_by_block[height].append(tx_hash)
                self._tx_by_address[from_addr].append(tx_hash)
                if to_addr:
                    self._tx_by_address[to_addr].append(tx_hash)
                block.transactions.append(tx_hash)

                # Generate event logs for contract calls
                if tx_type in ["contract_call", "contract_deploy", "nft_mint"] and random.random() > 0.5:
                    for k in range(random.randint(1, 3)):
                        log = EventLog(
                            log_index=k, tx_hash=tx_hash, block_height=height,
                            address=to_addr if to_addr else from_addr,
                            topic0=f"0x{secrets.token_hex(32)}",
                            topic1=f"0x{secrets.token_hex(32)}" if random.random() > 0.5 else "",
                            topic2=f"0x{secrets.token_hex(32)}" if random.random() > 0.5 else "",
                            data=f"0x{secrets.token_hex(64)}",
                            timestamp=block_ts,
                        )
                        self._logs.append(log)

                # Update address info
                self._update_address(from_addr, is_sender=True, tx_type=tx_type, value=value)
                self._update_address(to_addr, is_receiver=True, tx_type=tx_type, value=value)

            self._blocks[height] = block
            self._block_by_hash[block_hash] = height

            if i < 7:
                # Create some contracts
                contract_addr = to_addr if to_addr else f"0x{secrets.token_hex(20)}"
                self._contracts[contract_addr] = ContractInfo(
                    address=contract_addr, name=contract_names[i],
                    creator=from_addr, created_at=block_ts,
                    tx_hash=tx_hash, bytecode_hash=f"0x{secrets.token_hex(32)}",
                    standard=random.choice(["VRC-20", "VRC-721", "VRC-1155", ""]),
                    calls=random.randint(10, 1000),
                    verified=random.random() > 0.3,
                )

        self._current_height = base_height + 499

    def _update_address(self, address: str, is_sender: bool = False, is_receiver: bool = False,
                        tx_type: str = "transfer", value: float = 0):
        if not address:
            return
        if address not in self._addresses:
            self._addresses[address] = AddressInfo(
                address=address,
                first_seen=datetime.utcnow().isoformat(),
            )
        addr = self._addresses[address]
        addr.last_active = datetime.utcnow().isoformat()
        addr.tx_count += 1
        if is_sender:
            addr.sent_count += 1
            addr.balance -= value
        if is_receiver:
            addr.received_count += 1
            addr.balance += value
        if tx_type == "stake":
            addr.staked += value
        elif tx_type == "reward":
            addr.rewards += value

    # === Blocks ===

    def get_block(self, height: int = None, block_hash: str = None) -> Optional[Block]:
        if height is not None:
            return self._blocks.get(height)
        if block_hash:
            h = self._block_by_hash.get(block_hash)
            return self._blocks.get(h) if h else None
        return None

    def list_blocks(self, limit: int = 50, offset: int = 0) -> list[Block]:
        heights = sorted(self._blocks.keys(), reverse=True)
        paginated = heights[offset:offset + limit]
        return [self._blocks[h] for h in paginated]

    def get_latest_blocks(self, limit: int = 20) -> list[Block]:
        return self.list_blocks(limit=limit)

    def get_block_transactions(self, height: int, limit: int = 50) -> list[Transaction]:
        tx_hashes = self._tx_by_block.get(height, [])
        return [self._transactions[h] for h in tx_hashes[:limit] if h in self._transactions]

    # === Transactions ===

    def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        return self._transactions.get(tx_hash)

    def list_transactions(self, address: str = None, tx_type: str = None,
                          status: str = None, limit: int = 50,
                          offset: int = 0, sort_by: str = "timestamp") -> list[Transaction]:
        txs = list(self._transactions.values())
        if address:
            txs = [t for t in txs if t.from_address == address or t.to_address == address]
        if tx_type:
            txs = [t for t in txs if t.tx_type == tx_type]
        if status:
            txs = [t for t in txs if t.status == status]

        sort_map = {"timestamp": lambda t: t.timestamp, "value": lambda t: t.value, "gas_used": lambda t: t.gas_used}
        txs.sort(key=sort_map.get(sort_by, lambda t: t.timestamp), reverse=True)
        return txs[offset:offset + limit]

    # === Addresses ===

    def get_address(self, address: str) -> Optional[AddressInfo]:
        info = self._addresses.get(address)
        if not info:
            return None
        info.is_contract = address in self._contracts
        if info.is_contract:
            c = self._contracts[address]
            info.contract_name = c.name
        return info

    def get_address_transactions(self, address: str, limit: int = 50,
                                  offset: int = 0) -> list[Transaction]:
        tx_hashes = self._tx_by_address.get(address, [])
        paginated = tx_hashes[offset:offset + limit]
        return [self._transactions[h] for h in paginated if h in self._transactions]

    def list_top_addresses(self, sort_by: str = "balance", limit: int = 50) -> list[AddressInfo]:
        addresses = [a for a in self._addresses.values() if a.address.startswith("0x") and len(a.address) == 42]
        sort_map = {"balance": lambda a: a.balance, "tx_count": lambda a: a.tx_count,
                    "staked": lambda a: a.staked, "rewards": lambda a: a.rewards}
        addresses.sort(key=sort_map.get(sort_by, lambda a: a.balance), reverse=True)
        return addresses[:limit]

    # === Contracts ===

    def get_contract(self, address: str) -> Optional[ContractInfo]:
        return self._contracts.get(address)

    def list_contracts(self, verified: bool = None, standard: str = None,
                       limit: int = 50) -> list[ContractInfo]:
        contracts = list(self._contracts.values())
        if verified is not None:
            contracts = [c for c in contracts if c.verified == verified]
        if standard:
            contracts = [c for c in contracts if c.standard == standard]
        contracts.sort(key=lambda c: c.calls, reverse=True)
        return contracts[:limit]

    # === Event Logs ===

    def list_logs(self, address: str = None, tx_hash: str = None,
                  block_height: int = None, topic0: str = None,
                  limit: int = 100, offset: int = 0) -> list[EventLog]:
        logs = list(self._logs)
        if address:
            logs = [l for l in logs if l.address == address]
        if tx_hash:
            logs = [l for l in logs if l.tx_hash == tx_hash]
        if block_height is not None:
            logs = [l for l in logs if l.block_height == block_height]
        if topic0:
            logs = [l for l in logs if l.topic0 == topic0]
        logs.reverse()
        return logs[offset:offset + limit]

    # === Search ===

    def search(self, query: str) -> dict:
        """Search for block, transaction, address, or contract."""
        query = query.strip()
        results = {"query": query, "type": "unknown", "data": None}

        # Try block height
        try:
            height = int(query)
            block = self.get_block(height=height)
            if block:
                results["type"] = "block"
                results["data"] = block.to_dict()
                return results
        except ValueError:
            pass

        # Try tx hash
        if query.startswith("0x") and len(query) == 66:
            tx = self.get_transaction(query)
            if tx:
                results["type"] = "transaction"
                results["data"] = tx.to_dict()
                return results
            block = self.get_block(block_hash=query)
            if block:
                results["type"] = "block"
                results["data"] = block.to_dict()
                return results

        # Try address
        if query.startswith("0x"):
            addr = self.get_address(query)
            if addr:
                results["type"] = "address"
                results["data"] = addr.to_dict()
                return results
            contract = self.get_contract(query)
            if contract:
                results["type"] = "contract"
                results["data"] = contract.to_dict()
                return results

        # Partial match
        matching_txs = [h for h in self._transactions if h.startswith(query)]
        if matching_txs:
            results["type"] = "transaction_list"
            results["data"] = matching_txs[:5]
            return results

        results["error"] = "No results found"
        return results

    # === Network Stats ===

    def get_network_stats(self) -> dict:
        total_blocks = len(self._blocks)
        total_txs = len(self._transactions)
        successful = sum(1 for t in self._transactions.values() if t.status == "success")
        failed = sum(1 for t in self._transactions.values() if t.status == "failed")
        total_addresses = len(self._addresses)
        total_contracts = len(self._contracts)
        total_volume = sum(t.value for t in self._transactions.values() if t.status == "success")
        avg_gas = sum(t.gas_used for t in self._transactions.values()) / max(1, total_txs)
        avg_block_size = sum(b.size for b in self._blocks.values()) / max(1, total_blocks)
        avg_txs_per_block = total_txs / max(1, total_blocks)

        return {
            "current_height": self._current_height,
            "total_blocks": total_blocks,
            "total_transactions": total_txs,
            "successful_transactions": successful,
            "failed_transactions": failed,
            "success_rate": round(successful / max(1, total_txs) * 100, 2),
            "total_addresses": total_addresses,
            "total_contracts": total_contracts,
            "total_volume": round(total_volume, 2),
            "avg_gas_per_tx": round(avg_gas),
            "avg_block_size": round(avg_block_size),
            "avg_txs_per_block": round(avg_txs_per_block, 1),
            "block_time": 6,  # seconds
            "tps": round(total_txs / max(1, total_blocks * 6), 2),
        }

    def get_dashboard(self) -> dict:
        return {
            "network_stats": self.get_network_stats(),
            "latest_blocks": [b.to_dict() for b in self.get_latest_blocks(10)],
            "latest_transactions": [t.to_dict() for t in self.list_transactions(limit=10)],
            "top_addresses": [a.to_dict() for a in self.list_top_addresses(limit=10)],
            "contracts": [c.to_dict() for c in self.list_contracts(limit=10)],
            "monitoring": self._monitoring,
        }

    # === Monitoring ===

    def start_monitoring(self, interval: int = 6):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("block_explorer_monitoring_started", interval=interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int):
        while self._monitoring:
            try:
                # Simulate new block
                self._current_height += 1
                height = self._current_height
                block_hash = f"0x{secrets.token_hex(32)}"
                parent_hash = self._blocks.get(height - 1, Block(0, "", "")).hash

                block = Block(
                    height=height, hash=block_hash, parent_hash=parent_hash,
                    timestamp=datetime.utcnow().isoformat(),
                    proposer=f"0xval{secrets.randbelow(14):02d}",
                    tx_count=secrets.randbelow(20) + 1,
                    size=secrets.randbelow(40000) + 1000,
                    gas_used=secrets.randbelow(25000000) + 100000,
                    validator=f"0xval{secrets.randbelow(14):02d}",
                )
                with self._lock:
                    self._blocks[height] = block
                    self._block_by_hash[block_hash] = height
            except Exception as e:
                logger.error("monitor_error", error=str(e))
            time.sleep(interval)

    def is_monitoring(self) -> bool:
        return self._monitoring


_service: Optional[BlockExplorerService] = None

def get_block_explorer_service() -> BlockExplorerService:
    global _service
    if _service is None:
        _service = BlockExplorerService()
    return _service
