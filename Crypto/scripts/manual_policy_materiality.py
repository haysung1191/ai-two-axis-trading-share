from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.manual_daily_summary import build_manual_daily_summary


def render_text_materiality(payload: dict) -> str:
    materiality = payload.get("policy_materiality", {})
    snapshot_metadata = payload.get("snapshot_metadata", {})
    market_filter = snapshot_metadata.get("market_filter", {}) if isinstance(snapshot_metadata, dict) else {}
    lines = [
        f"generated_at: {payload.get('generated_at', '-')}",
        f"bundle_id: {payload.get('policy_snapshot', {}).get('bundle_id', '-')}",
        "",
        "market_filter:",
        f"- active: {bool(market_filter.get('below_ema', False))}",
        f"- symbol: {market_filter.get('symbol', '-')}",
        f"- close: {market_filter.get('close', '-')}",
        f"- ema_period: {market_filter.get('ema_period', '-')}",
        f"- ema: {market_filter.get('ema', '-')}",
        "",
        "policy_materiality:",
        f"- boosted_candidates: {materiality.get('boosted_candidate_count', 0)}",
        f"- direct_reversals: {materiality.get('direct_reversal_count', 0)}",
        f"- near_misses: {materiality.get('near_miss_count', 0)}",
        f"- cutoff_rank: {materiality.get('cutoff_rank', '-')}",
        f"- cutoff_score: {materiality.get('cutoff_score', '-')}",
        "",
        "closest_boosted_candidates_to_reversal:",
    ]
    rows = materiality.get("closest_to_reversal", [])
    if rows:
        for row in rows:
            lines.append(
                "  "
                + " | ".join(
                    [
                        str(row.get("symbol", "-")),
                        f"raw_rank={row.get('raw_rank', '-')}",
                        f"final_rank={row.get('final_rank', '-')}",
                        f"final_decision={row.get('final_decision', '-')}",
                        f"delta={row.get('applied_delta', '-')}",
                        f"gap_after_boost={row.get('gap_to_cutoff_after_boost', '-')}",
                        f"extra_delta_needed={row.get('required_extra_delta_for_cutoff', '-')}",
                        f"policy={row.get('policy_materiality', '-')}",
                    ]
                )
            )
    else:
        lines.append("  (none)")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print policy materiality around the current manual snapshot cutoff.")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument("--reexport-dir", default="artifacts_reexport")
    parser.add_argument("--logs-dir", default="logs")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    payload = build_manual_daily_summary(
        artifacts_dir=Path(args.artifacts_dir),
        reexport_dir=Path(args.reexport_dir),
        logs_dir=Path(args.logs_dir),
        run_id=args.run_id,
    )
    if args.format == "json":
        print(json.dumps(payload.get("policy_materiality", {}), ensure_ascii=False, indent=2))
    else:
        print(render_text_materiality(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
