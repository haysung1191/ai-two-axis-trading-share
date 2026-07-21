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
        raise RuntimeError("Need at least 3 carry-forward markets")
    return markets


def _raw_paths() -> dict[str, str]:
    payload = _load_json(CANDLE_AVAILABILITY_PATH)
    rows = payload.get("markets") or []
    return {str(row["market"]): str(row["raw_path"]) for row in rows if isinstance(row, dict) and row.get("market") and row.get("raw_path")}


def _load_close(path: str) -> pd.Series:
    rows = _load_json(Path(path))
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["candle_date_time_utc"], utc=True)
    frame = frame.sort_values("date")
    return pd.Series(frame["trade_price"].astype(float).to_numpy(), index=frame["date"], name=str(frame["market"].iloc[0]))


def _price_frame() -> pd.DataFrame:
    paths = _raw_paths()
    series = [_load_close(paths[market]) for market in _carry_markets() if market in paths]
    if len(series) < 3:
        raise RuntimeError("Fewer than 3 carry-forward markets have candle paths")
    return pd.concat(series, axis=1).sort_index()


def _max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    return float((equity / equity.cummax() - 1.0).min())


def _segment_returns(daily: pd.Series, segment_days: int) -> list[float]:
    values: list[float] = []
    for start in range(0, len(daily), segment_days):
        segment = daily.iloc[start : start + segment_days]
        if len(segment):
            values.append(float((1.0 + segment).prod() - 1.0))
    return values


def _metrics(name: str, daily: pd.Series, turnover: pd.Series, exposure: pd.Series, params: dict[str, Any]) -> dict[str, Any]:
    daily = daily.dropna()
    equity = (1.0 + daily).cumprod()
    days = max(1, len(daily))
    std = float(daily.std(ddof=0)) if len(daily) else 0.0
    segments = _segment_returns(daily, int(params["rebalance_days"]))
    positive_segments = [value for value in segments if value > 0.0]
    return {
        "variant": name,
        "params": params,
        "days": days,
        "total_return": float(equity.iloc[-1] - 1.0) if len(equity) else 0.0,
        "cagr": float(equity.iloc[-1] ** (365.0 / days) - 1.0) if len(equity) else 0.0,
        "mdd": _max_drawdown(equity),
        "sharpe": float(daily.mean() / std * math.sqrt(365.0)) if std else 0.0,
        "annualized_volatility": float(std * math.sqrt(365.0)),
        "average_turnover": float(turnover.reindex(daily.index).fillna(0.0).mean()) if len(turnover) else 0.0,
        "average_exposure": float(exposure.reindex(daily.index).fillna(0.0).mean()) if len(exposure) else 0.0,
        "walk_forward_segments": len(segments),
        "positive_segment_count": len(positive_segments),
        "positive_segment_rate": float(len(positive_segments) / len(segments)) if segments else 0.0,
        "segment_returns": segments,
        "final_equity": float(equity.iloc[-1]) if len(equity) else 1.0,
    }


def _target_exposure(prior_returns: pd.Series, vol_target: float | None) -> float:
    if vol_target is None:
        return 1.0
    realized = float(prior_returns.dropna().std(ddof=0) * math.sqrt(365.0)) if len(prior_returns.dropna()) >= 5 else 0.0
    if realized <= 0.0:
        return 1.0
    return max(0.0, min(1.0, vol_target / realized))


def _walk_forward(prices: pd.DataFrame, lookback: int, top_k: int, rebalance_days: int, vol_target: float | None, cost_bps: float) -> dict[str, Any]:
    returns = prices.pct_change()
    weights = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    exposure = pd.Series(0.0, index=prices.index)
    last_weights = pd.Series(0.0, index=prices.columns)
    next_rebalance_idx = lookback
    idx = lookback
    while idx < len(prices) - 1:
        if idx >= next_rebalance_idx:
            score_row: dict[str, float] = {}
            for symbol in prices.columns:
                history = prices[symbol].dropna()
                if prices.index[idx] not in history.index:
                    continue
                current_pos = history.index.get_loc(prices.index[idx])
                if current_pos < lookback:
                    continue
                now = float(history.iloc[current_pos])
                before = float(history.iloc[current_pos - lookback])
                if before > 0:
                    score_row[symbol] = now / before - 1.0
            winners = [symbol for symbol, value in sorted(score_row.items(), key=lambda item: (-item[1], item[0])) if value > 0.0][:top_k]
            new_weights = pd.Series(0.0, index=prices.columns)
            if winners:
                selected_return = returns[winners].mean(axis=1).iloc[max(0, idx - 10) : idx]
                scale = _target_exposure(selected_return, vol_target)
                for symbol in winners:
                    new_weights[symbol] = scale / len(winners)
                exposure.iloc[idx : min(idx + rebalance_days, len(exposure))] = scale
            last_weights = new_weights
            next_rebalance_idx = idx + rebalance_days
        weights.iloc[idx] = last_weights
        idx += 1
    shifted = weights.shift(1).reindex(returns.index).fillna(0.0)
    turnover = shifted.diff().abs().sum(axis=1).fillna(shifted.abs().sum(axis=1))
    daily = (shifted * returns).sum(axis=1).fillna(0.0) - turnover * cost_bps / 10_000.0
    daily = daily.iloc[lookback + 1 :]
    turnover = turnover.reindex(daily.index).fillna(0.0)
    exposure = shifted.abs().sum(axis=1).reindex(daily.index).fillna(0.0)
    target_label = "none" if vol_target is None else str(vol_target).replace(".", "p")
    return _metrics(
        f"wf_l{lookback}_top{top_k}_reb{rebalance_days}_vol{target_label}",
        daily,
        turnover,
        exposure,
        {"lookback_days": lookback, "top_k": top_k, "rebalance_days": rebalance_days, "vol_target": vol_target, "cost_bps": cost_bps},
    )


def _decision(best: dict[str, Any]) -> dict[str, Any]:
    if best["total_return"] > 0.0 and best["sharpe"] > 0.0 and best["positive_segment_rate"] >= 0.50:
        return {
            "status": "carry_forward_oos_candidate",
            "reason": "Walk-forward variant has positive return, positive Sharpe, and at least 50% positive segments.",
            "next_action": "Run focused risk sizing on the OOS candidate only; keep paper/live/broker submit OFF.",
        }
    return {
        "status": "oos_failed",
        "reason": "No walk-forward variant cleared positive return, positive Sharpe, and positive-segment requirements.",
        "next_action": "Do not promote. Try a different signal family or wait for a materially new market snapshot.",
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bithumb KRW Short-Horizon Walk-Forward",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- markets: `{', '.join(payload['markets'])}`",
        f"- decision: `{payload['decision']['status']}`",
        f"- reason: {payload['decision']['reason']}",
        f"- annualization_warning: {payload['annualization_warning']}",
        "",
        "## Ranked Variants",
        "",
        "| variant | total return | MDD | Sharpe | pos seg | turnover | exposure |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["ranked_variants"][:15]:
        lines.append(
            "| {variant} | {total_return:.2%} | {mdd:.2%} | {sharpe:.2f} | {pos:.2%} | {turnover:.2f} | {exposure:.2f} |".format(
                variant=row["variant"],
                total_return=row["total_return"],
                mdd=row["mdd"],
                sharpe=row["sharpe"],
                pos=row["positive_segment_rate"],
                turnover=row["average_turnover"],
                exposure=row["average_exposure"],
            )
        )
    best = payload["best_walk_forward_candidate"]
    lines.extend(
        [
            "",
            "## Best Candidate",
            "",
            f"- variant: `{best['variant']}`",
            f"- total_return: `{best['total_return']:.2%}`",
            f"- MDD: `{best['mdd']:.2%}`",
            f"- Sharpe: `{best['sharpe']:.2f}`",
            f"- positive_segment_rate: `{best['positive_segment_rate']:.2%}`",
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
    variants = []
    for lookback in (3, 7, 14):
        for top_k in (1, 2):
            for rebalance_days in (7, 14):
                for vol_target in (None, 0.8, 1.2):
                    variants.append(_walk_forward(prices, lookback, top_k, rebalance_days, vol_target, cost_bps))
    ranked = sorted(variants, key=lambda row: (row["total_return"], row["sharpe"], row["positive_segment_rate"]), reverse=True)
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
            "mode": "research_only_walk_forward",
        },
        "markets": [str(column) for column in prices.columns],
        "date_start": prices.index.min().isoformat(),
        "date_end": prices.index.max().isoformat(),
        "cost_bps": cost_bps,
        "ranked_variants": ranked,
        "best_walk_forward_candidate": best,
        "decision": _decision(best),
        "annualization_warning": "Walk-forward windows are still short. CAGR is omitted from the markdown table; use total return, MDD, Sharpe, and positive segment rate.",
    }


def main() -> int:
    payload = build_payload()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = OUT_DIR / f"bithumb_krw_short_horizon_walk_forward_{stamp}.json"
    md_path = OUT_DIR / f"bithumb_krw_short_horizon_walk_forward_{stamp}.md"
    latest_json = OUT_DIR / "bithumb_krw_short_horizon_walk_forward_latest.json"
    latest_md = OUT_DIR / "bithumb_krw_short_horizon_walk_forward_latest.md"
    markdown = _render_markdown(payload)
    for path in (json_path, latest_json):
        _write_json(path, payload)
    for path in (md_path, latest_md):
        path.write_text(markdown, encoding="utf-8")
    best = payload["best_walk_forward_candidate"]
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
                "positive_segment_rate": best["positive_segment_rate"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
