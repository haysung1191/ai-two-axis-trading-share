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
from tools.analysis.analyze_split_models_operational_conversion_concentration_carry_kr_etf_trim_micro import (
    _compose_patch as _compose_representative_patch,
)
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import _pct
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    _build_context,
    _summarize_candidate,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_mu_guard_sweep"
PROMOTION_RECOMMENDATION_JSON = (
    ROOT / "output" / "split_models_operational_conversion_promotion_recommendation" / "promotion_recommendation_summary.json"
)
MDD_TOL = 1e-9
MATERIAL_MDD_IMPROVEMENT = 5e-4
MATERIAL_CAGR_IMPROVEMENT = 5e-4
REPRESENTATIVE_TRIM_FRACTION = 0.21
MU_SYMBOL = "MU"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _compose_variant_name(mu_weight_trigger: float, mu_trim_fraction: float) -> str:
    return (
        f"{BASE_VARIANT}_muguard"
        f"_mw{int(round(mu_weight_trigger * 100)):02d}"
        f"_trim{int(round(mu_trim_fraction * 100)):02d}"
        "_gap02_top2"
    )


def _apply_mu_guard_to_book(book: pd.DataFrame, mu_weight_trigger: float, mu_trim_fraction: float) -> pd.DataFrame:
    if book.empty:
        return book

    out = book.copy()
    out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
    mu_mask = (
        out["Symbol"].astype(str).eq(MU_SYMBOL)
        & out["Market"].astype(str).eq("US")
        & out["Sector"].astype(str).eq("Information Technology")
    )
    if not mu_mask.any():
        return out

    mu_index = out.index[mu_mask][0]
    mu_weight = float(out.loc[mu_index, "TargetWeight"])
    if mu_weight < mu_weight_trigger:
        return out

    released = mu_weight * mu_trim_fraction
    if released <= 0:
        return out

    out.loc[mu_index, "TargetWeight"] = mu_weight - released

    recipient_mask = (
        out["Market"].astype(str).eq("KR")
        & out["Sector"].astype(str).eq("ETF")
        & ~out.index.isin([mu_index])
    )
    recipients = out.loc[recipient_mask].copy()
    if recipients.empty:
        total_after = float(out["TargetWeight"].sum())
        if total_after > 0:
            out["TargetWeight"] = out["TargetWeight"] / total_after
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


def _patch_mu_guard(mu_weight_trigger: float, mu_trim_fraction: float):
    representative_patch = _compose_representative_patch(REPRESENTATIVE_TRIM_FRACTION)

    def patch(book: pd.DataFrame) -> pd.DataFrame:
        return _apply_mu_guard_to_book(representative_patch(book), mu_weight_trigger, mu_trim_fraction)

    return patch


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion MU Guard Sweep",
        "",
        "## Purpose",
        "",
        "- test whether the current representative can recover more drawdown by adding a narrow MU-specific guard",
        "- only fire after the representative carry/trim logic has already activated",
        "",
        "## Current Read",
        "",
        f"- representative variant: `{summary['representative_variant']}`",
        f"- best MU-guard point: `{summary['best_variant']}`",
        f"- representative MDD: `{_pct(summary['representative_mdd'])}`",
        f"- best MU-guard MDD: `{_pct(summary['best_mdd'])}`",
        f"- representative CAGR: `{_pct(summary['representative_cagr'])}`",
        f"- best MU-guard CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | MU Trigger | MU Trim | Switch Count | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | {_pct(row['MuWeightTrigger'])} | {_pct(row['MuTrimFraction'])} | "
            f"{int(row['SwitchCount'])} | {_pct(row['CAGR'])} | {_pct(row['MDD'])} | {row['Sharpe']:.4f} | "
            f"{int(row['NegativeCAGRWindows'])} |"
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

    recommendation = _load_json(PROMOTION_RECOMMENDATION_JSON)
    representative_variant = str(recommendation["recommended_variant"])

    representative_variant_obj = replace(strongest, name=representative_variant)
    representative_result, representative_switch_count = _run_with_baseline_switch_carry(
        variant=representative_variant_obj,
        fallback_variant=baseline,
        redistribution_patch=_compose_representative_patch(REPRESENTATIVE_TRIM_FRACTION),
        threshold_gap=0.02,
        carry_count=2,
        universe=universe,
        price_cache=price_cache,
        flow_cache=flow_cache,
        monthly_close=monthly_close,
        signal_dates=signal_dates,
        cfg=cfg,
    )
    representative_summary = _summarize_candidate(representative_variant, representative_result, strongest_result)
    representative_summary["MuWeightTrigger"] = 0.0
    representative_summary["MuTrimFraction"] = 0.0
    representative_summary["SwitchCount"] = representative_switch_count
    representative_cagr = float(representative_summary["CAGR"])
    representative_mdd = float(representative_summary["MDD"])

    rows: list[dict[str, object]] = [representative_summary]
    for mu_weight_trigger, mu_trim_fraction in [
        (0.10, 0.10),
        (0.10, 0.15),
        (0.11, 0.10),
        (0.11, 0.15),
        (0.12, 0.10),
        (0.12, 0.15),
    ]:
        variant_name = _compose_variant_name(mu_weight_trigger, mu_trim_fraction)
        variant = replace(strongest, name=variant_name)
        result, switch_count = _run_with_baseline_switch_carry(
            variant=variant,
            fallback_variant=baseline,
            redistribution_patch=_patch_mu_guard(mu_weight_trigger, mu_trim_fraction),
            threshold_gap=0.02,
            carry_count=2,
            universe=universe,
            price_cache=price_cache,
            flow_cache=flow_cache,
            monthly_close=monthly_close,
            signal_dates=signal_dates,
            cfg=cfg,
        )
        summary = _summarize_candidate(variant_name, result, strongest_result)
        summary["MuWeightTrigger"] = mu_weight_trigger
        summary["MuTrimFraction"] = mu_trim_fraction
        summary["SwitchCount"] = switch_count
        rows.append(summary)

    compare = pd.DataFrame(rows)
    compare["MDDBucket"] = compare["MDD"].round(9)
    compare = compare.sort_values(
        ["NegativeCAGRWindows", "MDDBucket", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "mu_guard_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "representative_variant": representative_variant,
        "representative_cagr": representative_cagr,
        "representative_mdd": representative_mdd,
        "published_representative_cagr": float(
            next(row["cagr"] for row in recommendation["rows"] if row["variant"] == representative_variant)
        ),
        "published_representative_mdd": float(
            next(row["mdd"] for row in recommendation["rows"] if row["variant"] == representative_variant)
        ),
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_mu_weight_trigger": float(best["MuWeightTrigger"]),
        "best_mu_trim_fraction": float(best["MuTrimFraction"]),
        "best_switch_count": int(best["SwitchCount"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    mdd_improvement = float(best["MDD"]) - representative_mdd
    cagr_improvement = float(best["CAGR"]) - representative_cagr
    if mdd_improvement > MATERIAL_MDD_IMPROVEMENT:
        summary["verdict"] = (
            f"the MU guard opens a better drawdown point: `{summary['best_variant']}` improves MDD to "
            f"{_pct(summary['best_mdd'])} while keeping CAGR at {_pct(summary['best_cagr'])}."
        )
    elif (
        abs(mdd_improvement) <= MATERIAL_MDD_IMPROVEMENT
        and cagr_improvement >= -MATERIAL_CAGR_IMPROVEMENT
        and (
            cagr_improvement > MATERIAL_CAGR_IMPROVEMENT
            or float(best["Sharpe"]) > float(representative_summary["Sharpe"]) + MATERIAL_CAGR_IMPROVEMENT
        )
    ):
        summary["verdict"] = (
            f"the MU guard does not improve drawdown, but `{summary['best_variant']}` improves quality at the same "
            f"MDD bucket with CAGR {_pct(summary['best_cagr'])}."
        )
    else:
        summary["verdict"] = (
            f"the MU guard remains blocked: no narrow MU-specific point improves on `{representative_variant}`."
        )

    (OUTPUT_DIR / "mu_guard_sweep_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "mu_guard_sweep_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
