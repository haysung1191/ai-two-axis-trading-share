from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_representative_challenger_closure"
FOLLOWUP_CONTRACT_JSON = (
    ROOT / "output" / "split_models_operational_conversion_followup_contract" / "followup_contract_summary.json"
)
PROMOTION_RECOMMENDATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_promotion_recommendation"
    / "promotion_recommendation_summary.json"
)
SINGLE_NAME_TRIM_REFINE_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_single_name_trigger_trim_refine"
    / "single_name_trigger_trim_refine_summary.json"
)
TOP13_TRIGGER_JSON = (
    ROOT / "output" / "split_models_operational_conversion_top13_trigger_sweep" / "top13_trigger_sweep_summary.json"
)
WEAKFLOW_SECTORBIAS_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_weakflow_sectorbias_kr_etf_sweep"
    / "weakflow_sectorbias_kr_etf_sweep_summary.json"
)
BREATH_SECTOR_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_breadth_sector_kr_etf_sweep"
    / "breadth_sector_kr_etf_sweep_summary.json"
)
MOMFLOW_DIVERGENCE_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_momentum_flow_divergence_sweep"
    / "momentum_flow_divergence_sweep_summary.json"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _family_row(label: str, summary: dict) -> dict[str, object]:
    return {
        "family": label,
        "best_variant": str(summary["best_variant"]),
        "best_cagr": float(summary["best_cagr"]),
        "best_mdd": float(summary["best_mdd"]),
        "best_sharpe": float(summary["best_sharpe"]),
        "beats_representative_on_cagr": bool(summary["beats_representative_on_cagr"]),
        "beats_representative_on_mdd": bool(summary["beats_representative_on_mdd"]),
        "verdict": str(summary["verdict"]),
    }


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Representative Challenger Closure",
        "",
        "## Purpose",
        "",
        "- close the current representative challenger search",
        "- record why the recent challenger families do not replace the current representative",
        "",
        "## Active Representative",
        "",
        f"- representative: `{summary['representative_variant']}`",
        f"- representative CAGR / MDD: `{_pct(summary['representative_cagr'])}` / `{_pct(summary['representative_mdd'])}`",
        f"- growth boundary: `{summary['growth_boundary_variant']}`",
        f"- drawdown boundary: `{summary['drawdown_boundary_variant']}`",
        f"- quality reference: `{summary['quality_reference_variant']}`",
        "",
        "## Challenger Summary",
        "",
        "| Family | Best Variant | CAGR | MDD | Sharpe | Beats Rep CAGR | Beats Rep MDD |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| `{row['family']}` | `{row['best_variant']}` | {_pct(row['best_cagr'])} | "
            f"{_pct(row['best_mdd'])} | {row['best_sharpe']:.4f} | "
            f"`{row['beats_representative_on_cagr']}` | `{row['beats_representative_on_mdd']}` |"
        )

    lines.extend(
        [
            "",
            "## Closure Read",
            "",
        ]
    )
    for reason in summary["closure_reasons"]:
        lines.append(f"- {reason}")

    lines.extend(
        [
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

    contract = _load_json(FOLLOWUP_CONTRACT_JSON)
    recommendation = _load_json(PROMOTION_RECOMMENDATION_JSON)
    families = [
        _family_row("single_name_trim_refine", _load_json(SINGLE_NAME_TRIM_REFINE_JSON)),
        _family_row("top13_trigger", _load_json(TOP13_TRIGGER_JSON)),
        _family_row("breadth_sector", _load_json(BREATH_SECTOR_JSON)),
        _family_row("weakflow_sectorbias", _load_json(WEAKFLOW_SECTORBIAS_JSON)),
        _family_row("momentum_flow_divergence", _load_json(MOMFLOW_DIVERGENCE_JSON)),
    ]

    same_drawdown_overlay_count = sum(
        1 for row in families if (not row["beats_representative_on_mdd"]) and row["best_mdd"] <= contract["quality_reference_mdd"] + 1e-12
    )
    growth_boundary_collapse_count = sum(
        1
        for row in families
        if abs(row["best_cagr"] - contract["growth_boundary_cagr"]) <= 1e-12
        and abs(row["best_mdd"] - contract["growth_boundary_mdd"]) <= 1e-12
    )

    summary = {
        "representative_variant": contract["representative_variant"],
        "representative_cagr": contract["representative_cagr"],
        "representative_mdd": contract["representative_mdd"],
        "growth_boundary_variant": contract["growth_boundary_variant"],
        "growth_boundary_cagr": contract["growth_boundary_cagr"],
        "growth_boundary_mdd": contract["growth_boundary_mdd"],
        "drawdown_boundary_variant": contract["drawdown_boundary_variant"],
        "drawdown_boundary_cagr": contract["drawdown_boundary_cagr"],
        "drawdown_boundary_mdd": contract["drawdown_boundary_mdd"],
        "quality_reference_variant": contract["quality_reference_variant"],
        "quality_reference_cagr": contract["quality_reference_cagr"],
        "quality_reference_mdd": contract["quality_reference_mdd"],
        "recommended_variant": recommendation["recommended_variant"],
        "rows": families,
        "challenger_family_count": len(families),
        "representative_replacements_found": 0,
        "growth_boundary_collapses": growth_boundary_collapse_count,
        "same_drawdown_overlay_like_collapses": same_drawdown_overlay_count,
        "closure_reasons": [
            "no recent challenger family beats the representative on both drawdown and CAGR",
            "single-name trim refine stays in the growth-heavy bucket: it lifts CAGR but MDD remains worse than the representative",
            "top1-top3 and breadth-style challenger families collapse back to the existing growth boundary rather than producing a new middle point",
            "weak-flow sector-bias and momentum-flow divergence families collapse to the same-drawdown quality overlay shape rather than producing drawdown repair",
            "the current representative remains the cleanest balance point between the growth boundary and the drawdown boundary",
        ],
        "verdict": (
            f"keep `{contract['representative_variant']}` as the official representative. "
            f"The recent challenger search is closed: `{len(families)}` tested families produced zero representative replacements, "
            f"`{growth_boundary_collapse_count}` families collapsed to the growth boundary, and "
            f"`{same_drawdown_overlay_count}` families collapsed to same-drawdown overlay behavior."
        ),
    }

    (OUTPUT_DIR / "representative_challenger_closure_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "representative_challenger_closure.md").write_text(
        _build_markdown(summary),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
