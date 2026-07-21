from __future__ import annotations

from scripts.compare_btc_1d_shallow_liquidity_void_refill_repair_screen import build_report_from_batch


def test_void_refill_repair_screen_prefers_cleaner_overfit_profile() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["a", "b"],
        "results": [
            {
                "variant_label": "higher_cagr_but_unstable",
                "strategy_name": "a",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "DROP",
                "cagr": 0.31,
                "max_drawdown": 0.17,
                "sharpe": 1.2,
                "overfitting_flags": ["sensitivity_drift_exceeded"],
                "sensitivity_max_drift": 0.22,
                "unstable_parameters": ["atr_window"],
            },
            {
                "variant_label": "cleaner_repair_seed",
                "strategy_name": "b",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.24,
                "max_drawdown": 0.17,
                "sharpe": 1.1,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.12,
                "unstable_parameters": [],
            },
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "cleaner_repair_seed"
    assert report["repair_screen_verdict"]["has_candidate_repair_seed"] is True
    assert report["repair_screen_verdict"]["next_step"] == "friction_retest"


def test_void_refill_repair_screen_continues_search_when_flags_remain() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["a"],
        "results": [
            {
                "variant_label": "still_unstable",
                "strategy_name": "a",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "DROP",
                "cagr": 0.24,
                "max_drawdown": 0.17,
                "sharpe": 1.05,
                "overfitting_flags": ["unstable_parameters"],
                "sensitivity_max_drift": 0.21,
                "unstable_parameters": ["min_volume_ratio"],
            }
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "still_unstable"
    assert report["repair_screen_verdict"]["has_candidate_repair_seed"] is False
    assert report["repair_screen_verdict"]["next_step"] == "continue_candidate_repair_search"


def test_void_refill_repair_screen_does_not_promote_stage1_only_variant() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["b"],
        "results": [
            {
                "variant_label": "stage1_only_clean",
                "strategy_name": "a",
                "stage": "stage1",
                "stage1_passed": False,
                "decision": "KEEP",
                "cagr": 0.23,
                "max_drawdown": 0.17,
                "sharpe": 1.04,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.0,
                "unstable_parameters": [],
            },
            {
                "variant_label": "stage2_checked_but_unstable",
                "strategy_name": "b",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "DROP",
                "cagr": 0.24,
                "max_drawdown": 0.17,
                "sharpe": 1.05,
                "overfitting_flags": ["sensitivity_drift_exceeded"],
                "sensitivity_max_drift": 0.24,
                "unstable_parameters": ["atr_window"],
            },
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "stage2_checked_but_unstable"
    assert report["repair_screen_verdict"]["has_candidate_repair_seed"] is False
