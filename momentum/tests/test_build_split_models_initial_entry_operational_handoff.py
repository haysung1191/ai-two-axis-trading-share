from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.analysis import build_split_models_initial_entry_operational_handoff as handoff


def test_build_handoff_payload_fail() -> None:
    payload = handoff.build_handoff_payload(
        {
            "operational_readiness_verdict": "FAIL",
            "operational_readiness_reason": "scheduled_task_not_hardened_for_unattended_operation",
            "next_action": "run_harden_as_admin",
            "next_reason": "scheduled_task_not_hardened_for_unattended_operation",
            "next_command_bat": r"tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.bat",
            "next_command_ps1": r"tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.ps1",
            "submit_ready": True,
            "unattended_operation_ready": False,
            "capital_slug": "1000000",
            "check_timestamp": "20260419T180000",
            "planned_count": 3,
            "planned_symbols": ["DOW", "XOM", "COP"],
            "autotrade_task_name": "MomentumSplitModelsInitialEntryAutoTrade",
            "autotrade_task_state": "Ready",
            "autotrade_task_hardening_verdict": "FAIL",
            "autotrade_task_hardening_failures": ["run_level=Limited"],
            "latest_index_path": "latest.json",
            "check_json_path": "check.json",
            "report_path": "report.md",
        }
    )

    assert payload["handoff_verdict"] == "FAIL"
    assert payload["primary_blocker"] == "scheduled_task_not_hardened_for_unattended_operation"
    assert payload["next_step"] == "run_harden_as_admin"


def test_build_handoff_payload_pass() -> None:
    payload = handoff.build_handoff_payload(
        {
            "operational_readiness_verdict": "PASS",
            "operational_readiness_reason": "split_models_initial_entry_unattended_operation_ready",
            "next_action": "none",
            "next_reason": "all_operational_requirements_satisfied",
            "next_command_bat": None,
            "next_command_ps1": None,
            "submit_ready": True,
            "unattended_operation_ready": True,
            "capital_slug": "1000000",
            "check_timestamp": "20260419T180000",
            "planned_count": 3,
            "planned_symbols": ["DOW", "XOM", "COP"],
            "autotrade_task_name": "MomentumSplitModelsInitialEntryAutoTrade",
            "autotrade_task_state": "Ready",
            "autotrade_task_hardening_verdict": "PASS",
            "autotrade_task_hardening_failures": [],
            "latest_index_path": "latest.json",
            "check_json_path": "check.json",
            "report_path": "report.md",
        }
    )

    assert payload["handoff_verdict"] == "PASS"
    assert payload["primary_blocker"] == "-"
    assert payload["next_step"] == "monitor_scheduled_autotrade_run"


def test_main_reads_readiness_json_and_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    readiness_path = tmp_path / "readiness.json"
    out_json = tmp_path / "handoff.json"
    out_text = tmp_path / "handoff.txt"
    readiness_path.write_text(
        json.dumps(
            {
                "operational_readiness_verdict": "FAIL",
                "operational_readiness_reason": "scheduled_task_not_hardened_for_unattended_operation",
                "next_action": "run_harden_as_admin",
                "next_reason": "scheduled_task_not_hardened_for_unattended_operation",
                "next_command_bat": r"tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.bat",
                "next_command_ps1": r"tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.ps1",
                "submit_ready": True,
                "unattended_operation_ready": False,
                "capital_slug": "1000000",
                "check_timestamp": "20260419T180000",
                "planned_count": 3,
                "planned_symbols": ["DOW", "XOM", "COP"],
                "autotrade_task_name": "MomentumSplitModelsInitialEntryAutoTrade",
                "autotrade_task_state": "Ready",
                "autotrade_task_hardening_verdict": "FAIL",
                "autotrade_task_hardening_failures": ["run_level=Limited"],
                "latest_index_path": "latest.json",
                "check_json_path": "check.json",
                "report_path": "report.md",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/build_split_models_initial_entry_operational_handoff.py",
            "--readiness-json-path",
            str(readiness_path),
            "--output-json-path",
            str(out_json),
            "--output-text-path",
            str(out_text),
        ],
    )

    handoff.main()
    output = capsys.readouterr().out
    assert "handoff_verdict=FAIL" in output
    assert json.loads(out_json.read_text(encoding="utf-8"))["next_step"] == "run_harden_as_admin"
    assert "primary_blocker=scheduled_task_not_hardened_for_unattended_operation" in out_text.read_text(encoding="utf-8")


def test_main_recomputes_live_status_when_readiness_path_not_supplied(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    latest_index_path = tmp_path / "shadow_live_initial_adaptive_latest.json"
    check_json_path = tmp_path / "check.json"
    latest_index_path.write_text(
        json.dumps({"check_json_path": str(check_json_path)}),
        encoding="utf-8",
    )
    check_json_path.write_text(json.dumps({"planned_count": 3}), encoding="utf-8")
    monkeypatch.setattr(handoff, "SHADOW_DIR", tmp_path)
    monkeypatch.setattr(
        handoff.verify_ready.show_latest,
        "build_status_payload",
        lambda latest_index, check_payload: {
            "submit_ready": True,
            "unattended_operation_ready": True,
            "capital_slug": "1000000",
            "check_timestamp": "20260419T180500",
            "planned_count": 3,
            "planned_symbols": ["DOW", "XOM", "COP"],
            "autotrade_task_name": "MomentumSplitModelsInitialEntryAutoTrade",
            "autotrade_task_state": "Ready",
            "autotrade_task_hardening_verdict": "PASS",
            "autotrade_task_hardening_failures": [],
            "operational_next_action": "submit_and_show",
            "operational_next_reason": "all_submit_gates_passed_and_planned_orders_exist",
            "operational_next_command_bat": r"tools\analysis\submit_and_show_split_models_initial_entry_latest.bat",
            "operational_next_command_ps1": r"tools\analysis\submit_and_show_split_models_initial_entry_latest.ps1",
            "latest_index_path": str(latest_index_path),
            "check_json_path": str(check_json_path),
            "report_path": "report.md",
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/build_split_models_initial_entry_operational_handoff.py",
        ],
    )

    handoff.main()
    output = capsys.readouterr().out
    assert "handoff_verdict=PASS" in output
    assert "next_step=monitor_scheduled_autotrade_run" in output
