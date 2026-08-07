"""
Smart Contract Development Tools — Phase 33

Templates library, security analyzer, contract registry, and deployment manager.
"""

import re
import hashlib
import secrets
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
from app.core.logging import get_logger

logger = get_logger("service.smart_contracts")


class ContractCategory(str, Enum):
    TOKEN = "token"
    NFT = "nft"
    DEX = "dex"
    STAKING = "staking"
    GOVERNANCE = "governance"
    CARBON_CREDIT = "carbon_credit"
    REFORESTATION = "reforestation"
    GREEN_VALIDATOR = "green_validator"
    BRIDGE = "bridge"
    MULTISIG = "multisig"
    CROWDFUND = "crowdfund"
    VESTING = "vesting"


class VulnerabilitySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RegistryStatus(str, Enum):
    DEPLOYED = "deployed"
    VERIFIED = "verified"
    FAILED = "failed"
    DEPRECATED = "deprecated"


@dataclass
class ContractTemplate:
    id: str
    name: str
    category: str
    description: str
    source_code: str
    abi: str  # JSON string
    bytecode_length: int
    parameters: list[dict]  # constructor params
    tags: list[str] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Vulnerability:
    severity: str
    title: str
    description: str
    line_number: int
    pattern: str
    recommendation: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SecurityScan:
    id: str
    contract_name: str
    source_code: str
    vulnerabilities: list[dict] = field(default_factory=list)
    score: float = 100.0
    scanned_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    lines_scanned: int = 0
    checks_run: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RegisteredContract:
    id: str
    name: str
    address: str
    deployer: str
    category: str
    compiler_version: str
    source_hash: str
    abi: str
    verified: bool = False
    status: str = RegistryStatus.DEPLOYED.value
    network: str = "verdis-mainnet"
    block_number: int = 0
    tx_hash: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class SmartContractService:
    """Smart contract development tools: templates, security, registry."""

    def __init__(self):
        self._templates: dict[str, ContractTemplate] = {}
        self._scans: dict[str, SecurityScan] = {}
        self._registry: dict[str, RegisteredContract] = {}
        self._address_to_contract: dict[str, str] = {}
        self._lock = threading.Lock()
        self._init_default_templates()

    def _init_default_templates(self):
        templates = [
            ("vrc20-token", "VRC-20 Token", ContractCategory.TOKEN,
             "Standard fungible token with mint, burn, and transfer",
             self._template_vrc20(), [{"name": "name", "type": "string"}, {"name": "symbol", "type": "string"}, {"name": "totalSupply", "type": "uint256"}],
             ["token", "fungible", "vrc20"]),
            ("vrc721-nft", "VRC-721 NFT", ContractCategory.NFT,
             "Non-fungible token with metadata and minting",
             self._template_vrc721(), [{"name": "name", "type": "string"}, {"name": "symbol", "type": "string"}],
             ["nft", "vrc721", "metadata"]),
            ("carbon-credit", "Carbon Credit Token", ContractCategory.CARBON_CREDIT,
             "Carbon credit token with verification and retirement",
             self._template_carbon_credit(), [{"name": "project", "type": "string"}, {"name": "totalCredits", "type": "uint256"}],
             ["carbon", "eco", "green"]),
            ("reforestation", "Reforestation Tracker", ContractCategory.REFORESTATION,
             "Track reforestation projects with tree counts and locations",
             self._template_reforestation(), [{"name": "projectName", "type": "string"}, {"name": "location", "type": "string"}],
             ["reforestation", "eco", "trees"]),
            ("green-validator", "Green Validator Score", ContractCategory.GREEN_VALIDATOR,
             "Track and score eco-friendly validators",
             self._template_green_validator(), [{"name": "validatorId", "type": "address"}],
             ["validator", "green", "eco"]),
            ("staking", "Staking Contract", ContractCategory.STAKING,
             "DPoS staking with rewards and slashing",
             self._template_staking(), [{"name": "rewardRate", "type": "uint256"}],
             ["staking", "dpos", "rewards"]),
            ("governance", "Governance Proposal", ContractCategory.GOVERNANCE,
             "On-chain governance with proposal creation and voting",
             self._template_governance(), [{"name": "votingPeriod", "type": "uint256"}],
             ["governance", "dao", "voting"]),
            ("multisig-wallet", "Multi-Signature Wallet", ContractCategory.MULTISIG,
             "M-of-N multi-signature wallet for secure fund management",
             self._template_multisig(), [{"name": "owners", "type": "address[]"}, {"name": "required", "type": "uint256"}],
             ["multisig", "wallet", "security"]),
            ("vesting", "Token Vesting", ContractCategory.VESTING,
             "Token vesting schedule with cliff and gradual release",
             self._template_vesting(), [{"name": "beneficiary", "type": "address"}, {"name": "start", "type": "uint256"}, {"name": "cliff", "type": "uint256"}],
             ["vesting", "tokens", "schedule"]),
            ("crowdfund", "Crowdfunding", ContractCategory.CROWDFUND,
             "Crowdfunding with goal and refund mechanism",
             self._template_crowdfund(), [{"name": "goal", "type": "uint256"}, {"name": "deadline", "type": "uint256"}],
             ["crowdfund", "funding", "community"]),
        ]

        for tid, name, cat, desc, source, params, tags in templates:
            template = ContractTemplate(
                id=tid, name=name, category=cat.value, description=desc,
                source_code=source, abi="[]", bytecode_length=len(source) * 2,
                parameters=params, tags=tags,
            )
            self._templates[tid] = template

    def _template_vrc20(self) -> str:
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VRCToken {
    string public name;
    string public symbol;
    uint256 public totalSupply;
    uint8 public decimals = 18;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor(string memory _name, string memory _symbol, uint256 _totalSupply) {
        name = _name;
        symbol = _symbol;
        totalSupply = _totalSupply;
        balanceOf[msg.sender] = _totalSupply;
    }

    function transfer(address to, uint256 value) public returns (bool) {
        require(balanceOf[msg.sender] >= value, "Insufficient balance");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint256 value) public returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) public returns (bool) {
        require(balanceOf[from] >= value, "Insufficient balance");
        require(allowance[from][msg.sender] >= value, "Insufficient allowance");
        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        emit Transfer(from, to, value);
        return true;
    }
}'''

    def _template_vrc721(self) -> str:
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VRCNFT {
    string public name;
    string public symbol;

    uint256 public nextTokenId = 1;
    mapping(uint256 => address) public ownerOf;
    mapping(address => uint256) public balanceOf;
    mapping(uint256 => string) public tokenURI;

    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Mint(address indexed to, uint256 indexed tokenId, string uri);

    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
    }

    function mint(address to, string memory uri) public returns (uint256) {
        uint256 tokenId = nextTokenId++;
        ownerOf[tokenId] = to;
        balanceOf[to]++;
        tokenURI[tokenId] = uri;
        emit Mint(to, tokenId, uri);
        emit Transfer(address(0), to, tokenId);
        return tokenId;
    }

    function transfer(address to, uint256 tokenId) public {
        require(ownerOf[tokenId] == msg.sender, "Not owner");
        ownerOf[tokenId] = to;
        balanceOf[msg.sender]--;
        balanceOf[to]++;
        emit Transfer(msg.sender, to, tokenId);
    }
}'''

    def _template_carbon_credit(self) -> str:
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract CarbonCredit {
    string public project;
    uint256 public totalCredits;
    uint256 public retiredCredits;

    mapping(address => uint256) public credits;
    mapping(address => uint256) public retired;

    event CreditsIssued(address indexed to, uint256 amount);
    event CreditsRetired(address indexed from, uint256 amount);

    constructor(string memory _project, uint256 _totalCredits) {
        project = _project;
        totalCredits = _totalCredits;
        credits[msg.sender] = _totalCredits;
    }

    function issue(address to, uint256 amount) public {
        require(credits[msg.sender] >= amount, "Insufficient credits");
        credits[msg.sender] -= amount;
        credits[to] += amount;
        emit CreditsIssued(to, amount);
    }

    function retire(uint256 amount) public {
        require(credits[msg.sender] >= amount, "Insufficient credits");
        credits[msg.sender] -= amount;
        retired[msg.sender] += amount;
        retiredCredits += amount;
        emit CreditsRetired(msg.sender, amount);
    }

    function availableCredits() public view returns (uint256) {
        return totalCredits - retiredCredits;
    }
}'''

    def _template_reforestation(self) -> str:
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Reforestation {
    struct Project {
        string name;
        string location;
        uint256 treesPlanted;
        uint256 treesSurvived;
        bool verified;
    }

    mapping(uint256 => Project) public projects;
    uint256 public projectCount;

    event ProjectCreated(uint256 indexed id, string name, string location);
    event TreesPlanted(uint256 indexed projectId, uint256 count);
    event ProjectVerified(uint256 indexed projectId);

    constructor(string memory _projectName, string memory _location) {
        projects[0] = Project(_projectName, _location, 0, 0, false);
        projectCount = 1;
    }

    function plantTrees(uint256 projectId, uint256 count) public {
        require(projectId < projectCount, "Invalid project");
        projects[projectId].treesPlanted += count;
        emit TreesPlanted(projectId, count);
    }

    function recordSurvival(uint256 projectId, uint256 survived) public {
        require(projectId < projectCount, "Invalid project");
        projects[projectId].treesSurvived = survived;
    }

    function verifyProject(uint256 projectId) public {
        require(projectId < projectCount, "Invalid project");
        projects[projectId].verified = true;
        emit ProjectVerified(projectId);
    }

    function survivalRate(uint256 projectId) public view returns (uint256) {
        if (projects[projectId].treesPlanted == 0) return 0;
        return (projects[projectId].treesSurvived * 100) / projects[projectId].treesPlanted;
    }
}'''

    def _template_green_validator(self) -> str:
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract GreenValidator {
    struct Validator {
        address id;
        uint256 score;
        string energySource;
        uint256 carbonOffset;
        bool certified;
    }

    mapping(address => Validator) public validators;
    address[] public validatorList;

    event ValidatorRegistered(address indexed id);
    event ScoreUpdated(address indexed id, uint256 score);
    event Certified(address indexed id);

    constructor(address _validatorId) {
        validators[_validatorId] = Validator(_validatorId, 0, "solar", 0, false);
        validatorList.push(_validatorId);
    }

    function updateScore(address id, uint256 score) public {
        require(validators[id].id != address(0), "Not a validator");
        validators[id].score = score;
        emit ScoreUpdated(id, score);
    }

    function certify(address id) public {
        require(validators[id].score >= 80, "Score too low");
        validators[id].certified = true;
        emit Certified(id);
    }

    function getValidator(address id) public view returns (Validator memory) {
        return validators[id];
    }
}'''

    def _template_staking(self) -> str:
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Staking {
    uint256 public rewardRate;
    uint256 public totalStaked;

    struct Stake {
        uint256 amount;
        uint256 startTime;
        uint256 rewardDebt;
    }

    mapping(address => Stake) public stakes;

    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event RewardPaid(address indexed user, uint256 reward);

    constructor(uint256 _rewardRate) {
        rewardRate = _rewardRate;
    }

    function stake(uint256 amount) public {
        Stake storage s = stakes[msg.sender];
        s.amount += amount;
        s.startTime = block.timestamp;
        totalStaked += amount;
        emit Staked(msg.sender, amount);
    }

    function unstake(uint256 amount) public {
        require(stakes[msg.sender].amount >= amount, "Insufficient stake");
        stakes[msg.sender].amount -= amount;
        totalStaked -= amount;
        emit Unstaked(msg.sender, amount);
    }

    function calculateReward(address user) public view returns (uint256) {
        Stake storage s = stakes[user];
        uint256 duration = block.timestamp - s.startTime;
        return (s.amount * rewardRate * duration) / 10000;
    }
}'''

    def _template_governance(self) -> str:
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Governance {
    uint256 public votingPeriod;
    uint256 public proposalCount;

    struct Proposal {
        uint256 id;
        address proposer;
        string description;
        uint256 forVotes;
        uint256 againstVotes;
        uint256 startTime;
        bool executed;
    }

    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => mapping(address => bool)) public hasVoted;

    event ProposalCreated(uint256 indexed id, address indexed proposer, string description);
    event Voted(uint256 indexed proposalId, address indexed voter, bool support);

    constructor(uint256 _votingPeriod) {
        votingPeriod = _votingPeriod;
    }

    function createProposal(string memory description) public returns (uint256) {
        uint256 id = proposalCount++;
        proposals[id] = Proposal(id, msg.sender, description, 0, 0, block.timestamp, false);
        emit ProposalCreated(id, msg.sender, description);
        return id;
    }

    function vote(uint256 proposalId, bool support) public {
        require(!hasVoted[proposalId][msg.sender], "Already voted");
        require(block.timestamp <= proposals[proposalId].startTime + votingPeriod, "Voting ended");
        hasVoted[proposalId][msg.sender] = true;
        if (support) proposals[proposalId].forVotes++;
        else proposals[proposalId].againstVotes++;
        emit Voted(proposalId, msg.sender, support);
    }

    function execute(uint256 proposalId) public {
        require(block.timestamp > proposals[proposalId].startTime + votingPeriod, "Voting active");
        require(proposals[proposalId].forVotes > proposals[proposalId].againstVotes, "Not passed");
        proposals[proposalId].executed = true;
    }
}'''

    def _template_multisig(self) -> str:
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MultisigWallet {
    address[] public owners;
    uint256 public required;
    uint256 public txCount;

    struct Transaction {
        address to;
        uint256 value;
        bytes data;
        bool executed;
        uint256 approvals;
    }

    mapping(uint256 => Transaction) public transactions;
    mapping(uint256 => mapping(address => bool)) public approved;

    event TransactionSubmitted(uint256 indexed id, address indexed to, uint256 value);
    event TransactionApproved(uint256 indexed id, address indexed owner);
    event TransactionExecuted(uint256 indexed id);

    constructor(address[] memory _owners, uint256 _required) {
        owners = _owners;
        required = _required;
    }

    function submit(address to, uint256 value, bytes memory data) public returns (uint256) {
        uint256 id = txCount++;
        transactions[id] = Transaction(to, value, data, false, 0);
        emit TransactionSubmitted(id, to, value);
        return id;
    }

    function approve(uint256 txId) public {
        require(!approved[txId][msg.sender], "Already approved");
        approved[txId][msg.sender] = true;
        transactions[txId].approvals++;
        emit TransactionApproved(txId, msg.sender);
        if (transactions[txId].approvals >= required) {
            transactions[txId].executed = true;
            emit TransactionExecuted(txId);
        }
    }
}'''

    def _template_vesting(self) -> str:
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TokenVesting {
    address public beneficiary;
    uint256 public start;
    uint256 public cliff;
    uint256 public duration;
    uint256 public totalAmount;
    uint256 public released;

    event Released(uint256 amount);

    constructor(address _beneficiary, uint256 _start, uint256 _cliff) {
        beneficiary = _beneficiary;
        start = _start;
        cliff = _cliff;
        duration = 365 days * 4;
    }

    function releasableAmount() public view returns (uint256) {
        if (block.timestamp < start + cliff) return 0;
        uint256 elapsed = block.timestamp - start;
        if (elapsed >= duration) return totalAmount - released;
        return (totalAmount * elapsed) / duration - released;
    }

    function release() public {
        uint256 amount = releasableAmount();
        require(amount > 0, "Nothing to release");
        released += amount;
        emit Released(amount);
    }
}'''

    def _template_crowdfund(self) -> str:
        return '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Crowdfund {
    uint256 public goal;
    uint256 public deadline;
    uint256 public raised;
    bool public finalized;

    mapping(address => uint256) public contributions;

    event Contributed(address indexed contributor, uint256 amount);
    event Refunded(address indexed contributor, uint256 amount);
    event Finalized(bool success);

    constructor(uint256 _goal, uint256 _deadline) {
        goal = _goal;
        deadline = _deadline;
    }

    function contribute() public payable {
        require(block.timestamp < deadline, "Campaign ended");
        contributions[msg.sender] += msg.value;
        raised += msg.value;
        emit Contributed(msg.sender, msg.value);
    }

    function refund() public {
        require(block.timestamp >= deadline, "Campaign active");
        require(raised < goal, "Goal reached");
        uint256 amount = contributions[msg.sender];
        require(amount > 0, "No contribution");
        contributions[msg.sender] = 0;
        payable(msg.sender).transfer(amount);
        emit Refunded(msg.sender, amount);
    }

    function finalize() public {
        require(block.timestamp >= deadline, "Campaign active");
        require(!finalized, "Already finalized");
        finalized = true;
        emit Finalized(raised >= goal);
    }
}'''

    # === Template API ===

    def list_templates(self, category: str = None) -> list[ContractTemplate]:
        if category:
            return [t for t in self._templates.values() if t.category == category]
        return list(self._templates.values())

    def get_template(self, template_id: str) -> Optional[ContractTemplate]:
        return self._templates.get(template_id)

    def list_categories(self) -> list[dict]:
        return [{"value": c.value, "name": c.value.replace("_", " ").title()} for c in ContractCategory]

    # === Security Analyzer ===

    VULNERABILITY_PATTERNS = [
        {
            "id": "reentrancy",
            "severity": VulnerabilitySeverity.CRITICAL.value,
            "title": "Potential Reentrancy",
            "pattern": r"\.call\{value:",
            "description": "External call detected. Verify reentrancy guard is in place.",
            "recommendation": "Use ReentrancyGuard or checks-effects-interactions pattern.",
        },
        {
            "id": "tx-origin",
            "severity": VulnerabilitySeverity.HIGH.value,
            "title": "tx.origin Usage",
            "pattern": r"tx\.origin",
            "description": "tx.origin is used for authorization, which can be spoofed by phishing attacks.",
            "recommendation": "Use msg.sender instead of tx.origin for authorization.",
        },
        {
            "id": "delegatecall",
            "severity": VulnerabilitySeverity.HIGH.value,
            "title": "Untrusted delegatecall",
            "pattern": r"delegatecall",
            "description": "delegatecall executes code in the caller's context. Ensure target is trusted.",
            "recommendation": "Only use delegatecall with trusted contracts.",
        },
        {
            "id": "unsafe-math",
            "severity": VulnerabilitySeverity.MEDIUM.value,
            "title": "Unchecked Arithmetic",
            "pattern": r"\-=|\+=|/\=|\*=|-=|/\s",
            "description": "Arithmetic operation without SafeMath (pre-0.8.0).",
            "recommendation": "Use Solidity 0.8+ for built-in overflow checks, or SafeMath for older versions.",
        },
        {
            "id": "uninitialized-storage",
            "severity": VulnerabilitySeverity.HIGH.value,
            "title": "Uninitialized Storage Pointer",
            "pattern": r"struct\s+\w+\s+\w+\s*;",
            "description": "Potential uninitialized storage pointer detected.",
            "recommendation": "Always initialize struct variables with 'storage' or 'memory' keyword.",
        },
        {
            "id": "timestamp-dependence",
            "severity": VulnerabilitySeverity.LOW.value,
            "title": "Timestamp Dependence",
            "pattern": r"block\.timestamp",
            "description": "block.timestamp can be manipulated by miners within ~15 seconds.",
            "recommendation": "Avoid precise time-dependent logic. Use block numbers for critical timing.",
        },
        {
            "id": "block-number-dependence",
            "severity": VulnerabilitySeverity.INFO.value,
            "title": "Block Number Usage",
            "pattern": r"block\.number",
            "description": "block.number is used. This is generally safe but can be affected by chain reorgs.",
            "recommendation": "Use with caution for critical logic.",
        },
        {
            "id": "selfdestruct",
            "severity": VulnerabilitySeverity.CRITICAL.value,
            "title": "Self-Destruct",
            "pattern": r"selfdestruct",
            "description": "Contract can be destroyed, sending all funds to an address.",
            "recommendation": "Remove selfdestruct or add strict access control.",
        },
        {
            "id": "inline-assembly",
            "severity": VulnerabilitySeverity.MEDIUM.value,
            "title": "Inline Assembly",
            "pattern": r"assembly\s*\{",
            "description": "Inline assembly bypasses Solidity safety checks.",
            "recommendation": "Review assembly carefully for memory safety and gas usage.",
        },
        {
            "id": "low-level-call",
            "severity": VulnerabilitySeverity.MEDIUM.value,
            "title": "Low-Level Call",
            "pattern": r"\.call\(|\.send\(|\.transfer\(",
            "description": "Low-level call detected. Handle return values properly.",
            "recommendation": "Always check return values of low-level calls.",
        },
        {
            "id": "unprotected-fallback",
            "severity": VulnerabilitySeverity.MEDIUM.value,
            "title": "Fallback Function",
            "pattern": r"fallback\(\)|receive\(\)",
            "description": "Fallback/receive function detected. Ensure access control if needed.",
            "recommendation": "Add proper access control to fallback functions if they handle state changes.",
        },
        {
            "id": "pragma-too-old",
            "severity": VulnerabilitySeverity.LOW.value,
            "title": "Old Pragma Version",
            "pattern": r"pragma\s+solidity\s+\^0\.[0-7]\.",
            "description": "Old compiler version detected. Missing security features.",
            "recommendation": "Use Solidity 0.8.20 or later for latest security features.",
        },
    ]

    def scan_contract(self, source_code: str, contract_name: str = "unnamed") -> SecurityScan:
        """Run security analysis on Solidity source code."""
        scan_id = f"scan-{secrets.token_hex(8)}"
        lines = source_code.split("\n")
        vulnerabilities = []

        for vuln_def in self.VULNERABILITY_PATTERNS:
            pattern = vuln_def["pattern"]
            for i, line in enumerate(lines):
                if re.search(pattern, line, re.IGNORECASE):
                    vulnerabilities.append(Vulnerability(
                        severity=vuln_def["severity"],
                        title=vuln_def["title"],
                        description=vuln_def["description"],
                        line_number=i + 1,
                        pattern=pattern,
                        recommendation=vuln_def["recommendation"],
                    ).to_dict())

        # Calculate score
        score = 100.0
        for v in vulnerabilities:
            if v["severity"] == "critical":
                score -= 25
            elif v["severity"] == "high":
                score -= 15
            elif v["severity"] == "medium":
                score -= 8
            elif v["severity"] == "low":
                score -= 3
            elif v["severity"] == "info":
                score -= 1
        score = max(0.0, score)

        scan = SecurityScan(
            id=scan_id, contract_name=contract_name, source_code=source_code,
            vulnerabilities=vulnerabilities, score=score,
            lines_scanned=len(lines), checks_run=len(self.VULNERABILITY_PATTERNS),
        )
        self._scans[scan_id] = scan
        logger.info("contract_scanned", scan_id=scan_id, vulns=len(vulnerabilities), score=score)
        return scan

    def get_scan(self, scan_id: str) -> Optional[SecurityScan]:
        return self._scans.get(scan_id)

    def list_scans(self, limit: int = 50) -> list[SecurityScan]:
        return list(self._scans.values())[:limit]

    # === Contract Registry ===

    def register_contract(
        self, name: str, address: str, deployer: str, category: str,
        compiler_version: str = "0.8.20", abi: str = "[]",
        source_code: str = "", network: str = "verdis-mainnet",
        block_number: int = 0, tx_hash: str = "", metadata: dict = None,
    ) -> RegisteredContract:
        """Register a deployed contract."""
        with self._lock:
            source_hash = hashlib.sha256(source_code.encode()).hexdigest() if source_code else ""
            contract_id = f"ct-{secrets.token_hex(8)}"
            contract = RegisteredContract(
                id=contract_id, name=name, address=address, deployer=deployer,
                category=category, compiler_version=compiler_version,
                source_hash=source_hash, abi=abi,
                network=network, block_number=block_number, tx_hash=tx_hash,
                metadata=metadata or {},
            )
            self._registry[contract_id] = contract
            self._address_to_contract[address] = contract_id
            logger.info("contract_registered", id=contract_id, name=name, address=address)
            return contract

    def verify_contract(self, contract_id: str, source_code: str) -> Optional[RegisteredContract]:
        """Verify a contract by matching source code hash."""
        contract = self._registry.get(contract_id)
        if not contract:
            return None
        source_hash = hashlib.sha256(source_code.encode()).hexdigest()
        if source_hash == contract.source_hash:
            contract.verified = True
            contract.status = RegistryStatus.VERIFIED.value
        return contract

    def get_contract(self, contract_id: str) -> Optional[RegisteredContract]:
        return self._registry.get(contract_id)

    def get_contract_by_address(self, address: str) -> Optional[RegisteredContract]:
        cid = self._address_to_contract.get(address)
        if cid:
            return self._registry.get(cid)
        return None

    def list_contracts(
        self, category: str = None, deployer: str = None,
        verified: bool = None, limit: int = 50,
    ) -> list[RegisteredContract]:
        contracts = list(self._registry.values())
        if category:
            contracts = [c for c in contracts if c.category == category]
        if deployer:
            contracts = [c for c in contracts if c.deployer == deployer]
        if verified is not None:
            contracts = [c for c in contracts if c.verified == verified]
        return contracts[:limit]

    def deprecate_contract(self, contract_id: str) -> bool:
        contract = self._registry.get(contract_id)
        if contract:
            contract.status = RegistryStatus.DEPRECATED.value
            return True
        return False

    def get_stats(self) -> dict:
        return {
            "total_templates": len(self._templates),
            "total_scans": len(self._scans),
            "total_contracts": len(self._registry),
            "verified_contracts": sum(1 for c in self._registry.values() if c.verified),
            "by_category": {c: sum(1 for ct in self._registry.values() if ct.category == c) for c in set(ct.category for ct in self._registry.values())},
            "avg_security_score": sum(s.score for s in self._scans.values()) / max(1, len(self._scans)),
        }


_service: Optional[SmartContractService] = None

def get_smart_contract_service() -> SmartContractService:
    global _service
    if _service is None:
        _service = SmartContractService()
    return _service
