from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_PROFIT_REINVEST_RATE = 0.5
DEFAULT_DAILY_GROWTH_LIMIT = 0.10
DEFAULT_HARD_CEILING_MULTIPLE = 10.0


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if out == out and out not in {float("inf"), float("-inf")} else default


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def realized_profit_ratchet_cap(
    *,
    axis: str,
    base_cap_krw: float,
    realized_profit_krw: float,
    previous_effective_cap_krw: float | None = None,
    profit_reinvest_rate: float = DEFAULT_PROFIT_REINVEST_RATE,
    daily_growth_limit: float = DEFAULT_DAILY_GROWTH_LIMIT,
    hard_ceiling_krw: float | None = None,
) -> dict[str, Any]:
    base_cap = max(0.0, safe_float(base_cap_krw))
    realized_profit = safe_float(realized_profit_krw)
    reinvest_rate = max(0.0, safe_float(profit_reinvest_rate, DEFAULT_PROFIT_REINVEST_RATE))
    growth_limit = max(0.0, safe_float(daily_growth_limit, DEFAULT_DAILY_GROWTH_LIMIT))
    positive_profit = max(0.0, realized_profit)
    raw_cap = base_cap + positive_profit * reinvest_rate
    previous_cap = safe_float(previous_effective_cap_krw, base_cap)
    if previous_cap <= 0:
        previous_cap = base_cap
    growth_limited_cap = min(raw_cap, previous_cap * (1.0 + growth_limit)) if growth_limit else raw_cap
    ceiling = safe_float(hard_ceiling_krw, base_cap * DEFAULT_HARD_CEILING_MULTIPLE)
    if ceiling <= 0:
        ceiling = base_cap
    effective_cap = min(growth_limited_cap, ceiling)
    effective_cap = max(base_cap, effective_cap)
    effective_cap = round(effective_cap, 6)
    raw_cap = round(raw_cap, 6)
    growth_limited_cap = round(growth_limited_cap, 6)
    return {
        "axis": axis,
        "mode": "realized_profit_ratchet",
        "base_cap_krw": base_cap,
        "realized_profit_krw": realized_profit,
        "positive_realized_profit_krw": positive_profit,
        "profit_reinvest_rate": reinvest_rate,
        "raw_profit_adjusted_cap_krw": raw_cap,
        "previous_effective_cap_krw": previous_cap,
        "daily_growth_limit": growth_limit,
        "growth_limited_cap_krw": growth_limited_cap,
        "hard_ceiling_krw": ceiling,
        "effective_cap_krw": effective_cap,
        "cap_increase_krw": max(0.0, effective_cap - base_cap),
    }


def previous_effective_cap_from_status(path: Path, *keys: str) -> float | None:
    data = load_json(path, {})
    cursor: Any = data
    for key in keys:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(key)
    value = safe_float(cursor, -1.0)
    return value if value >= 0 else None


def bithumb_realized_profit_from_events(event_dir: Path) -> float:
    total = 0.0
    seen: set[str] = set()
    if not event_dir.exists():
        return total
    for path in sorted(event_dir.glob("*_event_latest.json")):
        data = load_json(path, {})
        market = str(data.get("market") or path.name)
        if market in seen:
            continue
        seen.add(market)
        total += safe_float(data.get("cumulative_realized_pnl_krw"))
    return total


def kis_realized_profit_from_ledger(path: Path) -> float:
    total = 0.0
    if not path.exists():
        return total
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += safe_float(row.get("realized_pnl_krw") or row.get("realized_profit_krw"))
    return total


def axis_cap_config(policy: dict[str, Any], axis_prefix: str, *, fallback_cap_key: str) -> dict[str, float]:
    base_cap = safe_float(policy.get(f"{axis_prefix}_cap_krw", policy.get(fallback_cap_key)))
    return {
        "base_cap_krw": base_cap,
        "profit_reinvest_rate": safe_float(
            policy.get(f"{axis_prefix}_profit_reinvest_rate"),
            DEFAULT_PROFIT_REINVEST_RATE,
        ),
        "daily_growth_limit": safe_float(
            policy.get(f"{axis_prefix}_cap_daily_growth_limit"),
            DEFAULT_DAILY_GROWTH_LIMIT,
        ),
        "hard_ceiling_krw": safe_float(
            policy.get(f"{axis_prefix}_profit_cap_hard_ceiling_krw"),
            base_cap * DEFAULT_HARD_CEILING_MULTIPLE,
        ),
    }
