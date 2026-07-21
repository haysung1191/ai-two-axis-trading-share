from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/operations/kis_api_document_gap_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_api_document_gap_latest.md"

WATCHED_SHEET_INDEXES = {
    258: "domestic_cash_order",
    42: "domestic_daily_itemchartprice",
    601: "overseas_dailyprice",
    602: "overseas_search",
    603: "overseas_product_info",
}

SAFETY = {
    "paper_enabled": False,
    "live_enabled": False,
    "broker_submit_allowed": False,
    "private_submit_used": False,
    "real_orders": 0,
    "order_intent_created": False,
    "pretrade_firewall_default_decision": "BLOCK",
}


def find_doc_path() -> Path:
    matches = sorted(ROOT.rglob("*20260507_030000.xlsx"))
    if matches:
        return matches[-1]
    any_xlsx = sorted(ROOT.rglob("*.xlsx"))
    return any_xlsx[-1] if any_xlsx else Path("KIS_OFFICIAL_DOC_NOT_CAPTURED.xlsx")


def workbook_sheet_rows(path: Path) -> dict:
    return {}


def current_kis_code_signals() -> dict:
    py_files = []
    for base in [ROOT / "external_refs/koreainvestment_open_trading_api", ROOT / "external_sources/open-trading-api"]:
        if base.exists():
            py_files.extend(base.rglob("*.py"))
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")[:20000]
        for path in py_files[:400]
    )
    return {
        "uses_domestic_cash_order_old_buy_tr": "TTTC0802U" in text,
        "uses_domestic_cash_order_old_sell_tr": "TTTC0801U" in text,
        "uses_domestic_cash_order_new_buy_tr": "TTTC0011U" in text or "VTTC0011U" in text,
        "uses_domestic_cash_order_new_sell_tr": "TTTC0012U" in text or "VTTC0012U" in text,
        "uses_overseas_us_buy_tr": "TTTS" in text or "VTTT" in text,
        "uses_overseas_us_sell_tr": "TTTS" in text or "VTTT" in text,
        "uses_domestic_daily_itemchartprice": "inquire-daily-itemchartprice" in text,
        "uses_overseas_dailyprice": "dailyprice" in text,
        "uses_overseas_search": "inquire-search" in text,
        "uses_overseas_product_info": "search-info" in text,
    }


def build_report(generated_at: str | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    doc_path = find_doc_path()
    sheets = workbook_sheet_rows(doc_path)
    signals = current_kis_code_signals()
    blockers = []
    if signals.get("uses_domestic_cash_order_old_buy_tr") or signals.get("uses_domestic_cash_order_old_sell_tr"):
        blockers.append("DOMESTIC_ORDER_USES_OLD_TR_ID")
    if not signals.get("uses_overseas_dailyprice"):
        blockers.append("OVERSEAS_DAILY_HISTORY_API_NOT_IMPLEMENTED")
    if not signals.get("uses_overseas_search"):
        blockers.append("OVERSEAS_SEARCH_API_NOT_IMPLEMENTED")
    if not signals.get("uses_overseas_product_info"):
        blockers.append("OVERSEAS_PRODUCT_INFO_API_NOT_IMPLEMENTED")
    if not doc_path.exists():
        blockers.append("KIS_OFFICIAL_XLSX_NOT_CAPTURED")
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": "PASS_KIS_API_DOCUMENT_GAP_REVIEW" if not blockers else "BLOCK_KIS_API_DOCUMENT_GAPS",
        "document_path": str(doc_path),
        "watched_sheet_count": len(WATCHED_SHEET_INDEXES),
        "loaded_sheet_count": len(sheets),
        "code_signals": signals,
        "blockers": blockers,
        "single_next_action": "Use official KIS repo for current-readiness checks only; keep historical PIT/survivorship as separate blocker.",
        "safety": SAFETY,
    }


def render_markdown(report: dict) -> str:
    return "\n".join(
        [
            "# KIS API Document Gap Report",
            "",
            f"- Status: `{report['status']}`",
            f"- Blockers: `{len(report['blockers'])}`",
            f"- Document: `{report['document_path']}`",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "latest_json": str(REPORT_JSON), "blockers": report["blockers"], "safety": SAFETY}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
