from __future__ import annotations

import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd


CRYPTO_ROOT = Path(r"C:\AI\Crypto")
AI_ROOT = CRYPTO_ROOT.parent
OUT_DIR = CRYPTO_ROOT / "analysis_results"
CANDLE_AVAILABILITY_PATH = OUT_DIR / "bithumb_krw_candle_availability_latest.json"

if str(CRYPTO_ROOT) not in sys.path:
    sys.path.insert(0, str(CRYPTO_ROOT))

from app.domains.strategy.krw_low_vol_breakout import compute_low_vol_breakout_signal_map
from app.domains.strategy.krw_relative_strength_rotation import compute_rotation_signal_map
from app.domains.strategy.krw_trend_pullback_reaccel import compute_trend_pullback_reaccel_signal_map
from app.domains.strategy.krw_volume_surge_breakout import compute_volume_breakout_signal_map


SignalBuilder = Callable[[pd.DataFrame, dict[str, pd.DataFrame]], dict[str, pd.Series]]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_ohlcv(raw_path: str, market: str) -> pd.DataFrame:
    rows = _load_json(Path(raw_path))
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError(f"{market} candle file is empty")
    frame["date"] = pd.to_datetime(frame["candle_date_time_utc"], utc=True)
    frame = frame.sort_values("date").set_index("date")
    return pd.DataFrame(
        {
            "open": frame["opening_price"].astype(float),
            "high": frame["high_price"].astype(float),
            "low": frame["low_price"].astype(float),
            "close": frame["trade_price"].astype(float),
            "volume": frame["candle_acc_trade_volume"].astype(float),
        },
        index=frame.index,
    )


def _ready_frames() -> tuple[pd.DataFrame, dict[str, pd.DataFrame], list[str]]:
    payload = _load_json(CANDLE_AVAILABILITY_PATH)
    ready = payload.get("summary", {}).get("ready_markets", [])
    frames: dict[str, pd.DataFrame] = {}
    for row in ready:
        if not isinstance(row, dict) or row.get("status") != "model_ready_1d":
            continue
        market = str(row.get("market"))
        raw_path = row.get("raw_path")
        if not raw_path:
            continue
        frames[market] = _load_ohlcv(str(raw_path), market)
    if "KRW-BTC" not in frames:
        raise RuntimeError("KRW-BTC is required for BTC regime filter")
    alt_frames = {market: frame for market, frame in frames.items() if market != "KRW-BTC" and market != "KRW-USDT"}
    if len(alt_frames) < 3:
        raise RuntimeError("Need at least 3 non-BTC/non-USDT model-ready markets")
    return frames["KRW-BTC"], alt_frames, sorted(frames)


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
    total_return = float(equity.iloc[-1] - 1.0) if len(equity) else 0.0
    cagr = float(equity.iloc[-1] ** (365.0 / days) - 1.0) if len(equity) else 0.0
    sharpe = float(daily_returns.mean() / std * math.sqrt(365.0)) if std else 0.0
    return {
        "variant": name,
        "params": params,
        "days": days,
        "total_return": total_return,
        "cagr": cagr,
        "mdd": _max_drawdown(equity),
        "sharpe": sharpe,
        "annualized_volatility": float(std * math.sqrt(365.0)),
        "average_daily_turnover": float(turnover.reindex(daily_returns.index).fillna(0.0).mean()) if len(turnover) else 0.0,
        "active_day_ratio": active_day_ratio,
        "final_equity": float(equity.iloc[-1]) if len(equity) else 1.0,
    }


def _evaluate_signal_map(
    name: str,
    signal_map: dict[str, pd.Series],
    alt_frames: dict[str, pd.DataFrame],
    *,
    cost_bps: float,
    params: dict[str, Any],
) -> dict[str, Any]:
    close = pd.concat({market: frame["close"].astype(float) for market, frame in alt_frames.items()}, axis=1).dropna(how="any")
    signals = pd.concat(signal_map, axis=1).reindex(close.index).fillna(0.0)
    row_sums = signals.sum(axis=1).replace(0.0, pd.NA)
    weights = signals.div(row_sums, axis=0).infer_objects(copy=False).fillna(0.0)
    returns = close.pct_change().fillna(0.0)
    shifted = weights.shift(1).fillna(0.0)
    turnover = shifted.diff().abs().sum(axis=1).fillna(shifted.abs().sum(axis=1))
    daily = (shifted * returns).sum(axis=1) - turnover * cost_bps / 10_000.0
    daily = daily.iloc[1:]
    turnover = turnover.reindex(daily.index).fillna(0.0)
    metrics = _metrics(name, daily, turnover, {**params, "cost_bps": cost_bps})
    selected_counts = {market: int((signals[market] > 0.0).sum()) for market in signals.columns}
    metrics["selected_day_counts"] = selected_counts
    metrics["signal_day_count"] = int((signals.sum(axis=1) > 0.0).sum())
    return metrics


def _variant_builders() -> list[tuple[str, SignalBuilder, dict[str, Any]]]:
    return [
        (
            "volume_surge_breakout_v1",
            lambda btc, alts: compute_volume_breakout_signal_map(
                btc,
                alts,
                ema_window=72,
                volume_lookback=24,
                volume_surge_threshold=1.5,
                breakout_window=10,
                top_k=2,
            ),
            {"family": "volume_surge_breakout", "ema_window": 72, "volume_lookback": 24, "volume_surge_threshold": 1.5, "breakout_window": 10, "top_k": 2},
        ),
        (
            "low_vol_breakout_v1",
            lambda btc, alts: compute_low_vol_breakout_signal_map(
                btc,
                alts,
                btc_ema_window=72,
                atr_window=14,
                contraction_history_window=45,
                breakout_window=10,
                volume_window=14,
                top_k=2,
            ),
            {"family": "low_vol_breakout", "btc_ema_window": 72, "atr_window": 14, "contraction_history_window": 45, "breakout_window": 10, "volume_window": 14, "top_k": 2},
        ),
        (
            "trend_pullback_reaccel_v1",
            lambda btc, alts: compute_trend_pullback_reaccel_signal_map(
                btc,
                alts,
                btc_ema_window=72,
                fast_ema_window=14,
                slow_ema_window=55,
                pullback_window=5,
                breakout_window=3,
                return_lookback=10,
                atr_window=14,
                top_k=2,
            ),
            {"family": "trend_pullback_reaccel", "btc_ema_window": 72, "fast_ema_window": 14, "slow_ema_window": 55, "pullback_window": 5, "breakout_window": 3, "return_lookback": 10, "atr_window": 14, "top_k": 2},
        ),
        (
            "relative_strength_rotation_v1",
            lambda btc, alts: compute_rotation_signal_map(
                btc,
                alts,
                ema_window=72,
                lookback=14,
                atr_window=14,
                top_k=2,
            ),
            {"family": "relative_strength_rotation", "ema_window": 72, "lookback": 14, "atr_window": 14, "top_k": 2},
        ),
    ]


def _decision(best: dict[str, Any]) -> dict[str, Any]:
    if best["total_return"] > 0.0 and best["sharpe"] > 0.0 and best["signal_day_count"] >= 5:
        return {
            "status": "carry_forward_new_signal_family",
            "reason": "A non-short-horizon-momentum signal family produced positive return-side metrics with enough signal days for validation.",
            "next_action": "Run a frozen-scope walk-forward validation for this family only; keep paper/live/broker submit OFF.",
        }
    return {
        "status": "killed_axis",
        "reason": "The bounded breakout/rotation family screen did not produce a positive and sufficiently active return-side candidate.",
        "next_action": "Record the axis as killed unless a materially new Bithumb snapshot or a different hypothesis is used.",
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bithumb KRW Signal Family Breakout Screen",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- scope_id: `{payload['scope']['scope_id']}`",
        f"- market_count: `{payload['market_count']}`",
        f"- safety: `{payload['safety']}`",
        f"- decision: `{payload['decision']['status']}`",
        f"- reason: {payload['decision']['reason']}",
        "",
        "## Ranked Variants",
        "",
        "| variant | family | total return | CAGR | MDD | Sharpe | active | signal days | turnover |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["ranked_variants"]:
        lines.append(
            "| {variant} | {family} | {total_return:.2%} | {cagr:.2%} | {mdd:.2%} | {sharpe:.2f} | {active:.2f} | {signal_days} | {turnover:.2f} |".format(
                variant=row["variant"],
                family=row["params"]["family"],
                total_return=row["total_return"],
                cagr=row["cagr"],
                mdd=row["mdd"],
                sharpe=row["sharpe"],
                active=row["active_day_ratio"],
                signal_days=row["signal_day_count"],
                turnover=row["average_daily_turnover"],
            )
        )
    best = payload["best_return_candidate"]
    lines.extend(
        [
            "",
            "## Best Candidate",
            "",
            f"- variant: `{best['variant']}`",
            f"- family: `{best['params']['family']}`",
            f"- total_return: `{best['total_return']:.2%}`",
            f"- CAGR: `{best['cagr']:.2%}`",
            f"- MDD: `{best['mdd']:.2%}`",
            f"- Sharpe: `{best['sharpe']:.2f}`",
            f"- signal_day_count: `{best['signal_day_count']}`",
            "",
            "## Next Action",
            "",
            f"- {payload['decision']['next_action']}",
        ]
    )
    return "\n".join(lines)


def build_payload() -> dict[str, Any]:
    btc_frame, alt_frames, all_markets = _ready_frames()
    cost_bps = 20.0
    variants: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for name, builder, params in _variant_builders():
        try:
            signal_map = builder(btc_frame, alt_frames)
            variants.append(_evaluate_signal_map(name, signal_map, alt_frames, cost_bps=cost_bps, params=params))
        except Exception as exc:
            errors.append({"variant": name, "error": str(exc)})
    if not variants:
        raise RuntimeError(f"No signal-family variants completed: {errors}")
    ranked = sorted(variants, key=lambda row: (row["total_return"], row["sharpe"], -abs(row["mdd"])), reverse=True)
    best = ranked[0]
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "scope": {
            "scope_id": "HOLIDAY-20260501-010",
            "lane": "research",
            "hypothesis": "A non-short-horizon-momentum Bithumb KRW signal family can preserve return-side upside on the current public 1d research batch.",
            "frozen_inputs": {
                "candle_availability": str(CANDLE_AVAILABILITY_PATH),
                "market_universe_rule": "model_ready_1d markets from the latest saved public candle availability; BTC used only as regime filter; USDT excluded from tradable alts",
            },
            "promotion_allowed": False,
        },
        "sources": {
            "candle_availability": str(CANDLE_AVAILABILITY_PATH),
            "strategy_modules": [
                "krw_volume_surge_breakout",
                "krw_low_vol_breakout",
                "krw_trend_pullback_reaccel",
                "krw_relative_strength_rotation",
            ],
        },
        "safety": {
            "private_api_used": False,
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "mode": "research_only_backtest",
        },
        "market_count": len(all_markets),
        "markets": all_markets,
        "tradable_alt_markets": sorted(alt_frames),
        "cost_bps": cost_bps,
        "ranked_variants": ranked,
        "best_return_candidate": best,
        "decision": _decision(best),
        "errors": errors,
        "interpretation": "Frozen-scope return-side screen only. Positive output is not paper/live readiness and requires separate OOS/walk-forward validation.",
    }


def main() -> int:
    payload = build_payload()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = OUT_DIR / f"bithumb_krw_signal_family_breakout_screen_{stamp}.json"
    md_path = OUT_DIR / f"bithumb_krw_signal_family_breakout_screen_{stamp}.md"
    latest_json = OUT_DIR / "bithumb_krw_signal_family_breakout_screen_latest.json"
    latest_md = OUT_DIR / "bithumb_krw_signal_family_breakout_screen_latest.md"
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
                "best_total_return": best["total_return"],
                "best_cagr": best["cagr"],
                "best_mdd": best["mdd"],
                "best_sharpe": best["sharpe"],
                "signal_day_count": best["signal_day_count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
