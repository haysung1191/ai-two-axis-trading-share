from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts import run_btc_1d_fresh_seed_active_step as step_mod


def _queue() -> list[dict]:
    return [
        {
            "family": "post_spike_consolidation_breakout",
            "seed_variant": "slower_trend",
            "phase": "seed_reopen",
            "step": "reopen_batch",
            "runner": "python scripts/run_btc_1d_post_spike_consolidation_breakout_high_cagr_batch.py --analysis-dir analysis_results --periods 2200",
            "status": "run_now",
        },
        {
            "family": "post_spike_consolidation_breakout",
            "seed_variant": "slower_trend",
            "phase": "candidate_validation",
            "step": "candidate_validation",
            "runner": "python scripts/validate_btc_1d_post_spike_consolidation_breakout_candidate.py --periods 2200",
            "status": "after_reopen_batch",
        },
    ]


def test_load_state_resets_stale_completed_queue(tmp_path: Path, monkeypatch) -> None:
    queue = _queue()
    signature = step_mod._queue_signature(queue)
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "queue_signature": signature,
                "completed_step_keys": signature,
                "failed_step_keys": [],
                "updated_at": (
                    datetime.now(tz=UTC) - timedelta(hours=step_mod.STALE_STATE_RESET_HOURS + 1)
                ).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(step_mod, "STATE_PATH", state_path)

    state = step_mod._load_state(queue)

    assert state["completed_step_keys"] == []
    assert state["failed_step_keys"] == []
    assert state["reset_reason"] == f"stale_completed_state_older_than_{step_mod.STALE_STATE_RESET_HOURS}h"
    assert state["previous_completed_count"] == len(signature)


def test_load_state_keeps_recent_completed_queue(tmp_path: Path, monkeypatch) -> None:
    queue = _queue()
    signature = step_mod._queue_signature(queue)
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "queue_signature": signature,
                "completed_step_keys": signature,
                "failed_step_keys": [],
                "updated_at": datetime.now(tz=UTC).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(step_mod, "STATE_PATH", state_path)

    state = step_mod._load_state(queue)

    assert state["completed_step_keys"] == signature
    assert "reset_reason" not in state


def test_select_active_step_skips_standby_secondary_when_primary_done(tmp_path: Path, monkeypatch) -> None:
    queue = _queue() + [
        {
            "family": "impulse_flag_breakout",
            "seed_variant": "slower_trend",
            "phase": "seed_reopen",
            "step": "reopen_batch",
            "runner": "python scripts/run_btc_1d_impulse_flag_breakout_high_cagr_batch.py --analysis-dir analysis_results --periods 2200",
            "status": "standby",
        }
    ]
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "queue_signature": step_mod._queue_signature(queue),
                "completed_step_keys": step_mod._queue_signature(queue[:2]),
                "failed_step_keys": [],
                "updated_at": datetime.now(tz=UTC).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(step_mod, "STATE_PATH", state_path)

    selected = step_mod._select_active_step(
        {
            "execution_queue": queue,
            "seed_snapshot": {
                "primary": {"attack_conversion_label": "defensive_hold_only"},
            },
        }
    )

    assert selected is None


def test_select_active_step_promotes_standby_after_single_step_primary(tmp_path: Path, monkeypatch) -> None:
    queue = [
        {
            "family": "impulse_flag_breakout",
            "seed_variant": "slower_trend",
            "priority_rank": 1,
            "phase": "seed_reopen",
            "step": "reopen_batch",
            "runner": "python scripts/run_btc_1d_impulse_flag_breakout_high_cagr_batch.py --analysis-dir analysis_results --periods 2200",
            "status": "run_now",
        },
        {
            "family": "narrow_range_expansion_drift",
            "seed_variant": "reference",
            "priority_rank": 2,
            "phase": "seed_reopen",
            "step": "reopen_batch",
            "runner": "python scripts/run_btc_1d_narrow_range_expansion_drift_high_cagr_batch.py --analysis-dir analysis_results --periods 2200",
            "status": "standby",
        },
    ]
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "queue_signature": step_mod._queue_signature(queue),
                "completed_step_keys": [step_mod._step_key(queue[0])],
                "failed_step_keys": [],
                "updated_at": datetime.now(tz=UTC).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(step_mod, "STATE_PATH", state_path)

    selected = step_mod._select_active_step(
        {
            "execution_queue": queue,
            "seed_snapshot": {
                "primary": {"attack_conversion_label": "kill_for_attack_conversion"},
            },
        }
    )

    assert selected is not None
    assert selected["family"] == "narrow_range_expansion_drift"
    assert selected["status"] == "promoted_from_standby_after_primary_seed_batch"
