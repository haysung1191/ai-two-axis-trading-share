from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_status_snapshot"
VERDICT_JSON = (
    ROOT / "output" / "split_models_operational_conversion_verdict" / "operational_conversion_verdict_summary.json"
)
PROMOTION_GATE_JSON = (
    ROOT / "output" / "split_models_operational_conversion_promotion_gate" / "promotion_gate_summary.json"
)
GUARDRAIL_MATRIX_JSON = (
    ROOT / "output" / "split_models_operational_conversion_guardrail_matrix" / "guardrail_matrix_summary.json"
)
PROMOTION_RECOMMENDATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_promotion_recommendation"
    / "promotion_recommendation_summary.json"
)
REPRESENTATIVE_CHALLENGER_CLOSURE_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_representative_challenger_closure"
    / "representative_challenger_closure_summary.json"
)
REPRESENTATIVE_DECISION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_representative_decision"
    / "representative_decision_summary.json"
)
PROBE_CONTRACT_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_probe_contract"
    / "probe_contract_summary.json"
)
REFRESH_CONTRACT_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_refresh_contract"
    / "refresh_contract_summary.json"
)
ENTRYPOINT_CONTRACT_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_entrypoint_contract"
    / "entrypoint_contract_summary.json"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Status Snapshot",
        "",
        "## Authoritative State",
        "",
        f"- gate status: `{summary['gate_status']}`",
        f"- promotion status: `{summary['promotion_status']}`",
        f"- current anchor: `{summary['anchor_variant']}`",
        f"- best quality overlay: `{summary['best_quality_variant']}`",
        f"- recommended representative candidate: `{summary['recommended_representative_variant']}`",
        f"- representative challenger search closed: `{summary['representative_challenger_search_closed']}`",
        "",
        "## Hard Numbers",
        "",
        f"- anchor MDD: `{summary['anchor_mdd_display']}`",
        f"- baseline MDD: `{summary['baseline_mdd_display']}`",
        f"- drawdown gap vs baseline: `{summary['drawdown_gap_vs_baseline_display']}`",
        f"- drawdown improver count: `{summary['drawdown_improver_count']}`",
        f"- quality overlay count: `{summary['quality_overlay_count']}`",
        f"- no-op count: `{summary['no_op_count']}`",
        "",
        "## Canonical Files",
        "",
        f"- verdict: `{summary['verdict_file']}`",
        f"- promotion gate: `{summary['promotion_gate_file']}`",
        f"- guardrail matrix: `{summary['guardrail_matrix_file']}`",
        f"- promotion recommendation: `{summary['promotion_recommendation_file']}`",
        f"- representative challenger closure: `{summary['representative_challenger_closure_file']}`",
        f"- representative decision: `{summary['representative_decision_file']}`",
        f"- probe contract: `{summary['probe_contract_file']}`",
        f"- refresh contract: `{summary['refresh_contract_file']}`",
        f"- entrypoint contract: `{summary['entrypoint_contract_file']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    verdict = _load_json(VERDICT_JSON)
    gate = _load_json(PROMOTION_GATE_JSON)
    matrix = _load_json(GUARDRAIL_MATRIX_JSON)
    recommendation = _load_json(PROMOTION_RECOMMENDATION_JSON)
    challenger_closure = _load_json(REPRESENTATIVE_CHALLENGER_CLOSURE_JSON)
    representative_decision = _load_json(REPRESENTATIVE_DECISION_JSON)
    probe_contract = _load_json(PROBE_CONTRACT_JSON)
    refresh_contract = _load_json(REFRESH_CONTRACT_JSON)
    entrypoint_contract = _load_json(ENTRYPOINT_CONTRACT_JSON)

    summary = {
        "gate_status": str(gate["gate_status"]),
        "promotion_status": str(verdict["promotion_status"]),
        "anchor_variant": str(verdict["anchor_variant"]),
        "best_quality_variant": str(matrix["best_quality_variant"]),
        "recommended_representative_variant": str(recommendation["recommended_variant"]),
        "recommendation_reason": str(recommendation["recommendation_reason"]),
        "representative_challenger_search_closed": True,
        "challenger_family_count": int(challenger_closure["challenger_family_count"]),
        "representative_replacements_found": int(challenger_closure["representative_replacements_found"]),
        "representative_challenger_closure_verdict": str(challenger_closure["verdict"]),
        "representative_decision_verdict": str(representative_decision["verdict"]),
        "probe_contract_verdict": str(probe_contract["verdict"]),
        "refresh_contract_verdict": str(refresh_contract["verdict"]),
        "entrypoint_contract_verdict": str(entrypoint_contract["verdict"]),
        "anchor_mdd": float(verdict["anchor_mdd"]),
        "anchor_mdd_display": str(gate["current_value_display"]),
        "baseline_mdd": float(verdict["baseline_mdd"]),
        "baseline_mdd_display": str(gate["baseline_reference_display"]),
        "drawdown_gap_vs_baseline": float(verdict["drawdown_gap_vs_baseline"]),
        "drawdown_gap_vs_baseline_display": str(gate["drawdown_gap_vs_baseline_display"]),
        "drawdown_improver_count": int(matrix["drawdown_improver_count"]),
        "quality_overlay_count": int(matrix["quality_up_same_drawdown_count"]),
        "no_op_count": int(matrix["no_op_count"]),
        "verdict_file": "output/split_models_operational_conversion_verdict/operational_conversion_verdict_summary.json",
        "promotion_gate_file": "output/split_models_operational_conversion_promotion_gate/promotion_gate_summary.json",
        "guardrail_matrix_file": "output/split_models_operational_conversion_guardrail_matrix/guardrail_matrix_summary.json",
        "promotion_recommendation_file": (
            "output/split_models_operational_conversion_promotion_recommendation/promotion_recommendation_summary.json"
        ),
        "representative_challenger_closure_file": (
            "output/split_models_operational_conversion_representative_challenger_closure/representative_challenger_closure_summary.json"
        ),
        "representative_decision_file": (
            "output/split_models_operational_conversion_representative_decision/representative_decision_summary.json"
        ),
        "probe_contract_file": "output/split_models_operational_conversion_probe_contract/probe_contract_summary.json",
        "refresh_contract_file": "output/split_models_operational_conversion_refresh_contract/refresh_contract_summary.json",
        "entrypoint_contract_file": "output/split_models_operational_conversion_entrypoint_contract/entrypoint_contract_summary.json",
    }

    (OUTPUT_DIR / "status_snapshot_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "status_snapshot.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
