from __future__ import annotations

import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


CRYPTO_ROOT = Path(r"C:\AI\Crypto")
OUT_DIR = CRYPTO_ROOT / "analysis_results"
CANDLE_AVAILABILITY_PATH = OUT_DIR / "bithumb_krw_candle_availability_latest.json"
SIGNAL_SCREEN_PATH = OUT_DIR / "bithumb_krw_signal_family_breakout_screen_latest.json"

if str(CRYPTO_ROOT) not in sys.path:
    sys.path.insert(0, str(CRYPTO_ROOT))

from app.domains.strategy.krw_relative_strength_rotation import compute_rotation_signal_map


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
        if raw_path:
            frames[market] = _load_ohlcv(str(raw_path), market)
    if "KRW-BTC" not in frames:
        raise RuntimeError("KRW-BTC is required for the regime filter")
    alt_frames = {market: frame for market, frame in frames.items() if market not in {"KRW-BTC", "KRW-USDT"}}
    if len(alt_frames) < 3:
        raise RuntimeError("Need at least 3 non-BTC/non-USDT model-ready markets")
    return frames["KRW-BTC"], alt_frames, sorted(frames)


def _max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    return float((equity / equity.cummax() - 1.0).min())


def _segment_metrics(daily: pd.Series, segment_days: int) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for offset, start in enumerate(range(0, len(daily), segment_days), start=1):
        segment = daily.iloc[start : start + segment_days]
        if segment.empty:
            continue
        equity = (1.0 + segment).cumprod()
        total_return = float(equity.iloc[-1] - 1.0)
        std = float(segment.std(ddof=0))
        segments.append(
            {
                "segment": offset,
                "date_start": segment.index.min().isoformat(),
                "date_end": segment.index.max().isoformat(),
                "days": int(len(segment)),
                "total_return": total_return,
                "mdd": _max_drawdown(equity),
                "sharpe": float(segment.mean() / std * math.sqrt(365.0)) if std else 0.0,
            }
        )
    return segments


def _evaluate_rotation(
    btc_frame: pd.DataFrame,
    alt_frames: dict[str, pd.DataFrame],
    *,
    ema_window: int,
    lookback: int,
    atr_window: int,
    top_k: int,
    cost_bps: float,
    segment_days: int,
) -> dict[str, Any]:
    signal_map = compute_rotation_signal_map(
        btc_frame,
        alt_frames,
        ema_window=ema_window,
        lookback=lookback,
        atr_window=atr_window,
        top_k=top_k,
    )
    close = pd.concat({market: frame["close"].astype(float) for market, frame in alt_frames.items()}, axis=1).dropna(how="any")
    signals = pd.concat(signal_map, axis=1).reindex(close.index).fillna(0.0)
    row_sums = signals.sum(axis=1).replace(0.0, pd.NA)
    weights = signals.div(row_sums, axis=0).infer_objects(copy=False).fillna(0.0)
    returns = close.pct_change().fillna(0.0)
    shifted = weights.shift(1).fillna(0.0)
    turnover = shifted.diff().abs().sum(axis=1).fillna(shifted.abs().sum(axis=1))
    daily = (shifted * returns).sum(axis=1) - turnover * cost_bps / 10_000.0
    daily = daily.iloc[1:].dropna()
    equity = (1.0 + daily).cumprod()
    std = float(daily.std(ddof=0)) if len(daily) else 0.0
    segments = _segment_metrics(daily, segment_days)
    positive_segments = [row for row in segments if row["total_return"] > 0.0]
    selected_counts = {market: int((signals[market] > 0.0).sum()) for market in signals.columns}
    days = max(1, len(daily))
    return {
        "variant": "relative_strength_rotation_v1",
        "params": {
            "family": "relative_strength_rotation",
            "ema_window": ema_window,
            "lookback": lookback,
            "atr_window": atr_window,
            "top_k": top_k,
            "cost_bps": cost_bps,
            "segment_days": segment_days,
        },
        "days": days,
        "date_start": daily.index.min().isoformat() if len(daily) else None,
        "date_end": daily.index.max().isoformat() if len(daily) else None,
        "total_return": float(equity.iloc[-1] - 1.0) if len(equity) else 0.0,
        "cagr": float(equity.iloc[-1] ** (365.0 / days) - 1.0) if len(equity) else 0.0,
        "mdd": _max_drawdown(equity),
        "sharpe": float(daily.mean() / std * math.sqrt(365.0)) if std else 0.0,
        "annualized_volatility": float(std * math.sqrt(365.0)),
        "average_daily_turnover": float(turnover.reindex(daily.index).fillna(0.0).mean()) if len(turnover) else 0.0,
        "active_day_ratio": float((signals.sum(axis=1).reindex(daily.index).fillna(0.0) > 0.0).mean()) if len(daily) else 0.0,
        "signal_day_count": int((signals.sum(axis=1) > 0.0).sum()),
        "selected_day_counts": selected_counts,
        "walk_forward_segments": len(segments),
        "positive_segment_count": len(positive_segments),
        "positive_segment_rate": float(len(positive_segments) / len(segments)) if segments else 0.0,
        "segment_returns": segments,
        "final_equity": float(equity.iloc[-1]) if len(equity) else 1.0,
    }


def _decision(candidate: dict[str, Any]) -> dict[str, str]:
    if (
        candidate["total_return"] > 0.0
        and candidate["sharpe"] > 0.0
        and candidate["positive_segment_rate"] >= 0.50
        and candidate["mdd"] >= -0.25
    ):
        return {
            "status": "carry_forward_signal_family_oos_candidate",
            "reason": "The carried-forward signal family retained positive return, positive Sharpe, acceptable MDD, and at least 50% positive validation segments.",
            "next_action": "Run focused risk-sizing/compression on this signal-family candidate only; keep paper/live/broker submit OFF.",
        }
    return {
        "status": "signal_family_oos_failed",
        "reason": "The carried-forward signal family did not clear the bounded OOS-style segment robustness gate.",
        "next_action": "Do not promote. Try a materially different Bithumb signal family or wait for a new market snapshot.",
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    candidate = payload["candidate"]
    lines = [
        "# Bithumb KRW Signal Family Walk-Forward",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- scope_id: `{payload['scope']['scope_id']}`",
        f"- variant: `{candidate['variant']}`",
        f"- decision: `{payload['decision']['status']}`",
        f"- reason: {payload['decision']['reason']}",
        f"- safety: `{payload['safety']}`",
        "",
        "## Candidate Metrics",
        "",
        f"- total_return: `{candidate['total_return']:.2%}`",
        f"- CAGR: `{candidate['cagr']:.2%}`",
        f"- MDD: `{candidate['mdd']:.2%}`",
        f"- Sharpe: `{candidate['sharpe']:.2f}`",
        f"- positive_segment_rate: `{candidate['positive_segment_rate']:.2%}`",
        f"- signal_day_count: `{candidate['signal_day_count']}`",
        "",
        "## Segments",
        "",
        "| segment | start | end | days | return | MDD | Sharpe |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in candidate["segment_returns"]:
        lines.append(
            "| {segment} | {start} | {end} | {days} | {ret:.2%} | {mdd:.2%} | {sharpe:.2f} |".format(
                segment=row["segment"],
                start=row["date_start"][:10],
                end=row["date_end"][:10],
                days=row["days"],
                ret=row["total_return"],
                mdd=row["mdd"],
                sharpe=row["sharpe"],
            )
        )
    lines.extend(["", "## Next Action", "", f"- {payload['decision']['next_action']}"])
    return "\n".join(lines)


def build_payload() -> dict[str, Any]:
    screen = _load_json(SIGNAL_SCREEN_PATH)
    best = screen.get("best_return_candidate") or {}
    if best.get("variant") != "relative_strength_rotation_v1":
        raise RuntimeError("Latest signal-family candidate is not relative_strength_rotation_v1")
    params = best.get("params") or {}
    btc_frame, alt_frames, all_markets = _ready_frames()
    candidate = _evaluate_rotation(
        btc_frame,
        alt_frames,
        ema_window=int(params.get("ema_window", 72)),
        lookback=int(params.get("lookback", 14)),
        atr_window=int(params.get("atr_window", 14)),
        top_k=int(params.get("top_k", 2)),
        cost_bps=20.0,
        segment_days=28,
    )
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "scope": {
            "scope_id": "HOLIDAY-20260501-011",
            "lane": "research_validation",
            "hypothesis": "The carried-forward Bithumb KRW relative-strength rotation family can retain return-side value across rolling validation segments.",
            "promotion_allowed": False,
            "frozen_inputs": {
                "signal_family_screen": str(SIGNAL_SCREEN_PATH),
                "candle_availability": str(CANDLE_AVAILABILITY_PATH),
            },
        },
        "sources": {
            "signal_family_screen": str(SIGNAL_SCREEN_PATH),
            "candle_availability": str(CANDLE_AVAILABILITY_PATH),
            "strategy_module": "krw_relative_strength_rotation",
        },
        "safety": {
            "private_api_used": False,
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "mode": "research_only_walk_forward",
        },
        "market_count": len(all_markets),
        "markets": all_markets,
        "tradable_alt_markets": sorted(alt_frames),
        "candidate": candidate,
        "decision": _decision(candidate),
        "interpretation": "Validation-only result. Passing this report is not paper/live readiness and does not permit promotion without separate gates.",
    }


def main() -> int:
    payload = build_payload()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = OUT_DIR / f"bithumb_krw_signal_family_walk_forward_{stamp}.json"
    md_path = OUT_DIR / f"bithumb_krw_signal_family_walk_forward_{stamp}.md"
    latest_json = OUT_DIR / "bithumb_krw_signal_family_walk_forward_latest.json"
    latest_md = OUT_DIR / "bithumb_krw_signal_family_walk_forward_latest.md"
    markdown = _render_markdown(payload)
    for path in (json_path, latest_json):
        _write_json(path, payload)
    for path in (md_path, latest_md):
        path.write_text(markdown, encoding="utf-8")
    candidate = payload["candidate"]
    print(
        json.dumps(
            {
                "json_path": str(json_path),
                "md_path": str(md_path),
                "decision": payload["decision"]["status"],
                "variant": candidate["variant"],
                "total_return": candidate["total_return"],
                "cagr": candidate["cagr"],
                "mdd": candidate["mdd"],
                "sharpe": candidate["sharpe"],
                "positive_segment_rate": candidate["positive_segment_rate"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
