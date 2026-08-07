"""
Transaction Security Service — Phase 27

Provides transaction signing, verification, and encryption for
secure wallet operations.
"""

import hashlib
import hmac
import json
import secrets
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
import threading
from app.core.logging import get_logger

logger = get_logger("service.tx_security")


@dataclass
class SignedTransaction:
    tx_id: str
    sender: str
    recipient: str
    amount: str
    timestamp: str
    signature: str
    nonce: int
    chain_id: int = 909

    def to_dict(self) -> dict:
        return asdict(self)


class TransactionSecurityService:
    """Secure transaction signing and verification."""

    def __init__(self, max_history: int = 5000):
        self._transactions: dict[str, SignedTransaction] = {}
        self._nonces: dict[str, int] = {}
        self._max = max_history
        self._lock = threading.Lock()
        self._chain_id = 909

    @staticmethod
    def _hash_payload(sender: str, recipient: str, amount: str, nonce: int, chain_id: int, timestamp: str) -> str:
        """Create SHA-256 hash of transaction payload."""
        payload = f"{sender}|{recipient}|{amount}|{nonce}|{chain_id}|{timestamp}"
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def _sign(hash_str: str, private_key: str) -> str:
        """Sign a hash with HMAC-SHA256 (simulated key signing)."""
        return hmac.new(private_key.encode(), hash_str.encode(), hashlib.sha256).hexdigest()

    def create_transaction(
        self, sender: str, recipient: str, amount: str, private_key: str
    ) -> SignedTransaction:
        """Create and sign a new transaction."""
        with self._lock:
            nonce = self._nonces.get(sender, 0)
            timestamp = datetime.utcnow().isoformat()
            tx_id = secrets.token_hex(16)

            # Create payload hash
            payload_hash = self._hash_payload(
                sender, recipient, amount, nonce, self._chain_id, timestamp
            )

            # Sign
            signature = self._sign(payload_hash, private_key)

            tx = SignedTransaction(
                tx_id=tx_id,
                sender=sender,
                recipient=recipient,
                amount=amount,
                timestamp=timestamp,
                signature=signature,
                nonce=nonce,
                chain_id=self._chain_id,
            )

            # Store
            self._transactions[tx_id] = tx
            self._nonces[sender] = nonce + 1

            # Trim history
            if len(self._transactions) > self._max:
                oldest = min(self._transactions.keys(), key=lambda k: self._transactions[k].timestamp)
                del self._transactions[oldest]

        logger.info("tx_signed", tx_id=tx_id, sender=sender, amount=amount)
        return tx

    def verify_transaction(self, tx: SignedTransaction, public_key: str) -> bool:
        """Verify a transaction signature."""
        try:
            # Recreate payload hash
            payload_hash = self._hash_payload(
                tx.sender, tx.recipient, tx.amount, tx.nonce, tx.chain_id, tx.timestamp
            )
            # Verify signature (in production, use proper ECDSA verification)
            expected_sig = self._sign(payload_hash, public_key)
            return hmac.compare_digest(tx.signature, expected_sig)
        except Exception:
            return False

    def get_transaction(self, tx_id: str) -> Optional[SignedTransaction]:
        return self._transactions.get(tx_id)

    def get_nonce(self, address: str) -> int:
        return self._nonces.get(address, 0)

    def get_history(self, address: str, limit: int = 20) -> list[SignedTransaction]:
        """Get transaction history for an address (sender or receiver)."""
        txs = [
            tx for tx in self._transactions.values()
            if tx.sender == address or tx.recipient == address
        ]
        txs.sort(key=lambda t: t.timestamp, reverse=True)
        return txs[:limit]

    def get_stats(self) -> dict:
        return {
            "total_transactions": len(self._transactions),
            "unique_senders": len(self._nonces),
            "chain_id": self._chain_id,
        }


_service: Optional[TransactionSecurityService] = None

def get_tx_security_service() -> TransactionSecurityService:
    global _service
    if _service is None:
        _service = TransactionSecurityService()
    return _service
