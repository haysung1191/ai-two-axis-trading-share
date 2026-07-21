from __future__ import annotations

import argparse
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
)



ROOT = REPO_ROOT


def _build_context(cfg: BacktestConfig) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict[str, pd.DataFrame], pd.DataFrame, list[pd.Timestamp]]:
    us_stocks, us_etfs = _load_us_universe()
    kr_universe = _load_kr_universe()
    universe = pd.concat([us_stocks, us_etfs, kr_universe], ignore_index=True)
    price_cache, flow_cache = _build_daily_caches(universe)
    monthly_close = _build_monthly_close_matrix(universe, price_cache)
    signal_dates = _signal_dates(monthly_close, cfg.signal_start)
    return universe, price_cache, flow_cache, monthly_close, signal_dates


def _run_variant(
    cfg: BacktestConfig,
    variant_name: str,
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
) -> dict[str, pd.DataFrame]:
    variant = _baseline_variant_map()[variant_name]
    return _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)


def _latest_book(positions: pd.DataFrame) -> pd.DataFrame:
    out = positions.copy()
    out["SignalDate"] = pd.to_datetime(out["SignalDate"])
    latest_signal = out["SignalDate"].max()
    out = out[out["SignalDate"] == latest_signal].copy()
    return out.sort_values(["TargetWeight", "MomentumScore", "Symbol"], ascending=[False, False, True]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="rule_breadth_it_risk_off")
    parser.add_argument("--candidate", default="rule_breadth_it_us5_cap")
    parser.add_argument("--output-dir", default=str(ROOT / "output" / "split_models_live_transition_review"))
    parser.add_argument("--canonical-shadow", action="store_true")
    args = parser.parse_args()

    output_dir = ROOT / "output" / "split_models_shadow" if args.canonical_shadow else Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    baseline = _run_variant(cfg, args.baseline, universe, price_cache, flow_cache, monthly_close, signal_dates)
    candidate = _run_variant(cfg, args.candidate, universe, price_cache, flow_cache, monthly_close, signal_dates)

    base_book = _latest_book(baseline["positions"])
    cand_book = _latest_book(candidate["positions"])

    key_cols = ["Market", "AssetType", "Symbol", "Name", "Sector"]
    merged = base_book[key_cols + ["TargetWeight"]].rename(columns={"TargetWeight": "BaselineWeight"}).merge(
        cand_book[key_cols + ["TargetWeight"]].rename(columns={"TargetWeight": "CandidateWeight"}),
        on=key_cols,
        how="outer",
    )
    merged["BaselineWeight"] = pd.to_numeric(merged["BaselineWeight"], errors="coerce").fillna(0.0)
    merged["CandidateWeight"] = pd.to_numeric(merged["CandidateWeight"], errors="coerce").fillna(0.0)
    merged["WeightDelta"] = merged["CandidateWeight"] - merged["BaselineWeight"]
    merged["Action"] = "Hold"
    merged.loc[(merged["BaselineWeight"] == 0.0) & (merged["CandidateWeight"] > 0.0), "Action"] = "Buy"
    merged.loc[(merged["BaselineWeight"] > 0.0) & (merged["CandidateWeight"] == 0.0), "Action"] = "Sell"
    merged.loc[merged["WeightDelta"] > 0, "Action"] = merged["Action"].where(merged["Action"] != "Hold", "Add")
    merged.loc[merged["WeightDelta"] < 0, "Action"] = merged["Action"].where(merged["Action"] != "Hold", "Trim")
    merged = merged.sort_values(["Action", "WeightDelta", "Market", "Symbol"], ascending=[True, False, True, True]).reset_index(drop=True)
    diff_name = "shadow_live_transition_diff.csv" if args.canonical_shadow else "live_transition_diff.csv"
    summary_name = "shadow_live_transition_summary.json" if args.canonical_shadow else "live_transition_summary.json"
    merged.to_csv(output_dir / diff_name, index=False, encoding="utf-8-sig")

    summary = {
        "baseline_variant": args.baseline,
        "candidate_variant": args.candidate,
        "signal_date": str(base_book["SignalDate"].iloc[0].date()) if not base_book.empty else "",
        "baseline_holdings": int(len(base_book)),
        "candidate_holdings": int(len(cand_book)),
        "baseline_us_count": int((base_book["Market"] == "US").sum()),
        "candidate_us_count": int((cand_book["Market"] == "US").sum()),
        "baseline_kr_count": int((base_book["Market"] == "KR").sum()),
        "candidate_kr_count": int((cand_book["Market"] == "KR").sum()),
        "buys": int((merged["Action"] == "Buy").sum()),
        "sells": int((merged["Action"] == "Sell").sum()),
        "adds": int((merged["Action"] == "Add").sum()),
        "trims": int((merged["Action"] == "Trim").sum()),
        "weight_turnover": float(0.5 * merged["WeightDelta"].abs().sum()),
    }
    (output_dir / summary_name).write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"signal_date={summary['signal_date']}")
    print(f"baseline_holdings={summary['baseline_holdings']}")
    print(f"candidate_holdings={summary['candidate_holdings']}")
    print(f"baseline_us_count={summary['baseline_us_count']}")
    print(f"candidate_us_count={summary['candidate_us_count']}")
    print(f"weight_turnover={summary['weight_turnover']:.6f}")


if __name__ == "__main__":
    main()


