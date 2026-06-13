// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title SentinelAlertRegistry
/// @notice On-chain registry for Mantle Sentinel drift alerts
contract SentinelAlertRegistry {
    struct Alert {
        address reporter;
        uint256 windowId;
        uint32  driftScore;
        bytes4  alertType;
        uint64  timestamp;
    }

    Alert[] private _alerts;

    event AlertLogged(
        address indexed reporter,
        uint256 indexed windowId,
        uint32  driftScore,
        bytes4  alertType,
        uint64  timestamp
    );

    /// @notice Log a drift alert on-chain
    /// @param windowId   The monitoring window identifier
    /// @param driftScore Numeric drift severity (0–4294967295)
    /// @param alertType  Four-byte alert category tag
    function logAlert(
        uint256 windowId,
        uint32  driftScore,
        bytes4  alertType
    ) external {
        uint64 ts = uint64(block.timestamp);
        _alerts.push(Alert({
            reporter:   msg.sender,
            windowId:   windowId,
            driftScore: driftScore,
            alertType:  alertType,
            timestamp:  ts
        }));
        emit AlertLogged(msg.sender, windowId, driftScore, alertType, ts);
    }

    /// @notice Total number of logged alerts
    function getAlertCount() external view returns (uint256) {
        return _alerts.length;
    }

    /// @notice Retrieve a single alert by index
    function getAlert(uint256 index)
        external
        view
        returns (
            address reporter,
            uint256 windowId,
            uint32  driftScore,
            bytes4  alertType,
            uint64  timestamp
        )
    {
        require(index < _alerts.length, "Index out of bounds");
        Alert storage a = _alerts[index];
        return (a.reporter, a.windowId, a.driftScore, a.alertType, a.timestamp);
    }
}
