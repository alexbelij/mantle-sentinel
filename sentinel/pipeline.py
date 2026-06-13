"""End-to-end detection pipeline — the single live entrypoint (T-08).

The benchmark/replay harness drives this exact `process_tx` (BENCHMARK_PROTOCOL §0,
no eval fork). Tier order per ARCHITECTURE_FREEZE:

    Tier 0 spam pre-filter → Tier 1 entropy → Tier 2 HDC encode + drift
        → Tier 3 static detector → Tier 4 interpreter → Alert JSON
"""
from __future__ import annotations

from collections import deque

from sentinel.alert import Alert, iso_ts, make_alert_id
from sentinel.config import WARMUP_FRAC, WINDOW
from sentinel.detector import StaticThresholdDetector
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
        detector: StaticThresholdDetector,
        entropy: EntropyFilter,
        prefilter: SpamPrefilter,
        interpreter: Interpreter,
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


def build_pipeline(contract: str, warmup: list[RawTx]) -> Pipeline:
    """Construct a pipeline whose baselines are all fit/frozen on the warm-up split."""
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
    detector = StaticThresholdDetector()
    interpreter = Interpreter(protoset)

    # seed the drift normalizer on warm-up windows (no alerts recorded)
    enc = [space.encode_tx(f) for f in warm_feats]
    win: deque = deque(maxlen=WINDOW)
    for i, v in enumerate(enc):
        win.append(v)
        if len(win) == WINDOW:
            tracker.update(space.bundle(list(win)), warm_dts[i])

    return Pipeline(
        contract, extractor, space, protoset, tracker, detector, entropy, prefilter, interpreter
    )


def split_warmup(records: list[RawTx], frac: float = WARMUP_FRAC) -> tuple[list[RawTx], list[RawTx]]:
    n = int(len(records) * frac)
    return records[:n], records[n:]
