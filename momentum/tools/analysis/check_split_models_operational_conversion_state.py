from __future__ import annotations

import json
from pathlib import Path
import sys
import ast
import py_compile


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
MANIFEST_JSON = ROOT / "output" / "split_models_operational_conversion_manifest.json"
CURRENT_STATE_JSON = ROOT / "output" / "split_models_operational_conversion_current_state.json"
SNAPSHOT_JSON = ROOT / "output" / "split_models_operational_conversion_status_snapshot" / "status_snapshot_summary.json"
GATE_JSON = ROOT / "output" / "split_models_operational_conversion_promotion_gate" / "promotion_gate_summary.json"
VERDICT_JSON = ROOT / "output" / "split_models_operational_conversion_verdict" / "operational_conversion_verdict_summary.json"
MATRIX_JSON = ROOT / "output" / "split_models_operational_conversion_guardrail_matrix" / "guardrail_matrix_summary.json"
HANDOFF_JSON = ROOT / "output" / "split_models_operational_conversion_handoff" / "handoff_summary.json"
CLOSURE_JSON = ROOT / "output" / "split_models_operational_conversion_closure" / "closure_summary.json"
CANDIDATE_LADDER_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_candidate_ladder"
    / "candidate_ladder_summary.json"
)
OOS_REGISTRATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_oos_registration"
    / "oos_registration_summary.json"
)
OOS_ROBUSTNESS_GATE_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_oos_robustness_gate"
    / "oos_robustness_gate_summary.json"
)
PROMOTION_RECOMMENDATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_promotion_recommendation"
    / "promotion_recommendation_summary.json"
)
FOLLOWUP_CONTRACT_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_followup_contract"
    / "followup_contract_summary.json"
)
REPRESENTATIVE_CHALLENGER_CLOSURE_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_representative_challenger_closure"
    / "representative_challenger_closure_summary.json"
)
REPRESENTATIVE_DECISION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_representative_decision"
    / "representative_decision_summary.json"
)
PROBE_CONTRACT_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_probe_contract"
    / "probe_contract_summary.json"
)
REFRESH_CONTRACT_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_refresh_contract"
    / "refresh_contract_summary.json"
)
ENTRYPOINT_CONTRACT_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_entrypoint_contract"
    / "entrypoint_contract_summary.json"
)
EXECUTION_GATE_JSON = (
    ROOT
    / "output"
    / "split_models_operational_execution_gate"
    / "execution_gate_summary.json"
)
DASHBOARD_HTML = ROOT / "output" / "split_models_operational_conversion_dashboard" / "dashboard.html"
CURRENT_STATE_MD = ROOT / "output" / "split_models_operational_conversion_current_state.md"
STATUS_SNAPSHOT_MD = ROOT / "output" / "split_models_operational_conversion_status_snapshot" / "status_snapshot.md"
MANIFEST_MD = ROOT / "output" / "split_models_operational_conversion_manifest.md"
HANDOFF_MD = ROOT / "output" / "split_models_operational_conversion_handoff" / "handoff.md"
CLOSURE_MD = ROOT / "output" / "split_models_operational_conversion_closure" / "closure.md"
CANDIDATE_LADDER_MD = (
    ROOT
    / "output"
    / "split_models_operational_conversion_candidate_ladder"
    / "candidate_ladder.md"
)
OOS_REGISTRATION_MD = (
    ROOT
    / "output"
    / "split_models_operational_conversion_oos_registration"
    / "oos_registration.md"
)
OOS_ROBUSTNESS_GATE_MD = (
    ROOT
    / "output"
    / "split_models_operational_conversion_oos_robustness_gate"
    / "oos_robustness_gate.md"
)
PROMOTION_RECOMMENDATION_MD = (
    ROOT
    / "output"
    / "split_models_operational_conversion_promotion_recommendation"
    / "promotion_recommendation.md"
)
FOLLOWUP_CONTRACT_MD = (
    ROOT
    / "output"
    / "split_models_operational_conversion_followup_contract"
    / "followup_contract.md"
)
REPRESENTATIVE_CHALLENGER_CLOSURE_MD = (
    ROOT
    / "output"
    / "split_models_operational_conversion_representative_challenger_closure"
    / "representative_challenger_closure.md"
)
REPRESENTATIVE_DECISION_MD = (
    ROOT
    / "output"
    / "split_models_operational_conversion_representative_decision"
    / "representative_decision.md"
)
PROBE_CONTRACT_MD = (
    ROOT
    / "output"
    / "split_models_operational_conversion_probe_contract"
    / "probe_contract.md"
)
REFRESH_CONTRACT_MD = (
    ROOT
    / "output"
    / "split_models_operational_conversion_refresh_contract"
    / "refresh_contract.md"
)
ENTRYPOINT_CONTRACT_MD = (
    ROOT
    / "output"
    / "split_models_operational_conversion_entrypoint_contract"
    / "entrypoint_contract.md"
)
EXECUTION_GATE_MD = ROOT / "output" / "split_models_operational_execution_gate" / "execution_gate.md"
README_MD = ROOT / "README.md"
REFRESH_STATE_SCRIPT = ROOT / "tools" / "analysis" / "refresh_split_models_operational_conversion_state.py"
SYNC_STATE_SCRIPT = ROOT / "tools" / "analysis" / "sync_split_models_operational_conversion_state.py"
DOCTOR_STATE_SCRIPT = ROOT / "tools" / "analysis" / "doctor_split_models_operational_conversion_state.py"
SHOW_STATE_SCRIPT = ROOT / "tools" / "analysis" / "show_split_models_operational_conversion_state.py"
PROBE_GATE_PY = ROOT / "tools" / "analysis" / "probe_split_models_operational_conversion_gate.py"
SMOKE_TEST_PROBE_PY = ROOT / "tools" / "analysis" / "smoke_test_split_models_operational_conversion_probe.py"
SMOKE_TEST_LOCK_PY = ROOT / "tools" / "analysis" / "smoke_test_split_models_operational_conversion_lock.py"
SMOKE_TEST_STALE_LOCK_PY = ROOT / "tools" / "analysis" / "smoke_test_split_models_operational_conversion_stale_lock.py"
OPEN_DASHBOARD_PY = ROOT / "tools" / "analysis" / "open_split_models_operational_conversion_dashboard.py"
LAUNCH_DASHBOARD_PY = ROOT / "tools" / "analysis" / "launch_split_models_operational_conversion_dashboard.py"
STREAMLIT_DASHBOARD_ANALYSIS_PY = ROOT / "tools" / "analysis" / "split_models_operational_conversion_dashboard.py"
STREAMLIT_DASHBOARD_REMOTE_PY = ROOT / "tools" / "dashboards" / "operational_conversion_dashboard.py"
GENERATE_DASHBOARD_PY = ROOT / "tools" / "analysis" / "generate_split_models_operational_conversion_dashboard.py"
PROBE_GATE_PS1 = ROOT / "tools" / "analysis" / "probe_split_models_operational_conversion_gate.ps1"
DOCTOR_STATE_PS1 = ROOT / "tools" / "analysis" / "doctor_split_models_operational_conversion_state.ps1"
LAUNCH_DASHBOARD_PS1 = ROOT / "tools" / "analysis" / "launch_split_models_operational_conversion_dashboard.ps1"
OPEN_DASHBOARD_PS1 = ROOT / "tools" / "analysis" / "open_split_models_operational_conversion_dashboard.ps1"
PROBE_GATE_BAT = ROOT / "tools" / "analysis" / "probe_split_models_operational_conversion_gate.bat"
DOCTOR_STATE_BAT = ROOT / "tools" / "analysis" / "doctor_split_models_operational_conversion_state.bat"
LAUNCH_DASHBOARD_BAT = ROOT / "tools" / "analysis" / "launch_split_models_operational_conversion_dashboard.bat"
OPEN_DASHBOARD_BAT = ROOT / "tools" / "analysis" / "open_split_models_operational_conversion_dashboard.bat"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_named_string_list(path: Path, variable_name: str) -> list[str]:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable_name:
                    if not isinstance(node.value, ast.List):
                        raise AssertionError(f"{variable_name} is not a list")
                    values: list[str] = []
                    for elt in node.value.elts:
                        if not isinstance(elt, ast.Constant) or not isinstance(elt.value, str):
                            raise AssertionError(f"{variable_name} contains non-string entry")
                        values.append(elt.value)
                    return values
    raise AssertionError(f"{variable_name} not found")


def _load_refresh_steps(path: Path) -> list[str]:
    return _load_named_string_list(path, "STEPS")


def _assert_python_compiles(label: str, path: Path) -> None:
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        raise AssertionError(f"{label} failed to compile: {exc.msg}") from exc


def _assert_equal(label: str, left, right) -> None:
    if left != right:
        raise AssertionError(f"{label} mismatch: {left!r} != {right!r}")


def _assert_true(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(f"{label} failed")


def main() -> None:
    manifest = _load_json(MANIFEST_JSON)
    current_state = _load_json(CURRENT_STATE_JSON)
    snapshot = _load_json(SNAPSHOT_JSON)
    gate = _load_json(GATE_JSON)
    verdict = _load_json(VERDICT_JSON)
    matrix = _load_json(MATRIX_JSON)
    handoff = _load_json(HANDOFF_JSON)
    closure = _load_json(CLOSURE_JSON)
    candidate_ladder = _load_json(CANDIDATE_LADDER_JSON)
    oos_registration = _load_json(OOS_REGISTRATION_JSON)
    oos_robustness_gate = _load_json(OOS_ROBUSTNESS_GATE_JSON)
    promotion_recommendation = _load_json(PROMOTION_RECOMMENDATION_JSON)
    followup_contract = _load_json(FOLLOWUP_CONTRACT_JSON)
    representative_challenger_closure = _load_json(REPRESENTATIVE_CHALLENGER_CLOSURE_JSON)
    representative_decision = _load_json(REPRESENTATIVE_DECISION_JSON)
    probe_contract = _load_json(PROBE_CONTRACT_JSON)
    refresh_contract = _load_json(REFRESH_CONTRACT_JSON)
    entrypoint_contract = _load_json(ENTRYPOINT_CONTRACT_JSON)
    execution_gate = _load_json(EXECUTION_GATE_JSON)
    refresh_steps = _load_refresh_steps(REFRESH_STATE_SCRIPT)
    sync_steps = _load_named_string_list(SYNC_STATE_SCRIPT, "STEPS")
    doctor_steps = _load_named_string_list(DOCTOR_STATE_SCRIPT, "STEPS")

    _assert_equal("manifest.gate_status", manifest["gate_status"], current_state["gate_status"])
    _assert_equal("manifest.promotion_status", manifest["promotion_status"], current_state["promotion_status"])
    _assert_equal("manifest.anchor_variant", manifest["anchor_variant"], current_state["anchor_variant"])
    _assert_equal(
        "manifest.recommended_representative_variant",
        manifest["recommended_representative_variant"],
        current_state["recommended_representative_variant"],
    )
    _assert_equal(
        "manifest.representative_challenger_search_closed",
        manifest["representative_challenger_search_closed"],
        current_state["representative_challenger_search_closed"],
    )
    _assert_equal("current_state.primary_human_command", current_state["primary_human_command"], manifest["primary_human_command"])
    _assert_equal("current_state.doctor_command", current_state["doctor_command"], manifest["doctor_command"])
    _assert_equal("current_state.sync_command", current_state["sync_command"], manifest["sync_command"])
    _assert_equal("current_state.refresh_command", current_state["refresh_command"], manifest["refresh_command"])
    _assert_equal("current_state.gate_probe_command", current_state["gate_probe_command"], manifest["gate_probe_command"])
    _assert_equal("current_state.dashboard_command", current_state["dashboard_command"], manifest["dashboard_command"])
    _assert_equal("current_state.dashboard_open_command", current_state["dashboard_open_command"], manifest["dashboard_open_command"])
    _assert_equal("current_state.dashboard_launch_command", current_state["dashboard_launch_command"], manifest["dashboard_launch_command"])
    _assert_equal("current_state.primary_read_file", current_state["primary_read_file"], manifest["primary_read_file"])
    _assert_equal("current_state.dashboard_file", current_state["dashboard_file"], manifest["dashboard_file"])
    _assert_equal("current_state.representative_decision_file", current_state["representative_decision_file"], manifest["representative_decision_file"])
    _assert_equal(
        "current_state.representative_decision_verdict",
        current_state["representative_decision_verdict"],
        manifest["representative_decision_verdict"],
    )
    _assert_equal("current_state.probe_contract_file", current_state["probe_contract_file"], manifest["probe_contract_file"])
    _assert_equal("current_state.probe_contract_verdict", current_state["probe_contract_verdict"], manifest["probe_contract_verdict"])
    _assert_equal("current_state.refresh_contract_file", current_state["refresh_contract_file"], manifest["refresh_contract_file"])
    _assert_equal("current_state.refresh_contract_verdict", current_state["refresh_contract_verdict"], manifest["refresh_contract_verdict"])
    _assert_equal("current_state.entrypoint_contract_file", current_state["entrypoint_contract_file"], manifest["entrypoint_contract_file"])
    _assert_equal(
        "current_state.entrypoint_contract_verdict",
        current_state["entrypoint_contract_verdict"],
        manifest["entrypoint_contract_verdict"],
    )
    _assert_equal("current_state.entrypoint_contract_verdict", current_state["entrypoint_contract_verdict"], snapshot["entrypoint_contract_verdict"])
    _assert_equal("manifest.probe_contract_file", manifest["probe_contract_file"], "output/split_models_operational_conversion_probe_contract/probe_contract_summary.json")
    _assert_equal("manifest.refresh_contract_file", manifest["refresh_contract_file"], "output/split_models_operational_conversion_refresh_contract/refresh_contract_summary.json")
    _assert_equal("manifest.entrypoint_contract_file", manifest["entrypoint_contract_file"], "output/split_models_operational_conversion_entrypoint_contract/entrypoint_contract_summary.json")
    _assert_equal("current_state.gate_status", current_state["gate_status"], snapshot["gate_status"])
    _assert_equal("current_state.promotion_status", current_state["promotion_status"], snapshot["promotion_status"])
    _assert_equal("current_state.anchor_variant", current_state["anchor_variant"], snapshot["anchor_variant"])
    _assert_equal("current_state.best_quality_variant", current_state["best_quality_variant"], snapshot["best_quality_variant"])
    _assert_equal(
        "current_state.recommended_representative_variant",
        current_state["recommended_representative_variant"],
        snapshot["recommended_representative_variant"],
    )
    _assert_equal(
        "current_state.representative_challenger_search_closed",
        current_state["representative_challenger_search_closed"],
        snapshot["representative_challenger_search_closed"],
    )
    _assert_equal(
        "current_state.challenger_family_count",
        current_state["challenger_family_count"],
        snapshot["challenger_family_count"],
    )
    _assert_equal("current_state.drawdown_improver_count", current_state["drawdown_improver_count"], matrix["drawdown_improver_count"])
    _assert_equal("current_state.quality_overlay_count", current_state["quality_overlay_count"], matrix["quality_up_same_drawdown_count"])
    _assert_equal("current_state.no_op_count", current_state["no_op_count"], matrix["no_op_count"])
    _assert_equal("gate.gate_status", gate["gate_status"], current_state["gate_status"])
    _assert_equal("gate.anchor_variant", gate["anchor_variant"], current_state["anchor_variant"])
    _assert_equal("verdict.anchor_variant", verdict["anchor_variant"], current_state["anchor_variant"])
    _assert_equal("verdict.best_quality_variant", verdict["best_quality_variant"], current_state["best_quality_variant"])
    _assert_equal(
        "verdict.recommended_representative_variant",
        verdict["recommended_representative_variant"],
        current_state["recommended_representative_variant"],
    )
    _assert_equal("handoff.gate_status", handoff["gate_status"], current_state["gate_status"])
    _assert_equal("handoff.promotion_status", handoff["promotion_status"], current_state["promotion_status"])
    _assert_equal("handoff.anchor_variant", handoff["anchor_variant"], current_state["anchor_variant"])
    _assert_equal("handoff.best_quality_variant", handoff["best_quality_variant"], current_state["best_quality_variant"])
    _assert_equal(
        "handoff.recommended_representative_variant",
        handoff["recommended_representative_variant"],
        current_state["recommended_representative_variant"],
    )
    _assert_equal(
        "handoff.representative_challenger_search_closed",
        handoff["representative_challenger_search_closed"],
        current_state["representative_challenger_search_closed"],
    )
    _assert_equal(
        "handoff.representative_decision_file",
        handoff["representative_decision_file"],
        current_state["representative_decision_file"],
    )
    _assert_equal(
        "handoff.representative_decision_verdict",
        handoff["representative_decision_verdict"],
        current_state["representative_decision_verdict"],
    )
    _assert_equal(
        "handoff.primary_read_file",
        handoff["primary_read_file"],
        manifest["primary_read_file"],
    )
    _assert_equal(
        "handoff.primary_human_command",
        handoff["primary_human_command"],
        "python tools/analysis/launch_split_models_operational_conversion_dashboard.py",
    )
    _assert_equal(
        "handoff.doctor_command",
        handoff["doctor_command"],
        "python tools/analysis/doctor_split_models_operational_conversion_state.py",
    )
    _assert_equal(
        "handoff.sync_command",
        handoff["sync_command"],
        "python tools/analysis/sync_split_models_operational_conversion_state.py",
    )
    _assert_equal(
        "handoff.gate_probe_command",
        handoff["gate_probe_command"],
        "python tools/analysis/probe_split_models_operational_conversion_gate.py",
    )
    _assert_equal(
        "handoff.dashboard_command",
        handoff["dashboard_command"],
        "python tools/analysis/generate_split_models_operational_conversion_dashboard.py",
    )
    _assert_equal(
        "handoff.dashboard_open_command",
        handoff["dashboard_open_command"],
        "python tools/analysis/open_split_models_operational_conversion_dashboard.py",
    )
    _assert_equal(
        "handoff.dashboard_launch_command",
        handoff["dashboard_launch_command"],
        "python tools/analysis/launch_split_models_operational_conversion_dashboard.py",
    )
    _assert_equal(
        "handoff.dashboard_file",
        handoff["dashboard_file"],
        "output/split_models_operational_conversion_dashboard/dashboard.html",
    )
    _assert_equal(
        "handoff.probe_contract_file",
        handoff["probe_contract_file"],
        manifest["probe_contract_file"],
    )
    _assert_equal(
        "handoff.probe_contract_verdict",
        handoff["probe_contract_verdict"],
        current_state["probe_contract_verdict"],
    )
    _assert_equal(
        "handoff.refresh_contract_file",
        handoff["refresh_contract_file"],
        manifest["refresh_contract_file"],
    )
    _assert_equal(
        "handoff.refresh_contract_verdict",
        handoff["refresh_contract_verdict"],
        current_state["refresh_contract_verdict"],
    )
    _assert_equal(
        "handoff.entrypoint_contract_file",
        handoff["entrypoint_contract_file"],
        manifest["entrypoint_contract_file"],
    )
    _assert_equal(
        "handoff.entrypoint_contract_verdict",
        handoff["entrypoint_contract_verdict"],
        current_state["entrypoint_contract_verdict"],
    )
    _assert_equal(
        "manifest.doctor_command",
        manifest["doctor_command"],
        "python tools/analysis/doctor_split_models_operational_conversion_state.py",
    )
    _assert_equal(
        "manifest.primary_human_command",
        manifest["primary_human_command"],
        "python tools/analysis/launch_split_models_operational_conversion_dashboard.py",
    )
    _assert_equal(
        "manifest.sync_command",
        manifest["sync_command"],
        "python tools/analysis/sync_split_models_operational_conversion_state.py",
    )
    _assert_equal(
        "manifest.gate_probe_command",
        manifest["gate_probe_command"],
        "python tools/analysis/probe_split_models_operational_conversion_gate.py",
    )
    _assert_equal(
        "manifest.dashboard_command",
        manifest["dashboard_command"],
        "python tools/analysis/generate_split_models_operational_conversion_dashboard.py",
    )
    _assert_equal(
        "manifest.dashboard_open_command",
        manifest["dashboard_open_command"],
        "python tools/analysis/open_split_models_operational_conversion_dashboard.py",
    )
    _assert_equal(
        "manifest.dashboard_launch_command",
        manifest["dashboard_launch_command"],
        "python tools/analysis/launch_split_models_operational_conversion_dashboard.py",
    )
    _assert_equal(
        "manifest.dashboard_file",
        manifest["dashboard_file"],
        "output/split_models_operational_conversion_dashboard/dashboard.html",
    )
    _assert_equal(
        "manifest.representative_decision_file",
        manifest["representative_decision_file"],
        current_state["representative_decision_file"],
    )
    _assert_equal(
        "candidate_ladder.balance_variant",
        candidate_ladder["balance_variant"],
        current_state["recommended_representative_variant"],
    )
    _assert_equal(
        "candidate_ladder.growth_variant",
        candidate_ladder["growth_variant"],
        representative_decision["growth_boundary_variant"],
    )
    _assert_equal(
        "candidate_ladder.drawdown_variant",
        candidate_ladder["drawdown_variant"],
        representative_decision["drawdown_boundary_variant"],
    )
    _assert_equal(
        "promotion_recommendation.recommended_variant",
        promotion_recommendation["recommended_variant"],
        current_state["recommended_representative_variant"],
    )
    _assert_equal(
        "promotion_recommendation.growth_variant",
        promotion_recommendation["growth_variant"],
        representative_decision["growth_boundary_variant"],
    )
    _assert_equal(
        "promotion_recommendation.drawdown_variant",
        promotion_recommendation["drawdown_variant"],
        representative_decision["drawdown_boundary_variant"],
    )
    _assert_equal(
        "promotion_recommendation.recommendation_reason",
        promotion_recommendation["recommendation_reason"],
        current_state["recommendation_reason"],
    )
    _assert_equal(
        "followup_contract.representative_variant",
        followup_contract["representative_variant"],
        current_state["recommended_representative_variant"],
    )
    _assert_equal(
        "followup_contract.growth_boundary_variant",
        followup_contract["growth_boundary_variant"],
        representative_decision["growth_boundary_variant"],
    )
    _assert_equal(
        "followup_contract.drawdown_boundary_variant",
        followup_contract["drawdown_boundary_variant"],
        representative_decision["drawdown_boundary_variant"],
    )
    _assert_equal(
        "followup_contract.quality_reference_variant",
        followup_contract["quality_reference_variant"],
        current_state["best_quality_variant"],
    )
    _assert_true(
        "followup_contract.followup_rules_nonempty",
        len(followup_contract["followup_rules"]) > 0,
    )
    _assert_equal("closure.gate_status", closure["gate_status"], current_state["gate_status"])
    _assert_equal("closure.promotion_status", closure["promotion_status"], current_state["promotion_status"])
    _assert_equal("closure.anchor_variant", closure["anchor_variant"], current_state["anchor_variant"])
    _assert_equal(
        "closure.primary_human_command",
        closure["primary_human_command"],
        manifest["primary_human_command"],
    )
    _assert_equal(
        "closure.doctor_command",
        closure["doctor_command"],
        manifest["doctor_command"],
    )
    _assert_equal(
        "closure.gate_probe_command",
        closure["gate_probe_command"],
        manifest["gate_probe_command"],
    )
    _assert_equal(
        "closure.dashboard_launch_command",
        closure["dashboard_launch_command"],
        manifest["dashboard_launch_command"],
    )
    _assert_equal(
        "closure.primary_read_file",
        closure["primary_read_file"],
        manifest["primary_read_file"],
    )
    _assert_equal(
        "closure.representative_decision_file",
        closure["representative_decision_file"],
        current_state["representative_decision_file"],
    )
    _assert_equal(
        "closure.recommended_representative_variant",
        closure["recommended_representative_variant"],
        current_state["recommended_representative_variant"],
    )
    _assert_equal(
        "closure.growth_boundary_variant",
        closure["growth_boundary_variant"],
        representative_decision["growth_boundary_variant"],
    )
    _assert_equal(
        "closure.drawdown_boundary_variant",
        closure["drawdown_boundary_variant"],
        representative_decision["drawdown_boundary_variant"],
    )
    _assert_equal(
        "closure.quality_reference_variant",
        closure["quality_reference_variant"],
        current_state["best_quality_variant"],
    )
    _assert_equal(
        "closure.representative_decision_verdict",
        closure["representative_decision_verdict"],
        representative_decision["verdict"],
    )
    _assert_equal(
        "closure.refresh_contract_file",
        closure["refresh_contract_file"],
        current_state["refresh_contract_file"],
    )
    _assert_equal(
        "closure.refresh_contract_verdict",
        closure["refresh_contract_verdict"],
        current_state["refresh_contract_verdict"],
    )
    _assert_equal(
        "closure.entrypoint_contract_file",
        closure["entrypoint_contract_file"],
        current_state["entrypoint_contract_file"],
    )
    _assert_equal(
        "closure.entrypoint_contract_verdict",
        closure["entrypoint_contract_verdict"],
        current_state["entrypoint_contract_verdict"],
    )
    _assert_equal("closure.doctor_smoke_test_status", closure["doctor_smoke_test_status"], "ok")
    _assert_equal("closure.probe_smoke_test_status", closure["probe_smoke_test_status"], "ok")
    _assert_equal("closure.doctor_smoke_process_a", closure["doctor_smoke_process_a"], 0)
    _assert_equal("closure.doctor_smoke_process_b", closure["doctor_smoke_process_b"], 0)
    _assert_equal(
        "closure.doctor_lock_event_sequence",
        closure["doctor_lock_event_sequence"],
        ["first:enter", "first:exit", "second:enter", "second:exit"],
    )
    expected_probe_exit_code = 0 if str(current_state["gate_status"]).upper() == "OPEN" else 2
    _assert_equal("closure.python_probe_exit_code", closure["python_probe_exit_code"], expected_probe_exit_code)
    _assert_equal("closure.powershell_probe_exit_code", closure["powershell_probe_exit_code"], expected_probe_exit_code)
    _assert_equal("closure.cmd_probe_exit_code", closure["cmd_probe_exit_code"], expected_probe_exit_code)
    _assert_equal("closure.stale_lock_smoke_test_status", closure["stale_lock_smoke_test_status"], "ok")
    _assert_equal("closure.stale_lock_sync_stdout", closure["stale_lock_sync_stdout"], "sync_complete")
    _assert_equal("closure.stale_lock_dir_exists_after_sync", closure["stale_lock_dir_exists_after_sync"], False)
    _assert_equal(
        "representative_challenger_closure.representative_variant",
        representative_challenger_closure["representative_variant"],
        current_state["recommended_representative_variant"],
    )
    _assert_equal(
        "representative_challenger_closure.recommended_variant",
        representative_challenger_closure["recommended_variant"],
        current_state["recommended_representative_variant"],
    )
    _assert_equal(
        "representative_challenger_closure.representative_replacements_found",
        representative_challenger_closure["representative_replacements_found"],
        0,
    )
    _assert_equal(
        "representative_challenger_closure.challenger_family_count",
        representative_challenger_closure["challenger_family_count"],
        current_state["challenger_family_count"],
    )
    _assert_equal(
        "representative_challenger_closure.quality_reference_variant",
        representative_challenger_closure["quality_reference_variant"],
        current_state["best_quality_variant"],
    )
    _assert_equal(
        "representative_decision.recommended_variant",
        representative_decision["recommended_variant"],
        current_state["recommended_representative_variant"],
    )
    _assert_equal(
        "representative_decision.challenger_family_count",
        representative_decision["challenger_family_count"],
        current_state["challenger_family_count"],
    )
    _assert_equal(
        "representative_decision.representative_replacements_found",
        representative_decision["representative_replacements_found"],
        current_state["representative_replacements_found"],
    )
    _assert_equal(
        "representative_decision.quality_reference_variant",
        representative_decision["quality_reference_variant"],
        current_state["best_quality_variant"],
    )
    _assert_equal(
        "probe_contract.probe_command",
        probe_contract["probe_command"],
        manifest["gate_probe_command"],
    )
    _assert_equal(
        "probe_contract.gate_status",
        probe_contract["gate_status"],
        current_state["gate_status"],
    )
    _assert_equal(
        "probe_contract.promotion_status",
        probe_contract["promotion_status"],
        current_state["promotion_status"],
    )
    _assert_equal(
        "probe_contract.recommended_representative_variant",
        probe_contract["recommended_representative_variant"],
        current_state["recommended_representative_variant"],
    )
    _assert_equal(
        "probe_contract.best_quality_variant",
        probe_contract["best_quality_variant"],
        current_state["best_quality_variant"],
    )
    _assert_equal(
        "probe_contract.representative_challenger_search_closed",
        probe_contract["representative_challenger_search_closed"],
        current_state["representative_challenger_search_closed"],
    )
    _assert_equal(
        "probe_contract.challenger_family_count",
        probe_contract["challenger_family_count"],
        current_state["challenger_family_count"],
    )
    _assert_equal(
        "probe_contract.representative_replacements_found",
        probe_contract["representative_replacements_found"],
        current_state["representative_replacements_found"],
    )
    _assert_equal(
        "probe_contract.representative_decision_file",
        probe_contract["representative_decision_file"],
        current_state["representative_decision_file"],
    )
    _assert_equal(
        "probe_contract.verdict",
        probe_contract["verdict"],
        current_state["probe_contract_verdict"],
    )
    _assert_equal("probe_contract.exit_code_open", probe_contract["exit_code_open"], 0)
    _assert_equal("probe_contract.exit_code_blocked", probe_contract["exit_code_blocked"], 2)
    _assert_equal("probe_contract.exit_code_unknown", probe_contract["exit_code_unknown"], 3)
    _assert_equal(
        "refresh_contract.refresh_command",
        refresh_contract["refresh_command"],
        manifest["refresh_command"],
    )
    _assert_equal(
        "refresh_contract.sync_command",
        refresh_contract["sync_command"],
        manifest["sync_command"],
    )
    _assert_equal(
        "refresh_contract.doctor_command",
        refresh_contract["doctor_command"],
        manifest["doctor_command"],
    )
    _assert_equal(
        "refresh_contract.verdict",
        refresh_contract["verdict"],
        current_state["refresh_contract_verdict"],
    )
    _assert_true(
        "refresh_contract.refresh_outputs_has_refresh_contract",
        "refresh contract" in refresh_contract["refresh_outputs"],
    )
    _assert_true(
        "refresh_contract.refresh_outputs_has_entrypoint_contract",
        "entrypoint contract" in refresh_contract["refresh_outputs"],
    )
    expected_refresh_steps = [
        "analyze_split_models_operational_conversion_candidate_ladder.py",
        "analyze_split_models_operational_conversion_oos_registration.py",
        "analyze_split_models_operational_conversion_oos_validation.py",
        "analyze_split_models_operational_conversion_no_submit_shadow_dry_run.py",
        "analyze_split_models_operational_conversion_oos_robustness_gate.py",
        "analyze_split_models_operational_conversion_promotion_recommendation.py",
        "analyze_split_models_operational_conversion_followup_contract.py",
        "analyze_split_models_operational_conversion_representative_challenger_closure.py",
        "analyze_split_models_operational_conversion_representative_decision.py",
        "analyze_split_models_operational_conversion_probe_contract.py",
        "analyze_split_models_operational_conversion_refresh_contract.py",
        "analyze_split_models_operational_conversion_entrypoint_contract.py",
        "analyze_split_models_operational_conversion_verdict.py",
        "analyze_split_models_operational_conversion_promotion_gate.py",
        "analyze_split_models_operational_conversion_status_snapshot.py",
        "analyze_split_models_operational_execution_gate.py",
        "analyze_split_models_operational_conversion_current_state.py",
        "analyze_split_models_model_scoreboard.py",
        "analyze_split_models_operational_conversion_manifest.py",
        "analyze_split_models_operational_conversion_handoff.py",
        "analyze_split_models_operational_conversion_closure.py",
        "generate_split_models_operational_conversion_dashboard.py",
    ]
    _assert_equal("refresh_state.steps", refresh_steps, expected_refresh_steps)
    _assert_equal(
        "sync_state.steps",
        sync_steps,
        [
            "refresh_split_models_operational_conversion_state.py",
            "check_split_models_operational_conversion_state.py",
        ],
    )
    _assert_equal(
        "doctor_state.steps",
        doctor_steps,
        [
            "sync_split_models_operational_conversion_state.py",
            "show_split_models_operational_conversion_state.py",
        ],
    )
    expected_refresh_outputs = [
        "candidate ladder",
        "OOS registration",
        "OOS validation",
        "no-submit shadow dry-run",
        "OOS robustness gate",
        "promotion recommendation",
        "follow-up contract",
        "representative challenger closure",
        "representative decision",
        "probe contract",
        "refresh contract",
        "entrypoint contract",
        "verdict",
        "promotion gate",
        "status snapshot",
        "current state",
        "manifest",
        "handoff",
        "closure",
        "dashboard",
    ]
    _assert_equal("refresh_contract.refresh_outputs", refresh_contract["refresh_outputs"], expected_refresh_outputs)
    expected_manifest_secondary_files = [
        "output/split_models_operational_conversion_oos_registration/oos_registration_summary.json",
        "output/split_models_operational_conversion_oos_validation/oos_validation_summary.json",
        "output/split_models_operational_conversion_no_submit_shadow_dry_run/no_submit_shadow_dry_run_summary.json",
        "output/split_models_operational_conversion_oos_robustness_gate/oos_robustness_gate_summary.json",
        "output/split_models_operational_conversion_verdict/operational_conversion_verdict_summary.json",
        "output/split_models_operational_conversion_promotion_gate/promotion_gate_summary.json",
        "output/split_models_operational_conversion_guardrail_matrix/guardrail_matrix_summary.json",
        "output/split_models_operational_conversion_promotion_recommendation/promotion_recommendation_summary.json",
        "output/split_models_operational_conversion_representative_challenger_closure/representative_challenger_closure_summary.json",
        "output/split_models_operational_conversion_representative_decision/representative_decision_summary.json",
        "output/split_models_operational_conversion_probe_contract/probe_contract_summary.json",
        "output/split_models_operational_conversion_refresh_contract/refresh_contract_summary.json",
        "output/split_models_operational_conversion_entrypoint_contract/entrypoint_contract_summary.json",
    ]
    _assert_equal("manifest.secondary_files", manifest["secondary_files"], expected_manifest_secondary_files)
    _assert_equal(
        "oos_registration.status",
        oos_registration["status"],
        "REGISTERED_FOR_OOS_ROBUSTNESS",
    )
    _assert_equal(
        "oos_registration.variant",
        oos_registration["variant"] in {
            candidate_ladder["drawdown_window_defense_variant"],
            "tail_release_top25_mid75_pen35_floor25_trim22_state_extsymbol_sym09_sector28_trim100_max08",
            "targeted_mdd_guard_energy_cooldown_ex088",
        },
        True,
    )
    _assert_equal(
        "oos_registration.promotion_decision",
        oos_registration["promotion_decision"],
        "NOT_OPERATION_READY",
    )
    _assert_equal(
        "oos_robustness_gate.candidate_id",
        oos_robustness_gate["candidate_id"],
        oos_registration["candidate_id"],
    )
    _assert_equal(
        "oos_robustness_gate.gate_decision",
        oos_robustness_gate["gate_decision"] in {
            "BLOCK_OOS_ROBUSTNESS_GATES",
            "PASS_OOS_ROBUSTNESS_GATES",
        },
        True,
    )
    _assert_equal(
        "entrypoint_contract.primary_human_command",
        entrypoint_contract["primary_human_command"],
        manifest["primary_human_command"],
    )
    _assert_equal(
        "entrypoint_contract.gate_probe_command",
        entrypoint_contract["gate_probe_command"],
        manifest["gate_probe_command"],
    )
    _assert_equal(
        "entrypoint_contract.refresh_command",
        entrypoint_contract["refresh_command"],
        manifest["refresh_command"],
    )
    _assert_equal(
        "entrypoint_contract.sync_command",
        entrypoint_contract["sync_command"],
        manifest["sync_command"],
    )
    _assert_equal(
        "entrypoint_contract.doctor_command",
        entrypoint_contract["doctor_command"],
        manifest["doctor_command"],
    )
    _assert_equal(
        "entrypoint_contract.primary_read_file",
        entrypoint_contract["primary_read_file"],
        current_state["primary_read_file"],
    )
    _assert_equal(
        "entrypoint_contract.representative_decision_file",
        entrypoint_contract["representative_decision_file"],
        current_state["representative_decision_file"],
    )
    _assert_equal(
        "entrypoint_contract.probe_contract_file",
        entrypoint_contract["probe_contract_file"],
        current_state["probe_contract_file"],
    )
    _assert_equal(
        "entrypoint_contract.refresh_contract_file",
        entrypoint_contract["refresh_contract_file"],
        current_state["refresh_contract_file"],
    )
    _assert_equal(
        "entrypoint_contract.verdict",
        entrypoint_contract["verdict"],
        current_state["entrypoint_contract_verdict"],
    )
    _assert_equal(
        "current_state.representative_decision_file",
        current_state["representative_decision_file"],
        "output/split_models_operational_conversion_representative_decision/representative_decision_summary.json",
    )
    _assert_equal("current_state.execution_gate_file", current_state["execution_gate_file"], "output/split_models_operational_execution_gate/execution_gate_summary.json")
    _assert_equal(
        "current_state.recommended_live_execution_mode",
        current_state["recommended_live_execution_mode"],
        execution_gate["recommended_live_execution_mode"],
    )
    _assert_equal(
        "current_state.operational_branch_ready_for_live_autotrade",
        current_state["operational_branch_ready_for_live_autotrade"],
        execution_gate["operational_branch_ready_for_live_autotrade"],
    )
    _assert_equal(
        "current_state.shadow_ready_for_live_autotrade",
        current_state["shadow_ready_for_live_autotrade"],
        execution_gate["shadow_ready_for_live_autotrade"],
    )
    _assert_equal(
        "current_state.execution_gate_verdict",
        current_state["execution_gate_verdict"],
        execution_gate["execution_gate_verdict"],
    )
    _assert_equal("current_state.doctor_smoke_test_status", current_state["doctor_smoke_test_status"], closure["doctor_smoke_test_status"])
    _assert_equal("current_state.doctor_smoke_process_a", current_state["doctor_smoke_process_a"], closure["doctor_smoke_process_a"])
    _assert_equal("current_state.doctor_smoke_process_b", current_state["doctor_smoke_process_b"], closure["doctor_smoke_process_b"])
    _assert_equal(
        "current_state.doctor_lock_event_sequence",
        current_state["doctor_lock_event_sequence"],
        closure["doctor_lock_event_sequence"],
    )
    _assert_equal("current_state.probe_smoke_test_status", current_state["probe_smoke_test_status"], closure["probe_smoke_test_status"])
    _assert_equal("current_state.python_probe_exit_code", current_state["python_probe_exit_code"], closure["python_probe_exit_code"])
    _assert_equal("current_state.powershell_probe_exit_code", current_state["powershell_probe_exit_code"], closure["powershell_probe_exit_code"])
    _assert_equal("current_state.cmd_probe_exit_code", current_state["cmd_probe_exit_code"], closure["cmd_probe_exit_code"])
    _assert_equal(
        "current_state.stale_lock_smoke_test_status",
        current_state["stale_lock_smoke_test_status"],
        closure["stale_lock_smoke_test_status"],
    )
    _assert_equal("current_state.stale_lock_sync_stdout", current_state["stale_lock_sync_stdout"], closure["stale_lock_sync_stdout"])
    _assert_equal(
        "current_state.stale_lock_dir_exists_after_sync",
        current_state["stale_lock_dir_exists_after_sync"],
        closure["stale_lock_dir_exists_after_sync"],
    )
    _assert_equal("manifest.primary_read_file", manifest["primary_read_file"], "output/split_models_operational_conversion_current_state.json")
    _assert_equal("manifest.refresh_command", manifest["refresh_command"], "python tools/analysis/refresh_split_models_operational_conversion_state.py")
    _assert_true("dashboard_html.exists", DASHBOARD_HTML.exists())
    dashboard_text = DASHBOARD_HTML.read_text(encoding="utf-8")
    _assert_true("dashboard_html.has_anchor", current_state["anchor_variant"] in dashboard_text)
    _assert_true("dashboard_html.has_gate_status", current_state["gate_status"] in dashboard_text)
    _assert_true(
        "dashboard_html.has_representative_decision_verdict",
        current_state["representative_decision_verdict"] in dashboard_text,
    )
    _assert_true(
        "dashboard_html.has_probe_contract_verdict",
        current_state["probe_contract_verdict"] in dashboard_text,
    )
    _assert_true(
        "dashboard_html.has_representative_decision_file",
        current_state["representative_decision_file"] in dashboard_text,
    )
    _assert_true(
        "dashboard_html.has_probe_contract_file",
        current_state["probe_contract_file"] in dashboard_text,
    )
    _assert_true(
        "dashboard_html.has_refresh_contract_file",
        current_state["refresh_contract_file"] in dashboard_text,
    )
    _assert_true(
        "dashboard_html.has_refresh_contract_verdict",
        current_state["refresh_contract_verdict"] in dashboard_text,
    )
    _assert_true(
        "dashboard_html.has_entrypoint_contract_file",
        current_state["entrypoint_contract_file"] in dashboard_text,
    )
    _assert_true(
        "dashboard_html.has_entrypoint_contract_verdict",
        current_state["entrypoint_contract_verdict"] in dashboard_text,
    )
    _assert_true(
        "dashboard_html.has_recommended_live_execution_mode",
        current_state["recommended_live_execution_mode"] in dashboard_text,
    )
    _assert_true(
        "dashboard_html.has_execution_gate_verdict",
        current_state["execution_gate_verdict"] in dashboard_text,
    )
    _assert_true(
        "dashboard_html.has_doctor_smoke_test_status",
        current_state["doctor_smoke_test_status"] in dashboard_text,
    )
    _assert_true(
        "dashboard_html.has_doctor_lock_event_sequence",
        ", ".join(current_state["doctor_lock_event_sequence"]) in dashboard_text,
    )
    _assert_true(
        "dashboard_html.has_stale_lock_smoke_test_status",
        current_state["stale_lock_smoke_test_status"] in dashboard_text,
    )
    _assert_true("current_state_md.exists", CURRENT_STATE_MD.exists())
    current_state_md_text = CURRENT_STATE_MD.read_text(encoding="utf-8")
    _assert_true(
        "current_state_md.has_entrypoint_contract_verdict",
        current_state["entrypoint_contract_verdict"] in current_state_md_text,
    )
    _assert_true(
        "current_state_md.has_refresh_contract_verdict",
        current_state["refresh_contract_verdict"] in current_state_md_text,
    )
    _assert_true(
        "current_state_md.has_doctor_smoke_test_status",
        f"doctor smoke test status: `{current_state['doctor_smoke_test_status']}`" in current_state_md_text,
    )
    _assert_true(
        "current_state_md.has_doctor_lock_event_sequence",
        f"doctor lock event sequence: `{', '.join(current_state['doctor_lock_event_sequence'])}`" in current_state_md_text,
    )
    _assert_true(
        "current_state_md.has_probe_exit_codes",
        f"probe exit codes: `{current_state['python_probe_exit_code']}`, "
        f"`{current_state['powershell_probe_exit_code']}`, `{current_state['cmd_probe_exit_code']}`"
        in current_state_md_text,
    )
    _assert_true(
        "current_state_md.has_stale_lock_sync_stdout",
        f"stale lock sync stdout: `{current_state['stale_lock_sync_stdout']}`" in current_state_md_text,
    )
    _assert_true(
        "current_state_md.has_execution_gate_verdict",
        f"execution gate verdict: `{current_state['execution_gate_verdict']}`" in current_state_md_text,
    )
    _assert_true("manifest_md.exists", MANIFEST_MD.exists())
    manifest_md_text = MANIFEST_MD.read_text(encoding="utf-8")
    _assert_true(
        "manifest_md.has_entrypoint_contract_verdict",
        current_state["entrypoint_contract_verdict"] in manifest_md_text,
    )
    _assert_true(
        "manifest_md.has_representative_decision_verdict",
        current_state["representative_decision_verdict"] in manifest_md_text,
    )
    _assert_true(
        "manifest_md.has_doctor_smoke_test_status",
        f"doctor smoke test status: `{current_state['doctor_smoke_test_status']}`" in manifest_md_text,
    )
    _assert_true(
        "manifest_md.has_doctor_lock_event_sequence",
        f"doctor lock event sequence: `{', '.join(current_state['doctor_lock_event_sequence'])}`" in manifest_md_text,
    )
    _assert_true(
        "manifest_md.has_stale_lock_sync_stdout",
        f"stale lock sync stdout: `{current_state['stale_lock_sync_stdout']}`" in manifest_md_text,
    )
    _assert_true("handoff_md.exists", HANDOFF_MD.exists())
    handoff_md_text = HANDOFF_MD.read_text(encoding="utf-8")
    _assert_true(
        "handoff_md.has_entrypoint_contract_verdict",
        current_state["entrypoint_contract_verdict"] in handoff_md_text,
    )
    _assert_true(
        "handoff_md.has_probe_contract_verdict",
        current_state["probe_contract_verdict"] in handoff_md_text,
    )
    _assert_true(
        "handoff_md.has_doctor_smoke_test_status",
        f"doctor smoke test status: `{current_state['doctor_smoke_test_status']}`" in handoff_md_text,
    )
    _assert_true(
        "handoff_md.has_doctor_lock_event_sequence",
        f"doctor lock event sequence: `{', '.join(current_state['doctor_lock_event_sequence'])}`" in handoff_md_text,
    )
    _assert_true(
        "handoff_md.has_stale_lock_sync_stdout",
        f"stale lock sync stdout: `{current_state['stale_lock_sync_stdout']}`" in handoff_md_text,
    )
    _assert_true("status_snapshot_md.exists", STATUS_SNAPSHOT_MD.exists())
    status_snapshot_md_text = STATUS_SNAPSHOT_MD.read_text(encoding="utf-8")
    _assert_true(
        "status_snapshot_md.has_gate_status",
        f"gate status: `{snapshot['gate_status']}`" in status_snapshot_md_text,
    )
    _assert_true(
        "status_snapshot_md.has_promotion_status",
        f"promotion status: `{snapshot['promotion_status']}`" in status_snapshot_md_text,
    )
    _assert_true(
        "status_snapshot_md.has_anchor_variant",
        f"current anchor: `{snapshot['anchor_variant']}`" in status_snapshot_md_text,
    )
    _assert_true(
        "status_snapshot_md.has_representative_variant",
        f"recommended representative candidate: `{snapshot['recommended_representative_variant']}`" in status_snapshot_md_text,
    )
    _assert_true(
        "status_snapshot_md.has_entrypoint_contract_file",
        snapshot["entrypoint_contract_file"] in status_snapshot_md_text,
    )
    _assert_true("execution_gate_md.exists", EXECUTION_GATE_MD.exists())
    execution_gate_md_text = EXECUTION_GATE_MD.read_text(encoding="utf-8")
    _assert_true(
        "execution_gate_md.has_recommended_live_execution_mode",
        f"recommended live execution mode: `{execution_gate['recommended_live_execution_mode']}`" in execution_gate_md_text,
    )
    _assert_true(
        "execution_gate_md.has_execution_gate_verdict",
        f"execution gate verdict: `{execution_gate['execution_gate_verdict']}`" in execution_gate_md_text,
    )
    _assert_true("closure_md.exists", CLOSURE_MD.exists())
    closure_md_text = CLOSURE_MD.read_text(encoding="utf-8")
    _assert_true(
        "closure_md.has_gate_status",
        f"gate status: `{closure['gate_status']}`" in closure_md_text,
    )
    _assert_true(
        "closure_md.has_representative_variant",
        f"representative: `{closure['recommended_representative_variant']}`" in closure_md_text,
    )
    _assert_true(
        "closure_md.has_representative_decision_verdict",
        closure["representative_decision_verdict"] in closure_md_text,
    )
    _assert_true(
        "closure_md.has_probe_contract_verdict",
        closure["probe_contract_verdict"] in closure_md_text,
    )
    _assert_true(
        "closure_md.has_refresh_contract_verdict",
        closure["refresh_contract_verdict"] in closure_md_text,
    )
    _assert_true(
        "closure_md.has_entrypoint_contract_verdict",
        closure["entrypoint_contract_verdict"] in closure_md_text,
    )
    _assert_true(
        "closure_md.has_stale_lock_smoke_status",
        f"stale lock smoke test status: `{closure['stale_lock_smoke_test_status']}`" in closure_md_text,
    )
    _assert_true(
        "closure_md.has_doctor_smoke_return_codes",
        f"doctor smoke return codes: `{closure['doctor_smoke_process_a']}`, `{closure['doctor_smoke_process_b']}`"
        in closure_md_text,
    )
    _assert_true(
        "closure_md.has_doctor_lock_event_sequence",
        f"doctor lock event sequence: `{', '.join(closure['doctor_lock_event_sequence'])}`" in closure_md_text,
    )
    _assert_true("candidate_ladder_md.exists", CANDIDATE_LADDER_MD.exists())
    candidate_ladder_md_text = CANDIDATE_LADDER_MD.read_text(encoding="utf-8")
    _assert_true(
        "candidate_ladder_md.has_growth_variant",
        candidate_ladder["growth_variant"] in candidate_ladder_md_text,
    )
    _assert_true(
        "candidate_ladder_md.has_balance_variant",
        candidate_ladder["balance_variant"] in candidate_ladder_md_text,
    )
    _assert_true(
        "candidate_ladder_md.has_drawdown_variant",
        candidate_ladder["drawdown_variant"] in candidate_ladder_md_text,
    )
    _assert_true(
        "candidate_ladder_md.has_verdict",
        candidate_ladder["verdict"] in candidate_ladder_md_text,
    )
    _assert_true("oos_registration_md.exists", OOS_REGISTRATION_MD.exists())
    oos_registration_md_text = OOS_REGISTRATION_MD.read_text(encoding="utf-8")
    _assert_true(
        "oos_registration_md.has_variant",
        oos_registration["variant"] in oos_registration_md_text,
    )
    _assert_true(
        "oos_registration_md.has_status",
        oos_registration["status"] in oos_registration_md_text,
    )
    _assert_true("oos_robustness_gate_md.exists", OOS_ROBUSTNESS_GATE_MD.exists())
    oos_robustness_gate_md_text = OOS_ROBUSTNESS_GATE_MD.read_text(encoding="utf-8")
    _assert_true(
        "oos_robustness_gate_md.has_decision",
        oos_robustness_gate["gate_decision"] in oos_robustness_gate_md_text,
    )
    _assert_true("promotion_recommendation_md.exists", PROMOTION_RECOMMENDATION_MD.exists())
    promotion_recommendation_md_text = PROMOTION_RECOMMENDATION_MD.read_text(encoding="utf-8")
    _assert_true(
        "promotion_recommendation_md.has_recommended_variant",
        promotion_recommendation["recommended_variant"] in promotion_recommendation_md_text,
    )
    _assert_true(
        "promotion_recommendation_md.has_recommendation_reason",
        promotion_recommendation["recommendation_reason"] in promotion_recommendation_md_text,
    )
    _assert_true(
        "promotion_recommendation_md.has_growth_variant",
        promotion_recommendation["growth_variant"] in promotion_recommendation_md_text,
    )
    _assert_true(
        "promotion_recommendation_md.has_drawdown_variant",
        promotion_recommendation["drawdown_variant"] in promotion_recommendation_md_text,
    )
    _assert_true(
        "promotion_recommendation_md.has_verdict",
        promotion_recommendation["verdict"] in promotion_recommendation_md_text,
    )
    _assert_true("followup_contract_md.exists", FOLLOWUP_CONTRACT_MD.exists())
    followup_contract_md_text = FOLLOWUP_CONTRACT_MD.read_text(encoding="utf-8")
    _assert_true(
        "followup_contract_md.has_representative_variant",
        followup_contract["representative_variant"] in followup_contract_md_text,
    )
    _assert_true(
        "followup_contract_md.has_growth_boundary_variant",
        followup_contract["growth_boundary_variant"] in followup_contract_md_text,
    )
    _assert_true(
        "followup_contract_md.has_drawdown_boundary_variant",
        followup_contract["drawdown_boundary_variant"] in followup_contract_md_text,
    )
    _assert_true(
        "followup_contract_md.has_quality_reference_variant",
        followup_contract["quality_reference_variant"] in followup_contract_md_text,
    )
    _assert_true(
        "followup_contract_md.has_verdict",
        followup_contract["verdict"] in followup_contract_md_text,
    )
    _assert_true("representative_challenger_closure_md.exists", REPRESENTATIVE_CHALLENGER_CLOSURE_MD.exists())
    representative_challenger_closure_md_text = REPRESENTATIVE_CHALLENGER_CLOSURE_MD.read_text(encoding="utf-8")
    _assert_true(
        "representative_challenger_closure_md.has_representative_variant",
        representative_challenger_closure["representative_variant"] in representative_challenger_closure_md_text,
    )
    _assert_true(
        "representative_challenger_closure_md.has_quality_reference_variant",
        representative_challenger_closure["quality_reference_variant"] in representative_challenger_closure_md_text,
    )
    _assert_true(
        "representative_challenger_closure_md.has_verdict",
        representative_challenger_closure["verdict"] in representative_challenger_closure_md_text,
    )
    _assert_true("representative_decision_md.exists", REPRESENTATIVE_DECISION_MD.exists())
    representative_decision_md_text = REPRESENTATIVE_DECISION_MD.read_text(encoding="utf-8")
    _assert_true(
        "representative_decision_md.has_recommended_variant",
        representative_decision["recommended_variant"] in representative_decision_md_text,
    )
    _assert_true(
        "representative_decision_md.has_growth_boundary_variant",
        representative_decision["growth_boundary_variant"] in representative_decision_md_text,
    )
    _assert_true(
        "representative_decision_md.has_drawdown_boundary_variant",
        representative_decision["drawdown_boundary_variant"] in representative_decision_md_text,
    )
    _assert_true(
        "representative_decision_md.has_quality_reference_variant",
        representative_decision["quality_reference_variant"] in representative_decision_md_text,
    )
    _assert_true(
        "representative_decision_md.has_verdict",
        representative_decision["verdict"] in representative_decision_md_text,
    )
    _assert_true("probe_contract_md.exists", PROBE_CONTRACT_MD.exists())
    probe_contract_md_text = PROBE_CONTRACT_MD.read_text(encoding="utf-8")
    _assert_true(
        "probe_contract_md.has_probe_command",
        probe_contract["probe_command"] in probe_contract_md_text,
    )
    _assert_true(
        "probe_contract_md.has_recommended_variant",
        probe_contract["recommended_representative_variant"] in probe_contract_md_text,
    )
    _assert_true(
        "probe_contract_md.has_representative_decision_verdict",
        probe_contract["representative_decision_verdict"] in probe_contract_md_text,
    )
    _assert_true(
        "probe_contract_md.has_verdict",
        probe_contract["verdict"] in probe_contract_md_text,
    )
    _assert_true("refresh_contract_md.exists", REFRESH_CONTRACT_MD.exists())
    refresh_contract_md_text = REFRESH_CONTRACT_MD.read_text(encoding="utf-8")
    _assert_true(
        "refresh_contract_md.has_refresh_command",
        refresh_contract["refresh_command"] in refresh_contract_md_text,
    )
    _assert_true(
        "refresh_contract_md.has_sync_command",
        refresh_contract["sync_command"] in refresh_contract_md_text,
    )
    _assert_true(
        "refresh_contract_md.has_doctor_command",
        refresh_contract["doctor_command"] in refresh_contract_md_text,
    )
    _assert_true(
        "refresh_contract_md.has_verdict",
        refresh_contract["verdict"] in refresh_contract_md_text,
    )
    _assert_true("entrypoint_contract_md.exists", ENTRYPOINT_CONTRACT_MD.exists())
    entrypoint_contract_md_text = ENTRYPOINT_CONTRACT_MD.read_text(encoding="utf-8")
    _assert_true(
        "entrypoint_contract_md.has_primary_human_command",
        entrypoint_contract["primary_human_command"] in entrypoint_contract_md_text,
    )
    _assert_true(
        "entrypoint_contract_md.has_gate_probe_command",
        entrypoint_contract["gate_probe_command"] in entrypoint_contract_md_text,
    )
    _assert_true(
        "entrypoint_contract_md.has_refresh_command",
        entrypoint_contract["refresh_command"] in entrypoint_contract_md_text,
    )
    _assert_true(
        "entrypoint_contract_md.has_sync_command",
        entrypoint_contract["sync_command"] in entrypoint_contract_md_text,
    )
    _assert_true(
        "entrypoint_contract_md.has_doctor_command",
        entrypoint_contract["doctor_command"] in entrypoint_contract_md_text,
    )
    _assert_true(
        "entrypoint_contract_md.has_verdict",
        entrypoint_contract["verdict"] in entrypoint_contract_md_text,
    )
    _assert_true("readme_md.exists", README_MD.exists())
    readme_text = README_MD.read_text(encoding="utf-8")
    _assert_true(
        "readme.has_official_representative",
        f"official representative: `{current_state['recommended_representative_variant']}`" in readme_text,
    )
    _assert_true(
        "readme.has_human_dashboard_entrypoint",
        f"human dashboard entrypoint: `{manifest['primary_human_command']}`" in readme_text,
    )
    _assert_true(
        "readme.has_machine_gate_probe",
        f"machine gate probe: `{manifest['gate_probe_command']}`" in readme_text,
    )
    _assert_true(
        "readme.has_refresh_entrypoint",
        f"cheap full refresh: `{manifest['refresh_command']}`" in readme_text,
    )
    _assert_true(
        "readme.has_sync_entrypoint",
        f"refresh plus validation: `{manifest['sync_command']}`" in readme_text,
    )
    _assert_true(
        "readme.has_doctor_entrypoint",
        f"terminal summary after sync: `{manifest['doctor_command']}`" in readme_text,
    )
    _assert_true(
        "readme.has_probe_contract_link",
        "output/split_models_operational_conversion_probe_contract/probe_contract.md" in readme_text,
    )
    _assert_true(
        "readme.has_refresh_contract_link",
        "output/split_models_operational_conversion_refresh_contract/refresh_contract.md" in readme_text,
    )
    _assert_true(
        "readme.has_entrypoint_contract_link",
        "output/split_models_operational_conversion_entrypoint_contract/entrypoint_contract.md" in readme_text,
    )
    _assert_true(
        "readme.has_representative_decision_link",
        "output/split_models_operational_conversion_representative_decision/representative_decision.md" in readme_text,
    )
    _assert_true(
        "readme.has_followup_contract_link",
        "output/split_models_operational_conversion_followup_contract/followup_contract.md" in readme_text,
    )
    _assert_true(
        "readme.has_candidate_ladder_link",
        "output/split_models_operational_conversion_candidate_ladder/candidate_ladder.md" in readme_text,
    )
    _assert_true(
        "readme.has_promotion_recommendation_link",
        "output/split_models_operational_conversion_promotion_recommendation/promotion_recommendation.md" in readme_text,
    )
    open_dashboard_py_text = OPEN_DASHBOARD_PY.read_text(encoding="utf-8")
    _assert_true("open_dashboard_py.exists", OPEN_DASHBOARD_PY.exists())
    _assert_true("open_dashboard_py.has_dashboard_html", "dashboard.html" in open_dashboard_py_text)
    _assert_true("launch_dashboard_py.exists", LAUNCH_DASHBOARD_PY.exists())
    launch_dashboard_py_text = LAUNCH_DASHBOARD_PY.read_text(encoding="utf-8")
    _assert_true(
        "launch_dashboard_py.has_sync_step",
        "sync_split_models_operational_conversion_state.py" in launch_dashboard_py_text,
    )
    _assert_true(
        "launch_dashboard_py.has_show_step",
        "show_split_models_operational_conversion_state.py" in launch_dashboard_py_text,
    )
    _assert_true(
        "launch_dashboard_py.has_open_step",
        "open_split_models_operational_conversion_dashboard.py" in launch_dashboard_py_text,
    )
    _assert_true("show_state_script.exists", SHOW_STATE_SCRIPT.exists())
    show_state_script_text = SHOW_STATE_SCRIPT.read_text(encoding="utf-8")
    _assert_true(
        "show_state_script.has_current_state_json",
        "split_models_operational_conversion_current_state.json" in show_state_script_text,
    )
    _assert_true(
        "show_state_script.has_doctor_lock_event_sequence",
        "doctor_lock_event_sequence" in show_state_script_text,
    )
    _assert_true(
        "show_state_script.has_stale_lock_smoke_test_status",
        "stale_lock_smoke_test_status" in show_state_script_text,
    )
    _assert_true(
        "show_state_script.has_probe_exit_codes",
        "probe_exit_codes" in show_state_script_text,
    )
    _assert_true("streamlit_dashboard_analysis_py.exists", STREAMLIT_DASHBOARD_ANALYSIS_PY.exists())
    streamlit_dashboard_analysis_text = STREAMLIT_DASHBOARD_ANALYSIS_PY.read_text(encoding="utf-8")
    _assert_true(
        "streamlit_dashboard_analysis_py.has_current_state_json",
        "split_models_operational_conversion_current_state.json" in streamlit_dashboard_analysis_text,
    )
    _assert_true(
        "streamlit_dashboard_analysis_py.has_manifest_json",
        "split_models_operational_conversion_manifest.json" in streamlit_dashboard_analysis_text,
    )
    _assert_true(
        "streamlit_dashboard_analysis_py.has_current_state_verification",
        "doctor_smoke_test_status" in streamlit_dashboard_analysis_text,
    )
    _assert_true(
        "streamlit_dashboard_analysis_py.has_check_script",
        "check_split_models_operational_conversion_state.py" in streamlit_dashboard_analysis_text,
    )
    _assert_true(
        "streamlit_dashboard_analysis_py.has_doctor_lock_event_sequence",
        "doctor_lock_event_sequence" in streamlit_dashboard_analysis_text,
    )
    _assert_true(
        "streamlit_dashboard_analysis_py.has_stale_lock_smoke",
        "stale_lock_smoke_test_status" in streamlit_dashboard_analysis_text,
    )
    _assert_true("streamlit_dashboard_remote_py.exists", STREAMLIT_DASHBOARD_REMOTE_PY.exists())
    streamlit_dashboard_remote_text = STREAMLIT_DASHBOARD_REMOTE_PY.read_text(encoding="utf-8")
    _assert_true(
        "streamlit_dashboard_remote_py.has_current_state_json",
        "split_models_operational_conversion_current_state.json" in streamlit_dashboard_remote_text,
    )
    _assert_true(
        "streamlit_dashboard_remote_py.has_manifest_json",
        "split_models_operational_conversion_manifest.json" in streamlit_dashboard_remote_text,
    )
    _assert_true(
        "streamlit_dashboard_remote_py.has_current_state_verification",
        "doctor_smoke_test_status" in streamlit_dashboard_remote_text,
    )
    _assert_true(
        "streamlit_dashboard_remote_py.has_doctor_lock_event_sequence",
        "doctor_lock_event_sequence" in streamlit_dashboard_remote_text,
    )
    _assert_true(
        "streamlit_dashboard_remote_py.has_stale_lock_smoke",
        "stale_lock_smoke_test_status" in streamlit_dashboard_remote_text,
    )
    _assert_true("generate_dashboard_py.exists", GENERATE_DASHBOARD_PY.exists())
    generate_dashboard_py_text = GENERATE_DASHBOARD_PY.read_text(encoding="utf-8")
    _assert_true(
        "generate_dashboard_py.has_current_state_json",
        "split_models_operational_conversion_current_state.json" in generate_dashboard_py_text,
    )
    _assert_true(
        "generate_dashboard_py.has_current_state_verification",
        "doctor_smoke_test_status" in generate_dashboard_py_text,
    )
    _assert_true(
        "generate_dashboard_py.has_dashboard_html",
        "dashboard.html" in generate_dashboard_py_text,
    )
    _assert_true(
        "generate_dashboard_py.has_doctor_lock_event_sequence",
        "doctor_lock_event_sequence" in generate_dashboard_py_text,
    )
    _assert_true(
        "generate_dashboard_py.has_stale_lock_smoke",
        "stale_lock_smoke_test_status" in generate_dashboard_py_text,
    )
    _assert_python_compiles("refresh_state_script.compiles", REFRESH_STATE_SCRIPT)
    _assert_python_compiles("sync_state_script.compiles", SYNC_STATE_SCRIPT)
    _assert_python_compiles("doctor_state_script.compiles", DOCTOR_STATE_SCRIPT)
    _assert_python_compiles("show_state_script.compiles", SHOW_STATE_SCRIPT)
    _assert_python_compiles("execution_gate_script.compiles", ROOT / "tools" / "analysis" / "analyze_split_models_operational_execution_gate.py")
    _assert_python_compiles("probe_gate_py.compiles", PROBE_GATE_PY)
    _assert_python_compiles("smoke_test_probe_py.compiles", SMOKE_TEST_PROBE_PY)
    _assert_python_compiles("smoke_test_lock_py.compiles", SMOKE_TEST_LOCK_PY)
    _assert_python_compiles("smoke_test_stale_lock_py.compiles", SMOKE_TEST_STALE_LOCK_PY)
    _assert_python_compiles("open_dashboard_py.compiles", OPEN_DASHBOARD_PY)
    _assert_python_compiles("launch_dashboard_py.compiles", LAUNCH_DASHBOARD_PY)
    _assert_python_compiles("streamlit_dashboard_analysis_py.compiles", STREAMLIT_DASHBOARD_ANALYSIS_PY)
    _assert_python_compiles("streamlit_dashboard_remote_py.compiles", STREAMLIT_DASHBOARD_REMOTE_PY)
    _assert_python_compiles("generate_dashboard_py.compiles", GENERATE_DASHBOARD_PY)
    probe_gate_ps1_text = PROBE_GATE_PS1.read_text(encoding="utf-8")
    _assert_true("probe_gate_ps1.exists", PROBE_GATE_PS1.exists())
    _assert_true("probe_gate_ps1.has_repo_root", "Join-Path $PSScriptRoot \"..\\..\"" in probe_gate_ps1_text)
    _assert_true(
        "probe_gate_ps1.has_python_target",
        "probe_split_models_operational_conversion_gate.py" in probe_gate_ps1_text,
    )
    doctor_state_ps1_text = DOCTOR_STATE_PS1.read_text(encoding="utf-8")
    _assert_true("doctor_state_ps1.exists", DOCTOR_STATE_PS1.exists())
    _assert_true("doctor_state_ps1.has_repo_root", "Join-Path $PSScriptRoot \"..\\..\"" in doctor_state_ps1_text)
    _assert_true(
        "doctor_state_ps1.has_python_target",
        "doctor_split_models_operational_conversion_state.py" in doctor_state_ps1_text,
    )
    launch_dashboard_ps1_text = LAUNCH_DASHBOARD_PS1.read_text(encoding="utf-8")
    _assert_true("launch_dashboard_ps1.exists", LAUNCH_DASHBOARD_PS1.exists())
    _assert_true("launch_dashboard_ps1.has_repo_root", "Join-Path $PSScriptRoot \"..\\..\"" in launch_dashboard_ps1_text)
    _assert_true(
        "launch_dashboard_ps1.has_python_target",
        "launch_split_models_operational_conversion_dashboard.py" in launch_dashboard_ps1_text,
    )
    open_dashboard_ps1_text = OPEN_DASHBOARD_PS1.read_text(encoding="utf-8")
    _assert_true("open_dashboard_ps1.exists", OPEN_DASHBOARD_PS1.exists())
    _assert_true("open_dashboard_ps1.has_repo_root", "Join-Path $PSScriptRoot \"..\\..\"" in open_dashboard_ps1_text)
    _assert_true(
        "open_dashboard_ps1.has_python_target",
        "open_split_models_operational_conversion_dashboard.py" in open_dashboard_ps1_text,
    )
    probe_gate_bat_text = PROBE_GATE_BAT.read_text(encoding="utf-8")
    _assert_true("probe_gate_bat.exists", PROBE_GATE_BAT.exists())
    _assert_true("probe_gate_bat.has_pushd", "pushd \"%SCRIPT_DIR%\\..\\..\"" in probe_gate_bat_text)
    _assert_true(
        "probe_gate_bat.has_python_target",
        "probe_split_models_operational_conversion_gate.py" in probe_gate_bat_text,
    )
    doctor_state_bat_text = DOCTOR_STATE_BAT.read_text(encoding="utf-8")
    _assert_true("doctor_state_bat.exists", DOCTOR_STATE_BAT.exists())
    _assert_true("doctor_state_bat.has_pushd", "pushd \"%SCRIPT_DIR%\\..\\..\"" in doctor_state_bat_text)
    _assert_true(
        "doctor_state_bat.has_python_target",
        "doctor_split_models_operational_conversion_state.py" in doctor_state_bat_text,
    )
    launch_dashboard_bat_text = LAUNCH_DASHBOARD_BAT.read_text(encoding="utf-8")
    _assert_true("launch_dashboard_bat.exists", LAUNCH_DASHBOARD_BAT.exists())
    _assert_true("launch_dashboard_bat.has_pushd", "pushd \"%SCRIPT_DIR%\\..\\..\"" in launch_dashboard_bat_text)
    _assert_true(
        "launch_dashboard_bat.has_python_target",
        "launch_split_models_operational_conversion_dashboard.py" in launch_dashboard_bat_text,
    )
    open_dashboard_bat_text = OPEN_DASHBOARD_BAT.read_text(encoding="utf-8")
    _assert_true("open_dashboard_bat.exists", OPEN_DASHBOARD_BAT.exists())
    _assert_true("open_dashboard_bat.has_pushd", "pushd \"%SCRIPT_DIR%\\..\\..\"" in open_dashboard_bat_text)
    _assert_true(
        "open_dashboard_bat.has_python_target",
        "open_split_models_operational_conversion_dashboard.py" in open_dashboard_bat_text,
    )

    report = {
        "check_status": "ok",
        "gate_status": current_state["gate_status"],
        "promotion_status": current_state["promotion_status"],
        "anchor_variant": current_state["anchor_variant"],
        "checked_files": [
            str(MANIFEST_JSON.relative_to(ROOT)),
            str(CURRENT_STATE_JSON.relative_to(ROOT)),
            str(CURRENT_STATE_MD.relative_to(ROOT)),
            str(STATUS_SNAPSHOT_MD.relative_to(ROOT)),
            str(SNAPSHOT_JSON.relative_to(ROOT)),
            str(GATE_JSON.relative_to(ROOT)),
            str(VERDICT_JSON.relative_to(ROOT)),
            str(MATRIX_JSON.relative_to(ROOT)),
            str(HANDOFF_JSON.relative_to(ROOT)),
            str(HANDOFF_MD.relative_to(ROOT)),
            str(CLOSURE_MD.relative_to(ROOT)),
            str(CANDIDATE_LADDER_MD.relative_to(ROOT)),
            str(PROMOTION_RECOMMENDATION_MD.relative_to(ROOT)),
            str(FOLLOWUP_CONTRACT_MD.relative_to(ROOT)),
            str(REPRESENTATIVE_CHALLENGER_CLOSURE_MD.relative_to(ROOT)),
            str(REPRESENTATIVE_DECISION_MD.relative_to(ROOT)),
            str(PROBE_CONTRACT_MD.relative_to(ROOT)),
            str(REFRESH_CONTRACT_MD.relative_to(ROOT)),
            str(ENTRYPOINT_CONTRACT_MD.relative_to(ROOT)),
            str(REFRESH_STATE_SCRIPT.relative_to(ROOT)),
            str(SYNC_STATE_SCRIPT.relative_to(ROOT)),
            str(DOCTOR_STATE_SCRIPT.relative_to(ROOT)),
            str(PROBE_GATE_PY.relative_to(ROOT)),
            str(SMOKE_TEST_PROBE_PY.relative_to(ROOT)),
            str(SMOKE_TEST_LOCK_PY.relative_to(ROOT)),
            str(SMOKE_TEST_STALE_LOCK_PY.relative_to(ROOT)),
            str(OPEN_DASHBOARD_PY.relative_to(ROOT)),
            str(LAUNCH_DASHBOARD_PY.relative_to(ROOT)),
            str(STREAMLIT_DASHBOARD_ANALYSIS_PY.relative_to(ROOT)),
            str(STREAMLIT_DASHBOARD_REMOTE_PY.relative_to(ROOT)),
            str(GENERATE_DASHBOARD_PY.relative_to(ROOT)),
            str(PROBE_GATE_PS1.relative_to(ROOT)),
            str(DOCTOR_STATE_PS1.relative_to(ROOT)),
            str(LAUNCH_DASHBOARD_PS1.relative_to(ROOT)),
            str(OPEN_DASHBOARD_PS1.relative_to(ROOT)),
            str(PROBE_GATE_BAT.relative_to(ROOT)),
            str(DOCTOR_STATE_BAT.relative_to(ROOT)),
            str(LAUNCH_DASHBOARD_BAT.relative_to(ROOT)),
            str(OPEN_DASHBOARD_BAT.relative_to(ROOT)),
            str(README_MD.relative_to(ROOT)),
            str(CLOSURE_JSON.relative_to(ROOT)),
            str(CANDIDATE_LADDER_JSON.relative_to(ROOT)),
            str(PROMOTION_RECOMMENDATION_JSON.relative_to(ROOT)),
            str(FOLLOWUP_CONTRACT_JSON.relative_to(ROOT)),
            str(MANIFEST_MD.relative_to(ROOT)),
            str(REPRESENTATIVE_CHALLENGER_CLOSURE_JSON.relative_to(ROOT)),
            str(REPRESENTATIVE_DECISION_JSON.relative_to(ROOT)),
            str(PROBE_CONTRACT_JSON.relative_to(ROOT)),
            str(REFRESH_CONTRACT_JSON.relative_to(ROOT)),
            str(ENTRYPOINT_CONTRACT_JSON.relative_to(ROOT)),
            str(DASHBOARD_HTML.relative_to(ROOT)),
        ],
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
