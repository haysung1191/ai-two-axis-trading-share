from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.analysis import register_split_models_initial_entry_autotrade_task as register_task


ROOT = REPO_ROOT
DEFAULT_TASK_NAME = register_task.DEFAULT_TASK_NAME
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _run_powershell_json(command: str) -> dict[str, object]:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; {command}",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    return json.loads(result.stdout)


def build_task_status_command(*, task_name: str) -> str:
    return (
        f"$t = Get-ScheduledTask -TaskName '{task_name}'; "
        "$payload = [ordered]@{"
        "TaskName = $t.TaskName; "
        "State = [string]$t.State; "
        "UserId = [string]$t.Principal.UserId; "
        "LogonType = [string]$t.Principal.LogonType; "
        "RunLevel = [string]$t.Principal.RunLevel; "
        "DisallowStartIfOnBatteries = [bool]$t.Settings.DisallowStartIfOnBatteries; "
        "StopIfGoingOnBatteries = [bool]$t.Settings.StopIfGoingOnBatteries; "
        "StartWhenAvailable = [bool]$t.Settings.StartWhenAvailable; "
        "MultipleInstances = [string]$t.Settings.MultipleInstances; "
        "ExecutionTimeLimit = [string]$t.Settings.ExecutionTimeLimit"
        "}; "
        "$payload | ConvertTo-Json -Compress"
    )


def build_status_payload(raw: dict[str, object]) -> dict[str, object]:
    failures: list[str] = []
    if str(raw.get("LogonType", "") or "") != "S4U":
        failures.append(f"logon_type={raw.get('LogonType')}")
    if str(raw.get("RunLevel", "") or "") != "Highest":
        failures.append(f"run_level={raw.get('RunLevel')}")
    if bool(raw.get("DisallowStartIfOnBatteries", True)):
        failures.append("disallow_start_if_on_batteries=true")
    if bool(raw.get("StopIfGoingOnBatteries", True)):
        failures.append("stop_if_going_on_batteries=true")
    if not bool(raw.get("StartWhenAvailable", False)):
        failures.append("start_when_available=false")
    if str(raw.get("MultipleInstances", "") or "") != "IgnoreNew":
        failures.append(f"multiple_instances={raw.get('MultipleInstances')}")
    verdict = "PASS" if not failures else "FAIL"
    recommended_next_action = (
        "none" if verdict == "PASS" else "run_harden_as_admin"
    )
    recommended_next_reason = (
        "task_hardening_requirements_satisfied"
        if verdict == "PASS"
        else "scheduled_task_not_hardened_for_unattended_operation"
    )
    return {
        "task_name": raw.get("TaskName"),
        "state": raw.get("State"),
        "user_id": raw.get("UserId"),
        "logon_type": raw.get("LogonType"),
        "run_level": raw.get("RunLevel"),
        "disallow_start_if_on_batteries": raw.get("DisallowStartIfOnBatteries"),
        "stop_if_going_on_batteries": raw.get("StopIfGoingOnBatteries"),
        "start_when_available": raw.get("StartWhenAvailable"),
        "multiple_instances": raw.get("MultipleInstances"),
        "execution_time_limit": raw.get("ExecutionTimeLimit"),
        "hardening_verdict": verdict,
        "hardening_failures": failures,
        "recommended_next_action": recommended_next_action,
        "recommended_next_reason": recommended_next_reason,
    }


def render_status_text(payload: dict[str, object]) -> str:
    failures = ",".join(str(item) for item in payload.get("hardening_failures", []) or []) or "-"
    lines = [
        "Split Models Initial Entry Autotrade Task",
        f"task_name={payload.get('task_name', '-')}",
        f"state={payload.get('state', '-')}",
        f"user_id={payload.get('user_id', '-')}",
        f"logon_type={payload.get('logon_type', '-')}",
        f"run_level={payload.get('run_level', '-')}",
        f"disallow_start_if_on_batteries={payload.get('disallow_start_if_on_batteries', '-')}",
        f"stop_if_going_on_batteries={payload.get('stop_if_going_on_batteries', '-')}",
        f"start_when_available={payload.get('start_when_available', '-')}",
        f"multiple_instances={payload.get('multiple_instances', '-')}",
        f"execution_time_limit={payload.get('execution_time_limit', '-')}",
        f"hardening_verdict={payload.get('hardening_verdict', '-')}",
        f"hardening_failures={failures}",
        f"recommended_next_action={payload.get('recommended_next_action', '-')}",
        f"recommended_next_reason={payload.get('recommended_next_reason', '-')}",
        r"harden_command_bat=tools\analysis\harden_split_models_initial_entry_autotrade_task.bat",
        r"harden_command_ps1=tools\analysis\harden_split_models_initial_entry_autotrade_task.ps1",
        r"harden_as_admin_command_bat=tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.bat",
        r"harden_as_admin_command_ps1=tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.ps1",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-name", default=DEFAULT_TASK_NAME)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-text-path")
    args = parser.parse_args()

    raw = _run_powershell_json(build_task_status_command(task_name=args.task_name))
    payload = build_status_payload(raw)
    text_output = render_status_text(payload)
    if args.output_json_path:
        output_json_path = Path(args.output_json_path)
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.output_text_path:
        output_text_path = Path(args.output_text_path)
        output_text_path.parent.mkdir(parents=True, exist_ok=True)
        output_text_path.write_text(text_output, encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(text_output, end="")


if __name__ == "__main__":
    main()
