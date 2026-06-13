"""T-10: Detection scorer — delay and false-positive metrics.

Measures detection quality:
- detection_delay: how quickly alerts fire after injection starts
- false_positive_rate: how many spurious alert episodes occur on clean data
"""
from __future__ import annotations

from sentinel.alert import Alert

# Mantle block time ≈ 2 seconds; 1 window = WINDOW txs ≈ 2 blocks ≈ 4 seconds.
_BLOCKS_PER_WINDOW = 2
_SECONDS_PER_BLOCK = 2.0
_SECONDS_PER_DAY = 86_400.0
_SECONDS_PER_WINDOW = _BLOCKS_PER_WINDOW * _SECONDS_PER_BLOCK  # ≈ 4 seconds


def detection_delay(alerts: list[Alert], inject_start_block: int) -> dict:
    """Measure how quickly alerts fire relative to injection start.

    Args:
        alerts: list of Alert objects from the pipeline run
        inject_start_block: the block number where injection started

    Returns:
        {
            "delay_blocks_median": float,
            "delay_blocks_p90": float,
            "missed": int  # 1 if no alert within 10 windows of inject_start, else 0
        }
    """
    import numpy as np

    # Filter alerts that fire after injection starts
    post_inject = [a for a in alerts if a.block >= inject_start_block]

    # Check if any alert fires within 10 windows (= 20 blocks) of inject_start
    window_10_block_limit = inject_start_block + 10 * _BLOCKS_PER_WINDOW
    alerts_within_10 = [a for a in post_inject if a.block <= window_10_block_limit]

    if not alerts_within_10:
        return {
            "delay_blocks_median": float("inf"),
            "delay_blocks_p90": float("inf"),
            "missed": 1,
        }

    delays = [float(a.block - inject_start_block) for a in post_inject if a.block >= inject_start_block]
    if not delays:
        return {
            "delay_blocks_median": float("inf"),
            "delay_blocks_p90": float("inf"),
            "missed": 1,
        }

    delays_arr = np.array(delays)
    return {
        "delay_blocks_median": float(np.median(delays_arr)),
        "delay_blocks_p90": float(np.quantile(delays_arr, 0.9)),
        "missed": 0,
    }


def false_positive_rate(alerts_clean: list[Alert], n_windows_clean: int) -> dict:
    """Measure false-positive rate on clean (no injection) data.

    Args:
        alerts_clean: alerts from a clean replay (no injection)
        n_windows_clean: total number of windows in the clean replay

    Returns:
        {"fp_episodes_per_day": float}
        Assuming 1 window ≈ 2 blocks ≈ 4 seconds on Mantle.
    """
    # Count unique episodes (episode collapsing already done by the detector)
    episode_ids = {a.episode_id for a in alerts_clean if a.episode_id is not None}
    n_fp_episodes = len(episode_ids)

    total_seconds = n_windows_clean * _SECONDS_PER_WINDOW
    if total_seconds <= 0:
        return {"fp_episodes_per_day": 0.0}

    days = total_seconds / _SECONDS_PER_DAY
    fp_per_day = n_fp_episodes / days if days > 0 else 0.0

    return {"fp_episodes_per_day": round(fp_per_day, 4)}
