from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAPER_DIR = ROOT / "docs" / "paper"
PLACEHOLDER_PATTERN = re.compile(r"\b(?:LLM-FIN|AUTO-STRAT|VALID|TAI)-\d+\b")
IGNORED_FILES = {"citation_tracker.md", "final_manuscript_compiled.md"}


def scan_placeholders(paper_dir: Path) -> dict[str, object]:
    counts: Counter[str] = Counter()
    files: dict[str, list[str]] = {}

    for path in sorted(paper_dir.glob("*.md")):
        if path.name in IGNORED_FILES:
            continue
        matches = PLACEHOLDER_PATTERN.findall(path.read_text(encoding="utf-8"))
        if not matches:
            continue
        counts.update(matches)
        files[str(path.relative_to(paper_dir))] = sorted(set(matches))

    return {
        "total_placeholders": sum(counts.values()),
        "unique_placeholders": sorted(counts.keys()),
        "counts": dict(sorted(counts.items())),
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report unresolved citation placeholders in docs/paper markdown files."
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=DEFAULT_PAPER_DIR,
        help="Directory containing paper markdown fragments.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_PAPER_DIR / "placeholder_report.json",
        help="Destination JSON report.",
    )
    args = parser.parse_args()

    report = scan_placeholders(args.paper_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote placeholder report to {args.output}")
    print(f"Total placeholders: {report['total_placeholders']}")


if __name__ == "__main__":
    main()
