import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import pandas as pd

from kis_backtest_from_prices import blend_strategy_results, build_market_matrices
from kis_flow_data import build_flow_matrices
from kis_shadow_common import build_strategy
from kis_walkforward import build_windows, choose_feasible_window_params, run_hybrid_test_with_warmup, run_test_with_warmup
from kis_backtest_from_prices import run_one


def main() -> None:
    base = "data/prices_operating_institutional_v1"
    save_dir = Path("backtests/flow_v3_eval_20260328")
    save_dir.mkdir(parents=True, exist_ok=True)

    close_s, value_s = build_market_matrices(base, "stock", 0)
    close_e, value_e = build_market_matrices(base, "etf", 0)
    common = close_s.index.intersection(close_e.index).sort_values()
    close_s = close_s.loc[common]
    close_e = close_e.loc[common]
    value_s = value_s.loc[common, close_s.columns]
    value_e = value_e.loc[common, close_e.columns]
    flow_mats = build_flow_matrices("data/flows_naver_8y", market="stock", max_files=0)

    strategy_names = [
        "Weekly ForeignFlow v2",
        "Weekly ForeignFlow v3",
        "Weekly Score50 RegimeState",
    ]
    component_results = {}
    baseline_rows = []
    cost_rows = []
    fee_net = 0.005 / 2.0
    for name in strategy_names:
        stg_g = build_strategy(name, fee_rate=0.0)
        _, m_g = run_one(
            close_s,
            close_e,
            stg_g,
            min_common_dates=180,
            traded_value_s=value_s,
            traded_value_e=value_e,
            flow_mats=flow_mats,
        )
        stg_n = build_strategy(name, fee_rate=fee_net)
        out_n, m_n = run_one(
            close_s,
            close_e,
            stg_n,
            min_common_dates=180,
            traded_value_s=value_s,
            traded_value_e=value_e,
            flow_mats=flow_mats,
        )
        component_results[name] = (out_n, m_n)
        baseline_rows.append(
            {
                "Strategy": name,
                "BaselineCAGR": float(m_g["CAGR"]),
                "BaselineMDD": float(m_g["MDD"]),
                "BaselineSharpe": float(m_g["Sharpe"]),
                "AnnualTurnover": float(m_g.get("AnnualTurnover", 0.0)),
            }
        )
        cost_rows.append(
            {
                "Strategy": name,
                "CAGR_net_0.5pct": float(m_n["CAGR"]),
                "MDD_net_0.5pct": float(m_n["MDD"]),
                "Sharpe_net_0.5pct": float(m_n["Sharpe"]),
                "AnnualTurnover_net": float(m_n.get("AnnualTurnover", 0.0)),
            }
        )

    hybrid_name = "Weekly Hybrid FV350 RS50"
    out_h, m_h = blend_strategy_results(hybrid_name, component_results)
    cost_rows.append(
        {
            "Strategy": hybrid_name,
            "CAGR_net_0.5pct": float(m_h["CAGR"]),
            "MDD_net_0.5pct": float(m_h["MDD"]),
            "Sharpe_net_0.5pct": float(m_h["Sharpe"]),
            "AnnualTurnover_net": float(m_h.get("AnnualTurnover", 0.0)),
        }
    )

    idx = close_s.index
    train_years, test_years, step_years, _ = choose_feasible_window_params(idx, 8, 2, 1, 3)
    windows = build_windows(idx, train_years, test_years, step_years)
    wf_rows = []
    for name in strategy_names:
        stg = build_strategy(name, fee_rate=fee_net)
        for _, _, ts, te in windows:
            m_short, _ = run_test_with_warmup(
                close_s,
                close_e,
                value_s,
                value_e,
                flow_mats,
                None,
                test_start=ts,
                test_end=te,
                stg=stg,
                min_common_dates=90,
            )
            wf_rows.append(
                {
                    "Strategy": name,
                    "TestStart": str(ts.date()),
                    "TestEnd": str(te.date()),
                    "CAGR_net": float(m_short["CAGR"]),
                    "MDD": float(m_short["MDD"]),
                    "Sharpe": float(m_short["Sharpe"]),
                }
            )

    named_map = {
        "Weekly ForeignFlow v3": build_strategy("Weekly ForeignFlow v3", fee_rate=fee_net),
        "Weekly Score50 RegimeState": build_strategy("Weekly Score50 RegimeState", fee_rate=fee_net),
    }
    for _, _, ts, te in windows:
        m_short, _ = run_hybrid_test_with_warmup(
            close_s,
            close_e,
            value_s,
            value_e,
            flow_mats,
            None,
            test_start=ts,
            test_end=te,
            strategy_name=hybrid_name,
            named_strategy_map=named_map,
            min_common_dates=90,
        )
        wf_rows.append(
            {
                "Strategy": hybrid_name,
                "TestStart": str(ts.date()),
                "TestEnd": str(te.date()),
                "CAGR_net": float(m_short["CAGR"]),
                "MDD": float(m_short["MDD"]),
                "Sharpe": float(m_short["Sharpe"]),
            }
        )

    baseline_df = pd.DataFrame(baseline_rows)
    cost_df = pd.DataFrame(cost_rows)
    wf_df = pd.DataFrame(wf_rows)
    wf_summary = (
        wf_df.groupby("Strategy")
        .agg(
            WindowCount=("CAGR_net", "size"),
            MedianCAGR=("CAGR_net", "median"),
            WorstCAGR=("CAGR_net", "min"),
            WorstMDD=("MDD", "min"),
            MedianSharpe=("Sharpe", "median"),
        )
        .reset_index()
    )
    merged = baseline_df.merge(cost_df, on="Strategy", how="outer").merge(wf_summary, on="Strategy", how="outer")

    baseline_df.to_csv(save_dir / "flow_v3_baseline.csv", index=False, encoding="utf-8-sig")
    cost_df.to_csv(save_dir / "flow_v3_cost.csv", index=False, encoding="utf-8-sig")
    wf_df.to_csv(save_dir / "flow_v3_walkforward_results.csv", index=False, encoding="utf-8-sig")
    wf_summary.to_csv(save_dir / "flow_v3_walkforward_summary.csv", index=False, encoding="utf-8-sig")
    merged.to_csv(save_dir / "flow_v3_eval_summary.csv", index=False, encoding="utf-8-sig")
    print(merged.to_string(index=False))


if __name__ == "__main__":
    main()
