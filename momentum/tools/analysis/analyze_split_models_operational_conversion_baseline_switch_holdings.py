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
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_sweep import (
    BASELINE_VARIANT,
    BASE_VARIANT,
    STRONGEST_VARIANT,
    _compose_variant_name,
    _run_with_baseline_switch,
)
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import (
    _patch_tail_release_custom,
    _pct,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import _build_context


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_baseline_switch_holdings"
SWEEP_SUMMARY_JSON = (
    ROOT / "output" / "split_models_operational_conversion_baseline_switch_sweep" / "baseline_switch_sweep_summary.json"
)
SWITCH_THRESHOLD_GAP = 0.00
SWITCH_SECTOR_BIAS_MIN = None


def _prepare_positions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["SignalDate"] = pd.to_datetime(out["SignalDate"])
    out["NextDate"] = pd.to_datetime(out["NextDate"])
    out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
    return out


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


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _month_signature(df: pd.DataFrame) -> dict[tuple[pd.Timestamp, pd.Timestamp], tuple[tuple[str, float], ...]]:
    signatures: dict[tuple[pd.Timestamp, pd.Timestamp], tuple[tuple[str, float], ...]] = {}
    for (signal_date, next_date), group in df.groupby(["SignalDate", "NextDate"]):
        rows = tuple(
            sorted(
                (
                    f"{row['Market']}::{row['Sector']}::{row['Symbol']}",
                    round(float(row["TargetWeight"]), 8),
                )
                for _, row in group.iterrows()
            )
        )
        signatures[(signal_date, next_date)] = rows
    return signatures


def _switch_months(
    switch_positions: pd.DataFrame,
    baseline_positions: pd.DataFrame,
    base_positions: pd.DataFrame,
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    switch_sig = _month_signature(switch_positions)
    baseline_sig = _month_signature(baseline_positions)
    base_sig = _month_signature(base_positions)

    months: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for key, sig in switch_sig.items():
        baseline_same = baseline_sig.get(key) == sig
        base_same = base_sig.get(key) == sig
        if baseline_same and not base_same:
            months.append(key)
    return months


def _monthly_return_compare(
    switch_nav: pd.DataFrame,
    base_nav: pd.DataFrame,
    baseline_nav: pd.DataFrame,
    switch_months: list[tuple[pd.Timestamp, pd.Timestamp]],
) -> pd.DataFrame:
    month_df = pd.DataFrame(switch_months, columns=["SignalDate", "NextDate"])
    compare = (
        month_df.merge(
            switch_nav[["SignalDate", "NextDate", "NetReturn"]].rename(columns={"NetReturn": "SwitchNetReturn"}),
            on=["SignalDate", "NextDate"],
            how="left",
        )
        .merge(
            base_nav[["SignalDate", "NextDate", "NetReturn"]].rename(columns={"NetReturn": "BaseNetReturn"}),
            on=["SignalDate", "NextDate"],
            how="left",
        )
        .merge(
            baseline_nav[["SignalDate", "NextDate", "NetReturn"]].rename(columns={"NetReturn": "BaselineNetReturn"}),
            on=["SignalDate", "NextDate"],
            how="left",
        )
    )
    compare["SwitchVsBaseDelta"] = compare["SwitchNetReturn"] - compare["BaseNetReturn"]
    compare["SwitchVsBaselineDelta"] = compare["SwitchNetReturn"] - compare["BaselineNetReturn"]
    return compare.sort_values("SignalDate").reset_index(drop=True)


def _symbol_delta(
    left: pd.DataFrame,
    right: pd.DataFrame,
    switch_months: list[tuple[pd.Timestamp, pd.Timestamp]],
    left_name: str,
    right_name: str,
) -> pd.DataFrame:
    month_df = pd.DataFrame(switch_months, columns=["SignalDate", "NextDate"])
    left_slice = month_df.merge(left, on=["SignalDate", "NextDate"], how="left")
    right_slice = month_df.merge(right, on=["SignalDate", "NextDate"], how="left")

    merged = (
        left_slice.groupby(["Market", "Sector", "Symbol"], as_index=False)
        .agg(**{f"{left_name}Contribution": ("Contribution", "sum")})
        .merge(
            right_slice.groupby(["Market", "Sector", "Symbol"], as_index=False).agg(
                **{f"{right_name}Contribution": ("Contribution", "sum")}
            ),
            on=["Market", "Sector", "Symbol"],
            how="outer",
        )
        .fillna(0.0)
    )
    merged[f"{left_name}Vs{right_name}Delta"] = (
        merged[f"{left_name}Contribution"] - merged[f"{right_name}Contribution"]
    )
    return merged.sort_values(f"{left_name}Vs{right_name}Delta").reset_index(drop=True)


def _top_records(df: pd.DataFrame, column: str, n: int) -> list[dict[str, object]]:
    rows = df.head(n).copy()
    records: list[dict[str, object]] = []
    for row in rows.to_dict(orient="records"):
        clean = {}
        for key, value in row.items():
            if isinstance(value, pd.Timestamp):
                clean[key] = value.strftime("%Y-%m-%d")
            else:
                clean[key] = value
        records.append(clean)
    return records


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Baseline Switch Holdings Diagnostic",
        "",
        "## Purpose",
        "",
        "- inspect the actual switch months for the baseline-switch axis",
        "- explain why switching books still failed to improve drawdown",
        "",
        "## Current Read",
        "",
        f"- switch variant under inspection: `{summary['switch_variant']}`",
        f"- reported trigger count: `{summary['reported_switch_count']}`",
        f"- inferred baseline-matched switch month count: `{summary['switch_month_count']}`",
        f"- average switch-vs-base monthly delta: `{_pct(summary['avg_switch_vs_base_delta'])}`",
        f"- average switch-vs-baseline monthly delta: `{_pct(summary['avg_switch_vs_baseline_delta'])}`",
        "",
        "## Switch Months",
        "",
        "| Rank | SignalDate | NextDate | Switch | Base | Baseline | Switch-Base | Switch-Baseline |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["switch_months"], start=1):
        lines.append(
            f"| {idx} | `{row['SignalDate']}` | `{row['NextDate']}` | {_pct(row['SwitchNetReturn'])} | "
            f"{_pct(row['BaseNetReturn'])} | {_pct(row['BaselineNetReturn'])} | {_pct(row['SwitchVsBaseDelta'])} | {_pct(row['SwitchVsBaselineDelta'])} |"
        )
    lines.extend(
        [
            "",
            "## Worst Switch-vs-Base Symbol Deltas",
            "",
            "| Rank | Symbol | Market | Sector | Delta |",
            "| --- | --- | --- | --- | ---: |",
        ]
    )
    for idx, row in enumerate(summary["worst_switch_vs_base_symbols"], start=1):
        lines.append(
            f"| {idx} | `{row['Symbol']}` | `{row['Market']}` | `{row['Sector']}` | {_pct(row['SwitchVsBaseDelta'])} |"
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
    redistribution_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)
    sweep_summary = _load_json(SWEEP_SUMMARY_JSON)

    base_result, _, _ = _run_with_baseline_switch(
        variant=replace(strongest, name=BASE_VARIANT),
        fallback_variant=baseline,
        redistribution_patch=redistribution_patch,
        threshold_gap=999.0,
        sector_bias_min=None,
        universe=universe,
        price_cache=price_cache,
        flow_cache=flow_cache,
        monthly_close=monthly_close,
        signal_dates=signal_dates,
        cfg=cfg,
    )
    baseline_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, baseline
    )
    switch_variant_name = _compose_variant_name(SWITCH_THRESHOLD_GAP, SWITCH_SECTOR_BIAS_MIN)
    reported_switch_row = next(
        row for row in sweep_summary["ranked_rows"] if row["Variant"] == switch_variant_name
    )
    switch_result, _, _ = _run_with_baseline_switch(
        variant=replace(strongest, name=switch_variant_name),
        fallback_variant=baseline,
        redistribution_patch=redistribution_patch,
        threshold_gap=SWITCH_THRESHOLD_GAP,
        sector_bias_min=SWITCH_SECTOR_BIAS_MIN,
        universe=universe,
        price_cache=price_cache,
        flow_cache=flow_cache,
        monthly_close=monthly_close,
        signal_dates=signal_dates,
        cfg=cfg,
    )

    base_positions = _prepare_positions(base_result["positions"])
    baseline_positions = _prepare_positions(baseline_result["positions"])
    switch_positions = _prepare_positions(switch_result["positions"])

    base_nav = _prepare_nav(base_result["nav"])
    baseline_nav = _prepare_nav(baseline_result["nav"])
    switch_nav = _prepare_nav(switch_result["nav"])

    base_symbol = _prepare_symbol_contrib(base_result["symbol_contrib"])
    baseline_symbol = _prepare_symbol_contrib(baseline_result["symbol_contrib"])
    switch_symbol = _prepare_symbol_contrib(switch_result["symbol_contrib"])

    switch_months = _switch_months(switch_positions, baseline_positions, base_positions)
    monthly_compare = _monthly_return_compare(switch_nav, base_nav, baseline_nav, switch_months)
    symbol_switch_vs_base = _symbol_delta(switch_symbol, base_symbol, switch_months, "Switch", "Base")
    symbol_switch_vs_baseline = _symbol_delta(switch_symbol, baseline_symbol, switch_months, "Switch", "Baseline")

    monthly_export = monthly_compare.copy()
    monthly_export["SignalDate"] = monthly_export["SignalDate"].dt.strftime("%Y-%m-%d")
    monthly_export["NextDate"] = monthly_export["NextDate"].dt.strftime("%Y-%m-%d")
    monthly_export.to_csv(OUTPUT_DIR / "baseline_switch_monthly_compare.csv", index=False, encoding="utf-8-sig")
    symbol_switch_vs_base.to_csv(OUTPUT_DIR / "baseline_switch_symbol_delta_vs_base.csv", index=False, encoding="utf-8-sig")
    symbol_switch_vs_baseline.to_csv(
        OUTPUT_DIR / "baseline_switch_symbol_delta_vs_baseline.csv", index=False, encoding="utf-8-sig"
    )

    avg_switch_vs_base = float(monthly_compare["SwitchVsBaseDelta"].mean()) if not monthly_compare.empty else 0.0
    avg_switch_vs_baseline = (
        float(monthly_compare["SwitchVsBaselineDelta"].mean()) if not monthly_compare.empty else 0.0
    )

    summary = {
        "switch_variant": switch_variant_name,
        "reported_switch_count": int(reported_switch_row["SwitchCount"]),
        "switch_month_count": len(switch_months),
        "switch_months": monthly_export.to_dict(orient="records"),
        "avg_switch_vs_base_delta": avg_switch_vs_base,
        "avg_switch_vs_baseline_delta": avg_switch_vs_baseline,
        "worst_switch_vs_base_symbols": _top_records(symbol_switch_vs_base, "SwitchVsBaseDelta", 8),
        "worst_switch_vs_baseline_symbols": _top_records(symbol_switch_vs_baseline, "SwitchVsBaselineDelta", 8),
    }
    if len(switch_months) == 0:
        summary["verdict"] = "the switch variant never actually matched the baseline book, so there is no holdings-level switch regime to analyze."
    else:
        worst_month = summary["switch_months"][0]
        worst_symbol = summary["worst_switch_vs_base_symbols"][0] if summary["worst_switch_vs_base_symbols"] else None
        summary["verdict"] = (
            f"`{switch_variant_name}` triggered {summary['reported_switch_count']} times, but only {len(switch_months)} months "
            f"fully matched the baseline holdings book. Across those matched months, "
            f"the average switch-vs-base monthly delta was {_pct(avg_switch_vs_base)} and the worst switched month "
            f"was `{worst_month['NextDate']}` at {_pct(worst_month['SwitchVsBaseDelta'])}; "
            f"the main negative symbol delta versus base was `{worst_symbol['Symbol']}`."
            if worst_symbol
            else f"`{switch_variant_name}` did switch into the baseline book for {len(switch_months)} months, but it still failed to beat the base book."
        )

    (OUTPUT_DIR / "baseline_switch_holdings_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "baseline_switch_holdings_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
