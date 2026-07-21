from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
CURRENT_STATE_JSON = ROOT / "output" / "split_models_operational_conversion_current_state.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    current_state = _load_json(CURRENT_STATE_JSON)

    lines = [
        f"gate_status={current_state['gate_status']}",
        f"promotion_status={current_state['promotion_status']}",
        f"anchor_variant={current_state['anchor_variant']}",
        f"anchor_mdd={current_state['anchor_mdd_display']}",
        f"baseline_mdd={current_state['baseline_mdd_display']}",
        f"drawdown_gap={current_state['drawdown_gap_vs_baseline_display']}",
        f"best_quality_overlay={current_state['best_quality_variant']}",
        f"recommended_representative={current_state['recommended_representative_variant']}",
        f"representative_challenger_search_closed={current_state['representative_challenger_search_closed']}",
        f"challenger_family_count={current_state['challenger_family_count']}",
        f"representative_replacements_found={current_state['representative_replacements_found']}",
        f"representative_challenger_closure_file={current_state['representative_challenger_closure_file']}",
        f"representative_challenger_closure_verdict={current_state['representative_challenger_closure_verdict']}",
        f"representative_decision_file={current_state['representative_decision_file']}",
        f"representative_decision_verdict={current_state['representative_decision_verdict']}",
        f"primary_human_command={current_state['primary_human_command']}",
        f"doctor_command={current_state['doctor_command']}",
        f"sync_command={current_state['sync_command']}",
        f"refresh_command={current_state['refresh_command']}",
        f"gate_probe_command={current_state['gate_probe_command']}",
        f"primary_read_file={current_state['primary_read_file']}",
        f"dashboard_command={current_state['dashboard_command']}",
        f"dashboard_open_command={current_state['dashboard_open_command']}",
        f"dashboard_launch_command={current_state['dashboard_launch_command']}",
        f"dashboard_file={current_state['dashboard_file']}",
        f"probe_contract_file={current_state['probe_contract_file']}",
        f"probe_contract_verdict={current_state['probe_contract_verdict']}",
        f"refresh_contract_file={current_state['refresh_contract_file']}",
        f"refresh_contract_verdict={current_state['refresh_contract_verdict']}",
        f"entrypoint_contract_file={current_state['entrypoint_contract_file']}",
        f"entrypoint_contract_verdict={current_state['entrypoint_contract_verdict']}",
        f"execution_gate_file={current_state['execution_gate_file']}",
        f"recommended_live_execution_mode={current_state['recommended_live_execution_mode']}",
        f"operational_branch_ready_for_live_autotrade={current_state['operational_branch_ready_for_live_autotrade']}",
        f"shadow_ready_for_live_autotrade={current_state['shadow_ready_for_live_autotrade']}",
        f"execution_gate_verdict={current_state['execution_gate_verdict']}",
        f"doctor_smoke_test_status={current_state['doctor_smoke_test_status']}",
        f"doctor_smoke_return_codes={current_state['doctor_smoke_process_a']},{current_state['doctor_smoke_process_b']}",
        f"doctor_lock_event_sequence={','.join(current_state['doctor_lock_event_sequence'])}",
        f"probe_smoke_test_status={current_state['probe_smoke_test_status']}",
        f"probe_exit_codes={current_state['python_probe_exit_code']},{current_state['powershell_probe_exit_code']},{current_state['cmd_probe_exit_code']}",
        f"stale_lock_smoke_test_status={current_state['stale_lock_smoke_test_status']}",
        f"stale_lock_sync_stdout={current_state['stale_lock_sync_stdout']}",
        f"stale_lock_dir_exists_after_sync={current_state['stale_lock_dir_exists_after_sync']}",
    ]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
