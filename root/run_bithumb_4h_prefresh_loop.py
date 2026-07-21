from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from loop_pid_registry import write_current_process_pid

ROOT = Path(r"C:\AI")
OPS_DIR = ROOT / "ops" / "bithumb_4h_prefresh_loop"
STATUS_JSON = OPS_DIR / "bithumb_4h_prefresh_loop_latest.json"
STATUS_MD = OPS_DIR / "bithumb_4h_prefresh_loop_latest.md"
STATE_JSON = OPS_DIR / "bithumb_4h_prefresh_loop_state.json"
MARKET_DATA_MANIFEST_JSON = ROOT / "ops" / "market_data" / "market_data_manifest_latest.json"
BITHUMB_AUTOTRADE_JSON = ROOT / "ops" / "bithumb_axis_autotrade" / "bithumb_axis_autotrade_latest.json"
BITHUMB_OOS_JSON = ROOT / "reports" / "model_factory" / "bithumb_current_actionable_oos_walkforward_latest.json"
BITHUMB_NON_ORCA_OOS_JSON = ROOT / "reports" / "model_factory" / "bithumb_non_orca_family_entry_source_rebuild_sweep_latest.json"
BITHUMB_DIRECT_DEVELOPMENT_JSON = ROOT / "reports" / "model_factory" / "two_axis_direct_model_development_latest.json"
BITHUMB_UPGRADE_PACKET_JSON = ROOT / "reports" / "model_factory" / "two_axis_model_upgrade_packet_latest.json"
BITHUMB_DATA_DIR = ROOT / "Crypto" / "data" / "bithumb_krw_4h"
BITHUMB_STATE_DIR = ROOT / "Crypto" / "logs" / "bithumb_axis_portfolio_states"


def utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_md(payload: dict[str, Any]) -> str:
    manifest = payload.get("market_data_manifest") if isinstance(payload.get("market_data_manifest"), dict) else {}
    return "\n".join(
        [
            "# Bithumb 4h Pre-Refresh Loop",
            "",
            f"- Status: `{payload.get('status')}`",
            f"- Updated UTC: `{payload.get('updated_at_utc')}`",
            f"- Last slot KST: `{payload.get('last_slot_kst') or '-'}`",
            f"- Next due KST: `{payload.get('next_due_kst') or '-'}`",
            f"- Manifest status: `{manifest.get('status') or '-'}`",
            f"- Bithumb usable: `{manifest.get('bithumb_usable_for_live')}`",
            f"- Safety: `data-only, no orders, no policy mutation, no live-loop stop`",
            "",
        ]
    )


def publish_status(payload: dict[str, Any]) -> None:
    write_json(STATUS_JSON, payload)
    STATUS_MD.write_text(render_md(payload), encoding="utf-8")


def run_command(name: str, command: list[str], timeout_seconds: int) -> dict[str, Any]:
    started = utc_now()
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=max(30, int(timeout_seconds)),
        )
        return {
            "name": name,
            "started_at_utc": started,
            "finished_at_utc": utc_now(),
            "returncode": completed.returncode,
            "ok": completed.returncode == 0,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
            "command": command,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": name,
            "started_at_utc": started,
            "finished_at_utc": utc_now(),
            "returncode": 124,
            "ok": False,
            "timed_out": True,
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "command": command,
        }


def parse_trade_hours(value: str) -> list[int]:
    hours = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        hour = int(item)
        if hour < 0 or hour > 23:
            raise ValueError(f"trade hour out of range: {hour}")
        hours.append(hour)
    if not hours:
        raise ValueError("at least one trade hour is required")
    return sorted(set(hours))


def normalize_bithumb_market(value: Any) -> str:
    market = str(value or "").strip().upper()
    if not market:
        return ""
    if market.startswith("KRW-"):
        return market
    if "-" not in market and market.replace("_", "").isalnum():
        return f"KRW-{market}"
    return ""


def collect_markets_from_obj(value: Any, out: set[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in {
                "market",
                "markets",
                "oos_markets",
                "account_held_markets",
                "account_recovered_markets",
            }:
                if isinstance(item, list):
                    for row in item:
                        market = normalize_bithumb_market(row)
                        if market:
                            out.add(market)
                else:
                    market = normalize_bithumb_market(item)
                    if market:
                        out.add(market)
            collect_markets_from_obj(item, out)
    elif isinstance(value, list):
        for item in value:
            collect_markets_from_obj(item, out)


def operational_markets() -> list[str]:
    markets: set[str] = set()
    for path in [
        BITHUMB_AUTOTRADE_JSON,
        BITHUMB_OOS_JSON,
        BITHUMB_NON_ORCA_OOS_JSON,
        BITHUMB_DIRECT_DEVELOPMENT_JSON,
        BITHUMB_UPGRADE_PACKET_JSON,
    ]:
        collect_markets_from_obj(read_json(path), markets)
    for path in BITHUMB_STATE_DIR.glob("*_state.json"):
        payload = read_json(path)
        market = normalize_bithumb_market(payload.get("market"))
        if market:
            markets.add(market)
    return sorted(markets)


def market_args(markets: list[str]) -> list[str]:
    args: list[str] = []
    for market in markets:
        args.extend(["--market", market])
    return args


def scheduled_slots(
    now_kst: datetime,
    *,
    trade_hours: list[int],
    trade_minute: int,
    lead_minutes: int,
) -> list[tuple[datetime, datetime]]:
    slots: list[tuple[datetime, datetime]] = []
    for day_offset in range(-1, 3):
        day = (now_kst + timedelta(days=day_offset)).date()
        for hour in trade_hours:
            trade_at = datetime(
                day.year,
                day.month,
                day.day,
                hour,
                trade_minute,
                tzinfo=now_kst.tzinfo,
            )
            refresh_at = trade_at - timedelta(minutes=lead_minutes)
            slots.append((refresh_at, trade_at))
    return sorted(slots, key=lambda row: row[0])


def current_due_slot(
    now_kst: datetime,
    *,
    trade_hours: list[int],
    trade_minute: int,
    lead_minutes: int,
    grace_minutes: int,
) -> tuple[datetime, datetime] | None:
    for refresh_at, trade_at in scheduled_slots(
        now_kst,
        trade_hours=trade_hours,
        trade_minute=trade_minute,
        lead_minutes=lead_minutes,
    ):
        if refresh_at <= now_kst < trade_at + timedelta(minutes=grace_minutes):
            return refresh_at, trade_at
    return None


def next_due_slot(
    now_kst: datetime,
    *,
    trade_hours: list[int],
    trade_minute: int,
    lead_minutes: int,
) -> tuple[datetime, datetime]:
    for refresh_at, trade_at in scheduled_slots(
        now_kst,
        trade_hours=trade_hours,
        trade_minute=trade_minute,
        lead_minutes=lead_minutes,
    ):
        if refresh_at > now_kst:
            return refresh_at, trade_at
    raise RuntimeError("no next due slot found")


def previous_elapsed_slot(
    now_kst: datetime,
    *,
    trade_hours: list[int],
    trade_minute: int,
    lead_minutes: int,
) -> tuple[datetime, datetime] | None:
    previous: tuple[datetime, datetime] | None = None
    for refresh_at, trade_at in scheduled_slots(
        now_kst,
        trade_hours=trade_hours,
        trade_minute=trade_minute,
        lead_minutes=lead_minutes,
    ):
        if refresh_at <= now_kst:
            previous = (refresh_at, trade_at)
        else:
            break
    return previous


def bithumb_manifest_state() -> dict[str, Any]:
    manifest = read_json(MARKET_DATA_MANIFEST_JSON)
    axes = manifest.get("axes") if isinstance(manifest.get("axes"), dict) else {}
    bithumb = axes.get("BITHUMB_KRW_4H") if isinstance(axes.get("BITHUMB_KRW_4H"), dict) else {}
    return {
        "status": manifest.get("status"),
        "generated_at_utc": manifest.get("generated_at_utc"),
        "bithumb_usable_for_live": bool(bithumb.get("usable_for_live")),
        "bithumb_usable_for_model": bool(bithumb.get("usable_for_model")),
        "bithumb_fresh_ratio": bithumb.get("fresh_ratio"),
        "bithumb_latest_timestamp": bithumb.get("actual_latest_timestamp"),
        "bithumb_blockers": bithumb.get("blockers", []),
    }


def run_refresh(args: argparse.Namespace, *, slot_key: str, reason: str) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    markets = operational_markets()
    selected_market_args = market_args(markets)
    started_payload = {
        "status": "RUNNING",
        "updated_at_utc": utc_now(),
        "last_slot_kst": slot_key,
        "reason": reason,
        "operational_markets": markets,
        "operational_market_count": len(markets),
        "safety": safety_payload(),
        "results": results,
    }
    publish_status(started_payload)

    commands = [
        (
            "bithumb_krw_4h_recent",
            [
                sys.executable,
                str(ROOT / "refresh_bithumb_krw_4h_history.py"),
                "--mode",
                "recent",
                "--pages-per-market",
                str(args.pages_per_market),
                "--max-seconds",
                str(args.max_seconds),
                "--request-sleep-seconds",
                str(args.request_sleep_seconds),
                "--format",
                "json",
            ]
            + selected_market_args,
            int(args.max_seconds) + 120,
        ),
        (
            "coordinate_freshness_manifest_and_snapshot",
            [
                sys.executable,
                str(ROOT / "run_data_coordinator.py"),
                "--mode",
                "publish",
                "--format",
                "json",
            ],
            600,
        ),
        (
            "bithumb_axis_runtime_artifacts",
            [
                sys.executable,
                str(ROOT / "build_axis_runtime_artifacts.py"),
                "--axis",
                "BITHUMB",
                "--format",
                "json",
            ],
            180,
        ),
    ]
    for name, command, timeout_seconds in commands:
        payload = {
            "status": "RUNNING",
            "updated_at_utc": utc_now(),
            "last_slot_kst": slot_key,
            "last_step": name,
            "reason": reason,
            "operational_markets": markets,
            "operational_market_count": len(markets),
            "safety": safety_payload(),
            "results": results,
        }
        publish_status(payload)
        results.append(run_command(name, command, timeout_seconds))

    ok = all(bool(row.get("ok")) for row in results)
    state = read_json(STATE_JSON)
    if ok:
        state["last_completed_slot_kst"] = slot_key
        state["last_completed_at_utc"] = utc_now()
        write_json(STATE_JSON, state)
    manifest_state = bithumb_manifest_state()
    status = "READY" if ok and manifest_state.get("bithumb_usable_for_live") else "DATA_NOT_READY"
    return {
        "status": status,
        "updated_at_utc": utc_now(),
        "last_slot_kst": slot_key,
        "reason": reason,
        "operational_markets": markets,
        "operational_market_count": len(markets),
        "market_data_manifest": manifest_state,
        "safety": safety_payload(),
        "results": results,
    }


def safety_payload() -> dict[str, bool]:
    return {
        "submits_orders": False,
        "mutates_policy": False,
        "stops_live_loops": False,
        "creates_disable_guard": False,
    }


def run_once(args: argparse.Namespace) -> dict[str, Any]:
    kst = ZoneInfo("Asia/Seoul")
    now_kst = datetime.now(tz=kst)
    trade_hours = parse_trade_hours(args.trade_hours_kst)
    due = current_due_slot(
        now_kst,
        trade_hours=trade_hours,
        trade_minute=args.trade_minute_kst,
        lead_minutes=args.lead_minutes,
        grace_minutes=args.grace_minutes,
    )
    next_due, next_trade = next_due_slot(
        now_kst,
        trade_hours=trade_hours,
        trade_minute=args.trade_minute_kst,
        lead_minutes=args.lead_minutes,
    )
    manifest_state = bithumb_manifest_state()
    state = read_json(STATE_JSON)
    due_slot_key = due[1].isoformat(timespec="minutes") if due else ""
    already_done = bool(due_slot_key and state.get("last_completed_slot_kst") == due_slot_key)
    catchup = previous_elapsed_slot(
        now_kst,
        trade_hours=trade_hours,
        trade_minute=args.trade_minute_kst,
        lead_minutes=args.lead_minutes,
    )
    catchup_slot_key = catchup[1].isoformat(timespec="minutes") if catchup else ""
    catchup_due = bool(
        catchup
        and not due
        and catchup_slot_key
        and state.get("last_completed_slot_kst") != catchup_slot_key
    )
    stale_recovery_due = bool(args.recover_if_stale and not manifest_state.get("bithumb_usable_for_live"))

    if due and not already_done:
        payload = run_refresh(args, slot_key=due_slot_key, reason="scheduled_pretrade_refresh")
    elif catchup_due:
        payload = run_refresh(args, slot_key=catchup_slot_key, reason="missed_pretrade_catchup")
    elif stale_recovery_due:
        payload = run_refresh(args, slot_key=f"stale-recovery-{now_kst.isoformat(timespec='minutes')}", reason="stale_recovery")
    else:
        payload = {
            "status": "SLEEPING",
            "updated_at_utc": utc_now(),
            "last_slot_kst": state.get("last_completed_slot_kst"),
            "next_due_kst": next_due.isoformat(timespec="minutes"),
            "next_trade_kst": next_trade.isoformat(timespec="minutes"),
            "market_data_manifest": manifest_state,
            "safety": safety_payload(),
            "results": [],
        }
    if "next_due_kst" not in payload:
        upcoming_due, upcoming_trade = next_due_slot(
            datetime.now(tz=kst),
            trade_hours=trade_hours,
            trade_minute=args.trade_minute_kst,
            lead_minutes=args.lead_minutes,
        )
        payload["next_due_kst"] = upcoming_due.isoformat(timespec="minutes")
        payload["next_trade_kst"] = upcoming_trade.isoformat(timespec="minutes")
    publish_status(payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Data-only Bithumb 4h pre-refresh loop.")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--sleep-seconds", type=int, default=60)
    parser.add_argument("--trade-hours-kst", default="0,4,8,12,16,20")
    parser.add_argument("--trade-minute-kst", type=int, default=30)
    parser.add_argument("--lead-minutes", type=int, default=25)
    parser.add_argument("--grace-minutes", type=int, default=20)
    parser.add_argument("--pages-per-market", type=int, default=1)
    parser.add_argument("--max-seconds", type=int, default=900)
    parser.add_argument("--request-sleep-seconds", type=float, default=1.05)
    parser.add_argument("--recover-if-stale", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    if args.loop:
        write_current_process_pid("bithumb_4h_data_loop")
    while True:
        payload = run_once(args)
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
        else:
            print(
                f"status={payload.get('status')} updated={payload.get('updated_at_utc')} "
                f"next_due_kst={payload.get('next_due_kst')}",
                flush=True,
            )
        if not args.loop:
            return 0
        time.sleep(max(15, int(args.sleep_seconds)))


if __name__ == "__main__":
    raise SystemExit(main())
