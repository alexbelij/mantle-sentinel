"""T-18 — Dream Mode (offline prototype consolidation).

"Dreaming" periodically replays a batch of recently-observed *safe* windows and
folds them back into a contract's behavioral prototype, so the baseline tracks
slow, legitimate drift without ever learning an attack window.

The update (MVP_MATH_SPEC, Dream Mode) is a weighted majority-sign bundle::

    λ      = alpha * N
    V_new  = sign( λ * V_old + Σ_i safe_vectors[i] )

``λ`` is the inertia of the existing prototype expressed *relative to* the number
of safe windows ``N`` being consolidated (so ``alpha`` is a dimensionless ratio:
``alpha`` large ⇒ prototype barely moves; ``alpha`` small ⇒ it snaps toward the
safe batch). Sign / tie convention matches :class:`sentinel.hdc.HDCSpace`
(``sum >= 0 → +1``), keeping vectors bipolar ``{-1, +1}`` int8.
"""
from __future__ import annotations

import numpy as np


def _sign(acc: np.ndarray) -> np.ndarray:
    """Bipolar sign with ties (== 0) resolving to +1 (HDC convention).

    W-DRM-1: tie→+1 introduces a negligible positive bias (exact ties require
    all contributing vectors to cancel, probability ≈ 2^{-N} per dimension).
    """
    return np.where(acc >= 0, 1, -1).astype(np.int8)


def dream_update(
    V_old: np.ndarray,
    safe_vectors: np.ndarray | list[np.ndarray],
    alpha: float = 1.0,
    N: int | None = None,
) -> np.ndarray:
    """Consolidate ``safe_vectors`` into prototype ``V_old``.

    Parameters
    ----------
    V_old:
        Current bipolar prototype, shape ``(D,)``.
    safe_vectors:
        Iterable / array of bipolar safe-window vectors, shape ``(N, D)`` (or a
        single ``(D,)`` vector). Must be non-empty.
    alpha:
        Inertia ratio for the old prototype (``λ = alpha * N``). Default 1.0.
    N:
        Number of safe windows. Defaults to ``len(safe_vectors)``; pass explicitly
        to weight the inertia by a different count than the batch size.

    Returns
    -------
    np.ndarray
        New bipolar prototype ``V_new`` of dtype int8, same shape as ``V_old``.
    """
    V_old = np.asarray(V_old)
    safe = np.asarray(safe_vectors, dtype=np.int64)
    if safe.ndim == 1:
        safe = safe[None, :]
    if safe.shape[0] == 0:
        raise ValueError("dream_update requires at least one safe vector")
    if safe.shape[1] != V_old.shape[0]:
        raise ValueError(
            f"dimension mismatch: V_old has D={V_old.shape[0]}, "
            f"safe_vectors have D={safe.shape[1]}"
        )

    n = safe.shape[0] if N is None else int(N)
    lam = float(alpha) * n
    acc = lam * V_old.astype(np.float64) + safe.sum(axis=0).astype(np.float64)
    return _sign(acc)
