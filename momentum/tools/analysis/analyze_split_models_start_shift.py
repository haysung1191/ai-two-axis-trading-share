from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from split_models.backtest import (
    BacktestConfig,
    _baseline_variant_map,
    _build_daily_caches,
    _build_monthly_close_matrix,
    _load_kr_universe,
    _load_us_universe,
    _run_trading_backtest_variant,
    _signal_dates,
    _summarize_returns,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_ranked_tail_start_shift_review"
BASELINE_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_risk_on"
CANDIDATE_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on"
SHIFT_STEP_MONTHS = 6
MAX_SHIFTS = 5


def _build_context() -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict[str, pd.DataFrame], pd.DataFrame]:
    us_stocks, us_etfs = _load_us_universe()
    kr_universe = _load_kr_universe()
    universe = pd.concat([us_stocks, us_etfs, kr_universe], ignore_index=True)
    price_cache, flow_cache = _build_daily_caches(universe)
    monthly_close = _build_monthly_close_matrix(universe, price_cache)
    return universe, price_cache, flow_cache, monthly_close


def _summarize_nav(nav: pd.DataFrame) -> dict[str, float | int | str]:
    rets = pd.to_numeric(nav["NetReturn"], errors="coerce").fillna(0.0)
    summary = _summarize_returns(rets, nav["NextDate"])
    return {
        "PeriodStart": str(pd.to_datetime(nav["SignalDate"]).min().date()),
        "PeriodEnd": str(pd.to_datetime(nav["NextDate"]).max().date()),
        "Months": int(len(nav)),
        "CAGR": float(summary["CAGR"]),
        "MDD": float(summary["MDD"]),
        "Sharpe": float(summary["Sharpe"]),
        "FinalNAV": float(summary["FinalNAV"]),
        "AnnualTurnover": float(pd.to_numeric(nav["Turnover"], errors="coerce").fillna(0.0).mean() * 12.0),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    universe, price_cache, flow_cache, monthly_close = _build_context()
    full_signal_dates = _signal_dates(monthly_close, BacktestConfig().signal_start)
    start_dates = [full_signal_dates[idx] for idx in range(0, min(len(full_signal_dates), SHIFT_STEP_MONTHS * MAX_SHIFTS), SHIFT_STEP_MONTHS)]
    variant_map = _baseline_variant_map()

    rows: list[dict[str, float | int | str]] = []
    for start_date in start_dates:
        cfg = BacktestConfig(signal_start=str(pd.Timestamp(start_date).date()))
        signal_dates = _signal_dates(monthly_close, cfg.signal_start)
        if len(signal_dates) < 24:
            continue
        baseline_nav = _run_trading_backtest_variant(
            universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant_map[BASELINE_VARIANT]
        )["nav"].copy()
        candidate_nav = _run_trading_backtest_variant(
            universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant_map[CANDIDATE_VARIANT]
        )["nav"].copy()

        baseline_summary = _summarize_nav(baseline_nav)
        candidate_summary = _summarize_nav(candidate_nav)
        rows.append(
            {
                "ShiftStart": str(pd.Timestamp(start_date).date()),
                "Months": int(candidate_summary["Months"]),
                "BaselineCAGR": float(baseline_summary["CAGR"]),
                "CandidateCAGR": float(candidate_summary["CAGR"]),
                "CAGRDelta": float(candidate_summary["CAGR"] - baseline_summary["CAGR"]),
                "BaselineSharpe": float(baseline_summary["Sharpe"]),
                "CandidateSharpe": float(candidate_summary["Sharpe"]),
                "SharpeDelta": float(candidate_summary["Sharpe"] - baseline_summary["Sharpe"]),
                "BaselineMDD": float(baseline_summary["MDD"]),
                "CandidateMDD": float(candidate_summary["MDD"]),
                "MDDDelta": float(candidate_summary["MDD"] - baseline_summary["MDD"]),
                "BaselineTurnover": float(baseline_summary["AnnualTurnover"]),
                "CandidateTurnover": float(candidate_summary["AnnualTurnover"]),
                "TurnoverDelta": float(candidate_summary["AnnualTurnover"] - baseline_summary["AnnualTurnover"]),
            }
        )

    compare = pd.DataFrame(rows)
    compare.to_csv(OUTPUT_DIR / "start_shift_compare.csv", index=False, encoding="utf-8-sig")

    summary = {
        "baseline_variant": BASELINE_VARIANT,
        "candidate_variant": CANDIDATE_VARIANT,
        "shifts_tested": int(len(compare)),
        "positive_cagr_shifts": int((pd.to_numeric(compare["CAGRDelta"], errors="coerce") > 0).sum()),
        "negative_cagr_shifts": int((pd.to_numeric(compare["CAGRDelta"], errors="coerce") < 0).sum()),
        "positive_sharpe_shifts": int((pd.to_numeric(compare["SharpeDelta"], errors="coerce") > 0).sum()),
        "negative_sharpe_shifts": int((pd.to_numeric(compare["SharpeDelta"], errors="coerce") < 0).sum()),
        "avg_cagr_delta": float(pd.to_numeric(compare["CAGRDelta"], errors="coerce").mean()),
        "avg_sharpe_delta": float(pd.to_numeric(compare["SharpeDelta"], errors="coerce").mean()),
        "best_shift_start": str(compare.sort_values("CAGRDelta", ascending=False).iloc[0]["ShiftStart"]),
        "worst_shift_start": str(compare.sort_values("CAGRDelta", ascending=True).iloc[0]["ShiftStart"]),
    }
    (OUTPUT_DIR / "start_shift_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
