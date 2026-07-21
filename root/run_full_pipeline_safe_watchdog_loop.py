from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_full_pipeline_safe_supervisor as supervisor


ROOT = Path(r"C:\AI")
REPORTS = ROOT / "reports" / "operations"
LATEST_JSON = REPORTS / "full_pipeline_safe_watchdog_latest.json"
DUPLICATE_EXIT_JSON = REPORTS / "full_pipeline_safe_watchdog_duplicate_exit_latest.json"


def unbounded_cycles(cycles: int) -> bool:
    return cycles <= 0


def cycles_requested_value(cycles: int) -> int | str:
    return "unbounded" if unbounded_cycles(cycles) else cycles


def existing_watchdog_processes() -> list[dict[str, Any]]:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.CommandLine -like '*run_full_pipeline_safe_watchdog_loop.py*' } | "
        "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress",
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=20)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    payload = json.loads(result.stdout)
    rows = payload if isinstance(payload, list) else [payload]
    current_pid = os.getpid()
    filtered: list[dict[str, Any]] = []
    for row in rows:
        command_line = str(row.get("CommandLine") or "")
        lower = command_line.lower()
        if int(row.get("ProcessId") or -1) == current_pid:
            continue
        if "get-ciminstance" in lower or "convertto-json" in lower:
            continue
        if "powershell" in lower and "-command" in lower:
            continue
        filtered.append(row)
    return filtered


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--sleep-seconds", type=float, default=60.0)
    parser.add_argument("--run-once-safe-each-cycle", action="store_true")
    args = parser.parse_args(argv)

    existing = existing_watchdog_processes()
    if existing:
        payload = {
            "status": "duplicate_exit",
            "existing_watchdog_processes": existing,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "safety": supervisor.SAFETY,
        }
        write_json(DUPLICATE_EXIT_JSON, payload)
        print(json.dumps(payload, ensure_ascii=False))
        return 2

    completed = 0
    while True:
        results = supervisor.run_once_safe_actions() if args.run_once_safe_each_cycle else []
        completed += 1
        payload = {
            "status": "running",
            "cycles_requested": cycles_requested_value(args.cycles),
            "unbounded": unbounded_cycles(args.cycles),
            "cycles_completed": completed,
            "run_once_safe_each_cycle": args.run_once_safe_each_cycle,
            "last_run_once_safe_results": results,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "safety": supervisor.SAFETY,
        }
        write_json(LATEST_JSON, payload)
        if not unbounded_cycles(args.cycles) and completed >= args.cycles:
            break
        if unbounded_cycles(args.cycles) and completed >= 1:
            break
        time.sleep(args.sleep_seconds)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
