from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.execution.paper_execution_ledger import (
    apply_exit_snapshot_to_paper_ledger,
    load_paper_execution_ledger,
    save_paper_execution_ledger,
)


def load_exit_snapshot(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def render_text_summary(payload: dict) -> str:
    summary = payload.get("last_exit_summary", {})
    lines = [
        f"last_run_id: {payload.get('last_run_id', '-')}",
        f"last_candle_close_utc: {payload.get('last_candle_close_utc', '-')}",
        f"closed_count: {summary.get('closed_count', 0)}",
        f"open_count: {summary.get('open_count', 0)}",
        "",
        "closed_positions:",
    ]
    closed = [row for row in payload.get("closed_positions", []) if row.get("exit_run_id") == payload.get("last_run_id")]
    for row in closed:
        lines.append(
            "  "
            + " | ".join(
                [
                    str(row.get("market", "-")),
                    f"reason={row.get('exit_reason', '-')}",
                    f"entry={row.get('entry_price_krw', '-')}",
                    f"exit={row.get('exit_price_krw', '-')}",
                    f"pnl={row.get('pnl_krw', '-')}",
                ]
            )
        )
    if not closed:
        lines.append("  (no closes this run)")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Apply an OHLC exit snapshot to the local Bithumb paper execution ledger. "
            "Standard operating check order: practical -> research -> contract -> brief."
        )
    )
    parser.add_argument("--exit-json", required=True, help="Exit snapshot JSON path")
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
    updated = apply_exit_snapshot_to_paper_ledger(
        load_paper_execution_ledger(ledger_path),
        load_exit_snapshot(Path(args.exit_json)),
    )
    save_paper_execution_ledger(ledger_path, updated)

    if args.format == "json":
        print(json.dumps(updated, ensure_ascii=False, indent=2))
    else:
        print(render_text_summary(updated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
