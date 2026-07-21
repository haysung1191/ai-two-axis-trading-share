from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path


SCRIPT_PATH = Path(r"C:\AI\Crypto\deploy\windows\inspect_bithumb_live_portfolio_status.ps1")


def _recent_run_logged_at_utc(minutes_ago: int = 1) -> str:
    return (datetime.now(UTC) - timedelta(minutes=minutes_ago)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_status_script(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["BITHUMB_LIVE_PORTFOLIO_PROJECT_ROOT"] = str(project_root)
    return subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT_PATH),
            *args,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=True,
    )


def test_status_script_uses_latest_snapshot_by_default(tmp_path: Path) -> None:
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

    result = _run_status_script(tmp_path)

    assert "=== Bithumb Live Portfolio Status ===" in result.stdout
    assert "mode.refresh=False" in result.stdout
    assert "--- latest inspect ---" in result.stdout
    assert "=== Bithumb Live Portfolio Latest Inspect ===" in result.stdout
    assert "status.action_hint=PREPARE_STOP" in result.stdout
    status_json = json.loads((logs_dir / "bithumb_live_portfolio_status_latest.json").read_text(encoding="utf-8-sig"))
    assert status_json["mode"]["refresh_requested"] is False
    assert status_json["mode"]["effective_refresh"] is False
    assert status_json["summary"]["severity"] == "WATCH"
    assert status_json["summary"]["reason"] == "prepare_stop"
    assert status_json["inspect_snapshot"]["generated_at_local"] == generated_at_local
    assert isinstance(status_json["inspect_snapshot"]["age_seconds"], (int, float))
    assert status_json["inspect_snapshot"]["stale"] is False
    assert status_json["health_snapshot"]["ok"] is True
    assert status_json["health_snapshot"]["last_status"] == "ok"
    assert status_json["health_snapshot"]["position_status"] == "OPEN"
    assert status_json["runs_snapshot"]["count"] == 10
    assert isinstance(status_json["runs_snapshot"]["latest_age_seconds"], (int, float))
    assert status_json["runs_snapshot"]["latest_stale"] is False
    assert status_json["runs_snapshot"]["latest_status"] == "ok"
    assert status_json["runs_snapshot"]["latest_mode"] == "manage_open_position"
    assert status_json["runs_snapshot"]["latest_next_trigger"] == "partial_stop_loss"
    assert status_json["inspect"]["generated_at_local"] == generated_at_local
    assert status_json["inspect"]["status"]["label"] == "NORMAL"
    assert status_json["inspect"]["status"]["action_hint"] == "PREPARE_STOP"
    assert status_json["inspect"]["event"]["next_trigger_stage"] == "partial_stop_loss"
    status_text = (logs_dir / "bithumb_live_portfolio_status_latest.txt").read_text(encoding="utf-8")
    assert "effective_refresh=False" in status_text
    assert "summary_severity=WATCH" in status_text
    assert "summary_reason=prepare_stop" in status_text
    assert "inspect_generated_at=" in status_text
    assert "inspect_age_seconds=" in status_text
    assert "inspect_stale=False" in status_text
    assert "health_ok=True" in status_text
    assert "health_last_status=ok" in status_text
    assert "health_issues=none" in status_text
    assert "health_position_status=OPEN" in status_text
    assert "runs_count=10" in status_text
    assert "run_status=ok" in status_text
    assert "run_mode=manage_open_position" in status_text
    assert "run_age_seconds=" in status_text
    assert "run_stale=False" in status_text
    assert "run_next_trigger=partial_stop_loss" in status_text
    assert "action_hint=PREPARE_STOP" in status_text
    status_bytes = (logs_dir / "bithumb_live_portfolio_status_latest.txt").read_bytes()
    assert status_bytes[:3] != b"\xef\xbb\xbf"


def test_status_script_can_refresh_and_include_runs(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    recent_run_logged_at_utc = _recent_run_logged_at_utc()
    _write_json(
        logs_dir / "bithumb_live_portfolio_health_latest.json",
        {
            "ok": True,
            "last_status": "ok",
            "age_seconds": 1,
            "symbol": "BTC",
            "position_status": "OPEN",
            "issues": [],
        },
    )
    _write_json(
        logs_dir / "bithumb_live_portfolio_event_latest.json",
        {
            "event_type": "no_new_event",
            "last_reason": "threshold_not_hit",
            "estimated_realized_pnl_krw": None,
            "estimated_unrealized_pnl_krw": -120.0,
            "current_price_krw": 111300000.0,
            "next_trigger_stage": "partial_stop_loss",
            "next_trigger_price_krw": 111177000.0,
            "next_trigger_distance_krw": -123000.0,
            "next_trigger_distance_pct": -0.11,
            "remaining_position_pct": 100.0,
            "sold_volume": 0.0,
            "cumulative_realized_pnl_krw": None,
            "cumulative_realized_return_pct": None,
            "reentry_ready": None,
        },
    )
    _write_json(
        logs_dir / "bithumb_live_portfolio_state.json",
        {
            "status": "OPEN",
            "remaining_volume": 0.00088869,
            "entry_price_krw": 112300000.0,
            "symbol": "BTC",
        },
    )
    (logs_dir / "bithumb_live_portfolio_manager_runs.jsonl").write_text(
        json.dumps(
            {
                "logged_at_utc": recent_run_logged_at_utc,
                "status": "ok",
                "mode": "manage_open_position",
                "position_status": "OPEN",
                "last_reason": "threshold_not_hit",
                "current_price_krw": 111300000.0,
                "next_trigger_stage": "partial_stop_loss",
                "next_trigger_distance_pct": -0.11,
                "remaining_position_pct": 100.0,
                "reentry_ready": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_status_script(tmp_path, "-Refresh", "-IncludeRuns")

    assert "mode.refresh=True" in result.stdout
    assert "mode.include_runs=True" in result.stdout
    assert "--- refresh inspect ---" in result.stdout
    assert "=== Bithumb Live Portfolio Inspect ===" in result.stdout
    assert "--- runs inspect ---" in result.stdout
    assert "=== Bithumb Live Portfolio Runs Inspect ===" in result.stdout
    assert "latest.next_trigger=partial_stop_loss" in result.stdout
    status_json = json.loads((logs_dir / "bithumb_live_portfolio_status_latest.json").read_text(encoding="utf-8-sig"))
    assert status_json["mode"]["refresh_requested"] is True
    assert status_json["mode"]["include_runs"] is True
    assert status_json["mode"]["effective_refresh"] is True
    assert status_json["summary"]["severity"] == "ALERT"
    assert status_json["health_snapshot"]["ok"] is True
    assert status_json["health_snapshot"]["last_status"] == "ok"
    assert status_json["health_snapshot"]["position_status"] == "OPEN"
    assert isinstance(status_json["runs_snapshot"]["latest_age_seconds"], (int, float))
    assert status_json["runs_snapshot"]["latest_stale"] is False
    assert status_json["runs_snapshot"]["latest_status"] == "ok"
    assert status_json["runs_snapshot"]["latest_mode"] == "manage_open_position"
    assert status_json["inspect_snapshot"]["generated_at_local"] is not None
    assert isinstance(status_json["inspect_snapshot"]["age_seconds"], (int, float))
    assert status_json["inspect_snapshot"]["stale"] is False
    assert status_json["inspect"]["status"]["action_hint"] == "WATCH_STOP"
    status_text = (logs_dir / "bithumb_live_portfolio_status_latest.txt").read_text(encoding="utf-8")
    assert "effective_refresh=True" in status_text
    assert "summary_severity=ALERT" in status_text
    assert "inspect_age_seconds=" in status_text
    assert "inspect_stale=False" in status_text
    assert "health_ok=True" in status_text
    assert "health_last_status=ok" in status_text
    assert "health_issues=none" in status_text
    assert "run_age_seconds=" in status_text
    assert "run_stale=False" in status_text
    assert "run_status=ok" in status_text
    assert "run_mode=manage_open_position" in status_text
    assert "include_runs=True" in status_text
    status_bytes = (logs_dir / "bithumb_live_portfolio_status_latest.txt").read_bytes()
    assert status_bytes[:3] != b"\xef\xbb\xbf"


def test_status_script_auto_refreshes_when_snapshot_is_stale(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    generated_at_local = (datetime.now() - timedelta(minutes=45)).replace(microsecond=0).isoformat()
    recent_run_logged_at_utc = _recent_run_logged_at_utc()
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
            "age_seconds": 1,
            "symbol": "BTC",
            "position_status": "OPEN",
            "issues": [],
        },
    )
    _write_json(
        logs_dir / "bithumb_live_portfolio_event_latest.json",
        {
            "event_type": "no_new_event",
            "last_reason": "threshold_not_hit",
            "estimated_realized_pnl_krw": None,
            "estimated_unrealized_pnl_krw": -120.0,
            "current_price_krw": 111300000.0,
            "next_trigger_stage": "partial_stop_loss",
            "next_trigger_price_krw": 111177000.0,
            "next_trigger_distance_krw": -123000.0,
            "next_trigger_distance_pct": -0.11,
            "remaining_position_pct": 100.0,
            "sold_volume": 0.0,
            "cumulative_realized_pnl_krw": None,
            "cumulative_realized_return_pct": None,
            "reentry_ready": None,
        },
    )
    _write_json(
        logs_dir / "bithumb_live_portfolio_state.json",
        {
            "status": "OPEN",
            "remaining_volume": 0.00088869,
            "entry_price_krw": 112300000.0,
            "symbol": "BTC",
        },
    )
    (logs_dir / "bithumb_live_portfolio_manager_runs.jsonl").write_text(
        json.dumps(
            {
                "logged_at_utc": recent_run_logged_at_utc,
                "status": "ok",
                "mode": "manage_open_position",
                "position_status": "OPEN",
                "last_reason": "threshold_not_hit",
                "current_price_krw": 111300000.0,
                "next_trigger_stage": "partial_stop_loss",
                "next_trigger_distance_pct": -0.11,
                "remaining_position_pct": 100.0,
                "reentry_ready": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_status_script(tmp_path, "-AutoRefreshWhenStale")

    assert "mode.auto_refresh_when_stale=True" in result.stdout
    assert "auto_refresh.snapshot_missing=False" in result.stdout
    assert "auto_refresh.snapshot_stale=True" in result.stdout
    assert "--- refresh inspect ---" in result.stdout
    assert "=== Bithumb Live Portfolio Inspect ===" in result.stdout
    status_json = json.loads((logs_dir / "bithumb_live_portfolio_status_latest.json").read_text(encoding="utf-8-sig"))
    assert status_json["mode"]["auto_refresh_when_stale"] is True
    assert status_json["mode"]["effective_refresh"] is True
    assert status_json["auto_refresh"]["snapshot_missing"] is False
    assert status_json["auto_refresh"]["snapshot_stale"] is True
    assert status_json["health_snapshot"]["ok"] is True
    assert status_json["inspect_snapshot"]["generated_at_local"] is not None
    assert isinstance(status_json["inspect_snapshot"]["age_seconds"], (int, float))
    assert status_json["inspect_snapshot"]["stale"] is False


def test_status_script_auto_refreshes_when_snapshot_is_missing(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    recent_run_logged_at_utc = _recent_run_logged_at_utc()
    _write_json(
        logs_dir / "bithumb_live_portfolio_health_latest.json",
        {
            "ok": True,
            "last_status": "ok",
            "age_seconds": 1,
            "symbol": "BTC",
            "position_status": "OPEN",
            "issues": [],
        },
    )
    _write_json(
        logs_dir / "bithumb_live_portfolio_event_latest.json",
        {
            "event_type": "no_new_event",
            "last_reason": "threshold_not_hit",
            "estimated_realized_pnl_krw": None,
            "estimated_unrealized_pnl_krw": -120.0,
            "current_price_krw": 111300000.0,
            "next_trigger_stage": "partial_stop_loss",
            "next_trigger_price_krw": 111177000.0,
            "next_trigger_distance_krw": -123000.0,
            "next_trigger_distance_pct": -0.11,
            "remaining_position_pct": 100.0,
            "sold_volume": 0.0,
            "cumulative_realized_pnl_krw": None,
            "cumulative_realized_return_pct": None,
            "reentry_ready": None,
        },
    )
    _write_json(
        logs_dir / "bithumb_live_portfolio_state.json",
        {
            "status": "OPEN",
            "remaining_volume": 0.00088869,
            "entry_price_krw": 112300000.0,
            "symbol": "BTC",
        },
    )
    (logs_dir / "bithumb_live_portfolio_manager_runs.jsonl").write_text(
        json.dumps(
            {
                "logged_at_utc": recent_run_logged_at_utc,
                "status": "ok",
                "mode": "manage_open_position",
                "position_status": "OPEN",
                "last_reason": "threshold_not_hit",
                "current_price_krw": 111300000.0,
                "next_trigger_stage": "partial_stop_loss",
                "next_trigger_distance_pct": -0.11,
                "remaining_position_pct": 100.0,
                "reentry_ready": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_status_script(tmp_path, "-AutoRefreshWhenStale")

    assert "mode.auto_refresh_when_stale=True" in result.stdout
    assert "auto_refresh.snapshot_missing=True" in result.stdout
    assert "auto_refresh.snapshot_stale=True" in result.stdout
    assert "--- refresh inspect ---" in result.stdout
    assert "=== Bithumb Live Portfolio Inspect ===" in result.stdout
    status_json = json.loads((logs_dir / "bithumb_live_portfolio_status_latest.json").read_text(encoding="utf-8-sig"))
    assert status_json["mode"]["auto_refresh_when_stale"] is True
    assert status_json["mode"]["effective_refresh"] is True
    assert status_json["auto_refresh"]["snapshot_missing"] is True
    assert status_json["auto_refresh"]["snapshot_stale"] is True
    assert status_json["health_snapshot"]["ok"] is True
    assert status_json["inspect_snapshot"]["generated_at_local"] is not None
    assert isinstance(status_json["inspect_snapshot"]["age_seconds"], (int, float))
    assert status_json["inspect_snapshot"]["stale"] is False


def test_status_script_keeps_status_snapshot_and_text_in_sync(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    generated_at_local = (datetime.now() - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    recent_run_logged_at_utc = _recent_run_logged_at_utc()
    _write_json(
        logs_dir / "bithumb_live_portfolio_inspect_latest.json",
        {
            "generated_at_local": generated_at_local,
            "status": {
                "label": "ALERT",
                "action_hint": "WATCH_STOP",
                "trigger_proximity": "URGENT",
                "reentry": "NONE",
                "run_coverage": "ENRICHED",
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
                "count": 7,
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
            "ok": False,
            "last_status": "error",
            "age_seconds": 95.0,
            "issues": ["stale_run_log", "last_run_not_ok"],
            "position_status": "OPEN",
        },
    )
    (logs_dir / "bithumb_live_portfolio_inspect_latest.txt").write_text(
        "inspect_at=test | status=ALERT | action_hint=WATCH_STOP",
        encoding="utf-8",
    )

    _run_status_script(tmp_path, "-IncludeRuns")

    status_json = json.loads((logs_dir / "bithumb_live_portfolio_status_latest.json").read_text(encoding="utf-8-sig"))
    status_text = (logs_dir / "bithumb_live_portfolio_status_latest.txt").read_text(encoding="utf-8")

    assert status_json["inspect_snapshot"]["generated_at_local"] == generated_at_local
    assert isinstance(status_json["inspect_snapshot"]["age_seconds"], (int, float))
    assert status_json["inspect_snapshot"]["stale"] is False
    assert status_json["inspect"]["status"]["label"] == "ALERT"
    assert status_json["inspect"]["status"]["action_hint"] == "WATCH_STOP"
    assert status_json["inspect"]["status"]["operator_alert_required"] is True
    assert status_json["inspect"]["status"]["operator_alert_escalation"] == "PROLONGED"
    assert status_json["health_snapshot"]["ok"] is False
    assert status_json["health_snapshot"]["last_status"] == "error"
    assert status_json["health_snapshot"]["issues"] == ["stale_run_log", "last_run_not_ok"]
    assert status_json["summary"]["severity"] == "ALERT"
    assert status_json["summary"]["reason"] == "health_degraded"
    assert status_json["runs_snapshot"]["count"] == 7
    assert isinstance(status_json["runs_snapshot"]["latest_age_seconds"], (int, float))
    assert status_json["runs_snapshot"]["latest_stale"] is False
    assert status_json["runs_snapshot"]["latest_status"] == "ok"
    assert status_json["runs_snapshot"]["latest_mode"] == "manage_open_position"
    assert status_json["inspect"]["event"]["next_trigger_stage"] == "partial_stop_loss"
    assert "inspect_generated_at=" in status_text
    assert "inspect_age_seconds=" in status_text
    assert "inspect_stale=False" in status_text
    assert "health_ok=False" in status_text
    assert "summary_severity=ALERT" in status_text
    assert "summary_reason=health_degraded" in status_text
    assert "health_last_status=error" in status_text
    assert "health_issues=stale_run_log,last_run_not_ok" in status_text
    assert "runs_count=7" in status_text
    assert "run_age_seconds=" in status_text
    assert "run_stale=False" in status_text
    assert "run_status=ok" in status_text
    assert "run_mode=manage_open_position" in status_text
    assert "status=ALERT" in status_text
    assert "action_hint=WATCH_STOP" in status_text
    assert "operator_alert_required=True" in status_text
    assert "operator_alert_escalation=PROLONGED" in status_text
    assert "next_trigger=partial_stop_loss" in status_text
    status_bytes = (logs_dir / "bithumb_live_portfolio_status_latest.txt").read_bytes()
    assert status_bytes[:3] != b"\xef\xbb\xbf"


def test_status_script_persists_complete_inspect_snapshot_contract(tmp_path: Path) -> None:
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

    _run_status_script(tmp_path)

    status_json = json.loads((logs_dir / "bithumb_live_portfolio_status_latest.json").read_text(encoding="utf-8-sig"))
    inspect_snapshot = status_json["inspect_snapshot"]
    health_snapshot = status_json["health_snapshot"]
    runs_snapshot = status_json["runs_snapshot"]

    assert set(inspect_snapshot) == {"generated_at_local", "age_seconds", "stale"}
    assert set(health_snapshot) == {"ok", "last_status", "age_seconds", "issues", "position_status"}
    assert set(runs_snapshot) == {
        "count",
        "latest_logged_at_utc",
        "latest_age_seconds",
        "latest_stale",
        "latest_status",
        "latest_mode",
        "latest_last_reason",
        "latest_current_price_krw",
        "latest_next_trigger",
        "latest_next_trigger_distance_pct",
        "latest_remaining_position_pct",
    }
    assert inspect_snapshot["generated_at_local"] == generated_at_local
    assert isinstance(inspect_snapshot["age_seconds"], (int, float))
    assert inspect_snapshot["stale"] is False
    assert health_snapshot["ok"] is True
    assert health_snapshot["last_status"] == "ok"
    assert health_snapshot["issues"] == []
    assert runs_snapshot["count"] == 10
    assert isinstance(runs_snapshot["latest_age_seconds"], (int, float))
    assert runs_snapshot["latest_stale"] is False
    assert runs_snapshot["latest_status"] == "ok"
    assert status_json["summary"]["severity"] == "WATCH"
