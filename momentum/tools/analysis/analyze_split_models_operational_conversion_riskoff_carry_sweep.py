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
    BASE_VARIANT,
    STRONGEST_VARIANT,
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
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_riskoff_carry_sweep"
FALLBACK_VARIANTS = [
    "rule_breadth_it_us5_cap",
    "rule_sector_cap2_breadth_it_us5_cap",
    "rule_breadth_it_risk_off",
    "rule_sector_cap2_breadth_it_risk_off",
    "rule_breadth_max_sector_risk_off",
]


def _variant_name(fallback_name: str, threshold_gap: float, carry_count: int) -> str:
    fallback_stub = fallback_name.replace("rule_", "")
    return f"{BASE_VARIANT}_riskcarry_{fallback_stub}_gap{int(round(threshold_gap * 100)):02d}_top{carry_count}"


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Risk-Off Carry Sweep",
        "",
        "## Purpose",
        "",
        "- test a stronger fallback family than the plain operating baseline",
        "- preserve the successful carry idea, but switch into risk-off variants instead of the raw baseline book",
        "",
        "## Current Read",
        "",
        f"- base point: `{summary['base_variant']}`",
        f"- best risk-off carry point: `{summary['best_variant']}`",
        f"- best fallback family: `{summary['best_fallback_variant']}`",
        f"- best MDD: `{_pct(summary['best_mdd'])}`",
        f"- best CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Fallback | Gap | Carry | Switch Count | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | `{row['FallbackVariant']}` | {_pct(row['ThresholdGap'])} | {int(row['CarryCount'])} | {int(row['SwitchCount'])} | "
            f"{_pct(row['CAGR'])} | {_pct(row['MDD'])} | {row['Sharpe']:.4f} | {int(row['NegativeCAGRWindows'])} |"
        )
    lines.extend(["", "## Verdict", "", f"- {summary['verdict']}", ""])
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    variants = _baseline_variant_map()
    strongest = variants[STRONGEST_VARIANT]
    redistribution_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)

    strongest_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, strongest
    )

    base_result, _ = _run_with_baseline_switch_carry(
        variant=replace(strongest, name=BASE_VARIANT),
        fallback_variant=variants["rule_breadth_it_us5_cap"],
        redistribution_patch=redistribution_patch,
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
    base_summary["FallbackVariant"] = None
    base_summary["ThresholdGap"] = None
    base_summary["CarryCount"] = 0
    base_summary["SwitchCount"] = 0

    rows: list[dict[str, object]] = [base_summary]
    for fallback_name in FALLBACK_VARIANTS:
        fallback_variant = variants[fallback_name]
        for threshold_gap in (0.02, 0.04):
            carry_count = 2
            variant_name = _variant_name(fallback_name, threshold_gap, carry_count)
            result, switch_count = _run_with_baseline_switch_carry(
                variant=replace(strongest, name=variant_name),
                fallback_variant=fallback_variant,
                redistribution_patch=redistribution_patch,
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
            summary["FallbackVariant"] = fallback_name
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
    compare.to_csv(OUTPUT_DIR / "riskoff_carry_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_VARIANT,
        "best_variant": str(best["Variant"]),
        "best_fallback_variant": None if pd.isna(best["FallbackVariant"]) else str(best["FallbackVariant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_threshold_gap": None if pd.isna(best["ThresholdGap"]) else float(best["ThresholdGap"]),
        "best_switch_count": int(best["SwitchCount"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if best["MDD"] > base_summary["MDD"] + 1e-9:
        summary["verdict"] = (
            f"the risk-off carry axis improves drawdown: `{summary['best_variant']}` lifts MDD to {_pct(summary['best_mdd'])} "
            f"with CAGR {_pct(summary['best_cagr'])}."
        )
    elif abs(best["MDD"] - base_summary["MDD"]) <= 1e-9 and (
        best["CAGR"] > base_summary["CAGR"] + 1e-12 or best["Sharpe"] > base_summary["Sharpe"] + 1e-12
    ):
        summary["verdict"] = (
            f"the risk-off carry axis improves quality but not drawdown. "
            f"`{summary['best_variant']}` keeps MDD flat at {_pct(summary['best_mdd'])} while moving CAGR to {_pct(summary['best_cagr'])}."
        )
    else:
        summary["verdict"] = (
            f"the risk-off carry axis fails: no tested fallback family improves drawdown or quality versus `{BASE_VARIANT}`."
        )

    (OUTPUT_DIR / "riskoff_carry_sweep_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "riskoff_carry_sweep_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
