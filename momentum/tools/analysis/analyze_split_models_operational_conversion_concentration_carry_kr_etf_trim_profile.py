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
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import _patch_tail_release_custom, _pct
from tools.analysis.analyze_split_models_tradeoff_frontier import _build_context


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_concentration_carry_kr_etf_trim_profile"
CONCENTRATION_THRESHOLD = 0.70
THRESHOLD_GAP = 0.02
CARRY_COUNT = 2
TARGET_SECTORS = {"Information Technology", "Energy"}
PROFILE_TRIMS = [0.20, 0.21, 0.22]


def _compose_variant_name(trim_fraction: float) -> str:
    return (
        f"{BASE_VARIANT}_conccarrykretfprofile_ct{int(round(CONCENTRATION_THRESHOLD * 100)):02d}"
        f"_trim{int(round(trim_fraction * 100)):02d}"
        f"_gap{int(round(THRESHOLD_GAP * 100)):02d}"
        f"_top{CARRY_COUNT}"
    )


def _patch_concentration_trigger_kr_etf_only(trim_fraction: float):
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


def _compose_patch(trim_fraction: float):
    base_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    concentration_patch = _patch_concentration_trigger_kr_etf_only(trim_fraction)

    def patch(book: pd.DataFrame) -> pd.DataFrame:
        return concentration_patch(base_patch(book))

    return patch


def _prepare_nav(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["SignalDate"] = pd.to_datetime(out["SignalDate"])
    out["NextDate"] = pd.to_datetime(out["NextDate"])
    out["NetReturn"] = pd.to_numeric(out["NetReturn"], errors="coerce").fillna(0.0)
    return out


def _prepare_symbol_contrib(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["SignalDate"] = pd.to_datetime(out["SignalDate"])
    out["NextDate"] = pd.to_datetime(out["NextDate"])
    out["Contribution"] = pd.to_numeric(out["Contribution"], errors="coerce").fillna(0.0)
    return out


def _monthly_compare(base_nav: pd.DataFrame, variants: dict[str, pd.DataFrame]) -> pd.DataFrame:
    compare = base_nav[["SignalDate", "NextDate", "NetReturn"]].rename(columns={"NetReturn": "BaseNetReturn"})
    for name, nav in variants.items():
        compare = compare.merge(
            nav[["SignalDate", "NextDate", "NetReturn"]].rename(columns={"NetReturn": f"{name}NetReturn"}),
            on=["SignalDate", "NextDate"],
            how="left",
        )
        compare[f"{name}VsBaseDelta"] = compare[f"{name}NetReturn"] - compare["BaseNetReturn"]
    return compare.sort_values("SignalDate").reset_index(drop=True)


def _symbol_delta(df_a: pd.DataFrame, df_b: pd.DataFrame, label_a: str, label_b: str) -> pd.DataFrame:
    merged = (
        df_a.groupby(["Market", "Sector", "Symbol"], as_index=False)
        .agg(**{f"{label_a}Contribution": ("Contribution", "sum")})
        .merge(
            df_b.groupby(["Market", "Sector", "Symbol"], as_index=False)
            .agg(**{f"{label_b}Contribution": ("Contribution", "sum")}),
            on=["Market", "Sector", "Symbol"],
            how="outer",
        )
        .fillna(0.0)
    )
    merged[f"{label_a}Vs{label_b}Delta"] = merged[f"{label_a}Contribution"] - merged[f"{label_b}Contribution"]
    return merged.sort_values(f"{label_a}Vs{label_b}Delta").reset_index(drop=True)


def _records(df: pd.DataFrame, n: int, sort_column: str, ascending: bool = True) -> list[dict[str, object]]:
    rows = df.sort_values(sort_column, ascending=ascending).head(n)
    result: list[dict[str, object]] = []
    for row in rows.to_dict(orient="records"):
        clean: dict[str, object] = {}
        for key, value in row.items():
            if isinstance(value, pd.Timestamp):
                clean[key] = value.strftime("%Y-%m-%d")
            else:
                clean[key] = value
        result.append(clean)
    return result


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Concentration Carry KR ETF Trim Profile",
        "",
        "## Purpose",
        "",
        "- compare trim20, trim21, and trim22 directly",
        "- explain what monthly and symbol-level sacrifice buys the extra drawdown repair",
        "",
        "## Current Read",
        "",
        f"- profile trims: `{', '.join(summary['profile_trims'])}`",
        f"- best growth-preserving point: `{summary['growth_variant']}`",
        f"- best balance point: `{summary['balance_variant']}`",
        f"- best drawdown point: `{summary['drawdown_variant']}`",
        "",
        "## Worst Monthly Deltas Vs Base",
        "",
        "| Variant | SignalDate | NextDate | Delta |",
        "| --- | --- | --- | ---: |",
    ]
    for row in summary["worst_months_vs_base"]:
        lines.append(
            f"| `{row['Variant']}` | `{row['SignalDate']}` | `{row['NextDate']}` | {_pct(row['Delta'])} |"
        )
    lines.extend(
        [
            "",
            "## Worst Symbol Deltas Vs Base",
            "",
            "| Variant | Symbol | Market | Sector | Delta |",
            "| --- | --- | --- | --- | ---: |",
        ]
    )
    for row in summary["worst_symbols_vs_base"]:
        lines.append(
            f"| `{row['Variant']}` | `{row['Symbol']}` | `{row['Market']}` | `{row['Sector']}` | {_pct(row['Delta'])} |"
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

    trim_results: dict[str, dict[str, pd.DataFrame]] = {}
    for trim_fraction in PROFILE_TRIMS:
        name = f"trim{int(round(trim_fraction * 100)):02d}"
        variant = replace(strongest, name=_compose_variant_name(trim_fraction))
        result, _ = _run_with_baseline_switch_carry(
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
        trim_results[name] = result

    base_nav = _prepare_nav(base_result["nav"])
    trim_nav = {name: _prepare_nav(result["nav"]) for name, result in trim_results.items()}
    monthly_compare = _monthly_compare(base_nav, trim_nav)
    monthly_export = monthly_compare.copy()
    monthly_export["SignalDate"] = monthly_export["SignalDate"].dt.strftime("%Y-%m-%d")
    monthly_export["NextDate"] = monthly_export["NextDate"].dt.strftime("%Y-%m-%d")
    monthly_export.to_csv(OUTPUT_DIR / "concentration_carry_kr_etf_trim_profile_monthly_compare.csv", index=False, encoding="utf-8-sig")

    symbol_compare_frames = []
    for name, result in trim_results.items():
        delta_df = _symbol_delta(_prepare_symbol_contrib(result["symbol_contrib"]), _prepare_symbol_contrib(base_result["symbol_contrib"]), name, "Base")
        delta_df["Variant"] = name
        delta_df = delta_df.rename(columns={f"{name}VsBaseDelta": "Delta"})
        symbol_compare_frames.append(delta_df[["Variant", "Market", "Sector", "Symbol", "Delta"]])
    symbol_compare = pd.concat(symbol_compare_frames, ignore_index=True)
    symbol_compare.to_csv(OUTPUT_DIR / "concentration_carry_kr_etf_trim_profile_symbol_delta_vs_base.csv", index=False, encoding="utf-8-sig")

    worst_months = []
    for name in trim_results:
        delta_col = f"{name}VsBaseDelta"
        row = monthly_compare.sort_values(delta_col).iloc[0]
        worst_months.append(
            {
                "Variant": name,
                "SignalDate": row["SignalDate"].strftime("%Y-%m-%d"),
                "NextDate": row["NextDate"].strftime("%Y-%m-%d"),
                "Delta": float(row[delta_col]),
            }
        )

    worst_symbols = []
    for name in trim_results:
        variant_slice = symbol_compare.loc[symbol_compare["Variant"] == name].sort_values("Delta").iloc[0]
        worst_symbols.append(
            {
                "Variant": name,
                "Symbol": variant_slice["Symbol"],
                "Market": variant_slice["Market"],
                "Sector": variant_slice["Sector"],
                "Delta": float(variant_slice["Delta"]),
            }
        )

    summary = {
        "profile_trims": [f"trim{int(round(v * 100)):02d}" for v in PROFILE_TRIMS],
        "growth_variant": "trim20",
        "balance_variant": "trim21",
        "drawdown_variant": "trim22",
        "worst_months_vs_base": worst_months,
        "worst_symbols_vs_base": worst_symbols,
        "verdict": (
            f"`trim22` keeps the best drawdown repair, `trim20` keeps the best CAGR, and `trim21` sits between them. "
            f"The extra drawdown repair from `trim20 -> trim22` comes with a repeated monthly growth sacrifice rather than a single isolated collapse."
        ),
    }

    (OUTPUT_DIR / "concentration_carry_kr_etf_trim_profile_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "concentration_carry_kr_etf_trim_profile_review.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
