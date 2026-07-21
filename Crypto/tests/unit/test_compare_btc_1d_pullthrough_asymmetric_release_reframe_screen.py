from __future__ import annotations

from scripts.compare_btc_1d_pullthrough_asymmetric_release_reframe_screen import build_report_from_batch


def test_pullthrough_asymmetric_release_reframe_screen_promotes_candidate_stage_seed() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["a", "b"],
        "results": [
            {
                "variant_label": "clean_progress",
                "strategy_name": "a",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.18,
                "max_drawdown": 0.12,
                "sharpe": 1.01,
                "trades": 18,
                "completed_trades": 9,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.18,
            },
            {
                "variant_label": "candidate_stage_seed",
                "strategy_name": "b",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.22,
                "max_drawdown": 0.14,
                "sharpe": 1.08,
                "trades": 20,
                "completed_trades": 10,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.14,
            },
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "candidate_stage_seed"
    assert report["reframe_verdict"]["has_candidate_stage_seed"] is True
    assert report["reframe_verdict"]["next_step"] == "candidate_stage_followup"


def test_pullthrough_asymmetric_release_reframe_screen_prefers_clean_stage2_variant() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["a", "b"],
        "results": [
            {
                "variant_label": "flagged_higher_cagr",
                "strategy_name": "a",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "DROP",
                "cagr": 0.24,
                "max_drawdown": 0.11,
                "sharpe": 1.12,
                "trades": 22,
                "completed_trades": 11,
                "overfitting_flags": ["unstable_parameters"],
                "sensitivity_max_drift": 0.30,
            },
            {
                "variant_label": "clean_progress",
                "strategy_name": "b",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.17,
                "max_drawdown": 0.12,
                "sharpe": 1.05,
                "trades": 18,
                "completed_trades": 9,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.19,
            },
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "clean_progress"
    assert report["reframe_verdict"]["has_candidate_stage_seed"] is False
