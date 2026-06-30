"""sentinel/plugins/alert_log.py — Persistent alert log plugin.

Provides an append-only NDJSON file + SQLite index for all alerts emitted by the
Sentinel pipeline. Designed as a zero-dependency drop-in: import AlertLog, point
it at a directory, and call .append() after every alert. No changes to core code.

Features
--------
- Atomic NDJSON append (line-buffered, fsync on write)
- SQLite index for fast queries by contract / block / type / fp_flag
- mark_fp(): operator marks an alert as false positive → threshold feedback hook
- Overflow guard: raises OverflowError when log file exceeds max_bytes
- Thread-safe: all public methods use a reentrant lock
- SQL injection–safe: all query parameters are passed via DB-API placeholders
- Graceful handling of KeyboardInterrupt / SystemExit during writes

Schema (SQLite table `alerts`)
-------------------------------
    alert_id    TEXT PRIMARY KEY
    ts          TEXT
    block       INTEGER
    contract    TEXT
    alert_type  TEXT
    drift       REAL
    branch      TEXT
    fp_flag     INTEGER DEFAULT 0   -- 1 = operator-marked false positive
    raw_json    TEXT                -- full serialised alert record
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_ALERT_ID_LEN = 256
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_\-]+$")
_VALID_COLUMNS = frozenset({"contract", "alert_type", "branch", "fp_flag"})
_DEFAULT_MAX_BYTES = 512 * 1024 * 1024  # 512 MB


# ---------------------------------------------------------------------------
# AlertLog
# ---------------------------------------------------------------------------


class AlertLog:
    """Persistent append-only alert log backed by NDJSON + SQLite.

    Parameters
    ----------
    directory:
        Directory where ``alerts.ndjson`` and ``alerts.db`` will be created.
        The directory is created if it does not exist.
    max_bytes:
        Maximum size of the NDJSON file in bytes.  Raises ``OverflowError``
        when the limit would be exceeded.  Default: 512 MB.

    Example
    -------
    >>> log = AlertLog("/var/lib/sentinel/logs")
    >>> log.append(alert)           # Alert dataclass or dict
    >>> results = log.query(contract="0xABC", limit=50)
    >>> log.mark_fp("spam_attack-0xabc-12345")
    """

    def __init__(self, directory: str | Path, max_bytes: int = _DEFAULT_MAX_BYTES) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._ndjson_path = self._dir / "alerts.ndjson"
        self._db_path = self._dir / "alerts.db"
        self._max_bytes = max_bytes
        self._lock = threading.RLock()
        self._init_db()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(self, alert: Any) -> None:
        """Append *alert* to the persistent log.

        Parameters
        ----------
        alert:
            An ``Alert`` dataclass instance, any object with a ``.to_dict()``
            method, or a plain ``dict``.

        Raises
        ------
        ValueError
            If the alert_id is missing, empty, too long, or contains unsafe
            characters (path traversal / injection guard).
        OverflowError
            If appending would exceed ``max_bytes``.
        """
        record = self._to_dict(alert)
        self._validate_alert_id(record.get("alert_id", ""))

        line = json.dumps(record, separators=(",", ":")) + "\n"
        encoded = line.encode("utf-8")

        with self._lock:
            current_size = self._ndjson_path.stat().st_size if self._ndjson_path.exists() else 0
            if current_size + len(encoded) > self._max_bytes:
                raise OverflowError(
                    f"Alert log would exceed max_bytes={self._max_bytes}. "
                    "Rotate or archive the log before appending."
                )
            try:
                with self._ndjson_path.open("ab") as fh:
                    fh.write(encoded)
                    fh.flush()
                    os.fsync(fh.fileno())
            except (KeyboardInterrupt, SystemExit):
                logger.warning("Interrupted during NDJSON write; record may be incomplete.")
                raise
            except Exception as exc:
                logger.error("Failed to write NDJSON: %s", exc)
                raise

            self._index(record)

    def mark_fp(self, alert_id: str) -> bool:
        """Mark *alert_id* as a false positive.

        Returns ``True`` if the record was found and updated, ``False`` if it
        did not exist.  Calling mark_fp on an already-FP alert is idempotent.
        """
        self._validate_alert_id(alert_id)
        with self._lock:
            conn = self._connect()
            try:
                cur = conn.execute(
                    "UPDATE alerts SET fp_flag = 1 WHERE alert_id = ?", (alert_id,)
                )
                conn.commit()
                updated = cur.rowcount > 0
                if not updated:
                    logger.warning("mark_fp: alert_id %r not found in index.", alert_id)
                return updated
            finally:
                conn.close()

    def query(
        self,
        *,
        contract: str | None = None,
        alert_type: str | None = None,
        branch: str | None = None,
        fp_flag: int | None = None,
        block_min: int | None = None,
        block_max: int | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Query the SQLite index.

        All filter parameters are combined with AND.  Returns a list of raw
        alert dicts (deserialised from ``raw_json``), newest-first.

        Parameters
        ----------
        contract, alert_type, branch:
            Exact-match string filters.
        fp_flag:
            ``0`` for non-FP, ``1`` for FP alerts.
        block_min, block_max:
            Inclusive block range filter.
        limit:
            Maximum number of records to return (default 100).
        """
        clauses: list[str] = []
        params: list[Any] = []

        # Build WHERE clauses using only safe column names (injection guard)
        for col, val in [("contract", contract), ("alert_type", alert_type),
                         ("branch", branch), ("fp_flag", fp_flag)]:
            if val is not None:
                if col not in _VALID_COLUMNS:  # belt-and-suspenders
                    raise ValueError(f"Invalid column name: {col!r}")
                clauses.append(f"{col} = ?")
                params.append(val)

        if block_min is not None:
            clauses.append("block >= ?")
            params.append(block_min)
        if block_max is not None:
            clauses.append("block <= ?")
            params.append(block_max)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT raw_json FROM alerts {where} ORDER BY block DESC LIMIT ?"
        params.append(limit)

        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(sql, params).fetchall()
                return [json.loads(r[0]) for r in rows]
            finally:
                conn.close()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        alert_id   TEXT PRIMARY KEY,
                        ts         TEXT,
                        block      INTEGER,
                        contract   TEXT,
                        alert_type TEXT,
                        drift      REAL,
                        branch     TEXT,
                        fp_flag    INTEGER DEFAULT 0,
                        raw_json   TEXT
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_contract ON alerts(contract)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_block ON alerts(block)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON alerts(alert_type)")
                conn.commit()
            finally:
                conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _index(self, record: dict) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """INSERT OR IGNORE INTO alerts
                   (alert_id, ts, block, contract, alert_type, drift, branch, fp_flag, raw_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)""",
                (
                    record.get("alert_id"),
                    record.get("ts"),
                    record.get("block"),
                    record.get("contract"),
                    record.get("alert_type"),
                    record.get("drift"),
                    record.get("branch"),
                    json.dumps(record, separators=(",", ":")),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _to_dict(alert: Any) -> dict:
        if isinstance(alert, dict):
            return alert
        if hasattr(alert, "to_dict"):
            return alert.to_dict()
        try:
            return asdict(alert)
        except TypeError:
            raise TypeError(  # noqa: B904
                f"Cannot serialise alert of type {type(alert).__name__}. "
                "Pass a dict, a dataclass, or an object with .to_dict()."
            )

    @staticmethod
    def _validate_alert_id(alert_id: Any) -> None:
        if not alert_id:
            raise ValueError("alert_id must be a non-empty string.")
        if not isinstance(alert_id, str):
            raise ValueError(f"alert_id must be str, got {type(alert_id).__name__}.")
        if len(alert_id) > _MAX_ALERT_ID_LEN:
            raise ValueError(
                f"alert_id too long ({len(alert_id)} chars, max {_MAX_ALERT_ID_LEN})."
            )
        if not _SAFE_ID_RE.match(alert_id):
            raise ValueError(
                f"alert_id contains unsafe characters: {alert_id!r}. "
                "Only A-Z, a-z, 0-9, '_', '-' are allowed."
            )
