from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.analysis.analyze_split_models_external_benchmarks import (
    _build_context,
    _build_xs_momentum_target_fn,
    _run_model_variant,
    _simulate_strategy,
)
from split_models.backtest import BacktestConfig, _walkforward_summary



ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_benchmark_walkforward_review"
PAIR_CONFIGS = [
    {
        "label": "baseline_vs_us_stock_xs_mom",
        "model": "rule_breadth_it_us5_cap",
        "benchmark": "benchmark_xs_mom_12_1_us_stock_top5_eq",
        "benchmark_top_n": 5,
        "benchmark_market": "US",
        "benchmark_asset_type": "STOCK",
    },
    {
        "label": "aggressive_vs_full_xs_mom",
        "model": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
        "benchmark": "benchmark_xs_mom_12_1_top5_eq",
        "benchmark_top_n": 5,
        "benchmark_market": None,
        "benchmark_asset_type": None,
    },
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)

    compare_rows: list[pd.DataFrame] = []
    summary: dict[str, dict[str, float | int | str]] = {}

    for pair in PAIR_CONFIGS:
        model_name = str(pair["model"])
        benchmark_name = str(pair["benchmark"])
        label = str(pair["label"])

        model_nav = _run_model_variant(
            cfg,
            model_name,
            universe,
            price_cache,
            flow_cache,
            monthly_close,
            signal_dates,
        )
        benchmark_fn = _build_xs_momentum_target_fn(
            universe,
            monthly_close,
            top_n=int(pair["benchmark_top_n"]),
            lookback_months=12,
            skip_recent_months=1,
            market=pair["benchmark_market"],
            asset_type=pair["benchmark_asset_type"],
        )
        benchmark_nav = _simulate_strategy(signal_dates, monthly_close, benchmark_fn, cfg.one_way_cost_bps)

        model_walk = _walkforward_summary(model_nav, window_months=24, step_months=12).rename(
            columns={"CAGR": "ModelCAGR", "Sharpe": "ModelSharpe", "MDD": "ModelMDD"}
        )
        benchmark_walk = _walkforward_summary(benchmark_nav, window_months=24, step_months=12).rename(
            columns={"CAGR": "BenchmarkCAGR", "Sharpe": "BenchmarkSharpe", "MDD": "BenchmarkMDD"}
        )
        for df in (model_walk, benchmark_walk):
            df["WindowStart"] = pd.to_datetime(df["WindowStart"], errors="coerce").dt.strftime("%Y-%m-%d")
            df["WindowEnd"] = pd.to_datetime(df["WindowEnd"], errors="coerce").dt.strftime("%Y-%m-%d")

        merged = model_walk.merge(
            benchmark_walk[["WindowStart", "WindowEnd", "BenchmarkCAGR", "BenchmarkSharpe", "BenchmarkMDD"]],
            on=["WindowStart", "WindowEnd"],
            how="inner",
        )
        merged.insert(0, "Label", label)
        merged.insert(1, "Model", model_name)
        merged.insert(2, "Benchmark", benchmark_name)
        merged["CAGRDelta"] = pd.to_numeric(merged["ModelCAGR"], errors="coerce") - pd.to_numeric(
            merged["BenchmarkCAGR"], errors="coerce"
        )
        merged["SharpeDelta"] = pd.to_numeric(merged["ModelSharpe"], errors="coerce") - pd.to_numeric(
            merged["BenchmarkSharpe"], errors="coerce"
        )
        merged["MDDDelta"] = pd.to_numeric(merged["ModelMDD"], errors="coerce") - pd.to_numeric(
            merged["BenchmarkMDD"], errors="coerce"
        )
        compare_rows.append(merged)

        merged.to_csv(OUTPUT_DIR / f"{label}_walkforward_compare.csv", index=False, encoding="utf-8-sig")

        summary[label] = {
            "model": model_name,
            "benchmark": benchmark_name,
            "windows_compared": int(len(merged)),
            "positive_cagr_windows": int((pd.to_numeric(merged["CAGRDelta"], errors="coerce") > 0).sum()),
            "negative_cagr_windows": int((pd.to_numeric(merged["CAGRDelta"], errors="coerce") < 0).sum()),
            "avg_cagr_delta": float(pd.to_numeric(merged["CAGRDelta"], errors="coerce").mean()),
            "avg_sharpe_delta": float(pd.to_numeric(merged["SharpeDelta"], errors="coerce").mean()),
            "avg_mdd_delta": float(pd.to_numeric(merged["MDDDelta"], errors="coerce").mean()),
            "best_cagr_delta_window": None
            if merged.empty
            else str(
                merged.loc[pd.to_numeric(merged["CAGRDelta"], errors="coerce").idxmax(), "WindowStart"]
            )
            + " -> "
            + str(merged.loc[pd.to_numeric(merged["CAGRDelta"], errors="coerce").idxmax(), "WindowEnd"]),
            "worst_cagr_delta_window": None
            if merged.empty
            else str(
                merged.loc[pd.to_numeric(merged["CAGRDelta"], errors="coerce").idxmin(), "WindowStart"]
            )
            + " -> "
            + str(merged.loc[pd.to_numeric(merged["CAGRDelta"], errors="coerce").idxmin(), "WindowEnd"]),
        }

    compare_df = pd.concat(compare_rows, ignore_index=True)
    compare_df.to_csv(OUTPUT_DIR / "benchmark_walkforward_compare.csv", index=False, encoding="utf-8-sig")
    (OUTPUT_DIR / "benchmark_walkforward_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()


