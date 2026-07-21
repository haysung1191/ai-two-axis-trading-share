from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.bithumb_client import BithumbPublicClient
from src.data.bithumb_private_client import BithumbPrivateClient


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def load_live_position(summary_path: Path) -> dict[str, Any]:
    summary = _load_json(summary_path)
    submitted_orders = summary.get("submitted_orders", [])
    if not isinstance(submitted_orders, list) or not submitted_orders:
        raise RuntimeError(f"no submitted_orders in {summary_path}")

    latest_order = submitted_orders[-1]
    if not isinstance(latest_order, dict):
        raise RuntimeError(f"invalid submitted order payload in {summary_path}")

    plan_path = Path(str(summary.get("artifacts", {}).get("plan_json") or ""))
    if not plan_path.exists():
        raise RuntimeError(f"plan_json not found for {summary_path}")
    plan = _load_json(plan_path)
    intents = plan.get("order_intents", [])
    if not isinstance(intents, list) or not intents:
        raise RuntimeError(f"no order_intents in {plan_path}")

    source_intent = intents[0]
    order_status = latest_order.get("order_status", {}) if isinstance(latest_order, dict) else {}
    order_payload = order_status.get("order", {}) if isinstance(order_status, dict) else {}
    trades = order_payload.get("trades", []) if isinstance(order_payload, dict) else []
    first_trade = trades[0] if isinstance(trades, list) and trades else {}
    entry_price_krw = (
        _safe_float((first_trade or {}).get("price"))
        or _safe_float(order_payload.get("price"))
        or _safe_float(source_intent.get("reference_price_krw"))
    )
    volume = _safe_float(order_payload.get("executed_volume")) or _safe_float((first_trade or {}).get("volume"))
    if entry_price_krw is None:
        raise RuntimeError(f"could not determine entry price from {summary_path}")

    return {
        "summary_path": str(summary_path),
        "plan_path": str(plan_path),
        "run_id": summary.get("run_id"),
        "market": latest_order.get("market") or source_intent.get("market"),
        "symbol": latest_order.get("symbol") or source_intent.get("symbol"),
        "entry_client_order_id": latest_order.get("client_order_id"),
        "entry_order_id": (latest_order.get("response") or {}).get("order_id"),
        "entry_price_krw": entry_price_krw,
        "entry_volume": volume,
        "suggested_stop_price_krw": _safe_float(source_intent.get("suggested_stop_price_krw")),
        "suggested_take_profit_price_krw": _safe_float(source_intent.get("suggested_take_profit_price_krw")),
        "time_exit_utc": source_intent.get("time_exit_utc"),
    }


def decide_exit(position: dict[str, Any], *, current_price_krw: float) -> dict[str, Any]:
    entry_price = _safe_float(position.get("entry_price_krw"))
    stop_price = _safe_float(position.get("suggested_stop_price_krw"))
    take_profit_price = _safe_float(position.get("suggested_take_profit_price_krw"))
    invalid_thresholds: list[str] = []
    if entry_price is not None:
        if stop_price is not None and stop_price >= entry_price:
            invalid_thresholds.append("stop_price")
            stop_price = None
        if take_profit_price is not None and take_profit_price <= entry_price:
            invalid_thresholds.append("take_profit_price")
            take_profit_price = None
    exit_reason = None
    should_exit = False

    if stop_price is not None and current_price_krw <= stop_price:
        should_exit = True
        exit_reason = "STOP_LOSS"
    elif take_profit_price is not None and current_price_krw >= take_profit_price:
        should_exit = True
        exit_reason = "TAKE_PROFIT"

    return {
        "should_exit": should_exit,
        "exit_reason": exit_reason,
        "current_price_krw": float(current_price_krw),
        "entry_price_krw": entry_price,
        "stop_price_krw": stop_price,
        "take_profit_price_krw": take_profit_price,
        "invalid_thresholds": invalid_thresholds,
    }


def build_exit_client_order_id(position: dict[str, Any]) -> str:
    base = str(position.get("entry_client_order_id") or "exit").lower()
    return f"{base}-exit"


def run_live_exit_check(
    *,
    summary_path: Path,
    access_key: str | None,
    secret_key: str | None,
    min_asset_balance: float,
    submit: bool,
) -> dict[str, Any]:
    position = load_live_position(summary_path)
    symbol = str(position.get("symbol") or "").upper()
    market = str(position.get("market") or "").upper()
    if not symbol or not market:
        raise RuntimeError(f"invalid live position payload in {summary_path}")

    public_client = BithumbPublicClient()
    private_client = BithumbPrivateClient(access_key=access_key, secret_key=secret_key)
    if not private_client.has_credentials():
        raise RuntimeError("Bithumb API credentials are missing")

    current_price_krw = public_client.get_current_price_krw(symbol)
    accounts_payload = private_client.get_accounts()
    asset_balance = _extract_asset_balance(accounts_payload, asset_symbol=symbol)
    if asset_balance is None:
        asset_balance = 0.0

    decision = decide_exit(position, current_price_krw=current_price_krw)
    payload: dict[str, Any] = {
        "position": position,
        "asset_balance": asset_balance,
        "min_asset_balance": float(min_asset_balance),
        "decision": decision,
        "submitted": False,
        "sell_order": None,
        "sell_order_status": None,
    }
    if asset_balance < float(min_asset_balance):
        payload["decision"]["should_exit"] = False
        payload["decision"]["exit_reason"] = None
        payload["decision"]["blocked_reason"] = "no_position_balance"
        return payload

    if not decision["should_exit"]:
        return payload

    client_order_id = build_exit_client_order_id(position)
    existing = None
    try:
        existing = private_client.get_order(client_order_id=client_order_id)
    except Exception:
        existing = None

    if isinstance(existing, dict) and existing.get("state") not in (None, ""):
        payload["submitted"] = False
        payload["sell_order_status"] = {"order": existing}
        payload["decision"]["blocked_reason"] = "existing_exit_order"
        return payload

    order_body = private_client.build_market_sell_order_body(
        {"market": market, "volume": asset_balance},
        client_order_id=client_order_id,
    )
    payload["sell_order_request"] = order_body
    if not submit:
        return payload

    sell_order = private_client.create_order(order_body)
    sell_order_status = private_client.get_order(
        uuid=str(sell_order.get("order_id")) if sell_order.get("order_id") not in (None, "") else None,
        client_order_id=client_order_id,
    )
    payload["submitted"] = True
    payload["sell_order"] = sell_order
    payload["sell_order_status"] = {"order": sell_order_status}
    return payload


def _render_text(payload: dict[str, Any]) -> str:
    position = payload.get("position", {})
    decision = payload.get("decision", {})
    lines = [
        f"market: {position.get('market', '-')}",
        f"symbol: {position.get('symbol', '-')}",
        f"entry_price_krw: {float(position.get('entry_price_krw', 0.0) or 0.0):,.0f}",
        f"current_price_krw: {float(decision.get('current_price_krw', 0.0) or 0.0):,.0f}",
        f"asset_balance: {float(payload.get('asset_balance', 0.0) or 0.0):.8f}",
        f"should_exit: {bool(decision.get('should_exit', False))}",
        f"exit_reason: {decision.get('exit_reason', '-')}",
        f"submitted: {bool(payload.get('submitted', False))}",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check the live Bithumb BTC position and submit a market sell on stop-loss/take-profit.")
    parser.add_argument("--summary-path", default="artifacts/live_execution/bithumb_live_execution_summary_1h-demo.json")
    parser.add_argument("--access-key", default=None)
    parser.add_argument("--secret-key", default=None)
    parser.add_argument("--min-asset-balance", type=float, default=0.000001)
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    payload = run_live_exit_check(
        summary_path=Path(args.summary_path),
        access_key=args.access_key,
        secret_key=args.secret_key,
        min_asset_balance=float(args.min_asset_balance),
        submit=bool(args.submit),
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
