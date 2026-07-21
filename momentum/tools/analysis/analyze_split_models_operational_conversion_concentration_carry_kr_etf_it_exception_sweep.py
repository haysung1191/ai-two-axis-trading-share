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
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import (
    _patch_tail_release_custom,
    _pct,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    _build_context,
    _summarize_candidate,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_concentration_carry_kr_etf_it_exception_sweep"
MDD_TOL = 1e-9
CONCENTRATION_THRESHOLD = 0.70
THRESHOLD_GAP = 0.02
CARRY_COUNT = 2
TARGET_SECTORS = {"Information Technology", "Energy"}
IT_SECTOR = "Information Technology"


def _compose_variant_name(trim_fraction: float, it_exception_share: float) -> str:
    return (
        f"{BASE_VARIANT}_conccarrykretfitex_ct{int(round(CONCENTRATION_THRESHOLD * 100)):02d}"
        f"_trim{int(round(trim_fraction * 100)):02d}"
        f"_gap{int(round(THRESHOLD_GAP * 100)):02d}"
        f"_top{CARRY_COUNT}"
        f"_itx{int(round(it_exception_share * 100)):02d}"
    )


def _patch_concentration_trigger_kr_etf_it_exception(trim_fraction: float, it_exception_share: float):
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 4:
            return book

        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        ranked = out.sort_values(
            ["TargetWeight", "MomentumScore", "FlowScore", "Symbol"],
            ascending=[False, False, False, True],
        )

        top2 = ranked.head(2).copy()
        if float(top2["TargetWeight"].sum()) < CONCENTRATION_THRESHOLD:
            return out

        sector_weights = (
            out.loc[out["Market"].astype(str).eq("US") & out["Sector"].astype(str).isin(TARGET_SECTORS)]
            .groupby("Sector", as_index=False)["TargetWeight"]
            .sum()
        )
        if sector_weights.empty or float(sector_weights["TargetWeight"].max()) < CONCENTRATION_THRESHOLD:
            return out

        released = 0.0
        for idx in top2.index:
            current = float(out.loc[idx, "TargetWeight"])
            delta = current * trim_fraction
            out.loc[idx, "TargetWeight"] = current - delta
            released += delta
        if released <= 0:
            return out

        market = out["Market"].astype(str)
        sector = out["Sector"].astype(str)
        kr_etf_mask = market.eq("KR") & sector.eq("ETF") & ~out.index.isin(top2.index)
        it_exception_mask = market.eq("US") & sector.eq(IT_SECTOR) & ~out.index.isin(top2.index)

        kr_etf = out.loc[kr_etf_mask].copy()
        it_exception = out.loc[it_exception_mask].copy()
        if kr_etf.empty and it_exception.empty:
            return out

        it_release = released * it_exception_share if not it_exception.empty else 0.0
        kr_release = released - it_release

        def _apply_release(slice_df: pd.DataFrame, release_amount: float) -> None:
            if slice_df.empty or release_amount <= 0:
                return
            weights = pd.to_numeric(slice_df["TargetWeight"], errors="coerce").fillna(0.0)
            total = float(weights.sum())
            if total > 0:
                out.loc[slice_df.index, "TargetWeight"] = weights + release_amount * (weights / total)
            else:
                out.loc[slice_df.index, "TargetWeight"] = weights + release_amount / float(len(slice_df))

        _apply_release(kr_etf, kr_release)
        _apply_release(it_exception, it_release)

        total_after = float(out["TargetWeight"].sum())
        if total_after > 0:
            out["TargetWeight"] = out["TargetWeight"] / total_after
        return out

    return patch


def _compose_patch(trim_fraction: float, it_exception_share: float):
    base_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    exception_patch = _patch_concentration_trigger_kr_etf_it_exception(trim_fraction, it_exception_share)

    def patch(book: pd.DataFrame) -> pd.DataFrame:
        return exception_patch(base_patch(book))

    return patch


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion KR ETF IT Exception Sweep",
        "",
        "## Purpose",
        "",
        "- keep the KR ETF recipient structure, but allow a small spill back into non-top2 US IT",
        "- test whether the MU / PLTR sacrifice can be reduced without losing too much drawdown repair",
        "",
        "## Current Read",
        "",
        f"- base point: `{summary['base_variant']}`",
        f"- best exception point: `{summary['best_variant']}`",
        f"- best exception MDD: `{_pct(summary['best_mdd'])}`",
        f"- best exception CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Trim | IT Exception | Switch Count | CAGR | MDD | Sharpe |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | {_pct(row['TrimFraction'])} | {_pct(row['ITExceptionShare'])} | "
            f"{int(row['SwitchCount'])} | {_pct(row['CAGR'])} | {_pct(row['MDD'])} | {row['Sharpe']:.4f} |"
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
    base_summary["ITExceptionShare"] = 0.0
    base_summary["SwitchCount"] = 0

    rows: list[dict[str, object]] = [base_summary]
    grid = [
        (0.20, 0.00),
        (0.20, 0.10),
        (0.20, 0.20),
        (0.21, 0.00),
        (0.21, 0.10),
        (0.21, 0.20),
        (0.22, 0.00),
        (0.22, 0.10),
        (0.22, 0.20),
    ]

    for trim_fraction, it_exception_share in grid:
        variant_name = _compose_variant_name(trim_fraction, it_exception_share)
        variant = replace(strongest, name=variant_name)
        result, switch_count = _run_with_baseline_switch_carry(
            variant=variant,
            fallback_variant=baseline,
            redistribution_patch=_compose_patch(trim_fraction, it_exception_share),
            threshold_gap=THRESHOLD_GAP,
            carry_count=CARRY_COUNT,
            universe=universe,
            price_cache=price_cache,
            flow_cache=flow_cache,
            monthly_close=monthly_close,
            signal_dates=signal_dates,
            cfg=cfg,
        )
        summary = _summarize_candidate(variant_name, result, strongest_result)
        summary["TrimFraction"] = trim_fraction
        summary["ITExceptionShare"] = it_exception_share
        summary["SwitchCount"] = switch_count
        rows.append(summary)

    compare = pd.DataFrame(rows)
    compare["MDDBucket"] = compare["MDD"].round(9)
    compare = compare.sort_values(
        ["NegativeCAGRWindows", "MDDBucket", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "concentration_carry_kr_etf_it_exception_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_VARIANT,
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_trim_fraction": float(best["TrimFraction"]),
        "best_it_exception_share": float(best["ITExceptionShare"]),
        "best_switch_count": int(best["SwitchCount"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if best["MDD"] > base_summary["MDD"] + MDD_TOL:
        summary["verdict"] = (
            f"the KR ETF IT-exception axis improves drawdown: `{summary['best_variant']}` lifts MDD to "
            f"{_pct(summary['best_mdd'])} with CAGR {_pct(summary['best_cagr'])}."
        )
    elif abs(best["MDD"] - base_summary["MDD"]) <= MDD_TOL and (
        best["CAGR"] > base_summary["CAGR"] + 1e-12 or best["Sharpe"] > base_summary["Sharpe"] + 1e-12
    ):
        summary["verdict"] = (
            f"the KR ETF IT-exception axis improves quality but not drawdown. `{summary['best_variant']}` keeps "
            f"MDD flat at {_pct(summary['best_mdd'])} while moving CAGR to {_pct(summary['best_cagr'])}."
        )
    else:
        summary["verdict"] = (
            f"the KR ETF IT-exception axis fails: no exception point improves drawdown or quality versus `{BASE_VARIANT}`."
        )

    (OUTPUT_DIR / "concentration_carry_kr_etf_it_exception_sweep_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "concentration_carry_kr_etf_it_exception_sweep_review.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
