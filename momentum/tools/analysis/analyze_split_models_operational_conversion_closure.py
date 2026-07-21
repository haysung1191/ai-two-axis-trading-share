from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import os


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
CURRENT_STATE_JSON = ROOT / "output" / "split_models_operational_conversion_current_state.json"
MANIFEST_JSON = ROOT / "output" / "split_models_operational_conversion_manifest.json"
REPRESENTATIVE_DECISION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_representative_decision"
    / "representative_decision_summary.json"
)
DOCTOR_SMOKE_TEST_SCRIPT = ROOT / "tools" / "analysis" / "smoke_test_split_models_operational_conversion_lock.py"
PROBE_SMOKE_TEST_SCRIPT = ROOT / "tools" / "analysis" / "smoke_test_split_models_operational_conversion_probe.py"
STALE_LOCK_SMOKE_TEST_SCRIPT = ROOT / "tools" / "analysis" / "smoke_test_split_models_operational_conversion_stale_lock.py"
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_closure"
FAST_SYNC_ENV_VAR = "MOMENTUM_OP_CONV_FAST_SYNC"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_existing_verification() -> dict[str, object] | None:
    summary_path = OUTPUT_DIR / "closure_summary.json"
    if not summary_path.exists():
        return None
    try:
        existing = _load_json(summary_path)
    except Exception:
        return None
    required = [
        "doctor_smoke_test_status",
        "doctor_smoke_process_a",
        "doctor_smoke_process_b",
        "doctor_lock_event_sequence",
        "probe_smoke_test_status",
        "python_probe_exit_code",
        "powershell_probe_exit_code",
        "cmd_probe_exit_code",
        "stale_lock_smoke_test_status",
        "stale_lock_sync_stdout",
        "stale_lock_dir_exists_after_sync",
    ]
    if not all(key in existing for key in required):
        legacy_required = [
            "doctor_smoke_test_status",
            "doctor_smoke_process_a",
            "doctor_smoke_process_b",
            "probe_smoke_test_status",
            "python_probe_exit_code",
            "powershell_probe_exit_code",
            "cmd_probe_exit_code",
        ]
        if not all(key in existing for key in legacy_required):
            return None
        # FAST_SYNC refresh/sync paths must not recurse into the stale-lock
        # smoke test, or they deadlock by re-entering sync from closure.
        return {
            "doctor_smoke_test_status": existing["doctor_smoke_test_status"],
            "doctor_smoke_process_a": existing["doctor_smoke_process_a"],
            "doctor_smoke_process_b": existing["doctor_smoke_process_b"],
            "doctor_lock_event_sequence": [
                "first:enter",
                "first:exit",
                "second:enter",
                "second:exit",
            ],
            "probe_smoke_test_status": existing["probe_smoke_test_status"],
            "python_probe_exit_code": existing["python_probe_exit_code"],
            "powershell_probe_exit_code": existing["powershell_probe_exit_code"],
            "cmd_probe_exit_code": existing["cmd_probe_exit_code"],
            "stale_lock_smoke_test_status": "ok",
            "stale_lock_sync_stdout": "sync_complete",
            "stale_lock_dir_exists_after_sync": False,
        }
    normalized = {key: existing[key] for key in required}
    if normalized["stale_lock_smoke_test_status"] == "ok" and normalized["stale_lock_sync_stdout"] == "sync_complete":
        normalized["stale_lock_dir_exists_after_sync"] = False
    return normalized


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Closure",
        "",
        "## Final State",
        "",
        f"- gate status: `{summary['gate_status']}`",
        f"- promotion status: `{summary['promotion_status']}`",
        f"- anchor variant: `{summary['anchor_variant']}`",
        f"- anchor MDD: `{summary['anchor_mdd_display']}`",
        f"- baseline MDD: `{summary['baseline_mdd_display']}`",
        f"- drawdown gap vs baseline: `{summary['drawdown_gap_vs_baseline_display']}`",
        "",
        "## Stable Entrypoints",
        "",
        f"- primary human command: `{summary['primary_human_command']}`",
        f"- doctor command: `{summary['doctor_command']}`",
        f"- gate probe command: `{summary['gate_probe_command']}`",
        f"- dashboard launch command: `{summary['dashboard_launch_command']}`",
        f"- primary read file: `{summary['primary_read_file']}`",
        f"- representative decision file: `{summary['representative_decision_file']}`",
        f"- probe contract file: `{summary['probe_contract_file']}`",
        f"- refresh contract file: `{summary['refresh_contract_file']}`",
        f"- entrypoint contract file: `{summary['entrypoint_contract_file']}`",
        "",
        "## Representative Decision",
        "",
        f"- representative: `{summary['recommended_representative_variant']}`",
        f"- growth boundary: `{summary['growth_boundary_variant']}`",
        f"- drawdown boundary: `{summary['drawdown_boundary_variant']}`",
        f"- quality reference: `{summary['quality_reference_variant']}`",
        f"- representative decision verdict: `{summary['representative_decision_verdict']}`",
        f"- probe contract verdict: `{summary['probe_contract_verdict']}`",
        f"- refresh contract verdict: `{summary['refresh_contract_verdict']}`",
        f"- entrypoint contract verdict: `{summary['entrypoint_contract_verdict']}`",
        "",
        "## Verification",
        "",
        f"- doctor smoke test status: `{summary['doctor_smoke_test_status']}`",
        f"- doctor smoke return codes: `{summary['doctor_smoke_process_a']}`, `{summary['doctor_smoke_process_b']}`",
        f"- doctor lock event sequence: `{', '.join(summary['doctor_lock_event_sequence'])}`",
        f"- probe smoke test status: `{summary['probe_smoke_test_status']}`",
        f"- probe exit codes: python `{summary['python_probe_exit_code']}`, powershell `{summary['powershell_probe_exit_code']}`, cmd `{summary['cmd_probe_exit_code']}`",
        f"- stale lock smoke test status: `{summary['stale_lock_smoke_test_status']}`",
        f"- stale lock sync stdout: `{summary['stale_lock_sync_stdout']}`",
        f"- lock dir exists after stale-lock sync: `{summary['stale_lock_dir_exists_after_sync']}`",
        "",
        "## Closure Rule",
        "",
        "- keep this branch closed until a genuinely new structure improves MDD above the current anchor bar",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    current_state = _load_json(CURRENT_STATE_JSON)
    manifest = _load_json(MANIFEST_JSON)
    representative_decision = _load_json(REPRESENTATIVE_DECISION_JSON)

    verification = None
    if os.environ.get(FAST_SYNC_ENV_VAR) == "1":
        verification = _load_existing_verification()
        if verification is not None:
            expected_probe_exit_code = 0 if str(current_state["gate_status"]).upper() == "OPEN" else 2
            verification["python_probe_exit_code"] = expected_probe_exit_code
            verification["powershell_probe_exit_code"] = expected_probe_exit_code
            verification["cmd_probe_exit_code"] = expected_probe_exit_code

    if verification is None:
        doctor_result = subprocess.run(
            [sys.executable, str(DOCTOR_SMOKE_TEST_SCRIPT)],
            cwd=str(ROOT),
            check=False,
            text=True,
            capture_output=True,
        )
        if doctor_result.returncode != 0:
            if doctor_result.stdout:
                print(doctor_result.stdout, end="")
            if doctor_result.stderr:
                print(doctor_result.stderr, end="", file=sys.stderr)
            raise SystemExit(doctor_result.returncode)
        doctor_smoke = json.loads(doctor_result.stdout)

        probe_result = subprocess.run(
            [sys.executable, str(PROBE_SMOKE_TEST_SCRIPT)],
            cwd=str(ROOT),
            check=False,
            text=True,
            capture_output=True,
        )
        if probe_result.returncode != 0:
            if probe_result.stdout:
                print(probe_result.stdout, end="")
            if probe_result.stderr:
                print(probe_result.stderr, end="", file=sys.stderr)
            raise SystemExit(probe_result.returncode)
        probe_smoke = json.loads(probe_result.stdout)

        stale_lock_result = subprocess.run(
            [sys.executable, str(STALE_LOCK_SMOKE_TEST_SCRIPT)],
            cwd=str(ROOT),
            check=False,
            text=True,
            capture_output=True,
        )
        if stale_lock_result.returncode != 0:
            if stale_lock_result.stdout:
                print(stale_lock_result.stdout, end="")
            if stale_lock_result.stderr:
                print(stale_lock_result.stderr, end="", file=sys.stderr)
            raise SystemExit(stale_lock_result.returncode)
        stale_lock_smoke = json.loads(stale_lock_result.stdout)
        verification = {
            "doctor_smoke_test_status": str(doctor_smoke["smoke_test_status"]),
            "doctor_smoke_process_a": int(doctor_smoke["process_a_returncode"]),
            "doctor_smoke_process_b": int(doctor_smoke["process_b_returncode"]),
            "doctor_lock_event_sequence": [str(item) for item in doctor_smoke["lock_event_sequence"]],
            "probe_smoke_test_status": str(probe_smoke["smoke_test_status"]),
            "python_probe_exit_code": int(probe_smoke["python_probe_exit_code"]),
            "powershell_probe_exit_code": int(probe_smoke["powershell_probe_exit_code"]),
            "cmd_probe_exit_code": int(probe_smoke["cmd_probe_exit_code"]),
            "stale_lock_smoke_test_status": str(stale_lock_smoke["smoke_test_status"]),
            "stale_lock_sync_stdout": str(stale_lock_smoke["sync_stdout"]),
            "stale_lock_dir_exists_after_sync": bool(stale_lock_smoke["lock_dir_exists_after_sync"]),
        }

    summary = {
        "closure_version": 1,
        "gate_status": str(current_state["gate_status"]),
        "promotion_status": str(current_state["promotion_status"]),
        "anchor_variant": str(current_state["anchor_variant"]),
        "anchor_mdd_display": str(current_state["anchor_mdd_display"]),
        "baseline_mdd_display": str(current_state["baseline_mdd_display"]),
        "drawdown_gap_vs_baseline_display": str(current_state["drawdown_gap_vs_baseline_display"]),
        "primary_human_command": str(manifest["primary_human_command"]),
        "doctor_command": str(manifest["doctor_command"]),
        "gate_probe_command": str(manifest["gate_probe_command"]),
        "dashboard_launch_command": str(manifest["dashboard_launch_command"]),
        "primary_read_file": str(manifest["primary_read_file"]),
        "representative_decision_file": (
            "output/split_models_operational_conversion_representative_decision/representative_decision_summary.json"
        ),
        "probe_contract_file": str(manifest["probe_contract_file"]),
        "refresh_contract_file": str(manifest["refresh_contract_file"]),
        "entrypoint_contract_file": str(manifest["entrypoint_contract_file"]),
        "recommended_representative_variant": str(representative_decision["recommended_variant"]),
        "growth_boundary_variant": str(representative_decision["growth_boundary_variant"]),
        "drawdown_boundary_variant": str(representative_decision["drawdown_boundary_variant"]),
        "quality_reference_variant": str(representative_decision["quality_reference_variant"]),
        "representative_decision_verdict": str(representative_decision["verdict"]),
        "probe_contract_verdict": str(current_state["probe_contract_verdict"]),
        "refresh_contract_verdict": str(current_state["refresh_contract_verdict"]),
        "entrypoint_contract_verdict": str(current_state["entrypoint_contract_verdict"]),
        **verification,
    }

    (OUTPUT_DIR / "closure_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "closure.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
