from __future__ import annotations

from scripts.compare_btc_1d_trend_dip_family_handoff import build_report


def test_trend_dip_family_handoff_marks_family_exhausted() -> None:
    report = build_report()

    assert report["family"]["label"] == "trend_dip_reversal_breakout"
    assert report["family"]["status"] == "exhausted_for_now"
    assert report["exhaustion_verdict"]["verdict"] == "pause_family"


def test_trend_dip_family_handoff_captures_key_repair_tradeoff() -> None:
    report = build_report()

    stage1 = report["stage1_summary"]["best_stage1_candidate"]
    repair = report["repair_summary"]
    validations = report["candidate_validation_summary"]

    assert stage1["variant_label"] == "volume_lookback_16_seeded"
    assert repair["best_cagr_repair"]["variant_label"] == "longer_stop_ema"
    assert repair["best_sensitivity_repair"]["variant_label"] == "faster88_hold28"
    assert repair["final_exit_repair_attempt"]["variant_label"] == "faster88_anchor"
    assert validations["all_failed"] is True
    assert "overfitting_sensitivity" in validations["shared_failed_gates"]
