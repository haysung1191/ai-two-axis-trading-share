from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.analysis import show_split_models_initial_entry_latest as show_latest


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _run(args: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def _load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_status_payload(latest_index_path: str | Path) -> dict[str, object]:
    latest_index = _load_json(latest_index_path)
    check_json_path = latest_index.get("check_json_path")
    if not check_json_path:
        raise SystemExit("latest_index_missing_check_json_path")
    check_payload = _load_json(str(check_json_path))
    return show_latest.build_status_payload(latest_index, check_payload)


def _was_already_submitted(status_payload: dict[str, object], allow_repeat_submit: bool) -> tuple[bool, str]:
    if allow_repeat_submit:
        return False, "repeat_submit_allowed"
    submit_summary_path = str(status_payload.get("submit_summary_path", "") or "")
    if not submit_summary_path or not Path(submit_summary_path).exists():
        return False, "submit_summary_missing"
    submit_summary = _load_json(submit_summary_path)
    latest_plan_hash = str(status_payload.get("plan_sha256", "") or "")
    latest_preflight_hash = str(status_payload.get("preflight_sha256", "") or "")
    submitted_plan_hash = str(submit_summary.get("submitted_plan_sha256", "") or "")
    submitted_preflight_hash = str(submit_summary.get("preflight_sha256", "") or "")
    if latest_plan_hash and latest_preflight_hash and latest_plan_hash == submitted_plan_hash and latest_preflight_hash == submitted_preflight_hash:
        return True, "same_plan_and_preflight_already_submitted"
    return False, "new_submission_required"


def build_decision_payload(
    status_payload: dict[str, object],
    *,
    enable_live_auto_submit: bool,
    allow_repeat_submit: bool,
    already_submitted: bool,
    duplicate_reason: str,
) -> dict[str, object]:
    submit_ready = bool(status_payload.get("submit_ready", False))
    unattended_operation_ready = bool(
        status_payload.get("unattended_operation_ready", submit_ready)
    )
    live_submit_env_allowed = os.environ.get("MOMENTUM_ALLOW_LIVE_AUTO_SUBMIT") == "1"
    if not submit_ready:
        action = "refresh_only"
        reason = str(status_payload.get("recommended_next_reason", "") or "submit_not_ready")
    elif not unattended_operation_ready:
        action = "blocked_until_operational_ready"
        reason = str(
            status_payload.get("operational_next_reason", "")
            or "unattended_operation_not_ready"
        )
    elif not enable_live_auto_submit:
        action = "ready_but_live_submit_disabled"
        reason = "submit_ready_but_enable_live_auto_submit_not_set"
    elif not live_submit_env_allowed:
        action = "ready_but_live_submit_env_guard_missing"
        reason = "set_MOMENTUM_ALLOW_LIVE_AUTO_SUBMIT_1_to_allow_unattended_live_submit"
    elif already_submitted:
        action = "skip_duplicate_submission"
        reason = duplicate_reason
    else:
        action = "submit_and_show"
        reason = "submit_ready_and_not_previously_submitted"
    return {
        "action": action,
        "reason": reason,
        "submit_ready": submit_ready,
        "unattended_operation_ready": unattended_operation_ready,
        "enable_live_auto_submit": bool(enable_live_auto_submit),
        "live_submit_env_allowed": live_submit_env_allowed,
        "recommended_next_action": str(status_payload.get("recommended_next_action", "") or ""),
        "recommended_next_reason": str(status_payload.get("recommended_next_reason", "") or ""),
        "operational_next_action": str(status_payload.get("operational_next_action", "") or ""),
        "operational_next_reason": str(status_payload.get("operational_next_reason", "") or ""),
        "allow_repeat_submit": bool(allow_repeat_submit),
        "capital_slug": status_payload.get("capital_slug"),
        "check_timestamp": status_payload.get("check_timestamp"),
        "planned_symbols": status_payload.get("planned_symbols"),
        "planned_count": status_payload.get("planned_count"),
        "skipped_count": status_payload.get("skipped_count"),
        "latest_index_path": status_payload.get("latest_index_path"),
        "submit_summary_path": status_payload.get("submit_summary_path"),
        "operational_next_command_bat": status_payload.get("operational_next_command_bat"),
        "operational_next_command_ps1": status_payload.get("operational_next_command_ps1"),
    }


def render_decision_text(payload: dict[str, object]) -> str:
    planned_symbols = ", ".join(str(item) for item in payload.get("planned_symbols", []) or []) or "-"
    lines = [
        "Split Models Initial Entry Auto Trade",
        f"action={payload.get('action', '-')}",
        f"reason={payload.get('reason', '-')}",
        f"submit_ready={payload.get('submit_ready', False)}",
        f"unattended_operation_ready={payload.get('unattended_operation_ready', False)}",
        f"enable_live_auto_submit={payload.get('enable_live_auto_submit', False)}",
        f"live_submit_env_allowed={payload.get('live_submit_env_allowed', False)}",
        f"recommended_next_action={payload.get('recommended_next_action', '-')}",
        f"recommended_next_reason={payload.get('recommended_next_reason', '-')}",
        f"operational_next_action={payload.get('operational_next_action', '-')}",
        f"operational_next_reason={payload.get('operational_next_reason', '-')}",
        f"allow_repeat_submit={payload.get('allow_repeat_submit', False)}",
        f"capital_slug={payload.get('capital_slug', '-')}",
        f"check_timestamp={payload.get('check_timestamp', '-')}",
        f"planned_count={payload.get('planned_count', 0)}",
        f"skipped_count={payload.get('skipped_count', 0)}",
        f"planned_symbols={planned_symbols}",
        f"latest_index_path={payload.get('latest_index_path', '-')}",
        f"submit_summary_path={payload.get('submit_summary_path', '-')}",
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
    parser.add_argument("--enable-live-auto-submit", action="store_true")
    parser.add_argument("--allow-repeat-submit", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    python = sys.executable
    latest_index_path = args.latest_index_path

    _run(
        [
            python,
            "tools/pipelines/submit_split_models_initial_entry_from_latest.py",
            "--latest-index-path",
            latest_index_path,
        ]
    )
    status_payload = _load_status_payload(latest_index_path)
    already_submitted, duplicate_reason = _was_already_submitted(status_payload, args.allow_repeat_submit)
    decision_payload = build_decision_payload(
        status_payload,
        enable_live_auto_submit=args.enable_live_auto_submit,
        allow_repeat_submit=args.allow_repeat_submit,
        already_submitted=already_submitted,
        duplicate_reason=duplicate_reason,
    )

    if decision_payload["action"] == "submit_and_show":
        _run(
            [
                python,
                "tools/analysis/submit_and_show_split_models_initial_entry_latest.py",
                "--latest-index-path",
                latest_index_path,
            ]
        )
        status_payload = _load_status_payload(latest_index_path)
        already_submitted, duplicate_reason = _was_already_submitted(status_payload, args.allow_repeat_submit)
        decision_payload = build_decision_payload(
            status_payload,
            enable_live_auto_submit=args.enable_live_auto_submit,
            allow_repeat_submit=args.allow_repeat_submit,
            already_submitted=already_submitted,
            duplicate_reason=duplicate_reason,
        )
        decision_payload["action"] = "submitted"
        decision_payload["reason"] = "submit_executed"

    if args.json:
        print(json.dumps(decision_payload, indent=2))
        return
    print(render_decision_text(decision_payload), end="")


if __name__ == "__main__":
    main()
