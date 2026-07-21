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
from src.manual.checklist import build_pretrade_checklist
from src.manual.watchlist import build_manual_watchlist


def render_text_checklist(payload: dict) -> str:
    lines = [
        f"generated_at: {payload.get('generated_at', '-')}",
        f"strategy_id: {payload.get('strategy_id', '-')}",
        f"bundle_id: {payload.get('bundle_id', '-')}",
        "",
        f"headline: {payload.get('headline', '-')}",
        "",
        "general_checks:",
    ]
    for item in payload.get("general_checks", []):
        lines.append(f"- {item}")

    lines.append("")
    lines.append("candidate_checklists:")
    candidate_checklists = payload.get("candidate_checklists", [])
    if candidate_checklists:
        for candidate in candidate_checklists:
            lines.append(
                f"  {candidate.get('symbol', '-')} | rank={candidate.get('rank', '-')} | policy={candidate.get('policy_materiality', '-')}"
            )
            for check in candidate.get("checks", []):
                lines.append(f"    - {check.get('label', '-')}: {check.get('detail', '-')}")
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
    parser = argparse.ArgumentParser(description="Print a manual pre-trade checklist from local artifacts.")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument("--reexport-dir", default="artifacts_reexport")
    parser.add_argument("--logs-dir", default="logs")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--max-items", type=int, default=3)
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
        max_buy=max(1, args.max_items),
        max_monitor=5,
    )
    checklist = build_pretrade_checklist(
        watchlist=watchlist,
        max_items=max(1, args.max_items),
    )

    if args.format == "json":
        print(json.dumps(checklist, ensure_ascii=False, indent=2))
    else:
        print(render_text_checklist(checklist))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
