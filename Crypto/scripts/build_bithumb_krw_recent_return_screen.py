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


def _load_market_frame(raw_path: str) -> pd.DataFrame:
    rows = _load_json(Path(raw_path))
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["candle_date_time_utc"], utc=True)
    frame = frame.sort_values("date").set_index("date")
    frame["close"] = frame["trade_price"].astype(float)
    return frame


def _window_return(close: pd.Series, days: int) -> float | None:
    if len(close) <= days:
        return None
    return float(close.iloc[-1] / close.iloc[-days - 1] - 1.0)


def _window_drawdown(close: pd.Series, days: int) -> float | None:
    if len(close) < 2:
        return None
    window = close.iloc[-min(days, len(close)) :]
    equity = window / float(window.iloc[0])
    return float((equity / equity.cummax() - 1.0).min())


def _window_vol(close: pd.Series, days: int) -> float | None:
    returns = close.pct_change().dropna().iloc[-days:]
    if len(returns) < 2:
        return None
    return float(returns.std(ddof=0) * math.sqrt(365.0))


def _score(row: dict[str, Any]) -> float:
    score = 0.0
    for key, weight in (("return_7d", 0.25), ("return_14d", 0.35), ("return_30d", 0.30), ("return_60d", 0.10)):
        value = row.get(key)
        if value is not None:
            score += float(value) * weight
    drawdown = row.get("drawdown_30d")
    if drawdown is not None:
        score += float(drawdown) * 0.20
    if row.get("fresh_listing_flag"):
        score += 0.03
    return score


def _build_rows() -> list[dict[str, Any]]:
    payload = _load_json(AVAILABILITY_PATH)
    markets = payload.get("markets") or []
    rows: list[dict[str, Any]] = []
    for market_row in markets:
        raw_path = market_row.get("raw_path")
        if not raw_path:
            continue
        frame = _load_market_frame(raw_path)
        close = frame["close"]
        row = {
            "market": market_row.get("market"),
            "symbol": market_row.get("symbol"),
            "english_name": market_row.get("english_name"),
            "available_rows": int(len(close)),
            "fresh_listing_flag": bool(len(close) < 180),
            "return_7d": _window_return(close, 7),
            "return_14d": _window_return(close, 14),
            "return_30d": _window_return(close, 30),
            "return_60d": _window_return(close, 60),
            "drawdown_30d": _window_drawdown(close, 30),
            "realized_vol_30d": _window_vol(close, 30),
            "latest_close": float(close.iloc[-1]),
            "latest_date": close.index.max().isoformat(),
        }
        row["score"] = _score(row)
        carry = (
            (row["return_14d"] is not None and row["return_14d"] > 0.05)
            or (row["return_30d"] is not None and row["return_30d"] > 0.10)
            or (row["fresh_listing_flag"] and row["return_7d"] is not None and row["return_7d"] > 0.03)
        )
        row["decision"] = "carry_forward_recent_return_axis" if carry else "do_not_prioritize"
        rows.append(row)
    return sorted(rows, key=lambda row: (row["decision"] != "carry_forward_recent_return_axis", -float(row["score"]), str(row["market"])))


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    carry = [row for row in rows if row["decision"] == "carry_forward_recent_return_axis"]
    killed = len(carry) == 0
    return {
        "checked_market_count": len(rows),
        "carry_forward_count": len(carry),
        "fresh_listing_count": sum(1 for row in rows if row["fresh_listing_flag"]),
        "top_candidates": carry[:10],
        "decision": "killed_axis" if killed else "carry_forward_recent_return_axis",
        "reason": (
            "No recent-return candidate met the carry-forward rule."
            if killed
            else "At least one high-liquidity market has enough recent return to justify a separate, bounded short-horizon research axis."
        ),
        "next_action": (
            "Do not retry this recent-return screen unless the market snapshot changes materially."
            if killed
            else "Run a bounded short-horizon return model only on the carry-forward markets; keep paper/live/broker submit OFF."
        ),
    }


def _fmt_pct(value: float | None) -> str:
    return "" if value is None else f"{value:.2%}"


def _render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Bithumb KRW Recent Return Screen",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- checked_market_count: `{summary['checked_market_count']}`",
        f"- carry_forward_count: `{summary['carry_forward_count']}`",
        f"- fresh_listing_count: `{summary['fresh_listing_count']}`",
        f"- decision: `{summary['decision']}`",
        f"- reason: {summary['reason']}",
        "",
        "## Top Candidates",
        "",
        "| market | rows | fresh | 7d | 14d | 30d | 30d DD | score |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["top_candidates"]:
        lines.append(
            f"| {row['market']} | {row['available_rows']} | {row['fresh_listing_flag']} | {_fmt_pct(row['return_7d'])} | {_fmt_pct(row['return_14d'])} | {_fmt_pct(row['return_30d'])} | {_fmt_pct(row['drawdown_30d'])} | {row['score']:.4f} |"
        )
    lines.extend(["", "## Next Action", "", f"- {summary['next_action']}"])
    return "\n".join(lines)


def build_payload() -> dict[str, Any]:
    rows = _build_rows()
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
            "mode": "research_only_screen",
        },
        "summary": _summary(rows),
        "markets": rows,
    }


def main() -> int:
    payload = build_payload()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = OUT_DIR / f"bithumb_krw_recent_return_screen_{stamp}.json"
    md_path = OUT_DIR / f"bithumb_krw_recent_return_screen_{stamp}.md"
    latest_json = OUT_DIR / "bithumb_krw_recent_return_screen_latest.json"
    latest_md = OUT_DIR / "bithumb_krw_recent_return_screen_latest.md"
    markdown = _render_markdown(payload)
    for path in (json_path, latest_json):
        _write_json(path, payload)
    for path in (md_path, latest_md):
        path.write_text(markdown, encoding="utf-8")
    print(
        json.dumps(
            {
                "json_path": str(json_path),
                "md_path": str(md_path),
                "decision": payload["summary"]["decision"],
                "carry_forward_count": payload["summary"]["carry_forward_count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
