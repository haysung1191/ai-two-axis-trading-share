from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_btc_1d_fresh_seed_priority_screen import build_report


def test_fresh_seed_priority_screen_selects_post_spike_as_primary() -> None:
    report = build_report()

    scope = report["fresh_seed_scope"]
    verdict = report["fresh_seed_verdict"]

    assert scope["queue_lane"] == "fresh_seed_search_required"
    assert "volatility_expansion_pullthrough" in scope["excluded_families"]
    assert "volatility_spike_reversal_continuation" in scope["excluded_families"]
    assert verdict["next_fresh_seed_family"] == "post_spike_consolidation_breakout"
    assert verdict["next_fresh_seed_variant"] == "slower_trend"


def test_fresh_seed_priority_screen_keeps_impulse_flag_as_secondary() -> None:
    report = build_report()

    rows = report["priority_rows"]
    verdict = report["fresh_seed_verdict"]

    assert rows[0]["priority_rank"] == 1
    assert rows[1]["priority_rank"] == 2
    assert rows[1]["family"] == "impulse_flag_breakout"
    assert verdict["secondary_fresh_seed_family"] == "impulse_flag_breakout"


def test_fresh_seed_priority_screen_skips_stage_ready_post_spike(tmp_path: Path) -> None:
    stage_review = tmp_path / "btc_1d_post_spike_consolidation_breakout_candidate_stage_review_latest.json"
    stage_review.write_text(
        json.dumps(
            {
                "post_spike_candidate_stage_review_verdict": {
                    "candidate_stage_ready": True,
                }
            }
        ),
        encoding="utf-8",
    )

    report = build_report(analysis_dir=tmp_path)

    scope = report["fresh_seed_scope"]
    verdict = report["fresh_seed_verdict"]

    assert "post_spike_consolidation_breakout" in scope["stage_ready_families_excluded"]
    assert verdict["next_fresh_seed_family"] == "impulse_flag_breakout"
