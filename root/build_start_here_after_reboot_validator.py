from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
START_MD = ROOT / "START_HERE_AFTER_REBOOT.md"
DASHBOARD_JSON = ROOT / "ops/dashboard/pipeline_dashboard_simple_latest.json"
HEALTH_MD = ROOT / "ops/health/two_axis_operational_health_latest.md"
LIMITED_LIVE_POLICY_JSON = ROOT / "ops/runstate/limited_live_policy.json"
BROKER_POLICY_JSON = ROOT / "ops/runstate/broker_paper_policy.json"
BITHUMB_LATEST_JSON = ROOT / "ops/bithumb_axis_autotrade/bithumb_axis_autotrade_latest.json"
KIS_OPERATION_JSON = ROOT / "ops/stock_etf_axis_operation/stock_etf_axis_operation_latest.json"
KIS_BRIDGE_JSON = ROOT / "ops/stock_etf_operating_candidate_bridge/stock_etf_operating_candidate_bridge_latest.json"
MODEL_FACTORY_JSON = ROOT / "ops/model_factory_loop/two_axis_model_factory_loop_latest.json"
DIRECT_DEVELOPMENT_JSON = ROOT / "reports/model_factory/two_axis_direct_model_development_latest.json"
MODEL_INVENTORY_JSON = ROOT / "reports/operations/two_axis_model_inventory_latest.json"
REPORT_JSON = ROOT / "reports/operations/start_here_after_reboot_validator_latest.json"
REPORT_MD = ROOT / "reports/operations/start_here_after_reboot_validator_latest.md"


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def build_report(start_text: str, generated_at: str | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    blockers: list[str] = []
    normalized_start_text = start_text.replace("\\", "/")
    required_paths = [
        str(DASHBOARD_JSON),
        str(HEALTH_MD),
        str(LIMITED_LIVE_POLICY_JSON),
        str(BROKER_POLICY_JSON),
        str(BITHUMB_LATEST_JSON),
        str(KIS_OPERATION_JSON),
        str(KIS_BRIDGE_JSON),
        str(MODEL_FACTORY_JSON),
        str(DIRECT_DEVELOPMENT_JSON),
        str(MODEL_INVENTORY_JSON),
    ]
    for path in required_paths:
        rel_path = str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else path
        variants = {path, rel_path, path.replace("\\", "/"), rel_path.replace("\\", "/")}
        if not any(variant in start_text or variant in normalized_start_text for variant in variants):
            blockers.append(f"missing_path:{path}")
    required_phrases = [
        "Do a read-only state check. Do not stop live loops.",
        "Do not start by reading old",
        "daily_close_presence",
        "PIT/survivorship-free KIS documents may still exist on disk as historical artifacts",
        "Older stage reports may still mention shadow/paper blockers. Treat those as stale",
    ]
    for phrase in required_phrases:
        if phrase not in start_text:
            blockers.append(f"missing_phrase:{phrase}")
    forbidden_current_phrases = [
        "KIS execution as blocked until historical PIT/survivorship-free data is verified",
        "paper/live 비활성",
        "Tiny Live 진입 불가",
    ]
    for phrase in forbidden_current_phrases:
        if phrase in start_text:
            blockers.append(f"stale_current_blocker_phrase_present:{phrase}")
    status = "PASS" if not blockers else "FAIL"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "report": "start_here_after_reboot_validator",
        "status": status,
        "blockers": sorted(set(blockers)),
        "validated_files": {
            "start_here": str(START_MD),
            "dashboard": str(DASHBOARD_JSON),
            "health": str(HEALTH_MD),
            "limited_live_policy": str(LIMITED_LIVE_POLICY_JSON),
            "broker_policy": str(BROKER_POLICY_JSON),
            "bithumb_latest": str(BITHUMB_LATEST_JSON),
            "kis_operation": str(KIS_OPERATION_JSON),
            "kis_bridge": str(KIS_BRIDGE_JSON),
            "model_factory": str(MODEL_FACTORY_JSON),
            "direct_development": str(DIRECT_DEVELOPMENT_JSON),
            "model_inventory": str(MODEL_INVENTORY_JSON),
        },
    }


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Start Here After Reboot Validator",
            "",
            f"- Status: `{report['status']}`",
            f"- Blockers: `{', '.join(report['blockers']) if report['blockers'] else 'none'}`",
            "",
        ]
    )


def main() -> int:
    report = build_report(_read_text(START_MD))
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "blockers": report["blockers"], "latest_json": str(REPORT_JSON)}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
