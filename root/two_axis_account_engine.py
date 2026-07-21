from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


class AxisExecutionLease(AbstractContextManager["AxisExecutionLease"]):
    """Small file lease for one account-level execution section."""

    def __init__(self, path: Path, *, owner: str, ttl_seconds: int = 1800) -> None:
        self.path = path
        self.owner = owner
        self.ttl_seconds = int(ttl_seconds)
        self.acquired = False

    def __enter__(self) -> "AxisExecutionLease":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._clear_stale_lock()
        payload = {
            "owner": self.owner,
            "created_at_utc": utc_now(),
            "pid": os.getpid(),
            "ttl_seconds": self.ttl_seconds,
        }
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RuntimeError(f"axis execution lease already held: {self.path}") from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        self.acquired = True
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        if self.acquired:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
        self.acquired = False
        return False

    def _clear_stale_lock(self) -> None:
        if not self.path.exists():
            return
        age = time.time() - self.path.stat().st_mtime
        if age > self.ttl_seconds:
            self.path.unlink()


def normalize_kis_account_snapshot(
    *,
    balance_rows: list[dict[str, Any]],
    cash_krw: float | None = None,
    open_orders: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    positions: list[dict[str, Any]] = []
    for row in balance_rows:
        symbol = str(row.get("pdno") or row.get("PDNO") or row.get("prdt_cd") or row.get("Symbol") or "").zfill(6)
        if not symbol or symbol == "000000":
            continue
        quantity = safe_int(row.get("hldg_qty") or row.get("HLDG_QTY") or row.get("quantity"))
        if quantity <= 0:
            continue
        evaluation_amount = safe_float(row.get("evlu_amt") or row.get("EVLU_AMT") or row.get("evaluation_amount"))
        positions.append(
            {
                "symbol": symbol,
                "asset_type": "STOCK",
                "quantity": quantity,
                "evaluation_amount_krw": evaluation_amount,
                "raw": row,
            }
        )
    return {
        "axis": "KIS_COMBINED_KRW",
        "generated_at_utc": utc_now(),
        "source": "broker_kis_balance",
        "cash_krw": cash_krw,
        "position_count": len(positions),
        "positions": sorted(positions, key=lambda row: row["symbol"]),
        "open_orders": list(open_orders or []),
    }


def normalize_bithumb_account_snapshot(
    *,
    account_rows: list[dict[str, Any]],
    open_orders: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    positions: list[dict[str, Any]] = []
    cash_krw: float | None = None
    for row in account_rows:
        currency = str(row.get("currency") or row.get("unit_currency") or "").upper()
        if not currency:
            continue
        balance = safe_float(row.get("balance") or row.get("available_balance") or row.get("avail_balance"))
        locked = safe_float(row.get("locked"))
        avg_buy_price = safe_float(row.get("avg_buy_price"))
        if currency == "KRW":
            cash_krw = balance
            continue
        if balance <= 0 and locked <= 0:
            continue
        positions.append(
            {
                "symbol": currency,
                "market": f"KRW-{currency}",
                "asset_type": "CRYPTO",
                "quantity": balance,
                "locked_quantity": locked,
                "avg_buy_price_krw": avg_buy_price,
                "evaluation_amount_krw": balance * avg_buy_price if avg_buy_price > 0 else 0.0,
                "raw": row,
            }
        )
    return {
        "axis": "BITHUMB_KRW",
        "generated_at_utc": utc_now(),
        "source": "broker_bithumb_accounts",
        "cash_krw": cash_krw,
        "position_count": len(positions),
        "positions": sorted(positions, key=lambda row: row["symbol"]),
        "open_orders": list(open_orders or []),
    }


def unavailable_account_snapshot(axis: str, *, reason: str) -> dict[str, Any]:
    return {
        "axis": axis,
        "generated_at_utc": utc_now(),
        "source": "unavailable",
        "reason": reason,
        "cash_krw": None,
        "position_count": 0,
        "positions": [],
        "open_orders": [],
    }


def target_from_order_rows(axis: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    targets: list[dict[str, Any]] = []
    for row in rows:
        symbol = str(row.get("Symbol") or row.get("symbol") or "").strip()
        if not symbol:
            continue
        market = str(row.get("Market") or row.get("market") or "").strip()
        if axis == "KIS_COMBINED_KRW":
            symbol = symbol.zfill(6)
        current_price = safe_float(row.get("CurrentPrice") or row.get("current_price") or row.get("reference_price_krw"))
        target_notional = safe_float(row.get("TargetNotionalKRW") or row.get("target_notional_krw") or row.get("quote_amount_krw"))
        target_quantity = safe_float(row.get("TargetQuantity") or row.get("target_quantity"))
        if target_quantity <= 0 and current_price > 0 and target_notional > 0:
            target_quantity = int(target_notional // current_price) if axis == "KIS_COMBINED_KRW" else target_notional / current_price
        targets.append(
            {
                "symbol": symbol,
                "market": market or (f"KRW-{symbol}" if axis == "BITHUMB_KRW" and not symbol.startswith("KRW-") else market),
                "asset_type": row.get("AssetType") or row.get("asset_type"),
                "candidate_id": row.get("CandidateId") or row.get("candidate_id") or row.get("source_candidate_id"),
                "target_notional_krw": target_notional,
                "target_quantity": target_quantity,
                "current_price_krw": current_price,
                "target_weight": safe_float(row.get("TargetWeight") or row.get("target_weight")),
                "submit_allowed": truthy(row.get("SubmitAllowed", True)),
                "raw": row,
            }
        )
    return {
        "axis": axis,
        "generated_at_utc": utc_now(),
        "target_count": len(targets),
        "targets": sorted(targets, key=lambda row: row["symbol"]),
    }


def _positions_by_symbol(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in snapshot.get("positions", []) or []:
        symbol = str(row.get("symbol") or "").strip()
        if symbol:
            out[symbol] = row
    return out


def _targets_by_symbol(target: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in target.get("targets", []) or []:
        symbol = str(row.get("symbol") or "").strip()
        if symbol:
            out[symbol] = row
    return out


def build_account_target_diff(
    *,
    axis: str,
    account_snapshot: dict[str, Any],
    target_portfolio: dict[str, Any],
    managed_symbols: set[str] | None = None,
    min_notional_krw: float = 0.0,
    allow_unmanaged_sells: bool = False,
) -> dict[str, Any]:
    positions = _positions_by_symbol(account_snapshot)
    targets = _targets_by_symbol(target_portfolio)
    symbols = sorted(set(positions) | set(targets))
    decisions: list[dict[str, Any]] = []
    managed_symbols = set(managed_symbols or set())

    for symbol in symbols:
        current = positions.get(symbol, {})
        target = targets.get(symbol, {})
        current_qty = safe_float(current.get("quantity"))
        target_qty = safe_float(target.get("target_quantity"))
        price = safe_float(target.get("current_price_krw") or current.get("avg_buy_price_krw"))
        delta_qty = target_qty - current_qty
        delta_notional = abs(delta_qty) * price if price > 0 else abs(safe_float(target.get("target_notional_krw")) - safe_float(current.get("evaluation_amount_krw")))
        action = "HOLD"
        reason = "TARGET_MATCHED"
        if symbol not in targets and current_qty > 0:
            if allow_unmanaged_sells or symbol in managed_symbols:
                action = "SELL"
                reason = "NO_LONGER_IN_TARGET"
                delta_qty = -current_qty
            else:
                action = "HOLD_UNMANAGED"
                reason = "UNMANAGED_POSITION_NOT_IN_TARGET"
        elif delta_qty > 0 and delta_notional >= min_notional_krw and target.get("submit_allowed", True):
            action = "BUY"
            reason = "BELOW_TARGET"
        elif delta_qty < 0 and delta_notional >= min_notional_krw:
            action = "SELL"
            reason = "ABOVE_TARGET"
        elif delta_qty != 0:
            action = "HOLD"
            reason = "DELTA_BELOW_MIN_NOTIONAL"

        decisions.append(
            {
                "symbol": symbol,
                "market": target.get("market") or current.get("market"),
                "action": action,
                "reason": reason,
                "current_quantity": current_qty,
                "target_quantity": target_qty,
                "delta_quantity": delta_qty,
                "current_notional_krw": safe_float(current.get("evaluation_amount_krw")),
                "target_notional_krw": safe_float(target.get("target_notional_krw")),
                "delta_notional_krw_estimate": delta_notional,
                "candidate_id": target.get("candidate_id"),
            }
        )

    actionable = [row for row in decisions if row["action"] in {"BUY", "SELL"}]
    return {
        "axis": axis,
        "generated_at_utc": utc_now(),
        "decision_count": len(decisions),
        "actionable_count": len(actionable),
        "decisions": decisions,
    }


def build_reconciliation(
    *,
    axis: str,
    submitted_events: list[dict[str, Any]] | None = None,
    broker_orders: list[dict[str, Any]] | None = None,
    account_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    submitted_events = list(submitted_events or [])
    broker_orders = list(broker_orders or [])
    submitted_count = len([row for row in submitted_events if row.get("status") == "SUBMITTED"])
    unresolved_orders = [
        row for row in broker_orders
        if str(row.get("state") or row.get("status") or "").lower() not in {"done", "filled", "cancel", "cancelled", "rejected"}
    ]
    return {
        "axis": axis,
        "generated_at_utc": utc_now(),
        "submitted_event_count": submitted_count,
        "broker_order_count": len(broker_orders),
        "unresolved_order_count": len(unresolved_orders),
        "position_count": len((account_snapshot or {}).get("positions", []) or []),
        "submitted_events": submitted_events,
        "broker_orders": broker_orders,
        "unresolved_orders": unresolved_orders,
    }


def write_axis_artifacts(
    *,
    root: Path,
    axis_slug: str,
    account_snapshot: dict[str, Any],
    target_portfolio: dict[str, Any],
    diff: dict[str, Any],
    reconciliation: dict[str, Any],
) -> dict[str, str]:
    base = root / "ops" / "account_engine" / axis_slug
    paths = {
        "account_snapshot": base / "account_snapshot_latest.json",
        "target_portfolio": base / "target_portfolio_latest.json",
        "diff": base / "target_diff_latest.json",
        "reconciliation": base / "reconciliation_latest.json",
    }
    write_json(paths["account_snapshot"], account_snapshot)
    write_json(paths["target_portfolio"], target_portfolio)
    write_json(paths["diff"], diff)
    write_json(paths["reconciliation"], reconciliation)
    manifest = {
        "axis_slug": axis_slug,
        "generated_at_utc": utc_now(),
        "artifacts": {key: str(path) for key, path in paths.items()},
    }
    manifest_path = base / "account_engine_manifest_latest.json"
    write_json(manifest_path, manifest)
    return {key: str(path) for key, path in paths.items()} | {"manifest": str(manifest_path)}

