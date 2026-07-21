from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "docs" / "paper"
DEFAULT_OUTPUT = PAPER_DIR / "final_manuscript_compiled.md"


SECTION_FILES: list[tuple[str, str]] = [
    ("Abstract", "abstract.md"),
    ("Introduction", "introduction.md"),
    ("Related Work", "related_work.md"),
    ("Method", "method.md"),
    ("Experimental Setup", "experiment_plan.md"),
    ("Results", "results_section.md"),
    ("Discussion", "discussion.md"),
    ("Limitations", "limitations.md"),
    ("Conclusion", "conclusion.md"),
]


def _sanitize_section(text: str) -> str:
    lines = text.splitlines()
    while lines and lines[0].strip().startswith("#"):
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines).strip()


def build_manuscript(paper_dir: Path = PAPER_DIR) -> str:
    title_candidates = (paper_dir / "title_candidates.md").read_text(encoding="utf-8")
    title_line = next(
        (
            line[3:].strip()
            for line in title_candidates.splitlines()
            if line.strip().startswith("1.")
        ),
        "Governance-Aware AI-Silo for Cryptocurrency Strategy Validation",
    )

    parts = [
        "# Final Manuscript",
        "",
        "## Working Title",
        "",
        title_line,
        "",
        "## Compilation Notes",
        "",
        "- This file is auto-assembled from `docs/paper/*.md` fragments.",
        "- It is intended as the single-source review draft before venue formatting.",
        "- Citation placeholders still need to be replaced with real references.",
        "",
    ]

    for section_title, filename in SECTION_FILES:
        raw_text = (paper_dir / filename).read_text(encoding="utf-8")
        body = _sanitize_section(raw_text)
        parts.extend(
            [
                f"## {section_title}",
                "",
                body,
                "",
            ]
        )

    parts.extend(
        [
            "## Figures and Tables",
            "",
            "Primary figure and table planning artifacts:",
            "",
            "- `docs/paper/figures_plan.md`",
            "- `docs/paper/figure_captions.md`",
            "- `docs/paper/results_tables.md`",
            "- `paper_figures/figure_manifest.json`",
            "- `paper_results/figure_summary.json`",
            "",
            "## Submission Readiness",
            "",
            "Final pre-submission checks live in:",
            "",
            "- `docs/paper/camera_ready_checklist.md`",
            "- `docs/paper/submission_checklist.md`",
            "- `docs/paper/clean_benchmark_protocol.md`",
            "",
        ]
    )

    return "\n".join(parts).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile the paper fragments under docs/paper into one review draft."
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=PAPER_DIR,
        help="Directory containing the paper markdown fragments.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination markdown file.",
    )
    args = parser.parse_args()

    manuscript = build_manuscript(args.paper_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(manuscript, encoding="utf-8")
    print(f"Wrote compiled manuscript to {args.output}")


if __name__ == "__main__":
    main()
