from __future__ import annotations

import json
from pathlib import Path

from scripts.publish_btc_1d_practical_scorecard import _render_markdown, main


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_publish_practical_scorecard(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "btc_1d_volatility_expansion_reclaim_stab_atrs_paper_validation_20260415T010122Z.json",
        {"decision_record": {"decision": "PASS", "key_metrics": {"sharpe": 1.0, "cagr": 0.3, "max_drawdown": 0.15, "trades": 40}}},
    )
    _write_json(
        tmp_path / "btc_1d_volatility_expansion_reclaim_stab_atrs_friction_20260415T010806Z.json",
        {"report": {"levels": [{"cost_bps": 20.0, "decision": "PASS", "sharpe": 1.0, "cagr": 0.28, "max_drawdown": 0.16}]}},
    )
    _write_json(
        tmp_path / "btc_1d_volatility_expansion_reclaim_stab_atrs_benchmark_stats_20260415T131904Z.json",
        {
            "report": {
                "symbols": [
                    {"symbol": "BTCUSDT", "leader": {"sharpe": 1.1, "max_drawdown": 0.16}, "benchmarks": [{"metrics": {"sharpe": 0.9, "max_drawdown": 0.7}, "paired_bootstrap": {"p_diff_mean_gt_0": 0.2}}]},
                    {"symbol": "ETHUSDT", "leader": {"sharpe": 0.8}, "benchmarks": [{"metrics": {"sharpe": 0.9}, "paired_bootstrap": {"p_diff_mean_gt_0": 0.1}}]},
                ]
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_volatility_expansion_reclaim_stab_atrs_stats_20260415T131400Z.json",
        {"report": {"statistics": {"psr": 1.0, "dsr": 0.0, "dsr_hurdle_sharpe": 1.9}, "bootstrap": {"sharpe_ci_95": [0.6, 2.1], "cagr_ci_95": [0.1, 0.8]}}},
    )
    _write_json(
        tmp_path / "btc_1d_volatility_expansion_reclaim_stab_atrs_regime_stability_20260415T133026Z.json",
        {"report": {"regime_metrics": {"regimes": {"high_volatility": {"sharpe": 0.6}, "low_volatility": {"sharpe": 0.2}, "range": {"sharpe": -1.0}}}, "leave_one_year_out": {"worst_cagr_year": 2020, "worst_mdd_year": 2023}}},
    )
    _write_json(
        tmp_path / "btc_1d_volatility_expansion_reclaim_stab_atrs_concentration_20260415T133941Z.json",
        {"report": {"trade_concentration": {"top_1_trade_share": 0.2, "top_3_trade_share": 0.4, "top_5_trade_share": 0.6}, "monthly_concentration": {"top_5_month_share": 0.5}}},
    )

    main(["--analysis-dir", str(tmp_path)])

    scorecards = list(tmp_path.glob("btc_1d_practical_scorecard_*.json"))
    assert scorecards
    payload = json.loads(scorecards[0].read_text(encoding="utf-8"))
    assert payload["status_label"] == "btc_only_practical_with_caveats"
    assert (tmp_path / "btc_1d_practical_scorecard_latest.json").exists()
    assert (tmp_path / "btc_1d_practical_scorecard_md_latest.md").exists()


def test_render_practical_scorecard_surfaces_eth_weakness_in_quick_read() -> None:
    rendered = _render_markdown(
        {
            "candidate": "cand",
            "decision": "paper_ready_btc_only_with_caveats",
            "status_label": "btc_only_practical_with_caveats",
            "summary": {
                "scope": "BTC-only",
                "paper_decision": "PASS",
                "carry_metrics": {
                    "sharpe": 1.3,
                    "cagr": 0.35,
                    "max_drawdown": 0.16,
                    "trades": 40,
                },
                "friction_20bps_decision": "PASS",
                "friction_20bps_metrics": {"sharpe": 1.2, "cagr": 0.33, "max_drawdown": 0.16},
            },
            "benchmark": {
                "btc": {
                    "leader": {"sharpe": 1.3, "max_drawdown": 0.16},
                    "benchmarks": [{"metrics": {"sharpe": 0.9, "max_drawdown": 0.7}}],
                },
                "eth": {
                    "leader": {"sharpe": 0.89},
                    "benchmarks": [{"paired_bootstrap": {"p_diff_mean_gt_0": 0.061}}],
                },
            },
            "statistical_defense": {"psr": 1.0, "dsr": 0.0, "dsr_hurdle_sharpe": 1.9},
            "bootstrap": {"sharpe_ci_95": [0.6, 2.1], "cagr_ci_95": [0.1, 0.8]},
            "regime": {
                "regimes": {
                    "high_volatility": {"sharpe": 0.6},
                    "low_volatility": {"sharpe": 0.2},
                    "range": {"sharpe": -1.0},
                }
            },
            "leave_one_year_out": {"worst_cagr_year": 2020, "worst_mdd_year": 2023},
            "concentration": {
                "trade_concentration": {"top_1_trade_share": 0.2, "top_3_trade_share": 0.4, "top_5_trade_share": 0.6},
                "monthly_concentration": {"top_5_month_share": 0.5},
            },
            "risks": ["BTC-only practical model; ETH generalization is weak."],
        }
    )

    assert "Quick read" in rendered
    assert "Status label" in rendered
    assert "ETH generalization weak" in rendered
    assert "P(diff>0)=0.0610" in rendered
