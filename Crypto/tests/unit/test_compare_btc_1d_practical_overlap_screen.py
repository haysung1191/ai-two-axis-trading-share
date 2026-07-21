from __future__ import annotations

from scripts.compare_btc_1d_practical_overlap_screen import build_report


def test_compare_btc_1d_practical_overlap_screen_keeps_practical_main_as_anchor() -> None:
    report = build_report()
    assert report["practical_anchor"] == "lower_atr_window_tighter_stop"
    assert report["overlap_verdict"]["preferred_practical_model"] == "lower_atr_window_tighter_stop"
    assert report["overlap_verdict"]["is_practical_substitute"] is False


def test_compare_btc_1d_practical_overlap_screen_names_pullthrough_as_nearest_hold() -> None:
    report = build_report()
    assert report["nearest_research_hold"] == "volatility_expansion_pullthrough_shorter_hold"
    hold = next(item for item in report["compared_models"] if item["label"] == "volatility_expansion_pullthrough_shorter_hold")
    assert hold["status_label"] == "candidate_stage_hold"
