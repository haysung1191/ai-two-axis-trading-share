from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.analysis import verify_split_models_initial_entry_operational_readiness as verify_ready


def test_build_readiness_payload_fail() -> None:
    payload = verify_ready.build_readiness_payload(
        {
            "submit_ready": True,
            "unattended_operation_ready": False,
            "capital_slug": "1000000",
            "check_timestamp": "20260419T180000",
            "planned_symbols": ["DOW", "XOM"],
            "planned_count": 2,
            "autotrade_task_name": "MomentumSplitModelsInitialEntryAutoTrade",
            "autotrade_task_state": "Ready",
            "autotrade_task_hardening_verdict": "FAIL",
            "autotrade_task_hardening_failures": ["run_level=Limited"],
            "operational_next_action": "run_harden_as_admin",
            "operational_next_reason": "scheduled_task_not_hardened_for_unattended_operation",
            "operational_next_command_bat": r"tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.bat",
            "operational_next_command_ps1": r"tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.ps1",
            "latest_index_path": "latest.json",
            "check_json_path": "check.json",
            "report_path": "report.md",
        }
    )

    assert payload["operational_readiness_verdict"] == "FAIL"
    assert payload["next_action"] == "run_harden_as_admin"
    assert (
        payload["operational_readiness_reason"]
        == "scheduled_task_not_hardened_for_unattended_operation"
    )


def test_build_readiness_payload_pass() -> None:
    payload = verify_ready.build_readiness_payload(
        {
            "submit_ready": True,
            "unattended_operation_ready": True,
            "capital_slug": "1000000",
            "check_timestamp": "20260419T180000",
            "planned_symbols": ["DOW", "XOM"],
            "planned_count": 2,
            "autotrade_task_name": "MomentumSplitModelsInitialEntryAutoTrade",
            "autotrade_task_state": "Ready",
            "autotrade_task_hardening_verdict": "PASS",
            "autotrade_task_hardening_failures": [],
            "operational_next_action": "submit_and_show",
            "operational_next_reason": "all_submit_gates_passed_and_planned_orders_exist",
            "operational_next_command_bat": "submit.bat",
            "operational_next_command_ps1": "submit.ps1",
            "latest_index_path": "latest.json",
            "check_json_path": "check.json",
            "report_path": "report.md",
        }
    )

    assert payload["operational_readiness_verdict"] == "PASS"
    assert payload["next_action"] == "none"
    assert payload["next_reason"] == "all_operational_requirements_satisfied"


def test_main_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    latest_index_path = tmp_path / "latest.json"
    check_json_path = tmp_path / "check.json"
    out_json = tmp_path / "ready.json"
    out_text = tmp_path / "ready.txt"
    latest_index_path.write_text(
        json.dumps({"check_json_path": str(check_json_path)}),
        encoding="utf-8",
    )
    check_json_path.write_text(json.dumps({"planned_count": 1}), encoding="utf-8")
    monkeypatch.setattr(
        verify_ready.show_latest,
        "build_status_payload",
        lambda latest_index, check_payload: {
            "submit_ready": True,
            "unattended_operation_ready": False,
            "capital_slug": "1000000",
            "check_timestamp": "20260419T180000",
            "planned_symbols": ["DOW"],
            "planned_count": 1,
            "autotrade_task_name": "MomentumSplitModelsInitialEntryAutoTrade",
            "autotrade_task_state": "Ready",
            "autotrade_task_hardening_verdict": "FAIL",
            "autotrade_task_hardening_failures": ["run_level=Limited"],
            "operational_next_action": "run_harden_as_admin",
            "operational_next_reason": "scheduled_task_not_hardened_for_unattended_operation",
            "operational_next_command_bat": r"tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.bat",
            "operational_next_command_ps1": r"tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.ps1",
            "latest_index_path": str(latest_index_path),
            "check_json_path": str(check_json_path),
            "report_path": "report.md",
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/verify_split_models_initial_entry_operational_readiness.py",
            "--latest-index-path",
            str(latest_index_path),
            "--output-json-path",
            str(out_json),
            "--output-text-path",
            str(out_text),
        ],
    )

    verify_ready.main()
    output = capsys.readouterr().out
    assert "operational_readiness_verdict=FAIL" in output
    assert json.loads(out_json.read_text(encoding="utf-8"))["next_action"] == "run_harden_as_admin"
    assert "next_action=run_harden_as_admin" in out_text.read_text(encoding="utf-8")
