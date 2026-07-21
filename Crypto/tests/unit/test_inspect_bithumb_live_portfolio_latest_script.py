from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


SCRIPT_PATH = Path(r"C:\AI\Crypto\deploy\windows\inspect_bithumb_live_portfolio_latest.ps1")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_latest_inspect_script(project_root: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["BITHUMB_LIVE_PORTFOLIO_PROJECT_ROOT"] = str(project_root)
    return subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT_PATH),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )


def test_latest_inspect_script_reports_snapshot_fields(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    generated_at_local = (datetime.now() - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    _write_json(
        logs_dir / "bithumb_live_portfolio_inspect_latest.json",
        {
            "generated_at_local": generated_at_local,
            "status": {
                "label": "NORMAL",
                "action_hint": "PREPARE_STOP",
                "trigger_proximity": "NEAR",
                "reentry": "NONE",
                "run_coverage": "ENRICHED",
                "operator_alert_required": False,
                "operator_alert_escalation": "NONE",
                "operator_alert_occurrence_count": 0,
            },
            "event": {
                "next_trigger_stage": "partial_stop_loss",
                "next_trigger_distance_pct": -0.83,
                "last_reason": "threshold_not_hit",
            },
            "runs": {
                "count": 10,
                "latest": {
                    "status": "ok",
                    "mode": "manage_open_position",
                    "last_reason": "threshold_not_hit",
                },
            },
        },
    )
    (logs_dir / "bithumb_live_portfolio_inspect_latest.txt").write_text(
        "inspect_at=test | status=NORMAL | action_hint=PREPARE_STOP",
        encoding="utf-8",
    )

    result = _run_latest_inspect_script(tmp_path)

    assert "snapshot.exists=True" in result.stdout
    assert "snapshot.stale=False" in result.stdout
    assert "status.label=NORMAL" in result.stdout
    assert "status.action_hint=PREPARE_STOP" in result.stdout
    assert "status.operator_alert_escalation=NONE" in result.stdout
    assert "event.next_trigger=partial_stop_loss" in result.stdout
    assert "runs.count=10" in result.stdout
    assert "--- inspect latest text ---" in result.stdout


def test_latest_inspect_script_marks_snapshot_stale(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    generated_at_local = (datetime.now() - timedelta(minutes=45)).replace(microsecond=0).isoformat()
    _write_json(
        logs_dir / "bithumb_live_portfolio_inspect_latest.json",
        {
            "generated_at_local": generated_at_local,
            "status": {
                "label": "ALERT",
                "action_hint": "WATCH_STOP",
                "trigger_proximity": "URGENT",
                "reentry": "NONE",
                "run_coverage": "LEGACY_MIXED",
                "operator_alert_required": True,
                "operator_alert_escalation": "PROLONGED",
                "operator_alert_occurrence_count": 4,
            },
            "event": {
                "next_trigger_stage": "partial_stop_loss",
                "next_trigger_distance_pct": -0.11,
                "last_reason": "threshold_not_hit",
            },
            "runs": {
                "count": 3,
                "latest": {
                    "status": "ok",
                    "mode": "manage_open_position",
                    "last_reason": "threshold_not_hit",
                },
            },
        },
    )

    result = _run_latest_inspect_script(tmp_path)

    assert "snapshot.exists=True" in result.stdout
    assert "snapshot.stale=True" in result.stdout
    assert "status.action_hint=WATCH_STOP" in result.stdout
    assert "status.operator_alert_required=True" in result.stdout
    assert "status.operator_alert_escalation=PROLONGED" in result.stdout
    assert "status.operator_alert_occurrence_count=4" in result.stdout
