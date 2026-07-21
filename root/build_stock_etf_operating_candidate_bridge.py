from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
MOMENTUM_ROOT = ROOT / "momentum"
if str(MOMENTUM_ROOT) not in sys.path:
    sys.path.insert(0, str(MOMENTUM_ROOT))

from split_models import run_pipeline  # noqa: E402
from split_models.backtest import (  # noqa: E402
    BacktestConfig,
    _asset_key,
    _baseline_variant_map,
    _build_daily_caches,
    _build_monthly_close_matrix,
    _build_momentum_candidates_for_date,
    _allowed_labels,
    _historical_flow_snapshot,
    _historical_metrics,
    _load_kr_universe,
    _load_us_universe,
    _signal_dates,
    _summarize_returns,
    _walkforward_summary,
)
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_sweep import (  # noqa: E402
    STRONGEST_VARIANT,
)
from tools.analysis.analyze_split_models_operational_conversion_concentration_carry_kr_etf_trim_micro import (  # noqa: E402
    _compose_patch as _compose_micro_patch,
)


OPS_DIR = ROOT / "ops" / "stock_etf_operating_candidate_bridge"
LATEST_JSON = OPS_DIR / "stock_etf_operating_candidate_bridge_latest.json"
TARGET_BOOK_CSV = OPS_DIR / "stock_etf_operating_target_book_latest.csv"
ORDER_INTENT_CSV = OPS_DIR / "stock_etf_operating_order_intent_latest.csv"
TINY_LIVE_REPAIR_CSV = OPS_DIR / "stock_etf_tiny_live_executable_repair_latest.csv"
LIMITED_LIVE_POLICY_PATH = ROOT / "ops" / "runstate" / "limited_live_policy.json"
BROKER_POLICY_PATH = ROOT / "ops" / "runstate" / "broker_paper_policy.json"
RISK_QUEUE_PATH = ROOT / "reports" / "model_factory" / "stock_risk_conversion_queue_latest.json"
DIRECT_DEVELOPMENT_PATH = ROOT / "reports" / "model_factory" / "two_axis_direct_model_development_latest.json"


NO_ORDER_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}


CANDIDATE_TRIM = {
    "stock_aggressive__tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim20_gap02_top2": 0.20,
    "stock_aggressive__tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim21_gap02_top2": 0.21,
    "stock_aggressive__tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim22_gap02_top2": 0.22,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def kis_universe_validation_state() -> dict[str, Any]:
    return {
        "mode": "daily_close_presence",
        "source": "operator_policy_daily_close_presence",
        "verifier_status": "NOT_REQUIRED",
        "operation_ready": True,
        "all_verified": True,
        "blockers": [],
        "generated_at": utc_now(),
    }


def truthy_flag(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def candidate_rows() -> list[dict[str, Any]]:
    return list(load_json(RISK_QUEUE_PATH).get("queue", []) or [])


def top_direct_kis_variant() -> dict[str, Any]:
    direct = load_json(DIRECT_DEVELOPMENT_PATH)
    variants = [
        row
        for row in (direct.get("kis") or {}).get("top_variants", [])
        if row.get("status") == "DIRECT_CONVERSION_PASS"
    ]
    return variants[0] if variants else {}


def direct_kis_parent_candidate_id() -> str:
    variant = top_direct_kis_variant()
    if variant.get("status") != "DIRECT_CONVERSION_PASS":
        return ""
    parent_id = str(variant.get("parent_candidate_id", "") or "")
    if parent_id not in CANDIDATE_TRIM:
        return ""
    if any(str(row.get("candidate_id", "")) == parent_id for row in candidate_rows()):
        return parent_id
    return ""


def default_candidate_id() -> str:
    direct_parent_id = direct_kis_parent_candidate_id()
    if direct_parent_id:
        return direct_parent_id
    for row in candidate_rows():
        cid = str(row.get("candidate_id", ""))
        if "trim21" in cid:
            return cid
    rows = candidate_rows()
    return str(rows[0].get("candidate_id", "")) if rows else ""


def select_candidate(candidate_id: str) -> dict[str, Any]:
    for row in candidate_rows():
        if str(row.get("candidate_id", "")) == candidate_id:
            return row
    raise SystemExit(f"unknown_stock_candidate_id:{candidate_id}")


def fixed_exposure_cap(candidate: dict[str, Any]) -> float:
    conversion = candidate.get("proposed_conversion") or {}
    return float(conversion.get("fixed_exposure_cap", 0.0) or 0.0)


def enrich_current_metrics(candidates: pd.DataFrame) -> pd.DataFrame:
    out = candidates.copy()
    out["AssetKey"] = out["Market"].astype(str) + ":" + out["AssetType"].astype(str) + ":" + out["Symbol"].astype(str)
    return out


def add_tiny_live_affordability(target: pd.DataFrame) -> pd.DataFrame:
    if target.empty:
        return target.copy()
    out = target.copy()
    prices = pd.to_numeric(out.get("CurrentPrice"), errors="coerce").fillna(0.0)
    notionals = pd.to_numeric(out.get("TargetNotionalKRW"), errors="coerce").fillna(0.0)
    quantities = []
    for notional, price in zip(notionals, prices):
        quantities.append(int(notional // price) if price > 0 else 0)
    out["EstimatedTargetQuantityAtLastClose"] = quantities
    out["TinyLiveBuyableAtLastClose"] = out["EstimatedTargetQuantityAtLastClose"] > 0
    out["EstimatedBuyableNotionalAtLastClose"] = out["EstimatedTargetQuantityAtLastClose"] * prices
    return out


def tiny_live_execution_warnings(target: pd.DataFrame, *, min_buyable_symbols: int = 2) -> list[str]:
    if target.empty or "TinyLiveBuyableAtLastClose" not in target.columns:
        return ["KIS_TINY_LIVE_TARGET_BOOK_NOT_EVALUATED"]
    buyable_count = int(target["TinyLiveBuyableAtLastClose"].sum())
    if buyable_count < min_buyable_symbols:
        return ["KIS_TINY_LIVE_LOW_BUYABLE_COVERAGE"]
    return []


def tiny_live_repair_quality_checks(rows: list[dict[str, Any]], *, min_buyable_count: int = 2) -> dict[str, Any]:
    if not rows:
        return {
            "status": "TINY_LIVE_REPAIR_QUALITY_INPUT_MISSING",
            "checks": {},
        }
    buyable_count = sum(1 for row in rows if int(row.get("estimated_quantity") or 0) >= 1)
    sectors = [str(row.get("sector") or "") for row in rows if row.get("sector")]
    sector_counts = {sector: sectors.count(sector) for sector in sorted(set(sectors))}
    momentum_scores = [float(row.get("momentum_score") or 0.0) for row in rows]
    target_notional = [float(row.get("target_notional_krw") or 0.0) for row in rows]
    estimated_quantity = [int(row.get("estimated_quantity") or 0) for row in rows]
    checks = {
        "buyable_count_at_least_minimum": buyable_count >= int(min_buyable_count),
        "all_rows_buyable": all(quantity >= 1 for quantity in estimated_quantity),
        "average_momentum_score_at_least_0_5": (sum(momentum_scores) / len(momentum_scores)) >= 0.5 if momentum_scores else False,
        "max_sector_count_at_most_2": max(sector_counts.values()) <= 2 if sector_counts else False,
        "positive_target_notional": all(value > 0 for value in target_notional),
    }
    return {
        "status": "TINY_LIVE_REPAIR_QUALITY_PASS" if all(checks.values()) else "TINY_LIVE_REPAIR_QUALITY_ATTENTION",
        "checks": checks,
        "buyable_count": buyable_count,
        "average_momentum_score": sum(momentum_scores) / len(momentum_scores) if momentum_scores else 0.0,
        "min_momentum_score": min(momentum_scores) if momentum_scores else 0.0,
        "sector_counts": sector_counts,
        "estimated_gross_notional_krw": sum(target_notional),
    }


def summarize_order_intent_frame(order_intent: pd.DataFrame) -> dict[str, Any]:
    if order_intent.empty or "SubmitAllowed" not in order_intent.columns:
        return {"rows": int(len(order_intent)), "submit_allowed_count": 0, "submit_allowed_symbols": []}
    submit_allowed = order_intent["SubmitAllowed"].map(truthy_flag)
    return {
        "rows": int(len(order_intent)),
        "submit_allowed_count": int(submit_allowed.sum()),
        "submit_allowed_symbols": (
            order_intent.loc[submit_allowed, "Symbol"].astype(str).tolist()
            if "Symbol" in order_intent.columns
            else []
        ),
    }


def target_book_summary(target: pd.DataFrame) -> dict[str, Any]:
    return {
        "gross_target_weight": float(target["TargetWeight"].sum()) if not target.empty else 0.0,
        "cash_weight": float(target["CashWeight"].iloc[0]) if not target.empty and "CashWeight" in target.columns else 1.0,
        "symbols": target["Symbol"].astype(str).tolist() if not target.empty else [],
        "tiny_live_buyable_symbol_count": int(target["TinyLiveBuyableAtLastClose"].sum()) if not target.empty and "TinyLiveBuyableAtLastClose" in target.columns else 0,
        "tiny_live_unbuyable_symbols": target.loc[~target["TinyLiveBuyableAtLastClose"], "Symbol"].astype(str).tolist() if not target.empty and "TinyLiveBuyableAtLastClose" in target.columns else [],
        "estimated_buyable_notional_krw": float(target["EstimatedBuyableNotionalAtLastClose"].sum()) if not target.empty and "EstimatedBuyableNotionalAtLastClose" in target.columns else 0.0,
    }


def build_tiny_live_executable_repair(
    current_candidates: pd.DataFrame,
    *,
    candidate_id: str,
    total_capital_krw: float,
    fixed_exposure: float,
    desired_positions: int = 3,
) -> dict[str, Any]:
    per_slot_budget = float(total_capital_krw) * float(fixed_exposure) / max(1, int(desired_positions))
    frame = current_candidates.copy()
    if frame.empty:
        return {"status": "TINY_LIVE_REPAIR_INPUT_MISSING", "candidates": []}

    frame["CurrentPrice"] = pd.to_numeric(frame.get("CurrentPrice"), errors="coerce").fillna(0.0)
    frame["MomentumScore"] = pd.to_numeric(frame.get("MomentumScore"), errors="coerce").fillna(0.0)
    frame["LiquidityOK"] = pd.to_numeric(frame.get("LiquidityOK"), errors="coerce").fillna(0)
    eligible = frame[
        frame["Market"].astype(str).eq("KR")
        & frame["CurrentPrice"].gt(0.0)
        & frame["CurrentPrice"].le(per_slot_budget)
        & frame["LiquidityOK"].ge(1)
    ].copy()
    if "CandidateState" in eligible.columns:
        eligible = eligible[eligible["CandidateState"].astype(str).isin(["ENTRY", "HOLD"])]
    eligible = eligible.sort_values(["MomentumScore", "CurrentPrice", "Symbol"], ascending=[False, True, True]).head(desired_positions)
    rows: list[dict[str, Any]] = []
    if not eligible.empty:
        target_weight = float(fixed_exposure) / float(len(eligible))
        target_notional = float(total_capital_krw) * target_weight
        for _, row in eligible.iterrows():
            price = float(row.get("CurrentPrice") or 0.0)
            quantity = int(target_notional // price) if price > 0 else 0
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "market": row.get("Market"),
                    "asset_type": row.get("AssetType"),
                    "symbol": row.get("Symbol"),
                    "name": row.get("Name"),
                    "sector": row.get("Sector"),
                    "momentum_score": float(row.get("MomentumScore") or 0.0),
                    "current_price": price,
                    "target_weight": target_weight,
                    "target_notional_krw": target_notional,
                    "estimated_quantity": quantity,
                }
            )
    buyable_count = sum(1 for row in rows if int(row["estimated_quantity"]) >= 1)
    quality = tiny_live_repair_quality_checks(rows, min_buyable_count=min(desired_positions, 2))
    return {
        "status": "TINY_LIVE_REPAIR_RESEARCH_READY" if buyable_count >= min(desired_positions, 2) and quality["status"] == "TINY_LIVE_REPAIR_QUALITY_PASS" else "TINY_LIVE_REPAIR_INSUFFICIENT_QUALITY",
        "order_paths_allowed": False,
        "counts_as_live_evidence": False,
        "reason": "lot_size_affordability_research_only",
        "desired_positions": int(desired_positions),
        "per_slot_budget_krw": per_slot_budget,
        "buyable_count": buyable_count,
        "candidate_symbols": [str(row["symbol"]) for row in rows],
        "quality": quality,
        "candidates": rows,
    }


def repair_can_drive_execution(repair: dict[str, Any]) -> bool:
    validation = repair.get("historical_oos_validation") or {}
    quality = repair.get("quality") or {}
    return (
        repair.get("status") == "TINY_LIVE_REPAIR_RESEARCH_READY"
        and quality.get("status") == "TINY_LIVE_REPAIR_QUALITY_PASS"
        and validation.get("status") == "TINY_LIVE_REPAIR_OOS_PASS"
        and int(repair.get("buyable_count") or 0) > 0
        and bool(repair.get("candidates"))
    )


def repair_candidates_to_target_frame(repair: dict[str, Any], *, candidate_id: str, total_capital_krw: float) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in repair.get("candidates", []) or []:
        target_weight = float(row.get("target_weight") or 0.0)
        rows.append(
            {
                "CandidateId": candidate_id,
                "Market": row.get("market"),
                "AssetType": row.get("asset_type"),
                "Symbol": str(row.get("symbol", "")).zfill(6),
                "Name": row.get("name"),
                "Sector": row.get("sector"),
                "TargetWeight": target_weight,
                "TargetNotionalKRW": float(row.get("target_notional_krw") or 0.0),
                "CurrentPrice": float(row.get("current_price") or 0.0),
                "MomentumScore": float(row.get("momentum_score") or 0.0),
                "PriceSource": "split_models_latest_local_backdata",
                "QuoteRequiredBeforeSubmit": True,
                "SourceModelWeight": target_weight,
                "FixedExposureCap": float(target_weight * len(repair.get("candidates", []) or [])),
            }
        )
    target = pd.DataFrame(rows)
    if target.empty:
        return target
    target["CashWeight"] = max(0.0, 1.0 - float(target["TargetWeight"].sum()))
    target["ExecutionTargetSource"] = "tiny_live_affordability_repair"
    target = target.sort_values(["TargetWeight", "MomentumScore", "Symbol"], ascending=[False, False, True]).reset_index(drop=True)
    return add_tiny_live_affordability(target)


def build_order_intent(target: pd.DataFrame, blockers: list[str]) -> pd.DataFrame:
    order_cols = [
        "CandidateId",
        "Market",
        "AssetType",
        "Symbol",
        "Name",
        "Sector",
        "TargetWeight",
        "TargetNotionalKRW",
        "CurrentPrice",
        "PriceSource",
        "QuoteRequiredBeforeSubmit",
        "ExecutionTargetSource",
    ]
    order_intent = target[[col for col in order_cols if col in target.columns]].copy() if not target.empty else pd.DataFrame(columns=order_cols)
    if not order_intent.empty:
        order_intent["ExecutionSide"] = "BUY"
        order_intent["SubmitAllowed"] = not blockers
    return order_intent


def _split_nav(nav: pd.DataFrame, start: int, end: int) -> dict[str, Any]:
    window = nav.iloc[start:end].copy()
    if window.empty:
        return {"months": 0, "CAGR": 0.0, "MDD": 0.0, "Sharpe": 0.0, "FinalNAV": 1.0}
    summary = _summarize_returns(window["NetReturn"], window["NextDate"])
    return {
        "months": int(len(window)),
        "CAGR": float(summary["CAGR"]),
        "MDD": float(summary["MDD"]),
        "Sharpe": float(summary["Sharpe"]),
        "FinalNAV": float(summary["FinalNAV"]),
    }


def _cost_stress_summary(nav: pd.DataFrame, *, extra_one_way_cost_bps: float) -> dict[str, Any]:
    if nav.empty:
        return {"months": 0, "CAGR": 0.0, "MDD": 0.0, "Sharpe": 0.0, "FinalNAV": 1.0}
    stressed = nav.copy()
    stressed["NetReturn"] = pd.to_numeric(stressed["GrossReturn"], errors="coerce").fillna(0.0) - pd.to_numeric(
        stressed["Turnover"], errors="coerce"
    ).fillna(0.0) * (float(extra_one_way_cost_bps) / 10000.0)
    summary = _summarize_returns(stressed["NetReturn"], stressed["NextDate"])
    return {
        "months": int(len(stressed)),
        "one_way_cost_bps": float(extra_one_way_cost_bps),
        "CAGR": float(summary["CAGR"]),
        "MDD": float(summary["MDD"]),
        "Sharpe": float(summary["Sharpe"]),
        "FinalNAV": float(summary["FinalNAV"]),
    }


def build_historical_tiny_live_repair_pool(metrics: pd.DataFrame, flow_snapshot: pd.DataFrame, cfg: BacktestConfig) -> pd.DataFrame:
    if metrics.empty or flow_snapshot.empty:
        return pd.DataFrame()
    countries, sectors = _allowed_labels(flow_snapshot, cfg)
    df = metrics.copy()
    df["CountryLabel"] = ["US" if str(market) == "US" else "Korea" for market in df["Market"]]
    df["CountryAligned"] = df["CountryLabel"].isin(countries).astype(int)
    df["SectorAligned"] = [
        int((row.Sector in sectors.get(str(row.Market), set())) or (str(row.Sector) in {"Unknown", "ETF"}))
        for row in df.itertuples(index=False)
    ]
    min_values = [cfg.us_min_median_value if str(market) == "US" else cfg.kr_min_median_value for market in df["Market"]]
    df["LiquidityOK"] = (
        (pd.to_numeric(df["MedianDailyValue60D"], errors="coerce").fillna(0.0) >= pd.Series(min_values, index=df.index))
        & (pd.to_numeric(df["CurrentPrice"], errors="coerce").fillna(0.0) >= cfg.min_price)
    ).astype(int)
    df["FlowAligned"] = ((df["CountryAligned"] == 1) & ((df["SectorAligned"] == 1) | df["AssetType"].isin(["ETF"]))).astype(int)
    df = df.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True]).reset_index(drop=True)
    df["CandidateState"] = "EXCLUDE"
    eligible = df[
        (pd.to_numeric(df["TrendOK"], errors="coerce").fillna(0).astype(int) == 1)
        & (df["LiquidityOK"] == 1)
        & (pd.to_numeric(df["MomentumScore"], errors="coerce").fillna(0.0) > 0.0)
    ].copy()
    entry_idx = eligible[eligible["FlowAligned"] == 1].head(cfg.trading_book_size).index
    hold_idx = eligible[eligible["FlowAligned"] == 1].iloc[cfg.trading_book_size : cfg.trading_book_size + cfg.trading_book_size].index
    df.loc[entry_idx, "CandidateState"] = "ENTRY"
    df.loc[hold_idx, "CandidateState"] = "HOLD"
    return df


def validate_tiny_live_repair_oos(
    *,
    total_capital_krw: float,
    fixed_exposure: float,
    desired_positions: int = 3,
    signal_start: str = "2020-01-31",
) -> dict[str, Any]:
    cfg = BacktestConfig(signal_start=signal_start)
    us_stocks, us_etfs = _load_us_universe()
    kr_universe = _load_kr_universe()
    universe = pd.concat([us_stocks, us_etfs, kr_universe], ignore_index=True)
    price_cache, flow_cache = _build_daily_caches(universe)
    monthly_close = _build_monthly_close_matrix(universe, price_cache)
    signal_dates = _signal_dates(monthly_close, cfg.signal_start)
    if len(signal_dates) < 4:
        return {"status": "TINY_LIVE_REPAIR_OOS_INPUT_MISSING", "months": 0}

    nav = 1.0
    prev_weights = pd.Series(0.0, index=monthly_close.columns)
    nav_rows: list[dict[str, Any]] = []
    position_rows: list[dict[str, Any]] = []

    for idx, signal_date in enumerate(signal_dates[:-1]):
        next_date = signal_dates[idx + 1]
        metrics = _historical_metrics(universe, price_cache, flow_cache, signal_date)
        if metrics.empty:
            continue
        flow_snapshot = _historical_flow_snapshot(metrics, monthly_close, signal_date, cfg)
        if flow_snapshot.empty:
            continue
        candidate_frame = build_historical_tiny_live_repair_pool(metrics, flow_snapshot, cfg)
        repair = build_tiny_live_executable_repair(
            candidate_frame,
            candidate_id="historical_tiny_live_affordability_repair",
            total_capital_krw=total_capital_krw,
            fixed_exposure=fixed_exposure,
            desired_positions=desired_positions,
        )
        weights = pd.Series(0.0, index=monthly_close.columns)
        for row in repair.get("candidates", []) or []:
            asset_key = _asset_key(str(row.get("market")), str(row.get("asset_type")), str(row.get("symbol")).zfill(6))
            if asset_key in weights.index:
                weights[asset_key] = float(row.get("target_weight") or 0.0)
                position_rows.append(
                    {
                        "SignalDate": signal_date.strftime("%Y-%m-%d"),
                        "NextDate": next_date.strftime("%Y-%m-%d"),
                        "AssetKey": asset_key,
                        "Symbol": str(row.get("symbol")).zfill(6),
                        "TargetWeight": float(row.get("target_weight") or 0.0),
                        "EstimatedQuantity": int(row.get("estimated_quantity") or 0),
                    }
                )
        turnover = float((weights - prev_weights).abs().sum())
        next_returns = monthly_close.loc[next_date] / monthly_close.loc[signal_date] - 1.0
        gross = float((weights * next_returns.reindex(weights.index).fillna(0.0)).sum())
        net = gross - turnover * (cfg.one_way_cost_bps / 10000.0)
        nav *= 1.0 + net
        nav_rows.append(
            {
                "SignalDate": signal_date.strftime("%Y-%m-%d"),
                "NextDate": next_date.strftime("%Y-%m-%d"),
                "GrossReturn": gross,
                "NetReturn": net,
                "Turnover": turnover,
                "NAV": nav,
                "Holdings": int((weights > 0).sum()),
            }
        )
        prev_weights = weights.copy()

    nav_df = pd.DataFrame(nav_rows)
    positions_df = pd.DataFrame(position_rows)
    if nav_df.empty:
        return {"status": "TINY_LIVE_REPAIR_OOS_EMPTY", "months": 0}

    summary = _split_nav(nav_df, 0, len(nav_df))
    split_idx = max(1, int(len(nav_df) * 0.7))
    train = _split_nav(nav_df, 0, split_idx)
    holdout = _split_nav(nav_df, split_idx, len(nav_df))
    walkforward = _walkforward_summary(nav_df, window_months=24, step_months=12)
    positive_folds = int((walkforward["CAGR"] > 0).sum()) if not walkforward.empty else 0
    pass_folds = int(((walkforward["CAGR"] > 0) & (walkforward["MDD"] >= -0.35)).sum()) if not walkforward.empty else 0
    stress = _cost_stress_summary(nav_df, extra_one_way_cost_bps=25.0)
    active_month_coverage = float((pd.to_numeric(nav_df["Holdings"], errors="coerce").fillna(0) > 0).mean())
    average_holdings = float(pd.to_numeric(nav_df["Holdings"], errors="coerce").mean())
    holdings_check = active_month_coverage >= 0.30 if int(desired_positions) <= 1 else average_holdings >= min(2.0, float(desired_positions)) * 0.50
    checks = {
        "months_at_least_36": int(summary["months"]) >= 36,
        "holdout_cagr_positive": float(holdout["CAGR"]) > 0.0,
        "holdout_mdd_above_minus_35": float(holdout["MDD"]) >= -0.35,
        "walkforward_two_positive_folds": positive_folds >= 2,
        "walkforward_two_pass_folds": pass_folds >= 2,
        "cost_25bps_cagr_positive": float(stress["CAGR"]) > 0.0,
        "tiny_live_position_coverage_ok": holdings_check,
    }
    return {
        "status": "TINY_LIVE_REPAIR_OOS_PASS" if all(checks.values()) else "TINY_LIVE_REPAIR_OOS_ATTENTION",
        "order_paths_allowed": False,
        "counts_as_live_evidence": False,
        "reason": "historical_oos_validation_only",
        "checks": checks,
        "months": int(summary["months"]),
        "summary": summary,
        "train_70pct": train,
        "holdout_30pct": holdout,
        "cost_stress_25bps": stress,
        "walkforward": {
            "folds": int(len(walkforward)),
            "positive_folds": positive_folds,
            "pass_folds": pass_folds,
            "worst_mdd": float(walkforward["MDD"].min()) if not walkforward.empty else 0.0,
        },
        "desired_positions": int(desired_positions),
        "average_holdings": average_holdings,
        "active_month_coverage": active_month_coverage,
        "unique_symbols": int(positions_df["Symbol"].nunique()) if not positions_df.empty else 0,
    }


def build_candidate_book(candidate_id: str, total_capital_krw: float) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    candidate = select_candidate(candidate_id)
    if candidate_id not in CANDIDATE_TRIM:
        raise SystemExit(f"candidate_not_currently_connectable:{candidate_id}")

    outputs = run_pipeline()
    current_candidates = enrich_current_metrics(outputs["momentum_trade_candidates"])
    flow_snapshot = outputs["flow_regime_snapshot"].copy()
    cfg = BacktestConfig()
    strongest = _baseline_variant_map()[STRONGEST_VARIANT]

    raw_book = _build_momentum_candidates_for_date(
        current_candidates,
        flow_snapshot,
        cfg,
        variant=strongest,
        prev_hold_keys=set(),
    )
    patched = _compose_micro_patch(CANDIDATE_TRIM[candidate_id])(raw_book)
    if patched.empty:
        target = patched.copy()
    else:
        target = patched.copy()
        target["SourceModelWeight"] = pd.to_numeric(target["TargetWeight"], errors="coerce").fillna(0.0)
        exposure = fixed_exposure_cap(candidate)
        target["TargetWeight"] = target["SourceModelWeight"] * exposure
        target["CashWeight"] = max(0.0, 1.0 - float(target["TargetWeight"].sum()))
        target["CandidateId"] = candidate_id
        target["FixedExposureCap"] = exposure
        target["TargetNotionalKRW"] = target["TargetWeight"] * float(total_capital_krw)
        target["PriceSource"] = "split_models_latest_local_backdata"
        target["QuoteRequiredBeforeSubmit"] = True
        target = target.sort_values(["TargetWeight", "MomentumScore", "Symbol"], ascending=[False, False, True]).reset_index(drop=True)
        target = add_tiny_live_affordability(target)

    max_asof = str(current_candidates["AsOfDate"].max()) if "AsOfDate" in current_candidates.columns else ""
    direct_recommendation = top_direct_kis_variant()
    universe_validation = kis_universe_validation_state()
    tiny_live_repair = build_tiny_live_executable_repair(
        current_candidates,
        candidate_id=f"{candidate_id}__tiny_live_affordability_repair",
        total_capital_krw=total_capital_krw,
        fixed_exposure=fixed_exposure_cap(candidate),
        desired_positions=1,
    )
    tiny_live_repair["historical_oos_validation"] = validate_tiny_live_repair_oos(
        total_capital_krw=total_capital_krw,
        fixed_exposure=fixed_exposure_cap(candidate),
        desired_positions=int(tiny_live_repair.get("desired_positions") or 1),
    )
    model_target = target.copy()
    execution_target_source = "source_model_target_book"
    execution_target = model_target
    min_buyable_symbols = 2
    model_warnings = tiny_live_execution_warnings(model_target, min_buyable_symbols=min_buyable_symbols)
    if model_warnings and repair_can_drive_execution(tiny_live_repair):
        execution_target = repair_candidates_to_target_frame(
            tiny_live_repair,
            candidate_id=f"{candidate_id}__tiny_live_affordability_repair",
            total_capital_krw=total_capital_krw,
        )
        execution_target_source = "tiny_live_affordability_repair"
        min_buyable_symbols = max(1, min(2, int(tiny_live_repair.get("desired_positions") or 1)))
    execution_warnings = tiny_live_execution_warnings(execution_target, min_buyable_symbols=min_buyable_symbols)
    blockers = stock_submit_blockers(execution_target)
    order_intent = build_order_intent(execution_target, blockers)
    order_intent_summary = summarize_order_intent_frame(order_intent)
    summary = {
        "generated_at_utc": utc_now(),
        "candidate_id": candidate_id,
        "candidate_selection_source": "direct_development_recommendation" if candidate_id == str(direct_recommendation.get("parent_candidate_id", "") or "") else "fallback_default",
        "status": "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY" if not blockers else "OPERATING_CANDIDATE_CONNECTED_SUBMIT_BLOCKED",
        "source_candidate_status": candidate.get("status"),
        "safe_experiment_scope": candidate.get("safe_experiment_scope"),
        "source_order_paths_allowed": truthy_flag(candidate.get("order_paths_allowed", False)),
        "no_order_assertions": dict(NO_ORDER_ASSERTIONS),
        "universe_validation_mode": universe_validation["mode"],
        "universe_validation_source": universe_validation["source"],
        "universe_validation_verifier_status": universe_validation["verifier_status"],
        "universe_validation_operation_ready": universe_validation["operation_ready"],
        "universe_validation_all_verified": universe_validation["all_verified"],
        "universe_validation_blockers": universe_validation["blockers"],
        "universe_validation_generated_at": universe_validation.get("generated_at"),
        "fixed_exposure_cap": fixed_exposure_cap(candidate),
        "before": candidate.get("before", {}),
        "proposed_conversion": candidate.get("proposed_conversion", {}),
        "direct_development_recommendation": direct_recommendation,
        "current_data": {
            "max_candidate_asof": max_asof,
            "flow_snapshot_asof": str(flow_snapshot["AsOfDate"].iloc[0]) if not flow_snapshot.empty else "",
            "candidate_rows": int(len(current_candidates)),
            "model_target_book_rows": int(len(model_target)),
            "target_book_rows": int(len(execution_target)),
            "order_intent_rows": order_intent_summary["rows"],
            "order_intent_submit_allowed_count": order_intent_summary["submit_allowed_count"],
            "order_intent_submit_allowed_symbols": order_intent_summary["submit_allowed_symbols"],
        },
        "execution_target_source": execution_target_source,
        "model_target_book": target_book_summary(model_target),
        "target_book": target_book_summary(execution_target),
        "tiny_live_executable_repair": tiny_live_repair,
        "execution_warnings": execution_warnings,
        "model_execution_warnings": model_warnings,
        "blockers": blockers,
        "artifacts": {
            "target_book_csv": str(TARGET_BOOK_CSV),
            "order_intent_csv": str(ORDER_INTENT_CSV),
            "latest_json": str(LATEST_JSON),
        },
    }
    return execution_target, order_intent, summary


def stock_submit_blockers(target: pd.DataFrame | None = None) -> list[str]:
    limited_live_policy = load_json(LIMITED_LIVE_POLICY_PATH)
    broker_policy = load_json(BROKER_POLICY_PATH)
    blockers: list[str] = []
    if target is not None:
        if target.empty:
            blockers.append("TARGET_BOOK_EMPTY")
        elif "CurrentPrice" not in target.columns or pd.to_numeric(target["CurrentPrice"], errors="coerce").fillna(0.0).le(0.0).any():
            blockers.append("TARGET_BOOK_DAILY_CLOSE_MISSING")
    if float(limited_live_policy.get("stock_cap_krw", 0.0) or 0.0) <= 0.0:
        blockers.append("STOCK_CAP_KRW_ZERO")
    if not truthy_flag(broker_policy.get("broker_submit_allowed", False)):
        blockers.append("BROKER_POLICY_SUBMIT_BLOCKED")
    if not truthy_flag(broker_policy.get("live_enabled", False)):
        blockers.append("BROKER_POLICY_LIVE_DISABLED")
    if not truthy_flag(broker_policy.get("real_orders_allowed", False)):
        blockers.append("BROKER_POLICY_REAL_ORDERS_BLOCKED")
    return blockers


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    tmp_path.replace(path)


def write_csv_atomic(path: Path, frame: pd.DataFrame) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    frame.to_csv(tmp_path, index=False, encoding="utf-8-sig")
    tmp_path.replace(path)


def bridge_semantic_payload(payload: dict[str, Any]) -> dict[str, Any]:
    semantic = dict(payload)
    semantic.pop("generated_at_utc", None)
    return semantic


def preserve_generated_at_for_same_bridge(summary: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    if not existing.get("generated_at_utc"):
        return summary
    if bridge_semantic_payload(summary) != bridge_semantic_payload(existing):
        return summary
    out = dict(summary)
    out["generated_at_utc"] = existing["generated_at_utc"]
    return out


def write_outputs(target: pd.DataFrame, order_intent: pd.DataFrame, summary: dict[str, Any]) -> None:
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv_atomic(TARGET_BOOK_CSV, target)
    write_csv_atomic(ORDER_INTENT_CSV, order_intent)
    repair_rows = (summary.get("tiny_live_executable_repair") or {}).get("candidates", [])
    write_csv_atomic(TINY_LIVE_REPAIR_CSV, pd.DataFrame(repair_rows))
    summary.setdefault("artifacts", {})["tiny_live_repair_csv"] = str(TINY_LIVE_REPAIR_CSV)
    summary = preserve_generated_at_for_same_bridge(summary, load_json(LATEST_JSON))
    write_json_atomic(LATEST_JSON, summary)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", default="")
    parser.add_argument("--total-capital-krw", type=float, default=100000.0)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    candidate_id = args.candidate_id or default_candidate_id()
    target, order_intent, summary = build_candidate_book(candidate_id, args.total_capital_krw)
    write_outputs(target, order_intent, summary)

    if args.format == "json":
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    print(f"status={summary['status']}")
    print(f"candidate_id={candidate_id}")
    print(f"target_book_rows={summary['current_data']['target_book_rows']}")
    print(f"symbols={','.join(summary['target_book']['symbols'])}")
    print(f"gross_target_weight={summary['target_book']['gross_target_weight']:.4f}")
    print(f"blockers={','.join(summary['blockers']) if summary['blockers'] else '-'}")


if __name__ == "__main__":
    main()
