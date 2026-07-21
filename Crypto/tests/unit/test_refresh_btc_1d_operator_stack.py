from __future__ import annotations

import io
import json
import shutil
from contextlib import redirect_stdout
from pathlib import Path

import scripts.run_btc_1d_shadow_update as shadow_update_script
from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
)
from scripts.refresh_btc_1d_operator_stack import build_parser, main as refresh_operator_stack_main
from scripts.run_bithumb_paper_nightly import run_nightly_paper
from scripts.run_btc_1d_shadow_update import main as run_shadow_update_main, refresh_operator_stack
from tests.unit.btc_1d_handoff_contract_keys import FAST_GATE_SHARED_HANDOFF_KEYS
from tests.unit.test_run_btc_1d_shadow_update_paper_bridge import _seed_shadow_inputs, _write_json


def _seed_remote_monitoring_handoff_ready_artifacts(analysis_dir: Path) -> None:
    _write_json(
        analysis_dir / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
        {
            "stack_context": {
                "attack_main": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
                "operator_verdict": "shadow_monitoring_ready",
                "shadow_decision": "shadow_ready_for_btc_only",
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "remote_monitoring_deployment_handoff_requirements": {
                "challenger_live_shadow_locked_release_governance_entry_ready": True,
                "operating_index_attack_challenger_reflects_governance_entry": True,
                "operating_brief_attack_challenger_reflects_governance_entry": True,
                "operator_dashboard_attack_challenger_reflects_governance_entry": True,
                "operator_dashboard_deployment_track_ready": True,
                "promotion_chain_still_green": True,
            },
            "remote_monitoring_deployment_handoff_verdict": {
                "remote_monitoring_deployment_handoff_ready": True,
                "remote_monitoring_deployment_handoff_lane": ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
                "next_step_now": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            },
        },
    )


def _seed_refresh_ready_analysis_dir(tmp_path: Path) -> Path:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir()
    _seed_shadow_inputs(analysis_dir)
    _write_json(
        analysis_dir / "btc_1d_latest_summary_latest.json",
        {
            "candidate": "low_vol_cap_045_025_minvol020_p2200",
            "scope": "BTC-only",
            "carry": {"periods": 2200, "decision": "PASS", "sharpe": 1.1, "cagr": 0.14, "max_drawdown": 0.12},
            "survivability": {"periods": 2600, "decision": "PASS", "sharpe": 1.05, "cagr": 0.14, "max_drawdown": 0.12},
            "walk_forward": {
                "passed": True,
                "oos_sharpe": 0.82,
                "oos_cagr": 0.05,
                "oos_max_drawdown": 0.06,
                "sensitivity_max_drift": 0.09,
                "unstable_parameters": [],
            },
            "friction": {"decision": "continue", "heaviest_level_bps": 20.0, "heaviest_level_sharpe": 1.04},
            "eth_cross_check": {"symbol": "ETHUSDT", "pass_rate": 0.0, "pass_count": 0, "total_count": 4},
            "shadow_decision": "shadow_ready_for_btc_only",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_shadow_packet_latest.json",
        {
            "status": "carryable_candidate",
            "paper_validation_decision": "PASS",
            "survivability_validation_decision": "PASS",
            "friction_validation_heaviest_level": {"decision": "PASS"},
        },
    )
    (analysis_dir / "btc_1d_latest_summary_md_latest.md").write_text("# latest", encoding="utf-8")
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
    shutil.copyfile(
        paper_nightly["artifacts"]["summary_json"],
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
    )
    shutil.copyfile(
        paper_nightly["artifacts"]["summary_md"],
        analysis_dir / "btc_1d_paper_nightly_summary_md_latest.md",
    )
    return analysis_dir


def test_refresh_btc_1d_operator_stack_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.analysis_dir == Path("analysis_results")
    assert args.sync_passes == 3


def test_refresh_btc_1d_operator_stack_main_emits_top_level_attack_challenger_fields(
    tmp_path: Path,
    monkeypatch,
) -> None:
    refresh_payload = {
        "analysis_dir": str(tmp_path / "analysis_results"),
        "sync_passes": 2,
        "refresh_summary": {
            "deployment_monitoring_active": True,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": "deployment monitoring active",
            "attack_challenger_bridge_report": (
                "analysis_results\\"
                "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
            ),
        },
        "deployment_monitoring_active": True,
        "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
        "attack_challenger_next_step": "deployment monitoring active",
        "attack_challenger_bridge_report": (
            "analysis_results\\"
            "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        ),
        "latest_aliases": {},
        "combined_health_line": "combined",
        "paper_nightly_health_line": "paper nightly",
        "execution_health_line": "execution",
        "contract_health": {},
        "execution_contract_state": {},
        "dashboard_summary": {},
    }

    monkeypatch.setattr(
        "scripts.refresh_btc_1d_operator_stack.refresh_operator_stack",
        lambda *, analysis_dir, sync_passes: refresh_payload,
    )

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = refresh_operator_stack_main(
            [
                "--analysis-dir",
                str(tmp_path / "analysis_results"),
                "--sync-passes",
                "2",
            ]
        )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["deployment_monitoring_active"] is True
    assert payload["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert payload["attack_challenger_next_step"] == "deployment monitoring active"
    assert payload["attack_challenger_bridge_report"] == (
        "analysis_results\\"
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )


def test_refresh_entrypoints_share_top_level_handoff_payload_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    refresh_payload = {
        "analysis_dir": str(tmp_path / "analysis_results"),
        "sync_passes": 2,
        "refresh_summary": {
            "deployment_monitoring_active": True,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": "deployment monitoring active",
            "attack_challenger_bridge_report": (
                "analysis_results\\"
                "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
            ),
        },
        "deployment_monitoring_active": True,
        "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
        "attack_challenger_next_step": "deployment monitoring active",
        "attack_challenger_bridge_report": (
            "analysis_results\\"
            "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        ),
        "latest_aliases": {},
        "combined_health_line": "combined",
        "paper_nightly_health_line": "paper nightly",
        "execution_health_line": "execution",
        "contract_health": {},
        "execution_contract_state": {},
        "dashboard_summary": {},
    }

    monkeypatch.setattr(
        "scripts.refresh_btc_1d_operator_stack.refresh_operator_stack",
        lambda *, analysis_dir, sync_passes: dict(refresh_payload),
    )
    monkeypatch.setattr(
        "scripts.run_btc_1d_shadow_update.refresh_operator_stack",
        lambda *, analysis_dir, sync_passes: dict(refresh_payload),
    )

    refresh_stdout = io.StringIO()
    with redirect_stdout(refresh_stdout):
        refresh_exit_code = refresh_operator_stack_main(
            [
                "--analysis-dir",
                str(tmp_path / "analysis_results"),
                "--sync-passes",
                "2",
            ]
        )

    shadow_stdout = io.StringIO()
    with redirect_stdout(shadow_stdout):
        shadow_exit_code = run_shadow_update_main(
            [
                "--analysis-dir",
                str(tmp_path / "analysis_results"),
                "--refresh-only",
                "--sync-passes",
                "2",
            ]
        )

    assert refresh_exit_code == 0
    assert shadow_exit_code == 0

    refresh_result = json.loads(refresh_stdout.getvalue())
    shadow_result = json.loads(shadow_stdout.getvalue())

    for key in FAST_GATE_SHARED_HANDOFF_KEYS:
        assert refresh_result[key] == shadow_result[key], key
        assert refresh_result[key] == refresh_result["refresh_summary"][key], key
        assert shadow_result[key] == shadow_result["refresh_summary"][key], key


def test_refresh_operator_stack_republishes_latest_operator_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir()
    _seed_shadow_inputs(analysis_dir)

    _write_json(
        analysis_dir / "btc_1d_latest_summary_latest.json",
        {
            "candidate": "low_vol_cap_045_025_minvol020_p2200",
            "scope": "BTC-only",
            "carry": {
                "periods": 2200,
                "decision": "PASS",
                "sharpe": 1.1,
                "cagr": 0.14,
                "max_drawdown": 0.12,
            },
            "survivability": {
                "periods": 2600,
                "decision": "PASS",
                "sharpe": 1.05,
                "cagr": 0.14,
                "max_drawdown": 0.12,
            },
            "walk_forward": {
                "passed": True,
                "oos_sharpe": 0.82,
                "oos_cagr": 0.05,
                "oos_max_drawdown": 0.06,
                "sensitivity_max_drift": 0.09,
                "unstable_parameters": [],
            },
            "friction": {
                "decision": "continue",
                "heaviest_level_bps": 20.0,
                "heaviest_level_sharpe": 1.04,
            },
            "eth_cross_check": {
                "symbol": "ETHUSDT",
                "pass_rate": 0.0,
                "pass_count": 0,
                "total_count": 4,
            },
            "shadow_decision": "shadow_ready_for_btc_only",
        },
    )
    (analysis_dir / "btc_1d_latest_summary_md_latest.md").write_text("# latest", encoding="utf-8")

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
                "KRW-BTC": {
                    "open": 151000000.0,
                    "high": 161000000.0,
                    "low": 149000000.0,
                    "close": 160500000.0,
                }
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
    shutil.copyfile(
        paper_nightly["artifacts"]["summary_json"],
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
    )
    shutil.copyfile(
        paper_nightly["artifacts"]["summary_md"],
        analysis_dir / "btc_1d_paper_nightly_summary_md_latest.md",
    )

    _write_json(
        analysis_dir / "btc_1d_operator_dashboard_latest.json",
        {
            "dashboard_summary": {
                "contract_health_aligned": False,
                "execution_contract_aligned": False,
                "paper_execution_contract_aligned": False,
                "paper_ledger_consistent": False,
                "quick_read_contract_partitioned": False,
            }
        },
    )
    _write_json(
        analysis_dir / "btc_1d_quick_read_contract_screen_latest.json",
        {
            "contract_summary": {
                "operating_contract_aligned": True,
                "paper_execution_contract_aligned": True,
                "contract_health_aligned": True,
            },
            "contract_verdict": {
                "contracts_are_well_partitioned": True,
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_contract_screen_latest.json",
        {
            "execution_contract_summary": {
                "execution_contract_health_line": "execution health || execution contract",
                "execution_contract_read": "execution contract | aligned | paper execution",
                "paper_ledger_snapshot_summary_aligned": True,
                "paper_execution_contract_aligned_summary_aligned": True,
            },
            "execution_contract_verdict": {
                "execution_contract_aligned": True,
            },
        },
    )
    seeded_attack_aliases = {
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        ),
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md_latest.md"
        ),
    }
    (
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    ).write_text("{}", encoding="utf-8")
    (
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md_latest.md"
    ).write_text("# handoff", encoding="utf-8")
    monkeypatch.setattr(
        shadow_update_script,
        "_publish_attack_challenger_outputs",
        lambda *, analysis_dir: seeded_attack_aliases,
    )
    monkeypatch.setattr(
        shadow_update_script,
        "_refresh_contract_artifacts_after_paper",
        lambda *, analysis_dir, latest_aliases: latest_aliases,
    )

    result = refresh_operator_stack(analysis_dir=analysis_dir, sync_passes=3)

    dashboard_payload = json.loads(
        (analysis_dir / "btc_1d_operator_dashboard_latest.json").read_text(encoding="utf-8")
    )
    dashboard_summary = dashboard_payload["dashboard_summary"]
    operating_index_payload = json.loads(
        (analysis_dir / "btc_1d_operating_index_latest.json").read_text(encoding="utf-8")
    )
    operating_brief_payload = json.loads(
        (analysis_dir / "btc_1d_operating_brief_latest.json").read_text(encoding="utf-8")
    )
    execution_contract_payload = json.loads(
        (analysis_dir / "btc_1d_execution_contract_screen_latest.json").read_text(encoding="utf-8")
    )
    paper_summary_payload = json.loads(
        (analysis_dir / "btc_1d_paper_nightly_summary_latest.json").read_text(encoding="utf-8")
    )

    assert result["dashboard_summary"]["contract_health_aligned"] is True
    assert result["refresh_summary"]["candidate"] == "low_vol_cap_045_025_minvol020_p2200"
    assert result["refresh_summary"]["shadow_decision"] == "shadow_ready_for_btc_only"
    assert result["refresh_summary"]["contract_health_aligned"] is True
    assert (
        result["refresh_summary"]["execution_contract_aligned"]
        == dashboard_summary["execution_contract_aligned"]
    )
    assert (
        result["refresh_summary"]["paper_execution_contract_aligned"]
        == dashboard_summary["paper_execution_contract_aligned"]
    )
    assert result["refresh_summary"]["paper_ledger_consistent"] is True
    assert result["refresh_summary"]["paper_exit_duplicate_run"] is False
    assert (
        result["refresh_summary"]["operator_verdict"]
        == dashboard_summary["operator_verdict"]
    )
    assert isinstance(
        result["refresh_summary"]["attack_challenger_remote_monitoring_deployment_handoff_ready"],
        bool,
    )
    assert (
        result["deployment_monitoring_active"]
        == result["refresh_summary"]["deployment_monitoring_active"]
    )
    assert (
        result["attack_challenger_remote_monitoring_deployment_handoff_ready"]
        == result["refresh_summary"][
            "attack_challenger_remote_monitoring_deployment_handoff_ready"
        ]
    )
    assert result["attack_challenger_next_step"] == result["refresh_summary"].get(
        "attack_challenger_next_step",
        "",
    )
    assert result["attack_challenger_bridge_report"] == result["refresh_summary"].get(
        "attack_challenger_bridge_report",
        "",
    )
    assert result["refresh_summary"]["dashboard_ready"] == dashboard_summary["dashboard_ready"]
    assert result["refresh_summary"]["refresh_read"].startswith("refresh summary | verdict=")
    assert result["refresh_summary"]["operator_dashboard_json"].endswith(
        "btc_1d_operator_dashboard_latest.json"
    )
    assert (
        dashboard_summary["contract_health_aligned"]
        == result["refresh_summary"]["contract_health_aligned"]
    )
    assert (
        dashboard_summary["execution_contract_aligned"]
        == result["refresh_summary"]["execution_contract_aligned"]
    )
    assert (
        dashboard_summary["paper_execution_contract_aligned"]
        == result["refresh_summary"]["paper_execution_contract_aligned"]
    )
    assert (
        dashboard_summary["paper_ledger_consistent"]
        == result["refresh_summary"]["paper_ledger_consistent"]
    )
    assert (
        dashboard_summary["dashboard_ready"]
        == result["refresh_summary"]["dashboard_ready"]
    )
    assert (
        dashboard_summary["quick_read_contract_partitioned"]
        == result["refresh_summary"]["quick_read_contract_partitioned"]
    )
    assert (
        operating_index_payload["execution_contract_aligned"]
        == dashboard_summary["execution_contract_aligned"]
    )
    assert (
        operating_brief_payload["execution_contract_aligned"]
        == dashboard_summary["execution_contract_aligned"]
    )
    assert (
        execution_contract_payload["execution_contract_summary"]["paper_ledger_snapshot_read"]
        == paper_summary_payload["paper_ledger_snapshot_read"]
    )


def test_shadow_update_main_refresh_only_reuses_fast_refresh(tmp_path: Path, capsys) -> None:
    analysis_dir = _seed_refresh_ready_analysis_dir(tmp_path)

    exit_code = run_shadow_update_main(
        ["--analysis-dir", str(analysis_dir), "--refresh-only", "--sync-passes", "2"]
    )
    output = capsys.readouterr().out
    payload = json.loads(output)
    dashboard_payload = json.loads(
        (analysis_dir / "btc_1d_operator_dashboard_latest.json").read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert payload["sync_passes"] == 2
    assert payload["refresh_summary"]["candidate"] == "low_vol_cap_045_025_minvol020_p2200"
    assert payload["refresh_summary"]["shadow_decision"] == "shadow_ready_for_btc_only"
    assert payload["refresh_summary"]["contract_health_aligned"] is True
    assert payload["refresh_summary"]["execution_contract_aligned"] is True
    assert payload["refresh_summary"]["paper_execution_contract_aligned"] is True
    assert payload["refresh_summary"]["paper_ledger_consistent"] is True
    assert payload["refresh_summary"]["operator_verdict"] == "shadow_monitoring_ready"
    assert isinstance(
        payload["refresh_summary"]["attack_challenger_remote_monitoring_deployment_handoff_ready"],
        bool,
    )
    assert (
        payload["deployment_monitoring_active"]
        == payload["refresh_summary"]["deployment_monitoring_active"]
    )
    assert (
        payload["attack_challenger_remote_monitoring_deployment_handoff_ready"]
        == payload["refresh_summary"][
            "attack_challenger_remote_monitoring_deployment_handoff_ready"
        ]
    )
    assert payload["attack_challenger_next_step"] == payload["refresh_summary"].get(
        "attack_challenger_next_step",
        "",
    )
    assert payload["attack_challenger_bridge_report"] == payload["refresh_summary"].get(
        "attack_challenger_bridge_report",
        "",
    )
    assert payload["refresh_summary"]["dashboard_ready"] is True
    assert payload["refresh_summary"]["project_direction"] == "ops hardening"
    assert payload["refresh_summary"]["next_actions"] == [
        "remote monitoring and deployment handoff"
    ]
    assert "verdict=shadow_monitoring_ready" in payload["refresh_summary"]["refresh_read"]
    assert (
        "next_actions=remote monitoring and deployment handoff"
        in payload["refresh_summary"]["refresh_read"]
    )
    assert payload["dashboard_summary"]["contract_health_aligned"] is True
    assert dashboard_payload["dashboard_summary"]["contract_health_aligned"] is True
    assert payload["dashboard_summary"]["dashboard_ready"] is True


def test_refresh_operator_stack_uses_remote_monitoring_handoff_when_seeded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir()
    _seed_shadow_inputs(analysis_dir)
    _seed_remote_monitoring_handoff_ready_artifacts(analysis_dir)

    _write_json(
        analysis_dir / "btc_1d_latest_summary_latest.json",
        {
            "candidate": "low_vol_cap_045_025_minvol020_p2200",
            "scope": "BTC-only",
            "carry": {"periods": 2200, "decision": "PASS", "sharpe": 1.1, "cagr": 0.14, "max_drawdown": 0.12},
            "survivability": {"periods": 2600, "decision": "PASS", "sharpe": 1.05, "cagr": 0.14, "max_drawdown": 0.12},
            "walk_forward": {
                "passed": True,
                "oos_sharpe": 0.82,
                "oos_cagr": 0.05,
                "oos_max_drawdown": 0.06,
                "sensitivity_max_drift": 0.09,
                "unstable_parameters": [],
            },
            "friction": {"decision": "continue", "heaviest_level_bps": 20.0, "heaviest_level_sharpe": 1.04},
            "eth_cross_check": {"symbol": "ETHUSDT", "pass_rate": 0.0, "pass_count": 0, "total_count": 4},
            "shadow_decision": "shadow_ready_for_btc_only",
        },
    )
    (analysis_dir / "btc_1d_latest_summary_md_latest.md").write_text("# latest", encoding="utf-8")

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
    shutil.copyfile(
        paper_nightly["artifacts"]["summary_json"],
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
    )
    shutil.copyfile(
        paper_nightly["artifacts"]["summary_md"],
        analysis_dir / "btc_1d_paper_nightly_summary_md_latest.md",
    )

    seeded_attack_aliases = {
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        ),
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md_latest.md"
        ),
    }
    (
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md_latest.md"
    ).write_text("# handoff", encoding="utf-8")
    monkeypatch.setattr(
        shadow_update_script,
        "_publish_attack_challenger_outputs",
        lambda *, analysis_dir: seeded_attack_aliases,
    )

    result = refresh_operator_stack(analysis_dir=analysis_dir, sync_passes=2)
    operating_index_payload = json.loads(
        (analysis_dir / "btc_1d_operating_index_latest.json").read_text(encoding="utf-8")
    )
    operating_brief_payload = json.loads(
        (analysis_dir / "btc_1d_operating_brief_latest.json").read_text(encoding="utf-8")
    )
    operating_index_md = (
        analysis_dir / "btc_1d_operating_index_md_latest.md"
    ).read_text(encoding="utf-8")
    operating_brief_md = (
        analysis_dir / "btc_1d_operating_brief_md_latest.md"
    ).read_text(encoding="utf-8")

    assert result["refresh_summary"]["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert result["refresh_summary"]["attack_challenger_next_step"] == "deployment monitoring active"
    assert result["deployment_monitoring_active"] is True
    assert (
        result["refresh_summary"]["attack_challenger_bridge_report"].endswith(
            "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        )
    )
    assert result["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert result["attack_challenger_next_step"] == "deployment monitoring active"
    assert (
        result["attack_challenger_bridge_report"].endswith(
            "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        )
    )
    assert result["contract_health"][
        "attack_challenger_remote_monitoring_deployment_handoff_ready"
    ] is True
    assert (
        result["contract_health"]["attack_challenger_next_step"]
        == "deployment monitoring active"
    )
    assert (
        result["contract_health"]["attack_challenger_bridge_report"].endswith(
            "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        )
    )
    assert result["execution_contract_state"][
        "attack_challenger_remote_monitoring_deployment_handoff_ready"
    ] is True
    assert (
        result["execution_contract_state"]["attack_challenger_next_step"]
        == "deployment monitoring active"
    )
    assert (
        result["execution_contract_state"]["attack_challenger_bridge_report"].endswith(
            "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        )
    )
    assert result["refresh_summary"]["next_actions"] == ["deployment monitoring active"]
    assert (
        "attack_challenger_bridge_report="
        in result["refresh_summary"]["refresh_read"]
    )
    assert (
        result["latest_aliases"][
            "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff"
        ].endswith(
            "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        )
    )
    assert operating_index_payload[
        "attack_challenger_remote_monitoring_deployment_handoff_ready"
    ] is True
    assert operating_index_payload["attack_challenger_next_step"] == "deployment monitoring active"
    assert operating_index_payload["attack_challenger_bridge_report"].endswith(
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
    assert operating_brief_payload[
        "attack_challenger_remote_monitoring_deployment_handoff_ready"
    ] is True
    assert operating_brief_payload["attack_challenger_next_step"] == "deployment monitoring active"
    assert operating_brief_payload["attack_challenger_bridge_report"].endswith(
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
    assert "Attack challenger next step: `deployment monitoring active`" in operating_index_md
    assert (
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        in operating_index_md
    )
    assert "Attack challenger next step: `deployment monitoring active`" in operating_brief_md
    assert (
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        in operating_brief_md
    )
