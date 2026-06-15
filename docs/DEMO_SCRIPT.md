# Demo Video Script (≤3 min)

---

## Structure (3 min = 180 sec)

| Seg. | Duration | What to show | On-screen caption |
|------|----------|--------------|-------------------|
| 0 | 0–15 s | Title slide: «Mantle Sentinel — Behavioral DNA for DeFi» | — |
| 1 | 15–45 s | Terminal: `python bench/self_attack.py --warmup 30` — 30 benign txs, drift ≈ 0.09 | «Normal behavior baseline» |
| 2 | 45–75 s | Terminal continues: 8 hi-entropy attack txs → `entropy_anomaly` alerts in console | «Attack detected» |
| 3 | 75–95 s | Mantlescan: anchor tx `0x086cf07a…fa91c`, status=1 | «Anchored on-chain» |
| 4 | 95–115 s | Dashboard `dashboard/index.html` in browser: drift gauge ≈ 1.0, alert row `ENTR`, drift bar | «Live dashboard» |
| 5 | 115–140 s | Terminal or file: Z.ai explanation («selector distribution changed 61%, gas elevated 22%…») | «Z.ai explains why» |
| 6 | 140–165 s | Code: `sentinel/dream.py` + `sentinel/bocpd.py` — show key line of each | «Self-healing + Bayesian detection» |
| 7 | 165–180 s | GitHub repo + DoraHacks link + contract on Mantlescan. «Try it yourself» | — |

---

## Production notes

1. **Segments 1–2**: run `bench/self_attack.py` with live env (MANTLE_PRIVATE_KEY, ZAI_API_KEY, TELEGRAM_BOT_TOKEN). Do a `--dry-run` first, then record the live run.
2. **Segment 3**: open `https://mantlescan.xyz/tx/0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c` in the browser.
3. **Segment 4**: open `dashboard/index.html` locally (file:// or local server). Alerts from the previous live run should be visible. Show gauge and table.
4. **Segment 5**: if Z.ai is live — show real output; if API limit — use a pre-generated explanation text.
5. **Segment 6**: recommended — open `sentinel/dream.py` line `V_new = sign(λ * V_old + Σ safe)`, then `sentinel/bocpd.py` line `last_cp_prob = R[:prev_map].sum()`. 5 seconds each. Demonstrates real code.
6. **Voiceover / captions**: English, «technical founder» tone, not marketing. Mention numbers 4.3×, 0 FP, ≤2 windows in segments 1–2.

---

## Key phrases for voiceover

- «Every normal day, your protocol has a behavioral fingerprint.»
- «Sentinel learns it — 10,000-dimensional hypervector, no training.»
- «Within 100 transactions of the attack: alert fired, anchored on Mantle mainnet.»
- «Z.ai explains *why* — not a black box.»
- «Dream Mode keeps the baseline current without retraining.»
- «BOCPD catches gradual drift before your static threshold would.»
- «Open source. 109 tests. Deterministic.»

---

## References

- Contract (mainnet): `0x0899E1507CFfefF8620455721F5bd528Bb072187`
- Anchor tx: `0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c` (block 96,680,154)
- Landing: https://mntsentinel.xyz
