from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
MOMENTUM_ROOT = ROOT / "momentum"
if str(MOMENTUM_ROOT) not in sys.path:
    sys.path.insert(0, str(MOMENTUM_ROOT))

from kis_api import KISApi  # noqa: E402
from two_axis_account_engine import (  # noqa: E402
    AxisExecutionLease,
    build_account_target_diff,
    build_reconciliation,
    normalize_kis_account_snapshot,
    target_from_order_rows,
    unavailable_account_snapshot,
    write_axis_artifacts,
)
from two_axis_cap_ratchet import (  # noqa: E402
    axis_cap_config,
    kis_realized_profit_from_ledger,
    previous_effective_cap_from_status,
    realized_profit_ratchet_cap,
)


ORDER_INTENT_CSV = ROOT / "ops" / "stock_etf_operating_candidate_bridge" / "stock_etf_operating_order_intent_latest.csv"
LIMITED_LIVE_POLICY_PATH = ROOT / "ops" / "runstate" / "limited_live_policy.json"
BROKER_POLICY_PATH = ROOT / "ops" / "runstate" / "broker_paper_policy.json"
OPS_DIR = ROOT / "ops" / "stock_etf_axis_operation"
LEDGER_PATH = OPS_DIR / "kis_stock_etf_order_ledger.jsonl"
LATEST_PATH = OPS_DIR / "kis_stock_etf_order_submit_latest.json"
ACCOUNT_ENGINE_LOCK = ROOT / "ops" / "account_engine" / "kis_combined_krw" / "axis_execution.lock"
ACCOUNT_ENGINE_ROOT = ROOT


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_order_intents(path: Path | None = None) -> list[dict[str, str]]:
    path = path or ORDER_INTENT_CSV
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_success_keys(path: Path | None = None) -> set[str]:
    path = path or LEDGER_PATH
    keys: set[str] = set()
    if not path.exists():
        return keys
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("status") == "SUBMITTED" and row.get("idempotency_key"):
            keys.add(str(row["idempotency_key"]))
    return keys


def managed_symbols_from_ledger(path: Path | None = None) -> set[str]:
    path = path or LEDGER_PATH
    symbols: set[str] = set()
    if not path.exists():
        return symbols
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("status") == "SUBMITTED" and row.get("symbol"):
            symbols.add(str(row["symbol"]).zfill(6))
    return symbols


def normalize_balance_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        symbol = str(row.get("pdno") or row.get("PDNO") or row.get("prdt_cd") or row.get("Symbol") or "").zfill(6)
        if not symbol or symbol == "000000":
            continue
        quantity = float(row.get("hldg_qty") or row.get("HLDG_QTY") or row.get("quantity") or 0)
        eval_amount = float(row.get("evlu_amt") or row.get("EVLU_AMT") or row.get("evaluation_amount") or 0.0)
        if quantity <= 0:
            continue
        out[symbol] = {"symbol": symbol, "quantity": quantity, "evaluation_amount_krw": eval_amount, "raw": row}
    return out


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def idempotency_key(row: dict[str, Any]) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return "|".join(
        [
            today,
            str(row.get("CandidateId", "")),
            str(row.get("Market", "")),
            str(row.get("Symbol", "")),
            str(row.get("ExecutionSide", "")),
        ]
    )


def domestic_fractional_orders_supported(api: Any | None) -> bool:
    if api is None:
        return False
    return bool(getattr(api, "domestic_fractional_orders_supported", False)) and callable(
        getattr(api, "place_domestic_fractional_order", None)
    )


def round_fractional_quantity(quantity: float) -> float:
    return round(max(0.0, float(quantity)), 8)


def policy_blockers(limited_live_policy: dict[str, Any], broker_policy: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not bool(limited_live_policy.get("live_enabled", False)):
        blockers.append("LIMITED_POLICY_LIVE_DISABLED")
    if not bool(limited_live_policy.get("broker_submit_allowed", False)):
        blockers.append("LIMITED_POLICY_SUBMIT_BLOCKED")
    if not bool(limited_live_policy.get("real_orders_allowed", False)):
        blockers.append("LIMITED_POLICY_REAL_ORDERS_BLOCKED")
    if not bool(broker_policy.get("broker_submit_allowed", False)):
        blockers.append("BROKER_POLICY_SUBMIT_BLOCKED")
    if not bool(broker_policy.get("live_enabled", False)):
        blockers.append("BROKER_POLICY_LIVE_DISABLED")
    if not bool(broker_policy.get("real_orders_allowed", False)):
        blockers.append("BROKER_POLICY_REAL_ORDERS_BLOCKED")
    if float(limited_live_policy.get("stock_cap_krw", 0.0) or 0.0) <= 0.0:
        blockers.append("STOCK_CAP_KRW_ZERO")
    if float(limited_live_policy.get("stock_max_order_krw", limited_live_policy.get("max_order_krw", 0.0)) or 0.0) <= 0.0:
        blockers.append("MAX_ORDER_KRW_ZERO")
    return blockers


def kr_market_open(now: datetime | None = None) -> bool:
    now = now or datetime.now(ZoneInfo("Asia/Seoul"))
    if now.weekday() >= 5:
        return False
    minutes = now.hour * 60 + now.minute
    return (9 * 60) <= minutes <= (15 * 60 + 20)


def append_ledger(events: list[dict[str, Any]], path: Path | None = None) -> None:
    if not events:
        return
    path = path or LEDGER_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def write_latest(payload: dict[str, Any], path: Path | None = None) -> None:
    path = path or LATEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def build_account_artifacts(
    *,
    rows: list[dict[str, Any]],
    holdings_by_symbol: dict[str, dict[str, Any]],
    submitted_events: list[dict[str, Any]] | None = None,
    unavailable_reason: str | None = None,
) -> dict[str, str]:
    account_snapshot = (
        unavailable_account_snapshot("KIS_COMBINED_KRW", reason=unavailable_reason)
        if unavailable_reason
        else normalize_kis_account_snapshot(balance_rows=[row["raw"] for row in holdings_by_symbol.values()])
    )
    target_portfolio = target_from_order_rows("KIS_COMBINED_KRW", rows)
    diff = build_account_target_diff(
        axis="KIS_COMBINED_KRW",
        account_snapshot=account_snapshot,
        target_portfolio=target_portfolio,
        managed_symbols=managed_symbols_from_ledger(),
        min_notional_krw=1.0,
    )
    reconciliation = build_reconciliation(
        axis="KIS_COMBINED_KRW",
        submitted_events=list(submitted_events or []),
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


def _submit_order_intents_unlocked(*, execute: bool, api: Any | None, enforce_market_session: bool) -> dict[str, Any]:
    limited_live_policy = load_json(LIMITED_LIVE_POLICY_PATH)
    broker_policy = load_json(BROKER_POLICY_PATH)
    blockers = policy_blockers(limited_live_policy, broker_policy)
    rows = load_order_intents()
    success_keys = load_success_keys()
    cap_cfg = axis_cap_config(limited_live_policy, "stock", fallback_cap_key="max_krw")
    cap_ratchet = realized_profit_ratchet_cap(
        axis="KIS_COMBINED_KRW",
        base_cap_krw=cap_cfg["base_cap_krw"],
        realized_profit_krw=kis_realized_profit_from_ledger(LEDGER_PATH),
        previous_effective_cap_krw=previous_effective_cap_from_status(LATEST_PATH, "safety", "effective_cap_krw"),
        profit_reinvest_rate=cap_cfg["profit_reinvest_rate"],
        daily_growth_limit=cap_cfg["daily_growth_limit"],
        hard_ceiling_krw=cap_cfg["hard_ceiling_krw"],
    )
    max_order_krw = float(limited_live_policy.get("stock_max_order_krw", limited_live_policy.get("max_order_krw", 0.0)) or 0.0)
    stock_cap_krw = float(cap_ratchet["effective_cap_krw"])
    submitted_notional = 0.0
    events: list[dict[str, Any]] = []
    holdings_by_symbol: dict[str, dict[str, Any]] = {}
    managed_symbols = managed_symbols_from_ledger()

    if blockers:
        artifacts = build_account_artifacts(rows=rows, holdings_by_symbol={}, unavailable_reason="policy_blocked")
        payload = {
            "generated_at_utc": utc_now(),
            "status": "KIS_ORDER_SUBMIT_BLOCKED",
            "execute": bool(execute),
            "blockers": blockers,
            "order_intent_rows": len(rows),
            "events": [],
            "ledger_path": str(LEDGER_PATH),
            "safety": {
                "base_cap_krw": cap_ratchet["base_cap_krw"],
                "effective_cap_krw": cap_ratchet["effective_cap_krw"],
                "max_order_krw": max_order_krw,
                "cap_ratchet": cap_ratchet,
            },
            "account_engine_artifacts": artifacts,
        }
        write_latest(payload)
        return payload

    if execute and enforce_market_session and not kr_market_open():
        artifacts = build_account_artifacts(rows=rows, holdings_by_symbol={}, unavailable_reason="market_closed")
        payload = {
            "generated_at_utc": utc_now(),
            "status": "KIS_ORDER_MARKET_CLOSED",
            "execute": bool(execute),
            "blockers": ["KR_MARKET_CLOSED"],
            "order_intent_rows": len(rows),
            "submitted_count": 0,
            "dry_run_ready_count": 0,
            "error_count": 0,
            "events": [],
            "ledger_path": str(LEDGER_PATH),
            "safety": {
                "base_cap_krw": cap_ratchet["base_cap_krw"],
                "effective_cap_krw": cap_ratchet["effective_cap_krw"],
                "max_order_krw": max_order_krw,
                "cap_ratchet": cap_ratchet,
            },
            "account_engine_artifacts": artifacts,
        }
        write_latest(payload)
        return payload

    if execute and api is None:
        try:
            api = KISApi()
        except Exception as exc:
            artifacts = build_account_artifacts(rows=rows, holdings_by_symbol={}, unavailable_reason="kis_credentials_unavailable")
            payload = {
                "generated_at_utc": utc_now(),
                "status": "KIS_ORDER_SUBMIT_CREDENTIALS_ERROR",
                "execute": bool(execute),
                "blockers": ["KIS_CREDENTIALS_UNAVAILABLE"],
                "order_intent_rows": len(rows),
                "submitted_count": 0,
                "dry_run_ready_count": 0,
                "error_count": 1,
                "error": str(exc),
                "events": [],
                "ledger_path": str(LEDGER_PATH),
                "safety": {
                    "base_cap_krw": cap_ratchet["base_cap_krw"],
                    "effective_cap_krw": cap_ratchet["effective_cap_krw"],
                    "max_order_krw": max_order_krw,
                    "cap_ratchet": cap_ratchet,
                },
                "account_engine_artifacts": artifacts,
            }
            write_latest(payload)
            return payload

    if api is not None:
        try:
            holdings_by_symbol = normalize_balance_rows(api.get_domestic_balance())
        except Exception as exc:
            if execute:
                artifacts = build_account_artifacts(rows=rows, holdings_by_symbol={}, unavailable_reason="kis_balance_unavailable")
                payload = {
                    "generated_at_utc": utc_now(),
                    "status": "KIS_ORDER_SUBMIT_BALANCE_ERROR",
                    "execute": bool(execute),
                    "blockers": ["KIS_BALANCE_UNAVAILABLE"],
                    "order_intent_rows": len(rows),
                    "submitted_count": 0,
                    "dry_run_ready_count": 0,
                    "error_count": 1,
                    "error": str(exc),
                    "events": [],
                    "ledger_path": str(LEDGER_PATH),
                    "safety": {
                        "base_cap_krw": cap_ratchet["base_cap_krw"],
                        "effective_cap_krw": cap_ratchet["effective_cap_krw"],
                        "max_order_krw": max_order_krw,
                        "cap_ratchet": cap_ratchet,
                    },
                    "account_engine_artifacts": artifacts,
                }
                write_latest(payload)
                return payload
            holdings_by_symbol = {}
    fractional_supported = domestic_fractional_orders_supported(api)
    current_managed_exposure = sum(
        float(holding.get("evaluation_amount_krw") or 0.0)
        for symbol, holding in holdings_by_symbol.items()
        if symbol in managed_symbols
    )

    for row in rows:
        key = idempotency_key(row)
        base_event = {
            "generated_at_utc": utc_now(),
            "idempotency_key": key,
            "candidate_id": row.get("CandidateId"),
            "market": row.get("Market"),
            "asset_type": row.get("AssetType"),
            "symbol": row.get("Symbol"),
            "side": row.get("ExecutionSide"),
        }
        if key in success_keys:
            events.append({**base_event, "status": "SKIPPED_ALREADY_SUBMITTED"})
            continue
        if not truthy(row.get("SubmitAllowed")):
            events.append({**base_event, "status": "SKIPPED_SUBMIT_NOT_ALLOWED"})
            continue
        if row.get("Market") != "KR":
            events.append({**base_event, "status": "SKIPPED_NON_KR_MARKET"})
            continue
        if row.get("ExecutionSide", "").upper() != "BUY":
            events.append({**base_event, "status": "SKIPPED_UNSUPPORTED_SIDE"})
            continue

        symbol = str(row["Symbol"]).zfill(6)
        target_notional = float(row.get("TargetNotionalKRW", 0.0) or 0.0)
        allowed_notional = min(target_notional, max_order_krw, max(0.0, stock_cap_krw - current_managed_exposure - submitted_notional))
        if allowed_notional <= 0.0:
            events.append(
                {
                    **base_event,
                    "status": "SKIPPED_CAP_EXHAUSTED",
                    "target_notional_krw": target_notional,
                    "current_managed_exposure_krw": current_managed_exposure,
                }
            )
            continue

        try:
            quote = api.get_domestic_quote(str(row["Symbol"])) if api is not None else {"price": float(row.get("CurrentPrice", 0.0) or 0.0)}
            quote_price = float(quote["price"])
            current_quantity = float((holdings_by_symbol.get(symbol) or {}).get("quantity") or 0.0)
            if fractional_supported:
                target_quantity = target_notional / quote_price
                allowed_quantity = allowed_notional / quote_price
                quantity = round_fractional_quantity(min(allowed_quantity, target_quantity - current_quantity))
            else:
                target_quantity = int(target_notional // quote_price)
                current_quantity = int(current_quantity)
                quantity = max(0, min(int(allowed_notional // quote_price), target_quantity - current_quantity))
            if quantity <= 0:
                events.append(
                    {
                        **base_event,
                        "status": "SKIPPED_TARGET_ALREADY_HELD" if current_quantity >= target_quantity and target_quantity > 0 else "SKIPPED_QUANTITY_ZERO",
                        "target_notional_krw": target_notional,
                        "allowed_notional_krw": allowed_notional,
                        "quote_price": quote_price,
                        "target_quantity": target_quantity,
                        "current_quantity": current_quantity,
                    }
                )
                continue
            estimated_notional = quantity * quote_price
            if execute:
                if fractional_supported:
                    response = api.place_domestic_fractional_order(
                        str(row["Symbol"]),
                        "BUY",
                        notional_krw=estimated_notional,
                        quantity=quantity,
                        order_type="market",
                    )
                else:
                    response = api.place_domestic_cash_order(str(row["Symbol"]), "BUY", int(quantity), order_type="market")
                status = "SUBMITTED"
            else:
                response = {"dry_run": True}
                status = "DRY_RUN_READY"
            submitted_notional += estimated_notional
            events.append(
                {
                    **base_event,
                    "status": status,
                    "target_notional_krw": target_notional,
                    "allowed_notional_krw": allowed_notional,
                    "quote_price": quote_price,
                    "target_quantity": target_quantity,
                    "current_quantity": current_quantity,
                    "quantity": quantity,
                    "quantity_mode": "fractional" if fractional_supported else "whole_share",
                    "estimated_notional_krw": estimated_notional,
                    "kis_response": response,
                }
            )
        except Exception as exc:
            events.append({**base_event, "status": "ERROR", "error": str(exc)})

    submitted = [event for event in events if event.get("status") == "SUBMITTED"]
    dry_ready = [event for event in events if event.get("status") == "DRY_RUN_READY"]
    errors = [event for event in events if event.get("status") == "ERROR"]
    append_ledger(submitted)
    artifacts = build_account_artifacts(rows=rows, holdings_by_symbol=holdings_by_symbol, submitted_events=submitted)
    payload = {
        "generated_at_utc": utc_now(),
        "status": "KIS_ORDER_SUBMIT_ERROR" if errors else ("KIS_ORDER_SUBMITTED" if submitted else ("KIS_ORDER_DRY_RUN_READY" if dry_ready else "KIS_ORDER_NO_SUBMITTABLE_QUANTITY")),
        "execute": bool(execute),
        "blockers": [],
        "order_intent_rows": len(rows),
        "submitted_count": len(submitted),
        "dry_run_ready_count": len(dry_ready),
        "error_count": len(errors),
        "submitted_estimated_notional_krw": sum(float(event.get("estimated_notional_krw", 0.0) or 0.0) for event in submitted),
        "current_managed_exposure_krw": current_managed_exposure,
        "managed_symbol_count": len(managed_symbols),
        "holding_count": len(holdings_by_symbol),
        "events": events,
        "ledger_path": str(LEDGER_PATH),
        "safety": {
            "base_cap_krw": cap_ratchet["base_cap_krw"],
            "effective_cap_krw": cap_ratchet["effective_cap_krw"],
            "max_order_krw": max_order_krw,
            "cap_ratchet": cap_ratchet,
        },
        "account_engine_artifacts": artifacts,
    }
    write_latest(payload)
    return payload


def submit_order_intents(*, execute: bool = True, api: Any | None = None, enforce_market_session: bool = True) -> dict[str, Any]:
    if execute:
        with AxisExecutionLease(ACCOUNT_ENGINE_LOCK, owner="kis_buy", ttl_seconds=1800):
            return _submit_order_intents_unlocked(execute=execute, api=api, enforce_market_session=enforce_market_session)
    return _submit_order_intents_unlocked(execute=execute, api=api, enforce_market_session=enforce_market_session)

def submit_order_intents_legacy_unused(*, execute: bool = True, api: Any | None = None, enforce_market_session: bool = True) -> dict[str, Any]:
    limited_live_policy = load_json(LIMITED_LIVE_POLICY_PATH)
    broker_policy = load_json(BROKER_POLICY_PATH)
    blockers = policy_blockers(limited_live_policy, broker_policy)
    rows = load_order_intents()
    success_keys = load_success_keys()
    max_order_krw = float(limited_live_policy.get("stock_max_order_krw", limited_live_policy.get("max_order_krw", 0.0)) or 0.0)
    stock_cap_krw = float(limited_live_policy.get("stock_cap_krw", 0.0) or 0.0)
    submitted_notional = 0.0
    events: list[dict[str, Any]] = []
    holdings_by_symbol: dict[str, dict[str, Any]] = {}
    managed_symbols = managed_symbols_from_ledger()

    if blockers:
        payload = {
            "generated_at_utc": utc_now(),
            "status": "KIS_ORDER_SUBMIT_BLOCKED",
            "execute": bool(execute),
            "blockers": blockers,
            "order_intent_rows": len(rows),
            "events": [],
            "ledger_path": str(LEDGER_PATH),
        }
        write_latest(payload)
        return payload

    if execute and enforce_market_session and not kr_market_open():
        payload = {
            "generated_at_utc": utc_now(),
            "status": "KIS_ORDER_MARKET_CLOSED",
            "execute": bool(execute),
            "blockers": ["KR_MARKET_CLOSED"],
            "order_intent_rows": len(rows),
            "submitted_count": 0,
            "dry_run_ready_count": 0,
            "error_count": 0,
            "events": [],
            "ledger_path": str(LEDGER_PATH),
        }
        write_latest(payload)
        return payload

    if execute and api is None:
        try:
            api = KISApi()
        except Exception as exc:
            payload = {
                "generated_at_utc": utc_now(),
                "status": "KIS_ORDER_SUBMIT_CREDENTIALS_ERROR",
                "execute": bool(execute),
                "blockers": ["KIS_CREDENTIALS_UNAVAILABLE"],
                "order_intent_rows": len(rows),
                "submitted_count": 0,
                "dry_run_ready_count": 0,
                "error_count": 1,
                "error": str(exc),
                "events": [],
                "ledger_path": str(LEDGER_PATH),
            }
            write_latest(payload)
            return payload

    if api is not None:
        try:
            holdings_by_symbol = normalize_balance_rows(api.get_domestic_balance())
        except Exception as exc:
            if execute:
                payload = {
                    "generated_at_utc": utc_now(),
                    "status": "KIS_ORDER_SUBMIT_BALANCE_ERROR",
                    "execute": bool(execute),
                    "blockers": ["KIS_BALANCE_UNAVAILABLE"],
                    "order_intent_rows": len(rows),
                    "submitted_count": 0,
                    "dry_run_ready_count": 0,
                    "error_count": 1,
                    "error": str(exc),
                    "events": [],
                    "ledger_path": str(LEDGER_PATH),
                }
                write_latest(payload)
                return payload
            holdings_by_symbol = {}
    current_managed_exposure = sum(
        float(holding.get("evaluation_amount_krw") or 0.0)
        for symbol, holding in holdings_by_symbol.items()
        if symbol in managed_symbols
    )

    for row in rows:
        key = idempotency_key(row)
        base_event = {
            "generated_at_utc": utc_now(),
            "idempotency_key": key,
            "candidate_id": row.get("CandidateId"),
            "market": row.get("Market"),
            "asset_type": row.get("AssetType"),
            "symbol": row.get("Symbol"),
            "side": row.get("ExecutionSide"),
        }
        if key in success_keys:
            events.append({**base_event, "status": "SKIPPED_ALREADY_SUBMITTED"})
            continue
        if not truthy(row.get("SubmitAllowed")):
            events.append({**base_event, "status": "SKIPPED_SUBMIT_NOT_ALLOWED"})
            continue
        if row.get("Market") != "KR":
            events.append({**base_event, "status": "SKIPPED_NON_KR_MARKET"})
            continue
        if row.get("ExecutionSide", "").upper() != "BUY":
            events.append({**base_event, "status": "SKIPPED_UNSUPPORTED_SIDE"})
            continue

        symbol = str(row["Symbol"]).zfill(6)
        target_notional = float(row.get("TargetNotionalKRW", 0.0) or 0.0)
        allowed_notional = min(target_notional, max_order_krw, max(0.0, stock_cap_krw - current_managed_exposure - submitted_notional))
        if allowed_notional <= 0.0:
            events.append(
                {
                    **base_event,
                    "status": "SKIPPED_CAP_EXHAUSTED",
                    "target_notional_krw": target_notional,
                    "current_managed_exposure_krw": current_managed_exposure,
                }
            )
            continue

        try:
            quote = api.get_domestic_quote(str(row["Symbol"])) if api is not None else {"price": float(row.get("CurrentPrice", 0.0) or 0.0)}
            quote_price = float(quote["price"])
            target_quantity = int(target_notional // quote_price)
            current_quantity = int((holdings_by_symbol.get(symbol) or {}).get("quantity") or 0)
            quantity = max(0, min(int(allowed_notional // quote_price), target_quantity - current_quantity))
            if quantity <= 0:
                events.append(
                    {
                        **base_event,
                        "status": "SKIPPED_TARGET_ALREADY_HELD" if current_quantity >= target_quantity and target_quantity > 0 else "SKIPPED_QUANTITY_ZERO",
                        "target_notional_krw": target_notional,
                        "allowed_notional_krw": allowed_notional,
                        "quote_price": quote_price,
                        "target_quantity": target_quantity,
                        "current_quantity": current_quantity,
                    }
                )
                continue
            estimated_notional = quantity * quote_price
            if execute:
                response = api.place_domestic_cash_order(str(row["Symbol"]), "BUY", quantity, order_type="market")
                status = "SUBMITTED"
            else:
                response = {"dry_run": True}
                status = "DRY_RUN_READY"
            submitted_notional += estimated_notional
            events.append(
                {
                    **base_event,
                    "status": status,
                    "target_notional_krw": target_notional,
                    "allowed_notional_krw": allowed_notional,
                    "quote_price": quote_price,
                    "target_quantity": target_quantity,
                    "current_quantity": current_quantity,
                    "quantity": quantity,
                    "estimated_notional_krw": estimated_notional,
                    "kis_response": response,
                }
            )
        except Exception as exc:
            events.append({**base_event, "status": "ERROR", "error": str(exc)})

    submitted = [event for event in events if event.get("status") == "SUBMITTED"]
    dry_ready = [event for event in events if event.get("status") == "DRY_RUN_READY"]
    errors = [event for event in events if event.get("status") == "ERROR"]
    append_ledger(submitted)
    payload = {
        "generated_at_utc": utc_now(),
        "status": "KIS_ORDER_SUBMIT_ERROR" if errors else ("KIS_ORDER_SUBMITTED" if submitted else ("KIS_ORDER_DRY_RUN_READY" if dry_ready else "KIS_ORDER_NO_SUBMITTABLE_QUANTITY")),
        "execute": bool(execute),
        "blockers": [],
        "order_intent_rows": len(rows),
        "submitted_count": len(submitted),
        "dry_run_ready_count": len(dry_ready),
        "error_count": len(errors),
        "submitted_estimated_notional_krw": sum(float(event.get("estimated_notional_krw", 0.0) or 0.0) for event in submitted),
        "current_managed_exposure_krw": current_managed_exposure,
        "managed_symbol_count": len(managed_symbols),
        "holding_count": len(holdings_by_symbol),
        "events": events,
        "ledger_path": str(LEDGER_PATH),
    }
    write_latest(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Submit real KIS orders. Without this flag, only compute order quantities.")
    parser.add_argument("--ignore-market-session", action="store_true", help="Allow calling KIS order API outside the local KR market-session guard.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    payload = submit_order_intents(execute=args.execute, enforce_market_session=not args.ignore_market_session)
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(f"status={payload['status']}")
    print(f"submitted_count={payload['submitted_count']}")
    print(f"error_count={payload['error_count']}")
    print(f"latest_path={LATEST_PATH}")


if __name__ == "__main__":
    main()
