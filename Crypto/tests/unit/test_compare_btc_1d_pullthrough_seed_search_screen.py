from __future__ import annotations

from scripts.compare_btc_1d_pullthrough_seed_search_screen import build_report_from_batch


def test_pullthrough_seed_search_screen_prefers_cleaner_overfit_profile() -> None:
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
                "max_drawdown": 0.18,
                "sharpe": 1.2,
                "overfitting_flags": ["sensitivity_drift_exceeded"],
                "sensitivity_max_drift": 0.22,
                "unstable_parameters": ["x"],
            },
            {
                "variant_label": "cleaner_seed",
                "strategy_name": "b",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.24,
                "max_drawdown": 0.17,
                "sharpe": 1.1,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.08,
                "unstable_parameters": [],
            },
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "cleaner_seed"
    assert report["seed_search_verdict"]["has_promising_seed"] is True
    assert report["seed_search_verdict"]["next_step"] == "candidate_stage_validation"


def test_pullthrough_seed_search_screen_continues_search_when_flags_remain() -> None:
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
                "cagr": 0.26,
                "max_drawdown": 0.18,
                "sharpe": 1.05,
                "overfitting_flags": ["unstable_parameters"],
                "sensitivity_max_drift": 0.19,
                "unstable_parameters": ["y"],
            }
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "still_unstable"
    assert report["seed_search_verdict"]["has_promising_seed"] is False
    assert report["seed_search_verdict"]["next_step"] == "continue_new_family_search"


def test_pullthrough_seed_search_screen_does_not_prefer_stage1_only_variant() -> None:
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
                "cagr": 0.30,
                "max_drawdown": 0.12,
                "sharpe": 1.3,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.0,
                "unstable_parameters": [],
            },
            {
                "variant_label": "stage2_checked_candidate",
                "strategy_name": "b",
                "stage": "stage2",
                "stage1_passed": True,
                "decision": "KEEP",
                "cagr": 0.22,
                "max_drawdown": 0.16,
                "sharpe": 1.05,
                "overfitting_flags": [],
                "sensitivity_max_drift": 0.14,
                "unstable_parameters": [],
            },
        ],
    }

    report = build_report_from_batch(batch)

    assert report["best_variant"]["variant_label"] == "stage2_checked_candidate"
    assert report["seed_search_verdict"]["has_promising_seed"] is True
    assert report["seed_search_verdict"]["next_step"] == "candidate_stage_validation"
