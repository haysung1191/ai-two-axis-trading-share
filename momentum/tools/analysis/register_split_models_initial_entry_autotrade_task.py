from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"
DEFAULT_TASK_NAME = "MomentumSplitModelsInitialEntryAutoTrade"
DEFAULT_START_TIME = "21:31"
DEFAULT_DAYS = "MON,TUE,WED,THU,FRI"


def build_task_command(*, latest_index_path: str | Path, enable_live_auto_submit: bool) -> str:
    script_path = ROOT / "tools" / "analysis" / "auto_trade_split_models_initial_entry.bat"
    parts = [f'"{script_path}"', "--latest-index-path", f'"{Path(latest_index_path)}"']
    if enable_live_auto_submit:
        parts.append("--enable-live-auto-submit")
    return " ".join(parts)


def build_schtasks_create_args(
    *,
    task_name: str,
    latest_index_path: str | Path,
    start_time: str,
    enable_live_auto_submit: bool,
) -> list[str]:
    return [
        "schtasks",
        "/Create",
        "/F",
        "/SC",
        "WEEKLY",
        "/D",
        DEFAULT_DAYS,
        "/ST",
        start_time,
        "/TN",
        task_name,
        "/TR",
        build_task_command(
            latest_index_path=latest_index_path,
            enable_live_auto_submit=enable_live_auto_submit,
        ),
    ]


def build_task_hardening_command(*, task_name: str, user_id: str) -> str:
    return (
        "$settings = New-ScheduledTaskSettingsSet "
        "-AllowStartIfOnBatteries "
        "-DontStopIfGoingOnBatteries "
        "-StartWhenAvailable "
        "-MultipleInstances IgnoreNew "
        "-ExecutionTimeLimit (New-TimeSpan -Hours 72); "
        f"$principal = New-ScheduledTaskPrincipal -UserId '{user_id}' -LogonType S4U -RunLevel Highest; "
        f"Set-ScheduledTask -TaskName '{task_name}' -Settings $settings -Principal $principal | Out-Null"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-name", default=DEFAULT_TASK_NAME)
    parser.add_argument(
        "--latest-index-path",
        default=str(SHADOW_DIR / "shadow_live_initial_adaptive_latest.json"),
    )
    parser.add_argument("--start-time", default=DEFAULT_START_TIME)
    parser.add_argument("--enable-live-auto-submit", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    create_args = build_schtasks_create_args(
        task_name=args.task_name,
        latest_index_path=args.latest_index_path,
        start_time=args.start_time,
        enable_live_auto_submit=args.enable_live_auto_submit,
    )
    user_id = f"{os.environ.get('USERDOMAIN', '')}\\{os.environ.get('USERNAME', '')}".strip("\\")

    print(f"task_name={args.task_name}")
    print(f"latest_index_path={Path(args.latest_index_path)}")
    print(f"start_time={args.start_time}")
    print(f"user_id={user_id}")
    print(f"enable_live_auto_submit={str(bool(args.enable_live_auto_submit)).lower()}")
    print(f"task_command={build_task_command(latest_index_path=args.latest_index_path, enable_live_auto_submit=args.enable_live_auto_submit)}")
    print(f"task_hardening_command={build_task_hardening_command(task_name=args.task_name, user_id=user_id)}")

    if args.dry_run:
        print("dry_run=true")
        return

    subprocess.run(create_args, cwd=ROOT, check=True)
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            build_task_hardening_command(task_name=args.task_name, user_id=user_id),
        ],
        cwd=ROOT,
        check=True,
    )
    print("registered=true")


if __name__ == "__main__":
    main()
