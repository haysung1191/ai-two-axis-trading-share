from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


SCRIPT_PATH = Path(r"C:\AI\Crypto\deploy\windows\inspect_bithumb_live_portfolio.ps1")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_inspect_script(project_root: Path) -> subprocess.CompletedProcess[str]:
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


def test_inspect_script_creates_operator_alert_for_watch_stop(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
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
            "estimated_unrealized_pnl_krw": -100.0,
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
        },
    )
    (logs_dir / "bithumb_live_portfolio_manager_runs.jsonl").write_text(
        json.dumps(
            {
                "logged_at_utc": "2026-04-19T03:30:00Z",
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

    result = _run_inspect_script(tmp_path)

    assert "status.action_hint=WATCH_STOP" in result.stdout
    assert "status.operator_alert_required=True" in result.stdout
    assert "status.operator_alert_transition=NEW" in result.stdout
    assert "status.operator_alert_escalation=NEW" in result.stdout
    assert "status.operator_alert_occurrence_count=1" in result.stdout
    assert "operator_alert.required=True" in result.stdout
    inspect_json = json.loads((logs_dir / "bithumb_live_portfolio_inspect_latest.json").read_text(encoding="utf-8-sig"))
    assert inspect_json["status"]["label"] == "NORMAL"
    assert inspect_json["status"]["action_hint"] == "WATCH_STOP"
    assert inspect_json["status"]["operator_alert_required"] is True
    assert inspect_json["status"]["operator_alert_escalation"] == "NEW"
    assert inspect_json["status"]["operator_alert_occurrence_count"] == 1
    assert inspect_json["event"]["next_trigger_stage"] == "partial_stop_loss"
    assert inspect_json["runs"]["count"] == 1
    inspect_text = (logs_dir / "bithumb_live_portfolio_inspect_latest.txt").read_text(encoding="utf-8")
    assert "action_hint=WATCH_STOP" in inspect_text
    assert "operator_alert_required=True" in inspect_text
    assert "operator_alert_escalation=NEW" in inspect_text
    assert "occurrence_count=1" in inspect_text
    alert_json = json.loads((logs_dir / "bithumb_live_portfolio_operator_alert.json").read_text(encoding="utf-8-sig"))
    assert alert_json["action_hint"] == "WATCH_STOP"
    assert alert_json["transition_state"] == "NEW"
    assert alert_json["alert_occurrence_count"] == 1
    assert alert_json["escalation_level"] == "NEW"
    assert alert_json["first_detected_local"] == alert_json["generated_at_local"]
    assert alert_json["event_next_trigger"] == "partial_stop_loss"
    assert len(alert_json["recent_runs"]) == 1
    assert alert_json["recent_runs"][0]["last_reason"] == "threshold_not_hit"
    alert_text = (logs_dir / "bithumb_live_portfolio_operator_alert.txt").read_text(encoding="utf-8")
    assert "operator_alert=WATCH_STOP" in alert_text
    assert "transition=NEW" in alert_text
    assert "escalation=NEW" in alert_text
    assert "occurrence_count=1" in alert_text
    assert "recent_runs=1" in alert_text
    action_hint_json = json.loads((logs_dir / "bithumb_live_portfolio_action_hint_latest.json").read_text(encoding="utf-8-sig"))
    assert action_hint_json["operator_alert_required"] is True
    assert action_hint_json["operator_alert_transition"] == "NEW"
    assert action_hint_json["operator_alert_escalation"] == "NEW"
    assert action_hint_json["operator_alert_occurrence_count"] == 1
    action_hint_text = (logs_dir / "bithumb_live_portfolio_action_hint_latest.txt").read_text(encoding="utf-8")
    assert "operator_alert_required=True" in action_hint_text
    assert "operator_alert_escalation=NEW" in action_hint_text
    assert "occurrence_count=1" in action_hint_text


def test_inspect_script_removes_operator_alert_for_noncritical_hint(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
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
            "estimated_unrealized_pnl_krw": -200.0,
            "current_price_krw": 111950000.0,
            "next_trigger_stage": "partial_stop_loss",
            "next_trigger_price_krw": 111177000.0,
            "next_trigger_distance_krw": -773000.0,
            "next_trigger_distance_pct": -0.69,
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
        },
    )
    (logs_dir / "bithumb_live_portfolio_manager_runs.jsonl").write_text(
        json.dumps(
            {
                "logged_at_utc": "2026-04-19T03:30:00Z",
                "status": "ok",
                "mode": "manage_open_position",
                "position_status": "OPEN",
                "last_reason": "threshold_not_hit",
                "current_price_krw": 111950000.0,
                "next_trigger_stage": "partial_stop_loss",
                "next_trigger_distance_pct": -0.69,
                "remaining_position_pct": 100.0,
                "reentry_ready": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (logs_dir / "bithumb_live_portfolio_operator_alert.json").write_text("{}", encoding="utf-8")
    (logs_dir / "bithumb_live_portfolio_operator_alert.txt").write_text("stale", encoding="utf-8")

    result = _run_inspect_script(tmp_path)

    assert "status.action_hint=PREPARE_STOP" in result.stdout
    assert "status.operator_alert_required=False" in result.stdout
    assert "status.operator_alert_escalation=NONE" in result.stdout
    assert "status.operator_alert_occurrence_count=0" in result.stdout
    assert "operator_alert.required=False" in result.stdout
    inspect_json = json.loads((logs_dir / "bithumb_live_portfolio_inspect_latest.json").read_text(encoding="utf-8-sig"))
    assert inspect_json["status"]["label"] == "NORMAL"
    assert inspect_json["status"]["action_hint"] == "PREPARE_STOP"
    assert inspect_json["status"]["operator_alert_required"] is False
    assert inspect_json["status"]["operator_alert_escalation"] == "NONE"
    assert inspect_json["status"]["operator_alert_occurrence_count"] == 0
    assert inspect_json["runs"]["count"] == 1
    inspect_text = (logs_dir / "bithumb_live_portfolio_inspect_latest.txt").read_text(encoding="utf-8")
    assert "action_hint=PREPARE_STOP" in inspect_text
    assert "operator_alert_required=False" in inspect_text
    assert "operator_alert_escalation=-" in inspect_text
    assert "occurrence_count=-" in inspect_text
    assert not (logs_dir / "bithumb_live_portfolio_operator_alert.json").exists()
    assert not (logs_dir / "bithumb_live_portfolio_operator_alert.txt").exists()
    action_hint_json = json.loads((logs_dir / "bithumb_live_portfolio_action_hint_latest.json").read_text(encoding="utf-8-sig"))
    assert action_hint_json["operator_alert_required"] is False
    assert action_hint_json["operator_alert_transition"] is None
    assert action_hint_json["operator_alert_escalation"] is None
    assert action_hint_json["operator_alert_occurrence_count"] is None
    action_hint_text = (logs_dir / "bithumb_live_portfolio_action_hint_latest.txt").read_text(encoding="utf-8")
    assert "operator_alert_required=False" in action_hint_text
    assert "operator_alert_escalation=-" in action_hint_text
    assert "occurrence_count=-" in action_hint_text


def test_inspect_script_marks_operator_alert_as_ongoing_when_same_condition_repeats(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
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
            "estimated_unrealized_pnl_krw": -90.0,
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
        },
    )
    (logs_dir / "bithumb_live_portfolio_manager_runs.jsonl").write_text(
        json.dumps(
            {
                "logged_at_utc": "2026-04-19T03:31:00Z",
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
    _write_json(
        logs_dir / "bithumb_live_portfolio_operator_alert.json",
        {
            "generated_at_local": "2026-04-19T12:00:00",
            "first_detected_local": "2026-04-19T11:50:00",
            "transition_state": "NEW",
            "action_hint": "WATCH_STOP",
            "event_next_trigger": "partial_stop_loss",
        },
    )

    result = _run_inspect_script(tmp_path)

    assert "status.operator_alert_transition=ONGOING" in result.stdout
    assert "status.operator_alert_escalation=PERSISTING" in result.stdout
    assert "status.operator_alert_occurrence_count=2" in result.stdout
    assert "operator_alert.required=True" in result.stdout
    alert_json = json.loads((logs_dir / "bithumb_live_portfolio_operator_alert.json").read_text(encoding="utf-8-sig"))
    assert alert_json["transition_state"] == "ONGOING"
    assert alert_json["alert_occurrence_count"] == 2
    assert alert_json["escalation_level"] == "PERSISTING"
    assert alert_json["first_detected_local"] == "2026-04-19T11:50:00"
    alert_text = (logs_dir / "bithumb_live_portfolio_operator_alert.txt").read_text(encoding="utf-8")
    assert "transition=ONGOING" in alert_text
    assert "escalation=PERSISTING" in alert_text
    assert "occurrence_count=2" in alert_text


def test_inspect_script_marks_operator_alert_as_prolonged_after_multiple_repeats(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
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
            "estimated_unrealized_pnl_krw": -90.0,
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
        },
    )
    (logs_dir / "bithumb_live_portfolio_manager_runs.jsonl").write_text(
        json.dumps(
            {
                "logged_at_utc": "2026-04-19T03:31:00Z",
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
    _write_json(
        logs_dir / "bithumb_live_portfolio_operator_alert.json",
        {
            "generated_at_local": "2026-04-19T12:00:00",
            "first_detected_local": "2026-04-19T11:50:00",
            "transition_state": "ONGOING",
            "alert_occurrence_count": 3,
            "escalation_level": "PERSISTING",
            "action_hint": "WATCH_STOP",
            "event_next_trigger": "partial_stop_loss",
        },
    )

    _run_inspect_script(tmp_path)

    alert_json = json.loads((logs_dir / "bithumb_live_portfolio_operator_alert.json").read_text(encoding="utf-8-sig"))
    assert alert_json["transition_state"] == "ONGOING"
    assert alert_json["alert_occurrence_count"] == 4
    assert alert_json["escalation_level"] == "PROLONGED"
    alert_text = (logs_dir / "bithumb_live_portfolio_operator_alert.txt").read_text(encoding="utf-8")
    assert "escalation=PROLONGED" in alert_text
    assert "occurrence_count=4" in alert_text
    action_hint_json = json.loads((logs_dir / "bithumb_live_portfolio_action_hint_latest.json").read_text(encoding="utf-8-sig"))
    assert action_hint_json["operator_alert_required"] is True
    assert action_hint_json["operator_alert_transition"] == "ONGOING"
    assert action_hint_json["operator_alert_escalation"] == "PROLONGED"
    assert action_hint_json["operator_alert_occurrence_count"] == 4
