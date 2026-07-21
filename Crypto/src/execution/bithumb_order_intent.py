from __future__ import annotations

from typing import Any

STANDARD_CHECK_ORDER_REFERENCE = ["practical", "research", "contract", "brief"]


def normalize_bithumb_market(symbol: str) -> str:
    raw = str(symbol or "").strip().upper()
    if raw.startswith("KRW-"):
        return raw
    if not raw:
        raise ValueError("symbol is required")
    if raw.endswith("_KRW"):
        return f"KRW-{raw[:-4]}"
    return f"KRW-{raw}"


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compute_candidate_metrics(row: dict[str, Any]) -> dict[str, float | None]:
    reference_price = _safe_float(row.get("reference_price_krw"))
    stop_price = _safe_float(row.get("suggested_stop_price_krw"))
    take_profit_price = _safe_float(row.get("suggested_take_profit_price_krw"))
    risk_reward_ratio = _safe_float(row.get("risk_reward_ratio"))

    stop_loss_pct = None
    upside_pct = None
    if reference_price is not None and reference_price > 0:
        if stop_price is not None and stop_price < reference_price:
            stop_loss_pct = (reference_price - stop_price) / reference_price
        if take_profit_price is not None and take_profit_price > reference_price:
            upside_pct = (take_profit_price - reference_price) / reference_price

    return {
        "reference_price_krw": reference_price,
        "stop_loss_pct": stop_loss_pct,
        "upside_pct": upside_pct,
        "risk_reward_ratio": risk_reward_ratio,
    }


def _track_priority_key(row: dict[str, Any], *, strategy_track: str) -> tuple[float, float, float, int, str]:
    metrics = _compute_candidate_metrics(row)
    rank = int(row.get("rank", 10**6))
    symbol = str(row.get("symbol", "")).upper()
    risk_reward_ratio = float(metrics["risk_reward_ratio"] or 0.0)
    upside_pct = float(metrics["upside_pct"] or 0.0)
    stop_loss_pct = float(metrics["stop_loss_pct"] or 1.0)

    if strategy_track == "attack":
        return (-upside_pct, -risk_reward_ratio, stop_loss_pct, rank, symbol)
    return (stop_loss_pct, -risk_reward_ratio, -upside_pct, rank, symbol)


def _build_track_rationale(row: dict[str, Any], *, strategy_track: str) -> str:
    metrics = _compute_candidate_metrics(row)
    upside_pct = metrics["upside_pct"]
    stop_loss_pct = metrics["stop_loss_pct"]
    rr = metrics["risk_reward_ratio"]
    if strategy_track == "attack":
        return (
            f"attack priority: upside_pct={upside_pct if upside_pct is not None else '-'}"
            f", rr={rr if rr is not None else '-'}"
            f", stop_loss_pct={stop_loss_pct if stop_loss_pct is not None else '-'}"
        )
    return (
        f"operating priority: stop_loss_pct={stop_loss_pct if stop_loss_pct is not None else '-'}"
        f", rr={rr if rr is not None else '-'}"
        f", upside_pct={upside_pct if upside_pct is not None else '-'}"
    )


def build_bithumb_entry_plan(
    payload: dict[str, Any],
    *,
    notional_krw: float,
    max_orders: int = 1,
    strategy_track: str = "operating",
) -> dict[str, Any]:
    brief = payload.get("manual_brief", {})
    watchlist = brief.get("watchlist", [])
    if not isinstance(watchlist, list):
        raise ValueError("manual_brief.watchlist must be a list")

    intents: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    buy_rows = [row for row in watchlist if isinstance(row, dict) and str(row.get("action", "")).upper() == "BUY"]
    prioritized_buy_rows = sorted(
        buy_rows,
        key=lambda row: _track_priority_key(row, strategy_track=strategy_track),
    )
    prioritized_buy_ids = {id(row) for row in prioritized_buy_rows}

    for row in watchlist:
        if not isinstance(row, dict):
            continue
        action = str(row.get("action", "")).upper()
        symbol = str(row.get("symbol", "")).upper()
        if action != "BUY":
            skipped.append(
                {
                    "symbol": symbol or None,
                    "action": action or None,
                    "reason": "non_buy_action",
                }
            )
            continue
        if id(row) not in prioritized_buy_ids:
            continue

    for row in prioritized_buy_rows:
        symbol = str(row.get("symbol", "")).upper()
        candidate_metrics = _compute_candidate_metrics(row)
        intent = {
            "symbol": symbol,
            "market": normalize_bithumb_market(symbol),
            "side": "buy",
            "order_type": "market",
            "quote_amount_krw": float(notional_krw),
            "reference_price_krw": _safe_float(row.get("reference_price_krw")),
            "suggested_stop_price_krw": _safe_float(row.get("suggested_stop_price_krw")),
            "suggested_take_profit_price_krw": _safe_float(row.get("suggested_take_profit_price_krw")),
            "risk_reward_ratio": _safe_float(row.get("risk_reward_ratio")),
            "time_exit_utc": row.get("time_exit_utc"),
            "source_rank": row.get("rank"),
            "source_action": action,
            "source_decision": row.get("final_decision"),
            "action_reason": row.get("action_reason"),
            "strategy_track": strategy_track,
            "candidate_metrics": candidate_metrics,
            "track_rationale": _build_track_rationale(row, strategy_track=strategy_track),
        }
        intents.append(intent)
        if len(intents) >= int(max_orders):
            break

    return {
        "run_id": payload.get("run_id"),
        "candle_close_utc": payload.get("candle_close_utc"),
        "strategy_track": strategy_track,
        "notional_krw": float(notional_krw),
        "max_orders": int(max_orders),
        "intent_count": len(intents),
        "order_intents": intents,
        "skipped_watchlist_rows": skipped,
        "source_summary_path": payload.get("summary_path"),
        "standard_check_order_reference": list(STANDARD_CHECK_ORDER_REFERENCE),
    }
