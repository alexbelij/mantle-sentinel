# Contracts

## Deployed Addresses

### Mantle Mainnet (chainId 5000)

| Contract | Address | Explorer |
|----------|---------|---------|
| SentinelAlertRegistry | `0x593C9a4dd6806510e379e30481eaCd27d2016FbE` | [View](https://explorer.mantle.xyz/address/0x593C9a4dd6806510e379e30481eaCd27d2016FbE) |

- Deploy block: 96,624,965
- Deploy tx: `0xac6ff2a2f4cbb7e7d8ac37fe1094f1f7a52b4bf144931932fdbbd11a3bcd4...`

### Sepolia Testnet (chainId 11155111)

| Contract | Address | Explorer |
|----------|---------|---------|
| VictimCounter (demo target) | `0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64` | [View](https://sepolia.etherscan.io/address/0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64) |

## SentinelAlertRegistry ABI (key methods)

```solidity
// Log an alert on-chain
function logAlert(
    address target,
    string calldata alertType,
    uint256 driftScore,    // scaled ×1e18
    string calldata payload // JSON summary
) external;

// Read latest alert for a target
function latestAlert(address target) 
    external view returns (Alert memory);

struct Alert {
    address target;
    string  alertType;
    uint256 driftScore;
    string  payload;
    uint256 timestamp;
}
```

## Source

Solidity source: `contracts/SentinelAlertRegistry.sol`  
Deployment config: `contracts/deployments.json`

## Alert Schema

Full JSON schema: `contracts/alert.schema.json`

```json
{
  "alert_type": "entropy_anomaly | drift_alert | spam_attack",
  "target": "0x...",
  "drift_score": 0.87,
  "detector": "static | bocpd",
  "dream_mode": false,
  "attribution": {...},
  "timestamp": 1718323200
}
```
