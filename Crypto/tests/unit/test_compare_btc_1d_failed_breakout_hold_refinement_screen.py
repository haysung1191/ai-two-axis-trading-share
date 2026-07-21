from __future__ import annotations

from scripts.compare_btc_1d_failed_breakout_hold_refinement_screen import build_report_from_batch


def test_failed_breakout_hold_refinement_screen_promotes_candidate_stage_seed() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["a", "b"],
        "results": [
            {
                "variant_label": "close_but_not_enough",
                "strategy_name": "a",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.19,
                "max_drawdown": 0.10,
                "sharpe": 1.03,
                "trades": 14,
                "completed_trades": 7,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.12,
            },
            {
                "variant_label": "candidate_push",
                "strategy_name": "b",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.22,
                "max_drawdown": 0.13,
                "sharpe": 1.11,
                "trades": 16,
                "completed_trades": 8,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.10,
            },
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "candidate_push"
    assert report["hold_refinement_verdict"]["promoted_to_candidate_stage"] is True
    assert report["hold_refinement_verdict"]["next_step"] == "candidate_stage_followup"


def test_failed_breakout_hold_refinement_screen_prefers_clean_stage2_progress_variant() -> None:
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
                "cagr": 0.21,
                "max_drawdown": 0.09,
                "sharpe": 1.07,
                "trades": 16,
                "completed_trades": 8,
                "overfitting_flags": ["unstable_parameters"],
                "sensitivity_max_drift": 0.35,
            },
            {
                "variant_label": "clean_progress",
                "strategy_name": "b",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.18,
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
    assert report["hold_refinement_verdict"]["promoted_to_candidate_stage"] is False
