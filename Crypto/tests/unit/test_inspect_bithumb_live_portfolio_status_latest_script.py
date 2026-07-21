from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path


SCRIPT_PATH = Path(r"C:\AI\Crypto\deploy\windows\inspect_bithumb_live_portfolio_status_latest.ps1")
STATUS_SCRIPT_PATH = Path(r"C:\AI\Crypto\deploy\windows\inspect_bithumb_live_portfolio_status.ps1")


def _recent_run_logged_at_utc(minutes_ago: int = 1) -> str:
    return (datetime.now(UTC) - timedelta(minutes=minutes_ago)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_latest_status_script(project_root: Path) -> subprocess.CompletedProcess[str]:
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
        encoding="utf-8",
        errors="replace",
        env=env,
        check=True,
    )


def _run_status_script(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["BITHUMB_LIVE_PORTFOLIO_PROJECT_ROOT"] = str(project_root)
    return subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(STATUS_SCRIPT_PATH),
            *args,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=True,
    )


def test_latest_status_script_reports_snapshot_fields(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    generated_at_local = (datetime.now() - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    _write_json(
        logs_dir / "bithumb_live_portfolio_status_latest.json",
        {
            "generated_at_local": generated_at_local,
            "mode": {
                "refresh_requested": False,
                "include_runs": True,
                "auto_refresh_when_stale": True,
                "effective_refresh": False,
            },
            "auto_refresh": {
                "snapshot_missing": False,
                "snapshot_stale": False,
            },
            "summary": {
                "severity": "WATCH",
                "reason": "prepare_stop",
            },
            "inspect_snapshot": {
                "generated_at_local": generated_at_local,
                "age_seconds": 60.0,
                "stale": False,
            },
            "health_snapshot": {
                "ok": True,
                "last_status": "ok",
                "age_seconds": 30.0,
                "issues": [],
                "position_status": "OPEN",
            },
            "runs_snapshot": {
                "count": 10,
                "latest_logged_at_utc": "2026-04-19T03:30:00Z",
                "latest_age_seconds": 60.0,
                "latest_stale": False,
                "latest_status": "ok",
                "latest_mode": "manage_open_position",
                "latest_last_reason": "threshold_not_hit",
                "latest_current_price_krw": 111300000.0,
                "latest_next_trigger": "partial_stop_loss",
                "latest_next_trigger_distance_pct": -0.11,
                "latest_remaining_position_pct": 100.0,
            },
            "inspect": {
                "generated_at_local": generated_at_local,
                "status": {
                    "label": "NORMAL",
                    "action_hint": "PREPARE_STOP",
                    "operator_alert_required": False,
                    "operator_alert_escalation": "NONE",
                },
                "event": {
                    "next_trigger_stage": "partial_stop_loss",
                },
            },
        },
    )
    (logs_dir / "bithumb_live_portfolio_status_latest.txt").write_text(
        "status_at=test | effective_refresh=False | action_hint=PREPARE_STOP",
        encoding="utf-8",
    )

    result = _run_latest_status_script(tmp_path)

    assert "snapshot.exists=True" in result.stdout
    assert "snapshot.stale=False" in result.stdout
    assert "inspect.generated_at_local=" in result.stdout
    assert "inspect.stale=False" in result.stdout
    assert "mode.include_runs=True" in result.stdout
    assert "mode.auto_refresh_when_stale=True" in result.stdout
    assert "summary.severity=WATCH" in result.stdout
    assert "summary.reason=prepare_stop" in result.stdout
    assert "health.ok=True" in result.stdout
    assert "health.last_status=ok" in result.stdout
    assert "health.issues=none" in result.stdout
    assert "health.position_status=OPEN" in result.stdout
    assert "runs.count=10" in result.stdout
    assert "run.age_seconds=60" in result.stdout
    assert "run.stale=False" in result.stdout
    assert "run.status=ok" in result.stdout
    assert "run.mode=manage_open_position" in result.stdout
    assert "run.next_trigger=partial_stop_loss" in result.stdout
    assert "status.label=NORMAL" in result.stdout
    assert "status.action_hint=PREPARE_STOP" in result.stdout
    assert "event.next_trigger=partial_stop_loss" in result.stdout
    assert "--- status latest text ---" in result.stdout


def test_latest_status_script_marks_snapshot_stale(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    generated_at_local = (datetime.now() - timedelta(minutes=45)).replace(microsecond=0).isoformat()
    _write_json(
        logs_dir / "bithumb_live_portfolio_status_latest.json",
        {
            "generated_at_local": generated_at_local,
            "mode": {
                "refresh_requested": False,
                "include_runs": False,
                "auto_refresh_when_stale": True,
                "effective_refresh": True,
            },
            "auto_refresh": {
                "snapshot_missing": False,
                "snapshot_stale": True,
            },
            "summary": {
                "severity": "ALERT",
                "reason": "health_degraded",
            },
            "inspect_snapshot": {
                "generated_at_local": generated_at_local,
                "age_seconds": 2700.0,
                "stale": True,
            },
            "health_snapshot": {
                "ok": False,
                "last_status": "error",
                "age_seconds": 120.0,
                "issues": ["stale_run_log", "last_run_not_ok"],
                "position_status": "OPEN",
            },
            "runs_snapshot": {
                "count": 3,
                "latest_logged_at_utc": "2026-04-19T03:30:00Z",
                "latest_age_seconds": 2700.0,
                "latest_stale": True,
                "latest_status": "ok",
                "latest_mode": "manage_open_position",
                "latest_last_reason": "threshold_not_hit",
                "latest_current_price_krw": 111300000.0,
                "latest_next_trigger": "partial_stop_loss",
                "latest_next_trigger_distance_pct": -0.11,
                "latest_remaining_position_pct": 100.0,
            },
            "inspect": {
                "generated_at_local": generated_at_local,
                "status": {
                    "label": "ALERT",
                    "action_hint": "WATCH_STOP",
                    "operator_alert_required": True,
                    "operator_alert_escalation": "PROLONGED",
                },
                "event": {
                    "next_trigger_stage": "partial_stop_loss",
                },
            },
        },
    )

    result = _run_latest_status_script(tmp_path)

    assert "snapshot.exists=True" in result.stdout
    assert "snapshot.stale=True" in result.stdout
    assert "inspect.generated_at_local=" in result.stdout
    assert "inspect.stale=True" in result.stdout
    assert "mode.effective_refresh=True" in result.stdout
    assert "summary.severity=ALERT" in result.stdout
    assert "auto_refresh.snapshot_stale=True" in result.stdout
    assert "health.ok=False" in result.stdout
    assert "health.last_status=error" in result.stdout
    assert "health.issues=stale_run_log,last_run_not_ok" in result.stdout
    assert "runs.count=3" in result.stdout
    assert "run.age_seconds=2700" in result.stdout
    assert "run.stale=True" in result.stdout
    assert "run.status=ok" in result.stdout
    assert "status.action_hint=WATCH_STOP" in result.stdout
    assert "status.operator_alert_required=True" in result.stdout
    assert "status.operator_alert_escalation=PROLONGED" in result.stdout


def test_latest_status_script_keeps_json_and_text_summary_in_sync(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    generated_at_local = (datetime.now() - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    _write_json(
        logs_dir / "bithumb_live_portfolio_status_latest.json",
        {
            "generated_at_local": generated_at_local,
            "mode": {
                "refresh_requested": False,
                "include_runs": True,
                "auto_refresh_when_stale": False,
                "effective_refresh": False,
            },
            "auto_refresh": {
                "snapshot_missing": None,
                "snapshot_stale": None,
            },
            "summary": {
                "severity": "OK",
                "reason": "normal",
            },
            "inspect_snapshot": {
                "generated_at_local": generated_at_local,
                "age_seconds": 60.0,
                "stale": False,
            },
            "health_snapshot": {
                "ok": True,
                "last_status": "ok",
                "age_seconds": 30.0,
                "issues": [],
                "position_status": "OPEN",
            },
            "runs_snapshot": {
                "count": 10,
                "latest_logged_at_utc": "2026-04-19T03:30:00Z",
                "latest_age_seconds": 60.0,
                "latest_stale": False,
                "latest_status": "ok",
                "latest_mode": "manage_open_position",
                "latest_last_reason": "threshold_not_hit",
                "latest_current_price_krw": 111300000.0,
                "latest_next_trigger": "partial_stop_loss",
                "latest_next_trigger_distance_pct": -0.11,
                "latest_remaining_position_pct": 100.0,
            },
            "inspect": {
                "generated_at_local": generated_at_local,
                "status": {
                    "label": "NORMAL",
                    "action_hint": "HOLD_MONITOR",
                    "operator_alert_required": False,
                    "operator_alert_escalation": "NONE",
                },
                "event": {
                    "next_trigger_stage": "partial_stop_loss",
                },
            },
        },
    )
    (logs_dir / "bithumb_live_portfolio_status_latest.txt").write_text(
        "status_at=test | effective_refresh=False | include_runs=True | action_hint=HOLD_MONITOR | operator_alert_required=False | operator_alert_escalation=NONE | next_trigger=partial_stop_loss",
        encoding="utf-8",
    )

    result = _run_latest_status_script(tmp_path)

    assert "mode.include_runs=True" in result.stdout
    assert "status.action_hint=HOLD_MONITOR" in result.stdout
    assert "summary.severity=OK" in result.stdout
    assert "status.operator_alert_required=False" in result.stdout
    assert "status.operator_alert_escalation=NONE" in result.stdout
    assert "health.ok=True" in result.stdout
    assert "health.last_status=ok" in result.stdout
    assert "health.issues=none" in result.stdout
    assert "runs.count=10" in result.stdout
    assert "run.age_seconds=60" in result.stdout
    assert "run.stale=False" in result.stdout
    assert "run.status=ok" in result.stdout
    assert "event.next_trigger=partial_stop_loss" in result.stdout
    assert "--- status latest text ---" in result.stdout
    assert "action_hint=HOLD_MONITOR" in result.stdout
    assert "operator_alert_required=False" in result.stdout
    assert "operator_alert_escalation=NONE" in result.stdout
    assert "next_trigger=partial_stop_loss" in result.stdout


def test_latest_status_script_reads_snapshot_generated_by_status_script(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    generated_at_local = (datetime.now() - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    recent_run_logged_at_utc = _recent_run_logged_at_utc()
    _write_json(
        logs_dir / "bithumb_live_portfolio_inspect_latest.json",
        {
            "generated_at_local": generated_at_local,
            "status": {
                "label": "NORMAL",
                "action_hint": "PREPARE_STOP",
                "trigger_proximity": "NEAR",
                "reentry": "NONE",
                "run_coverage": "LEGACY_MIXED",
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
                    "logged_at_utc": recent_run_logged_at_utc,
                    "status": "ok",
                    "mode": "manage_open_position",
                    "last_reason": "threshold_not_hit",
                    "current_price_krw": 111300000.0,
                    "next_trigger_stage": "partial_stop_loss",
                    "next_trigger_distance_pct": -0.11,
                    "remaining_position_pct": 100.0,
                },
            },
        },
    )
    _write_json(
        logs_dir / "bithumb_live_portfolio_health_latest.json",
        {
            "ok": True,
            "last_status": "ok",
            "age_seconds": 30.0,
            "issues": [],
            "position_status": "OPEN",
        },
    )
    (logs_dir / "bithumb_live_portfolio_inspect_latest.txt").write_text(
        "inspect_at=test | status=NORMAL | action_hint=PREPARE_STOP",
        encoding="utf-8",
    )

    _run_status_script(tmp_path, "-IncludeRuns")
    result = _run_latest_status_script(tmp_path)

    assert "snapshot.exists=True" in result.stdout
    assert "summary.severity=WATCH" in result.stdout
    assert "inspect.generated_at_local=" in result.stdout
    assert "inspect.stale=False" in result.stdout
    assert "mode.include_runs=True" in result.stdout
    assert "health.ok=True" in result.stdout
    assert "runs.count=10" in result.stdout
    assert "run.stale=False" in result.stdout
    assert "run.status=ok" in result.stdout
    assert "status.label=NORMAL" in result.stdout
    assert "status.action_hint=PREPARE_STOP" in result.stdout
    assert "status.operator_alert_required=False" in result.stdout
    assert "event.next_trigger=partial_stop_loss" in result.stdout
    assert "--- status latest text ---" in result.stdout


def test_latest_status_script_prefers_stored_inspect_snapshot_metadata(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    status_generated_at_local = (datetime.now() - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    old_inspect_generated_at_local = (datetime.now() - timedelta(minutes=45)).replace(microsecond=0).isoformat()
    _write_json(
        logs_dir / "bithumb_live_portfolio_status_latest.json",
        {
            "generated_at_local": status_generated_at_local,
            "mode": {
                "refresh_requested": False,
                "include_runs": True,
                "auto_refresh_when_stale": False,
                "effective_refresh": False,
            },
            "auto_refresh": {
                "snapshot_missing": None,
                "snapshot_stale": None,
            },
            "summary": {
                "severity": "WATCH",
                "reason": "prepare_stop",
            },
            "inspect_snapshot": {
                "generated_at_local": status_generated_at_local,
                "age_seconds": 60.0,
                "stale": False,
            },
            "health_snapshot": {
                "ok": True,
                "last_status": "ok",
                "age_seconds": 30.0,
                "issues": [],
                "position_status": "OPEN",
            },
            "runs_snapshot": {
                "count": 10,
                "latest_logged_at_utc": "2026-04-19T03:30:00Z",
                "latest_age_seconds": 60.0,
                "latest_stale": False,
                "latest_status": "ok",
                "latest_mode": "manage_open_position",
                "latest_last_reason": "threshold_not_hit",
                "latest_current_price_krw": 111300000.0,
                "latest_next_trigger": "partial_stop_loss",
                "latest_next_trigger_distance_pct": -0.11,
                "latest_remaining_position_pct": 100.0,
            },
            "inspect": {
                "generated_at_local": old_inspect_generated_at_local,
                "status": {
                    "label": "NORMAL",
                    "action_hint": "PREPARE_STOP",
                    "operator_alert_required": False,
                    "operator_alert_escalation": "NONE",
                },
                "event": {
                    "next_trigger_stage": "partial_stop_loss",
                },
            },
        },
    )

    result = _run_latest_status_script(tmp_path)

    assert f"inspect.generated_at_local={status_generated_at_local}" in result.stdout
    assert "inspect.age_seconds=60" in result.stdout
    assert "inspect.stale=False" in result.stdout


def test_latest_status_script_recomputes_summary_when_missing(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    generated_at_local = (datetime.now() - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    _write_json(
        logs_dir / "bithumb_live_portfolio_status_latest.json",
        {
            "generated_at_local": generated_at_local,
            "mode": {
                "refresh_requested": False,
                "include_runs": True,
                "auto_refresh_when_stale": False,
                "effective_refresh": False,
            },
            "auto_refresh": {
                "snapshot_missing": None,
                "snapshot_stale": None,
            },
            "inspect_snapshot": {
                "generated_at_local": generated_at_local,
                "age_seconds": 60.0,
                "stale": False,
            },
            "health_snapshot": {
                "ok": True,
                "last_status": "ok",
                "age_seconds": 30.0,
                "issues": [],
                "position_status": "OPEN",
            },
            "runs_snapshot": {
                "count": 10,
                "latest_logged_at_utc": "2026-04-19T03:30:00Z",
                "latest_age_seconds": 60.0,
                "latest_stale": False,
                "latest_status": "ok",
                "latest_mode": "manage_open_position",
                "latest_last_reason": "threshold_not_hit",
                "latest_current_price_krw": 111300000.0,
                "latest_next_trigger": "partial_stop_loss",
                "latest_next_trigger_distance_pct": -0.11,
                "latest_remaining_position_pct": 100.0,
            },
            "inspect": {
                "generated_at_local": generated_at_local,
                "status": {
                    "label": "NORMAL",
                    "action_hint": "PREPARE_STOP",
                    "trigger_proximity": "NEAR",
                    "operator_alert_required": False,
                    "operator_alert_escalation": "NONE",
                },
                "event": {
                    "next_trigger_stage": "partial_stop_loss",
                },
            },
        },
    )

    result = _run_latest_status_script(tmp_path)

    assert "summary.severity=WATCH" in result.stdout
    assert "summary.reason=prepare_stop" in result.stdout


def test_latest_status_script_handles_missing_health_snapshot_in_legacy_snapshot(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    generated_at_local = (datetime.now() - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    _write_json(
        logs_dir / "bithumb_live_portfolio_status_latest.json",
        {
            "generated_at_local": generated_at_local,
            "mode": {
                "refresh_requested": False,
                "include_runs": True,
                "auto_refresh_when_stale": False,
                "effective_refresh": False,
            },
            "inspect_snapshot": {
                "generated_at_local": generated_at_local,
                "age_seconds": 60.0,
                "stale": False,
            },
            "inspect": {
                "generated_at_local": generated_at_local,
                "status": {
                    "label": "NORMAL",
                    "action_hint": "PREPARE_STOP",
                    "trigger_proximity": "NEAR",
                    "operator_alert_required": False,
                    "operator_alert_escalation": "NONE",
                },
                "event": {
                    "next_trigger_stage": "partial_stop_loss",
                },
                "runs": {
                    "count": 1,
                    "latest": {
                        "logged_at_utc": _recent_run_logged_at_utc(),
                        "status": "ok",
                        "mode": "manage_open_position",
                        "last_reason": "threshold_not_hit",
                        "current_price_krw": 111300000.0,
                        "next_trigger_stage": "partial_stop_loss",
                        "next_trigger_distance_pct": -0.11,
                        "remaining_position_pct": 100.0,
                    },
                },
            },
        },
    )

    result = _run_latest_status_script(tmp_path)

    assert "summary.severity=WATCH" in result.stdout
    assert "summary.reason=prepare_stop" in result.stdout
    assert "health.ok=-" in result.stdout
    assert "health.issues=-" in result.stdout


def test_latest_status_script_handles_minimal_legacy_inspect_snapshot(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    generated_at_local = (datetime.now() - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    _write_json(
        logs_dir / "bithumb_live_portfolio_status_latest.json",
        {
            "generated_at_local": generated_at_local,
            "inspect": {
                "generated_at_local": generated_at_local,
            },
        },
    )

    result = _run_latest_status_script(tmp_path)

    assert "snapshot.exists=True" in result.stdout
    assert "summary.severity=OK" in result.stdout
    assert "summary.reason=normal" in result.stdout
    assert "mode.include_runs=-" in result.stdout
    assert "health.ok=-" in result.stdout
    assert "runs.count=-" in result.stdout
    assert "status.label=-" in result.stdout
    assert "status.action_hint=-" in result.stdout
    assert "event.next_trigger=-" in result.stdout
