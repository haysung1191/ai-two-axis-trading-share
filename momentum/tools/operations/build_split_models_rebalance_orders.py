from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _load_transition_diff(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    numeric_cols = ["BaselineWeight", "CandidateWeight", "WeightDelta"]
    for col in numeric_cols:
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0.0)
    return frame


def _format_order_sheet(frame: pd.DataFrame, total_capital: float | None) -> pd.DataFrame:
    out = frame.copy()
    out["TargetWeightPct"] = out["CandidateWeight"] * 100.0
    out["DeltaWeightPct"] = out["WeightDelta"] * 100.0
    out["ExecutionSide"] = out["WeightDelta"].map(lambda v: "BUY" if v > 0 else ("SELL" if v < 0 else "HOLD"))

    if total_capital is not None:
        out["TargetNotional"] = out["CandidateWeight"] * total_capital
        out["DeltaNotional"] = out["WeightDelta"] * total_capital
    else:
        out["TargetNotional"] = pd.NA
        out["DeltaNotional"] = pd.NA

    out["OrderPriority"] = out["ExecutionSide"].map({"SELL": 0, "BUY": 1, "HOLD": 2}).fillna(9)
    out = out.sort_values(["OrderPriority", "Market", "Symbol"], ascending=[True, True, True]).reset_index(drop=True)
    return out[
        [
            "ExecutionSide",
            "Action",
            "Market",
            "AssetType",
            "Symbol",
            "Name",
            "Sector",
            "BaselineWeight",
            "CandidateWeight",
            "WeightDelta",
            "TargetWeightPct",
            "DeltaWeightPct",
            "TargetNotional",
            "DeltaNotional",
        ]
    ]


def _build_execution_summary(orders: pd.DataFrame, total_capital: float | None) -> tuple[pd.DataFrame, dict[str, object]]:
    actionable = orders[orders["ExecutionSide"] != "HOLD"].copy()
    market_summary = (
        actionable.groupby(["Market", "ExecutionSide"], dropna=False)
        .agg(
            OrderCount=("Symbol", "count"),
            GrossDeltaWeightPct=("DeltaWeightPct", lambda s: float(s.abs().sum())),
            GrossDeltaNotional=("DeltaNotional", lambda s: float(s.abs().sum()) if total_capital is not None else 0.0),
        )
        .reset_index()
        .sort_values(["Market", "ExecutionSide"])
    )

    summary = {
        "total_capital": total_capital,
        "actionable_rows": int(len(actionable)),
        "sell_count": int((actionable["ExecutionSide"] == "SELL").sum()),
        "buy_count": int((actionable["ExecutionSide"] == "BUY").sum()),
        "markets": [],
    }
    for market, group in actionable.groupby("Market", dropna=False):
        market_payload = {
            "market": market,
            "sell_count": int((group["ExecutionSide"] == "SELL").sum()),
            "buy_count": int((group["ExecutionSide"] == "BUY").sum()),
            "gross_delta_weight_pct": float(group["DeltaWeightPct"].abs().sum()),
        }
        if total_capital is not None:
            market_payload["gross_delta_notional"] = float(group["DeltaNotional"].abs().sum())
        summary["markets"].append(market_payload)
    return market_summary, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transition-diff", default=str(SHADOW_DIR / "shadow_live_transition_diff.csv"))
    parser.add_argument("--output-path", default=str(SHADOW_DIR / "shadow_rebalance_orders.csv"))
    parser.add_argument("--summary-path", default=str(SHADOW_DIR / "shadow_rebalance_execution_summary.json"))
    parser.add_argument("--market-summary-path", default=str(SHADOW_DIR / "shadow_rebalance_market_summary.csv"))
    parser.add_argument("--total-capital", type=float, default=None)
    args = parser.parse_args()

    transition_diff = _load_transition_diff(Path(args.transition_diff))
    orders = _format_order_sheet(transition_diff, args.total_capital)
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    orders.to_csv(output_path, index=False, encoding="utf-8-sig")

    market_summary, execution_summary = _build_execution_summary(orders, args.total_capital)
    market_summary.to_csv(Path(args.market_summary_path), index=False, encoding="utf-8-sig")
    Path(args.summary_path).write_text(json.dumps(execution_summary, indent=2), encoding="utf-8")

    actionable = orders[orders["ExecutionSide"] != "HOLD"].copy()
    print(f"orders_path={output_path}")
    print(f"actionable_rows={len(actionable)}")
    if not actionable.empty:
        sell_count = int((actionable["ExecutionSide"] == "SELL").sum())
        buy_count = int((actionable["ExecutionSide"] == "BUY").sum())
        print(f"sells={sell_count}")
        print(f"buys={buy_count}")
        print(f"summary_path={args.summary_path}")
        print(f"market_summary_path={args.market_summary_path}")


if __name__ == "__main__":
    main()
