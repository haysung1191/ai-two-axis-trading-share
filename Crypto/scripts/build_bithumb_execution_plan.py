from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.manual_trade_brief import load_manual_brief
from src.execution import build_bithumb_entry_plan


def render_text_plan(payload: dict) -> str:
    lines = [
        f"run_id: {payload.get('run_id', '-')}",
        f"candle_close_utc: {payload.get('candle_close_utc', '-')}",
        f"strategy_track: {payload.get('strategy_track', '-')}",
        f"intent_count: {payload.get('intent_count', 0)}",
        f"notional_krw: {payload.get('notional_krw', 0):,.0f}",
        "",
        "order_intents:",
    ]
    for row in payload.get("order_intents", []):
        lines.append(
            "  "
            + " | ".join(
                [
                    str(row.get("market", "-")),
                    f"side={row.get('side', '-')}",
                    f"order_type={row.get('order_type', '-')}",
                    f"quote={float(row.get('quote_amount_krw', 0.0)):,.0f} KRW",
                    f"rank={row.get('source_rank', '-')}",
                    f"decision={row.get('source_decision', '-')}",
                ]
            )
        )
        lines.append(f"    note: {row.get('action_reason', '-')}")
    if not payload.get("order_intents"):
        lines.append("  (no actionable BUY intents)")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Bithumb execution plan from the latest manual trading brief. "
            "Standard operating check order: practical -> research -> contract -> brief."
        )
    )
    parser.add_argument("--run-id", default=None, help="Optional run_id like 1h:1773572400000")
    parser.add_argument("--logs-dir", default="logs", help="Directory containing hourly_run_*.json files")
    parser.add_argument("--notional-krw", type=float, default=100000.0, help="Quote KRW size per market buy intent")
    parser.add_argument("--max-orders", type=int, default=1, help="Maximum number of BUY intents to emit")
    parser.add_argument("--track", choices=["operating", "attack"], default="operating")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", default=None, help="Optional JSON output path")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    brief_payload = load_manual_brief(Path(args.logs_dir), run_id=args.run_id)
    plan = build_bithumb_entry_plan(
        brief_payload,
        notional_krw=float(args.notional_krw),
        max_orders=int(args.max_orders),
        strategy_track=str(args.track),
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print(render_text_plan(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
