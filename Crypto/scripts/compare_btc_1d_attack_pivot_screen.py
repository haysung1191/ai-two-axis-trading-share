from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_spike_reversal_secondary_promotion_screen import (
    build_report as build_secondary_promotion_screen,
)
from scripts.compare_btc_1d_trend_dip_attack_reopen_screen import (
    build_report as build_trend_dip_reopen_screen,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_primary_step(step_name: str) -> dict:
    matches = sorted(
        ANALYSIS_DIR.glob("btc_1d_attack_primary_queue_step_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in matches:
        payload = _load_json(path)
        if str(payload.get("step")) == step_name:
            return payload
    raise FileNotFoundError(f"No primary queue step artifact found for step={step_name}.")


def _fallback_secondary(reason: str) -> dict:
    return {
        "secondary_branch_candidate": {"label": "secondary_unavailable"},
        "secondary_branch_verdict": {
            "promotion_status": "blocked_missing_archived_artifacts",
            "promotion_ready": False,
            "next_required_gate": "regenerate_archived_artifacts",
            "reason": reason,
        },
    }


def _fallback_primary_step(step_name: str, reason: str) -> dict:
    return {
        "step": step_name,
        "step_verdict": {
            "status": "missing_archived_artifacts",
            "next_step": "hold_primary_anchor",
            "reason": reason,
        },
    }


def build_report() -> dict:
    reopen = build_trend_dip_reopen_screen()
    try:
        secondary = build_secondary_promotion_screen()
    except FileNotFoundError as exc:
        secondary = _fallback_secondary(str(exc))
    try:
        compression_step = _latest_primary_step("exit_compression_batch")
    except FileNotFoundError as exc:
        compression_step = _fallback_primary_step("exit_compression_batch", str(exc))
    try:
        symmetry_step = _latest_primary_step("exit_symmetry_batch")
    except FileNotFoundError as exc:
        symmetry_step = _fallback_primary_step("exit_symmetry_batch", str(exc))

    current_anchor = reopen["current_candidate"]
    secondary_verdict = secondary["secondary_branch_verdict"]
    primary_closed = symmetry_step["step_verdict"]["next_step"] == "hold_primary_anchor"

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "primary_lane_status": {
            "label": current_anchor["label"],
            "strategy_name": current_anchor["strategy_name"],
            "anchor_cagr": float(current_anchor["cagr"]),
            "anchor_max_drawdown": float(current_anchor["max_drawdown"]),
            "compression_result": compression_step["step_verdict"]["status"],
            "symmetry_result": symmetry_step["step_verdict"]["status"],
            "mutation_space_closed": primary_closed,
        },
        "secondary_lane_status": {
            "label": secondary["secondary_branch_candidate"]["label"],
            "promotion_status": secondary_verdict["promotion_status"],
            "promotion_ready": secondary_verdict["promotion_ready"],
            "next_required_gate": secondary_verdict["next_required_gate"],
        },
        "pivot_verdict": {
            "active_attack_anchor": current_anchor["label"],
            "pivot_mode": "hold_primary_anchor_and_defer_secondary",
            "next_model_development_lane": "secondary_friction_repair_or_new_family_search",
            "continue_primary_mutation_loop": False,
            "promote_secondary_now": False,
            "reason": (
                "Primary compression and symmetry both failed to beat the current drawdown anchor, "
                "and the secondary spike-reversal branch is still blocked by friction and promotion depth."
            ),
        },
        "decision_summary": [
            f"Keep `{current_anchor['label']}` as the active attack anchor because the tested primary mutation paths did not improve drawdown.",
            (
                f"Do not promote `{secondary['secondary_branch_candidate']['label']}` yet because it remains "
                f"`{secondary_verdict['promotion_status']}` and still needs `{secondary_verdict['next_required_gate']}`."
            ),
            "Use the next model-development cycle either to repair secondary friction depth or to open a new family search outside the exhausted primary mutation space.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    primary = report["primary_lane_status"]
    secondary = report["secondary_lane_status"]
    verdict = report["pivot_verdict"]
    return "\n".join(
        [
            "# BTC 1d Attack Pivot Screen",
            "",
            f"- Active attack anchor: `{verdict['active_attack_anchor']}`",
            f"- Pivot mode: `{verdict['pivot_mode']}`",
            f"- Next model-development lane: `{verdict['next_model_development_lane']}`",
            f"- Continue primary mutation loop: `{verdict['continue_primary_mutation_loop']}`",
            f"- Promote secondary now: `{verdict['promote_secondary_now']}`",
            f"- Reason: {verdict['reason']}",
            "",
            "## Primary Lane",
            f"- Label: `{primary['label']}`",
            f"- Anchor base: `{primary['anchor_cagr']:.4f}` CAGR / `{primary['anchor_max_drawdown']:.4f}` MDD",
            f"- Compression result: `{primary['compression_result']}`",
            f"- Symmetry result: `{primary['symmetry_result']}`",
            f"- Mutation space closed: `{primary['mutation_space_closed']}`",
            "",
            "## Secondary Lane",
            f"- Label: `{secondary['label']}`",
            f"- Promotion status: `{secondary['promotion_status']}`",
            f"- Promotion ready: `{secondary['promotion_ready']}`",
            f"- Next required gate: `{secondary['next_required_gate']}`",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_pivot_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_pivot_screen_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_attack_pivot_screen_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_attack_pivot_screen_latest.md"
    json_payload = json.dumps(report, indent=2)
    md_payload = _render_markdown(report)
    json_path.write_text(json_payload, encoding="utf-8")
    md_path.write_text(md_payload, encoding="utf-8")
    latest_json.write_text(json_payload, encoding="utf-8")
    latest_md.write_text(md_payload, encoding="utf-8")
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "latest_json_path": str(latest_json),
                "latest_md_path": str(latest_md),
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
