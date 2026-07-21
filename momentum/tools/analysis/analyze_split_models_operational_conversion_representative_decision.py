from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_representative_decision"
LADDER_JSON = (
    ROOT / "output" / "split_models_operational_conversion_candidate_ladder" / "candidate_ladder_summary.json"
)
RECOMMENDATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_promotion_recommendation"
    / "promotion_recommendation_summary.json"
)
FOLLOWUP_CONTRACT_JSON = (
    ROOT / "output" / "split_models_operational_conversion_followup_contract" / "followup_contract_summary.json"
)
CHALLENGER_CLOSURE_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_representative_challenger_closure"
    / "representative_challenger_closure_summary.json"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _build_markdown(summary: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Split Models Operational Conversion Representative Decision",
            "",
            "## Final Decision",
            "",
            f"- official representative: `{summary['recommended_variant']}`",
            f"- decision reason: `{summary['recommendation_reason']}`",
            f"- growth boundary: `{summary['growth_boundary_variant']}`",
            f"- drawdown boundary: `{summary['drawdown_boundary_variant']}`",
            f"- same-drawdown quality reference: `{summary['quality_reference_variant']}`",
            "",
            "## Key Tradeoff",
            "",
            f"- representative CAGR / MDD: `{summary['recommended_cagr_display']}` / `{summary['recommended_mdd_display']}`",
            f"- growth boundary CAGR / MDD: `{summary['growth_boundary_cagr_display']}` / `{summary['growth_boundary_mdd_display']}`",
            f"- drawdown boundary CAGR / MDD: `{summary['drawdown_boundary_cagr_display']}` / `{summary['drawdown_boundary_mdd_display']}`",
            "",
            "## Challenger Search Closure",
            "",
            f"- challenger family count: `{summary['challenger_family_count']}`",
            f"- representative replacements found: `{summary['representative_replacements_found']}`",
            f"- closure verdict: `{summary['challenger_closure_verdict']}`",
            "",
            "## Working Rule",
            "",
            f"- final verdict: `{summary['verdict']}`",
            "",
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ladder = _load_json(LADDER_JSON)
    recommendation = _load_json(RECOMMENDATION_JSON)
    followup_contract = _load_json(FOLLOWUP_CONTRACT_JSON)
    challenger_closure = _load_json(CHALLENGER_CLOSURE_JSON)

    representative_row = next(row for row in ladder["rows"] if row["role"] == "balance")
    growth_row = next(row for row in ladder["rows"] if row["role"] == "growth")
    drawdown_row = next(row for row in ladder["rows"] if row["role"] == "drawdown")

    summary = {
        "recommended_variant": str(recommendation["recommended_variant"]),
        "recommendation_reason": str(recommendation["recommendation_reason"]),
        "recommended_cagr": float(representative_row["cagr"]),
        "recommended_cagr_display": _pct(float(representative_row["cagr"])),
        "recommended_mdd": float(representative_row["mdd"]),
        "recommended_mdd_display": _pct(float(representative_row["mdd"])),
        "growth_boundary_variant": str(followup_contract["growth_boundary_variant"]),
        "growth_boundary_cagr": float(growth_row["cagr"]),
        "growth_boundary_cagr_display": _pct(float(growth_row["cagr"])),
        "growth_boundary_mdd": float(growth_row["mdd"]),
        "growth_boundary_mdd_display": _pct(float(growth_row["mdd"])),
        "drawdown_boundary_variant": str(followup_contract["drawdown_boundary_variant"]),
        "drawdown_boundary_cagr": float(drawdown_row["cagr"]),
        "drawdown_boundary_cagr_display": _pct(float(drawdown_row["cagr"])),
        "drawdown_boundary_mdd": float(drawdown_row["mdd"]),
        "drawdown_boundary_mdd_display": _pct(float(drawdown_row["mdd"])),
        "quality_reference_variant": str(followup_contract["quality_reference_variant"]),
        "challenger_family_count": int(challenger_closure["challenger_family_count"]),
        "representative_replacements_found": int(challenger_closure["representative_replacements_found"]),
        "challenger_closure_verdict": str(challenger_closure["verdict"]),
        "verdict": (
            f"keep `{recommendation['recommended_variant']}` as the official representative. "
            f"Use `{followup_contract['growth_boundary_variant']}` as the growth boundary, "
            f"`{followup_contract['drawdown_boundary_variant']}` as the drawdown boundary, and "
            f"`{followup_contract['quality_reference_variant']}` only as the same-drawdown quality reference."
        ),
    }

    (OUTPUT_DIR / "representative_decision_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "representative_decision.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
