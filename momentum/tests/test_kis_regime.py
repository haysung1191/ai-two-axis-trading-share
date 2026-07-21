from types import SimpleNamespace

import pandas as pd

from live_core.kis_regime import compute_regime_state, merge_rank_frames, rotation_signal_from_ranks


def _strategy(**overrides):
    kwargs = {
        "rotation_top_k": 5,
        "rotation_tilt_strength": 0.20,
        "rotation_min_sleeve_weight": 0.25,
        "regime_ma_window": 200,
        "regime_slope_window": 20,
        "regime_breadth_threshold": 0.55,
        "osc_lookback": 20,
        "range_slope_threshold": 0.015,
        "range_dist_threshold": 0.03,
        "range_breakout_persistence_threshold": 0.35,
        "range_breadth_tolerance": 0.15,
        "use_regime_state_model": False,
    }
    kwargs.update(overrides)
    return SimpleNamespace(**kwargs)


def test_merge_rank_frames_preserves_order_without_duplicates():
    primary = pd.DataFrame({"buy_score": [5.0, 4.0, 3.0]}, index=["AAA", "BBB", "CCC"])
    additions = pd.DataFrame({"buy_score": [9.0, 8.0]}, index=["DDD", "BBB"])

    merged = merge_rank_frames(primary, ["BBB"], additions, limit=3)

    assert list(merged.index) == ["BBB", "DDD", "AAA"]


def test_rotation_signal_from_ranks_handles_empty_and_etf_tilt():
    stg = _strategy(rotation_top_k=2, rotation_tilt_strength=0.2, rotation_min_sleeve_weight=0.25)

    empty_signal = rotation_signal_from_ranks(pd.DataFrame(), pd.DataFrame(), stg)
    assert empty_signal == (0.0, 0.5, 0.5)

    rank_s = pd.DataFrame({"buy_score": [1.0, 0.9], "avg_mom": [0.1, 0.2]}, index=["AAA", "BBB"])
    rank_e = pd.DataFrame({"buy_score": [3.0, 2.5], "avg_mom": [0.4, 0.3]}, index=["ETF1", "ETF2"])

    raw_signal, stock_sleeve, etf_sleeve = rotation_signal_from_ranks(rank_s, rank_e, stg)

    assert raw_signal > 0
    assert etf_sleeve > stock_sleeve
    assert round(stock_sleeve + etf_sleeve, 10) == 1.0


def test_compute_regime_state_returns_expected_columns():
    idx = pd.date_range("2024-01-01", periods=260, freq="B")
    close_s = pd.DataFrame(
        {
            "AAA": pd.Series(range(100, 360), index=idx, dtype=float),
            "BBB": pd.Series(range(80, 340), index=idx, dtype=float),
            "CCC": pd.Series(range(120, 380), index=idx, dtype=float),
        }
    )
    stg = _strategy(use_regime_state_model=True)

    regime_df = compute_regime_state(close_s, stg)

    expected_columns = {
        "MarketProxy",
        "MarketMA",
        "MarketSlope",
        "SlopeNorm",
        "Breadth",
        "DistFromMA",
        "BreakoutPersistence",
        "RiskOn",
        "RegimeState",
    }
    assert expected_columns.issubset(regime_df.columns)
    assert len(regime_df) == len(close_s)
    assert set(regime_df["RegimeState"].dropna().unique()).issubset({"UPTREND", "DOWNTREND", "RANGE", "TRANSITION"})
    assert regime_df["RiskOn"].dtype == bool
