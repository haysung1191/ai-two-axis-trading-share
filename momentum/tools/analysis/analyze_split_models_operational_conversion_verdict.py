from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_verdict"
GUARDRAIL_MATRIX_JSON = (
    ROOT / "output" / "split_models_operational_conversion_guardrail_matrix" / "guardrail_matrix_summary.json"
)
DRAWDOWN_JSON = (
    ROOT / "output" / "split_models_operational_conversion_drawdown" / "operational_conversion_drawdown_summary.json"
)
ANCHOR_RESET_JSON = (
    ROOT / "output" / "split_models_operational_conversion_anchor_reset_sweep" / "anchor_reset_sweep_summary.json"
)
PROMOTION_RECOMMENDATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_promotion_recommendation"
    / "promotion_recommendation_summary.json"
)
OOS_REGISTRATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_oos_registration"
    / "oos_registration_summary.json"
)
OOS_ROBUSTNESS_GATE_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_oos_robustness_gate"
    / "oos_robustness_gate_summary.json"
)


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Verdict",
        "",
        "## Current State",
        "",
        f"- current anchor: `{summary['anchor_variant']}`",
        f"- anchor CAGR: `{_pct(summary['anchor_cagr'])}`",
        f"- anchor MDD: `{_pct(summary['anchor_mdd'])}`",
        f"- operating baseline MDD: `{_pct(summary['baseline_mdd'])}`",
        f"- remaining drawdown gap: `{_pct(summary['drawdown_gap_vs_baseline'])}`",
        "",
        "## Verdict",
        "",
        f"- promotion status: `{summary['promotion_status']}`",
        f"- OOS registered candidate: `{summary['oos_registered_variant']}`",
        f"- anchor reset result: `{summary['anchor_reset_result']}`",
        f"- guardrail result: `{summary['guardrail_result']}`",
        f"- recommended representative candidate: `{summary['recommended_representative_variant']}`",
        "",
        "## Why It Fails",
        "",
        f"- tested drawdown-improving axes found: `{summary['drawdown_improver_count']}`",
        f"- repeated overlays only improved quality at the same drawdown: `{summary['quality_overlay_count']}`",
        f"- worst known drawdown regime runs from `{summary['drawdown_window_peak']}` to `{summary['drawdown_window_trough']}`",
        f"- main symbol drags in that regime remain `{summary['top_symbol_drags']}`",
        "",
        "## Resume Condition",
        "",
        "- only reopen this branch if a new structure beats the anchor on MDD first",
        f"- minimum bar for reopening: improve MDD above `{_pct(summary['anchor_mdd'])}` without introducing negative walk-forward windows",
        "- otherwise treat this branch as research-strong but operating-blocked",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    guardrail = _load_json(GUARDRAIL_MATRIX_JSON)
    drawdown = _load_json(DRAWDOWN_JSON)
    anchor_reset = _load_json(ANCHOR_RESET_JSON)
    recommendation = _load_json(PROMOTION_RECOMMENDATION_JSON)
    oos_registration = _load_json(OOS_REGISTRATION_JSON)
    oos_robustness_gate = _load_json(OOS_ROBUSTNESS_GATE_JSON) if OOS_ROBUSTNESS_GATE_JSON.exists() else {}

    top_symbol_drags = ", ".join(item["Symbol"] for item in drawdown["worst_symbol_deltas_vs_baseline"][:2])
    drawdown_improver_count = int(guardrail["drawdown_improver_count"])
    summary = {
        "anchor_variant": guardrail["base_variant"],
        "anchor_cagr": float(guardrail["base_cagr"]),
        "anchor_mdd": float(guardrail["base_mdd"]),
        "anchor_sharpe": float(guardrail["base_sharpe"]),
        "baseline_mdd": float(guardrail["baseline_mdd"]),
        "drawdown_gap_vs_baseline": float(guardrail["base_mdd"] - guardrail["baseline_mdd"]),
        "drawdown_improver_count": drawdown_improver_count,
        "quality_overlay_count": int(guardrail["quality_up_same_drawdown_count"]),
        "no_op_count": int(guardrail["no_op_count"]),
        "best_quality_axis": str(guardrail["best_quality_axis"]),
        "best_quality_variant": str(guardrail["best_quality_variant"]),
        "recommended_representative_variant": str(recommendation["recommended_variant"]),
        "recommendation_reason": str(recommendation["recommendation_reason"]),
        "drawdown_window_peak": str(drawdown["candidate_drawdown_window"]["peak_next_date"]),
        "drawdown_window_trough": str(drawdown["candidate_drawdown_window"]["trough_next_date"]),
        "top_symbol_drags": top_symbol_drags,
        "anchor_reset_result": (
            "current_anchor_confirmed"
            if anchor_reset["best_variant"] == guardrail["base_variant"]
            else "better_nearby_anchor_found"
        ),
        "guardrail_result": (
            "drawdown_repair_axes_found_but_not_promotable"
            if drawdown_improver_count > 0
            else "no_drawdown_repair_axis_found"
        ),
        "oos_registration_status": str(oos_registration["status"]),
        "oos_registered_candidate_id": str(oos_registration["candidate_id"]),
        "oos_registered_variant": str(oos_registration["variant"]),
        "oos_next_stage": str(oos_registration["next_stage"]),
        "oos_required_next_gates": [str(item) for item in oos_registration["required_next_gates"]],
        "oos_robustness_gate_decision": str(oos_robustness_gate.get("gate_decision") or ""),
        "promotion_status": (
            "ready_for_operation_review"
            if oos_robustness_gate.get("promotion_decision") == "READY_FOR_OPERATION_REVIEW"
            else "blocked_by_oos_robustness"
            if oos_registration.get("status") == "REGISTERED_FOR_OOS_ROBUSTNESS"
            else "blocked_by_drawdown"
        ),
        "verdict": (
            f"`{oos_registration['variant']}` passed registration, OOS start-shift, parameter sensitivity, "
            f"window-overfit, cost/turnover, and no-submit shadow dry-run gates as `{oos_registration['candidate_id']}`. "
            f"The operational-conversion branch is ready for operation review; this does not enable paper, live, "
            f"broker submit, or order intent."
            if oos_robustness_gate.get("promotion_decision") == "READY_FOR_OPERATION_REVIEW"
            else
            f"`{oos_registration['variant']}` closes the current drawdown bottleneck on first-order metrics and is "
            f"registered as `{oos_registration['candidate_id']}` for `{oos_registration['next_stage']}`. "
            f"Promotion remains blocked until OOS, parameter sensitivity, window-overfit, cost/turnover stress, "
            f"and no-submit shadow dry-run gates pass."
            if oos_registration.get("status") == "REGISTERED_FOR_OOS_ROBUSTNESS"
            else (
                f"`{guardrail['base_variant']}` remains the best nearby operational-conversion anchor, "
                f"but promotion is blocked because drawdown stays {_pct(guardrail['base_mdd'])}, "
                f"which is {_pct(guardrail['base_mdd'] - guardrail['baseline_mdd'])} worse than the operating baseline. "
                f"The branch now has `{drawdown_improver_count}` drawdown-improving axis/axes, but even the recommended "
                f"representative `{recommendation['recommended_variant']}` remains below the operating drawdown bar."
            )
        ),
    }

    (OUTPUT_DIR / "operational_conversion_verdict_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "operational_conversion_verdict.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
