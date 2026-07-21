from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_step(args: list[str]) -> None:
    completed = subprocess.run(args, cwd=ROOT, check=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(args)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate the full paper package: results, figures, and compiled manuscript."
    )
    parser.add_argument("--artifacts-root", default="artifacts")
    parser.add_argument("--paper-results-dir", default="paper_results")
    parser.add_argument("--paper-figures-dir", default="paper_figures")
    parser.add_argument("--registry-path", default="strategy_registry.json")
    parser.add_argument("--paper-dir", default="docs/paper")
    parser.add_argument(
        "--compiled-manuscript",
        default="docs/paper/final_manuscript_compiled.md",
    )
    args = parser.parse_args()

    python = sys.executable
    _run_step(
        [
            python,
            "scripts/export_paper_results.py",
            "--artifacts-root",
            args.artifacts_root,
            "--output-dir",
            args.paper_results_dir,
            "--registry-path",
            args.registry_path,
        ]
    )
    _run_step(
        [
            python,
            "scripts/build_paper_figures.py",
            "--paper-results-dir",
            args.paper_results_dir,
            "--output-dir",
            args.paper_figures_dir,
        ]
    )
    _run_step(
        [
            python,
            "scripts/assemble_paper_manuscript.py",
            "--paper-dir",
            args.paper_dir,
            "--output",
            args.compiled_manuscript,
        ]
    )
    print("Paper package regenerated successfully.")


if __name__ == "__main__":
    main()
