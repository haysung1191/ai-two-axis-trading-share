from __future__ import annotations

from scripts.compare_btc_1d_shallow_liquidity_void_refill_refinement_screen import build_report_from_batch


def test_void_refill_refinement_screen_prefers_friction_ready_seed() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["a", "b"],
        "results": [
            {
                "variant_label": "still_too_sensitive",
                "strategy_name": "a",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "DROP",
                "cagr": 0.25,
                "max_drawdown": 0.17,
                "sharpe": 1.12,
                "overfitting_flags": ["sensitivity_drift_exceeded"],
                "sensitivity_max_drift": 0.21,
                "unstable_parameters": ["refill_window"],
            },
            {
                "variant_label": "compressed_seed",
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

    assert report["best_variant"]["variant_label"] == "compressed_seed"
    assert report["refinement_verdict"]["has_friction_ready_seed"] is True
    assert report["refinement_verdict"]["next_step"] == "friction_retest"


def test_void_refill_refinement_screen_keeps_search_open_when_drift_remains_high() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["a"],
        "results": [
            {
                "variant_label": "close_but_not_enough",
                "strategy_name": "a",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.22,
                "max_drawdown": 0.18,
                "sharpe": 1.03,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.20,
                "unstable_parameters": [],
            }
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "close_but_not_enough"
    assert report["refinement_verdict"]["has_friction_ready_seed"] is False
    assert report["refinement_verdict"]["next_step"] == "continue_candidate_repair_search"
