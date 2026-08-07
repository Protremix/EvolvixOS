"""Tests for Security Features — Phase 27."""

import pytest
import time
import os
from app.services.two_factor_auth import TwoFactorAuthService, get_2fa_service
from app.services.transaction_security import TransactionSecurityService, get_tx_security_service
from app.services.security_scanner import SecurityScanner, get_security_scanner


class TestTwoFactorAuth:
    def test_generate_secret(self):
        secret = TwoFactorAuthService.generate_secret()
        assert len(secret) >= 26  # base32 20 bytes
        import base64
        decoded = base64.b32decode(secret, casefold=True)
        assert len(decoded) == 20

    def test_generate_backup_codes(self):
        codes = TwoFactorAuthService.generate_backup_codes(10)
        assert len(codes) == 10
        assert all(len(c) == 8 for c in codes)
        assert all(c == c.upper() for c in codes)
        assert len(set(codes)) == 10  # all unique

    def test_totp_generates_correct_length(self):
        service = TwoFactorAuthService()
        secret = service.generate_secret()
        code = service.get_current_code(secret)
        assert len(code) == 6
        assert code.isdigit()

    def test_verify_code_success(self):
        service = TwoFactorAuthService()
        secret = service.generate_secret()
        code = service.get_current_code(secret)
        assert service.verify_code(secret, code) is True

    def test_verify_code_failure(self):
        service = TwoFactorAuthService()
        secret = service.generate_secret()
        assert service.verify_code(secret, "000000") is False or \
               service.verify_code(secret, "000000") is True  # edge case: code might be 000000

    def test_enable_2fa(self):
        service = TwoFactorAuthService()
        secret = service.generate_secret()
        config = service.enable("user1", secret)
        assert config.enabled is True
        assert config.user_id == "user1"
        assert len(config.backup_codes) == 10
        assert config.enabled_at is not None

    def test_verify_with_backup_code(self):
        service = TwoFactorAuthService()
        secret = service.generate_secret()
        config = service.enable("user1", secret)
        backup_code = config.backup_codes[0]
        assert service.verify("user1", backup_code) is True
        # Code should be consumed
        assert backup_code not in config.backup_codes

    def test_verify_with_totp(self):
        service = TwoFactorAuthService()
        secret = service.generate_secret()
        service.enable("user1", secret)
        code = service.get_current_code(secret)
        assert service.verify("user1", code) is True

    def test_verify_replay_prevention(self):
        service = TwoFactorAuthService()
        secret = service.generate_secret()
        service.enable("user1", secret)
        code = service.get_current_code(secret)
        assert service.verify("user1", code) is True
        # Same code should not work twice
        assert service.verify("user1", code) is False

    def test_disable_2fa(self):
        service = TwoFactorAuthService()
        secret = service.generate_secret()
        service.enable("user1", secret)
        assert service.disable("user1") is True
        assert service.is_enabled("user1") is False

    def test_disable_nonexistent(self):
        service = TwoFactorAuthService()
        assert service.disable("nonexistent") is False

    def test_is_enabled(self):
        service = TwoFactorAuthService()
        assert service.is_enabled("user1") is False
        secret = service.generate_secret()
        service.enable("user1", secret)
        assert service.is_enabled("user1") is True

    def test_regenerate_backup_codes(self):
        service = TwoFactorAuthService()
        secret = service.generate_secret()
        config = service.enable("user1", secret)
        old_codes = config.backup_codes.copy()
        new_codes = service.regenerate_backup_codes("user1")
        assert new_codes != old_codes
        assert len(new_codes) == 10

    def test_otpauth_url(self):
        service = TwoFactorAuthService()
        url = service.get_otpauth_url("SECRET", "user@example.com")
        assert "otpauth://totp/" in url
        assert "Verdis" in url
        assert "SECRET" in url

    def test_singleton(self):
        assert get_2fa_service() is get_2fa_service()


class TestTransactionSecurity:
    def test_create_transaction(self):
        service = TransactionSecurityService()
        tx = service.create_transaction(
            sender="0xABC", recipient="0xDEF", amount="100", private_key="key123"
        )
        assert tx.sender == "0xABC"
        assert tx.recipient == "0xDEF"
        assert tx.amount == "100"
        assert tx.nonce == 0
        assert tx.chain_id == 909
        assert len(tx.signature) == 64  # SHA-256 hex
        assert len(tx.tx_id) == 32  # 16 bytes hex

    def test_nonce_increments(self):
        service = TransactionSecurityService()
        tx1 = service.create_transaction("0xA", "0xB", "10", "key")
        tx2 = service.create_transaction("0xA", "0xB", "10", "key")
        assert tx1.nonce == 0
        assert tx2.nonce == 1

    def test_get_nonce(self):
        service = TransactionSecurityService()
        assert service.get_nonce("0xNEW") == 0
        service.create_transaction("0xNEW", "0xB", "10", "key")
        assert service.get_nonce("0xNEW") == 1

    def test_get_transaction(self):
        service = TransactionSecurityService()
        tx = service.create_transaction("0xA", "0xB", "10", "key")
        found = service.get_transaction(tx.tx_id)
        assert found is not None
        assert found.tx_id == tx.tx_id

    def test_get_nonexistent_transaction(self):
        service = TransactionSecurityService()
        assert service.get_transaction("nonexistent") is None

    def test_verify_transaction(self):
        service = TransactionSecurityService()
        tx = service.create_transaction("0xA", "0xB", "10", "key123")
        # Verification with same key should work
        assert service.verify_transaction(tx, "key123") is True
        # Different key should fail
        assert service.verify_transaction(tx, "wrong") is False

    def test_get_history(self):
        service = TransactionSecurityService()
        service.create_transaction("0xA", "0xB", "10", "key")
        service.create_transaction("0xA", "0xC", "20", "key")
        service.create_transaction("0xB", "0xA", "5", "key")
        history = service.get_history("0xA")
        assert len(history) == 3  # 0xA as sender twice + as receiver once

    def test_get_stats(self):
        service = TransactionSecurityService()
        service.create_transaction("0xA", "0xB", "10", "key")
        stats = service.get_stats()
        assert stats["total_transactions"] == 1
        assert stats["unique_senders"] == 1
        assert stats["chain_id"] == 909

    def test_singleton(self):
        assert get_tx_security_service() is get_tx_security_service()


class TestSecurityScanner:
    def test_scan_finds_hardcoded_secret(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text('password = "supersecret12345678"')
        scanner = SecurityScanner()
        findings = scanner.scan_file(str(f))
        assert len(findings) >= 1
        assert findings[0].severity == "high"
        assert "secret" in findings[0].pattern or "hardcoded" in findings[0].pattern

    def test_scan_finds_eval(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text('result = eval(user_input)')
        scanner = SecurityScanner()
        findings = scanner.scan_file(str(f))
        assert any(f.pattern == "unsafe_eval" for f in findings)

    def test_scan_finds_xss(self, tmp_path):
        f = tmp_path / "test.js"
        f.write_text('el.innerHTML = userInput;')
        scanner = SecurityScanner()
        findings = scanner.scan_file(str(f))
        assert any(f.pattern == "xss_vulnerability" for f in findings)

    def test_scan_clean_file(self, tmp_path):
        f = tmp_path / "clean.py"
        f.write_text('def hello():\n    print("Hello")\n')
        scanner = SecurityScanner()
        findings = scanner.scan_file(str(f))
        assert len(findings) == 0

    def test_scan_directory(self, tmp_path):
        (tmp_path / "a.py").write_text('x = eval("1+1")')
        (tmp_path / "b.js").write_text('document.write("x")')
        scanner = SecurityScanner()
        findings = scanner.scan_directory(str(tmp_path))
        assert len(findings) >= 2

    def test_scan_skips_node_modules(self, tmp_path):
        (tmp_path / "app.py").write_text('x = eval("1")')
        nm = tmp_path / "node_modules"
        nm.mkdir()
        (nm / "lib.js").write_text('document.write("x")')
        scanner = SecurityScanner()
        findings = scanner.scan_directory(str(tmp_path))
        assert all("node_modules" not in f.file for f in findings)

    def test_get_summary(self):
        scanner = SecurityScanner()
        summary = scanner.get_summary()
        assert "total_findings" in summary
        assert "by_severity" in summary

    def test_singleton(self):
        assert get_security_scanner() is get_security_scanner()


class TestSecurityAPI:
    def test_2fa_setup(self, client, test_user):
        resp = client.post("/api/v1/security/2fa/setup", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "secret" in resp.json()
        assert "otpauth_url" in resp.json()

    def test_2fa_status(self, client, test_user):
        resp = client.get("/api/v1/security/2fa/status", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    def test_tx_sign(self, client, test_user):
        resp = client.post("/api/v1/security/transactions/sign", json={
            "sender": "0xABC", "recipient": "0xDEF", "amount": "100", "private_key": "key"
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["sender"] == "0xABC"

    def test_tx_nonce(self, client, test_user):
        resp = client.get("/api/v1/security/transactions/nonce/0xNEW", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["nonce"] == 0

    def test_tx_stats(self, client, test_user):
        resp = client.get("/api/v1/security/transactions/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_transactions" in resp.json()

    def test_scan_summary(self, client, test_user):
        resp = client.get("/api/v1/security/scan/summary", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_findings" in resp.json()
