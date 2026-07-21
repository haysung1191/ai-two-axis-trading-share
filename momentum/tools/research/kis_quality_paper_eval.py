import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import argparse
import os
from typing import Dict

import pandas as pd

from kis_backtest_from_prices import build_market_matrices, run_one
from kis_cost_sensitivity import parse_roundtrip_costs
from kis_flow_data import build_flow_matrices
from kis_quality_backfill import list_stock_codes
from kis_quality_data import build_quality_matrices, default_quality_base
from kis_shadow_common import build_strategy
from kis_walkforward import build_windows, choose_feasible_window_params, run_test_with_warmup


def summarize_quality_coverage(quality_base: str) -> pd.DataFrame:
    root = os.path.join(quality_base, "stock")
    rows = []
    for code in list_stock_codes("data/prices_operating_institutional_v1"):
        path = os.path.join(root, f"{code}.csv.gz")
        if not os.path.exists(path):
            rows.append({"Code": code, "Status": "MISSING"})
            continue
        df = pd.read_csv(path, compression="gzip", parse_dates=["effective_date", "period_end"])
        rows.append(
            {
                "Code": code,
                "Status": "OK",
                "Rows": int(len(df)),
                "CoverageStart": str(df["effective_date"].min().date()) if not df.empty else "",
                "CoverageEnd": str(df["effective_date"].max().date()) if not df.empty else "",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    p = argparse.ArgumentParser(description="Evaluate Weekly QualityProfitability MVP on current Korea operating universe.")
    p.add_argument("--base", type=str, default="data/prices_operating_institutional_v1")
    p.add_argument("--quality-base", type=str, default=default_quality_base())
    p.add_argument("--save-dir", type=str, default="backtests/quality_eval_20260328")
    p.add_argument("--manifest-path", type=str, default=None)
    p.add_argument("--max-files", type=int, default=0)
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--roundtrip-costs", type=str, default="0.50")
    args = p.parse_args()

    os.makedirs(args.save_dir, exist_ok=True)

    close_s, value_s = build_market_matrices(args.base, "stock", args.max_files)
    close_e, value_e = build_market_matrices(args.base, "etf", args.max_files)
    idx = close_s.index.intersection(close_e.index).sort_values()
    close_s = close_s.loc[idx]
    close_e = close_e.loc[idx]
    value_s = value_s.loc[idx, close_s.columns]
    value_e = value_e.loc[idx, close_e.columns]
    flow_mats = build_flow_matrices("data/flows_naver_8y", market="stock", max_files=args.max_files)
    quality_mats = build_quality_matrices(args.quality_base, close_s.index, list(close_s.columns))

    coverage = summarize_quality_coverage(args.quality_base)
    coverage.to_csv(os.path.join(args.save_dir, "quality_coverage.csv"), index=False, encoding="utf-8-sig")

    gross = build_strategy("Weekly QualityProfitability MVP", fee_rate=0.0, manifest_path=args.manifest_path)
    out_g, m_g = run_one(
        close_s,
        close_e,
        gross,
        min_common_dates=args.min_common_dates,
        traded_value_s=value_s,
        traded_value_e=value_e,
        flow_mats=flow_mats,
        quality_mats=quality_mats,
    )

    cost_rows = []
    for rt_pct in parse_roundtrip_costs(args.roundtrip_costs):
        stg = build_strategy("Weekly QualityProfitability MVP", fee_rate=(rt_pct / 100.0) / 2.0, manifest_path=args.manifest_path)
        _, m_c = run_one(
            close_s,
            close_e,
            stg,
            min_common_dates=args.min_common_dates,
            traded_value_s=value_s,
            traded_value_e=value_e,
            flow_mats=flow_mats,
            quality_mats=quality_mats,
        )
        cost_rows.append(
            {
                "Strategy": stg.name,
                "RoundtripCostPct": rt_pct,
                "CAGR_net": float(m_c["CAGR"]),
                "MDD_net": float(m_c["MDD"]),
                "Sharpe_net": float(m_c["Sharpe"]),
                "AnnualTurnover": float(m_c.get("AnnualTurnover", 0.0)),
            }
        )

    train_years, test_years, step_years, _ = choose_feasible_window_params(close_s.index, 8, 2, 1, 3)
    windows = build_windows(close_s.index, train_years=train_years, test_years=test_years, step_years=step_years)
    wf_rows = []
    for _, _, test_start, test_end in windows:
        m_test, _ = run_test_with_warmup(
            close_s,
            close_e,
            value_s,
            value_e,
            flow_mats,
            quality_mats,
            test_start=test_start,
            test_end=test_end,
            stg=gross,
            min_common_dates=max(80, args.min_common_dates // 2),
        )
        wf_rows.append(
            {
                "WindowStart": str(test_start.date()),
                "WindowEnd": str(test_end.date()),
                "StrategyName": gross.name,
                "CAGR_net": float(m_test["CAGR"]),
                "MDD": float(m_test["MDD"]),
                "Sharpe": float(m_test["Sharpe"]),
            }
        )

    wf_df = pd.DataFrame(wf_rows)
    wf_summary: Dict[str, float] = {
        "StrategyName": gross.name,
        "WindowCount": int(len(wf_df)),
        "MedianCAGR": float(wf_df["CAGR_net"].median()) if not wf_df.empty else float("nan"),
        "WorstCAGR": float(wf_df["CAGR_net"].min()) if not wf_df.empty else float("nan"),
        "WorstMDD": float(wf_df["MDD"].min()) if not wf_df.empty else float("nan"),
        "CAGRStd": float(wf_df["CAGR_net"].std(ddof=0)) if len(wf_df) > 1 else float("nan"),
    }

    summary = pd.DataFrame(
        [
            {
                "Strategy": gross.name,
                "BaselineCAGR": float(m_g["CAGR"]),
                "BaselineMDD": float(m_g["MDD"]),
                "BaselineSharpe": float(m_g["Sharpe"]),
                "AnnualTurnover": float(m_g.get("AnnualTurnover", 0.0)),
                "CoverageStart": str(coverage.loc[coverage["Status"] == "OK", "CoverageStart"].min()) if not coverage.empty else "",
                "CoverageEnd": str(coverage.loc[coverage["Status"] == "OK", "CoverageEnd"].max()) if not coverage.empty else "",
            }
        ]
    )

    out_g.reset_index().to_csv(os.path.join(args.save_dir, "quality_nav.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(cost_rows).to_csv(os.path.join(args.save_dir, "quality_cost.csv"), index=False, encoding="utf-8-sig")
    wf_df.to_csv(os.path.join(args.save_dir, "quality_walkforward_results.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame([wf_summary]).to_csv(os.path.join(args.save_dir, "quality_walkforward_summary.csv"), index=False, encoding="utf-8-sig")
    summary.to_csv(os.path.join(args.save_dir, "quality_eval_summary.csv"), index=False, encoding="utf-8-sig")
    print(summary.to_string(index=False))
    print(pd.DataFrame(cost_rows).to_string(index=False))
    print(pd.DataFrame([wf_summary]).to_string(index=False))


if __name__ == "__main__":
    main()
