from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from scripts.check_bithumb_live_portfolio_health import (
    build_parser,
    check_bithumb_live_portfolio_health,
    render_bithumb_live_portfolio_health_line,
    write_health_outputs,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def test_health_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.run_log == Path("logs\\bithumb_live_portfolio_manager_runs.jsonl")
    assert args.state_path == Path("logs\\bithumb_live_portfolio_state.json")
    assert args.stale_after_minutes == 20.0
    assert args.output_json is None
    assert args.output_text is None
    assert args.alert_path is None
    assert args.as_json is False


def test_check_bithumb_live_portfolio_health_ok(tmp_path: Path) -> None:
    run_log = tmp_path / "runs.jsonl"
    state_path = tmp_path / "state.json"
    _write_jsonl(
        run_log,
        [
            {
                "logged_at_utc": "2026-04-19T01:22:03Z",
                "status": "ok",
                "mode": "manage_open_position",
                "last_action": "hold",
                "last_reason": "threshold_not_hit",
                "current_price_krw": 112291000.0,
                "asset_balance": 0.00088869,
                "krw_balance": 223.384443,
            }
        ],
    )
    _write_json(
        state_path,
        {
            "status": "OPEN",
            "remaining_volume": 0.00088869,
            "symbol": "BTC",
        },
    )

    result = check_bithumb_live_portfolio_health(
        run_log=run_log,
        state_path=state_path,
        stale_after_minutes=20.0,
        now_utc=datetime(2026, 4, 19, 1, 30, 0, tzinfo=UTC),
    )

    assert result["ok"] is True
    assert result["issues"] == []
    assert result["last_status"] == "ok"
    assert result["position_status"] == "OPEN"
    assert result["symbol"] == "BTC"


def test_check_bithumb_live_portfolio_health_flags_stale_and_error(tmp_path: Path) -> None:
    run_log = tmp_path / "runs.jsonl"
    state_path = tmp_path / "state.json"
    _write_jsonl(
        run_log,
        [
            {
                "logged_at_utc": "2026-04-19T01:00:00Z",
                "status": "error",
                "error": "timeout",
            }
        ],
    )
    _write_json(state_path, {"status": "OPEN", "remaining_volume": 0.0001, "symbol": "BTC"})

    result = check_bithumb_live_portfolio_health(
        run_log=run_log,
        state_path=state_path,
        stale_after_minutes=20.0,
        now_utc=datetime(2026, 4, 19, 1, 30, 1, tzinfo=UTC),
    )

    assert result["ok"] is False
    assert "stale_run_log" in result["issues"]
    assert "last_run_not_ok" in result["issues"]
    assert result["last_error"] == "timeout"


def test_render_health_line_includes_core_fields() -> None:
    rendered = render_bithumb_live_portfolio_health_line(
        {
            "ok": False,
            "last_status": "error",
            "age_seconds": 1800.0,
            "symbol": "BTC",
            "position_status": "OPEN",
            "issues": ["stale_run_log", "last_run_not_ok"],
        }
    )

    assert "Bithumb live portfolio health" in rendered
    assert "ok=False" in rendered
    assert "last_status=error" in rendered
    assert "issues=stale_run_log,last_run_not_ok" in rendered


def test_write_health_outputs_persists_json_and_text(tmp_path: Path) -> None:
    result = {
        "ok": True,
        "last_status": "ok",
        "age_seconds": 30.0,
        "symbol": "BTC",
        "position_status": "OPEN",
        "issues": [],
    }
    output_json = tmp_path / "health.json"
    output_text = tmp_path / "health.txt"
    alert_path = tmp_path / "alert.json"

    write_health_outputs(
        result=result,
        output_json=output_json,
        output_text=output_text,
        alert_path=alert_path,
    )

    assert json.loads(output_json.read_text(encoding="utf-8"))["ok"] is True
    rendered = output_text.read_text(encoding="utf-8")
    assert "Bithumb live portfolio health" in rendered
    assert "ok=True" in rendered
    assert alert_path.exists() is False


def test_write_health_outputs_creates_and_clears_alert_file(tmp_path: Path) -> None:
    degraded = {
        "ok": False,
        "last_status": "error",
        "last_error": "timeout",
        "age_seconds": 1800.0,
        "symbol": "BTC",
        "position_status": "OPEN",
        "issues": ["stale_run_log", "last_run_not_ok"],
    }
    recovered = {
        "ok": True,
        "last_status": "ok",
        "last_error": None,
        "age_seconds": 10.0,
        "symbol": "BTC",
        "position_status": "OPEN",
        "issues": [],
    }
    alert_path = tmp_path / "alert.json"

    write_health_outputs(
        result=degraded,
        output_json=None,
        output_text=None,
        alert_path=alert_path,
    )
    alert_payload = json.loads(alert_path.read_text(encoding="utf-8"))
    assert alert_payload["alert_type"] == "bithumb_live_portfolio_health_degraded"
    assert "stale_run_log" in alert_payload["issues"]

    write_health_outputs(
        result=recovered,
        output_json=None,
        output_text=None,
        alert_path=alert_path,
    )
    assert alert_path.exists() is False
