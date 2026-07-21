from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


AI_ROOT = Path(r"C:\AI")
CRYPTO_ROOT = AI_ROOT / "Crypto"
RAW_ROOT = CRYPTO_ROOT / "data" / "bithumb_stage2_archive" / "raw"
OUT_DIR = CRYPTO_ROOT / "analysis_results"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_file(name: str, min_size: int = 1) -> Path | None:
    if not RAW_ROOT.exists():
        return None
    files = [path for path in RAW_ROOT.glob(f"*\\{name}") if path.stat().st_size >= min_size]
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)


def _market_symbol(market: str) -> str:
    return market.split("-", 1)[1] if "-" in market else market


def _core_ticker_map(path: Path | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    rows = _load_json(path)
    if not isinstance(rows, list):
        return {}
    tickers: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict) and row.get("market"):
            tickers[str(row["market"])] = row
    return tickers


def _coverage_status(market: str, warning: str | None, ticker: dict[str, Any] | None) -> str:
    if warning not in {None, "", "NONE"}:
        return "excluded_warning"
    if market == "KRW-BTC":
        return "researched_btc_only"
    if ticker:
        return "core_liquidity_observed"
    return "needs_local_liquidity_snapshot"


def _build_rows(markets: list[dict[str, Any]], tickers: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for market_row in markets:
        market = str(market_row.get("market", ""))
        if not market.startswith("KRW-"):
            continue
        ticker = tickers.get(market)
        warning = market_row.get("market_warning")
        rows.append(
            {
                "market": market,
                "symbol": _market_symbol(market),
                "english_name": market_row.get("english_name"),
                "market_warning": warning,
                "status": _coverage_status(market, warning, ticker),
                "has_core_ticker_snapshot": bool(ticker),
                "acc_trade_price_24h": ticker.get("acc_trade_price_24h") if ticker else None,
                "trade_price": ticker.get("trade_price") if ticker else None,
                "signed_change_rate": ticker.get("signed_change_rate") if ticker else None,
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            row["status"] != "core_liquidity_observed",
            -(float(row["acc_trade_price_24h"]) if row["acc_trade_price_24h"] is not None else -1.0),
            row["market"],
        ),
    )


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    eligible = [row for row in rows if row["status"] != "excluded_warning"]
    observed = [row for row in rows if row["status"] == "core_liquidity_observed"]
    needs_snapshot = [row for row in rows if row["status"] == "needs_local_liquidity_snapshot"]
    return {
        "krw_market_count": len(rows),
        "eligible_non_warning_count": len(eligible),
        "warning_excluded_count": by_status.get("excluded_warning", 0),
        "btc_researched_count": by_status.get("researched_btc_only", 0),
        "core_liquidity_observed_count": len(observed),
        "needs_local_liquidity_snapshot_count": len(needs_snapshot),
        "status_counts": dict(sorted(by_status.items())),
        "top_core_liquidity_markets": observed[:10],
        "first_snapshot_backlog_markets": needs_snapshot[:30],
        "coverage_gap": "Current research scoreboard is BTC-only; most Bithumb KRW markets still need local liquidity/data-availability screening before model search.",
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Bithumb KRW Universe Inventory",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- market_source: `{payload['sources']['market_all']}`",
        f"- ticker_source: `{payload['sources']['ticker_core_markets']}`",
        "",
        "## Summary",
        "",
        f"- KRW markets: `{summary['krw_market_count']}`",
        f"- eligible non-warning markets: `{summary['eligible_non_warning_count']}`",
        f"- warning excluded: `{summary['warning_excluded_count']}`",
        f"- BTC researched: `{summary['btc_researched_count']}`",
        f"- core liquidity observed: `{summary['core_liquidity_observed_count']}`",
        f"- needs local liquidity snapshot: `{summary['needs_local_liquidity_snapshot_count']}`",
        f"- gap: {summary['coverage_gap']}",
        "",
        "## Top Core Liquidity Observed",
        "",
        "| market | 24h KRW volume | status |",
        "| --- | ---: | --- |",
    ]
    for row in summary["top_core_liquidity_markets"]:
        volume = row["acc_trade_price_24h"]
        volume_text = f"{float(volume):,.0f}" if volume is not None else ""
        lines.append(f"| {row['market']} | {volume_text} | {row['status']} |")
    lines.extend(
        [
            "",
            "## First Snapshot Backlog",
            "",
            ", ".join(row["market"] for row in summary["first_snapshot_backlog_markets"]) or "none",
            "",
            "## Next Frozen-Scope Experiment",
            "",
            "- Build a local data-availability and liquidity screen for all eligible KRW markets, then select a small multi-asset research batch. No paper/live/broker submit.",
        ]
    )
    return "\n".join(lines)


def build_payload() -> dict[str, Any]:
    market_path = _latest_file("market_all.json", min_size=1000)
    if not market_path:
        raise FileNotFoundError(f"No market_all.json found under {RAW_ROOT}")
    ticker_path = _latest_file("ticker_core_markets.json", min_size=100)
    markets = _load_json(market_path)
    if not isinstance(markets, list):
        raise TypeError(f"Expected list in {market_path}")
    rows = _build_rows(markets, _core_ticker_map(ticker_path))
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "sources": {
            "market_all": str(market_path),
            "ticker_core_markets": str(ticker_path) if ticker_path else None,
            "scoreboard_scope": "BTC 1d only",
            "scoreboard_path": str(OUT_DIR / "btc_1d_model_scoreboard_latest.json"),
        },
        "safety": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "mode": "read_only_inventory",
        },
        "summary": _summarize(rows),
        "markets": rows,
    }


def main() -> int:
    payload = build_payload()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = OUT_DIR / f"bithumb_krw_universe_inventory_{stamp}.json"
    md_path = OUT_DIR / f"bithumb_krw_universe_inventory_{stamp}.md"
    latest_json = OUT_DIR / "bithumb_krw_universe_inventory_latest.json"
    latest_md = OUT_DIR / "bithumb_krw_universe_inventory_latest.md"
    markdown = _render_markdown(payload)
    for path in (json_path, latest_json):
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    for path in (md_path, latest_md):
        path.write_text(markdown, encoding="utf-8")
    print(
        json.dumps(
            {
                "json_path": str(json_path),
                "md_path": str(md_path),
                "krw_market_count": payload["summary"]["krw_market_count"],
                "eligible_non_warning_count": payload["summary"]["eligible_non_warning_count"],
                "needs_local_liquidity_snapshot_count": payload["summary"]["needs_local_liquidity_snapshot_count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
