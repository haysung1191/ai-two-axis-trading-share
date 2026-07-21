import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import argparse
from io import BytesIO
from typing import Dict, List

import numpy as np
import pandas as pd

import config
from kis_backtest_from_prices import write_csv_any


def read_csv_any(path: str) -> pd.DataFrame:
    try:
        if path.startswith("gs://"):
            from google.cloud import storage

            no_scheme = path.replace("gs://", "", 1)
            bucket_name, blob_name = no_scheme.split("/", 1) if "/" in no_scheme else (no_scheme, "")
            raw = storage.Client().bucket(bucket_name).blob(blob_name).download_as_bytes()
            return pd.read_csv(BytesIO(raw))
        return pd.read_csv(path)
    except Exception as e:
        print(f"[WARN] could not read {path}: {e}")
        return pd.DataFrame()


def _pick_cost_row(group: pd.DataFrame, target_pct: float) -> pd.Series:
    g = group.copy()
    g["RoundtripCostPct"] = pd.to_numeric(g["RoundtripCostPct"], errors="coerce")
    g["_dist"] = (g["RoundtripCostPct"] - float(target_pct)).abs()
    return g.sort_values(["_dist", "RoundtripCostPct"]).iloc[0]


def main() -> None:
    default_base = f"gs://{config.GCS_BUCKET_NAME}/backtests" if config.GCS_BUCKET_NAME else "."
    p = argparse.ArgumentParser(description="Build compact operator-facing cost stress summary from extended cost sensitivity.")
    p.add_argument("--cost-path", type=str, default=f"{default_base}/kis_bt_cost_sensitivity_extended.csv")
    p.add_argument("--leaderboard-path", type=str, default=f"{default_base}/kis_strategy_leaderboard.csv")
    p.add_argument("--save-path", type=str, default=f"{default_base}/kis_cost_stress_report.csv")
    p.add_argument("--base-roundtrip-cost-pct", type=float, default=0.20)
    p.add_argument("--moderate-roundtrip-cost-pct", type=float, default=0.50)
    p.add_argument("--severe-roundtrip-cost-pct", type=float, default=1.00)
    args = p.parse_args()

    cost_df = read_csv_any(args.cost_path)
    leader_df = read_csv_any(args.leaderboard_path)
    if cost_df.empty or "StrategyName" not in cost_df.columns:
        out = pd.DataFrame(
            columns=[
                "RunId",
                "RunStartedAt",
                "Strategy",
                "Rank",
                "IsTopStrategy",
                "BaselineRoundtripCostPct",
                "ModerateStressRoundtripCostPct",
                "SevereStressRoundtripCostPct",
                "CAGR_gross",
                "CAGR_net_base",
                "CAGR_net_moderate",
                "CAGR_net_severe",
                "CAGR_drag_base",
                "CAGR_drag_moderate",
                "CAGR_drag_severe",
                "AnnualTurnover",
                "AvgTurnover",
                "AvgHoldings",
                "RebalanceCount",
                "CostModel",
                "OperatorComment",
            ]
        )
        write_csv_any(out, args.save_path, index=False)
        print(f"saved {args.save_path}")
        return

    strategy_order: List[str]
    if not leader_df.empty and "Strategy" in leader_df.columns:
        strategy_order = list(leader_df["Strategy"].dropna().astype(str))
    else:
        strategy_order = sorted(cost_df["StrategyName"].dropna().astype(str).unique())
    rank_map: Dict[str, int] = {s: i + 1 for i, s in enumerate(strategy_order)}
    top_strategy = strategy_order[0] if strategy_order else ""

    rows: List[Dict[str, object]] = []
    for strategy, group in cost_df.groupby("StrategyName"):
        base_row = _pick_cost_row(group, args.base_roundtrip_cost_pct)
        moderate_row = _pick_cost_row(group, args.moderate_roundtrip_cost_pct)
        severe_row = _pick_cost_row(group, args.severe_roundtrip_cost_pct)
        rows.append(
            {
                "RunId": str(base_row.get("RunId", "")),
                "RunStartedAt": str(base_row.get("RunStartedAt", "")),
                "Strategy": str(strategy),
                "Rank": int(rank_map.get(str(strategy), len(rank_map) + 1)),
                "IsTopStrategy": int(str(strategy) == top_strategy),
                "BaselineRoundtripCostPct": float(base_row.get("RoundtripCostPct", np.nan)),
                "ModerateStressRoundtripCostPct": float(moderate_row.get("RoundtripCostPct", np.nan)),
                "SevereStressRoundtripCostPct": float(severe_row.get("RoundtripCostPct", np.nan)),
                "CAGR_gross": float(base_row.get("CAGR_gross", np.nan)),
                "CAGR_net_base": float(base_row.get("CAGR_net", np.nan)),
                "CAGR_net_moderate": float(moderate_row.get("CAGR_net", np.nan)),
                "CAGR_net_severe": float(severe_row.get("CAGR_net", np.nan)),
                "CAGR_drag_base": float(base_row.get("CAGR_drag", np.nan)),
                "CAGR_drag_moderate": float(moderate_row.get("CAGR_drag", np.nan)),
                "CAGR_drag_severe": float(severe_row.get("CAGR_drag", np.nan)),
                "AnnualTurnover": float(base_row.get("AnnualTurnover", np.nan)),
                "AvgTurnover": float(base_row.get("AvgTurnover", np.nan)),
                "AvgHoldings": float(base_row.get("AvgHoldings", np.nan)),
                "RebalanceCount": int(base_row.get("RebalanceCount", 0)),
                "CostModel": "gross_weight_turnover x one_way_fee; roundtrip input converted to one-way",
                "OperatorComment": "uniform_friction_model_no_asset_type_split",
            }
        )

    out = pd.DataFrame(rows).sort_values(["Rank", "Strategy"]).reset_index(drop=True)
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print("\n=== Cost Stress Report ===")
    print(out.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
