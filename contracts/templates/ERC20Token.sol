// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Verdis ERC-20 Token Template
/// @notice Standard ERC-20 token for deployment on the Verdis EVM
/// @dev Compatible with Verdis chain ID 909, uses VRDX as gas currency

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract VerdisToken is ERC20, Ownable, Pausable {
    uint8 private immutable _decimals;
    uint256 public immutable maxSupply;

    event TokensMinted(address indexed to, uint256 amount);
    event TokensBurned(address indexed from, uint256 amount);

    constructor(
        string memory name_,
        string memory symbol_,
        uint8 decimals_,
        uint256 initialSupply,
        uint256 maxSupply_
    ) ERC20(name_, symbol_) Ownable(msg.sender) {
        require(decimals_ <= 18, "Decimals cannot exceed 18");
        require(maxSupply_ >= initialSupply, "Max supply must be >= initial");
        require(maxSupply_ <= 100_000_000_000 * 10**decimals_, "Cannot exceed 100B Verdis supply cap");

        _decimals = decimals_;
        maxSupply = maxSupply_;

        if (initialSupply > 0) {
            _mint(msg.sender, initialSupply);
        }
    }

    function decimals() public view override returns (uint8) {
        return _decimals;
    }

    function mint(address to, uint256 amount) external onlyOwner whenNotPaused {
        require(totalSupply() + amount <= maxSupply, "Exceeds max supply");
        _mint(to, amount);
        emit TokensMinted(to, amount);
    }

    function burn(uint256 amount) external whenNotPaused {
        _burn(msg.sender, amount);
        emit TokensBurned(msg.sender, amount);
    }

    function burnFrom(address account, uint256 amount) external onlyOwner whenNotPaused {
        _burn(account, amount);
        emit TokensBurned(account, amount);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }
}
