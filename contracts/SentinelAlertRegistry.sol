// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title  SentinelAlertRegistry v2
/// @notice Immutable on-chain registry for Mantle Sentinel behavioral-drift alerts.
///         Only the authorized reporter (the Sentinel agent wallet set at deploy time)
///         may write. All reads are O(1) or bounded-gas. Events carry the storage
///         index so any off-chain consumer can reconstruct the full timeline without
///         scanning the entire array.
///
/// @dev    driftScore is scaled ×10000:
///           0      = 0.0000 (no drift)
///           10 000 = 1.0000 (maximum drift)
///         Example: pipeline value 0.87  → pass 8700 as driftScore.
contract SentinelAlertRegistry {

    // ─── Types ───────────────────────────────────────────────────────────────

    struct Alert {
        address reporter;   // msg.sender (Sentinel agent wallet)
        uint256 windowId;   // monitoring-window block number
        uint32  driftScore; // drift severity ×10000, range 0..10000
        bytes4  alertType;  // four-byte tag: ENTR, HMNG, TMNG, etc.
        uint64  timestamp;  // block.timestamp at log time (seconds)
    }

    // ─── State ───────────────────────────────────────────────────────────────

    /// @notice Address authorised to write alerts (immutable after deploy)
    address public immutable owner;

    Alert[] private _alerts;

    // ─── Events ──────────────────────────────────────────────────────────────

    event AlertLogged(
        address indexed reporter,
        uint256 indexed windowId,
        uint32          driftScore,
        bytes4          alertType,
        uint64          timestamp,
        uint256         alertIndex   // position in _alerts[] for O(1) getAlert()
    );

    // ─── Errors ──────────────────────────────────────────────────────────────

    error Unauthorized();
    error InvalidDriftScore(uint32 score);
    error IndexOutOfBounds(uint256 requested, uint256 length);

    // ─── Constructor ─────────────────────────────────────────────────────────

    constructor() {
        owner = msg.sender;
    }

    // ─── Modifier ────────────────────────────────────────────────────────────

    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    // ─── Write ───────────────────────────────────────────────────────────────

    /// @notice Log a drift alert on-chain.
    ///         Can only be called by the Sentinel agent wallet (owner).
    /// @param windowId   Block number of the monitoring window that triggered the alert
    /// @param driftScore Drift severity ×10000. Must be in 0..10000.
    ///                   Pass (float_score * 10000) truncated to uint32.
    /// @param alertType  Four-byte alert category tag:
    ///                     0x454e5452 = "ENTR" (entropy)
    ///                     0x484d4e47 = "HMNG" (Hamming)
    ///                     0x544d4e47 = "TMNG" (timing)
    function logAlert(
        uint256 windowId,
        uint32  driftScore,
        bytes4  alertType
    ) external onlyOwner {
        if (driftScore > 10_000) revert InvalidDriftScore(driftScore);

        uint256 idx = _alerts.length;
        uint64  ts  = uint64(block.timestamp);

        _alerts.push(Alert({
            reporter:   msg.sender,
            windowId:   windowId,
            driftScore: driftScore,
            alertType:  alertType,
            timestamp:  ts
        }));

        emit AlertLogged(msg.sender, windowId, driftScore, alertType, ts, idx);
    }

    // ─── Read ────────────────────────────────────────────────────────────────

    /// @notice Total number of logged alerts
    function getAlertCount() external view returns (uint256) {
        return _alerts.length;
    }

    /// @notice Retrieve a single alert by its storage index
    /// @param index Zero-based position (0 = first ever alert)
    function getAlert(uint256 index) external view returns (Alert memory) {
        if (index >= _alerts.length)
            revert IndexOutOfBounds(index, _alerts.length);
        return _alerts[index];
    }

    /// @notice Return the last `count` alerts ordered newest-first.
    ///         If count exceeds the total, all alerts are returned.
    ///         Maximum recommended: 50 alerts per call (gas safety margin).
    /// @param count Maximum number of alerts to return
    function getLatestAlerts(uint256 count)
        external view
        returns (Alert[] memory result)
    {
        uint256 total = _alerts.length;
        uint256 n     = count > total ? total : count;
        result = new Alert[](n);
        unchecked {
            for (uint256 i = 0; i < n; ++i) {
                result[i] = _alerts[total - 1 - i];
            }
        }
    }
}
