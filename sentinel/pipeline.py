"""End-to-end detection pipeline — the single live entrypoint (T-08).

The benchmark/replay harness drives this exact `process_tx` (BENCHMARK_PROTOCOL §0,
no eval fork). Tier order per ARCHITECTURE_FREEZE:

    Tier 0 spam pre-filter → Tier 1 entropy → Tier 2 HDC encode + drift
        → Tier 3 static detector → Tier 4 interpreter → Alert JSON
"""
from __future__ import annotations

from collections import deque

import numpy as np

from sentinel.alert import Alert, iso_ts, make_alert_id
from sentinel.bocpd import BOCPDDetector
from sentinel.config import WARMUP_FRAC, WINDOW, detector_name
from sentinel.detector import StaticThresholdDetector
from sentinel.dream import dream_update
from sentinel.drift import DriftTracker
from sentinel.entropy import EntropyFilter
from sentinel.episodes import EpisodeTracker
from sentinel.explain_zai import explain_alert
from sentinel.features import FeatureExtractor, RawTx
from sentinel.hdc import HDCSpace
from sentinel.interpreter import Interpreter, ProtoSet
from sentinel.notify_telegram import notify_telegram
from sentinel.prefilter import SpamPrefilter


class Pipeline:
    def __init__(
        self,
        contract: str,
        extractor: FeatureExtractor,
        space: HDCSpace,
        protoset: ProtoSet,
        tracker: DriftTracker,
        detector: StaticThresholdDetector | BOCPDDetector,
        entropy: EntropyFilter,
        prefilter: SpamPrefilter,
        interpreter: Interpreter,
        dream_mode: bool = False,
        n_dream: int = 100,
        alpha_dream: float = 0.5,
    ):
        self.contract = contract.lower()
        self.extractor = extractor
        self.space = space
        self.protoset = protoset
        self.tracker = tracker
        self.detector = detector
        self.entropy = entropy
        self.prefilter = prefilter
        self.interpreter = interpreter
        self._feat_window: deque = deque(maxlen=WINDOW)
        self._vec_window: deque = deque(maxlen=WINDOW)
        self._spam_ep = EpisodeTracker(prefix="spam")
        self._entropy_ep = EpisodeTracker(prefix="entropy")
        self.last_drift: float | None = None  # observability (spike/metrics)

        # Dream Mode (T-18, MVP_MATH_SPEC §6): periodically consolidate "safe"
        # window vectors back into the drift prototype so the baseline tracks slow,
        # legitimate drift. A window is safe iff the Tier-4 detector did not fire AND
        # its drift is below the recent median (proxy for the spec's ±50-block locale).
        self.dream_mode = bool(dream_mode)
        self.n_dream = int(n_dream)
        self.alpha_dream = float(alpha_dream)
        self._safe_buf: list[np.ndarray] = []
        self._drift_hist: deque[float] = deque(maxlen=100)
        self._dream_min_hist = WINDOW  # need a stable median before consolidating
        self.dream_count = 0  # observability: number of consolidations performed

    def process_tx(self, r: RawTx) -> list[Alert]:
        alerts: list[Alert] = []
        ts = float(r["block_timestamp"])
        block = int(r["block_number"])
        calldata = r.get("calldata", "0x") or "0x"
        feat, dt = self.extractor.extract(r)

        # Tier 0 — spam pre-filter
        spam = self.prefilter.process(dt)
        if spam.alert:
            ep, _ = self._spam_ep.assign(ts)
            alerts.append(self._mk(block, ts, "spam_attack", "spam", 1.0, [], ep, {"interval": dt}))
        if spam.is_spam:
            return self._enrich(alerts)  # excluded from all baselines/windows

        # Tier 1 — entropy (independent sensor, bypasses Tier 4)
        if self.entropy.check(calldata):
            ep, _ = self._entropy_ep.assign(ts)
            alerts.append(
                self._mk(block, ts, "entropy_anomaly", "entropy", 1.0, [], ep, {"selector": feat.selector})
            )

        # Tier 2 — HDC encode + window bundle + drift
        self._feat_window.append(feat)
        self._vec_window.append(self.space.encode_tx(feat))
        if len(self._vec_window) < WINDOW:
            return self._enrich(alerts)
        v_win = self.space.bundle(list(self._vec_window))
        dr = self.tracker.update(v_win, dt)
        self.last_drift = dr.drift

        # Tier 3 — static detector
        trig = self.detector.process(dr.drift, ts)

        # Dream Mode — consolidate safe windows into the prototype (opt-in)
        if self.dream_mode:
            self._dream_step(v_win, dr.drift, fired=trig is not None)

        if trig is None:
            return self._enrich(alerts)

        # Tier 4/5 — interpreter
        top = self.interpreter.attribute(list(self._feat_window), dr.branch)
        alerts.append(
            self._mk(
                block, ts, "regime_shift", dr.branch, round(dr.drift, 6), top, trig.episode_id,
                {"hamming": round(dr.hamming, 6), "timing": round(dr.timing, 6)},
            )
        )
        return self._enrich(alerts)

    def _dream_step(self, v_win: np.ndarray, drift: float, fired: bool) -> None:
        """Accumulate safe window vectors and consolidate every ``n_dream`` of them.

        ``λ = alpha_dream · N`` (D-04). Consolidation replaces the drift prototype
        with ``sign(λ·V_old + Σ V_safe)``. An alert clears the pending batch so attack
        windows are never folded into the baseline.
        """
        if fired:
            self._safe_buf.clear()
            self._drift_hist.append(drift)
            return
        med = (
            float(np.median(self._drift_hist))
            if len(self._drift_hist) >= self._dream_min_hist
            else None
        )
        self._drift_hist.append(drift)
        if med is None or drift >= med:
            return  # not a "safe" (below-median) window
        self._safe_buf.append(v_win)
        if len(self._safe_buf) >= self.n_dream:
            self.tracker.prototype = dream_update(
                self.tracker.prototype, self._safe_buf, alpha=self.alpha_dream
            )
            self._safe_buf.clear()
            self.dream_count += 1

    def _enrich(self, alerts: list[Alert]) -> list[Alert]:
        """Attach Z.ai explanation and send Telegram notification for each alert."""
        for a in alerts:
            a.explanation = explain_alert(a)
            notify_telegram(a)
        return alerts

    def _mk(self, block, ts, alert_type, branch, drift, top, episode_id, window_stats) -> Alert:
        return Alert(
            alert_id=make_alert_id(alert_type, self.contract, block),
            ts=iso_ts(ts),
            block=block,
            contract=self.contract,
            alert_type=alert_type,
            drift=drift,
            branch=branch,
            top_features=top,
            window_stats=window_stats,
            episode_id=episode_id,
        )


def _make_detector(name: str | None) -> StaticThresholdDetector | BOCPDDetector:
    """Select the Tier-4 detector ('static' | 'bocpd'); falls back to env, then static."""
    kind = (name or detector_name()).strip().lower()
    if kind == "bocpd":
        return BOCPDDetector()
    return StaticThresholdDetector()


def build_pipeline(
    contract: str,
    warmup: list[RawTx],
    detector: str | None = None,
    dream_mode: bool = False,
    n_dream: int = 100,
) -> Pipeline:
    """Construct a pipeline whose baselines are all fit/frozen on the warm-up split.

    ``detector`` selects the Tier-4 detector ('static' | 'bocpd'); when None it is
    resolved from the SENTINEL_DETECTOR env var (frozen default: 'static').
    ``dream_mode`` enables periodic Dream-Mode consolidation of the drift prototype
    every ``n_dream`` safe windows (MVP_MATH_SPEC §6); off by default (frozen behaviour).
    """
    extractor = FeatureExtractor().fit(warmup)
    space = HDCSpace()

    # stream warm-up to extract features (populates streaming state) + intervals
    warm_feats = []
    warm_dts = []
    for r in warmup:
        f, dt = extractor.extract(r)
        warm_feats.append(f)
        warm_dts.append(dt)

    protoset = ProtoSet(space, warm_feats)
    entropy = EntropyFilter().fit([r.get("calldata", "0x") or "0x" for r in warmup])
    prefilter = SpamPrefilter().fit([d for d in warm_dts if d > 0])
    tracker = DriftTracker(space, protoset.full)
    detector_obj = _make_detector(detector)
    interpreter = Interpreter(protoset)

    # seed the drift normalizer on warm-up windows (no alerts recorded)
    enc = [space.encode_tx(f) for f in warm_feats]
    win: deque = deque(maxlen=WINDOW)
    for i, v in enumerate(enc):
        win.append(v)
        if len(win) == WINDOW:
            tracker.update(space.bundle(list(win)), warm_dts[i])

    return Pipeline(
        contract, extractor, space, protoset, tracker, detector_obj, entropy, prefilter, interpreter,
        dream_mode=dream_mode, n_dream=n_dream,
    )


def split_warmup(records: list[RawTx], frac: float = WARMUP_FRAC) -> tuple[list[RawTx], list[RawTx]]:
    n = int(len(records) * frac)
    return records[:n], records[n:]
