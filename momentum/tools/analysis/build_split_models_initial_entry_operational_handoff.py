from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.analysis import verify_split_models_initial_entry_operational_readiness as verify_ready


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_handoff_payload(readiness_payload: dict[str, object]) -> dict[str, object]:
    verdict = str(
        readiness_payload.get("operational_readiness_verdict", "FAIL") or "FAIL"
    )
    ready = verdict == "PASS"
    if ready:
        headline = "split_models_initial_entry_is_ready_for_unattended_operation"
        blocker = "-"
        next_step = "monitor_scheduled_autotrade_run"
    else:
        headline = "split_models_initial_entry_is_not_ready_for_unattended_operation"
        blocker = str(
            readiness_payload.get("operational_readiness_reason", "")
            or "unattended_operation_not_ready"
        )
        next_step = str(readiness_payload.get("next_action", "") or "inspect_status")
    return {
        "handoff_verdict": verdict,
        "handoff_headline": headline,
        "primary_blocker": blocker,
        "next_step": next_step,
        "next_reason": readiness_payload.get("next_reason"),
        "next_command_bat": readiness_payload.get("next_command_bat"),
        "next_command_ps1": readiness_payload.get("next_command_ps1"),
        "submit_ready": readiness_payload.get("submit_ready"),
        "unattended_operation_ready": readiness_payload.get(
            "unattended_operation_ready"
        ),
        "capital_slug": readiness_payload.get("capital_slug"),
        "check_timestamp": readiness_payload.get("check_timestamp"),
        "planned_count": readiness_payload.get("planned_count"),
        "planned_symbols": readiness_payload.get("planned_symbols"),
        "autotrade_task_name": readiness_payload.get("autotrade_task_name"),
        "autotrade_task_state": readiness_payload.get("autotrade_task_state"),
        "autotrade_task_hardening_verdict": readiness_payload.get(
            "autotrade_task_hardening_verdict"
        ),
        "autotrade_task_hardening_failures": readiness_payload.get(
            "autotrade_task_hardening_failures"
        ),
        "latest_index_path": readiness_payload.get("latest_index_path"),
        "check_json_path": readiness_payload.get("check_json_path"),
        "report_path": readiness_payload.get("report_path"),
    }


def render_handoff_text(payload: dict[str, object]) -> str:
    planned_symbols = ", ".join(str(item) for item in payload.get("planned_symbols", []) or []) or "-"
    hardening_failures = ",".join(
        str(item) for item in payload.get("autotrade_task_hardening_failures", []) or []
    ) or "-"
    lines = [
        "Split Models Initial Entry Operational Handoff",
        f"handoff_verdict={payload.get('handoff_verdict', '-')}",
        f"handoff_headline={payload.get('handoff_headline', '-')}",
        f"primary_blocker={payload.get('primary_blocker', '-')}",
        f"next_step={payload.get('next_step', '-')}",
        f"next_reason={payload.get('next_reason', '-')}",
        f"next_command_bat={payload.get('next_command_bat', '-')}",
        f"next_command_ps1={payload.get('next_command_ps1', '-')}",
        f"submit_ready={payload.get('submit_ready', False)}",
        f"unattended_operation_ready={payload.get('unattended_operation_ready', False)}",
        f"capital_slug={payload.get('capital_slug', '-')}",
        f"check_timestamp={payload.get('check_timestamp', '-')}",
        f"planned_count={payload.get('planned_count', 0)}",
        f"planned_symbols={planned_symbols}",
        f"autotrade_task_name={payload.get('autotrade_task_name', '-')}",
        f"autotrade_task_state={payload.get('autotrade_task_state', '-')}",
        f"autotrade_task_hardening_verdict={payload.get('autotrade_task_hardening_verdict', '-')}",
        f"autotrade_task_hardening_failures={hardening_failures}",
        f"latest_index_path={payload.get('latest_index_path', '-')}",
        f"check_json_path={payload.get('check_json_path', '-')}",
        f"report_path={payload.get('report_path', '-')}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--readiness-json-path",
        default="",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-text-path")
    args = parser.parse_args()

    readiness_json_path = str(args.readiness_json_path or "").strip()
    readiness_path = Path(readiness_json_path) if readiness_json_path else None
    if readiness_path and readiness_path.exists():
        readiness_payload = _load_json(readiness_path)
    else:
        latest_index_path = SHADOW_DIR / "shadow_live_initial_adaptive_latest.json"
        latest_index = _load_json(latest_index_path)
        check_json_path = latest_index.get("check_json_path")
        if not check_json_path:
            raise SystemExit("latest_index_missing_check_json_path")
        check_payload = _load_json(str(check_json_path))
        status_payload = verify_ready.show_latest.build_status_payload(
            latest_index, check_payload
        )
        readiness_payload = verify_ready.build_readiness_payload(status_payload)

    payload = build_handoff_payload(readiness_payload)
    text_output = render_handoff_text(payload)

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
