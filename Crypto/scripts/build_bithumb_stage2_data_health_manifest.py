from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\AI\Crypto")
ARCHIVE_ROOT = ROOT / "data" / "bithumb_stage2_archive"
REPORT_ROOT = ROOT / "analysis_results"
BASE_URL = "https://api.bithumb.com/v1"

CORE_MARKETS = ["KRW-BTC", "KRW-ETH"]
TIMEFRAMES = {
    "1d": "/candles/days",
    "4h": "/candles/minutes/240",
    "1h": "/candles/minutes/60",
}


def utc_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def stamp() -> str:
    return datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")


def fetch_json(path: str, params: dict[str, Any] | None = None) -> tuple[Any | None, str | None]:
    url = BASE_URL + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "codex-stage2-data-health/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw), None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def row_count(payload: Any) -> int:
    return len(payload) if isinstance(payload, list) else 0


def build_manifest() -> dict[str, Any]:
    run_stamp = stamp()
    raw_dir = ARCHIVE_ROOT / "raw" / run_stamp
    market_payload, market_error = fetch_json("/market/all", {"isDetails": "true"})
    if market_payload is not None:
        write_json(raw_dir / "market_all.json", market_payload)

    markets_by_code = {
        row.get("market"): row
        for row in market_payload or []
        if isinstance(row, dict) and isinstance(row.get("market"), str)
    }
    target_markets = [market for market in CORE_MARKETS if market in markets_by_code or market_error]
    if not target_markets:
        target_markets = CORE_MARKETS

    candle_checks: list[dict[str, Any]] = []
    for market in target_markets:
        for timeframe, path in TIMEFRAMES.items():
            payload, error = fetch_json(path, {"market": market, "count": 2})
            raw_path = raw_dir / "candles" / timeframe / f"{market}.json"
            if payload is not None:
                write_json(raw_path, payload)
            candle_checks.append(
                {
                    "market": market,
                    "timeframe": timeframe,
                    "endpoint": path,
                    "raw_path": str(raw_path) if payload is not None else None,
                    "row_count": row_count(payload),
                    "ok": payload is not None and row_count(payload) > 0,
                    "error": error,
                }
            )
            time.sleep(0.12)

    orderbook_checks: list[dict[str, Any]] = []
    if target_markets:
        payload, error = fetch_json("/orderbook", {"markets": ",".join(target_markets)})
        raw_path = raw_dir / "orderbook_core_markets.json"
        if payload is not None:
            write_json(raw_path, payload)
        orderbook_checks.append(
            {
                "markets": target_markets,
                "endpoint": "/orderbook",
                "raw_path": str(raw_path) if payload is not None else None,
                "row_count": row_count(payload),
                "ok": payload is not None and row_count(payload) > 0,
                "error": error,
            }
        )

    ticker_checks: list[dict[str, Any]] = []
    if target_markets:
        payload, error = fetch_json("/ticker", {"markets": ",".join(target_markets)})
        raw_path = raw_dir / "ticker_core_markets.json"
        if payload is not None:
            write_json(raw_path, payload)
        ticker_checks.append(
            {
                "markets": target_markets,
                "endpoint": "/ticker",
                "raw_path": str(raw_path) if payload is not None else None,
                "row_count": row_count(payload),
                "ok": payload is not None and row_count(payload) > 0,
                "error": error,
            }
        )

    all_checks = candle_checks + orderbook_checks + ticker_checks
    manifest = {
        "generated_at": utc_now(),
        "stage": "stage2_data_health_archival_seed",
        "policy": {
            "scope": "BTC/ETH only; no broad Bithumb search",
            "mode": "public_data_archive_only",
            "private_api_used": False,
            "paper_enabled": False,
            "live_enabled": False,
        },
        "archive_root": str(ARCHIVE_ROOT),
        "raw_dir": str(raw_dir),
        "market_all": {
            "ok": market_payload is not None and row_count(market_payload) > 0,
            "row_count": row_count(market_payload),
            "raw_path": str(raw_dir / "market_all.json") if market_payload is not None else None,
            "error": market_error,
        },
        "target_markets": target_markets,
        "candle_checks": candle_checks,
        "orderbook_checks": orderbook_checks,
        "ticker_checks": ticker_checks,
        "health": {
            "green": bool(all_checks) and all(check.get("ok") for check in all_checks),
            "ok_count": sum(1 for check in all_checks if check.get("ok")),
            "fail_count": sum(1 for check in all_checks if not check.get("ok")),
        },
        "next_action": "Keep collecting BTC/ETH public data only. Do not run broad all-coin or minute strategy search.",
    }
    return manifest


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bithumb Stage 2 Data Health Manifest",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- scope: {payload['policy']['scope']}",
        f"- private_api_used: `{payload['policy']['private_api_used']}`",
        f"- health_green: `{payload['health']['green']}`",
        f"- archive_root: `{payload['archive_root']}`",
        "",
        "## Checks",
        "",
        "| type | market/timeframe | ok | rows | error |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for check in payload["candle_checks"]:
        lines.append(
            f"| candle | {check['market']} {check['timeframe']} | {check['ok']} | {check['row_count']} | {check.get('error') or ''} |"
        )
    for check in payload["orderbook_checks"]:
        lines.append(f"| orderbook | {','.join(check['markets'])} | {check['ok']} | {check['row_count']} | {check.get('error') or ''} |")
    for check in payload["ticker_checks"]:
        lines.append(f"| ticker | {','.join(check['markets'])} | {check['ok']} | {check['row_count']} | {check.get('error') or ''} |")
    lines.extend(["", f"- next_action: {payload['next_action']}"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = build_manifest()
    json_path = REPORT_ROOT / "bithumb_stage2_data_health_manifest_latest.json"
    md_path = REPORT_ROOT / "bithumb_stage2_data_health_manifest_latest.md"
    write_json(json_path, payload)
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"json_path": str(json_path), "md_path": str(md_path), "health": payload["health"]}, indent=2))


if __name__ == "__main__":
    main()
