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


def _build_context(
    cfg: BacktestConfig,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict[str, pd.DataFrame], pd.DataFrame, list[pd.Timestamp]]:
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
    parser.add_argument("--top-n", type=int, default=5)
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

    total_compare = base_nav.merge(
        cand_nav,
        on=["SignalDate", "NextDate"],
        suffixes=("_baseline", "_candidate"),
        how="inner",
    )
    total_compare["TotalDelta"] = total_compare["NetReturn_candidate"] - total_compare["NetReturn_baseline"]

    base_symbol = baseline["symbol_contrib"].copy()
    cand_symbol = candidate["symbol_contrib"].copy()
    for df in (base_symbol, cand_symbol):
        df["SignalDate"] = pd.to_datetime(df["SignalDate"])
        df["NextDate"] = pd.to_datetime(df["NextDate"])
        df["Symbol"] = df["Symbol"].astype(str).str.upper()

    symbol_compare = base_symbol.merge(
        cand_symbol,
        on=["SignalDate", "NextDate", "Market", "Sector", "Symbol"],
        suffixes=("_baseline", "_candidate"),
        how="outer",
    ).fillna({"Contribution_baseline": 0.0, "Contribution_candidate": 0.0})
    symbol_compare["ContributionDelta"] = (
        pd.to_numeric(symbol_compare["Contribution_candidate"], errors="coerce").fillna(0.0)
        - pd.to_numeric(symbol_compare["Contribution_baseline"], errors="coerce").fillna(0.0)
    )

    top_symbols = (
        symbol_compare.groupby(["Market", "Sector", "Symbol"], as_index=False)
        .agg(ContributionDelta=("ContributionDelta", "sum"))
        .sort_values("ContributionDelta", ascending=False)
        .head(max(int(args.top_n), 1))
        .reset_index(drop=True)
    )
    top_symbols.to_csv(output_dir / "variant_leave_one_out_top_symbols.csv", index=False, encoding="utf-8-sig")

    rows: list[dict[str, float | int | str]] = []
    for row in top_symbols.itertuples(index=False):
        excluded = str(row.Symbol).upper()
        excluded_monthly = (
            symbol_compare[symbol_compare["Symbol"] == excluded]
            .groupby(["SignalDate", "NextDate"], as_index=False)
            .agg(ExcludedDelta=("ContributionDelta", "sum"))
        )
        residual = total_compare.merge(excluded_monthly, on=["SignalDate", "NextDate"], how="left").fillna({"ExcludedDelta": 0.0})
        residual["ResidualDelta"] = residual["TotalDelta"] - residual["ExcludedDelta"]
        rows.append(
            {
                "Market": row.Market,
                "Sector": row.Sector,
                "Symbol": excluded,
                "ContributionDelta": float(row.ContributionDelta),
                "AvgTotalDelta": float(pd.to_numeric(residual["TotalDelta"], errors="coerce").mean()),
                "AvgExcludedDelta": float(pd.to_numeric(residual["ExcludedDelta"], errors="coerce").mean()),
                "AvgResidualDelta": float(pd.to_numeric(residual["ResidualDelta"], errors="coerce").mean()),
                "PositiveResidualMonths": int((pd.to_numeric(residual["ResidualDelta"], errors="coerce") > 0).sum()),
                "NegativeResidualMonths": int((pd.to_numeric(residual["ResidualDelta"], errors="coerce") < 0).sum()),
            }
        )

    leave_one_out = pd.DataFrame(rows).sort_values("ContributionDelta", ascending=False).reset_index(drop=True)
    leave_one_out.to_csv(output_dir / "variant_leave_one_out_summary.csv", index=False, encoding="utf-8-sig")

    summary = {
        "baseline_variant": args.baseline,
        "candidate_variant": args.candidate,
        "symbols_analyzed": int(len(leave_one_out)),
        "best_residual_symbol": None if leave_one_out.empty else str(leave_one_out.sort_values("AvgResidualDelta", ascending=False).iloc[0]["Symbol"]),
        "worst_residual_symbol": None if leave_one_out.empty else str(leave_one_out.sort_values("AvgResidualDelta", ascending=True).iloc[0]["Symbol"]),
    }
    (output_dir / "variant_leave_one_out_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"symbols_analyzed={summary['symbols_analyzed']}")
    if not leave_one_out.empty:
        print(leave_one_out.to_string(index=False))


if __name__ == "__main__":
    main()


