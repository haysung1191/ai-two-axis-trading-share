from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.execution.paper_execution_ledger import (
    apply_execution_plan_to_paper_ledger,
    load_paper_execution_ledger,
    save_paper_execution_ledger,
)


def load_execution_plan(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render_text_summary(payload: dict) -> str:
    summary = payload.get("last_apply_summary", {})
    lines = [
        f"last_run_id: {payload.get('last_run_id', '-')}",
        f"last_candle_close_utc: {payload.get('last_candle_close_utc', '-')}",
        f"applied_count: {summary.get('applied_count', 0)}",
        f"rejected_count: {summary.get('rejected_count', 0)}",
        f"duplicate_count: {summary.get('duplicate_count', 0)}",
        f"open_positions: {len([row for row in payload.get('positions', []) if row.get('status') == 'OPEN'])}",
        "",
        "positions:",
    ]
    positions = [row for row in payload.get("positions", []) if row.get("status") == "OPEN"]
    for row in positions:
        lines.append(
            "  "
            + " | ".join(
                [
                    str(row.get("market", "-")),
                    f"track={row.get('strategy_track', '-')}",
                    f"entry={row.get('entry_price_krw', '-')}",
                    f"quote={row.get('quote_amount_krw', '-')}",
                ]
            )
        )
    if not positions:
        lines.append("  (no open positions)")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Apply a Bithumb execution plan to the local paper execution ledger. "
            "Standard operating check order: practical -> research -> contract -> brief."
        )
    )
    parser.add_argument("--plan-json", required=True, help="Execution plan JSON path")
    parser.add_argument(
        "--ledger-json",
        default="artifacts/paper_execution/bithumb_paper_ledger.json",
        help="Paper ledger JSON path",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    ledger_path = Path(args.ledger_json)
    updated = apply_execution_plan_to_paper_ledger(
        load_paper_execution_ledger(ledger_path),
        load_execution_plan(Path(args.plan_json)),
    )
    save_paper_execution_ledger(ledger_path, updated)

    if args.format == "json":
        print(json.dumps(updated, ensure_ascii=False, indent=2))
    else:
        print(render_text_summary(updated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
