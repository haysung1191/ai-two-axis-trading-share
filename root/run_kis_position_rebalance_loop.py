from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
MOMENTUM_ROOT = ROOT / "momentum"
if str(MOMENTUM_ROOT) not in sys.path:
    sys.path.insert(0, str(MOMENTUM_ROOT))

from kis_api import KISApi  # noqa: E402
from submit_kis_stock_etf_order_intents import kr_market_open, policy_blockers  # noqa: E402
from two_axis_account_engine import (  # noqa: E402
    AxisExecutionLease,
    build_account_target_diff,
    build_reconciliation,
    normalize_kis_account_snapshot,
    target_from_order_rows,
    unavailable_account_snapshot,
    write_axis_artifacts,
)


OPS_DIR = ROOT / "ops" / "kis_position_rebalance"
LATEST_JSON = OPS_DIR / "kis_position_rebalance_latest.json"
LATEST_ORDERS_CSV = OPS_DIR / "kis_position_rebalance_orders_latest.csv"
LEDGER_PATH = ROOT / "ops" / "stock_etf_axis_operation" / "kis_stock_etf_order_ledger.jsonl"
TARGET_BOOK_CSV = ROOT / "ops" / "stock_etf_operating_candidate_bridge" / "stock_etf_operating_target_book_latest.csv"
LIMITED_LIVE_POLICY_PATH = ROOT / "ops" / "runstate" / "limited_live_policy.json"
BROKER_POLICY_PATH = ROOT / "ops" / "runstate" / "broker_paper_policy.json"
ACCOUNT_ENGINE_LOCK = ROOT / "ops" / "account_engine" / "kis_combined_krw" / "axis_execution.lock"
ACCOUNT_ENGINE_ROOT = ROOT


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def managed_symbols_from_ledger(path: Path | None = None) -> set[str]:
    path = path or LEDGER_PATH
    symbols: set[str] = set()
    if not path.exists():
        return symbols
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("status") == "SUBMITTED" and event.get("symbol"):
            symbols.add(str(event["symbol"]).zfill(6))
    return symbols


def normalize_balance_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        symbol = str(row.get("pdno") or row.get("PDNO") or row.get("prdt_cd") or row.get("Symbol") or "").zfill(6)
        if not symbol or symbol == "000000":
            continue
        quantity = int(float(row.get("hldg_qty") or row.get("HLDG_QTY") or row.get("quantity") or 0))
        if quantity <= 0:
            continue
        eval_amount = float(row.get("evlu_amt") or row.get("EVLU_AMT") or row.get("evaluation_amount") or 0.0)
        out.append({"symbol": symbol, "quantity": quantity, "evaluation_amount_krw": eval_amount, "raw": row})
    return out


def build_rebalance_orders(holdings: list[dict[str, Any]], target_rows: list[dict[str, str]], managed_symbols: set[str]) -> list[dict[str, Any]]:
    target_symbols = {str(row.get("Symbol", "")).zfill(6) for row in target_rows if row.get("Symbol")}
    target_quantities: dict[str, int] = {}
    for row in target_rows:
        symbol = str(row.get("Symbol", "")).zfill(6)
        if not symbol or symbol == "000000":
            continue
        try:
            target_notional = float(row.get("TargetNotionalKRW") or 0.0)
            price = float(row.get("CurrentPrice") or 0.0)
        except ValueError:
            target_notional = 0.0
            price = 0.0
        target_quantities[symbol] = int(target_notional // price) if price > 0 else 0
    orders: list[dict[str, Any]] = []
    for holding in holdings:
        symbol = str(holding["symbol"]).zfill(6)
        if symbol not in managed_symbols:
            continue
        if symbol in target_symbols:
            target_quantity = target_quantities.get(symbol, 0)
            excess_quantity = int(holding["quantity"]) - target_quantity
            if excess_quantity > 0:
                orders.append(
                    {
                        "symbol": symbol,
                        "side": "SELL",
                        "quantity": excess_quantity,
                        "reason": "ABOVE_TARGET_QUANTITY",
                        "current_quantity": int(holding["quantity"]),
                        "target_quantity": target_quantity,
                    }
                )
            continue
        orders.append(
            {
                "symbol": symbol,
                "side": "SELL",
                "quantity": int(holding["quantity"]),
                "reason": "NO_LONGER_IN_TARGET_BOOK",
                "current_quantity": int(holding["quantity"]),
                "target_quantity": 0,
            }
        )
    return orders


def write_orders_csv(rows: list[dict[str, Any]]) -> None:
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    cols = ["symbol", "side", "quantity", "reason", "current_quantity", "target_quantity", "status", "error"]
    with LATEST_ORDERS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in cols})


def write_latest(payload: dict[str, Any]) -> None:
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_account_artifacts(
    *,
    target_rows: list[dict[str, Any]],
    holdings: list[dict[str, Any]],
    orders: list[dict[str, Any]] | None = None,
    unavailable_reason: str | None = None,
) -> dict[str, str]:
    account_snapshot = (
        unavailable_account_snapshot("KIS_COMBINED_KRW", reason=unavailable_reason)
        if unavailable_reason
        else normalize_kis_account_snapshot(balance_rows=[row.get("raw", row) for row in holdings])
    )
    target_portfolio = target_from_order_rows("KIS_COMBINED_KRW", target_rows)
    diff = build_account_target_diff(
        axis="KIS_COMBINED_KRW",
        account_snapshot=account_snapshot,
        target_portfolio=target_portfolio,
        managed_symbols=managed_symbols_from_ledger(),
        min_notional_krw=1.0,
    )
    reconciliation = build_reconciliation(
        axis="KIS_COMBINED_KRW",
        submitted_events=list(orders or []),
        account_snapshot=account_snapshot,
    )
    return write_axis_artifacts(
        root=ACCOUNT_ENGINE_ROOT,
        axis_slug="kis_combined_krw",
        account_snapshot=account_snapshot,
        target_portfolio=target_portfolio,
        diff=diff,
        reconciliation=reconciliation,
    )


def _run_once_unlocked(*, execute: bool, api: Any | None = None, enforce_market_session: bool = True) -> dict[str, Any]:
    limited = load_json(LIMITED_LIVE_POLICY_PATH)
    broker = load_json(BROKER_POLICY_PATH)
    blockers = policy_blockers(limited, broker)
    if execute and enforce_market_session and not kr_market_open():
        blockers.append("KR_MARKET_CLOSED")

    target_rows = read_csv(TARGET_BOOK_CSV)
    managed_symbols = managed_symbols_from_ledger()
    holdings: list[dict[str, Any]] = []
    orders: list[dict[str, Any]] = []

    if blockers:
        artifacts = write_account_artifacts(target_rows=target_rows, holdings=[], unavailable_reason="blocked")
        payload = {
            "generated_at_utc": utc_now(),
            "status": "KIS_POSITION_REBALANCE_BLOCKED",
            "execute": bool(execute),
            "blockers": blockers,
            "managed_symbol_count": len(managed_symbols),
            "holding_count": 0,
            "order_count": 0,
            "submitted_count": 0,
            "orders_csv": str(LATEST_ORDERS_CSV),
            "account_engine_artifacts": artifacts,
        }
        write_orders_csv([])
        write_latest(payload)
        return payload

    if api is None:
        try:
            api = KISApi()
        except Exception as exc:
            artifacts = write_account_artifacts(target_rows=target_rows, holdings=[], unavailable_reason="kis_credentials_unavailable")
            payload = {
                "generated_at_utc": utc_now(),
                "status": "KIS_POSITION_REBALANCE_CREDENTIALS_ERROR",
                "execute": bool(execute),
                "blockers": ["KIS_CREDENTIALS_UNAVAILABLE"],
                "error": str(exc),
                "managed_symbol_count": len(managed_symbols),
                "holding_count": 0,
                "order_count": 0,
                "submitted_count": 0,
                "orders_csv": str(LATEST_ORDERS_CSV),
                "account_engine_artifacts": artifacts,
            }
            write_orders_csv([])
            write_latest(payload)
            return payload

    try:
        holdings = normalize_balance_rows(api.get_domestic_balance())
        orders = build_rebalance_orders(holdings, target_rows, managed_symbols)
        submitted = 0
        for order in orders:
            if not execute:
                order["status"] = "DRY_RUN_READY"
                continue
            try:
                order["kis_response"] = api.place_domestic_cash_order(order["symbol"], "SELL", int(order["quantity"]), order_type="market")
                order["status"] = "SUBMITTED"
                submitted += 1
            except Exception as exc:
                order["status"] = "ERROR"
                order["error"] = str(exc)
        error_count = sum(1 for row in orders if row.get("status") == "ERROR")
        artifacts = write_account_artifacts(target_rows=target_rows, holdings=holdings, orders=orders)
        payload = {
            "generated_at_utc": utc_now(),
            "status": "KIS_POSITION_REBALANCE_ERROR" if error_count else ("KIS_POSITION_REBALANCE_SUBMITTED" if submitted else "KIS_POSITION_REBALANCE_OK"),
            "execute": bool(execute),
            "blockers": [],
            "managed_symbol_count": len(managed_symbols),
            "holding_count": len(holdings),
            "order_count": len(orders),
            "submitted_count": submitted,
            "error_count": error_count,
            "orders": orders,
            "orders_csv": str(LATEST_ORDERS_CSV),
            "account_engine_artifacts": artifacts,
        }
    except Exception as exc:
        artifacts = write_account_artifacts(target_rows=target_rows, holdings=holdings, unavailable_reason="rebalance_error")
        payload = {
            "generated_at_utc": utc_now(),
            "status": "KIS_POSITION_REBALANCE_ERROR",
            "execute": bool(execute),
            "blockers": [],
            "error": str(exc),
            "managed_symbol_count": len(managed_symbols),
            "holding_count": len(holdings),
            "order_count": 0,
            "submitted_count": 0,
            "orders_csv": str(LATEST_ORDERS_CSV),
            "account_engine_artifacts": artifacts,
        }
    write_orders_csv(orders)
    write_latest(payload)
    return payload


def run_once(*, execute: bool, api: Any | None = None, enforce_market_session: bool = True) -> dict[str, Any]:
    if execute:
        with AxisExecutionLease(ACCOUNT_ENGINE_LOCK, owner="kis_rebalance", ttl_seconds=1800):
            return _run_once_unlocked(execute=execute, api=api, enforce_market_session=enforce_market_session)
    return _run_once_unlocked(execute=execute, api=api, enforce_market_session=enforce_market_session)

def run_once_legacy_unused(*, execute: bool, api: Any | None = None, enforce_market_session: bool = True) -> dict[str, Any]:
    limited = load_json(LIMITED_LIVE_POLICY_PATH)
    broker = load_json(BROKER_POLICY_PATH)
    blockers = policy_blockers(limited, broker)
    if execute and enforce_market_session and not kr_market_open():
        blockers.append("KR_MARKET_CLOSED")

    target_rows = read_csv(TARGET_BOOK_CSV)
    managed_symbols = managed_symbols_from_ledger()
    holdings: list[dict[str, Any]] = []
    orders: list[dict[str, Any]] = []

    if blockers:
        payload = {
            "generated_at_utc": utc_now(),
            "status": "KIS_POSITION_REBALANCE_BLOCKED",
            "execute": bool(execute),
            "blockers": blockers,
            "managed_symbol_count": len(managed_symbols),
            "holding_count": 0,
            "order_count": 0,
            "submitted_count": 0,
            "orders_csv": str(LATEST_ORDERS_CSV),
        }
        write_orders_csv([])
        write_latest(payload)
        return payload

    if api is None:
        try:
            api = KISApi()
        except Exception as exc:
            payload = {
                "generated_at_utc": utc_now(),
                "status": "KIS_POSITION_REBALANCE_CREDENTIALS_ERROR",
                "execute": bool(execute),
                "blockers": ["KIS_CREDENTIALS_UNAVAILABLE"],
                "error": str(exc),
                "managed_symbol_count": len(managed_symbols),
                "holding_count": 0,
                "order_count": 0,
                "submitted_count": 0,
                "orders_csv": str(LATEST_ORDERS_CSV),
            }
            write_orders_csv([])
            write_latest(payload)
            return payload

    try:
        holdings = normalize_balance_rows(api.get_domestic_balance())
        orders = build_rebalance_orders(holdings, target_rows, managed_symbols)
        submitted = 0
        for order in orders:
            if not execute:
                order["status"] = "DRY_RUN_READY"
                continue
            try:
                order["kis_response"] = api.place_domestic_cash_order(order["symbol"], "SELL", int(order["quantity"]), order_type="market")
                order["status"] = "SUBMITTED"
                submitted += 1
            except Exception as exc:
                order["status"] = "ERROR"
                order["error"] = str(exc)
        error_count = sum(1 for row in orders if row.get("status") == "ERROR")
        payload = {
            "generated_at_utc": utc_now(),
            "status": "KIS_POSITION_REBALANCE_ERROR" if error_count else ("KIS_POSITION_REBALANCE_SUBMITTED" if submitted else "KIS_POSITION_REBALANCE_OK"),
            "execute": bool(execute),
            "blockers": [],
            "managed_symbol_count": len(managed_symbols),
            "holding_count": len(holdings),
            "order_count": len(orders),
            "submitted_count": submitted,
            "error_count": error_count,
            "orders": orders,
            "orders_csv": str(LATEST_ORDERS_CSV),
        }
    except Exception as exc:
        payload = {
            "generated_at_utc": utc_now(),
            "status": "KIS_POSITION_REBALANCE_ERROR",
            "execute": bool(execute),
            "blockers": [],
            "error": str(exc),
            "managed_symbol_count": len(managed_symbols),
            "holding_count": len(holdings),
            "order_count": 0,
            "submitted_count": 0,
            "orders_csv": str(LATEST_ORDERS_CSV),
        }
    write_orders_csv(orders)
    write_latest(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--ignore-market-session", action="store_true")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()
    payload = run_once(execute=args.execute, enforce_market_session=not args.ignore_market_session)
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"status={payload['status']}")
        print(f"order_count={payload['order_count']}")
        print(f"submitted_count={payload['submitted_count']}")


if __name__ == "__main__":
    main()
