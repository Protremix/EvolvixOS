"""Tests for Governance & Treasury — Phase 35."""

import pytest
from app.services.governance import (
    GovernanceService, get_governance_service,
    ProposalStatus, ProposalType, VoteType, TreasuryStatus,
)


class TestProposals:
    def test_create_proposal(self):
        service = GovernanceService()
        p = service.create_proposal("referendum", "Test", "Description", "0xproposer")
        assert p.id.startswith("prop-")
        assert p.status == "active"
        assert p.aye_votes == 0

    def test_get_proposal(self):
        service = GovernanceService()
        p = service.create_proposal("referendum", "Test", "Desc", "0x1")
        found = service.get_proposal(p.id)
        assert found is not None
        assert found.title == "Test"

    def test_list_proposals(self):
        service = GovernanceService()
        service.create_proposal("referendum", "A", "Desc", "0x1")
        service.create_proposal("treasury_spend", "B", "Desc", "0x2")
        assert len(service.list_proposals()) >= 2

    def test_list_by_status(self):
        service = GovernanceService()
        service.create_proposal("referendum", "A", "Desc", "0x1")
        active = service.list_proposals(status="active")
        assert all(p.status == "active" for p in active)

    def test_list_by_type(self):
        service = GovernanceService()
        service.create_proposal("referendum", "A", "Desc", "0x1")
        service.create_proposal("runtime_upgrade", "B", "Desc", "0x2")
        refs = service.list_proposals(type="referendum")
        assert all(p.type == "referendum" for p in refs)

    def test_list_by_proposer(self):
        service = GovernanceService()
        service.create_proposal("referendum", "A", "Desc", "0xalice")
        service.create_proposal("referendum", "B", "Desc", "0xbob")
        alice = service.list_proposals(proposer="0xalice")
        assert all(p.proposer == "0xalice" for p in alice)

    def test_cancel_proposal(self):
        service = GovernanceService()
        p = service.create_proposal("referendum", "T", "D", "0x1")
        assert service.cancel_proposal(p.id, "0x1") is True
        assert service.get_proposal(p.id).status == "cancelled"

    def test_cancel_wrong_proposer(self):
        service = GovernanceService()
        p = service.create_proposal("referendum", "T", "D", "0x1")
        assert service.cancel_proposal(p.id, "0x2") is False

    def test_cancel_nonexistent(self):
        service = GovernanceService()
        assert service.cancel_proposal("nonexistent", "0x1") is False


class TestVoting:
    def test_vote_aye(self):
        service = GovernanceService()
        p = service.create_proposal("referendum", "T", "D", "0x1")
        vote = service.vote(p.id, "0x2", "aye")
        assert vote is not None
        assert vote.vote_type == "aye"
        assert service.get_proposal(p.id).aye_votes == 1

    def test_vote_nay(self):
        service = GovernanceService()
        p = service.create_proposal("referendum", "T", "D", "0x1")
        service.vote(p.id, "0x2", "nay")
        assert service.get_proposal(p.id).nay_votes == 1

    def test_vote_abstain(self):
        service = GovernanceService()
        p = service.create_proposal("referendum", "T", "D", "0x1")
        service.vote(p.id, "0x2", "abstain")
        assert service.get_proposal(p.id).abstain_votes == 1

    def test_double_vote_rejected(self):
        service = GovernanceService()
        p = service.create_proposal("referendum", "T", "D", "0x1")
        service.vote(p.id, "0x2", "aye")
        result = service.vote(p.id, "0x2", "nay")
        assert result is None

    def test_vote_nonexistent(self):
        service = GovernanceService()
        assert service.vote("nonexistent", "0x1", "aye") is None

    def test_tally_votes(self):
        service = GovernanceService()
        p = service.create_proposal("referendum", "T", "D", "0x1", threshold=0.5)
        service.vote(p.id, "0x2", "aye")
        service.vote(p.id, "0x3", "aye")
        service.vote(p.id, "0x4", "nay")
        tally = service.tally_votes(p.id)
        assert tally["aye"] == 2
        assert tally["nay"] == 1
        assert tally["passes"] is True

    def test_tally_fails(self):
        service = GovernanceService()
        p = service.create_proposal("referendum", "T", "D", "0x1", threshold=0.5)
        service.vote(p.id, "0x2", "nay")
        service.vote(p.id, "0x3", "nay")
        service.vote(p.id, "0x4", "aye")
        tally = service.tally_votes(p.id)
        assert tally["passes"] is False

    def test_get_votes(self):
        service = GovernanceService()
        p = service.create_proposal("referendum", "T", "D", "0x1")
        service.vote(p.id, "0x2", "aye")
        votes = service.get_votes(p.id)
        assert len(votes) == 1

    def test_voting_power(self):
        service = GovernanceService()
        p = service.create_proposal("referendum", "T", "D", "0x1")
        service.vote(p.id, "0x2", "aye", voting_power=5.0)
        assert service.get_proposal(p.id).aye_votes == 5.0

    def test_proposal_stats(self):
        service = GovernanceService()
        service.create_proposal("referendum", "A", "D", "0x1")
        stats = service.get_proposal_stats()
        assert stats["total"] >= 1
        assert stats["active"] >= 1


class TestTreasury:
    def test_create_treasury_proposal(self):
        service = GovernanceService()
        t = service.create_treasury_proposal("Fund", "Dev", "0x1", "0x2", 50000)
        assert t.id.startswith("tr-")
        assert t.status == "pending"

    def test_treasury_exceeds_balance(self):
        service = GovernanceService()
        with pytest.raises(ValueError):
            service.create_treasury_proposal("Too Much", "Desc", "0x1", "0x2", 2_000_000_000)

    def test_approve_treasury(self):
        service = GovernanceService()
        t = service.create_treasury_proposal("Fund", "Dev", "0x1", "0x2", 10000, threshold=2)
        service.approve_treasury_proposal(t.id, "0xc1")
        assert t.approvals == 1
        assert t.status == "pending"  # Not enough yet
        service.approve_treasury_proposal(t.id, "0xc2")
        assert t.status == "approved"

    def test_reject_treasury(self):
        service = GovernanceService()
        t = service.create_treasury_proposal("Fund", "Dev", "0x1", "0x2", 10000)
        service.reject_treasury_proposal(t.id)
        assert t.status == "rejected"

    def test_disburse_treasury(self):
        service = GovernanceService()
        t = service.create_treasury_proposal("Fund", "Dev", "0x1", "0x2", 10000, threshold=1)
        service.approve_treasury_proposal(t.id, "0xc1")
        service.disburse_treasury(t.id, "0xtx123")
        assert t.status == "disbursed"
        assert t.disbursement_tx == "0xtx123"

    def test_treasury_balance(self):
        service = GovernanceService()
        balance = service.get_treasury_balance()
        assert "balance" in balance
        assert balance["currency"] == "VRS"

    def test_list_treasury(self):
        service = GovernanceService()
        service.create_treasury_proposal("A", "D", "0x1", "0x2", 100, category="eco")
        service.create_treasury_proposal("B", "D", "0x1", "0x2", 200, category="infra")
        assert len(service.list_treasury_proposals()) >= 2
        eco = service.list_treasury_proposals(category="eco")
        assert all(t.category == "eco" for t in eco)

    def test_treasury_stats(self):
        service = GovernanceService()
        service.create_treasury_proposal("A", "D", "0x1", "0x2", 100, threshold=1)
        stats = service.get_treasury_stats()
        assert "total_proposals" in stats
        assert "remaining_balance" in stats


class TestCouncil:
    def test_add_council_member(self):
        service = GovernanceService()
        member = service.add_council_member("0xmember", "Alice")
        assert member.address == "0xmember"
        assert member.name == "Alice"
        assert member.active is True

    def test_remove_council_member(self):
        service = GovernanceService()
        service.add_council_member("0xm", "Bob")
        assert service.remove_council_member("0xm") is True
        assert service.get_council_member("0xm").active is False

    def test_list_council(self):
        service = GovernanceService()
        service.add_council_member("0x1", "A")
        service.add_council_member("0x2", "B")
        members = service.list_council_members()
        assert len(members) >= 2

    def test_council_stats(self):
        service = GovernanceService()
        service.add_council_member("0x1", "A")
        stats = service.get_council_stats()
        assert stats["active_members"] >= 1

    def test_council_vote_tracking(self):
        service = GovernanceService()
        service.add_council_member("0xc1", "Councilor")
        p = service.create_proposal("referendum", "T", "D", "0xc1")
        service.vote(p.id, "0xc1", "aye")
        member = service.get_council_member("0xc1")
        assert member.votes_cast == 1
        assert member.proposals_created == 1


class TestDashboard:
    def test_dashboard(self):
        service = GovernanceService()
        service.create_proposal("referendum", "T", "D", "0x1")
        service.add_council_member("0xc", "C")
        dash = service.get_dashboard()
        assert "proposals" in dash
        assert "treasury" in dash
        assert "council" in dash
        assert len(dash["active_proposals"]) >= 1


class TestGovernanceAPI:
    def test_create_proposal(self, client, test_user):
        resp = client.post("/api/v1/governance/proposals", json={
            "type": "referendum", "title": "Test", "description": "Desc",
            "proposer": "0xtest",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    def test_vote(self, client, test_user):
        create = client.post("/api/v1/governance/proposals", json={
            "type": "referendum", "title": "Vote", "description": "Desc",
            "proposer": "0x1",
        }, headers=test_user["headers"])
        pid = create.json()["id"]
        resp = client.post(f"/api/v1/governance/proposals/{pid}/vote", json={
            "voter": "0x2", "vote_type": "aye",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["vote_type"] == "aye"

    def test_treasury(self, client, test_user):
        resp = client.post("/api/v1/governance/treasury", json={
            "title": "Eco Fund", "description": "Green", "proposer": "0x1",
            "beneficiary": "0x2", "amount": 5000, "category": "eco",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    def test_council(self, client, test_user):
        resp = client.post("/api/v1/governance/council/members", json={
            "address": "0xcouncil1", "name": "Councilor 1",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["name"] == "Councilor 1"

    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/governance/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "proposals" in resp.json()

    def test_types(self, client):
        resp = client.get("/api/v1/governance/types/proposals")
        assert resp.status_code == 200
        assert len(resp.json()) >= 6

    def test_singleton(self):
        assert get_governance_service() is get_governance_service()
