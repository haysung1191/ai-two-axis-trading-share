from __future__ import annotations

import pandas as pd

from research_lane_stage1.data.fx_loader import apply_fx_to_kis_prices, load_usdkrw_fx
from research_lane_stage1.data.bithumb_loader import load_bithumb_metadata
from research_lane_stage1.data.kis_loader import load_kis_metadata
from research_lane_stage1.quality.data_quality import scan_ohlcv_quality
from research_lane_stage1.universe.bithumb_universe import build_bithumb_universe
from research_lane_stage1.universe.kis_universe import build_kis_universe


def test_fx_conversion_uses_previous_fx_without_future_leakage() -> None:
    kis = pd.DataFrame(
        [
            {"date": "2026-01-02", "symbol": "AAPL", "currency": "USD", "adj_close": 10.0},
            {"date": "2026-01-02", "symbol": "005930", "currency": "KRW", "adj_close": 70000.0},
            {"date": "2026-01-04", "symbol": "MSFT", "currency": "USD", "adj_close": 20.0},
        ]
    )
    fx = pd.DataFrame(
        [
            {"date": "2026-01-02", "fx_rate": 1300.0},
            {"date": "2026-01-03", "fx_rate": 1310.0},
        ]
    )

    out = apply_fx_to_kis_prices(kis, fx)

    assert out.loc[out["symbol"].eq("AAPL"), "price_krw"].iloc[0] == 13000.0
    assert out.loc[out["symbol"].eq("005930"), "price_krw"].iloc[0] == 70000.0
    assert out.loc[out["symbol"].eq("MSFT"), "price_krw"].iloc[0] == 26200.0
    assert out.loc[out["symbol"].eq("MSFT"), "fx_alignment_flag"].iloc[0] == "fx_forward_filled_from_previous_date"


def test_quality_scan_blocks_duplicate_and_non_positive_prices() -> None:
    df = pd.DataFrame(
        [
            {"date": "2026-01-01", "symbol": "AAA", "close": 1.0, "high": 1.1, "low": 0.9, "volume": 10},
            {"date": "2026-01-01", "symbol": "AAA", "close": -1.0, "high": 1.1, "low": 0.9, "volume": 10},
        ]
    )

    quality = scan_ohlcv_quality(df, "KIS_COMBINED_KRW")

    flags = quality.iloc[0]["blocking_flags"]
    assert "duplicate_dates_unresolved" in flags
    assert "non_positive_close" in flags


def test_bithumb_universe_filters_liquid_nonstable_assets() -> None:
    meta = pd.DataFrame(
        [
            {"symbol": "BTC_KRW", "quote_asset": "KRW", "row_count": 1000, "volume_quote_krw_24h": 2_000_000_000, "is_stablecoin": False, "is_leveraged_token": False},
            {"symbol": "USDT_KRW", "quote_asset": "KRW", "row_count": 2000, "volume_quote_krw_24h": 5_000_000_000, "is_stablecoin": True, "is_leveraged_token": False},
            {"symbol": "NEW_KRW", "quote_asset": "KRW", "row_count": 10, "volume_quote_krw_24h": 5_000_000_000, "is_stablecoin": False, "is_leveraged_token": False},
        ]
    )

    universe, diag = build_bithumb_universe(pd.DataFrame(), meta, pd.DataFrame(), {})

    assert list(universe["symbol"]) == ["BTC_KRW"]
    assert diag["symbol_count"] == 1


def test_kis_universe_keeps_all_four_asset_types_from_metadata() -> None:
    meta = pd.DataFrame(
        [
            {"symbol": "A", "asset_type": "us_stock", "country": "US", "currency": "USD", "is_suspended": False},
            {"symbol": "SPY", "asset_type": "us_etf", "country": "US", "currency": "USD", "is_suspended": False},
            {"symbol": "005930", "asset_type": "kr_stock", "country": "KR", "currency": "KRW", "is_suspended": False},
            {"symbol": "069500", "asset_type": "kr_etf", "country": "KR", "currency": "KRW", "is_suspended": False},
        ]
    )

    universe, diag = build_kis_universe(pd.DataFrame(), meta, pd.DataFrame(), {"row_count_min": 252})

    assert set(universe["asset_type"]) == {"us_stock", "us_etf", "kr_stock", "kr_etf"}
    assert diag["symbol_count"] == 4


def test_live_local_metadata_sources_are_visible() -> None:
    bithumb_meta = load_bithumb_metadata()
    kis_meta = load_kis_metadata()
    fx = load_usdkrw_fx()

    assert len(bithumb_meta) >= 400
    assert len(kis_meta) >= 10000
    assert {"kr_stock", "us_stock", "kr_etf", "us_etf"}.issubset(set(kis_meta["asset_type"]))
    assert fx["date"].max().date().isoformat() >= "2026-05-07"

