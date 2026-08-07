"""Tests for Staking Dashboard — Phase 41."""

import pytest
import time
from app.services.staking_dashboard import (
    StakingDashboardService, get_staking_dashboard_service, StakeStatus, RewardStatus,
)


class TestStaking:
    def test_stake(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 1000)
        assert p.id.startswith("stk-")
        assert p.status == "active"
        assert p.amount == 1000

    def test_stake_invalid_validator(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "invalid", 1000)
        assert p is None

    def test_stake_zero(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 0)
        assert p is None

    def test_stake_auto_compound(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 1000, auto_compound=True)
        assert p.auto_compound is True

    def test_get_position(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 1000)
        found = service.get_position(p.id)
        assert found is not None

    def test_list_positions(self):
        service = StakingDashboardService()
        service.stake("0xuser1", "val-001", 1000)
        service.stake("0xuser2", "val-002", 2000)
        assert len(service.list_positions()) >= 2

    def test_list_by_delegator(self):
        service = StakingDashboardService()
        service.stake("0xuser1", "val-001", 1000)
        service.stake("0xuser2", "val-002", 2000)
        user1 = service.list_positions(delegator="0xuser1")
        assert all(p.delegator == "0xuser1" for p in user1)

    def test_list_by_validator(self):
        service = StakingDashboardService()
        service.stake("0xuser", "val-001", 1000)
        service.stake("0xuser", "val-002", 2000)
        val1 = service.list_positions(validator_id="val-001")
        assert all(p.validator_id == "val-001" for p in val1)

    def test_list_by_status(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 1000)
        service.unstake(p.id)
        unbonding = service.list_positions(status="unbonding")
        assert all(p.status == "unbonding" for p in unbonding)


class TestUnstaking:
    def test_unstake(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 1000)
        result = service.unstake(p.id)
        assert result.status == "unbonding"
        assert result.unbonding_at != ""

    def test_unstake_already_unstaking(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 1000)
        service.unstake(p.id)
        result = service.unstake(p.id)
        assert result is None

    def test_withdraw_too_early(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 1000)
        service.unstake(p.id)
        result = service.withdraw(p.id)
        assert result is None  # Still unbonding

    def test_toggle_auto_compound(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 1000)
        result = service.toggle_auto_compound(p.id)
        assert result.auto_compound is True


class TestRewards:
    def test_calculate_rewards(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 10000)
        rewards = service.calculate_rewards(p.id)
        assert rewards >= 0

    def test_claim_rewards(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 100000)
        # Manually set created to past
        from datetime import datetime, timedelta
        p.created = (datetime.utcnow() - timedelta(days=30)).isoformat()
        r = service.claim_rewards(p.id)
        assert r is not None
        assert r.status == "claimed"
        assert r.amount > 0

    def test_compound_rewards(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 100000)
        from datetime import datetime, timedelta
        p.created = (datetime.utcnow() - timedelta(days=30)).isoformat()
        result = service.compound_rewards(p.id)
        assert result is not None
        assert result.amount > 100000  # Compounded

    def test_list_rewards(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 100000)
        from datetime import datetime, timedelta
        p.created = (datetime.utcnow() - timedelta(days=30)).isoformat()
        service.claim_rewards(p.id)
        rewards = service.list_rewards("0xuser")
        assert len(rewards) >= 1

    def test_get_total_rewards(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 100000)
        from datetime import datetime, timedelta
        p.created = (datetime.utcnow() - timedelta(days=30)).isoformat()
        service.claim_rewards(p.id)
        totals = service.get_total_rewards("0xuser")
        assert totals["total_claimed"] > 0
        assert totals["total_earned"] > 0


class TestSlash:
    def test_slash(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 1000)
        result = service.slash(p.id, 5.0)
        assert result.amount == 950  # 5% slash
        assert result.slashes == 1


class TestValidators:
    def test_list_validators(self):
        service = StakingDashboardService()
        validators = service.list_validators()
        assert len(validators) >= 7

    def test_sort_by_apy(self):
        service = StakingDashboardService()
        validators = service.list_validators(sort_by="apy")
        apys = [v.apy for v in validators]
        assert apys == sorted(apys, reverse=True)

    def test_get_validator(self):
        service = StakingDashboardService()
        v = service.get_validator("val-001")
        assert v is not None
        assert v.name == "Green Node Alpha"


class TestCalculator:
    def test_simple_calculation(self):
        service = StakingDashboardService()
        result = service.calculate_staking_projection(10000, 17.0, 365, compound=False)
        assert result["projected_rewards"] > 0
        assert result["projected_total"] > 10000

    def test_compound_calculation(self):
        service = StakingDashboardService()
        result = service.calculate_staking_projection(10000, 17.0, 365, compound=True)
        assert result["projected_rewards"] > 0
        assert result["compound"] is True

    def test_compound_more_than_simple(self):
        service = StakingDashboardService()
        simple = service.calculate_staking_projection(10000, 17.0, 365, compound=False)
        compound = service.calculate_staking_projection(10000, 17.0, 365, compound=True)
        assert compound["projected_rewards"] > simple["projected_rewards"]


class TestHistory:
    def test_history_on_stake(self):
        service = StakingDashboardService()
        service.stake("0xuser", "val-001", 1000)
        history = service.list_history(delegator="0xuser")
        assert any(h.event_type == "stake" for h in history)

    def test_history_on_claim(self):
        service = StakingDashboardService()
        p = service.stake("0xuser", "val-001", 100000)
        from datetime import datetime, timedelta
        p.created = (datetime.utcnow() - timedelta(days=30)).isoformat()
        service.claim_rewards(p.id)
        history = service.list_history(delegator="0xuser", event_type="claim")
        assert len(history) >= 1


class TestStats:
    def test_network_stats(self):
        service = StakingDashboardService()
        stats = service.get_network_stats()
        assert stats["total_validators"] >= 7
        assert stats["total_staked"] > 0
        assert "avg_apy" in stats
        assert "staking_ratio" in stats

    def test_user_dashboard(self):
        service = StakingDashboardService()
        service.stake("0xdash", "val-001", 5000)
        dash = service.get_user_dashboard("0xdash")
        assert dash["total_staked"] >= 5000
        assert dash["active_positions"] >= 1

    def test_dashboard(self):
        service = StakingDashboardService()
        dash = service.get_dashboard("0xverdis")
        assert "network" in dash
        assert "user" in dash
        assert "top_validators" in dash


class TestMonitoring:
    def test_start_stop(self):
        service = StakingDashboardService()
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(2)
        service.stop_monitoring()
        assert service.is_monitoring() is False


class TestStakingAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/staking/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "network" in resp.json()

    def test_stake(self, client, test_user):
        resp = client.post("/api/v1/staking/stake", json={
            "delegator": "0xapi", "validator_id": "val-001", "amount": 1000,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("stk-")

    def test_validators(self, client, test_user):
        resp = client.get("/api/v1/staking/validators", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 7

    def test_calculate(self, client, test_user):
        resp = client.post("/api/v1/staking/calculate", json={
            "amount": 10000, "apy": 17.0, "days": 365, "compound": True,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["projected_rewards"] > 0

    def test_network_stats(self, client, test_user):
        resp = client.get("/api/v1/staking/network/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["total_validators"] >= 7

    def test_singleton(self):
        assert get_staking_dashboard_service() is get_staking_dashboard_service()
