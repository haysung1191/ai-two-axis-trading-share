from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check live Bithumb portfolio manager health from recent run checkpoints. "
            "Standard operating check order: practical -> research -> contract -> brief."
        )
    )
    parser.add_argument(
        "--run-log",
        type=Path,
        default=Path("logs\\bithumb_live_portfolio_manager_runs.jsonl"),
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=Path("logs\\bithumb_live_portfolio_state.json"),
    )
    parser.add_argument("--stale-after-minutes", type=float, default=20.0)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-text", type=Path, default=None)
    parser.add_argument("--alert-path", type=Path, default=None)
    parser.add_argument("--as-json", action="store_true")
    return parser


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def check_bithumb_live_portfolio_health(
    *,
    run_log: Path,
    state_path: Path,
    stale_after_minutes: float,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now = now_utc or _utc_now()
    rows = _load_jsonl(run_log)
    last_row = rows[-1] if rows else None
    state_payload = _load_json(state_path) if state_path.exists() else {}

    last_logged_at = _parse_utc((last_row or {}).get("logged_at_utc")) if isinstance(last_row, dict) else None
    age_seconds = (now - last_logged_at).total_seconds() if last_logged_at is not None else None
    stale_threshold_seconds = timedelta(minutes=float(stale_after_minutes)).total_seconds()
    is_stale = age_seconds is None or age_seconds > stale_threshold_seconds
    last_status = str((last_row or {}).get("status") or "missing") if isinstance(last_row, dict) else "missing"
    has_error = last_status != "ok"

    issues: list[str] = []
    if not rows:
        issues.append("missing_run_log")
    if is_stale:
        issues.append("stale_run_log")
    if has_error:
        issues.append("last_run_not_ok")
    if not state_path.exists():
        issues.append("missing_state_file")

    return {
        "ok": not issues,
        "issues": issues,
        "run_log": str(run_log),
        "state_path": str(state_path),
        "run_log_exists": run_log.exists(),
        "state_exists": state_path.exists(),
        "run_count": len(rows),
        "last_logged_at_utc": last_row.get("logged_at_utc") if isinstance(last_row, dict) else None,
        "last_status": last_status,
        "last_error": (last_row or {}).get("error") if isinstance(last_row, dict) else None,
        "last_mode": (last_row or {}).get("mode") if isinstance(last_row, dict) else None,
        "last_action": (last_row or {}).get("last_action") if isinstance(last_row, dict) else None,
        "last_reason": (last_row or {}).get("last_reason") if isinstance(last_row, dict) else None,
        "last_price_krw": (last_row or {}).get("current_price_krw") if isinstance(last_row, dict) else None,
        "last_asset_balance": (last_row or {}).get("asset_balance") if isinstance(last_row, dict) else None,
        "last_krw_balance": (last_row or {}).get("krw_balance") if isinstance(last_row, dict) else None,
        "age_seconds": age_seconds,
        "stale_after_seconds": stale_threshold_seconds,
        "position_status": state_payload.get("status") if isinstance(state_payload, dict) else None,
        "remaining_volume": state_payload.get("remaining_volume") if isinstance(state_payload, dict) else None,
        "symbol": state_payload.get("symbol") if isinstance(state_payload, dict) else None,
    }


def render_bithumb_live_portfolio_health_line(result: dict[str, Any]) -> str:
    ok = "True" if result["ok"] else "False"
    age_seconds = result.get("age_seconds")
    age_part = f"{float(age_seconds):.0f}s" if isinstance(age_seconds, (int, float)) else "n/a"
    issues_part = ",".join(result.get("issues", [])) or "none"
    return (
        f"Bithumb live portfolio health | ok={ok} | last_status={result['last_status']} | "
        f"age={age_part} | symbol={result.get('symbol') or '-'} | "
        f"position_status={result.get('position_status') or '-'} | issues={issues_part}"
    )


def write_health_outputs(
    *,
    result: dict[str, Any],
    output_json: Path | None,
    output_text: Path | None,
    alert_path: Path | None,
) -> None:
    if output_json is not None:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if output_text is not None:
        output_text.parent.mkdir(parents=True, exist_ok=True)
        output_text.write_text(render_bithumb_live_portfolio_health_line(result) + "\n", encoding="utf-8")
    if alert_path is not None:
        alert_path.parent.mkdir(parents=True, exist_ok=True)
        if result.get("ok"):
            if alert_path.exists():
                alert_path.unlink()
        else:
            alert_payload = {
                "alert_type": "bithumb_live_portfolio_health_degraded",
                "generated_at_utc": _utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "summary": render_bithumb_live_portfolio_health_line(result),
                "issues": result.get("issues", []),
                "last_status": result.get("last_status"),
                "last_error": result.get("last_error"),
            }
            alert_path.write_text(json.dumps(alert_payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = check_bithumb_live_portfolio_health(
        run_log=args.run_log,
        state_path=args.state_path,
        stale_after_minutes=float(args.stale_after_minutes),
    )
    write_health_outputs(
        result=result,
        output_json=args.output_json,
        output_text=args.output_text,
        alert_path=args.alert_path,
    )
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_bithumb_live_portfolio_health_line(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
