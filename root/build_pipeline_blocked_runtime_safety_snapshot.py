from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
DISABLE_GUARD = ROOT / "overnight_runs/DISABLE_DUAL_REPO_RESEARCH_LOOP"
GLOBAL_DISABLE_ALL_TRADING = ROOT / "ops/runstate/DISABLE_ALL_TRADING"
KILL_SWITCH_JSON = ROOT / "ops/runstate/kill_switch.json"
DIRECT_NEXT_JSON = ROOT / "reports/operations/pipeline_direct_next_command_latest.json"
REPORT_JSON = ROOT / "reports/operations/pipeline_blocked_runtime_safety_snapshot_latest.json"
REPORT_MD = ROOT / "reports/operations/pipeline_blocked_runtime_safety_snapshot_latest.md"

TASK_NAMES = [
    "CodexDualRepoResearchLoop",
    "MomentumSplitModelsInitialEntryAutoTrade",
    "CodexLatestRunEmailEvery2Hours",
    "CodexLatestRunEmailEvery3Hours",
    "CodexLatestRunEmailEvery4Hours",
    "CodexExternalIntelEvery24Hours",
    "CodexHolidayAutonomousContinue",
]


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _powershell_json(command: str) -> object:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )
    text = result.stdout.strip()
    if not text:
        return []
    return json.loads(text)


def collect_python_processes() -> list[dict]:
    command = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -like 'python*' -and $_.CommandLine -like '*C:\\AI*' } | "
        "Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Depth 4"
    )
    rows = _powershell_json(command)
    if isinstance(rows, dict):
        return [rows]
    return rows if isinstance(rows, list) else []


def collect_scheduled_tasks() -> list[dict]:
    quoted = ",".join(f"'{name}'" for name in TASK_NAMES)
    command = (
        f"$names=@({quoted}); "
        "$rows = foreach($n in $names){ "
        "$t=Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue; "
        "if($t){ [pscustomobject]@{TaskName=$n; State=[string]$t.State; TaskPath=$t.TaskPath} } "
        "else { [pscustomobject]@{TaskName=$n; State='MISSING'; TaskPath=''} } "
        "}; $rows | ConvertTo-Json -Depth 4"
    )
    rows = _powershell_json(command)
    if isinstance(rows, dict):
        return [rows]
    return rows if isinstance(rows, list) else []


def build_report(
    python_processes: list[dict],
    scheduled_tasks: list[dict],
    kill_switch: dict,
    disable_guard_exists: bool,
    direct_safety: dict | None = None,
    direct_status: str | None = None,
    global_disable_all_trading_exists: bool | None = None,
    generated_at: str | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    direct_safety = direct_safety or {}
    direct_status = direct_status or ""
    global_disable_all_trading_exists = (
        GLOBAL_DISABLE_ALL_TRADING.exists()
        if global_disable_all_trading_exists is None
        else bool(global_disable_all_trading_exists)
    )
    limited_live_preflight_passed = (
        direct_status == "TINY_LIVE_PREFLIGHT_PASSED_BROKER_SUBMIT_BLOCKED_BY_GLOBAL_DISABLE"
    )
    task_state = {row.get("TaskName"): row.get("State") for row in scheduled_tasks}
    blockers: list[str] = []
    warnings: list[str] = []
    if python_processes:
        warnings.append("c_ai_python_processes_running")
    if task_state.get("CodexDualRepoResearchLoop") in {"Ready", "Running"} and not disable_guard_exists:
        blockers.append("dual_repo_task_ready_without_disable_guard")
    if task_state.get("MomentumSplitModelsInitialEntryAutoTrade") not in {"Disabled", "MISSING"}:
        warnings.append("momentum_autotrade_task_not_disabled")
    if kill_switch.get("paper_enabled") is not False:
        blockers.append("paper_enabled_not_false")
    if kill_switch.get("live_enabled") is not False and not limited_live_preflight_passed:
        blockers.append("live_enabled_not_false")
    if limited_live_preflight_passed:
        required_direct_safety = {
            "paper_enabled": False,
            "live_enabled": True,
            "broker_submit_allowed": True,
            "private_submit_used": False,
            "real_orders": 0,
            "order_intent_created": True,
            "pretrade_firewall_default_decision": "ALLOW_LIMITED_LIVE",
        }
        if not global_disable_all_trading_exists:
            blockers.append("global_disable_all_trading_missing_after_preflight")
    else:
        required_direct_safety = {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "private_submit_used": False,
            "real_orders": 0,
            "order_intent_created": False,
            "pretrade_firewall_default_decision": "BLOCK",
        }
    for key, expected in required_direct_safety.items():
        if direct_safety.get(key) != expected:
            blockers.append(f"direct_safety_{key}_not_{expected}")
    status = "PASS" if not blockers else "FAIL"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "report": "pipeline_blocked_runtime_safety_snapshot",
        "status": status,
        "python_process_count": len(python_processes),
        "python_processes": python_processes,
        "scheduled_tasks": scheduled_tasks,
        "disable_dual_repo_research_loop_guard_exists": disable_guard_exists,
        "kill_switch": kill_switch,
        "direct_safety": direct_safety,
        "direct_status": direct_status,
        "global_disable_all_trading_exists": global_disable_all_trading_exists,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "safety_interpretation": (
            "Limited-live preflight may hold live/order-intent state only while global disable blocks broker submit."
            if limited_live_preflight_passed
            else "No paper/live/broker/order-intent state enabled; scheduled dual-repo task is only acceptable when repo disable guard exists."
        ),
    }


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Pipeline Blocked Runtime Safety Snapshot",
            "",
            f"- Status: `{report['status']}`",
            f"- C:\\AI Python processes: `{report['python_process_count']}`",
            f"- Disable guard exists: `{report['disable_dual_repo_research_loop_guard_exists']}`",
            f"- Blockers: `{', '.join(report['blockers']) if report['blockers'] else 'none'}`",
            f"- Warnings: `{', '.join(report['warnings']) if report['warnings'] else 'none'}`",
            "",
        ]
    )


def main() -> int:
    report = build_report(
        collect_python_processes(),
        collect_scheduled_tasks(),
        read_json(KILL_SWITCH_JSON, {}),
        DISABLE_GUARD.exists(),
        read_json(DIRECT_NEXT_JSON, {}).get("safety", {}),
        direct_status=read_json(DIRECT_NEXT_JSON, {}).get("status", ""),
    )
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "python_process_count": report["python_process_count"], "blockers": report["blockers"], "warnings": report["warnings"], "latest_json": str(REPORT_JSON)}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
