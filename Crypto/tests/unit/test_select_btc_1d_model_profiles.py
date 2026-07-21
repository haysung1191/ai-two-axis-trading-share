from __future__ import annotations

import json
from pathlib import Path

from scripts.select_btc_1d_model_profiles import build_model_profile_selection, write_outputs


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_model_profile_selection_picks_attack_and_operating_leaders(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_practical_scorecard_latest.json",
        {
            "candidate": "practical_low_vol",
            "summary": {
                "carry_metrics": {"cagr": 0.31, "max_drawdown": 0.12, "sharpe": 1.21},
                "friction_20bps_metrics": {"cagr": 0.28, "max_drawdown": 0.13, "sharpe": 1.12},
            },
            "walk_forward_check": {
                "sensitivity_max_drift": 0.08,
                "oos_metrics": {"cagr": 0.05, "max_drawdown": 0.05, "sharpe": 0.80},
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "models": {
                "attack_main": {
                    "label": "attack_frontier",
                    "base_cagr": 0.42,
                    "base_mdd": 0.16,
                    "base_sharpe": 1.56,
                    "oos_cagr": 0.09,
                    "oos_mdd": 0.12,
                    "oos_sharpe": 0.64,
                    "sensitivity_max_drift": 0.42,
                    "cost20_cagr": 0.40,
                    "cost20_mdd": 0.16,
                    "cost20_sharpe": 1.49,
                },
                "attack_backup": {
                    "label": "attack_backup",
                    "base_cagr": 0.39,
                    "base_mdd": 0.16,
                    "base_sharpe": 1.50,
                    "oos_cagr": 0.07,
                    "oos_mdd": 0.15,
                    "oos_sharpe": 0.50,
                    "sensitivity_max_drift": 0.41,
                    "cost20_cagr": 0.37,
                    "cost20_mdd": 0.17,
                    "cost20_sharpe": 1.46,
                },
                "defensive_hold": {
                    "label": "defensive_hold",
                    "base_cagr": 0.24,
                    "base_mdd": 0.18,
                    "base_sharpe": 1.10,
                    "oos_cagr": 0.05,
                    "oos_mdd": 0.14,
                    "oos_sharpe": 0.48,
                    "sensitivity_max_drift": 0.36,
                    "cost20_cagr": 0.23,
                    "cost20_mdd": 0.18,
                    "cost20_sharpe": 1.02,
                },
            }
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "attack_challenger_candidate": "attack_challenger",
            "attack_challenger_paper_validation_cagr": 0.27,
            "attack_challenger_paper_validation_max_drawdown": 0.16,
            "attack_challenger_walk_forward_sensitivity_max_drift": 0.09,
        },
    )

    payload = build_model_profile_selection(analysis_dir=analysis_dir)

    assert payload["attack_model"]["label"] == "attack_frontier"
    assert payload["operating_model"]["label"] == "practical_low_vol"
    assert payload["objective_map"]["attack"] == "maximize_cagr"
    assert payload["objective_map"]["operating"] == "minimize_mdd"


def test_write_outputs_creates_latest_aliases(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    payload = {
        "attack_model": {"label": "attack_frontier", "cagr": 0.42, "mdd": 0.16, "sharpe": 1.56, "drift": 0.42, "selection_reason": "x"},
        "operating_model": {"label": "practical_low_vol", "cagr": 0.31, "mdd": 0.12, "sharpe": 1.21, "drift": 0.08, "selection_reason": "y"},
    }

    artifacts = write_outputs(payload, output_dir=analysis_dir)

    assert Path(artifacts["json"]).exists()
    assert Path(artifacts["txt"]).exists()
    assert Path(artifacts["latest_json"]).exists()
    assert Path(artifacts["latest_txt"]).exists()
