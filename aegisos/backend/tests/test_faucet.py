"""Tests for Faucet — Phase 46."""

import pytest
import time
from app.services.faucet import (
    FaucetService, get_faucet_service, FaucetStatus, RequestStatus,
)


class TestClaim:
    def test_request_tokens_no_captcha(self):
        service = FaucetService()
        service._config.captcha_required = False
        result = service.request_tokens("0xnewuser", "127.0.0.1")
        assert "request_id" in result
        assert result["status"] == "distributed"

    def test_request_tokens_captcha_required(self):
        service = FaucetService()
        result = service.request_tokens("0xnewuser", "127.0.0.1")
        assert "error" in result
        assert "captcha" in result["error"].lower() or "captcha" in result

    def test_request_with_captcha(self):
        service = FaucetService()
        captcha = service.generate_captcha()
        # Parse answer from question
        import re
        nums = re.findall(r'\d+', captcha["question"])
        answer = str(int(nums[0]) + int(nums[1]))
        result = service.request_tokens("0xcaptcha_user", "127.0.0.1", "", captcha["challenge_id"], answer)
        assert "request_id" in result

    def test_cooldown(self):
        service = FaucetService()
        service._config.captcha_required = False
        service.request_tokens("0xcooldown", "127.0.0.1")
        result = service.request_tokens("0xcooldown", "127.0.0.1")
        assert "error" in result
        assert "cooldown" in result["error"].lower()

    def test_ip_cooldown(self):
        service = FaucetService()
        service._config.captcha_required = False
        service._config.cooldown_hours = 0  # Disable address cooldown
        service.request_tokens("0xuser1", "127.0.0.1")
        result = service.request_tokens("0xuser2", "127.0.0.1")
        assert "error" in result
        assert "ip" in result["error"].lower()

    def test_blacklisted(self):
        service = FaucetService()
        service._config.captcha_required = False
        service.add_to_blacklist("0xbad")
        result = service.request_tokens("0xbad", "127.0.0.1")
        assert "error" in result
        assert "blacklist" in result["error"].lower()

    def test_whitelist(self):
        service = FaucetService()
        service._config.captcha_required = False
        service._config.whitelist_enabled = True
        service.add_to_whitelist("0xgood")
        result = service.request_tokens("0xgood", "127.0.0.1")
        assert "request_id" in result
        result2 = service.request_tokens("0xnotlisted", "127.0.0.1")
        assert "error" in result2

    def test_daily_limit(self):
        service = FaucetService()
        service._config.captcha_required = False
        service._config.cooldown_hours = 0
        service._config.ip_cooldown_hours = 0
        service._config.drip_amount = 100
        service._config.daily_limit = 100
        service.request_tokens("0xlimit1", "127.0.0.1")
        result = service.request_tokens("0xlimit2", "127.0.0.2")
        assert "error" in result
        assert "daily" in result["error"].lower()

    def test_paused(self):
        service = FaucetService()
        service._config.captcha_required = False
        service.pause()
        result = service.request_tokens("0xpaused", "127.0.0.1")
        assert "error" in result


class TestCaptcha:
    def test_generate_captcha(self):
        service = FaucetService()
        captcha = service.generate_captcha()
        assert "challenge_id" in captcha
        assert "question" in captcha

    def test_verify_captcha(self):
        service = FaucetService()
        import re
        captcha = service.generate_captcha()
        nums = re.findall(r'\d+', captcha["question"])
        answer = str(int(nums[0]) + int(nums[1]))
        assert service.verify_captcha(captcha["challenge_id"], answer) is True

    def test_verify_wrong_answer(self):
        service = FaucetService()
        captcha = service.generate_captcha()
        assert service.verify_captcha(captcha["challenge_id"], "wrong") is False

    def test_verify_expired(self):
        service = FaucetService()
        captcha = service.generate_captcha()
        # Expire manually
        service._captcha_challenges[captcha["challenge_id"]]["expires"] = "2020-01-01T00:00:00"
        assert service.verify_captcha(captcha["challenge_id"], "1") is False


class TestRequests:
    def test_list_requests(self):
        service = FaucetService()
        requests = service.list_requests(limit=10)
        assert len(requests) > 0

    def test_get_request(self):
        service = FaucetService()
        requests = service.list_requests(limit=1)
        found = service.get_request(requests[0].id)
        assert found is not None

    def test_filter_by_status(self):
        service = FaucetService()
        distributed = service.list_requests(status="distributed")
        assert all(r.status == "distributed" for r in distributed)

    def test_address_info(self):
        service = FaucetService()
        service._config.captcha_required = False
        service._config.cooldown_hours = 0
        service._config.ip_cooldown_hours = 0
        service.request_tokens("0xinfo_test", "10.0.0.1")
        info = service.get_address_info("0xinfo_test")
        assert info["total_claims"] >= 1
        assert info["can_claim"] is True


class TestConfig:
    def test_get_config(self):
        service = FaucetService()
        config = service.get_config()
        assert "drip_amount" in config
        assert "remaining_supply" in config

    def test_update_config(self):
        service = FaucetService()
        updated = service.update_config(drip_amount=500)
        assert updated["drip_amount"] == 500

    def test_pause_resume(self):
        service = FaucetService()
        service.pause()
        assert service.get_config()["status"] == "paused"
        service.resume()
        assert service.get_config()["status"] == "active"

    def test_refill(self):
        service = FaucetService()
        before = service.get_config()["total_supply"]
        service.refill(1000)
        after = service.get_config()["total_supply"]
        assert after == before + 1000


class TestWhitelistBlacklist:
    def test_whitelist(self):
        service = FaucetService()
        service.add_to_whitelist("0xwl")
        assert "0xwl" in service.get_whitelist()
        service.remove_from_whitelist("0xwl")
        assert "0xwl" not in service.get_whitelist()

    def test_blacklist(self):
        service = FaucetService()
        service.add_to_blacklist("0xbl")
        assert "0xbl" in service.get_blacklist()
        service.remove_from_blacklist("0xbl")
        assert "0xbl" not in service.get_blacklist()


class TestStats:
    def test_stats(self):
        service = FaucetService()
        stats = service.get_stats()
        assert stats["total_requests"] > 0
        assert stats["distributed"] > 0

    def test_dashboard(self):
        service = FaucetService()
        dash = service.get_dashboard()
        assert "stats" in dash
        assert "config" in dash
        assert "recent_requests" in dash
        assert "top_claimers" in dash


class TestMonitoring:
    def test_start_stop(self):
        service = FaucetService()
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(2)
        service.stop_monitoring()
        assert service.is_monitoring() is False


class TestFaucetAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/faucet/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_stats(self, client, test_user):
        resp = client.get("/api/v1/faucet/stats", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_config(self, client, test_user):
        resp = client.get("/api/v1/faucet/config", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_captcha(self, client, test_user):
        resp = client.post("/api/v1/faucet/captcha", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "challenge_id" in resp.json()

    def test_list_requests(self, client, test_user):
        resp = client.get("/api/v1/faucet/requests", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_address_info(self, client, test_user):
        resp = client.get("/api/v1/faucet/address/0xverdis", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_singleton(self):
        assert get_faucet_service() is get_faucet_service()
