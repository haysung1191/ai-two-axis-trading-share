from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.analysis import auto_trade_split_models_initial_entry as auto_trade


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_build_decision_payload_refresh_only() -> None:
    status_payload = {
        "submit_ready": False,
        "unattended_operation_ready": False,
        "recommended_next_action": "refresh_and_show",
        "recommended_next_reason": "planned_count_not_positive",
        "operational_next_action": "refresh_and_show",
        "operational_next_reason": "planned_count_not_positive",
        "capital_slug": "1000000",
        "check_timestamp": "20260419T160000",
        "planned_symbols": [],
        "planned_count": 0,
        "skipped_count": 0,
        "latest_index_path": "latest.json",
        "submit_summary_path": "submit_summary.json",
        "operational_next_command_bat": "refresh.bat",
        "operational_next_command_ps1": "refresh.ps1",
    }

    payload = auto_trade.build_decision_payload(
        status_payload,
        enable_live_auto_submit=False,
        allow_repeat_submit=False,
        already_submitted=False,
        duplicate_reason="new_submission_required",
    )

    assert payload["action"] == "refresh_only"
    assert payload["reason"] == "planned_count_not_positive"


def test_build_decision_payload_skip_duplicate() -> None:
    status_payload = {
        "submit_ready": True,
        "unattended_operation_ready": True,
        "recommended_next_action": "submit_and_show",
        "recommended_next_reason": "all_submit_gates_passed_and_planned_orders_exist",
        "operational_next_action": "submit_and_show",
        "operational_next_reason": "all_submit_gates_passed_and_planned_orders_exist",
        "capital_slug": "1000000",
        "check_timestamp": "20260419T160000",
        "planned_symbols": ["DOW"],
        "planned_count": 1,
        "skipped_count": 0,
        "latest_index_path": "latest.json",
        "submit_summary_path": "submit_summary.json",
        "operational_next_command_bat": "submit.bat",
        "operational_next_command_ps1": "submit.ps1",
    }

    payload = auto_trade.build_decision_payload(
        status_payload,
        enable_live_auto_submit=True,
        allow_repeat_submit=False,
        already_submitted=True,
        duplicate_reason="same_plan_and_preflight_already_submitted",
    )

    assert payload["action"] == "skip_duplicate_submission"
    assert payload["reason"] == "same_plan_and_preflight_already_submitted"


def test_was_already_submitted_detects_same_hashes(tmp_path: Path) -> None:
    submit_summary_path = tmp_path / "submit_summary.json"
    _write_json(
        submit_summary_path,
        {
            "submitted_plan_sha256": "plan-hash",
            "preflight_sha256": "preflight-hash",
        },
    )
    status_payload = {
        "submit_summary_path": str(submit_summary_path),
        "plan_sha256": "plan-hash",
        "preflight_sha256": "preflight-hash",
    }

    already_submitted, reason = auto_trade._was_already_submitted(status_payload, allow_repeat_submit=False)

    assert already_submitted is True
    assert reason == "same_plan_and_preflight_already_submitted"


def test_main_skips_duplicate_submission(monkeypatch, tmp_path: Path, capsys) -> None:
    latest_index_path = tmp_path / "latest.json"
    check_json_path = tmp_path / "check.json"
    submit_summary_path = tmp_path / "submit_summary.json"
    _write_json(
        latest_index_path,
        {
            "capital_slug": "1000000",
            "total_capital": 1000000.0,
            "submit_live_requested": False,
            "check_timestamp": "20260419T160000",
            "check_json_path": str(check_json_path),
            "plan_sha256": "plan-hash",
            "preflight_sha256": "preflight-hash",
            "submit_summary_path": str(submit_summary_path),
            "latest_index_path": str(latest_index_path),
        },
    )
    _write_json(
        check_json_path,
        {
            "check_verdict": "PASS",
            "preflight_verdict": "PASS",
            "live_readiness": "GO",
            "operator_gate_verdict": "PASS",
            "planned_count": 1,
            "skipped_count": 0,
            "planned_symbols": ["DOW"],
        },
    )
    _write_json(
        submit_summary_path,
        {
            "submitted_plan_sha256": "plan-hash",
            "preflight_sha256": "preflight-hash",
        },
    )

    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd, check: bool, text: bool = False, capture_output: bool = False):
        calls.append(args)
        class _Done:
            stdout = ""
        return _Done()

    monkeypatch.setattr(auto_trade.subprocess, "run", _fake_run)
    monkeypatch.setattr(auto_trade.sys, "executable", "python")
    monkeypatch.setattr(
        auto_trade,
        "_load_status_payload",
        lambda latest_index_path: {
            "submit_ready": True,
            "unattended_operation_ready": True,
            "recommended_next_action": "submit_and_show",
            "recommended_next_reason": "all_submit_gates_passed_and_planned_orders_exist",
            "operational_next_action": "submit_and_show",
            "operational_next_reason": "all_submit_gates_passed_and_planned_orders_exist",
            "capital_slug": "1000000",
            "check_timestamp": "20260419T160000",
            "planned_symbols": ["DOW"],
            "planned_count": 1,
            "skipped_count": 0,
            "latest_index_path": str(latest_index_path),
            "submit_summary_path": str(submit_summary_path),
            "plan_sha256": "plan-hash",
            "preflight_sha256": "preflight-hash",
            "operational_next_command_bat": "submit.bat",
            "operational_next_command_ps1": "submit.ps1",
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/auto_trade_split_models_initial_entry.py",
            "--latest-index-path",
            str(latest_index_path),
        ],
    )

    auto_trade.main()
    output = capsys.readouterr().out
    assert len(calls) == 1
    assert calls[0][1] == "tools/pipelines/submit_split_models_initial_entry_from_latest.py"
    assert "action=ready_but_live_submit_disabled" in output


def test_build_decision_payload_ready_but_disabled() -> None:
    status_payload = {
        "submit_ready": True,
        "unattended_operation_ready": True,
        "recommended_next_action": "submit_and_show",
        "recommended_next_reason": "all_submit_gates_passed_and_planned_orders_exist",
        "operational_next_action": "submit_and_show",
        "operational_next_reason": "all_submit_gates_passed_and_planned_orders_exist",
        "capital_slug": "1000000",
        "check_timestamp": "20260419T160000",
        "planned_symbols": ["DOW"],
        "planned_count": 1,
        "skipped_count": 0,
        "latest_index_path": "latest.json",
        "submit_summary_path": "submit_summary.json",
        "operational_next_command_bat": "submit.bat",
        "operational_next_command_ps1": "submit.ps1",
    }

    payload = auto_trade.build_decision_payload(
        status_payload,
        enable_live_auto_submit=False,
        allow_repeat_submit=False,
        already_submitted=False,
        duplicate_reason="new_submission_required",
    )

    assert payload["action"] == "ready_but_live_submit_disabled"
    assert payload["reason"] == "submit_ready_but_enable_live_auto_submit_not_set"


def test_build_decision_payload_blocks_until_operational_ready() -> None:
    status_payload = {
        "submit_ready": True,
        "unattended_operation_ready": False,
        "recommended_next_action": "submit_and_show",
        "recommended_next_reason": "all_submit_gates_passed_and_planned_orders_exist",
        "operational_next_action": "run_harden_as_admin",
        "operational_next_reason": "scheduled_task_not_hardened_for_unattended_operation",
        "capital_slug": "1000000",
        "check_timestamp": "20260419T160000",
        "planned_symbols": ["DOW"],
        "planned_count": 1,
        "skipped_count": 0,
        "latest_index_path": "latest.json",
        "submit_summary_path": "submit_summary.json",
        "operational_next_command_bat": "run_harden.bat",
        "operational_next_command_ps1": "run_harden.ps1",
    }

    payload = auto_trade.build_decision_payload(
        status_payload,
        enable_live_auto_submit=True,
        allow_repeat_submit=False,
        already_submitted=False,
        duplicate_reason="new_submission_required",
    )

    assert payload["action"] == "blocked_until_operational_ready"
    assert (
        payload["reason"]
        == "scheduled_task_not_hardened_for_unattended_operation"
    )
    assert payload["operational_next_action"] == "run_harden_as_admin"
    assert payload["operational_next_command_bat"] == "run_harden.bat"
