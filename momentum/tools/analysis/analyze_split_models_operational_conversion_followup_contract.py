from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_followup_contract"
CANDIDATE_LADDER_JSON = (
    ROOT / "output" / "split_models_operational_conversion_candidate_ladder" / "candidate_ladder_summary.json"
)
PROMOTION_RECOMMENDATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_promotion_recommendation"
    / "promotion_recommendation_summary.json"
)
GUARDRAIL_MATRIX_JSON = (
    ROOT / "output" / "split_models_operational_conversion_guardrail_matrix" / "guardrail_matrix_summary.json"
)


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _row_by_role(summary: dict, role: str) -> dict:
    for row in summary["rows"]:
        if row["role"] == role:
            return row
    raise KeyError(role)


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Follow-up Contract",
        "",
        "## Purpose",
        "",
        "- lock the official comparison set for the next operational-conversion experiments",
        "- stop future threads from re-deciding which trim point or overlay is the active benchmark",
        "",
        "## Fixed Comparison Set",
        "",
        f"- representative candidate: `{summary['representative_variant']}`",
        f"- growth boundary: `{summary['growth_boundary_variant']}`",
        f"- drawdown boundary: `{summary['drawdown_boundary_variant']}`",
        f"- same-drawdown quality reference: `{summary['quality_reference_variant']}`",
        "",
        "## Follow-up Rules",
        "",
    ]
    for item in summary["followup_rules"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Current Numbers",
            "",
            f"- representative CAGR / MDD: `{_pct(summary['representative_cagr'])}` / `{_pct(summary['representative_mdd'])}`",
            f"- growth boundary CAGR / MDD: `{_pct(summary['growth_boundary_cagr'])}` / `{_pct(summary['growth_boundary_mdd'])}`",
            f"- drawdown boundary CAGR / MDD: `{_pct(summary['drawdown_boundary_cagr'])}` / `{_pct(summary['drawdown_boundary_mdd'])}`",
            f"- quality reference CAGR / MDD: `{_pct(summary['quality_reference_cagr'])}` / `{_pct(summary['quality_reference_mdd'])}`",
            "",
            "## Verdict",
            "",
            f"- {summary['verdict']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ladder = _load_json(CANDIDATE_LADDER_JSON)
    recommendation = _load_json(PROMOTION_RECOMMENDATION_JSON)
    matrix = _load_json(GUARDRAIL_MATRIX_JSON)

    growth = _row_by_role(ladder, "growth")
    balance = _row_by_role(ladder, "balance")
    drawdown = _row_by_role(ladder, "drawdown")

    summary = {
        "representative_variant": recommendation["recommended_variant"],
        "growth_boundary_variant": growth["variant"],
        "drawdown_boundary_variant": drawdown["variant"],
        "quality_reference_variant": matrix["best_quality_variant"],
        "representative_cagr": balance["cagr"],
        "representative_mdd": balance["mdd"],
        "growth_boundary_cagr": growth["cagr"],
        "growth_boundary_mdd": growth["mdd"],
        "drawdown_boundary_cagr": drawdown["cagr"],
        "drawdown_boundary_mdd": drawdown["mdd"],
        "quality_reference_cagr": next(
            row["cagr"] for row in matrix["rows"] if row["best_variant"] == matrix["best_quality_variant"]
        ),
        "quality_reference_mdd": next(
            row["mdd"] for row in matrix["rows"] if row["best_variant"] == matrix["best_quality_variant"]
        ),
        "followup_rules": [
            (
                f"use `{recommendation['recommended_variant']}` as the default representative benchmark for any "
                "new drawdown-repair structure"
            ),
            (
                f"only call a new structure a better balance representative if it beats `{recommendation['recommended_variant']}` "
                "on MDD or CAGR without losing the other side of the tradeoff materially"
            ),
            (
                f"use `{growth['variant']}` as the growth boundary: if a new structure falls below its CAGR, "
                "it must earn that sacrifice with a cleaner drawdown repair story"
            ),
            (
                f"use `{drawdown['variant']}` as the drawdown boundary: if a new structure does not beat its MDD, "
                "it is not the new drawdown-first reference"
            ),
            (
                f"use `{matrix['best_quality_variant']}` only for same-drawdown quality overlays; do not compare it "
                "directly against drawdown-repair candidates as if it were a replacement representative"
            ),
        ],
        "verdict": (
            f"the next thread should treat `{recommendation['recommended_variant']}` as the working representative, "
            f"`{growth['variant']}` and `{drawdown['variant']}` as boundary sentinels, and "
            f"`{matrix['best_quality_variant']}` as the separate same-drawdown quality reference."
        ),
    }

    (OUTPUT_DIR / "followup_contract_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "followup_contract.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
