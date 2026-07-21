from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_parameter_sweep_latest.json"
REPORT_MD = ROOT / "reports/model_factory/bithumb_current_actionable_parameter_sweep_latest.md"
FROZEN_CANDIDATES_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_frozen_candidate_latest.json"
RISK_CONVERSION_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_risk_conversion_latest.json"
CURRENT_SIGNAL_SCOUT_JSON = ROOT / "reports/operations/bithumb_current_actionable_nonzero_signal_scout_latest.json"
BITHUMB_BACKFILL_ROOT = ROOT / "Crypto/data/bithumb_stage2_archive/backfill_full"

TARGET_MDD_ABS = 0.20
MIN_ESTIMATED_CAGR = 0.15
MIN_TRADE_COUNT = 8
MIN_PROFIT_FACTOR = 1.30
MIN_EXPOSURE_CAP = 0.25

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


def read_json(path: Path, default: dict | list | None = None):
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def write_json_atomic(path: Path, payload: dict) -> None:
    write_text_atomic(path, json.dumps(payload, indent=2, ensure_ascii=True))


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
    return sorted(candles, key=lambda item: item["timestamp"])


backtest = SimpleNamespace(fetch_candles=fetch_candles)


def trade_metrics(candles: list[dict], params: dict) -> dict:
    lookback = int(params.get("lookback_bars", 3) or 3)
    hold = int(params.get("hold_bars", 3) or 3)
    volume_window = int(params.get("volume_window", lookback) or lookback)
    volume_floor = float(params.get("volume_ratio_floor", 0.0) or 0.0)
    threshold = float(params.get("momentum_threshold", 0.02) or 0.02)
    cost = float(params.get("round_trip_cost_rate", 0.002) or 0.002)
    stop_loss = abs(float(params.get("stop_loss", 0.12) or 0.12))
    take_profit = abs(float(params.get("take_profit", 0.35) or 0.35))
    returns = []
    holds = []
    index = max(lookback, volume_window)
    while index + 1 < len(candles):
        base = float(candles[index - lookback]["close"])
        close = float(candles[index]["close"])
        if base <= 0 or close <= 0:
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
            holds.append(exit_index - index)
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
        "win_rate": len(wins) / len(returns) if returns else 0.0,
        "profit_factor": profit_factor,
        "trade_count": len(returns),
        "average_holding_bars": sum(holds) / len(holds) if holds else 0.0,
    }


def conversion_for_screen(screen: dict) -> dict:
    metrics = screen.get("metrics") or {}
    source_mdd = float(metrics.get("mdd", 0.0) or 0.0)
    source_cagr = float(metrics.get("cagr", 0.0) or 0.0)
    source_total_return = float(metrics.get("total_return", 0.0) or 0.0)
    source_trade_count = int(metrics.get("trade_count", 0) or 0)
    source_profit_factor = float(metrics.get("profit_factor", 0.0) or 0.0)
    exposure_cap = 1.0 if source_mdd >= 0 else min(1.0, TARGET_MDD_ABS / abs(source_mdd))
    estimated_cagr = source_cagr * exposure_cap
    estimated_total_return = source_total_return * exposure_cap
    estimated_mdd = source_mdd * exposure_cap
    pass_like = (
        exposure_cap >= MIN_EXPOSURE_CAP
        and estimated_cagr >= MIN_ESTIMATED_CAGR
        and source_trade_count >= MIN_TRADE_COUNT
        and source_profit_factor >= MIN_PROFIT_FACTOR
        and estimated_mdd >= -TARGET_MDD_ABS - 1e-12
    )
    return {
        "recommended_exposure_cap": exposure_cap,
        "estimated_cagr": estimated_cagr,
        "estimated_total_return": estimated_total_return,
        "estimated_mdd": estimated_mdd,
        "source_cagr": source_cagr,
        "source_total_return": source_total_return,
        "source_mdd": source_mdd,
        "source_trade_count": source_trade_count,
        "source_profit_factor": source_profit_factor,
        "pass_like": pass_like,
    }


def _rounded_threshold(value: float) -> float:
    return round(float(value), 4)


def _adaptive_thresholds_from_scout(seed: dict, scout: dict | None) -> list[float]:
    if not scout:
        return []
    parent_id = seed.get("candidate_id") or ""
    thresholds = set()
    for row in scout.get("top_near_miss_candidates", []):
        candidate_id = row.get("candidate_id") or ""
        if parent_id and not candidate_id.startswith(f"{parent_id}_"):
            continue
        signal = row.get("signal") or {}
        momentum = signal.get("momentum")
        if momentum is None:
            continue
        momentum = float(momentum)
        if not math.isfinite(momentum):
            continue
        for delta in (-0.02, -0.01, 0.0, 0.01, 0.02):
            thresholds.add(_rounded_threshold(max(-0.25, min(0.08, momentum + delta))))
    return sorted(thresholds)


def parameter_grid(seed: dict, scout: dict | None = None) -> list[dict]:
    frozen = seed.get("frozen_parameters") or {}
    adaptive_thresholds = _adaptive_thresholds_from_scout(seed, scout)
    rows = []
    for lookback in sorted({3, 5, 7, int(frozen.get("lookback_bars", 3) or 3)}):
        for hold in sorted({3, 5, 7, int(frozen.get("hold_bars", 7) or 7)}):
            for volume_window in sorted({lookback, 5, 10, 20, int(frozen.get("volume_window", 20) or 20)}):
                for volume_floor in sorted({0.0, 0.8, 1.0, 1.2, float(frozen.get("volume_ratio_floor", 1.0) or 1.0)}):
                    for threshold in sorted(
                        {0.01, 0.02, 0.03, 0.04, float(frozen.get("momentum_threshold", 0.02) or 0.02), *adaptive_thresholds}
                    ):
                        for stop_loss in sorted({0.08, 0.12, float(frozen.get("stop_loss", 0.12) or 0.12)}):
                            for take_profit in sorted({0.25, 0.35, 0.50, float(frozen.get("take_profit", 0.35) or 0.35)}):
                                rows.append(
                                    {
                                        "lookback_bars": lookback,
                                        "hold_bars": hold,
                                        "volume_window": volume_window,
                                        "volume_ratio_floor": volume_floor,
                                        "momentum_threshold": threshold,
                                        "stop_loss": stop_loss,
                                        "take_profit": take_profit,
                                        "round_trip_cost_rate": float(frozen.get("round_trip_cost_rate", 0.002) or 0.002),
                                        "model_generation_source": (
                                            "current_signal_near_miss_adaptive"
                                            if threshold in adaptive_thresholds
                                            else "static_parameter_grid"
                                        ),
                                    }
                                )
    return rows


def sweep_rank(row: dict) -> tuple:
    conversion = row.get("conversion") or {}
    metrics = row.get("metrics") or {}
    return (
        row.get("status") == "PARAMETER_SWEEP_PASS",
        float(conversion.get("estimated_cagr", 0.0) or 0.0),
        int(metrics.get("trade_count", 0) or 0),
        float(metrics.get("profit_factor", 0.0) or 0.0),
        float(metrics.get("mdd", 0.0) or 0.0),
    )


def sweep_candidate(candidate: dict, candles: list[dict], scout: dict | None = None) -> list[dict]:
    rows = []
    parent_id = candidate.get("candidate_id")
    for index, params in enumerate(parameter_grid(candidate, scout), start=1):
        metrics = trade_metrics(candles, params)
        conversion = conversion_for_screen({"metrics": metrics})
        status = "PARAMETER_SWEEP_PASS" if conversion["pass_like"] else "PARAMETER_SWEEP_ITERATE"
        rows.append(
            {
                "candidate_id": f"{parent_id}_sweep{index:04d}",
                "parent_candidate_id": parent_id,
                "market": candidate.get("market"),
                "timeframe": candidate.get("timeframe", "1d"),
                "status": status,
                "next_gate": "G05_GATEKEEPER_REVIEW_RESEARCH_ONLY" if status == "PARAMETER_SWEEP_PASS" else "G04_PARAMETER_SWEEP_ITERATE",
                "parameters": params,
                "model_generation_source": params.get("model_generation_source", "static_parameter_grid"),
                "metrics": metrics,
                "conversion": conversion,
                "order_paths_allowed": False,
                "counts_as_paper_or_live_evidence": False,
            }
        )
    return sorted(rows, key=sweep_rank, reverse=True)


def source_candidates() -> list[dict]:
    frozen = read_json(FROZEN_CANDIDATES_JSON, {})
    risk = read_json(RISK_CONVERSION_JSON, {})
    frozen_candidates = [row for row in frozen.get("candidates", []) if isinstance(row, dict)]
    risk_ids = {
        row.get("candidate_id")
        for row in risk.get("conversions", [])
        if isinstance(row, dict) and row.get("candidate_id")
    }
    if risk_ids:
        selected = [row for row in frozen_candidates if row.get("candidate_id") in risk_ids]
        if selected:
            return selected
    return frozen_candidates


def build_report(generated_at_utc: str | None = None) -> dict:
    generated_at_utc = generated_at_utc or utc_now()
    candidates = source_candidates()
    scout = read_json(CURRENT_SIGNAL_SCOUT_JSON, {})
    sweeps = []
    errors = []
    for candidate in candidates:
        candles = backtest.fetch_candles(candidate.get("market"), candidate.get("timeframe", "1d"))
        if not candles:
            errors.append({"candidate_id": candidate.get("candidate_id"), "market": candidate.get("market"), "error": "no_candles_available"})
            continue
        sweeps.extend(sweep_candidate(candidate, candles, scout))
    sweeps = sorted(sweeps, key=sweep_rank, reverse=True)
    pass_like_count = sum(1 for row in sweeps if row.get("status") == "PARAMETER_SWEEP_PASS")
    status = "READY_FOR_GATEKEEPER_REVIEW" if pass_like_count else "PARAMETER_SWEEP_ITERATE"
    return {
        "schema_version": "1.2.0",
        "generated_at_utc": generated_at_utc,
        "generated_at": datetime.fromisoformat(generated_at_utc).astimezone(KST).isoformat(),
        "report": "bithumb_current_actionable_parameter_sweep",
        "status": status,
        "scope": "parameter_sweep_risk_conversion_research_only_no_order_paths",
        "sources": {
            "frozen_candidates": str(FROZEN_CANDIDATES_JSON),
            "risk_conversion": str(RISK_CONVERSION_JSON),
            "current_signal_scout": str(CURRENT_SIGNAL_SCOUT_JSON),
        },
        "lane": "bithumb_1d",
        "candidate_count": len(candidates),
        "sweep_count": len(sweeps),
        "pass_like_count": pass_like_count,
        "adaptive_sweep_count": sum(
            1 for row in sweeps if row.get("model_generation_source") == "current_signal_near_miss_adaptive"
        ),
        "adaptive_sweep_pass_like_count": sum(
            1
            for row in sweeps
            if row.get("model_generation_source") == "current_signal_near_miss_adaptive"
            and row.get("status") == "PARAMETER_SWEEP_PASS"
        ),
        "current_signal_scout_status": scout.get("status"),
        "current_signal_near_miss_gap_summary": scout.get("near_miss_gap_summary", {}),
        "errors": errors,
        "top_sweep": sweeps[0] if sweeps else {},
        "sweeps": sweeps,
        "no_order_assertions": dict(NO_ORDER_ASSERTIONS),
        "next_action": "Freeze the top Bithumb current-actionable sweep result for Gatekeeper review; keep all order paths disabled."
        if pass_like_count
        else "Improve the Bithumb current-actionable parameter grid; keep all order paths disabled.",
    }


def render_md(report: dict) -> str:
    lines = [
        "# Bithumb Current-Actionable Parameter Sweep",
        "",
        f"- generated_at_utc: `{report['generated_at_utc']}`",
        f"- status: `{report['status']}`",
        f"- scope: `{report['scope']}`",
        f"- candidate_count: `{report['candidate_count']}`",
        f"- sweep_count: `{report['sweep_count']}`",
        f"- pass_like_count: `{report['pass_like_count']}`",
        f"- adaptive_sweep_count: `{report.get('adaptive_sweep_count', 0)}`",
        f"- adaptive_sweep_pass_like_count: `{report.get('adaptive_sweep_pass_like_count', 0)}`",
        f"- current_signal_scout_status: `{report.get('current_signal_scout_status')}`",
        f"- next_action: `{report['next_action']}`",
        "",
        "## Top Sweeps",
        "",
        "| candidate | parent | market | status | cap | est CAGR | est MDD | source CAGR | source MDD | trades | PF | next gate |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report.get("sweeps", [])[:10]:
        conversion = row.get("conversion") or {}
        metrics = row.get("metrics") or {}
        lines.append(
            "| `{candidate}` | `{parent}` | `{market}` | `{status}` | `{cap:.2%}` | `{est_cagr:.2%}` | `{est_mdd:.2%}` | `{source_cagr:.2%}` | `{source_mdd:.2%}` | `{trades}` | `{pf:.2f}` | `{gate}` |".format(
                candidate=row.get("candidate_id"),
                parent=row.get("parent_candidate_id"),
                market=row.get("market"),
                status=row.get("status"),
                cap=float(conversion.get("recommended_exposure_cap") or 0.0),
                est_cagr=float(conversion.get("estimated_cagr") or 0.0),
                est_mdd=float(conversion.get("estimated_mdd") or 0.0),
                source_cagr=float(conversion.get("source_cagr") or 0.0),
                source_mdd=float(conversion.get("source_mdd") or 0.0),
                trades=int(metrics.get("trade_count") or 0),
                pf=float(metrics.get("profit_factor") or 0.0),
                gate=row.get("next_gate"),
            )
        )
    lines.extend(["", "## Safety", ""])
    lines.extend(f"- {key}: `{value}`" for key, value in report["no_order_assertions"].items())
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    write_json_atomic(REPORT_JSON, report)
    write_text_atomic(REPORT_MD, render_md(report))
    print(
        json.dumps(
            {
                "status": report["status"],
                "candidate_count": report["candidate_count"],
                "sweep_count": report["sweep_count"],
                "pass_like_count": report["pass_like_count"],
                "latest_json": str(REPORT_JSON),
                "no_order_assertions": report["no_order_assertions"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
