from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


CRYPTO_ROOT = Path(r"C:\AI\Crypto")
OUT_DIR = CRYPTO_ROOT / "analysis_results"
RECENT_SCREEN_PATH = OUT_DIR / "bithumb_krw_recent_return_screen_latest.json"
CANDLE_AVAILABILITY_PATH = OUT_DIR / "bithumb_krw_candle_availability_latest.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _carry_markets() -> list[str]:
    payload = _load_json(RECENT_SCREEN_PATH)
    rows = payload.get("markets") or []
    markets = [str(row["market"]) for row in rows if isinstance(row, dict) and row.get("decision") == "carry_forward_recent_return_axis"]
    if len(markets) < 3:
        raise RuntimeError("Need at least 3 carry-forward recent-return markets")
    return markets


def _raw_paths() -> dict[str, str]:
    payload = _load_json(CANDLE_AVAILABILITY_PATH)
    rows = payload.get("markets") or []
    return {str(row["market"]): str(row["raw_path"]) for row in rows if isinstance(row, dict) and row.get("market") and row.get("raw_path")}


def _load_close_series(path: str) -> pd.Series:
    rows = _load_json(Path(path))
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["candle_date_time_utc"], utc=True)
    frame = frame.sort_values("date")
    return pd.Series(frame["trade_price"].astype(float).to_numpy(), index=frame["date"], name=str(frame["market"].iloc[0]))


def _price_frame() -> pd.DataFrame:
    paths = _raw_paths()
    series = []
    for market in _carry_markets():
        if market not in paths:
            continue
        series.append(_load_close_series(paths[market]))
    if len(series) < 3:
        raise RuntimeError("Fewer than 3 carry-forward markets have candle paths")
    return pd.concat(series, axis=1).sort_index()


def _max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    return float((equity / equity.cummax() - 1.0).min())


def _metrics(name: str, daily_returns: pd.Series, turnover: pd.Series, params: dict[str, Any]) -> dict[str, Any]:
    daily_returns = daily_returns.dropna()
    equity = (1.0 + daily_returns).cumprod()
    days = max(1, len(daily_returns))
    std = float(daily_returns.std(ddof=0)) if len(daily_returns) else 0.0
    active_day_ratio = float((daily_returns != 0.0).mean()) if len(daily_returns) else 0.0
    return {
        "variant": name,
        "params": params,
        "days": days,
        "total_return": float(equity.iloc[-1] - 1.0) if len(equity) else 0.0,
        "cagr": float(equity.iloc[-1] ** (365.0 / days) - 1.0) if len(equity) else 0.0,
        "mdd": _max_drawdown(equity),
        "sharpe": float(daily_returns.mean() / std * math.sqrt(365.0)) if std else 0.0,
        "annualized_volatility": float(std * math.sqrt(365.0)),
        "average_daily_turnover": float(turnover.reindex(daily_returns.index).fillna(0.0).mean()) if len(turnover) else 0.0,
        "active_day_ratio": active_day_ratio,
        "final_equity": float(equity.iloc[-1]) if len(equity) else 1.0,
    }


def _window_prices(prices: pd.DataFrame, window_days: int) -> pd.DataFrame:
    return prices.iloc[-min(window_days + 1, len(prices)) :]


def _buy_hold_top_recent(prices: pd.DataFrame, score_window: int, hold_window: int, top_k: int, cost_bps: float) -> dict[str, Any]:
    frame = _window_prices(prices, hold_window + score_window + 1)
    score_frame = frame.pct_change(score_window)
    first_scores = score_frame.iloc[score_window].dropna().sort_values(ascending=False)
    winners = [symbol for symbol, value in first_scores.items() if value > 0.0][:top_k]
    returns = frame[winners].pct_change().dropna() if winners else pd.DataFrame(index=frame.index[1:])
    daily = returns.mean(axis=1) if winners else pd.Series(0.0, index=frame.index[1:])
    turnover = pd.Series(0.0, index=daily.index)
    if len(turnover):
        turnover.iloc[0] = 1.0
    daily = daily - turnover * cost_bps / 10_000.0
    return _metrics(
        f"locked_recent_score{score_window}_hold{hold_window}_top{top_k}",
        daily,
        turnover,
        {"score_window_days": score_window, "hold_window_days": hold_window, "top_k": top_k, "cost_bps": cost_bps, "selected": winners},
    )


def _rolling_momentum(prices: pd.DataFrame, lookback: int, top_k: int, trade_window: int, cost_bps: float) -> dict[str, Any]:
    frame = _window_prices(prices, trade_window + lookback + 1)
    returns = frame.pct_change()
    trailing = frame.pct_change(lookback)
    weights = pd.DataFrame(0.0, index=frame.index, columns=frame.columns)
    for idx in range(lookback, len(frame) - 1):
        available = trailing.iloc[idx].dropna().sort_values(ascending=False)
        winners = [symbol for symbol, value in available.items() if value > 0.0][:top_k]
        if winners:
            weights.loc[frame.index[idx], winners] = 1.0 / len(winners)
    shifted = weights.shift(1).reindex(returns.index).fillna(0.0)
    turnover = shifted.diff().abs().sum(axis=1).fillna(shifted.abs().sum(axis=1))
    daily = (shifted * returns).sum(axis=1) - turnover * cost_bps / 10_000.0
    daily = daily.iloc[lookback + 1 :]
    turnover = turnover.reindex(daily.index).fillna(0.0)
    return _metrics(
        f"rolling_momentum_l{lookback}_top{top_k}_w{trade_window}",
        daily,
        turnover,
        {"lookback_days": lookback, "top_k": top_k, "trade_window_days": trade_window, "cost_bps": cost_bps},
    )


def _single_asset_recent(prices: pd.DataFrame, hold_window: int, cost_bps: float) -> list[dict[str, Any]]:
    frame = _window_prices(prices, hold_window + 1)
    out = []
    for symbol in frame.columns:
        series = frame[symbol].dropna()
        if len(series) < 8:
            continue
        returns = series.pct_change().dropna()
        turnover = pd.Series(0.0, index=returns.index)
        if len(turnover):
            turnover.iloc[0] = 1.0
        daily = returns - turnover * cost_bps / 10_000.0
        out.append(_metrics(f"single_asset_{symbol}_hold{hold_window}", daily, turnover, {"market": symbol, "hold_window_days": hold_window, "cost_bps": cost_bps}))
    return out


def _decision(best: dict[str, Any]) -> dict[str, Any]:
    if best["cagr"] > 0.0 and best["sharpe"] > 0.0:
        return {
            "status": "carry_forward_return_candidate",
            "reason": "Short-horizon carry-forward axis produced a positive CAGR and Sharpe candidate.",
            "next_action": "Run risk-compression and OOS checks for this candidate only; keep paper/live/broker submit OFF.",
        }
    return {
        "status": "killed_axis",
        "reason": "No short-horizon candidate produced positive CAGR and Sharpe.",
        "next_action": "Do not retry this axis without a materially different signal or new market snapshot.",
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bithumb KRW Short-Horizon Return Model",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- markets: `{', '.join(payload['markets'])}`",
        f"- decision: `{payload['decision']['status']}`",
        f"- reason: {payload['decision']['reason']}",
        f"- annualization_warning: {payload['annualization_warning']}",
        "",
        "## Ranked Variants",
        "",
        "| variant | CAGR | MDD | Sharpe | total return | turnover | active |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["ranked_variants"][:15]:
        lines.append(
            "| {variant} | {cagr:.2%} | {mdd:.2%} | {sharpe:.2f} | {total_return:.2%} | {turnover:.2f} | {active:.2f} |".format(
                variant=row["variant"],
                cagr=row["cagr"],
                mdd=row["mdd"],
                sharpe=row["sharpe"],
                total_return=row["total_return"],
                turnover=row["average_daily_turnover"],
                active=row["active_day_ratio"],
            )
        )
    best = payload["best_return_candidate"]
    lines.extend(
        [
            "",
            "## Best Candidate",
            "",
            f"- variant: `{best['variant']}`",
            f"- CAGR: `{best['cagr']:.2%}`",
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
    prices = _price_frame()
    cost_bps = 20.0
    variants: list[dict[str, Any]] = []
    for hold_window in (14, 30, 60):
        variants.extend(_single_asset_recent(prices, hold_window=hold_window, cost_bps=cost_bps))
    for score_window in (3, 7, 14):
        for hold_window in (14, 30, 60):
            for top_k in (1, 2):
                variants.append(_buy_hold_top_recent(prices, score_window=score_window, hold_window=hold_window, top_k=top_k, cost_bps=cost_bps))
    for lookback in (3, 7, 14):
        for top_k in (1, 2):
            for trade_window in (30, 60):
                variants.append(_rolling_momentum(prices, lookback=lookback, top_k=top_k, trade_window=trade_window, cost_bps=cost_bps))
    ranked = sorted(variants, key=lambda row: (row["cagr"], row["sharpe"]), reverse=True)
    best = ranked[0]
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "sources": {
            "recent_return_screen": str(RECENT_SCREEN_PATH),
            "candle_availability": str(CANDLE_AVAILABILITY_PATH),
        },
        "safety": {
            "private_api_used": False,
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "mode": "research_only_backtest",
        },
        "markets": [str(column) for column in prices.columns],
        "cost_bps": cost_bps,
        "ranked_variants": ranked,
        "best_return_candidate": best,
        "decision": _decision(best),
        "annualization_warning": "CAGR is annualized from short windows and can be explosively large. Use total_return, MDD, Sharpe, and validation before any promotion.",
        "interpretation": "Return-side short-horizon research only. Positive output is not paper/live readiness.",
    }


def main() -> int:
    payload = build_payload()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = OUT_DIR / f"bithumb_krw_short_horizon_return_model_{stamp}.json"
    md_path = OUT_DIR / f"bithumb_krw_short_horizon_return_model_{stamp}.md"
    latest_json = OUT_DIR / "bithumb_krw_short_horizon_return_model_latest.json"
    latest_md = OUT_DIR / "bithumb_krw_short_horizon_return_model_latest.md"
    markdown = _render_markdown(payload)
    for path in (json_path, latest_json):
        _write_json(path, payload)
    for path in (md_path, latest_md):
        path.write_text(markdown, encoding="utf-8")
    best = payload["best_return_candidate"]
    print(
        json.dumps(
            {
                "json_path": str(json_path),
                "md_path": str(md_path),
                "decision": payload["decision"]["status"],
                "best_variant": best["variant"],
                "best_cagr": best["cagr"],
                "best_mdd": best["mdd"],
                "best_sharpe": best["sharpe"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
