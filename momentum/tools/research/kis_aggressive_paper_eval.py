import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from typing import List

import numpy as np
import pandas as pd

from kis_backtest_from_prices import build_market_matrices, default_flow_base, run_one
from kis_flow_data import build_flow_matrices
from kis_shadow_common import build_strategy
from kis_walkforward import build_windows, choose_feasible_window_params, run_test_with_warmup


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate aggressive Korean paper candidates with baseline + 0.5% cost + named-only walkforward.")
    p.add_argument("--base", type=str, default="data/prices_operating_institutional_v1")
    p.add_argument("--save-dir", type=str, default="backtests/aggressive_eval_20260328")
    p.add_argument("--candidates", type=str, default="ScoreN30_P2.0_ROE0.4,ScoreN30_P2.0_ROE0.6")
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--train-years", type=int, default=8)
    p.add_argument("--test-years", type=int, default=2)
    p.add_argument("--step-years", type=int, default=1)
    p.add_argument("--min-oos-windows", type=int, default=3)
    p.add_argument("--cost-roundtrip-pct", type=float, default=0.5)
    p.add_argument("--tracker-path", type=str, default="backtests/korea_aggressive_alpha_tracker.csv")
    return p.parse_args()


def evaluate_baseline(
    strategy_name: str,
    close_s: pd.DataFrame,
    close_e: pd.DataFrame,
    value_s: pd.DataFrame,
    value_e: pd.DataFrame,
    flow_mats: dict[str, pd.DataFrame] | None,
    min_common_dates: int,
) -> dict:
    fee_rate = 0.0
    stg = build_strategy(strategy_name, fee_rate=fee_rate, manifest_path=None)
    out, metrics = run_one(
        close_s,
        close_e,
        stg,
        min_common_dates=min_common_dates,
        traded_value_s=value_s,
        traded_value_e=value_e,
        flow_mats=flow_mats,
    )
    return {
        "Strategy": strategy_name,
        "BaselineCAGR": float(metrics.get("CAGR", np.nan)),
        "BaselineMDD": float(metrics.get("MDD", np.nan)),
        "BaselineSharpe": float(metrics.get("Sharpe", np.nan)),
        "AnnualTurnover": float(metrics.get("AnnualTurnover", np.nan)),
    }


def evaluate_cost(
    strategy_name: str,
    close_s: pd.DataFrame,
    close_e: pd.DataFrame,
    value_s: pd.DataFrame,
    value_e: pd.DataFrame,
    flow_mats: dict[str, pd.DataFrame] | None,
    min_common_dates: int,
    roundtrip_cost_pct: float,
) -> dict:
    fee_rate = float(roundtrip_cost_pct) / 100.0 / 2.0
    stg = build_strategy(strategy_name, fee_rate=fee_rate, manifest_path=None)
    _, metrics = run_one(
        close_s,
        close_e,
        stg,
        min_common_dates=min_common_dates,
        traded_value_s=value_s,
        traded_value_e=value_e,
        flow_mats=flow_mats,
    )
    return {
        "Strategy": strategy_name,
        "CAGR_net_0.5pct": float(metrics.get("CAGR", np.nan)),
        "MDD_net_0.5pct": float(metrics.get("MDD", np.nan)),
        "Sharpe_net_0.5pct": float(metrics.get("Sharpe", np.nan)),
    }


def evaluate_walkforward(
    strategy_name: str,
    close_s: pd.DataFrame,
    close_e: pd.DataFrame,
    value_s: pd.DataFrame,
    value_e: pd.DataFrame,
    flow_mats: dict[str, pd.DataFrame] | None,
    min_common_dates: int,
    train_years: int,
    test_years: int,
    step_years: int,
    min_oos_windows: int,
    roundtrip_cost_pct: float,
) -> tuple[pd.DataFrame, dict]:
    idx = close_s.index.intersection(close_e.index).sort_values()
    train_years, test_years, step_years, _ = choose_feasible_window_params(
        idx, train_years, test_years, step_years, min_oos_windows
    )
    windows = build_windows(idx, train_years, test_years, step_years)
    fee_rate = float(roundtrip_cost_pct) / 100.0 / 2.0
    rows: List[dict] = []
    for train_start, train_end, test_start, test_end in windows:
        stg = build_strategy(strategy_name, fee_rate=fee_rate, manifest_path=None)
        m_short, m_full = run_test_with_warmup(
            close_s,
            close_e,
            value_s,
            value_e,
            flow_mats,
            test_start=test_start,
            test_end=test_end,
            stg=stg,
            min_common_dates=min_common_dates,
        )
        rows.append(
            {
                "Strategy": strategy_name,
                "TrainStart": str(train_start.date()),
                "TrainEnd": str(train_end.date()),
                "TestStart": str(test_start.date()),
                "TestEnd": str(test_end.date()),
                "CAGR_net": float(m_short.get("CAGR", np.nan)),
                "MDD": float(m_short.get("MDD", np.nan)),
                "Sharpe_net": float(m_short.get("Sharpe", np.nan)),
                "AnnualTurnover": float(m_full.get("AnnualTurnover", np.nan)),
            }
        )
    wf = pd.DataFrame(rows)
    if wf.empty:
        return wf, {
            "Strategy": strategy_name,
            "WindowCount": 0,
            "MedianCAGR": np.nan,
            "WorstCAGR": np.nan,
            "MedianMDD": np.nan,
            "WorstMDD": np.nan,
            "CAGRStd": np.nan,
        }
    summary = {
        "Strategy": strategy_name,
        "WindowCount": int(len(wf)),
        "MedianCAGR": float(wf["CAGR_net"].median()),
        "WorstCAGR": float(wf["CAGR_net"].min()),
        "MedianMDD": float(wf["MDD"].median()),
        "WorstMDD": float(wf["MDD"].min()),
        "CAGRStd": float(wf["CAGR_net"].std(ddof=0)),
    }
    return wf, summary


def update_tracker(tracker_path: Path, merged: pd.DataFrame) -> None:
    if not tracker_path.exists():
        return
    tracker = pd.read_csv(tracker_path)
    out = tracker.copy()
    for _, row in merged.iterrows():
        candidate = str(row["Strategy"])
        mask = out["Candidate"].astype(str).eq(candidate)
        if not mask.any():
            continue
        status = "FAIL"
        if pd.notna(row.get("CAGR_net_0.5pct")) and pd.notna(row.get("WorstMDD")):
            target_cagr = float(out.loc[mask, "TargetNetCAGR_0p5pct"].iloc[0])
            max_worst_mdd = float(out.loc[mask, "MaxWorstMDD"].iloc[0])
            if float(row["CAGR_net_0.5pct"]) >= target_cagr and float(row["WorstMDD"]) >= max_worst_mdd:
                status = "PASS"
            elif float(row["CAGR_net_0.5pct"]) >= 0.10:
                status = "REVIEW"
        out.loc[mask, "Status"] = status
        out.loc[mask, "Notes"] = (
            out.loc[mask, "Notes"].astype(str)
            + f" | baseline={float(row.get('BaselineCAGR', np.nan)):.4f}, net05={float(row.get('CAGR_net_0.5pct', np.nan)):.4f}, worstMDD={float(row.get('WorstMDD', np.nan)):.4f}"
        )
    out.to_csv(tracker_path, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    candidates = [c.strip() for c in args.candidates.split(",") if c.strip()]

    close_s, value_s = build_market_matrices(args.base, "stock", 0)
    close_e, value_e = build_market_matrices(args.base, "etf", 0)
    flow_mats = build_flow_matrices(default_flow_base(), market="stock", max_files=0)

    baseline_rows = []
    cost_rows = []
    wf_rows = []
    wf_summary_rows = []
    for strategy_name in candidates:
        baseline_rows.append(
            evaluate_baseline(strategy_name, close_s, close_e, value_s, value_e, flow_mats, args.min_common_dates)
        )
        cost_rows.append(
            evaluate_cost(
                strategy_name,
                close_s,
                close_e,
                value_s,
                value_e,
                flow_mats,
                args.min_common_dates,
                args.cost_roundtrip_pct,
            )
        )
        wf_df, wf_summary = evaluate_walkforward(
            strategy_name,
            close_s,
            close_e,
            value_s,
            value_e,
            flow_mats,
            args.min_common_dates,
            args.train_years,
            args.test_years,
            args.step_years,
            args.min_oos_windows,
            args.cost_roundtrip_pct,
        )
        wf_rows.append(wf_df)
        wf_summary_rows.append(wf_summary)

    baseline_df = pd.DataFrame(baseline_rows)
    cost_df = pd.DataFrame(cost_rows)
    wf_df = pd.concat(wf_rows, ignore_index=True) if wf_rows else pd.DataFrame()
    wf_summary_df = pd.DataFrame(wf_summary_rows)
    merged = baseline_df.merge(cost_df, on="Strategy", how="left").merge(wf_summary_df, on="Strategy", how="left")
    merged["OperatingBaseline"] = "Weekly ETF RiskBudget"

    baseline_df.to_csv(save_dir / "aggressive_baseline.csv", index=False, encoding="utf-8-sig")
    cost_df.to_csv(save_dir / "aggressive_cost_0p5.csv", index=False, encoding="utf-8-sig")
    wf_df.to_csv(save_dir / "aggressive_walkforward_results.csv", index=False, encoding="utf-8-sig")
    wf_summary_df.to_csv(save_dir / "aggressive_walkforward_summary.csv", index=False, encoding="utf-8-sig")
    merged.to_csv(save_dir / "aggressive_eval_summary.csv", index=False, encoding="utf-8-sig")

    update_tracker(Path(args.tracker_path), merged)

    print("saved", save_dir / "aggressive_eval_summary.csv")
    print(merged.to_string(index=False))


if __name__ == "__main__":
    main()
