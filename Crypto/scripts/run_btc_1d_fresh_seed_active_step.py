from __future__ import annotations

import json
import shlex
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_fresh_seed_execution_queue import (
    build_report as build_fresh_seed_execution_queue,
)
from scripts.compare_btc_1d_post_void_new_family_queue import (
    build_report as build_post_void_new_family_queue,
)


ANALYSIS_DIR = ROOT / "analysis_results"
STATE_PATH = ANALYSIS_DIR / "btc_1d_fresh_seed_active_step_state_latest.json"
STALE_STATE_RESET_HOURS = 12


def _normalize_runner(runner: str) -> list[str]:
    parts = shlex.split(runner, posix=False)
    if not parts:
        raise ValueError("Fresh-seed runner string is empty.")
    if parts[0].lower() == "python":
        return [sys.executable, *parts[1:]]
    return parts


def _write_latest(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _step_key(step: dict) -> str:
    return "|".join(
        [
            str(step.get("family", "")),
            str(step.get("seed_variant", "")),
            str(step.get("phase", "")),
            str(step.get("step", "")),
            str(step.get("runner", "")),
        ]
    )


def _queue_signature(execution_queue: list[dict]) -> list[str]:
    return [_step_key(step) for step in execution_queue]


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _state_is_stale(state: dict, now: datetime | None = None) -> bool:
    updated_at = _parse_utc(str(state.get("updated_at") or ""))
    if updated_at is None:
        return False
    now = now or datetime.now(tz=UTC)
    age_hours = (now - updated_at).total_seconds() / 3600
    return age_hours >= STALE_STATE_RESET_HOURS


def _load_state(execution_queue: list[dict], *, force_reset: bool = False) -> dict:
    signature = _queue_signature(execution_queue)
    if force_reset:
        return {
            "queue_signature": signature,
            "completed_step_keys": [],
            "failed_step_keys": [],
            "reset_reason": "force_reset_requested",
        }
    if not STATE_PATH.exists():
        return {"queue_signature": signature, "completed_step_keys": [], "failed_step_keys": []}
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"queue_signature": signature, "completed_step_keys": [], "failed_step_keys": []}
    if list(state.get("queue_signature", [])) != signature:
        signature_set = set(signature)
        completed = [key for key in state.get("completed_step_keys", []) if key in signature_set]
        failed = [key for key in state.get("failed_step_keys", []) if key in signature_set]
        return {"queue_signature": signature, "completed_step_keys": completed, "failed_step_keys": failed}
    if _state_is_stale(state) and len(state.get("completed_step_keys", [])) >= len(signature):
        return {
            "queue_signature": signature,
            "completed_step_keys": [],
            "failed_step_keys": [],
            "previous_completed_count": len(state.get("completed_step_keys", [])),
            "previous_updated_at": state.get("updated_at"),
            "reset_reason": f"stale_completed_state_older_than_{STALE_STATE_RESET_HOURS}h",
        }
    state.setdefault("queue_signature", signature)
    state.setdefault("completed_step_keys", [])
    state.setdefault("failed_step_keys", [])
    return state


def _write_state(state: dict) -> None:
    _write_latest(STATE_PATH, state)


def _step_is_unlocked(step: dict) -> bool:
    return str(step.get("status") or "") not in {"standby", "deferred"}


def _select_active_step(fresh_seed_queue: dict) -> dict | None:
    execution_queue = fresh_seed_queue["execution_queue"]
    seed_snapshot = fresh_seed_queue.get("seed_snapshot", {})
    primary_snapshot = seed_snapshot.get("primary") or {}
    force_reset = primary_snapshot.get("attack_conversion_label") == "missing_archived_artifact"
    state = _load_state(execution_queue, force_reset=force_reset)
    completed = set(state.get("completed_step_keys", []))
    for step in execution_queue:
        if not _step_is_unlocked(step):
            continue
        if _step_key(step) not in completed:
            return step
    primary_completed_steps = [
        step
        for step in execution_queue
        if int(step.get("priority_rank") or 0) == 1 and _step_key(step) in completed
    ]
    primary_reached_stage_review = any(step.get("phase") == "stage_review" for step in primary_completed_steps)
    if primary_completed_steps and not primary_reached_stage_review:
        for step in execution_queue:
            if str(step.get("status") or "") == "standby" and _step_key(step) not in completed:
                return {**step, "status": "promoted_from_standby_after_primary_seed_batch"}
    return None


def _legacy_select_active_step(fresh_seed_queue: dict) -> dict:
    execution_queue = fresh_seed_queue["execution_queue"]
    latest_path = ANALYSIS_DIR / "btc_1d_fresh_seed_active_step_latest.json"
    if not latest_path.exists():
        return execution_queue[0]
    try:
        latest = json.loads(latest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return execution_queue[0]

    previous_step = (latest.get("active_step") or {}).get("step")
    previous_family = (latest.get("active_step") or {}).get("family")
    previous_status = (latest.get("execution_result") or {}).get("status")
    if not previous_step or not previous_family:
        return execution_queue[0]

    for index, row in enumerate(execution_queue):
        if row.get("family") != previous_family or row.get("step") != previous_step:
            continue
        if previous_status == "ok" and index + 1 < len(execution_queue):
            next_row = execution_queue[index + 1]
            if next_row.get("family") == previous_family or previous_step == "stage_review":
                return next_row
        if previous_status != "ok":
            return row
        break
    return execution_queue[0]


def _render_markdown(report: dict) -> str:
    queue = report["queue_snapshot"]
    step = report["active_step"]
    execution = report["execution_result"]
    return "\n".join(
        [
            "# BTC 1d Fresh Seed Active Step",
            "",
            f"- Generated at: `{report['generated_at']}`",
            f"- Active family: `{queue['active_family']}`",
            f"- Active variant: `{queue['active_variant']}`",
            f"- Queue mode: `{queue['queue_mode']}`",
            f"- Trigger source: `{queue['trigger_source']}`",
            f"- Step: `{step['step']}`",
            f"- Phase: `{step['phase']}`",
            f"- Runner: `{step['runner']}`",
            f"- Return code: `{execution['return_code']}`",
            f"- Status: `{execution['status']}`",
            f"- Duration seconds: `{execution['duration_seconds']}`",
            f"- Log path: `{execution['log_path']}`",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    post_void_queue = build_post_void_new_family_queue()
    fresh_seed_queue = build_fresh_seed_execution_queue()
    active_step = _select_active_step(fresh_seed_queue)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    if active_step is None:
        finish = datetime.now(tz=UTC)
        report = {
            "generated_at": finish.isoformat(),
            "queue_snapshot": {
                "queue_mode": fresh_seed_queue["queue_summary"]["queue_mode"],
                "active_family": fresh_seed_queue["queue_summary"]["primary_seed_family"],
                "active_variant": fresh_seed_queue["queue_summary"]["primary_seed_variant"],
                "trigger_source": post_void_queue["queue_verdict"]["selected_family"],
                "post_void_next_step": post_void_queue["queue_verdict"]["next_step_now"],
                "post_void_next_runner": post_void_queue["queue_verdict"]["next_runner_now"],
            },
            "active_step": {
                "family": None,
                "phase": "queue_complete",
                "step": "idle_completed",
                "runner": None,
                "reason": "All fresh-seed execution queue steps have already completed for the current queue signature.",
            },
            "execution_result": {
                "status": "idle_completed",
                "return_code": 0,
                "duration_seconds": 0.0,
                "log_path": None,
            },
        }
        json_path = ANALYSIS_DIR / f"btc_1d_fresh_seed_active_step_{stamp}.json"
        md_path = ANALYSIS_DIR / f"btc_1d_fresh_seed_active_step_{stamp}.md"
        latest_json = ANALYSIS_DIR / "btc_1d_fresh_seed_active_step_latest.json"
        latest_md = ANALYSIS_DIR / "btc_1d_fresh_seed_active_step_latest.md"
        payload = json.dumps(report, indent=2)
        markdown = _render_markdown(report)
        json_path.write_text(payload, encoding="utf-8")
        md_path.write_text(markdown, encoding="utf-8")
        latest_json.write_text(payload, encoding="utf-8")
        latest_md.write_text(markdown, encoding="utf-8")
        print(
            json.dumps(
                {
                    "report_json_path": str(json_path),
                    "report_md_path": str(md_path),
                    "latest_json_path": str(latest_json),
                    "latest_md_path": str(latest_md),
                    "report": report,
                },
                indent=2,
            )
        )
        return 0
    runner = str(active_step["runner"])
    command = _normalize_runner(runner)

    log_path = ANALYSIS_DIR / f"btc_1d_fresh_seed_active_step_{stamp}.log"
    start = datetime.now(tz=UTC)

    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"[start] {start.isoformat()}\n")
        log_file.write(f"[runner] {runner}\n")
        log_file.write(f"[cwd] {ROOT}\n\n")
        log_file.flush()
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )

    finish = datetime.now(tz=UTC)
    duration_seconds = round((finish - start).total_seconds(), 2)
    status = "ok" if completed.returncode == 0 else "failed"

    report = {
        "generated_at": finish.isoformat(),
        "queue_snapshot": {
            "queue_mode": fresh_seed_queue["queue_summary"]["queue_mode"],
            "active_family": fresh_seed_queue["queue_summary"]["primary_seed_family"],
            "active_variant": fresh_seed_queue["queue_summary"]["primary_seed_variant"],
            "trigger_source": post_void_queue["queue_verdict"]["selected_family"],
            "post_void_next_step": post_void_queue["queue_verdict"]["next_step_now"],
            "post_void_next_runner": post_void_queue["queue_verdict"]["next_runner_now"],
        },
        "active_step": {
            "family": active_step["family"],
            "phase": active_step["phase"],
            "step": active_step["step"],
            "runner": runner,
            "reason": active_step["reason"],
        },
        "execution_result": {
            "status": status,
            "return_code": completed.returncode,
            "duration_seconds": duration_seconds,
            "log_path": str(log_path),
        },
    }

    json_path = ANALYSIS_DIR / f"btc_1d_fresh_seed_active_step_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_fresh_seed_active_step_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_fresh_seed_active_step_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_fresh_seed_active_step_latest.md"

    payload = json.dumps(report, indent=2)
    markdown = _render_markdown(report)
    json_path.write_text(payload, encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    latest_json.write_text(payload, encoding="utf-8")
    latest_md.write_text(markdown, encoding="utf-8")

    state = _load_state(fresh_seed_queue["execution_queue"])
    step_key = _step_key(active_step)
    completed_keys = list(state.get("completed_step_keys", []))
    failed_keys = list(state.get("failed_step_keys", []))
    if status == "ok":
        if step_key not in completed_keys:
            completed_keys.append(step_key)
        failed_keys = [key for key in failed_keys if key != step_key]
    else:
        if step_key not in failed_keys:
            failed_keys.append(step_key)
    state.update(
        {
            "updated_at": finish.isoformat(),
            "last_step_key": step_key,
            "last_status": status,
            "completed_step_keys": completed_keys,
            "failed_step_keys": failed_keys,
            "completed_count": len(completed_keys),
            "queue_count": len(state.get("queue_signature", [])),
        }
    )
    _write_state(state)

    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "latest_json_path": str(latest_json),
                "latest_md_path": str(latest_md),
                "report": report,
            },
            indent=2,
        )
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
