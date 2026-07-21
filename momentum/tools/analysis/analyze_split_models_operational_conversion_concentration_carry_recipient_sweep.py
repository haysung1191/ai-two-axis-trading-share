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
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_concentration_carry_recipient_sweep"
MDD_TOL = 1e-9
CONCENTRATION_THRESHOLD = 0.70
TRIM_FRACTION = 0.20
THRESHOLD_GAP = 0.02
CARRY_COUNT = 2
TARGET_SECTORS = {"Information Technology", "Energy"}
DEFENSIVE_US_SECTORS = {"Health Care", "Utilities", "Consumer Staples", "Financials"}


def _compose_variant_name(recipient_mode: str) -> str:
    return (
        f"{BASE_VARIANT}_conccarryrec_ct{int(round(CONCENTRATION_THRESHOLD * 100)):02d}"
        f"_trim{int(round(TRIM_FRACTION * 100)):02d}"
        f"_gap{int(round(THRESHOLD_GAP * 100)):02d}"
        f"_top{CARRY_COUNT}_{recipient_mode}"
    )


def _patch_concentration_trigger_with_recipient(recipient_mode: str):
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
        top2_weight = float(top2["TargetWeight"].sum())
        if top2_weight < CONCENTRATION_THRESHOLD:
            return out

        sector_weights = (
            out.loc[out["Market"].astype(str).eq("US") & out["Sector"].astype(str).isin(TARGET_SECTORS)]
            .groupby("Sector", as_index=False)["TargetWeight"]
            .sum()
        )
        if sector_weights.empty:
            return out
        dominant_sector_weight = float(sector_weights["TargetWeight"].max())
        if dominant_sector_weight < CONCENTRATION_THRESHOLD:
            return out

        released = 0.0
        for idx in top2.index:
            current = float(out.loc[idx, "TargetWeight"])
            delta = current * TRIM_FRACTION
            out.loc[idx, "TargetWeight"] = current - delta
            released += delta
        if released <= 0:
            return out

        market = out["Market"].astype(str)
        sector = out["Sector"].astype(str)
        kr_etf_mask = market.eq("KR") & sector.eq("ETF")
        non_target_mask = ~sector.isin(TARGET_SECTORS)
        defensive_us_mask = market.eq("US") & sector.isin(DEFENSIVE_US_SECTORS)
        recipient_map = {
            "mixed": (kr_etf_mask | non_target_mask),
            "kr_etf_only": kr_etf_mask,
            "ex_target_only": non_target_mask,
            "all_ex_top2": pd.Series(True, index=out.index),
            "kr_etf_plus_defensive": (kr_etf_mask | defensive_us_mask),
        }
        recipient_mask = recipient_map[recipient_mode] & ~out.index.isin(top2.index)
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


def _compose_patch(recipient_mode: str):
    base_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    concentration_patch = _patch_concentration_trigger_with_recipient(recipient_mode)

    def patch(book: pd.DataFrame) -> pd.DataFrame:
        return concentration_patch(base_patch(book))

    return patch


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Concentration Carry Recipient Sweep",
        "",
        "## Purpose",
        "",
        "- keep the best concentration-carry trigger fixed",
        "- test whether changing release recipients can preserve the drawdown gain while recovering more CAGR",
        "",
        "## Current Read",
        "",
        f"- base point: `{summary['base_variant']}`",
        f"- best recipient point: `{summary['best_variant']}`",
        f"- best recipient MDD: `{_pct(summary['best_mdd'])}`",
        f"- best recipient CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Recipient Mode | Switch Count | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | `{row['RecipientMode']}` | {int(row['SwitchCount'])} | "
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
    base_summary["RecipientMode"] = "base"
    base_summary["SwitchCount"] = 0

    rows: list[dict[str, object]] = [base_summary]
    recipient_modes = [
        "mixed",
        "kr_etf_only",
        "ex_target_only",
        "all_ex_top2",
        "kr_etf_plus_defensive",
    ]
    for recipient_mode in recipient_modes:
        variant_name = _compose_variant_name(recipient_mode)
        variant = replace(strongest, name=variant_name)
        result, switch_count = _run_with_baseline_switch_carry(
            variant=variant,
            fallback_variant=baseline,
            redistribution_patch=_compose_patch(recipient_mode),
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
        summary["RecipientMode"] = recipient_mode
        summary["SwitchCount"] = switch_count
        rows.append(summary)

    compare = pd.DataFrame(rows)
    compare["MDDBucket"] = compare["MDD"].round(9)
    compare = compare.sort_values(
        ["NegativeCAGRWindows", "MDDBucket", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "concentration_carry_recipient_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_VARIANT,
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_recipient_mode": str(best["RecipientMode"]),
        "best_switch_count": int(best["SwitchCount"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if best["MDD"] > base_summary["MDD"] + MDD_TOL:
        summary["verdict"] = (
            f"the recipient axis improves drawdown: `{summary['best_variant']}` lifts MDD to "
            f"{_pct(summary['best_mdd'])} with CAGR {_pct(summary['best_cagr'])}."
        )
    elif abs(best["MDD"] - base_summary["MDD"]) <= MDD_TOL and (
        best["CAGR"] > base_summary["CAGR"] + 1e-12 or best["Sharpe"] > base_summary["Sharpe"] + 1e-12
    ):
        summary["verdict"] = (
            f"the recipient axis improves quality but not drawdown. `{summary['best_variant']}` keeps "
            f"MDD flat at {_pct(summary['best_mdd'])} while moving CAGR to {_pct(summary['best_cagr'])}."
        )
    else:
        summary["verdict"] = (
            f"the recipient axis fails: no recipient mode improves drawdown or quality versus `{BASE_VARIANT}`."
        )

    (OUTPUT_DIR / "concentration_carry_recipient_sweep_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "concentration_carry_recipient_sweep_review.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
