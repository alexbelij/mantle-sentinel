# DEMO_SCRIPT.md — Demo Video Pokadrovyi Stsenariy (≤3 min)

> Kurator Viktor. Podat' v repo kak `docs/DEMO_SCRIPT.md` cherez Developer Viktor.

---

## Struktura (3 min = 180 sek)

| Segm. | Dlitelnost' | Chto pokazyvat' | Vopros na ekrane |
|-------|-------------|-----------------|------------------|
| 0 | 0–15 s | Titulirovannyi slajd: «Mantle Sentinel — Behavioral DNA for DeFi» | — |
| 1 | 15–45 s | Terminal: `python bench/self_attack.py --warmup 30` — 30 benign txs, drift pulsiryet' ~0.09 | «Normal behavior baseline» |
| 2 | 45–75 s | Terminal prodolzhayet'sya: 8 hi-entropy attack txs → `entropy_anomaly` alerts v konsoli | «Attack detected» |
| 3 | 75–95 s | Mantle Explorer: anchor tx `0x4aca92d7…09a78`, status=1 | «Anchored on-chain» |
| 4 | 95–115 s | Dashboard `dashboard/index.html` v brauzere: drift gauge ~1.0, alert row `ENTR`, drift bar | «Live dashboard» |
| 5 | 115–140 s | Terminal ili fajl: Z.ai ob'yasnenie («selector distribution changed 61%, gas elevated 22%…») | «Z.ai explains why» |
| 6 | 140–165 s | Kod `sentinel/dream.py` + `sentinel/bocpd.py` — pokazat' klyuchevuyu stroku kazhdogo | «Self-healing + Bayesian detection» |
| 7 | 165–180 s | GitHub repo + DoraHacks ssylka + kontrakt na Explorer. «Try it yourself» | — |

---

## Prikhmechaniya dlya Developer Viktor

1. **Scenariy 1–2**: zapustit' `bench/self_attack.py` s zhivymi env (MANTLE_PRIVATE_KEY, ZAI_API_KEY, TELEGRAM_BOT_TOKEN). Predvaritel'no sdelat' `--dry-run` prony, zathem zapisat' zhivoj pusk.
2. **Segment 3**: v brauzere otkryt' `https://explorer.mantle.xyz/tx/0x4aca92d7...09a78` — staraya tx, vsegda dostupna.
3. **Segment 4**: otkryt' `dashboard/index.html` lokal'no (file:// ili lokalnyi server). Tam uzhe est' alerty s predydushchego live-pusk. Pokazar' gauge i tablitsu.
4. **Segment 5**: esli Z.ai zhivoe — pokazat' real'nyi output; esli API limit — mozhno pokazat' prigotovlennyi tekst iz `docs/status/T13C_LIVE.md` razdel «Explain + notify».
5. **Segment 6**: rekomendatsiya — otkryt' `sentinel/dream.py` stroka `V_new = sign(λ * V_old + Σ safe)`, potom `sentinel/bocpd.py` stroka `last_cp_prob = R[:prev_map].sum()`. 5 sekund kazhdaya. Demonstriruet chto eto real'nyi kod.
6. **Voiceover / captions**: angliiski, tonalnost' «technical founder», ne «marketing». Tsifry 4.3×, 0 FP, ≤2 windows — upomyanut' v segment 1–2.

---

## Key phrases for voiceover

- «Every normal day, your protocol has a behavioral fingerprint.»
- «Sentinel learns it — 10,000-dimensional hypervector, no training.»
- «Within 100 transactions of the attack: alert fired, anchored on Mantle mainnet.»
- «Z.ai explains *why* — not a black box.»
- «Dream Mode keeps the baseline current without retraining.»
- «BOCPD catches gradual drift before your static threshold would.»
- «Open source. 91 tests. Deterministic.»
