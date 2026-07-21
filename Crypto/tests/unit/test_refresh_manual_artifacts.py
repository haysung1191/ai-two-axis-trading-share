from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from scripts.refresh_manual_artifacts import refresh_run_artifacts


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_refresh_run_artifacts_recovers_parameters_and_reexports_bundle(tmp_path: Path) -> None:
    run_id = "run-1"
    artifacts_dir = tmp_path / "artifacts"
    reexport_dir = tmp_path / "artifacts_reexport"
    backup_dir = tmp_path / "backups"

    _write_json(
        artifacts_dir / run_id / "approved_strategy.json",
        {
            "winners": [
                {
                    "strategy_id": "Bollinger Mean Reversion_approved",
                    "approved_at": "2026-03-08T02:04:35Z",
                    "source_run_id": run_id,
                    "symbol": "BTCUSDT",
                    "timeframe": "1h",
                    "parameters": {},
                    "metrics": {"sharpe": 1.2},
                    "risk_limits": {"position_size": 0.1},
                }
            ],
            "top_k": 1,
        },
    )
    _write_json(
        artifacts_dir / run_id / "evaluation_scorecards.json",
        [
            {
                "run_id": run_id,
                "strategy": {
                    "name": "Bollinger Mean Reversion",
                    "strategy_id": "Bollinger Mean Reversion_approved",
                    "source_type": "new",
                    "parent_strategy": None,
                    "category": "mean_reversion",
                },
                "single_asset": {
                    "symbol": "BTCUSDT",
                    "trades": 10,
                    "sharpe": 1.2,
                    "max_drawdown": 0.1,
                    "win_rate": 0.55,
                    "cagr": 0.08,
                    "equity_curve_summary": {},
                    "equity_curve": [],
                },
                "multi_asset": {
                    "sharpe_mean": 1.2,
                    "sharpe_std": 0.1,
                    "drawdown_mean": 0.1,
                    "drawdown_worst": 0.1,
                },
                "regime": {
                    "sharpe_by_regime": {},
                    "drawdown_by_regime": {},
                    "sharpe_regime_std": 0.1,
                },
                "overfitting": {
                    "is_metrics": {},
                    "oos_metrics": {},
                    "walk_forward": [],
                    "sensitivity_drift": 0.0,
                    "unstable_parameters": [],
                    "flags": [],
                },
                "qa_passed": True,
                "applied_rules": [],
                "violations": [],
                "passed_gates": ["qa", "risk_policy"],
                "failed_gates": [],
                "candidate_pass": True,
                "metadata": {
                    "symbols_tested": ["BTCUSDT"],
                    "deterministic_seed": 42,
                    "strategy_parameters": {"period": 30.0, "std_dev": 2.25},
                },
            }
        ],
    )
    _write_json(
        reexport_dir / run_id / "publish" / "policy_bundle.json",
        {
            "bundle_id": "old_policy",
            "bundle_mode": "shadow",
            "strategies": [
                {
                    "strategy_id": "Bollinger Mean Reversion_approved",
                    "valid_until": "2026-03-10T00:00:00Z",
                }
            ],
        },
    )
    _write_json(reexport_dir / run_id / "publish" / "manifest.json", {"bundle_id": "old_policy"})

    result = refresh_run_artifacts(
        run_id=run_id,
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        backup_root=backup_dir,
    )

    refreshed_approved = json.loads((artifacts_dir / run_id / "approved_strategy.json").read_text(encoding="utf-8"))
    assert refreshed_approved["winners"][0]["parameters"] == {"period": 30.0, "std_dev": 2.25}
    refreshed_approved_at = datetime.fromisoformat(refreshed_approved["winners"][0]["approved_at"].replace("Z", "+00:00"))
    assert refreshed_approved_at > datetime(2026, 3, 8, tzinfo=UTC)
    refreshed_bundle = json.loads((reexport_dir / run_id / "publish" / "policy_bundle.json").read_text(encoding="utf-8"))
    assert refreshed_bundle["bundle_id"] == result["bundle_id"]
    assert refreshed_bundle["strategies"][0]["parameters"]["policy_params"] == {"period": 30.0, "std_dev": 2.25}
    refreshed_valid_until = datetime.fromisoformat(refreshed_bundle["strategies"][0]["valid_until"].replace("Z", "+00:00"))
    assert refreshed_valid_until > refreshed_approved_at
    assert Path(result["backup_dir"]).exists()
    assert result["recovered_parameters"] == 1
