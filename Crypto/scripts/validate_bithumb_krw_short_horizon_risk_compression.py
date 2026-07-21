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
    return float((equity / equity.cummax() - 1.0).min())


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
        "cagr": float(equity.iloc[-1] ** (365.0 / days) - 1.0) if len(equity) else 0.0,
        "mdd": _max_drawdown(equity),
        "sharpe": float(daily_returns.mean() / std * math.sqrt(365.0)) if std else 0.0,
        "active_day_ratio": float((daily_returns != 0.0).mean()) if len(daily_returns) else 0.0,
        "final_equity": float(equity.iloc[-1]) if len(equity) else 1.0,
    }


def _baseline(close: pd.Series, hold_window: int, cost_bps: float) -> dict[str, Any]:
    window = close.iloc[-min(hold_window + 1, len(close)) :]
    returns = window.pct_change().dropna()
    if len(returns):
        returns.iloc[0] -= cost_bps / 10_000.0
    return _metrics("baseline_hold", returns, {"hold_window_days": hold_window, "cost_bps": cost_bps}, "hold_to_end")


def _compressed(close: pd.Series, hold_window: int, cost_bps: float, stop_loss: float | None, trailing_stop: float | None, take_profit: float | None) -> dict[str, Any]:
    window = close.iloc[-min(hold_window + 1, len(close)) :]
    raw_returns = window.pct_change().dropna()
    out = []
    equity = 1.0
    peak = 1.0
    exit_reason = "hold_to_end"
    active = True
    for idx, value in enumerate(raw_returns):
        if not active:
            out.append(0.0)
            continue
        daily = float(value)
        if idx == 0:
            daily -= cost_bps / 10_000.0
        equity *= 1.0 + daily
        peak = max(peak, equity)
        out.append(daily)
        entry_drawdown = equity - 1.0
        trailing_drawdown = equity / peak - 1.0
        if stop_loss is not None and entry_drawdown <= -stop_loss:
            active = False
            exit_reason = f"stop_loss_{stop_loss:.0%}"
        elif trailing_stop is not None and trailing_drawdown <= -trailing_stop:
            active = False
            exit_reason = f"trailing_stop_{trailing_stop:.0%}"
        elif take_profit is not None and equity - 1.0 >= take_profit:
            active = False
            exit_reason = f"take_profit_{take_profit:.0%}"
    returns = pd.Series(out, index=raw_returns.index)
    bits = []
    if stop_loss is not None:
        bits.append(f"sl{int(stop_loss * 100)}")
    if trailing_stop is not None:
        bits.append(f"tr{int(trailing_stop * 100)}")
    if take_profit is not None:
        bits.append(f"tp{int(take_profit * 100)}")
    name = "compressed_" + "_".join(bits)
    return _metrics(
        name,
        returns,
        {"hold_window_days": hold_window, "cost_bps": cost_bps, "stop_loss": stop_loss, "trailing_stop": trailing_stop, "take_profit": take_profit},
        exit_reason,
    )


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bithumb KRW Short-Horizon Risk Compression",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- market: `{payload['market']}`",
        f"- decision: `{payload['decision']['status']}`",
        f"- reason: {payload['decision']['reason']}",
        f"- annualization_warning: {payload['annualization_warning']}",
        "",
        "## Ranked Variants",
        "",
        "| variant | total return | MDD | Sharpe | MDD reduction | retained return | exit |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["ranked_variants"]:
        lines.append(
            "| {variant} | {total_return:.2%} | {mdd:.2%} | {sharpe:.2f} | {mdd_red:.2%} | {retained:.2%} | {exit_reason} |".format(
                variant=row["variant"],
                total_return=row["total_return"],
                mdd=row["mdd"],
                sharpe=row["sharpe"],
                mdd_red=row["mdd_reduction_ratio"],
                retained=row["retained_return_ratio"],
                exit_reason=row["exit_reason"],
            )
        )
    best = payload["best_compressed_candidate"]
    lines.extend(
        [
            "",
            "## Best Compressed Candidate",
            "",
            f"- variant: `{best['variant']}`",
            f"- total_return: `{best['total_return']:.2%}`",
            f"- MDD: `{best['mdd']:.2%}`",
            f"- retained_return_ratio: `{best['retained_return_ratio']:.2%}`",
            f"- mdd_reduction_ratio: `{best['mdd_reduction_ratio']:.2%}`",
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
    for stop_loss in (0.05, 0.10, 0.15, 0.20):
        variants.append(_compressed(close, hold_window, cost_bps, stop_loss=stop_loss, trailing_stop=None, take_profit=None))
    for trailing_stop in (0.05, 0.10, 0.15, 0.20):
        variants.append(_compressed(close, hold_window, cost_bps, stop_loss=None, trailing_stop=trailing_stop, take_profit=None))
    for trailing_stop in (0.10, 0.15, 0.20):
        for take_profit in (0.25, 0.50, 0.75):
            variants.append(_compressed(close, hold_window, cost_bps, stop_loss=None, trailing_stop=trailing_stop, take_profit=take_profit))
    base_return = base["total_return"]
    base_mdd_abs = abs(base["mdd"])
    for row in variants:
        row["retained_return_ratio"] = float(row["total_return"] / base_return) if base_return > 0 else 0.0
        row["mdd_reduction_ratio"] = float((base_mdd_abs - abs(row["mdd"])) / base_mdd_abs) if base_mdd_abs > 0 else 0.0
        row["compression_pass"] = row["total_return"] > 0 and row["mdd_reduction_ratio"] > 0 and row["retained_return_ratio"] >= 0.40
    ranked = sorted(variants, key=lambda row: (row["compression_pass"], row["mdd_reduction_ratio"], row["retained_return_ratio"], row["total_return"]), reverse=True)
    pass_rows = [row for row in ranked if row["compression_pass"]]
    best = pass_rows[0] if pass_rows else max(variants, key=lambda row: (row["total_return"], row["mdd_reduction_ratio"]))
    decision = (
        {
            "status": "carry_forward_risk_compression_candidate",
            "reason": "At least one stop/trailing variant retained positive return while reducing MDD.",
            "next_action": "Run OOS/walk-forward validation for the compressed candidate only; keep paper/live/broker submit OFF.",
        }
        if best["compression_pass"]
        else {
            "status": "risk_compression_failed",
            "reason": "No tested stop/trailing variant retained enough return while reducing MDD.",
            "next_action": "Keep the source as return-only research; do not promote.",
        }
    )
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "sources": {
            "short_horizon_model": str(SHORT_MODEL_PATH),
            "candle_availability": str(CANDLE_AVAILABILITY_PATH),
        },
        "safety": {
            "private_api_used": False,
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "mode": "research_only_validation",
        },
        "market": market,
        "hold_window_days": hold_window,
        "source_best_candidate": source_best,
        "baseline": base,
        "ranked_variants": ranked,
        "best_compressed_candidate": best,
        "decision": decision,
        "annualization_warning": "Window is very short. Treat CAGR and Sharpe as screening hints; total return and MDD compression are the primary evidence here.",
    }


def main() -> int:
    payload = build_payload()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = OUT_DIR / f"bithumb_krw_short_horizon_risk_compression_{stamp}.json"
    md_path = OUT_DIR / f"bithumb_krw_short_horizon_risk_compression_{stamp}.md"
    latest_json = OUT_DIR / "bithumb_krw_short_horizon_risk_compression_latest.json"
    latest_md = OUT_DIR / "bithumb_krw_short_horizon_risk_compression_latest.md"
    markdown = _render_markdown(payload)
    for path in (json_path, latest_json):
        _write_json(path, payload)
    for path in (md_path, latest_md):
        path.write_text(markdown, encoding="utf-8")
    best = payload["best_compressed_candidate"]
    print(
        json.dumps(
            {
                "json_path": str(json_path),
                "md_path": str(md_path),
                "decision": payload["decision"]["status"],
                "best_variant": best["variant"],
                "best_total_return": best["total_return"],
                "best_mdd": best["mdd"],
                "mdd_reduction_ratio": best["mdd_reduction_ratio"],
                "retained_return_ratio": best["retained_return_ratio"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
