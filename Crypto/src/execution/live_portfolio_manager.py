from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.execution.live_portfolio_profiles import LivePortfolioProfile


def _now_utc() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_live_portfolio_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid live portfolio state: {path}")
    return payload


def save_live_portfolio_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _extract_latest_entry(summary_payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    submitted_orders = summary_payload.get("submitted_orders", [])
    if not isinstance(submitted_orders, list) or not submitted_orders:
        raise RuntimeError("live summary has no submitted_orders")
    latest_order = submitted_orders[-1]
    if not isinstance(latest_order, dict):
        raise RuntimeError("invalid submitted order")

    plan_path = Path(str(summary_payload.get("artifacts", {}).get("plan_json") or ""))
    if not plan_path.exists():
        raise RuntimeError(f"plan_json not found: {plan_path}")
    plan_payload = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    intents = plan_payload.get("order_intents", [])
    if not isinstance(intents, list) or not intents:
        raise RuntimeError("plan has no order_intents")
    return latest_order, intents[0]


def _resolve_entry_trade(order_payload: dict[str, Any], intent_payload: dict[str, Any]) -> dict[str, Any]:
    order_status = order_payload.get("order_status", {})
    order = order_status.get("order", {}) if isinstance(order_status, dict) else {}
    trades = order.get("trades", []) if isinstance(order, dict) else []
    first_trade = trades[0] if isinstance(trades, list) and trades else {}
    entry_price_krw = (
        _safe_float((first_trade or {}).get("price"))
        or _safe_float(order.get("price"))
        or _safe_float(intent_payload.get("reference_price_krw"))
    )
    entry_volume = _safe_float(order.get("executed_volume")) or _safe_float((first_trade or {}).get("volume"))
    executed_funds = _safe_float(order.get("executed_funds"))
    paid_fee = _safe_float(order.get("paid_fee")) or 0.0
    if entry_price_krw is None or entry_volume is None or entry_volume <= 0:
        raise RuntimeError("could not resolve entry trade")
    return {
        "entry_price_krw": entry_price_krw,
        "entry_volume": entry_volume,
        "executed_funds_krw": executed_funds,
        "paid_fee_krw": paid_fee,
    }


def build_thresholds(
    *,
    entry_price_krw: float,
    partial_take_profit_pct: float,
    full_take_profit_pct: float,
    partial_stop_loss_pct: float,
    full_stop_loss_pct: float,
    planned_take_profit_price_krw: float | None,
    planned_stop_price_krw: float | None,
) -> dict[str, float | None]:
    partial_tp = entry_price_krw * (1.0 + float(partial_take_profit_pct))
    full_tp = entry_price_krw * (1.0 + float(full_take_profit_pct))
    partial_sl = entry_price_krw * (1.0 - float(partial_stop_loss_pct))
    full_sl = entry_price_krw * (1.0 - float(full_stop_loss_pct))

    planned_tp = _safe_float(planned_take_profit_price_krw)
    if planned_tp is not None and planned_tp > entry_price_krw:
        full_tp = planned_tp
        partial_tp = entry_price_krw + ((full_tp - entry_price_krw) * 0.5)

    planned_sl = _safe_float(planned_stop_price_krw)
    if planned_sl is not None and planned_sl < entry_price_krw:
        full_sl = planned_sl
        partial_sl = entry_price_krw - ((entry_price_krw - full_sl) * 0.5)

    return {
        "partial_take_profit_price_krw": partial_tp,
        "full_take_profit_price_krw": full_tp,
        "partial_stop_loss_price_krw": partial_sl,
        "full_stop_loss_price_krw": full_sl,
    }


def bootstrap_live_portfolio_state(
    summary_payload: dict[str, Any],
    *,
    profile: LivePortfolioProfile | None = None,
    partial_take_profit_pct: float,
    full_take_profit_pct: float,
    partial_stop_loss_pct: float,
    full_stop_loss_pct: float,
    partial_take_profit_fraction: float,
    partial_stop_loss_fraction: float,
) -> dict[str, Any]:
    latest_order, intent_payload = _extract_latest_entry(summary_payload)
    entry_trade = _resolve_entry_trade(latest_order, intent_payload)
    thresholds = build_thresholds(
        entry_price_krw=float(entry_trade["entry_price_krw"]),
        partial_take_profit_pct=partial_take_profit_pct,
        full_take_profit_pct=full_take_profit_pct,
        partial_stop_loss_pct=partial_stop_loss_pct,
        full_stop_loss_pct=full_stop_loss_pct,
        planned_take_profit_price_krw=_safe_float(intent_payload.get("suggested_take_profit_price_krw")),
        planned_stop_price_krw=_safe_float(intent_payload.get("suggested_stop_price_krw")),
    )
    return {
        "generated_at": _now_utc(),
        "updated_at": _now_utc(),
        "state_version": "live_portfolio_v1",
        "status": "OPEN",
        "run_id": summary_payload.get("run_id"),
        "market": latest_order.get("market") or intent_payload.get("market"),
        "symbol": latest_order.get("symbol") or intent_payload.get("symbol"),
        "entry_summary_path": summary_payload.get("artifacts", {}).get("summary_json"),
        "entry_order_id": (latest_order.get("response") or {}).get("order_id"),
        "entry_client_order_id": latest_order.get("client_order_id"),
        "entry_price_krw": entry_trade["entry_price_krw"],
        "initial_volume": entry_trade["entry_volume"],
        "remaining_volume": entry_trade["entry_volume"],
        "realized_quote_krw": 0.0,
        "realized_fee_krw": 0.0,
        "entry_paid_fee_krw": entry_trade["paid_fee_krw"],
        "time_exit_utc": intent_payload.get("time_exit_utc"),
        "profile": (
            profile.to_state_payload()
            if profile is not None
            else {
                "name": "custom",
                "objective": "unspecified",
                "description": "Custom live portfolio thresholds supplied directly.",
            }
        ),
        "rules": {
            "partial_take_profit_fraction": float(partial_take_profit_fraction),
            "partial_stop_loss_fraction": float(partial_stop_loss_fraction),
            **thresholds,
        },
        "flags": {
            "partial_take_profit_done": False,
            "partial_stop_loss_done": False,
            "full_exit_done": False,
        },
        "exits": [],
        "last_decision": None,
    }


def decide_live_portfolio_action(
    state: dict[str, Any],
    *,
    current_price_krw: float,
    min_order_volume: float,
) -> dict[str, Any]:
    if str(state.get("status") or "").upper() != "OPEN":
        return {"action": "hold", "reason": "position_closed", "volume": 0.0}

    remaining_volume = _safe_float(state.get("remaining_volume")) or 0.0
    if remaining_volume < float(min_order_volume):
        return {"action": "hold", "reason": "dust_position", "volume": 0.0}

    rules = state.get("rules", {})
    flags = state.get("flags", {})
    initial_volume = _safe_float(state.get("initial_volume")) or remaining_volume

    full_tp = _safe_float(rules.get("full_take_profit_price_krw"))
    full_sl = _safe_float(rules.get("full_stop_loss_price_krw"))
    partial_tp = _safe_float(rules.get("partial_take_profit_price_krw"))
    partial_sl = _safe_float(rules.get("partial_stop_loss_price_krw"))

    if full_sl is not None and current_price_krw <= full_sl:
        return {"action": "sell", "stage": "full_stop_loss", "reason": "FULL_STOP_LOSS", "volume": remaining_volume}
    if full_tp is not None and current_price_krw >= full_tp:
        return {"action": "sell", "stage": "full_take_profit", "reason": "FULL_TAKE_PROFIT", "volume": remaining_volume}

    if not bool(flags.get("partial_stop_loss_done")) and partial_sl is not None and current_price_krw <= partial_sl:
        volume = min(remaining_volume, initial_volume * float(rules.get("partial_stop_loss_fraction", 0.5) or 0.5))
        if volume >= float(min_order_volume):
            return {"action": "sell", "stage": "partial_stop_loss", "reason": "PARTIAL_STOP_LOSS", "volume": volume}

    if not bool(flags.get("partial_take_profit_done")) and partial_tp is not None and current_price_krw >= partial_tp:
        volume = min(remaining_volume, initial_volume * float(rules.get("partial_take_profit_fraction", 0.5) or 0.5))
        if volume >= float(min_order_volume):
            return {"action": "sell", "stage": "partial_take_profit", "reason": "PARTIAL_TAKE_PROFIT", "volume": volume}

    return {"action": "hold", "reason": "threshold_not_hit", "volume": 0.0}


def apply_live_exit_fill(
    state: dict[str, Any],
    *,
    stage: str,
    reason: str,
    volume: float,
    current_price_krw: float,
    order_id: str | None,
    client_order_id: str | None,
    paid_fee_krw: float | None,
    executed_funds_krw: float | None,
) -> dict[str, Any]:
    next_state = deepcopy(state)
    remaining_volume = _safe_float(next_state.get("remaining_volume")) or 0.0
    sold_volume = min(float(volume), remaining_volume)
    remaining_after = max(0.0, remaining_volume - sold_volume)
    next_state["remaining_volume"] = remaining_after
    next_state["realized_quote_krw"] = (_safe_float(next_state.get("realized_quote_krw")) or 0.0) + float(
        executed_funds_krw if executed_funds_krw is not None else sold_volume * current_price_krw
    )
    next_state["realized_fee_krw"] = (_safe_float(next_state.get("realized_fee_krw")) or 0.0) + float(
        paid_fee_krw or 0.0
    )
    flags = next_state.setdefault("flags", {})
    if stage == "partial_take_profit":
        flags["partial_take_profit_done"] = True
    elif stage == "partial_stop_loss":
        flags["partial_stop_loss_done"] = True
    elif stage in {"full_take_profit", "full_stop_loss"}:
        flags["full_exit_done"] = True

    exit_row = {
        "stage": stage,
        "reason": reason,
        "volume": sold_volume,
        "price_krw": float(current_price_krw),
        "order_id": order_id,
        "client_order_id": client_order_id,
        "paid_fee_krw": float(paid_fee_krw or 0.0),
        "executed_funds_krw": float(executed_funds_krw or (sold_volume * current_price_krw)),
        "created_at": _now_utc(),
    }
    next_state.setdefault("exits", []).append(exit_row)
    next_state["updated_at"] = _now_utc()
    next_state["last_decision"] = {
        "action": "sell",
        "stage": stage,
        "reason": reason,
        "volume": sold_volume,
        "price_krw": float(current_price_krw),
    }
    if remaining_after <= 0.0:
        next_state["status"] = "CLOSED"
    return next_state


def mark_manager_hold(state: dict[str, Any], *, reason: str, current_price_krw: float) -> dict[str, Any]:
    next_state = deepcopy(state)
    next_state["updated_at"] = _now_utc()
    next_state["last_decision"] = {
        "action": "hold",
        "reason": reason,
        "price_krw": float(current_price_krw),
    }
    return next_state
