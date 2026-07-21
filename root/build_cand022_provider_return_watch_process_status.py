from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/live_readiness/CAND-022_provider_return_watch_process_status.latest.json"
REPORT_MD = ROOT / "reports/live_readiness/CAND-022_provider_return_watch_process_status.latest.md"
WATCH_REPORT_JSON = ROOT / "reports/live_readiness/CAND-022_provider_return_watch.latest.json"
WATCH_SCRIPT = "run_cand022_provider_return_watch.py"
SAFETY = {
    "paper_enabled": False,
    "live_enabled": False,
    "broker_submit_allowed": False,
    "private_submit_used": False,
    "real_orders": 0,
    "order_intent_created": False,
    "pretrade_firewall_default_decision": "BLOCK",
}


def read_json_optional(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _current_kst() -> datetime:
    return datetime.now(tz=KST)


def _parse_creation_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    match = re.search(r"/Date\((\d+)\)/", raw)
    if match:
        millis = int(match.group(1))
        return datetime.fromtimestamp(millis / 1000, tz=timezone.utc).astimezone(KST)
    try:
        # CIM datetime format can be yyyyMMddHHmmss.xxxxxx+utcOffsetMinutes.
        compact = raw[:14]
        return datetime.strptime(compact, "%Y%m%d%H%M%S").replace(tzinfo=KST)
    except ValueError:
        return None


def _parse_int_arg(command_line: str, name: str, default: int) -> int:
    match = re.search(rf"--{re.escape(name)}\s+(\d+)", command_line)
    return int(match.group(1)) if match else default


def _watcher_started(row: dict, generated_at: datetime) -> dict:
    command_line = row.get("CommandLine", "") or ""
    created = _parse_creation_date(str(row.get("CreationDate", "")))
    cycles = _parse_int_arg(command_line, "cycles", 180)
    sleep_seconds = _parse_int_arg(command_line, "sleep-seconds", 60)
    expected_duration_minutes = round(cycles * sleep_seconds / 60, 1)
    age_minutes = None
    remaining_minutes = None
    expected_end = None
    if created:
        age_minutes = round(max((generated_at - created).total_seconds(), 0) / 60, 1)
        expected_end_dt = created + timedelta(minutes=expected_duration_minutes)
        expected_end = expected_end_dt.isoformat(timespec="seconds")
        remaining_minutes = round(max((expected_end_dt - generated_at).total_seconds(), 0) / 60, 1)
    return {
        "process_id": int(row.get("ProcessId", 0) or 0),
        "started_at_kst": created.isoformat(timespec="seconds") if created else "",
        "age_minutes": age_minutes,
        "cycles": cycles,
        "sleep_seconds": sleep_seconds,
        "expected_duration_minutes": expected_duration_minutes,
        "expected_end_at_kst": expected_end,
        "remaining_minutes": remaining_minutes,
    }


def _process_rows_from_cim() -> list[dict]:
    command = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -like 'python*' -and $_.CommandLine -like '*run_cand022_provider_return_watch.py*' } | "
        "Select-Object ProcessId,Name,CreationDate,CommandLine | ConvertTo-Json -Depth 3"
    )
    try:
        output = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", command],
            text=True,
            encoding="utf-8",
            errors="replace",
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return []
    if not output:
        return []
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return [row for row in parsed if isinstance(row, dict)]
    return []


def build_report(generated_at: str | None = None, rows: list[dict] | None = None) -> dict:
    generated_dt = datetime.fromisoformat(generated_at) if generated_at else _current_kst()
    if generated_dt.tzinfo is None:
        generated_dt = generated_dt.replace(tzinfo=KST)
    rows = rows if rows is not None else _process_rows_from_cim()
    watch_report = read_json_optional(WATCH_REPORT_JSON, {})
    watch_status = watch_report.get("status", "WAITING_FOR_DISPATCH_CONFIRMATION_OR_RETURNED_FILES")
    blockers = watch_report.get("blockers", [])
    copy_review_ready = watch_status == "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW"
    watch_running = bool(rows)
    if watch_running:
        status = "WATCHER_RUNNING"
    elif copy_review_ready:
        status = "WATCHER_NOT_RUNNING_COPY_REVIEW_READY"
    else:
        status = "WATCHER_NOT_RUNNING_WAITING_FOR_EXTERNAL_INPUT"
    policy = {
        "copy_review_required_before_refresh": bool(watch_report.get("copy_review_required_before_refresh", True)),
        "refresh_stack_invocation_policy": watch_report.get(
            "refresh_stack_invocation_policy",
            "manual_after_returned_to_handoff_copy_review_ready",
        ),
        "refresh_allowed_only_if_copy_review_status": watch_report.get(
            "refresh_allowed_only_if_copy_review_status",
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        ),
        "refresh_forbidden_if_copy_review_status": watch_report.get(
            "refresh_forbidden_if_copy_review_status",
            "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
        ),
    }
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_dt.isoformat(timespec="seconds"),
        "candidate_id": "CAND-022",
        "status": status,
        "watch_running": watch_running,
        "watcher_process_ids": [int(row.get("ProcessId", 0) or 0) for row in rows],
        "watcher_started": [_watcher_started(row, generated_dt) for row in rows],
        "process_rows": rows,
        "provider_return_watch_status": watch_status,
        "provider_return_watch_blockers": blockers,
        "provider_return_watch_policy": policy,
        "copy_review_ready_for_manual_followup": copy_review_ready,
        "ready_for_unattended_wait": watch_running or copy_review_ready,
        "recommended_command_if_not_running": f"python .\\{WATCH_SCRIPT} --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
        "non_goals": [
            "does_not_start_watcher",
            "does_not_stop_processes",
            "does_not_send_email",
            "does_not_write_dispatch_confirmation",
            "does_not_copy_or_generate_provider_csvs",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
        "source_files": {"provider_return_watch": str(WATCH_REPORT_JSON)},
    }


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# CAND-022 Provider Return Watch Process Status",
            "",
            f"- Status: `{report['status']}`",
            f"- Watch running: `{str(report['watch_running']).lower()}`",
            f"- Watcher process ids: `{', '.join(str(pid) for pid in report['watcher_process_ids']) or 'none'}`",
            f"- Provider return watch status: `{report['provider_return_watch_status']}`",
            f"- Ready for unattended wait: `{str(report['ready_for_unattended_wait']).lower()}`",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "watch_running": report["watch_running"], "watcher_process_ids": report["watcher_process_ids"], "latest_json": str(REPORT_JSON), "latest_md": str(REPORT_MD), "safety": SAFETY}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
