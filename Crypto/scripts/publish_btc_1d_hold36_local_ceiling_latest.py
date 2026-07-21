from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish latest aliases for BTC 1d hold36 local ceiling artifacts."
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    return parser


def _latest(analysis_dir: Path, pattern: str) -> Path:
    matches = sorted(analysis_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return matches[0]


def publish_latest(*, analysis_dir: Path) -> dict[str, str]:
    analysis_dir.mkdir(parents=True, exist_ok=True)

    handoff_json = _latest(analysis_dir, "btc_1d_hold36_local_ceiling_handoff_*.json")
    handoff_md = _latest(analysis_dir, "btc_1d_hold36_local_ceiling_handoff_*.md")
    ceiling_json = _latest(analysis_dir, "btc_1d_hold36_pressure_watch_ceiling_*.json")
    ceiling_md = _latest(analysis_dir, "btc_1d_hold36_pressure_watch_ceiling_*.md")

    latest_targets = {
        "handoff_latest_json": analysis_dir / "btc_1d_hold36_local_ceiling_handoff_latest.json",
        "handoff_latest_md": analysis_dir / "btc_1d_hold36_local_ceiling_handoff_md_latest.md",
        "ceiling_latest_json": analysis_dir / "btc_1d_hold36_pressure_watch_ceiling_latest.json",
        "ceiling_latest_md": analysis_dir / "btc_1d_hold36_pressure_watch_ceiling_md_latest.md",
    }

    latest_targets["handoff_latest_json"].write_text(handoff_json.read_text(encoding="utf-8"), encoding="utf-8")
    latest_targets["handoff_latest_md"].write_text(handoff_md.read_text(encoding="utf-8"), encoding="utf-8")
    latest_targets["ceiling_latest_json"].write_text(ceiling_json.read_text(encoding="utf-8"), encoding="utf-8")
    latest_targets["ceiling_latest_md"].write_text(ceiling_md.read_text(encoding="utf-8"), encoding="utf-8")

    return {
        "handoff_source_json": str(handoff_json),
        "handoff_latest_json": str(latest_targets["handoff_latest_json"]),
        "handoff_source_md": str(handoff_md),
        "handoff_latest_md": str(latest_targets["handoff_latest_md"]),
        "ceiling_source_json": str(ceiling_json),
        "ceiling_latest_json": str(latest_targets["ceiling_latest_json"]),
        "ceiling_source_md": str(ceiling_md),
        "ceiling_latest_md": str(latest_targets["ceiling_latest_md"]),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = publish_latest(analysis_dir=args.analysis_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
