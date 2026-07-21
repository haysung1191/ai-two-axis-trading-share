from __future__ import annotations

import json
from pathlib import Path

from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
)
from scripts.check_btc_1d_practical_health import (
    build_parser,
    check_practical_health,
    render_practical_health_line,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_practical_health_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.analysis_dir == Path("analysis_results")
    assert args.as_json is False


def test_check_practical_health_reads_latest_gate_and_brief(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_practical_promotion_gate_latest.json",
        {
            "ok": True,
            "decision": "btc_only_practical_with_caveats",
            "status_label": "btc_only_practical_with_caveats",
            "candidate": "lower_atr_window_tighter_stop",
            "scope": "BTC-only",
            "carry_metrics": {"sharpe": 1.3946, "cagr": 0.3772, "max_drawdown": 0.1609},
            "caveats": ["dsr weak", "range weak"],
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "candidate": "lower_atr_window_tighter_stop",
            "scope": "BTC-only",
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
        },
    )

    result = check_practical_health(analysis_dir=analysis_dir)

    assert result["regression_lock_test"] == "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    assert result["standard_check_order_reference"] == ["practical", "research", "contract", "brief"]
    assert result["ok"] is True
    assert result["status_label"] == "btc_only_practical_with_caveats"
    assert result["caveat_count"] == 2
    assert result["sharpe"] == 1.3946
    assert result["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert (
        result["attack_challenger_next_step"]
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    )
    assert (
        result["attack_challenger_bridge_report"]
        == "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )


def test_render_practical_health_line_includes_core_fields() -> None:
    rendered = render_practical_health_line(
        {
            "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
            "ok": True,
            "status_label": "btc_only_practical_with_caveats",
            "candidate": "lower_atr_window_tighter_stop",
            "scope": "BTC-only",
            "caveat_count": 4,
            "caveats": [],
            "sharpe": 1.3946,
            "cagr": 0.3772,
            "max_drawdown": 0.1609,
        }
    )

    assert "BTC 1d practical health" in rendered
    assert "status=btc_only_practical_with_caveats" in rendered
    assert "caveats=4" in rendered
