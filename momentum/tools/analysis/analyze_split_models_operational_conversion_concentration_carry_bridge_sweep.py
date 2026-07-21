from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models.backtest import BacktestConfig, _baseline_variant_map, _run_trading_backtest_variant
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_carry_sweep import (
    _run_with_baseline_switch_carry,
)
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_sweep import (
    BASELINE_VARIANT,
    BASE_VARIANT,
    STRONGEST_VARIANT,
)
from tools.analysis.analyze_split_models_operational_conversion_concentration_trigger_sweep import (
    _patch_concentration_trigger,
)
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import (
    _patch_tail_release_custom,
    _pct,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    _build_context,
    _summarize_candidate,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_concentration_carry_bridge_sweep"
MDD_TOL = 1e-9
CONCENTRATION_THRESHOLD = 0.60


def _compose_variant_name(trim_fraction: float, threshold_gap: float, carry_count: int) -> str:
    return (
        f"{BASE_VARIANT}_conccarry_ct{int(round(CONCENTRATION_THRESHOLD * 100)):02d}"
        f"_trim{int(round(trim_fraction * 100)):02d}"
        f"_gap{int(round(threshold_gap * 100)):02d}"
        f"_top{carry_count}"
    )


def _compose_patch(trim_fraction: float):
    base_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    concentration_patch = _patch_concentration_trigger(CONCENTRATION_THRESHOLD, trim_fraction)

    def patch(book: pd.DataFrame) -> pd.DataFrame:
        return concentration_patch(base_patch(book))

    return patch


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Concentration Carry Bridge Sweep",
        "",
        "## Purpose",
        "",
        "- bridge the first real drawdown improver with the current best same-drawdown quality overlay",
        "- start from the concentration trigger and add the baseline-switch carry overlay only in weak-flow months",
        "",
        "## Current Read",
        "",
        f"- base point: `{summary['base_variant']}`",
        f"- best bridge point: `{summary['best_variant']}`",
        f"- best bridge MDD: `{_pct(summary['best_mdd'])}`",
        f"- best bridge CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Trim | Gap | Carry | Switch Count | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | {_pct(row['TrimFraction'])} | {_pct(row['ThresholdGap'])} | "
            f"{int(row['CarryCount'])} | {int(row['SwitchCount'])} | {_pct(row['CAGR'])} | {_pct(row['MDD'])} | "
            f"{row['Sharpe']:.4f} | {int(row['NegativeCAGRWindows'])} |"
        )
    lines.extend(["", "## Verdict", "", f"- {summary['verdict']}", ""])
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    variants = _baseline_variant_map()
    baseline = variants[BASELINE_VARIANT]
    strongest = variants[STRONGEST_VARIANT]

    strongest_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, strongest
    )

    base_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    base_variant = replace(strongest, name=BASE_VARIANT)
    base_result, _ = _run_with_baseline_switch_carry(
        variant=base_variant,
        fallback_variant=baseline,
        redistribution_patch=base_patch,
        threshold_gap=999.0,
        carry_count=0,
        universe=universe,
        price_cache=price_cache,
        flow_cache=flow_cache,
        monthly_close=monthly_close,
        signal_dates=signal_dates,
        cfg=cfg,
    )
    base_summary = _summarize_candidate(BASE_VARIANT, base_result, strongest_result)
    base_summary["TrimFraction"] = 0.0
    base_summary["ThresholdGap"] = None
    base_summary["CarryCount"] = 0
    base_summary["SwitchCount"] = 0

    rows: list[dict[str, object]] = [base_summary]
    grid = [
        (0.10, 0.00, 2),
        (0.10, 0.02, 2),
        (0.12, 0.00, 2),
        (0.12, 0.02, 2),
        (0.14, 0.00, 2),
        (0.14, 0.02, 2),
        (0.16, 0.00, 2),
        (0.16, 0.02, 2),
        (0.18, 0.00, 2),
        (0.18, 0.02, 2),
        (0.20, 0.00, 2),
        (0.20, 0.02, 2),
    ]

    for trim_fraction, threshold_gap, carry_count in grid:
        variant_name = _compose_variant_name(trim_fraction, threshold_gap, carry_count)
        variant = replace(strongest, name=variant_name)
        result, switch_count = _run_with_baseline_switch_carry(
            variant=variant,
            fallback_variant=baseline,
            redistribution_patch=_compose_patch(trim_fraction),
            threshold_gap=threshold_gap,
            carry_count=carry_count,
            universe=universe,
            price_cache=price_cache,
            flow_cache=flow_cache,
            monthly_close=monthly_close,
            signal_dates=signal_dates,
            cfg=cfg,
        )
        summary = _summarize_candidate(variant_name, result, strongest_result)
        summary["TrimFraction"] = trim_fraction
        summary["ThresholdGap"] = threshold_gap
        summary["CarryCount"] = carry_count
        summary["SwitchCount"] = switch_count
        rows.append(summary)

    compare = pd.DataFrame(rows)
    compare["MDDBucket"] = compare["MDD"].round(9)
    compare = compare.sort_values(
        ["NegativeCAGRWindows", "MDDBucket", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "concentration_carry_bridge_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_VARIANT,
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_trim_fraction": float(best["TrimFraction"]),
        "best_threshold_gap": None if pd.isna(best["ThresholdGap"]) else float(best["ThresholdGap"]),
        "best_carry_count": int(best["CarryCount"]),
        "best_switch_count": int(best["SwitchCount"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if best["MDD"] > base_summary["MDD"] + MDD_TOL:
        summary["verdict"] = (
            f"the concentration-carry bridge improves drawdown: `{summary['best_variant']}` lifts MDD to "
            f"{_pct(summary['best_mdd'])} with CAGR {_pct(summary['best_cagr'])}."
        )
    elif abs(best["MDD"] - base_summary["MDD"]) <= MDD_TOL and (
        best["CAGR"] > base_summary["CAGR"] + 1e-12 or best["Sharpe"] > base_summary["Sharpe"] + 1e-12
    ):
        summary["verdict"] = (
            f"the concentration-carry bridge improves quality but not drawdown. `{summary['best_variant']}` keeps "
            f"MDD flat at {_pct(summary['best_mdd'])} while moving CAGR to {_pct(summary['best_cagr'])}."
        )
    else:
        summary["verdict"] = (
            f"the concentration-carry bridge fails: no bridge point improves drawdown or quality versus `{BASE_VARIANT}`."
        )

    (OUTPUT_DIR / "concentration_carry_bridge_sweep_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "concentration_carry_bridge_sweep_review.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
