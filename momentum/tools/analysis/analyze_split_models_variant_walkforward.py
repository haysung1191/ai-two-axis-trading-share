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
    _walkforward_summary,
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
    parser.add_argument("--variants", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--window-months", type=int, default=24)
    parser.add_argument("--step-months", type=int, default=12)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)

    walk_rows: list[pd.DataFrame] = []
    summary: dict[str, dict[str, float | int | str]] = {}
    for variant_name in args.variants:
        result = _run_variant(cfg, variant_name, universe, price_cache, flow_cache, monthly_close, signal_dates)
        walk = _walkforward_summary(result["nav"], window_months=args.window_months, step_months=args.step_months)
        walk.insert(0, "Variant", variant_name)
        walk_rows.append(walk)
        summary[variant_name] = {
            "windows": int(len(walk)),
            "best_cagr": float(pd.to_numeric(walk["CAGR"], errors="coerce").max()) if not walk.empty else 0.0,
            "worst_cagr": float(pd.to_numeric(walk["CAGR"], errors="coerce").min()) if not walk.empty else 0.0,
            "avg_cagr": float(pd.to_numeric(walk["CAGR"], errors="coerce").mean()) if not walk.empty else 0.0,
            "avg_sharpe": float(pd.to_numeric(walk["Sharpe"], errors="coerce").mean()) if not walk.empty else 0.0,
        }

    compare = pd.concat(walk_rows, ignore_index=True)
    compare.to_csv(output_dir / "variant_walkforward_compare.csv", index=False, encoding="utf-8-sig")

    pivot = compare.pivot_table(index=["WindowStart", "WindowEnd", "Months"], columns="Variant", values=["CAGR", "Sharpe", "MDD"])
    pivot.columns = [f"{metric}_{variant}" for metric, variant in pivot.columns]
    pivot = pivot.reset_index()
    pivot.to_csv(output_dir / "variant_walkforward_pivot.csv", index=False, encoding="utf-8-sig")

    if len(args.variants) >= 2:
        lead = args.variants[0]
        ref = args.variants[1]
        lead_cmp = compare[compare["Variant"] == lead][["WindowStart", "WindowEnd", "CAGR", "Sharpe", "MDD"]].rename(
            columns={"CAGR": "LeadCAGR", "Sharpe": "LeadSharpe", "MDD": "LeadMDD"}
        )
        ref_cmp = compare[compare["Variant"] == ref][["WindowStart", "WindowEnd", "CAGR", "Sharpe", "MDD"]].rename(
            columns={"CAGR": "RefCAGR", "Sharpe": "RefSharpe", "MDD": "RefMDD"}
        )
        delta = lead_cmp.merge(ref_cmp, on=["WindowStart", "WindowEnd"], how="inner")
        delta["CAGRDelta"] = pd.to_numeric(delta["LeadCAGR"], errors="coerce") - pd.to_numeric(delta["RefCAGR"], errors="coerce")
        delta["SharpeDelta"] = pd.to_numeric(delta["LeadSharpe"], errors="coerce") - pd.to_numeric(delta["RefSharpe"], errors="coerce")
        delta["MDDDelta"] = pd.to_numeric(delta["LeadMDD"], errors="coerce") - pd.to_numeric(delta["RefMDD"], errors="coerce")
        delta.to_csv(output_dir / "variant_walkforward_delta.csv", index=False, encoding="utf-8-sig")

        summary["lead_vs_reference"] = {
            "lead_variant": lead,
            "reference_variant": ref,
            "windows_compared": int(len(delta)),
            "positive_cagr_windows": int((pd.to_numeric(delta["CAGRDelta"], errors="coerce") > 0).sum()),
            "negative_cagr_windows": int((pd.to_numeric(delta["CAGRDelta"], errors="coerce") < 0).sum()),
            "avg_cagr_delta": float(pd.to_numeric(delta["CAGRDelta"], errors="coerce").mean()),
            "avg_sharpe_delta": float(pd.to_numeric(delta["SharpeDelta"], errors="coerce").mean()),
        }

    (output_dir / "variant_walkforward_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"variants={len(args.variants)}")
    if "lead_vs_reference" in summary:
        print(f"positive_cagr_windows={summary['lead_vs_reference']['positive_cagr_windows']}")
        print(f"negative_cagr_windows={summary['lead_vs_reference']['negative_cagr_windows']}")
        print(f"avg_cagr_delta={summary['lead_vs_reference']['avg_cagr_delta']:.6f}")


if __name__ == "__main__":
    main()


