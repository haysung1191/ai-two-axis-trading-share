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


AI_ROOT = Path(r"C:\AI")
CRYPTO_ROOT = AI_ROOT / "Crypto"
ARCHIVE_ROOT = CRYPTO_ROOT / "data" / "bithumb_stage2_archive"
OUT_DIR = CRYPTO_ROOT / "analysis_results"
INVENTORY_PATH = OUT_DIR / "bithumb_krw_universe_inventory_latest.json"
BASE_URL = "https://api.bithumb.com/v1"


def _stamp() -> str:
    return datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[idx : idx + size] for idx in range(0, len(items), size)]


def _fetch_json(path: str, params: dict[str, Any]) -> Any:
    url = BASE_URL + path + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "codex-krw-liquidity-screen/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _eligible_markets(inventory: dict[str, Any], limit: int | None = None) -> list[dict[str, Any]]:
    rows = inventory.get("markets") or []
    eligible = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("market")
        and row.get("status") != "excluded_warning"
    ]
    eligible = sorted(eligible, key=lambda row: str(row["market"]))
    return eligible[:limit] if limit else eligible


def _fetch_tickers(markets: list[str], chunk_size: int, sleep_seconds: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for chunk in _chunks(markets, chunk_size):
        try:
            payload = _fetch_json("/ticker", {"markets": ",".join(chunk)})
            if isinstance(payload, list):
                rows.extend(row for row in payload if isinstance(row, dict))
            else:
                errors.append({"markets": chunk, "error": "non_list_response"})
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append({"markets": chunk, "error": f"{type(exc).__name__}: {exc}"})
        time.sleep(sleep_seconds)
    return rows, errors


def _rank_rows(markets: list[dict[str, Any]], tickers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    market_meta = {str(row["market"]): row for row in markets}
    ticker_map = {str(row.get("market")): row for row in tickers if row.get("market")}
    ranked: list[dict[str, Any]] = []
    for market, meta in market_meta.items():
        ticker = ticker_map.get(market)
        volume_24h = ticker.get("acc_trade_price_24h") if ticker else None
        trade_price = ticker.get("trade_price") if ticker else None
        signed_change_rate = ticker.get("signed_change_rate") if ticker else None
        if volume_24h is None:
            lane = "missing_ticker"
        elif float(volume_24h) >= 10_000_000_000:
            lane = "research_batch"
        elif float(volume_24h) >= 1_000_000_000:
            lane = "watchlist"
        else:
            lane = "low_liquidity"
        ranked.append(
            {
                "market": market,
                "symbol": meta.get("symbol"),
                "english_name": meta.get("english_name"),
                "lane": lane,
                "acc_trade_price_24h": volume_24h,
                "trade_price": trade_price,
                "signed_change_rate": signed_change_rate,
                "inventory_status": meta.get("status"),
            }
        )
    return sorted(
        ranked,
        key=lambda row: (
            row["lane"] not in {"research_batch", "watchlist"},
            -(float(row["acc_trade_price_24h"]) if row["acc_trade_price_24h"] is not None else -1.0),
            row["market"],
        ),
    )


def _summary(ranked: list[dict[str, Any]], fetch_errors: list[dict[str, Any]], requested_count: int) -> dict[str, Any]:
    lane_counts: dict[str, int] = {}
    for row in ranked:
        lane_counts[row["lane"]] = lane_counts.get(row["lane"], 0) + 1
    fetched_count = sum(1 for row in ranked if row["lane"] != "missing_ticker")
    research = [row for row in ranked if row["lane"] == "research_batch"]
    watchlist = [row for row in ranked if row["lane"] == "watchlist"]
    return {
        "requested_market_count": requested_count,
        "fetched_market_count": fetched_count,
        "missing_ticker_count": lane_counts.get("missing_ticker", 0),
        "fetch_error_count": len(fetch_errors),
        "public_ticker_fetch_success_rate": round(fetched_count / requested_count, 4) if requested_count else 0.0,
        "lane_counts": dict(sorted(lane_counts.items())),
        "research_batch_count": len(research),
        "watchlist_count": len(watchlist),
        "low_liquidity_count": lane_counts.get("low_liquidity", 0),
        "top_research_batch": research[:30],
        "top_watchlist": watchlist[:30],
        "next_action": "Run a bounded candle-history availability screen for the top research_batch markets before any multi-asset strategy search.",
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Bithumb KRW Liquidity Screen",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- mode: `{payload['mode']}`",
        f"- requested_market_count: `{summary['requested_market_count']}`",
        f"- fetched_market_count: `{summary['fetched_market_count']}`",
        f"- public_ticker_fetch_success_rate: `{summary['public_ticker_fetch_success_rate']}`",
        f"- research_batch_count: `{summary['research_batch_count']}`",
        f"- watchlist_count: `{summary['watchlist_count']}`",
        f"- low_liquidity_count: `{summary['low_liquidity_count']}`",
        f"- missing_ticker_count: `{summary['missing_ticker_count']}`",
        "",
        "## Top Research Batch",
        "",
        "| market | 24h KRW volume | change | lane |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in summary["top_research_batch"]:
        volume = row["acc_trade_price_24h"]
        volume_text = f"{float(volume):,.0f}" if volume is not None else ""
        change = row["signed_change_rate"]
        change_text = f"{float(change):.4f}" if change is not None else ""
        lines.append(f"| {row['market']} | {volume_text} | {change_text} | {row['lane']} |")
    lines.extend(
        [
            "",
            "## Top Watchlist",
            "",
            "| market | 24h KRW volume | change | lane |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for row in summary["top_watchlist"][:15]:
        volume = row["acc_trade_price_24h"]
        volume_text = f"{float(volume):,.0f}" if volume is not None else ""
        change = row["signed_change_rate"]
        change_text = f"{float(change):.4f}" if change is not None else ""
        lines.append(f"| {row['market']} | {volume_text} | {change_text} | {row['lane']} |")
    lines.extend(["", "## Next Action", "", f"- {summary['next_action']}"])
    return "\n".join(lines)


def build_payload(limit: int | None, chunk_size: int, sleep_seconds: float, offline: bool) -> dict[str, Any]:
    inventory = _load_json(INVENTORY_PATH)
    markets = _eligible_markets(inventory, limit=limit)
    market_codes = [str(row["market"]) for row in markets]
    fetch_errors: list[dict[str, Any]] = []
    if offline:
        tickers = [
            row
            for row in markets
            if row.get("has_core_ticker_snapshot")
            for _ in [None]
        ]
        mode = "offline_inventory_snapshot"
    else:
        tickers, fetch_errors = _fetch_tickers(market_codes, chunk_size=chunk_size, sleep_seconds=sleep_seconds)
        mode = "public_ticker_screen"
        raw_dir = ARCHIVE_ROOT / "raw" / _stamp()
        _write_json(raw_dir / "ticker_all_krw_screen.json", tickers)
    ranked = _rank_rows(markets, tickers)
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "mode": mode,
        "sources": {
            "inventory": str(INVENTORY_PATH),
            "public_endpoint": None if offline else f"{BASE_URL}/ticker",
        },
        "safety": {
            "private_api_used": False,
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
        },
        "fetch_errors": fetch_errors,
        "summary": _summary(ranked, fetch_errors, requested_count=len(markets)),
        "markets": ranked,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--chunk-size", type=int, default=80)
    parser.add_argument("--sleep-seconds", type=float, default=0.15)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    payload = build_payload(
        limit=args.limit,
        chunk_size=max(1, args.chunk_size),
        sleep_seconds=max(0.0, args.sleep_seconds),
        offline=args.offline,
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _stamp()
    json_path = OUT_DIR / f"bithumb_krw_liquidity_screen_{stamp}.json"
    md_path = OUT_DIR / f"bithumb_krw_liquidity_screen_{stamp}.md"
    latest_json = OUT_DIR / "bithumb_krw_liquidity_screen_latest.json"
    latest_md = OUT_DIR / "bithumb_krw_liquidity_screen_latest.md"
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
                "requested_market_count": payload["summary"]["requested_market_count"],
                "fetched_market_count": payload["summary"]["fetched_market_count"],
                "research_batch_count": payload["summary"]["research_batch_count"],
                "fetch_error_count": payload["summary"]["fetch_error_count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
