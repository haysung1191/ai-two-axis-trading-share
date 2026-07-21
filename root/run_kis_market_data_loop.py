from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from loop_pid_registry import write_current_process_pid


ROOT = Path(r"C:\AI")
MOMENTUM_ROOT = ROOT / "momentum"
MARKET_DATA_MANIFEST = ROOT / "ops" / "market_data" / "market_data_manifest_latest.json"
CRYPTO_INVERSE_ETF_SYMBOL = "BITI"
MARKET_MANIFEST_AXES = {
    "KR": ["KIS_KR_STOCK_1D", "KIS_KR_ETF_1D"],
    "US": ["KIS_US_STOCK_1D", "KIS_US_ETF_1D"],
}


@dataclass(frozen=True)
class DataTask:
    market: str
    timezone_name: str
    run_hour: int
    run_minute: int
    commands: list[tuple[str, list[str], Path]]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ops_dir(market: str) -> Path:
    return ROOT / "ops" / f"kis_{market.lower()}_data_loop"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_utc_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def build_task(market: str) -> DataTask:
    py = sys.executable
    market = market.upper()
    if market == "KR":
        return DataTask(
            market="KR",
            timezone_name="Asia/Seoul",
            run_hour=15,
            run_minute=35,
            commands=[
                (
                    "refresh_kr_operating_close_prices",
                    [py, "tools/data_ingestion/refresh_kr_operating_prices.py"],
                    MOMENTUM_ROOT,
                ),
                (
                    "refresh_kr_axis_runtime_full_history_targets",
                    [
                        py,
                        str(ROOT / "refresh_kis_full_universe_recent_history.py"),
                        "--market",
                        "KR",
                        "--asset-type",
                        "all",
                        "--symbols-from-axis-runtime",
                        "--symbols-from-kis-source-book",
                        "--target-symbols-only",
                        "--no-resume-cursor",
                        "--lookback-days",
                        "10",
                        "--format",
                        "json",
                    ],
                    ROOT,
                ),
                (
                    "refresh_kr_stock_full_history_recent",
                    [
                        py,
                        str(ROOT / "refresh_kis_full_universe_recent_history.py"),
                        "--market",
                        "KR",
                        "--asset-type",
                        "stock",
                        "--lookback-days",
                        "10",
                        "--max-seconds",
                        "600",
                        "--format",
                        "json",
                    ],
                    ROOT,
                ),
                (
                    "refresh_kr_etf_full_history_recent",
                    [
                        py,
                        str(ROOT / "refresh_kis_full_universe_recent_history.py"),
                        "--market",
                        "KR",
                        "--asset-type",
                        "etf",
                        "--lookback-days",
                        "10",
                        "--max-seconds",
                        "300",
                        "--format",
                        "json",
                    ],
                    ROOT,
                ),
                (
                    "coordinate_freshness_manifest_and_snapshot",
                    [py, str(ROOT / "run_data_coordinator.py"), "--mode", "publish", "--format", "json"],
                    ROOT,
                ),
                (
                    "build_kis_kr_axis_runtime_artifacts",
                    [py, str(ROOT / "build_axis_runtime_artifacts.py"), "--axis", "KIS_KR", "--format", "json"],
                    ROOT,
                ),
            ],
        )
    if market == "US":
        return DataTask(
            market="US",
            timezone_name="America/New_York",
            run_hour=16,
            run_minute=5,
            commands=[
                (
                    "refresh_us_sp100_operating_close_prices",
                    [
                        py,
                        "tools/data_ingestion/us_stock_sp100_backfill.py",
                        "--out-base",
                        "data/prices_us_stock_sp100_pitwiki",
                        "--membership-path",
                        "backtests/us_stock_sp100_universe_pitwiki.csv",
                        "--report-path",
                        "backtests/us_stock_sp100_universe_pitwiki_refresh.csv",
                    ],
                    MOMENTUM_ROOT,
                ),
                (
                    "refresh_us_core_etf_close_prices",
                    [py, "tools/data_ingestion/us_etf_backfill.py"],
                    MOMENTUM_ROOT,
                ),
                (
                    "refresh_us_stock_axis_runtime_full_history_targets",
                    [
                        py,
                        str(ROOT / "refresh_kis_full_universe_recent_history.py"),
                        "--market",
                        "US",
                        "--asset-type",
                        "stock",
                        "--symbols-from-axis-runtime",
                        "--symbols-from-kis-source-book",
                        "--target-symbols-only",
                        "--no-resume-cursor",
                        "--lookback-days",
                        "10",
                        "--format",
                        "json",
                    ],
                    ROOT,
                ),
                (
                    "refresh_us_etf_axis_runtime_full_history_targets",
                    [
                        py,
                        str(ROOT / "refresh_kis_full_universe_recent_history.py"),
                        "--market",
                        "US",
                        "--asset-type",
                        "etf",
                        "--symbols-from-axis-runtime",
                        "--symbols-from-kis-source-book",
                        "--target-symbols-only",
                        "--symbols",
                        CRYPTO_INVERSE_ETF_SYMBOL,
                        "--no-resume-cursor",
                        "--lookback-days",
                        "10",
                        "--format",
                        "json",
                    ],
                    ROOT,
                ),
                (
                    "refresh_us_stock_full_history_recent",
                    [
                        py,
                        str(ROOT / "refresh_kis_full_universe_recent_history.py"),
                        "--market",
                        "US",
                        "--asset-type",
                        "stock",
                        "--lookback-days",
                        "10",
                        "--max-seconds",
                        "900",
                        "--format",
                        "json",
                    ],
                    ROOT,
                ),
                (
                    "refresh_us_etf_full_history_recent",
                    [
                        py,
                        str(ROOT / "refresh_kis_full_universe_recent_history.py"),
                        "--market",
                        "US",
                        "--asset-type",
                        "etf",
                        "--lookback-days",
                        "10",
                        "--max-seconds",
                        "600",
                        "--format",
                        "json",
                    ],
                    ROOT,
                ),
                (
                    "coordinate_freshness_manifest_and_snapshot",
                    [py, str(ROOT / "run_data_coordinator.py"), "--mode", "publish", "--format", "json"],
                    ROOT,
                ),
                (
                    "build_kis_us_axis_runtime_artifacts",
                    [py, str(ROOT / "build_axis_runtime_artifacts.py"), "--axis", "KIS_US", "--format", "json"],
                    ROOT,
                ),
            ],
        )
    raise ValueError(f"unsupported market: {market}")


def due_state(task: DataTask, now: datetime) -> tuple[bool, str, str, str]:
    start = now.replace(hour=task.run_hour, minute=task.run_minute, second=0, microsecond=0)
    if now.weekday() < 5 and now >= start:
        return True, now.date().isoformat(), start.isoformat(), "DUE_AFTER_CLOSE"

    lookback = now.date() - timedelta(days=1)
    while lookback.weekday() >= 5:
        lookback -= timedelta(days=1)
    catchup_start = datetime(
        lookback.year,
        lookback.month,
        lookback.day,
        task.run_hour,
        task.run_minute,
        tzinfo=now.tzinfo,
    )
    return True, lookback.isoformat(), catchup_start.isoformat(), "CATCH_UP_PREVIOUS_CLOSE"


def next_window_start(task: DataTask, now: datetime) -> str:
    for day_offset in range(0, 8):
        candidate = (now + timedelta(days=day_offset)).replace(
            hour=task.run_hour,
            minute=task.run_minute,
            second=0,
            microsecond=0,
        )
        if candidate <= now:
            continue
        if candidate.weekday() < 5:
            return candidate.isoformat()
    return ""


def stale_retry_wait_until(last_finished_at_utc: Any, retry_minutes: int) -> datetime | None:
    finished = parse_utc_datetime(last_finished_at_utc)
    if finished is None:
        return None
    return finished + timedelta(minutes=max(1, int(retry_minutes)))


def validate_market_manifest_for_market(market: str) -> dict[str, Any]:
    manifest = read_json(MARKET_DATA_MANIFEST, {})
    axes = manifest.get("axes") if isinstance(manifest.get("axes"), dict) else {}
    rows: list[dict[str, Any]] = []
    ok = True
    for axis in MARKET_MANIFEST_AXES[market.upper()]:
        row = axes.get(axis) if isinstance(axes.get(axis), dict) else {}
        operational_count = int(safe_float(row.get("operational_symbol_count"), 0.0))
        operational_fresh_ratio = safe_float(row.get("operational_fresh_ratio"), 1.0)
        row_ok = bool(row.get("usable_for_live")) and bool(row.get("usable_for_model"))
        if operational_count > 0 and operational_fresh_ratio < 1.0:
            row_ok = False
        if not row_ok:
            ok = False
        rows.append(
            {
                "axis": axis,
                "ok": row_ok,
                "expected_latest_date": row.get("expected_latest_date"),
                "actual_latest_date": row.get("actual_latest_date"),
                "fresh_ratio": row.get("fresh_ratio"),
                "operational_symbol_count": row.get("operational_symbol_count"),
                "operational_latest_date": row.get("operational_latest_date"),
                "operational_fresh_ratio": row.get("operational_fresh_ratio"),
                "operational_missing_symbols": row.get("operational_missing_symbols") or [],
                "operational_stale_symbols": row.get("operational_stale_symbols") or [],
                "blockers": row.get("blockers") or [],
            }
        )
    return {
        "ok": ok,
        "manifest_path": str(MARKET_DATA_MANIFEST),
        "axes": rows,
    }


def stale_operational_symbols_by_asset(validation: dict[str, Any]) -> dict[str, list[str]]:
    by_asset: dict[str, set[str]] = {"stock": set(), "etf": set()}
    for row in validation.get("axes") or []:
        axis = str(row.get("axis") or "").upper()
        asset_type = "etf" if "_ETF_" in axis else "stock" if "_STOCK_" in axis else ""
        if asset_type not in by_asset:
            continue
        symbols = list(row.get("operational_missing_symbols") or []) + list(row.get("operational_stale_symbols") or [])
        by_asset[asset_type].update(str(symbol).strip().upper() for symbol in symbols if str(symbol).strip())
    return {asset_type: sorted(symbols) for asset_type, symbols in by_asset.items() if symbols}


def build_operational_stale_repair_commands(task: DataTask, validation: dict[str, Any]) -> list[tuple[str, list[str], Path]]:
    py = sys.executable
    commands: list[tuple[str, list[str], Path]] = []
    for asset_type, symbols in stale_operational_symbols_by_asset(validation).items():
        commands.append(
            (
                f"repair_{task.market.lower()}_{asset_type}_operational_stale_symbols",
                [
                    py,
                    str(ROOT / "refresh_kis_full_universe_recent_history.py"),
                    "--market",
                    task.market,
                    "--asset-type",
                    asset_type,
                    "--symbols",
                    ",".join(symbols),
                    "--target-symbols-only",
                    "--no-resume-cursor",
                    "--lookback-days",
                    "10",
                    "--max-seconds",
                    "300",
                    "--format",
                    "json",
                ],
                ROOT,
            )
        )
    if commands:
        commands.extend(
            [
                (
                    "coordinate_freshness_manifest_and_snapshot",
                    [py, str(ROOT / "run_data_coordinator.py"), "--mode", "publish", "--format", "json"],
                    ROOT,
                ),
                (
                    f"build_kis_{task.market.lower()}_axis_runtime_artifacts",
                    [
                        py,
                        str(ROOT / "build_axis_runtime_artifacts.py"),
                        "--axis",
                        f"KIS_{task.market}",
                        "--format",
                        "json",
                    ],
                    ROOT,
                ),
            ]
        )
    return commands


def run_command(label: str, command: list[str], cwd: Path, timeout_seconds: int) -> dict[str, Any]:
    started = utc_now()
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=max(30, int(timeout_seconds)),
            check=False,
        )
        return {
            "label": label,
            "started_at_utc": started,
            "finished_at_utc": utc_now(),
            "returncode": completed.returncode,
            "ok": completed.returncode == 0,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
            "command": command,
            "cwd": str(cwd),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "label": label,
            "started_at_utc": started,
            "finished_at_utc": utc_now(),
            "returncode": 124,
            "ok": False,
            "timed_out": True,
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "command": command,
            "cwd": str(cwd),
        }


def run_once(args: argparse.Namespace) -> dict[str, Any]:
    task = build_task(args.market)
    out_dir = ops_dir(task.market)
    latest_json = out_dir / f"kis_{task.market.lower()}_data_loop_latest.json"
    latest_md = out_dir / f"kis_{task.market.lower()}_data_loop_latest.md"
    state_json = out_dir / f"kis_{task.market.lower()}_data_loop_state.json"
    state = read_json(state_json, {})
    runs = state.setdefault("runs", {})

    now = datetime.now(ZoneInfo(task.timezone_name))
    due, date_key, window_start, state_name = due_state(task, now)
    market_run = runs.get(task.market) or {}
    already_done = market_run.get("last_run_date") == date_key and market_run.get("status") == "FINISHED"
    manifest_before_run = validate_market_manifest_for_market(task.market)
    stale_after_finished_run = due and already_done and not manifest_before_run.get("ok")
    retry_wait_until = stale_retry_wait_until(market_run.get("last_finished_at_utc"), int(args.stale_retry_minutes))
    retry_wait_active = (
        due
        and market_run.get("status") == "FINISHED_DATA_STALE"
        and retry_wait_until is not None
        and datetime.now(timezone.utc) < retry_wait_until
    )
    should_run = due and (not already_done or stale_after_finished_run) and not retry_wait_active
    run_reason = "scheduled_refresh"
    commands_to_run = task.commands
    if stale_after_finished_run:
        repair_commands = build_operational_stale_repair_commands(task, manifest_before_run)
        if repair_commands:
            commands_to_run = repair_commands
            run_reason = "operational_stale_symbol_repair_after_finished_run"

    results: list[dict[str, Any]] = []
    data_fresh_after_run: dict[str, Any] | None = None
    if should_run:
        runs[task.market] = {
            "last_attempt_date": date_key,
            "last_started_at_utc": utc_now(),
            "status": "RUNNING",
        }
        write_json(state_json, state)
        for label, command, cwd in commands_to_run:
            results.append(run_command(label, command, cwd, int(args.step_timeout_seconds)))
            if not results[-1]["ok"]:
                break
        command_ok = bool(results) and all(row.get("ok") for row in results)
        if command_ok:
            data_fresh_after_run = validate_market_manifest_for_market(task.market)
        finished_status = (
            "FINISHED"
            if command_ok and data_fresh_after_run and data_fresh_after_run.get("ok")
            else "FINISHED_DATA_STALE"
            if command_ok
            else "FINISHED_WITH_ERROR"
        )
        runs[task.market].update(
            {
                "last_finished_at_utc": utc_now(),
                "status": finished_status,
                "last_run_date": date_key if finished_status == "FINISHED" else market_run.get("last_run_date"),
                "data_fresh_after_run": data_fresh_after_run,
            }
        )
        write_json(state_json, state)

    due_state_name = (
        "OPERATIONAL_STALE_SYMBOL_REPAIR"
        if should_run and stale_after_finished_run
        else "OPERATIONAL_STALE_SYMBOL_REPAIR_DUE"
        if stale_after_finished_run
        else "ALREADY_RAN_TARGET_DATE"
        if already_done
        else "STALE_DATA_RETRY_WAIT"
        if retry_wait_active
        else state_name
    )
    payload = {
        "status": f"KIS_{task.market}_DATA_LOOP_RUNNING",
        "updated_at_utc": utc_now(),
        "market": task.market,
        "timezone": task.timezone_name,
        "window_start": window_start,
        "next_window_start": next_window_start(task, now),
        "due_state": due_state_name,
        "executed_count": len(results),
        "run_reason": run_reason if should_run else "",
        "results": results,
        "manifest_before_run": manifest_before_run,
        "data_fresh_after_run": data_fresh_after_run,
        "stale_retry_wait_until_utc": retry_wait_until.isoformat().replace("+00:00", "Z") if retry_wait_active and retry_wait_until else "",
        "state_path": str(state_json),
    }
    write_json(latest_json, payload)
    latest_md.parent.mkdir(parents=True, exist_ok=True)
    latest_md.write_text(
        "\n".join(
            [
                f"# KIS {task.market} Data Loop",
                "",
                f"- Status: `{payload['status']}`",
                f"- Updated: `{payload['updated_at_utc']}`",
                f"- Window: `{payload['window_start']}`",
                f"- Due state: `{payload['due_state']}`",
                f"- Executed count: `{payload['executed_count']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KIS per-market data refresh loop.")
    parser.add_argument("--market", choices=["KR", "US"], required=True)
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--sleep-seconds", type=int, default=300)
    parser.add_argument("--step-timeout-seconds", type=int, default=1800)
    parser.add_argument("--stale-retry-minutes", type=int, default=60)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.loop:
        write_current_process_pid(f"kis_{args.market.lower()}_data_loop")
    while True:
        payload = run_once(args)
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
        else:
            print(
                f"status={payload['status']} market={payload['market']} "
                f"due={payload['due_state']} executed={payload['executed_count']}",
                flush=True,
            )
        if not args.loop:
            return 0
        time.sleep(max(10, int(args.sleep_seconds)))


if __name__ == "__main__":
    raise SystemExit(main())
