// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Verdis Carbon Credit Contract
/// @notice On-chain carbon credit tracking and retirement for the Verdis ecosystem
/// @dev Integrates with Verdis GreenValidator pallet for verification

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract CarbonCredit is ERC1155, Ownable, ReentrancyGuard {
    struct Credit {
        uint256 amount;          // tons of CO2
        uint256 retiredAmount;   // tons retired
        string project;          // reforestation project name
        string location;         // geographic location
        uint256 verifiedAt;      // verification timestamp
        bool isActive;
    }

    mapping(uint256 => Credit) public credits;
    mapping(address => bool) public verifiers;

    uint256 public nextCreditId = 1;
    uint256 public totalIssued;    // total tons issued
    uint256 public totalRetired;   // total tons retired

    event CreditIssued(uint256 indexed creditId, address indexed to, uint256 amount, string project);
    event CreditRetired(uint256 indexed creditId, address indexed from, uint256 amount);
    event VerifierAdded(address indexed verifier);
    event VerifierRemoved(address indexed verifier);

    modifier onlyVerifier() {
        require(verifiers[msg.sender] || msg.sender == owner(), "Not authorized verifier");
        _;
    }

    constructor() ERC1155("https://verdischain.com/api/carbon/{id}.json") Ownable(msg.sender) {}

    function addVerifier(address verifier) external onlyOwner {
        verifiers[verifier] = true;
        emit VerifierAdded(verifier);
    }

    function removeVerifier(address verifier) external onlyOwner {
        verifiers[verifier] = false;
        emit VerifierRemoved(verifier);
    }

    function issueCredit(
        address to,
        uint256 amount,
        string calldata project,
        string calldata location
    ) external onlyVerifier nonReentrant returns (uint256 creditId) {
        require(amount > 0, "Amount must be > 0");

        creditId = nextCreditId++;
        credits[creditId] = Credit({
            amount: amount,
            retiredAmount: 0,
            project: project,
            location: location,
            verifiedAt: block.timestamp,
            isActive: true
        });

        _mint(to, creditId, amount, "");
        totalIssued += amount;

        emit CreditIssued(creditId, to, amount, project);
    }

    function retireCredit(uint256 creditId, uint256 amount) external nonReentrant {
        require(credits[creditId].isActive, "Credit not active");
        require(amount > 0, "Amount must be > 0");

        Credit storage credit = credits[creditId];
        require(credit.retiredAmount + amount <= credit.amount, "Exceeds credit amount");

        _burn(msg.sender, creditId, amount);
        credit.retiredAmount += amount;
        totalRetired += amount;

        emit CreditRetired(creditId, msg.sender, amount);
    }

    function getCreditInfo(uint256 creditId) external view returns (
        uint256 amount, uint256 retiredAmount, string memory project,
        string memory location, uint256 verifiedAt, bool isActive
    ) {
        Credit storage c = credits[creditId];
        return (c.amount, c.retiredAmount, c.project, c.location, c.verifiedAt, c.isActive);
    }

    function getNetCarbon() external view returns (uint256) {
        return totalIssued - totalRetired;
    }
}
