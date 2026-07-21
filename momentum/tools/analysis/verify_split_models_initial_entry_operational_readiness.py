from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.analysis import show_split_models_initial_entry_latest as show_latest


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_readiness_payload(status_payload: dict[str, object]) -> dict[str, object]:
    unattended_operation_ready = bool(
        status_payload.get("unattended_operation_ready", False)
    )
    submit_ready = bool(status_payload.get("submit_ready", False))
    if unattended_operation_ready:
        verdict = "PASS"
        reason = "split_models_initial_entry_unattended_operation_ready"
        next_action = "none"
        next_reason = "all_operational_requirements_satisfied"
    else:
        verdict = "FAIL"
        reason = str(
            status_payload.get("operational_next_reason", "")
            or "split_models_initial_entry_unattended_operation_not_ready"
        )
        next_action = str(
            status_payload.get("operational_next_action", "") or "inspect_latest_status"
        )
        next_reason = str(
            status_payload.get("operational_next_reason", "")
            or "split_models_initial_entry_unattended_operation_not_ready"
        )
    return {
        "operational_readiness_verdict": verdict,
        "operational_readiness_reason": reason,
        "submit_ready": submit_ready,
        "unattended_operation_ready": unattended_operation_ready,
        "capital_slug": status_payload.get("capital_slug"),
        "check_timestamp": status_payload.get("check_timestamp"),
        "planned_symbols": status_payload.get("planned_symbols"),
        "planned_count": status_payload.get("planned_count"),
        "autotrade_task_name": status_payload.get("autotrade_task_name"),
        "autotrade_task_state": status_payload.get("autotrade_task_state"),
        "autotrade_task_hardening_verdict": status_payload.get(
            "autotrade_task_hardening_verdict"
        ),
        "autotrade_task_hardening_failures": status_payload.get(
            "autotrade_task_hardening_failures"
        ),
        "next_action": next_action,
        "next_reason": next_reason,
        "next_command_bat": status_payload.get("operational_next_command_bat"),
        "next_command_ps1": status_payload.get("operational_next_command_ps1"),
        "latest_index_path": status_payload.get("latest_index_path"),
        "check_json_path": status_payload.get("check_json_path"),
        "report_path": status_payload.get("report_path"),
    }


def render_readiness_text(payload: dict[str, object]) -> str:
    planned_symbols = ", ".join(str(item) for item in payload.get("planned_symbols", []) or []) or "-"
    task_failures = ",".join(
        str(item) for item in payload.get("autotrade_task_hardening_failures", []) or []
    ) or "-"
    lines = [
        "Split Models Initial Entry Operational Readiness",
        f"operational_readiness_verdict={payload.get('operational_readiness_verdict', '-')}",
        f"operational_readiness_reason={payload.get('operational_readiness_reason', '-')}",
        f"submit_ready={payload.get('submit_ready', False)}",
        f"unattended_operation_ready={payload.get('unattended_operation_ready', False)}",
        f"capital_slug={payload.get('capital_slug', '-')}",
        f"check_timestamp={payload.get('check_timestamp', '-')}",
        f"planned_count={payload.get('planned_count', 0)}",
        f"planned_symbols={planned_symbols}",
        f"autotrade_task_name={payload.get('autotrade_task_name', '-')}",
        f"autotrade_task_state={payload.get('autotrade_task_state', '-')}",
        f"autotrade_task_hardening_verdict={payload.get('autotrade_task_hardening_verdict', '-')}",
        f"autotrade_task_hardening_failures={task_failures}",
        f"next_action={payload.get('next_action', '-')}",
        f"next_reason={payload.get('next_reason', '-')}",
        f"next_command_bat={payload.get('next_command_bat', '-')}",
        f"next_command_ps1={payload.get('next_command_ps1', '-')}",
        f"latest_index_path={payload.get('latest_index_path', '-')}",
        f"check_json_path={payload.get('check_json_path', '-')}",
        f"report_path={payload.get('report_path', '-')}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--latest-index-path",
        default=str(SHADOW_DIR / "shadow_live_initial_adaptive_latest.json"),
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-text-path")
    args = parser.parse_args()

    latest_index_path = Path(args.latest_index_path)
    latest_index = _load_json(latest_index_path)
    check_json_path = latest_index.get("check_json_path")
    if not check_json_path:
        raise SystemExit("latest_index_missing_check_json_path")
    check_payload = _load_json(str(check_json_path))
    status_payload = show_latest.build_status_payload(latest_index, check_payload)
    payload = build_readiness_payload(status_payload)
    text_output = render_readiness_text(payload)

    if args.output_json_path:
        out_json = Path(args.output_json_path)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.output_text_path:
        out_text = Path(args.output_text_path)
        out_text.parent.mkdir(parents=True, exist_ok=True)
        out_text.write_text(text_output, encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(text_output, end="")


if __name__ == "__main__":
    main()
