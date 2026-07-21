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
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_concentration_carry_kr_etf_carry_sweep"
FOLLOWUP_CONTRACT_JSON = (
    ROOT / "output" / "split_models_operational_conversion_followup_contract" / "followup_contract_summary.json"
)
MDD_TOL = 1e-9
CONCENTRATION_THRESHOLD = 0.70
TRIM_FRACTION = 0.21
TARGET_SECTORS = {"Information Technology", "Energy"}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _compose_variant_name(threshold_gap: float, carry_count: int) -> str:
    return (
        f"{BASE_VARIANT}_conccarrykretfcarry_ct{int(round(CONCENTRATION_THRESHOLD * 100)):02d}"
        f"_trim{int(round(TRIM_FRACTION * 100)):02d}"
        f"_gap{int(round(threshold_gap * 100)):02d}"
        f"_top{carry_count}"
    )


def _patch_concentration_trigger_kr_etf_only():
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
            delta = current * TRIM_FRACTION
            out.loc[idx, "TargetWeight"] = current - delta
            released += delta
        if released <= 0:
            return out

        recipient_mask = (
            out["Market"].astype(str).eq("KR")
            & out["Sector"].astype(str).eq("ETF")
            & ~out.index.isin(top2.index)
        )
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


def _compose_patch():
    base_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    concentration_patch = _patch_concentration_trigger_kr_etf_only()

    def patch(book: pd.DataFrame) -> pd.DataFrame:
        return concentration_patch(base_patch(book))

    return patch


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Concentration Carry KR ETF Carry Sweep",
        "",
        "## Purpose",
        "",
        "- keep the current representative trim21 KR ETF-only structure fixed",
        "- test whether changing weak-flow carry count can beat the current representative benchmark",
        "",
        "## Current Read",
        "",
        f"- base point: `{summary['base_variant']}`",
        f"- best carry point: `{summary['best_variant']}`",
        f"- best carry MDD: `{_pct(summary['best_mdd'])}`",
        f"- best carry CAGR: `{_pct(summary['best_cagr'])}`",
        f"- representative benchmark: `{summary['representative_variant']}`",
        f"- representative CAGR / MDD: `{_pct(summary['representative_cagr'])}` / `{_pct(summary['representative_mdd'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Gap | Carry | Switch Count | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | {_pct(row['ThresholdGap'])} | {int(row['CarryCount'])} | "
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
    followup_contract = _load_json(FOLLOWUP_CONTRACT_JSON)
    representative_variant = str(followup_contract["representative_variant"])
    representative_cagr = float(followup_contract["representative_cagr"])
    representative_mdd = float(followup_contract["representative_mdd"])

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
    base_summary["CarryCount"] = 0
    base_summary["ThresholdGap"] = None
    base_summary["SwitchCount"] = 0

    rows: list[dict[str, object]] = [base_summary]
    grid = [
        (0.00, 1),
        (0.00, 2),
        (0.00, 3),
        (0.02, 1),
        (0.02, 2),
        (0.02, 3),
    ]

    for threshold_gap, carry_count in grid:
        variant_name = _compose_variant_name(threshold_gap, carry_count)
        variant = replace(strongest, name=variant_name)
        result, switch_count = _run_with_baseline_switch_carry(
            variant=variant,
            fallback_variant=baseline,
            redistribution_patch=_compose_patch(),
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
        summary["CarryCount"] = carry_count
        summary["ThresholdGap"] = threshold_gap
        summary["SwitchCount"] = switch_count
        rows.append(summary)

    compare = pd.DataFrame(rows)
    compare["MDDBucket"] = compare["MDD"].round(9)
    compare = compare.sort_values(
        ["NegativeCAGRWindows", "MDDBucket", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(
        OUTPUT_DIR / "concentration_carry_kr_etf_carry_sweep_compare.csv",
        index=False,
        encoding="utf-8-sig",
    )

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_VARIANT,
        "representative_variant": representative_variant,
        "representative_cagr": representative_cagr,
        "representative_mdd": representative_mdd,
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_carry_count": int(best["CarryCount"]),
        "best_threshold_gap": None if pd.isna(best["ThresholdGap"]) else float(best["ThresholdGap"]),
        "best_switch_count": int(best["SwitchCount"]),
        "beats_representative_on_mdd": bool(best["MDD"] > representative_mdd + MDD_TOL),
        "beats_representative_on_cagr": bool(best["CAGR"] > representative_cagr + 1e-12),
        "matches_representative": bool(
            abs(float(best["MDD"]) - representative_mdd) <= MDD_TOL
            and abs(float(best["CAGR"]) - representative_cagr) <= 1e-12
        ),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if summary["matches_representative"]:
        summary["verdict"] = (
            f"the KR ETF carry sweep does not produce a new representative challenger. "
            f"`{summary['best_variant']}` matches the current representative at "
            f"CAGR {_pct(summary['best_cagr'])} and MDD {_pct(summary['best_mdd'])}."
        )
    elif (
        best["MDD"] > representative_mdd + MDD_TOL
        or best["CAGR"] > representative_cagr + 1e-12
    ):
        summary["verdict"] = (
            f"the KR ETF carry sweep finds a representative challenger. `{summary['best_variant']}` "
            f"moves to CAGR {_pct(summary['best_cagr'])} and MDD {_pct(summary['best_mdd'])} versus representative "
            f"{_pct(representative_cagr)} / {_pct(representative_mdd)}."
        )
    elif best["MDD"] > base_summary["MDD"] + MDD_TOL:
        summary["verdict"] = (
            f"the KR ETF carry sweep improves drawdown: `{summary['best_variant']}` lifts MDD to "
            f"{_pct(summary['best_mdd'])} with CAGR {_pct(summary['best_cagr'])}."
        )
    elif abs(best["MDD"] - base_summary["MDD"]) <= MDD_TOL and (
        best["CAGR"] > base_summary["CAGR"] + 1e-12 or best["Sharpe"] > base_summary["Sharpe"] + 1e-12
    ):
        summary["verdict"] = (
            f"the KR ETF carry sweep improves quality but not drawdown. `{summary['best_variant']}` keeps "
            f"MDD flat at {_pct(summary['best_mdd'])} while moving CAGR to {_pct(summary['best_cagr'])}."
        )
    else:
        summary["verdict"] = (
            f"the KR ETF carry sweep fails: no carry point improves drawdown or quality versus `{BASE_VARIANT}`."
        )

    (OUTPUT_DIR / "concentration_carry_kr_etf_carry_sweep_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "concentration_carry_kr_etf_carry_sweep_review.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
