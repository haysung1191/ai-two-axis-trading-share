from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.analysis._operational_conversion_lock import LOCK_ENV_VAR, operational_conversion_lock


STEPS = [
    "sync_split_models_operational_conversion_state.py",
    "show_split_models_operational_conversion_state.py",
    "open_split_models_operational_conversion_dashboard.py",
]


def _render_stdout(script_name: str, stdout: str) -> None:
    if not stdout:
        return
    if script_name != "open_split_models_operational_conversion_dashboard.py":
        print(stdout, end="")
        return

    filtered_lines = [
        line
        for line in stdout.splitlines()
        if not line.startswith("dashboard_file=")
    ]
    if filtered_lines:
        print("\n".join(filtered_lines))


def main() -> None:
    analysis_dir = REPO_ROOT / "tools" / "analysis"
    python_exe = sys.executable
    child_env = os.environ.copy()

    with operational_conversion_lock(REPO_ROOT):
        child_env[LOCK_ENV_VAR] = "1"
        for idx, script_name in enumerate(STEPS):
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
            if idx > 0 and result.stdout:
                _render_stdout(script_name, result.stdout)

    print("launch_complete")


if __name__ == "__main__":
    main()
