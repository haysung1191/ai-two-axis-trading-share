from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
STATUS_SNAPSHOT_JSON = (
    ROOT / "output" / "split_models_operational_conversion_status_snapshot" / "status_snapshot_summary.json"
)
MANIFEST_JSON = ROOT / "output" / "split_models_operational_conversion_manifest.json"
CLOSURE_JSON = ROOT / "output" / "split_models_operational_conversion_closure" / "closure_summary.json"
EXECUTION_GATE_JSON = ROOT / "output" / "split_models_operational_execution_gate" / "execution_gate_summary.json"
OUTPUT_JSON = ROOT / "output" / "split_models_operational_conversion_current_state.json"
OUTPUT_MD = ROOT / "output" / "split_models_operational_conversion_current_state.md"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Current State",
        "",
        f"- gate status: `{summary['gate_status']}`",
        f"- promotion status: `{summary['promotion_status']}`",
        f"- anchor variant: `{summary['anchor_variant']}`",
        f"- anchor MDD: `{summary['anchor_mdd_display']}`",
        f"- baseline MDD: `{summary['baseline_mdd_display']}`",
        f"- drawdown gap vs baseline: `{summary['drawdown_gap_vs_baseline_display']}`",
        f"- best quality overlay: `{summary['best_quality_variant']}`",
        f"- recommended representative candidate: `{summary['recommended_representative_variant']}`",
        f"- representative challenger search closed: `{summary['representative_challenger_search_closed']}`",
        f"- challenger family count: `{summary['challenger_family_count']}`",
        f"- drawdown improver count: `{summary['drawdown_improver_count']}`",
        f"- quality overlay count: `{summary['quality_overlay_count']}`",
        f"- no-op count: `{summary['no_op_count']}`",
        "",
        "Primary entrypoints:",
        f"- primary human command: `{summary['primary_human_command']}`",
        f"- doctor command: `{summary['doctor_command']}`",
        f"- gate probe command: `{summary['gate_probe_command']}`",
        f"- dashboard generate command: `{summary['dashboard_command']}`",
        f"- dashboard open command: `{summary['dashboard_open_command']}`",
        f"- dashboard launch command: `{summary['dashboard_launch_command']}`",
        f"- primary read file: `{summary['primary_read_file']}`",
        f"- dashboard file: `{summary['dashboard_file']}`",
        "",
        "Canonical snapshot sources:",
        f"- verdict: `{summary['verdict_file']}`",
        f"- promotion gate: `{summary['promotion_gate_file']}`",
        f"- guardrail matrix: `{summary['guardrail_matrix_file']}`",
        f"- promotion recommendation: `{summary['promotion_recommendation_file']}`",
        f"- representative challenger closure: `{summary['representative_challenger_closure_file']}`",
        f"- representative decision: `{summary['representative_decision_file']}`",
        f"- probe contract: `{summary['probe_contract_file']}`",
        f"- refresh contract: `{summary['refresh_contract_file']}`",
        f"- entrypoint contract: `{summary['entrypoint_contract_file']}`",
        "",
        "Operational contract verdicts:",
        f"- representative decision verdict: `{summary['representative_decision_verdict']}`",
        f"- probe contract verdict: `{summary['probe_contract_verdict']}`",
        f"- refresh contract verdict: `{summary['refresh_contract_verdict']}`",
        f"- entrypoint contract verdict: `{summary['entrypoint_contract_verdict']}`",
        "",
        "Execution gate:",
        f"- execution gate file: `{summary['execution_gate_file']}`",
        f"- recommended live execution mode: `{summary['recommended_live_execution_mode']}`",
        f"- operational branch ready for live autotrade: `{summary['operational_branch_ready_for_live_autotrade']}`",
        f"- shadow baseline ready for live autotrade: `{summary['shadow_ready_for_live_autotrade']}`",
        f"- execution gate verdict: `{summary['execution_gate_verdict']}`",
        "",
        "Verification summary:",
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
    return "\n".join(lines)


def main() -> None:
    snapshot = _load_json(STATUS_SNAPSHOT_JSON)
    manifest = _load_json(MANIFEST_JSON)
    closure = _load_json(CLOSURE_JSON)
    execution_gate = _load_json(EXECUTION_GATE_JSON)
    current_state = {
        "state_file_version": 1,
        "source": "output/split_models_operational_conversion_status_snapshot/status_snapshot_summary.json",
        **snapshot,
        "primary_human_command": manifest["primary_human_command"],
        "doctor_command": manifest["doctor_command"],
        "sync_command": manifest["sync_command"],
        "refresh_command": manifest["refresh_command"],
        "gate_probe_command": manifest["gate_probe_command"],
        "dashboard_command": manifest["dashboard_command"],
        "dashboard_open_command": manifest["dashboard_open_command"],
        "dashboard_launch_command": manifest["dashboard_launch_command"],
        "primary_read_file": manifest["primary_read_file"],
        "dashboard_file": manifest["dashboard_file"],
        "probe_contract_file": manifest["probe_contract_file"],
        "refresh_contract_file": manifest["refresh_contract_file"],
        "entrypoint_contract_file": manifest["entrypoint_contract_file"],
        "execution_gate_file": "output/split_models_operational_execution_gate/execution_gate_summary.json",
        "recommended_live_execution_mode": execution_gate["recommended_live_execution_mode"],
        "operational_branch_ready_for_live_autotrade": execution_gate["operational_branch_ready_for_live_autotrade"],
        "shadow_ready_for_live_autotrade": execution_gate["shadow_ready_for_live_autotrade"],
        "execution_gate_verdict": execution_gate["execution_gate_verdict"],
        "doctor_smoke_test_status": closure["doctor_smoke_test_status"],
        "doctor_smoke_process_a": closure["doctor_smoke_process_a"],
        "doctor_smoke_process_b": closure["doctor_smoke_process_b"],
        "doctor_lock_event_sequence": closure["doctor_lock_event_sequence"],
        "probe_smoke_test_status": closure["probe_smoke_test_status"],
        "python_probe_exit_code": closure["python_probe_exit_code"],
        "powershell_probe_exit_code": closure["powershell_probe_exit_code"],
        "cmd_probe_exit_code": closure["cmd_probe_exit_code"],
        "stale_lock_smoke_test_status": closure["stale_lock_smoke_test_status"],
        "stale_lock_sync_stdout": closure["stale_lock_sync_stdout"],
        "stale_lock_dir_exists_after_sync": closure["stale_lock_dir_exists_after_sync"],
    }
    OUTPUT_JSON.write_text(json.dumps(current_state, indent=2), encoding="utf-8")
    OUTPUT_MD.write_text(_build_markdown(current_state), encoding="utf-8")
    print(json.dumps(current_state, indent=2))


if __name__ == "__main__":
    main()
