from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_conversion_candidates import build_attack_conversion_screen
from scripts.compare_btc_1d_pullthrough_exit_to_fresh_seed_brief import (
    build_report as build_pullthrough_exit_report,
)


ANALYSIS_DIR = Path("analysis_results")
POST_SPIKE_STAGE_REVIEW_LATEST = "btc_1d_post_spike_consolidation_breakout_candidate_stage_review_latest.json"


def _load_json_optional(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _stage_ready_families(analysis_dir: Path) -> set[str]:
    stage_review = _load_json_optional(analysis_dir / POST_SPIKE_STAGE_REVIEW_LATEST)
    verdict = stage_review.get("post_spike_candidate_stage_review_verdict") or {}
    if verdict.get("candidate_stage_ready") is True:
        return {"post_spike_consolidation_breakout"}
    return set()


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    upstream_warning: str | None = None
    try:
        pullthrough_exit = build_pullthrough_exit_report()
        fresh_seed_scope = {
            "queue_lane": pullthrough_exit["fresh_seed_verdict"]["queue_lane"],
            "next_step_now": pullthrough_exit["fresh_seed_verdict"]["next_step_now"],
        }
    except (FileNotFoundError, ValueError, KeyError, StopIteration) as exc:
        upstream_warning = str(exc)
        fresh_seed_scope = {
            "queue_lane": "fresh_seed_search_required",
            "next_step_now": "derive_fresh_non_adjacent_attack_seed",
        }
    conversion = build_attack_conversion_screen(analysis_results_dir=analysis_dir)

    stage_ready_families = _stage_ready_families(analysis_dir)
    exhausted_families = {
        "volatility_expansion_pullthrough",
        "volatility_spike_reversal_continuation",
        "trend_dip_reversal_breakout",
        "shallow_liquidity_void_refill_continuation",
    } | stage_ready_families

    candidate_rows = [
        row
        for row in conversion["rows"]
        if row["family"] not in exhausted_families
    ]
    if not candidate_rows:
        raise ValueError("No fresh non-adjacent seed candidates remain after excluding exhausted families.")

    candidate_rows.sort(
        key=lambda row: (
            0 if row["attack_conversion_label"] == "defensive_hold_only" else 1,
            float(row["max_drawdown"]),
            -float(row["sharpe"]),
            -float(row["cagr"]),
        )
    )
    primary = dict(candidate_rows[0])
    secondary = dict(candidate_rows[1]) if len(candidate_rows) > 1 else dict(candidate_rows[0])

    primary_reason = (
        "It is the strongest non-adjacent family still standing after excluding the exhausted pullthrough and spike-reversal lanes, and it already combines low drawdown with positive conversion quality."
    )
    secondary_reason = (
        "It remains behind the primary fresh seed, but it is still a distinct family that can be revisited if the primary seed stalls."
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "fresh_seed_scope": {
            "queue_lane": fresh_seed_scope["queue_lane"],
            "next_step_now": fresh_seed_scope["next_step_now"],
            "excluded_families": sorted(exhausted_families),
            "stage_ready_families_excluded": sorted(stage_ready_families),
            "upstream_warning": upstream_warning,
        },
        "fresh_seed_priority": {
            "primary_seed_family": primary["family"],
            "primary_variant_label": primary["variant_label"],
            "primary_seed_reason": primary_reason,
            "secondary_seed_family": secondary["family"],
            "secondary_variant_label": secondary["variant_label"],
            "secondary_seed_reason": secondary_reason,
        },
        "priority_rows": [
            {
                **primary,
                "priority_rank": 1,
                "priority_reason": primary_reason,
            },
            {
                **secondary,
                "priority_rank": 2,
                "priority_reason": secondary_reason,
            },
        ],
        "decision_summary": [
            f"Open the next fresh seed from `{primary['family']}` because it is the strongest surviving non-adjacent family after exhausted and already-stage-ready families are excluded.",
            f"Keep `{secondary['family']}` as the secondary fresh seed only if the primary seed stalls.",
            "Do not spend the next cycle reopening pullthrough, void-refill, spike-reversal, or trend-dip lanes.",
        ],
        "fresh_seed_verdict": {
            "next_fresh_seed_family": primary["family"],
            "next_fresh_seed_variant": primary["variant_label"],
            "secondary_fresh_seed_family": secondary["family"],
            "reason": (
                "The current practical-adjacent board is exhausted, so the next attack cycle should promote the cleanest surviving family from the broader conversion board rather than continue repairing a closed lane."
            ),
        },
    }
    return report


def _render_markdown(report: dict) -> str:
    scope = report["fresh_seed_scope"]
    rows = report["priority_rows"]
    verdict = report["fresh_seed_verdict"]
    lines = [
        "# BTC 1d Fresh Seed Priority Screen",
        "",
        f"- Queue lane: `{scope['queue_lane']}`",
        f"- Next step now: `{scope['next_step_now']}`",
        f"- Next fresh seed family: `{verdict['next_fresh_seed_family']}`",
        f"- Next fresh seed variant: `{verdict['next_fresh_seed_variant']}`",
        f"- Secondary fresh seed family: `{verdict['secondary_fresh_seed_family']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Excluded Families",
        *(f"- `{family}`" for family in scope["excluded_families"]),
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"## Rank {row['priority_rank']} - {row['family']}",
                f"- variant: `{row['variant_label']}`",
                f"- conversion label: `{row['attack_conversion_label']}`",
                f"- base: `{row['cagr_pct']:.2f}%` CAGR / `{row['mdd_pct']:.2f}%` MDD / Sharpe `{row['sharpe']}`",
                f"- reason: {row['priority_reason']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_fresh_seed_priority_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_fresh_seed_priority_screen_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_fresh_seed_priority_screen_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_fresh_seed_priority_screen_md_latest.md"
    json_payload = json.dumps(report, indent=2)
    md_payload = _render_markdown(report)
    json_path.write_text(json_payload, encoding="utf-8")
    md_path.write_text(md_payload, encoding="utf-8")
    latest_json.write_text(json_payload, encoding="utf-8")
    latest_md.write_text(md_payload, encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
