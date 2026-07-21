from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.analysis import register_split_models_initial_entry_autotrade_task as register_task


ROOT = REPO_ROOT
DEFAULT_TASK_NAME = register_task.DEFAULT_TASK_NAME


def _run_powershell(command: str, *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def build_inspect_command(*, task_name: str) -> str:
    return (
        f"$t = Get-ScheduledTask -TaskName '{task_name}'; "
        "$t.Principal | Select-Object UserId,LogonType,RunLevel | Format-List; "
        "$t.Settings | Select-Object DisallowStartIfOnBatteries,StopIfGoingOnBatteries,StartWhenAvailable,MultipleInstances,ExecutionTimeLimit | Format-List"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-name", default=DEFAULT_TASK_NAME)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    user_id = f"{os.environ.get('USERDOMAIN', '')}\\{os.environ.get('USERNAME', '')}".strip("\\")
    hardening_command = register_task.build_task_hardening_command(task_name=args.task_name, user_id=user_id)
    inspect_command = build_inspect_command(task_name=args.task_name)

    print(f"task_name={args.task_name}")
    print(f"user_id={user_id}")
    print(f"hardening_command={hardening_command}")
    print(f"inspect_command={inspect_command}")

    if args.dry_run:
        print("dry_run=true")
        return

    _run_powershell(hardening_command)
    print("hardened=true")
    inspect_result = _run_powershell(inspect_command, capture_output=True)
    print(inspect_result.stdout, end="")


if __name__ == "__main__":
    main()
