from __future__ import annotations

from pathlib import Path

import pandas as pd

from split_models.backtest import BacktestConfig, run_backtests
from split_models.backtest import _baseline_variant_map
from split_models.backtest import TradingVariant, _build_momentum_candidates_for_date


def test_split_models_backtest_smoke(tmp_path: Path) -> None:
    outputs = run_backtests(output_dir=tmp_path, config=BacktestConfig(signal_start="2022-01-31"))

    assert "CAGR" in outputs["trading_book_backtest_summary"].columns
    assert "WatchGrade" in outputs["tenbagger_backtest_occurrences"].columns
    assert "Benchmark" in outputs["trading_book_benchmark_compare"].columns
    assert "WindowStart" in outputs["trading_book_walkforward_summary"].columns
    assert "OneWayCostBps" in outputs["trading_book_cost_sensitivity"].columns
    assert "Variant" in outputs["trading_book_ablation_compare"].columns
    assert "Variant" in outputs["trading_book_refinement_compare"].columns
    assert "Contribution" in outputs["trading_book_market_contribution_summary"].columns
    assert "WindowStart" in outputs["trading_book_weak_period_window"].columns
    assert (tmp_path / "trading_book_backtest_nav.csv").exists()
    assert (tmp_path / "trading_book_backtest_summary.csv").exists()
    assert (tmp_path / "trading_book_benchmark_compare.csv").exists()
    assert (tmp_path / "trading_book_walkforward_summary.csv").exists()
    assert (tmp_path / "trading_book_cost_sensitivity.csv").exists()
    assert (tmp_path / "trading_book_ablation_compare.csv").exists()
    assert (tmp_path / "trading_book_refinement_compare.csv").exists()
    assert (tmp_path / "trading_book_market_contribution_summary.csv").exists()
    assert (tmp_path / "trading_book_sector_contribution_summary.csv").exists()
    assert (tmp_path / "trading_book_symbol_contribution_summary.csv").exists()
    assert (tmp_path / "trading_book_weak_period_window.csv").exists()
    assert (tmp_path / "trading_book_weak_period_monthly_diagnostics.csv").exists()
    assert (tmp_path / "trading_book_weak_period_market_summary.csv").exists()
    assert (tmp_path / "trading_book_weak_period_sector_summary.csv").exists()
    assert (tmp_path / "tenbagger_backtest_occurrences.csv").exists()
    assert (tmp_path / "tenbagger_backtest_grade_summary.csv").exists()


def test_split_models_backtest_promoted_variant(tmp_path: Path) -> None:
    outputs = run_backtests(
        output_dir=tmp_path,
        config=BacktestConfig(signal_start="2022-01-31", baseline_variant="equal_weight_no_mad"),
    )

    summary = outputs["trading_book_backtest_summary"].iloc[0]
    assert float(summary["CAGR"]) == float(summary["CAGR"])
    assert (tmp_path / "split_models_backtest_summary.json").exists()


def test_baseline_variant_map_includes_ranked_tail_count4_floor35() -> None:
    variant = _baseline_variant_map()["rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count4_floor35_risk_on"]

    assert variant.breadth_bottom_slice_count == 4
    assert variant.breadth_bottom_slice_penalty == 0.60
    assert variant.breadth_bottom_slice_penalty_floor == 0.35


def test_baseline_variant_map_includes_ranked_tail_count5_floor40() -> None:
    variant = _baseline_variant_map()["rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_floor40_risk_on"]

    assert variant.breadth_bottom_slice_count == 5
    assert variant.breadth_bottom_slice_penalty == 0.60
    assert variant.breadth_bottom_slice_penalty_floor == 0.40


def test_baseline_variant_map_includes_ranked_tail_count5_pen55_floor35() -> None:
    variant = _baseline_variant_map()["rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen55_floor35_risk_on"]

    assert variant.breadth_bottom_slice_count == 5
    assert variant.breadth_bottom_slice_penalty == 0.55
    assert variant.breadth_bottom_slice_penalty_floor == 0.35


def test_baseline_variant_map_includes_ranked_tail_count5_pen50_floor30() -> None:
    variant = _baseline_variant_map()["rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen50_floor30_risk_on"]

    assert variant.breadth_bottom_slice_count == 5
    assert variant.breadth_bottom_slice_penalty == 0.50
    assert variant.breadth_bottom_slice_penalty_floor == 0.30


def test_baseline_variant_map_includes_ranked_tail_count7_pen40_floor20() -> None:
    variant = _baseline_variant_map()["rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_risk_on"]

    assert variant.breadth_bottom_slice_count == 7
    assert variant.breadth_bottom_slice_penalty == 0.40
    assert variant.breadth_bottom_slice_penalty_floor == 0.20


def test_baseline_variant_map_includes_ranked_tail_count7_pen40_floor20_bonus18() -> None:
    variant = _baseline_variant_map()["rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_risk_on"]

    assert variant.breadth_top_slice_bonus_exposure == 0.18
    assert variant.breadth_bottom_slice_count == 7
    assert variant.breadth_bottom_slice_penalty == 0.40
    assert variant.breadth_bottom_slice_penalty_floor == 0.20


def test_baseline_variant_map_includes_ranked_tail_count7_pen40_floor20_bonus18_pow05() -> None:
    variant = _baseline_variant_map()["rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on"]

    assert variant.breadth_top_slice_bonus_exposure == 0.18
    assert variant.breadth_bottom_slice_count == 7
    assert variant.breadth_bottom_slice_penalty == 0.40
    assert variant.breadth_bottom_slice_penalty_floor == 0.20
    assert variant.breadth_bottom_slice_penalty_power == 0.50


def test_baseline_variant_map_includes_ranked_tail_count6_pen35_floor20_bonus18_pow05() -> None:
    variant = _baseline_variant_map()["rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"]

    assert variant.breadth_top_slice_bonus_exposure == 0.18
    assert variant.breadth_bottom_slice_count == 6
    assert variant.breadth_bottom_slice_penalty == 0.35
    assert variant.breadth_bottom_slice_penalty_floor == 0.20
    assert variant.breadth_bottom_slice_penalty_power == 0.50


def test_build_momentum_candidates_filters_trend_chase_names() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "FAST",
                "Name": "Fast Runner",
                "Sector": "Industrials",
                "AssetKey": "US:STOCK:FAST",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.30,
                "FlowScore": 0.20,
                "RelVolume20D60D": 1.1,
                "R1M": 0.28,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "CALM",
                "Name": "Calm Compounder",
                "Sector": "Industrials",
                "AssetKey": "US:STOCK:CALM",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.20,
                "FlowScore": 0.15,
                "RelVolume20D60D": 1.0,
                "R1M": 0.12,
            },
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Industrials", "Rank": 1, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_trend_chase_cap",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=1,
            max_r1m=0.20,
        ),
    )

    assert "CALM" in book["Symbol"].tolist()
    assert "FAST" not in book["Symbol"].tolist()


def test_build_momentum_candidates_soft_penalizes_trend_chase_names() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "FAST",
                "Name": "Fast Runner",
                "Sector": "Industrials",
                "AssetKey": "US:STOCK:FAST",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.30,
                "FlowScore": 0.20,
                "RelVolume20D60D": 1.1,
                "R1M": 0.28,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "CALM",
                "Name": "Calm Compounder",
                "Sector": "Industrials",
                "AssetKey": "US:STOCK:CALM",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.20,
                "FlowScore": 0.15,
                "RelVolume20D60D": 1.0,
                "R1M": 0.12,
            },
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Industrials", "Rank": 1, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_trend_chase_soft",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=1,
            soft_max_r1m=0.20,
            soft_r1m_penalty=0.5,
        ),
    )

    weights = dict(zip(book["Symbol"], book["TargetWeight"], strict=False))
    assert "CALM" in weights
    assert "FAST" in weights
    assert weights["FAST"] < weights["CALM"]


def test_build_momentum_candidates_entry_soft_penalizes_only_new_overheated_names() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "OLDHOT",
                "Name": "Old Hot Name",
                "Sector": "Industrials",
                "AssetKey": "US:STOCK:OLDHOT",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.30,
                "FlowScore": 0.20,
                "RelVolume20D60D": 1.1,
                "R1M": 0.28,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "NEWHOT",
                "Name": "New Hot Name",
                "Sector": "Industrials",
                "AssetKey": "US:STOCK:NEWHOT",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.25,
                "FlowScore": 0.18,
                "RelVolume20D60D": 1.0,
                "R1M": 0.26,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "CALM",
                "Name": "Calm Compounder",
                "Sector": "Industrials",
                "AssetKey": "US:STOCK:CALM",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.20,
                "FlowScore": 0.15,
                "RelVolume20D60D": 1.0,
                "R1M": 0.12,
            },
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Industrials", "Rank": 1, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_trend_chase_entry_soft",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=1,
            entry_soft_max_r1m=0.20,
            entry_soft_r1m_penalty=0.5,
        ),
        prev_hold_keys={"US:STOCK:OLDHOT"},
    )

    weights = dict(zip(book["Symbol"], book["TargetWeight"], strict=False))
    assert weights["NEWHOT"] < weights["OLDHOT"]
    assert weights["NEWHOT"] < weights["CALM"]


def test_build_momentum_candidates_sector_cap_limits_same_sector_count() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "A1",
                "Name": "A1",
                "Sector": "Health Care",
                "AssetKey": "US:STOCK:A1",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.30,
                "FlowScore": 0.20,
                "RelVolume20D60D": 1.1,
                "R1M": 0.10,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "A2",
                "Name": "A2",
                "Sector": "Health Care",
                "AssetKey": "US:STOCK:A2",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.29,
                "FlowScore": 0.19,
                "RelVolume20D60D": 1.1,
                "R1M": 0.09,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "A3",
                "Name": "A3",
                "Sector": "Health Care",
                "AssetKey": "US:STOCK:A3",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.28,
                "FlowScore": 0.18,
                "RelVolume20D60D": 1.1,
                "R1M": 0.08,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "B1",
                "Name": "B1",
                "Sector": "Industrials",
                "AssetKey": "US:STOCK:B1",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.27,
                "FlowScore": 0.17,
                "RelVolume20D60D": 1.1,
                "R1M": 0.07,
            },
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Health Care", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Industrials", "Rank": 2, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_sector_cap2",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=1,
            max_positions_per_sector=2,
        ),
    )

    health_care_count = int((book["Sector"] == "Health Care").sum())
    assert health_care_count == 2
    assert "B1" in book["Symbol"].tolist()


def test_build_momentum_candidates_breadth_risk_off_scales_total_exposure() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": f"S{i}",
                "Name": f"S{i}",
                "Sector": "Industrials" if i < 3 else "Health Care",
                "AssetKey": f"US:STOCK:S{i}",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.30 - i * 0.01,
                "FlowScore": 0.20 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.10,
            }
            for i in range(4)
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Industrials", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Health Care", "Rank": 2, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_breadth_risk_off",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            breadth_risk_off_threshold=4,
            breadth_risk_off_exposure=0.75,
        ),
    )

    assert round(float(book["TargetWeight"].sum()), 8) == 0.75


def test_build_momentum_candidates_it_sector_risk_off_scales_when_it_is_dominant() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": f"IT{i}",
                "Name": f"IT{i}",
                "Sector": "Information Technology",
                "AssetKey": f"US:STOCK:IT{i}",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.30 - i * 0.01,
                "FlowScore": 0.20 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.10,
            }
            for i in range(5)
        ]
        + [
            {
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": f"ETF{i}",
                "Name": f"ETF{i}",
                "Sector": "ETF",
                "AssetKey": f"KR:ETF:ETF{i}",
                "MedianDailyValue60D": 50_000_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.20 - i * 0.01,
                "FlowScore": 0.10 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.05,
            }
            for i in range(4)
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "Korea", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Information Technology", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "KR", "Label": "ETF", "Rank": 1, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_breadth_it_risk_off",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            sector_risk_off_name="Information Technology",
            sector_risk_off_weight_threshold=0.55,
            sector_risk_off_exposure=0.80,
        ),
    )

    assert round(float(book["TargetWeight"].sum()), 8) == 0.8


def test_build_momentum_candidates_sector_cap_and_breadth_risk_off_work_together() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "HC1",
                "Name": "HC1",
                "Sector": "Health Care",
                "AssetKey": "US:STOCK:HC1",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.30,
                "FlowScore": 0.20,
                "RelVolume20D60D": 1.1,
                "R1M": 0.10,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "HC2",
                "Name": "HC2",
                "Sector": "Health Care",
                "AssetKey": "US:STOCK:HC2",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.29,
                "FlowScore": 0.19,
                "RelVolume20D60D": 1.1,
                "R1M": 0.09,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "HC3",
                "Name": "HC3",
                "Sector": "Health Care",
                "AssetKey": "US:STOCK:HC3",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.28,
                "FlowScore": 0.18,
                "RelVolume20D60D": 1.1,
                "R1M": 0.08,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "IN1",
                "Name": "IN1",
                "Sector": "Industrials",
                "AssetKey": "US:STOCK:IN1",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.27,
                "FlowScore": 0.17,
                "RelVolume20D60D": 1.1,
                "R1M": 0.07,
            },
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Health Care", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Industrials", "Rank": 2, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_sector_cap2_breadth_risk_off",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            max_positions_per_sector=2,
            breadth_risk_off_threshold=4,
            breadth_risk_off_exposure=0.75,
        ),
    )

    assert int((book["Sector"] == "Health Care").sum()) == 2
    assert round(float(book["TargetWeight"].sum()), 8) == 0.75


def test_build_momentum_candidates_sector_cap_breadth_and_it_risk_off_work_together() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": f"IT{i}",
                "Name": f"IT{i}",
                "Sector": "Information Technology",
                "AssetKey": f"US:STOCK:IT{i}",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.30 - i * 0.01,
                "FlowScore": 0.20 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.10,
            }
            for i in range(3)
        ]
        + [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "HC1",
                "Name": "HC1",
                "Sector": "Health Care",
                "AssetKey": "US:STOCK:HC1",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.21,
                "FlowScore": 0.11,
                "RelVolume20D60D": 1.1,
                "R1M": 0.07,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "HC2",
                "Name": "HC2",
                "Sector": "Health Care",
                "AssetKey": "US:STOCK:HC2",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.20,
                "FlowScore": 0.10,
                "RelVolume20D60D": 1.1,
                "R1M": 0.06,
            },
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Information Technology", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Health Care", "Rank": 2, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_sector_cap2_breadth_it_risk_off",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            max_positions_per_sector=2,
            breadth_risk_off_threshold=4,
            breadth_risk_off_exposure=0.75,
            sector_risk_off_name="Information Technology",
            sector_risk_off_weight_threshold=0.55,
            sector_risk_off_exposure=0.80,
        ),
    )

    assert int((book["Sector"] == "Information Technology").sum()) == 2
    assert round(float(book["TargetWeight"].sum()), 8) == 0.75


def test_build_momentum_candidates_max_sector_risk_off_scales_when_any_sector_dominates() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": f"IT{i}",
                "Name": f"IT{i}",
                "Sector": "Information Technology",
                "AssetKey": f"US:STOCK:IT{i}",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.30 - i * 0.01,
                "FlowScore": 0.20 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.10,
            }
            for i in range(5)
        ]
        + [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "HC1",
                "Name": "HC1",
                "Sector": "Health Care",
                "AssetKey": "US:STOCK:HC1",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.20,
                "FlowScore": 0.10,
                "RelVolume20D60D": 1.1,
                "R1M": 0.05,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "HC2",
                "Name": "HC2",
                "Sector": "Health Care",
                "AssetKey": "US:STOCK:HC2",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.19,
                "FlowScore": 0.09,
                "RelVolume20D60D": 1.1,
                "R1M": 0.05,
            },
            {
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": "ETF1",
                "Name": "ETF1",
                "Sector": "ETF",
                "AssetKey": "KR:ETF:ETF1",
                "MedianDailyValue60D": 50_000_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.18,
                "FlowScore": 0.08,
                "RelVolume20D60D": 1.1,
                "R1M": 0.04,
            },
            {
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": "ETF2",
                "Name": "ETF2",
                "Sector": "ETF",
                "AssetKey": "KR:ETF:ETF2",
                "MedianDailyValue60D": 50_000_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.17,
                "FlowScore": 0.07,
                "RelVolume20D60D": 1.1,
                "R1M": 0.04,
            },
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "Korea", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Information Technology", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Health Care", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "KR", "Label": "ETF", "Rank": 1, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_breadth_max_sector_risk_off",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            breadth_risk_off_threshold=4,
            breadth_risk_off_exposure=0.75,
            sector_risk_off_weight_threshold=0.50,
            sector_risk_off_exposure=0.85,
        ),
    )

    assert round(float(book["TargetWeight"].sum()), 8) == 0.85


def test_build_momentum_candidates_us_position_cap_limits_us_names() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": f"US{i}",
                "Name": f"US{i}",
                "Sector": "Information Technology" if i < 3 else "Industrials",
                "AssetKey": f"US:STOCK:US{i}",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.30 - i * 0.01,
                "FlowScore": 0.20 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.10,
            }
            for i in range(6)
        ]
        + [
            {
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": f"KR{i}",
                "Name": f"KR{i}",
                "Sector": "ETF",
                "AssetKey": f"KR:ETF:KR{i}",
                "MedianDailyValue60D": 50_000_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.18 - i * 0.01,
                "FlowScore": 0.08 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.05,
            }
            for i in range(3)
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "Korea", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Information Technology", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Industrials", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "KR", "Label": "ETF", "Rank": 1, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_breadth_it_us5_cap",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            us_position_cap=5,
            breadth_risk_off_threshold=4,
            breadth_risk_off_exposure=0.75,
            sector_risk_off_name="Information Technology",
            sector_risk_off_weight_threshold=0.55,
            sector_risk_off_exposure=0.80,
        ),
    )

    assert int((book["Market"] == "US").sum()) == 5


def test_build_momentum_candidates_sector_cap_breadth_it_and_us5_cap_work_together() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": f"IT{i}",
                "Name": f"IT{i}",
                "Sector": "Information Technology",
                "AssetKey": f"US:STOCK:IT{i}",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.35 - i * 0.01,
                "FlowScore": 0.25 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.10,
            }
            for i in range(3)
        ]
        + [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": f"IN{i}",
                "Name": f"IN{i}",
                "Sector": "Industrials",
                "AssetKey": f"US:STOCK:IN{i}",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.30 - i * 0.01,
                "FlowScore": 0.20 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.08,
            }
            for i in range(2)
        ]
        + [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": f"HC{i}",
                "Name": f"HC{i}",
                "Sector": "Health Care",
                "AssetKey": f"US:STOCK:HC{i}",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.28 - i * 0.01,
                "FlowScore": 0.18 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.07,
            }
            for i in range(2)
        ]
        + [
            {
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": f"KR{i}",
                "Name": f"KR{i}",
                "Sector": "ETF",
                "AssetKey": f"KR:ETF:KR{i}",
                "MedianDailyValue60D": 50_000_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.18 - i * 0.01,
                "FlowScore": 0.08 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.05,
            }
            for i in range(3)
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "Korea", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Information Technology", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Industrials", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Health Care", "Rank": 3, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "KR", "Label": "ETF", "Rank": 1, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_sector_cap2_breadth_it_us5_cap",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            max_positions_per_sector=2,
            us_position_cap=5,
            breadth_risk_off_threshold=4,
            breadth_risk_off_exposure=0.75,
            sector_risk_off_name="Information Technology",
            sector_risk_off_weight_threshold=0.55,
            sector_risk_off_exposure=0.80,
        ),
    )

    assert int((book["Market"] == "US").sum()) == 5
    assert int((book["Sector"] == "Information Technology").sum()) == 2
    assert round(float(book["TargetWeight"].sum()), 8) == 1.0


def test_build_momentum_candidates_breadth_risk_on_scales_when_book_is_broad() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": f"US{i}",
                "Name": f"US{i}",
                "Sector": "Information Technology" if i < 2 else ("Industrials" if i < 4 else "Health Care"),
                "AssetKey": f"US:STOCK:US{i}",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.35 - i * 0.01,
                "FlowScore": 0.25 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.10,
            }
            for i in range(5)
        ]
        + [
            {
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": f"KR{i}",
                "Name": f"KR{i}",
                "Sector": "ETF",
                "AssetKey": f"KR:ETF:KR{i}",
                "MedianDailyValue60D": 50_000_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.18 - i * 0.01,
                "FlowScore": 0.08 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.05,
            }
            for i in range(3)
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "Korea", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Information Technology", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Industrials", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Health Care", "Rank": 3, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "KR", "Label": "ETF", "Rank": 1, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_sector_cap2_breadth_it_us5_risk_on",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            max_positions_per_sector=2,
            us_position_cap=5,
            breadth_risk_off_threshold=4,
            breadth_risk_off_exposure=0.75,
            breadth_risk_on_min_holdings=7,
            breadth_risk_on_exposure=1.15,
            sector_risk_off_name="Information Technology",
            sector_risk_off_weight_threshold=0.55,
            sector_risk_off_exposure=0.80,
        ),
    )

    assert len(book) == 7
    assert round(float(book["TargetWeight"].sum()), 8) == 1.15


def test_build_momentum_candidates_top_slice_risk_on_overweights_top_two() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": f"US{i}",
                "Name": f"US{i}",
                "Sector": "Information Technology" if i < 2 else ("Industrials" if i < 4 else "Health Care"),
                "AssetKey": f"US:STOCK:US{i}",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.35 - i * 0.02,
                "FlowScore": 0.25 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.10,
            }
            for i in range(5)
        ]
        + [
            {
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": f"KR{i}",
                "Name": f"KR{i}",
                "Sector": "ETF",
                "AssetKey": f"KR:ETF:KR{i}",
                "MedianDailyValue60D": 50_000_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.18 - i * 0.01,
                "FlowScore": 0.08 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.05,
            }
            for i in range(3)
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "Korea", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Information Technology", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Industrials", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Health Care", "Rank": 3, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "KR", "Label": "ETF", "Rank": 1, "AsOfDate": "2026-03-31"},
        ]
    )

    book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_sector_cap2_breadth_it_us5_top2_risk_on",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            breadth_risk_on_min_holdings=7,
            breadth_risk_on_exposure=1.0,
            breadth_top_slice_count=2,
            breadth_top_slice_bonus_exposure=0.15,
        ),
    )

    weights = dict(zip(book["Symbol"], book["TargetWeight"], strict=False))
    assert round(float(book["TargetWeight"].sum()), 8) == 1.15
    assert weights["US0"] == weights["US1"]
    assert weights["US0"] > weights["US2"]


def test_build_momentum_candidates_convex_top_slice_penalizes_tail() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": f"US{i}",
                "Name": f"US{i}",
                "Sector": "Information Technology" if i < 2 else ("Industrials" if i < 4 else "Health Care"),
                "AssetKey": f"US:STOCK:US{i}",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.35 - i * 0.02,
                "FlowScore": 0.25 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.10,
            }
            for i in range(5)
        ]
        + [
            {
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": f"KR{i}",
                "Name": f"KR{i}",
                "Sector": "ETF",
                "AssetKey": f"KR:ETF:KR{i}",
                "MedianDailyValue60D": 50_000_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.18 - i * 0.01,
                "FlowScore": 0.08 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.05,
            }
            for i in range(3)
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "Korea", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Information Technology", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Industrials", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Health Care", "Rank": 3, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "KR", "Label": "ETF", "Rank": 1, "AsOfDate": "2026-03-31"},
        ]
    )

    top2_book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_sector_cap2_breadth_it_us5_top2_risk_on",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            max_positions_per_sector=2,
            us_position_cap=5,
            breadth_risk_on_min_holdings=7,
            breadth_risk_on_exposure=1.0,
            breadth_top_slice_count=2,
            breadth_top_slice_bonus_exposure=0.15,
        ),
    )
    convex_book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="rule_sector_cap2_breadth_it_us5_top2_convex_risk_on",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            max_positions_per_sector=2,
            us_position_cap=5,
            breadth_risk_on_min_holdings=7,
            breadth_risk_on_exposure=1.0,
            breadth_top_slice_count=2,
            breadth_top_slice_bonus_exposure=0.15,
            breadth_bottom_slice_count=3,
            breadth_bottom_slice_penalty=0.60,
        ),
    )

    top2_weights = dict(zip(top2_book["Symbol"], top2_book["TargetWeight"], strict=False))
    convex_weights = dict(zip(convex_book["Symbol"], convex_book["TargetWeight"], strict=False))

    assert round(float(convex_book["TargetWeight"].sum()), 8) == 1.15
    assert convex_weights["US0"] > top2_weights["US0"]
    assert convex_weights["US1"] > top2_weights["US1"]
    assert convex_weights["KR0"] < top2_weights["KR0"]


def test_build_momentum_candidates_convex_tail_can_penalize_worst_more() -> None:
    metrics = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": f"US{i}",
                "Name": f"US{i}",
                "Sector": "Information Technology" if i < 2 else ("Industrials" if i < 4 else "Health Care"),
                "AssetKey": f"US:STOCK:US{i}",
                "MedianDailyValue60D": 50_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.35 - i * 0.02,
                "FlowScore": 0.25 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.10,
            }
            for i in range(5)
        ]
        + [
            {
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": f"KR{i}",
                "Name": f"KR{i}",
                "Sector": "ETF",
                "AssetKey": f"KR:ETF:KR{i}",
                "MedianDailyValue60D": 50_000_000_000.0,
                "CurrentPrice": 100.0,
                "TrendOK": 1,
                "MomentumScore": 0.18 - i * 0.01,
                "FlowScore": 0.08 - i * 0.01,
                "RelVolume20D60D": 1.1,
                "R1M": 0.05,
            }
            for i in range(3)
        ]
    )
    flow_snapshot = pd.DataFrame(
        [
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "US", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "COUNTRY", "Market": "GLOBAL", "Label": "Korea", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Information Technology", "Rank": 1, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Industrials", "Rank": 2, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "US", "Label": "Health Care", "Rank": 3, "AsOfDate": "2026-03-31"},
            {"ScopeType": "SECTOR", "Market": "KR", "Label": "ETF", "Rank": 1, "AsOfDate": "2026-03-31"},
        ]
    )

    flat_tail_book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="top2_convex_flat_tail",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            max_positions_per_sector=2,
            us_position_cap=5,
            breadth_risk_on_min_holdings=7,
            breadth_risk_on_exposure=1.0,
            breadth_top_slice_count=2,
            breadth_top_slice_bonus_exposure=0.15,
            breadth_bottom_slice_count=3,
            breadth_bottom_slice_penalty=0.60,
        ),
    )
    ranked_tail_book = _build_momentum_candidates_for_date(
        metrics,
        flow_snapshot,
        BacktestConfig(),
        variant=TradingVariant(
            name="top2_convex_ranked_tail",
            use_flow_filter=True,
            use_sector_filter=True,
            use_mad_weighting=False,
            min_holdings=4,
            max_positions_per_sector=2,
            us_position_cap=5,
            breadth_risk_on_min_holdings=7,
            breadth_risk_on_exposure=1.0,
            breadth_top_slice_count=2,
            breadth_top_slice_bonus_exposure=0.15,
            breadth_bottom_slice_count=3,
            breadth_bottom_slice_penalty=0.60,
            breadth_bottom_slice_penalty_floor=0.45,
        ),
    )

    flat_tail_weights = dict(zip(flat_tail_book["Symbol"], flat_tail_book["TargetWeight"], strict=False))
    ranked_tail_weights = dict(zip(ranked_tail_book["Symbol"], ranked_tail_book["TargetWeight"], strict=False))

    assert round(float(ranked_tail_book["TargetWeight"].sum()), 8) == 1.15
    assert ranked_tail_weights["KR1"] < flat_tail_weights["KR1"]
    assert ranked_tail_weights["US0"] > flat_tail_weights["US0"]
