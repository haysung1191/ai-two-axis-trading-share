from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
)
from scripts.run_btc_1d_shadow_update import (
    _build_shadow_update_output,
    main as run_shadow_update_main,
    _load_execution_contract_state,
    _load_attack_challenger_state,
    _normalize_attack_challenger_handoff_fields,
    _paper_summary_contract_bool,
    _refresh_contract_artifacts_after_paper,
    _render_combined_health_line,
    _render_execution_health_line,
    _latest_index,
    _publish_execution_outputs,
    _publish_attack_challenger_outputs,
    _publish_research_outputs,
    _latest_summary,
    _publish_practical_outputs,
    _write_operator_dashboard_artifacts,
    _write_operating_brief,
    _write_latest_aliases,
    _write_latest_index,
    _write_latest_summary,
    build_parser,
)
from scripts.run_bithumb_paper_nightly import render_paper_nightly_health_line


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_btc_1d_shadow_update_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.periods == 2200
    assert args.survivability_periods == 2600
    assert args.friction_periods == 2200
    assert args.walk_forward_periods == 2200
    assert args.eth_symbol == "ETHUSDT"
    assert args.fee_bps == 8.0
    assert args.slippage_bps == 8.0
    assert args.refresh_only is False
    assert args.sync_passes == 3


def test_btc_1d_shadow_update_refresh_only_parser() -> None:
    args = build_parser().parse_args(["--refresh-only", "--sync-passes", "5"])

    assert args.refresh_only is True
    assert args.sync_passes == 5


def test_normalize_attack_challenger_handoff_fields_prefers_refresh_summary() -> None:
    result = _normalize_attack_challenger_handoff_fields(
        refresh_summary={
            "deployment_monitoring_active": True,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": (
                "analysis_results\\"
                "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
            ),
        },
        target={
            "attack_challenger_remote_monitoring_deployment_handoff_ready": False,
            "attack_challenger_next_step": "stale step",
            "attack_challenger_bridge_report": "stale.json",
        },
    )

    assert result["deployment_monitoring_active"] is True
    assert result["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert (
        result["attack_challenger_next_step"]
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    )
    assert result["attack_challenger_bridge_report"] == (
        "analysis_results\\"
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )


def test_normalize_attack_challenger_handoff_fields_falls_back_to_target() -> None:
    result = _normalize_attack_challenger_handoff_fields(
        refresh_summary={},
        target={
            "deployment_monitoring_active": True,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": "target step",
            "attack_challenger_bridge_report": "target.json",
        },
    )

    assert result["deployment_monitoring_active"] is True
    assert result["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert result["attack_challenger_next_step"] == "target step"
    assert result["attack_challenger_bridge_report"] == "target.json"


def test_normalize_attack_challenger_handoff_fields_uses_empty_defaults_without_target() -> None:
    result = _normalize_attack_challenger_handoff_fields(
        refresh_summary={},
    )

    assert result["deployment_monitoring_active"] is False
    assert result["attack_challenger_remote_monitoring_deployment_handoff_ready"] is False
    assert result["attack_challenger_next_step"] == ""
    assert result["attack_challenger_bridge_report"] == ""


def test_btc_1d_shadow_update_refresh_only_main_emits_top_level_attack_challenger_fields(
    tmp_path: Path,
    monkeypatch,
) -> None:
    refresh_payload = {
        "analysis_dir": str(tmp_path / "analysis_results"),
        "sync_passes": 2,
        "refresh_summary": {
            "deployment_monitoring_active": True,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": (
                "analysis_results\\"
                "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
            ),
        },
        "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
        "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
        "attack_challenger_bridge_report": (
            "analysis_results\\"
            "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        ),
        "latest_aliases": {},
        "combined_health_line": "combined",
        "paper_nightly_health_line": "paper nightly",
        "execution_health_line": "execution",
        "contract_health": {
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": (
                "analysis_results\\"
                "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
            ),
        },
        "execution_contract_state": {
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": (
                "analysis_results\\"
                "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
            ),
        },
        "dashboard_summary": {},
    }

    monkeypatch.setattr(
        "scripts.run_btc_1d_shadow_update.refresh_operator_stack",
        lambda *, analysis_dir, sync_passes: refresh_payload,
    )

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = run_shadow_update_main(
            [
                "--analysis-dir",
                str(tmp_path / "analysis_results"),
                "--refresh-only",
                "--sync-passes",
                "2",
            ]
        )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["deployment_monitoring_active"] is True
    assert payload["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert (
        payload["attack_challenger_next_step"]
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    )
    assert payload["attack_challenger_bridge_report"] == (
        "analysis_results\\"
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )


def test_latest_summary_extracts_operating_read() -> None:
    summary = _latest_summary(
        shadow_packet={
            "candidate": "low_vol_cap_050_025_minvol020_p2200",
            "carry_reference_period": 2200,
            "survivability_reference_period": 2600,
            "paper_validation_decision": "PASS",
            "paper_validation_metrics": {"sharpe": 1.16, "cagr": 0.14, "max_drawdown": 0.10},
            "survivability_validation_decision": "PASS",
            "survivability_validation_metrics": {"sharpe": 1.15, "cagr": 0.15, "max_drawdown": 0.13},
            "friction_validation_decision": "continue",
            "friction_validation_heaviest_level": {"cost_bps": 20.0, "sharpe": 1.04},
            "shadow_decision": "shadow_ready_for_btc_only",
        },
        walk_forward={
            "overfitting": {
                "passed": True,
                "oos_metrics": {"sharpe": 0.82, "cagr": 0.05, "max_drawdown": 0.06},
                "sensitivity_max_drift": 0.09,
                "unstable_parameters": [],
            }
        },
        eth_regression={
            "summary": {"pass_rate": 0.0, "pass_count": 0, "total_count": 4},
        },
        eth_symbol="ETHUSDT",
    )

    assert summary["candidate"] == "low_vol_cap_050_025_minvol020_p2200"
    assert summary["carry"]["periods"] == 2200
    assert summary["walk_forward"]["oos_sharpe"] == 0.82
    assert summary["friction"]["heaviest_level_bps"] == 20.0
    assert summary["eth_cross_check"]["symbol"] == "ETHUSDT"


def test_write_latest_summary_creates_json_and_md(tmp_path: Path) -> None:
    summary = {
        "candidate": "low_vol_cap_050_025_minvol020_p2200",
        "scope": "BTC-only",
        "carry": {"periods": 2200, "decision": "PASS", "sharpe": 1.16, "cagr": 0.14, "max_drawdown": 0.10},
        "survivability": {"periods": 2600, "decision": "PASS", "sharpe": 1.15, "cagr": 0.15, "max_drawdown": 0.13},
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
    }

    result = _write_latest_summary(analysis_dir=tmp_path, summary=summary)

    json_payload = json.loads(Path(result["json"]).read_text(encoding="utf-8"))
    md_payload = Path(result["md"]).read_text(encoding="utf-8")

    assert json_payload["candidate"] == "low_vol_cap_050_025_minvol020_p2200"
    assert "BTC 1d Latest Summary" in md_payload


def test_render_combined_health_line_contains_practical_and_research() -> None:
    line = _render_combined_health_line(
        practical_health={
            "status_label": "btc_only_practical_with_caveats",
            "ok": True,
            "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
            "sharpe": 1.3946,
            "cagr": 0.3772,
            "max_drawdown": 0.1609,
            "caveat_count": 2,
            "caveats": ["a", "b"],
        },
        research_stack_health={
            "attack_frontier": "ratio112_tighter_stop_main",
            "attack_backup": "ratio111_tighter_stop_backup",
            "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
            "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
            "attack_frontier_cagr": 0.4243,
            "attack_frontier_max_drawdown": 0.1609,
            "attack_frontier_sharpe": 1.5613,
            "attack_backup_drift": 0.4172,
            "defensive_hold_status": "candidate_stage_hold",
            "near_miss_status": "validated_fail_hold",
        },
    )

    assert "BTC 1d practical health | status=btc_only_practical_with_caveats" in line
    assert "||" in line
    assert "BTC 1d research stack | frontier=ratio112_tighter_stop_main" in line


def test_load_attack_challenger_state_prefers_operator_runbook_candidate_entry(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_operator_runbook_candidate_entry_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "operator_runbook_candidate_entry_requirements": {
                "promotion_chain_still_green": True,
                "operator_stack_handoff_ready": True,
            },
            "operator_runbook_candidate_entry_verdict": {
                "operator_runbook_candidate_entry_ready": True,
                "operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue",
                "next_step_now": "operator_runbook_execution_entry",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_operator_runbook_candidate_entry_ready"] is True
    assert (
        state["attack_challenger_operator_runbook_candidate_entry_lane"]
        == "operator_runbook_candidate_queue"
    )
    assert state["attack_challenger_next_step"] == "operator_runbook_execution_entry"


def test_load_attack_challenger_state_prefers_operator_runbook_execution_entry(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_operator_runbook_execution_entry_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "operator_runbook_execution_entry_requirements": {
                "promotion_chain_still_green": True,
                "operator_runbook_candidate_entry_ready": True,
            },
            "operator_runbook_execution_entry_verdict": {
                "operator_runbook_execution_entry_ready": True,
                "operator_runbook_execution_entry_lane": "operator_runbook_execution_queue",
                "next_step_now": "challenger_shadow_monitoring_entry",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_operator_runbook_candidate_entry_ready"] is True
    assert state["attack_challenger_operator_runbook_execution_entry_ready"] is True
    assert (
        state["attack_challenger_operator_runbook_execution_entry_lane"]
        == "operator_runbook_execution_queue"
    )
    assert state["attack_challenger_next_step"] == "challenger_shadow_monitoring_entry"


def test_load_attack_challenger_state_prefers_shadow_monitoring_entry(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_shadow_monitoring_entry_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_shadow_monitoring_entry_requirements": {
                "promotion_chain_still_green": True,
                "operator_runbook_execution_entry_ready": True,
            },
            "challenger_shadow_monitoring_entry_verdict": {
                "challenger_shadow_monitoring_entry_ready": True,
                "challenger_shadow_monitoring_entry_lane": "challenger_shadow_monitoring_queue",
                "next_step_now": "challenger_candidate_live_readiness_review",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_operator_runbook_execution_entry_ready"] is True
    assert (
        state["attack_challenger_operator_runbook_execution_entry_lane"]
        == "challenger_shadow_monitoring_queue"
    )
    assert state["attack_challenger_live_readiness_review_ready"] is False
    assert state["attack_challenger_next_step"] == "challenger_candidate_live_readiness_review"


def test_load_attack_challenger_state_prefers_live_readiness_review(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_readiness_review_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_candidate_live_readiness_review_requirements": {
                "promotion_chain_still_green": True,
                "challenger_shadow_monitoring_entry_ready": True,
            },
            "challenger_candidate_live_readiness_review_verdict": {
                "challenger_candidate_live_readiness_review_ready": True,
                "challenger_candidate_live_readiness_review_lane": "challenger_live_readiness_review_queue",
                "next_step_now": "challenger_live_shadow_activation_review",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_operator_runbook_execution_entry_ready"] is True
    assert (
        state["attack_challenger_operator_runbook_execution_entry_lane"]
        == "challenger_shadow_monitoring_queue"
    )
    assert state["attack_challenger_live_readiness_review_ready"] is True
    assert (
        state["attack_challenger_live_readiness_review_lane"]
        == "challenger_live_readiness_review_queue"
    )
    assert state["attack_challenger_live_shadow_activation_review_ready"] is False
    assert state["attack_challenger_next_step"] == "challenger_live_shadow_activation_review"


def test_publish_attack_challenger_outputs_runs_release_chain(
    tmp_path: Path,
    monkeypatch,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    calls: list[tuple[str, Path]] = []

    def _stub(name: str):
        def _run() -> int:
            calls.append((name, analysis_dir))
            return 0

        return _run

    monkeypatch.setattr(
        "scripts.run_btc_1d_shadow_update.live_shadow_locked_release_entry_script.main",
        _stub("entry"),
    )
    monkeypatch.setattr(
        "scripts.run_btc_1d_shadow_update.live_shadow_locked_release_candidate_review_script.main",
        _stub("candidate_review"),
    )
    monkeypatch.setattr(
        "scripts.run_btc_1d_shadow_update.live_shadow_locked_release_governance_check_script.main",
        _stub("governance_check"),
    )
    monkeypatch.setattr(
        "scripts.run_btc_1d_shadow_update.live_shadow_locked_release_governance_entry_script.main",
        _stub("governance_entry"),
    )
    monkeypatch.setattr(
        "scripts.run_btc_1d_shadow_update.remote_monitoring_deployment_handoff_script.main",
        _stub("remote_handoff"),
    )

    paths = _publish_attack_challenger_outputs(analysis_dir=analysis_dir)

    assert calls == [
        ("entry", analysis_dir),
        ("candidate_review", analysis_dir),
        ("governance_check", analysis_dir),
        ("governance_entry", analysis_dir),
        ("remote_handoff", analysis_dir),
    ]
    assert paths[
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_candidate_review"
    ].endswith(
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_candidate_review_latest.json"
    )
    assert paths[
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry"
    ].endswith(
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry_latest.json"
    )
    assert paths[
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff"
    ].endswith(
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )


def test_load_attack_challenger_state_prefers_remote_monitoring_deployment_handoff(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    handoff_path = (
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
    _write_json(
        handoff_path,
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
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
                "promotion_chain_still_green": True,
            },
            "remote_monitoring_deployment_handoff_verdict": {
                "remote_monitoring_deployment_handoff_ready": True,
                "remote_monitoring_deployment_handoff_lane": ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
                "next_step_now": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert (
        state["attack_challenger_remote_monitoring_deployment_handoff_lane"]
        == ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE
    )
    assert state["attack_challenger_live_shadow_locked_release_governance_entry_ready"] is True
    assert (
        state["attack_challenger_next_step"]
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    )
    assert state["attack_challenger_bridge_report"] == str(handoff_path)


def test_load_attack_challenger_state_prefers_live_shadow_activation_review(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_activation_review_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_activation_review_requirements": {
                "promotion_chain_still_green": True,
                "challenger_candidate_live_readiness_review_ready": True,
            },
            "challenger_live_shadow_activation_review_verdict": {
                "challenger_live_shadow_activation_review_ready": True,
                "challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue",
                "next_step_now": "challenger_live_candidate_entry",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_live_readiness_review_ready"] is True
    assert (
        state["attack_challenger_live_readiness_review_lane"]
        == "challenger_live_readiness_review_queue"
    )
    assert state["attack_challenger_live_shadow_activation_review_ready"] is True
    assert (
        state["attack_challenger_live_shadow_activation_review_lane"]
        == "challenger_live_shadow_activation_queue"
    )
    assert state["attack_challenger_next_step"] == "challenger_live_candidate_entry"


def test_load_attack_challenger_state_prefers_live_candidate_entry(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_candidate_entry_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_candidate_entry_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_shadow_activation_review_ready": True,
            },
            "challenger_live_candidate_entry_verdict": {
                "challenger_live_candidate_entry_ready": True,
                "challenger_live_candidate_entry_lane": "challenger_live_candidate_queue",
                "next_step_now": "challenger_live_operator_paper_entry",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_live_shadow_activation_review_ready"] is True
    assert (
        state["attack_challenger_live_shadow_activation_review_lane"]
        == "challenger_live_shadow_activation_queue"
    )
    assert state["attack_challenger_live_candidate_entry_ready"] is True
    assert (
        state["attack_challenger_live_candidate_entry_lane"]
        == "challenger_live_candidate_queue"
    )
    assert state["attack_challenger_next_step"] == "challenger_live_operator_paper_entry"


def test_load_attack_challenger_state_prefers_live_operator_paper_entry(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_operator_paper_entry_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_operator_paper_entry_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_candidate_entry_ready": True,
            },
            "challenger_live_operator_paper_entry_verdict": {
                "challenger_live_operator_paper_entry_ready": True,
                "challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue",
                "next_step_now": "challenger_live_shadow_governance_review",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_live_candidate_entry_ready"] is True
    assert (
        state["attack_challenger_live_candidate_entry_lane"]
        == "challenger_live_candidate_queue"
    )
    assert state["attack_challenger_live_operator_paper_entry_ready"] is True
    assert (
        state["attack_challenger_live_operator_paper_entry_lane"]
        == "challenger_live_operator_paper_queue"
    )
    assert state["attack_challenger_next_step"] == "challenger_live_shadow_governance_review"


def test_load_attack_challenger_state_prefers_live_shadow_governance_review(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_governance_review_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_governance_review_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_operator_paper_entry_ready": True,
            },
            "challenger_live_shadow_governance_review_verdict": {
                "challenger_live_shadow_governance_review_ready": True,
                "challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue",
                "next_step_now": "challenger_live_governed_shadow_entry",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_live_operator_paper_entry_ready"] is True
    assert (
        state["attack_challenger_live_operator_paper_entry_lane"]
        == "challenger_live_operator_paper_queue"
    )
    assert state["attack_challenger_live_shadow_governance_review_ready"] is True
    assert (
        state["attack_challenger_live_shadow_governance_review_lane"]
        == "challenger_live_shadow_governance_queue"
    )
    assert state["attack_challenger_next_step"] == "challenger_live_governed_shadow_entry"


def test_load_attack_challenger_state_prefers_live_governed_shadow_entry(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_governed_shadow_entry_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_governed_shadow_entry_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_shadow_governance_review_ready": True,
            },
            "challenger_live_governed_shadow_entry_verdict": {
                "challenger_live_governed_shadow_entry_ready": True,
                "challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue",
                "next_step_now": "challenger_live_shadow_candidate_paper_review",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_live_shadow_governance_review_ready"] is True
    assert (
        state["attack_challenger_live_shadow_governance_review_lane"]
        == "challenger_live_shadow_governance_queue"
    )
    assert state["attack_challenger_live_governed_shadow_entry_ready"] is True
    assert (
        state["attack_challenger_live_governed_shadow_entry_lane"]
        == "challenger_live_governed_shadow_queue"
    )
    assert state["attack_challenger_next_step"] == "challenger_live_shadow_candidate_paper_review"


def test_load_attack_challenger_state_prefers_live_shadow_candidate_paper_review(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_candidate_paper_review_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_candidate_paper_review_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_governed_shadow_entry_ready": True,
            },
            "challenger_live_shadow_candidate_paper_review_verdict": {
                "challenger_live_shadow_candidate_paper_review_ready": True,
                "challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue",
                "next_step_now": "challenger_live_shadow_candidate_governance_lock",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_live_governed_shadow_entry_ready"] is True
    assert state["attack_challenger_live_shadow_candidate_paper_review_ready"] is True
    assert (
        state["attack_challenger_live_shadow_candidate_paper_review_lane"]
        == "challenger_live_shadow_candidate_paper_queue"
    )
    assert state["attack_challenger_next_step"] == "challenger_live_shadow_candidate_governance_lock"


def test_load_attack_challenger_state_prefers_live_shadow_candidate_governance_lock(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_candidate_governance_lock_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_candidate_governance_lock_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_shadow_candidate_paper_review_ready": True,
            },
            "challenger_live_shadow_candidate_governance_lock_verdict": {
                "challenger_live_shadow_candidate_governance_lock_ready": True,
                "challenger_live_shadow_candidate_governance_lock_lane": "challenger_live_shadow_candidate_governance_lock_queue",
                "next_step_now": "challenger_live_shadow_locked_entry",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_live_shadow_candidate_paper_review_ready"] is True
    assert state["attack_challenger_live_shadow_candidate_governance_lock_ready"] is True
    assert (
        state["attack_challenger_live_shadow_candidate_governance_lock_lane"]
        == "challenger_live_shadow_candidate_governance_lock_queue"
    )
    assert state["attack_challenger_next_step"] == "challenger_live_shadow_locked_entry"


def test_load_attack_challenger_state_prefers_live_shadow_locked_entry(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_entry_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_locked_entry_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_shadow_candidate_governance_lock_ready": True,
            },
            "challenger_live_shadow_locked_entry_verdict": {
                "challenger_live_shadow_locked_entry_ready": True,
                "challenger_live_shadow_locked_entry_lane": "challenger_live_shadow_locked_queue",
                "next_step_now": "challenger_live_shadow_locked_candidate_review",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_live_shadow_candidate_governance_lock_ready"] is True
    assert state["attack_challenger_live_shadow_locked_entry_ready"] is True
    assert (
        state["attack_challenger_live_shadow_locked_entry_lane"]
        == "challenger_live_shadow_locked_queue"
    )
    assert state["attack_challenger_next_step"] == "challenger_live_shadow_locked_candidate_review"


def test_load_attack_challenger_state_prefers_live_shadow_locked_candidate_review(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_candidate_review_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_locked_candidate_review_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_shadow_locked_entry_ready": True,
            },
            "challenger_live_shadow_locked_candidate_review_verdict": {
                "challenger_live_shadow_locked_candidate_review_ready": True,
                "challenger_live_shadow_locked_candidate_review_lane": "challenger_live_shadow_locked_candidate_review_queue",
                "next_step_now": "challenger_live_shadow_locked_candidate_release_review",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_live_shadow_locked_entry_ready"] is True
    assert state["attack_challenger_live_shadow_locked_candidate_review_ready"] is True
    assert (
        state["attack_challenger_live_shadow_locked_candidate_review_lane"]
        == "challenger_live_shadow_locked_candidate_review_queue"
    )
    assert (
        state["attack_challenger_next_step"]
        == "challenger_live_shadow_locked_candidate_release_review"
    )


def test_load_attack_challenger_state_prefers_live_shadow_locked_candidate_release_review(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_candidate_release_review_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_locked_candidate_release_review_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_shadow_locked_candidate_review_ready": True,
            },
            "challenger_live_shadow_locked_candidate_release_review_verdict": {
                "challenger_live_shadow_locked_candidate_release_review_ready": True,
                "challenger_live_shadow_locked_candidate_release_review_lane": "challenger_live_shadow_locked_candidate_release_review_queue",
                "next_step_now": "challenger_live_shadow_locked_release_entry",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_live_shadow_locked_candidate_review_ready"] is True
    assert (
        state["attack_challenger_live_shadow_locked_candidate_release_review_ready"]
        is True
    )
    assert (
        state["attack_challenger_live_shadow_locked_candidate_release_review_lane"]
        == "challenger_live_shadow_locked_candidate_release_review_queue"
    )
    assert state["attack_challenger_next_step"] == "challenger_live_shadow_locked_release_entry"


def test_load_attack_challenger_state_prefers_live_shadow_locked_release_entry(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_entry_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_locked_release_entry_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_shadow_locked_candidate_release_review_ready": True,
            },
            "challenger_live_shadow_locked_release_entry_verdict": {
                "challenger_live_shadow_locked_release_entry_ready": True,
                "challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue",
                "next_step_now": "challenger_live_shadow_locked_release_candidate_review",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert (
        state["attack_challenger_live_shadow_locked_candidate_release_review_ready"]
        is True
    )
    assert state["attack_challenger_live_shadow_locked_release_entry_ready"] is True
    assert (
        state["attack_challenger_live_shadow_locked_release_entry_lane"]
        == "challenger_live_shadow_locked_release_queue"
    )
    assert (
        state["attack_challenger_next_step"]
        == "challenger_live_shadow_locked_release_candidate_review"
    )


def test_load_attack_challenger_state_prefers_live_shadow_locked_release_candidate_review(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_candidate_review_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_locked_release_candidate_review_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_shadow_locked_release_entry_ready": True,
            },
            "challenger_live_shadow_locked_release_candidate_review_verdict": {
                "challenger_live_shadow_locked_release_candidate_review_ready": True,
                "challenger_live_shadow_locked_release_candidate_review_lane": "challenger_live_shadow_locked_release_candidate_review_queue",
                "next_step_now": "challenger_live_shadow_locked_release_governance_check",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_live_shadow_locked_release_entry_ready"] is True
    assert (
        state["attack_challenger_live_shadow_locked_release_candidate_review_ready"]
        is True
    )
    assert (
        state["attack_challenger_live_shadow_locked_release_candidate_review_lane"]
        == "challenger_live_shadow_locked_release_candidate_review_queue"
    )
    assert (
        state["attack_challenger_next_step"]
        == "challenger_live_shadow_locked_release_governance_check"
    )


def test_load_attack_challenger_state_prefers_live_shadow_locked_release_governance_check(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_check_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_locked_release_governance_check_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_shadow_locked_release_candidate_review_ready": True,
            },
            "challenger_live_shadow_locked_release_governance_check_verdict": {
                "challenger_live_shadow_locked_release_governance_check_ready": True,
                "challenger_live_shadow_locked_release_governance_check_lane": "challenger_live_shadow_locked_release_governance_check_queue",
                "next_step_now": "challenger_live_shadow_locked_release_governance_entry",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_live_shadow_locked_release_candidate_review_ready"] is True
    assert state["attack_challenger_live_shadow_locked_release_governance_check_ready"] is True
    assert (
        state["attack_challenger_live_shadow_locked_release_governance_check_lane"]
        == "challenger_live_shadow_locked_release_governance_check_queue"
    )
    assert (
        state["attack_challenger_next_step"]
        == "challenger_live_shadow_locked_release_governance_entry"
    )


def test_load_attack_challenger_state_prefers_live_shadow_locked_release_governance_entry(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "challenger_live_shadow_locked_release_governance_entry_requirements": {
                "promotion_chain_still_green": True,
                "challenger_live_shadow_locked_release_governance_check_ready": True,
            },
            "challenger_live_shadow_locked_release_governance_entry_verdict": {
                "challenger_live_shadow_locked_release_governance_entry_ready": True,
                "challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue",
                "next_step_now": "remote monitoring and deployment handoff",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_live_shadow_locked_release_governance_check_ready"] is True
    assert state["attack_challenger_live_shadow_locked_release_governance_entry_ready"] is True
    assert (
        state["attack_challenger_live_shadow_locked_release_governance_entry_lane"]
        == "challenger_live_shadow_locked_release_governance_entry_queue"
    )
    assert state["attack_challenger_next_step"] == "remote monitoring and deployment handoff"


def test_render_execution_health_line_appends_paper_nightly_when_present() -> None:
    line = _render_execution_health_line(
        combined_health_line="BTC 1d practical health ... || BTC 1d research stack ...",
        paper_nightly_health_line="BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=0 | open=1",
    )

    assert line == (
        "BTC 1d practical health ... || BTC 1d research stack ... || "
        "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=0 | open=1"
    )


def test_paper_summary_contract_bool_prefers_nightly_self_check_field() -> None:
    summary = {
        "paper_execution_contract_checked_aligned": False,
        "execution_contract_paper_execution_contract_checked_aligned": True,
    }

    assert (
        _paper_summary_contract_bool(
            summary,
            "paper_execution_contract_checked_aligned",
            "execution_contract_paper_execution_contract_checked_aligned",
        )
        is False
    )


def test_build_shadow_update_output_includes_contract_health() -> None:
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
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
        },
        contract_health_line=(
            "BTC 1d contract health | operating_brief=operating_v3 | "
            "operating_index=operating_v3 | aligned=True | research=research_stack_v2 | "
            "distinct=True | partitioned=True"
        ),
        regression_lock_test="tests/unit/test_btc_1d_operating_cli_help_contract.py",
        combined_health_line="BTC 1d practical health ... || BTC 1d research stack ...",
        paper_nightly_health_line="BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=0 | open=1",
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
        latest_aliases={
            "btc_1d_operating_index": "analysis_results\\btc_1d_operating_index_latest.json",
            "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
        },
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
    )

    assert payload["contract_health"]["operating_brief_version"] == "operating_v3"
    assert payload["contract_health_line"].startswith("BTC 1d contract health | operating_brief=operating_v3")
    assert (
        payload["contract_health"]["attack_challenger_bridge_report"]
        == "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
    assert payload["contract_health_operating_contract_aligned"] is True
    assert payload["contract_health_paper_execution_contract_aligned"] is True
    assert payload["contract_health_aligned"] is True
    assert payload["contract_health_contracts_are_well_partitioned"] is True
    assert payload["regression_lock_test"] == "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    assert payload["combined_health_line"] == "BTC 1d practical health ... || BTC 1d research stack ..."
    assert payload["paper_nightly_health_line"].startswith("BTC 1d paper nightly | track=operating")
    assert payload["execution_health_line"].startswith("BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly")
    assert payload["execution_contract_health_line"].endswith("execution contract | aligned | paper execution | track=operating | applied=1 | closed=0 | open=1")
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
    assert payload["paper_execution_read"] == "paper execution | track=operating | applied=1 | closed=0 | open=1"
    assert payload["paper_exit_duplicate_run"] is False
    assert payload["paper_ledger_consistent"] is True
    assert payload["paper_ledger_snapshot_read"] == "paper ledger | open=1 | closed=0 | exit_fills=0 | orders=0 | fills=0"


def test_write_latest_aliases_creates_fixed_name_copies(tmp_path: Path) -> None:
    source_json = tmp_path / "btc_1d_shadow_packet_20260414T000000Z.json"
    source_md = tmp_path / "btc_1d_shadow_packet_20260414T000000Z.md"
    source_json.write_text('{"ok": true}', encoding="utf-8")
    source_md.write_text("# ok", encoding="utf-8")

    result = _write_latest_aliases(
        analysis_dir=tmp_path,
        paths={
            "btc_1d_shadow_packet": str(source_json),
            "btc_1d_shadow_packet_md": str(source_md),
            "btc_1d_low_vol_cap_friction_md": "",
        },
    )

    alias_json_path = Path(result["btc_1d_shadow_packet"])
    alias_md_path = Path(result["btc_1d_shadow_packet_md"])
    assert alias_json_path.name == "btc_1d_shadow_packet_latest.json"
    assert alias_json_path.read_text(encoding="utf-8") == '{"ok": true}'
    assert alias_md_path.name == "btc_1d_shadow_packet_md_latest.md"
    assert alias_md_path.read_text(encoding="utf-8") == "# ok"
    assert "btc_1d_low_vol_cap_friction_md" not in result


def test_write_latest_index_creates_json_and_md(tmp_path: Path) -> None:
    summary = {
        "candidate": "low_vol_cap_050_025_minvol020_p2200",
        "scope": "BTC-only",
        "shadow_decision": "shadow_ready_for_btc_only",
        "carry": {"periods": 2200, "decision": "PASS", "sharpe": 1.16, "cagr": 0.14, "max_drawdown": 0.10},
        "survivability": {"periods": 2600, "decision": "PASS", "sharpe": 1.15, "cagr": 0.15, "max_drawdown": 0.13},
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
    }
    practical_gate_path = tmp_path / "btc_1d_practical_promotion_gate_latest.json"
    _write_json(
        practical_gate_path,
        {
            "decision": "btc_only_practical_with_caveats",
            "status_label": "btc_only_practical_with_caveats",
            "ok": True,
            "caveats": ["dsr weak", "range weak"],
        },
    )
    aliases = {
        "btc_1d_operating_brief": "analysis_results\\btc_1d_operating_brief_latest.json",
        "btc_1d_operating_brief_txt": "analysis_results\\btc_1d_operating_brief_txt_latest.txt",
        "btc_1d_operating_brief_md": "analysis_results\\btc_1d_operating_brief_md_latest.md",
        "btc_1d_practical_scorecard": "analysis_results\\btc_1d_practical_scorecard_latest.json",
        "btc_1d_practical_scorecard_md": "analysis_results\\btc_1d_practical_scorecard_md_latest.md",
        "btc_1d_practical_promotion_gate": str(practical_gate_path),
        "btc_1d_practical_promotion_gate_md": "analysis_results\\btc_1d_practical_promotion_gate_md_latest.md",
        "btc_1d_research_stack_operating_brief": "analysis_results\\btc_1d_research_stack_operating_brief_latest.json",
        "btc_1d_research_stack_operating_brief_md": "analysis_results\\btc_1d_research_stack_operating_brief_md_latest.md",
        "btc_1d_quick_read_contract_screen": "analysis_results\\btc_1d_quick_read_contract_screen_latest.json",
        "btc_1d_quick_read_contract_screen_md": "analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md",
        "btc_1d_execution_contract_screen": "analysis_results\\btc_1d_execution_contract_screen_latest.json",
        "btc_1d_execution_contract_screen_md": "analysis_results\\btc_1d_execution_contract_screen_md_latest.md",
        "btc_1d_meta_contract_screen": "analysis_results\\btc_1d_meta_contract_screen_latest.json",
        "btc_1d_meta_contract_screen_md": "analysis_results\\btc_1d_meta_contract_screen_md_latest.md",
        "btc_1d_paper_nightly_summary": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
        "btc_1d_paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
        "btc_1d_latest_summary": "analysis_results\\btc_1d_latest_summary_latest.json",
        "btc_1d_latest_summary_md": "analysis_results\\btc_1d_latest_summary_md_latest.md",
        "btc_1d_shadow_packet": "analysis_results\\btc_1d_shadow_packet_latest.json",
        "btc_1d_shadow_packet_md": "analysis_results\\btc_1d_shadow_packet_md_latest.md",
        "btc_1d_candidate_status_board": "analysis_results\\btc_1d_candidate_status_board_latest.json",
        "btc_1d_candidate_status_board_md": "analysis_results\\btc_1d_candidate_status_board_md_latest.md",
        "btc_1d_baseline_freeze": "analysis_results\\btc_1d_baseline_freeze_latest.json",
        "btc_1d_baseline_freeze_md": "analysis_results\\btc_1d_baseline_freeze_md_latest.md",
        "btc_1d_shadow_readiness": "analysis_results\\btc_1d_shadow_readiness_latest.json",
        "btc_1d_shadow_readiness_md": "analysis_results\\btc_1d_shadow_readiness_md_latest.md",
        "btc_1d_walk_forward_diagnostic": "analysis_results\\btc_1d_walk_forward_diagnostic_latest.json",
        "btc_1d_walk_forward_diagnostic_md": "analysis_results\\btc_1d_walk_forward_diagnostic_md_latest.md",
        "btc_1d_low_vol_cap_friction": "analysis_results\\btc_1d_low_vol_cap_friction_latest.json",
        "btc_1d_low_vol_cap_friction_md": "analysis_results\\btc_1d_low_vol_cap_friction_md_latest.md",
    }

    index_payload = _latest_index(
        summary=summary,
        latest_aliases=aliases,
        contract_health={
            "operating_contract_aligned": True,
            "paper_execution_contract_aligned": True,
            "contract_health_aligned": True,
            "contracts_are_well_partitioned": True,
        },
        research_stack_health_line=(
            "BTC 1d research stack | frontier=ratio112_tighter_stop_main | "
            "backup=ratio111_tighter_stop_backup | defensive=volatility_expansion_pullthrough_shorter_hold"
        ),
        combined_health_line=(
            "BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | "
            "candidate=low_vol_cap_050_025_minvol020_p2200 | sharpe=1.1600 | cagr=14.00% | mdd=10.00% | caveats=2 "
            "|| BTC 1d research stack | frontier=ratio112_tighter_stop_main"
        ),
        paper_nightly_health_line=(
            "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0"
        ),
        execution_health_line=(
            "BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | "
            "candidate=low_vol_cap_050_025_minvol020_p2200 | sharpe=1.1600 | cagr=14.00% | mdd=10.00% | caveats=2 "
            "|| BTC 1d research stack | frontier=ratio112_tighter_stop_main || "
            "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0"
        ),
        execution_contract_health_line=(
            "BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | "
            "candidate=low_vol_cap_050_025_minvol020_p2200 | sharpe=1.1600 | cagr=14.00% | mdd=10.00% | caveats=2 "
            "|| BTC 1d research stack | frontier=ratio112_tighter_stop_main || "
            "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0 || "
            "execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0"
        ),
        execution_contract_read="execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0",
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
        paper_execution_read="paper execution | track=operating | applied=1 | closed=1 | open=0",
        paper_exit_duplicate_run=True,
        paper_ledger_consistent=True,
        paper_ledger_snapshot={"open_position_count": 0, "closed_position_count": 1},
        attack_challenger_candidate="pullthrough_asymmetric_release_tighter_exit",
        attack_challenger_role_assignment="attack_challenger_candidate",
        attack_challenger_promotion_ready=True,
        attack_challenger_bridge_entry_ready=True,
        attack_challenger_bridge_queue_lane="attack_challenger_queue",
        attack_challenger_execution_contract_entry_ready=True,
        attack_challenger_execution_contract_queue_lane="challenger_execution_contract_queue",
        attack_challenger_operator_stack_handoff_ready=True,
        attack_challenger_operator_stack_handoff_lane="operator_stack_handoff_queue",
        attack_challenger_next_step=ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
        attack_challenger_paper_validation_cagr=0.2712,
        attack_challenger_paper_validation_max_drawdown=0.16,
        attack_challenger_walk_forward_sensitivity_max_drift=0.0928,
        attack_challenger_friction_final_decision="continue",
        attack_challenger_remote_monitoring_deployment_handoff_ready=True,
        attack_challenger_remote_monitoring_deployment_handoff_lane=ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
        attack_challenger_bridge_report="analysis_results\\btc_1d_pullthrough_asymmetric_release_promotion_bridge_latest.json",
    )
    result = _write_latest_index(analysis_dir=tmp_path, index_payload=index_payload)

    json_payload = json.loads(Path(result["json"]).read_text(encoding="utf-8"))
    md_payload = Path(result["md"]).read_text(encoding="utf-8")

    assert json_payload["candidate"] == "low_vol_cap_050_025_minvol020_p2200"
    assert json_payload["operator_verdict"] == "shadow_monitoring_ready"
    assert json_payload["standard_check_order"] == ["practical", "research", "contract", "brief"]
    assert json_payload["regression_lock_test"] == "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    assert json_payload["quick_read_order_version"] == "operating_v3"
    assert json_payload["quick_read_order"] == [
        "practical_status",
        "combined_health",
        "research_stack_status",
        "carry",
        "survivability",
        "walk_forward",
        "friction",
        "eth_cross_check",
        "quick_read_contract",
        "open_first",
    ]
    assert json_payload["operating_brief"] == "analysis_results\\btc_1d_operating_brief_latest.json"
    assert json_payload["operating_brief_txt"] == "analysis_results\\btc_1d_operating_brief_txt_latest.txt"
    assert json_payload["operating_brief_md"] == "analysis_results\\btc_1d_operating_brief_md_latest.md"
    assert json_payload["practical_status_label"] == "btc_only_practical_with_caveats"
    assert json_payload["practical_scorecard"] == "analysis_results\\btc_1d_practical_scorecard_latest.json"
    assert json_payload["practical_promotion_gate_md"] == "analysis_results\\btc_1d_practical_promotion_gate_md_latest.md"
    assert json_payload["research_stack_operating_brief"] == "analysis_results\\btc_1d_research_stack_operating_brief_latest.json"
    assert json_payload["research_stack_operating_brief_md"] == "analysis_results\\btc_1d_research_stack_operating_brief_md_latest.md"
    assert json_payload["quick_read_contract_screen"] == "analysis_results\\btc_1d_quick_read_contract_screen_latest.json"
    assert json_payload["quick_read_contract_screen_md"] == "analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md"
    assert json_payload["execution_contract_screen"] == "analysis_results\\btc_1d_execution_contract_screen_latest.json"
    assert json_payload["execution_contract_screen_md"] == "analysis_results\\btc_1d_execution_contract_screen_md_latest.md"
    assert json_payload["meta_contract_screen"] == "analysis_results\\btc_1d_meta_contract_screen_latest.json"
    assert json_payload["meta_contract_screen_md"] == "analysis_results\\btc_1d_meta_contract_screen_md_latest.md"
    assert json_payload["paper_nightly_summary"] == "analysis_results\\btc_1d_paper_nightly_summary_latest.json"
    assert json_payload["paper_nightly_summary_md"] == "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md"
    assert json_payload["practical"]["decision"] == "btc_only_practical_with_caveats"
    assert json_payload["practical"]["status_label"] == "btc_only_practical_with_caveats"
    assert json_payload["practical"]["caveat_count"] == 2
    assert json_payload["combined_health_line"].startswith("BTC 1d practical health | status=btc_only_practical_with_caveats")
    assert json_payload["execution_health_line"].startswith("BTC 1d practical health | status=btc_only_practical_with_caveats")
    assert json_payload["execution_contract_health_line"].endswith("execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0")
    assert json_payload["execution_contract_read"] == "execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0"
    assert json_payload["execution_contract_aligned"] is True
    assert json_payload["execution_contract_paper_ledger_snapshot_summary_aligned"] is True
    assert json_payload["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert json_payload["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert json_payload["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert json_payload["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert json_payload["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert json_payload["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert json_payload["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert json_payload["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert json_payload["paper_execution_contract_checked"] is True
    assert json_payload["paper_execution_contract_aligned"] is True
    assert json_payload["paper_execution_contract_checked_aligned"] is True
    assert json_payload["paper_execution_contract_aligned_aligned"] is True
    assert json_payload["paper_execution_contract_checked_summary_aligned"] is True
    assert json_payload["paper_execution_contract_aligned_summary_aligned"] is True
    assert json_payload["paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert json_payload["paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert json_payload["paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert json_payload["paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert json_payload["paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert json_payload["paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert json_payload["paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert json_payload["paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert json_payload["paper_execution_read"] == "paper execution | track=operating | applied=1 | closed=1 | open=0"
    assert json_payload["paper_exit_duplicate_run"] is True
    assert json_payload["paper_ledger_consistent"] is True
    assert json_payload["paper_ledger_snapshot"]["closed_position_count"] == 1
    assert json_payload["paper_ledger_snapshot_read"] == "paper ledger | open=0 | closed=1 | exit_fills=0 | orders=0 | fills=0"
    assert json_payload["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert json_payload["attack_challenger_role_assignment"] == "attack_challenger_candidate"
    assert json_payload["attack_challenger_promotion_ready"] is True
    assert json_payload["attack_challenger_bridge_entry_ready"] is True
    assert json_payload["attack_challenger_bridge_queue_lane"] == "attack_challenger_queue"
    assert json_payload["attack_challenger_execution_contract_entry_ready"] is True
    assert json_payload["attack_challenger_execution_contract_queue_lane"] == "challenger_execution_contract_queue"
    assert json_payload["attack_challenger_operator_stack_handoff_ready"] is True
    assert json_payload["attack_challenger_operator_stack_handoff_lane"] == "operator_stack_handoff_queue"
    assert (
        json_payload["attack_challenger_next_step"]
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    )
    assert json_payload["deployment_monitoring_active"] is True
    assert json_payload["research_stack_status"].startswith("BTC 1d research stack | frontier=ratio112_tighter_stop_main")
    assert json_payload["research_stack_health_line"].startswith("BTC 1d research stack | frontier=ratio112_tighter_stop_main")
    assert json_payload["paper_nightly_health_line"].startswith("BTC 1d paper nightly | track=operating")
    assert json_payload["shadow_packet_md"] == "analysis_results\\btc_1d_shadow_packet_md_latest.md"
    assert "BTC 1d Operating Index" in md_payload
    assert "Operator verdict: `shadow_monitoring_ready`" in md_payload
    assert "Deployment monitoring active: `True`" in md_payload
    assert "## Standard Check Order" in md_payload
    assert "1. Practical" in md_payload
    assert "2. Research" in md_payload
    assert "3. Contract" in md_payload
    assert "4. Brief" in md_payload
    assert "Regression lock: `tests/unit/test_btc_1d_operating_cli_help_contract.py`" in md_payload
    assert "Execution health: `BTC 1d practical health | status=btc_only_practical_with_caveats" in md_payload
    assert "Execution contract read: `execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`" in md_payload
    assert "Execution contract aligned: `True`" in md_payload
    assert "Execution contract paper ledger snapshot summary aligned: `True`" in md_payload
    assert "Execution contract paper execution contract checked aligned entry aligned: `True`" in md_payload
    assert "Execution contract paper execution contract aligned aligned entry aligned: `True`" in md_payload
    assert "Execution contract paper execution contract checked summary aligned entry aligned: `True`" in md_payload
    assert "Execution contract paper execution contract aligned summary aligned entry aligned: `True`" in md_payload
    assert "Execution contract paper execution contract checked aligned summary aligned: `True`" in md_payload
    assert "Execution contract paper execution contract aligned aligned summary aligned: `True`" in md_payload
    assert "Execution contract paper execution contract checked summary aligned summary aligned: `True`" in md_payload
    assert "Execution contract paper execution contract aligned summary aligned summary aligned: `True`" in md_payload
    assert "Paper execution contract checked: `True`" in md_payload
    assert "Paper execution contract aligned: `True`" in md_payload
    assert "Paper execution contract checked aligned: `True`" in md_payload
    assert "Paper execution contract aligned aligned: `True`" in md_payload
    assert "Paper execution contract checked summary aligned: `True`" in md_payload
    assert "Paper execution contract aligned summary aligned: `True`" in md_payload
    assert "Paper execution contract checked aligned entry aligned: `True`" in md_payload
    assert "Paper execution contract aligned aligned entry aligned: `True`" in md_payload
    assert "Paper execution contract checked summary aligned entry aligned: `True`" in md_payload
    assert "Paper execution contract aligned summary aligned entry aligned: `True`" in md_payload
    assert "Paper execution contract checked aligned summary aligned: `True`" in md_payload
    assert "Paper execution contract aligned aligned summary aligned: `True`" in md_payload
    assert "Paper execution contract checked summary aligned summary aligned: `True`" in md_payload
    assert "Paper execution contract aligned summary aligned summary aligned: `True`" in md_payload
    assert "Attack challenger: `pullthrough_asymmetric_release_tighter_exit`" in md_payload
    assert "Attack challenger role: `attack_challenger_candidate`" in md_payload
    assert "Attack challenger promotion ready: `True`" in md_payload
    assert "Attack challenger bridge entry ready: `True`" in md_payload
    assert "Attack challenger queue lane: `attack_challenger_queue`" in md_payload
    assert "Attack challenger execution contract entry ready: `True`" in md_payload
    assert "Attack challenger execution contract queue lane: `challenger_execution_contract_queue`" in md_payload
    assert "Attack challenger operator stack handoff ready: `True`" in md_payload
    assert "Attack challenger operator stack handoff lane: `operator_stack_handoff_queue`" in md_payload
    assert (
        "Attack challenger next step: "
        f"`{ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP}`"
    ) in md_payload
    assert "Practical status: `btc_only_practical_with_caveats`" in md_payload
    assert "Combined health: `BTC 1d practical health | status=btc_only_practical_with_caveats" in md_payload
    assert "Research stack status: `BTC 1d research stack | frontier=ratio112_tighter_stop_main" in md_payload
    assert "Paper nightly: `BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0`" in md_payload
    assert "Paper exit duplicate run: `True`" in md_payload
    assert "Paper ledger consistent: `True`" in md_payload
    assert "Paper ledger snapshot: `paper ledger | open=0 | closed=1 | exit_fills=0 | orders=0 | fills=0`" in md_payload
    assert "## Quick-Read Contract" in md_payload
    assert "## Promotion Bridge" in md_payload
    assert (
        "Attack challenger bridge report: "
        "`analysis_results\\btc_1d_pullthrough_asymmetric_release_promotion_bridge_latest.json`"
    ) in md_payload
    assert "## Open First" in md_payload
    assert "`analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md`" in md_payload
    assert "`analysis_results\\btc_1d_execution_contract_screen_md_latest.md`" in md_payload
    assert "`analysis_results\\btc_1d_meta_contract_screen_md_latest.md`" in md_payload
    assert "`analysis_results\\btc_1d_operating_brief_md_latest.md`" in md_payload
    assert "## Latest Stable Pointers" in md_payload
    standard_pos = md_payload.index("## Standard Check Order")
    regression_lock_pos = md_payload.index("Regression lock: `tests/unit/test_btc_1d_operating_cli_help_contract.py`")
    execution_pos = md_payload.index("Execution health: `BTC 1d practical health | status=btc_only_practical_with_caveats")
    execution_contract_pos = md_payload.index("Execution contract read: `execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`")
    execution_contract_aligned_pos = md_payload.index("Execution contract aligned: `True`")
    execution_contract_snapshot_summary_aligned_pos = md_payload.index(
        "Execution contract paper ledger snapshot summary aligned: `True`"
    )
    paper_execution_contract_checked_pos = md_payload.index("Paper execution contract checked: `True`")
    paper_execution_contract_aligned_pos = md_payload.index("Paper execution contract aligned: `True`")
    paper_execution_contract_checked_aligned_pos = md_payload.index(
        "Paper execution contract checked aligned: `True`"
    )
    paper_execution_contract_aligned_aligned_pos = md_payload.index(
        "Paper execution contract aligned aligned: `True`"
    )
    paper_execution_contract_checked_summary_aligned_pos = md_payload.index(
        "Paper execution contract checked summary aligned: `True`"
    )
    paper_execution_contract_aligned_summary_aligned_pos = md_payload.index(
        "Paper execution contract aligned summary aligned: `True`"
    )
    practical_pos = md_payload.index("Practical status: `btc_only_practical_with_caveats`")
    combined_pos = md_payload.index("Combined health: `BTC 1d practical health | status=btc_only_practical_with_caveats")
    research_pos = md_payload.index("Research stack status: `BTC 1d research stack | frontier=ratio112_tighter_stop_main")
    paper_pos = md_payload.index("Paper nightly: `BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0`")
    duplicate_pos = md_payload.index("Paper exit duplicate run: `True`")
    carry_pos = md_payload.index("Carry `2200`: `PASS`")
    contract_pos = md_payload.index("## Quick-Read Contract")
    open_first_pos = md_payload.index("## Open First")
    latest_pointers_pos = md_payload.index("## Latest Stable Pointers")
    assert standard_pos < regression_lock_pos < execution_pos < execution_contract_pos < execution_contract_aligned_pos < execution_contract_snapshot_summary_aligned_pos < paper_execution_contract_checked_pos < paper_execution_contract_aligned_pos < paper_execution_contract_checked_aligned_pos < paper_execution_contract_aligned_aligned_pos < paper_execution_contract_checked_summary_aligned_pos < paper_execution_contract_aligned_summary_aligned_pos < practical_pos < combined_pos < research_pos < paper_pos < duplicate_pos < carry_pos < contract_pos < open_first_pos < latest_pointers_pos
    assert "Operating brief MD" in md_payload
    assert "Practical scorecard MD" in md_payload
    assert "Research stack brief MD" in md_payload
    assert "Quick-read contract screen MD" in md_payload
    assert "Execution contract screen MD" in md_payload
    assert "Meta contract screen MD" in md_payload
    assert "Paper nightly summary JSON" in md_payload
    assert "Paper nightly summary MD" in md_payload
    assert (
        "Attack challenger bridge report JSON: "
        "`analysis_results\\btc_1d_pullthrough_asymmetric_release_promotion_bridge_latest.json`"
    ) in md_payload
    latest_json = tmp_path / "btc_1d_operating_index_latest.json"
    latest_md = tmp_path / "btc_1d_operating_index_md_latest.md"
    assert latest_json.exists()
    assert latest_md.exists()
    latest_json_payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert latest_json_payload["quick_read_order_version"] == "operating_v3"
    assert latest_json_payload["quick_read_order"][-2:] == ["quick_read_contract", "open_first"]
    latest_md_payload = latest_md.read_text(encoding="utf-8")
    latest_carry_pos = latest_md_payload.index("Carry `2200`: `PASS`")
    latest_contract_pos = latest_md_payload.index("## Quick-Read Contract")
    latest_open_first_pos = latest_md_payload.index("## Open First")
    latest_pointers_pos = latest_md_payload.index("## Latest Stable Pointers")
    assert latest_carry_pos < latest_contract_pos < latest_open_first_pos < latest_pointers_pos


def test_write_operating_brief_creates_json_and_txt(tmp_path: Path) -> None:
    brief = {
        "candidate": "low_vol_cap_050_025_minvol020_p2200",
        "scope": "BTC-only",
        "shadow_decision": "shadow_ready_for_btc_only",
        "quick_read_order_version": "operating_v2",
        "quick_read_order": [
            "practical_status",
            "combined_health",
            "research_stack_status",
            "carry",
            "survivability",
            "walk_forward",
            "friction",
            "eth_cross_check",
        ],
        "carry": {"periods": 2200, "decision": "PASS", "sharpe": 1.16, "cagr": 0.14, "max_drawdown": 0.10},
        "survivability": {"periods": 2600, "decision": "PASS", "sharpe": 1.15, "cagr": 0.15, "max_drawdown": 0.13},
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
        "paths": {
            "operating_index_md": "analysis_results\\btc_1d_operating_index_md_latest.md",
            "quick_read_contract_screen_md": "analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md",
            "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
        },
    }

    result = _write_operating_brief(analysis_dir=tmp_path, brief=brief)

    json_payload = json.loads(Path(result["json"]).read_text(encoding="utf-8"))
    txt_payload = Path(result["txt"]).read_text(encoding="utf-8")
    md_payload = Path(result["md"]).read_text(encoding="utf-8")

    assert json_payload["candidate"] == "low_vol_cap_050_025_minvol020_p2200"
    assert json_payload["quick_read_order_version"] == "operating_v2"
    assert json_payload["quick_read_order"] == [
        "practical_status",
        "combined_health",
        "research_stack_status",
        "carry",
        "survivability",
        "walk_forward",
        "friction",
        "eth_cross_check",
    ]
    assert json_payload["paths"]["quick_read_contract_screen_md"] == (
        "analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md"
    )
    assert json_payload["paths"]["paper_nightly_summary_md"] == (
        "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md"
    )
    assert "BTC 1d Operating Brief" in txt_payload
    assert "quick_read_contract: analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md" in txt_payload
    assert "paper_nightly: analysis_results\\btc_1d_paper_nightly_summary_md_latest.md" in txt_payload
    assert "# BTC 1d Operating Brief" in md_payload
    assert "## Quick-Read Contract" in md_payload
    assert "## Paper Nightly" in md_payload
    assert "`analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md`" in md_payload
    assert "`analysis_results\\btc_1d_paper_nightly_summary_md_latest.md`" in md_payload
    latest_json = tmp_path / "btc_1d_operating_brief_latest.json"
    latest_txt = tmp_path / "btc_1d_operating_brief_txt_latest.txt"
    latest_md = tmp_path / "btc_1d_operating_brief_md_latest.md"
    assert latest_json.exists()
    assert latest_txt.exists()
    assert latest_md.exists()
    assert json.loads(latest_json.read_text(encoding="utf-8"))["paths"]["quick_read_contract_screen_md"] == (
        "analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md"
    )
    assert json.loads(latest_json.read_text(encoding="utf-8"))["paths"]["paper_nightly_summary_md"] == (
        "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md"
    )
    latest_md_payload = latest_md.read_text(encoding="utf-8")
    assert "## Quick-Read Contract" in latest_md_payload
    assert "## Paper Nightly" in latest_md_payload
    assert "## Open First" in latest_md_payload
    contract_pos = latest_md_payload.index("## Quick-Read Contract")
    paper_pos = latest_md_payload.index("## Paper Nightly")
    open_first_pos = latest_md_payload.index("## Open First")
    carry_pos = latest_md_payload.index("## Carry")
    assert contract_pos < paper_pos < open_first_pos < carry_pos


def test_publish_practical_outputs_returns_latest_paths(tmp_path: Path) -> None:
    analysis_dir = tmp_path
    _write_json(
        analysis_dir / "btc_1d_volatility_expansion_reclaim_stab_atrs_paper_validation_20260415T010122Z.json",
        {"decision_record": {"decision": "PASS", "key_metrics": {"sharpe": 1.0, "cagr": 0.3, "max_drawdown": 0.15, "trades": 40}}},
    )
    _write_json(
        analysis_dir / "btc_1d_volatility_expansion_reclaim_stab_atrs_friction_20260415T010806Z.json",
        {"report": {"levels": [{"cost_bps": 20.0, "decision": "PASS", "sharpe": 1.0, "cagr": 0.28, "max_drawdown": 0.16}]}},
    )
    _write_json(
        analysis_dir / "btc_1d_volatility_expansion_reclaim_stab_atrs_benchmark_stats_20260415T131904Z.json",
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
        analysis_dir / "btc_1d_volatility_expansion_reclaim_stab_atrs_stats_20260415T131400Z.json",
        {"report": {"statistics": {"psr": 1.0, "dsr": 0.0, "dsr_hurdle_sharpe": 1.9}, "bootstrap": {"sharpe_ci_95": [0.6, 2.1], "cagr_ci_95": [0.1, 0.8], "p_sharpe_gt_0": 1.0}}},
    )
    _write_json(
        analysis_dir / "btc_1d_volatility_expansion_reclaim_stab_atrs_regime_stability_20260415T133026Z.json",
        {"report": {"regime_metrics": {"regimes": {"high_volatility": {"sharpe": 0.6}, "low_volatility": {"sharpe": 0.2}, "range": {"sharpe": -1.0}}}, "leave_one_year_out": {"worst_cagr_year": 2020, "worst_mdd_year": 2023}}},
    )
    _write_json(
        analysis_dir / "btc_1d_volatility_expansion_reclaim_stab_atrs_concentration_20260415T133941Z.json",
        {"report": {"trade_concentration": {"top_1_trade_share": 0.2, "top_3_trade_share": 0.4, "top_5_trade_share": 0.6}, "monthly_concentration": {"top_5_month_share": 0.5}}},
    )

    result = _publish_practical_outputs(analysis_dir=analysis_dir)

    assert Path(result["btc_1d_practical_scorecard"]).exists()
    assert Path(result["btc_1d_practical_scorecard_md"]).exists()
    assert Path(result["btc_1d_practical_promotion_gate"]).exists()
    assert Path(result["btc_1d_practical_promotion_gate_md"]).exists()


def test_publish_research_outputs_returns_latest_paths(tmp_path: Path) -> None:
    analysis_dir = tmp_path
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
            "scope": "btc_only_practical_with_caveats",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
            "standard_check_order": ["practical", "research", "contract", "brief"],
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
                "regression_lock_test": "tests/unit/test_btc_1d_execution_contract_wording_contract.py",
                "standard_check_order_reference": ["practical", "research", "contract", "brief"],
                "wording_regression_test": "tests/unit/test_btc_1d_execution_contract_wording_contract.py",
                "symmetry_regression_test": "tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py",
            },
            "entries": [],
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json",
        {
            "summary": {"meta_contract_tests": []},
            "tests": [],
        },
    )
    _write_json(
        analysis_dir / "btc_1d_attack_main_backup_screen_latest.json",
        {
            "preferred_main": {"name": "ratio112_tighter_stop_main", "cagr": 0.4243, "max_drawdown": 0.1609, "sharpe": 1.5613},
            "preferred_backup": {"name": "ratio111_tighter_stop_backup", "cagr": 0.4154, "max_drawdown": 0.1609, "sharpe": 1.5348},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_attack_defensive_bridge_screen_latest.json",
        {
            "preferred_attack_model": {"name": "ratio112_tighter_stop_main", "cagr": 0.4243, "max_drawdown": 0.1609, "sharpe": 1.5613},
            "preferred_defensive_model": {"name": "volatility_expansion_pullthrough_shorter_hold", "cagr": 0.2621, "max_drawdown": 0.1637, "sharpe": 1.2805},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_near_miss_priority_screen_latest.json",
        {
            "highest_priority_near_miss": {
                "name": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
                "cagr": 0.3909,
                "max_drawdown": 0.2484,
            }
        },
    )

    result = _publish_research_outputs(analysis_dir=analysis_dir)

    assert Path(result["btc_1d_research_stack_operating_brief"]).exists()
    assert Path(result["btc_1d_research_stack_operating_brief_md"]).exists()
    assert Path(result["btc_1d_meta_contract_screen"]).exists()
    assert Path(result["btc_1d_meta_contract_screen_md"]).exists()


def test_publish_execution_outputs_returns_latest_paths(tmp_path: Path) -> None:
    analysis_dir = tmp_path
    execution_health_line = "BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ..."
    paper_nightly_health_line = (
        "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0"
    )
    paper_execution_read = "paper execution | track=operating | applied=1 | closed=1 | open=0"
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
            "paper_nightly_summary": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
            "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "paper_execution_read": paper_execution_read,
            "paper_nightly_health_line": paper_nightly_health_line,
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 1,
            "paper_closed_count": 1,
            "paper_open_count": 0,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_quick_read_contract_screen_latest.json",
        {
            "contract_summary": {
                "contract_health_aligned": False,
            }
        },
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

    result = _publish_execution_outputs(analysis_dir=analysis_dir)

    assert Path(result["btc_1d_execution_contract_screen"]).exists()
    assert Path(result["btc_1d_execution_contract_screen_md"]).exists()


def test_refresh_contract_artifacts_after_paper_republishes_latest_execution_screen(tmp_path: Path) -> None:
    analysis_dir = tmp_path
    paper_nightly_health_line = (
        "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=0 | closed=0 | open=0"
    )
    paper_execution_read = "paper execution | track=operating | applied=0 | closed=0 | open=0"
    execution_health_line = "BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ..."
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
            "scope": "btc_only_practical_with_caveats",
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
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
                "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0"
            },
            "execution_contract_verdict": {"execution_contract_aligned": False},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json",
        {"summary": {"meta_contract_tests": []}, "tests": []},
    )
    _write_json(
        analysis_dir / "btc_1d_attack_main_backup_screen_latest.json",
        {
            "preferred_main": {"name": "ratio112_tighter_stop_main", "cagr": 0.4243, "max_drawdown": 0.1609, "sharpe": 1.5613},
            "preferred_backup": {"name": "ratio111_tighter_stop_backup", "cagr": 0.4154, "max_drawdown": 0.1609, "sharpe": 1.5348},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_attack_defensive_bridge_screen_latest.json",
        {
            "preferred_attack_model": {"name": "ratio112_tighter_stop_main", "cagr": 0.4243, "max_drawdown": 0.1609, "sharpe": 1.5613},
            "preferred_defensive_model": {"name": "volatility_expansion_pullthrough_shorter_hold", "cagr": 0.2621, "max_drawdown": 0.1637, "sharpe": 1.2805},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_near_miss_priority_screen_latest.json",
        {
            "highest_priority_near_miss": {
                "name": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
                "cagr": 0.3909,
                "max_drawdown": 0.2484,
            }
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "paper_execution_read": paper_execution_read,
            "paper_nightly_health_line": paper_nightly_health_line,
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 0,
            "paper_closed_count": 0,
            "paper_open_count": 0,
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

    refreshed_aliases = _refresh_contract_artifacts_after_paper(
        analysis_dir=analysis_dir,
        latest_aliases={
            "btc_1d_operating_brief": str(analysis_dir / "btc_1d_operating_brief_latest.json"),
            "btc_1d_operating_index": str(analysis_dir / "btc_1d_operating_index_latest.json"),
            "btc_1d_paper_nightly_summary": str(analysis_dir / "btc_1d_paper_nightly_summary_latest.json"),
        },
    )

    execution_contract_payload = json.loads(
        (analysis_dir / "btc_1d_execution_contract_screen_latest.json").read_text(encoding="utf-8")
    )
    assert refreshed_aliases["btc_1d_execution_contract_screen"].endswith(
        "btc_1d_execution_contract_screen_latest.json"
    )
    assert (
        execution_contract_payload["execution_contract_summary"]["paper_execution_read"]
        == paper_execution_read
    )


def test_load_execution_contract_state_prefers_latest_screen_truth(tmp_path: Path) -> None:
    analysis_dir = tmp_path
    paper_execution_read = "paper execution | track=operating | applied=0 | closed=0 | open=0"
    execution_contract_read = f"execution contract | drifted | {paper_execution_read}"
    _write_json(
        analysis_dir / "btc_1d_execution_contract_screen_latest.json",
        {
            "execution_contract_summary": {
                "execution_contract_read": execution_contract_read,
                "paper_ledger_snapshot_summary_aligned": True,
                "paper_execution_contract_checked_aligned_entry_aligned": True,
                "paper_execution_contract_aligned_aligned_entry_aligned": False,
                "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
                "paper_execution_contract_aligned_summary_aligned_entry_aligned": False,
                "paper_execution_contract_checked_aligned_summary_aligned": True,
                "paper_execution_contract_aligned_aligned_summary_aligned": False,
                "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
                "paper_execution_contract_aligned_summary_aligned_summary_aligned": False,
            },
            "execution_contract_verdict": {
                "execution_contract_aligned": False,
            },
        },
    )

    state = _load_execution_contract_state(
        analysis_dir=analysis_dir,
        latest_aliases={
            "btc_1d_execution_contract_screen": str(
                analysis_dir / "btc_1d_execution_contract_screen_latest.json"
            )
        },
        paper_execution_read=paper_execution_read,
        execution_health_line="BTC 1d practical health ... || BTC 1d research stack ...",
    )

    assert state["execution_contract_aligned"] is False
    assert state["execution_contract_read"] == execution_contract_read
    assert state["execution_contract_paper_ledger_snapshot_summary_aligned"] is True
    assert state["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert state["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"] is False
    assert state["execution_contract_health_line"].endswith(execution_contract_read)


def test_load_attack_challenger_state_prefers_bridge_entry_screen(tmp_path: Path) -> None:
    analysis_dir = tmp_path
    _write_json(
        analysis_dir / "btc_1d_pullthrough_asymmetric_release_bridge_entry_screen_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "bridge_entry_verdict": {
                "bridge_entry_ready": True,
                "bridge_queue_lane": "attack_challenger_queue",
                "next_step_now": "execution_contract_entry_check",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_promotion_ready"] is True
    assert state["attack_challenger_bridge_entry_ready"] is True
    assert state["attack_challenger_bridge_queue_lane"] == "attack_challenger_queue"
    assert state["attack_challenger_next_step"] == "execution_contract_entry_check"


def test_load_attack_challenger_state_prefers_execution_contract_entry_check(tmp_path: Path) -> None:
    analysis_dir = tmp_path
    _write_json(
        analysis_dir / "btc_1d_pullthrough_asymmetric_release_execution_contract_entry_check_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "execution_contract_entry_requirements": {
                "promotion_ready": True,
                "bridge_entry_ready": True,
            },
            "execution_contract_entry_verdict": {
                "execution_contract_entry_ready": True,
                "execution_contract_queue_lane": "challenger_execution_contract_queue",
                "next_step_now": "candidate_operator_stack_handoff",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_promotion_ready"] is True
    assert state["attack_challenger_bridge_entry_ready"] is True
    assert state["attack_challenger_execution_contract_entry_ready"] is True
    assert (
        state["attack_challenger_execution_contract_queue_lane"]
        == "challenger_execution_contract_queue"
    )
    assert state["attack_challenger_next_step"] == "candidate_operator_stack_handoff"


def test_load_attack_challenger_state_prefers_operator_stack_handoff(tmp_path: Path) -> None:
    analysis_dir = tmp_path
    _write_json(
        analysis_dir / "btc_1d_pullthrough_asymmetric_release_operator_stack_handoff_latest.json",
        {
            "stack_context": {
                "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit"
            },
            "candidate_profile": {
                "label": "pullthrough_asymmetric_release_tighter_exit",
                "paper_validation_cagr": 0.2712,
                "paper_validation_max_drawdown": 0.16,
                "walk_forward_sensitivity_max_drift": 0.0928,
                "friction_final_decision": "continue",
            },
            "operator_stack_handoff_requirements": {
                "promotion_chain_still_green": True,
                "execution_contract_entry_ready": True,
            },
            "operator_stack_handoff_verdict": {
                "operator_stack_handoff_ready": True,
                "operator_stack_handoff_lane": "operator_stack_handoff_queue",
                "next_step_now": "operator_runbook_candidate_entry",
            },
        },
    )

    state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    assert state["attack_challenger_candidate"] == "pullthrough_asymmetric_release_tighter_exit"
    assert state["attack_challenger_promotion_ready"] is True
    assert state["attack_challenger_execution_contract_entry_ready"] is True
    assert state["attack_challenger_operator_stack_handoff_ready"] is True
    assert (
        state["attack_challenger_operator_stack_handoff_lane"]
        == "operator_stack_handoff_queue"
    )
    assert state["attack_challenger_next_step"] == "operator_runbook_candidate_entry"


def test_write_operator_dashboard_artifacts_publishes_latest_dashboard(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir()
    _write_json(
        analysis_dir / "btc_1d_latest_summary_latest.json",
        {
            "candidate": "btc_1d_prod_candidate",
            "shadow_decision": "shadow_ready_for_btc_only",
            "carry": {"decision": "pass", "sharpe": 1.2, "cagr": 0.2, "max_drawdown": 0.1},
            "survivability": {"decision": "pass", "sharpe": 1.1, "cagr": 0.18, "max_drawdown": 0.12},
            "walk_forward": {"passed": True, "oos_sharpe": 0.8, "oos_cagr": 0.1, "oos_max_drawdown": 0.09},
            "friction": {"decision": "pass", "heaviest_level_bps": 20, "heaviest_level_sharpe": 0.9},
            "eth_cross_check": {"symbol": "ETHUSDT", "pass_rate": 0.0},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "practical_status_label": "btc_only_practical_with_caveats",
            "combined_health_line": "combined",
            "research_stack_status": "research",
            "execution_contract_health_line": "execution health",
            "execution_contract_read": "execution contract | aligned | paper execution | track=operating | applied=0 | closed=0 | open=0",
            "paper_execution_read": "paper execution | track=operating | applied=0 | closed=0 | open=0",
            "paper_execution_contract_aligned": True,
            "paper_exit_duplicate_run": False,
            "paper_ledger_consistent": True,
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
            "contract_health_aligned": True,
            "attack_challenger_candidate": "pullthrough_asymmetric_release_tighter_exit",
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_remote_monitoring_deployment_handoff_lane": ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": (
                "analysis_results\\"
                "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
            ),
            "attack_challenger_paper_validation_cagr": 0.2712,
            "attack_challenger_paper_validation_max_drawdown": 0.16,
            "attack_challenger_walk_forward_sensitivity_max_drift": 0.0928,
            "attack_challenger_friction_final_decision": "continue",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {"contract_health_line": "BTC 1d contract health | aligned=True"},
    )
    _write_json(
        analysis_dir / "btc_1d_quick_read_contract_screen_latest.json",
        {
            "contract_summary": {
                "operating_contract_aligned": True,
                "paper_execution_contract_aligned": True,
                "contract_health_aligned": True,
            },
            "contract_verdict": {"contracts_are_well_partitioned": True},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_contract_screen_latest.json",
        {
            "execution_contract_summary": {
                "execution_contract_health_line": "execution health",
                "execution_contract_read": "execution contract | aligned | paper execution | track=operating | applied=0 | closed=0 | open=0",
                "paper_ledger_snapshot_summary_aligned": True,
                "paper_execution_contract_aligned_summary_aligned": True,
            },
            "execution_contract_verdict": {"execution_contract_aligned": True},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "paper_execution_read": "paper execution | track=operating | applied=0 | closed=0 | open=0",
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 0,
            "paper_duplicate_count": 1,
            "paper_closed_count": 0,
            "paper_open_count": 0,
            "paper_ledger_consistent": True,
        },
    )

    aliases = _write_operator_dashboard_artifacts(
        analysis_dir=analysis_dir,
        latest_aliases={},
    )

    latest_dashboard_json = Path(aliases["btc_1d_operator_dashboard"])
    latest_dashboard_md = Path(aliases["btc_1d_operator_dashboard_md"])
    latest_dashboard_html = Path(aliases["btc_1d_operator_dashboard_html"])
    payload = json.loads(latest_dashboard_json.read_text(encoding="utf-8"))
    md_payload = latest_dashboard_md.read_text(encoding="utf-8")
    html_payload = latest_dashboard_html.read_text(encoding="utf-8")

    assert latest_dashboard_json.name == "btc_1d_operator_dashboard_latest.json"
    assert latest_dashboard_md.name == "btc_1d_operator_dashboard_md_latest.md"
    assert latest_dashboard_html.name == "btc_1d_operator_dashboard_html_latest.html"
    assert payload["dashboard_summary"]["paper_ledger_consistent"] is True
    assert payload["dashboard_summary"]["execution_contract_aligned"] is True
    assert payload["dashboard_summary"]["deployment_monitoring_active"] is True
    assert (
        payload["dashboard_summary"]["attack_challenger_next_step"]
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    )
    assert payload["artifacts"]["attack_challenger_bridge_report_json"].endswith(
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
    assert (
        f"- Next step: `{ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP}`"
        in md_payload
    )
    assert (
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        in md_payload
    )
    assert ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP in html_payload
    assert (
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
        in html_payload
    )
    assert "paper_ledger=inconsistent" not in payload["dashboard_summary"]["attention_flags"]
