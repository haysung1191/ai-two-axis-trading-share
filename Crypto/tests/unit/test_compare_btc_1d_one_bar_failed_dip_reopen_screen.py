from __future__ import annotations

from scripts.compare_btc_1d_one_bar_failed_dip_reopen_screen import build_report_from_batch


def test_one_bar_failed_dip_reopen_screen_promotes_candidate_stage_seed() -> None:
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
                "max_drawdown": 0.10,
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
                "cagr": 0.22,
                "max_drawdown": 0.12,
                "sharpe": 1.08,
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


def test_one_bar_failed_dip_reopen_screen_keeps_search_open_when_bar_not_cleared() -> None:
    batch = {
        "run_id": "demo",
        "stage1_survivors": ["a"],
        "results": [
            {
                "variant_label": "still_low_alpha",
                "strategy_name": "a",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.17,
                "max_drawdown": 0.10,
                "sharpe": 1.04,
                "trades": 10,
                "completed_trades": 5,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.08,
            }
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "still_low_alpha"
    assert report["reopen_verdict"]["has_candidate_stage_seed"] is False
    assert report["reopen_verdict"]["next_step"] == "continue_broad_family_search"
