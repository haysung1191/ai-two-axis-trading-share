from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models.backtest import BacktestConfig, _baseline_variant_map, _run_trading_backtest_variant
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    _build_context,
    _patch_tail_release_top50_mid50,
    _run_with_patch,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_drawdown"
BASELINE_VARIANT = "rule_breadth_it_us5_cap"
STRONGEST_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
CANDIDATE_VARIANT = "tail_release_top50_mid50"


def _prepare_nav(nav: pd.DataFrame) -> pd.DataFrame:
    out = nav.copy()
    out["SignalDate"] = pd.to_datetime(out["SignalDate"])
    out["NextDate"] = pd.to_datetime(out["NextDate"])
    out["NetReturn"] = pd.to_numeric(out["NetReturn"], errors="coerce").fillna(0.0)
    if "NAV" in out.columns:
        out["NAV"] = pd.to_numeric(out["NAV"], errors="coerce").fillna(0.0)
    else:
        out["NAV"] = (1.0 + out["NetReturn"]).cumprod()
    out["RunningPeak"] = out["NAV"].cummax()
    out["Drawdown"] = out["NAV"] / out["RunningPeak"] - 1.0
    return out


def _prepare_symbol_contrib(symbol_contrib: pd.DataFrame) -> pd.DataFrame:
    out = symbol_contrib.copy()
    out["SignalDate"] = pd.to_datetime(out["SignalDate"])
    out["NextDate"] = pd.to_datetime(out["NextDate"])
    out["Contribution"] = pd.to_numeric(out["Contribution"], errors="coerce").fillna(0.0)
    return out


def _drawdown_window(nav: pd.DataFrame) -> dict[str, object]:
    trough_idx = nav["Drawdown"].idxmin()
    trough = nav.loc[trough_idx]
    before = nav.loc[:trough_idx].copy()
    peak_value = float(before["RunningPeak"].max())
    peak_rows = before[before["NAV"] == peak_value]
    peak = peak_rows.iloc[-1]
    after = nav.loc[trough_idx + 1 :].copy()
    recovery = after[after["NAV"] >= peak_value]
    recovery_date = None if recovery.empty else recovery.iloc[0]["NextDate"]
    window = nav[(nav["SignalDate"] >= peak["SignalDate"]) & (nav["NextDate"] <= trough["NextDate"])].copy()
    return {
        "peak_signal_date": peak["SignalDate"],
        "peak_next_date": peak["NextDate"],
        "trough_signal_date": trough["SignalDate"],
        "trough_next_date": trough["NextDate"],
        "recovery_next_date": recovery_date,
        "peak_nav": float(peak["NAV"]),
        "trough_nav": float(trough["NAV"]),
        "max_drawdown": float(trough["Drawdown"]),
        "months": int(len(window)),
        "window_nav": window,
    }


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _monthly_gap_table(candidate_nav: pd.DataFrame, baseline_nav: pd.DataFrame, strongest_nav: pd.DataFrame) -> pd.DataFrame:
    merged = (
        candidate_nav[["SignalDate", "NextDate", "NetReturn", "Drawdown", "NAV"]]
        .rename(
            columns={
                "NetReturn": "CandidateNetReturn",
                "Drawdown": "CandidateDrawdown",
                "NAV": "CandidateNAV",
            }
        )
        .merge(
            baseline_nav[["SignalDate", "NextDate", "NetReturn", "Drawdown", "NAV"]].rename(
                columns={
                    "NetReturn": "BaselineNetReturn",
                    "Drawdown": "BaselineDrawdown",
                    "NAV": "BaselineNAV",
                }
            ),
            on=["SignalDate", "NextDate"],
            how="inner",
        )
        .merge(
            strongest_nav[["SignalDate", "NextDate", "NetReturn", "Drawdown", "NAV"]].rename(
                columns={
                    "NetReturn": "StrongestNetReturn",
                    "Drawdown": "StrongestDrawdown",
                    "NAV": "StrongestNAV",
                }
            ),
            on=["SignalDate", "NextDate"],
            how="inner",
        )
    )
    merged["CandidateVsBaselineReturnDelta"] = merged["CandidateNetReturn"] - merged["BaselineNetReturn"]
    merged["CandidateVsStrongestReturnDelta"] = merged["CandidateNetReturn"] - merged["StrongestNetReturn"]
    merged["CandidateVsBaselineDrawdownGap"] = merged["CandidateDrawdown"] - merged["BaselineDrawdown"]
    merged["CandidateVsStrongestDrawdownGap"] = merged["CandidateDrawdown"] - merged["StrongestDrawdown"]
    return merged.sort_values("CandidateVsBaselineReturnDelta")


def _window_symbol_delta(
    candidate_symbol: pd.DataFrame,
    baseline_symbol: pd.DataFrame,
    strongest_symbol: pd.DataFrame,
    start_signal: pd.Timestamp,
    end_next: pd.Timestamp,
) -> pd.DataFrame:
    candidate_window = candidate_symbol[
        (candidate_symbol["SignalDate"] >= start_signal) & (candidate_symbol["NextDate"] <= end_next)
    ].copy()
    baseline_window = baseline_symbol[
        (baseline_symbol["SignalDate"] >= start_signal) & (baseline_symbol["NextDate"] <= end_next)
    ].copy()
    strongest_window = strongest_symbol[
        (strongest_symbol["SignalDate"] >= start_signal) & (strongest_symbol["NextDate"] <= end_next)
    ].copy()

    merged = (
        candidate_window.groupby(["Market", "Sector", "Symbol"], as_index=False)
        .agg(CandidateContribution=("Contribution", "sum"))
        .merge(
            baseline_window.groupby(["Market", "Sector", "Symbol"], as_index=False).agg(
                BaselineContribution=("Contribution", "sum")
            ),
            on=["Market", "Sector", "Symbol"],
            how="outer",
        )
        .merge(
            strongest_window.groupby(["Market", "Sector", "Symbol"], as_index=False).agg(
                StrongestContribution=("Contribution", "sum")
            ),
            on=["Market", "Sector", "Symbol"],
            how="outer",
        )
        .fillna(0.0)
    )
    merged["CandidateVsBaselineDelta"] = merged["CandidateContribution"] - merged["BaselineContribution"]
    merged["CandidateVsStrongestDelta"] = merged["CandidateContribution"] - merged["StrongestContribution"]
    return merged.sort_values("CandidateVsBaselineDelta")


def _window_sector_delta(symbol_delta: pd.DataFrame) -> pd.DataFrame:
    sector = (
        symbol_delta.groupby(["Market", "Sector"], as_index=False)
        .agg(
            CandidateContribution=("CandidateContribution", "sum"),
            BaselineContribution=("BaselineContribution", "sum"),
            StrongestContribution=("StrongestContribution", "sum"),
            CandidateVsBaselineDelta=("CandidateVsBaselineDelta", "sum"),
            CandidateVsStrongestDelta=("CandidateVsStrongestDelta", "sum"),
        )
        .sort_values("CandidateVsBaselineDelta")
    )
    return sector


def _top_records(df: pd.DataFrame, column: str, n: int, ascending: bool) -> list[dict[str, object]]:
    rows = df.sort_values(column, ascending=ascending).head(n).copy()
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
        "# Split Models Operational Conversion Drawdown Diagnostic",
        "",
        "## Purpose",
        "",
        "- explain why the current best operating-conversion watch is still blocked on drawdown",
        "- isolate the candidate's worst drawdown window and the main symbol / sector deltas behind it",
        "",
        "## Current Read",
        "",
        f"- operating baseline: `{summary['baseline_variant']}`",
        f"- aggressive strongest: `{summary['strongest_variant']}`",
        f"- conversion watch under review: `{summary['candidate_variant']}`",
        f"- candidate max drawdown: `{_fmt_pct(summary['candidate_max_drawdown'])}`",
        f"- baseline max drawdown: `{_fmt_pct(summary['baseline_max_drawdown'])}`",
        f"- strongest max drawdown: `{_fmt_pct(summary['strongest_max_drawdown'])}`",
        f"- candidate drawdown gap vs baseline: `{_fmt_pct(summary['candidate_drawdown_gap_vs_baseline'])}`",
        f"- candidate drawdown gap vs strongest: `{_fmt_pct(summary['candidate_drawdown_gap_vs_strongest'])}`",
        "",
        "## Worst Candidate Drawdown Window",
        "",
        f"- peak month: `{summary['candidate_drawdown_window']['peak_next_date']}`",
        f"- trough month: `{summary['candidate_drawdown_window']['trough_next_date']}`",
        f"- recovery month: `{summary['candidate_drawdown_window']['recovery_next_date']}`",
        f"- window length: `{summary['candidate_drawdown_window']['months']}` months",
        "",
        "## Worst Candidate-vs-Baseline Months",
        "",
        "| Rank | NextDate | Candidate | Baseline | Delta | Candidate DD | Baseline DD |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for idx, row in enumerate(summary["worst_candidate_vs_baseline_months"], start=1):
        lines.append(
            f"| {idx} | `{row['NextDate']}` | {_fmt_pct(row['CandidateNetReturn'])} | {_fmt_pct(row['BaselineNetReturn'])} | "
            f"{_fmt_pct(row['CandidateVsBaselineReturnDelta'])} | {_fmt_pct(row['CandidateDrawdown'])} | {_fmt_pct(row['BaselineDrawdown'])} |"
        )

    lines.extend(
        [
            "",
            "## Worst Candidate-vs-Baseline Symbols In Candidate Drawdown Window",
            "",
            "| Rank | Symbol | Market | Sector | Candidate-Baseline Delta | Candidate-Strongest Delta |",
            "| --- | --- | --- | --- | ---: | ---: |",
        ]
    )

    for idx, row in enumerate(summary["worst_symbol_deltas_vs_baseline"], start=1):
        lines.append(
            f"| {idx} | `{row['Symbol']}` | `{row['Market']}` | `{row['Sector']}` | "
            f"{_fmt_pct(row['CandidateVsBaselineDelta'])} | {_fmt_pct(row['CandidateVsStrongestDelta'])} |"
        )

    lines.extend(
        [
            "",
            "## Sector Pressure In Candidate Drawdown Window",
            "",
            "| Rank | Market | Sector | Candidate-Baseline Delta | Candidate-Strongest Delta |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )

    for idx, row in enumerate(summary["worst_sector_deltas_vs_baseline"], start=1):
        lines.append(
            f"| {idx} | `{row['Market']}` | `{row['Sector']}` | "
            f"{_fmt_pct(row['CandidateVsBaselineDelta'])} | {_fmt_pct(row['CandidateVsStrongestDelta'])} |"
        )

    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"- {summary['verdict']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    variants = _baseline_variant_map()
    baseline = variants[BASELINE_VARIANT]
    strongest = variants[STRONGEST_VARIANT]

    baseline_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, baseline
    )
    strongest_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, strongest
    )
    candidate_result = _run_with_patch(
        strongest,
        _patch_tail_release_top50_mid50(),
        universe,
        price_cache,
        flow_cache,
        monthly_close,
        signal_dates,
        cfg,
    )

    baseline_nav = _prepare_nav(baseline_result["nav"])
    strongest_nav = _prepare_nav(strongest_result["nav"])
    candidate_nav = _prepare_nav(candidate_result["nav"])

    baseline_symbol = _prepare_symbol_contrib(baseline_result["symbol_contrib"])
    strongest_symbol = _prepare_symbol_contrib(strongest_result["symbol_contrib"])
    candidate_symbol = _prepare_symbol_contrib(candidate_result["symbol_contrib"])

    candidate_window = _drawdown_window(candidate_nav)
    baseline_window = _drawdown_window(baseline_nav)
    strongest_window = _drawdown_window(strongest_nav)

    monthly_gap = _monthly_gap_table(candidate_nav, baseline_nav, strongest_nav)
    symbol_delta = _window_symbol_delta(
        candidate_symbol,
        baseline_symbol,
        strongest_symbol,
        candidate_window["peak_signal_date"],
        candidate_window["trough_next_date"],
    )
    sector_delta = _window_sector_delta(symbol_delta)

    monthly_gap_export = monthly_gap.copy()
    for column in ["SignalDate", "NextDate"]:
        monthly_gap_export[column] = monthly_gap_export[column].dt.strftime("%Y-%m-%d")
    monthly_gap_export.to_csv(
        OUTPUT_DIR / "candidate_vs_baseline_monthly_gap.csv", index=False, encoding="utf-8-sig"
    )

    symbol_delta_export = symbol_delta.copy()
    symbol_delta_export.to_csv(
        OUTPUT_DIR / "candidate_drawdown_window_symbol_delta.csv", index=False, encoding="utf-8-sig"
    )

    sector_delta_export = sector_delta.copy()
    sector_delta_export.to_csv(
        OUTPUT_DIR / "candidate_drawdown_window_sector_delta.csv", index=False, encoding="utf-8-sig"
    )

    summary = {
        "baseline_variant": BASELINE_VARIANT,
        "strongest_variant": STRONGEST_VARIANT,
        "candidate_variant": CANDIDATE_VARIANT,
        "candidate_max_drawdown": float(candidate_window["max_drawdown"]),
        "baseline_max_drawdown": float(baseline_window["max_drawdown"]),
        "strongest_max_drawdown": float(strongest_window["max_drawdown"]),
        "candidate_drawdown_gap_vs_baseline": float(candidate_window["max_drawdown"] - baseline_window["max_drawdown"]),
        "candidate_drawdown_gap_vs_strongest": float(candidate_window["max_drawdown"] - strongest_window["max_drawdown"]),
        "candidate_drawdown_window": {
            "peak_next_date": candidate_window["peak_next_date"].strftime("%Y-%m-%d"),
            "trough_next_date": candidate_window["trough_next_date"].strftime("%Y-%m-%d"),
            "recovery_next_date": None
            if candidate_window["recovery_next_date"] is None
            else candidate_window["recovery_next_date"].strftime("%Y-%m-%d"),
            "months": candidate_window["months"],
        },
        "worst_candidate_vs_baseline_months": _top_records(
            monthly_gap.assign(
                SignalDate=monthly_gap["SignalDate"].dt.strftime("%Y-%m-%d"),
                NextDate=monthly_gap["NextDate"].dt.strftime("%Y-%m-%d"),
            ),
            "CandidateVsBaselineReturnDelta",
            6,
            True,
        ),
        "worst_symbol_deltas_vs_baseline": _top_records(symbol_delta, "CandidateVsBaselineDelta", 8, True),
        "worst_sector_deltas_vs_baseline": _top_records(sector_delta, "CandidateVsBaselineDelta", 6, True),
    }

    worst_month = summary["worst_candidate_vs_baseline_months"][0] if summary["worst_candidate_vs_baseline_months"] else None
    worst_symbol = summary["worst_symbol_deltas_vs_baseline"][0] if summary["worst_symbol_deltas_vs_baseline"] else None
    second_worst_symbol = (
        summary["worst_symbol_deltas_vs_baseline"][1]
        if len(summary["worst_symbol_deltas_vs_baseline"]) > 1
        else None
    )
    symbol_suffix = "" if second_worst_symbol is None else f" and {second_worst_symbol['Symbol']}"
    summary["verdict"] = (
        f"`{CANDIDATE_VARIANT}` still fails direct operating conversion because its worst drawdown window "
        f"extends drawdown by {_fmt_pct(abs(summary['candidate_drawdown_gap_vs_baseline']))} versus baseline; "
        f"the worst candidate-vs-baseline month is `{worst_month['NextDate']}` "
        f"and the main symbol drags in that drawdown regime are {worst_symbol['Symbol']}{symbol_suffix}."
        if worst_month and worst_symbol
        else f"`{CANDIDATE_VARIANT}` still fails direct operating conversion because its drawdown remains materially worse than baseline."
    )

    (OUTPUT_DIR / "operational_conversion_drawdown_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "operational_conversion_drawdown.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
