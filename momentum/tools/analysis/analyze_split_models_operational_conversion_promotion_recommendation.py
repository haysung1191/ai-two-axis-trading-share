from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_promotion_recommendation"
CANDIDATE_LADDER_JSON = (
    ROOT / "output" / "split_models_operational_conversion_candidate_ladder" / "candidate_ladder_summary.json"
)
TRIM_PROFILE_JSON = (
    ROOT / "output" / "split_models_operational_conversion_concentration_carry_kr_etf_trim_profile"
    / "concentration_carry_kr_etf_trim_profile_summary.json"
)
BASELINE_MDD = -0.2524158832009178


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
        "# Split Models Operational Conversion Promotion Recommendation",
        "",
        "## Purpose",
        "",
        "- choose the official representative candidate inside the current trim20 / trim21 / trim22 ladder",
        "- separate the recommended working candidate from the growth-first and drawdown-first boundary points",
        "",
        "## Recommendation",
        "",
        f"- recommended representative candidate: `{summary['recommended_variant']}`",
        f"- reason: `{summary['recommendation_reason']}`",
        f"- growth boundary: `{summary['growth_variant']}`",
        f"- drawdown boundary: `{summary['drawdown_variant']}`",
        "",
        "## Candidate Read",
        "",
        "| Role | Variant | CAGR | MDD | Sharpe | Gap vs baseline MDD |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| `{row['role']}` | `{row['variant']}` | {_pct(row['cagr'])} | {_pct(row['mdd'])} | "
            f"{row['sharpe']:.4f} | {_pct(row['gap_vs_operating_baseline_mdd'])} |"
        )
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

    ladder = _load_json(CANDIDATE_LADDER_JSON)
    profile = _load_json(TRIM_PROFILE_JSON)
    growth = _row_by_role(ladder, "growth")
    balance = _row_by_role(ladder, "balance")
    drawdown = _row_by_role(ladder, "drawdown")

    worst_months = {row["Variant"]: row for row in profile["worst_months_vs_base"]}
    worst_symbols = {row["Variant"]: row for row in profile["worst_symbols_vs_base"]}

    summary = {
        "recommended_variant": balance["variant"],
        "recommendation_reason": "balance-first representative candidate",
        "growth_variant": growth["variant"],
        "drawdown_variant": drawdown["variant"],
        "rows": [growth, balance, drawdown],
        "worst_month_vs_base": {
            "growth": worst_months["trim20"],
            "balance": worst_months["trim21"],
            "drawdown": worst_months["trim22"],
        },
        "worst_symbol_vs_base": {
            "growth": worst_symbols["trim20"],
            "balance": worst_symbols["trim21"],
            "drawdown": worst_symbols["trim22"],
        },
        "verdict": (
            f"`{balance['variant']}` is the recommended representative because it sits between the two boundary points: "
            f"it gives up only {_pct(growth['cagr'] - balance['cagr'])} CAGR versus the growth point while recovering "
            f"{_pct(balance['mdd'] - growth['mdd'])} additional drawdown, and it avoids committing all the extra MU sacrifice "
            f"required by the pure drawdown point. It remains blocked for direct promotion because its MDD is still "
            f"{_pct(balance['mdd'] - BASELINE_MDD)} worse than the operating baseline."
        ),
    }

    (OUTPUT_DIR / "promotion_recommendation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "promotion_recommendation.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
