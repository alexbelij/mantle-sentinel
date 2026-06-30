"""sentinel/plugins/prototype_store.py — Versioned HDC prototype store.

Stores the last K=5 prototype vectors with metadata so the operator can
roll back if the False Positive rate spikes after a Dream Mode consolidation.

Design constraints
------------------
    * No external dependencies — pure stdlib (json, pathlib, threading, gzip).
    * Thread-safe: all mutations hold a reentrant lock.
    * Atomic file writes: write to temp file, then os.replace() — no partial
      writes on crash.
    * Overflow guard: the store never holds more than ``max_versions`` entries;
      oldest is evicted automatically.
    * The prototype vector is stored as a compact gzip+base64 blob so even a
      D=10,000 int8 vector fits in a few KB on disk.
    * No numpy dependency at import time — numpy is imported lazily only when
      a vector is stored/loaded.

Schema (each version record)
-----------------------------
    {
        "epoch_id":            str,    # unique epoch identifier
        "timestamp":           str,    # ISO-8601 UTC
        "consolidation_count": int,    # Dream Mode consolidation counter
        "contract":            str,    # contract address this prototype guards
        "drift_median":        float,  # median drift at consolidation time
        "vector_b64gz":        str,    # gzip+base64 encoded int8 numpy array
        "dim":                 int,    # HDC dimension (must equal len of vector)
    }

Usage
-----
    from sentinel.plugins.prototype_store import PrototypeStore
    import numpy as np

    store = PrototypeStore("/data/sentinel/prototypes", contract="0x...")

    # Save after each Dream Mode consolidation
    epoch = store.save(vector=prototype_vector, consolidation_count=42, drift_median=0.12)

    # List available epochs (newest first)
    for rec in store.list():
        print(rec["epoch_id"], rec["timestamp"])

    # Rollback to previous version
    prev = store.list()[1]
    vector = store.load(prev["epoch_id"])
"""
from __future__ import annotations

import base64
import gzip
import json
import os
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# PrototypeStore
# ---------------------------------------------------------------------------

class PrototypeStore:
    """Append-only, capped store for HDC prototype versions.

    Parameters
    ----------
    directory : str | Path
        Directory on disk where the store file lives. Created if absent.
    contract : str
        Contract address this store manages (used in metadata + filename).
    max_versions : int
        Maximum number of versions to retain (default 5). When exceeded,
        the oldest version is evicted.
    """

    _INDEX_VERSION = 1

    def __init__(
        self,
        directory: str | Path,
        contract: str,
        max_versions: int = 5,
    ) -> None:
        if not contract or not isinstance(contract, str):
            raise ValueError("contract must be a non-empty string")
        if not isinstance(max_versions, int) or max_versions < 1:
            raise ValueError(
                f"max_versions must be a positive integer; got {max_versions!r}"
            )

        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)

        # Sanitise contract address for use in filename
        safe = contract.lower().replace("0x", "").replace("/", "_")[:40]
        self._path = self._dir / f"prototype_store_{safe}.json"

        self._contract     = contract
        self._max_versions = max_versions
        self._lock         = threading.RLock()

        # Initialise or load existing store
        self._index: dict[str, Any] = self._load_index()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(
        self,
        vector: Any,
        consolidation_count: int,
        drift_median: float,
        epoch_id: str | None = None,
    ) -> str:
        """Persist a new prototype version.

        Parameters
        ----------
        vector :
            A numpy ndarray (int8 or bool) of shape ``(D,)``.
        consolidation_count : int
            Dream Mode consolidation counter at the time of this save.
        drift_median : float
            Median drift score over the consolidation window. Used by the
            caller to detect poison (> 0.3 → block consolidation).
        epoch_id : str, optional
            Custom epoch identifier. Auto-generated UUID4 if omitted.

        Returns
        -------
        str
            The ``epoch_id`` under which the version was stored.

        Raises
        ------
        ValueError
            * ``vector`` is None or has wrong shape/dtype.
            * ``consolidation_count`` < 0.
            * ``drift_median`` outside [0.0, 1.0].
        ImportError
            numpy is not installed (required for vector serialisation).
        """
        import numpy as np  # lazy import — not required at module load

        if vector is None:
            raise ValueError("vector must not be None")
        if not isinstance(vector, np.ndarray):
            raise TypeError(
                f"vector must be a numpy ndarray; got {type(vector).__name__}"
            )
        if vector.ndim != 1:
            raise ValueError(
                f"vector must be 1-D; got shape {vector.shape}"
            )
        if len(vector) == 0:
            raise ValueError("vector must not be empty")
        if not isinstance(consolidation_count, int) or consolidation_count < 0:
            raise ValueError(
                f"consolidation_count must be a non-negative int; got {consolidation_count!r}"
            )
        if not isinstance(drift_median, (int, float)):
            raise ValueError(
                f"drift_median must be a float; got {type(drift_median).__name__}"
            )
        import math
        if math.isnan(drift_median) or math.isinf(drift_median):
            raise ValueError(f"drift_median must be finite; got {drift_median!r}")
        if not (0.0 <= float(drift_median) <= 1.0):
            raise ValueError(
                f"drift_median={drift_median!r} outside [0.0, 1.0]"
            )

        eid = epoch_id or str(uuid.uuid4())
        ts  = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Serialise vector: cast to int8, gzip, base64
        v8  = vector.astype(np.int8)
        gz  = gzip.compress(v8.tobytes(), compresslevel=6)
        b64 = base64.b64encode(gz).decode("ascii")

        record: dict[str, Any] = {
            "epoch_id":            eid,
            "timestamp":           ts,
            "consolidation_count": consolidation_count,
            "contract":            self._contract,
            "drift_median":        float(drift_median),
            "vector_b64gz":        b64,
            "dim":                 len(vector),
        }

        with self._lock:
            versions: list[dict] = self._index.get("versions", [])
            versions.append(record)

            # Evict oldest if over capacity
            if len(versions) > self._max_versions:
                versions = versions[-self._max_versions:]

            self._index["versions"] = versions
            self._flush()

        return eid

    def load(self, epoch_id: str) -> Any:
        """Load a prototype vector by epoch_id.

        Returns
        -------
        numpy.ndarray
            int8 array of shape ``(D,)``.

        Raises
        ------
        KeyError
            ``epoch_id`` not found in the store.
        ImportError
            numpy is not installed.
        """
        import numpy as np

        with self._lock:
            rec = self._get_record(epoch_id)

        gz  = base64.b64decode(rec["vector_b64gz"])
        raw = gzip.decompress(gz)
        return np.frombuffer(raw, dtype=np.int8).copy()

    def list(self) -> list[dict[str, Any]]:
        """Return version metadata (newest first), without vector blobs."""
        with self._lock:
            versions = self._index.get("versions", [])
            return [
                {k: v for k, v in rec.items() if k != "vector_b64gz"}
                for rec in reversed(versions)
            ]

    def latest(self) -> dict[str, Any] | None:
        """Return the metadata of the most recent version, or None."""
        recs = self.list()
        return recs[0] if recs else None

    def delete(self, epoch_id: str) -> None:
        """Remove a specific version from the store."""
        with self._lock:
            versions = self._index.get("versions", [])
            before = len(versions)
            self._index["versions"] = [
                r for r in versions if r["epoch_id"] != epoch_id
            ]
            if len(self._index["versions"]) == before:
                raise KeyError(f"epoch_id {epoch_id!r} not found in store")
            self._flush()

    def clear(self) -> None:
        """Remove ALL versions from the store (irreversible)."""
        with self._lock:
            self._index["versions"] = []
            self._flush()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_record(self, epoch_id: str) -> dict[str, Any]:
        for rec in self._index.get("versions", []):
            if rec["epoch_id"] == epoch_id:
                return rec
        raise KeyError(
            f"epoch_id {epoch_id!r} not found. "
            f"Available: {[r['epoch_id'] for r in self._index.get('versions', [])]}"
        )

    def _load_index(self) -> dict[str, Any]:
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if not isinstance(data, dict):
                    raise ValueError("corrupt index — expected a JSON object")
                return data
            except (json.JSONDecodeError, ValueError):
                # Corrupt file: start fresh but keep a backup
                backup = self._path.with_suffix(".corrupt.json")
                self._path.rename(backup)
        return {"_version": self._INDEX_VERSION, "versions": []}

    def _flush(self) -> None:
        """Atomic write: temp file → os.replace()."""
        tmp = self._path.with_suffix(".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(self._index, fh, indent=2, ensure_ascii=False)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self._path)
        except Exception:
            # Clean up temp file on failure; do not leave partial state
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise
