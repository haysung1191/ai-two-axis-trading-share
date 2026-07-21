from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.manual_daily_summary import build_manual_daily_summary
from scripts.manual_trade_brief import load_manual_brief
from src.manual.watchlist import build_manual_watchlist


def _fmt(value: object) -> str:
    return "-" if value in (None, "") else str(value)


def render_text_watchlist(payload: dict) -> str:
    lines = [
        f"generated_at: {payload.get('generated_at', '-')}",
        f"strategy_id: {payload.get('strategy_id', '-')}",
        f"bundle_id: {payload.get('bundle_id', '-')}",
        "",
        f"headline: {payload.get('headline', '-')}",
        "",
        "buy_candidates:",
    ]
    buy_candidates = payload.get("buy_candidates", [])
    if buy_candidates:
        for row in buy_candidates:
            lines.append(
                "  "
                + " | ".join(
                    [
                        str(row.get("symbol", "-")),
                        f"rank={row.get('rank', '-')}",
                        f"policy={row.get('policy_materiality', '-')}",
                        f"ref={_fmt(row.get('reference_price_krw'))}",
                        f"stop={_fmt(row.get('suggested_stop_price_krw'))}",
                        f"tp={_fmt(row.get('suggested_take_profit_price_krw'))}",
                        f"rr={_fmt(row.get('risk_reward_ratio'))}",
                    ]
                )
            )
            lines.append(f"    note: {row.get('action_reason', '-')}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("monitor_candidates:")
    monitor_candidates = payload.get("monitor_candidates", [])
    if monitor_candidates:
        for row in monitor_candidates:
            lines.append(
                "  "
                + " | ".join(
                    [
                        str(row.get("symbol", "-")),
                        f"rank={row.get('rank', '-')}",
                        f"policy={row.get('policy_materiality', '-')}",
                        f"decision={row.get('final_decision', '-')}",
                    ]
                )
            )
            lines.append(f"    note: {row.get('action_reason', '-')}")
    else:
        lines.append("  (none)")

    warnings = payload.get("warnings", [])
    if warnings:
        lines.append("")
        lines.append("warnings:")
        for warning in warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a focused manual trading watchlist from local artifacts.")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument("--reexport-dir", default="artifacts_reexport")
    parser.add_argument("--logs-dir", default="logs")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--max-buy", type=int, default=3)
    parser.add_argument("--max-monitor", type=int, default=5)
    args = parser.parse_args()

    daily_summary = build_manual_daily_summary(
        artifacts_dir=Path(args.artifacts_dir),
        reexport_dir=Path(args.reexport_dir),
        logs_dir=Path(args.logs_dir),
        run_id=args.run_id,
    )
    brief_payload = load_manual_brief(Path(args.logs_dir), run_id=args.run_id)
    watchlist = build_manual_watchlist(
        daily_summary=daily_summary,
        recommendations=brief_payload["manual_recommendations"],
        max_buy=max(1, args.max_buy),
        max_monitor=max(1, args.max_monitor),
    )

    if args.format == "json":
        print(json.dumps(watchlist, ensure_ascii=False, indent=2))
    else:
        print(render_text_watchlist(watchlist))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
