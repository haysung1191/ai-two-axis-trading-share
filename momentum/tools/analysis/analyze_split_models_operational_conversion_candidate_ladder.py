from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_candidate_ladder"
MICRO_SUMMARY_JSON = (
    ROOT / "output" / "split_models_operational_conversion_concentration_carry_kr_etf_trim_micro"
    / "concentration_carry_kr_etf_trim_micro_summary.json"
)
WINDOW_DEFENSE_SUMMARY_JSON = (
    ROOT / "output" / "split_models_operational_conversion_drawdown_window_defense_sweep"
    / "drawdown_window_defense_sweep_summary.json"
)
BASE_CAGR = 0.7479958086653411
BASE_MDD = -0.3383321870730238
BASELINE_MDD = -0.2524158832009178


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pick(summary: dict, trim_fraction: float) -> dict:
    for row in summary["ranked_rows"]:
        if abs(float(row["TrimFraction"]) - trim_fraction) <= 1e-12:
            return row
    raise KeyError(f"trim {trim_fraction} not found")


def _row_payload(role: str, row: dict) -> dict[str, object]:
    cagr = float(row["CAGR"])
    mdd = float(row["MDD"])
    sharpe = float(row["Sharpe"])
    return {
        "role": role,
        "variant": str(row["Variant"]),
        "trim_fraction": float(row["TrimFraction"]),
        "cagr": cagr,
        "mdd": mdd,
        "sharpe": sharpe,
        "cagr_delta_vs_base": cagr - BASE_CAGR,
        "mdd_delta_vs_base": mdd - BASE_MDD,
        "gap_vs_operating_baseline_mdd": mdd - BASELINE_MDD,
    }


def _summary_row_payload(role: str, summary: dict) -> dict[str, object]:
    cagr = float(summary["best_cagr"])
    mdd = float(summary["best_mdd"])
    sharpe = float(summary["best_sharpe"])
    return {
        "role": role,
        "variant": str(summary["best_variant"]),
        "trim_fraction": None,
        "cagr": cagr,
        "mdd": mdd,
        "sharpe": sharpe,
        "cagr_delta_vs_base": cagr - BASE_CAGR,
        "mdd_delta_vs_base": mdd - BASE_MDD,
        "gap_vs_operating_baseline_mdd": mdd - BASELINE_MDD,
    }


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Candidate Ladder",
        "",
        "## Purpose",
        "",
        "- lock the current representative drawdown-repair points into a simple ladder",
        "- separate the growth-first, balance, and drawdown-first candidates so the next thread does not have to rediscover them",
        "",
        "## Candidate Ladder",
        "",
        "| Role | Variant | Trim | CAGR | MDD | Sharpe | MDD delta vs base | Gap vs operating baseline |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["rows"]:
        trim_display = "n/a" if row["trim_fraction"] is None else _pct(row["trim_fraction"])
        lines.append(
            f"| `{row['role']}` | `{row['variant']}` | {trim_display} | {_pct(row['cagr'])} | "
            f"{_pct(row['mdd'])} | {row['sharpe']:.4f} | {_pct(row['mdd_delta_vs_base'])} | {_pct(row['gap_vs_operating_baseline_mdd'])} |"
        )
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            f"- official growth-preserving candidate: `{summary['growth_variant']}`",
            f"- official balance candidate: `{summary['balance_variant']}`",
            f"- official drawdown-first candidate: `{summary['drawdown_variant']}`",
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

    micro = _load_json(MICRO_SUMMARY_JSON)
    window_defense = _load_json(WINDOW_DEFENSE_SUMMARY_JSON)
    trim20 = _row_payload("growth", _pick(micro, 0.20))
    trim21 = _row_payload("balance", _pick(micro, 0.21))
    trim22 = _row_payload("drawdown", _pick(micro, 0.22))
    window_defense_row = _summary_row_payload("drawdown_window_defense", window_defense)
    rows = [trim20, trim21, trim22, window_defense_row]

    summary = {
        "base_variant": micro["base_variant"],
        "growth_variant": trim20["variant"],
        "balance_variant": trim21["variant"],
        "drawdown_variant": trim22["variant"],
        "drawdown_window_defense_variant": window_defense_row["variant"],
        "rows": rows,
        "verdict": (
            f"`trim20` is the best growth-preserving drawdown improver, `trim21` is the cleanest balance point, "
            f"`trim22` is the best general drawdown point, and the drawdown-window defense is the closest operating-MDD "
            f"candidate. The best remaining operating-baseline MDD gap is "
            f"{_pct(max(row['gap_vs_operating_baseline_mdd'] for row in rows))}."
        ),
    }

    (OUTPUT_DIR / "candidate_ladder_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "candidate_ladder.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
