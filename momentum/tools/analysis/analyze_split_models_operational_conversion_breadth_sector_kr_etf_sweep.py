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
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_breadth_sector_kr_etf_sweep"
FOLLOWUP_CONTRACT_JSON = (
    ROOT / "output" / "split_models_operational_conversion_followup_contract" / "followup_contract_summary.json"
)
MDD_TOL = 1e-9
THRESHOLD_GAP = 0.02
CARRY_COUNT = 2
ACTIVE_WEIGHT_THRESHOLD = 0.05
TARGET_SECTORS = {"Information Technology", "Energy"}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _compose_variant_name(active_count_max: int, sector_bias_min: float, trim_fraction: float) -> str:
    return (
        f"{BASE_VARIANT}_breadthsectorkretf"
        f"_active{int(active_count_max)}"
        f"_bias{int(round(sector_bias_min * 100)):02d}"
        f"_trim{int(round(trim_fraction * 100)):02d}"
        f"_top{CARRY_COUNT}"
    )


def _patch_breadth_sector_kr_etf_only(active_count_max: int, sector_bias_min: float, trim_fraction: float):
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 4:
            return book

        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        ranked = out.sort_values(
            ["TargetWeight", "MomentumScore", "FlowScore", "Symbol"],
            ascending=[False, False, False, True],
        )

        active_count = int((ranked["TargetWeight"] >= ACTIVE_WEIGHT_THRESHOLD).sum())
        if active_count > active_count_max:
            return out

        sector_bias = float(
            ranked.loc[
                ranked["Market"].astype(str).eq("US")
                & ranked["Sector"].astype(str).isin(TARGET_SECTORS),
                "TargetWeight",
            ].sum()
        )
        if sector_bias < sector_bias_min:
            return out

        top2 = ranked.head(2).copy()
        released = 0.0
        for idx in top2.index:
            current = float(out.loc[idx, "TargetWeight"])
            delta = current * trim_fraction
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


def _compose_patch(active_count_max: int, sector_bias_min: float, trim_fraction: float):
    base_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    trigger_patch = _patch_breadth_sector_kr_etf_only(active_count_max, sector_bias_min, trim_fraction)

    def patch(book: pd.DataFrame) -> pd.DataFrame:
        return trigger_patch(base_patch(book))

    return patch


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Breadth Sector KR ETF Sweep",
        "",
        "## Purpose",
        "",
        "- test a breadth-driven representative-type trigger family",
        "- trigger only when effective active holdings are low and US IT/Energy bias is high, then trim top2 into KR ETF recipients",
        "",
        "## Current Read",
        "",
        f"- representative benchmark: `{summary['representative_variant']}`",
        f"- best breadth-sector point: `{summary['best_variant']}`",
        f"- best CAGR / MDD: `{_pct(summary['best_cagr'])}` / `{_pct(summary['best_mdd'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Active Max | Sector Bias Min | Trim | Switch Count | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        active_max = "-" if pd.isna(row["ActiveCountMax"]) else str(int(row["ActiveCountMax"]))
        sector_bias = "-" if pd.isna(row["SectorBiasMin"]) else _pct(row["SectorBiasMin"])
        lines.append(
            f"| {idx} | `{row['Variant']}` | {active_max} | {sector_bias} | "
            f"{_pct(row['TrimFraction'])} | {int(row['SwitchCount'])} | {_pct(row['CAGR'])} | "
            f"{_pct(row['MDD'])} | {row['Sharpe']:.4f} | {int(row['NegativeCAGRWindows'])} |"
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
    base_summary["ActiveCountMax"] = None
    base_summary["SectorBiasMin"] = None
    base_summary["TrimFraction"] = 0.0
    base_summary["SwitchCount"] = 0

    rows: list[dict[str, object]] = [base_summary]
    for active_count_max, sector_bias_min, trim_fraction in [
        (6, 0.55, 0.18),
        (6, 0.55, 0.20),
        (6, 0.60, 0.18),
        (6, 0.60, 0.20),
        (7, 0.55, 0.18),
        (7, 0.55, 0.20),
        (7, 0.60, 0.18),
        (7, 0.60, 0.20),
    ]:
        variant_name = _compose_variant_name(active_count_max, sector_bias_min, trim_fraction)
        variant = replace(strongest, name=variant_name)
        result, switch_count = _run_with_baseline_switch_carry(
            variant=variant,
            fallback_variant=baseline,
            redistribution_patch=_compose_patch(active_count_max, sector_bias_min, trim_fraction),
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
        summary["ActiveCountMax"] = active_count_max
        summary["SectorBiasMin"] = sector_bias_min
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
        OUTPUT_DIR / "breadth_sector_kr_etf_sweep_compare.csv",
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
        "best_active_count_max": None if pd.isna(best["ActiveCountMax"]) else int(best["ActiveCountMax"]),
        "best_sector_bias_min": None if pd.isna(best["SectorBiasMin"]) else float(best["SectorBiasMin"]),
        "best_trim_fraction": float(best["TrimFraction"]),
        "best_switch_count": int(best["SwitchCount"]),
        "beats_representative_on_mdd": bool(best["MDD"] > representative_mdd + MDD_TOL),
        "beats_representative_on_cagr": bool(best["CAGR"] > representative_cagr + 1e-12),
        "improves_base_on_mdd": bool(best["MDD"] > float(base_summary["MDD"]) + MDD_TOL),
        "ranked_rows": compare.to_dict(orient="records"),
    }

    if best["MDD"] > representative_mdd + MDD_TOL and best["CAGR"] >= representative_cagr - 1e-12:
        summary["verdict"] = (
            f"the breadth-sector KR ETF trigger finds a representative challenger. `{summary['best_variant']}` reaches "
            f"{_pct(summary['best_cagr'])} / {_pct(summary['best_mdd'])} versus representative "
            f"{_pct(representative_cagr)} / {_pct(representative_mdd)}."
        )
    elif best["MDD"] > representative_mdd + MDD_TOL:
        summary["verdict"] = (
            f"the breadth-sector KR ETF trigger improves drawdown beyond the representative but pays for it in CAGR. "
            f"`{summary['best_variant']}` reaches {_pct(summary['best_cagr'])} / {_pct(summary['best_mdd'])}."
        )
    elif best["CAGR"] > representative_cagr + 1e-12 and best["MDD"] < representative_mdd - MDD_TOL:
        summary["verdict"] = (
            f"the breadth-sector KR ETF trigger becomes a growth-heavy alternative, not a representative replacement. "
            f"`{summary['best_variant']}` lifts CAGR to {_pct(summary['best_cagr'])} but MDD stays at "
            f"{_pct(summary['best_mdd'])} versus representative {_pct(representative_mdd)}."
        )
    elif best["MDD"] > float(base_summary["MDD"]) + MDD_TOL:
        summary["verdict"] = (
            f"the breadth-sector KR ETF trigger improves on the base anchor but does not replace the representative. "
            f"`{summary['best_variant']}` reaches {_pct(summary['best_cagr'])} / {_pct(summary['best_mdd'])}."
        )
    else:
        summary["verdict"] = (
            f"the breadth-sector KR ETF trigger does not improve the current representative tradeoff. "
            f"`{summary['best_variant']}` does not beat `{representative_variant}` on the benchmark balance."
        )

    (OUTPUT_DIR / "breadth_sector_kr_etf_sweep_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "breadth_sector_kr_etf_sweep_review.md").write_text(
        _build_markdown(summary),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
