from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


CRYPTO_ROOT = Path(r"C:\AI\Crypto")
OUT_DIR = CRYPTO_ROOT / "analysis_results"
AVAILABILITY_PATH = OUT_DIR / "bithumb_krw_candle_availability_latest.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_close_series(raw_path: str) -> pd.Series:
    rows = _load_json(Path(raw_path))
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["candle_date_time_utc"], utc=True)
    frame = frame.sort_values("date")
    return pd.Series(frame["trade_price"].astype(float).to_numpy(), index=frame["date"], name=str(frame["market"].iloc[0]))


def _price_frame() -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    payload = _load_json(AVAILABILITY_PATH)
    ready = payload.get("summary", {}).get("ready_markets", [])
    if len(ready) < 3:
        raise RuntimeError("Need at least 3 model_ready_1d markets for a multi-asset baseline")
    series = [_load_close_series(row["raw_path"]) for row in ready if row.get("raw_path")]
    prices = pd.concat(series, axis=1).dropna(how="any")
    return prices, ready


def _max_drawdown(equity: pd.Series) -> float:
    drawdown = equity / equity.cummax() - 1.0
    return float(drawdown.min())


def _metrics(name: str, daily_returns: pd.Series, turnover: pd.Series, params: dict[str, Any]) -> dict[str, Any]:
    daily_returns = daily_returns.dropna()
    equity = (1.0 + daily_returns).cumprod()
    days = max(1, len(daily_returns))
    total_return = float(equity.iloc[-1] - 1.0) if len(equity) else 0.0
    cagr = float(equity.iloc[-1] ** (365.0 / days) - 1.0) if len(equity) else 0.0
    vol = float(daily_returns.std(ddof=0) * math.sqrt(365.0)) if len(daily_returns) else 0.0
    sharpe = float(daily_returns.mean() / daily_returns.std(ddof=0) * math.sqrt(365.0)) if daily_returns.std(ddof=0) else 0.0
    return {
        "variant": name,
        "params": params,
        "days": days,
        "total_return": total_return,
        "cagr": cagr,
        "mdd": _max_drawdown(equity) if len(equity) else 0.0,
        "sharpe": sharpe,
        "annualized_volatility": vol,
        "average_daily_turnover": float(turnover.reindex(daily_returns.index).fillna(0.0).mean()) if len(turnover) else 0.0,
        "final_equity": float(equity.iloc[-1]) if len(equity) else 1.0,
    }


def _buy_hold_equal(prices: pd.DataFrame, cost_bps: float) -> dict[str, Any]:
    returns = prices.pct_change().dropna()
    daily = returns.mean(axis=1)
    turnover = pd.Series(0.0, index=daily.index)
    turnover.iloc[0] = 1.0
    daily = daily - turnover * cost_bps / 10_000.0
    return _metrics("buy_hold_equal_ready", daily, turnover, {"cost_bps": cost_bps, "market_count": prices.shape[1]})


def _xs_momentum(prices: pd.DataFrame, lookback: int, top_k: int, cost_bps: float) -> dict[str, Any]:
    returns = prices.pct_change()
    trailing = prices.pct_change(lookback)
    weights = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    for idx in range(lookback, len(prices) - 1):
        scores = trailing.iloc[idx].dropna().sort_values(ascending=False)
        winners = [symbol for symbol, value in scores.items() if value > 0.0][:top_k]
        if winners:
            weights.loc[prices.index[idx], winners] = 1.0 / len(winners)
    shifted = weights.shift(1).reindex(returns.index).fillna(0.0)
    turnover = shifted.diff().abs().sum(axis=1).fillna(shifted.abs().sum(axis=1))
    daily = (shifted * returns).sum(axis=1) - turnover * cost_bps / 10_000.0
    daily = daily.iloc[lookback + 1 :]
    turnover = turnover.reindex(daily.index).fillna(0.0)
    return _metrics(
        f"xs_momentum_l{lookback}_top{top_k}",
        daily,
        turnover,
        {"lookback_days": lookback, "top_k": top_k, "cost_bps": cost_bps},
    )


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bithumb KRW Multi-Asset Return Baseline",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- market_count: `{payload['market_count']}`",
        f"- date_start: `{payload['date_start']}`",
        f"- date_end: `{payload['date_end']}`",
        "",
        "## Ranked Variants",
        "",
        "| variant | CAGR | MDD | Sharpe | total return | avg turnover |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["ranked_variants"]:
        lines.append(
            "| {variant} | {cagr:.2%} | {mdd:.2%} | {sharpe:.2f} | {total_return:.2%} | {turnover:.2f} |".format(
                variant=row["variant"],
                cagr=row["cagr"],
                mdd=row["mdd"],
                sharpe=row["sharpe"],
                total_return=row["total_return"],
                turnover=row["average_daily_turnover"],
            )
        )
    best = payload["best_return_candidate"]
    decision = payload["decision"]
    lines.extend(
        [
            "",
            "## Best Return Candidate",
            "",
            f"- variant: `{best['variant']}`",
            f"- CAGR: `{best['cagr']:.2%}`",
            f"- MDD: `{best['mdd']:.2%}`",
            f"- Sharpe: `{best['sharpe']:.2f}`",
            "",
            "## Decision",
            "",
            f"- status: `{decision['status']}`",
            f"- reason: {decision['reason']}",
            "",
            "## Next Action",
            "",
            f"- {decision['next_action']}",
        ]
    )
    return "\n".join(lines)


def build_payload() -> dict[str, Any]:
    prices, ready = _price_frame()
    cost_bps = 20.0
    variants = [_buy_hold_equal(prices, cost_bps=cost_bps)]
    for lookback in (3, 7, 14, 28):
        for top_k in (1, 2, 3):
            variants.append(_xs_momentum(prices, lookback=lookback, top_k=top_k, cost_bps=cost_bps))
    ranked = sorted(variants, key=lambda row: (row["cagr"], row["sharpe"]), reverse=True)
    best = ranked[0]
    if best["cagr"] <= 0.0 or best["sharpe"] <= 0.0:
        decision = {
            "status": "killed_axis",
            "reason": "Naive 200-day multi-asset buy-hold/cross-sectional momentum did not produce a positive return-side candidate.",
            "next_action": "Do not repair code blindly. Try a separate frozen-scope regime filter or shorter-horizon fresh-listing axis, still research-only.",
        }
    else:
        decision = {
            "status": "carry_forward_return_candidate",
            "reason": "At least one return-side candidate has positive CAGR and Sharpe before risk compression.",
            "next_action": "Preserve this as a return-side candidate, then run risk-compression variants. Do not promote to paper/live.",
        }
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "sources": {
            "candle_availability": str(AVAILABILITY_PATH),
        },
        "safety": {
            "private_api_used": False,
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "mode": "research_only_backtest",
        },
        "market_count": int(prices.shape[1]),
        "markets": [str(column) for column in prices.columns],
        "date_start": prices.index.min().isoformat(),
        "date_end": prices.index.max().isoformat(),
        "cost_bps": cost_bps,
        "ranked_variants": ranked,
        "best_return_candidate": best,
        "decision": decision,
        "ready_market_source_rows": ready,
        "interpretation": "Return-side screen only. High CAGR does not imply operational readiness until drawdown, turnover, slippage, and OOS checks are compressed.",
    }


def main() -> int:
    payload = build_payload()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = OUT_DIR / f"bithumb_krw_multi_asset_return_baseline_{stamp}.json"
    md_path = OUT_DIR / f"bithumb_krw_multi_asset_return_baseline_{stamp}.md"
    latest_json = OUT_DIR / "bithumb_krw_multi_asset_return_baseline_latest.json"
    latest_md = OUT_DIR / "bithumb_krw_multi_asset_return_baseline_latest.md"
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
                "market_count": payload["market_count"],
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
