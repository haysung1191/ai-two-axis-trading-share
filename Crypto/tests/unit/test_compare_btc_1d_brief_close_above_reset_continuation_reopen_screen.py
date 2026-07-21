from __future__ import annotations

from scripts.compare_btc_1d_brief_close_above_reset_continuation_reopen_screen import build_report_from_batch


def test_brief_close_above_reset_continuation_reopen_screen_promotes_candidate_stage_seed() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["a", "b"],
        "results": [
            {
                "variant_label": "not_quite",
                "strategy_name": "a",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.18,
                "max_drawdown": 0.09,
                "sharpe": 1.02,
                "trades": 9,
                "completed_trades": 5,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.10,
            },
            {
                "variant_label": "candidate_stage_seed",
                "strategy_name": "b",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.24,
                "max_drawdown": 0.11,
                "sharpe": 1.10,
                "trades": 12,
                "completed_trades": 6,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.12,
            },
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "candidate_stage_seed"
    assert report["reopen_verdict"]["has_candidate_stage_seed"] is True
    assert report["reopen_verdict"]["next_step"] == "candidate_stage_followup"


def test_brief_close_above_reset_continuation_reopen_screen_prefers_clean_stage2_progress_variant() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["a", "b"],
        "results": [
            {
                "variant_label": "lower_mdd_but_flagged",
                "strategy_name": "a",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "DROP",
                "cagr": 0.10,
                "max_drawdown": 0.07,
                "sharpe": 1.01,
                "trades": 14,
                "completed_trades": 7,
                "overfitting_flags": ["sensitivity_drift_exceeded"],
                "sensitivity_max_drift": 0.38,
            },
            {
                "variant_label": "clean_progress",
                "strategy_name": "b",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.12,
                "max_drawdown": 0.12,
                "sharpe": 1.04,
                "trades": 20,
                "completed_trades": 10,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.23,
            },
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "clean_progress"
    assert report["reopen_verdict"]["has_candidate_stage_seed"] is False
