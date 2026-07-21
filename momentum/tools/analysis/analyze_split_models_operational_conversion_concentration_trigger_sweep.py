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
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import (
    _patch_tail_release_custom,
    _pct,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    _build_context,
    _run_with_patch,
    _summarize_candidate,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_concentration_trigger_sweep"
BASELINE_VARIANT = "rule_breadth_it_us5_cap"
STRONGEST_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
BASE_VARIANT = "tail_release_top25_mid75_pen35_floor25"
TARGET_SECTORS = {"Information Technology", "Energy"}


def _compose_variant_name(concentration_threshold: float, trim_fraction: float) -> str:
    return (
        f"{BASE_VARIANT}_conctrig_ct{int(round(concentration_threshold * 100)):02d}"
        f"_trim{int(round(trim_fraction * 100)):02d}"
    )


def _patch_concentration_trigger(concentration_threshold: float, trim_fraction: float):
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 4:
            return book
        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        ranked = out.sort_values(["TargetWeight", "MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, False, True])

        top2 = ranked.head(2).copy()
        top2_weight = float(top2["TargetWeight"].sum())
        if top2_weight < concentration_threshold:
            return out

        sector_weights = (
            out.loc[out["Market"].astype(str).eq("US") & out["Sector"].astype(str).isin(TARGET_SECTORS)]
            .groupby("Sector", as_index=False)["TargetWeight"]
            .sum()
        )
        if sector_weights.empty:
            return out
        dominant_sector_weight = float(sector_weights["TargetWeight"].max())
        if dominant_sector_weight < concentration_threshold:
            return out

        released = 0.0
        for idx in top2.index:
            current = float(out.loc[idx, "TargetWeight"])
            delta = current * trim_fraction
            out.loc[idx, "TargetWeight"] = current - delta
            released += delta

        if released <= 0:
            return out

        kr_etf_mask = out["Market"].astype(str).eq("KR") & out["Sector"].astype(str).eq("ETF")
        recipient_mask = kr_etf_mask | ~out["Sector"].astype(str).isin(TARGET_SECTORS)
        recipient_mask &= ~out.index.isin(top2.index)
        recipients = out.loc[recipient_mask].copy()
        if recipients.empty:
            return out

        recipients["TargetWeight"] = pd.to_numeric(recipients["TargetWeight"], errors="coerce").fillna(0.0)
        recipient_total = float(recipients["TargetWeight"].sum())
        if recipient_total > 0:
            out.loc[recipients.index, "TargetWeight"] = recipients["TargetWeight"] + released * (
                recipients["TargetWeight"] / recipient_total
            )
        else:
            out.loc[recipients.index, "TargetWeight"] = recipients["TargetWeight"] + released / float(len(recipients))

        total_after = float(out["TargetWeight"].sum())
        if total_after > 0:
            out["TargetWeight"] = out["TargetWeight"] / total_after
        return out

    return patch


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Concentration Trigger Sweep",
        "",
        "## Purpose",
        "",
        "- target the actual anchor drawdown window pattern directly",
        "- trim top-2 exposure only when top concentration and US IT / Energy concentration spike together",
        "",
        "## Current Read",
        "",
        f"- base point: `{summary['base_variant']}`",
        f"- best concentration-trigger point: `{summary['best_variant']}`",
        f"- best MDD: `{_pct(summary['best_mdd'])}`",
        f"- best CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Concentration Trigger | Trim | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | {_pct(row['ConcentrationThreshold'])} | {_pct(row['TrimFraction'])} | "
            f"{_pct(row['CAGR'])} | {_pct(row['MDD'])} | {row['Sharpe']:.4f} | {int(row['NegativeCAGRWindows'])} |"
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
    baseline_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, baseline
    )
    _ = _summarize_candidate(BASELINE_VARIANT, baseline_result, strongest_result)

    base_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    rows: list[dict[str, object]] = []

    base_variant = replace(strongest, name=BASE_VARIANT)
    base_result = _run_with_patch(
        base_variant,
        base_patch,
        universe,
        price_cache,
        flow_cache,
        monthly_close,
        signal_dates,
        cfg,
    )
    base_summary = _summarize_candidate(BASE_VARIANT, base_result, strongest_result)
    base_summary["ConcentrationThreshold"] = None
    base_summary["TrimFraction"] = 0.0
    rows.append(base_summary)

    for concentration_threshold, trim_fraction in [
        (0.60, 0.10),
        (0.60, 0.20),
        (0.65, 0.10),
        (0.65, 0.20),
        (0.70, 0.10),
        (0.70, 0.20),
    ]:
        variant_name = _compose_variant_name(concentration_threshold, trim_fraction)
        variant = replace(strongest, name=variant_name)
        result = _run_with_patch(
            variant,
            lambda book, bp=base_patch, cp=_patch_concentration_trigger(concentration_threshold, trim_fraction): cp(bp(book)),
            universe,
            price_cache,
            flow_cache,
            monthly_close,
            signal_dates,
            cfg,
        )
        summary = _summarize_candidate(variant_name, result, strongest_result)
        summary["ConcentrationThreshold"] = concentration_threshold
        summary["TrimFraction"] = trim_fraction
        rows.append(summary)

    compare = pd.DataFrame(rows)
    compare["MDDBucket"] = compare["MDD"].round(9)
    compare = compare.sort_values(
        ["NegativeCAGRWindows", "MDDBucket", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "concentration_trigger_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_VARIANT,
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_concentration_threshold": None if pd.isna(best["ConcentrationThreshold"]) else float(best["ConcentrationThreshold"]),
        "best_trim_fraction": float(best["TrimFraction"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if best["MDD"] > base_summary["MDD"] + 1e-9:
        summary["verdict"] = (
            f"the concentration-trigger axis improves drawdown: `{summary['best_variant']}` lifts MDD to {_pct(summary['best_mdd'])} "
            f"with CAGR {_pct(summary['best_cagr'])}."
        )
    elif abs(best["MDD"] - base_summary["MDD"]) <= 1e-9 and (
        best["CAGR"] > base_summary["CAGR"] + 1e-12 or best["Sharpe"] > base_summary["Sharpe"] + 1e-12
    ):
        summary["verdict"] = (
            f"the concentration-trigger axis improves quality but not drawdown. "
            f"`{summary['best_variant']}` keeps MDD flat at {_pct(summary['best_mdd'])} while moving CAGR to {_pct(summary['best_cagr'])}."
        )
    else:
        summary["verdict"] = (
            f"the concentration-trigger axis fails: no trigger point improves drawdown or quality versus `{BASE_VARIANT}`."
        )

    (OUTPUT_DIR / "concentration_trigger_sweep_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "concentration_trigger_sweep_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
