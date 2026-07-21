from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
MANIFEST_JSON = ROOT / "output" / "split_models_operational_conversion_manifest.json"
CURRENT_STATE_JSON = ROOT / "output" / "split_models_operational_conversion_current_state.json"
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_handoff"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown(summary: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Split Models Operational Conversion Handoff",
            "",
            f"- status: `{summary['gate_status']}` / `{summary['promotion_status']}`",
            f"- anchor: `{summary['anchor_variant']}`",
            f"- anchor MDD: `{summary['anchor_mdd_display']}`",
            f"- baseline MDD: `{summary['baseline_mdd_display']}`",
            f"- drawdown gap: `{summary['drawdown_gap_vs_baseline_display']}`",
            f"- best quality overlay: `{summary['best_quality_variant']}`",
            f"- recommended representative candidate: `{summary['recommended_representative_variant']}`",
            f"- representative challenger search closed: `{summary['representative_challenger_search_closed']}`",
            f"- representative decision file: `{summary['representative_decision_file']}`",
            f"- representative decision verdict: `{summary['representative_decision_verdict']}`",
            f"- one command to run: `{summary['primary_human_command']}`",
            f"- one command to probe gate: `{summary['gate_probe_command']}`",
            f"- one file to read: `{summary['primary_read_file']}`",
            f"- one dashboard command: `{summary['dashboard_command']}`",
            f"- one dashboard open command: `{summary['dashboard_open_command']}`",
            f"- one dashboard launch command: `{summary['dashboard_launch_command']}`",
            f"- one dashboard file: `{summary['dashboard_file']}`",
            f"- one probe contract file: `{summary['probe_contract_file']}`",
            f"- one probe contract verdict: `{summary['probe_contract_verdict']}`",
            f"- one refresh contract file: `{summary['refresh_contract_file']}`",
            f"- one refresh contract verdict: `{summary['refresh_contract_verdict']}`",
            f"- one entrypoint contract file: `{summary['entrypoint_contract_file']}`",
            f"- one entrypoint contract verdict: `{summary['entrypoint_contract_verdict']}`",
            f"- doctor smoke test status: `{summary['doctor_smoke_test_status']}`",
            f"- doctor smoke return codes: `{summary['doctor_smoke_process_a']}`, `{summary['doctor_smoke_process_b']}`",
            f"- doctor lock event sequence: `{', '.join(summary['doctor_lock_event_sequence'])}`",
            f"- probe smoke test status: `{summary['probe_smoke_test_status']}`",
            f"- probe exit codes: `{summary['python_probe_exit_code']}`, `{summary['powershell_probe_exit_code']}`, `{summary['cmd_probe_exit_code']}`",
            f"- stale lock smoke test status: `{summary['stale_lock_smoke_test_status']}`",
            f"- stale lock sync stdout: `{summary['stale_lock_sync_stdout']}`",
            f"- stale lock dir exists after sync: `{summary['stale_lock_dir_exists_after_sync']}`",
            "",
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = _load_json(MANIFEST_JSON)
    current_state = _load_json(CURRENT_STATE_JSON)
    summary = {
        "handoff_version": 1,
        "gate_status": str(current_state["gate_status"]),
        "promotion_status": str(current_state["promotion_status"]),
        "anchor_variant": str(current_state["anchor_variant"]),
        "anchor_mdd_display": str(current_state["anchor_mdd_display"]),
        "baseline_mdd_display": str(current_state["baseline_mdd_display"]),
        "drawdown_gap_vs_baseline_display": str(current_state["drawdown_gap_vs_baseline_display"]),
        "best_quality_variant": str(current_state["best_quality_variant"]),
        "recommended_representative_variant": str(current_state["recommended_representative_variant"]),
        "representative_challenger_search_closed": bool(current_state["representative_challenger_search_closed"]),
        "representative_decision_file": str(current_state["representative_decision_file"]),
        "representative_decision_verdict": str(current_state["representative_decision_verdict"]),
        "primary_human_command": str(manifest["primary_human_command"]),
        "doctor_command": "python tools/analysis/doctor_split_models_operational_conversion_state.py",
        "sync_command": "python tools/analysis/sync_split_models_operational_conversion_state.py",
        "gate_probe_command": str(manifest["gate_probe_command"]),
        "primary_read_file": str(manifest["primary_read_file"]),
        "dashboard_command": str(manifest["dashboard_command"]),
        "dashboard_open_command": str(manifest["dashboard_open_command"]),
        "dashboard_launch_command": str(manifest["dashboard_launch_command"]),
        "dashboard_file": str(manifest["dashboard_file"]),
        "probe_contract_file": str(manifest["probe_contract_file"]),
        "probe_contract_verdict": str(current_state["probe_contract_verdict"]),
        "refresh_contract_file": str(manifest["refresh_contract_file"]),
        "refresh_contract_verdict": str(current_state["refresh_contract_verdict"]),
        "entrypoint_contract_file": str(manifest["entrypoint_contract_file"]),
        "entrypoint_contract_verdict": str(current_state["entrypoint_contract_verdict"]),
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
    }

    (OUTPUT_DIR / "handoff_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "handoff.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
