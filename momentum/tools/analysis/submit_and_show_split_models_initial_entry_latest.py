from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _run(args: list[str]) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--latest-index-path",
        default=str(SHADOW_DIR / "shadow_live_initial_adaptive_latest.json"),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    python = sys.executable
    submit_args = [
        python,
        "tools/pipelines/submit_split_models_initial_entry_from_latest.py",
        "--latest-index-path",
        args.latest_index_path,
        "--submit-live",
    ]
    show_args = [
        python,
        "tools/analysis/show_split_models_initial_entry_latest.py",
        "--latest-index-path",
        args.latest_index_path,
    ]
    if args.json:
        show_args.append("--json")

    _run(submit_args)
    _run(show_args)


if __name__ == "__main__":
    main()
