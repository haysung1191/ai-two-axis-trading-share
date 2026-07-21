from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from split_models.backtest import BacktestConfig, _signal_dates, _summarize_returns
from tools.analysis.analyze_split_models_external_benchmarks import (
    _build_context,
    _build_xs_momentum_target_fn,
    _run_model_variant,
    _simulate_strategy,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_benchmark_start_shift_review"
MODEL_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
BENCHMARK_NAME = "benchmark_xs_mom_12_1_top5_eq"
SHIFT_STEP_MONTHS = 6
MAX_SHIFTS = 5


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
    base_cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, full_signal_dates = _build_context(base_cfg)
    start_dates = [full_signal_dates[idx] for idx in range(0, min(len(full_signal_dates), SHIFT_STEP_MONTHS * MAX_SHIFTS), SHIFT_STEP_MONTHS)]

    rows: list[dict[str, float | int | str]] = []
    for start_date in start_dates:
        cfg = BacktestConfig(signal_start=str(pd.Timestamp(start_date).date()))
        signal_dates = _signal_dates(monthly_close, cfg.signal_start)
        if len(signal_dates) < 24:
            continue
        model_nav = _run_model_variant(
            cfg,
            MODEL_VARIANT,
            universe,
            price_cache,
            flow_cache,
            monthly_close,
            signal_dates,
        )
        benchmark_fn = _build_xs_momentum_target_fn(
            universe,
            monthly_close,
            top_n=5,
            lookback_months=12,
            skip_recent_months=1,
            market=None,
            asset_type=None,
        )
        benchmark_nav = _simulate_strategy(signal_dates, monthly_close, benchmark_fn, cfg.one_way_cost_bps)

        model_summary = _summarize_nav(model_nav)
        benchmark_summary = _summarize_nav(benchmark_nav)
        rows.append(
            {
                "ShiftStart": str(pd.Timestamp(start_date).date()),
                "Months": int(model_summary["Months"]),
                "ModelCAGR": float(model_summary["CAGR"]),
                "BenchmarkCAGR": float(benchmark_summary["CAGR"]),
                "CAGRDelta": float(model_summary["CAGR"] - benchmark_summary["CAGR"]),
                "ModelSharpe": float(model_summary["Sharpe"]),
                "BenchmarkSharpe": float(benchmark_summary["Sharpe"]),
                "SharpeDelta": float(model_summary["Sharpe"] - benchmark_summary["Sharpe"]),
                "ModelMDD": float(model_summary["MDD"]),
                "BenchmarkMDD": float(benchmark_summary["MDD"]),
                "MDDDelta": float(model_summary["MDD"] - benchmark_summary["MDD"]),
            }
        )

    compare = pd.DataFrame(rows)
    compare.to_csv(OUTPUT_DIR / "benchmark_start_shift_compare.csv", index=False, encoding="utf-8-sig")

    summary = {
        "model_variant": MODEL_VARIANT,
        "benchmark_variant": BENCHMARK_NAME,
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
    (OUTPUT_DIR / "benchmark_start_shift_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
