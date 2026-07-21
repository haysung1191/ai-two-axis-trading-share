import math

import pandas as pd

from live_core.kis_metrics import blend_component_metrics, summarize_backtest_metrics


def test_summarize_backtest_metrics_smoke():
    idx = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
    out = pd.DataFrame(
        {
            "daily_return": [0.01, -0.02, 0.03],
            "nav": [1.01, 0.9898, 1.019494],
        },
        index=idx,
    )
    regime_state = pd.Series(["UPTREND", "RANGE", "TRANSITION"], index=idx)

    metrics = summarize_backtest_metrics(
        out,
        turns=[0.1, 0.2],
        exposures=[0.8, 0.9],
        holdings_count=[5, 6, 7],
        rebalance_dates_log=[pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-04")],
        trade_buy_count=3,
        trade_sell_count=2,
        regime_state=regime_state,
        osc_entry_count=1,
        osc_exit_count=2,
        osc_stop_count=0,
        rotation_signals=[0.1, 0.2],
        stock_sleeves=[0.6, 0.7],
        etf_sleeves=[0.4, 0.3],
    )

    assert math.isclose(metrics["FinalNAV"], 1.019494)
    assert math.isclose(metrics["AvgTurnover"], 0.15)
    assert math.isclose(metrics["AvgGrossExposure"], 0.85)
    assert math.isclose(metrics["AvgHoldings"], 6.0)
    assert metrics["RebalanceCount"] == 2
    assert metrics["BuyTrades"] == 3
    assert metrics["SellTrades"] == 2
    assert metrics["FirstRebalance"] == "2024-01-02"
    assert metrics["LastRebalance"] == "2024-01-04"
    assert math.isclose(metrics["RangeDaysPct"], 1 / 3)
    assert math.isclose(metrics["UptrendDaysPct"], 1 / 3)
    assert math.isclose(metrics["TransitionDaysPct"], 1 / 3)


def test_blend_component_metrics_weighted_fields():
    idx = pd.to_datetime(["2024-01-02", "2024-01-03"])
    out = pd.DataFrame(
        {
            "daily_return": [0.01, 0.02],
            "nav": [1.01, 1.0302],
        },
        index=idx,
    )
    spec = {"A": 0.6, "B": 0.4}
    component_results = {
        "A": (
            out,
            {
                "AvgTurnover": 0.10,
                "AnnualTurnover": 1.0,
                "AvgGrossExposure": 0.80,
                "AvgHoldings": 5.0,
                "RebalanceCount": 10,
                "BuyTrades": 4,
                "SellTrades": 2,
                "RangeDaysPct": 0.2,
                "UptrendDaysPct": 0.7,
                "DowntrendDaysPct": 0.1,
                "TransitionDaysPct": 0.0,
                "OscEntryCount": 1,
                "OscExitCount": 2,
                "OscStopCount": 0,
                "RotationSignalAvg": 0.3,
                "AvgStockSleeve": 0.9,
                "AvgEtfSleeve": 0.1,
                "FirstRebalance": "2024-01-02",
                "LastRebalance": "2024-01-10",
            },
        ),
        "B": (
            out,
            {
                "AvgTurnover": 0.30,
                "AnnualTurnover": 3.0,
                "AvgGrossExposure": 0.60,
                "AvgHoldings": 3.0,
                "RebalanceCount": 20,
                "BuyTrades": 8,
                "SellTrades": 6,
                "RangeDaysPct": 0.4,
                "UptrendDaysPct": 0.3,
                "DowntrendDaysPct": 0.2,
                "TransitionDaysPct": 0.1,
                "OscEntryCount": 3,
                "OscExitCount": 4,
                "OscStopCount": 1,
                "RotationSignalAvg": 0.5,
                "AvgStockSleeve": 0.7,
                "AvgEtfSleeve": 0.3,
                "FirstRebalance": "2024-01-03",
                "LastRebalance": "2024-01-11",
            },
        ),
    }

    metrics = blend_component_metrics(spec, component_results, out)

    assert math.isclose(metrics["AvgTurnover"], 0.18)
    assert math.isclose(metrics["AnnualTurnover"], 1.8)
    assert math.isclose(metrics["AvgGrossExposure"], 0.72)
    assert math.isclose(metrics["AvgHoldings"], 4.2)
    assert metrics["RebalanceCount"] == 14
    assert metrics["BuyTrades"] == 6
    assert metrics["SellTrades"] == 4
    assert metrics["OscEntryCount"] == 2
    assert metrics["OscExitCount"] == 3
    assert metrics["OscStopCount"] == 0
    assert metrics["FirstRebalance"] == "2024-01-02"
    assert metrics["LastRebalance"] == "2024-01-11"
