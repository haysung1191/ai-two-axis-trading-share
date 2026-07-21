from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_kis_axis_wide_source_export_intake_contract as intake_contract


KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/operations/krx_data_marketplace_access_probe_latest.json"
REPORT_MD = ROOT / "reports/operations/krx_data_marketplace_access_probe_latest.md"
SAFETY = intake_contract.SAFETY


def _default_probe() -> dict:
    return {
        "ok": True,
        "http_status": 200,
        "body_prefix": "LOGOUT",
        "note": "No unattended session cookie is configured; report-only probe records expected login barrier.",
    }


def build_report(generated_at: str | None = None, probe: dict | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    probe = probe or _default_probe()
    blockers = []
    non_goals = [
        "does_not_download_krx_csv",
        "does_not_bypass_login_or_license_terms",
        "does_not_import_rows",
        "does_not_enable_paper_live_broker_submit_or_order_intent",
    ]
    if not probe.get("ok"):
        status = "BLOCK_KRX_DATA_MARKETPLACE_UNATTENDED_ACCESS"
        operation_ready = False
        blockers.append("krx_generate_otp_request_failed")
    elif str(probe.get("body_prefix", "")).upper().startswith("LOGOUT"):
        status = "BLOCK_KRX_DATA_MARKETPLACE_UNATTENDED_ACCESS"
        operation_ready = False
        blockers.append("krx_generate_otp_requires_login_or_session")
    else:
        status = "KRX_GENERATE_OTP_ACCESSIBLE_REVIEW_REQUIRED"
        operation_ready = True
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "operation_ready": operation_ready,
        "probe": probe,
        "blockers": blockers,
        "single_next_action": "Use a reviewed manual KRX export or licensed vendor export; do not bypass KRX login/session controls.",
        "non_goals": non_goals,
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    return "\n".join([
        "# KRX Data Marketplace Access Probe",
        "",
        f"- Status: `{report['status']}`",
        f"- Operation ready: `{report['operation_ready']}`",
        f"- Blockers: `{', '.join(report['blockers'])}`",
    ]) + "\n"


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "operation_ready": report["operation_ready"],
        "blockers": report["blockers"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
