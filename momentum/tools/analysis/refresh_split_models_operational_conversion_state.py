from __future__ import annotations

import subprocess
from pathlib import Path
import sys
import os

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.analysis._operational_conversion_lock import LOCK_ENV_VAR, operational_conversion_lock
from tools.analysis.analyze_split_models_operational_conversion_closure import FAST_SYNC_ENV_VAR

STEPS = [
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


def main() -> None:
    analysis_dir = REPO_ROOT / "tools" / "analysis"
    python_exe = sys.executable
    child_env = os.environ.copy()

    with operational_conversion_lock(REPO_ROOT):
        child_env[LOCK_ENV_VAR] = "1"
        child_env[FAST_SYNC_ENV_VAR] = "1"
        for script_name in STEPS:
            script_path = analysis_dir / script_name
            result = subprocess.run(
                [python_exe, str(script_path)],
                cwd=str(REPO_ROOT),
                check=False,
                text=True,
                capture_output=True,
                env=child_env,
            )
            if result.returncode != 0:
                if result.stdout:
                    print(result.stdout, end="")
                if result.stderr:
                    print(result.stderr, end="", file=sys.stderr)
                raise SystemExit(result.returncode)

    print("refresh_complete")


if __name__ == "__main__":
    main()
