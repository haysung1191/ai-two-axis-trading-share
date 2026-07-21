from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\AI")
RUNSTATE = ROOT / "ops" / "runstate"
KILL_SWITCH = RUNSTATE / "kill_switch.json"
BROKER_POLICY = RUNSTATE / "broker_paper_policy.json"
GLOBAL_DISABLE = RUNSTATE / "DISABLE_ALL_TRADING"
REPORTS = ROOT / "reports" / "operations"
STAGE13_JSON = REPORTS / "stage13_completion_audit_latest.json"
DIRECT_BLOCKER_JSON = REPORTS / "pipeline_direct_blocker_packet_latest.json"
DIRECT_NEXT_JSON = REPORTS / "pipeline_direct_next_command_latest.json"
STAGE_STATUS_JSON = REPORTS / "full_pipeline_stage_status_latest.json"
STAGE_STATUS_MD = REPORTS / "full_pipeline_stage_status_latest.md"

SAFETY = {
    "paper_enabled": False,
    "live_enabled": False,
    "broker_submit_allowed": False,
    "private_submit_used": False,
    "real_orders": 0,
    "order_intent_created": False,
    "pretrade_firewall_default_decision": "BLOCK",
}


@dataclass(frozen=True)
class LoopSpec:
    name: str
    stage: str
    script: str
    args: tuple[str, ...] = ()
    blocked_by_research_disable: bool = False
    required: bool = True
    role: str = "required"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def loop_specs() -> list[LoopSpec]:
    return [
        LoopSpec(
            name="research_lane_refresh",
            stage="stage1_research_and_candidate_generation",
            script="run_research_lane_stage1_loop.py",
            args=("--cycles", "1", "--sleep-seconds", "0"),
            blocked_by_research_disable=True,
        ),
        LoopSpec(
            name="crypto_recursive_improvement",
            stage="stage1_research_and_candidate_generation",
            script="run_crypto_recursive_improvement_loop.py",
            args=("--cycles", "96", "--sleep-seconds", "300"),
            blocked_by_research_disable=True,
        ),
        LoopSpec(
            name="gatekeeper_refresh",
            stage="stage2_to_stage5_signal_risk_pretrade_refresh",
            script="run_gatekeeper_refresh_loop.py",
            args=("--cycles", "1", "--sleep-seconds", "0"),
        ),
        LoopSpec(
            name="stage13_completion_audit",
            stage="stage13_report_only_completion_audit",
            script="build_stage13_completion_audit.py",
        ),
        LoopSpec(
            name="direct_blocker_packet",
            stage="stage9_live_approval_wait_report",
            script="build_pipeline_direct_blocker_packet.py",
        ),
        LoopSpec(
            name="direct_next_command",
            stage="stage9_live_approval_wait_report",
            script="build_pipeline_direct_next_command.py",
        ),
        LoopSpec(
            name="runtime_safety_snapshot",
            stage="stage9_live_approval_wait_report",
            script="build_pipeline_blocked_runtime_safety_snapshot.py",
        ),
        LoopSpec(
            name="shadow_observation_optional",
            stage="optional_diagnostic_shadow_review_no_submit",
            script="run_stage6_shadow_loop.py",
            args=("--cycles", "1", "--dry-run"),
            required=False,
            role="optional_diagnostic",
        ),
        LoopSpec(
            name="paper_sim_optional",
            stage="optional_diagnostic_paper_sim_no_submit",
            script="run_stage7_local_sim_from_shadow.py",
            args=("--dry-run",),
            required=False,
            role="optional_diagnostic",
        ),
    ]


def required_loop_specs() -> list[LoopSpec]:
    return [spec for spec in loop_specs() if spec.required]


def command_for(spec: LoopSpec) -> list[str]:
    return [sys.executable, str(ROOT / spec.script), *spec.args]


def safety_preflight() -> dict[str, Any]:
    kill = read_json(KILL_SWITCH, {}) or {}
    broker = read_json(BROKER_POLICY, {}) or {}
    blockers: list[str] = []
    if kill.get("live_enabled") is True:
        blockers.append("KILL_SWITCH_LIVE_ENABLED")
    if kill.get("paper_enabled") is True:
        blockers.append("KILL_SWITCH_PAPER_ENABLED")
    if broker.get("live_enabled") is True:
        blockers.append("BROKER_POLICY_LIVE_ENABLED")
    if broker.get("private_submit_used") is True:
        blockers.append("PRIVATE_SUBMIT_USED")
    if broker.get("broker_submit_allowed") is True and broker.get("broker_submit_scope") not in {None, "paper_only"}:
        blockers.append("BROKER_SUBMIT_SCOPE_NOT_SAFE")

    return {
        "status": "BLOCKED" if blockers else "PASS",
        "blockers": blockers,
        "global_disable_present": GLOBAL_DISABLE.exists(),
        "does_enable_paper": False,
        "does_enable_live": False,
        "does_enable_broker_submit": False,
        "does_create_order_intent": False,
        "safety": {
            **SAFETY,
            "paper_enabled": bool(kill.get("paper_enabled", False)),
            "live_enabled": bool(kill.get("live_enabled", False)),
            "broker_submit_allowed": bool(broker.get("broker_submit_allowed", False)),
            "private_submit_used": bool(broker.get("private_submit_used", False)),
        },
    }


def process_rows() -> list[dict[str, Any]]:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.CommandLine -like '*C:\\AI*' } | "
        "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress",
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=20)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    payload = json.loads(result.stdout)
    rows = payload if isinstance(payload, list) else [payload]
    filtered: list[dict[str, Any]] = []
    for row in rows:
        command_line = str(row.get("CommandLine") or "")
        lower = command_line.lower()
        if "get-ciminstance" in lower or "convertto-json" in lower:
            continue
        filtered.append(row)
    return filtered


def known_loop_blocker(spec: LoopSpec) -> str | None:
    if spec.name != "shadow_observation_optional":
        return None
    payload = read_json(REPORTS / "bithumb_current_actionable_shadow_observation_loop_latest.json", {}) or {}
    blockers = payload.get("last_cycle", {}).get("observation", {}).get("blockers", [])
    if "OOS_PARAMETERS_NOT_FOUND_FOR_REGISTERED_CANDIDATE" in blockers:
        return "blocked_by_OOS_PARAMETERS_NOT_FOUND_FOR_REGISTERED_CANDIDATE"
    return None


def stage_specs() -> list[dict[str, Any]]:
    names = {
        0: "Safety State",
        1: "Research",
        2: "Signal Qualification",
        3: "Risk Compression",
        4: "Robustness",
        5: "Pretrade Readiness",
        6: "Optional Shadow Diagnostic",
        7: "Optional Paper Diagnostic",
        8: "Live Approval Wait",
        9: "Tiny Limited Live Request",
        10: "Firewall Decision",
        11: "Tiny Live Execution",
        12: "Execution Audit",
        13: "Capital Deployment Review",
    }
    loops = {
        0: "runtime safety snapshot report",
        1: "research_lane_refresh / crypto_recursive_improvement",
        2: "gatekeeper_refresh report",
        3: "gatekeeper_refresh report",
        4: "stage13_completion_audit report",
        5: "direct_blocker_packet report",
        6: "optional diagnostic only; not required",
        7: "optional diagnostic only; not required",
        8: "blocked until exact LIVE APPROVE phrase",
        9: "blocked until exact LIVE APPROVE phrase",
        10: "blocked unless pretrade firewall passes after approval",
        11: "blocked; no submit loop in supervisor",
        12: "audit report only after execution",
        13: "deployment review report only",
    }
    return [{"id": idx, "name": names[idx], "loop": loops[idx]} for idx in range(14)]


def build_stage_status_board(processes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    processes = processes if processes is not None else process_rows()
    stage13 = read_json(STAGE13_JSON, {}) or {}
    direct = read_json(DIRECT_BLOCKER_JSON, {}) or {}
    failed = set(stage13.get("failed_required_stage_ids", []))
    current_target_stage_id = int(stage13.get("current_target_stage_id", 13) or 13)
    stages: list[dict[str, Any]] = []
    for row in stage_specs():
        stage_id = row["id"]
        stage_key = f"stage{stage_id}"
        blocked = stage_key in failed or (stage_id > current_target_stage_id and stage_id >= 8)
        if stage_id in {6, 7}:
            action = "OPTIONAL_DIAGNOSTIC_ONLY_NOT_REQUIRED"
            status = "OPTIONAL"
        elif blocked:
            action = "BLOCK_OR_REPORT_ONLY_UNLESS_EXACT_LIVE_APPROVAL_AND_FIREWALL_PASS"
            status = "BLOCKED"
        else:
            action = "AUTO_RUN_ALLOWED"
            status = "PASS"
        stages.append({**row, "status": status, "autonomous_action": action, "blockers": []})

    board = {
        "generated_at_utc": utc_now(),
        "completion_decision": "NOT_COMPLETE",
        "stages": stages,
        "process_count": len(processes),
        "direct_blocker": direct,
        "safety_policy": {
            "does_enable_paper": False,
            "does_enable_live": False,
            "does_enable_broker_submit": False,
            "does_create_order_intent": False,
        },
        "safety": SAFETY,
    }
    write_json(STAGE_STATUS_JSON, board)
    STAGE_STATUS_MD.parent.mkdir(parents=True, exist_ok=True)
    STAGE_STATUS_MD.write_text(
        "# Full Pipeline Stage Status\n\n"
        "Shadow and paper are optional diagnostics, not required promotion stages.\n"
        "The required loop stops at exact live approval wait and does not create order intents.\n",
        encoding="utf-8",
    )
    return board


def shadow_queue_candidate_ids() -> list[str]:
    return []


def run_safe_command(name: str, command: list[str], timeout_seconds: int = 180) -> dict[str, Any]:
    result = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout_seconds)
    return {
        "name": name,
        "command": command,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def run_once_safe_actions() -> list[dict[str, Any]]:
    commands = [
        LoopSpec("stage13_completion_audit", "report", "build_stage13_completion_audit.py"),
        LoopSpec("direct_blocker_packet", "report", "build_pipeline_direct_blocker_packet.py"),
        LoopSpec("direct_next_command", "report", "build_pipeline_direct_next_command.py"),
        LoopSpec("runtime_safety_snapshot", "report", "build_pipeline_blocked_runtime_safety_snapshot.py"),
    ]
    return [run_safe_command(spec.name, command_for(spec)) for spec in commands]


def cand022_provider_watch_continuity() -> dict[str, Any]:
    return read_json(REPORTS / "cand022_provider_watch_continuity_latest.json", {}) or {}


def stage6_operating_status() -> dict[str, Any]:
    payload = read_json(REPORTS / "stage6_operating_status_latest.json", {}) or {}
    return {
        "status": payload.get("status", "OPTIONAL_DIAGNOSTIC_NOT_REQUIRED"),
        "broader_stage6_running": payload.get("broader_stage6_operation", {}).get("running", False),
        "broader_stage6_candidates": payload.get("broader_stage6_operation", {}).get("shadow_queue_candidates", []),
        "cand022_stage6_reached": payload.get("cand022_stage6", {}).get("stage6_reached", False),
        "cand022_completion_percent": payload.get("cand022_stage6", {}).get("completion_percent"),
        "safety": payload.get("safety", SAFETY),
        "required_for_current_pipeline": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-once-safe", action="store_true")
    args = parser.parse_args(argv)
    preflight = safety_preflight()
    board = build_stage_status_board()
    results = run_once_safe_actions() if args.run_once_safe and preflight["status"] == "PASS" else []
    print(json.dumps({"preflight": preflight, "stage_status": board, "run_once_safe_results": results}, ensure_ascii=False))
    return 0 if preflight["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
