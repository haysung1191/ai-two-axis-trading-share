from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.manual_daily_summary import build_manual_daily_summary, render_text_summary
from scripts.manual_operator_watchlist import build_manual_operator_watchlist, render_text_operator_watchlist
from scripts.manual_pretrade_checklist import render_text_checklist
from scripts.manual_trade_brief import load_manual_brief
from scripts.manual_watchlist import render_text_watchlist
from src.manual.checklist import build_pretrade_checklist
from src.manual.watchlist import build_manual_watchlist


def build_manual_today_briefing(
    *,
    artifacts_dir: Path,
    reexport_dir: Path,
    logs_dir: Path,
    run_id: str | None = None,
    max_buy: int = 3,
    max_monitor: int = 5,
    max_checklist_items: int = 3,
    max_operator_baseline: int = 5,
    max_operator_policy_assisted: int = 5,
    max_operator_recheck: int = 5,
) -> dict:
    daily_summary = build_manual_daily_summary(
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        logs_dir=logs_dir,
        run_id=run_id,
    )
    brief_payload = load_manual_brief(logs_dir, run_id=run_id)
    watchlist = build_manual_watchlist(
        daily_summary=daily_summary,
        recommendations=brief_payload["manual_recommendations"],
        max_buy=max(1, max_buy),
        max_monitor=max(1, max_monitor),
    )
    checklist = build_pretrade_checklist(
        watchlist=watchlist,
        max_items=max(1, max_checklist_items),
    )
    operator_watchlist = build_manual_operator_watchlist(
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        logs_dir=logs_dir,
        run_id=run_id,
        max_baseline=max(1, max_operator_baseline),
        max_policy_assisted=max(1, max_operator_policy_assisted),
        max_recheck=max(1, max_operator_recheck),
    )
    return {
        "generated_at": daily_summary.get("generated_at"),
        "run_id": daily_summary.get("manual_brief", {}).get("run_id"),
        "daily_summary": daily_summary,
        "operator_watchlist": operator_watchlist,
        "watchlist": watchlist,
        "pretrade_checklist": checklist,
    }


def render_text_today_briefing(payload: dict) -> str:
    lines = [
        "=== Daily Summary ===",
        render_text_summary(payload["daily_summary"]),
        "",
        "=== Operator Watchlist ===",
        render_text_operator_watchlist(payload["operator_watchlist"]),
        "",
        "=== Watchlist ===",
        render_text_watchlist(payload["watchlist"]),
        "",
        "=== Pre-trade Checklist ===",
        render_text_checklist(payload["pretrade_checklist"]),
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the full manual trading briefing from local artifacts.")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument("--reexport-dir", default="artifacts_reexport")
    parser.add_argument("--logs-dir", default="logs")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--max-buy", type=int, default=3)
    parser.add_argument("--max-monitor", type=int, default=5)
    parser.add_argument("--max-checklist-items", type=int, default=3)
    parser.add_argument("--max-operator-baseline", type=int, default=5)
    parser.add_argument("--max-operator-policy-assisted", type=int, default=5)
    parser.add_argument("--max-operator-recheck", type=int, default=5)
    args = parser.parse_args()

    payload = build_manual_today_briefing(
        artifacts_dir=Path(args.artifacts_dir),
        reexport_dir=Path(args.reexport_dir),
        logs_dir=Path(args.logs_dir),
        run_id=args.run_id,
        max_buy=args.max_buy,
        max_monitor=args.max_monitor,
        max_checklist_items=args.max_checklist_items,
        max_operator_baseline=args.max_operator_baseline,
        max_operator_policy_assisted=args.max_operator_policy_assisted,
        max_operator_recheck=args.max_operator_recheck,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text_today_briefing(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
