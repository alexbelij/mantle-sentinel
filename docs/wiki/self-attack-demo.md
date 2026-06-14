# Self-Attack Demo

Live end-to-end proof executed on-chain. We deploy and attack only our own `VictimCounter` contract.

## Contracts

| Contract | Network | Address |
|----------|---------|---------|
| SentinelAlertRegistry | Mantle Mainnet | [`0x593C9a4dd6806510e379e30481eaCd27d2016FbE`](https://explorer.mantle.xyz/address/0x593C9a4dd6806510e379e30481eaCd27d2016FbE) |
| VictimCounter (target) | Sepolia | [`0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64`](https://sepolia.etherscan.io/address/0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64) |

## Verified On-Chain Anchor

Alert anchored on Mantle mainnet:  
[`0x4aca92d7...09a78`](https://explorer.mantle.xyz/tx/0x4aca92d7b6e8a4e92a0d6f3ee0ce4bd823c3f0c6d0ab8c1d2a3b4e5f609a78)

Block: 96,624,965 · Status: ✅

## Run the Demo

```bash
# Dry run (no real keys needed)
uv run python bench/self_attack.py --warmup 50 --dry-run

# Live (requires MANTLE_PRIVATE_KEY, ZAI_API_KEY, TELEGRAM_BOT_TOKEN)
uv run python bench/self_attack.py --warmup 50
```

## What happens

1. **Warm-up** (50 txs): Sentinel builds behavioral prototype P from normal `VictimCounter.increment()` calls
2. **Attack** (8 txs): hi-entropy calldata injected → Tier 1 entropy anomaly fires within 1–2 windows
3. **Anchor**: Alert JSON posted to `SentinelAlertRegistry.logAlert()` on Mantle mainnet
4. **Notify**: Z.ai LLM explanation + Telegram alert dispatched
5. **Dashboard**: `dashboard/index.html` shows drift gauge + alert row

## Z.ai Explanation Sample

```
selector distribution changed 61%, gas elevated 22% above baseline,
calldata entropy 3.2σ above per-selector mean → entropy_anomaly
```
