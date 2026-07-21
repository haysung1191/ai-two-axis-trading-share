from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import sys
from typing import Callable

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import split_models.backtest as bt
from split_models.backtest import (
    BacktestConfig,
    TradingVariant,
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


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_tradeoff_frontier_review"
BASE_VARIANT_NAME = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
EXCLUDED_SYMBOLS = {"PLTR", "NVDA", "MU"}


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


def _share_of_positive(series: pd.Series, top_n: int) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    positive = values[values > 0]
    total = float(positive.sum())
    if total <= 0 or positive.empty:
        return 0.0
    return float(positive.nlargest(min(top_n, len(positive))).sum() / total)


def _run_with_patch(
    variant: TradingVariant,
    patch_fn: Callable[[pd.DataFrame], pd.DataFrame] | None,
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
    cfg: BacktestConfig,
) -> dict[str, pd.DataFrame]:
    if patch_fn is None:
        return _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)

    original = bt._build_momentum_candidates_for_date

    def wrapped_build(metrics, flow_snapshot, cfg_inner, variant=None, prev_hold_keys=None, **kwargs):
        variant_inner = variant
        book = original(
            metrics,
            flow_snapshot,
            cfg_inner,
            variant=variant_inner,
            prev_hold_keys=prev_hold_keys,
            **kwargs,
        )
        if variant_inner.name != variant.name:
            return book
        return patch_fn(book)

    bt._build_momentum_candidates_for_date = wrapped_build
    try:
        return _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)
    finally:
        bt._build_momentum_candidates_for_date = original


def _patch_hybrid_top2_plus_third(extra_weight: float) -> Callable[[pd.DataFrame], pd.DataFrame]:
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 3:
            return book
        out = book.copy()
        original_total = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        third_index = ranked.index[2]
        out.loc[third_index, "TargetWeight"] = float(out.loc[third_index, "TargetWeight"]) + float(extra_weight)
        new_total = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        if new_total > 0:
            out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0) * (original_total / new_total)
        return out

    return patch


def _patch_top2_split(first_share: float, second_share: float) -> Callable[[pd.DataFrame], pd.DataFrame]:
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 2:
            return book
        out = book.copy()
        ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        first_index = ranked.index[0]
        second_index = ranked.index[1]
        pair_total = float(pd.to_numeric(out.loc[[first_index, second_index], "TargetWeight"], errors="coerce").fillna(0.0).sum())
        out.loc[first_index, "TargetWeight"] = pair_total * float(first_share)
        out.loc[second_index, "TargetWeight"] = pair_total * float(second_share)
        return out

    return patch


def _patch_bonus_schedule(first_share: float, second_share: float, bonus_total: float = 0.18) -> Callable[[pd.DataFrame], pd.DataFrame]:
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 2:
            return book
        out = book.copy()
        original_total = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        top_index = ranked.head(2).index.tolist()
        equal_piece = float(bonus_total) / 2.0
        for idx in top_index:
            out.loc[idx, "TargetWeight"] = float(out.loc[idx, "TargetWeight"]) - equal_piece
        out.loc[top_index[0], "TargetWeight"] = float(out.loc[top_index[0], "TargetWeight"]) + float(bonus_total) * float(first_share)
        out.loc[top_index[1], "TargetWeight"] = float(out.loc[top_index[1], "TargetWeight"]) + float(bonus_total) * float(second_share)
        new_total = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        if new_total > 0:
            out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0) * (original_total / new_total)
        return out

    return patch


def _patch_bonus_recipients(first_share: float, third_share: float, bonus_total: float = 0.18) -> Callable[[pd.DataFrame], pd.DataFrame]:
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 3:
            return book
        out = book.copy()
        original_total = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        first_index = ranked.index[0]
        second_index = ranked.index[1]
        third_index = ranked.index[2]
        equal_piece = float(bonus_total) / 2.0
        out.loc[first_index, "TargetWeight"] = float(out.loc[first_index, "TargetWeight"]) - equal_piece
        out.loc[second_index, "TargetWeight"] = float(out.loc[second_index, "TargetWeight"]) - equal_piece
        out.loc[first_index, "TargetWeight"] = float(out.loc[first_index, "TargetWeight"]) + float(bonus_total) * float(first_share)
        out.loc[third_index, "TargetWeight"] = float(out.loc[third_index, "TargetWeight"]) + float(bonus_total) * float(third_share)
        new_total = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        if new_total > 0:
            out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0) * (original_total / new_total)
        return out

    return patch


def _patch_skip_entry_flowweakest_new_bottom4_top25_mid75() -> Callable[[pd.DataFrame], pd.DataFrame]:
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 6:
            return book
        out = book.copy()
        ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        candidate_pool = ranked.iloc[2:].copy()
        if candidate_pool.empty:
            return out
        bottom_slice = candidate_pool.tail(min(4, len(candidate_pool)))
        if bottom_slice.empty:
            return out
        drop_row = bottom_slice.sort_values(["FlowScore", "MomentumScore", "Symbol"], ascending=[True, True, True]).head(1)
        drop_index = drop_row.index[0]
        released = float(out.loc[drop_index, "TargetWeight"])
        out = out.drop(index=drop_index).copy()
        if released > 0 and not out.empty:
            reranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
            top_index = reranked.head(2).index
            mid_index = reranked.iloc[2:5].index
            top_share = released * 0.25
            mid_share = released * 0.75
            if len(top_index) > 0:
                out.loc[top_index, "TargetWeight"] = out.loc[top_index, "TargetWeight"].astype(float) + top_share / float(len(top_index))
            if len(mid_index) > 0:
                out.loc[mid_index, "TargetWeight"] = out.loc[mid_index, "TargetWeight"].astype(float) + mid_share / float(len(mid_index))
            total = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
            if total > 0:
                out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0) / total
        return out

    return patch


def _patch_tail_release_to_nonbottom_proportional() -> Callable[[pd.DataFrame], pd.DataFrame]:
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 4:
            return book
        out = book.copy()
        ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        top_index = ranked.head(2).index
        candidate_bottom = ranked.loc[~ranked.index.isin(top_index)]
        if candidate_bottom.empty:
            return out
        bottom_count = min(6, len(candidate_bottom))
        bottom_index = candidate_bottom.tail(bottom_count).index
        bottom_before = pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0).copy()
        if len(bottom_index) > 1:
            penalty_steps = pd.Series(np.linspace(0.0, 1.0, len(bottom_index)) ** 0.50, index=bottom_index)
            penalty_series = pd.Series(0.35 + (0.20 - 0.35) * penalty_steps, index=bottom_index)
            out.loc[bottom_index, "TargetWeight"] = (
                pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0) * penalty_series
            )
        else:
            out.loc[bottom_index, "TargetWeight"] = (
                pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0) * 0.35
            )
        released = float(
            bottom_before.sum() - pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0).sum()
        )
        if released > 0:
            recipients = ranked.loc[~ranked.index.isin(bottom_index)].index
            recipient_weights = pd.to_numeric(out.loc[recipients, "TargetWeight"], errors="coerce").fillna(0.0)
            total = float(recipient_weights.sum())
            if total > 0:
                out.loc[recipients, "TargetWeight"] = recipient_weights + released * (recipient_weights / total)
        total_after = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        if total_after > 0:
            out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0) / total_after
        return out

    return patch


def _patch_tail_release_top50_mid50() -> Callable[[pd.DataFrame], pd.DataFrame]:
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 5:
            return book
        out = book.copy()
        ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        top_index = ranked.head(2).index
        candidate_bottom = ranked.loc[~ranked.index.isin(top_index)]
        if candidate_bottom.empty:
            return out
        bottom_count = min(6, len(candidate_bottom))
        bottom_index = candidate_bottom.tail(bottom_count).index
        bottom_before = pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0).copy()
        if len(bottom_index) > 1:
            penalty_steps = pd.Series(np.linspace(0.0, 1.0, len(bottom_index)) ** 0.50, index=bottom_index)
            penalty_series = pd.Series(0.35 + (0.20 - 0.35) * penalty_steps, index=bottom_index)
            out.loc[bottom_index, "TargetWeight"] = (
                pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0) * penalty_series
            )
        else:
            out.loc[bottom_index, "TargetWeight"] = (
                pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0) * 0.35
            )
        released = float(
            bottom_before.sum() - pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0).sum()
        )
        if released > 0:
            top2_part = released * 0.50
            mid_part = released - top2_part
            out.loc[top_index, "TargetWeight"] = (
                pd.to_numeric(out.loc[top_index, "TargetWeight"], errors="coerce").fillna(0.0)
                + top2_part / float(len(top_index))
            )
            mid_index = ranked.loc[~ranked.index.isin(bottom_index.union(top_index))].index
            if len(mid_index) > 0 and mid_part > 0:
                mid_weights = pd.to_numeric(out.loc[mid_index, "TargetWeight"], errors="coerce").fillna(0.0)
                total = float(mid_weights.sum())
                if total > 0:
                    out.loc[mid_index, "TargetWeight"] = mid_weights + mid_part * (mid_weights / total)
                else:
                    out.loc[mid_index, "TargetWeight"] = mid_weights + mid_part / float(len(mid_index))
        total_after = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        if total_after > 0:
            out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0) / total_after
        return out

    return patch


def _patch_multi_step_confirm_top1_flowtop2() -> Callable[[pd.DataFrame], pd.DataFrame]:
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 3:
            return book
        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        mom_ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        flow_ranked = out.sort_values(["FlowScore", "MomentumScore", "Symbol"], ascending=[False, False, True])
        top_idx = mom_ranked.index[0]
        second_idx = mom_ranked.index[1]
        top_symbol = str(mom_ranked.iloc[0]["Symbol"])
        top2_flow_symbols = set(flow_ranked.head(2)["Symbol"].astype(str).tolist())
        if top_symbol in top2_flow_symbols:
            return out
        donor_weight = float(out.loc[top_idx, "TargetWeight"])
        shift = min(0.03, donor_weight * 0.4)
        if shift <= 0:
            return out
        out.loc[top_idx, "TargetWeight"] = donor_weight - shift
        out.loc[second_idx, "TargetWeight"] = float(out.loc[second_idx, "TargetWeight"]) + shift
        total_after = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        if total_after > 0:
            out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0) / total_after
        return out

    return patch


def _patch_regime_weight_defensive_if_top2flowsoft() -> Callable[[pd.DataFrame], pd.DataFrame]:
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 4 or "FlowScore" not in book.columns:
            return book
        out = book.copy()
        out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0)
        out["FlowScore"] = pd.to_numeric(out["FlowScore"], errors="coerce").fillna(0.0)
        ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        top_idx = ranked.head(2).index
        top_flow_avg = float(ranked.head(2)["FlowScore"].mean())
        book_flow_median = float(ranked["FlowScore"].median())
        if top_flow_avg >= book_flow_median:
            return out
        top_weights = pd.to_numeric(out.loc[top_idx, "TargetWeight"], errors="coerce").fillna(0.0)
        top_total = float(top_weights.sum())
        shift = min(0.05, top_total * 0.25)
        if shift <= 0:
            return out
        out.loc[top_idx, "TargetWeight"] = top_weights - shift * (top_weights / top_total)
        rest_idx = ranked.index[2:]
        rest_weights = pd.to_numeric(out.loc[rest_idx, "TargetWeight"], errors="coerce").fillna(0.0)
        rest_total = float(rest_weights.sum())
        if rest_total > 0:
            out.loc[rest_idx, "TargetWeight"] = rest_weights + shift * (rest_weights / rest_total)
        else:
            out.loc[rest_idx, "TargetWeight"] = rest_weights + shift / float(len(rest_idx))
        total_after = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        if total_after > 0:
            out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0) / total_after
        return out

    return patch


def _summarize_candidate(
    name: str,
    result: dict[str, pd.DataFrame],
    base_result: dict[str, pd.DataFrame],
) -> dict[str, float | int | str]:
    nav = result["nav"].copy()
    base_nav = base_result["nav"].copy()
    summary = _summarize_returns(nav["NetReturn"], nav["NextDate"])
    annual_turnover = float(pd.to_numeric(nav["Turnover"], errors="coerce").fillna(0.0).mean() * 12.0)

    walk = _walkforward_summary(nav, window_months=24, step_months=12)
    base_walk = _walkforward_summary(base_nav, window_months=24, step_months=12)
    walk_compare = walk[["WindowStart", "WindowEnd", "CAGR", "Sharpe"]].merge(
        base_walk[["WindowStart", "WindowEnd", "CAGR", "Sharpe"]],
        on=["WindowStart", "WindowEnd"],
        how="inner",
        suffixes=("_candidate", "_base"),
    )
    walk_compare["CAGRDelta"] = (
        pd.to_numeric(walk_compare["CAGR_candidate"], errors="coerce")
        - pd.to_numeric(walk_compare["CAGR_base"], errors="coerce")
    )
    walk_compare["SharpeDelta"] = (
        pd.to_numeric(walk_compare["Sharpe_candidate"], errors="coerce")
        - pd.to_numeric(walk_compare["Sharpe_base"], errors="coerce")
    )

    cost = _cost_sensitivity(nav, [0, 10, 25, 50, 75])
    base_cost = _cost_sensitivity(base_nav, [0, 10, 25, 50, 75])
    cost_compare = cost[["OneWayCostBps", "CAGR", "Sharpe"]].merge(
        base_cost[["OneWayCostBps", "CAGR", "Sharpe"]],
        on="OneWayCostBps",
        how="inner",
        suffixes=("_candidate", "_base"),
    )
    cost_compare["CAGRDelta"] = (
        pd.to_numeric(cost_compare["CAGR_candidate"], errors="coerce")
        - pd.to_numeric(cost_compare["CAGR_base"], errors="coerce")
    )
    cost_compare["SharpeDelta"] = (
        pd.to_numeric(cost_compare["Sharpe_candidate"], errors="coerce")
        - pd.to_numeric(cost_compare["Sharpe_base"], errors="coerce")
    )

    for df in (nav, base_nav):
        df["SignalDate"] = pd.to_datetime(df["SignalDate"])
        df["NextDate"] = pd.to_datetime(df["NextDate"])
    nav_compare = nav[["SignalDate", "NextDate", "NetReturn"]].merge(
        base_nav[["SignalDate", "NextDate", "NetReturn"]],
        on=["SignalDate", "NextDate"],
        how="inner",
        suffixes=("_candidate", "_base"),
    )
    nav_compare["TotalDelta"] = (
        pd.to_numeric(nav_compare["NetReturn_candidate"], errors="coerce")
        - pd.to_numeric(nav_compare["NetReturn_base"], errors="coerce")
    )

    symbol = result["symbol_contrib"].copy()
    base_symbol = base_result["symbol_contrib"].copy()
    for df in (symbol, base_symbol):
        df["SignalDate"] = pd.to_datetime(df["SignalDate"])
        df["NextDate"] = pd.to_datetime(df["NextDate"])
    symbol_compare = symbol.merge(
        base_symbol,
        on=["SignalDate", "NextDate", "Symbol", "Market", "Sector"],
        how="outer",
        suffixes=("_candidate", "_base"),
    ).fillna({"Contribution_candidate": 0.0, "Contribution_base": 0.0})
    symbol_compare["ContributionDelta"] = (
        pd.to_numeric(symbol_compare["Contribution_candidate"], errors="coerce").fillna(0.0)
        - pd.to_numeric(symbol_compare["Contribution_base"], errors="coerce").fillna(0.0)
    )
    symbol_compare["Excluded"] = symbol_compare["Symbol"].isin(EXCLUDED_SYMBOLS)

    excluded_monthly = (
        symbol_compare[symbol_compare["Excluded"]]
        .groupby(["SignalDate", "NextDate"], as_index=False)
        .agg(ExcludedDelta=("ContributionDelta", "sum"))
    )
    residual = nav_compare.merge(excluded_monthly, on=["SignalDate", "NextDate"], how="left").fillna({"ExcludedDelta": 0.0})
    residual["ResidualDelta"] = residual["TotalDelta"] - residual["ExcludedDelta"]

    symbol_summary = (
        symbol_compare.groupby(["Market", "Sector", "Symbol"], as_index=False)
        .agg(ContributionDelta=("ContributionDelta", "sum"))
        .sort_values("ContributionDelta", ascending=False)
    )

    return {
        "Variant": name,
        "CAGR": float(summary["CAGR"]),
        "MDD": float(summary["MDD"]),
        "Sharpe": float(summary["Sharpe"]),
        "AnnualTurnover": annual_turnover,
        "CAGRDeltaVsStrongest": float(summary["CAGR"] - _summarize_returns(base_nav["NetReturn"], base_nav["NextDate"])["CAGR"]),
        "SharpeDeltaVsStrongest": float(summary["Sharpe"] - _summarize_returns(base_nav["NetReturn"], base_nav["NextDate"])["Sharpe"]),
        "MDDDeltaVsStrongest": float(summary["MDD"] - _summarize_returns(base_nav["NetReturn"], base_nav["NextDate"])["MDD"]),
        "PositiveCAGRWindows": int((pd.to_numeric(walk_compare["CAGRDelta"], errors="coerce") > 0).sum()),
        "NegativeCAGRWindows": int((pd.to_numeric(walk_compare["CAGRDelta"], errors="coerce") < 0).sum()),
        "AvgWalkforwardCAGRDelta": float(pd.to_numeric(walk_compare["CAGRDelta"], errors="coerce").mean()),
        "AvgWalkforwardSharpeDelta": float(pd.to_numeric(walk_compare["SharpeDelta"], errors="coerce").mean()),
        "Cost75BpsCAGRDelta": float(cost_compare.loc[cost_compare["OneWayCostBps"] == 75, "CAGRDelta"].iloc[0]),
        "Cost75BpsSharpeDelta": float(cost_compare.loc[cost_compare["OneWayCostBps"] == 75, "SharpeDelta"].iloc[0]),
        "AvgMonthlyDelta": float(pd.to_numeric(nav_compare["TotalDelta"], errors="coerce").mean()),
        "ResidualExTop3": float(pd.to_numeric(residual["ResidualDelta"], errors="coerce").mean()),
        "ResidualPositiveMonths": int((pd.to_numeric(residual["ResidualDelta"], errors="coerce") > 0).sum()),
        "ResidualNegativeMonths": int((pd.to_numeric(residual["ResidualDelta"], errors="coerce") < 0).sum()),
        "Top1PositiveSymbolShare": _share_of_positive(symbol_summary["ContributionDelta"], 1),
        "Top3PositiveSymbolShare": _share_of_positive(symbol_summary["ContributionDelta"], 3),
        "TopSymbol": None if symbol_summary.empty else str(symbol_summary.iloc[0]["Symbol"]),
        "Top3Symbols": ",".join(symbol_summary.head(3)["Symbol"].astype(str).tolist()),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    strongest = _baseline_variant_map()[BASE_VARIANT_NAME]
    strongest_result = _run_trading_backtest_variant(
        universe,
        price_cache,
        flow_cache,
        monthly_close,
        signal_dates,
        cfg,
        strongest,
    )

    candidates: list[tuple[TradingVariant, Callable[[pd.DataFrame], pd.DataFrame] | None]] = [
        (strongest, None),
        (replace(strongest, name="hybrid_top2_plus_third00125"), _patch_hybrid_top2_plus_third(0.00125)),
        (replace(strongest, name="bonus_schedule_first55_second45"), _patch_bonus_schedule(0.55, 0.45)),
        (replace(strongest, name="bonus_recipient_top1_third_85_15"), _patch_bonus_recipients(0.85, 0.15)),
        (replace(strongest, name="tail_skip_entry_flowweakest_new_bottom4_top25_mid75"), _patch_skip_entry_flowweakest_new_bottom4_top25_mid75()),
        (replace(strongest, name="tail_release_to_nonbottom_proportional"), _patch_tail_release_to_nonbottom_proportional()),
        (replace(strongest, name="tail_release_top50_mid50"), _patch_tail_release_top50_mid50()),
        (replace(strongest, name="multi_step_confirm_top1_flowtop2"), _patch_multi_step_confirm_top1_flowtop2()),
        (replace(strongest, name="regime_weight_defensive_if_top2flowsoft"), _patch_regime_weight_defensive_if_top2flowsoft()),
        (replace(strongest, name="top2_split_49_51"), _patch_top2_split(0.49, 0.51)),
        (
            replace(
                strongest,
                name="alt_family_top3_flat_bonus18",
                breadth_top_slice_count=3,
                breadth_top_slice_bonus_exposure=0.18,
                breadth_bottom_slice_count=None,
                breadth_bottom_slice_penalty=1.0,
                breadth_bottom_slice_penalty_floor=None,
                breadth_bottom_slice_penalty_power=1.0,
            ),
            None,
        ),
    ]

    rows: list[dict[str, float | int | str]] = []
    for variant, patch_fn in candidates:
        result = _run_with_patch(
            variant,
            patch_fn,
            universe,
            price_cache,
            flow_cache,
            monthly_close,
            signal_dates,
            cfg,
        )
        rows.append(_summarize_candidate(variant.name, result, strongest_result))

    compare = pd.DataFrame(rows)
    compare.to_csv(OUTPUT_DIR / "tradeoff_frontier_compare.csv", index=False, encoding="utf-8-sig")

    challengers = compare[compare["Variant"] != BASE_VARIANT_NAME].copy()

    summary = {
        "strongest_variant": BASE_VARIANT_NAME,
        "variants_compared": compare["Variant"].astype(str).tolist(),
        "best_cagr_variant": str(compare.sort_values("CAGR", ascending=False).iloc[0]["Variant"]),
        "best_sharpe_challenger": str(challengers.sort_values("Sharpe", ascending=False).iloc[0]["Variant"]),
        "best_lower_turnover_challenger": str(challengers.sort_values("AnnualTurnover", ascending=True).iloc[0]["Variant"]),
        "lowest_top3_share_challenger": str(challengers.sort_values("Top3PositiveSymbolShare", ascending=True).iloc[0]["Variant"]),
        "most_positive_residual_challenger": str(challengers.sort_values("ResidualExTop3", ascending=False).iloc[0]["Variant"]),
    }
    (OUTPUT_DIR / "tradeoff_frontier_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
