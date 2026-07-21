from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


CRYPTO_ROOT = Path(r"C:\AI\Crypto")
OUT_DIR = CRYPTO_ROOT / "analysis_results"
SHORT_MODEL_PATH = OUT_DIR / "bithumb_krw_short_horizon_return_model_latest.json"
CANDLE_AVAILABILITY_PATH = OUT_DIR / "bithumb_krw_candle_availability_latest.json"
KILLED_AXES_PATH = Path(r"C:\AI\automation\state\killed_axes.json")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _candidate() -> tuple[str, int, dict[str, Any]]:
    payload = _load_json(SHORT_MODEL_PATH)
    best = payload["best_return_candidate"]
    params = best.get("params") or {}
    selected = params.get("selected") or [params.get("market")]
    market = str(selected[0])
    hold_window = int(params.get("hold_window_days") or 14)
    return market, hold_window, best


def _raw_path(market: str) -> str:
    payload = _load_json(CANDLE_AVAILABILITY_PATH)
    for row in payload.get("markets") or []:
        if isinstance(row, dict) and row.get("market") == market and row.get("raw_path"):
            return str(row["raw_path"])
    raise FileNotFoundError(f"No raw candle path for {market}")


def _close_series(path: str) -> pd.Series:
    rows = _load_json(Path(path))
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["candle_date_time_utc"], utc=True)
    frame = frame.sort_values("date")
    return pd.Series(frame["trade_price"].astype(float).to_numpy(), index=frame["date"], name=str(frame["market"].iloc[0]))


def _max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    seeded = pd.concat([pd.Series([1.0]), equity.reset_index(drop=True)], ignore_index=True)
    return float((seeded / seeded.cummax() - 1.0).min())


def _metrics(name: str, daily_returns: pd.Series, params: dict[str, Any], exit_reason: str) -> dict[str, Any]:
    daily_returns = daily_returns.dropna()
    equity = (1.0 + daily_returns).cumprod()
    days = max(1, len(daily_returns))
    std = float(daily_returns.std(ddof=0)) if len(daily_returns) else 0.0
    return {
        "variant": name,
        "params": params,
        "exit_reason": exit_reason,
        "days": days,
        "total_return": float(equity.iloc[-1] - 1.0) if len(equity) else 0.0,
        "cagr": float(equity.iloc[-1] ** (365.0 / days) - 1.0) if len(equity) and equity.iloc[-1] > 0 else -1.0,
        "mdd": _max_drawdown(equity),
        "sharpe": float(daily_returns.mean() / std * math.sqrt(365.0)) if std else 0.0,
        "annualized_volatility": float(std * math.sqrt(365.0)),
        "average_exposure": float(params.get("exposure", 1.0)),
        "active_day_ratio": float((daily_returns != 0.0).mean()) if len(daily_returns) else 0.0,
        "final_equity": float(equity.iloc[-1]) if len(equity) else 1.0,
    }


def _recent_returns(close: pd.Series, hold_window: int) -> pd.Series:
    window = close.iloc[-min(hold_window + 1, len(close)) :]
    return window.pct_change().dropna()


def _realized_pre_entry_vol(close: pd.Series, hold_window: int, lookback_days: int) -> float:
    end = max(1, len(close) - hold_window)
    start = max(0, end - lookback_days - 1)
    history = close.iloc[start:end]
    returns = history.pct_change().dropna()
    if len(returns) < 5:
        return 0.0
    return float(returns.std(ddof=0) * math.sqrt(365.0))


def _baseline(close: pd.Series, hold_window: int, cost_bps: float) -> dict[str, Any]:
    returns = _recent_returns(close, hold_window)
    if len(returns):
        returns.iloc[0] -= cost_bps / 10_000.0
    return _metrics("baseline_hold", returns, {"hold_window_days": hold_window, "cost_bps": cost_bps, "exposure": 1.0}, "hold_to_end")


def _vol_time_stop(close: pd.Series, hold_window: int, cost_bps: float, vol_lookback: int, vol_target: float, time_stop_days: int) -> dict[str, Any]:
    raw_returns = _recent_returns(close, hold_window)
    realized = _realized_pre_entry_vol(close, hold_window, vol_lookback)
    exposure = 1.0 if realized <= 0.0 else max(0.05, min(1.0, vol_target / realized))
    active_days = min(time_stop_days, len(raw_returns))
    out = []
    for idx, value in enumerate(raw_returns):
        if idx >= active_days:
            out.append(0.0)
            continue
        daily = float(value) * exposure
        if idx == 0:
            daily -= exposure * cost_bps / 10_000.0
        out.append(daily)
    returns = pd.Series(out, index=raw_returns.index)
    return _metrics(
        f"vol_time_stop_lb{vol_lookback}_target{str(vol_target).replace('.', 'p')}_days{time_stop_days}",
        returns,
        {
            "hold_window_days": hold_window,
            "cost_bps": cost_bps,
            "vol_lookback_days": vol_lookback,
            "vol_target": vol_target,
            "time_stop_days": time_stop_days,
            "realized_pre_entry_vol": realized,
            "exposure": exposure,
        },
        f"time_stop_{time_stop_days}d",
    )


def _killed_axis_reopen_rule() -> dict[str, Any]:
    if not KILLED_AXES_PATH.exists():
        return {}
    payload = _load_json(KILLED_AXES_PATH)
    for row in payload.get("killed_axes") or []:
        if row.get("axis_id") == "bithumb_krw_bio_short_horizon_stop_trailing_compression":
            return {
                "axis_id": row.get("axis_id"),
                "killed_at_utc": row.get("killed_at_utc"),
                "reopen_rule": row.get("reopen_rule"),
                "why_this_run_is_distinct": "Tests volatility sizing plus time-stop exits, not stop-loss/trailing-stop/take-profit compression.",
            }
    return {}


def _decision(best: dict[str, Any]) -> dict[str, Any]:
    if best["compression_pass"]:
        return {
            "status": "carry_forward_alt_risk_mechanism_candidate",
            "reason": "A volatility-sizing plus time-stop variant retained positive return while reducing MDD versus the recent hold baseline.",
            "next_action": "Run a non-overlapping frozen validation or wait for a materially new Bithumb snapshot before any shadow/paper consideration.",
        }
    return {
        "status": "alt_risk_mechanism_failed",
        "reason": "No volatility-sizing plus time-stop variant retained enough return while reducing MDD.",
        "next_action": "Keep this source in research only; do not promote or retune the same current snapshot.",
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bithumb KRW Short-Horizon Alt Risk Mechanism",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- market: `{payload['market']}`",
        f"- decision: `{payload['decision']['status']}`",
        f"- reason: {payload['decision']['reason']}",
        f"- safety: `private_api_used={payload['safety']['private_api_used']}`, `paper_enabled={payload['safety']['paper_enabled']}`, `live_enabled={payload['safety']['live_enabled']}`, `broker_submit_allowed={payload['safety']['broker_submit_allowed']}`",
        "",
        "## Reopen Rule",
        "",
        f"- axis_id: `{payload['reopen_rule_evidence'].get('axis_id', 'unknown')}`",
        f"- rule: {payload['reopen_rule_evidence'].get('reopen_rule', 'not found')}",
        f"- distinction: {payload['reopen_rule_evidence'].get('why_this_run_is_distinct', 'not recorded')}",
        "",
        "## Ranked Variants",
        "",
        "| variant | total return | MDD | Sharpe | exposure | MDD reduction | retained return | pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["ranked_variants"]:
        lines.append(
            "| {variant} | {total_return:.2%} | {mdd:.2%} | {sharpe:.2f} | {exposure:.2f} | {mdd_red:.2%} | {retained:.2%} | {passed} |".format(
                variant=row["variant"],
                total_return=row["total_return"],
                mdd=row["mdd"],
                sharpe=row["sharpe"],
                exposure=row["average_exposure"],
                mdd_red=row["mdd_reduction_ratio"],
                retained=row["retained_return_ratio"],
                passed="yes" if row["compression_pass"] else "no",
            )
        )
    best = payload["best_alt_risk_candidate"]
    lines.extend(
        [
            "",
            "## Best Candidate",
            "",
            f"- variant: `{best['variant']}`",
            f"- total_return: `{best['total_return']:.2%}`",
            f"- MDD: `{best['mdd']:.2%}`",
            f"- Sharpe: `{best['sharpe']:.2f}`",
            f"- params: `{json.dumps(best['params'], ensure_ascii=False)}`",
            "",
            "## Next Action",
            "",
            f"- {payload['decision']['next_action']}",
        ]
    )
    return "\n".join(lines)


def build_payload() -> dict[str, Any]:
    market, hold_window, source_best = _candidate()
    close = _close_series(_raw_path(market))
    cost_bps = 20.0
    base = _baseline(close, hold_window, cost_bps)
    variants = [base]
    for vol_lookback in (10, 20, 30):
        for vol_target in (0.60, 0.80, 1.00, 1.20):
            for time_stop_days in (3, 5, 7, 10):
                variants.append(_vol_time_stop(close, hold_window, cost_bps, vol_lookback, vol_target, time_stop_days))
    base_return = base["total_return"]
    base_mdd_abs = abs(base["mdd"])
    for row in variants:
        row["retained_return_ratio"] = float(row["total_return"] / base_return) if base_return > 0 else 0.0
        row["mdd_reduction_ratio"] = float((base_mdd_abs - abs(row["mdd"])) / base_mdd_abs) if base_mdd_abs > 0 else 0.0
        row["compression_pass"] = (
            row["variant"] != "baseline_hold"
            and row["total_return"] > 0.0
            and row["retained_return_ratio"] >= 0.40
            and row["mdd_reduction_ratio"] >= 0.15
            and row["sharpe"] > 0.0
        )
    ranked = sorted(
        variants,
        key=lambda row: (row["compression_pass"], row["mdd_reduction_ratio"], row["retained_return_ratio"], row["sharpe"], row["total_return"]),
        reverse=True,
    )
    pass_rows = [row for row in ranked if row["compression_pass"]]
    best = pass_rows[0] if pass_rows else max(variants, key=lambda row: (row["total_return"], row["mdd_reduction_ratio"], row["sharpe"]))
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "scope": "HISTORICAL-REVIVAL-ALT-RISK-001",
        "sources": {
            "short_horizon_model": str(SHORT_MODEL_PATH),
            "candle_availability": str(CANDLE_AVAILABILITY_PATH),
            "killed_axes": str(KILLED_AXES_PATH),
        },
        "safety": {
            "private_api_used": False,
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "mode": "research_only_alt_risk_mechanism_validation",
        },
        "market": market,
        "hold_window_days": hold_window,
        "source_best_candidate": source_best,
        "baseline": base,
        "ranked_variants": ranked,
        "best_alt_risk_candidate": best,
        "decision": _decision(best),
        "reopen_rule_evidence": _killed_axis_reopen_rule(),
        "annualization_warning": "Window is very short. Treat CAGR and Sharpe as screening hints; total return, MDD reduction, and follow-on validation are the primary evidence.",
        "interpretation": "This is a bounded historical-revival check for a different risk mechanism. It is not paper/live readiness and does not enable broker submission.",
    }


def main() -> int:
    payload = build_payload()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = OUT_DIR / f"bithumb_krw_short_horizon_alt_risk_mechanism_{stamp}.json"
    md_path = OUT_DIR / f"bithumb_krw_short_horizon_alt_risk_mechanism_{stamp}.md"
    latest_json = OUT_DIR / "bithumb_krw_short_horizon_alt_risk_mechanism_latest.json"
    latest_md = OUT_DIR / "bithumb_krw_short_horizon_alt_risk_mechanism_latest.md"
    markdown = _render_markdown(payload)
    for path in (json_path, latest_json):
        _write_json(path, payload)
    for path in (md_path, latest_md):
        path.write_text(markdown, encoding="utf-8")
    best = payload["best_alt_risk_candidate"]
    print(
        json.dumps(
            {
                "json_path": str(json_path),
                "md_path": str(md_path),
                "decision": payload["decision"]["status"],
                "best_variant": best["variant"],
                "best_total_return": best["total_return"],
                "best_mdd": best["mdd"],
                "best_sharpe": best["sharpe"],
                "paper_enabled": payload["safety"]["paper_enabled"],
                "live_enabled": payload["safety"]["live_enabled"],
                "broker_submit_allowed": payload["safety"]["broker_submit_allowed"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
