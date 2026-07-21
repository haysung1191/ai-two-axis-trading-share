from __future__ import annotations

import scripts.compare_btc_1d_post_spike_exact_hit_backup_replacement_review as mod


def test_exact_hit_backup_replacement_review_marks_bridge_as_new_backup(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "build_attack_stack_screen",
        lambda: {
            "compared_models": [
                {
                    "label": "ratio112_tighter_stop_main",
                    "base_cagr": 0.42427487,
                    "base_mdd": 0.16094425,
                    "base_sharpe": 1.56134975,
                    "sensitivity_max_drift": 0.42935022,
                    "cost20_cagr": 0.40362936,
                },
                {
                    "label": "bridge_28_relief",
                    "base_cagr": 0.34639312,
                    "base_mdd": 0.09526207,
                    "base_sharpe": 1.81320199,
                    "sensitivity_max_drift": 0.13222176,
                    "cost20_cagr": 0.34639312,
                    "cost20_mdd": 0.09526207,
                    "cost20_sharpe": 1.81320199,
                },
                {
                    "label": "post_spike_trend960_depth055_volume100_hold36",
                    "base_cagr": 0.341816,
                    "base_mdd": 0.10024497,
                    "base_sharpe": 1.76013984,
                    "sensitivity_max_drift": 0.203704,
                    "cost20_cagr": 0.341816,
                },
            ]
        },
    )
    monkeypatch.setattr(
        mod,
        "build_frontier_bridge_review",
        lambda: {
            "frontier_bridge_verdict": {
                "frontier_bridge_found_backup_replacement": True,
            }
        },
    )

    report = mod.build_report()

    assert report["backup_replacement_verdict"]["backup_replacement_ready"] is True
    assert report["backup_replacement_verdict"]["attack_backup_replaced"] is True
    assert report["replacement_reference"]["new_attack_backup"] == "bridge_28_relief"
