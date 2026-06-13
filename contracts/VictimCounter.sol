// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title VictimCounter
/// @notice A simple counter contract — used as the self-attack target in T-13c demo
contract VictimCounter {
    uint256 public count;

    function increment() external {
        count++;
    }

    function reset() external {
        count = 0;
    }

    /// @notice Overloaded selector for S7 mutation testing
    function incrementBy(uint256 n) external {
        count += n;
    }
}
