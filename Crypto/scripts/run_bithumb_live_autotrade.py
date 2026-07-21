from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_bithumb_execution_plan import load_manual_brief
from scripts.execute_bithumb_execution_plan import (
    append_execution_log,
    assert_no_duplicate_submission,
    build_execution_log_record,
    submit_execution_plan,
)
from src.data.bithumb_private_client import BithumbPrivateClient
from src.execution import build_bithumb_entry_plan


def _load_plan_from_logs(
    *,
    logs_dir: Path,
    run_id: str | None,
    notional_krw: float,
    max_orders: int,
    strategy_track: str,
) -> dict[str, Any]:
    brief_payload = load_manual_brief(logs_dir, run_id=run_id)
    return build_bithumb_entry_plan(
        brief_payload,
        notional_krw=notional_krw,
        max_orders=max_orders,
        strategy_track=strategy_track,
    )


def _render_text_summary(payload: dict[str, Any]) -> str:
    lines = [
        f"run_id: {payload.get('run_id', '-')}",
        f"candle_close_utc: {payload.get('candle_close_utc', '-')}",
        f"strategy_track: {payload.get('strategy_track', '-')}",
        f"intent_count: {payload.get('intent_count', 0)}",
        f"submitted_count: {payload.get('submitted_count', 0)}",
        f"total_quote_krw: {float(payload.get('total_quote_krw', 0.0) or 0.0):,.0f}",
        "",
        "artifacts:",
        f"  plan_json: {payload.get('artifacts', {}).get('plan_json', '-')}",
        f"  summary_json: {payload.get('artifacts', {}).get('summary_json', '-')}",
    ]
    for row in payload.get("submitted_orders", []):
        order_state = ((row.get("order_status") or {}).get("order") or {}).get("state")
        lines.append(
            "  "
            + " | ".join(
                [
                    str(row.get("market", "-")),
                    f"client_order_id={row.get('client_order_id', '-')}",
                    f"quote={float(row.get('quote_amount_krw', 0.0) or 0.0):,.0f}",
                    f"state={order_state or '-'}",
                    f"timed_out={bool(row.get('timed_out', False))}",
                ]
            )
        )
    if not payload.get("submitted_orders"):
        lines.append("  (no submitted orders)")
    return "\n".join(lines)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_asset_balance(accounts_payload: Any, *, asset_symbol: str) -> float | None:
    rows = accounts_payload
    if isinstance(accounts_payload, dict):
        for key in ("data", "accounts", "result"):
            candidate = accounts_payload.get(key)
            if isinstance(candidate, list):
                rows = candidate
                break
    if not isinstance(rows, list):
        return None

    normalized_symbol = str(asset_symbol).upper().strip()
    for row in rows:
        if not isinstance(row, dict):
            continue
        currency = str(row.get("currency") or row.get("unit_currency") or "").upper()
        if currency != normalized_symbol:
            continue
        for key in ("balance", "available_balance", "avail_balance"):
            amount = _safe_float(row.get(key))
            if amount is not None:
                return amount
    return None


def assert_no_existing_asset_position(
    *,
    plan: dict[str, Any],
    access_key: str | None,
    secret_key: str | None,
    min_asset_balance: float,
) -> None:
    client = BithumbPrivateClient(access_key=access_key, secret_key=secret_key)
    if not client.has_credentials():
        raise RuntimeError("Bithumb API credentials are missing")

    accounts_payload = client.get_accounts()
    blocking_symbols: list[str] = []
    for order_intent in plan.get("order_intents", []):
        if not isinstance(order_intent, dict):
            continue
        symbol = str(order_intent.get("symbol") or "").upper().strip()
        if not symbol:
            continue
        balance = _extract_asset_balance(accounts_payload, asset_symbol=symbol)
        if balance is not None and balance >= float(min_asset_balance):
            blocking_symbols.append(f"{symbol}={balance:.8f}")

    if blocking_symbols:
        raise RuntimeError(
            "existing asset position blocks new live entry: " + ", ".join(sorted(set(blocking_symbols)))
        )


def run_live_autotrade(
    *,
    logs_dir: Path,
    run_id: str | None,
    output_dir: Path,
    execution_log: Path | None,
    notional_krw: float,
    max_orders: int,
    strategy_track: str,
    access_key: str | None,
    secret_key: str | None,
    client_order_prefix: str,
    allowed_markets: list[str] | None,
    max_total_quote_krw: float,
    status_poll_seconds: float,
    status_timeout_seconds: float,
    cancel_on_timeout: bool,
    allow_duplicate_submission: bool,
    skip_exchange_duplicate_check: bool,
    block_existing_asset_position: bool,
    min_existing_asset_balance: float,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    plan = _load_plan_from_logs(
        logs_dir=logs_dir,
        run_id=run_id,
        notional_krw=notional_krw,
        max_orders=max_orders,
        strategy_track=strategy_track,
    )
    safe_run_id = str(plan.get("run_id") or "unknown").replace(":", "-")
    plan_json = output_dir / f"bithumb_live_execution_plan_{safe_run_id}.json"
    summary_json = output_dir / f"bithumb_live_execution_summary_{safe_run_id}.json"
    plan_json.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    if execution_log is not None and not allow_duplicate_submission:
        assert_no_duplicate_submission(
            plan,
            client_order_prefix=client_order_prefix,
            execution_log_path=execution_log,
        )
    if block_existing_asset_position:
        assert_no_existing_asset_position(
            plan=plan,
            access_key=access_key,
            secret_key=secret_key,
            min_asset_balance=min_existing_asset_balance,
        )

    execution_summary = submit_execution_plan(
        plan,
        access_key=access_key,
        secret_key=secret_key,
        client_order_prefix=client_order_prefix,
        allowed_markets=allowed_markets,
        max_total_quote_krw=max_total_quote_krw,
        status_poll_seconds=status_poll_seconds,
        status_timeout_seconds=status_timeout_seconds,
        cancel_on_timeout=cancel_on_timeout,
        enforce_exchange_duplicate_check=not skip_exchange_duplicate_check,
    )
    execution_summary["artifacts"] = {
        "plan_json": str(plan_json),
        "summary_json": str(summary_json),
        "execution_log": str(execution_log) if execution_log else None,
    }
    execution_summary["duplicate_submission_policy"] = {
        "allow_duplicate_submission": allow_duplicate_submission,
        "skip_exchange_duplicate_check": skip_exchange_duplicate_check,
    }
    summary_json.write_text(json.dumps(execution_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if execution_log is not None:
        append_execution_log(
            execution_log,
            build_execution_log_record(
                execution_summary,
                plan_path=str(plan_json.resolve()),
                mode="submit",
            ),
        )
    return execution_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the live Bithumb autotrade pipeline from manual brief to execution plan to real submission. "
            "Standard operating check order: practical -> research -> contract -> brief."
        )
    )
    parser.add_argument("--logs-dir", default="logs", help="Directory containing hourly_run_*.json files")
    parser.add_argument("--run-id", default=None, help="Optional run_id like 1h:1773572400000")
    parser.add_argument("--output-dir", default="artifacts/live_execution")
    parser.add_argument("--execution-log", default="logs\\bithumb_live_execution_log.jsonl")
    parser.add_argument("--notional-krw", type=float, default=100000.0)
    parser.add_argument("--max-orders", type=int, default=1)
    parser.add_argument("--track", choices=["operating", "attack"], default="operating")
    parser.add_argument("--access-key", default=None)
    parser.add_argument("--secret-key", default=None)
    parser.add_argument("--client-order-prefix", default="live")
    parser.add_argument("--allowed-market", action="append", default=None)
    parser.add_argument("--max-total-quote-krw", type=float, default=100000.0)
    parser.add_argument("--status-poll-seconds", type=float, default=2.0)
    parser.add_argument("--status-timeout-seconds", type=float, default=20.0)
    parser.add_argument("--cancel-on-timeout", action="store_true")
    parser.add_argument("--allow-duplicate-submission", action="store_true")
    parser.add_argument("--skip-exchange-duplicate-check", action="store_true")
    parser.add_argument("--allow-existing-asset-position", action="store_true")
    parser.add_argument("--min-existing-asset-balance", type=float, default=0.000001)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    payload = run_live_autotrade(
        logs_dir=Path(args.logs_dir),
        run_id=args.run_id,
        output_dir=Path(args.output_dir),
        execution_log=Path(args.execution_log) if args.execution_log else None,
        notional_krw=float(args.notional_krw),
        max_orders=int(args.max_orders),
        strategy_track=str(args.track),
        access_key=args.access_key,
        secret_key=args.secret_key,
        client_order_prefix=str(args.client_order_prefix),
        allowed_markets=args.allowed_market,
        max_total_quote_krw=float(args.max_total_quote_krw),
        status_poll_seconds=float(args.status_poll_seconds),
        status_timeout_seconds=float(args.status_timeout_seconds),
        cancel_on_timeout=bool(args.cancel_on_timeout),
        allow_duplicate_submission=bool(args.allow_duplicate_submission),
        skip_exchange_duplicate_check=bool(args.skip_exchange_duplicate_check),
        block_existing_asset_position=not bool(args.allow_existing_asset_position),
        min_existing_asset_balance=float(args.min_existing_asset_balance),
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_text_summary(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
