from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.paper.exit_rules import evaluate_long_exit

STANDARD_CHECK_ORDER_REFERENCE = ["practical", "research", "contract", "brief"]


def _now_utc() -> str:
    return datetime.now(tz=UTC).isoformat()


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _opened_after_or_at_candle_close(position: dict[str, Any], candle_close_utc: Any) -> bool:
    opened_at = position.get("opened_at")
    if not opened_at or not candle_close_utc:
        return False
    return str(opened_at) >= str(candle_close_utc)


def _build_intent_dedupe_key(run_id: str, intent: dict[str, Any], index: int) -> str:
    market = str(intent.get("market") or "")
    symbol = str(intent.get("symbol") or "")
    side = str(intent.get("side") or "")
    order_type = str(intent.get("order_type") or "")
    quote_amount = _safe_float(intent.get("quote_amount_krw"))
    reference_price = _safe_float(intent.get("reference_price_krw"))
    stop_price = _safe_float(intent.get("suggested_stop_price_krw"))
    take_profit_price = _safe_float(intent.get("suggested_take_profit_price_krw"))
    time_exit_utc = str(intent.get("time_exit_utc") or "")
    quote_amount_token = "na" if quote_amount is None else f"{quote_amount:.10f}"
    reference_price_token = "na" if reference_price is None else f"{reference_price:.10f}"
    stop_price_token = "na" if stop_price is None else f"{stop_price:.10f}"
    take_profit_price_token = "na" if take_profit_price is None else f"{take_profit_price:.10f}"
    return "|".join(
        [
            run_id,
            str(index),
            market,
            symbol,
            side,
            order_type,
            quote_amount_token,
            reference_price_token,
            stop_price_token,
            take_profit_price_token,
            time_exit_utc,
        ]
    )


def _normalize_list_by_identity(
    rows: list[dict[str, Any]],
    *,
    identity_fn,
    choose_fn=None,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    index_by_identity: dict[tuple[Any, ...], int] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        identity = identity_fn(row)
        if identity is None:
            normalized.append(deepcopy(row))
            continue
        existing_index = index_by_identity.get(identity)
        candidate = deepcopy(row)
        if existing_index is None:
            index_by_identity[identity] = len(normalized)
            normalized.append(candidate)
            continue
        current = normalized[existing_index]
        normalized[existing_index] = choose_fn(current, candidate) if choose_fn else current
    return normalized


def _position_identity(position: dict[str, Any]) -> tuple[Any, ...] | None:
    position_id = position.get("position_id")
    if position_id:
        return ("position_id", str(position_id))
    opened_from_order_id = position.get("opened_from_order_id")
    if opened_from_order_id:
        return ("opened_from_order_id", str(opened_from_order_id))
    market = position.get("market")
    symbol = position.get("symbol")
    opened_at = position.get("opened_at")
    if market or symbol or opened_at:
        return ("market_symbol_opened_at", str(market or ""), str(symbol or ""), str(opened_at or ""))
    return None


def _position_score(position: dict[str, Any]) -> tuple[int, int, int, str]:
    status = str(position.get("status") or "").upper()
    status_rank = 2 if status == "CLOSED" else 1 if status == "OPEN" else 0
    closure_rank = int(
        any(
            position.get(field) is not None
            for field in ("closed_at", "exit_run_id", "exit_reason", "exit_price_krw")
        )
    )
    populated_fields = sum(1 for value in position.values() if value is not None)
    timestamp_hint = str(position.get("closed_at") or position.get("opened_at") or "")
    return (status_rank, closure_rank, populated_fields, timestamp_hint)


def _choose_position_row(current: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return candidate if _position_score(candidate) > _position_score(current) else current


def normalize_paper_execution_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    next_ledger = deepcopy(ledger)
    next_ledger["orders"] = _normalize_list_by_identity(
        list(next_ledger.get("orders", [])),
        identity_fn=lambda row: ("order_id", str(row.get("order_id"))) if row.get("order_id") else None,
    )
    next_ledger["fills"] = _normalize_list_by_identity(
        list(next_ledger.get("fills", [])),
        identity_fn=lambda row: ("fill_id", str(row.get("fill_id"))) if row.get("fill_id") else None,
    )
    next_ledger["positions"] = _normalize_list_by_identity(
        list(next_ledger.get("positions", [])),
        identity_fn=_position_identity,
        choose_fn=_choose_position_row,
    )
    next_ledger["closed_positions"] = _normalize_list_by_identity(
        list(next_ledger.get("closed_positions", [])),
        identity_fn=lambda row: (
            "closed_position",
            str(row.get("position_id") or ""),
            str(row.get("exit_run_id") or ""),
        )
        if row.get("position_id") or row.get("exit_run_id")
        else None,
    )
    next_ledger["exit_fills"] = _normalize_list_by_identity(
        list(next_ledger.get("exit_fills", [])),
        identity_fn=lambda row: (
            "exit_fill_id",
            str(row.get("fill_id")),
        )
        if row.get("fill_id")
        else (
            "exit_fill_fallback",
            str(row.get("position_id") or ""),
            str(row.get("filled_at") or ""),
            str(row.get("exit_reason") or ""),
        ),
    )
    return next_ledger


def load_paper_execution_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "generated_at": _now_utc(),
            "updated_at": _now_utc(),
            "ledger_version": "paper_execution_v1",
            "account_currency": "KRW",
            "last_run_id": None,
            "last_candle_close_utc": None,
            "orders": [],
            "fills": [],
            "positions": [],
            "rejections": [],
            "standard_check_order_reference": list(STANDARD_CHECK_ORDER_REFERENCE),
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid paper ledger payload: {path}")
    return normalize_paper_execution_ledger(payload)


def save_paper_execution_ledger(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_paper_execution_ledger(payload)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_execution_plan_to_paper_ledger(
    ledger: dict[str, Any],
    plan_payload: dict[str, Any],
    *,
    venue: str = "bithumb",
) -> dict[str, Any]:
    next_ledger = deepcopy(ledger)
    run_id = str(plan_payload.get("run_id") or "unknown")
    candle_close_utc = plan_payload.get("candle_close_utc")
    intents = plan_payload.get("order_intents", [])
    if not isinstance(intents, list):
        raise ValueError("order_intents must be a list")

    positions = next_ledger.setdefault("positions", [])
    orders = next_ledger.setdefault("orders", [])
    fills = next_ledger.setdefault("fills", [])
    rejections = next_ledger.setdefault("rejections", [])
    applied_intent_keys = set()
    existing_order_ids = set()
    for row in orders:
        dedupe_key = row.get("intent_dedupe_key")
        if dedupe_key:
            applied_intent_keys.add(str(dedupe_key))
        order_id = row.get("order_id")
        if order_id:
            existing_order_ids.add(str(order_id))
    open_markets = {str(row.get("market")) for row in positions if row.get("status") == "OPEN"}

    applied = 0
    rejected = 0
    duplicate = 0
    for index, intent in enumerate(intents, start=1):
        market = str(intent.get("market") or "")
        symbol = str(intent.get("symbol") or "")
        dedupe_key = _build_intent_dedupe_key(run_id, intent, index)
        order_id = f"paper-order-{run_id.replace(':', '-')}-{index:02d}"
        fill_id = f"paper-fill-{run_id.replace(':', '-')}-{index:02d}"
        if dedupe_key in applied_intent_keys or order_id in existing_order_ids:
            duplicate += 1
            continue
        if market in open_markets:
            rejections.append(
                {
                    "run_id": run_id,
                    "candle_close_utc": candle_close_utc,
                    "market": market,
                    "symbol": symbol,
                    "reason": "existing_open_position",
                    "created_at": _now_utc(),
                }
            )
            rejected += 1
            continue
        reference_price = _safe_float(intent.get("reference_price_krw"))
        quote_amount = float(intent.get("quote_amount_krw") or 0.0)
        qty = None
        if reference_price and reference_price > 0:
            qty = quote_amount / reference_price

        order_row = {
            "order_id": order_id,
            "run_id": run_id,
            "intent_dedupe_key": dedupe_key,
            "candle_close_utc": candle_close_utc,
            "venue": venue,
            "symbol": symbol,
            "market": market,
            "side": intent.get("side"),
            "order_type": intent.get("order_type"),
            "quote_amount_krw": quote_amount,
            "status": "FILLED_PAPER",
            "created_at": _now_utc(),
        }
        fill_row = {
            "fill_id": fill_id,
            "order_id": order_id,
            "run_id": run_id,
            "venue": venue,
            "market": market,
            "symbol": symbol,
            "fill_price_krw": reference_price,
            "quote_amount_krw": quote_amount,
            "filled_qty": qty,
            "fill_mode": "reference_price",
            "filled_at": candle_close_utc,
        }
        position_row = {
            "position_id": f"paper-pos-{run_id.replace(':', '-')}-{index:02d}",
            "opened_from_order_id": order_id,
            "run_id": run_id,
            "venue": venue,
            "market": market,
            "symbol": symbol,
            "status": "OPEN",
            "strategy_track": plan_payload.get("strategy_track"),
            "entry_price_krw": reference_price,
            "quote_amount_krw": quote_amount,
            "qty": qty,
            "suggested_stop_price_krw": _safe_float(intent.get("suggested_stop_price_krw")),
            "suggested_take_profit_price_krw": _safe_float(intent.get("suggested_take_profit_price_krw")),
            "time_exit_utc": intent.get("time_exit_utc"),
            "opened_at": candle_close_utc,
        }
        orders.append(order_row)
        fills.append(fill_row)
        positions.append(position_row)
        applied_intent_keys.add(dedupe_key)
        existing_order_ids.add(order_id)
        open_markets.add(market)
        applied += 1

    next_ledger["generated_at"] = next_ledger.get("generated_at") or _now_utc()
    next_ledger["updated_at"] = _now_utc()
    next_ledger["last_run_id"] = run_id
    next_ledger["last_candle_close_utc"] = candle_close_utc
    next_ledger["last_apply_summary"] = {
        "run_id": run_id,
        "intent_count": len(intents),
        "applied_count": applied,
        "rejected_count": rejected,
        "duplicate_count": duplicate,
    }
    next_ledger["standard_check_order_reference"] = list(
        plan_payload.get("standard_check_order_reference", STANDARD_CHECK_ORDER_REFERENCE)
    )
    return next_ledger


def apply_exit_snapshot_to_paper_ledger(
    ledger: dict[str, Any],
    exit_snapshot_payload: dict[str, Any],
    *,
    venue: str = "bithumb",
) -> dict[str, Any]:
    next_ledger = deepcopy(ledger)
    run_id = str(exit_snapshot_payload.get("run_id") or "unknown")
    candle_close_utc = exit_snapshot_payload.get("candle_close_utc")
    market_ohlc = exit_snapshot_payload.get("market_ohlc", {})
    if not isinstance(market_ohlc, dict):
        raise ValueError("market_ohlc must be a mapping")
    last_exit_summary = next_ledger.get("last_exit_summary", {})
    if (
        isinstance(last_exit_summary, dict)
        and str(last_exit_summary.get("run_id") or "") == run_id
        and str(last_exit_summary.get("candle_close_utc") or "") == str(candle_close_utc or "")
    ):
        positions = next_ledger.setdefault("positions", [])
        next_ledger["updated_at"] = _now_utc()
        next_ledger["last_run_id"] = run_id
        next_ledger["last_candle_close_utc"] = candle_close_utc
        next_ledger["last_exit_summary"] = {
            "run_id": run_id,
            "candle_close_utc": candle_close_utc,
            "closed_count": 0,
            "open_count": len([row for row in positions if row.get("status") == "OPEN"]),
            "duplicate_run": True,
        }
        next_ledger["standard_check_order_reference"] = list(
            exit_snapshot_payload.get(
                "standard_check_order_reference",
                next_ledger.get("standard_check_order_reference", STANDARD_CHECK_ORDER_REFERENCE),
            )
        )
        return next_ledger

    positions = next_ledger.setdefault("positions", [])
    closed_positions = next_ledger.setdefault("closed_positions", [])
    exit_fills = next_ledger.setdefault("exit_fills", [])

    closed_count = 0
    for position in positions:
        if position.get("status") != "OPEN":
            continue
        # A position opened at the candle close should only be evaluated from the
        # next candle onward. Re-using the same candle OHLC would create a false
        # same-bar exit on reruns and break nightly idempotency.
        if _opened_after_or_at_candle_close(position, candle_close_utc):
            continue
        market = str(position.get("market") or "")
        snapshot = market_ohlc.get(market)
        if not isinstance(snapshot, dict):
            continue
        candle_o = _safe_float(snapshot.get("open"))
        candle_h = _safe_float(snapshot.get("high"))
        candle_l = _safe_float(snapshot.get("low"))
        candle_c = _safe_float(snapshot.get("close"))
        stop_price = _safe_float(position.get("suggested_stop_price_krw"))
        tp_price = _safe_float(position.get("suggested_take_profit_price_krw"))
        if None in (candle_o, candle_h, candle_l, candle_c, stop_price, tp_price):
            continue

        time_exit_now = bool(position.get("time_exit_utc")) and str(position.get("time_exit_utc")) == str(candle_close_utc)
        decision = evaluate_long_exit(candle_o, candle_h, candle_l, candle_c, stop_price, tp_price, time_exit_now)
        if not decision.should_exit:
            continue

        entry_price = _safe_float(position.get("entry_price_krw"))
        quote_amount = float(position.get("quote_amount_krw") or 0.0)
        qty = _safe_float(position.get("qty"))
        exit_price = float(decision.exit_price_pre_slip or 0.0)
        pnl_krw = None
        pnl_pct = None
        if entry_price and qty is not None:
            entry_notional = entry_price * qty
            exit_notional = exit_price * qty
            pnl_krw = exit_notional - entry_notional
            pnl_pct = 0.0 if entry_notional == 0 else pnl_krw / entry_notional

        position["status"] = "CLOSED"
        position["closed_at"] = candle_close_utc
        position["exit_reason"] = decision.reason
        position["exit_price_krw"] = exit_price
        position["exit_run_id"] = run_id
        position["venue"] = venue

        closed_positions.append(
            {
                "position_id": position.get("position_id"),
                "opened_from_order_id": position.get("opened_from_order_id"),
                "run_id": position.get("run_id"),
                "exit_run_id": run_id,
                "venue": venue,
                "market": market,
                "symbol": position.get("symbol"),
                "entry_price_krw": entry_price,
                "exit_price_krw": exit_price,
                "quote_amount_krw": quote_amount,
                "qty": qty,
                "pnl_krw": pnl_krw,
                "pnl_pct": pnl_pct,
                "exit_reason": decision.reason,
                "opened_at": position.get("opened_at"),
                "closed_at": candle_close_utc,
            }
        )
        exit_fills.append(
            {
                "fill_id": f"paper-exit-{run_id.replace(':', '-')}-{closed_count + 1:02d}",
                "position_id": position.get("position_id"),
                "market": market,
                "symbol": position.get("symbol"),
                "venue": venue,
                "fill_price_krw": exit_price,
                "filled_qty": qty,
                "fill_mode": "ohlc_exit_rule",
                "exit_reason": decision.reason,
                "filled_at": candle_close_utc,
            }
        )
        closed_count += 1

    next_ledger["updated_at"] = _now_utc()
    next_ledger["last_run_id"] = run_id
    next_ledger["last_candle_close_utc"] = candle_close_utc
    next_ledger["last_exit_summary"] = {
        "run_id": run_id,
        "candle_close_utc": candle_close_utc,
        "closed_count": closed_count,
        "open_count": len([row for row in positions if row.get("status") == "OPEN"]),
    }
    next_ledger["standard_check_order_reference"] = list(
        exit_snapshot_payload.get("standard_check_order_reference", next_ledger.get("standard_check_order_reference", STANDARD_CHECK_ORDER_REFERENCE))
    )
    return next_ledger
