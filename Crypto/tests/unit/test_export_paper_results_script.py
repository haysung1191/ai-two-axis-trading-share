import csv
import json
from pathlib import Path

from scripts.export_paper_results import export_paper_results


def test_export_paper_results_writes_expected_csvs(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts"
    run_dir = artifacts_root / "run-1"
    candidate_dir = run_dir / "candidates" / "alpha"
    candidate_dir.mkdir(parents=True, exist_ok=True)

    (candidate_dir / "scorecard.json").write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "strategy": {
                    "name": "alpha",
                    "strategy_id": "alpha_approved",
                    "source_type": "mutation",
                    "parent_strategy": "alpha_v1_approved",
                    "category": "momentum",
                },
                "single_asset": {
                    "symbol": "BTCUSDT",
                    "trades": 12,
                    "sharpe": 1.2,
                    "max_drawdown": 0.1,
                    "win_rate": 0.6,
                    "cagr": 0.15,
                    "equity_curve_summary": {},
                },
                "multi_asset": {
                    "sharpe_mean": 1.1,
                    "sharpe_std": 0.2,
                    "drawdown_mean": 0.12,
                    "drawdown_worst": 0.18,
                },
                "regime": {
                    "sharpe_by_regime": {},
                    "drawdown_by_regime": {},
                    "sharpe_regime_std": 0.3,
                },
                "overfitting": {
                    "flags": ["unstable_parameters"],
                },
                "qa_passed": True,
                "failed_gates": ["overfitting_flags"],
                "candidate_pass": False,
            }
        ),
        encoding="utf-8",
    )

    (run_dir / "decision_record.json").write_text(
        json.dumps(
            {
                "decision": "FAIL",
                "iteration": 1,
                "reject_count": 1,
                "failed_gates": ["overfitting_flags"],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "run_leaderboard.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "strategy_name": "alpha",
                        "sharpe": 1.1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    registry_path = tmp_path / "strategy_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "strategies": [
                    {
                        "strategy_id": "alpha_approved",
                        "source_type": "mutation",
                        "parent_strategy": "alpha_v1_approved",
                        "first_seen_run": "run-1",
                        "latest_run": "run-1",
                        "best_sharpe": 1.1,
                        "best_cagr": 0.15,
                        "best_drawdown": 0.18,
                        "runs": [{"run_id": "run-1"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "paper_results"
    outputs = export_paper_results(artifacts_root=artifacts_root, output_dir=output_dir, registry_path=registry_path)

    assert outputs["candidate_metrics"].exists()
    assert outputs["decision_outcomes"].exists()
    assert outputs["rejection_reasons"].exists()
    assert outputs["lineage_stats"].exists()
    assert outputs["source_type_stats"].exists()
    assert outputs["category_stats"].exists()
    assert outputs["terminal_state_stats"].exists()
    assert outputs["lineage_edges"].exists()
    assert outputs["candidate_funnel"].exists()
    assert outputs["figure_summary"].exists()

    with outputs["candidate_metrics"].open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["strategy_name"] == "alpha"
    assert rows[0]["source_type"] == "mutation"

    with outputs["rejection_reasons"].open("r", encoding="utf-8", newline="") as handle:
        rejection_rows = list(csv.DictReader(handle))
    assert rejection_rows[0]["failed_gate"] == "overfitting_flags"

    with outputs["lineage_edges"].open("r", encoding="utf-8", newline="") as handle:
        lineage_rows = list(csv.DictReader(handle))
    assert lineage_rows[0]["parent_strategy"] == "alpha_v1_approved"
