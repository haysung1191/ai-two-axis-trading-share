from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_btc_1d_shadow_update import refresh_operator_stack


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Fast-refresh the BTC 1d operator stack from existing latest artifacts "
            "(paper nightly, operating index/brief, contract screens, dashboard)."
        )
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--sync-passes", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = refresh_operator_stack(
        analysis_dir=args.analysis_dir,
        sync_passes=int(args.sync_passes),
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
