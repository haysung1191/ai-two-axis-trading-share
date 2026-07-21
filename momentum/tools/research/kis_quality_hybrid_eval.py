import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import os

import pandas as pd

from kis_backtest_from_prices import HYBRID_STRATEGY_COMPONENTS, blend_strategy_results, build_market_matrices, run_one
from kis_flow_data import build_flow_matrices
from kis_quality_data import build_quality_matrices
from kis_shadow_common import build_strategy


def main() -> None:
    base = "data/prices_operating_institutional_v1"
    save_dir = "backtests/quality_eval_20260328"
    os.makedirs(save_dir, exist_ok=True)

    close_s, value_s = build_market_matrices(base, "stock", 0)
    close_e, value_e = build_market_matrices(base, "etf", 0)
    idx = close_s.index.intersection(close_e.index).sort_values()
    close_s = close_s.loc[idx]
    close_e = close_e.loc[idx]
    value_s = value_s.loc[idx, close_s.columns]
    value_e = value_e.loc[idx, close_e.columns]
    flow_mats = build_flow_matrices("data/flows_naver_8y", market="stock", max_files=0)
    quality_mats = build_quality_matrices("data/quality_fnguide", close_s.index, list(close_s.columns))

    coverage_start = pd.Timestamp("2022-03-31")
    mask = idx >= coverage_start
    cs = close_s.loc[mask]
    ce = close_e.loc[mask]
    vs = value_s.loc[mask, cs.columns]
    ve = value_e.loc[mask, ce.columns]

    component_names = [
        "Weekly QualityProfitability MVP",
        "Weekly Score50 RegimeState",
        "Weekly ETF RiskBudget",
    ]
    component_results = {}
    rows = []
    for name in component_names:
        stg = build_strategy(name, fee_rate=0.0)
        out, m = run_one(
            cs,
            ce,
            stg,
            min_common_dates=180,
            traded_value_s=vs,
            traded_value_e=ve,
            flow_mats=flow_mats,
            quality_mats=quality_mats,
        )
        component_results[name] = (out, m)
        rows.append(
            {
                "Strategy": name,
                "CoverageStart": str(coverage_start.date()),
                "CAGR": float(m["CAGR"]),
                "MDD": float(m["MDD"]),
                "Sharpe": float(m["Sharpe"]),
                "AnnualTurnover": float(m.get("AnnualTurnover", 0.0)),
            }
        )

    hybrid_name = "Weekly Hybrid QP50 RS50"
    out_h, m_h = blend_strategy_results(hybrid_name, component_results)
    rows.append(
        {
            "Strategy": hybrid_name,
            "CoverageStart": str(coverage_start.date()),
            "CAGR": float(m_h["CAGR"]),
            "MDD": float(m_h["MDD"]),
            "Sharpe": float(m_h["Sharpe"]),
            "AnnualTurnover": float(m_h.get("AnnualTurnover", 0.0)),
        }
    )

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(save_dir, "quality_hybrid_compare.csv"), index=False, encoding="utf-8-sig")
    out_h.reset_index().to_csv(os.path.join(save_dir, "quality_hybrid_nav.csv"), index=False, encoding="utf-8-sig")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
