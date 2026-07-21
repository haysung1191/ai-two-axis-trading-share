from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from split_models.backtest import (
    BacktestConfig,
    _asset_key,
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


def _regime_frame(monthly_close: pd.DataFrame, signal_dates: list[pd.Timestamp]) -> pd.DataFrame:
    rows = []
    spy_key = _asset_key("US", "ETF", "SPY")
    kr_key = _asset_key("KR", "ETF", "069500")
    for idx, signal_date in enumerate(signal_dates[:-1]):
        next_date = signal_dates[idx + 1]
        month_ret = monthly_close.loc[next_date] / monthly_close.loc[signal_date] - 1.0
        spy = float(month_ret.get(spy_key, np.nan))
        kr = float(month_ret.get(kr_key, np.nan))
        rows.append(
            {
                "SignalDate": signal_date,
                "NextDate": next_date,
                "SPYReturn": spy,
                "KOSPI200Return": kr,
                "SPYRegime": "UP" if pd.notna(spy) and spy >= 0 else "DOWN",
                "KOSPIRegime": "UP" if pd.notna(kr) and kr >= 0 else "DOWN",
            }
        )
    return pd.DataFrame(rows)


def _summarize(group: pd.DataFrame, label_cols: list[str]) -> pd.DataFrame:
    out = (
        group.groupby(label_cols, as_index=False)
        .agg(
            Months=("NetReturnDelta", "count"),
            AvgDelta=("NetReturnDelta", "mean"),
            PositiveMonths=("NetReturnDelta", lambda s: int((pd.to_numeric(s, errors="coerce") > 0).sum())),
            NegativeMonths=("NetReturnDelta", lambda s: int((pd.to_numeric(s, errors="coerce") < 0).sum())),
            AvgBaselineReturn=("NetReturn_baseline", "mean"),
            AvgCandidateReturn=("NetReturn_candidate", "mean"),
        )
        .sort_values(label_cols)
    )
    return out


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
    regimes = _regime_frame(monthly_close, signal_dates)
    compare = compare.merge(regimes, on=["SignalDate", "NextDate"], how="left")
    compare.to_csv(output_dir / "variant_regime_compare.csv", index=False, encoding="utf-8-sig")

    spy_summary = _summarize(compare, ["SPYRegime"])
    kr_summary = _summarize(compare, ["KOSPIRegime"])
    joint_summary = _summarize(compare, ["SPYRegime", "KOSPIRegime"])
    spy_summary.to_csv(output_dir / "variant_regime_spy_summary.csv", index=False, encoding="utf-8-sig")
    kr_summary.to_csv(output_dir / "variant_regime_kospi_summary.csv", index=False, encoding="utf-8-sig")
    joint_summary.to_csv(output_dir / "variant_regime_joint_summary.csv", index=False, encoding="utf-8-sig")

    summary = {
        "baseline_variant": args.baseline,
        "candidate_variant": args.candidate,
        "months_compared": int(len(compare)),
        "spy_up_avg_delta": float(spy_summary.loc[spy_summary["SPYRegime"] == "UP", "AvgDelta"].iloc[0]),
        "spy_down_avg_delta": float(spy_summary.loc[spy_summary["SPYRegime"] == "DOWN", "AvgDelta"].iloc[0]),
        "kospi_up_avg_delta": float(kr_summary.loc[kr_summary["KOSPIRegime"] == "UP", "AvgDelta"].iloc[0]),
        "kospi_down_avg_delta": float(kr_summary.loc[kr_summary["KOSPIRegime"] == "DOWN", "AvgDelta"].iloc[0]),
    }
    (output_dir / "variant_regime_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"months_compared={summary['months_compared']}")
    print(f"spy_up_avg_delta={summary['spy_up_avg_delta']:.6f}")
    print(f"spy_down_avg_delta={summary['spy_down_avg_delta']:.6f}")
    print(f"kospi_up_avg_delta={summary['kospi_up_avg_delta']:.6f}")
    print(f"kospi_down_avg_delta={summary['kospi_down_avg_delta']:.6f}")


if __name__ == "__main__":
    main()


