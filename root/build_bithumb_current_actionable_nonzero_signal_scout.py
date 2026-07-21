from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/operations/bithumb_current_actionable_nonzero_signal_scout_latest.json"
REPORT_MD = ROOT / "reports/operations/bithumb_current_actionable_nonzero_signal_scout_latest.md"
OOS_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_oos_walkforward_latest.json"
BITHUMB_BACKFILL_ROOT = ROOT / "Crypto/data/bithumb_stage2_archive/backfill_full"
BITHUMB_PUBLIC_API = "https://api.bithumb.com"
TOP_NEAR_MISS_LIMIT = 5

SAFETY = {
    "does_emit_order_signal": False,
    "does_write_order_intent": False,
    "paper_allowed_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "real_orders": 0,
}


SELECTION_POLICY = {
    "description": "top_triggered_candidate is selected from currently triggered candidates by source_conversion.estimated_cagr, then aggregate.pass_fold_count, descending.",
    "sort_keys": ["source_conversion.estimated_cagr", "aggregate.pass_fold_count"],
    "sort_order": "descending",
    "uses_oos_average_fold_cagr_as_primary_key": False,
}


def _read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _latest_backfill_dir() -> Path | None:
    if not BITHUMB_BACKFILL_ROOT.exists():
        return None
    dirs = [path for path in BITHUMB_BACKFILL_ROOT.iterdir() if path.is_dir()]
    return sorted(dirs, key=lambda path: path.name)[-1] if dirs else None


def _load_candles(market: str, timeframe: str) -> list[dict]:
    latest = _latest_backfill_dir()
    if latest is None:
        return []
    path = latest / "candles" / timeframe / f"{market}.json"
    rows = _read_json(path, [])
    candles = []
    for row in rows if isinstance(rows, list) else []:
        timestamp = row.get("candle_date_time_utc") or row.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        candles.append(
            {
                "timestamp": timestamp,
                "open": float(row.get("opening_price", row.get("open", 0.0)) or 0.0),
                "high": float(row.get("high_price", row.get("high", 0.0)) or 0.0),
                "low": float(row.get("low_price", row.get("low", 0.0)) or 0.0),
                "close": float(row.get("trade_price", row.get("close", 0.0)) or 0.0),
                "volume": float(row.get("candle_acc_trade_volume", row.get("volume", 0.0)) or 0.0),
            }
        )
    return sorted(candles, key=lambda row: row["timestamp"])


def _load_live_candles(market: str, timeframe: str, count: int = 200) -> tuple[list[dict], dict]:
    if timeframe != "1d":
        return [], {"source": "live_bithumb_public_api", "status": "UNSUPPORTED_TIMEFRAME", "timeframe": timeframe}
    query = urllib.parse.urlencode({"market": market, "count": count})
    url = f"{BITHUMB_PUBLIC_API}/v1/candles/days?{query}"
    try:
        request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "cai-nonzero-signal-scout/1.0"})
        with urllib.request.urlopen(request, timeout=10) as response:
            rows = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # Public data only; fallback to local archive if the network/API is unavailable.
        return [], {"source": "live_bithumb_public_api", "status": "FETCH_FAILED", "url": url, "error": str(exc)}
    candles = []
    for row in rows if isinstance(rows, list) else []:
        timestamp = row.get("candle_date_time_utc") or row.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        candles.append(
            {
                "timestamp": timestamp,
                "open": float(row.get("opening_price", row.get("open", 0.0)) or 0.0),
                "high": float(row.get("high_price", row.get("high", 0.0)) or 0.0),
                "low": float(row.get("low_price", row.get("low", 0.0)) or 0.0),
                "close": float(row.get("trade_price", row.get("close", 0.0)) or 0.0),
                "volume": float(row.get("candle_acc_trade_volume", row.get("volume", 0.0)) or 0.0),
            }
        )
    candles = sorted(candles, key=lambda row: row["timestamp"])
    latest_timestamp = candles[-1]["timestamp"].isoformat() if candles else None
    return candles, {
        "source": "live_bithumb_public_api",
        "status": "LIVE_FETCH_OK" if candles else "LIVE_FETCH_EMPTY",
        "url": url,
        "row_count": len(candles),
        "latest_timestamp": latest_timestamp,
    }


def _default_candles_package(oos: dict) -> tuple[dict[str, list[dict]], dict[str, dict]]:
    oos = oos or {}
    loaded: dict[str, list[dict]] = {}
    freshness: dict[str, dict] = {}
    for evaluation in oos.get("evaluations", []):
        market = evaluation.get("market", "")
        timeframe = evaluation.get("timeframe", "1d")
        if market and market not in loaded:
            live_candles, live_meta = _load_live_candles(market, timeframe)
            if live_candles:
                loaded[market] = live_candles
                freshness[market] = live_meta
                continue
            archive_candles = _load_candles(market, timeframe)
            loaded[market] = archive_candles
            freshness[market] = {
                "source": "local_bithumb_backfill_archive",
                "status": "FALLBACK_ARCHIVE_USED",
                "live_fetch": live_meta,
                "row_count": len(archive_candles),
                "latest_timestamp": archive_candles[-1]["timestamp"].isoformat() if archive_candles else None,
            }
    return loaded, freshness


def _default_candles_by_market(oos: dict) -> dict[str, list[dict]]:
    candles_by_market, _freshness = _default_candles_package(oos)
    return candles_by_market


def _selection_key(row: dict) -> dict:
    source_conversion = row.get("source_conversion") or {}
    aggregate = row.get("aggregate") or {}
    return {
        "estimated_cagr": source_conversion.get("estimated_cagr"),
        "pass_fold_count": aggregate.get("pass_fold_count"),
        "average_fold_cagr": aggregate.get("average_fold_cagr"),
        "total_trade_count": aggregate.get("total_trade_count"),
    }


def _sortable_selection_key(row: dict) -> tuple[float, int]:
    key = _selection_key(row)
    return (
        float(key.get("estimated_cagr") or 0.0),
        int(key.get("pass_fold_count") or 0),
    )


def _signal_gap(signal: dict) -> dict:
    if not signal or "momentum" not in signal or "volume_ratio" not in signal:
        return {
            "eligible_for_gap_ranking": False,
            "momentum_gap": None,
            "volume_gap": None,
            "nearest_trigger_gap": None,
            "blocking_conditions": [signal.get("reason", "missing_signal_metrics") if isinstance(signal, dict) else "missing_signal_metrics"],
        }
    momentum_gap = float(signal.get("momentum") or 0.0) - float(signal.get("momentum_threshold") or 0.0)
    volume_gap = float(signal.get("volume_ratio") or 0.0) - float(signal.get("volume_ratio_floor") or 0.0)
    blocking_conditions = []
    if momentum_gap < 0:
        blocking_conditions.append("momentum_below_threshold")
    if volume_gap < 0:
        blocking_conditions.append("volume_ratio_below_floor")
    return {
        "eligible_for_gap_ranking": True,
        "momentum_gap": momentum_gap,
        "volume_gap": volume_gap,
        "nearest_trigger_gap": min(momentum_gap, volume_gap),
        "blocking_conditions": blocking_conditions,
    }


def _near_miss_key(row: dict) -> tuple[float, float, float]:
    gap = row.get("signal_gap") or {}
    selection = _selection_key(row)
    return (
        float(gap.get("nearest_trigger_gap") if gap.get("nearest_trigger_gap") is not None else -999.0),
        float(selection.get("estimated_cagr") or 0.0),
        float(selection.get("pass_fold_count") or 0.0),
    )


def _attach_signal_gap_aliases(row: dict) -> dict:
    gap = row.get("signal_gap") or {}
    row["momentum_gap"] = gap.get("momentum_gap")
    row["volume_gap"] = gap.get("volume_gap")
    row["nearest_trigger_gap"] = gap.get("nearest_trigger_gap")
    row["blocking_conditions"] = gap.get("blocking_conditions", [])
    row["blockers"] = row["blocking_conditions"]
    return row


def _blocking_condition_counts(rows: list[dict]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.get("blocking_conditions") or [])
    return dict(counter)


def _numeric_values(rows: list[dict], key: str) -> list[float]:
    values = []
    for row in rows:
        value = row.get(key)
        if value is None:
            continue
        value = float(value)
        if math.isfinite(value):
            values.append(value)
    return values


def _value_summary(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "min": None, "max": None, "average": None, "closest_to_trigger": None}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "average": sum(values) / len(values),
        "closest_to_trigger": max(values),
    }


def _near_miss_gap_summary(rows: list[dict]) -> dict:
    return {
        "candidate_count": len(rows),
        "momentum_gap": _value_summary(_numeric_values(rows, "momentum_gap")),
        "volume_gap": _value_summary(_numeric_values(rows, "volume_gap")),
        "nearest_trigger_gap": _value_summary(_numeric_values(rows, "nearest_trigger_gap")),
        "blocking_condition_counts": _blocking_condition_counts(rows),
    }


def _momentum_signal(candles: list[dict], params: dict) -> dict:
    lookback = int(params.get("lookback_bars", 0) or 0)
    volume_window = int(params.get("volume_window", lookback) or lookback or 1)
    threshold = float(params.get("momentum_threshold", 0.0) or 0.0)
    volume_floor = float(params.get("volume_ratio_floor", 0.0) or 0.0)
    if len(candles) <= max(lookback, volume_window) or lookback <= 0:
        return {"triggered": False, "reason": "insufficient_candles"}
    closes = [float(row["close"]) for row in candles]
    volumes = [float(row.get("volume", 0.0) or 0.0) for row in candles]
    base = closes[-lookback - 1]
    latest = closes[-1]
    if not math.isfinite(base) or base <= 0:
        return {"triggered": False, "reason": "invalid_base_close"}
    momentum = latest / base - 1.0
    prior_volumes = volumes[-volume_window - 1:-1]
    avg_volume = sum(prior_volumes) / len(prior_volumes) if prior_volumes else 0.0
    latest_volume = volumes[-1]
    volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 0.0
    triggered = momentum >= threshold and volume_ratio >= volume_floor
    return {
        "triggered": triggered,
        "momentum": momentum,
        "momentum_threshold": threshold,
        "volume_ratio": volume_ratio,
        "volume_ratio_floor": volume_floor,
        "latest_close": latest,
        "base_close": base,
    }


def build_report(oos: dict | None = None, candles_by_market: dict[str, list[dict]] | None = None, generated_at: str | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    generated_at_utc = datetime.fromisoformat(generated_at).astimezone(ZoneInfo("UTC")).isoformat()
    oos = (oos if oos is not None else _read_json(OOS_JSON, {})) or {}
    if candles_by_market is None:
        candles_by_market, data_source_by_market = _default_candles_package(oos)
    else:
        data_source_by_market = {
            market: {
                "source": "injected_test_or_caller_candles",
                "status": "CALLER_SUPPLIED",
                "row_count": len(candles),
                "latest_timestamp": candles[-1]["timestamp"].isoformat() if candles else None,
            }
            for market, candles in candles_by_market.items()
        }
    triggered = []
    evaluated = []
    blockers = []
    for evaluation in oos.get("evaluations", []):
        market = evaluation.get("market", "")
        candles = candles_by_market.get(market, [])
        signal = _momentum_signal(candles, evaluation.get("parameters", {}))
        row = {
            "candidate_id": evaluation.get("candidate_id"),
            "market": market,
            "timeframe": evaluation.get("timeframe", "1d"),
            "signal": signal,
            "signal_gap": _signal_gap(signal),
            "source_conversion": evaluation.get("source_conversion", {}),
            "aggregate": evaluation.get("aggregate", {}),
        }
        _attach_signal_gap_aliases(row)
        evaluated.append(row)
        if signal.get("triggered"):
            triggered.append(row)
    if not evaluated:
        blockers.append("NO_BITHUMB_OOS_EVALUATIONS_AVAILABLE")
    verified_source_statuses = {"LIVE_FETCH_OK", "CALLER_SUPPLIED"}
    if any(meta.get("status") not in verified_source_statuses for meta in data_source_by_market.values()):
        blockers.append("CURRENT_BITHUMB_MARKET_DATA_NOT_LIVE_VERIFIED")
    if not triggered:
        blockers.append("NO_CURRENT_NONZERO_BITHUMB_SIGNAL_CANDIDATE_FOUND")
    triggered.sort(key=_sortable_selection_key, reverse=True)
    for index, row in enumerate(triggered, start=1):
        row["selection_rank"] = index
        row["selection_key"] = _selection_key(row)
    triggered_rank_by_candidate = {row.get("candidate_id"): row.get("selection_rank") for row in triggered}
    evaluated_ranked_by_selection_key = sorted(evaluated, key=_sortable_selection_key, reverse=True)
    for index, row in enumerate(evaluated_ranked_by_selection_key, start=1):
        row["selection_rank_among_evaluated"] = index
        row["selection_key"] = _selection_key(row)
    near_miss_candidates = [row for row in evaluated if not row.get("signal", {}).get("triggered") and row.get("signal_gap", {}).get("eligible_for_gap_ranking")]
    near_miss_candidates.sort(key=_near_miss_key, reverse=True)
    for index, row in enumerate(near_miss_candidates, start=1):
        row["near_miss_rank"] = index
    status = "NONZERO_SIGNAL_CANDIDATE_READY_FOR_REVIEW" if triggered else "NO_CURRENT_NONZERO_SIGNAL_FOUND"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "generated_at_utc": generated_at_utc,
        "status": status,
        "selection_policy": SELECTION_POLICY,
        "evaluated_candidate_count": len(evaluated),
        "evaluated_count": len(evaluated),
        "triggered_candidate_count": len(triggered),
        "triggered_count": len(triggered),
        "current_data_live_verified": bool(data_source_by_market) and all(
            meta.get("status") == "LIVE_FETCH_OK" for meta in data_source_by_market.values()
        ),
        "data_source_by_market": data_source_by_market,
        "top_triggered_candidate": triggered[0] if triggered else None,
        "top_triggered_selection": {
            "candidate_id": triggered[0].get("candidate_id") if triggered else None,
            "selection_rank": triggered[0].get("selection_rank") if triggered else None,
            "selection_key": triggered[0].get("selection_key") if triggered else None,
        },
        "top_near_miss_candidate": near_miss_candidates[0] if near_miss_candidates else None,
        "top_near_miss": near_miss_candidates[0] if near_miss_candidates else None,
        "top_near_miss_candidates": near_miss_candidates[:TOP_NEAR_MISS_LIMIT],
        "top_near_miss_limit": TOP_NEAR_MISS_LIMIT,
        "near_miss_count": len(near_miss_candidates),
        "near_miss_blocking_condition_counts": _blocking_condition_counts(near_miss_candidates),
        "near_miss_gap_summary": _near_miss_gap_summary(near_miss_candidates),
        "triggered_rank_by_candidate": triggered_rank_by_candidate,
        "triggered_candidates": triggered,
        "evaluated_candidates": evaluated,
        "blockers": blockers,
        "single_next_action": "Review the top natural nonzero Bithumb signal candidate for shadow registration." if triggered else "Wait for a natural nonzero Bithumb signal or improve current-actionable OOS candidates.",
        "non_goals": [
            "does_not_emit_order_signal",
            "does_not_write_order_intent",
            "does_not_enable_paper_live_broker_submit",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    top = report.get("top_triggered_candidate") or {}
    return "\n".join(
        [
            "# Bithumb Current-Actionable Nonzero Signal Scout",
            "",
            f"- Status: `{report['status']}`",
            f"- Evaluated candidates: `{report['evaluated_candidate_count']}`",
            f"- Triggered candidates: `{report['triggered_candidate_count']}`",
            f"- Top candidate: `{top.get('candidate_id', 'none')}`",
            f"- Near-miss candidates: `{report.get('near_miss_count', 0)}`",
            f"- Near-miss blockers: `{report.get('near_miss_blocking_condition_counts', {})}`",
            f"- Near-miss momentum gap: `{(report.get('near_miss_gap_summary') or {}).get('momentum_gap', {})}`",
            f"- Single next action: {report['single_next_action']}",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "triggered_candidate_count": report["triggered_candidate_count"], "latest_json": str(REPORT_JSON), "safety": SAFETY}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
