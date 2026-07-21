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


def _dominant_sleeve(stock_w: float, etf_w: float) -> str:
    if pd.isna(stock_w) or pd.isna(etf_w):
        return "UNKNOWN"
    if etf_w >= 0.70:
        return "ETF_HEAVY"
    if stock_w >= 0.70:
        return "STOCK_HEAVY"
    return "BALANCED"


def main() -> None:
    default_base = f"gs://{config.GCS_BUCKET_NAME}/backtests" if config.GCS_BUCKET_NAME else "."
    p = argparse.ArgumentParser(description="Build compact stock-vs-ETF sleeve attribution report from baseline summary.")
    p.add_argument("--base-summary-path", type=str, default=f"{default_base}/kis_bt_auto_summary.csv")
    p.add_argument("--leaderboard-path", type=str, default=f"{default_base}/kis_strategy_leaderboard.csv")
    p.add_argument("--save-path", type=str, default=f"{default_base}/kis_sleeve_attribution_report.csv")
    args = p.parse_args()

    base_df = read_csv_any(args.base_summary_path)
    leader_df = read_csv_any(args.leaderboard_path)
    if base_df.empty or "Strategy" not in base_df.columns:
        out = pd.DataFrame(
            columns=[
                "RunId",
                "RunStartedAt",
                "Strategy",
                "Rank",
                "IsTopStrategy",
                "CAGR",
                "MDD",
                "Sharpe",
                "AnnualTurnover",
                "RotationSignalAvg",
                "AvgStockSleeve",
                "AvgEtfSleeve",
                "DominantSleeve",
                "SleeveGap",
                "OperatorComment",
            ]
        )
        write_csv_any(out, args.save_path, index=False)
        print(f"saved {args.save_path}")
        return

    strategy_order = list(leader_df["Strategy"].dropna().astype(str)) if not leader_df.empty and "Strategy" in leader_df.columns else list(base_df["Strategy"].dropna().astype(str))
    rank_map: Dict[str, int] = {s: i + 1 for i, s in enumerate(strategy_order)}
    top_strategy = strategy_order[0] if strategy_order else ""

    rows: List[Dict[str, object]] = []
    for _, r in base_df.iterrows():
        strategy = str(r["Strategy"])
        stock_w = float(r.get("AvgStockSleeve", np.nan))
        etf_w = float(r.get("AvgEtfSleeve", np.nan))
        rows.append(
            {
                "RunId": str(r.get("RunId", "")),
                "RunStartedAt": str(r.get("RunStartedAt", "")),
                "Strategy": strategy,
                "Rank": int(rank_map.get(strategy, len(rank_map) + 1)),
                "IsTopStrategy": int(strategy == top_strategy),
                "CAGR": float(r.get("CAGR", np.nan)),
                "MDD": float(r.get("MDD", np.nan)),
                "Sharpe": float(r.get("Sharpe", np.nan)),
                "AnnualTurnover": float(r.get("AnnualTurnover", np.nan)),
                "RotationSignalAvg": float(r.get("RotationSignalAvg", np.nan)),
                "AvgStockSleeve": stock_w,
                "AvgEtfSleeve": etf_w,
                "DominantSleeve": _dominant_sleeve(stock_w, etf_w),
                "SleeveGap": float(etf_w - stock_w) if pd.notna(stock_w) and pd.notna(etf_w) else np.nan,
                "OperatorComment": "sleeve averages come from realized portfolio allocation over the backtest",
            }
        )

    out = pd.DataFrame(rows).sort_values(["Rank", "Strategy"]).reset_index(drop=True)
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print("\n=== Sleeve Attribution Report ===")
    print(out.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
