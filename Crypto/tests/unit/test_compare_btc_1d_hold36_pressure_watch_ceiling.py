from __future__ import annotations

from scripts.compare_btc_1d_hold36_pressure_watch_ceiling import build_report


def test_hold36_pressure_watch_ceiling_confirms_current_local_ceiling() -> None:
    report = build_report()
    ceiling = report["pressure_watch_ceiling"]

    assert report["ceiling_reference"]["active_backup"] == "post_spike_trend92_depth058_volume105_hold36"
    assert ceiling["status_band"] == "pressure_watch"
    assert ceiling["ceiling_confirmed"] is True
    assert ceiling["primary_blocker"] == "base_cagr_gap"
    assert ceiling["local_axis_count_closed"] >= 5


def test_hold36_pressure_watch_ceiling_keeps_base_gap_as_remaining_blocker() -> None:
    report = build_report()
    ceiling = report["pressure_watch_ceiling"]
    metrics = report["ceiling_metrics"]

    assert ceiling["remaining_base_cagr_gap_to_open"] > 0.0
    assert ceiling["remaining_cost20_cagr_gap_to_open"] == 0.0
    assert metrics["base_cagr_gap_to_main"] > 0.04
    assert metrics["cost20_cagr_gap_to_main"] <= 0.06
