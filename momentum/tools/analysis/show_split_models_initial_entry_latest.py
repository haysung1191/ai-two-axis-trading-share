from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_task_status_payload() -> dict[str, object]:
    try:
        from tools.analysis import show_split_models_initial_entry_autotrade_task_status as show_task

        raw = show_task._run_powershell_json(
            show_task.build_task_status_command(task_name=show_task.DEFAULT_TASK_NAME)
        )
        return show_task.build_status_payload(raw)
    except Exception:
        return {
            "task_name": None,
            "state": None,
            "hardening_verdict": "UNKNOWN",
            "hardening_failures": ["task_status_unavailable"],
            "recommended_next_action": "inspect_task_status",
            "recommended_next_reason": "autotrade_task_status_unavailable",
        }


def _is_submit_ready(check_payload: dict[str, object]) -> bool:
    return (
        str(check_payload.get("check_verdict", "") or "") == "PASS"
        and str(check_payload.get("preflight_verdict", "") or "") == "PASS"
        and str(check_payload.get("live_readiness", "") or "") == "GO"
        and str(check_payload.get("operator_gate_verdict", "") or "") == "PASS"
        and int(check_payload.get("planned_count", 0) or 0) > 0
        and int(check_payload.get("skipped_count", 0) or 0) == 0
    )


def _build_recommended_next_reason(check_payload: dict[str, object], submit_ready: bool) -> str:
    if submit_ready:
        return "all_submit_gates_passed_and_planned_orders_exist"
    reasons: list[str] = []
    if str(check_payload.get("check_verdict", "") or "") != "PASS":
        reasons.append("check_verdict_not_pass")
    if str(check_payload.get("preflight_verdict", "") or "") != "PASS":
        reasons.append("preflight_verdict_not_pass")
    if str(check_payload.get("live_readiness", "") or "") != "GO":
        reasons.append("live_readiness_not_go")
    if str(check_payload.get("operator_gate_verdict", "") or "") != "PASS":
        reasons.append("operator_gate_not_pass")
    if int(check_payload.get("planned_count", 0) or 0) <= 0:
        reasons.append("planned_count_not_positive")
    if int(check_payload.get("skipped_count", 0) or 0) != 0:
        reasons.append("skipped_rows_present")
    return ",".join(reasons) if reasons else "submit_not_ready"


def build_status_payload(latest_index: dict[str, object], check_payload: dict[str, object]) -> dict[str, object]:
    task_status_payload = _load_task_status_payload()
    submit_ready = _is_submit_ready(check_payload)
    recommended_next_reason = _build_recommended_next_reason(check_payload, submit_ready)
    recommended_next_action = "submit_and_show" if submit_ready else "refresh_and_show"
    recommended_next_command_bat = (
        r"tools\analysis\submit_and_show_split_models_initial_entry_latest.bat"
        if submit_ready
        else r"tools\analysis\refresh_and_show_split_models_initial_entry_latest.bat"
    )
    recommended_next_command_ps1 = (
        r"tools\analysis\submit_and_show_split_models_initial_entry_latest.ps1"
        if submit_ready
        else r"tools\analysis\refresh_and_show_split_models_initial_entry_latest.ps1"
    )
    task_hardening_verdict = str(task_status_payload.get("hardening_verdict", "UNKNOWN") or "UNKNOWN")
    task_hardening_failures = list(task_status_payload.get("hardening_failures", []) or [])
    unattended_operation_ready = submit_ready and task_hardening_verdict == "PASS"
    if not submit_ready:
        operational_next_action = recommended_next_action
        operational_next_reason = recommended_next_reason
        operational_next_command_bat = recommended_next_command_bat
        operational_next_command_ps1 = recommended_next_command_ps1
    elif task_hardening_verdict != "PASS":
        operational_next_action = str(
            task_status_payload.get("recommended_next_action", "") or "run_harden_as_admin"
        )
        operational_next_reason = str(
            task_status_payload.get("recommended_next_reason", "") or "scheduled_task_not_hardened_for_unattended_operation"
        )
        operational_next_command_bat = (
            r"tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.bat"
        )
        operational_next_command_ps1 = (
            r"tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.ps1"
        )
    else:
        operational_next_action = recommended_next_action
        operational_next_reason = recommended_next_reason
        operational_next_command_bat = recommended_next_command_bat
        operational_next_command_ps1 = recommended_next_command_ps1
    return {
        "capital_slug": latest_index.get("capital_slug"),
        "total_capital": latest_index.get("total_capital"),
        "submit_live_requested": latest_index.get("submit_live_requested"),
        "check_timestamp": latest_index.get("check_timestamp"),
        "check_verdict": check_payload.get("check_verdict"),
        "preflight_verdict": check_payload.get("preflight_verdict"),
        "live_readiness": check_payload.get("live_readiness"),
        "operator_gate_verdict": check_payload.get("operator_gate_verdict"),
        "archive_stability_verdict": check_payload.get("archive_stability_verdict"),
        "planned_count": check_payload.get("planned_count"),
        "skipped_count": check_payload.get("skipped_count"),
        "planned_symbols": check_payload.get("planned_symbols"),
        "planned_quantity_total": check_payload.get("planned_quantity_total"),
        "estimated_order_notional_krw_total": check_payload.get("estimated_order_notional_krw_total"),
        "fundable_count_at_capital": check_payload.get("fundable_count_at_capital"),
        "fundable_symbols_at_capital": check_payload.get("fundable_symbols_at_capital"),
        "latest_index_path": latest_index.get("latest_index_path") or str(
            SHADOW_DIR / "shadow_live_initial_adaptive_latest.json"
        ),
        "check_json_path": latest_index.get("check_json_path"),
        "check_md_path": latest_index.get("check_md_path"),
        "check_history_json_path": latest_index.get("check_history_json_path"),
        "check_history_md_path": latest_index.get("check_history_md_path"),
        "plan_path": latest_index.get("plan_path"),
        "preflight_path": latest_index.get("preflight_path"),
        "report_path": latest_index.get("report_path"),
        "refresh_and_show_command_bat": r"tools\analysis\refresh_and_show_split_models_initial_entry_latest.bat",
        "refresh_and_show_command_ps1": r"tools\analysis\refresh_and_show_split_models_initial_entry_latest.ps1",
        "submit_and_show_command_bat": r"tools\analysis\submit_and_show_split_models_initial_entry_latest.bat",
        "submit_and_show_command_ps1": r"tools\analysis\submit_and_show_split_models_initial_entry_latest.ps1",
        "autotrade_task_name": task_status_payload.get("task_name"),
        "autotrade_task_state": task_status_payload.get("state"),
        "autotrade_task_hardening_verdict": task_hardening_verdict,
        "autotrade_task_hardening_failures": task_hardening_failures,
        "autotrade_task_status_command_bat": r"tools\analysis\show_split_models_initial_entry_autotrade_task_status.bat",
        "autotrade_task_status_command_ps1": r"tools\analysis\show_split_models_initial_entry_autotrade_task_status.ps1",
        "autotrade_task_harden_as_admin_command_bat": r"tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.bat",
        "autotrade_task_harden_as_admin_command_ps1": r"tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.ps1",
        "submit_ready": submit_ready,
        "unattended_operation_ready": unattended_operation_ready,
        "recommended_next_action": recommended_next_action,
        "recommended_next_reason": recommended_next_reason,
        "recommended_next_command_bat": recommended_next_command_bat,
        "recommended_next_command_ps1": recommended_next_command_ps1,
        "operational_next_action": operational_next_action,
        "operational_next_reason": operational_next_reason,
        "operational_next_command_bat": operational_next_command_bat,
        "operational_next_command_ps1": operational_next_command_ps1,
    }


def render_status_text(payload: dict[str, object]) -> str:
    planned_symbols = ", ".join(str(item) for item in payload.get("planned_symbols", []) or []) or "-"
    fundable_symbols = ", ".join(str(item) for item in payload.get("fundable_symbols_at_capital", []) or []) or "-"
    task_failures = ",".join(str(item) for item in payload.get("autotrade_task_hardening_failures", []) or []) or "-"
    lines = [
        "Split Models Initial Entry Latest",
        f"capital_slug={payload.get('capital_slug', '-')}",
        f"total_capital={float(payload.get('total_capital', 0.0) or 0.0):,.0f}",
        f"submit_live_requested={payload.get('submit_live_requested', False)}",
        f"check_timestamp={payload.get('check_timestamp', '-')}",
        f"check_verdict={payload.get('check_verdict', '-')}",
        f"preflight_verdict={payload.get('preflight_verdict', '-')}",
        f"live_readiness={payload.get('live_readiness', '-')}",
        f"operator_gate_verdict={payload.get('operator_gate_verdict', '-')}",
        f"archive_stability_verdict={payload.get('archive_stability_verdict', '-')}",
        f"planned_count={payload.get('planned_count', 0)}",
        f"skipped_count={payload.get('skipped_count', 0)}",
        f"planned_symbols={planned_symbols}",
        f"planned_quantity_total={payload.get('planned_quantity_total', 0)}",
        f"estimated_order_notional_krw_total={float(payload.get('estimated_order_notional_krw_total', 0.0) or 0.0):,.0f}",
        f"fundable_count_at_capital={payload.get('fundable_count_at_capital', 0)}",
        f"fundable_symbols_at_capital={fundable_symbols}",
        f"latest_index_path={payload.get('latest_index_path', '-')}",
        f"check_json_path={payload.get('check_json_path', '-')}",
        f"check_md_path={payload.get('check_md_path', '-')}",
        f"check_history_json_path={payload.get('check_history_json_path', '-')}",
        f"check_history_md_path={payload.get('check_history_md_path', '-')}",
        f"plan_path={payload.get('plan_path', '-')}",
        f"preflight_path={payload.get('preflight_path', '-')}",
        f"report_path={payload.get('report_path', '-')}",
        f"refresh_and_show_command_bat={payload.get('refresh_and_show_command_bat', '-')}",
        f"refresh_and_show_command_ps1={payload.get('refresh_and_show_command_ps1', '-')}",
        f"submit_and_show_command_bat={payload.get('submit_and_show_command_bat', '-')}",
        f"submit_and_show_command_ps1={payload.get('submit_and_show_command_ps1', '-')}",
        f"autotrade_task_name={payload.get('autotrade_task_name', '-')}",
        f"autotrade_task_state={payload.get('autotrade_task_state', '-')}",
        f"autotrade_task_hardening_verdict={payload.get('autotrade_task_hardening_verdict', '-')}",
        f"autotrade_task_hardening_failures={task_failures}",
        f"autotrade_task_status_command_bat={payload.get('autotrade_task_status_command_bat', '-')}",
        f"autotrade_task_status_command_ps1={payload.get('autotrade_task_status_command_ps1', '-')}",
        f"autotrade_task_harden_as_admin_command_bat={payload.get('autotrade_task_harden_as_admin_command_bat', '-')}",
        f"autotrade_task_harden_as_admin_command_ps1={payload.get('autotrade_task_harden_as_admin_command_ps1', '-')}",
        f"submit_ready={payload.get('submit_ready', False)}",
        f"unattended_operation_ready={payload.get('unattended_operation_ready', False)}",
        f"recommended_next_action={payload.get('recommended_next_action', '-')}",
        f"recommended_next_reason={payload.get('recommended_next_reason', '-')}",
        f"recommended_next_command_bat={payload.get('recommended_next_command_bat', '-')}",
        f"recommended_next_command_ps1={payload.get('recommended_next_command_ps1', '-')}",
        f"operational_next_action={payload.get('operational_next_action', '-')}",
        f"operational_next_reason={payload.get('operational_next_reason', '-')}",
        f"operational_next_command_bat={payload.get('operational_next_command_bat', '-')}",
        f"operational_next_command_ps1={payload.get('operational_next_command_ps1', '-')}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--latest-index-path",
        default=str(SHADOW_DIR / "shadow_live_initial_adaptive_latest.json"),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    latest_index_path = Path(args.latest_index_path)
    if not latest_index_path.exists():
        raise SystemExit("missing_latest_index")

    latest_index = _load_json(latest_index_path)
    check_json_path = latest_index.get("check_json_path")
    if not check_json_path:
        raise SystemExit("latest_index_missing_check_json_path")
    check_payload = _load_json(str(check_json_path))
    payload = build_status_payload(latest_index, check_payload)

    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(render_status_text(payload), end="")


if __name__ == "__main__":
    main()
