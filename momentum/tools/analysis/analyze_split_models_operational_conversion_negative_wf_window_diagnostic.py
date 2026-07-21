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

from split_models.backtest import BacktestConfig, _baseline_variant_map, _run_trading_backtest_variant, _walkforward_summary
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_sweep import (
    BASELINE_VARIANT,
    STRONGEST_VARIANT,
)
from tools.analysis.analyze_split_models_operational_conversion_state_condition_defense_sweep import (
    _run_state_condition_defense,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import _build_context, _summarize_candidate


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_negative_wf_window_diagnostic"


def _walk_compare(candidate_nav: pd.DataFrame, base_nav: pd.DataFrame) -> list[dict[str, object]]:
    walk = _walkforward_summary(candidate_nav, window_months=24, step_months=12)
    base_walk = _walkforward_summary(base_nav, window_months=24, step_months=12)
    compare = walk[["WindowStart", "WindowEnd", "CAGR", "Sharpe"]].merge(
        base_walk[["WindowStart", "WindowEnd", "CAGR", "Sharpe"]],
        on=["WindowStart", "WindowEnd"],
        how="inner",
        suffixes=("_candidate", "_base"),
    )
    compare["CAGRDelta"] = pd.to_numeric(compare["CAGR_candidate"], errors="coerce") - pd.to_numeric(
        compare["CAGR_base"], errors="coerce"
    )
    compare["SharpeDelta"] = pd.to_numeric(compare["Sharpe_candidate"], errors="coerce") - pd.to_numeric(
        compare["Sharpe_base"], errors="coerce"
    )
    for column in ("WindowStart", "WindowEnd"):
        compare[column] = pd.to_datetime(compare[column]).dt.strftime("%Y-%m-%d")
    return compare.to_dict(orient="records")


def _monthly_compare(candidate_nav: pd.DataFrame, base_nav: pd.DataFrame, start: str, end: str) -> list[dict[str, object]]:
    left = candidate_nav[["SignalDate", "NextDate", "NetReturn"]].copy()
    right = base_nav[["SignalDate", "NextDate", "NetReturn"]].copy()
    for frame in (left, right):
        frame["SignalDate"] = pd.to_datetime(frame["SignalDate"])
        frame["NextDate"] = pd.to_datetime(frame["NextDate"])
    compare = left.merge(right, on=["SignalDate", "NextDate"], suffixes=("_candidate", "_base"))
    compare = compare[
        (compare["NextDate"] >= pd.Timestamp(start))
        & (compare["NextDate"] <= pd.Timestamp(end))
    ].copy()
    compare["Delta"] = pd.to_numeric(compare["NetReturn_candidate"], errors="coerce") - pd.to_numeric(
        compare["NetReturn_base"], errors="coerce"
    )
    for column in ("SignalDate", "NextDate"):
        compare[column] = compare[column].dt.strftime("%Y-%m-%d")
    return compare.sort_values("Delta").to_dict(orient="records")


def _run_shift(
    *,
    start_shift_months: int,
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
    shifted_dates = signal_dates[start_shift_months:]
    base_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, shifted_dates, cfg, strongest
    )
    variant_name = "negative_wf_diag_state_sym09_sector28_trim100_max08"
    candidate_result, diagnostics = _run_state_condition_defense(
        variant=replace(strongest, name=variant_name),
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
    summary_row = _summarize_candidate(variant_name, candidate_result, base_result)
    walk_rows = _walk_compare(candidate_result["nav"], base_result["nav"])
    negative_windows = [row for row in walk_rows if float(row["CAGRDelta"]) < 0]
    return {
        "start_shift_months": start_shift_months,
        "summary_row": summary_row,
        "diagnostics": diagnostics,
        "negative_windows": negative_windows,
        "all_walk_windows": walk_rows,
        "negative_window_months": [
            {
                "window_start": row["WindowStart"],
                "window_end": row["WindowEnd"],
                "monthly_rows": _monthly_compare(
                    candidate_result["nav"],
                    base_result["nav"],
                    str(row["WindowStart"]),
                    str(row["WindowEnd"]),
                ),
            }
            for row in negative_windows
        ],
    }


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Negative WF Window Diagnostic",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        f"- decision: `{summary['diagnostic_decision']}`",
        f"- negative shift ids: `{summary['negative_shift_ids']}`",
        "",
        "## Negative Windows",
        "",
        "| Shift | Window Start | Window End | Candidate CAGR | Base CAGR | CAGR Delta |",
        "| ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for shift in summary["shift_diagnostics"]:
        for row in shift["negative_windows"]:
            lines.append(
                f"| {int(shift['start_shift_months'])} | {row['WindowStart']} | {row['WindowEnd']} | "
                f"{float(row['CAGR_candidate']):.2%} | {float(row['CAGR_base']):.2%} | "
                f"{float(row['CAGRDelta']):.2%} |"
            )
    lines.extend(["", "## Safety", "", json.dumps(summary["safety"], indent=2), ""])
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    shift_diagnostics = [
        _run_shift(
            start_shift_months=shift,
            universe=universe,
            price_cache=price_cache,
            flow_cache=flow_cache,
            monthly_close=monthly_close,
            signal_dates=signal_dates,
            cfg=cfg,
        )
        for shift in [1, 2]
    ]
    negative_shift_ids = [
        int(row["start_shift_months"]) for row in shift_diagnostics if row["negative_windows"]
    ]
    summary = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "diagnostic_decision": "NEGATIVE_WF_WINDOWS_IDENTIFIED"
        if negative_shift_ids
        else "NO_NEGATIVE_WF_WINDOWS_FOUND",
        "negative_shift_ids": negative_shift_ids,
        "shift_diagnostics": shift_diagnostics,
        "safety": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "order_intent_created": False,
        },
    }
    (OUTPUT_DIR / "negative_wf_window_diagnostic_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "negative_wf_window_diagnostic.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
