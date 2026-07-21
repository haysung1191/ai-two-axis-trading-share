from __future__ import annotations

import json
from pathlib import Path

from scripts.run_bithumb_paper_nightly import run_nightly_paper, render_paper_nightly_health_line
from scripts.run_btc_1d_shadow_update import (
    _build_shadow_update_output,
    _refresh_contract_artifacts_after_paper,
    _write_latest_aliases,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_shadow_inputs(base: Path) -> None:
    _write_json(
        base / "btc_1d_baseline_freeze_20260417T000000Z.json",
        {"frozen_candidate": "low_vol_cap_045_025_minvol020_p2200"},
    )
    _write_json(
        base / "btc_1d_candidate_status_board_20260417T000001Z.json",
        {
            "active_candidate": "low_vol_cap_045_025_minvol020_p2200",
            "status": "carryable_candidate",
            "carry_reference_period": 2200,
            "survivability_reference_period": 2600,
        },
    )
    _write_json(
        base / "btc_1d_shadow_readiness_20260417T000002Z.json",
        {
            "decision": "shadow_ready_for_btc_only",
            "why": {
                "btc": {
                    "pass_count": 2,
                    "total_count": 4,
                    "pass_rate": 0.5,
                    "stability_score": 0.5,
                    "failing_regimes": ["low_volatility", "range"],
                }
            },
        },
    )
    _write_json(
        base / "btc_1d_low_vol_cap_friction_20260417T000003Z.json",
        {
            "final_decision": "continue",
            "decision_reason": "ok",
            "levels": [{"cost_bps": 20.0, "decision": "PASS", "sharpe": 1.04}],
        },
    )
    _write_json(
        base / "btc_1d_walk_forward_diagnostic_20260417T000004Z.json",
        {
            "config": {"periods": 2200},
            "overfitting": {
                "passed": True,
                "oos_metrics": {"sharpe": 0.82, "cagr": 0.05, "max_drawdown": 0.06},
                "sensitivity_max_drift": 0.09,
                "unstable_parameters": [],
            },
            "analysis_result_json": str(base / "btc_1d_walk_forward_diagnostic_20260417T000004Z.json"),
            "analysis_result_md": str(base / "btc_1d_walk_forward_diagnostic_20260417T000004Z.md"),
        },
    )
    (base / "btc_1d_walk_forward_diagnostic_20260417T000004Z.md").write_text("# wf", encoding="utf-8")
    _write_json(
        base / "btc_1d_promoted_candidate_regression_20260417T000005Z.json",
        {
            "config": {"symbol": "ETHUSDT"},
            "summary": {"pass_rate": 0.0, "pass_count": 0, "total_count": 4},
            "results": [],
            "analysis_result_json": str(base / "btc_1d_promoted_candidate_regression_20260417T000005Z.json"),
        },
    )
    for stamp, periods, sharpe in [
        ("20260417T000006Z", 2200, 1.1),
        ("20260417T000007Z", 2600, 1.05),
    ]:
        _write_json(
            base / f"btc_1d_ema_trend_atr_exit_paper_validation_{stamp}.json",
            {
                "config": {
                    "periods": periods,
                    "ema_fast_window": 20,
                    "ema_slow_window": 50,
                    "atr_window": 14,
                    "atr_multiple": 3.5,
                    "time_stop_bars": 90,
                    "extra_parameters": {},
                },
                "decision_record": {
                    "decision": "PASS",
                    "key_metrics": {
                        "sharpe": sharpe,
                        "cagr": 0.14,
                        "max_drawdown": 0.12,
                        "win_rate": 0.5,
                        "trades": 100,
                        "completed_trades": 80,
                    },
                },
                "analysis_result_json": str(base / f"btc_1d_ema_trend_atr_exit_paper_validation_{stamp}.json"),
                "analysis_result_csv": str(base / f"btc_1d_ema_trend_atr_exit_paper_validation_{stamp}.csv"),
            },
        )
        (base / f"btc_1d_ema_trend_atr_exit_paper_validation_{stamp}.csv").write_text("ok", encoding="utf-8")
    _write_json(
        base / "btc_1d_attack_main_backup_screen_latest.json",
        {
            "preferred_main": {"name": "ratio112_tighter_stop_main", "cagr": 0.4243, "max_drawdown": 0.1609, "sharpe": 1.5613},
            "preferred_backup": {"name": "ratio111_tighter_stop_backup", "cagr": 0.4154, "max_drawdown": 0.1609, "sharpe": 1.5348},
        },
    )
    _write_json(
        base / "btc_1d_attack_defensive_bridge_screen_latest.json",
        {
            "preferred_attack_model": {"name": "ratio112_tighter_stop_main", "cagr": 0.4243, "max_drawdown": 0.1609, "sharpe": 1.5613},
            "preferred_defensive_model": {"name": "volatility_expansion_pullthrough_shorter_hold", "cagr": 0.2621, "max_drawdown": 0.1637, "sharpe": 1.2805},
        },
    )
    _write_json(
        base / "btc_1d_near_miss_priority_screen_latest.json",
        {"highest_priority_near_miss": {"name": "trend_dip_reversal_breakout_tighter_stop_mid_hold", "cagr": 0.3909, "max_drawdown": 0.2484}},
    )
    _write_json(
        base / "btc_1d_volatility_expansion_reclaim_stab_atrs_paper_validation_20260417T000008Z.json",
        {"decision_record": {"decision": "PASS", "key_metrics": {"sharpe": 1.0, "cagr": 0.3, "max_drawdown": 0.15, "trades": 40}}},
    )
    _write_json(
        base / "btc_1d_volatility_expansion_reclaim_stab_atrs_friction_20260417T000009Z.json",
        {
            "report": {
                "levels": [
                    {
                        "cost_bps": 20.0,
                        "decision": "PASS",
                        "sharpe": 1.0,
                        "cagr": 0.28,
                        "max_drawdown": 0.16,
                    }
                ]
            }
        },
    )
    _write_json(
        base / "btc_1d_volatility_expansion_reclaim_stab_atrs_benchmark_stats_20260417T000010Z.json",
        {
            "report": {
                "symbols": [
                    {"symbol": "BTCUSDT", "leader": {"sharpe": 1.1, "max_drawdown": 0.16}, "benchmarks": [{"label": "buy_and_hold", "metrics": {"sharpe": 0.9, "max_drawdown": 0.7}, "paired_bootstrap": {"p_diff_mean_gt_0": 0.2}}]},
                    {"symbol": "ETHUSDT", "leader": {"sharpe": 0.8}, "benchmarks": [{"label": "buy_and_hold", "metrics": {"sharpe": 0.9}, "paired_bootstrap": {"p_diff_mean_gt_0": 0.1}}]},
                ]
            }
        },
    )
    _write_json(
        base / "btc_1d_volatility_expansion_reclaim_stab_atrs_stats_20260417T000011Z.json",
        {"report": {"statistics": {"psr": 1.0, "dsr": 0.0, "dsr_hurdle_sharpe": 1.9}, "bootstrap": {"sharpe_ci_95": [0.6, 2.1], "cagr_ci_95": [0.1, 0.8], "p_sharpe_gt_0": 1.0}}},
    )
    _write_json(
        base / "btc_1d_volatility_expansion_reclaim_stab_atrs_regime_stability_20260417T000012Z.json",
        {"report": {"regime_metrics": {"regimes": {"high_volatility": {"sharpe": 0.6}, "low_volatility": {"sharpe": 0.2}, "range": {"sharpe": -1.0}}}, "leave_one_year_out": {"worst_cagr_year": 2020, "worst_mdd_year": 2023}}},
    )
    _write_json(
        base / "btc_1d_volatility_expansion_reclaim_stab_atrs_concentration_20260417T000013Z.json",
        {"report": {"trade_concentration": {"top_1_trade_share": 0.2, "top_3_trade_share": 0.4, "top_5_trade_share": 0.6}, "monthly_concentration": {"top_5_month_share": 0.5}}},
    )


def test_shadow_update_build_output_includes_paper_nightly_payload(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    paper_dir = tmp_path / "paper"
    ledger_path = tmp_path / "paper_ledger.json"
    exit_path = tmp_path / "exit_snapshot.json"
    logs_dir.mkdir()
    _write_json(
        logs_dir / "hourly_run_test.json",
        {
            "run_id": "1h:test",
            "candle_close_utc": "2026-04-16T12:00:00Z",
            "manual_brief": {
                "watchlist": [
                    {
                        "symbol": "BTC",
                        "rank": 1,
                        "action": "BUY",
                        "reference_price_krw": 150000000.0,
                        "suggested_stop_price_krw": 145000000.0,
                        "suggested_take_profit_price_krw": 160000000.0,
                        "risk_reward_ratio": 2.0,
                        "final_decision": "SCHEDULED",
                        "action_reason": "Scheduled by the baseline scanner.",
                    }
                ]
            },
        },
    )
    _write_json(
        exit_path,
        {
            "run_id": "1h:test-close",
            "candle_close_utc": "2026-04-16T13:00:00Z",
            "market_ohlc": {
                "KRW-BTC": {"open": 151000000.0, "high": 161000000.0, "low": 149000000.0, "close": 160500000.0}
            },
            "standard_check_order_reference": ["practical", "research", "contract", "brief"],
        },
    )
    paper_nightly = run_nightly_paper(
        logs_dir=logs_dir,
        run_id=None,
        ledger_json=ledger_path,
        output_dir=paper_dir,
        exit_json=exit_path,
        notional_krw=250000.0,
        max_orders=1,
        strategy_track="operating",
        access_key="ak",
        secret_key="sk",
        client_order_prefix="shadow-nightly",
    )
    payload = _build_shadow_update_output(
        practical_health={"status_label": "btc_only_practical_with_caveats"},
        practical_health_line="BTC 1d practical health | status=btc_only_practical_with_caveats",
        research_stack_health={"attack_frontier": "ratio112_tighter_stop_main"},
        research_stack_health_line="BTC 1d research stack | frontier=ratio112_tighter_stop_main",
        contract_health={
            "operating_brief_version": "operating_v3",
            "operating_index_version": "operating_v3",
            "research_stack_version": "research_stack_v2",
            "operating_contract_aligned": True,
            "paper_execution_contract_aligned": True,
            "contract_health_aligned": True,
            "research_contract_distinct": True,
            "contracts_are_well_partitioned": True,
            "preferred_operating_contract_version": "operating_v3",
            "preferred_research_contract_version": "research_stack_v2",
            "shared_standard_check_order": ["practical", "research", "contract", "brief"],
            "standard_check_order_aligned": True,
            "health_order_aligned": True,
        },
        contract_health_line="BTC 1d contract health | operating_brief=operating_v3",
        regression_lock_test="tests/unit/test_btc_1d_operating_cli_help_contract.py",
        combined_health_line="BTC 1d practical health ... || BTC 1d research stack ...",
        paper_nightly_health_line=render_paper_nightly_health_line(paper_nightly),
        execution_health_line="BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=0 | open=1",
        execution_contract_health_line="BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=0 | open=1 || execution contract | aligned | paper execution | track=operating | applied=1 | closed=0 | open=1",
        execution_contract_read="execution contract | aligned | paper execution | track=operating | applied=1 | closed=0 | open=1",
        execution_contract_aligned=True,
        execution_contract_paper_ledger_snapshot_summary_aligned=True,
        execution_contract_paper_execution_contract_checked_aligned_entry_aligned=True,
        execution_contract_paper_execution_contract_aligned_aligned_entry_aligned=True,
        execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned=True,
        execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned=True,
        execution_contract_paper_execution_contract_checked_aligned_summary_aligned=True,
        execution_contract_paper_execution_contract_aligned_aligned_summary_aligned=True,
        execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned=True,
        execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned=True,
        paper_execution_contract_checked=True,
        paper_execution_contract_aligned=True,
        paper_execution_contract_checked_aligned=True,
        paper_execution_contract_aligned_aligned=True,
        paper_execution_contract_checked_summary_aligned=True,
        paper_execution_contract_aligned_summary_aligned=True,
        paper_execution_contract_checked_aligned_entry_aligned=True,
        paper_execution_contract_aligned_aligned_entry_aligned=True,
        paper_execution_contract_checked_summary_aligned_entry_aligned=True,
        paper_execution_contract_aligned_summary_aligned_entry_aligned=True,
        paper_execution_contract_checked_aligned_summary_aligned=True,
        paper_execution_contract_aligned_aligned_summary_aligned=True,
        paper_execution_contract_checked_summary_aligned_summary_aligned=True,
        paper_execution_contract_aligned_summary_aligned_summary_aligned=True,
        paper_execution_read="paper execution | track=operating | applied=1 | closed=0 | open=1",
        paper_exit_duplicate_run=False,
        paper_ledger_consistent=True,
        paper_ledger_snapshot={"open_position_count": 1, "closed_position_count": 0},
        latest_summary={"candidate": "x"},
        latest_summary_paths={"json": "a.json", "md": "a.md"},
        latest_index_paths={"json": "b.json", "md": "b.md"},
        operating_brief_paths={"json": "c.json", "txt": "c.txt", "md": "c.md"},
        latest_aliases={"btc_1d_operating_index": "analysis_results\\btc_1d_operating_index_latest.json"},
        carry_validation={
            "analysis_result_json": "carry.json",
            "analysis_result_csv": "carry.csv",
            "decision_record": {"decision": "PASS"},
        },
        survivability_validation={
            "analysis_result_json": "surv.json",
            "analysis_result_csv": "surv.csv",
            "decision_record": {"decision": "PASS"},
        },
        eth_regression={"analysis_result_json": "eth.json", "summary": {"pass_rate": 0.0}},
        walk_forward={
            "analysis_result_json": "wf.json",
            "analysis_result_md": "wf.md",
            "overfitting": {
                "passed": True,
                "oos_metrics": {"sharpe": 0.82},
                "sensitivity_max_drift": 0.09,
                "unstable_parameters": [],
            },
        },
        shadow_packet_result={"packet": {"candidate": "x"}, "json_path": "sp.json", "md_path": "sp.md"},
        operating_snapshot={"status_json": "status.json"},
        eth_symbol="ETHUSDT",
        carry_periods=2200,
        survivability_periods=2600,
        walk_forward_periods=2200,
        paper_nightly=paper_nightly,
    )
    assert payload["paper_nightly"]["intent_count"] == 1
    assert payload["paper_nightly"]["paper_applied_count"] == 1
    assert payload["paper_nightly"]["paper_closed_count"] == 0
    assert payload["paper_nightly"]["paper_exit_duplicate_run"] is False
    assert payload["paper_nightly"]["paper_ledger_consistent"] is True
    assert payload["paper_nightly_health_line"].startswith("BTC 1d paper nightly | track=operating")
    assert payload["execution_health_line"].startswith("BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly")
    assert payload["execution_contract_read"] == "execution contract | aligned | paper execution | track=operating | applied=1 | closed=0 | open=1"
    assert payload["execution_contract_aligned"] is True
    assert payload["execution_contract_paper_ledger_snapshot_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert payload["paper_execution_contract_checked"] is True
    assert payload["paper_execution_contract_aligned"] is True
    assert payload["paper_execution_contract_checked_aligned"] is True
    assert payload["paper_execution_contract_aligned_aligned"] is True
    assert payload["paper_execution_contract_checked_summary_aligned"] is True
    assert payload["paper_execution_contract_aligned_summary_aligned"] is True
    assert payload["paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert payload["paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert payload["paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert payload["paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert payload["paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert payload["paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert payload["paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert payload["paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert payload["contract_health_operating_contract_aligned"] is True
    assert payload["contract_health_paper_execution_contract_aligned"] is True
    assert payload["contract_health_aligned"] is True
    assert payload["contract_health_contracts_are_well_partitioned"] is True
    assert payload["paper_execution_read"] == "paper execution | track=operating | applied=1 | closed=0 | open=1"
    assert payload["paper_exit_duplicate_run"] is False
    assert payload["paper_ledger_consistent"] is True
    assert Path(payload["paper_nightly"]["artifacts"]["summary_json"]).exists()
    assert Path(payload["paper_nightly"]["artifacts"]["summary_md"]).exists()


def test_shadow_update_paper_bridge_republishes_execution_contract_after_paper(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    logs_dir = tmp_path / "logs"
    paper_dir = tmp_path / "paper"
    ledger_path = tmp_path / "paper_ledger.json"
    exit_path = tmp_path / "exit_snapshot.json"
    logs_dir.mkdir()
    analysis_dir.mkdir()
    _seed_shadow_inputs(analysis_dir)
    _write_json(
        logs_dir / "hourly_run_test.json",
        {
            "run_id": "1h:test",
            "candle_close_utc": "2026-04-16T12:00:00Z",
            "manual_brief": {
                "watchlist": [
                    {
                        "symbol": "BTC",
                        "rank": 1,
                        "action": "BUY",
                        "reference_price_krw": 150000000.0,
                        "suggested_stop_price_krw": 145000000.0,
                        "suggested_take_profit_price_krw": 160000000.0,
                        "risk_reward_ratio": 2.0,
                        "final_decision": "SCHEDULED",
                        "action_reason": "Scheduled by the baseline scanner.",
                    }
                ]
            },
        },
    )
    _write_json(
        exit_path,
        {
            "run_id": "1h:test-close",
            "candle_close_utc": "2026-04-16T13:00:00Z",
            "market_ohlc": {
                "KRW-BTC": {"open": 151000000.0, "high": 161000000.0, "low": 149000000.0, "close": 160500000.0}
            },
            "standard_check_order_reference": ["practical", "research", "contract", "brief"],
        },
    )
    paper_nightly = run_nightly_paper(
        logs_dir=logs_dir,
        run_id=None,
        ledger_json=ledger_path,
        output_dir=paper_dir,
        exit_json=exit_path,
        notional_krw=250000.0,
        max_orders=1,
        strategy_track="operating",
        access_key="ak",
        secret_key="sk",
        client_order_prefix="shadow-nightly",
    )
    latest_aliases = _write_latest_aliases(
        analysis_dir=analysis_dir,
        paths={
            "btc_1d_paper_nightly_summary": paper_nightly["artifacts"]["summary_json"],
            "btc_1d_paper_nightly_summary_md": paper_nightly["artifacts"]["summary_md"],
        },
    )
    paper_nightly_health_line = render_paper_nightly_health_line(paper_nightly)
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
            "scope": "btc_only_practical_with_caveats",
            "execution_health_line": f"BTC 1d practical health ... || BTC 1d research stack ... || {paper_nightly_health_line}",
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_nightly["paper_execution_read"],
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "execution_health_line": f"BTC 1d practical health ... || BTC 1d research stack ... || {paper_nightly_health_line}",
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_nightly["paper_execution_read"],
            "paper_nightly_summary": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
            "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_practical_promotion_gate_latest.json",
        {
            "ok": False,
            "status_label": "btc_only_practical_with_caveats",
            "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
            "scope": "btc_only_practical_with_caveats",
            "caveats": [],
            "carry_metrics": {"sharpe": 1.3946, "cagr": 0.3772, "max_drawdown": 0.1609},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_contract_screen_latest.json",
        {
            "execution_contract_summary": {
                "paper_execution_read": "paper execution | track=operating | applied=999 | closed=999 | open=999"
            },
            "execution_contract_verdict": {"execution_contract_aligned": False},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_quick_read_contract_screen_latest.json",
        {"contract_summary": {"contract_health_aligned": False}},
    )
    _write_json(
        analysis_dir / "btc_1d_meta_contract_screen_latest.json",
        {
            "meta_contract_summary": {
                "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
                "standard_check_order": ["practical", "research", "contract", "brief"],
                "standard_check_order_aligned": True,
                "health_order_aligned": True,
                "execution_contract_symmetry_ready": True,
            }
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json",
        {"summary": {"meta_contract_tests": []}, "tests": []},
    )

    refreshed_aliases = _refresh_contract_artifacts_after_paper(
        analysis_dir=analysis_dir,
        latest_aliases=latest_aliases,
    )

    execution_contract_payload = json.loads(
        (analysis_dir / "btc_1d_execution_contract_screen_latest.json").read_text(encoding="utf-8")
    )
    assert refreshed_aliases["btc_1d_execution_contract_screen"].endswith(
        "btc_1d_execution_contract_screen_latest.json"
    )
    assert (
        execution_contract_payload["execution_contract_summary"]["paper_execution_read"]
        == paper_nightly["paper_execution_read"]
    )
