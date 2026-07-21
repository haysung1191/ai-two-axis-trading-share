from __future__ import annotations

import json
from pathlib import Path

from scripts.check_btc_1d_practical_promotion_gate import (
    build_parser,
    evaluate_practical_promotion_gate,
    main,
    render_practical_promotion_gate,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_scorecard(analysis_dir: Path, *, dsr: float = 0.0, range_sharpe: float = -0.5, top_5_trade_share: float = 0.68) -> None:
    _write_json(
        analysis_dir / "btc_1d_practical_scorecard_latest.json",
        {
            "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
            "status_label": "btc_only_practical_with_caveats",
            "summary": {
                "scope": "BTC-only",
                "paper_decision": "PASS",
                "carry_metrics": {"sharpe": 1.39, "cagr": 0.37, "max_drawdown": 0.16},
                "friction_20bps_decision": "PASS",
            },
            "benchmark": {
                "btc": {
                    "leader": {"sharpe": 1.39},
                    "benchmarks": [
                        {"label": "buy_and_hold", "metrics": {"sharpe": 0.95}},
                        {"label": "simple_ma_trend", "metrics": {"sharpe": 0.72}},
                        {"label": "simple_breakout", "metrics": {"sharpe": 0.94}},
                    ],
                },
                "eth": {
                    "leader": {"sharpe": 0.89},
                    "benchmarks": [
                        {
                            "label": "buy_and_hold",
                            "metrics": {"sharpe": 0.95},
                            "paired_bootstrap": {"p_diff_mean_gt_0": 0.06},
                        }
                    ],
                },
            },
            "statistical_defense": {"psr": 1.0, "dsr": dsr},
            "bootstrap": {"p_sharpe_gt_0": 1.0},
            "regime": {"regimes": {"range": {"sharpe": range_sharpe}}},
            "concentration": {"trade_concentration": {"top_5_trade_share": top_5_trade_share}},
        },
    )


def test_practical_promotion_gate_returns_caveated_pass_for_current_shape(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_scorecard(analysis_dir)

    result = evaluate_practical_promotion_gate(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is True
    assert result["decision"] == "btc_only_practical_with_caveats"
    assert result["status_label"] == "btc_only_practical_with_caveats"
    assert any("dsr below floor" in item for item in result["caveats"])
    assert any("range regime sharpe below floor" in item for item in result["caveats"])
    assert any("top 5 trade share above ceiling" in item for item in result["caveats"])
    assert any("eth buy&hold paired p(diff>0) below floor" in item for item in result["caveats"])


def test_practical_promotion_gate_fails_on_core_gate_break(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_scorecard(analysis_dir)
    payload = json.loads((analysis_dir / "btc_1d_practical_scorecard_latest.json").read_text(encoding="utf-8"))
    payload["summary"]["paper_decision"] = "FAIL"
    _write_json(analysis_dir / "btc_1d_practical_scorecard_latest.json", payload)

    result = evaluate_practical_promotion_gate(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert result["decision"] == "hold_not_promotable"
    assert any("paper decision mismatch" in item for item in result["failures"])


def test_practical_promotion_gate_main_writes_latest_files(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_scorecard(analysis_dir)

    exit_code = main(["--analysis-dir", str(analysis_dir)])

    assert exit_code == 0
    assert (analysis_dir / "btc_1d_practical_promotion_gate_latest.json").exists()
    assert (analysis_dir / "btc_1d_practical_promotion_gate_md_latest.md").exists()


def test_practical_promotion_gate_falls_back_to_active_post_spike_candidate(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_practical_scorecard_latest.json",
        {
            "status": "unavailable",
            "reason": "legacy scorecard source absent",
        },
    )
    _write_json(
        analysis_dir
        / "btc_1d_post_spike_consolidation_breakout_v4_btcusdt_1d_2200_trend960_depth055_volume100_hold36_paper_validation_20260516T000000Z.json",
        {
            "config": {"strategy_name": "btc_1d_post_spike_consolidation_breakout_v4"},
            "decision_record": {
                "decision": "PASS",
                "key_metrics": {
                    "sharpe": 1.50,
                    "cagr": 0.2469,
                    "max_drawdown": 0.1352,
                    "trades": 22,
                },
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_post_spike_consolidation_breakout_friction_latest.json",
        {
            "candidate": "post_spike_consolidation_breakout_trend960_depth055_volume100_hold36",
            "levels": [
                {"cost_bps": 8.0, "decision": "PASS"},
                {"cost_bps": 20.0, "decision": "PASS"},
            ],
        },
    )

    result = evaluate_practical_promotion_gate(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is True
    assert result["candidate"] == "post_spike_consolidation_breakout_trend960_depth055_volume100_hold36"
    assert result["friction_20bps_decision"] == "PASS"
    assert any("fallback_without_legacy_scorecard" in item for item in result["caveats"])


def test_render_practical_promotion_gate_mentions_caveats() -> None:
    rendered = render_practical_promotion_gate(
        {
            "ok": True,
            "decision": "btc_only_practical_with_caveats",
            "status_label": "btc_only_practical_with_caveats",
            "candidate": "cand",
            "scope": "BTC-only",
            "paper_decision": "PASS",
            "friction_20bps_decision": "PASS",
            "carry_metrics": {"sharpe": 1.1, "cagr": 0.3, "max_drawdown": 0.16},
            "psr": 1.0,
            "dsr": 0.0,
            "bootstrap_p_sharpe_gt_0": 1.0,
            "range_regime_sharpe": -0.5,
            "top_5_trade_share": 0.68,
            "eth_leader_sharpe": 0.89,
            "eth_buyhold_paired_p_diff_gt_0": 0.06,
            "failures": [],
            "caveats": ["dsr below floor"],
            "source_scorecard": "x",
        }
    )

    assert "BTC 1d Practical Promotion Gate" in rendered
    assert "btc_only_practical_with_caveats" in rendered
    assert "status_label" in rendered
    assert "- dsr below floor" in rendered
    assert "eth_buyhold_paired_p_diff_gt_0" in rendered
