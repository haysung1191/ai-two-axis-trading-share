from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


CRYPTO_ROOT = Path(r"C:\AI\Crypto")
ARCHIVE_ROOT = CRYPTO_ROOT / "data" / "bithumb_stage2_archive"
OUT_DIR = CRYPTO_ROOT / "analysis_results"
LIQUIDITY_PATH = OUT_DIR / "bithumb_krw_liquidity_screen_latest.json"
BASE_URL = "https://api.bithumb.com/v1"


def _stamp() -> str:
    return datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _fetch_candles(market: str, count: int) -> Any:
    url = BASE_URL + "/candles/days?" + urllib.parse.urlencode({"market": market, "count": count})
    request = urllib.request.Request(url, headers={"User-Agent": "codex-krw-candle-availability/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _selected_batch(limit: int | None, lanes: set[str]) -> list[dict[str, Any]]:
    payload = _load_json(LIQUIDITY_PATH)
    rows = payload.get("markets") or []
    batch = [row for row in rows if isinstance(row, dict) and row.get("lane") in lanes]
    batch = sorted(
        batch,
        key=lambda row: (
            row.get("lane") != "research_batch",
            -(float(row["acc_trade_price_24h"]) if row.get("acc_trade_price_24h") is not None else -1.0),
            str(row.get("market")),
        ),
    )
    return batch[:limit] if limit else batch


def _parse_lanes(value: str) -> set[str]:
    lanes = {part.strip() for part in value.split(",") if part.strip()}
    if "all" in lanes or "all_krw" in lanes:
        return {"research_batch", "watchlist", "low_liquidity"}
    return lanes or {"research_batch"}


def _date_value(row: dict[str, Any]) -> str | None:
    for key in ("candle_date_time_utc", "candle_date_time_kst"):
        value = row.get(key)
        if value:
            return str(value)
    return None


def _check_market(market_row: dict[str, Any], raw_dir: Path, count: int, min_rows: int) -> dict[str, Any]:
    market = str(market_row["market"])
    raw_path = raw_dir / "candles" / "1d" / f"{market}.json"
    try:
        payload = _fetch_candles(market, count=count)
        if isinstance(payload, list):
            _write_json(raw_path, payload)
            dates = [_date_value(row) for row in payload if isinstance(row, dict)]
            dates = [date for date in dates if date]
            status = "model_ready_1d" if len(payload) >= min_rows else "insufficient_history"
            return {
                "market": market,
                "symbol": market_row.get("symbol"),
                "english_name": market_row.get("english_name"),
                "status": status,
                "row_count": len(payload),
                "min_required_rows": min_rows,
                "earliest_candle": min(dates) if dates else None,
                "latest_candle": max(dates) if dates else None,
                "acc_trade_price_24h": market_row.get("acc_trade_price_24h"),
                "raw_path": str(raw_path),
                "error": None,
            }
        return {
            "market": market,
            "symbol": market_row.get("symbol"),
            "english_name": market_row.get("english_name"),
            "status": "fetch_error",
            "row_count": 0,
            "min_required_rows": min_rows,
            "earliest_candle": None,
            "latest_candle": None,
            "acc_trade_price_24h": market_row.get("acc_trade_price_24h"),
            "raw_path": None,
            "error": "non_list_response",
        }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "market": market,
            "symbol": market_row.get("symbol"),
            "english_name": market_row.get("english_name"),
            "status": "fetch_error",
            "row_count": 0,
            "min_required_rows": min_rows,
            "earliest_candle": None,
            "latest_candle": None,
            "acc_trade_price_24h": market_row.get("acc_trade_price_24h"),
            "raw_path": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _summary(rows: list[dict[str, Any]], *, selected_count: int, total_liquidity_markets: int, selected_lanes: set[str]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    ready = [row for row in rows if row["status"] == "model_ready_1d"]
    covers_full_bithumb_krw_universe = selected_count == total_liquidity_markets and total_liquidity_markets > 0
    return {
        "checked_market_count": len(rows),
        "selected_market_count": selected_count,
        "total_liquidity_market_count": total_liquidity_markets,
        "selected_lane_count": len(selected_lanes),
        "covers_full_bithumb_krw_universe": covers_full_bithumb_krw_universe,
        "coverage_ratio": round(selected_count / total_liquidity_markets, 6) if total_liquidity_markets else None,
        "model_ready_1d_count": len(ready),
        "insufficient_history_count": status_counts.get("insufficient_history", 0),
        "fetch_error_count": status_counts.get("fetch_error", 0),
        "status_counts": dict(sorted(status_counts.items())),
        "ready_markets": ready,
        "next_action": "Run the first bounded multi-asset 1d return-maximization baseline on model_ready_1d markets only; keep paper/live/broker submit OFF.",
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Bithumb KRW Candle Availability",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- checked_market_count: `{summary['checked_market_count']}`",
        f"- total_liquidity_market_count: `{summary['total_liquidity_market_count']}`",
        f"- covers_full_bithumb_krw_universe: `{summary['covers_full_bithumb_krw_universe']}`",
        f"- coverage_ratio: `{summary['coverage_ratio']}`",
        f"- model_ready_1d_count: `{summary['model_ready_1d_count']}`",
        f"- insufficient_history_count: `{summary['insufficient_history_count']}`",
        f"- fetch_error_count: `{summary['fetch_error_count']}`",
        "",
        "## Ready Markets",
        "",
        "| market | rows | earliest | latest | 24h KRW volume |",
        "| --- | ---: | --- | --- | ---: |",
    ]
    for row in summary["ready_markets"]:
        volume = row.get("acc_trade_price_24h")
        volume_text = f"{float(volume):,.0f}" if volume is not None else ""
        lines.append(f"| {row['market']} | {row['row_count']} | {row['earliest_candle']} | {row['latest_candle']} | {volume_text} |")
    lines.extend(["", "## Next Action", "", f"- {summary['next_action']}"])
    return "\n".join(lines)


def build_payload(limit: int | None, count: int, min_rows: int, sleep_seconds: float, lanes: set[str] | None = None) -> dict[str, Any]:
    selected_lanes = lanes or {"research_batch"}
    liquidity_payload = _load_json(LIQUIDITY_PATH)
    liquidity_rows = [row for row in liquidity_payload.get("markets") or [] if isinstance(row, dict)]
    batch = _selected_batch(limit, selected_lanes)
    raw_dir = ARCHIVE_ROOT / "raw" / _stamp()
    rows = []
    for market_row in batch:
        rows.append(_check_market(market_row, raw_dir=raw_dir, count=count, min_rows=min_rows))
        time.sleep(sleep_seconds)
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "sources": {
            "liquidity_screen": str(LIQUIDITY_PATH),
            "public_endpoint": f"{BASE_URL}/candles/days",
            "raw_dir": str(raw_dir),
        },
        "safety": {
            "private_api_used": False,
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
        },
        "params": {
            "selected_lanes": sorted(selected_lanes),
            "requested_candle_count": count,
            "min_required_rows": min_rows,
        },
        "summary": _summary(
            rows,
            selected_count=len(batch),
            total_liquidity_markets=len(liquidity_rows),
            selected_lanes=selected_lanes,
        ),
        "markets": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--min-rows", type=int, default=180)
    parser.add_argument("--sleep-seconds", type=float, default=0.15)
    parser.add_argument("--lanes", default="research_batch", help="Comma-separated lanes, or 'all' for every Bithumb KRW lane.")
    args = parser.parse_args()
    payload = build_payload(
        limit=args.limit,
        count=args.count,
        min_rows=args.min_rows,
        sleep_seconds=max(0.0, args.sleep_seconds),
        lanes=_parse_lanes(args.lanes),
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _stamp()
    json_path = OUT_DIR / f"bithumb_krw_candle_availability_{stamp}.json"
    md_path = OUT_DIR / f"bithumb_krw_candle_availability_{stamp}.md"
    latest_json = OUT_DIR / "bithumb_krw_candle_availability_latest.json"
    latest_md = OUT_DIR / "bithumb_krw_candle_availability_latest.md"
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
                "checked_market_count": payload["summary"]["checked_market_count"],
                "model_ready_1d_count": payload["summary"]["model_ready_1d_count"],
                "fetch_error_count": payload["summary"]["fetch_error_count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
