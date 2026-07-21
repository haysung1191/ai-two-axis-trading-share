from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/operations/cand022_kis_api_tradability_audit_latest.json"
REPORT_MD = ROOT / "reports/operations/cand022_kis_api_tradability_audit_latest.md"

SAFETY = {
    "paper_enabled": False,
    "live_enabled": False,
    "broker_submit_allowed": False,
    "private_submit_used": False,
    "real_orders": 0,
    "order_intent_created": False,
    "pretrade_firewall_default_decision": "BLOCK",
}

CAND022_US_EXCHANGE_MAP = {
    "CAT": ("NYSE", "NYS"),
    "DOW": ("NYSE", "NYS"),
    "GEV": ("NYSE", "NYS"),
    "XLE": ("AMEX", "AMS"),
    "XOM": ("NYSE", "NYS"),
}


def resolve_us_exchange(symbol: str) -> tuple[str | None, str | None]:
    return CAND022_US_EXCHANGE_MAP.get(symbol.upper(), (None, None))


def _read_mandate_caps(path: Path) -> dict:
    if not path.exists():
        return {"status": "MISSING", "caps_present": False}
    text = path.read_text(encoding="utf-8")
    return {
        "status": "PRESENT",
        "caps_present": all(key in text for key in ["max_order_krw", "max_daily_loss_krw", "max_total_loss_krw"]),
        "paper_live_submit_disabled": all(
            marker in text
            for marker in [
                "paper_enabled: false",
                "live_enabled: false",
                "broker_submit_allowed: false",
            ]
        ),
    }


def build_report(generated_at: str | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    symbols = sorted(CAND022_US_EXCHANGE_MAP)
    symbol_reports = []
    blockers = []
    for symbol in symbols:
        exchange, kis_code = resolve_us_exchange(symbol)
        ok = exchange is not None and kis_code is not None
        if not ok:
            blockers.append(f"missing_exchange_mapping:{symbol}")
        symbol_reports.append(
            {
                "symbol": symbol,
                "asset_axis": "kis_us_stocks" if symbol != "XLE" else "kis_us_etfs",
                "resolved_exchange": exchange,
                "kis_market_code": kis_code,
                "current_readiness_check": "mapping_only_read_only",
                "tradability_operation_ready": ok,
            }
        )
    mandate = _read_mandate_caps(ROOT / "contracts/human_mandate.yaml")
    if not mandate["caps_present"]:
        blockers.append("human_mandate_caps_missing")
    report = {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "candidate_id": "CAND-022",
        "status": "PASS_CURRENT_KIS_API_TRADABILITY_MAPPING"
        if not blockers
        else "BLOCK_CURRENT_KIS_API_TRADABILITY_MAPPING",
        "operation_ready_for_historical_pit": False,
        "symbol_reports": symbol_reports,
        "human_mandate": mandate,
        "blockers": blockers,
        "single_next_action": "Keep current KIS tradability mapping as read-only evidence; KIS historical PIT/survivorship data remains the live blocker.",
        "non_goals": [
            "does_not_mark_historical_pit_ready",
            "does_not_create_order_intent",
            "does_not_enable_paper_live_broker_submit",
        ],
        "safety": SAFETY,
    }
    return report


def render_markdown(report: dict) -> str:
    return "\n".join(
        [
            "# CAND-022 KIS API Tradability Audit",
            "",
            f"- Status: `{report['status']}`",
            f"- Historical PIT operation ready: `{report['operation_ready_for_historical_pit']}`",
            f"- Blockers: `{len(report['blockers'])}`",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "latest_json": str(REPORT_JSON), "safety": SAFETY}, indent=2))
    return 0 if not report["blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
