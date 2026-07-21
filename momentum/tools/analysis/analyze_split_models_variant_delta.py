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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    baseline = _run_variant(cfg, args.baseline, universe, price_cache, flow_cache, monthly_close, signal_dates)
    candidate = _run_variant(cfg, args.candidate, universe, price_cache, flow_cache, monthly_close, signal_dates)

    base_nav = baseline["nav"].copy()
    cand_nav = candidate["nav"].copy()
    for df in (base_nav, cand_nav):
        df["SignalDate"] = pd.to_datetime(df["SignalDate"])
        df["NextDate"] = pd.to_datetime(df["NextDate"])

    compare = base_nav.merge(
        cand_nav,
        on=["SignalDate", "NextDate"],
        suffixes=("_baseline", "_candidate"),
        how="inner",
    )
    compare["NetReturnDelta"] = compare["NetReturn_candidate"] - compare["NetReturn_baseline"]
    compare["TurnoverDelta"] = compare["Turnover_candidate"] - compare["Turnover_baseline"]
    compare = compare.sort_values("SignalDate").reset_index(drop=True)
    compare.to_csv(output_dir / "variant_delta_compare.csv", index=False, encoding="utf-8-sig")

    top_positive = compare.nlargest(5, "NetReturnDelta")[
        ["SignalDate", "NextDate", "NetReturn_baseline", "NetReturn_candidate", "NetReturnDelta", "TurnoverDelta"]
    ]
    top_negative = compare.nsmallest(5, "NetReturnDelta")[
        ["SignalDate", "NextDate", "NetReturn_baseline", "NetReturn_candidate", "NetReturnDelta", "TurnoverDelta"]
    ]
    top_positive.to_csv(output_dir / "variant_delta_top_positive.csv", index=False, encoding="utf-8-sig")
    top_negative.to_csv(output_dir / "variant_delta_top_negative.csv", index=False, encoding="utf-8-sig")

    summary = {
        "baseline_variant": args.baseline,
        "candidate_variant": args.candidate,
        "months_compared": int(len(compare)),
        "avg_net_return_delta": float(pd.to_numeric(compare["NetReturnDelta"], errors="coerce").mean()),
        "positive_months": int((pd.to_numeric(compare["NetReturnDelta"], errors="coerce") > 0).sum()),
        "negative_months": int((pd.to_numeric(compare["NetReturnDelta"], errors="coerce") < 0).sum()),
        "best_delta_month": None if compare.empty else str(compare.sort_values("NetReturnDelta", ascending=False).iloc[0]["SignalDate"].date()),
        "best_delta_value": None if compare.empty else float(compare["NetReturnDelta"].max()),
        "worst_delta_month": None if compare.empty else str(compare.sort_values("NetReturnDelta", ascending=True).iloc[0]["SignalDate"].date()),
        "worst_delta_value": None if compare.empty else float(compare["NetReturnDelta"].min()),
    }
    (output_dir / "variant_delta_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"months_compared={summary['months_compared']}")
    print(f"avg_net_return_delta={summary['avg_net_return_delta']:.6f}")
    print(f"positive_months={summary['positive_months']}")
    print(f"negative_months={summary['negative_months']}")


if __name__ == "__main__":
    main()


