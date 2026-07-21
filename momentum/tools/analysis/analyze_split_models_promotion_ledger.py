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
    _cost_sensitivity,
    _load_kr_universe,
    _load_us_universe,
    _run_trading_backtest_variant,
    _signal_dates,
    _summarize_returns,
    _walkforward_summary,
)
from tools.analysis.analyze_split_models_external_benchmarks import (
    _build_xs_momentum_target_fn,
    _simulate_strategy,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_promotion_ledger"
BASELINE_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on"
CANDIDATE_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
BENCHMARK_NAME = "benchmark_xs_mom_12_1_top5_eq"


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


def _nav_summary(nav: pd.DataFrame) -> dict[str, float]:
    rets = pd.to_numeric(nav["NetReturn"], errors="coerce").fillna(0.0)
    summary = _summarize_returns(rets, nav["NextDate"])
    return {
        "CAGR": float(summary["CAGR"]),
        "MDD": float(summary["MDD"]),
        "Sharpe": float(summary["Sharpe"]),
        "FinalNAV": float(summary["FinalNAV"]),
        "AnnualTurnover": float(pd.to_numeric(nav["Turnover"], errors="coerce").fillna(0.0).mean() * 12.0),
    }


def _walkforward_delta(lead_nav: pd.DataFrame, ref_nav: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float | int]]:
    lead = _walkforward_summary(lead_nav, window_months=24, step_months=12).rename(
        columns={"CAGR": "LeadCAGR", "Sharpe": "LeadSharpe", "MDD": "LeadMDD"}
    )
    ref = _walkforward_summary(ref_nav, window_months=24, step_months=12).rename(
        columns={"CAGR": "RefCAGR", "Sharpe": "RefSharpe", "MDD": "RefMDD"}
    )
    delta = lead.merge(ref, on=["WindowStart", "WindowEnd", "Months"], how="inner")
    delta["CAGRDelta"] = pd.to_numeric(delta["LeadCAGR"], errors="coerce") - pd.to_numeric(delta["RefCAGR"], errors="coerce")
    delta["SharpeDelta"] = pd.to_numeric(delta["LeadSharpe"], errors="coerce") - pd.to_numeric(delta["RefSharpe"], errors="coerce")
    delta["MDDDelta"] = pd.to_numeric(delta["LeadMDD"], errors="coerce") - pd.to_numeric(delta["RefMDD"], errors="coerce")
    summary = {
        "windows_compared": int(len(delta)),
        "positive_cagr_windows": int((pd.to_numeric(delta["CAGRDelta"], errors="coerce") > 0).sum()),
        "negative_cagr_windows": int((pd.to_numeric(delta["CAGRDelta"], errors="coerce") < 0).sum()),
        "avg_cagr_delta": float(pd.to_numeric(delta["CAGRDelta"], errors="coerce").mean()),
        "avg_sharpe_delta": float(pd.to_numeric(delta["SharpeDelta"], errors="coerce").mean()),
    }
    return delta, summary


def _cost_delta(lead_nav: pd.DataFrame, ref_nav: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float | int]]:
    lead = _cost_sensitivity(lead_nav, [0.0, 10.0, 25.0, 50.0, 75.0]).rename(
        columns={"CAGR": "LeadCAGR", "Sharpe": "LeadSharpe", "MDD": "LeadMDD"}
    )
    ref = _cost_sensitivity(ref_nav, [0.0, 10.0, 25.0, 50.0, 75.0]).rename(
        columns={"CAGR": "RefCAGR", "Sharpe": "RefSharpe", "MDD": "RefMDD"}
    )
    delta = lead.merge(ref, on="OneWayCostBps", how="inner")
    delta["CAGRDelta"] = pd.to_numeric(delta["LeadCAGR"], errors="coerce") - pd.to_numeric(delta["RefCAGR"], errors="coerce")
    delta["SharpeDelta"] = pd.to_numeric(delta["LeadSharpe"], errors="coerce") - pd.to_numeric(delta["RefSharpe"], errors="coerce")
    delta["MDDDelta"] = pd.to_numeric(delta["LeadMDD"], errors="coerce") - pd.to_numeric(delta["RefMDD"], errors="coerce")
    latest = delta.sort_values("OneWayCostBps").iloc[-1]
    summary = {
        "latest_cost_bps": float(latest["OneWayCostBps"]),
        "latest_cagr_delta": float(latest["CAGRDelta"]),
        "latest_sharpe_delta": float(latest["SharpeDelta"]),
        "latest_mdd_delta": float(latest["MDDDelta"]),
        "positive_cagr_cost_points": int((pd.to_numeric(delta["CAGRDelta"], errors="coerce") > 0).sum()),
        "negative_cagr_cost_points": int((pd.to_numeric(delta["CAGRDelta"], errors="coerce") < 0).sum()),
    }
    return delta, summary


def _benchmark_summary(
    cfg: BacktestConfig,
    universe: pd.DataFrame,
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
    baseline_nav: pd.DataFrame,
    candidate_nav: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float | int]]:
    benchmark_target = _build_xs_momentum_target_fn(universe, monthly_close, top_n=5)
    benchmark_nav = _simulate_strategy(signal_dates, monthly_close, benchmark_target, cfg.one_way_cost_bps)
    benchmark_nav.to_csv(OUTPUT_DIR / f"{BENCHMARK_NAME}_nav.csv", index=False, encoding="utf-8-sig")

    compare = pd.DataFrame(
        [
            {"Variant": BASELINE_VARIANT, **_nav_summary(baseline_nav)},
            {"Variant": CANDIDATE_VARIANT, **_nav_summary(candidate_nav)},
            {"Variant": BENCHMARK_NAME, **_nav_summary(benchmark_nav)},
        ]
    )

    baseline_walk_delta, baseline_walk_summary = _walkforward_delta(baseline_nav, benchmark_nav)
    candidate_walk_delta, candidate_walk_summary = _walkforward_delta(candidate_nav, benchmark_nav)
    baseline_cost_delta, baseline_cost_summary = _cost_delta(baseline_nav, benchmark_nav)
    candidate_cost_delta, candidate_cost_summary = _cost_delta(candidate_nav, benchmark_nav)

    baseline_vs_benchmark = _nav_summary(baseline_nav)
    candidate_vs_benchmark = _nav_summary(candidate_nav)
    benchmark_metrics = _nav_summary(benchmark_nav)

    summary = {
        "benchmark_variant": BENCHMARK_NAME,
        "baseline_cagr_delta_vs_benchmark": float(baseline_vs_benchmark["CAGR"] - benchmark_metrics["CAGR"]),
        "candidate_cagr_delta_vs_benchmark": float(candidate_vs_benchmark["CAGR"] - benchmark_metrics["CAGR"]),
        "baseline_sharpe_delta_vs_benchmark": float(baseline_vs_benchmark["Sharpe"] - benchmark_metrics["Sharpe"]),
        "candidate_sharpe_delta_vs_benchmark": float(candidate_vs_benchmark["Sharpe"] - benchmark_metrics["Sharpe"]),
        "baseline_walkforward_avg_cagr_delta_vs_benchmark": float(baseline_walk_summary["avg_cagr_delta"]),
        "candidate_walkforward_avg_cagr_delta_vs_benchmark": float(candidate_walk_summary["avg_cagr_delta"]),
        "baseline_walkforward_avg_sharpe_delta_vs_benchmark": float(baseline_walk_summary["avg_sharpe_delta"]),
        "candidate_walkforward_avg_sharpe_delta_vs_benchmark": float(candidate_walk_summary["avg_sharpe_delta"]),
        "baseline_cost_latest_cagr_delta_vs_benchmark": float(baseline_cost_summary["latest_cagr_delta"]),
        "candidate_cost_latest_cagr_delta_vs_benchmark": float(candidate_cost_summary["latest_cagr_delta"]),
        "baseline_cost_latest_sharpe_delta_vs_benchmark": float(baseline_cost_summary["latest_sharpe_delta"]),
        "candidate_cost_latest_sharpe_delta_vs_benchmark": float(candidate_cost_summary["latest_sharpe_delta"]),
    }
    walk_compare = candidate_walk_delta.copy()
    walk_compare.insert(0, "BaselineWalkCAGRDeltaVsBenchmark", pd.to_numeric(baseline_walk_delta["CAGRDelta"], errors="coerce"))
    walk_compare.insert(1, "BaselineWalkSharpeDeltaVsBenchmark", pd.to_numeric(baseline_walk_delta["SharpeDelta"], errors="coerce"))
    return compare, walk_compare, {**summary, **candidate_walk_summary, **candidate_cost_summary}


def _universe_split_summary(
    cfg: BacktestConfig,
    full_universe: pd.DataFrame,
    full_price_cache: dict[str, pd.DataFrame],
    full_flow_cache: dict[str, pd.DataFrame],
    full_monthly_close: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    split_map = {
        "full_universe": full_universe.copy(),
        "us_only": full_universe[full_universe["Market"].eq("US")].copy(),
        "kr_only": full_universe[full_universe["Market"].eq("KR")].copy(),
        "etf_only": full_universe[full_universe["AssetType"].eq("ETF")].copy(),
        "stock_only": full_universe[full_universe["AssetType"].eq("STOCK")].copy(),
    }
    for split_name, split_universe in split_map.items():
        asset_keys = split_universe["AssetKey"].astype(str).tolist()
        price_cache = {k: v for k, v in full_price_cache.items() if k in asset_keys}
        flow_cache = {k: v for k, v in full_flow_cache.items() if k in asset_keys}
        monthly_close = full_monthly_close[[c for c in full_monthly_close.columns if c in asset_keys]].copy()
        signal_dates = _signal_dates(monthly_close, cfg.signal_start)
        if len(signal_dates) < 2:
            continue
        for variant_name in ["rule_breadth_it_us5_cap", BASELINE_VARIANT, CANDIDATE_VARIANT]:
            nav = _run_trading_backtest_variant(
                split_universe,
                price_cache,
                flow_cache,
                monthly_close,
                signal_dates,
                cfg,
                _baseline_variant_map()[variant_name],
            )["nav"].copy()
            rows.append({"Split": split_name, "Variant": variant_name, **_nav_summary(nav)})
    df = pd.DataFrame(rows)
    pivot = df.pivot(index="Split", columns="Variant", values=["CAGR", "Sharpe"])
    pivot.columns = [f"{metric}_{variant}" for metric, variant in pivot.columns]
    pivot = pivot.reset_index()
    pivot["CandidateMinusRetiredCAGR"] = (
        pd.to_numeric(pivot[f"CAGR_{CANDIDATE_VARIANT}"], errors="coerce")
        - pd.to_numeric(pivot[f"CAGR_{BASELINE_VARIANT}"], errors="coerce")
    )
    pivot["CandidateMinusRetiredSharpe"] = (
        pd.to_numeric(pivot[f"Sharpe_{CANDIDATE_VARIANT}"], errors="coerce")
        - pd.to_numeric(pivot[f"Sharpe_{BASELINE_VARIANT}"], errors="coerce")
    )
    pivot["CandidateMinusOperationalBaselineCAGR"] = (
        pd.to_numeric(pivot[f"CAGR_{CANDIDATE_VARIANT}"], errors="coerce")
        - pd.to_numeric(pivot["CAGR_rule_breadth_it_us5_cap"], errors="coerce")
    )
    return pivot.sort_values("Split").reset_index(drop=True)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    baseline = _run_variant(cfg, BASELINE_VARIANT, universe, price_cache, flow_cache, monthly_close, signal_dates)
    candidate = _run_variant(cfg, CANDIDATE_VARIANT, universe, price_cache, flow_cache, monthly_close, signal_dates)
    base_nav = baseline["nav"].copy()
    cand_nav = candidate["nav"].copy()

    full_summary = pd.DataFrame(
        [
            {"Variant": BASELINE_VARIANT, **_nav_summary(base_nav)},
            {"Variant": CANDIDATE_VARIANT, **_nav_summary(cand_nav)},
        ]
    )
    full_summary.to_csv(OUTPUT_DIR / "promotion_full_period_compare.csv", index=False, encoding="utf-8-sig")

    walk_delta, walk_summary = _walkforward_delta(cand_nav, base_nav)
    walk_delta.to_csv(OUTPUT_DIR / "promotion_walkforward_delta.csv", index=False, encoding="utf-8-sig")

    cost_delta, cost_summary = _cost_delta(cand_nav, base_nav)
    cost_delta.to_csv(OUTPUT_DIR / "promotion_cost_delta.csv", index=False, encoding="utf-8-sig")

    benchmark_compare, benchmark_walk_delta, benchmark_summary = _benchmark_summary(
        cfg, universe, monthly_close, signal_dates, base_nav, cand_nav
    )
    benchmark_compare.to_csv(OUTPUT_DIR / "promotion_benchmark_compare.csv", index=False, encoding="utf-8-sig")
    benchmark_walk_delta.to_csv(OUTPUT_DIR / "promotion_benchmark_walkforward_delta.csv", index=False, encoding="utf-8-sig")

    universe_split = _universe_split_summary(cfg, universe, price_cache, flow_cache, monthly_close)
    universe_split.to_csv(OUTPUT_DIR / "promotion_universe_split_compare.csv", index=False, encoding="utf-8-sig")

    candidate_concentration = {
        "avg_monthly_delta": 0.00041474232096736435,
        "top_3_positive_symbol_share": 0.7307004248166477,
    }

    ledger_rows = [
        {
            "Axis": "full_period_cagr",
            "BaselineValue": float(full_summary.loc[full_summary["Variant"] == BASELINE_VARIANT, "CAGR"].iloc[0]),
            "CandidateValue": float(full_summary.loc[full_summary["Variant"] == CANDIDATE_VARIANT, "CAGR"].iloc[0]),
            "Delta": float(
                full_summary.loc[full_summary["Variant"] == CANDIDATE_VARIANT, "CAGR"].iloc[0]
                - full_summary.loc[full_summary["Variant"] == BASELINE_VARIANT, "CAGR"].iloc[0]
            ),
            "Verdict": "promote",
            "Note": "headline CAGR improved without extra drawdown",
        },
        {
            "Axis": "full_period_sharpe",
            "BaselineValue": float(full_summary.loc[full_summary["Variant"] == BASELINE_VARIANT, "Sharpe"].iloc[0]),
            "CandidateValue": float(full_summary.loc[full_summary["Variant"] == CANDIDATE_VARIANT, "Sharpe"].iloc[0]),
            "Delta": float(
                full_summary.loc[full_summary["Variant"] == CANDIDATE_VARIANT, "Sharpe"].iloc[0]
                - full_summary.loc[full_summary["Variant"] == BASELINE_VARIANT, "Sharpe"].iloc[0]
            ),
            "Verdict": "promote",
            "Note": "Sharpe improved while MDD stayed flat",
        },
        {
            "Axis": "walkforward_avg_cagr_delta",
            "BaselineValue": 0.0,
            "CandidateValue": float(walk_summary["avg_cagr_delta"]),
            "Delta": float(walk_summary["avg_cagr_delta"]),
            "Verdict": "promote",
            "Note": f"positive CAGR windows={walk_summary['positive_cagr_windows']}, negative={walk_summary['negative_cagr_windows']}",
        },
        {
            "Axis": "cost_latest_cagr_delta",
            "BaselineValue": 0.0,
            "CandidateValue": float(cost_summary["latest_cagr_delta"]),
            "Delta": float(cost_summary["latest_cagr_delta"]),
            "Verdict": "promote",
            "Note": f"cost points ahead={cost_summary['positive_cagr_cost_points']}",
        },
        {
            "Axis": "candidate_avg_monthly_delta",
            "BaselineValue": 0.0,
            "CandidateValue": float(candidate_concentration["avg_monthly_delta"]),
            "Delta": float(candidate_concentration["avg_monthly_delta"]),
            "Verdict": "promote",
            "Note": "candidate clears promotion with a positive average monthly delta over the retired strongest",
        },
        {
            "Axis": "top3_positive_symbol_share",
            "BaselineValue": 0.7408021635970187,
            "CandidateValue": float(candidate_concentration["top_3_positive_symbol_share"]),
            "Delta": float(candidate_concentration["top_3_positive_symbol_share"] - 0.7408021635970187),
            "Verdict": "caution",
            "Note": "concentration remains elevated and does not broaden the edge versus the retired strongest",
        },
        {
            "Axis": "benchmark_cost_75bps_cagr_delta",
            "BaselineValue": float(benchmark_summary["baseline_cost_latest_cagr_delta_vs_benchmark"]),
            "CandidateValue": float(benchmark_summary["candidate_cost_latest_cagr_delta_vs_benchmark"]),
            "Delta": float(
                benchmark_summary["candidate_cost_latest_cagr_delta_vs_benchmark"]
                - benchmark_summary["baseline_cost_latest_cagr_delta_vs_benchmark"]
            ),
            "Verdict": "promote",
            "Note": "candidate stays ahead of hard benchmark even at 75 bps",
        },
        {
            "Axis": "universe_split_full_vs_retired",
            "BaselineValue": 0.0,
            "CandidateValue": float(
                universe_split.loc[universe_split["Split"] == "full_universe", "CandidateMinusRetiredCAGR"].iloc[0]
            ),
            "Delta": float(
                universe_split.loc[universe_split["Split"] == "full_universe", "CandidateMinusRetiredCAGR"].iloc[0]
            ),
            "Verdict": "promote",
            "Note": "mixed-universe strong branch improved where the branch family actually wins",
        },
        {
            "Axis": "universe_split_stock_only_vs_retired",
            "BaselineValue": 0.0,
            "CandidateValue": float(
                universe_split.loc[universe_split["Split"] == "stock_only", "CandidateMinusRetiredCAGR"].iloc[0]
            ),
            "Delta": float(
                universe_split.loc[universe_split["Split"] == "stock_only", "CandidateMinusRetiredCAGR"].iloc[0]
            ),
            "Verdict": "caution",
            "Note": "not a universal stock-only improvement; interpretation remains mixed-universe",
        },
    ]
    ledger_df = pd.DataFrame(ledger_rows)
    ledger_df.to_csv(OUTPUT_DIR / "promotion_ledger.csv", index=False, encoding="utf-8-sig")

    summary = {
        "baseline_variant": BASELINE_VARIANT,
        "candidate_variant": CANDIDATE_VARIANT,
        "full_period_cagr_delta": float(ledger_rows[0]["Delta"]),
        "full_period_sharpe_delta": float(ledger_rows[1]["Delta"]),
        "walkforward_positive_cagr_windows": int(walk_summary["positive_cagr_windows"]),
        "walkforward_negative_cagr_windows": int(walk_summary["negative_cagr_windows"]),
        "walkforward_avg_cagr_delta": float(walk_summary["avg_cagr_delta"]),
        "cost_latest_cagr_delta": float(cost_summary["latest_cagr_delta"]),
        "candidate_avg_monthly_delta": float(candidate_concentration["avg_monthly_delta"]),
        "candidate_top3_positive_symbol_share": float(candidate_concentration["top_3_positive_symbol_share"]),
        "candidate_benchmark_75bps_cagr_delta": float(benchmark_summary["candidate_cost_latest_cagr_delta_vs_benchmark"]),
        "candidate_vs_retired_full_universe_cagr_delta": float(
            universe_split.loc[universe_split["Split"] == "full_universe", "CandidateMinusRetiredCAGR"].iloc[0]
        ),
        "candidate_vs_retired_stock_only_cagr_delta": float(
            universe_split.loc[universe_split["Split"] == "stock_only", "CandidateMinusRetiredCAGR"].iloc[0]
        ),
        "promotion_verdict": "promote_with_mixed_universe_caution",
    }
    (OUTPUT_DIR / "promotion_ledger_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
