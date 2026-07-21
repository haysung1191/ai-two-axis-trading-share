from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\AI")
REPORTS = ROOT / "reports" / "operations"
REPORT_JSON = REPORTS / "stage0_13_autonomous_loop_completion_audit_latest.json"
REPORT_MD = REPORTS / "stage0_13_autonomous_loop_completion_audit_latest.md"

SAFETY = {
    "paper_enabled": False,
    "live_enabled": False,
    "broker_submit_allowed": False,
    "private_submit_used": False,
    "real_orders": 0,
    "order_intent_created": False,
    "pretrade_firewall_default_decision": "BLOCK",
}

CORE_LOOP_MARKERS = [
    "run_full_pipeline_safe_watchdog_loop.py",
    "run_crypto_recursive_improvement_loop.py",
    "run_gatekeeper_refresh_loop.py",
]


def safety_ok(*payloads: dict[str, Any]) -> bool:
    for payload in payloads:
        safety = payload.get("safety", {})
        for key, expected in SAFETY.items():
            if safety.get(key, expected) != expected:
                return False
    return True


def command_lines(processes: list[dict[str, Any]]) -> list[str]:
    return [str(row.get("CommandLine") or "") for row in processes]


def build_report(
    now: str,
    *,
    stage_board: dict[str, Any],
    watchdog: dict[str, Any],
    stage13: dict[str, Any],
    processes: list[dict[str, Any]],
) -> dict[str, Any]:
    lines = command_lines(processes)
    missing_core = [marker for marker in CORE_LOOP_MARKERS if not any(marker in line for line in lines)]
    watchdog_rows = [line for line in lines if "run_full_pipeline_safe_watchdog_loop.py" in line]

    checklist = [
        {
            "requirement_id": "watchdog_running_unattended",
            "passed": watchdog.get("status") == "running",
            "missing_or_blocked": [] if watchdog.get("status") == "running" else ["watchdog_not_running"],
        },
        {
            "requirement_id": "watchdog_unbounded",
            "passed": watchdog.get("unbounded") is True,
            "missing_or_blocked": [] if watchdog.get("unbounded") is True else ["watchdog_unbounded_not_satisfied"],
        },
        {
            "requirement_id": "watchdog_singleton",
            "passed": len(watchdog_rows) == 1,
            "missing_or_blocked": [] if len(watchdog_rows) == 1 else ["watchdog_singleton_not_satisfied"],
        },
        {
            "requirement_id": "core_loops_running",
            "passed": not missing_core,
            "missing_or_blocked": missing_core,
        },
        {
            "requirement_id": "execution_ladder_blocked_safely",
            "passed": all(
                row.get("autonomous_action") != "AUTO_RUN_ALLOWED"
                for row in stage_board.get("stages", [])
                if int(row.get("id", 0)) >= 8
            ),
            "missing_or_blocked": [],
        },
        {
            "requirement_id": "safety_invariants_preserved",
            "passed": safety_ok(stage_board, watchdog, stage13),
            "missing_or_blocked": [] if safety_ok(stage_board, watchdog, stage13) else ["safety_invariants_preserved_not_satisfied"],
        },
    ]

    missing_or_blocked: list[str] = []
    for row in checklist:
        if not row["passed"]:
            missing_or_blocked.extend(row["missing_or_blocked"])

    complete = not missing_or_blocked
    report = {
        "generated_at": now,
        "completion_decision": "COMPLETE" if complete else "NOT_COMPLETE",
        "automation_completion_decision": "COMPLETE" if complete else "NOT_COMPLETE",
        "stage13_deployment_completion_decision": stage13.get("completion_decision", "NOT_COMPLETE"),
        "automation_state": "SAFE_UNATTENDED_LOOP_RUNNING" if complete else "SAFE_UNATTENDED_LOOP_INCOMPLETE",
        "stage13_complete": bool(stage13.get("stage13_complete")),
        "stage13_complete_required_for_automation_goal": False,
        "missing_or_blocked": missing_or_blocked,
        "prompt_to_artifact_checklist": checklist,
        "safety": SAFETY,
        "required_core_loop_markers": CORE_LOOP_MARKERS,
        "retired_required_loop_markers": ["run_stage6_shadow_loop.py", "run_stage7_local_sim_from_shadow.py"],
    }
    return report


def main() -> int:
    import run_full_pipeline_safe_supervisor as supervisor

    def read(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    report = build_report(
        datetime.now().isoformat(),
        stage_board=read(REPORTS / "full_pipeline_stage_status_latest.json", {"stages": [], "safety": SAFETY}),
        watchdog=read(REPORTS / "full_pipeline_safe_watchdog_latest.json", {"status": "stopped", "safety": SAFETY}),
        stage13=read(REPORTS / "stage13_completion_audit_latest.json", {"completion_decision": "NOT_COMPLETE", "safety": SAFETY}),
        processes=supervisor.process_rows(),
    )
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text("# Stage 0-13 Autonomous Loop Audit\n\n" + report["completion_decision"] + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
