"""Tier 5 — DNA Drift explainer (MVP_MATH_SPEC §5).

Feature-ablation attribution (D-01): recompute the window bundle with feature f
ablated (V_win^{-f}) against an ablated prototype (P^{-f}), and attribute drift to
the feature whose ablation most reduces the Hamming distance:

    contribution_f = hamming(V_win, P) − hamming(V_win^{-f}, P^{-f})        (normalised by D)

Report the top-2 features with contribution > 0. Timing-branch alerts are
attributed directly to `timing`. The 5 ablated prototypes are precomputed once.
"""
from __future__ import annotations

import numpy as np

from sentinel.alert import FeatureContribution
from sentinel.hdc import FEATURE_GROUPS, HDCSpace, TxFeatures


class ProtoSet:
    """Full Behavioral DNA prototype + one ablated prototype per feature group."""

    def __init__(self, space: HDCSpace, warmup: list[TxFeatures]):
        self.space = space
        self.full = space.bundle([space.encode_tx(f) for f in warmup])
        self.ablated = {
            g: space.bundle([space.encode_tx(f, ablate=g) for f in warmup])
            for g in FEATURE_GROUPS
        }


class Interpreter:
    def __init__(self, protoset: ProtoSet):
        self.space = protoset.space
        self.protos = protoset

    def _hamming_norm(self, a: np.ndarray, b: np.ndarray) -> float:
        return self.space.hamming(a, b) / self.space.d

    def attribute(
        self, window_feats: list[TxFeatures], branch: str, top_n: int = 2
    ) -> list[FeatureContribution]:
        if branch == "timing":
            return [FeatureContribution(name="timing", contribution=1.0)]

        v_win = self.space.bundle([self.space.encode_tx(f) for f in window_feats])
        h_full = self._hamming_norm(v_win, self.protos.full)

        contribs: list[FeatureContribution] = []
        for g in FEATURE_GROUPS:
            v_win_g = self.space.bundle(
                [self.space.encode_tx(f, ablate=g) for f in window_feats]
            )
            h_g = self._hamming_norm(v_win_g, self.protos.ablated[g])
            contribs.append(FeatureContribution(name=g, contribution=round(h_full - h_g, 6)))

        contribs = [c for c in contribs if c.contribution > 0]
        contribs.sort(key=lambda c: c.contribution, reverse=True)
        return contribs[:top_n]
