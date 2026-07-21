from __future__ import annotations

from scripts.compare_btc_1d_post_spike_reopen_seed_pressure_reconciliation import (
    build_report,
)


def test_reopen_seed_pressure_reconciliation_detects_framing_conflict() -> None:
    report = build_report()

    assert report["lane_alignment"]["same_seed_across_lanes"] is True
    assert report["lane_alignment"]["seed_cycle_passed"] is True
    assert report["lane_alignment"]["main_pressure_quality_passed"] is False
    assert report["lane_alignment"]["framing_conflict"] is True
    assert report["verdict"]["lane_status"] == "revalidation_hold"


def test_reopen_seed_pressure_reconciliation_records_metric_degradation() -> None:
    report = build_report()
    delta = report["lane_delta"]

    assert delta is not None
    assert delta["base_cagr_delta"] < 0.0
    assert delta["base_sharpe_delta"] < 0.0
    assert delta["base_max_drawdown_delta"] > 0.0
