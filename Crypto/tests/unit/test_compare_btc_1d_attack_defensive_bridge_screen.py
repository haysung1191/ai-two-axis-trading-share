from __future__ import annotations

from scripts.compare_btc_1d_attack_defensive_bridge_screen import build_report


def test_compare_btc_1d_attack_defensive_bridge_screen_keeps_attack_anchor() -> None:
    report = build_report()
    assert report["stack_top"]["attack_anchor"] == "ratio112_tighter_stop_main"
    assert report["bridge_verdict"]["preferred_attack_model"] == "ratio112_tighter_stop_main"
    assert report["bridge_verdict"]["roles_are_distinct"] is True


def test_compare_btc_1d_attack_defensive_bridge_screen_names_pullthrough_defensive_hold() -> None:
    report = build_report()
    assert report["stack_top"]["defensive_hold"] == "volatility_expansion_pullthrough_shorter_hold"
    defensive = next(item for item in report["compared_models"] if item["label"] == "volatility_expansion_pullthrough_shorter_hold")
    assert defensive["role"] == "defensive_research_hold"
