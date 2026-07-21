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
from src.manual.operator_watchlist import build_operator_watchlist


def build_manual_operator_watchlist(
    *,
    artifacts_dir: Path,
    reexport_dir: Path,
    logs_dir: Path,
    run_id: str | None = None,
    max_baseline: int = 5,
    max_policy_assisted: int = 5,
    max_recheck: int = 5,
) -> dict:
    daily_summary = build_manual_daily_summary(
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        logs_dir=logs_dir,
        run_id=run_id,
    )
    brief_payload = load_manual_brief(logs_dir, run_id=run_id)
    return build_operator_watchlist(
        daily_summary=daily_summary,
        recommendations=brief_payload["manual_recommendations"],
        max_baseline=max_baseline,
        max_policy_assisted=max_policy_assisted,
        max_recheck=max_recheck,
    )


def render_text_operator_watchlist(payload: dict) -> str:
    lines = [
        f"generated_at: {payload.get('generated_at', '-')}",
        f"headline: {payload.get('headline', '-')}",
        f"market_filter_active: {payload.get('market_filter_active', False)}",
        "",
        "baseline_priority:",
    ]
    baseline = payload.get("baseline_priority", [])
    if baseline:
        for row in baseline:
            lines.append(
                "  "
                + " | ".join(
                    [
                        str(row.get("symbol", "-")),
                        f"rank={row.get('final_rank', '-')}",
                        f"score={row.get('final_ranking_score', '-')}",
                        f"policy={row.get('policy_materiality', '-')}",
                    ]
                )
            )
            lines.append(f"    note: {row.get('note', '-')}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("policy_assisted:")
    assisted = payload.get("policy_assisted", [])
    if assisted:
        for row in assisted:
            lines.append(
                "  "
                + " | ".join(
                    [
                        str(row.get("symbol", "-")),
                        f"rank={row.get('final_rank', '-')}",
                        f"score={row.get('final_ranking_score', '-')}",
                        f"delta={row.get('policy_score_delta', '-')}",
                        f"policy={row.get('policy_materiality', '-')}",
                    ]
                )
            )
            lines.append(f"    note: {row.get('note', '-')}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("recheck_on_filter_release:")
    recheck = payload.get("recheck_on_filter_release", [])
    if recheck:
        for row in recheck:
            lines.append(
                "  "
                + " | ".join(
                    [
                        str(row.get("symbol", "-")),
                        f"rank={row.get('final_rank', '-')}",
                        f"score={row.get('final_ranking_score', '-')}",
                        f"policy={row.get('policy_materiality', '-')}",
                    ]
                )
            )
    else:
        lines.append("  (none)")

    if payload.get("warnings"):
        lines.extend(["", "warnings:"])
        for warning in payload["warnings"]:
            lines.append(f"- {warning}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the operator watchlist from the latest manual snapshot.")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument("--reexport-dir", default="artifacts_reexport")
    parser.add_argument("--logs-dir", default="logs")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--max-baseline", type=int, default=5)
    parser.add_argument("--max-policy-assisted", type=int, default=5)
    parser.add_argument("--max-recheck", type=int, default=5)
    args = parser.parse_args()

    payload = build_manual_operator_watchlist(
        artifacts_dir=Path(args.artifacts_dir),
        reexport_dir=Path(args.reexport_dir),
        logs_dir=Path(args.logs_dir),
        run_id=args.run_id,
        max_baseline=max(1, args.max_baseline),
        max_policy_assisted=max(1, args.max_policy_assisted),
        max_recheck=max(1, args.max_recheck),
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text_operator_watchlist(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
