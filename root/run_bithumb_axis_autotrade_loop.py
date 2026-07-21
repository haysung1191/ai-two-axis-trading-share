from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from datetime import UTC, datetime
from datetime import timedelta
from pathlib import Path
from typing import Any

ROOT = Path(r"C:\AI")
CRYPTO_ROOT = ROOT / "Crypto"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(CRYPTO_ROOT) not in sys.path:
    sys.path.insert(0, str(CRYPTO_ROOT))

from build_bithumb_current_actionable_nonzero_signal_scout import (  # noqa: E402
    _load_candles,
    _load_live_candles,
    _latest_backfill_dir,
    _momentum_signal,
)
from scripts.execute_bithumb_execution_plan import (  # noqa: E402
    append_execution_log,
    build_execution_log_record,
    submit_execution_plan,
)
from scripts.run_bithumb_live_portfolio_manager import run_live_portfolio_manager  # noqa: E402
from src.data.bithumb_private_client import BithumbPrivateClient  # noqa: E402
from two_axis_account_engine import (  # noqa: E402
    build_account_target_diff,
    build_reconciliation,
    normalize_bithumb_account_snapshot,
    target_from_order_rows,
    unavailable_account_snapshot,
    write_axis_artifacts,
)
from two_axis_cap_ratchet import (  # noqa: E402
    axis_cap_config,
    bithumb_realized_profit_from_events,
    previous_effective_cap_from_status,
    realized_profit_ratchet_cap,
)

RUNSTATE = ROOT / "ops" / "runstate"
POLICY_JSON = RUNSTATE / "limited_live_policy.json"
GLOBAL_DISABLE = RUNSTATE / "DISABLE_ALL_TRADING"
OOS_JSON = ROOT / "reports" / "model_factory" / "bithumb_current_actionable_oos_walkforward_latest.json"
NON_ORCA_OOS_JSON = ROOT / "reports" / "model_factory" / "bithumb_non_orca_family_entry_source_rebuild_sweep_latest.json"
DIRECT_DEVELOPMENT_JSON = ROOT / "reports" / "model_factory" / "two_axis_direct_model_development_latest.json"
OUTPUT_DIR = CRYPTO_ROOT / "artifacts" / "bithumb_axis_autotrade"
STATE_DIR = CRYPTO_ROOT / "logs" / "bithumb_axis_portfolio_states"
EVENT_DIR = CRYPTO_ROOT / "logs" / "bithumb_axis_portfolio_events"
STATUS_JSON = ROOT / "ops" / "bithumb_axis_autotrade" / "bithumb_axis_autotrade_latest.json"
STATUS_MD = ROOT / "ops" / "bithumb_axis_autotrade" / "bithumb_axis_autotrade_latest.md"
ENTRY_SCAN_STATE_JSON = ROOT / "ops" / "bithumb_axis_autotrade" / "bithumb_entry_scan_state.json"
EXECUTION_LOG = CRYPTO_ROOT / "logs" / "bithumb_live_execution_log.jsonl"

MIN_BITHUMB_MARKET_BUY_KRW = 5000.0
DEFAULT_ORDER_KRW = 10000.0
STANDARD_CHECK_ORDER_REFERENCE = ["practical", "research", "contract", "brief"]


def utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def entry_scan_window(args: argparse.Namespace, now: datetime | None = None) -> tuple[bool, str, str]:
    mode = str(getattr(args, "entry_scan_cadence", "always") or "always")
    if mode == "always":
        return True, "always", utc_now()[:10]

    now = now or datetime.now(tz=UTC)
    hour_utc = int(getattr(args, "entry_scan_hour_utc", 15) or 15)
    if now.hour < hour_utc:
        close_date = (now.date() - timedelta(days=1)).isoformat()
        return False, f"daily_utc_waiting_for_{hour_utc:02d}00", close_date
    return True, f"daily_utc_after_{hour_utc:02d}00", now.date().isoformat()


def entry_scan_due(args: argparse.Namespace, now: datetime | None = None) -> tuple[bool, dict[str, Any]]:
    due_by_window, reason, date_key = entry_scan_window(args, now)
    state_path = Path(str(getattr(args, "entry_scan_state", ENTRY_SCAN_STATE_JSON)))
    state = read_json(state_path, {}) if state_path.exists() else {}
    last_completed_date = str(state.get("last_completed_date") or "")
    due = bool(due_by_window and last_completed_date != date_key)
    return due, {
        "cadence": str(getattr(args, "entry_scan_cadence", "always") or "always"),
        "due": due,
        "reason": reason,
        "date_key": date_key,
        "state_path": str(state_path),
        "last_completed_date": last_completed_date,
    }


def mark_entry_scan_complete(args: argparse.Namespace, scan: dict[str, Any], payload: dict[str, Any]) -> None:
    if scan.get("cadence") == "always" or not scan.get("due"):
        return
    state_path = Path(str(getattr(args, "entry_scan_state", ENTRY_SCAN_STATE_JSON)))
    write_json(
        state_path,
        {
            "updated_at_utc": utc_now(),
            "last_completed_date": scan.get("date_key"),
            "last_status": payload.get("status"),
            "triggered_candidate_count": payload.get("triggered_candidate_count", 0),
            "new_submitted_order_count": payload.get("new_submitted_order_count", 0),
        },
    )


def render_md(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Bithumb Axis Autotrade",
            "",
            f"- Status: `{payload['status']}`",
            f"- Submit enabled: `{payload['submit_enabled']}`",
            f"- Universe scanned: `{payload['universe_scanned_count']}`",
            f"- OOS candidate count: `{payload['oos_candidate_count']}`",
            f"- Triggered candidate count: `{payload['triggered_candidate_count']}`",
            f"- New submitted orders: `{payload['new_submitted_order_count']}`",
            f"- Managed open positions: `{payload['managed_open_position_count']}`",
            f"- Blockers: `{', '.join(payload['blockers']) if payload['blockers'] else 'none'}`",
            "",
        ]
    )


def load_policy() -> dict[str, Any]:
    policy = read_json(POLICY_JSON, {})
    required = {
        "policy_mode": "limited_live",
        "live_enabled": True,
        "broker_submit_allowed": True,
        "broker_submit_scope": "limited_live",
        "real_orders_allowed": True,
    }
    for key, expected in required.items():
        if policy.get(key) != expected:
            raise RuntimeError(f"limited live policy not enabled: {key}={policy.get(key)!r}")
    approval = str(policy.get("approval_text") or "")
    expected_approval = (
        f"LIVE APPROVE {int(safe_float(policy.get('crypto_cap_krw', policy.get('max_krw'))))} "
        f"{int(safe_float(policy.get('crypto_max_daily_loss_krw', policy.get('max_daily_loss_krw'))))} "
        f"{int(safe_float(policy.get('crypto_max_total_loss_krw', policy.get('max_total_loss_krw'))))}"
    )
    if expected_approval not in approval:
        raise RuntimeError("limited live approval text does not match policy caps")
    return policy


def list_bithumb_universe() -> list[str]:
    latest = _latest_backfill_dir()
    if latest is None:
        return []
    candle_dir = latest / "candles" / "1d"
    if not candle_dir.exists():
        return []
    return sorted(path.stem for path in candle_dir.glob("KRW-*.json"))


def load_oos_pass_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    primary = read_json(OOS_JSON, {})
    for row in primary.get("evaluations", []):
        if row.get("status") == "OOS_CANDIDATE_PASS":
            item = dict(row)
            item["source_file"] = str(OOS_JSON)
            item["robustness_status"] = row.get("robustness", {}).get("status")
            candidates.append(item)

    non_orca = read_json(NON_ORCA_OOS_JSON, {})
    for row in non_orca.get("trial_results", []):
        robustness_status = (row.get("robustness") or {}).get("status")
        if row.get("status") == "OOS_CANDIDATE_PASS" and robustness_status == "ROBUSTNESS_STRESS_PASS":
            item = dict(row)
            item["source_file"] = str(NON_ORCA_OOS_JSON)
            item["robustness_status"] = robustness_status
            candidates.append(item)

    direct = read_json(DIRECT_DEVELOPMENT_JSON, {})
    for row in (direct.get("crypto") or {}).get("top_candidates", []):
        if row.get("status") == "DIRECT_VALIDATED_PASS":
            item = dict(row)
            holdout = row.get("holdout_validation") or {}
            item["source_file"] = str(DIRECT_DEVELOPMENT_JSON)
            item["robustness_status"] = "DIRECT_HOLDOUT_HIGH_COST_PASS" if holdout.get("passed") else "DIRECT_HOLDOUT_ATTENTION"
            item["source_conversion"] = {
                "estimated_cagr": (holdout.get("holdout") or row.get("metrics") or {}).get("cagr"),
                "estimated_mdd": (holdout.get("holdout") or row.get("metrics") or {}).get("mdd"),
                "estimated_total_return": (holdout.get("holdout") or row.get("metrics") or {}).get("total_return"),
                "source_cagr": (row.get("metrics") or {}).get("cagr"),
                "source_mdd": (row.get("metrics") or {}).get("mdd"),
                "source_profit_factor": (row.get("metrics") or {}).get("profit_factor"),
                "pass_like": True,
            }
            item["aggregate"] = {
                "pass_fold_count": (row.get("walkforward") or {}).get("pass_fold_count"),
                "positive_fold_count": (row.get("walkforward") or {}).get("positive_fold_count"),
                "total_trade_count": (row.get("walkforward") or {}).get("total_trade_count"),
            }
            candidates.append(item)
    return candidates


def select_best_candidate_per_market(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        market = str(candidate.get("market") or "").upper()
        if not market:
            continue
        current = best.get(market)
        if current is None or candidate_rank(candidate) > candidate_rank(current):
            best[market] = candidate
    return sorted(best.values(), key=candidate_rank, reverse=True)


def candidate_rank(candidate: dict[str, Any]) -> tuple[float, int, float, str]:
    conversion = candidate.get("source_conversion") or candidate.get("conversion") or {}
    aggregate = candidate.get("aggregate") or {}
    return (
        safe_float(conversion.get("estimated_cagr")),
        int(aggregate.get("pass_fold_count") or 0),
        -abs(safe_float(conversion.get("estimated_mdd"))),
        str(candidate.get("candidate_id") or ""),
    )


def transform_candles_for_candidate(candles: list[dict[str, Any]], params: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(candles)
    window_policy = str(params.get("data_window_policy") or "").lower()
    if window_policy == "recent_regime_365d":
        rows = rows[-365:]
    elif window_policy == "post_listing_warmup_90d":
        rows = rows[90:]

    price_source = str(params.get("price_source") or "close").lower()
    if price_source not in {"hlc3", "ohlc4"}:
        return rows
    transformed: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        high = safe_float(row.get("high"))
        low = safe_float(row.get("low"))
        close = safe_float(row.get("close"))
        open_ = safe_float(row.get("open"))
        if price_source == "hlc3":
            item["close"] = (high + low + close) / 3.0
        else:
            item["close"] = (open_ + high + low + close) / 4.0
        transformed.append(item)
    return transformed


def range_breakout_retest_signal(candles: list[dict[str, Any]], params: dict[str, Any]) -> dict[str, Any]:
    lookback = int(params.get("lookback_bars", 5) or 5)
    volume_window = int(params.get("volume_window", 20) or 20)
    threshold = safe_float(params.get("momentum_threshold"))
    volume_floor = safe_float(params.get("volume_ratio_floor"), 1.0)
    if len(candles) <= max(lookback + 1, volume_window + 1):
        return {"triggered": False, "reason": "insufficient_candles"}

    closes = [safe_float(row.get("close")) for row in candles]
    highs = [safe_float(row.get("high")) for row in candles]
    volumes = [safe_float(row.get("volume")) for row in candles]
    latest = closes[-1]
    base = closes[-lookback - 1]
    prior_high = max(highs[-lookback - 1:-1])
    avg_volume = sum(volumes[-volume_window - 1:-1]) / volume_window
    volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 0.0
    momentum = latest / base - 1.0 if base > 0 else 0.0
    breakout = latest >= prior_high * (1.0 - 0.005)
    triggered = breakout and momentum >= threshold and volume_ratio >= volume_floor
    return {
        "triggered": triggered,
        "entry_signal_family": "range_breakout_retest",
        "breakout": breakout,
        "prior_high": prior_high,
        "momentum": momentum,
        "momentum_threshold": threshold,
        "volume_ratio": volume_ratio,
        "volume_ratio_floor": volume_floor,
        "latest_close": latest,
        "base_close": base,
    }


def evaluate_candidate_signal(candidate: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    market = str(candidate.get("market") or "").upper()
    timeframe = str(candidate.get("timeframe") or "1d")
    live_candles, live_meta = _load_live_candles(market, timeframe, count=200)
    candles = live_candles or _load_candles(market, timeframe)
    data_meta = live_meta if live_candles else {
        "source": "local_bithumb_backfill_archive",
        "status": "FALLBACK_ARCHIVE_USED",
        "row_count": len(candles),
        "latest_timestamp": candles[-1]["timestamp"].isoformat() if candles else None,
        "live_fetch": live_meta,
    }
    params = candidate.get("parameters") or {}
    transformed = transform_candles_for_candidate(candles, params)
    family = str(params.get("entry_signal_family") or "momentum").lower()
    if family == "range_breakout_retest":
        signal = range_breakout_retest_signal(transformed, params)
    else:
        signal = _momentum_signal(transformed, params)
    return signal, data_meta


def discover_open_states(state_dir: Path) -> list[Path]:
    paths: list[Path] = []
    known = [
        CRYPTO_ROOT / "logs" / "bithumb_live_orca_portfolio_state.json",
        CRYPTO_ROOT / "logs" / "bithumb_live_portfolio_state.json",
    ]
    for path in known:
        if path.exists():
            paths.append(path)
    if state_dir.exists():
        paths.extend(sorted(state_dir.glob("*.json")))
    dedup: dict[str, Path] = {}
    for path in paths:
        dedup[str(path.resolve()).lower()] = path
    return list(dedup.values())


def load_open_positions(state_dir: Path) -> dict[str, dict[str, Any]]:
    positions: dict[str, dict[str, Any]] = {}
    for path in discover_open_states(state_dir):
        try:
            state = read_json(path, {})
        except json.JSONDecodeError:
            continue
        if str(state.get("status") or "").upper() != "OPEN":
            continue
        market = str(state.get("market") or "").upper()
        if not market:
            continue
        exposure = safe_float(state.get("entry_price_krw")) * safe_float(state.get("remaining_volume"))
        positions[market] = {
            "market": market,
            "symbol": state.get("symbol"),
            "state_path": str(path),
            "entry_summary_path": state.get("entry_summary_path"),
            "remaining_volume": state.get("remaining_volume"),
            "estimated_exposure_krw": exposure,
        }
    return positions


def load_bithumb_account_snapshot() -> dict[str, Any]:
    try:
        client = BithumbPrivateClient()
        if not client.has_credentials():
            return unavailable_account_snapshot("BITHUMB_KRW", reason="bithumb_credentials_unavailable")
        return normalize_bithumb_account_snapshot(account_rows=client.get_accounts())
    except Exception as exc:
        return unavailable_account_snapshot("BITHUMB_KRW", reason=f"bithumb_account_unavailable:{exc}")


def write_account_engine_artifacts(
    *,
    selected_entries: list[dict[str, Any]],
    submitted_entries: list[dict[str, Any]],
) -> dict[str, str]:
    account_snapshot = load_bithumb_account_snapshot()
    target_rows = [
        {
            "Symbol": str(row.get("market") or "").replace("KRW-", ""),
            "Market": row.get("market"),
            "AssetType": "CRYPTO",
            "CandidateId": row.get("candidate_id"),
            "TargetNotionalKRW": row.get("notional_krw"),
            "CurrentPrice": 0,
            "SubmitAllowed": True,
        }
        for row in selected_entries
    ]
    target_portfolio = target_from_order_rows("BITHUMB_KRW", target_rows)
    diff = build_account_target_diff(
        axis="BITHUMB_KRW",
        account_snapshot=account_snapshot,
        target_portfolio=target_portfolio,
        min_notional_krw=MIN_BITHUMB_MARKET_BUY_KRW,
    )
    reconciliation = build_reconciliation(
        axis="BITHUMB_KRW",
        submitted_events=submitted_entries,
        account_snapshot=account_snapshot,
    )
    return write_axis_artifacts(
        root=ROOT,
        axis_slug="bithumb_krw",
        account_snapshot=account_snapshot,
        target_portfolio=target_portfolio,
        diff=diff,
        reconciliation=reconciliation,
    )


def manage_open_positions(
    positions: dict[str, dict[str, Any]],
    *,
    submit: bool,
    state_dir: Path,
    output_dir: Path,
) -> list[dict[str, Any]]:
    managed: list[dict[str, Any]] = []
    for market, position in sorted(positions.items()):
        state_path = Path(position["state_path"])
        summary_path = Path(str(position.get("entry_summary_path") or ""))
        if not summary_path.exists():
            managed.append({"market": market, "status": "SKIPPED", "reason": "entry_summary_missing"})
            continue
        event_stem = market.lower().replace("krw-", "")
        try:
            payload = run_live_portfolio_manager(
                state_path=state_path,
                summary_path=summary_path,
                logs_dir=CRYPTO_ROOT / "logs",
                output_dir=output_dir,
                execution_log=EXECUTION_LOG,
                event_log_path=EVENT_DIR / f"{event_stem}_events.jsonl",
                latest_event_json_path=EVENT_DIR / f"{event_stem}_event_latest.json",
                latest_event_text_path=EVENT_DIR / f"{event_stem}_event_latest.txt",
                access_key=None,
                secret_key=None,
                client_order_prefix=f"axis-exit-{event_stem}",
                allowed_markets=[market],
                portfolio_profile="operating",
                partial_take_profit_pct=None,
                full_take_profit_pct=None,
                partial_stop_loss_pct=None,
                full_stop_loss_pct=None,
                partial_take_profit_fraction=None,
                partial_stop_loss_fraction=None,
                min_order_volume=0.00005,
                min_reentry_krw=10000.0,
                reentry_notional_krw=10000.0,
                max_total_quote_krw=100000.0,
                submit=submit,
                reentry_enabled=False,
                status_poll_seconds=2.0,
                status_timeout_seconds=20.0,
                cancel_on_timeout=True,
            )
            managed.append(
                {
                    "market": market,
                    "mode": payload.get("mode"),
                    "submitted": payload.get("submitted"),
                    "position_status": (payload.get("state") or {}).get("status"),
                    "last_decision": (payload.get("state") or {}).get("last_decision"),
                    "current_price_krw": payload.get("current_price_krw"),
                    "state_path": str(state_path),
                }
            )
        except Exception as exc:
            managed.append({"market": market, "status": "ERROR", "error": str(exc), "state_path": str(state_path)})
    return managed


def build_plan(candidate: dict[str, Any], signal: dict[str, Any], *, notional_krw: float, run_id: str) -> dict[str, Any]:
    market = str(candidate.get("market") or "").upper()
    symbol = market.replace("KRW-", "")
    params = candidate.get("parameters") or {}
    latest_close = safe_float(signal.get("latest_close"))
    stop_loss = safe_float(params.get("stop_loss"))
    take_profit = safe_float(params.get("take_profit"))
    intent = {
        "symbol": symbol,
        "market": market,
        "side": "buy",
        "order_type": "market",
        "quote_amount_krw": float(notional_krw),
        "reference_price_krw": latest_close or None,
        "suggested_stop_price_krw": latest_close * (1.0 - stop_loss) if latest_close and stop_loss else None,
        "suggested_take_profit_price_krw": latest_close * (1.0 + take_profit) if latest_close and take_profit else None,
        "time_exit_utc": None,
        "source_candidate_id": candidate.get("candidate_id"),
        "source_file": candidate.get("source_file"),
        "source_signal": signal,
    }
    return {
        "run_id": run_id,
        "generated_at_utc": utc_now(),
        "strategy_track": "bithumb_axis_autotrade",
        "intent_count": 1,
        "order_intents": [intent],
        "standard_check_order_reference": list(STANDARD_CHECK_ORDER_REFERENCE),
    }


def submit_new_entry(
    candidate: dict[str, Any],
    signal: dict[str, Any],
    *,
    policy: dict[str, Any],
    notional_krw: float,
    output_dir: Path,
) -> dict[str, Any]:
    market = str(candidate.get("market") or "").upper()
    symbol = market.replace("KRW-", "").lower()
    run_id = f"bithumb-axis-{symbol}-{datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%SZ')}"
    plan = build_plan(candidate, signal, notional_krw=notional_krw, run_id=run_id)
    plan_path = output_dir / f"{run_id}_plan.json"
    summary_path = output_dir / f"{run_id}_summary.json"
    write_json(plan_path, plan)
    summary = submit_execution_plan(
        plan,
        access_key=None,
        secret_key=None,
        client_order_prefix=f"axis-{symbol}-{datetime.now(tz=UTC).strftime('%H%M%S')}",
        allowed_markets=[market],
        max_total_quote_krw=min(safe_float(policy.get("max_order_krw")), safe_float(policy.get("max_krw"))),
        status_poll_seconds=2.0,
        status_timeout_seconds=20.0,
        cancel_on_timeout=True,
    )
    summary["artifacts"] = {
        "plan_json": str(plan_path),
        "summary_json": str(summary_path),
        "execution_log": str(EXECUTION_LOG),
    }
    write_json(summary_path, summary)
    append_execution_log(EXECUTION_LOG, build_execution_log_record(summary, plan_path=str(plan_path), mode="submit"))

    state_path = STATE_DIR / f"{market.lower().replace('krw-', '')}_state.json"
    EVENT_DIR.mkdir(parents=True, exist_ok=True)
    manager_payload = run_live_portfolio_manager(
        state_path=state_path,
        summary_path=summary_path,
        logs_dir=CRYPTO_ROOT / "logs",
        output_dir=output_dir,
        execution_log=EXECUTION_LOG,
        event_log_path=EVENT_DIR / f"{symbol}_events.jsonl",
        latest_event_json_path=EVENT_DIR / f"{symbol}_event_latest.json",
        latest_event_text_path=EVENT_DIR / f"{symbol}_event_latest.txt",
        access_key=None,
        secret_key=None,
        client_order_prefix=f"axis-exit-{symbol}",
        allowed_markets=[market],
        portfolio_profile="operating",
        partial_take_profit_pct=None,
        full_take_profit_pct=None,
        partial_stop_loss_pct=None,
        full_stop_loss_pct=None,
        partial_take_profit_fraction=None,
        partial_stop_loss_fraction=None,
        min_order_volume=0.00005,
        min_reentry_krw=10000.0,
        reentry_notional_krw=10000.0,
        max_total_quote_krw=safe_float(policy.get("max_krw")),
        submit=True,
        reentry_enabled=False,
        status_poll_seconds=2.0,
        status_timeout_seconds=20.0,
        cancel_on_timeout=True,
    )
    return {
        "market": market,
        "candidate_id": candidate.get("candidate_id"),
        "notional_krw": notional_krw,
        "submitted_count": summary.get("submitted_count"),
        "summary_path": str(summary_path),
        "state_path": str(state_path),
        "manager_mode": manager_payload.get("mode"),
        "position_status": (manager_payload.get("state") or {}).get("status"),
    }


def run_once(args: argparse.Namespace) -> dict[str, Any]:
    generated_at = utc_now()
    blockers: list[str] = []
    submit_enabled = bool(args.submit)
    if GLOBAL_DISABLE.exists():
        blockers.append("DISABLE_ALL_TRADING_PRESENT")
        submit_enabled = False

    policy = load_policy()
    entry_due, entry_scan = entry_scan_due(args)
    universe = list_bithumb_universe() if entry_due else []
    oos_candidates = select_best_candidate_per_market(load_oos_pass_candidates()) if entry_due else []
    oos_markets = {str(row.get("market") or "").upper() for row in oos_candidates}
    skipped_non_oos = [market for market in universe if market not in oos_markets]
    open_positions = load_open_positions(Path(args.state_dir))
    managed = manage_open_positions(
        open_positions,
        submit=submit_enabled,
        state_dir=Path(args.state_dir),
        output_dir=Path(args.output_dir),
    )

    triggered: list[dict[str, Any]] = []
    evaluated: list[dict[str, Any]] = []
    if entry_due:
        for candidate in oos_candidates:
            signal, data_meta = evaluate_candidate_signal(candidate)
            row = {
                "candidate_id": candidate.get("candidate_id"),
                "market": candidate.get("market"),
                "status": candidate.get("status"),
                "robustness_status": candidate.get("robustness_status"),
                "source_file": candidate.get("source_file"),
                "signal": signal,
                "data": data_meta,
                "rank": candidate_rank(candidate),
            }
            evaluated.append(row)
            if signal.get("triggered"):
                triggered.append(row | {"candidate": candidate})
        triggered.sort(key=lambda row: row["rank"], reverse=True)

    cap_cfg = axis_cap_config(policy, "crypto", fallback_cap_key="max_krw")
    cap_ratchet = realized_profit_ratchet_cap(
        axis="BITHUMB_KRW",
        base_cap_krw=cap_cfg["base_cap_krw"],
        realized_profit_krw=bithumb_realized_profit_from_events(EVENT_DIR),
        previous_effective_cap_krw=previous_effective_cap_from_status(STATUS_JSON, "safety", "effective_cap_krw"),
        profit_reinvest_rate=cap_cfg["profit_reinvest_rate"],
        daily_growth_limit=cap_cfg["daily_growth_limit"],
        hard_ceiling_krw=cap_cfg["hard_ceiling_krw"],
    )
    max_total = safe_float(cap_ratchet.get("effective_cap_krw"))
    max_order = safe_float(policy.get("crypto_max_order_krw", policy.get("max_order_krw")))
    current_exposure = sum(safe_float(row.get("estimated_exposure_krw")) for row in open_positions.values())
    remaining_cap = max(0.0, max_total - current_exposure)
    default_order = max(MIN_BITHUMB_MARKET_BUY_KRW, min(float(args.default_order_krw), max_order))

    submitted: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    for row in triggered:
        market = str(row.get("market") or "").upper()
        if market in open_positions:
            row["selection_skip_reason"] = "ALREADY_OPEN_POSITION"
            continue
        if remaining_cap < MIN_BITHUMB_MARKET_BUY_KRW:
            row["selection_skip_reason"] = "TOTAL_CAP_EXHAUSTED"
            continue
        notional = min(default_order, max_order, remaining_cap)
        if notional < MIN_BITHUMB_MARKET_BUY_KRW:
            row["selection_skip_reason"] = "ORDER_BELOW_BITHUMB_MINIMUM"
            continue
        selected.append({"market": market, "candidate_id": row.get("candidate_id"), "notional_krw": notional})
        if not submit_enabled:
            remaining_cap -= notional
            continue
        result = submit_new_entry(
            row["candidate"],
            row["signal"],
            policy=policy,
            notional_krw=notional,
            output_dir=Path(args.output_dir),
        )
        submitted.append(result)
        remaining_cap -= notional
        if len(submitted) >= int(args.max_new_orders):
            break
        if len(selected) >= int(args.max_new_orders) and not submit_enabled:
            break

    status = "BITHUMB_AXIS_AUTOTRADE_READY"
    if blockers and args.submit:
        status = "BITHUMB_AXIS_AUTOTRADE_BLOCKED"
    elif submit_enabled and submitted:
        status = "BITHUMB_AXIS_AUTOTRADE_SUBMITTED"
    elif triggered:
        status = "BITHUMB_AXIS_AUTOTRADE_SIGNAL_READY"
    elif not entry_due:
        status = "BITHUMB_AXIS_AUTOTRADE_POSITION_MONITOR_ONLY"
    else:
        status = "BITHUMB_AXIS_AUTOTRADE_NO_NEW_SIGNAL"

    payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": generated_at,
        "status": status,
        "submit_enabled": submit_enabled,
        "entry_scan": entry_scan,
        "policy_path": str(POLICY_JSON),
        "global_disable_present": GLOBAL_DISABLE.exists(),
        "universe_scanned_count": len(universe),
        "oos_candidate_count": len(oos_candidates),
        "oos_markets": sorted(oos_markets),
        "skipped_non_oos_market_count": len(skipped_non_oos),
        "evaluated_oos_candidate_count": len(evaluated),
        "triggered_candidate_count": len(triggered),
        "selected_new_entry_count": len(selected),
        "new_submitted_order_count": sum(int(row.get("submitted_count") or 0) for row in submitted),
        "managed_open_position_count": len(open_positions),
        "current_open_positions": open_positions,
        "managed_positions": managed,
        "current_exposure_krw_estimate": current_exposure,
        "remaining_cap_krw_estimate": remaining_cap,
        "selected_new_entries": selected,
        "submitted_new_entries": submitted,
        "triggered_candidates": [
            {key: value for key, value in row.items() if key != "candidate"} for row in triggered
        ],
        "evaluated_candidates": evaluated,
        "blockers": blockers,
        "safety": {
            "max_total_krw": max_total,
            "base_cap_krw": cap_ratchet["base_cap_krw"],
            "effective_cap_krw": cap_ratchet["effective_cap_krw"],
            "cap_ratchet": cap_ratchet,
            "max_order_krw": max_order,
            "default_order_krw": default_order,
            "max_daily_loss_krw": safe_float(policy.get("crypto_max_daily_loss_krw", policy.get("max_daily_loss_krw"))),
            "max_total_loss_krw": safe_float(policy.get("crypto_max_total_loss_krw", policy.get("max_total_loss_krw"))),
            "reentry_enabled": False,
        },
    }
    payload["account_engine_artifacts"] = write_account_engine_artifacts(
        selected_entries=selected,
        submitted_entries=submitted,
    )
    write_json(STATUS_JSON, payload)
    STATUS_MD.parent.mkdir(parents=True, exist_ok=True)
    STATUS_MD.write_text(render_md(payload), encoding="utf-8")
    mark_entry_scan_complete(args, entry_scan, payload)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the account-level Bithumb axis autotrade loop.")
    parser.add_argument("--submit", action="store_true", help="Allow real Bithumb order submission under limited_live_policy caps.")
    parser.add_argument("--loop", action="store_true", help="Keep running instead of one cycle.")
    parser.add_argument("--interval-seconds", type=int, default=300)
    parser.add_argument("--max-new-orders", type=int, default=3)
    parser.add_argument("--default-order-krw", type=float, default=DEFAULT_ORDER_KRW)
    parser.add_argument("--entry-scan-cadence", choices=["always", "daily_utc"], default="always")
    parser.add_argument("--entry-scan-hour-utc", type=int, default=15)
    parser.add_argument("--entry-scan-state", default=str(ENTRY_SCAN_STATE_JSON))
    parser.add_argument("--state-dir", default=str(STATE_DIR))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--format", choices=["json", "text"], default="json")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    Path(args.state_dir).mkdir(parents=True, exist_ok=True)
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    while True:
        payload = run_once(args)
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(render_md(payload))
        if not args.loop:
            return 0
        time.sleep(max(30, int(args.interval_seconds)))


if __name__ == "__main__":
    raise SystemExit(main())
