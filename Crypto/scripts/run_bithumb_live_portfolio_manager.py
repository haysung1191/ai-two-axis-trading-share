from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_bithumb_live_autotrade import run_live_autotrade
from src.data.bithumb_client import BithumbPublicClient
from src.data.bithumb_private_client import BithumbPrivateClient
from src.execution import (
    LivePortfolioProfile,
    apply_live_exit_fill,
    bootstrap_live_portfolio_state,
    decide_live_portfolio_action,
    load_live_portfolio_state,
    mark_manager_hold,
    resolve_live_portfolio_profile,
    save_live_portfolio_state,
)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_profile(
    *,
    profile_name: str,
    partial_take_profit_pct: float | None,
    full_take_profit_pct: float | None,
    partial_stop_loss_pct: float | None,
    full_stop_loss_pct: float | None,
    partial_take_profit_fraction: float | None,
    partial_stop_loss_fraction: float | None,
) -> LivePortfolioProfile:
    return resolve_live_portfolio_profile(
        profile_name,
        partial_take_profit_pct=partial_take_profit_pct,
        full_take_profit_pct=full_take_profit_pct,
        partial_stop_loss_pct=partial_stop_loss_pct,
        full_stop_loss_pct=full_stop_loss_pct,
        partial_take_profit_fraction=partial_take_profit_fraction,
        partial_stop_loss_fraction=partial_stop_loss_fraction,
    )


def _utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _estimate_realized_pnl_krw(*, state: dict[str, Any], payload: dict[str, Any]) -> float | None:
    if not isinstance(state, dict) or not isinstance(payload, dict):
        return None
    last_decision = state.get("last_decision", {})
    if not isinstance(last_decision, dict):
        return None
    if last_decision.get("action") != "sell":
        return None
    sold_volume = _safe_float(last_decision.get("volume"))
    sell_price = _safe_float(last_decision.get("price_krw")) or _safe_float(payload.get("current_price_krw"))
    entry_price = _safe_float(state.get("entry_price_krw"))
    if sold_volume is None or sell_price is None or entry_price is None:
        return None
    paid_fee = 0.0
    sell_order_status = payload.get("sell_order_status")
    if isinstance(sell_order_status, dict):
        order = sell_order_status.get("order")
        if isinstance(order, dict):
            paid_fee = _safe_float(order.get("paid_fee")) or 0.0
    return (sell_price - entry_price) * sold_volume - paid_fee


def _estimate_unrealized_pnl_krw(*, state: dict[str, Any], payload: dict[str, Any]) -> float | None:
    if not isinstance(state, dict) or not isinstance(payload, dict):
        return None
    remaining_volume = _safe_float(state.get("remaining_volume"))
    current_price = _safe_float(payload.get("current_price_krw"))
    entry_price = _safe_float(state.get("entry_price_krw"))
    if remaining_volume is None or current_price is None or entry_price is None:
        return None
    return (current_price - entry_price) * remaining_volume


def _build_position_progress_snapshot(
    *,
    state: dict[str, Any],
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(state, dict):
        return {}
    payload = payload if isinstance(payload, dict) else {}

    initial_volume = _safe_float(state.get("initial_volume"))
    remaining_volume = _safe_float(state.get("remaining_volume"))
    entry_price = _safe_float(state.get("entry_price_krw"))
    realized_quote = _safe_float(state.get("realized_quote_krw")) or 0.0
    realized_fee = _safe_float(state.get("realized_fee_krw")) or 0.0

    sold_volume = None
    remaining_position_pct = None
    cumulative_realized_pnl_krw = None
    cumulative_realized_return_pct = None

    if initial_volume is not None and remaining_volume is not None and initial_volume > 0:
        sold_volume = max(0.0, initial_volume - remaining_volume)
        remaining_position_pct = (remaining_volume / initial_volume) * 100.0
        if entry_price is not None and sold_volume > 0:
            realized_cost_basis = entry_price * sold_volume
            cumulative_realized_pnl_krw = realized_quote - realized_cost_basis - realized_fee
            if realized_cost_basis > 0:
                cumulative_realized_return_pct = (cumulative_realized_pnl_krw / realized_cost_basis) * 100.0

    status = str(state.get("status") or "").upper()
    krw_balance = _safe_float(payload.get("krw_balance"))
    min_reentry_krw = _safe_float(payload.get("min_reentry_krw"))
    reentry_enabled = bool(payload.get("reentry_enabled"))
    reentry_ready = None
    if status == "CLOSED" and krw_balance is not None and min_reentry_krw is not None:
        reentry_ready = reentry_enabled and krw_balance >= min_reentry_krw

    return {
        "initial_volume": initial_volume,
        "sold_volume": sold_volume,
        "remaining_position_pct": remaining_position_pct,
        "cumulative_realized_pnl_krw": cumulative_realized_pnl_krw,
        "cumulative_realized_return_pct": cumulative_realized_return_pct,
        "reentry_ready": reentry_ready,
    }


def _build_prior_closed_position_snapshot(state: dict[str, Any] | None) -> dict[str, Any]:
    state = state if isinstance(state, dict) else {}
    if str(state.get("status") or "").upper() != "CLOSED":
        return {}
    exits = state.get("exits", [])
    last_exit = exits[-1] if isinstance(exits, list) and exits and isinstance(exits[-1], dict) else {}
    snapshot = _build_position_progress_snapshot(state=state, payload={})
    return {
        "prior_position_status": state.get("status"),
        "prior_exit_reason": last_exit.get("reason") or (state.get("last_decision") or {}).get("reason"),
        "prior_exit_stage": last_exit.get("stage") or (state.get("last_decision") or {}).get("stage"),
        "prior_exit_price_krw": _safe_float(last_exit.get("price_krw")),
        "prior_exit_order_id": last_exit.get("order_id"),
        "prior_remaining_position_pct": snapshot.get("remaining_position_pct"),
        "prior_cumulative_realized_pnl_krw": snapshot.get("cumulative_realized_pnl_krw"),
        "prior_cumulative_realized_return_pct": snapshot.get("cumulative_realized_return_pct"),
    }


def _resolve_latest_snapshot_event_type(*, state: dict[str, Any], payload: dict[str, Any]) -> str:
    status = str((state or {}).get("status") or "").upper()
    if status != "CLOSED":
        return "no_new_event"
    reentry_enabled = bool((payload or {}).get("reentry_enabled"))
    krw_balance = _safe_float((payload or {}).get("krw_balance"))
    min_reentry_krw = _safe_float((payload or {}).get("min_reentry_krw"))
    if reentry_enabled and krw_balance is not None and min_reentry_krw is not None:
        if krw_balance >= min_reentry_krw:
            return "closed_waiting_reentry"
        return "closed_waiting_funds"
    return "closed_idle"


def _build_next_trigger_snapshot(*, state: dict[str, Any], current_price_krw: Any) -> dict[str, Any]:
    if not isinstance(state, dict):
        return {}
    if str(state.get("status") or "").upper() != "OPEN":
        return {}

    current_price = _safe_float(current_price_krw)
    if current_price is None:
        return {}

    rules = state.get("rules", {})
    flags = state.get("flags", {})
    if not isinstance(rules, dict) or not isinstance(flags, dict):
        return {}

    candidates: list[tuple[str, float]] = []

    full_tp = _safe_float(rules.get("full_take_profit_price_krw"))
    if full_tp is not None and current_price < full_tp:
        candidates.append(("full_take_profit", full_tp))

    full_sl = _safe_float(rules.get("full_stop_loss_price_krw"))
    if full_sl is not None and current_price > full_sl:
        candidates.append(("full_stop_loss", full_sl))

    partial_tp = _safe_float(rules.get("partial_take_profit_price_krw"))
    if not bool(flags.get("partial_take_profit_done")) and partial_tp is not None and current_price < partial_tp:
        candidates.append(("partial_take_profit", partial_tp))

    partial_sl = _safe_float(rules.get("partial_stop_loss_price_krw"))
    if not bool(flags.get("partial_stop_loss_done")) and partial_sl is not None and current_price > partial_sl:
        candidates.append(("partial_stop_loss", partial_sl))

    if not candidates:
        return {}

    next_stage, next_price = min(candidates, key=lambda item: abs(item[1] - current_price))
    distance_krw = next_price - current_price
    distance_pct = (distance_krw / current_price) * 100.0 if current_price else None
    return {
        "next_trigger_stage": next_stage,
        "next_trigger_price_krw": next_price,
        "next_trigger_distance_krw": distance_krw,
        "next_trigger_distance_pct": distance_pct,
    }


def _format_number_or_dash(value: Any, *, digits: int) -> str:
    if value is None or value == "":
        return "-"
    number = _safe_float(value)
    if number is None:
        return str(value)
    rounded = round(number, digits)
    if digits == 0:
        return str(int(rounded))
    text = f"{rounded:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if text in {"-0", "-0.0"} else text


def _format_text_or_dash(value: Any) -> str:
    if value is None:
        return "-"
    text = str(value)
    return "-" if text == "" else text


def _build_latest_event_text_summary(event_payload: dict[str, Any]) -> str:
    parts = [
        _format_text_or_dash(event_payload.get("event_type")),
        f"symbol={_format_text_or_dash(event_payload.get('symbol'))}",
        f"position_status={_format_text_or_dash(event_payload.get('position_status'))}",
        f"last_reason={_format_text_or_dash(event_payload.get('last_reason'))}",
    ]
    if any(
        event_payload.get(key) is not None
        for key in (
            "prior_exit_reason",
            "prior_cumulative_realized_pnl_krw",
            "prior_cumulative_realized_return_pct",
        )
    ):
        parts.extend(
            [
                f"prior_exit_reason={_format_text_or_dash(event_payload.get('prior_exit_reason'))}",
                f"prior_realized_pnl_krw={_format_number_or_dash(event_payload.get('prior_cumulative_realized_pnl_krw'), digits=2)}",
                f"prior_realized_return_pct={_format_number_or_dash(event_payload.get('prior_cumulative_realized_return_pct'), digits=2)}",
            ]
        )
    parts.extend(
        [
            f"current_price_krw={_format_number_or_dash(event_payload.get('current_price_krw'), digits=0)}",
            f"next_trigger={_format_text_or_dash(event_payload.get('next_trigger_stage'))}",
            f"next_trigger_price_krw={_format_number_or_dash(event_payload.get('next_trigger_price_krw'), digits=0)}",
            f"next_trigger_distance_krw={_format_number_or_dash(event_payload.get('next_trigger_distance_krw'), digits=0)}",
            f"next_trigger_distance_pct={_format_number_or_dash(event_payload.get('next_trigger_distance_pct'), digits=2)}",
            f"remaining_volume={_format_number_or_dash(event_payload.get('remaining_volume'), digits=8)}",
            f"remaining_position_pct={_format_number_or_dash(event_payload.get('remaining_position_pct'), digits=2)}",
            f"sold_volume={_format_number_or_dash(event_payload.get('sold_volume'), digits=8)}",
            f"cumulative_realized_pnl_krw={_format_number_or_dash(event_payload.get('cumulative_realized_pnl_krw'), digits=2)}",
            f"cumulative_realized_return_pct={_format_number_or_dash(event_payload.get('cumulative_realized_return_pct'), digits=2)}",
            f"reentry_ready={_format_text_or_dash(event_payload.get('reentry_ready'))}",
            f"realized_pnl_krw={_format_number_or_dash(event_payload.get('estimated_realized_pnl_krw'), digits=2)}",
            f"unrealized_pnl_krw={_format_number_or_dash(event_payload.get('estimated_unrealized_pnl_krw'), digits=2)}",
        ]
    )
    return " | ".join(parts)


def append_manager_run_log(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def append_manager_event_log(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_latest_event_outputs(
    *,
    event_payload: dict[str, Any],
    latest_json_path: Path | None,
    latest_text_path: Path | None,
) -> None:
    if latest_json_path is not None:
        latest_json_path.parent.mkdir(parents=True, exist_ok=True)
        latest_json_path.write_text(json.dumps(event_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if latest_text_path is not None:
        latest_text_path.parent.mkdir(parents=True, exist_ok=True)
        summary = _build_latest_event_text_summary(event_payload)
        latest_text_path.write_text(summary + "\n", encoding="utf-8")


def write_no_event_outputs(
    *,
    state: dict[str, Any] | None,
    payload: dict[str, Any] | None,
    latest_json_path: Path | None,
    latest_text_path: Path | None,
) -> None:
    state = state if isinstance(state, dict) else {}
    payload = payload if isinstance(payload, dict) else {}
    last_decision = state.get("last_decision", {}) if isinstance(state, dict) else {}
    snapshot = {
        "event_type": _resolve_latest_snapshot_event_type(state=state, payload=payload),
        "logged_at_utc": _utc_now_iso(),
        "mode": payload.get("mode"),
        "submitted": payload.get("submitted"),
        "symbol": state.get("symbol"),
        "position_status": state.get("status"),
        "remaining_volume": state.get("remaining_volume"),
        "current_price_krw": payload.get("current_price_krw"),
        "asset_balance": payload.get("asset_balance"),
        "krw_balance": payload.get("krw_balance"),
        "last_action": last_decision.get("action") if isinstance(last_decision, dict) else None,
        "last_reason": last_decision.get("reason") if isinstance(last_decision, dict) else None,
        "estimated_realized_pnl_krw": _safe_float(last_decision.get("estimated_realized_pnl_krw"))
        if isinstance(last_decision, dict)
        else None,
        "estimated_unrealized_pnl_krw": _estimate_unrealized_pnl_krw(state=state, payload=payload),
    }
    snapshot.update(_build_next_trigger_snapshot(state=state, current_price_krw=payload.get("current_price_krw")))
    snapshot.update(_build_position_progress_snapshot(state=state, payload=payload))
    if latest_json_path is not None:
        latest_json_path.parent.mkdir(parents=True, exist_ok=True)
        latest_json_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    if latest_text_path is not None:
        latest_text_path.parent.mkdir(parents=True, exist_ok=True)
        summary = _build_latest_event_text_summary(snapshot)
        latest_text_path.write_text(summary + "\n", encoding="utf-8")


def build_manager_run_log_record(
    *,
    status: str,
    state_path: Path,
    payload: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    state = (payload or {}).get("state", {}) if isinstance(payload, dict) else {}
    last_decision = state.get("last_decision", {}) if isinstance(state, dict) else {}
    record = {
        "logged_at_utc": _utc_now_iso(),
        "status": status,
        "error": error,
        "state_path": str(state_path),
        "mode": (payload or {}).get("mode") if isinstance(payload, dict) else None,
        "submitted": (payload or {}).get("submitted") if isinstance(payload, dict) else None,
        "current_price_krw": (payload or {}).get("current_price_krw") if isinstance(payload, dict) else None,
        "asset_balance": (payload or {}).get("asset_balance") if isinstance(payload, dict) else None,
        "krw_balance": (payload or {}).get("krw_balance") if isinstance(payload, dict) else None,
        "symbol": state.get("symbol") if isinstance(state, dict) else None,
        "position_status": state.get("status") if isinstance(state, dict) else None,
        "remaining_volume": state.get("remaining_volume") if isinstance(state, dict) else None,
        "last_action": last_decision.get("action") if isinstance(last_decision, dict) else None,
        "last_reason": last_decision.get("reason") if isinstance(last_decision, dict) else None,
    }
    if isinstance(state, dict):
        record.update(_build_next_trigger_snapshot(state=state, current_price_krw=(payload or {}).get("current_price_krw")))
        record.update(_build_position_progress_snapshot(state=state, payload=(payload or {})))
        prior_state = (payload or {}).get("prior_state") if isinstance(payload, dict) else None
        prior_snapshot = _build_prior_closed_position_snapshot(prior_state)
        if prior_snapshot:
            record.update(prior_snapshot)
    return record


def build_manager_event_log_record(
    *,
    event_type: str,
    state: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = state if isinstance(state, dict) else {}
    payload = payload if isinstance(payload, dict) else {}
    last_decision = state.get("last_decision", {}) if isinstance(state, dict) else {}
    record = {
        "logged_at_utc": _utc_now_iso(),
        "event_type": event_type,
        "mode": payload.get("mode"),
        "submitted": payload.get("submitted"),
        "symbol": state.get("symbol"),
        "position_status": state.get("status"),
        "remaining_volume": state.get("remaining_volume"),
        "current_price_krw": payload.get("current_price_krw"),
        "asset_balance": payload.get("asset_balance"),
        "krw_balance": payload.get("krw_balance"),
        "last_action": last_decision.get("action") if isinstance(last_decision, dict) else None,
        "last_reason": last_decision.get("reason") if isinstance(last_decision, dict) else None,
        "last_stage": last_decision.get("stage") if isinstance(last_decision, dict) else None,
        "estimated_realized_pnl_krw": _estimate_realized_pnl_krw(state=state, payload=payload),
        "estimated_unrealized_pnl_krw": _estimate_unrealized_pnl_krw(state=state, payload=payload),
    }
    record.update(_build_next_trigger_snapshot(state=state, current_price_krw=payload.get("current_price_krw")))
    record.update(_build_position_progress_snapshot(state=state, payload=payload))
    prior_state = payload.get("prior_state") if isinstance(payload, dict) else None
    record.update(_build_prior_closed_position_snapshot(prior_state))
    return record


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


def _extract_krw_balance(accounts_payload: Any) -> float | None:
    rows = accounts_payload
    if isinstance(accounts_payload, dict):
        for key in ("data", "accounts", "result"):
            candidate = accounts_payload.get(key)
            if isinstance(candidate, list):
                rows = candidate
                break
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, dict):
            continue
        currency = str(row.get("currency") or row.get("unit_currency") or "").upper()
        if currency != "KRW":
            continue
        for key in ("balance", "available_balance", "avail_balance", "available_krw"):
            amount = _safe_float(row.get(key))
            if amount is not None:
                return amount
    return None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _fetch_order_status(client: BithumbPrivateClient, *, order_response: dict[str, Any], client_order_id: str) -> dict[str, Any] | None:
    order_id = order_response.get("order_id")
    try:
        order = client.get_order(
            uuid=str(order_id) if order_id not in (None, "") else None,
            client_order_id=client_order_id,
        )
    except Exception:
        return None
    return {"order": order}


def _bootstrap_if_needed(
    *,
    state_path: Path,
    summary_path: Path,
    profile: LivePortfolioProfile | None,
    partial_take_profit_pct: float,
    full_take_profit_pct: float,
    partial_stop_loss_pct: float,
    full_stop_loss_pct: float,
    partial_take_profit_fraction: float,
    partial_stop_loss_fraction: float,
    event_log_path: Path | None = None,
    latest_event_json_path: Path | None = None,
    latest_event_text_path: Path | None = None,
) -> dict[str, Any]:
    existing = load_live_portfolio_state(state_path)
    if existing is not None:
        return existing
    summary_payload = _load_json(summary_path)
    state = bootstrap_live_portfolio_state(
        summary_payload,
        profile=profile,
        partial_take_profit_pct=partial_take_profit_pct,
        full_take_profit_pct=full_take_profit_pct,
        partial_stop_loss_pct=partial_stop_loss_pct,
        full_stop_loss_pct=full_stop_loss_pct,
        partial_take_profit_fraction=partial_take_profit_fraction,
        partial_stop_loss_fraction=partial_stop_loss_fraction,
    )
    save_live_portfolio_state(state_path, state)
    if event_log_path is not None:
        event_payload = build_manager_event_log_record(
            event_type="bootstrap_entry_state",
            state=state,
            payload={
                "mode": "bootstrap",
                "submitted": False,
                "reentry_enabled": False,
                "min_reentry_krw": None,
            },
        )
        append_manager_event_log(event_log_path, event_payload)
        write_latest_event_outputs(
            event_payload=event_payload,
            latest_json_path=latest_event_json_path,
            latest_text_path=latest_event_text_path,
        )
    return state


def _attempt_reentry(
    *,
    state: dict[str, Any],
    logs_dir: Path,
    output_dir: Path,
    execution_log: Path,
    event_log_path: Path,
    latest_event_json_path: Path | None,
    latest_event_text_path: Path | None,
    access_key: str | None,
    secret_key: str | None,
    client_order_prefix: str,
    allowed_markets: list[str] | None,
    strategy_track: str,
    max_total_quote_krw: float,
    reentry_notional_krw: float,
    status_poll_seconds: float,
    status_timeout_seconds: float,
    cancel_on_timeout: bool,
) -> dict[str, Any] | None:
    payload = run_live_autotrade(
        logs_dir=logs_dir,
        run_id=None,
        output_dir=output_dir,
        execution_log=execution_log,
        notional_krw=reentry_notional_krw,
        max_orders=1,
        strategy_track=strategy_track,
        access_key=access_key,
        secret_key=secret_key,
        client_order_prefix=client_order_prefix,
        allowed_markets=allowed_markets,
        max_total_quote_krw=max_total_quote_krw,
        status_poll_seconds=status_poll_seconds,
        status_timeout_seconds=status_timeout_seconds,
        cancel_on_timeout=cancel_on_timeout,
        allow_duplicate_submission=False,
        skip_exchange_duplicate_check=False,
        block_existing_asset_position=True,
        min_existing_asset_balance=0.000001,
    )
    if int(payload.get("submitted_count", 0) or 0) <= 0:
        return None
    return payload


def run_live_portfolio_manager(
    *,
    state_path: Path,
    summary_path: Path,
    logs_dir: Path,
    output_dir: Path,
    execution_log: Path,
    event_log_path: Path,
    latest_event_json_path: Path | None,
    latest_event_text_path: Path | None,
    access_key: str | None,
    secret_key: str | None,
    client_order_prefix: str,
    allowed_markets: list[str] | None,
    portfolio_profile: str,
    partial_take_profit_pct: float | None,
    full_take_profit_pct: float | None,
    partial_stop_loss_pct: float | None,
    full_stop_loss_pct: float | None,
    partial_take_profit_fraction: float | None,
    partial_stop_loss_fraction: float | None,
    min_order_volume: float,
    min_reentry_krw: float,
    reentry_notional_krw: float,
    max_total_quote_krw: float,
    submit: bool,
    reentry_enabled: bool,
    status_poll_seconds: float,
    status_timeout_seconds: float,
    cancel_on_timeout: bool,
) -> dict[str, Any]:
    profile = _resolve_profile(
        profile_name=portfolio_profile,
        partial_take_profit_pct=partial_take_profit_pct,
        full_take_profit_pct=full_take_profit_pct,
        partial_stop_loss_pct=partial_stop_loss_pct,
        full_stop_loss_pct=full_stop_loss_pct,
        partial_take_profit_fraction=partial_take_profit_fraction,
        partial_stop_loss_fraction=partial_stop_loss_fraction,
    )
    state = _bootstrap_if_needed(
        state_path=state_path,
        summary_path=summary_path,
        profile=profile,
        partial_take_profit_pct=profile.partial_take_profit_pct,
        full_take_profit_pct=profile.full_take_profit_pct,
        partial_stop_loss_pct=profile.partial_stop_loss_pct,
        full_stop_loss_pct=profile.full_stop_loss_pct,
        partial_take_profit_fraction=profile.partial_take_profit_fraction,
        partial_stop_loss_fraction=profile.partial_stop_loss_fraction,
        event_log_path=event_log_path,
        latest_event_json_path=latest_event_json_path,
        latest_event_text_path=latest_event_text_path,
    )

    public_client = BithumbPublicClient()
    private_client = BithumbPrivateClient(access_key=access_key, secret_key=secret_key)
    if not private_client.has_credentials():
        raise RuntimeError("Bithumb API credentials are missing")

    accounts_payload = private_client.get_accounts()
    symbol = str(state.get("symbol") or "").upper()
    market = str(state.get("market") or "").upper()
    asset_balance = _extract_asset_balance(accounts_payload, asset_symbol=symbol) or 0.0
    krw_balance = _extract_krw_balance(accounts_payload) or 0.0
    current_price_krw = public_client.get_current_price_krw(symbol)

    if str(state.get("status") or "").upper() == "OPEN":
        if asset_balance > 0:
            state["remaining_volume"] = asset_balance
        decision = decide_live_portfolio_action(
            state,
            current_price_krw=current_price_krw,
            min_order_volume=min_order_volume,
        )
        if decision["action"] != "sell":
            state = mark_manager_hold(state, reason=str(decision.get("reason") or "hold"), current_price_krw=current_price_krw)
            save_live_portfolio_state(state_path, state)
            result = {
                "mode": "manage_open_position",
                "submitted": False,
                "portfolio_profile": profile.to_state_payload(),
                "state": state,
                "current_price_krw": current_price_krw,
                "asset_balance": asset_balance,
                "krw_balance": krw_balance,
                "reentry_enabled": reentry_enabled,
                "min_reentry_krw": min_reentry_krw,
            }
            write_no_event_outputs(
                state=state,
                payload=result,
                latest_json_path=latest_event_json_path,
                latest_text_path=latest_event_text_path,
            )
            return result

        client_order_id = f"{client_order_prefix}-{symbol.lower()}-{decision['stage']}"
        order_body = private_client.build_market_sell_order_body(
            {"market": market, "volume": decision["volume"]},
            client_order_id=client_order_id,
        )
        result: dict[str, Any] = {
            "mode": "manage_open_position",
            "submitted": False,
            "portfolio_profile": profile.to_state_payload(),
            "sell_order_request": order_body,
            "state": state,
            "current_price_krw": current_price_krw,
            "asset_balance": asset_balance,
            "krw_balance": krw_balance,
            "reentry_enabled": reentry_enabled,
            "min_reentry_krw": min_reentry_krw,
            "decision": decision,
        }
        if not submit:
            return result

        order_response = private_client.create_order(order_body)
        order_status = _fetch_order_status(private_client, order_response=order_response, client_order_id=client_order_id)
        order_payload = (order_status or {}).get("order", {})
        executed_funds = _safe_float(order_payload.get("executed_funds"))
        paid_fee = _safe_float(order_payload.get("paid_fee"))
        state = apply_live_exit_fill(
            state,
            stage=str(decision["stage"]),
            reason=str(decision["reason"]),
            volume=float(decision["volume"]),
            current_price_krw=current_price_krw,
            order_id=str(order_response.get("order_id") or ""),
            client_order_id=client_order_id,
            paid_fee_krw=paid_fee,
            executed_funds_krw=executed_funds,
        )
        save_live_portfolio_state(state_path, state)
        result["submitted"] = True
        result["sell_order_response"] = order_response
        result["sell_order_status"] = order_status
        result["state"] = state
        event_payload = build_manager_event_log_record(
            event_type="exit_order_submitted",
            state=state,
            payload=result,
        )
        append_manager_event_log(event_log_path, event_payload)
        write_latest_event_outputs(
            event_payload=event_payload,
            latest_json_path=latest_event_json_path,
            latest_text_path=latest_event_text_path,
        )
        return result

    state = mark_manager_hold(state, reason="position_closed", current_price_krw=current_price_krw)
    if reentry_enabled and krw_balance >= float(min_reentry_krw):
        prior_closed_state = state
        reentry_payload = _attempt_reentry(
            state=state,
            logs_dir=logs_dir,
            output_dir=output_dir,
            execution_log=execution_log,
            event_log_path=event_log_path,
            latest_event_json_path=latest_event_json_path,
            latest_event_text_path=latest_event_text_path,
            access_key=access_key,
            secret_key=secret_key,
            client_order_prefix=client_order_prefix,
            allowed_markets=allowed_markets,
            strategy_track=profile.name,
            max_total_quote_krw=max_total_quote_krw,
            reentry_notional_krw=reentry_notional_krw,
            status_poll_seconds=status_poll_seconds,
            status_timeout_seconds=status_timeout_seconds,
            cancel_on_timeout=cancel_on_timeout,
        )
        if reentry_payload is not None:
            next_state = bootstrap_live_portfolio_state(
                reentry_payload,
                profile=profile,
                partial_take_profit_pct=profile.partial_take_profit_pct,
                full_take_profit_pct=profile.full_take_profit_pct,
                partial_stop_loss_pct=profile.partial_stop_loss_pct,
                full_stop_loss_pct=profile.full_stop_loss_pct,
                partial_take_profit_fraction=profile.partial_take_profit_fraction,
                partial_stop_loss_fraction=profile.partial_stop_loss_fraction,
            )
            save_live_portfolio_state(state_path, next_state)
            event_payload = build_manager_event_log_record(
                event_type="reentry_submitted",
                state=next_state,
                payload={
                    "mode": "reentry",
                    "submitted": True,
                    "current_price_krw": current_price_krw,
                    "asset_balance": asset_balance,
                    "krw_balance": krw_balance,
                    "reentry_enabled": reentry_enabled,
                    "min_reentry_krw": min_reentry_krw,
                    "prior_state": prior_closed_state,
                },
            )
            append_manager_event_log(event_log_path, event_payload)
            write_latest_event_outputs(
                event_payload=event_payload,
                latest_json_path=latest_event_json_path,
                latest_text_path=latest_event_text_path,
            )
            return {
                "mode": "reentry",
                "submitted": True,
                "portfolio_profile": profile.to_state_payload(),
                "current_price_krw": current_price_krw,
                "asset_balance": asset_balance,
                "krw_balance": krw_balance,
                "reentry_enabled": reentry_enabled,
                "min_reentry_krw": min_reentry_krw,
                "prior_state": prior_closed_state,
                "reentry_payload": reentry_payload,
                "state": next_state,
            }

    save_live_portfolio_state(state_path, state)
    result = {
        "mode": "closed_waiting",
        "submitted": False,
        "portfolio_profile": profile.to_state_payload(),
        "current_price_krw": current_price_krw,
        "asset_balance": asset_balance,
        "krw_balance": krw_balance,
        "reentry_enabled": reentry_enabled,
        "min_reentry_krw": min_reentry_krw,
        "state": state,
    }
    write_no_event_outputs(
        state=state,
        payload=result,
        latest_json_path=latest_event_json_path,
        latest_text_path=latest_event_text_path,
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage live Bithumb BTC position with partial exits and re-entry.")
    parser.add_argument("--state-path", default="logs\\bithumb_live_portfolio_state.json")
    parser.add_argument("--summary-path", default="artifacts\\live_execution\\bithumb_live_execution_summary_1h-demo.json")
    parser.add_argument("--logs-dir", default="logs")
    parser.add_argument("--output-dir", default="artifacts\\live_execution")
    parser.add_argument("--execution-log", default="logs\\bithumb_live_execution_log.jsonl")
    parser.add_argument("--manager-run-log", default="logs\\bithumb_live_portfolio_manager_runs.jsonl")
    parser.add_argument("--manager-event-log", default="logs\\bithumb_live_portfolio_events.jsonl")
    parser.add_argument("--manager-latest-event-json", default="logs\\bithumb_live_portfolio_event_latest.json")
    parser.add_argument("--manager-latest-event-text", default="logs\\bithumb_live_portfolio_event_latest.txt")
    parser.add_argument("--access-key", default=None)
    parser.add_argument("--secret-key", default=None)
    parser.add_argument("--client-order-prefix", default="live")
    parser.add_argument("--allowed-market", action="append", default=None)
    parser.add_argument("--portfolio-profile", choices=["operating", "attack"], default="operating")
    parser.add_argument("--partial-take-profit-pct", type=float, default=None)
    parser.add_argument("--full-take-profit-pct", type=float, default=None)
    parser.add_argument("--partial-stop-loss-pct", type=float, default=None)
    parser.add_argument("--full-stop-loss-pct", type=float, default=None)
    parser.add_argument("--partial-take-profit-fraction", type=float, default=None)
    parser.add_argument("--partial-stop-loss-fraction", type=float, default=None)
    parser.add_argument("--min-order-volume", type=float, default=0.00005)
    parser.add_argument("--min-reentry-krw", type=float, default=10000.0)
    parser.add_argument("--reentry-notional-krw", type=float, default=50000.0)
    parser.add_argument("--max-total-quote-krw", type=float, default=100000.0)
    parser.add_argument("--status-poll-seconds", type=float, default=2.0)
    parser.add_argument("--status-timeout-seconds", type=float, default=20.0)
    parser.add_argument("--cancel-on-timeout", action="store_true")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--reentry-enabled", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def _render_text(payload: dict[str, Any]) -> str:
    state = payload.get("state", {})
    last_decision = state.get("last_decision", {}) if isinstance(state, dict) else {}
    profile = payload.get("portfolio_profile", {}) if isinstance(payload, dict) else {}
    lines = [
        f"mode: {payload.get('mode', '-')}",
        f"submitted: {bool(payload.get('submitted', False))}",
        f"portfolio_profile: {profile.get('name', '-')}",
        f"profile_objective: {profile.get('objective', '-')}",
        f"symbol: {state.get('symbol', '-')}",
        f"status: {state.get('status', '-')}",
        f"remaining_volume: {float(state.get('remaining_volume', 0.0) or 0.0):.8f}",
        f"current_price_krw: {float(payload.get('current_price_krw', 0.0) or 0.0):,.0f}",
        f"krw_balance: {float(payload.get('krw_balance', 0.0) or 0.0):,.0f}",
        f"last_action: {last_decision.get('action', '-')}",
        f"last_reason: {last_decision.get('reason', '-')}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    state_path = Path(args.state_path)
    manager_run_log = Path(args.manager_run_log)
    manager_event_log = Path(args.manager_event_log)
    manager_latest_event_json = Path(args.manager_latest_event_json)
    manager_latest_event_text = Path(args.manager_latest_event_text)
    try:
        payload = run_live_portfolio_manager(
            state_path=state_path,
            summary_path=Path(args.summary_path),
            logs_dir=Path(args.logs_dir),
            output_dir=Path(args.output_dir),
            execution_log=Path(args.execution_log),
            event_log_path=manager_event_log,
            latest_event_json_path=manager_latest_event_json,
            latest_event_text_path=manager_latest_event_text,
            access_key=args.access_key,
            secret_key=args.secret_key,
            client_order_prefix=str(args.client_order_prefix),
            allowed_markets=args.allowed_market,
            portfolio_profile=str(args.portfolio_profile),
            partial_take_profit_pct=args.partial_take_profit_pct,
            full_take_profit_pct=args.full_take_profit_pct,
            partial_stop_loss_pct=args.partial_stop_loss_pct,
            full_stop_loss_pct=args.full_stop_loss_pct,
            partial_take_profit_fraction=args.partial_take_profit_fraction,
            partial_stop_loss_fraction=args.partial_stop_loss_fraction,
            min_order_volume=float(args.min_order_volume),
            min_reentry_krw=float(args.min_reentry_krw),
            reentry_notional_krw=float(args.reentry_notional_krw),
            max_total_quote_krw=float(args.max_total_quote_krw),
            submit=bool(args.submit),
            reentry_enabled=bool(args.reentry_enabled),
            status_poll_seconds=float(args.status_poll_seconds),
            status_timeout_seconds=float(args.status_timeout_seconds),
            cancel_on_timeout=bool(args.cancel_on_timeout),
        )
    except Exception as exc:
        append_manager_run_log(
            manager_run_log,
            build_manager_run_log_record(
                status="error",
                state_path=state_path,
                error=str(exc),
            ),
        )
        raise
    append_manager_run_log(
        manager_run_log,
        build_manager_run_log_record(
            status="ok",
            state_path=state_path,
            payload=payload,
        ),
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
