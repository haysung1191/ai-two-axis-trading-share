from __future__ import annotations

import json
from pathlib import Path

from scripts.publish_btc_1d_operating_snapshot import publish_operating_snapshot


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_publish_btc_1d_operating_snapshot_writes_current_docs(tmp_path: Path) -> None:
    analysis = tmp_path / "analysis"
    analysis.mkdir()

    _write(
        analysis / "btc_1d_shadow_packet_20260414T000100Z.json",
        {
            "candidate": "low_vol_cap_050_025_minvol020_p2200",
            "status": "carryable_candidate",
            "carry_reference_period": 2200,
            "survivability_reference_period": 2600,
            "paper_validation_decision": "PASS",
            "paper_validation_metrics": {"sharpe": 1.16, "cagr": 0.14, "max_drawdown": 0.10, "win_rate": 0.51},
            "survivability_validation_decision": "PASS",
            "survivability_validation_metrics": {"sharpe": 1.15, "cagr": 0.15, "max_drawdown": 0.13, "win_rate": 0.52},
            "friction_validation_decision": "continue",
            "friction_validation_reason": "ok",
            "friction_validation_heaviest_level": {"cost_bps": 20.0, "sharpe": 1.04, "cagr": 0.12, "max_drawdown": 0.12},
            "walk_forward": {
                "passed": True,
                "oos_metrics": {"sharpe": 0.82, "cagr": 0.11, "max_drawdown": 0.10},
                "sensitivity_max_drift": 0.09,
                "unstable_parameters": [],
            },
            "parameters": {
                "low_volatility_cap_threshold": 0.5,
                "low_volatility_position_cap": 0.25,
                "min_annualized_volatility": 0.2,
            },
        },
    )
    _write(
        analysis / "btc_1d_shadow_readiness_20260414T000090Z.json",
        {
            "decision": "shadow_ready_for_btc_only",
            "why": {
                "btc": {"pass_rate": 0.5},
                "eth": {"pass_rate": 0.0},
            },
        },
    )
    _write(
        analysis / "btc_1d_low_vol_cap_friction_20260414T000110Z.json",
        {
            "final_decision": "continue",
            "levels": [
                {"cost_bps": 0.0},
                {"cost_bps": 20.0, "sharpe": 1.04, "cagr": 0.12, "max_drawdown": 0.12},
            ],
        },
    )
    _write(
        analysis / "btc_1d_promoted_candidate_regression_20260414T000120Z.json",
        {
            "config": {"symbol": "ETHUSDT"},
            "summary": {"pass_rate": 0.0},
            "results": [
                {"periods": 2200, "sharpe": 0.85, "max_drawdown": 0.30},
                {"periods": 2600, "sharpe": 0.86, "max_drawdown": 0.31},
            ],
        },
    )

    result = publish_operating_snapshot(analysis_dir=analysis)

    status_payload = json.loads(Path(result["status_json"]).read_text(encoding="utf-8"))
    readiness_payload = json.loads(Path(result["readiness_json"]).read_text(encoding="utf-8"))

    assert status_payload["candidate"] == "low_vol_cap_050_025_minvol020_p2200"
    assert status_payload["friction_check"]["decision"] == "continue"
    assert status_payload["walk_forward_check"]["oos_metrics"]["sharpe"] == 0.82
    assert readiness_payload["why"]["eth"]["pass_rate"] == 0.0
    assert readiness_payload["why"]["walk_forward"]["passed"] is True
