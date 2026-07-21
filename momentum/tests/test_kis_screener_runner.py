from datetime import datetime

from live_core.kis_screener_runner import (
    annotate_stock_ranking_comparison,
    build_screening_frame,
    resolve_screening_window,
)


def test_resolve_screening_window_rolls_weekend_back() -> None:
    past_str, today_str = resolve_screening_window(datetime(2026, 4, 18, 9, 0))
    assert today_str == "20260417"
    assert past_str == "20250313"


def test_build_screening_frame_sorts_by_mode_and_builds_rows() -> None:
    class FakeApi:
        def get_historical_prices(self, code, start, end, period):
            assert start == "20250312"
            assert end == "20260416"
            assert period == "D"
            return [{"code": code}]

    def calc(prices):
        code = prices[0]["code"]
        if code == "A":
            return {"MAD_gap_pct": 5.0, "avg_momentum": 1.0}
        if code == "B":
            return {"MAD_gap_pct": 8.0, "avg_momentum": 9.0}
        return None

    df = build_screening_frame(
        api=FakeApi(),
        tickers=[("A", "Alpha"), ("B", "Beta"), ("C", "Gamma")],
        momentum_calculator=calc,
        etf_mode=False,
        max_items=3,
        print_fn=lambda _: None,
        now=datetime(2026, 4, 16, 9, 0),
    )

    assert list(df["Code"]) == ["B", "A"]
    assert list(df["Type"]) == ["개별종목", "개별종목"]
    assert df.attrs["screening_quality"]["attempted_ticker_count"] == 3
    assert df.attrs["screening_quality"]["price_fetch_success_count"] == 3
    assert df.attrs["screening_quality"]["valid_momentum_count"] == 2
    assert df.attrs["screening_quality"]["invalid_momentum_count"] == 1
    assert df.attrs["screening_quality"]["empty_price_count"] == 0
    assert df.attrs["screening_quality"]["quality_status"] == "caution"
    assert df.attrs["screening_quality"]["success_coverage"] == 0.6667


def test_build_screening_frame_tracks_empty_price_and_invalid_momentum_samples() -> None:
    class FakeApi:
        def get_historical_prices(self, code, start, end, period):
            if code == "A":
                return []
            return [{"code": code}]

    def calc(prices):
        if not prices:
            return None
        code = prices[0]["code"]
        if code == "B":
            return None
        return {"MAD_gap_pct": 4.0, "avg_momentum": 2.0}

    df = build_screening_frame(
        api=FakeApi(),
        tickers=[("A", "Alpha"), ("B", "Beta"), ("C", "Gamma")],
        momentum_calculator=calc,
        etf_mode=False,
        max_items=3,
        print_fn=lambda _: None,
        now=datetime(2026, 4, 16, 9, 0),
    )

    quality = df.attrs["screening_quality"]
    assert list(df["Code"]) == ["C"]
    assert quality["price_fetch_success_count"] == 2
    assert quality["empty_price_count"] == 1
    assert quality["invalid_momentum_count"] == 1
    assert quality["empty_price_codes_sample"] == ["A"]
    assert quality["invalid_momentum_codes_sample"] == ["B"]
    assert quality["quality_status"] == "review"
    assert quality["price_fetch_coverage"] == 0.6667
    assert quality["success_coverage"] == 0.3333


def test_classify_screening_quality_marks_stable_when_coverage_is_clean() -> None:
    from live_core.kis_screener_runner import classify_screening_quality

    status, note = classify_screening_quality(
        attempted_ticker_count=20,
        price_fetch_success_count=20,
        valid_momentum_count=20,
        empty_price_count=0,
        invalid_momentum_count=0,
    )

    assert status == "stable"
    assert "healthy" in note


def test_build_screening_frame_uses_avg_momentum_for_etf_mode() -> None:
    class FakeApi:
        def get_historical_prices(self, code, start, end, period):
            return [{"code": code}]

    def calc(prices):
        code = prices[0]["code"]
        return {
            "MAD_gap_pct": 1.0 if code == "A" else 9.0,
            "avg_momentum": 9.0 if code == "A" else 1.0,
        }

    df = build_screening_frame(
        api=FakeApi(),
        tickers=[("A", "Alpha"), ("B", "Beta")],
        momentum_calculator=calc,
        etf_mode=True,
        max_items=2,
        print_fn=lambda _: None,
        now=datetime(2026, 4, 16, 9, 0),
    )

    assert list(df["Code"]) == ["A", "B"]
    assert list(df["Type"]) == ["ETF", "ETF"]


def test_build_screening_frame_prefers_offensive_score_for_stocks() -> None:
    class FakeApi:
        def get_historical_prices(self, code, start, end, period):
            return [{"code": code}]

    def calc(prices):
        code = prices[0]["code"]
        if code == "A":
            return {"MAD_gap_pct": 9.0, "avg_momentum": 2.0, "offensive_score": 20.0}
        return {"MAD_gap_pct": 5.0, "avg_momentum": 1.0, "offensive_score": 80.0}

    df = build_screening_frame(
        api=FakeApi(),
        tickers=[("A", "Alpha"), ("B", "Beta")],
        momentum_calculator=calc,
        etf_mode=False,
        max_items=2,
        print_fn=lambda _: None,
        now=datetime(2026, 4, 16, 9, 0),
    )

    assert list(df["Code"]) == ["B", "A"]
    assert list(df["offensive_rank"]) == [1, 2]
    assert list(df["legacy_mad_rank"]) == [2, 1]
    assert list(df["rank_delta_vs_legacy"]) == [1, -1]


def test_annotate_stock_ranking_comparison_is_noop_without_required_columns() -> None:
    df = annotate_stock_ranking_comparison(
        build_screening_frame(
            api=type(
                "FakeApi",
                (),
                {"get_historical_prices": lambda self, code, start, end, period: [{"code": code}]},
            )(),
            tickers=[("A", "Alpha")],
            momentum_calculator=lambda prices: {"avg_momentum": 1.0},
            etf_mode=True,
            max_items=1,
            print_fn=lambda _: None,
            now=datetime(2026, 4, 16, 9, 0),
        )
    )

    assert "offensive_rank" not in df.columns
