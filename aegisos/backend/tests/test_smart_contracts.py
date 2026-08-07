"""Tests for Smart Contract Tools — Phase 33."""

import pytest
from app.services.smart_contracts import (
    SmartContractService, get_smart_contract_service,
    ContractCategory, VulnerabilitySeverity, RegistryStatus,
)


class TestTemplates:
    def test_list_templates(self):
        service = SmartContractService()
        templates = service.list_templates()
        assert len(templates) == 10

    def test_list_templates_by_category(self):
        service = SmartContractService()
        tokens = service.list_templates(ContractCategory.TOKEN.value)
        assert len(tokens) == 1
        assert tokens[0].category == "token"

    def test_get_template(self):
        service = SmartContractService()
        t = service.get_template("vrc20-token")
        assert t is not None
        assert t.name == "VRC-20 Token"
        assert "contract" in t.source_code.lower() or "pragma" in t.source_code.lower()

    def test_get_nonexistent_template(self):
        service = SmartContractService()
        assert service.get_template("nonexistent") is None

    def test_template_has_source_code(self):
        service = SmartContractService()
        for t in service.list_templates():
            assert len(t.source_code) > 100  # Each template has real code
            assert "pragma solidity" in t.source_code

    def test_template_has_parameters(self):
        service = SmartContractService()
        t = service.get_template("vrc20-token")
        assert len(t.parameters) == 3
        assert any(p["name"] == "name" for p in t.parameters)

    def test_list_categories(self):
        service = SmartContractService()
        cats = service.list_categories()
        assert len(cats) == len(ContractCategory)
        assert any(c["value"] == "token" for c in cats)


class TestSecurityScanner:
    def test_scan_clean_contract(self):
        service = SmartContractService()
        clean_code = '''pragma solidity ^0.8.20;
contract Clean {
    uint256 public value;
    function setValue(uint256 v) public { value = v; }
}'''
        scan = service.scan_contract(clean_code, "Clean")
        assert scan.score >= 90
        assert len(scan.vulnerabilities) <= 1  # Maybe just pragma check

    def test_scan_tx_origin(self):
        service = SmartContractService()
        code = '''pragma solidity ^0.8.20;
contract Bad {
    function check() public view returns (bool) {
        return tx.origin == msg.sender;
    }
}'''
        scan = service.scan_contract(code, "Bad")
        assert scan.score < 100
        assert any(v["title"] == "tx.origin Usage" for v in scan.vulnerabilities)

    def test_scan_selfdestruct(self):
        service = SmartContractService()
        code = '''pragma solidity ^0.8.20;
contract Dangerous {
    function destroy() public {
        selfdestruct(payable(msg.sender));
    }
}'''
        scan = service.scan_contract(code, "Dangerous")
        assert any(v["severity"] == "critical" for v in scan.vulnerabilities)

    def test_scan_block_timestamp(self):
        service = SmartContractService()
        code = '''pragma solidity ^0.8.20;
contract Time {
    uint256 public lastTime;
    function update() public { lastTime = block.timestamp; }
}'''
        scan = service.scan_contract(code, "Time")
        assert any(v["title"] == "Timestamp Dependence" for v in scan.vulnerabilities)

    def test_scan_reentrancy(self):
        service = SmartContractService()
        code = '''pragma solidity ^0.8.20;
contract Withdraw {
    mapping(address => uint256) balances;
    function withdraw() public {
        (bool sent,) = msg.sender.call{value: balances[msg.sender]}("");
        require(sent);
        balances[msg.sender] = 0;
    }
}'''
        scan = service.scan_contract(code, "Withdraw")
        assert any(v["title"] == "Potential Reentrancy" for v in scan.vulnerabilities)

    def test_get_scan(self):
        service = SmartContractService()
        scan = service.scan_contract("pragma solidity ^0.8.20;", "test")
        found = service.get_scan(scan.id)
        assert found is not None
        assert found.id == scan.id

    def test_list_scans(self):
        service = SmartContractService()
        service.scan_contract("pragma solidity ^0.8.20;", "a")
        service.scan_contract("pragma solidity ^0.8.20;", "b")
        assert len(service.list_scans()) >= 2

    def test_scan_score_calculation(self):
        service = SmartContractService()
        code = '''pragma solidity ^0.8.20;
contract Multi {
    function a() public { selfdestruct(payable(msg.sender)); }
    function b() public view returns (bool) { return tx.origin == msg.sender; }
}'''
        scan = service.scan_contract(code, "Multi")
        assert scan.score <= 60  # Critical + High


class TestContractRegistry:
    def test_register_contract(self):
        service = SmartContractService()
        contract = service.register_contract(
            name="TestToken", address="0x123abc", deployer="0xdeployer",
            category="token", source_code="pragma solidity ^0.8.20;",
        )
        assert contract.id.startswith("ct-")
        assert contract.verified is False
        assert contract.status == "deployed"

    def test_verify_contract(self):
        service = SmartContractService()
        source = "pragma solidity ^0.8.20; contract T {}"
        contract = service.register_contract(
            name="T", address="0x456", deployer="0xdeployer",
            category="token", source_code=source,
        )
        verified = service.verify_contract(contract.id, source)
        assert verified.verified is True
        assert verified.status == "verified"

    def test_verify_wrong_source(self):
        service = SmartContractService()
        contract = service.register_contract(
            name="T", address="0x789", deployer="0xdeployer",
            category="token", source_code="original code",
        )
        result = service.verify_contract(contract.id, "different code")
        assert result.verified is False

    def test_get_contract(self):
        service = SmartContractService()
        contract = service.register_contract("T", "0xaaa", "0xd", "token")
        found = service.get_contract(contract.id)
        assert found is not None
        assert found.name == "T"

    def test_get_contract_by_address(self):
        service = SmartContractService()
        contract = service.register_contract("T", "0xbbb", "0xd", "token")
        found = service.get_contract_by_address("0xbbb")
        assert found is not None
        assert found.id == contract.id

    def test_list_contracts(self):
        service = SmartContractService()
        service.register_contract("A", "0x1", "0xd", "token")
        service.register_contract("B", "0x2", "0xd", "nft")
        assert len(service.list_contracts()) >= 2

    def test_list_contracts_by_category(self):
        service = SmartContractService()
        service.register_contract("A", "0x3", "0xd", "token")
        service.register_contract("B", "0x4", "0xd", "nft")
        tokens = service.list_contracts(category="token")
        assert all(c.category == "token" for c in tokens)

    def test_list_contracts_by_verified(self):
        service = SmartContractService()
        c1 = service.register_contract("A", "0x5", "0xd", "token", source_code="x")
        c2 = service.register_contract("B", "0x6", "0xd", "token", source_code="y")
        service.verify_contract(c1.id, "x")
        verified = service.list_contracts(verified=True)
        assert all(c.verified for c in verified)

    def test_deprecate_contract(self):
        service = SmartContractService()
        contract = service.register_contract("T", "0x7", "0xd", "token")
        assert service.deprecate_contract(contract.id) is True
        assert service.get_contract(contract.id).status == "deprecated"


class TestStats:
    def test_stats(self):
        service = SmartContractService()
        stats = service.get_stats()
        assert "total_templates" in stats
        assert stats["total_templates"] == 10
        assert "total_scans" in stats
        assert "total_contracts" in stats


class TestSmartContractAPI:
    def test_list_templates(self, client, test_user):
        resp = client.get("/api/v1/smart-contracts/templates", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) == 10

    def test_get_template(self, client, test_user):
        resp = client.get("/api/v1/smart-contracts/templates/vrc20-token", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "VRC-20" in resp.json()["name"]

    def test_categories(self, client):
        resp = client.get("/api/v1/smart-contracts/categories")
        assert resp.status_code == 200
        assert len(resp.json()) >= 10

    def test_scan(self, client, test_user):
        resp = client.post("/api/v1/smart-contracts/scan", json={
            "source_code": "pragma solidity ^0.8.20; contract T { function f() public { tx.origin; } }",
            "contract_name": "T",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert "score" in resp.json()
        assert "vulnerabilities" in resp.json()

    def test_register_contract(self, client, test_user):
        resp = client.post("/api/v1/smart-contracts/register", json={
            "name": "TestToken", "address": "0xabc", "deployer": "0xdef",
            "category": "token", "source_code": "pragma solidity ^0.8.20;",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["status"] == "deployed"

    def test_verify_contract(self, client, test_user):
        source = "pragma solidity ^0.8.20; contract T {}"
        reg = client.post("/api/v1/smart-contracts/register", json={
            "name": "T", "address": "0xverify", "deployer": "0xd",
            "category": "token", "source_code": source,
        }, headers=test_user["headers"])
        cid = reg.json()["id"]
        resp = client.post(f"/api/v1/smart-contracts/contract/{cid}/verify", json={
            "source_code": source,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["verified"] is True

    def test_stats(self, client, test_user):
        resp = client.get("/api/v1/smart-contracts/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["total_templates"] == 10

    def test_singleton(self):
        assert get_smart_contract_service() is get_smart_contract_service()
