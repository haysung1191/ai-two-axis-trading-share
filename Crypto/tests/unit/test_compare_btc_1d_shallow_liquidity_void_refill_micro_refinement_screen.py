from __future__ import annotations

from scripts.compare_btc_1d_shallow_liquidity_void_refill_micro_refinement_screen import build_report_from_batch


def test_void_refill_micro_refinement_screen_promotes_ready_seed() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["a", "b"],
        "results": [
            {
                "variant_label": "still_too_sensitive",
                "strategy_name": "a",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.24,
                "max_drawdown": 0.17,
                "sharpe": 1.08,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.20,
                "unstable_parameters": [],
            },
            {
                "variant_label": "friction_ready_seed",
                "strategy_name": "b",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.23,
                "max_drawdown": 0.17,
                "sharpe": 1.06,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.16,
                "unstable_parameters": [],
            },
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "friction_ready_seed"
    assert report["micro_refinement_verdict"]["has_friction_ready_seed"] is True
    assert report["micro_refinement_verdict"]["next_step"] == "friction_retest"


def test_void_refill_micro_refinement_screen_flags_lane_exhaustion_when_drift_remains() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["a"],
        "results": [
            {
                "variant_label": "best_available_but_not_enough",
                "strategy_name": "a",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.23,
                "max_drawdown": 0.19,
                "sharpe": 1.05,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.24,
                "unstable_parameters": [],
            }
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "best_available_but_not_enough"
    assert report["micro_refinement_verdict"]["has_friction_ready_seed"] is False
    assert report["micro_refinement_verdict"]["next_step"] == "lane_exhausted_or_new_family_search"
