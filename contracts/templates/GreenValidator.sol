// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Verdis Green Validator Registry
/// @notice On-chain green validator scoring and carbon footprint tracking
/// @dev EVM counterpart to the Substrate GreenValidator pallet

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract GreenValidatorRegistry is Ownable, ReentrancyGuard {
    struct ValidatorGreenScore {
        uint256 carbonFootprint;     // kg CO2 per block
        uint256 renewablePercentage; // 0-100
        uint256 greenScore;          // 0-1000 (scaled)
        uint256 lastUpdated;
        bool isActive;
    }

    mapping(address => ValidatorGreenScore) public validators;
    address[] public validatorList;

    uint256 public constant MAX_SCORE = 1000;
    uint256 public constant RENEWABLE_WEIGHT = 400;    // 40% of score
    uint256 public constant CARBON_WEIGHT = 400;        // 40% of score
    uint256 public constant UPTIME_WEIGHT = 200;        // 20% of score

    event ValidatorRegistered(address indexed validator);
    event ScoreUpdated(address indexed validator, uint256 newScore);
    event ValidatorRemoved(address indexed validator);

    constructor() Ownable(msg.sender) {}

    function registerValidator(address validator) external onlyOwner {
        require(!validators[validator].isActive, "Already registered");
        validators[validator] = ValidatorGreenScore({
            carbonFootprint: 0,
            renewablePercentage: 0,
            greenScore: 0,
            lastUpdated: block.timestamp,
            isActive: true
        });
        validatorList.push(validator);
        emit ValidatorRegistered(validator);
    }

    function updateGreenScore(
        address validator,
        uint256 carbonFootprint,
        uint256 renewablePercentage,
        uint256 uptimePercentage
    ) external onlyOwner nonReentrant {
        require(validators[validator].isActive, "Validator not active");
        require(renewablePercentage <= 100, "Renewable > 100%");
        require(uptimePercentage <= 100, "Uptime > 100%");

        uint256 renewableScore = (renewablePercentage * RENEWABLE_WEIGHT) / 100;
        uint256 carbonScore = carbonFootprint == 0 ? CARBON_WEIGHT :
            (CARBON_WEIGHT * 10) / (carbonFootprint + 10); // Lower footprint = higher score
        uint256 uptimeScore = (uptimePercentage * UPTIME_WEIGHT) / 100;

        uint256 totalScore = renewableScore + carbonScore + uptimeScore;
        require(totalScore <= MAX_SCORE, "Score exceeds max");

        validators[validator].carbonFootprint = carbonFootprint;
        validators[validator].renewablePercentage = renewablePercentage;
        validators[validator].greenScore = totalScore;
        validators[validator].lastUpdated = block.timestamp;

        emit ScoreUpdated(validator, totalScore);
    }

    function getValidatorScore(address validator) external view returns (
        uint256 carbonFootprint, uint256 renewablePercentage,
        uint256 greenScore, uint256 lastUpdated, bool isActive
    ) {
        ValidatorGreenScore storage v = validators[validator];
        return (v.carbonFootprint, v.renewablePercentage, v.greenScore, v.lastUpdated, v.isActive);
    }

    function getTopValidators(uint256 limit) external view returns (address[] memory, uint256[] memory) {
        uint256 count = validatorList.length < limit ? validatorList.length : limit;
        address[] memory topAddr = new address[](count);
        uint256[] memory topScores = new uint256[](count);

        // Simple selection — in production, use a sorted data structure
        for (uint256 i = 0; i < count; i++) {
            topAddr[i] = validatorList[i];
            topScores[i] = validators[validatorList[i]].greenScore;
        }

        return (topAddr, topScores);
    }

    function getValidatorCount() external view returns (uint256) {
        return validatorList.length;
    }
}
