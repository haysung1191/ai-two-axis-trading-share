from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parent
REPORT_JSON = ROOT / "reports" / "model_factory" / "two_axis_direct_model_development_latest.json"
REPORT_MD = ROOT / "reports" / "model_factory" / "two_axis_direct_model_development_latest.md"
BITHUMB_PUBLIC_API = "https://api.bithumb.com"


NO_ORDER_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default


def latest_bithumb_raw_dir() -> Path | None:
    verified = read_json(ROOT / "reports" / "operations" / "bithumb_verified_crypto_model_factory_latest.json", {})
    raw_dir = verified.get("data", {}).get("raw_dir")
    if raw_dir and Path(raw_dir).exists():
        return Path(raw_dir)
    base = ROOT / "Crypto" / "data" / "bithumb_stage2_archive" / "backfill_full"
    dirs = sorted([p for p in base.glob("*") if p.is_dir()], reverse=True)
    return dirs[0] if dirs else None


def load_candles(path: Path) -> list[dict[str, float]]:
    rows = read_json(path, [])
    candles: list[dict[str, float]] = []
    for row in rows:
        close = row.get("trade_price", row.get("close"))
        volume = row.get("candle_acc_trade_volume", row.get("volume"))
        traded_value = row.get("candle_acc_trade_price", 0.0)
        if close is None or volume is None:
            continue
        candles.append(
            {
                "close": float(close),
                "volume": float(volume),
                "traded_value": float(traded_value or 0.0),
            }
        )
    return candles


def fetch_bithumb_live_candles(market: str, count: int = 200) -> tuple[list[dict[str, float]], dict[str, Any]]:
    query = urllib.parse.urlencode({"market": market, "count": count})
    url = f"{BITHUMB_PUBLIC_API}/v1/candles/days?{query}"
    try:
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "cai-direct-model-development/1.0"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            rows = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return [], {"source": "bithumb_public_api", "status": "FETCH_FAILED", "url": url, "error": str(exc)}
    candles: list[dict[str, float]] = []
    latest_timestamp = rows[0].get("candle_date_time_utc") or rows[0].get("timestamp") if isinstance(rows, list) and rows else None
    for row in rows if isinstance(rows, list) else []:
        close = row.get("trade_price", row.get("close"))
        volume = row.get("candle_acc_trade_volume", row.get("volume"))
        traded_value = row.get("candle_acc_trade_price", row.get("traded_value", 0.0))
        if close is None or volume is None:
            continue
        candles.append(
            {
                "close": float(close),
                "volume": float(volume),
                "traded_value": float(traded_value or 0.0),
            }
        )
    candles.reverse()
    return candles, {
        "source": "bithumb_public_api",
        "status": "LIVE_FETCH_OK" if candles else "LIVE_FETCH_EMPTY",
        "url": url,
        "row_count": len(candles),
        "latest_timestamp": latest_timestamp,
    }


def max_drawdown(equity: list[float]) -> float:
    peak = equity[0] if equity else 1.0
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak:
            worst = min(worst, value / peak - 1.0)
    return worst


def backtest_momentum(candles: list[dict[str, float]], params: dict[str, Any]) -> dict[str, Any]:
    lookback = int(params["lookback_bars"])
    hold_bars = int(params["hold_bars"])
    volume_window = int(params["volume_window"])
    volume_floor = float(params["volume_ratio_floor"])
    momentum_threshold = float(params["momentum_threshold"])
    stop_loss = float(params["stop_loss"])
    take_profit = float(params["take_profit"])
    cost = float(params["round_trip_cost_rate"])

    equity = [1.0]
    trades: list[float] = []
    holds: list[int] = []
    index = max(lookback, volume_window)
    while index < len(candles) - 1:
        prev = candles[index - lookback]["close"]
        current = candles[index]["close"]
        if prev <= 0 or current <= 0:
            equity.append(equity[-1])
            index += 1
            continue
        momentum = current / prev - 1.0
        volume_base = mean([r["volume"] for r in candles[index - volume_window : index]]) or 1.0
        volume_ratio = candles[index]["volume"] / volume_base
        if momentum < momentum_threshold or volume_ratio < volume_floor:
            equity.append(equity[-1])
            index += 1
            continue

        entry = current
        exit_index = min(index + hold_bars, len(candles) - 1)
        for probe in range(index + 1, exit_index + 1):
            ret = candles[probe]["close"] / entry - 1.0
            if ret <= -stop_loss or ret >= take_profit:
                exit_index = probe
                break
        raw_return = candles[exit_index]["close"] / entry - 1.0
        trade_return = raw_return - cost
        trades.append(trade_return)
        holds.append(exit_index - index)
        equity.extend([equity[-1]] * max(0, exit_index - index - 1))
        equity.append(equity[-1] * (1.0 + trade_return))
        index = exit_index + 1

    while len(equity) < len(candles):
        equity.append(equity[-1])

    total_return = equity[-1] - 1.0
    years = max(len(candles) / 365.0, 1 / 365.0)
    cagr = equity[-1] ** (1.0 / years) - 1.0 if equity[-1] > 0 else -1.0
    wins = [r for r in trades if r > 0]
    losses = [r for r in trades if r < 0]
    profit_factor = (sum(wins) / abs(sum(losses))) if losses else (999.0 if wins else 0.0)
    return {
        "total_return": total_return,
        "cagr": cagr,
        "mdd": max_drawdown(equity),
        "trade_count": len(trades),
        "win_rate": len(wins) / len(trades) if trades else 0.0,
        "profit_factor": profit_factor,
        "average_holding_bars": mean(holds) if holds else 0.0,
    }


def current_momentum_signal(candles: list[dict[str, float]], params: dict[str, Any]) -> dict[str, Any]:
    lookback = int(params["lookback_bars"])
    volume_window = int(params["volume_window"])
    volume_floor = float(params["volume_ratio_floor"])
    momentum_threshold = float(params["momentum_threshold"])
    required = max(lookback, volume_window) + 1
    if len(candles) < required:
        return {
            "triggered": False,
            "reason": "insufficient_candles",
            "required_candle_count": required,
            "available_candle_count": len(candles),
        }
    base = float(candles[-lookback - 1]["close"])
    latest = float(candles[-1]["close"])
    if base <= 0 or latest <= 0:
        return {"triggered": False, "reason": "invalid_close"}
    prior_volumes = [float(row["volume"]) for row in candles[-volume_window - 1 : -1]]
    average_volume = mean(prior_volumes) if prior_volumes else 0.0
    latest_volume = float(candles[-1]["volume"])
    volume_ratio = latest_volume / average_volume if average_volume > 0 else 0.0
    momentum = latest / base - 1.0
    return {
        "triggered": bool(momentum >= momentum_threshold and volume_ratio >= volume_floor),
        "momentum": momentum,
        "momentum_threshold": momentum_threshold,
        "volume_ratio": volume_ratio,
        "volume_ratio_floor": volume_floor,
        "latest_close": latest,
        "base_close": base,
    }


def current_signal_gap(signal: dict[str, Any]) -> dict[str, Any]:
    if "momentum" not in signal or "volume_ratio" not in signal:
        return {
            "eligible_for_gap_ranking": False,
            "nearest_trigger_gap": None,
            "blocking_conditions": [signal.get("reason", "missing_signal_metrics")],
        }
    momentum_gap = float(signal["momentum"]) - float(signal["momentum_threshold"])
    volume_gap = float(signal["volume_ratio"]) - float(signal["volume_ratio_floor"])
    blockers: list[str] = []
    if momentum_gap < 0:
        blockers.append("momentum_below_threshold")
    if volume_gap < 0:
        blockers.append("volume_ratio_below_floor")
    return {
        "eligible_for_gap_ranking": True,
        "momentum_gap": momentum_gap,
        "volume_gap": volume_gap,
        "nearest_trigger_gap": min(momentum_gap, volume_gap),
        "blocking_conditions": blockers,
    }


def crypto_params() -> list[dict[str, Any]]:
    params: list[dict[str, Any]] = []
    for lookback in (3, 5, 7, 14):
        for hold in (3, 5, 7, 10):
            for volume_window in (10, 20):
                for volume_floor in (0.8, 1.0, 1.3):
                    for threshold in (0.015, 0.03, 0.06):
                        params.append(
                            {
                                "lookback_bars": lookback,
                                "hold_bars": hold,
                                "volume_window": volume_window,
                                "volume_ratio_floor": volume_floor,
                                "momentum_threshold": threshold,
                                "stop_loss": 0.08,
                                "take_profit": 0.35,
                                "round_trip_cost_rate": 0.002,
                            }
                        )
    return params


def candidate_id(prefix: str, payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return f"{prefix}_{hashlib.sha1(raw).hexdigest()[:10]}"


def pass_screen(metrics: dict[str, Any]) -> bool:
    return (
        metrics["cagr"] >= 0.20
        and metrics["mdd"] >= -0.35
        and metrics["trade_count"] >= 6
        and metrics["profit_factor"] >= 1.3
    )


def with_cost(params: dict[str, Any], cost: float) -> dict[str, Any]:
    stressed = dict(params)
    stressed["round_trip_cost_rate"] = cost
    return stressed


def holdout_validation(candles: list[dict[str, float]], params: dict[str, Any]) -> dict[str, Any]:
    split = max(int(len(candles) * 0.70), 1)
    train = candles[:split]
    holdout = candles[split:]
    train_metrics = backtest_momentum(train, params) if len(train) >= 90 else {}
    holdout_metrics = backtest_momentum(holdout, params) if len(holdout) >= 90 else {}
    high_cost_metrics = backtest_momentum(holdout, with_cost(params, 0.006)) if len(holdout) >= 90 else {}
    holdout_pass = bool(holdout_metrics) and pass_screen(holdout_metrics)
    high_cost_pass = bool(high_cost_metrics) and (
        high_cost_metrics["total_return"] > 0
        and high_cost_metrics["mdd"] >= -0.35
        and high_cost_metrics["profit_factor"] >= 1.1
        and high_cost_metrics["trade_count"] >= 3
    )
    return {
        "train": train_metrics,
        "holdout": holdout_metrics,
        "high_cost_holdout": high_cost_metrics,
        "holdout_pass": holdout_pass,
        "high_cost_pass": high_cost_pass,
        "passed": holdout_pass and high_cost_pass,
    }


def walkforward(candles: list[dict[str, float]], params: dict[str, Any]) -> dict[str, Any]:
    fold_size = len(candles) // 3
    folds = []
    for fold in range(3):
        start = fold * fold_size
        end = len(candles) if fold == 2 else (fold + 1) * fold_size
        part = candles[start:end]
        metrics = backtest_momentum(part, params) if len(part) >= 90 else {
            "total_return": 0.0,
            "cagr": -1.0,
            "mdd": 0.0,
            "trade_count": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "average_holding_bars": 0.0,
        }
        folds.append(metrics)
    positive = sum(1 for row in folds if row["total_return"] > 0)
    pass_folds = sum(1 for row in folds if pass_screen(row))
    return {
        "folds": folds,
        "positive_fold_count": positive,
        "pass_fold_count": pass_folds,
        "average_fold_cagr": mean([row["cagr"] for row in folds]),
        "worst_fold_mdd": min(row["mdd"] for row in folds),
        "total_trade_count": sum(row["trade_count"] for row in folds),
        "passed": positive >= 2 and pass_folds >= 2 and min(row["mdd"] for row in folds) >= -0.35,
    }


def crypto_candidate_rank(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["status"] == "DIRECT_VALIDATED_PASS",
        row["walkforward"]["average_fold_cagr"],
        (row["holdout_validation"].get("holdout") or {}).get("cagr", -1.0),
        row["metrics"]["cagr"],
        row["metrics"]["profit_factor"],
    )


def diverse_top_crypto_candidates(candidates: list[dict[str, Any]], limit: int = 25) -> list[dict[str, Any]]:
    ranked = sorted(candidates, key=crypto_candidate_rank, reverse=True)
    best_by_market: dict[str, dict[str, Any]] = {}
    for row in ranked:
        if row["status"] != "DIRECT_VALIDATED_PASS":
            continue
        market = str(row.get("market") or "")
        if market and market not in best_by_market:
            best_by_market[market] = row

    selected = sorted(best_by_market.values(), key=crypto_candidate_rank, reverse=True)
    selected_ids = {row["candidate_id"] for row in selected}
    for row in ranked:
        if len(selected) >= limit:
            break
        if row["candidate_id"] in selected_ids:
            continue
        selected.append(row)
        selected_ids.add(row["candidate_id"])
    return selected[:limit]


def attach_live_current_signals(top_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    live_by_market: dict[str, tuple[list[dict[str, float]], dict[str, Any]]] = {}
    for market in sorted({str(row.get("market") or "") for row in top_candidates if row.get("market")}):
        live_by_market[market] = fetch_bithumb_live_candles(market)
    for row in top_candidates:
        candles, meta = live_by_market.get(str(row.get("market") or ""), ([], {"status": "MARKET_NOT_REQUESTED"}))
        signal = current_momentum_signal(candles, row["parameters"]) if candles else {"triggered": False, "reason": meta.get("status", "live_data_missing")}
        row["live_current_signal_data"] = meta
        row["live_current_signal"] = signal
        row["live_current_signal_gap"] = current_signal_gap(signal)
    near_miss_candidates = [
        row
        for row in top_candidates
        if not row.get("live_current_signal", {}).get("triggered")
        and (row.get("live_current_signal_gap") or {}).get("eligible_for_gap_ranking")
    ]
    near_miss_candidates.sort(
        key=lambda row: (
            float((row.get("live_current_signal_gap") or {}).get("nearest_trigger_gap") or -999.0),
            float((row.get("holdout_validation") or {}).get("holdout", {}).get("cagr") or -999.0),
            float((row.get("metrics") or {}).get("cagr") or -999.0),
        ),
        reverse=True,
    )
    for index, row in enumerate(near_miss_candidates, start=1):
        row["live_near_miss_rank"] = index
    top_near_miss = near_miss_candidates[0] if near_miss_candidates else None
    return {
        "market_count": len(live_by_market),
        "all_live_verified": bool(live_by_market) and all(meta.get("status") == "LIVE_FETCH_OK" for _candles, meta in live_by_market.values()),
        "data_source_by_market": {market: meta for market, (_candles, meta) in live_by_market.items()},
        "triggered_count": sum(1 for row in top_candidates if row.get("live_current_signal", {}).get("triggered")),
        "top_live_near_miss_candidate": {
            "candidate_id": top_near_miss.get("candidate_id"),
            "market": top_near_miss.get("market"),
            "live_near_miss_rank": top_near_miss.get("live_near_miss_rank"),
            "momentum": (top_near_miss.get("live_current_signal") or {}).get("momentum"),
            "momentum_threshold": (top_near_miss.get("live_current_signal") or {}).get("momentum_threshold"),
            "volume_ratio": (top_near_miss.get("live_current_signal") or {}).get("volume_ratio"),
            "volume_ratio_floor": (top_near_miss.get("live_current_signal") or {}).get("volume_ratio_floor"),
            "momentum_gap": (top_near_miss.get("live_current_signal_gap") or {}).get("momentum_gap"),
            "volume_gap": (top_near_miss.get("live_current_signal_gap") or {}).get("volume_gap"),
            "nearest_trigger_gap": (top_near_miss.get("live_current_signal_gap") or {}).get("nearest_trigger_gap"),
            "blocking_conditions": (top_near_miss.get("live_current_signal_gap") or {}).get("blocking_conditions", []),
            "data_status": (top_near_miss.get("live_current_signal_data") or {}).get("status"),
            "latest_timestamp": (top_near_miss.get("live_current_signal_data") or {}).get("latest_timestamp"),
        }
        if top_near_miss
        else None,
    }


def build_crypto_development(max_markets: int, max_evaluations: int) -> dict[str, Any]:
    raw_dir = latest_bithumb_raw_dir()
    if raw_dir is None:
        return {"status": "CRYPTO_INPUT_MISSING", "candidates": [], "errors": ["no_bithumb_raw_dir"]}
    candle_dir = raw_dir / "candles" / "1d"
    files = sorted(candle_dir.glob("KRW-*.json"))
    market_rows = []
    for path in files:
        candles = load_candles(path)
        if len(candles) < 250:
            continue
        recent_value = mean([row["traded_value"] for row in candles[-20:] if row["traded_value"] >= 0] or [0.0])
        market_rows.append((recent_value, path.stem, candles))
    market_rows.sort(reverse=True, key=lambda row: row[0])
    params = crypto_params()
    candidates: list[dict[str, Any]] = []
    evaluated = 0
    for _, market, candles in market_rows[:max_markets]:
        for param in params:
            if evaluated >= max_evaluations:
                break
            evaluated += 1
            metrics = backtest_momentum(candles, param)
            if not pass_screen(metrics):
                continue
            wf = walkforward(candles, param)
            holdout = holdout_validation(candles, param)
            validated = bool(wf["passed"] and holdout["passed"])
            current_signal = current_momentum_signal(candles, param)
            row = {
                "candidate_id": candidate_id(f"bithumb_direct_{market.lower().replace('-', '_')}", {"market": market, **param}),
                "market": market,
                "timeframe": "1d",
                "strategy_family": "direct_volume_momentum",
                "parameters": param,
                "metrics": metrics,
                "walkforward": wf,
                "holdout_validation": holdout,
                "current_signal": current_signal,
                "current_signal_gap": current_signal_gap(current_signal),
                "status": "DIRECT_VALIDATED_PASS" if validated else ("DIRECT_OOS_PASS_HOLDOUT_ITERATE" if wf["passed"] else "DIRECT_SCREEN_PASS_OOS_ITERATE"),
                "order_paths_allowed": False,
                "counts_as_live_evidence": False,
            }
            candidates.append(row)
        if evaluated >= max_evaluations:
            break
    candidates.sort(key=crypto_candidate_rank, reverse=True)
    validated_markets = sorted({row["market"] for row in candidates if row["status"] == "DIRECT_VALIDATED_PASS"})
    top_candidates = diverse_top_crypto_candidates(candidates, limit=25)
    live_signal_summary = attach_live_current_signals(top_candidates)
    return {
        "status": "CRYPTO_DIRECT_DEVELOPMENT_OK",
        "raw_dir": str(raw_dir),
        "market_count": len(market_rows[:max_markets]),
        "candidate_market_count": len({row["market"] for row in candidates}),
        "validated_market_count": len(validated_markets),
        "validated_markets": validated_markets,
        "evaluated_count": evaluated,
        "candidate_count": len(candidates),
        "oos_pass_count": sum(1 for row in candidates if row["status"] in {"DIRECT_VALIDATED_PASS", "DIRECT_OOS_PASS_HOLDOUT_ITERATE"}),
        "validated_pass_count": sum(1 for row in candidates if row["status"] == "DIRECT_VALIDATED_PASS"),
        "archive_signal_triggered_count": sum(1 for row in candidates if row.get("current_signal", {}).get("triggered")),
        "top_live_signal_summary": live_signal_summary,
        "top_live_signal_triggered_count": live_signal_summary["triggered_count"],
        "top_live_near_miss_candidate": live_signal_summary.get("top_live_near_miss_candidate"),
        "top_candidates": top_candidates,
    }


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def kis_universe_validation_is_operational(mode: object) -> bool:
    normalized = str(mode or "").strip().lower()
    return normalized == "daily_close_presence"


def build_kis_development() -> dict[str, Any]:
    queue = read_json(ROOT / "reports" / "model_factory" / "stock_risk_conversion_queue_latest.json", {})
    bridge = read_json(ROOT / "ops" / "stock_etf_operating_candidate_bridge" / "stock_etf_operating_candidate_bridge_latest.json", {})
    target_book = read_csv_rows(ROOT / "ops" / "stock_etf_operating_candidate_bridge" / "stock_etf_operating_target_book_latest.csv")
    universe_validation_mode = bridge.get("universe_validation_mode")
    universe_validation_operational = kis_universe_validation_is_operational(universe_validation_mode)
    variants: list[dict[str, Any]] = []
    for row in queue.get("queue", []):
        before = row.get("before", {})
        base_mdd = abs(float(before.get("mdd", 0.0) or 0.0))
        base_cagr = float(before.get("cagr", 0.0) or 0.0)
        base_sharpe = float(before.get("sharpe", 0.0) or 0.0)
        if base_mdd <= 0:
            continue
        for cap in (0.56, 0.59, 0.62, 0.64, 0.66):
            estimated_mdd = -base_mdd * cap
            estimated_cagr = base_cagr * cap
            gate = estimated_mdd >= -0.20 and estimated_cagr >= 0.35
            variant = {
                "candidate_id": candidate_id("kis_direct_exposure", {"id": row.get("candidate_id"), "cap": cap}),
                "parent_candidate_id": row.get("candidate_id"),
                "strategy_family": "direct_fixed_exposure_conversion",
                "fixed_exposure_cap": cap,
                "estimated_cagr": estimated_cagr,
                "estimated_mdd": estimated_mdd,
                "source_sharpe": base_sharpe,
                "score": estimated_cagr + min(0.0, estimated_mdd + 0.20) * 2.0 + base_sharpe * 0.05,
                "status": "DIRECT_CONVERSION_PASS" if gate else "DIRECT_CONVERSION_ITERATE",
                "order_paths_allowed": False,
                "counts_as_live_evidence": False,
            }
            variants.append(variant)
    symbols = [
        {
            "symbol": row.get("Symbol"),
            "name": row.get("Name"),
            "asset_type": row.get("AssetType"),
            "target_weight": float(row.get("TargetWeight") or 0.0),
            "momentum_rank": int(float(row.get("MomentumRank") or 999)),
            "momentum_score": float(row.get("MomentumScore") or 0.0),
        }
        for row in target_book
    ]
    variants.sort(key=lambda row: (row["status"] == "DIRECT_CONVERSION_PASS", row["score"]), reverse=True)
    return {
        "status": "KIS_DIRECT_DEVELOPMENT_OK" if variants else "KIS_DIRECT_DEVELOPMENT_INPUT_MISSING",
        "source_queue_count": len(queue.get("queue", [])),
        "source_bridge": {
            "generated_at_utc": bridge.get("generated_at_utc"),
            "status": bridge.get("status"),
            "candidate_id": bridge.get("candidate_id"),
            "universe_validation_mode": bridge.get("universe_validation_mode"),
            "universe_validation_verifier_status": bridge.get("universe_validation_verifier_status"),
        },
        "universe_validation_mode": universe_validation_mode,
        "universe_validation_source": bridge.get("universe_validation_source"),
        "universe_validation_verifier_status": bridge.get("universe_validation_verifier_status"),
        "universe_validation_operation_ready": bool(bridge.get("universe_validation_operation_ready")),
        "universe_validation_all_verified": bool(bridge.get("universe_validation_all_verified")),
        "universe_validation_blockers": bridge.get("universe_validation_blockers", []),
        "universe_validation_generated_at": bridge.get("universe_validation_generated_at"),
        "universe_validation_operational": universe_validation_operational,
        "counts_as_live_evidence": universe_validation_operational,
        "target_symbol_count": len(symbols),
        "conversion_variant_count": len(variants),
        "pass_count": sum(1 for row in variants if row["status"] == "DIRECT_CONVERSION_PASS"),
        "top_variants": variants[:20],
        "current_target_symbols": symbols,
    }


def build_report(max_markets: int = 10, max_evaluations: int = 1500) -> dict[str, Any]:
    crypto = build_crypto_development(max_markets=max_markets, max_evaluations=max_evaluations)
    kis = build_kis_development()
    return {
        "schema_version": 1,
        "generated_at_utc": utc_now(),
        "report": "two_axis_direct_model_development",
        "status": "TWO_AXIS_DIRECT_DEVELOPMENT_OK"
        if crypto["status"].endswith("_OK") and kis["status"].endswith("_OK")
        else "TWO_AXIS_DIRECT_DEVELOPMENT_ATTENTION",
        "crypto": crypto,
        "kis": kis,
        "no_order_assertions": NO_ORDER_ASSERTIONS,
    }


def render_md(report: dict[str, Any]) -> str:
    crypto = report["crypto"]
    kis = report["kis"]
    top_crypto = crypto.get("top_candidates", [])[:5]
    top_kis = kis.get("top_variants", [])[:5]
    lines = [
        "# Two Axis Direct Model Development",
        "",
        f"- Status: `{report['status']}`",
        f"- Crypto evaluated: `{crypto.get('evaluated_count', 0)}`; candidates: `{crypto.get('candidate_count', 0)}`; OOS pass: `{crypto.get('oos_pass_count', 0)}`; validated pass: `{crypto.get('validated_pass_count', 0)}`; validated markets: `{crypto.get('validated_market_count', 0)}`.",
        f"- Crypto archive triggered candidates: `{crypto.get('archive_signal_triggered_count', 0)}`; top live triggered candidates: `{crypto.get('top_live_signal_triggered_count', 0)}`; top live verified: `{(crypto.get('top_live_signal_summary') or {}).get('all_live_verified')}`.",
        f"- Crypto top live near miss: `{(crypto.get('top_live_near_miss_candidate') or {}).get('candidate_id') or '-'}` `{(crypto.get('top_live_near_miss_candidate') or {}).get('market') or '-'}` gap `{(crypto.get('top_live_near_miss_candidate') or {}).get('nearest_trigger_gap')}` blockers `{', '.join((crypto.get('top_live_near_miss_candidate') or {}).get('blocking_conditions') or []) or '-'}`.",
        f"- KIS variants: `{kis.get('conversion_variant_count', 0)}`; pass: `{kis.get('pass_count', 0)}`.",
        f"- KIS universe validation: `{kis.get('universe_validation_mode') or '-'}`; operational: `{kis.get('universe_validation_operational')}`; live evidence: `{kis.get('counts_as_live_evidence')}`.",
        f"- KIS universe verifier: `{kis.get('universe_validation_verifier_status') or '-'}`; operation ready: `{kis.get('universe_validation_operation_ready')}`; all verified: `{kis.get('universe_validation_all_verified')}`.",
        f"- KIS source bridge: `{(kis.get('source_bridge') or {}).get('status') or '-'}`; generated: `{(kis.get('source_bridge') or {}).get('generated_at_utc') or '-'}`; candidate: `{(kis.get('source_bridge') or {}).get('candidate_id') or '-'}`.",
        "",
        "## Crypto Top",
    ]
    for row in top_crypto:
        metrics = row["metrics"]
        wf = row["walkforward"]
        signal = row.get("current_signal", {})
        gap = row.get("current_signal_gap", {})
        live_signal = row.get("live_current_signal", {})
        live_gap = row.get("live_current_signal_gap", {})
        lines.append(
            f"- `{row['candidate_id']}` {row['market']} {row['status']} "
            f"CAGR={metrics['cagr']:.3f} MDD={metrics['mdd']:.3f} PF={metrics['profit_factor']:.2f} "
            f"WF={wf['positive_fold_count']}/3 HV={row.get('holdout_validation', {}).get('passed')} "
            f"ARCHIVE_SIG={signal.get('triggered')} ARCHIVE_GAP={gap.get('nearest_trigger_gap')} "
            f"LIVE_SIG={live_signal.get('triggered')} LIVE_GAP={live_gap.get('nearest_trigger_gap')}"
        )
    lines.append("")
    lines.append("## KIS Top")
    for row in top_kis:
        lines.append(
            f"- `{row['candidate_id']}` {row['status']} cap={row['fixed_exposure_cap']:.2f} "
            f"est_CAGR={row['estimated_cagr']:.3f} est_MDD={row['estimated_mdd']:.3f}"
        )
    return "\n".join(lines) + "\n"


def write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    write_text_atomic(path, json.dumps(payload, indent=2, ensure_ascii=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-markets", type=int, default=10)
    parser.add_argument("--max-evaluations", type=int, default=1500)
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()
    report = build_report(max_markets=max(1, args.max_markets), max_evaluations=max(1, args.max_evaluations))
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(REPORT_JSON, report)
    write_text_atomic(REPORT_MD, render_md(report))
    summary = {
        "status": report["status"],
        "crypto_candidates": report["crypto"].get("candidate_count", 0),
        "crypto_oos_pass": report["crypto"].get("oos_pass_count", 0),
        "crypto_validated_pass": report["crypto"].get("validated_pass_count", 0),
        "crypto_archive_signal_triggered": report["crypto"].get("archive_signal_triggered_count", 0),
        "crypto_top_live_signal_triggered": report["crypto"].get("top_live_signal_triggered_count", 0),
        "kis_variants": report["kis"].get("conversion_variant_count", 0),
        "kis_pass": report["kis"].get("pass_count", 0),
        "latest_json": str(REPORT_JSON),
    }
    if args.format == "json":
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(
            f"status={summary['status']} crypto_candidates={summary['crypto_candidates']} "
            f"crypto_oos_pass={summary['crypto_oos_pass']} kis_variants={summary['kis_variants']} kis_pass={summary['kis_pass']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
