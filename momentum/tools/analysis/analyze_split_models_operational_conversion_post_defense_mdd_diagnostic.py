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
from tools.analysis.analyze_split_models_operational_conversion_post_defense_cooldown_sweep import (
    _run_post_defense_cooldown,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import _build_context


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_post_defense_mdd_diagnostic"


def _drawdown_summary(nav: pd.DataFrame) -> dict[str, object]:
    frame = nav.copy()
    frame["NextDate"] = pd.to_datetime(frame["NextDate"])
    frame["NAV"] = pd.to_numeric(frame["NAV"], errors="coerce")
    frame["PeakNAV"] = frame["NAV"].cummax()
    frame["Drawdown"] = frame["NAV"] / frame["PeakNAV"] - 1.0
    trough_idx = frame["Drawdown"].idxmin()
    trough = frame.loc[trough_idx]
    peak_frame = frame.loc[:trough_idx]
    peak_idx = peak_frame["NAV"].idxmax()
    peak = frame.loc[peak_idx]
    window = frame[(frame["NextDate"] >= peak["NextDate"]) & (frame["NextDate"] <= trough["NextDate"])].copy()
    for date_column in ("SignalDate", "NextDate"):
        window[date_column] = pd.to_datetime(window[date_column]).dt.strftime("%Y-%m-%d")
    return {
        "peak_next_date": pd.Timestamp(peak["NextDate"]).strftime("%Y-%m-%d"),
        "trough_next_date": pd.Timestamp(trough["NextDate"]).strftime("%Y-%m-%d"),
        "mdd": float(trough["Drawdown"]),
        "peak_nav": float(peak["NAV"]),
        "trough_nav": float(trough["NAV"]),
        "window_months": window[["SignalDate", "NextDate", "NetReturn", "Turnover", "NAV", "Drawdown"]].to_dict(
            orient="records"
        ),
        "worst_window_months": window.sort_values("NetReturn").head(8)[
            ["SignalDate", "NextDate", "NetReturn", "Turnover", "NAV", "Drawdown"]
        ].to_dict(orient="records"),
    }


def _position_rows(result: dict[str, pd.DataFrame], signal_dates: list[str]) -> list[dict[str, object]]:
    positions = result["positions"].copy()
    if positions.empty:
        return []
    positions = positions[positions["SignalDate"].astype(str).isin(signal_dates)].copy()
    positions["TargetWeight"] = pd.to_numeric(positions["TargetWeight"], errors="coerce").fillna(0.0)
    positions["NextMonthReturn"] = pd.to_numeric(positions["NextMonthReturn"], errors="coerce").fillna(0.0)
    positions["Contribution"] = pd.to_numeric(positions["Contribution"], errors="coerce").fillna(0.0)
    rows: list[dict[str, object]] = []
    for signal_date, group in positions.groupby("SignalDate"):
        top_weight = group.sort_values("TargetWeight", ascending=False).head(8)
        worst_contrib = group.sort_values("Contribution").head(8)
        sector = (
            group.groupby(["Market", "Sector"], as_index=False)
            .agg(TargetWeight=("TargetWeight", "sum"), Contribution=("Contribution", "sum"))
            .sort_values("Contribution")
        )
        rows.append(
            {
                "signal_date": signal_date,
                "top_weight_positions": top_weight[
                    ["Market", "Sector", "Symbol", "TargetWeight", "NextMonthReturn", "Contribution"]
                ].to_dict(orient="records"),
                "worst_contribution_positions": worst_contrib[
                    ["Market", "Sector", "Symbol", "TargetWeight", "NextMonthReturn", "Contribution"]
                ].to_dict(orient="records"),
                "sector_contribution": sector.to_dict(orient="records"),
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
    result, diagnostics = _run_post_defense_cooldown(
        variant=replace(strongest, name="post_defense_mdd_diag_raw_m2_ex100"),
        fallback_variant=baseline,
        cooldown_months=2,
        cooldown_mode="raw",
        cooldown_exposure=1.0,
        universe=universe,
        price_cache=price_cache,
        flow_cache=flow_cache,
        monthly_close=monthly_close,
        signal_dates=shifted_dates,
        cfg=cfg,
    )
    dd = _drawdown_summary(result["nav"])
    worst_signal_dates = sorted({str(row["SignalDate"]) for row in dd["worst_window_months"]})
    return {
        "shift": shift,
        "diagnostics": diagnostics,
        "drawdown": dd,
        "worst_month_positions": _position_rows(result, worst_signal_dates),
    }


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Post-Defense MDD Diagnostic",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        f"- decision: `{summary['diagnostic_decision']}`",
        "",
        "## Drawdown Windows",
        "",
        "| Shift | Peak | Trough | MDD |",
        "| ---: | --- | --- | ---: |",
    ]
    for row in summary["shift_diagnostics"]:
        dd = row["drawdown"]
        lines.append(
            f"| {int(row['shift'])} | {dd['peak_next_date']} | {dd['trough_next_date']} | {float(dd['mdd']):.2%} |"
        )
    lines.extend(["", "## Safety", "", json.dumps(summary["safety"], indent=2), ""])
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
        for shift in [0, 1, 2]
    ]
    summary = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "diagnostic_decision": "POST_DEFENSE_MDD_DRIVERS_IDENTIFIED",
        "shift_diagnostics": shift_diagnostics,
        "safety": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "order_intent_created": False,
        },
    }
    (OUTPUT_DIR / "post_defense_mdd_diagnostic_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "post_defense_mdd_diagnostic.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
