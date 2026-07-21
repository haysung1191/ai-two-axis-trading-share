from __future__ import annotations

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
DEFAULT_OUTPUT_DIR = ROOT / "output" / "split_models_it_overlay_review"
WEAK_START = pd.Timestamp("2021-04-30")
WEAK_END = pd.Timestamp("2023-08-31")
DEFAULT_BASELINE_NAME = "rule_breadth_risk_off"
DEFAULT_CANDIDATE_NAME = "rule_breadth_it_risk_off"


def _build_backtest_context(cfg: BacktestConfig) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict[str, pd.DataFrame], pd.DataFrame, list[pd.Timestamp]]:
    us_stocks, us_etfs = _load_us_universe()
    kr_universe = _load_kr_universe()
    universe = pd.concat([us_stocks, us_etfs, kr_universe], ignore_index=True)
    price_cache, flow_cache = _build_daily_caches(universe)
    monthly_close = _build_monthly_close_matrix(universe, price_cache)
    signal_dates = _signal_dates(monthly_close, cfg.signal_start)
    return universe, price_cache, flow_cache, monthly_close, signal_dates


def _load_variant_results(
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


def _weak_period_nav(nav: pd.DataFrame, label: str) -> pd.DataFrame:
    out = nav.copy()
    out["SignalDate"] = pd.to_datetime(out["SignalDate"])
    out["NextDate"] = pd.to_datetime(out["NextDate"])
    out = out[(out["SignalDate"] >= WEAK_START) & (out["SignalDate"] <= WEAK_END)].copy()
    return out.rename(
        columns={
            "GrossReturn": f"{label}_GrossReturn",
            "NetReturn": f"{label}_NetReturn",
            "Turnover": f"{label}_Turnover",
            "NAV": f"{label}_NAV",
            "Holdings": f"{label}_Holdings",
        }
    )


def _weak_period_sector_state(positions: pd.DataFrame, label: str) -> pd.DataFrame:
    out = positions.copy()
    out["SignalDate"] = pd.to_datetime(out["SignalDate"])
    out = out[(out["SignalDate"] >= WEAK_START) & (out["SignalDate"] <= WEAK_END)].copy()
    if out.empty:
        return pd.DataFrame(columns=["SignalDate"])

    sector_mix = (
        out.groupby(["SignalDate", "Sector"], as_index=False)
        .agg(SectorWeight=("TargetWeight", "sum"), PositionCount=("Symbol", "count"))
        .sort_values(["SignalDate", "SectorWeight", "PositionCount", "Sector"], ascending=[True, False, False, True])
    )
    dominant = (
        sector_mix.groupby("SignalDate", as_index=False)
        .first()
        .rename(
            columns={
                "Sector": f"{label}_DominantSector",
                "SectorWeight": f"{label}_DominantSectorWeight",
                "PositionCount": f"{label}_DominantSectorCount",
            }
        )
    )
    it_weight = (
        sector_mix[sector_mix["Sector"].eq("Information Technology")]
        .groupby("SignalDate", as_index=False)
        .agg(**{f"{label}_ITWeight": ("SectorWeight", "sum")})
    )
    return dominant.merge(it_weight, on="SignalDate", how="left")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default=DEFAULT_BASELINE_NAME)
    parser.add_argument("--candidate", default=DEFAULT_CANDIDATE_NAME)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_backtest_context(cfg)

    baseline_results = _load_variant_results(cfg, args.baseline, universe, price_cache, flow_cache, monthly_close, signal_dates)
    candidate_results = _load_variant_results(cfg, args.candidate, universe, price_cache, flow_cache, monthly_close, signal_dates)

    baseline_nav = _weak_period_nav(baseline_results["nav"], "Baseline")
    candidate_nav = _weak_period_nav(candidate_results["nav"], "Candidate")
    baseline_sector = _weak_period_sector_state(baseline_results["positions"], "Baseline")
    candidate_sector = _weak_period_sector_state(candidate_results["positions"], "Candidate")

    compare = baseline_nav.merge(candidate_nav, on=["SignalDate", "NextDate"], how="outer")
    compare = compare.merge(baseline_sector, on="SignalDate", how="left")
    compare = compare.merge(candidate_sector, on="SignalDate", how="left")
    compare = compare.sort_values("SignalDate").reset_index(drop=True)

    compare["NetReturnDelta"] = compare["Candidate_NetReturn"] - compare["Baseline_NetReturn"]
    compare["TurnoverDelta"] = compare["Candidate_Turnover"] - compare["Baseline_Turnover"]
    compare["OverlayTriggered"] = (pd.to_numeric(compare["Baseline_ITWeight"], errors="coerce") >= 0.55).astype(int)
    compare["LossMonthBaseline"] = (pd.to_numeric(compare["Baseline_NetReturn"], errors="coerce") < 0).astype(int)
    compare["LossMonthCandidate"] = (pd.to_numeric(compare["Candidate_NetReturn"], errors="coerce") < 0).astype(int)
    compare["LossReduced"] = (
        (compare["LossMonthBaseline"] == 1)
        & (pd.to_numeric(compare["Candidate_NetReturn"], errors="coerce") > pd.to_numeric(compare["Baseline_NetReturn"], errors="coerce"))
    ).astype(int)
    compare.to_csv(output_dir / "weak_period_it_overlay_compare.csv", index=False, encoding="utf-8-sig")

    triggered = compare[compare["OverlayTriggered"] == 1].copy()
    baseline_losses = compare[compare["LossMonthBaseline"] == 1].copy()
    summary = {
        "baseline_variant": args.baseline,
        "candidate_variant": args.candidate,
        "weak_period_start": str(WEAK_START.date()),
        "weak_period_end": str(WEAK_END.date()),
        "months_compared": int(len(compare)),
        "overlay_triggered_months": int(len(triggered)),
        "baseline_loss_months": int(len(baseline_losses)),
        "loss_months_improved": int(compare["LossReduced"].sum()),
        "avg_net_return_delta_all_months": float(pd.to_numeric(compare["NetReturnDelta"], errors="coerce").mean()),
        "avg_net_return_delta_triggered_months": float(pd.to_numeric(triggered["NetReturnDelta"], errors="coerce").mean()) if not triggered.empty else 0.0,
        "avg_net_return_delta_loss_months": float(pd.to_numeric(baseline_losses["NetReturnDelta"], errors="coerce").mean()) if not baseline_losses.empty else 0.0,
        "worst_baseline_month": None if baseline_losses.empty else str(baseline_losses.sort_values("Baseline_NetReturn").iloc[0]["SignalDate"].date()),
        "best_delta_month": None if compare.empty else str(compare.sort_values("NetReturnDelta", ascending=False).iloc[0]["SignalDate"].date()),
        "worst_delta_month": None if compare.empty else str(compare.sort_values("NetReturnDelta", ascending=True).iloc[0]["SignalDate"].date()),
    }
    (output_dir / "weak_period_it_overlay_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"months_compared={summary['months_compared']}")
    print(f"overlay_triggered_months={summary['overlay_triggered_months']}")
    print(f"loss_months_improved={summary['loss_months_improved']}")
    print(f"avg_net_return_delta_triggered_months={summary['avg_net_return_delta_triggered_months']:.6f}")


if __name__ == "__main__":
    main()


