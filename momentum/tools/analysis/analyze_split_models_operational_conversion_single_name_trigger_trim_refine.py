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
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_single_name_trigger_trim_refine"
FOLLOWUP_CONTRACT_JSON = (
    ROOT / "output" / "split_models_operational_conversion_followup_contract" / "followup_contract_summary.json"
)
BASE_SINGLE_NAME_JSON = (
    ROOT / "output" / "split_models_operational_conversion_single_name_trigger_sweep" / "single_name_trigger_sweep_summary.json"
)
MDD_TOL = 1e-9
TOP1_THRESHOLD = 0.16
SECTOR_CONCENTRATION_THRESHOLD = 0.70
THRESHOLD_GAP = 0.02
CARRY_COUNT = 2
TARGET_SECTORS = {"Information Technology", "Energy"}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _compose_variant_name(trim_fraction: float) -> str:
    return (
        f"{BASE_VARIANT}_singtrigref_t1{int(round(TOP1_THRESHOLD * 100)):02d}"
        f"_sct{int(round(SECTOR_CONCENTRATION_THRESHOLD * 100)):02d}"
        f"_trim{int(round(trim_fraction * 100)):02d}"
        f"_gap{int(round(THRESHOLD_GAP * 100)):02d}"
        f"_top{CARRY_COUNT}"
    )


def _patch_single_name_trigger_kr_etf_only(trim_fraction: float):
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 4:
            return book

        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        ranked = out.sort_values(
            ["TargetWeight", "MomentumScore", "FlowScore", "Symbol"],
            ascending=[False, False, False, True],
        )

        top1 = ranked.head(1).copy()
        if float(top1["TargetWeight"].sum()) < TOP1_THRESHOLD:
            return out

        sector_weights = (
            out.loc[out["Market"].astype(str).eq("US") & out["Sector"].astype(str).isin(TARGET_SECTORS)]
            .groupby("Sector", as_index=False)["TargetWeight"]
            .sum()
        )
        if sector_weights.empty or float(sector_weights["TargetWeight"].max()) < SECTOR_CONCENTRATION_THRESHOLD:
            return out

        released = 0.0
        for idx in top1.index:
            current = float(out.loc[idx, "TargetWeight"])
            delta = current * trim_fraction
            out.loc[idx, "TargetWeight"] = current - delta
            released += delta
        if released <= 0:
            return out

        recipient_mask = (
            out["Market"].astype(str).eq("KR")
            & out["Sector"].astype(str).eq("ETF")
            & ~out.index.isin(top1.index)
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


def _compose_patch(trim_fraction: float):
    base_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    trigger_patch = _patch_single_name_trigger_kr_etf_only(trim_fraction)

    def patch(book: pd.DataFrame) -> pd.DataFrame:
        return trigger_patch(base_patch(book))

    return patch


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Single Name Trigger Trim Refine",
        "",
        "## Purpose",
        "",
        "- keep the single-name trigger family fixed",
        "- refine stronger trim values to see whether the growth-heavy alternative can move closer to the representative MDD bar",
        "",
        "## Current Read",
        "",
        f"- representative benchmark: `{summary['representative_variant']}`",
        f"- base single-name point: `{summary['base_single_name_variant']}`",
        f"- best refined point: `{summary['best_variant']}`",
        f"- best refined CAGR / MDD: `{_pct(summary['best_cagr'])}` / `{_pct(summary['best_mdd'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Trim | Switch Count | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | {_pct(row['TrimFraction'])} | {int(row['SwitchCount'])} | "
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

    followup_contract = _load_json(FOLLOWUP_CONTRACT_JSON)
    base_single_name = _load_json(BASE_SINGLE_NAME_JSON)
    representative_variant = str(followup_contract["representative_variant"])
    representative_cagr = float(followup_contract["representative_cagr"])
    representative_mdd = float(followup_contract["representative_mdd"])

    rows: list[dict[str, object]] = []
    for trim_fraction in [0.21, 0.22, 0.24, 0.26]:
        variant_name = _compose_variant_name(trim_fraction)
        variant = replace(strongest, name=variant_name)
        result, switch_count = _run_with_baseline_switch_carry(
            variant=variant,
            fallback_variant=baseline,
            redistribution_patch=_compose_patch(trim_fraction),
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
        summary["SwitchCount"] = switch_count
        rows.append(summary)

    compare = pd.DataFrame(rows)
    compare["MDDBucket"] = compare["MDD"].round(9)
    compare = compare.sort_values(
        ["NegativeCAGRWindows", "MDDBucket", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(
        OUTPUT_DIR / "single_name_trigger_trim_refine_compare.csv",
        index=False,
        encoding="utf-8-sig",
    )

    best = compare.iloc[0]
    summary = {
        "representative_variant": representative_variant,
        "representative_cagr": representative_cagr,
        "representative_mdd": representative_mdd,
        "base_single_name_variant": base_single_name["best_variant"],
        "base_single_name_cagr": float(base_single_name["best_cagr"]),
        "base_single_name_mdd": float(base_single_name["best_mdd"]),
        "best_variant": str(best["Variant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "best_trim_fraction": float(best["TrimFraction"]),
        "best_switch_count": int(best["SwitchCount"]),
        "beats_representative_on_mdd": bool(best["MDD"] > representative_mdd + MDD_TOL),
        "beats_representative_on_cagr": bool(best["CAGR"] > representative_cagr + 1e-12),
        "improves_base_single_name_on_mdd": bool(best["MDD"] > float(base_single_name["best_mdd"]) + MDD_TOL),
        "ranked_rows": compare.to_dict(orient="records"),
    }

    if best["MDD"] > representative_mdd + MDD_TOL and best["CAGR"] >= representative_cagr - 1e-12:
        summary["verdict"] = (
            f"the refined single-name trigger finds a representative challenger. `{summary['best_variant']}` moves to "
            f"CAGR {_pct(summary['best_cagr'])} and MDD {_pct(summary['best_mdd'])} versus representative "
            f"{_pct(representative_cagr)} / {_pct(representative_mdd)}."
        )
    elif best["CAGR"] > representative_cagr + 1e-12 and best["MDD"] < representative_mdd - MDD_TOL:
        summary["verdict"] = (
            f"the refined single-name trigger remains a growth-heavy alternative. `{summary['best_variant']}` keeps "
            f"CAGR {_pct(summary['best_cagr'])} above representative {_pct(representative_cagr)} but MDD stays at "
            f"{_pct(summary['best_mdd'])}, below representative {_pct(representative_mdd)}."
        )
    elif best["MDD"] > float(base_single_name["best_mdd"]) + MDD_TOL:
        summary["verdict"] = (
            f"the refined single-name trigger improves on the base single-name point but still does not replace the representative. "
            f"`{summary['best_variant']}` reaches {_pct(summary['best_cagr'])} / {_pct(summary['best_mdd'])}."
        )
    else:
        summary["verdict"] = (
            f"the refined single-name trigger does not improve the current single-name alternative. "
            f"`{summary['best_variant']}` does not beat `{base_single_name['best_variant']}` on the representative tradeoff."
        )

    (OUTPUT_DIR / "single_name_trigger_trim_refine_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "single_name_trigger_trim_refine_review.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
