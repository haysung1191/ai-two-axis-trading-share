from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models.backtest import BacktestConfig, _baseline_variant_map, _run_trading_backtest_variant
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_sweep import (
    BASELINE_VARIANT,
    STRONGEST_VARIANT,
)
from tools.analysis.analyze_split_models_operational_conversion_state_condition_defense_sweep import (
    _run_state_condition_defense,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import _build_context


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_negative_wf_contribution_diagnostic"
WINDOWS_BY_SHIFT = {
    1: ("2022-08-31", "2025-01-31"),
    2: ("2022-09-30", "2025-02-28"),
}


def _date_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for column in ("SignalDate", "NextDate"):
        out[column] = pd.to_datetime(out[column])
    return out


def _window_filter(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    out = _date_columns(frame)
    return out[(out["NextDate"] >= pd.Timestamp(start)) & (out["NextDate"] <= pd.Timestamp(end))].copy()


def _contrib_delta(
    candidate: pd.DataFrame,
    base: pd.DataFrame,
    keys: list[str],
    start: str,
    end: str,
) -> pd.DataFrame:
    left = _window_filter(candidate, start, end)
    right = _window_filter(base, start, end)
    merged = left.merge(
        right,
        on=["SignalDate", "NextDate", *keys],
        how="outer",
        suffixes=("_candidate", "_base"),
    ).fillna({"Contribution_candidate": 0.0, "Contribution_base": 0.0})
    merged["ContributionDelta"] = (
        pd.to_numeric(merged["Contribution_candidate"], errors="coerce").fillna(0.0)
        - pd.to_numeric(merged["Contribution_base"], errors="coerce").fillna(0.0)
    )
    grouped = (
        merged.groupby(keys, as_index=False)
        .agg(
            ContributionDelta=("ContributionDelta", "sum"),
            CandidateContribution=("Contribution_candidate", "sum"),
            BaseContribution=("Contribution_base", "sum"),
        )
        .sort_values("ContributionDelta", ascending=True)
    )
    return grouped


def _position_snapshot(
    candidate_positions: pd.DataFrame,
    start: str,
    end: str,
    top_negative_symbols: set[str],
) -> list[dict[str, object]]:
    positions = _window_filter(candidate_positions, start, end)
    if positions.empty:
        return []
    positions["TargetWeight"] = pd.to_numeric(positions["TargetWeight"], errors="coerce").fillna(0.0)
    positions["FlowScore"] = pd.to_numeric(positions["FlowScore"], errors="coerce").fillna(0.0)
    positions["MomentumScore"] = pd.to_numeric(positions["MomentumScore"], errors="coerce").fillna(0.0)
    positions["NextMonthReturn"] = pd.to_numeric(positions["NextMonthReturn"], errors="coerce").fillna(0.0)
    rows = []
    for signal_date, group in positions.groupby("SignalDate"):
        top_weight = group.sort_values("TargetWeight", ascending=False).head(5)
        watched = group[group["Symbol"].astype(str).isin(top_negative_symbols)]
        rows.append(
            {
                "SignalDate": pd.Timestamp(signal_date).strftime("%Y-%m-%d"),
                "TopWeightSymbols": ",".join(top_weight["Symbol"].astype(str).tolist()),
                "TopWeightTotal": float(top_weight["TargetWeight"].sum()),
                "NegativeDriverWeight": float(watched["TargetWeight"].sum()),
                "NegativeDriverSymbols": ",".join(watched["Symbol"].astype(str).tolist()),
                "NegativeDriverAvgFlow": None if watched.empty else float(watched["FlowScore"].mean()),
                "NegativeDriverAvgMomentum": None if watched.empty else float(watched["MomentumScore"].mean()),
                "NegativeDriverAvgNextReturn": None if watched.empty else float(watched["NextMonthReturn"].mean()),
            }
        )
    return rows


def _run_shift(
    *,
    shift: int,
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
    cfg: BacktestConfig,
) -> dict[str, object]:
    variants = _baseline_variant_map()
    strongest = variants[STRONGEST_VARIANT]
    baseline = variants[BASELINE_VARIANT]
    shifted_dates = signal_dates[shift:]
    base_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, shifted_dates, cfg, strongest
    )
    candidate_result, diagnostics = _run_state_condition_defense(
        variant=replace(strongest, name="negative_wf_contrib_diag_state_sym09_sector28_trim100_max08"),
        fallback_variant=baseline,
        min_symbol_weight=0.09,
        min_sector_weight=0.28,
        require_weak_flow=False,
        require_drag_flow_weak=False,
        max_defense_count=8,
        trim_fraction=1.0,
        universe=universe,
        price_cache=price_cache,
        flow_cache=flow_cache,
        monthly_close=monthly_close,
        signal_dates=shifted_dates,
        cfg=cfg,
    )
    start, end = WINDOWS_BY_SHIFT[shift]
    symbol_delta = _contrib_delta(
        candidate_result["symbol_contrib"],
        base_result["symbol_contrib"],
        ["Market", "Sector", "Symbol"],
        start,
        end,
    )
    sector_delta = _contrib_delta(
        candidate_result["sector_contrib"],
        base_result["sector_contrib"],
        ["Market", "Sector"],
        start,
        end,
    )
    top_negative_symbols = set(symbol_delta.head(5)["Symbol"].astype(str).tolist())
    position_rows = _position_snapshot(candidate_result["positions"], start, end, top_negative_symbols)
    return {
        "shift": shift,
        "window_start": start,
        "window_end": end,
        "diagnostics": diagnostics,
        "worst_symbols": symbol_delta.head(10).to_dict(orient="records"),
        "best_symbols": symbol_delta.tail(10).sort_values("ContributionDelta", ascending=False).to_dict(orient="records"),
        "worst_sectors": sector_delta.head(10).to_dict(orient="records"),
        "position_snapshots": position_rows,
    }


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Negative WF Contribution Diagnostic",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        f"- decision: `{summary['diagnostic_decision']}`",
        "",
        "## Worst Symbol Deltas",
        "",
        "| Shift | Symbol | Market | Sector | Delta | Candidate | Base |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for shift in summary["shift_diagnostics"]:
        for row in shift["worst_symbols"][:5]:
            lines.append(
                f"| {int(shift['shift'])} | `{row['Symbol']}` | {row['Market']} | {row['Sector']} | "
                f"{float(row['ContributionDelta']):.2%} | {float(row['CandidateContribution']):.2%} | "
                f"{float(row['BaseContribution']):.2%} |"
            )
    lines.extend(["", "## Worst Sector Deltas", "", "| Shift | Market | Sector | Delta |", "| ---: | --- | --- | ---: |"])
    for shift in summary["shift_diagnostics"]:
        for row in shift["worst_sectors"][:5]:
            lines.append(
                f"| {int(shift['shift'])} | {row['Market']} | {row['Sector']} | "
                f"{float(row['ContributionDelta']):.2%} |"
            )
    lines.extend(["", "## Candidate Direction", "", f"- {summary['next_candidate_direction']}", ""])
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    shift_diagnostics = [
        _run_shift(
            shift=shift,
            universe=universe,
            price_cache=price_cache,
            flow_cache=flow_cache,
            monthly_close=monthly_close,
            signal_dates=signal_dates,
            cfg=cfg,
        )
        for shift in (1, 2)
    ]
    repeated_worst_symbols = sorted(
        set.intersection(*(set(row["Symbol"] for row in shift["worst_symbols"][:5]) for shift in shift_diagnostics))
    )
    repeated_worst_sectors = sorted(
        set.intersection(*(set(f"{row['Market']}::{row['Sector']}" for row in shift["worst_sectors"][:5]) for shift in shift_diagnostics))
    )
    summary = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "diagnostic_decision": "NEGATIVE_WF_CONTRIBUTION_DRIVERS_IDENTIFIED",
        "repeated_worst_symbols_top5": repeated_worst_symbols,
        "repeated_worst_sectors_top5": repeated_worst_sectors,
        "shift_diagnostics": shift_diagnostics,
        "next_candidate_direction": (
            "Test a no-date observable trigger that softens or redirects defense when the repeated negative drivers "
            "dominate candidate exposure after the state-condition defense fires."
        ),
        "safety": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "order_intent_created": False,
        },
    }
    (OUTPUT_DIR / "negative_wf_contribution_diagnostic_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "negative_wf_contribution_diagnostic.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
