from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
CURRENT_STATE_JSON = ROOT / "output" / "split_models_operational_conversion_current_state.json"
OUTPUT_JSON = ROOT / "output" / "split_models_operational_conversion_manifest.json"
OUTPUT_MD = ROOT / "output" / "split_models_operational_conversion_manifest.md"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Manifest",
        "",
        f"- primary human command: `{summary['primary_human_command']}`",
        f"- doctor command: `{summary['doctor_command']}`",
        f"- sync command: `{summary['sync_command']}`",
        f"- refresh command: `{summary['refresh_command']}`",
        f"- gate probe command: `{summary['gate_probe_command']}`",
        f"- dashboard command: `{summary['dashboard_command']}`",
        f"- dashboard open command: `{summary['dashboard_open_command']}`",
        f"- dashboard launch command: `{summary['dashboard_launch_command']}`",
        f"- primary read file: `{summary['primary_read_file']}`",
        f"- dashboard file: `{summary['dashboard_file']}`",
        f"- representative decision file: `{summary['representative_decision_file']}`",
        f"- representative decision verdict: `{summary['representative_decision_verdict']}`",
        f"- probe contract file: `{summary['probe_contract_file']}`",
        f"- probe contract verdict: `{summary['probe_contract_verdict']}`",
        f"- refresh contract file: `{summary['refresh_contract_file']}`",
        f"- refresh contract verdict: `{summary['refresh_contract_verdict']}`",
        f"- entrypoint contract file: `{summary['entrypoint_contract_file']}`",
        f"- entrypoint contract verdict: `{summary['entrypoint_contract_verdict']}`",
        f"- gate status: `{summary['gate_status']}`",
        f"- promotion status: `{summary['promotion_status']}`",
        f"- anchor variant: `{summary['anchor_variant']}`",
        f"- recommended representative candidate: `{summary['recommended_representative_variant']}`",
        f"- representative challenger search closed: `{summary['representative_challenger_search_closed']}`",
        f"- doctor smoke test status: `{summary['doctor_smoke_test_status']}`",
        f"- doctor smoke return codes: `{summary['doctor_smoke_process_a']}`, `{summary['doctor_smoke_process_b']}`",
        f"- doctor lock event sequence: `{', '.join(summary['doctor_lock_event_sequence'])}`",
        f"- probe smoke test status: `{summary['probe_smoke_test_status']}`",
        f"- probe exit codes: `{summary['python_probe_exit_code']}`, `{summary['powershell_probe_exit_code']}`, `{summary['cmd_probe_exit_code']}`",
        f"- stale lock smoke test status: `{summary['stale_lock_smoke_test_status']}`",
        f"- stale lock sync stdout: `{summary['stale_lock_sync_stdout']}`",
        f"- stale lock dir exists after sync: `{summary['stale_lock_dir_exists_after_sync']}`",
        "",
        "Secondary files:",
    ]
    for path in summary["secondary_files"]:
        lines.append(f"- `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    current_state = _load_json(CURRENT_STATE_JSON)
    summary = {
        "manifest_version": 1,
        "primary_human_command": "python tools/analysis/launch_split_models_operational_conversion_dashboard.py",
        "doctor_command": "python tools/analysis/doctor_split_models_operational_conversion_state.py",
        "sync_command": "python tools/analysis/sync_split_models_operational_conversion_state.py",
        "refresh_command": "python tools/analysis/refresh_split_models_operational_conversion_state.py",
        "gate_probe_command": "python tools/analysis/probe_split_models_operational_conversion_gate.py",
        "dashboard_command": "python tools/analysis/generate_split_models_operational_conversion_dashboard.py",
        "dashboard_open_command": "python tools/analysis/open_split_models_operational_conversion_dashboard.py",
        "dashboard_launch_command": "python tools/analysis/launch_split_models_operational_conversion_dashboard.py",
        "primary_read_file": "output/split_models_operational_conversion_current_state.json",
        "dashboard_file": "output/split_models_operational_conversion_dashboard/dashboard.html",
        "representative_decision_file": str(current_state["representative_decision_file"]),
        "representative_decision_verdict": str(current_state["representative_decision_verdict"]),
        "probe_contract_file": "output/split_models_operational_conversion_probe_contract/probe_contract_summary.json",
        "probe_contract_verdict": str(current_state["probe_contract_verdict"]),
        "refresh_contract_file": "output/split_models_operational_conversion_refresh_contract/refresh_contract_summary.json",
        "refresh_contract_verdict": str(current_state["refresh_contract_verdict"]),
        "entrypoint_contract_file": "output/split_models_operational_conversion_entrypoint_contract/entrypoint_contract_summary.json",
        "entrypoint_contract_verdict": str(current_state["entrypoint_contract_verdict"]),
        "gate_status": str(current_state["gate_status"]),
        "promotion_status": str(current_state["promotion_status"]),
        "anchor_variant": str(current_state["anchor_variant"]),
        "recommended_representative_variant": str(current_state["recommended_representative_variant"]),
        "doctor_smoke_test_status": str(current_state["doctor_smoke_test_status"]),
        "doctor_smoke_process_a": int(current_state["doctor_smoke_process_a"]),
        "doctor_smoke_process_b": int(current_state["doctor_smoke_process_b"]),
        "doctor_lock_event_sequence": [str(item) for item in current_state["doctor_lock_event_sequence"]],
        "probe_smoke_test_status": str(current_state["probe_smoke_test_status"]),
        "python_probe_exit_code": int(current_state["python_probe_exit_code"]),
        "powershell_probe_exit_code": int(current_state["powershell_probe_exit_code"]),
        "cmd_probe_exit_code": int(current_state["cmd_probe_exit_code"]),
        "stale_lock_smoke_test_status": str(current_state["stale_lock_smoke_test_status"]),
        "stale_lock_sync_stdout": str(current_state["stale_lock_sync_stdout"]),
        "stale_lock_dir_exists_after_sync": bool(current_state["stale_lock_dir_exists_after_sync"]),
        "secondary_files": [
            "output/split_models_operational_conversion_oos_registration/oos_registration_summary.json",
            "output/split_models_operational_conversion_oos_validation/oos_validation_summary.json",
            "output/split_models_operational_conversion_no_submit_shadow_dry_run/no_submit_shadow_dry_run_summary.json",
            "output/split_models_operational_conversion_oos_robustness_gate/oos_robustness_gate_summary.json",
            str(current_state["verdict_file"]),
            str(current_state["promotion_gate_file"]),
            str(current_state["guardrail_matrix_file"]),
            str(current_state["promotion_recommendation_file"]),
            str(current_state["representative_challenger_closure_file"]),
            str(current_state["representative_decision_file"]),
            "output/split_models_operational_conversion_probe_contract/probe_contract_summary.json",
            "output/split_models_operational_conversion_refresh_contract/refresh_contract_summary.json",
            "output/split_models_operational_conversion_entrypoint_contract/entrypoint_contract_summary.json",
        ],
        "representative_challenger_search_closed": bool(current_state["representative_challenger_search_closed"]),
    }
    OUTPUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    OUTPUT_MD.write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
