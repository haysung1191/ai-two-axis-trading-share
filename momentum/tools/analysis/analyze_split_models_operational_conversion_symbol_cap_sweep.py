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
    _make_variant_name,
    _patch_tail_release_custom,
    _pct,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    _build_context,
    _run_with_patch,
    _summarize_candidate,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_symbol_cap_sweep"
BASELINE_VARIANT = "rule_breadth_it_us5_cap"
STRONGEST_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
BASE_REDISTRIBUTION_VARIANT = "tail_release_top25_mid75_pen35_floor25"


def _compose_patches(*patches):
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        out = book.copy()
        for patch_fn in patches:
            out = patch_fn(out)
        return out

    return patch


def _patch_us_single_name_cap(max_weight: float):
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or "TargetWeight" not in book.columns:
            return book
        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        if "Market" not in out.columns:
            return out

        us_single_mask = out["Market"].astype(str).eq("US")
        if "Sector" in out.columns:
            us_single_mask &= ~out["Sector"].astype(str).eq("ETF")
        capped = out.loc[us_single_mask].copy()
        if capped.empty:
            return out

        excess = (capped["TargetWeight"] - max_weight).clip(lower=0.0)
        total_excess = float(excess.sum())
        if total_excess <= 0:
            return out

        out.loc[capped.index, "TargetWeight"] = capped["TargetWeight"].clip(upper=max_weight)

        kr_etf_mask = out["Market"].astype(str).eq("KR")
        if "Sector" in out.columns:
            kr_etf_mask &= out["Sector"].astype(str).eq("ETF")
        recipients = out.loc[kr_etf_mask].copy()
        if recipients.empty:
            recipients = out.loc[~us_single_mask].copy()
        if recipients.empty:
            recipients = out.loc[capped.index].copy()

        recipient_weights = pd.to_numeric(recipients["TargetWeight"], errors="coerce").fillna(0.0)
        total = float(recipient_weights.sum())
        if total > 0:
            out.loc[recipients.index, "TargetWeight"] = recipient_weights + total_excess * (recipient_weights / total)
        else:
            out.loc[recipients.index, "TargetWeight"] = recipient_weights + total_excess / float(len(recipients))

        total_after = float(out["TargetWeight"].sum())
        if total_after > 0:
            out["TargetWeight"] = out["TargetWeight"] / total_after
        return out

    return patch


def _bucket(row: pd.Series, baseline: pd.Series) -> str:
    if (
        row["NegativeCAGRWindows"] == 0
        and row["CAGR"] > baseline["CAGR"]
        and row["Sharpe"] > baseline["Sharpe"]
        and row["MDD"] >= -0.32
    ):
        return "tight_watch"
    if row["NegativeCAGRWindows"] == 0 and row["CAGR"] > 0.70:
        return "watch"
    return "monitor"


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Symbol Cap Sweep",
        "",
        "## Purpose",
        "",
        "- test whether a narrow US single-name cap improves the best redistribution drawdown-control point",
        "- keep the redistribution structure fixed and only add one operating-style pressure-release axis",
        "",
        "## Current Read",
        "",
        f"- redistribution base point: `{summary['base_variant']}`",
        f"- best symbol-cap point: `{summary['best_cap_variant']}`",
        f"- best symbol-cap MDD: `{_pct(summary['best_cap_mdd'])}`",
        f"- best symbol-cap CAGR: `{_pct(summary['best_cap_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Bucket | Max US Name | CAGR | MDD | Sharpe | Neg WF | Top3 Share |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | `{row['Bucket']}` | {_pct(row['MaxUSNameWeight'])} | {_pct(row['CAGR'])} | "
            f"{_pct(row['MDD'])} | {row['Sharpe']:.4f} | {int(row['NegativeCAGRWindows'])} | {_pct(row['Top3PositiveSymbolShare'])} |"
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
    baseline_summary = _summarize_candidate(BASELINE_VARIANT, baseline_result, strongest_result)

    base_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    cap_grid = [0.14, 0.12, 0.10, 0.08]

    rows: list[dict[str, object]] = []
    for cap in cap_grid:
        variant_name = f"{BASE_REDISTRIBUTION_VARIANT}_uscap{int(round(cap * 100)):02d}"
        variant = replace(strongest, name=variant_name)
        result = _run_with_patch(
            variant,
            _compose_patches(base_patch, _patch_us_single_name_cap(cap)),
            universe,
            price_cache,
            flow_cache,
            monthly_close,
            signal_dates,
            cfg,
        )
        summary = _summarize_candidate(variant_name, result, strongest_result)
        summary["MaxUSNameWeight"] = cap
        summary["Bucket"] = _bucket(pd.Series(summary), pd.Series(baseline_summary))
        rows.append(summary)

    base_variant_name = _make_variant_name(0.25, 0.35, 0.25)
    base_variant = replace(strongest, name=base_variant_name)
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
    base_summary = _summarize_candidate(base_variant_name, base_result, strongest_result)
    base_summary["MaxUSNameWeight"] = 1.0
    base_summary["Bucket"] = _bucket(pd.Series(base_summary), pd.Series(baseline_summary))
    rows.append(base_summary)

    compare = pd.DataFrame(rows).sort_values(
        ["NegativeCAGRWindows", "MDD", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "symbol_cap_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "base_variant": BASE_REDISTRIBUTION_VARIANT,
        "best_cap_variant": str(best["Variant"]),
        "best_cap_cagr": float(best["CAGR"]),
        "best_cap_mdd": float(best["MDD"]),
        "best_cap_sharpe": float(best["Sharpe"]),
        "best_cap_max_us_name_weight": float(best["MaxUSNameWeight"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    if summary["best_cap_variant"] == BASE_REDISTRIBUTION_VARIANT:
        summary["verdict"] = (
            f"the narrow US single-name cap axis fails: no capped point beats `{BASE_REDISTRIBUTION_VARIANT}`. "
            f"Caps reduce CAGR too aggressively and break walk-forward quality before they deliver a meaningful drawdown repair."
        )
    else:
        summary["verdict"] = (
            f"adding a narrow US single-name cap finds `{summary['best_cap_variant']}` as the cleanest next point; "
            f"it moves MDD to {_pct(summary['best_cap_mdd'])} with CAGR {_pct(summary['best_cap_cagr'])}. "
            f"This tells us whether single-name pressure relief is enough to keep pushing the redistribution branch toward operating conversion."
        )

    (OUTPUT_DIR / "symbol_cap_sweep_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "symbol_cap_sweep_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
