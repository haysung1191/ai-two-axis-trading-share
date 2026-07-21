from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_oos_walkforward_latest.json"
REPORT_MD = ROOT / "reports/model_factory/bithumb_current_actionable_oos_walkforward_latest.md"
SOURCE_SWEEP = ROOT / "reports/model_factory/bithumb_current_actionable_parameter_sweep_latest.json"
BITHUMB_BACKFILL_ROOT = ROOT / "Crypto/data/bithumb_stage2_archive/backfill_full"

NO_ORDER_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}


def read_json(path: Path, default: dict | None = None) -> dict:
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


def fetch_candles(market: str, timeframe: str) -> list[dict]:
    latest = _latest_backfill_dir()
    if latest is None:
        return []
    path = latest / "candles" / timeframe / f"{market}.json"
    rows = read_json(path, [])
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


backtest = SimpleNamespace(fetch_candles=fetch_candles)


def split_validation_windows(candles: list[dict], folds: int = 3) -> list[list[dict]]:
    if folds <= 0:
        return []
    fold_size = len(candles) // folds
    windows = []
    for index in range(folds):
        start = index * fold_size
        end = (index + 1) * fold_size if index < folds - 1 else len(candles)
        windows.append(candles[start:end])
    return windows


def _trade_metrics(candles: list[dict], params: dict) -> dict:
    lookback = int(params.get("lookback_bars", 3) or 3)
    hold = int(params.get("hold_bars", 3) or 3)
    threshold = float(params.get("momentum_threshold", 0.02) or 0.02)
    volume_window = int(params.get("volume_window", lookback) or lookback)
    volume_floor = float(params.get("volume_ratio_floor", 0.0) or 0.0)
    cost = float(params.get("round_trip_cost_rate", 0.002) or 0.002)
    stop_loss = abs(float(params.get("stop_loss", 0.12) or 0.12))
    take_profit = abs(float(params.get("take_profit", 0.35) or 0.35))
    returns = []
    index = max(lookback, volume_window)
    while index + 1 < len(candles):
        base = float(candles[index - lookback]["close"])
        close = float(candles[index]["close"])
        if base <= 0:
            index += 1
            continue
        prior_volumes = [float(row.get("volume", 0.0) or 0.0) for row in candles[index - volume_window:index]]
        avg_volume = sum(prior_volumes) / len(prior_volumes) if prior_volumes else 0.0
        volume_ratio = float(candles[index].get("volume", 0.0) or 0.0) / avg_volume if avg_volume > 0 else 0.0
        if close / base - 1 >= threshold and volume_ratio >= volume_floor:
            exit_index = min(index + hold, len(candles) - 1)
            exit_price = float(candles[exit_index]["close"])
            gross = exit_price / close - 1
            clipped = min(max(gross, -stop_loss), take_profit)
            returns.append(clipped - cost)
            index = exit_index + 1
        else:
            index += 1
    total_return = math.prod(1 + ret for ret in returns) - 1 if returns else 0.0
    days = max(len(candles), 1)
    cagr = (1 + total_return) ** (365 / days) - 1 if total_return > -1 else -1.0
    wins = [ret for ret in returns if ret > 0]
    losses = [-ret for ret in returns if ret < 0]
    profit_factor = sum(wins) / sum(losses) if losses else (sum(wins) if wins else 0.0)
    return {
        "total_return": total_return,
        "cagr": cagr,
        "mdd": min(0.0, min(returns) if returns else 0.0),
        "trade_count": len(returns),
        "profit_factor": profit_factor,
        "win_rate": len(wins) / len(returns) if returns else 0.0,
    }


def _evaluate(row: dict, candles: list[dict]) -> dict:
    folds = split_validation_windows(candles, folds=3)
    fold_metrics = [_trade_metrics(fold, row.get("parameters", {})) for fold in folds if fold]
    positive = [metric for metric in fold_metrics if metric["total_return"] > 0]
    pass_folds = [
        metric
        for metric in fold_metrics
        if metric["trade_count"] >= 1 and metric["mdd"] >= -0.25 and metric["profit_factor"] >= 1.0
    ]
    total_trade_count = sum(metric["trade_count"] for metric in fold_metrics)
    average_fold_cagr = sum(metric["cagr"] for metric in fold_metrics) / len(fold_metrics) if fold_metrics else 0.0
    aggregate = {
        "fold_count": len(fold_metrics),
        "pass_fold_count": len(pass_folds),
        "positive_fold_count": len(positive),
        "worst_fold_mdd": min((metric["mdd"] for metric in fold_metrics), default=0.0),
        "average_fold_cagr": average_fold_cagr,
        "total_trade_count": total_trade_count,
    }
    status = "OOS_CANDIDATE_PASS" if aggregate["pass_fold_count"] >= 2 and total_trade_count >= 3 else "OOS_CANDIDATE_ITERATE"
    return {
        "candidate_id": row.get("candidate_id"),
        "parent_candidate_id": row.get("parent_candidate_id"),
        "market": row.get("market"),
        "timeframe": row.get("timeframe", "1d"),
        "status": status,
        "parameters": row.get("parameters", {}),
        "source_conversion": row.get("conversion", row.get("source_conversion", {})),
        "folds": fold_metrics,
        "aggregate": aggregate,
        "order_paths_allowed": False,
        "counts_as_paper_or_live_evidence": False,
    }


def oos_candidate_rank(row: dict) -> tuple:
    aggregate = row.get("aggregate") or {}
    conversion = row.get("source_conversion") or {}
    return (
        row.get("status") == "OOS_CANDIDATE_PASS",
        int(aggregate.get("pass_fold_count", 0) or 0),
        int(aggregate.get("positive_fold_count", 0) or 0),
        float(aggregate.get("average_fold_cagr", 0.0) or 0.0),
        int(aggregate.get("total_trade_count", 0) or 0),
        float(conversion.get("estimated_cagr", 0.0) or 0.0),
        float(aggregate.get("worst_fold_mdd", 0.0) or 0.0),
    )


def build_report(generated_at: str | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    source = read_json(SOURCE_SWEEP, {})
    candidates = []
    if source.get("top_sweep"):
        candidates.append(source["top_sweep"])
    candidates.extend(row for row in source.get("sweeps", [])[:9] if row.get("candidate_id") != (source.get("top_sweep") or {}).get("candidate_id"))
    evaluations = []
    errors = []
    for row in candidates:
        candles = backtest.fetch_candles(row.get("market"), row.get("timeframe", "1d"))
        if not candles:
            errors.append({"candidate_id": row.get("candidate_id"), "error": "no_candles_available"})
            continue
        evaluations.append(_evaluate(row, candles))
    pass_count = sum(1 for row in evaluations if row["status"] == "OOS_CANDIDATE_PASS")
    top_oos = sorted(
        [row for row in evaluations if row["status"] == "OOS_CANDIDATE_PASS"],
        key=oos_candidate_rank,
        reverse=True,
    )
    status = "OOS_WALKFORWARD_PASS" if pass_count else "OOS_WALKFORWARD_ITERATE"
    aggregate = {
        "fold_count": 3,
        "candidate_count": len(candidates),
        "evaluated_count": len(evaluations),
        "pass_count": pass_count,
        "error_count": len(errors),
    }
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "source": str(SOURCE_SWEEP),
        "candidate_count": len(candidates),
        "top_oos": top_oos[0] if top_oos else {},
        "evaluations": evaluations,
        "errors": errors,
        "aggregate": aggregate,
        "no_order_assertions": dict(NO_ORDER_ASSERTIONS),
        "single_next_action": "Keep OOS pass candidates in model verification for tiny-live precondition review." if pass_count else "Improve or wait for Bithumb current-actionable OOS candidates.",
    }


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Bithumb Current-Actionable OOS Walkforward",
            "",
            f"- Status: `{report['status']}`",
            f"- Candidates: `{report['candidate_count']}`",
            f"- Evaluated: `{report['aggregate']['evaluated_count']}`",
            f"- Pass: `{report['aggregate']['pass_count']}`",
            f"- Errors: `{report['aggregate']['error_count']}`",
            f"- Top OOS: `{(report.get('top_oos') or {}).get('candidate_id') or '-'}` / `{(report.get('top_oos') or {}).get('market') or '-'}`",
            f"- Single next action: {report['single_next_action']}",
            "",
        ]
    )


def write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def write_json_atomic(path: Path, payload: dict) -> None:
    write_text_atomic(path, json.dumps(payload, indent=2))


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(REPORT_JSON, report)
    write_text_atomic(REPORT_MD, render_md(report))
    print(json.dumps({"status": report["status"], "candidate_count": report["candidate_count"], "evaluated_count": report["aggregate"]["evaluated_count"], "latest_json": str(REPORT_JSON), "no_order_assertions": report["no_order_assertions"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
