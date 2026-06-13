# T-13c — Self-attack END-TO-END (LIVE), verified on-chain

Executed by **Developer Viktor** on 2026-06-13. We deploy and attack only our
own `VictimCounter`. `bench/self_attack.py` `run_live()` implements the real
flow (it was a placeholder before).

## Flow
1. **Warm-up (Mantle Sepolia 5003):** 30 benign `incrementBy(small)` txs → low byte-entropy bodies. Pipeline (`build_pipeline`) is fit on this real traffic.
2. **Attack (same chain):** 8 `incrementBy(random 256-bit)` txs — same selector `0x03df179c`, same length bucket, high-entropy body. Each fires a real Tier-1 `entropy_anomaly`.
3. **Anchor (Mantle mainnet 5000):** the first alert is written to `SentinelAlertRegistry.logAlert(windowId, driftScore, alertType)`.
4. **Explain + notify:** Z.ai (`glm-4.5-flash`) explanation + Telegram delivery.

## Live evidence (verified server-side)
| Item | Value |
|---|---|
| Victim (Sepolia) | `0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64` |
| Signer / reporter | `0x419E59C9A0C825491477BE7bfDD7B0A17E9aF5CD` |
| Warm-up txs | 30 (blocks 39920651–39920656) |
| Attack txs | 8 → **8 `entropy_anomaly`** alerts |
| First alert | `entropy_anomaly-0x1f88…68e64-39920662` (drift 1.0, branch entropy, selector `0x03df179c`) |
| Registry (mainnet) | `0x593C9a4dd6806510e379e30481eaCd27d2016FbE` |
| **Anchor tx (mainnet)** | `0x4aca92d711c79a3081ebc700c9ffa5c3d1e4cc44bb5f28d2df02dc6cfad09a78` (status 1, block 96627847) |
| logAlert args | windowId `39920662`, driftScore `1000000`, alertType `0x454e5452` (`ENTR`) |
| Registry state after | `getAlertCount() == 1`; `getAlert(0)` → reporter=signer, windowId=39920662, drift=1000000, type=`ENTR` |
| Explorer | https://explorer.mantle.xyz/tx/0x4aca92d711c79a3081ebc700c9ffa5c3d1e4cc44bb5f28d2df02dc6cfad09a78 |

Z.ai explanation + Telegram alert were generated/sent live for the first alert.

## Run it
```bash
export MANTLE_PRIVATE_KEY=0x...           # funded on Sepolia (+ mainnet for anchor)
export ZAI_API_KEY=...                    # optional: live Z.ai explanation
export TELEGRAM_BOT_TOKEN=...             # optional: live Telegram delivery
.venv/bin/python bench/self_attack.py --rpc https://rpc.sepolia.mantle.xyz
# flags: --warmup N --attack N --no-anchor
```

## Bugs fixed alongside (T-13c/T-19/T-21)
- `bench/self_attack.py`: `SEL_INCREMENT_BY` was `0x30f3f0db`; the real selector is `0x03df179c` (would revert live).
- `sentinel/explain_zai.py`: default base URL/model (`https://api.z.ai/v1`, `z-ai/z-ai-preview`) don't exist → always fell back to canned. Fixed to verified `https://api.z.ai/api/paas/v4` + `glm-4.5-flash`. Also `max_tokens` 200→800: GLM-4.5 is a reasoning model whose hidden thinking phase consumed the small budget and returned empty content.
- `pyproject.toml`: `httpx` was imported by `explain_zai`/`notify_telegram` but missing from deps → live path silently failed. Added it; added a `live` extra (`web3`, `eth-account`).
