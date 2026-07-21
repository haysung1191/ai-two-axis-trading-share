from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.analysis import show_split_models_initial_entry_latest as show_latest


def test_build_status_payload_and_text(tmp_path: Path) -> None:
    show_latest._load_task_status_payload = lambda: {
        "task_name": "MomentumSplitModelsInitialEntryAutoTrade",
        "state": "Ready",
        "hardening_verdict": "FAIL",
        "hardening_failures": ["run_level=Limited"],
        "recommended_next_action": "run_harden_as_admin",
        "recommended_next_reason": "scheduled_task_not_hardened_for_unattended_operation",
    }
    latest_index = {
        "capital_slug": "1000000",
        "total_capital": 1000000.0,
        "submit_live_requested": False,
        "check_timestamp": "20260419T150200",
        "check_json_path": str(tmp_path / "check.json"),
        "check_md_path": str(tmp_path / "check.md"),
        "check_history_json_path": str(tmp_path / "check_hist.json"),
        "check_history_md_path": str(tmp_path / "check_hist.md"),
        "plan_path": "plan.csv",
        "preflight_path": "preflight.json",
        "report_path": "report.md",
    }
    check_payload = {
        "check_verdict": "PASS",
        "preflight_verdict": "PASS",
        "live_readiness": "GO",
        "operator_gate_verdict": "PASS",
        "archive_stability_verdict": "FAIL",
        "planned_count": 3,
        "skipped_count": 0,
        "planned_symbols": ["DOW", "XOM", "COP"],
        "planned_quantity_total": 8,
        "estimated_order_notional_krw_total": 694029.424,
        "fundable_count_at_capital": 2,
        "fundable_symbols_at_capital": ["DOW", "COP"],
    }

    payload = show_latest.build_status_payload(latest_index, check_payload)
    text = show_latest.render_status_text(payload)

    assert payload["check_timestamp"] == "20260419T150200"
    assert payload["planned_symbols"] == ["DOW", "XOM", "COP"]
    assert payload["submit_ready"] is True
    assert payload["unattended_operation_ready"] is False
    assert payload["recommended_next_action"] == "submit_and_show"
    assert payload["recommended_next_reason"] == "all_submit_gates_passed_and_planned_orders_exist"
    assert payload["operational_next_action"] == "run_harden_as_admin"
    assert payload["operational_next_reason"] == "scheduled_task_not_hardened_for_unattended_operation"
    assert payload["recommended_next_command_bat"].endswith("submit_and_show_split_models_initial_entry_latest.bat")
    assert payload["refresh_and_show_command_bat"].endswith("refresh_and_show_split_models_initial_entry_latest.bat")
    assert payload["submit_and_show_command_ps1"].endswith("submit_and_show_split_models_initial_entry_latest.ps1")
    assert payload["autotrade_task_harden_as_admin_command_bat"].endswith("run_harden_split_models_initial_entry_autotrade_task_as_admin.bat")
    assert "Split Models Initial Entry Latest" in text
    assert "planned_symbols=DOW, XOM, COP" in text
    assert "check_verdict=PASS" in text
    assert "refresh_and_show_command_bat=tools\\analysis\\refresh_and_show_split_models_initial_entry_latest.bat" in text
    assert "recommended_next_action=submit_and_show" in text
    assert "recommended_next_reason=all_submit_gates_passed_and_planned_orders_exist" in text
    assert "autotrade_task_hardening_verdict=FAIL" in text
    assert "operational_next_action=run_harden_as_admin" in text


def test_main_prints_json(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(
        show_latest,
        "_load_task_status_payload",
        lambda: {
            "task_name": "MomentumSplitModelsInitialEntryAutoTrade",
            "state": "Ready",
            "hardening_verdict": "FAIL",
            "hardening_failures": ["run_level=Limited"],
            "recommended_next_action": "run_harden_as_admin",
            "recommended_next_reason": "scheduled_task_not_hardened_for_unattended_operation",
        },
    )
    latest_index_path = tmp_path / "latest.json"
    check_json_path = tmp_path / "check.json"
    latest_index_path.write_text(
        json.dumps(
            {
                "capital_slug": "1000000",
                "total_capital": 1000000.0,
                "submit_live_requested": False,
                "check_timestamp": "20260419T150200",
                "check_json_path": str(check_json_path),
                "check_md_path": "check.md",
                "check_history_json_path": "check_hist.json",
                "check_history_md_path": "check_hist.md",
                "plan_path": "plan.csv",
                "preflight_path": "preflight.json",
                "report_path": "report.md",
            }
        ),
        encoding="utf-8",
    )
    check_json_path.write_text(
        json.dumps(
            {
                "check_verdict": "PASS",
                "preflight_verdict": "PASS",
                "live_readiness": "GO",
                "operator_gate_verdict": "PASS",
                "archive_stability_verdict": "FAIL",
                "planned_count": 3,
                "skipped_count": 0,
                "planned_symbols": ["DOW", "XOM", "COP"],
                "planned_quantity_total": 8,
                "estimated_order_notional_krw_total": 694029.424,
                "fundable_count_at_capital": 2,
                "fundable_symbols_at_capital": ["DOW", "COP"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/show_split_models_initial_entry_latest.py",
            "--latest-index-path",
            str(latest_index_path),
            "--json",
        ],
    )

    show_latest.main()
    output = json.loads(capsys.readouterr().out)
    assert output["check_verdict"] == "PASS"
    assert output["planned_symbols"] == ["DOW", "XOM", "COP"]
    assert output["submit_ready"] is True
    assert output["unattended_operation_ready"] is False
    assert output["recommended_next_action"] == "submit_and_show"
    assert output["recommended_next_reason"] == "all_submit_gates_passed_and_planned_orders_exist"
    assert output["operational_next_action"] == "run_harden_as_admin"
    assert output["submit_and_show_command_bat"].endswith("submit_and_show_split_models_initial_entry_latest.bat")


def test_build_status_payload_recommends_refresh_when_not_ready(tmp_path: Path) -> None:
    show_latest._load_task_status_payload = lambda: {
        "task_name": "MomentumSplitModelsInitialEntryAutoTrade",
        "state": "Ready",
        "hardening_verdict": "PASS",
        "hardening_failures": [],
        "recommended_next_action": "none",
        "recommended_next_reason": "task_hardening_requirements_satisfied",
    }
    latest_index = {
        "capital_slug": "1000000",
        "total_capital": 1000000.0,
        "submit_live_requested": False,
        "check_timestamp": "20260419T150200",
        "check_json_path": str(tmp_path / "check.json"),
        "check_md_path": str(tmp_path / "check.md"),
        "check_history_json_path": str(tmp_path / "check_hist.json"),
        "check_history_md_path": str(tmp_path / "check_hist.md"),
        "plan_path": "plan.csv",
        "preflight_path": "preflight.json",
        "report_path": "report.md",
    }
    check_payload = {
        "check_verdict": "PASS",
        "preflight_verdict": "PASS",
        "live_readiness": "GO",
        "operator_gate_verdict": "PASS",
        "archive_stability_verdict": "FAIL",
        "planned_count": 0,
        "skipped_count": 0,
        "planned_symbols": [],
        "planned_quantity_total": 0,
        "estimated_order_notional_krw_total": 0.0,
        "fundable_count_at_capital": 0,
        "fundable_symbols_at_capital": [],
    }

    payload = show_latest.build_status_payload(latest_index, check_payload)

    assert payload["submit_ready"] is False
    assert payload["unattended_operation_ready"] is False
    assert payload["recommended_next_action"] == "refresh_and_show"
    assert payload["recommended_next_reason"] == "planned_count_not_positive"
    assert payload["operational_next_action"] == "refresh_and_show"
    assert payload["recommended_next_command_bat"].endswith("refresh_and_show_split_models_initial_entry_latest.bat")
